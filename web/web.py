"""Flask web app for Samuel Malíšek Klimabot.

Layout:
- Header: title "Samuel Malíšek Klimabot" + Reset button
- Left sidebar: live customer state as it gets mutated via update_customer_state
- Center: chat (SSE streamed bot replies, tool call indicators)
- Right sidebar: handoff Markdown rendered when capture_lead fires

Every browser tab gets its own bot.Session (id sent in the X-Session-Id header),
so concurrent visitors never share a conversation.

Run:  .venv/bin/python web/web.py   (Windows: .venv/Scripts/python.exe; create with ./setup_project.sh)
Then: open http://127.0.0.1:5000 in a browser.

This app is a public demo, so its limits are ON by default (KLIMABOT_DEMO=0 turns them
off for local debugging). Set HOST=0.0.0.0 and PORT for the hosting platform, and
KLIMABOT_TRUSTED_PROXIES=1 behind a single reverse proxy (e.g. a Hugging Face Space).
Spend is bounded in three layers: bot.py (per message and per conversation, checked
before every model call), this file (per network and per day, saved to disk), and the
Anthropic Console (a workspace spend limit on the demo's API key, the last backstop).

The first run loads the KB + embeddings (~30-60s), then it's instant.
"""
from __future__ import annotations

import atexit
import collections
import datetime
import hashlib
import hmac
import html
import ipaddress
import json
import logging
import secrets
import signal
import sys
import threading
import time
from pathlib import Path

# bot.py sits one level up. Add parent dir to sys.path so `import bot` works.
PARENT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PARENT_DIR))

# Chdir so relative paths (knowledge/, config/, data/) resolve from the project root.
import os
os.chdir(PARENT_DIR)
# .env first: KLIMABOT_DEMO / LEAD_MAIL_DEMO set there must count below (bot loads it only at import).
from dotenv import load_dotenv  # noqa: E402
load_dotenv(PARENT_DIR / ".env")
# Demo leads may carry made-up or someone else's details: tag the PM's e-mail (read by bot at import).
if os.getenv("KLIMABOT_DEMO", "1") == "1":
    os.environ.setdefault("LEAD_MAIL_DEMO", "1")

# Importing bot.py executes module-level KB loading, embedding cache load, BM25 build, etc.
# REPL is guarded by `if __name__ == "__main__":` so it won't trigger.
import bot  # noqa: E402  (intentional after sys.path mutation)
import cost_report  # noqa: E402

from flask import Flask, Response, jsonify, request, send_from_directory  # noqa: E402
from werkzeug.middleware.proxy_fix import ProxyFix  # noqa: E402

app = Flask(__name__, static_folder=str(Path(__file__).parent / "static"))
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024  # a chat message is small; refuse bigger bodies before parsing
log = logging.getLogger("klimabot.web")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# Number of reverse proxies in front of the app (e.g. 1 on a Hugging Face Space).
# Only then is X-Forwarded-For trusted, and only the hop those proxies appended —
# the left part of the header is client-controlled and would let anyone dodge the
# per-IP limits. 0 (default) uses the socket address.
TRUSTED_PROXIES = int(os.getenv("KLIMABOT_TRUSTED_PROXIES", "0"))
if TRUSTED_PROXIES:
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=TRUSTED_PROXIES)


# ---------------------------------------------------------------------------
# Demo limits (0 = unlimited). On by default: this app is a public demo.
# ---------------------------------------------------------------------------

DEMO = os.getenv("KLIMABOT_DEMO", "1") == "1"


def _limit(name, demo_default, cast=int):
    return cast(os.getenv(name, demo_default if DEMO else 0))


MAX_TURNS_PER_SESSION = _limit("KLIMABOT_MAX_TURNS", 25)
MAX_MESSAGE_CHARS = _limit("KLIMABOT_MAX_MESSAGE_CHARS", 800)
NEW_SESSIONS_PER_IP_PER_HOUR = _limit("KLIMABOT_SESSIONS_PER_IP_HOUR", 20)   # a Reset counts too
MESSAGES_PER_IP_PER_MINUTE = _limit("KLIMABOT_MESSAGES_PER_IP_MINUTE", 8)
TURNS_IN_FLIGHT_PER_IP = _limit("KLIMABOT_TURNS_IN_FLIGHT_PER_IP", 2)
MAX_CONCURRENT_TURNS = _limit("KLIMABOT_MAX_CONCURRENT_TURNS", 6)
# USD, priced by bot.py from model_prices.json. One conversation is capped in bot.py
# (KLIMABOT_SESSION_USD_CAP); these cap what one network and all visitors together
# can spend per day (UTC).
IP_DAILY_USD = _limit("KLIMABOT_IP_DAILY_USD", 2.0, float)
DAILY_USD_BUDGET = _limit("KLIMABOT_DAILY_USD_BUDGET", 5.0, float)
REPO_URL = os.getenv("KLIMABOT_REPO_URL", "")

# A conversation is finished when its tab closes (/api/end) or after this long without a
# message; ending it is what e-mails a captured lead to the PM (bot.end_session).
SESSION_IDLE_SECONDS = int(os.getenv("KLIMABOT_IDLE_MINUTES") or 30) * 60
EVICTABLE_AFTER_SECONDS = 10 * 60   # when the registry is full, only visitors quiet this long may be dropped
# A closed tab (/api/end) is finished after this grace, unless the same tab comes back first: a page
# reload sends /api/end too and then resumes the conversation from sessionStorage.
END_GRACE_SECONDS = 20
SWEEP_SECONDS = 5
MAX_TRANSCRIPT_EVENTS = 1_500        # what /api/history replays after a reload
# Events a reloaded page needs to rebuild the conversation (state and sidebars included).
TRANSCRIPT_EVENTS = {"token", "notice", "tool_call", "tool_result", "state", "handoff", "quote",
                     "quick_replies", "turn_complete", "error"}
# /admin (the cost report) is off unless a token is set; the login is any user name + this password.
ADMIN_TOKEN = os.getenv("KLIMABOT_ADMIN_TOKEN", "").strip()
MAX_SESSIONS = 300
LEDGER_PATH = bot.DATA_DIR / ".demo_spend.json"


# ---------------------------------------------------------------------------
# Visitor sessions
# ---------------------------------------------------------------------------

class Visitor:
    def __init__(self):
        self.session = bot.Session()
        self.last_seen = time.time()
        self.turns = 0
        self.lock = threading.Lock()  # one bot turn at a time per visitor
        self.transcript = []          # (event, payload) the page showed, for /api/history after a reload
        self.ending_at = None         # set by /api/end: finished then, unless the tab comes back


_visitors: dict[str, Visitor] = {}
_registry_lock = threading.Lock()
_hits: dict[tuple[str, str], collections.deque] = collections.defaultdict(collections.deque)
_in_flight: collections.Counter = collections.Counter()   # running turns per network
_turn_slots = threading.BoundedSemaphore(MAX_CONCURRENT_TURNS) if MAX_CONCURRENT_TURNS else None


def _client_key():
    """The visitor's network: the IPv4 address, or the IPv6 /64 (one home or phone
    gets a whole /64, so per-address limits would be free to dodge)."""
    # ProxyFix (see TRUSTED_PROXIES) has already put the trusted client address here.
    raw = request.remote_addr or "?"
    try:
        ip = ipaddress.ip_address(raw)
    except ValueError:
        return raw
    if ip.version == 6 and not ip.ipv4_mapped:
        return str(ipaddress.ip_network(f"{ip}/64", strict=False))
    return str(getattr(ip, "ipv4_mapped", None) or ip)


def _rate_limited(kind, limit, window_seconds):
    """Sliding-window counter per client network. Returns True if this hit exceeds `limit`."""
    if not limit:
        return False
    now = time.time()
    with _registry_lock:
        if len(_hits) > 5000:  # drop networks with no hit in the last hour so the table can't grow forever
            for key in [k for k, q in _hits.items() if not q or q[-1] <= now - 3600]:
                del _hits[key]
        q = _hits[(kind, _client_key())]
        while q and q[0] <= now - window_seconds:
            q.popleft()
        if len(q) >= limit:
            return True
        q.append(now)
        return False


def _prune_visitors():
    """Under the registry lock: remove visitors to make room and return their sessions,
    so the caller can end them (a log rewrite) after releasing the lock. Returns None
    when the registry is full of recently active visitors — they are never dropped
    mid-conversation."""
    now = time.time()
    drop = [sid for sid, v in _visitors.items() if _finished(v, now) and not v.lock.locked()]
    need = len(_visitors) - len(drop) - MAX_SESSIONS + 1
    if need > 0:
        quiet = sorted((v.last_seen, sid) for sid, v in _visitors.items()
                       if sid not in drop and not v.lock.locked()
                       and now - v.last_seen > EVICTABLE_AFTER_SECONDS)
        if len(quiet) < need:
            return None
        drop += [sid for _, sid in quiet[:need]]
    return [_visitors.pop(sid).session for sid in drop]


def _finished(v, now):
    """Idle for SESSION_IDLE_SECONDS, or its tab closed (/api/end) and didn't come back in time."""
    return now - v.last_seen > SESSION_IDLE_SECONDS or (v.ending_at is not None and now >= v.ending_at)


def _end_idle_visitors():
    """End the conversations nobody has written to for SESSION_IDLE_SECONDS, or whose tab closed
    and didn't come back within END_GRACE_SECONDS. Never one with a reply being prepared."""
    now = time.time()
    with _registry_lock:
        idle = [sid for sid, v in _visitors.items() if _finished(v, now) and not v.lock.locked()]
        sessions = [_visitors.pop(sid).session for sid in idle]
    for session in sessions:  # outside the registry lock: log rewrites, mail queueing
        bot.end_session(session)
    return len(sessions)


def _sweep_forever():
    while True:
        time.sleep(SWEEP_SECONDS)
        try:
            _end_idle_visitors()
        except Exception:
            log.exception("idle sweep failed")


def _end_all_visitors():
    """At shutdown: every open conversation is finished (so captured leads still reach the PM)."""
    with _registry_lock:
        sessions = [v.session for v in _visitors.values()]
        _visitors.clear()
    for session in sessions:
        bot.end_session(session)


def _current_visitor():
    sid = request.headers.get("X-Session-Id", "")
    with _registry_lock:
        v = _visitors.get(sid)
        if v:
            v.last_seen = time.time()
            v.ending_at = None  # the tab is back (a reload): the conversation goes on
        return v


# --- Daily spend ledger (USD), saved to disk so a restart doesn't reset it -----------
# Networks are stored as salted hashes; the salt changes with the day, like the totals.

def _today():
    return datetime.datetime.now(datetime.timezone.utc).date().isoformat()


def _fresh_ledger():
    return {"date": _today(), "salt": secrets.token_hex(8), "total": 0.0, "per_ip": {}}


def _load_ledger():
    try:
        data = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
        if data.get("date") == _today():
            return {"date": data["date"], "salt": str(data["salt"]), "total": float(data["total"]),
                    "per_ip": {str(k): float(x) for k, x in data["per_ip"].items()}}
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        pass
    return _fresh_ledger()


_ledger = _load_ledger()
_reserved = {"total": 0.0, "per_ip": collections.Counter()}   # turns still running; memory only
_ledger_io_lock = threading.Lock()


def _ledger_roll():
    """Under the registry lock: start a new ledger at UTC midnight."""
    if _ledger["date"] != _today():
        _ledger.clear()
        _ledger.update(_fresh_ledger())


def _net_id(key):
    return hashlib.sha256((_ledger["salt"] + key).encode()).hexdigest()[:16]


def _reserve(key, amount):
    """Reserve `amount` USD for one turn against today's global and per-network budget.
    Returns (reason, net_id): reason is "daily" / "ip" when it doesn't fit, None once reserved."""
    with _registry_lock:
        _ledger_roll()
        net = _net_id(key)
        if DAILY_USD_BUDGET and _ledger["total"] + _reserved["total"] + amount > DAILY_USD_BUDGET:
            return "daily", net
        if IP_DAILY_USD and _ledger["per_ip"].get(net, 0.0) + _reserved["per_ip"][net] + amount > IP_DAILY_USD:
            return "ip", net
        _reserved["total"] += amount
        _reserved["per_ip"][net] += amount
        return None, net


def _settle(net, reserved, spent):
    """Swap a turn's reservation for what it actually cost, and save the day's totals."""
    with _registry_lock:
        _ledger_roll()
        _reserved["total"] = max(_reserved["total"] - reserved, 0.0)
        left = _reserved["per_ip"][net] - reserved
        if left > 1e-9:
            _reserved["per_ip"][net] = left
        else:
            _reserved["per_ip"].pop(net, None)
        if spent <= 0:
            return
        _ledger["total"] += spent
        _ledger["per_ip"][net] = _ledger["per_ip"].get(net, 0.0) + spent
        snapshot = json.dumps(_ledger)
    with _ledger_io_lock:  # tmp + rename, outside the registry lock
        try:
            tmp = LEDGER_PATH.with_suffix(".json.tmp")
            tmp.write_text(snapshot, encoding="utf-8")
            tmp.replace(LEDGER_PATH)
        except OSError as e:
            log.warning("spend ledger write failed: %s", e)


def _rejected(kind):
    """Log a refused request (the network as today's salted hash, never the raw IP)."""
    log.info("limit %s net=%s", kind, _net_id(_client_key()))


def _error(status, message):
    return jsonify({"error": message}), status


EXPIRED = "Relácia vypršala. Začíname novú konverzáciu."
CONTACT_HINT = f"Napíšte nám prosím na {bot.COMPANY_CONTACT}."
TOO_MANY_SESSIONS = "Príliš veľa nových konverzácií z vašej siete. Skúste to o chvíľu."


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/")
def index():
    """Serve the single-file UI."""
    return send_from_directory(app.static_folder, "index.html")


@app.get("/api/config")
def get_config():
    """Tell the UI whether to show the demo banner and where the source lives."""
    return jsonify({"demo": DEMO, "repo_url": REPO_URL, "max_turns": MAX_TURNS_PER_SESSION,
                    "max_message_chars": MAX_MESSAGE_CHARS, "lead_mail": bot.LEAD_MAIL_ENABLED})


@app.post("/api/session")
def new_session():
    """Start a fresh conversation for this browser tab."""
    if _rate_limited("session", NEW_SESSIONS_PER_IP_PER_HOUR, 3600):
        _rejected("sessions_per_hour")
        return _error(429, TOO_MANY_SESSIONS)
    sid = secrets.token_urlsafe(16)
    with _registry_lock:
        dropped = _prune_visitors()
        if dropped is not None:
            _visitors[sid] = Visitor()
    if dropped is None:
        _rejected("server_full")
        return _error(503, "Demo je práve plné. Skúste to prosím o pár minút.")
    for session in dropped:  # log rewrites happen outside the registry lock
        bot.end_session(session)
    return jsonify({"session_id": sid})


@app.get("/api/state")
def get_state():
    """Return this visitor's customer state as JSON."""
    v = _current_visitor()
    if not v:
        return _error(409, EXPIRED)
    return jsonify(dict(v.session.customer_state))


@app.get("/api/handoff")
def get_handoff():
    """Return the handoff Markdown captured in this visitor's session. 204 if none yet."""
    v = _current_visitor()
    if not v:
        return _error(409, EXPIRED)
    path = v.session.handoff_path
    if path is None or not path.exists():
        return ("", 204)
    return jsonify({
        "path": bot._rel(path),
        "markdown": path.read_text(encoding="utf-8"),
        "modified": path.stat().st_mtime,
    })


@app.post("/api/reset")
def reset():
    """Replace this visitor's session with a fresh one (new log file). A reset starts a
    conversation with a fresh budget, so it counts against the new-sessions limit."""
    v = _current_visitor()
    if not v:
        return _error(409, EXPIRED)
    if not v.lock.acquire(blocking=False):
        return _error(429, "Počkajte, kým bot dokončí odpoveď.")
    try:
        if _rate_limited("session", NEW_SESSIONS_PER_IP_PER_HOUR, 3600):
            _rejected("sessions_per_hour")
            return _error(429, TOO_MANY_SESSIONS)
        old, v.session, v.turns, v.transcript = v.session, bot.Session(), 0, []
    finally:
        v.lock.release()
    bot.end_session(old)
    return jsonify({"ok": True})


@app.post("/api/end")
def end():
    """The tab is closing (navigator.sendBeacon on pagehide, which can't set headers, so the
    id comes in the body). A reload sends this too, so the conversation is finished — and its
    lead e-mailed to the PM — by the sweep after END_GRACE_SECONDS, unless the tab comes back."""
    data = request.get_json(force=True, silent=True)
    sid = str((data.get("session_id") if isinstance(data, dict) else "") or request.headers.get("X-Session-Id", ""))
    with _registry_lock:
        v = _visitors.get(sid)
        if v is not None:
            v.ending_at = time.time() + END_GRACE_SECONDS
    return ("", 204)


@app.get("/api/history")
def history():
    """What this tab has shown so far, as the events the page replays after a reload."""
    v = _current_visitor()
    if not v:
        return _error(409, EXPIRED)
    resp = jsonify({"events": [{"event": e, "data": d} for e, d in list(v.transcript)], "turns": v.turns})
    resp.headers["Cache-Control"] = "no-store"  # personal data
    return resp


@app.post("/api/feedback")
def feedback():
    """👍 / 👎 on a bot reply, logged in the conversation's log (cost_report counts them)."""
    v = _current_visitor()
    if not v:
        return _error(409, EXPIRED)
    if _rate_limited("feedback", 30, 60):
        return _error(429, "Príliš veľa hodnotení naraz.")
    data = request.get_json(force=True, silent=True)
    rating = data.get("rating") if isinstance(data, dict) else None
    if rating not in ("up", "down"):
        return _error(400, "rating musí byť up alebo down")
    index = data.get("reply_index")
    bot.use_session(v.session)
    bot.log_event("reply_feedback", rating=rating, reply_index=index if isinstance(index, int) else None,
                  reply_excerpt=str(data.get("excerpt") or "")[:300])
    return ("", 204)


_admin_lock = threading.Lock()


def _admin_authorized():
    auth = request.authorization
    password = (auth.password or "") if auth is not None and auth.type == "basic" else ""
    return hmac.compare_digest(password.encode(), ADMIN_TOKEN.encode())


@app.get("/admin")
def admin():
    """The cost report and today's demo spend, behind HTTP Basic auth (KLIMABOT_ADMIN_TOKEN)."""
    if not ADMIN_TOKEN:
        return ("", 404)
    if _rate_limited("admin", 20, 60):
        _rejected("admin_rate")
        return ("", 429)
    if not _admin_authorized():
        return Response("Prihlásenie je potrebné.", 401,
                        {"WWW-Authenticate": 'Basic realm="Klimabot admin", charset="UTF-8"'})
    paths = sorted((bot.DATA_DIR / "logs").glob("*.jsonl"))
    with _admin_lock:  # render_report prints into a swapped sys.stdout
        summaries = [(p, cost_report.summarize(p)) for p in paths]
        rows = [(p, s) for p, s in summaries if s["user_msgs"]]  # every start of the app logs an empty session
        report = cost_report.render_report(rows)
    with _registry_lock:
        spent, reserved, active = _ledger["total"], _reserved["total"], len(_visitors)
    sessions = [s for _, s in rows]
    votes = sum((s["feedback"] for s in sessions), collections.Counter())
    cards = [
        ("Dnešná útrata dema", f"${spent:.2f}" + (f" / ${DAILY_USD_BUDGET:.2f}" if DAILY_USD_BUDGET else ""),
         f"rezervované ${reserved:.2f}"),
        ("Otvorené konverzácie", str(active), f"limit {MAX_SESSIONS}"),
        ("Konverzácie v logoch", str(len(sessions)),
         f"${sum(s['cost_usd'] for s in sessions):.2f} spolu · bez správ: {len(summaries) - len(rows)}"),
        ("Leady", str(sum(s["leads"] for s in sessions)),
         f"GDPR porušenia: {sum(1 for s in sessions if s['gdpr_status'] == 'violation')}"),
        ("Hodnotenia odpovedí", f"👍 {votes['up']} · 👎 {votes['down']}", "z webového chatu"),
    ]
    card_html = "".join(f'<div class="card"><div class="k">{html.escape(k)}</div><div class="v">{html.escape(v)}</div>'
                        f'<div class="s">{html.escape(sub)}</div></div>' for k, v, sub in cards)
    page = ADMIN_PAGE.replace("{cards}", card_html).replace("{report}", html.escape(report or "Žiadne logy."))
    page = page.replace("{generated}", html.escape(datetime.datetime.now().strftime("%d. %m. %Y %H:%M")))
    return Response(page, 200, {"Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store"})


ADMIN_PAGE = """<!doctype html>
<html lang="sk"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex"><meta name="color-scheme" content="light dark"><title>Klimabot · prehľad</title>
<style>
:root { --bg:#f4f6fa; --surface:#fff; --border:#e2e8f0; --text:#0f172a; --muted:#64748b; }
@media (prefers-color-scheme: dark) { :root { --bg:#0b1220; --surface:#111a2b; --border:#1e293b; --text:#e2e8f0; --muted:#8696ab; } }
body { margin:0; background:var(--bg); color:var(--text); font:14px/1.5 ui-sans-serif, system-ui, "Segoe UI", Roboto, sans-serif; }
main { max-width:1200px; margin:0 auto; padding:24px clamp(12px, 3vw, 32px); }
h1 { font-size:20px; margin:0 0 4px; letter-spacing:-0.01em; } p.sub { margin:0 0 20px; color:var(--muted); }
.cards { display:grid; grid-template-columns:repeat(auto-fit, minmax(200px, 1fr)); gap:12px; margin-bottom:20px; }
.card { background:var(--surface); border:1px solid var(--border); border-radius:14px; padding:14px 16px; }
.card .k { font-size:12.5px; color:var(--muted); } .card .v { font-size:22px; font-weight:700; margin:2px 0; }
.card .s { font-size:12.5px; color:var(--muted); }
pre { background:var(--surface); border:1px solid var(--border); border-radius:14px; padding:16px; overflow:auto;
      font:12.5px/1.5 ui-monospace, SFMono-Regular, Consolas, monospace; }
</style></head><body><main>
<h1>Klimabot · prehľad</h1><p class="sub">Vygenerované {generated} z logov konverzácií (cost_report.py).</p>
<div class="cards">{cards}</div>
<pre>{report}</pre>
</main></body></html>
"""


@app.post("/api/chat")
def chat():
    """SSE stream of bot events for one user turn.

    Request body: {"message": "..."}; header X-Session-Id from /api/session.
    Response: text/event-stream with events: notice, token, tool_call, tool_result,
              state, handoff, turn_complete, done, error.
    """
    data = request.get_json(force=True, silent=True)
    user_input = str(data.get("message") or "").strip() if isinstance(data, dict) else ""
    if not user_input:
        return ("Missing 'message'", 400)
    v = _current_visitor()
    if not v:
        return _error(409, EXPIRED)
    if MAX_MESSAGE_CHARS and len(user_input) > MAX_MESSAGE_CHARS:
        return _error(413, f"Správa je príliš dlhá (max {MAX_MESSAGE_CHARS} znakov).")
    if MAX_TURNS_PER_SESSION and v.turns >= MAX_TURNS_PER_SESSION:
        _rejected("turns_per_session")
        return _error(429, f"Táto ukážková konverzácia dosiahla limit správ. Začnite prosím novú "
                           f"(tlačidlo Reset), alebo nám napíšte na {bot.COMPANY_CONTACT}.")
    if _rate_limited("message", MESSAGES_PER_IP_PER_MINUTE, 60):
        _rejected("messages_per_minute")
        return _error(429, "Posielate správy príliš rýchlo. Skúste to o minútu.")

    # Claim what the turn needs, in order; on a refusal give back what was claimed.
    key = _client_key()
    claimed = []

    def give_back():
        while claimed:
            claimed.pop()()

    if not v.lock.acquire(blocking=False):
        return _error(429, "Počkajte, kým bot dokončí predchádzajúcu odpoveď.")
    claimed.append(v.lock.release)
    with _registry_lock:
        busy = bool(TURNS_IN_FLIGHT_PER_IP) and _in_flight[key] >= TURNS_IN_FLIGHT_PER_IP
        if not busy:
            _in_flight[key] += 1
    if busy:
        give_back()
        _rejected("turns_in_flight")
        return _error(429, "Z vašej siete už bežia iné odpovede. Chvíľu počkajte.")
    claimed.append(lambda: _dec_in_flight(key))
    if _turn_slots is not None:
        if not _turn_slots.acquire(blocking=False):
            give_back()
            _rejected("server_busy")
            return _error(503, "Bot je práve vyťažený. Skúste to prosím o chvíľu.")
        claimed.append(_turn_slots.release)

    sess = v.session
    # Reserve the most this turn may cost (bot.py checks the same caps before every model
    # call). A conversation already at its cap costs nothing: bot.py answers it from code.
    reserve = min(bot.TURN_USD_CAP, max(bot.SESSION_USD_CAP - sess.cost_usd, 0.0))
    reason, net = _reserve(key, reserve)
    if reason:
        give_back()
        _rejected("daily_budget" if reason == "daily" else "ip_daily_budget")
        if reason == "daily":
            return _error(503, f"Demo dnes dosiahlo denný limit. Skúste to prosím zajtra. {CONTACT_HINT}")
        return _error(429, f"Z vašej siete sme dnes vyčerpali limit ukážky. Skúste to prosím zajtra. {CONTACT_HINT}")

    v.turns += 1
    sess.network = net  # today's salted network hash: bot.py caps lead mails per network
    usd_before = sess.cost_usd
    settled = []

    def settle_once():
        if not settled:
            settled.append(True)
            _settle(net, reserve, sess.cost_usd - usd_before)

    def stream():
        bot.use_session(sess)  # the generator runs in this request's thread
        history_len = len(sess.conversation)
        transcript_len = len(v.transcript)
        v.transcript.append(("user", {"text": user_input}))
        finished = False
        try:
            for event_name, payload in bot.run_user_turn_streaming(user_input):
                if event_name in TRANSCRIPT_EVENTS:
                    v.transcript.append((event_name, payload))
                yield _sse(event_name, payload)
            finished = True
            if len(v.transcript) > MAX_TRANSCRIPT_EVENTS:
                del v.transcript[:len(v.transcript) - MAX_TRANSCRIPT_EVENTS]
        except Exception:
            log.exception("turn failed")
            # Generic text: an exception message can carry API or file-system details.
            yield _sse("error", {"message": f"Nastala chyba servera. Skúste to prosím znova. {CONTACT_HINT}"})
        finally:
            # A turn cut short (client disconnected / crash) can leave a tool_use
            # without its tool_result, which the API rejects on the next turn.
            if not finished:
                del sess.conversation[history_len:]
                del v.transcript[transcript_len:]
            settle_once()

    resp = Response(stream(), mimetype="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",  # disable nginx/proxy buffering if anyone puts one in front
    })

    def on_close():
        # Runs even if the client disconnects before the stream starts (when the
        # generator's finally never would), so nothing stays locked or reserved.
        settle_once()
        give_back()

    resp.call_on_close(on_close)
    return resp


def _dec_in_flight(key):
    with _registry_lock:
        _in_flight[key] -= 1
        if _in_flight[key] <= 0:
            del _in_flight[key]


# The page loads nothing from other sites (marked and DOMPurify are pinned local copies) and
# talks only to this server, so the policy can say so. Inline <script>/<style> are allowed because
# the UI is one file; framing stays allowed for a Hugging Face Space iframe.
CONTENT_SECURITY_POLICY = (
    "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; form-action 'self'"
)


@app.after_request
def _security_headers(resp):
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    if resp.mimetype == "text/html":
        resp.headers.setdefault("Content-Security-Policy", CONTENT_SECURITY_POLICY)
    return resp


@app.errorhandler(413)
def _too_large(_e):
    return _error(413, "Požiadavka je príliš veľká.")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sse(event: str, data) -> str:
    """Format a single SSE event with a named event and JSON-encoded data.
    Each event ends with a blank line; multi-line data is split across `data:` lines."""
    payload = json.dumps(data, ensure_ascii=False)
    # JSON doesn't contain raw newlines after encoding (escaped), so one data: line is safe.
    return f"event: {event}\ndata: {payload}\n\n"


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "5000"))
    print("\n=== Samuel Malíšek Klimabot — web ===")
    print(f"  KB chunks: {len(bot.KB)}")
    print(f"  Product index: {len(bot.PRODUCT_BY_CODE)} model codes")
    print(f"  Memory rules: {len(list((bot.KNOWLEDGE_DIR / 'rules').glob('feedback_*.md')))}")
    print(f"  Demo limits: {'ON' if DEMO else 'OFF (KLIMABOT_DEMO=0)'}")
    print(f"  Budgets: ${bot.SESSION_USD_CAP:.2f}/conversation, ${bot.TURN_USD_CAP:.2f}/message, "
          f"${IP_DAILY_USD:.2f}/network/day, ${DAILY_USD_BUDGET:.2f}/day (0 = unlimited)")
    print(f"  Lead e-mail to PM: {', '.join(bot.LEAD_MAIL_TO) + ' (when a conversation ends)' if bot.LEAD_MAIL_ENABLED else 'off (set SMTP_HOST and LEAD_MAIL_TO)'}")
    print(f"  URL: http://{host}:{port}")
    print()
    threading.Thread(target=_sweep_forever, name="idle-sweep", daemon=True).start()
    # On shutdown (Ctrl+C, or SIGTERM from a hosting platform) end the open conversations,
    # so their leads still reach the PM.
    atexit.register(_end_all_visitors)
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    # threaded=True so SSE doesn't block other visitors; MAX_CONCURRENT_TURNS bounds the
    # work. debug=False because the reloader would re-run the KB embedding pipeline.
    app.run(host=host, port=port, threaded=True, debug=False)
