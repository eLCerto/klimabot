"""AI review of an eval run: a model reads each conversation and scores it against the owner's sales rules
— the mistakes analyze.py's regexes can't see (no question about which rooms, "najlacnejšie" answered with the
dearest series, the same question asked three times, broken Slovak).

Usage:  python eval/judge.py eval/runs/<timestamp> [--only c01,c03] [--model M] [--budget-usd 1.0]
Writes judge.md and judge.json into the run directory. Needs ANTHROPIC_API_KEY in .env; every call is priced
from config/model_prices.json and the run stops before a call that could pass --budget-usd.
"""
import argparse
import json
import os
import sys
from pathlib import Path

import anthropic
from dotenv import load_dotenv

REPO = Path(__file__).resolve().parent.parent
PRICES = json.loads((REPO / "config" / "model_prices.json").read_text(encoding="utf-8"))
DEFAULT_MODEL = "claude-haiku-4-5-20251001"
MAX_TOKENS = 3000
TOOL_PREVIEW_CHARS = 400

# What each score means; the owner's decisions behind them are in CLAUDE.md and knowledge/rules/.
CRITERIA = {
    "discovery": "Pred prvou ponukou zistil, čo treba: plochu, pri byte alebo dome s viacerými izbami ktoré izby a "
                 "ich m², čo je pre zákazníka dôležité. Nepýtal sa na značku ani rozpočet a nepýtal sa znova na to, "
                 "čo zákazník už povedal.",
    "wishes": "Ponuka rešpektuje, čo zákazník chcel (najnižšia cena, tichý chod, filtrácia, Wi-Fi, značka, farba). "
              "Pri „najlacnejšie“ neponúkol drahý prémiový rad; pri prvej ponuke ukázal dve nacenené možnosti.",
    "sizing": "Výkon sedí k priestoru: približne 1 kW na 10 m² na každú chladenú miestnosť, nie na plochu celého "
              "bytu; nič výrazne väčšie ani menšie bez dôvodu od zákazníka.",
    "grounding": "Technické údaje, funkcie a služby (Wi-Fi, filtre, hlasové ovládanie, fotovoltika, splátky, "
                 "záruka, sklad) tvrdí iba podľa výsledkov nástrojov v prepise, nie z vlastných vedomostí.",
    "language": "Spisovná slovenčina bez českých a anglických slov a bez neexistujúcich tvarov (napr. „poviedate“, "
                "„naceením“); tyká iba zákazníkovi, ktorý tyká, inak vyká, a nestrieda to.",
    "flow": "Rozhovor napreduje: cena príde, keď je na rade, otázky sa neopakujú, odpovede nie sú zbytočne dlhé; "
            "po výbere ponuky požiada o kontakt a súhlas, nesľubuje termín dodania či montáže ani cenu montáže "
            "(„projektový manažér sa vám ozve do 1 pracovného dňa“ po súhlase je schválená veta, nie chyba).",
}
SYSTEM = (
    "Si skúsený vedúci predaja klimatizácií Samsung a Toshiba a hodnotíš prepis rozhovoru predajného chatbota so "
    "zákazníkom. Kritériá:\n" + "\n".join(f"- {name}: {text}" for name, text in CRITERIA.items())
    + "\n\nKaždé kritérium oboduj 1–5 (5 = bez chyby, 3 = viditeľná chyba, 1 = vážne poškodí predaj alebo dôveru) "
    "a ku každej chybe uveď kritérium, kolo, krátky doslovný citát z odpovede bota a v čom je problém. Hodnoť iba to, čo je "
    "v prepise; ceny počíta server a kontroluje ich iný test, preto ich správnosť nehodnoť. Ak kritérium "
    "v rozhovore nenastalo, daj 5 bez nálezov. Odpovedz iba nástrojom report_review."
)
# Flat on purpose: Haiku returned a nested "criteria" object as a JSON string.
TOOL = {
    "name": "report_review",
    "description": "Hodnotenie jedného rozhovoru.",
    "input_schema": {
        "type": "object",
        "properties": {
            **{f"{name}_score": {"type": "integer", "minimum": 1, "maximum": 5} for name in CRITERIA},
            "findings": {"type": "array", "items": {
                "type": "object",
                "properties": {"criterion": {"type": "string", "enum": list(CRITERIA)}, "turn": {"type": "integer"},
                               "quote": {"type": "string"}, "problem": {"type": "string"}},
                "required": ["criterion", "turn", "problem"]}},
            "summary": {"type": "string", "description": "Dve až tri vety: čo bolo najhoršie a čo dobré."},
        },
        "required": [f"{name}_score" for name in CRITERIA] + ["findings", "summary"],
    },
}


def _parsed(value):
    """A value the model may have sent as a JSON string, trailing text ignored (as bot.py does for updates)."""
    if isinstance(value, str):
        try:
            return json.JSONDecoder().raw_decode(value.strip())[0]
        except ValueError:
            return value
    return value


def normalized(raw):
    """{scores: {criterion: 1–5}, findings: [...], summary}; ValueError when the answer doesn't fit the schema."""
    scores = {}
    for name in CRITERIA:
        score = _parsed(raw.get(f"{name}_score"))
        if not isinstance(score, int) or not 1 <= score <= 5:
            raise ValueError(f"{name}_score = {score!r}")
        scores[name] = score
    findings = _parsed(raw.get("findings")) or []
    if not isinstance(findings, list):  # the scores still count
        findings = [{"criterion": "?", "turn": None, "problem": f"(nálezy sa nedali prečítať: {str(findings)[:200]})"}]
    findings = [f for f in (_parsed(f) for f in findings) if isinstance(f, dict) and f.get("problem")]
    return {"scores": scores, "findings": findings, "summary": str(raw.get("summary") or "")}


def render(conv):
    """The conversation as the reviewer reads it: customer, tool calls with a short result, bot."""
    out = [f"Konverzácia {conv['id']}: {conv.get('title', '')}"]
    if conv.get("review"):
        out.append(f"Čo mal scenár overiť: {conv['review']}")
    for i, turn in enumerate(conv["turns"], 1):
        out += ["", f"## Kolo {i}", f"Zákazník: {turn['user']}"]
        for tool in turn.get("tools", []):
            error = " [CHYBA]" if str(tool.get("is_error")) == "True" else ""
            out.append(f"Nástroj {tool['name']} {str(tool.get('input'))[:200]}{error} → "
                       f"{str(tool.get('output_preview', ''))[:TOOL_PREVIEW_CHARS]}")
        out.append("Bot: " + ("\n\n".join(turn.get("assistant") or []) or "(bez textu)"))
    return "\n".join(out)


def usage_usd(model, usage):
    p = PRICES[model]
    return (usage.input_tokens * p["input"] + usage.output_tokens * p["output"]
            + (getattr(usage, "cache_creation_input_tokens", 0) or 0) * p["cache_write_5m"]
            + (getattr(usage, "cache_read_input_tokens", 0) or 0) * p["cache_read"]) / 1e6


def projected_usd(model, text):
    """The most a call can cost: the prompt (about 3 characters a token, rounded up) and every output token."""
    p = PRICES[model]
    return ((len(SYSTEM) + len(json.dumps(TOOL)) + len(text)) / 3 * p["input"] + MAX_TOKENS * p["output"]) / 1e6


def review(client, model, conv):
    """(the report_review input, the call's USD)."""
    msg = client.messages.create(model=model, max_tokens=MAX_TOKENS, system=SYSTEM, tools=[TOOL],
                                 tool_choice={"type": "tool", "name": "report_review"},
                                 messages=[{"role": "user", "content": render(conv)}])
    block = next(b for b in msg.content if getattr(b, "type", "") == "tool_use")
    return block.input, usage_usd(model, msg.usage)


def judge(run_dir, client, model=DEFAULT_MODEL, budget_usd=1.0, only=None):
    if model not in PRICES:
        raise SystemExit(f"{model} has no prices in config/model_prices.json — add them first (the budget needs them).")
    run_dir = Path(run_dir)
    convs = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((run_dir / "conversations").glob("*.json"))]
    convs = [c for c in convs if not only or c["id"] in only or c["id"].split("_")[0] in only]
    results, spent, skipped = [], 0.0, []
    for conv in convs:
        text = render(conv)
        if spent + projected_usd(model, text) > budget_usd:
            skipped.append(conv["id"])
            continue
        try:
            raw, usd = review(client, model, conv)
        except anthropic.APIError as e:
            print(f"{conv['id']}: {e}", file=sys.stderr)
            skipped.append(conv["id"])
            continue
        spent += usd
        try:
            result = normalized(raw)
        except ValueError as e:
            print(f"{conv['id']}: the review doesn't fit the schema ({e})", file=sys.stderr)
            skipped.append(conv["id"])
            continue
        results.append({"id": conv["id"], "title": conv.get("title", ""), "usd": round(usd, 4), **result})
        print(f"{conv['id']}: " + " ".join(f"{k}={v}" for k, v in result["scores"].items()))
    write_report(run_dir, results, skipped, model, spent)
    return results


def write_report(run_dir, results, skipped, model, spent):
    out = ["# Klimabot eval — hodnotenie rozhovorov", "",
           f"Beh `{run_dir.name}` · model `{model}` · {len(results)} rozhovorov · {spent:.3f} $"
           + (f" · nehodnotené (rozpočet alebo chyba API): {', '.join(skipped)}" if skipped else ""), "",
           "Body 1–5 (5 = bez chyby). Kritériá: " + "; ".join(f"**{k}** — {v}" for k, v in CRITERIA.items()), "",
           "| rozhovor | " + " | ".join(CRITERIA) + " | spolu |", "|---|" + "---|" * (len(CRITERIA) + 1)]
    for r in sorted(results, key=lambda r: sum(r["scores"].values())):
        scores = [r["scores"][k] for k in CRITERIA]
        out.append(f"| {r['id']} | " + " | ".join(str(s) for s in scores) + f" | {sum(scores)} |")
    if results:
        out.append("| **priemer** | " + " | ".join(
            f"{sum(r['scores'][k] for r in results) / len(results):.1f}" for k in CRITERIA) + " | |")
    out += ["", "## Nálezy", ""]
    order = {k: i for i, k in enumerate(CRITERIA)}
    for r in results:
        out += [f"### {r['id']} — {r['title']}", "", r["summary"], ""]
        for f in sorted(r["findings"], key=lambda f: (order.get(f.get("criterion"), 99), f.get("turn") or 0)):
            quote = f" „{f['quote']}“" if f.get("quote") else ""
            out.append(f"- **{f.get('criterion', '?')}**, kolo {f.get('turn', '?')}:{quote} — {f['problem']}")
        out.append("")
    (run_dir / "judge.md").write_text("\n".join(out), encoding="utf-8")
    (run_dir / "judge.json").write_text(json.dumps({"model": model, "usd": round(spent, 4), "skipped": skipped,
                                                    "results": results}, ensure_ascii=False, indent=2),
                                        encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("run_dir")
    ap.add_argument("--only", help="conversation ids or their prefixes, comma-separated (c01,c03)")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--budget-usd", type=float, default=1.0)
    args = ap.parse_args()
    load_dotenv(REPO / ".env")
    key = os.getenv("ANTHROPIC_API_KEY", "")
    if not key or key.endswith("..."):  # the same check as bot.py: missing, or the .env.example placeholder
        raise SystemExit("ANTHROPIC_API_KEY is missing or still the placeholder from .env.example.")
    only = {x.strip() for x in args.only.split(",")} if args.only else None
    judge(args.run_dir, anthropic.Anthropic(api_key=key, max_retries=2), args.model, args.budget_usd, only)
    print(f"→ {Path(args.run_dir) / 'judge.md'}")


if __name__ == "__main__":
    main()
