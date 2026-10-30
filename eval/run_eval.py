"""Run the scripted customer conversations in eval/conversations.json through bot.py,
with the model served by the local Claude Code CLI (subscription login, no API key) or,
with --api, by the real Anthropic API (the key from .env; this costs money).

Usage (from the repo, inside .venv):
    python eval/run_eval.py                 # all conversations, 4 in parallel
    python eval/run_eval.py --only c01 c13  # a subset (id prefixes)
    python eval/run_eval.py --workers 2
    python eval/run_eval.py --scenarios "scenarios/round2_*.json"   # the agents' round-2 scenarios
    python eval/run_eval.py --api --budget-usd 10 --scenarios "scenarios/round2_*.json" scenarios/abuse.json

--api keeps the production spend caps ($0.50 per conversation, $0.40 per message), so a
run costs at most about $0.50 per conversation; --budget-usd stops starting conversations
once what is spent plus a full conversation for each one running would pass the budget.

Everything the bot writes (logs, sessions, leads.jsonl, handoff_records/) goes to
eval/runs/<timestamp>/ instead of the repo root. Then run eval/analyze.py on that dir.
"""
import argparse
import datetime
import json
import os
import sys
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

EVAL_DIR = Path(__file__).resolve().parent
REPO = EVAL_DIR.parent
# Decided before `import bot`, which reads the key and the caps at import.
API_MODE = "--api" in sys.argv
if not API_MODE:
    os.environ.setdefault("ANTHROPIC_API_KEY", "unused-claude-cli")  # bot.py refuses to start without one
    # The CLI's usage figures carry its own prompt overhead, so the spend caps would cut
    # scripted conversations short. The CLI eval measures behaviour; --api measures the caps too.
    os.environ.setdefault("KLIMABOT_SESSION_USD_CAP", "50")
    os.environ.setdefault("KLIMABOT_TURN_USD_CAP", "10")
os.environ["LEAD_MAIL_TO"] = ""  # scripted leads must never reach the PM's inbox
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(EVAL_DIR))
os.chdir(REPO)

import bot  # noqa: E402
from claude_cli_client import ClaudeCLIClient  # noqa: E402


def redirect_outputs(run_dir):
    for name in ("logs", "sessions", "handoff_records", "conversations"):
        (run_dir / name).mkdir(parents=True, exist_ok=True)
    bot.LOG_DIR = run_dir / "logs"
    bot.SESSIONS_DIR = run_dir / "sessions"
    bot.HANDOFF_RECORDS_DIR = run_dir / "handoff_records"
    bot.LEADS_PATH = run_dir / "leads.jsonl"
    bot.HANDOFF_PATH = run_dir / "handoff_queue.jsonl"


LIMIT_HIT = threading.Event()  # set once the subscription limit is reached: stop all conversations
_budget = {"limit": None, "committed": 0.0, "spent": 0.0}  # --budget-usd (API mode)
_budget_lock = threading.Lock()


def _reserve_conversation():
    """Reserve a full conversation's cap against --budget-usd. False when it doesn't fit."""
    with _budget_lock:
        if _budget["limit"] is not None and _budget["committed"] + bot.SESSION_USD_CAP > _budget["limit"]:
            return False
        _budget["committed"] += bot.SESSION_USD_CAP
        return True


def _settle_conversation(spent):
    with _budget_lock:
        _budget["committed"] += spent - bot.SESSION_USD_CAP
        _budget["spent"] += spent


def run_conversation(conv, run_dir):
    if LIMIT_HIT.is_set():
        raise RuntimeError("skipped — subscription limit reached")
    if not _reserve_conversation():
        raise RuntimeError(f"skipped — --budget-usd {_budget['limit']} would be exceeded")
    sess = bot.Session()
    try:
        return _run_conversation(conv, run_dir, sess)
    finally:
        _settle_conversation(sess.cost_usd)


def _run_conversation(conv, run_dir, sess):
    bot.use_session(sess)
    started = time.time()
    turns = []
    for message in conv["messages"]:
        if LIMIT_HIT.is_set():
            raise RuntimeError("stopped — subscription limit reached (conversation incomplete, not saved)")
        t0 = time.time()
        turn = {"user": message, "assistant": [], "tools": [], "notices": [], "errors": [], "handoff": None}
        try:
            for event, data in bot.run_user_turn_streaming(message):
                if event == "token":
                    turn["assistant"].append(data["text"])
                elif event == "tool_call":
                    turn["tools"].append({"name": data["name"], "input": data["input"]})
                elif event == "tool_result":
                    pending = [t for t in turn["tools"] if t["name"] == data["name"] and "is_error" not in t]
                    if pending:
                        pending[-1].update(is_error=data["is_error"], output_preview=data["output_preview"])
                elif event == "notice":
                    turn["notices"].append(data["text"])
                elif event == "error":
                    turn["errors"].append(data["message"])
                elif event == "handoff":
                    turn["handoff"] = data["path"]
        except Exception as e:  # keep going: one broken turn shouldn't lose the conversation
            turn["errors"].append(f"{type(e).__name__}: {e}\n{traceback.format_exc()}")
        turn["seconds"] = round(time.time() - t0, 1)
        if bot.breaker_open():  # the API account can't be charged: every reply would be the offline text
            LIMIT_HIT.set()
            raise RuntimeError("API spend limit reached (conversation incomplete, not saved)")
        if not API_MODE and any("limit" in e.lower() for e in turn["errors"]):
            LIMIT_HIT.set()
            raise RuntimeError("subscription limit reached (conversation incomplete, not saved)")
        turns.append(turn)
        print(f"  [{conv['id']}] turn {len(turns)}/{len(conv['messages'])} done ({turn['seconds']} s)", flush=True)

    bot.end_session()  # masks personal data in the log when there was no consent
    handoff_md = sess.handoff_path.read_text(encoding="utf-8") if sess.handoff_path and sess.handoff_path.exists() else None
    record = {
        "id": conv["id"],
        "author": conv.get("author", ""),
        "title": conv["title"],
        "expect": conv["expect"],
        "review": conv.get("review", ""),
        "turns": turns,
        "final_state": dict(sess.customer_state),
        "quotes": sess.quotes,
        "gdpr_question_asked": sess.gdpr_question_asked,
        "consent": sess.consent,
        "consent_refused": sess.consent_refused,
        "handoff_markdown": handoff_md,
        "handoff_path": str(sess.handoff_path) if sess.handoff_path else None,
        "log_file": sess.log_path.name,
        "session_input_tokens": sess.input_tokens,
        "session_usd": round(sess.cost_usd, 6),
        "limit_reached": sess.limit_reached,
        "client": "api" if API_MODE else "claude-cli",
        "seconds": round(time.time() - started, 1),
    }
    (run_dir / "conversations" / f"{conv['id']}.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", nargs="*", help="conversation id prefixes to run")
    parser.add_argument("--workers", type=int, default=4)
    # The production model, not the CLI's "haiku" alias, which moves on with new releases.
    parser.add_argument("--model", default=bot.MODEL, help="CLI model (CLI mode only; default: bot.MODEL)")
    parser.add_argument("--api", action="store_true", help="use the real Anthropic API (costs money)")
    parser.add_argument("--budget-usd", type=float, default=10.0,
                        help="API mode: stop starting conversations past this spend (default 10)")
    parser.add_argument("--run-dir")
    parser.add_argument("--scenarios", nargs="*", default=["conversations.json"],
                        help="scenario files relative to eval/ (e.g. scenarios/round2_*.json)")
    args = parser.parse_args()

    conversations = []
    for pattern in args.scenarios:
        for path in sorted(EVAL_DIR.glob(pattern)):
            conversations += json.loads(path.read_text(encoding="utf-8"))
    if args.only:
        conversations = [c for c in conversations if any(c["id"].startswith(p) for p in args.only)]
    run_dir = Path(args.run_dir) if args.run_dir else EVAL_DIR / "runs" / datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    run_dir = run_dir.resolve()  # bot.py takes paths relative to its absolute BOT_DIR
    redirect_outputs(run_dir)
    if API_MODE:
        key = os.getenv("ANTHROPIC_API_KEY", "")
        if not key.startswith("sk-ant") or key.endswith("...") or len(key) < 40:
            raise SystemExit("--api needs a real ANTHROPIC_API_KEY in .env (not the .env.example placeholder)")
        _budget["limit"] = args.budget_usd  # bot.client is already the real API client
        client_info = (f"Anthropic API, {bot.MODEL}; caps ${bot.SESSION_USD_CAP:.2f}/conversation, "
                       f"${bot.TURN_USD_CAP:.2f}/message; run budget ${args.budget_usd:.2f}")
    else:
        bot.client = ClaudeCLIClient(model=args.model, log_dir=run_dir)
        client_info = f"claude CLI: {bot.client.exe}"
    bot.get_reranker()  # load the lazy reranker once here, not in four threads at once
    print(f"{client_info}\nrun dir: {run_dir}\n{len(conversations)} conversations, {args.workers} workers", flush=True)

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(run_conversation, c, run_dir): c["id"] for c in conversations}
        for future in futures:
            cid = futures[future]
            try:
                rec = future.result()
                print(f"DONE {cid}: {rec['seconds']} s, ${rec['session_usd']:.3f}, "
                      f"lead={'yes' if rec['handoff_markdown'] else 'no'}"
                      + (", hit the conversation cap" if rec["limit_reached"] else ""), flush=True)
            except Exception as e:
                print(f"FAILED {cid}: {e}", flush=True)
    print(f"all done in {round(time.time() - t0)} s, ${_budget['spent']:.2f} → {run_dir}", flush=True)


if __name__ == "__main__":
    main()
