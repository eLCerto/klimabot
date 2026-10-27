"""Stability check: the same scripted conversations several times through the real API, and how often each reply
heads where it should and agrees with its repeats. Compares two versions of the bot (an A/B of a change).

Usage:  python eval/stability.py --repo <checkout> --out <file.json> [--reps 3] [--budget-usd 3]
        python eval/stability.py --compare a.json b.json
Needs ANTHROPIC_API_KEY (this repo's .env is read). The production caps stay on; the run stops before a
conversation once --budget-usd is spent. Each reply's direction is read by code (direction()), not by a model.
"""
import argparse
import json
import os
import re
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent

# Each turn lists the directions that are right for it (knowledge/rules/feedback_overit_potreby_pred_ponukou.md and
# the owner's decisions in CLAUDE.md: rooms and what matters before the first offer, two priced options, decline in
# one sentence, the contact after a choice).
SCENARIOS = {
    "spalna_cena": [("Dobrý deň, hľadám klimatizáciu do spálne, má 14 m². Koľko by stála?", {"ponuka"})],
    "byt_dve_izby": [("Dobrý deň, potrebujem klímu do dvojizbového bytu, má 50 m2.", {"zisti-izby"}),
                     ("Chcem chladiť obe izby, každá má 20 m2.", {"zisti-priority"}),
                     ("Hlavne nech je to čo najlacnejšie.", {"ponuka"})],
    "vagny_zaciatok": [("Dobrý deň, chcem klimatizáciu.", {"zisti-priestor"}),
                       ("Obývačka 30 m2, chcem aby bola tichá.", {"ponuka"})],
    "fotovoltika": [("Dá sa vaša klimatizácia napojiť na fotovoltiku?", {"neponukame"})],
    "vyber_a_kontakt": [("Spálňa 12 m2, koľko stojí najlacnejšia klimatizácia?", {"ponuka"}),
                        ("Beriem tú lacnejšiu.", {"kontakt"})],
    "otazka_po_ponuke": [("Spálňa 16 m2, chcem Wi-Fi. Koľko to stojí?", {"ponuka"}),
                         ("Má tá lacnejšia aj dobrý filter?", {"odpoved", "ponuka"})],
}

_EUR_RE = re.compile(r"\d[\d\s.,]*\s*€|€\s*\d")
_QUESTION_SENTENCES_RE = re.compile(r"[^.!?\n]*\?")


def direction(reply, quoted):
    """Where a reply heads, read from its text and whether a quote was made this turn. A first question about
    the type of space counts as zisti-priestor even when it also asks about the rooms (the directive asks both)."""
    low = reply.lower()
    questions = " ".join(_QUESTION_SENTENCES_RE.findall(low))
    if re.search(r"neponúk|nepredáv|nezaober|nezahŕň|nerobíme|neposkytuj|nemôžeme|nie je (?:súčasť|predmet|naš)", low):
        return "neponukame"
    if re.search(r"\bmeno\b|telefón|e-mail", low) and re.search(r"súhlas|nechajte|potrebujem|napíšte", low):
        return "kontakt"
    if quoted and _EUR_RE.search(reply):
        return "ponuka"
    if re.search(r"ak[ýá] (?:typ )?priestor|typ priestoru|\bbyt, rodinný dom", questions):
        return "zisti-priestor"
    if re.search(r"izb|miestnost", questions):
        return "zisti-izby"
    if re.search(r"dôležit|tich|filtr|wi-?fi|dizajn|najnižš", questions):
        return "zisti-priority"
    if re.search(r"m²|m2|ploch", questions):
        return "zisti-priestor"
    return "odpoved"


def run(repo, reps, budget_usd):
    """{scenario: [[turn record, …] per repeat]} through the bot in `repo`."""
    from dotenv import load_dotenv
    load_dotenv(HERE / ".env")
    data = Path(tempfile.mkdtemp(prefix="klimabot_stability_"))
    os.environ.update(KLIMABOT_DATA_DIR=str(data), LEAD_MAIL_TO="",
                      KLIMABOT_KB_CACHE_DIR=os.environ.get("KLIMABOT_KB_CACHE_DIR", str(HERE / "data")))
    sys.path.insert(0, str(repo))
    os.chdir(repo)
    import bot  # noqa: E402 — the version under test

    spent, out = 0.0, {}
    for rep in range(reps):
        for name, turns in SCENARIOS.items():
            if spent >= budget_usd:
                print(f"budget reached ({spent:.2f} $): stopping", file=sys.stderr)
                return out, spent
            sess = bot.Session()
            bot.use_session(sess)
            records = []
            for message, expected in turns:
                quotes_before, usd_before, start = len(sess.quotes), sess.cost_usd, time.time()
                events = list(bot.run_user_turn_streaming(message))
                reply = "\n\n".join(d["text"] for e, d in events if e == "token")
                records.append({"message": message, "expected": sorted(expected), "reply": reply,
                                "direction": direction(reply, len(sess.quotes) > quotes_before),
                                "calls": sum(1 for e, _ in events if e == "turn_complete"),
                                "regens": sum(1 for e, d in events
                                              if e == "notice" and d.get("text", "").startswith("Validator zamietol")),
                                "usd": round(sess.cost_usd - usd_before, 5), "seconds": round(time.time() - start, 1)})
            log = sess.log_path.read_text(encoding="utf-8") if sess.log_path.exists() else ""
            records[-1]["sentences_dropped"] = log.count('"event": "bot_reply_sentences_dropped"')
            bot.end_session(sess)
            spent += sum(r["usd"] for r in records)
            out.setdefault(name, []).append(records)
            print(f"rep {rep + 1} {name}: " + " | ".join(r["direction"] for r in records)
                  + f"  ({sum(r['usd'] for r in records):.3f} $)", file=sys.stderr)
    return out, spent


def summary(result):
    turns = [(name, i, rec) for name, repeats in result["runs"].items() for rep in repeats
             for i, rec in enumerate(rep)]
    n = len(turns) or 1
    on_target = sum(rec["direction"] in rec["expected"] for _, _, rec in turns)
    agree, positions = 0, 0
    for name, repeats in result["runs"].items():
        for i in range(max(len(r) for r in repeats)):
            dirs = [r[i]["direction"] for r in repeats if len(r) > i]
            if len(dirs) > 1:
                positions += 1
                agree += len(set(dirs)) == 1
    convs = sum(len(r) for r in result["runs"].values()) or 1
    return {"turns": len(turns), "on_target": on_target / n, "repeats_agree": agree / (positions or 1),
            "regens_per_turn": sum(r["regens"] for _, _, r in turns) / n,
            "calls_per_turn": sum(r["calls"] for _, _, r in turns) / n,
            "seconds_per_turn": sum(r["seconds"] for _, _, r in turns) / n,
            "usd_per_conversation": result["usd"] / convs}


def compare(paths):
    rows = [(Path(p).stem, summary(json.loads(Path(p).read_text(encoding="utf-8")))) for p in paths]
    keys = ["turns", "on_target", "repeats_agree", "regens_per_turn", "calls_per_turn", "seconds_per_turn",
            "usd_per_conversation"]
    print("| metric | " + " | ".join(name for name, _ in rows) + " |")
    print("|---|" + "---|" * len(rows))
    for k in keys:
        cells = [f"{s[k]:.0%}" if k in ("on_target", "repeats_agree") else f"{s[k]:.3f}" if isinstance(s[k], float)
                 else str(s[k]) for _, s in rows]
        print(f"| {k} | " + " | ".join(cells) + " |")
    for name, s in rows:
        result = json.loads(Path(paths[[r[0] for r in rows].index(name)]).read_text(encoding="utf-8"))
        misses = Counter(f"{scen} kolo {i + 1}: {rec['direction']} (čakané {'/'.join(rec['expected'])})"
                         for scen, reps in result["runs"].items() for rep in reps for i, rec in enumerate(rep)
                         if rec["direction"] not in rec["expected"])
        print(f"\n{name} — mimo cieľa: " + ("; ".join(f"{k} ×{v}" for k, v in misses.most_common()) or "nič"))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--repo", default=str(HERE))
    ap.add_argument("--out")
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--budget-usd", type=float, default=3.0)
    ap.add_argument("--compare", nargs="+")
    args = ap.parse_args()
    if args.compare:
        compare(args.compare)
        return
    out = Path(args.out).resolve()  # run() changes into the repo under test
    runs, spent = run(Path(args.repo).resolve(), args.reps, args.budget_usd)
    out.write_text(json.dumps({"repo": args.repo, "usd": spent, "runs": runs}, ensure_ascii=False,
                                         indent=1), encoding="utf-8")
    print(f"→ {args.out} ({spent:.2f} $)", file=sys.stderr)


if __name__ == "__main__":
    main()
