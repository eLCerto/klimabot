"""Compare eval runs on the outcomes that matter, independently of bot.py.

Usage:  python eval/compare_runs.py eval/runs/round2 eval/runs/round2_final
Run eval/analyze.py on each run directory first (it writes summary.json).

Per run it reports:
  - expectation hits (lead, consent, handoff, quote, price before the GDPR question)
  - the GDPR audit from cost_report.py over the run's logs
  - personal data typed by customers who never consented, found in logs / sessions / handoff queue
  - sentences shown to the customer that look like internal reasoning, and promises made before consent
"""
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
import cost_report  # noqa: E402

PHONE_RE = re.compile(r"(?<![\d+])(?:\+\d{3}\s?|0)\d(?:[\s\-/]?\d){8}(?!\d)")
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
LEAK_RE = re.compile(r"čakám na\b[^.?!\n]{0,40}(?:zákazník|súhlas|server)|\b(?:od|na|pre)\s+zákazník(?:a|ovi|om)\b|"
                     r"`quote`|capture_lead|update_customer_state|customer_state|consent_given|\bzo servera\b|"
                     r"server\w*\s+(?:\w+\s+)?(?:pripoj|pripája|zaznamen)", re.I)
PROMISE_RE = re.compile(r"\b(?:ozve|ozvú|zavolá|zaznamenal\w*\s+som|uložil\w*\s+som|will\s+(?:call|contact)|"
                        r"i(?:'ve|\s+have)\s+(?:recorded|saved))\b", re.I)
CONDITIONAL_RE = re.compile(r"\b(?:keď|ak|až|akonáhle|hneď\s+ako|po\s+súhlase|once|if|after|when)\b", re.I)


def sentences(text):
    return [s for line in text.split("\n") for s in re.split(r"(?<=[.!?])\s+", line) if s.strip()]


def run_stats(run_dir):
    run_dir = Path(run_dir)
    convs = {c["id"]: c for c in (json.loads(p.read_text(encoding="utf-8"))
                                  for p in sorted((run_dir / "conversations").glob("*.json")))}
    rows = {r["id"]: r for r in json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))["rows"]}
    queue = (run_dir / "handoff_queue.jsonl").read_text(encoding="utf-8") if (run_dir / "handoff_queue.jsonl").exists() else ""
    out = {}
    for cid, c in convs.items():
        e = c["expect"]
        consent = (c.get("consent") or {}).get("purpose") or ("refused" if c.get("consent_refused") else "none")
        handoffs = [json.loads(l) for l in queue.splitlines() if l.strip() and json.loads(l)["log_file"] == c["log_file"]]
        checks = {
            "lead": e.get("lead") is None or e["lead"] == bool(c["handoff_markdown"]),
            "consent": not e.get("consent") or e["consent"] == consent,
            "handoff": e.get("handoff_request") is None or e["handoff_request"] == bool(handoffs),
            "quote": e.get("quote") is None or e["quote"] == bool(c["quotes"]),
        }
        # GDPR audit (independent): only matters when a lead exists
        audit = cost_report.summarize(run_dir / "logs" / c["log_file"])["gdpr_status"]
        # personal data without consent
        typed = " ".join(t["user"] for t in c["turns"])
        secrets = {re.sub(r"[\s\-/]", "", p) for p in PHONE_RE.findall(typed)} | set(EMAIL_RE.findall(typed))
        stored = (run_dir / "logs" / c["log_file"]).read_text(encoding="utf-8")
        sess = run_dir / "sessions" / c["log_file"].replace(".jsonl", ".json")
        stored += sess.read_text(encoding="utf-8") if sess.exists() else ""
        stored += "".join(json.dumps(h, ensure_ascii=False) for h in handoffs)
        flat = re.sub(r"[\s\-/]", "", stored)
        leaked_pii = sorted(s for s in secrets if consent == "none" or consent == "refused"
                            if s in flat or s in stored) if secrets else []
        # shown text: internal reasoning, promises before consent
        leaks, promises = [], []
        consent_seen = False
        for t in c["turns"]:
            notices = " ".join(t["notices"])
            if "Súhlas zaznamenaný" in notices:
                consent_seen = True
            for s in sentences("\n".join(t["assistant"])):
                if LEAK_RE.search(s):
                    leaks.append(s.strip()[:100])
                if not consent_seen and PROMISE_RE.search(s) and not CONDITIONAL_RE.search(s):
                    promises.append(s.strip()[:100])
        out[cid] = {"checks": checks, "audit": audit, "consent": consent, "pii": leaked_pii,
                    "leaks": leaks, "promises": promises, "row": rows.get(cid, {})}
    return out


def main(paths):
    stats = {p: run_stats(p) for p in paths}
    ids = sorted(set().union(*(s.keys() for s in stats.values())))
    for p, s in stats.items():
        n = len(s)
        hits = {k: sum(v["checks"][k] for v in s.values()) for k in ("lead", "consent", "handoff", "quote")}
        audit = {}
        for v in s.values():
            audit[v["audit"]] = audit.get(v["audit"], 0) + 1
        rows = [v["row"] for v in s.values()]
        print(f"\n== {p}  ({n} conversations)")
        print("  expectations met:", ", ".join(f"{k} {hits[k]}/{n}" for k in hits))
        print("  GDPR audit:", audit)
        print("  personal data stored without consent:", sum(bool(v["pii"]) for v in s.values()), "conversations",
              [k for k, v in s.items() if v["pii"]])
        print("  internal reasoning shown:", sum(len(v["leaks"]) for v in s.values()), "sentences in",
              sum(bool(v["leaks"]) for v in s.values()), "conversations")
        print("  promises before consent:", sum(len(v["promises"]) for v in s.values()), "sentences in",
              sum(bool(v["promises"]) for v in s.values()), "conversations")
        print("  regenerations:", sum(r.get("regens", 0) for r in rows), "| cut sentences (notices):",
              sum(r.get("leftovers", 0) for r in rows), "| soft:", sum(r.get("soft", 0) for r in rows),
              "| analyzer findings:", sum(r.get("flags", 0) for r in rows),
              "| quote problems:", sum(r.get("quote_problems", 0) for r in rows),
              "| untrusted amounts:", sum(r.get("price_notes", 0) for r in rows))
    print("\nper conversation (lead/consent/handoff/quote ✓✗ · leaks · promises):")
    for cid in ids:
        cells = []
        for p, s in stats.items():
            v = s.get(cid)
            if not v:
                cells.append("—")
                continue
            marks = "".join("✓" if v["checks"][k] else "✗" for k in ("lead", "consent", "handoff", "quote"))
            cells.append(f"{marks} L{len(v['leaks'])} P{len(v['promises'])} {v['consent']}")
        print(f"  {cid:42} " + " | ".join(cells))


if __name__ == "__main__":
    main(sys.argv[1:])
