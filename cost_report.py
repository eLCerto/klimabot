"""Token usage, cost, conversation analytics, and GDPR compliance audit
across `logs/*.jsonl`.

Usage:
  python cost_report.py                          # print to stdout only
  python cost_report.py --output                 # save to data/reports/cost_report_<YYYY-MM-DD>.txt
  python cost_report.py --output data/reports/x.txt   # save to specific path
  python cost_report.py -o                       # short form of --output (default path)
  python cost_report.py data/logs/2026-05-13*.jsonl   # restrict to specific logs
  python cost_report.py data/logs/*.jsonl -o          # combine: subset + auto-save

Sections:
  - Per-session table (cost, tokens, turns, msgs, ?, duration, leads, gdpr)
  - TOTAL row
  - Conversion funnel (sessions → discovery → GDPR asked → lead captured)
  - GDPR / ÚOOÚ compliance audit (flags leads captured without verifiable consent)
  - Lead quality (regenerations, total leads)
  - Daily rollup
  - Tool call distribution
  - Safety / errors (jailbreak attempts, API errors, token cap hits)
  - Averages (words per message, questions per session, $/lead)

Requires the bot to log `assistant_reply` events (added 2026-05-13). Logs without
them are flagged as 'transcript unavailable' rather than 'GDPR violation' so the
report doesn't false-positive on pre-logging sessions.
"""
import argparse
import io
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# The bot writes its logs under KLIMABOT_DATA_DIR (data/ by default; /data in Docker).
BOT_DIR = Path(__file__).parent
load_dotenv(BOT_DIR / ".env")
DATA_DIR = BOT_DIR / (os.getenv("KLIMABOT_DATA_DIR", "").strip() or "data")

# USD per 1M tokens, from the same file bot.py's spend caps use.
MODEL = "claude-haiku-4-5-20251001"
_PRICES = json.loads((Path(__file__).resolve().parent / "config" / "model_prices.json").read_text(encoding="utf-8"))[MODEL]
PRICE_INPUT = _PRICES["input"]
PRICE_OUTPUT = _PRICES["output"]
PRICE_CACHE_WRITE = _PRICES["cache_write_5m"]
PRICE_CACHE_READ = _PRICES["cache_read"]

# GDPR audit vocabulary — the same file bot.py uses, so audit and live guard can't drift.
# A lead is compliant only if: the canonical SALES question appeared in an assistant_reply,
# the customer's very next message said an explicit yes (and no refusal), and only then
# lead_captured. See knowledge/rules/feedback_handoff_zapis_z_rozhovoru.md Section 3.
_PHRASES = json.loads((Path(__file__).resolve().parent / "config" / "consent_phrases.json").read_text(encoding="utf-8"))
# Every wording the audit recognises, current and previous (older logs keep passing).
CONSENT_QUESTIONS = {purpose: [q["sk"]] for purpose, q in _PHRASES["questions"].items()}
for _purpose, _old in _PHRASES.get("previous_questions", {}).items():
    if not _purpose.startswith("_"):
        CONSENT_QUESTIONS.setdefault(_purpose, []).extend(_old)
CONSENT_YES_RE = re.compile(_PHRASES["yes_re"], re.IGNORECASE)
CONSENT_YES_NOT_CONSENT_RE = re.compile(_PHRASES["yes_not_consent_re"], re.IGNORECASE)
CONSENT_NO_RE = re.compile(_PHRASES["no_re"], re.IGNORECASE)
CONSENT_NO_NOT_REFUSAL_RE = re.compile(_PHRASES["no_not_refusal_re"], re.IGNORECASE)  # "nesúhlasím s cenou"
CONSENT_NO_IN_WINDOW_RE = re.compile(_PHRASES["no_in_window_re"], re.IGNORECASE)


def consent_answer(text):
    """'yes', 'no' or None for the customer's message right after the question."""
    if CONSENT_NO_RE.search(CONSENT_NO_NOT_REFUSAL_RE.sub(" ", text)) or CONSENT_NO_IN_WINDOW_RE.search(text):
        return "no"
    return "yes" if CONSENT_YES_RE.search(CONSENT_YES_NOT_CONSENT_RE.sub(" ", text)) else None


def cost(input_tok, output_tok, cache_write, cache_read):
    return (
        input_tok * PRICE_INPUT
        + output_tok * PRICE_OUTPUT
        + cache_write * PRICE_CACHE_WRITE
        + cache_read * PRICE_CACHE_READ
    ) / 1_000_000


def word_count(text):
    return len((text or "").split())


def parse_ts(ts):
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts)
    except ValueError:
        return None


def fmt_min(m):
    if m is None:
        return "—"
    return f"{m:.1f}m"


def summarize(path):
    s = {
        "name": path.name,
        "started": None, "ended": None,
        "first_user_ts": None, "last_event_ts": None,
        "in": 0, "out": 0, "cw": 0, "cr": 0,
        "turns": 0,
        "user_msgs": 0, "user_words": 0,
        "bot_replies": 0, "bot_words": 0, "bot_questions": 0,
        "tools": Counter(),
        "leads": 0,
        "lead_captured_ts": [],
        "auto_leads": 0,                       # workflow safety net captures
        "handoff_regenerated": 0,
        "jailbreak": 0,
        "api_errors": 0,
        # Validator + sanitization analytics — populated from bot_reply_violations
        # / bot_reply_regen_triggered / bot_reply_sanitized events.
        "violations": Counter(),               # rule_name → count
        "regens": 0,                           # bot_reply_regen_triggered events
        "sanitizations": 0,                    # bot_reply_sanitized events
        # Drop-off analysis — last user message before session went silent
        # (useful for spotting where conversations die).
        "last_user_text": "",
        "last_user_turn_idx": 0,
        "gdpr_blocks": 0,                      # capture_lead_blocked_gdpr
        "limits": Counter(),                   # limit_hit events: limit name -> count
        "api_retries": 0,
        "mail_failed": 0,                      # lead e-mails to the PM that couldn't be sent
        "feedback": Counter(),                 # reply_feedback: up / down
        "feedback_down": [],                   # excerpts of the replies rated down
        "gdpr_question_asked": False,
        "gdpr_question_ts": None,
        # Consent audit, by event order (timestamps have 1 s resolution):
        "asked_purpose": None,                 # purpose of the question in the latest bot turn
        "consent_purpose": None,               # set by an explicit yes right after the question
        "consent_refused": False,
        "lead_before_consent": False,
        "lead_without_sales_consent": False,
    }
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        ev = r.get("event")
        ts = r.get("ts")
        if ts:
            s["last_event_ts"] = ts

        if ev == "session_start":
            s["started"] = ts
        elif ev == "session_end":
            s["ended"] = ts
        elif ev == "user_input":
            s["user_msgs"] += 1
            user_txt = r.get("text", "") or ""
            s["user_words"] += word_count(user_txt)
            s["last_user_text"] = user_txt
            s["last_user_turn_idx"] = s["user_msgs"]
            if s["first_user_ts"] is None:
                s["first_user_ts"] = ts
            # Only the message right after the question can answer it.
            if s["asked_purpose"] and s["consent_purpose"] is None:
                answer = consent_answer(user_txt)
                if answer == "yes":
                    s["consent_purpose"] = s["asked_purpose"]
                elif answer == "no":
                    s["consent_refused"] = True
            s["asked_purpose"] = None
        elif ev == "assistant_reply":
            text = r.get("text", "") or ""
            s["bot_replies"] += 1
            s["bot_words"] += word_count(text)
            s["bot_questions"] += text.count("?")
            asked = next((p for p, qs in CONSENT_QUESTIONS.items() if any(q in text for q in qs)), None)
            if asked:
                s["asked_purpose"] = asked
                s["gdpr_question_asked"] = True
                if s["gdpr_question_ts"] is None:
                    s["gdpr_question_ts"] = ts
        elif ev == "llm_turn":
            s["turns"] += 1
            s["in"] += r.get("input_tokens", 0) or 0
            s["out"] += r.get("output_tokens", 0) or 0
            s["cw"] += r.get("cache_write", 0) or 0
            s["cr"] += r.get("cache_read", 0) or 0
        elif ev == "tool_call":
            s["tools"][r.get("name", "?")] += 1
        elif ev == "lead_captured":
            s["leads"] += 1
            s["lead_captured_ts"].append(ts)
            if s["consent_purpose"] is None:
                s["lead_before_consent"] = True
            elif s["consent_purpose"] != "sales":
                s["lead_without_sales_consent"] = True
        elif ev == "auto_lead_capture_triggered":
            s["auto_leads"] += 1
        elif ev == "handoff_regenerated":
            s["handoff_regenerated"] += 1
        elif ev == "bot_reply_violations":
            for v in r.get("violations", []) or []:
                rule = v.split(":", 1)[0].strip() if isinstance(v, str) else "?"
                s["violations"][rule] += 1
        elif ev == "bot_reply_regen_triggered":
            s["regens"] += 1
            for v in r.get("violations", []) or []:
                rule = v.split(":", 1)[0].strip() if isinstance(v, str) else "?"
                s["violations"][rule] += 1
        elif ev == "bot_reply_sanitized":
            s["sanitizations"] += 1
        elif ev == "capture_lead_blocked_gdpr":
            s["gdpr_blocks"] += 1
        elif ev == "jailbreak_suspected":
            s["jailbreak"] += 1
        elif ev == "api_error":
            s["api_errors"] += 1
        elif ev == "limit_hit":
            s["limits"][r.get("limit", "?")] += 1
        elif ev == "lead_mail_failed":
            s["mail_failed"] += 1
        elif ev == "api_retry":
            s["api_retries"] += 1
        elif ev == "reply_feedback":
            s["feedback"][r.get("rating", "?")] += 1
            if r.get("rating") == "down":
                s["feedback_down"].append((r.get("reply_excerpt") or "")[:160])

    # Derived
    s["cost_usd"] = cost(s["in"], s["out"], s["cw"], s["cr"])
    s["cache_hit_pct"] = 100 * s["cr"] / max(1, s["cr"] + s["cw"] + s["in"])
    start = parse_ts(s["started"] or s["first_user_ts"])
    end = parse_ts(s["ended"] or s["last_event_ts"])
    s["duration_min"] = (end - start).total_seconds() / 60 if (start and end) else None
    s["transcript_logged"] = s["bot_replies"] > 0

    # GDPR audit per session (question < explicit yes < lead, sales purpose):
    #   - no leads → not applicable
    #   - leads + no transcript → "unverifiable" (pre-logging era)
    #   - a lead before the yes, or with support-only consent → VIOLATION
    #   - otherwise OK
    s["gdpr_status"] = "n/a"
    if s["leads"] > 0:
        if not s["transcript_logged"]:
            s["gdpr_status"] = "unverifiable"
        elif s["lead_before_consent"] or s["lead_without_sales_consent"]:
            s["gdpr_status"] = "violation"
        else:
            s["gdpr_status"] = "ok"
    return s


def print_per_session(rows):
    print()
    print("=== Per-session summary ===")
    hdr = (
        f"{'session':<30} {'turns':>5} {'user':>4} {'bot':>4} {'?':>3} "
        f"{'in':>7} {'out':>6} {'cache_w':>8} {'cache_r':>8} {'hit%':>5} "
        f"{'$':>7} {'lead':>4} {'gdpr':>11} {'dur':>6}"
    )
    print(hdr)
    print("-" * len(hdr))
    totals = defaultdict(int)
    totals["cost"] = 0.0
    totals["dur"] = 0.0
    totals["dur_n"] = 0
    for p, s in rows:
        print(
            f"{p.name:<30} {s['turns']:>5} {s['user_msgs']:>4} {s['bot_replies']:>4} "
            f"{s['bot_questions']:>3} {s['in']:>7} {s['out']:>6} {s['cw']:>8} {s['cr']:>8} "
            f"{s['cache_hit_pct']:>4.1f}% ${s['cost_usd']:>6.4f} {s['leads']:>4} "
            f"{s['gdpr_status']:>11} {fmt_min(s['duration_min']):>6}"
        )
        for k in ("in", "out", "cw", "cr", "turns", "user_msgs", "bot_replies",
                  "user_words", "bot_words", "bot_questions", "leads"):
            totals[k] += s[k]
        totals["cost"] += s["cost_usd"]
        if s["duration_min"]:
            totals["dur"] += s["duration_min"]
            totals["dur_n"] += 1
    print("-" * len(hdr))
    hit = 100 * totals["cr"] / max(1, totals["cr"] + totals["cw"] + totals["in"])
    avg_dur = totals["dur"] / totals["dur_n"] if totals["dur_n"] else None
    print(
        f"{'TOTAL':<30} {totals['turns']:>5} {totals['user_msgs']:>4} {totals['bot_replies']:>4} "
        f"{totals['bot_questions']:>3} {totals['in']:>7} {totals['out']:>6} {totals['cw']:>8} {totals['cr']:>8} "
        f"{hit:>4.1f}% ${totals['cost']:>6.4f} {totals['leads']:>4} {'':>11} {fmt_min(avg_dur):>6}"
    )
    return totals


def print_funnel(rows):
    n = len(rows)
    n_discovery = sum(1 for _, s in rows if s["user_msgs"] >= 3)
    n_gdpr = sum(1 for _, s in rows if s["gdpr_question_asked"])
    n_lead = sum(1 for _, s in rows if s["leads"] > 0)
    print()
    print("=== Conversion funnel ===")
    print(f"  Sessions total:            {n}")
    pct = lambda v: f"({100*v/max(1,n):.0f}%)"
    print(f"  With discovery (≥3 msgs):  {n_discovery}  {pct(n_discovery)}")
    print(f"  GDPR question asked:       {n_gdpr}  {pct(n_gdpr)}")
    print(f"  Lead captured:             {n_lead}  {pct(n_lead)}")
    if n_discovery:
        print(f"  Discovery → Lead rate:     {100*n_lead/n_discovery:.0f}%")
    if n_gdpr:
        print(f"  GDPR asked → Lead rate:    {100*n_lead/n_gdpr:.0f}%")


def print_gdpr_audit(rows):
    violations = [(p, s) for p, s in rows if s["gdpr_status"] == "violation"]
    unverif = [(p, s) for p, s in rows if s["gdpr_status"] == "unverifiable"]
    ok = [(p, s) for p, s in rows if s["gdpr_status"] == "ok"]
    print()
    print("=== GDPR / ÚOOÚ compliance audit ===")
    print(f"  ✓ OK (consent recorded before lead):  {len(ok)}")
    print(f"  ⚠ Unverifiable (no transcript log):   {len(unverif)}")
    print(f"  ✗ Violations (lead w/o GDPR):         {len(violations)}")
    if violations:
        print()
        print("  Violation sessions — investigate:")
        for p, s in violations:
            print(f"    - {p.name}: leads={s['leads']}, bot_replies={s['bot_replies']}, "
                  f"question_seen={s['gdpr_question_asked']} consent={s['consent_purpose']} "
                  f"before_consent={s['lead_before_consent']} support_only={s['lead_without_sales_consent']}")
    if unverif:
        print()
        print("  Unverifiable sessions (predate assistant_reply logging — 2026-05-13):")
        for p, s in unverif[:10]:
            print(f"    - {p.name}: leads={s['leads']} (no assistant_reply events)")
        if len(unverif) > 10:
            print(f"    ... and {len(unverif)-10} more")


def print_lead_quality(rows):
    n_leads = sum(s["leads"] for _, s in rows)
    n_regen = sum(s["handoff_regenerated"] for _, s in rows)
    print()
    print("=== Lead quality ===")
    print(f"  Total leads captured:             {n_leads}")
    print(f"  Post-capture handoff regenerated: {n_regen}  (customer corrected info)")


def print_daily_rollup(rows):
    by_date = defaultdict(lambda: {"sessions": 0, "leads": 0, "cost": 0.0, "in": 0, "out": 0})
    for _, s in rows:
        d = (s["started"] or s["first_user_ts"] or "")[:10]
        if not d:
            continue
        v = by_date[d]
        v["sessions"] += 1
        v["leads"] += s["leads"]
        v["cost"] += s["cost_usd"]
        v["in"] += s["in"]
        v["out"] += s["out"]
    if not by_date:
        return
    print()
    print("=== Daily rollup ===")
    print(f"  {'date':<12} {'sess':>5} {'leads':>5} {'in_tok':>9} {'out_tok':>8} {'$ cost':>9}")
    for d in sorted(by_date):
        v = by_date[d]
        print(f"  {d:<12} {v['sessions']:>5} {v['leads']:>5} {v['in']:>9} {v['out']:>8} ${v['cost']:>8.4f}")


def print_tool_calls(rows):
    breakdown = Counter()
    for _, s in rows:
        breakdown.update(s["tools"])
    if not breakdown:
        return
    total = sum(breakdown.values())
    print()
    print("=== Tool calls ===")
    for name, n in breakdown.most_common():
        print(f"  {name:<26} {n:>5}  ({100*n/total:.1f}%)")


def print_validator_triggers(rows):
    """Aggregate bot_reply_violations + bot_reply_regen_triggered counts by
    rule name. Useful for seeing which rule the bot drifts on most often —
    that's where rule text or guardrail logic should be tightened next."""
    totals = Counter()
    total_regens = 0
    total_sanitized = 0
    for _, s in rows:
        totals.update(s["violations"])
        total_regens += s["regens"]
        total_sanitized += s["sanitizations"]
    if not (totals or total_regens or total_sanitized):
        return
    print()
    print("=== Validator triggers (rule drift signal) ===")
    print(f"  Sessions analyzed:        {len(rows)}")
    print(f"  Total regens fired:       {total_regens}")
    print(f"  Total sanitizations:      {total_sanitized}  (auto-fixes, no regen)")
    if totals:
        print()
        print("  Top violations by rule:")
        for rule, n in totals.most_common(10):
            avg_per_session = n / max(1, len(rows))
            print(f"    {rule:<32} {n:>5}  ({avg_per_session:.2f}/session)")


def print_drop_off(rows):
    """For sessions that did NOT capture a lead, group the last user
    message by 'where it died'. Helps spot patterns: e.g. 'most leads die
    after bot asks for color' → fix the color question."""
    lost = [(p, s) for p, s in rows if s["leads"] == 0 and s["user_msgs"] > 0]
    if not lost:
        return
    print()
    print(f"=== Drop-off analysis ({len(lost)} sessions ended without lead) ===")
    # Bucket by last-message turn index — quick view of when conversations
    # typically die (1st msg = bounce; 5+ = late drop-off, more painful).
    buckets = Counter()
    for _, s in lost:
        idx = s["last_user_turn_idx"]
        bucket = "1 (immediate bounce)" if idx == 1 else \
                 "2-3 (early)" if idx <= 3 else \
                 "4-6 (mid)" if idx <= 6 else \
                 "7+ (late — most painful)"
        buckets[bucket] += 1
    print("  Drop-off by user-turn index:")
    for bucket, n in buckets.most_common():
        print(f"    {bucket:<32} {n:>4}  ({100*n/len(lost):.0f}%)")
    # Show sample last-user messages from late drop-offs — those are the
    # leads most worth saving.
    late = sorted(
        [(p, s) for p, s in lost if s["last_user_turn_idx"] >= 4],
        key=lambda x: -x[1]["last_user_turn_idx"],
    )[:5]
    if late:
        print()
        print("  Sample late drop-off messages (last user text before silence):")
        for p, s in late:
            txt = s["last_user_text"][:80].replace("\n", " ")
            print(f"    [{p.name} @ turn {s['last_user_turn_idx']}] {txt!r}")


def print_auto_capture_stats(rows):
    """Auto-capture is the workflow safety net. If many leads come from it,
    the bot is consistently failing to close — fix the prompts. If few,
    safety net is rarely needed (= bot is doing the right thing on its own)."""
    n_auto = sum(s["auto_leads"] for _, s in rows)
    n_blocks = sum(s["gdpr_blocks"] for _, s in rows)
    n_leads = sum(s["leads"] for _, s in rows)
    if not (n_auto or n_blocks):
        return
    print()
    print("=== Auto-capture safety net + GDPR guard ===")
    print(f"  Leads via safety net:        {n_auto}  "
          f"({100*n_auto/max(1,n_leads):.0f}% of all leads)")
    print(f"  capture_lead blocked by GDPR: {n_blocks}  "
          "(bot tried but guard rejected — bot must ask canonical phrase first)")


def print_safety(rows):
    n_jb = sum(s["jailbreak"] for _, s in rows)
    n_api = sum(s["api_errors"] for _, s in rows)
    limits = sum((s["limits"] for _, s in rows), Counter())
    n_retry = sum(s["api_retries"] for _, s in rows)
    n_mail = sum(s["mail_failed"] for _, s in rows)
    if not any((n_jb, n_api, limits, n_retry, n_mail)):
        return
    print()
    print("=== Safety / errors ===")
    if n_jb:
        print(f"  Jailbreak attempts:   {n_jb}")
    if n_api:
        print(f"  API errors:           {n_api}")
    if n_mail:
        print(f"  Lead e-mails failed: {n_mail}  (the brief is in handoff_records/; forward it by hand)")
    if n_retry:
        print(f"  API retries:          {n_retry}")
    for name, n in limits.most_common():
        print(f"  Limit hit ({name}): {n}")


def print_feedback(rows):
    votes = sum((s["feedback"] for _, s in rows), Counter())
    if not votes:
        return
    print()
    print("=== Reply feedback (thumbs in the web chat) ===")
    print(f"  Helpful: {votes['up']}   Not helpful: {votes['down']}")
    for name, s in rows:
        for excerpt in s["feedback_down"]:
            print(f"  - not helpful, {name.name}: {excerpt}")


def print_averages(rows, totals):
    if not rows:
        return
    n = len(rows)
    avg_user_w = totals["user_words"] / max(1, totals["user_msgs"])
    avg_bot_w = totals["bot_words"] / max(1, totals["bot_replies"])
    avg_q = totals["bot_questions"] / max(1, n)
    avg_turns = totals["turns"] / max(1, n)
    avg_user_msgs = totals["user_msgs"] / max(1, n)
    print()
    print("=== Averages (per session) ===")
    print(f"  User messages:                {avg_user_msgs:.1f}")
    print(f"  LLM turns:                    {avg_turns:.1f}")
    print(f"  Bot questions ('?' count):    {avg_q:.1f}")
    print(f"  Avg user words / message:     {avg_user_w:.1f}")
    print(f"  Avg bot words / reply:        {avg_bot_w:.1f}")
    if totals["leads"]:
        print(f"  Avg $ per lead:               ${totals['cost']/totals['leads']:.4f}")


def render_report(rows):
    """Run all sections and return the rendered text."""
    buf = io.StringIO()
    real_stdout = sys.stdout
    try:
        sys.stdout = buf
        totals = print_per_session(rows)
        print_funnel(rows)
        print_validator_triggers(rows)
        print_drop_off(rows)
        print_auto_capture_stats(rows)
        print_gdpr_audit(rows)
        print_lead_quality(rows)
        print_daily_rollup(rows)
        print_tool_calls(rows)
        print_safety(rows)
        print_feedback(rows)
        print_averages(rows, totals)
    finally:
        sys.stdout = real_stdout
    return buf.getvalue()


def main(paths, output_arg):
    rows = [(p, summarize(p)) for p in paths]
    report = render_report(rows)

    # Always print to stdout so the user sees feedback immediately.
    sys.stdout.write(report)

    # Optionally also save to file.
    if output_arg is None:
        return  # stdout only
    save_path = resolve_output_path(output_arg)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    save_path.write_text(report, encoding="utf-8")
    sys.stderr.write(f"\n[Saved to {save_path}]\n")


def resolve_output_path(output_arg):
    """Resolve --output value to a concrete Path.

    - '__default__' (flag used without a value) → reports/cost_report_<YYYY-MM-DD>.txt
    - explicit path → use that path verbatim
    """
    if output_arg == "__default__":
        date = datetime.now().strftime("%Y-%m-%d")
        return DATA_DIR / "reports" / f"cost_report_{date}.txt"
    return Path(output_arg)


def parse_args(argv):
    parser = argparse.ArgumentParser(
        prog="cost_report.py",
        description=(
            "Summarize token usage, cost, conversation analytics, and GDPR "
            "compliance from Samuel Malíšek Klimabot logs."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  cost_report.py                    # all logs, stdout only\n"
            "  cost_report.py -o                 # save to data/reports/cost_report_<YYYY-MM-DD>.txt\n"
            "  cost_report.py -o data/reports/x.txt   # save to specific path\n"
            "  cost_report.py data/logs/2026-05-13*.jsonl -o   # combine\n"
        ),
    )
    parser.add_argument(
        "logs",
        nargs="*",
        help="Log files to analyze (default: samuel-malisek-klimabot-selling-bot/logs/*.jsonl)",
    )
    parser.add_argument(
        "-o", "--output",
        nargs="?",
        const="__default__",  # used when flag is given without a value
        default=None,
        metavar="PATH",
        help=(
            "Save the rendered report to PATH (and also print to stdout). "
            "If used without a value, defaults to "
            "reports/cost_report_<YYYY-MM-DD>.txt"
        ),
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    if args.logs:
        paths = [Path(a) for a in args.logs]
    else:
        paths = sorted((DATA_DIR / "logs").glob("*.jsonl"))
    if not paths:
        sys.stderr.write("No logs found.\n")
        sys.exit(1)
    main(paths, args.output)
