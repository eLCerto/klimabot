"""Direction metrics: the scripted conversations of eval/scenarios/direction.json, several times each, through the
bot of a checkout or a commit — where each reply heads, whether the conversation policy picked the expected move,
whether the reply followed it, whether the conversation ended as scripted — plus regenerations, calls, time, cost.

By default the model runs through the local Claude Code CLI on the subscription (eval/claude_cli_client.py, the
production model ID), not the paid API; --api opts in to the real API with --budget-usd. CLI figures (seconds, USD)
are the CLI's, comparable between commits, not with production.

    python eval/stability.py                      # this checkout: the table, and a run dir under eval/runs/metrics/
    python eval/stability.py --commit HEAD        # a commit, in a temporary worktree; appends to the history
    python eval/stability.py --history            # the metrics of every measured commit (local, gitignored)
    python eval/stability.py --install-hook       # measure every commit: a git post-commit hook, in the background
    python eval/stability.py --compare a.json b.json
"""
import argparse
import fcntl
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
SCENARIOS = HERE / "eval" / "scenarios" / "direction.json"
METRICS_DIR = HERE / "eval" / "runs" / "metrics"  # eval/runs/ is gitignored: the history stays on this machine
HISTORY = METRICS_DIR / "history.jsonl"

# Where a reply heads, per move of the policy (docs/conversation_policy.md). A first question about the space may
# also ask about the rooms; an answer may show a price or ask what matters; a referral gives the company contact.
ALL = {"ponuka", "kontakt", "neponukame", "zisti-priestor", "zisti-izby", "zisti-priority", "odpoved", "odkaz",
       "bezpecnost"}
MOVE_DIRECTIONS = {
    "ponuka": {"ponuka"}, "nova-ponuka": {"ponuka"},
    "zisti-priestor": {"zisti-priestor", "zisti-izby"}, "zisti-izby": {"zisti-izby", "zisti-priestor"},
    "zisti-priority": {"zisti-priority"},
    "kontakt": {"kontakt"}, "neponukame": {"neponukame"},
    "odpoved": {"odpoved", "ponuka", "zisti-priority"}, "pokracuj": ALL,
    "zapis": {"odpoved", "kontakt", "odkaz"}, "po-zapise": ALL,  # the thanks may give the company contact
    "bezpecnost": {"bezpecnost"}, "reklamacia": {"odkaz"},
    "priemysel": {"odkaz", "kontakt", "odpoved"}, "vlastna-montaz": {"odkaz", "odpoved"},
}
_EUR_RE = re.compile(r"\d[\d\s.,]*\s*€|€\s*\d")
_QUESTION_SENTENCES_RE = re.compile(r"[^.!?\n]*\?")
_DECLINE_RE = re.compile(r"neponúk|nepredáv|nezaober|nezahŕň|nerobíme|neposkytuj|nemôžeme|nie je (?:súčasť|predmet|naš)|"
                         r"nemáme (?:\w+ )?(?:informáci|podklad)|v podkladoch (?:som )?(?:to |nič )?(?:nemám|nemáme|nenašiel)|"
                         r"nevieme potvrdiť|neviem potvrdiť|nemôžem (?:vám )?(?:to )?potvrdiť")
_PRIORITY_WORDS_RE = re.compile(r"tich|filtr|wi-?fi|dizajn|najnižš")


def direction(reply, quoted, company_email, asks_contact):
    """Where a reply heads, read by code from its text, whether a quote was made this turn and the bot's own
    contact-request check. A first question about the type of space counts as zisti-priestor even when it also
    asks about the rooms (the directive asks both)."""
    low = reply.lower()
    questions = " ".join(_QUESTION_SENTENCES_RE.findall(low))
    if re.search(r"\b112\b", reply):
        return "bezpecnost"
    if _DECLINE_RE.search(low):
        return "neponukame"
    if asks_contact(reply):
        return "kontakt"
    if quoted and _EUR_RE.search(reply):
        return "ponuka"
    if company_email and company_email.lower() in low and not _EUR_RE.search(reply):
        return "odkaz"
    if re.search(r"ak[ýá] (?:typ )?priestor|typ priestoru|\bbyt, rodinný dom", questions):
        return "zisti-priestor"
    if re.search(r"izb|miestnost", questions):
        return "zisti-izby"
    if re.search(r"dôležit|tich|filtr|wi-?fi|dizajn|najnižš", questions) or (
            questions and len(set(_PRIORITY_WORDS_RE.findall(low))) >= 3):  # the options listed above the question
        return "zisti-priority"
    if re.search(r"m²|m2|ploch", questions):
        return "zisti-priestor"
    return "odpoved"


def load_scenarios(path=SCENARIOS):
    raw = path.read_bytes()
    return json.loads(raw)["conversations"], hashlib.sha1(raw).hexdigest()[:10]


def check_final(final, quotes, consent, lead, replies, company_email):
    """The scripted end of a conversation, checked by code: [] when it ended as it should."""
    def rx(p):
        return p.replace("{COMPANY_EMAIL}", re.escape(company_email or ""))
    failed = []
    if "quotes_min" in final and quotes < final["quotes_min"]:
        failed.append(f"quotes {quotes} < {final['quotes_min']}")
    if "quotes_max" in final and quotes > final["quotes_max"]:
        failed.append(f"quotes {quotes} > {final['quotes_max']}")
    shown = any(_EUR_RE.search(r) for r in replies)
    if "price_shown" in final and shown != final["price_shown"]:
        failed.append(f"price shown: {shown}")
    if "lead" in final and lead != final["lead"]:
        failed.append(f"lead: {lead}")
    if "consent" in final and consent != final["consent"]:
        failed.append(f"consent: {consent}")
    last = replies[-1] if replies else ""
    failed += [f"last reply lacks /{p}/" for p in final.get("last_has", []) if not re.search(rx(p), last, re.I)]
    failed += [f"last reply has /{p}/" for p in final.get("last_lacks", []) if re.search(rx(p), last, re.I)]
    failed += [f"a reply has /{p}/" for p in final.get("any_lacks", [])
               if any(re.search(rx(p), r, re.I) for r in replies)]
    return failed


def run(repo, run_dir, reps, workers, use_api=False, budget_usd=3.0, only=None, model=None, effort=None):
    """{"runs": {conversation id: [{"turns": [...], "final_failed": [...]} per repeat]}, "usd": …, "mode": …}."""
    conversations, scen_hash = load_scenarios()
    if only:
        conversations = [c for c in conversations if any(c["id"].startswith(p) for p in only)]
    os.environ.update(KLIMABOT_DATA_DIR=str(run_dir / "data"), LEAD_MAIL_TO="",
                      KLIMABOT_KB_CACHE_DIR=os.environ.get("KLIMABOT_KB_CACHE_DIR", str(HERE / "data")))
    if use_api:
        from dotenv import load_dotenv
        load_dotenv(HERE / ".env")
    else:
        os.environ["ANTHROPIC_API_KEY"] = "unused-claude-cli"  # bot.py refuses to start without one
        # The CLI's usage figures carry its own prompt overhead: the production caps would cut the scripts short.
        os.environ.setdefault("KLIMABOT_SESSION_USD_CAP", "50")
        os.environ.setdefault("KLIMABOT_TURN_USD_CAP", "10")
    sys.path.insert(0, str(HERE / "eval"))   # the CLI adapter of this checkout
    sys.path.insert(0, str(repo))            # the bot under test
    os.chdir(repo)
    import bot  # noqa: E402
    from claude_cli_client import ClaudeCLIClient  # noqa: E402

    model = model or bot.MODEL
    if not use_api:
        bot.client = ClaudeCLIClient(model=model, log_dir=run_dir, effort=effort)
        prices = json.loads((HERE / "config" / "model_prices.json").read_text(encoding="utf-8"))
        if model not in prices:
            raise SystemExit(f"{model} has no prices in config/model_prices.json — add them first.")
        bot.PRICES = prices[model]  # the run's USD at its own model's rates; production's table stays bot.MODEL's
    bot.get_reranker()  # once here, not in every thread
    spent = {"usd": 0.0}

    def conversation(job):
        rep, conv = job
        if use_api and spent["usd"] >= budget_usd:
            return conv["id"], None
        sess = bot.Session()
        bot.use_session(sess)
        turns, replies = [], []
        for turn in conv["turns"]:
            quotes_before, usd_before, start = len(sess.quotes), sess.cost_usd, time.time()
            events = list(bot.run_user_turn_streaming(turn["customer"]))
            reply = "\n\n".join(d["text"] for e, d in events if e == "token")
            replies.append(reply)
            quoted = len(sess.quotes) > quotes_before
            turns.append({"customer": turn["customer"], "expect": turn["expect"], "reply": reply, "quoted": quoted,
                          "asks_contact": bool(bot._asks_contact(reply)),
                          "direction": direction(reply, quoted, bot.COMPANY_EMAIL, bot._asks_contact),
                          "calls": sum(1 for e, _ in events if e == "turn_complete"),
                          "regens": sum(1 for e, d in events
                                        if e == "notice" and d.get("text", "").startswith("Validator zamietol")),
                          "usd": round(sess.cost_usd - usd_before, 5), "seconds": round(time.time() - start, 1)})
        log = sess.log_path.read_text(encoding="utf-8") if sess.log_path.exists() else ""
        moves = [json.loads(line)["move"] for line in log.splitlines() if '"event": "policy_move"' in line]
        for i, t in enumerate(turns):
            t["move"] = moves[i] if i < len(moves) else None
        consent = bool(sess.consent and sess.consent.get("purpose") == "sales")
        failed = check_final(conv.get("final", {}), len(sess.quotes), consent, bool(sess.handoff_path), replies,
                             bot.COMPANY_EMAIL)
        bot.end_session(sess)
        spent["usd"] += sum(t["usd"] for t in turns)
        print(f"rep {rep + 1} {conv['id']}: " + " | ".join(f"{t['move'] or '-'}→{t['direction']}" for t in turns)
              + (f"  FINAL ✗ {failed}" if failed else "  final ✓"), file=sys.stderr, flush=True)
        return conv["id"], {"turns": turns, "final_failed": failed}

    jobs = [(rep, conv) for rep in range(reps) for conv in conversations]
    runs = {c["id"]: [] for c in conversations}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for cid, result in pool.map(conversation, jobs):
            if result is not None:
                runs[cid].append(result)
    return {"runs": runs, "usd": round(spent["usd"], 4), "reps": reps, "scenarios": scen_hash,
            "mode": "api" if use_api else f"cli:{model}" + (f"+{effort}" if effort else "")}


def summary(result):
    turns = [t for reps in result["runs"].values() for rep in reps for t in rep["turns"]]
    n = len(turns) or 1

    def ok(direction, moves):
        return direction in set().union(*(MOVE_DIRECTIONS.get(m, ALL) for m in moves))
    with_move = [t for t in turns if t.get("move")]
    agree = positions = 0
    for reps in result["runs"].values():
        for i in range(max((len(r["turns"]) for r in reps), default=0)):
            dirs = [r["turns"][i]["direction"] for r in reps if len(r["turns"]) > i]
            if len(dirs) > 1:
                positions += 1
                agree += len(set(dirs)) == 1
    convs = [r for reps in result["runs"].values() for r in reps]
    return {
        "turns": len(turns),
        "on_target": sum(ok(t["direction"], t["expect"]) for t in turns) / n,
        "policy_correct": (sum(t["move"] in t["expect"] for t in with_move) / len(with_move)) if with_move else None,
        "model_followed": (sum(ok(t["direction"], [t["move"]]) for t in with_move) / len(with_move))
        if with_move else None,
        "repeats_agree": agree / positions if positions else None,
        "final_ok": sum(not r["final_failed"] for r in convs) / (len(convs) or 1),
        "regens_per_turn": sum(t["regens"] for t in turns) / n,
        "calls_per_turn": sum(t["calls"] for t in turns) / n,
        "seconds_per_turn": sum(t["seconds"] for t in turns) / n,
        "usd_per_conversation": result["usd"] / (len(convs) or 1),
    }


def misses(result):
    out = []
    for cid, reps in result["runs"].items():
        for rep in reps:
            for i, t in enumerate(rep["turns"]):
                if t["direction"] not in set().union(*(MOVE_DIRECTIONS.get(m, ALL) for m in t["expect"])):
                    out.append(f"{cid} kolo {i + 1}: {t['move'] or '-'}→{t['direction']} (čakané {'/'.join(t['expect'])})")
            if rep["final_failed"]:
                out.append(f"{cid} koniec: {'; '.join(rep['final_failed'])}")
    return out


def write_report(result, path):
    s = summary(result)
    lines = [f"# Direction metrics — {result.get('commit', 'working tree')}", "",
             f"Mode `{result['mode']}`, scenarios `{result['scenarios']}`, {result['reps']} repeats.", "",
             "| metric | value |", "|---|---|"]
    lines += [f"| {k} | {fmt(k, v)} |" for k, v in s.items()]
    lines += ["", "## Off target", ""] + [f"- {m}" for m in misses(result)] + ["", "## Conversations", ""]
    for cid, reps in result["runs"].items():
        for r, rep in enumerate(reps, 1):
            lines.append(f"### {cid} (repeat {r}) — final {'✓' if not rep['final_failed'] else '✗ ' + '; '.join(rep['final_failed'])}")
            for i, t in enumerate(rep["turns"], 1):
                lines += [f"**{i}. Zákazník:** {t['customer']}  ",
                          f"čakané `{'/'.join(t['expect'])}`, politika `{t['move']}`, odpoveď `{t['direction']}`, "
                          f"regen {t['regens']}, {t['seconds']} s", "", "> " + t["reply"][:600].replace("\n", "\n> "), ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def fmt(key, value):
    if value is None:
        return "–"
    if key in ("on_target", "policy_correct", "model_followed", "repeats_agree", "final_ok"):
        return f"{value:.0%}"
    return f"{value:.3f}" if isinstance(value, float) else str(value)


KEYS = ["on_target", "policy_correct", "model_followed", "repeats_agree", "final_ok", "regens_per_turn",
        "calls_per_turn", "seconds_per_turn", "usd_per_conversation"]


def print_table(rows):
    print("| " + " | ".join(["run"] + KEYS) + " |")
    print("|---|" + "---|" * len(KEYS))
    for name, s in rows:
        print(f"| {name} | " + " | ".join(fmt(k, s.get(k)) for k in KEYS) + " |")


# A post-commit hook runs with git's own GIT_INDEX_FILE / GIT_DIR set: inherited, they made `git worktree add`
# fail with status 128 (the first five hook runs, 2026-10-28).
GIT_ENV = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}


def git(*args, cwd=HERE):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True,
                          env=GIT_ENV).stdout.strip()


def run_failure(run_dir, result):
    """Why a run can't be recorded (model calls that failed, replies that never came), or None."""
    errors = [json.loads(line).get("error", "") for path in (run_dir / "data" / "logs").glob("*.jsonl")
              for line in path.read_text(encoding="utf-8").splitlines() if '"event": "api_error"' in line]
    empty = sum(1 for reps in result["runs"].values() for rep in reps for t in rep["turns"] if not t["reply"].strip())
    if errors or empty:
        return f"{len(errors)} failed model calls, {empty} turns without a reply" + (f" ({errors[0][:120]})" if errors else "")
    return None


def measure_commit(ref, reps, workers, only):
    """A commit in a temporary worktree, one run at a time (a lock): appends a row to the history."""
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    sha = git("rev-parse", ref)
    with open(METRICS_DIR / ".lock", "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)  # commits made while a run is going wait for it
        worktree = METRICS_DIR / "worktrees" / sha[:12]
        run_dir = METRICS_DIR / f"{datetime.now():%Y-%m-%d_%H-%M-%S}_{sha[:8]}"
        run_dir.mkdir(parents=True)
        added = subprocess.run(["git", "worktree", "add", "--detach", str(worktree), sha], cwd=HERE,
                               capture_output=True, text=True, env=GIT_ENV)
        if added.returncode:
            raise SystemExit(f"git worktree add failed: {added.stderr.strip()}")
        try:
            result = run(worktree, run_dir, reps, workers, only=only)
        finally:
            os.chdir(HERE)
            subprocess.run(["git", "worktree", "remove", "--force", str(worktree)], cwd=HERE, capture_output=True,
                           env=GIT_ENV)
        result.update(commit=sha, subject=git("log", "-1", "--format=%s", sha),
                      branch=git("rev-parse", "--abbrev-ref", "HEAD"))
        (run_dir / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
        write_report(result, run_dir / "report.md")
        failure = run_failure(run_dir, result)
        if failure:
            # 2026-10-28: the subscription's 5-hour limit hit mid-run, 18 turns got no reply and the row said
            # 79 % on target. A run whose model calls failed measures nothing: it isn't recorded.
            run_dir.rename(run_dir.with_name(run_dir.name + "_failed"))
            raise SystemExit(f"{sha[:8]} NOT RECORDED — {failure}")
        row = {"ts": datetime.now().isoformat(timespec="seconds"), "commit": sha, "subject": result["subject"],
               "branch": result["branch"], "mode": result["mode"], "scenarios": result["scenarios"],
               "reps": reps, "only": only, "run_dir": str(run_dir), **summary(result), "misses": misses(result)}
        with HISTORY.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print_table([(sha[:8], row)])


def show_history(limit):
    if not HISTORY.exists():
        print("No measured commits yet: commit with the hook installed, or run --commit HEAD.")
        return
    rows = [json.loads(line) for line in HISTORY.read_text(encoding="utf-8").splitlines() if line.strip()][-limit:]
    print("| " + " | ".join(["date", "commit", "subject"] + KEYS) + " |")
    print("|---|---|---|" + "---|" * len(KEYS))
    for r in rows:
        print(f"| {r['ts'][:16]} | {r['commit'][:8]} | {r['subject'][:40]} | "
              + " | ".join(fmt(k, r.get(k)) for k in KEYS) + " |")


HOOK = """#!/bin/sh
# Klimabot: direction metrics for every commit (eval/stability.py --commit), in the background, on the Claude Code
# CLI subscription. History: eval/runs/metrics/history.jsonl — show it with: {python} eval/stability.py --history
# Skip once with KLIMABOT_METRICS=0 git commit …
[ "$KLIMABOT_METRICS" = "0" ] && exit 0
root=$(git rev-parse --show-toplevel)
unset GIT_DIR GIT_INDEX_FILE GIT_WORK_TREE GIT_PREFIX  # git sets them for hooks; the worktree must not inherit them
sha=$(git rev-parse HEAD)
mkdir -p "$root/eval/runs/metrics/logs"
nohup "{python}" "$root/eval/stability.py" --commit "$sha" > "$root/eval/runs/metrics/logs/$sha.log" 2>&1 &
"""


def install_hook():
    hook = Path(git("rev-parse", "--git-path", "hooks/post-commit"))
    hook = hook if hook.is_absolute() else HERE / hook
    if hook.exists() and "eval/stability.py" not in hook.read_text(encoding="utf-8"):
        raise SystemExit(f"{hook} exists and isn't ours — add the line from HOOK in eval/stability.py by hand.")
    hook.write_text(HOOK.replace("{python}", sys.executable), encoding="utf-8")
    hook.chmod(0o755)
    print(f"installed {hook}: every commit is measured in the background (KLIMABOT_METRICS=0 skips one)")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--commit", help="measure this commit (a temporary worktree) and append to the history")
    ap.add_argument("--repo", default=str(HERE), help="measure this checkout (default: this one)")
    ap.add_argument("--out", help="also save the result JSON here")
    ap.add_argument("--reps", type=int, default=2)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--only", nargs="*", help="conversation id prefixes")
    ap.add_argument("--api", action="store_true", help="the real Anthropic API instead of the CLI (costs money)")
    ap.add_argument("--budget-usd", type=float, default=3.0, help="--api only")
    ap.add_argument("--model", help="CLI only: another model on the same bot code (not recorded in the history)")
    ap.add_argument("--effort", help="CLI only: low, medium, high…")
    ap.add_argument("--history", nargs="?", const=30, type=int, metavar="N")
    ap.add_argument("--install-hook", action="store_true")
    ap.add_argument("--compare", nargs="+", metavar="RESULT_JSON")
    args = ap.parse_args()
    if (args.model or args.effort) and (args.commit or args.api):
        ap.error("--model and --effort are for CLI runs of a checkout: the history compares one setup")
    if args.install_hook:
        return install_hook()
    if args.history:
        return show_history(args.history)
    if args.compare:
        return print_table([(Path(p).parent.name if Path(p).name == "result.json" else Path(p).stem,
                             summary(json.loads(Path(p).read_text(encoding="utf-8")))) for p in args.compare])
    if args.commit:
        return measure_commit(args.commit, args.reps, args.workers, args.only)
    run_dir = METRICS_DIR / f"{datetime.now():%Y-%m-%d_%H-%M-%S}_worktree"
    run_dir.mkdir(parents=True)
    result = run(Path(args.repo).resolve(), run_dir, args.reps, args.workers, args.api, args.budget_usd, args.only,
                 args.model, args.effort)
    (run_dir / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    if args.out:
        Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    write_report(result, run_dir / "report.md")
    print_table([("this run", summary(result))])
    failure = run_failure(run_dir, result)
    if failure:
        raise SystemExit(f"NOT VALID — {failure}")
    print(f"→ {run_dir}/report.md", file=sys.stderr)


if __name__ == "__main__":
    main()
