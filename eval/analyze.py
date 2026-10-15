"""Analyze an eval run: verify every quoted price against the raw product JSONs and
discounts.json (independently of bot.py's pricing code), check every euro amount the
bot wrote, flag rule violations, and collect the leads.

Usage:  python eval/analyze.py eval/runs/<timestamp>
Writes report.md and transcripts.md into the run directory.
"""
import difflib
import json
import os
import re
import statistics
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CODE_FIELDS = ("set", "model", "indoor", "outdoor", "code")
FOLDERS = {"single_split": "single_split", "multi_split": "multi_split",
           "light_commercial": "commercial", "accessories": "accessories"}
PHRASES = json.loads((REPO / "config" / "consent_phrases.json").read_text(encoding="utf-8"))
# Every wording the audit recognises, current and previous (older logs keep passing).
QUESTIONS = {purpose: [q["sk"]] for purpose, q in PHRASES["questions"].items()}
for _purpose, _old in PHRASES.get("previous_questions", {}).items():
    if not _purpose.startswith("_"):
        QUESTIONS.setdefault(_purpose, []).extend(_old)
YES_RE = re.compile(PHRASES["yes_re"], re.I)
YES_NOT_CONSENT_RE = re.compile(PHRASES["yes_not_consent_re"], re.I)
NO_RE = re.compile(PHRASES["no_re"], re.I)
NO_NOT_REFUSAL_RE = re.compile(PHRASES["no_not_refusal_re"], re.I)  # "nesúhlasím s cenou"
NO_IN_WINDOW_RE = re.compile(PHRASES["no_in_window_re"], re.I)
_N = r"\d{1,3}(?:[ \u00a0\u202f.,]\d{3})+(?:[.,]\d{1,2})?|\d+(?:[.,]\d{1,2})?"
EUR_RE = re.compile(rf"(?<![\d,.])({_N})(?=\s*(?:,-\s*)?(?:€|eur\b|eurá\b|eurov\b|euro\b))|€\s*({_N})"
                    rf"|(?<![\d,.])({_N})(?=\s*(?:–|—|-|až|to)\s*(?:{_N})\s*(?:€|eur\b))", re.I)
NUM_RE = re.compile(r"\d{1,3}(?:[ \u00a0\u202f.,]\d{3})+(?:[.,]\d+)?|\d+(?:[.,]\d+)?")
CODE_LIKE_RE = re.compile(
    r"\b(AR\d{2,3}[A-Z]\d{2}[A-Z0-9]+(?:/EU)?|AJ\d{3}TXJ\d+KG(?:/EU)?|AC\d{2,3}[A-Z]{3,5}[A-Z0-9]*(?:/EU|/NG|/KG)?|"
    r"RAS-(?:B?\d{2,4}[A-Z]+\d*[A-Z]+(?:-[A-Z]\d*)?|[2-5]M\d{2,3}G\d[A-Z]+(?:-[A-Z]\d*)?)|"
    r"RAV-[A-Z]{2,3}\d{3,4}[A-Z]+(?:-[A-Z]\d*)?|(?:RBC|TCB|MIM|MXJ|TO-RC)-[A-Z0-9]+(?:-[A-Z0-9]+)*)\b")
CZECH_RE = re.compile(r"\b(výborně|pojďme|děkuji|jakmile|venkovní|vnitřní|konfigurace|kroků|třída|celkem|jméno|tady|"
                      r"nebo|včetně|nyní|další|více|protože|přesně|zajistím)\b", re.I)
PERMIT_RE = re.compile(r"spoločenstv\w*\s+vlastník|správc\w*\s+(domu|budovy)|\bSVB\b|\bHOA\b|stavebn\w+\s+úrad|povolen", re.I)
APPROX_RE = re.compile(r"(~|\bcca\.?|\bokolo|\bpribli[žz]ne|\bzhruba|\baround|\babout|\bapprox\w*)\s*[*_]*\s*"
                       r"(?:€\s*\d|\d[\d\s.,–-]*[*_]*\s*€)", re.I)
SESSION_USD_CAP = float(os.getenv("KLIMABOT_SESSION_USD_CAP", "0.50"))  # API runs keep bot.py's cap
PRICES = json.loads((REPO / "config" / "model_prices.json").read_text(encoding="utf-8"))["claude-haiku-4-5-20251001"]


def usage_from_log(path):
    """Token and USD totals of a session from its llm_turn events (every API call)."""
    totals = {"input": 0, "output": 0, "cache_write": 0, "cache_read": 0, "usd": 0.0, "calls": 0}
    if not path.exists():
        return totals
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        if e.get("event") != "llm_turn":
            continue
        totals["calls"] += 1
        totals["input"] += e.get("input_tokens", 0)
        totals["output"] += e.get("output_tokens", 0)
        totals["cache_write"] += e.get("cache_write", 0)
        totals["cache_read"] += e.get("cache_read", 0)
        totals["usd"] += e["usd"] if "usd" in e else (  # logs from before the USD meter
            e.get("input_tokens", 0) * PRICES["input"] + e.get("output_tokens", 0) * PRICES["output"]
            + e.get("cache_write", 0) * PRICES["cache_write_5m"] + e.get("cache_read", 0) * PRICES["cache_read"]) / 1e6
    return totals


def cache_share(u):
    """Share of input tokens served from the prompt cache."""
    total = u["input"] + u["cache_write"] + u["cache_read"]
    return 100 * u["cache_read"] / total if total else 0.0


EMOJI_RE = re.compile("[\U0001F300-\U0001FAFF☀-➿]")


# ---------- raw product DB (independent of bot.py) ----------

def load_db():
    by_code = defaultdict(list)
    for brand_dir in ("knowledge/samsung", "knowledge/toshiba"):
        for path in (REPO / brand_dir).rglob("*.json"):
            if "glossary" in path.name:
                continue
            folder = next((FOLDERS[p] for p in path.parts if p in FOLDERS), None)
            data = json.loads(path.read_text(encoding="utf-8"))

            def walk(node, trail):
                if isinstance(node, dict):
                    for field in CODE_FIELDS:
                        if isinstance(node.get(field), str):
                            for code in re.split(r"[\s+,]+", node[field]):
                                if len(code) >= 4:
                                    by_code[code.upper()].append({"file": path.name, "folder": folder, "trail": trail,
                                                                  "field": field, "rec": node})
                    for k, v in node.items():
                        walk(v, trail + [k])
                elif isinstance(node, list):
                    for v in node:
                        walk(v, trail)
            walk(data, [])
    return by_code


def catalog_prices(entries, code, as_set_codes=None):
    """Possible catalog prices for a code (or a set of codes) per the raw data."""
    prices = set()
    for e in entries:
        rec, field = e["rec"], e["field"]
        if as_set_codes:
            codes = {c.upper() for f in CODE_FIELDS if isinstance(rec.get(f), str) for c in re.split(r"[\s+,]+", rec[f])}
            if set(as_set_codes) <= codes and isinstance(rec.get("set_price_EUR"), (int, float)):
                prices.add(float(rec["set_price_EUR"]))
            continue
        if field == "indoor" and "indoor_price_EUR" in rec:
            prices.add(float(rec["indoor_price_EUR"]))
        elif field == "outdoor" and "outdoor_price_EUR" in rec:
            prices.add(float(rec["outdoor_price_EUR"]))
        elif "set_price_EUR" not in rec:
            for key in ("price_EUR", "catalog_price_EUR"):
                if isinstance(rec.get(key), (int, float)):
                    prices.add(float(rec[key]))
                    break
    return prices


def expected_category(entries, n_codes):
    cats = set()
    for e in entries:
        trail = ".".join(e["trail"]).lower()
        if e["field"] == "code":
            if "panel" in trail:
                cats.add("panels")
            elif any(k in trail for k in ("control", "remote", "sensor", "wifi", "bms", "central")):
                cats.add("controls")
            else:
                cats.add("accessories")
        elif e["folder"] == "single_split":
            cats.add("single_split_sets" if n_codes == 2 else "single_split_units")
        elif e["folder"] in ("multi_split", "commercial"):
            unit = "indoor" if e["field"] == "indoor" else "outdoor"
            cats.add(f"{'multi_split' if e['folder'] == 'multi_split' else 'commercial'}_{unit}")
    return cats


# ---------- helpers ----------

def parse_amount(m):
    raw = re.sub(r"[\s\u00a0\u202f]", "", next(g for g in m.groups() if g))
    mm = re.fullmatch(r"(\d+(?:[.,]\d{3})*)(?:[.,](\d{1,2}))?", raw)
    return float(re.sub(r"[.,]", "", mm.group(1)) + ("." + mm.group(2) if mm.group(2) else ""))


def consent_answer(text):
    """'yes', 'no' or None for the customer's message right after the consent question."""
    if NO_RE.search(NO_NOT_REFUSAL_RE.sub(" ", text)) or NO_IN_WINDOW_RE.search(text):
        return "no"
    return "yes" if YES_RE.search(YES_NOT_CONSENT_RE.sub(" ", text)) else None


TOTAL_PATHS = (("total_eur",), ("total_with_DPH_23pct_eur",))


def derived_amounts(quotes, customer):
    """Differences / sums of same-basis quote totals, and |total - customer amount|."""
    totals = []
    for q in quotes:
        for path in TOTAL_PATHS:
            node = q
            for k in path:
                node = node.get(k) if isinstance(node, dict) else None
            if isinstance(node, (int, float)):
                totals.append((path, float(node)))
    out = set()
    for i, (pa, a) in enumerate(totals):
        out |= {abs(a - c) for c in customer}
        for j, (pb, b) in enumerate(totals[i + 1:], i + 1):
            if pa == pb:
                out |= {abs(a - b), a + b}
                # two systems together vs. a third variant, as bot.py verifies it (d03, d05)
                out |= {abs(a + b - c) for k, (pc, c) in enumerate(totals) if k not in (i, j) and pc == pa}
    return out


def numbers_in(text):
    """Every plausible reading of every number: Slovak ('1 290,50', '5.000') and English ('3,500', '1,290.50')."""
    out = set()
    for raw in NUM_RE.findall(text):
        flat = re.sub(r"[\s\u00a0\u202f]", "", raw)
        variants = [flat.replace(",", "."), flat.replace(".", "").replace(",", ".")]
        if re.fullmatch(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?", flat):  # English thousands separator
            variants.append(flat.replace(",", ""))
        for variant in variants:
            try:
                out.add(float(variant))
            except ValueError:
                pass
    return out


def euro_fields(node):
    if isinstance(node, dict):
        for k, v in node.items():
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                if "eur" in k.lower():
                    yield float(v)
            else:
                yield from euro_fields(v)
    elif isinstance(node, list):
        for v in node:
            yield from euro_fields(v)


def close(a, b, tol=0.011):
    return abs(a - b) <= tol


# ---------- checks ----------

def verify_quote(q, db, policy):
    problems = []
    cats_pct = policy["category_discount_pct"]
    seg = policy["customer_segment_modifiers"]
    cap = seg["max_total_discount_pct"]
    seg_pct = seg[q["segment"]]["additional_pct"]
    total = catalog_total = 0.0
    counts = defaultdict(int)
    for line in q["lines"]:
        codes = [c.upper() for c in line["codes"]]
        entries = [e for c in codes for e in db.get(c, [])]
        if not entries:
            problems.append(f"{codes}: kód nie je v databáze")
            continue
        if len(codes) == 2:
            prices = catalog_prices(db[codes[0]], codes[0], as_set_codes=codes)
        else:
            prices = catalog_prices(db[codes[0]], codes[0])
        if not any(close(line["unit_catalog_price_eur"], p, 0.5) for p in prices):
            problems.append(f"{codes}: katalógová cena {line['unit_catalog_price_eur']} € nie je v DB (DB: {sorted(prices)})")
        exp_cats = expected_category(entries, len(codes))
        if line["discount_category"] not in exp_cats:
            problems.append(f"{codes}: kategória {line['discount_category']}, podľa DB {sorted(exp_cats)}")
        exp_pct = min(cats_pct[line["discount_category"]] + seg_pct, cap)
        if line["discount_pct"] != exp_pct and not q.get("promotion"):
            problems.append(f"{codes}: zľava {line['discount_pct']} %, očakávané {exp_pct} %")
        unit = round(line["unit_catalog_price_eur"] * (1 - line["discount_pct"] / 100), 2)
        for key, expected in (("unit_price_eur", unit),
                              ("unit_discount_eur", round(line["unit_catalog_price_eur"] - unit, 2)),
                              ("unit_price_with_DPH_23pct_eur", round(unit * 1.23, 2)),
                              ("line_total_eur", round(unit * line["qty"], 2))):
            if not close(line[key], expected, 0.02):
                problems.append(f"{codes}: {key} = {line[key]}, prepočet {expected}")
        total += unit * line["qty"]
        catalog_total += line["unit_catalog_price_eur"] * line["qty"]
        counts[line["discount_category"]] += line["qty"]
    for key, expected in (("total_eur", total), ("catalog_total_eur", catalog_total),
                          ("discount_total_eur", catalog_total - total), ("DPH_23pct_eur", total * 0.23),
                          ("total_with_DPH_23pct_eur", total * 1.23)):
        if key in q and not close(q[key], round(expected, 2), 0.05):
            problems.append(f"{key} = {q[key]}, prepočet {round(expected, 2)}")
    if "budget" in q:
        # Compared on the customer's basis (with DPH unless they said "bez DPH"); older runs: without DPH.
        b = q["budget"]["budget_eur"]
        t = q["budget"].get("compared_price_eur", q["total_eur"])
        if t not in (q["total_eur"], q["total_with_DPH_23pct_eur"]):
            problems.append(f"budget.compared_price_eur {t} nie je cena jednotiek bez DPH ani s DPH")
        exp = ("v rozpočte" if t <= b else "na hranici rozpočtu" if t <= b * 1.05
               else "nad rozpočtom" if t <= b * 1.2 else "výrazne nad rozpočtom")
        if q["budget"]["status"] != exp:
            problems.append(f"budget.status '{q['budget']['status']}', prepočet '{exp}'")
    if q.get("installation_estimate") or q.get("all_in_estimate"):
        problems.append("ponuka obsahuje cenu montáže, hoci ju bot neuvádza")
    return problems


def reply_checks(text, turn_idx, expect, lead_already):
    flags = []
    if expect.get("language") == "sk" and CZECH_RE.search(text):
        flags.append(f"čeština: {sorted({m.lower() for m in CZECH_RE.findall(text)})}")
    if expect.get("language") == "en" and re.search(r"[áäčďéíĺľňóôŕšťúýž]{1}\w*\s", text) and \
            len(re.findall(r"\b(je|pre|alebo|cena|ktorá|vám)\b", text)) >= 3:
        flags.append("odpoveď po slovensky zákazníkovi, ktorý píše po anglicky")
    if PERMIT_RE.search(text):
        flags.append(f"povolenia/súhlas k inštalácii: '{PERMIT_RE.search(text).group(0)}'")
    if re.search(r"kam\b[^.?!\n]{0,60}vonkajš|vonkajš[^.?!\n]{0,60}\bkam\b", text, re.I) and "?" in text:
        flags.append("pýta sa, kam pôjde vonkajšia jednotka")
    if re.search(r"(chcete|chceš|potrebujete|potrebuješ|má\w*)[^.?!\n]{0,60}(vykurovan|kúren)[^.!\n]{0,40}\?", text, re.I):
        flags.append("pýta sa na vykurovanie")
    if turn_idx == 0 and re.search(r"rozpo[čc]et[^.!\n]{0,40}\?", text, re.I):
        flags.append("pýta rozpočet v prvej odpovedi")
    if re.search(r"^#{1,3}\s", text, re.M):
        flags.append("Markdown nadpis")
    if re.search(r"objednávk|objednan", text, re.I) and lead_already:
        flags.append("po zápise hovorí o objednávke")
    if APPROX_RE.search(text):
        flags.append(f"odhad sumy: '{APPROX_RE.search(text).group(0)}'")
    return flags


def analyze(run_dir):
    run_dir = Path(run_dir)
    db = load_db()
    policy = json.loads((REPO / "config" / "discounts.json").read_text(encoding="utf-8"))
    all_codes = set(db)
    convs = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((run_dir / "conversations").glob("*.json"))]
    leads = [json.loads(l) for l in (run_dir / "leads.jsonl").read_text(encoding="utf-8").splitlines()] \
        if (run_dir / "leads.jsonl").exists() else []
    queue = [json.loads(l) for l in (run_dir / "handoff_queue.jsonl").read_text(encoding="utf-8").splitlines()] \
        if (run_dir / "handoff_queue.jsonl").exists() else []
    by_log = {c["log_file"]: c["id"] for c in convs}

    rows, details, summary = [], [], {"conversations": len(convs)}
    total_quotes = total_quote_problems = total_amounts = total_untrusted = 0
    for c in convs:
        expect = c["expect"]
        flags, price_notes = [], []
        quote_problems = []
        for i, q in enumerate(c["quotes"]):
            for p in verify_quote(q, db, policy):
                quote_problems.append(f"quote #{i + 1}: {p}")
        total_quotes += len(c["quotes"])
        total_quote_problems += len(quote_problems)

        quotes_seen = 0
        customer_text = ""
        lead_turn = None
        gdpr_turn = None
        first_quote_turn = None
        asked_purpose = None      # canonical question shown in the previous turn
        consent_turn = consent_purpose = None
        refused = False
        regens = leftovers = soft_total = 0
        tool_errors = []
        for ti, t in enumerate(c["turns"]):
            customer_text += "\n" + t["user"]
            if asked_purpose and consent_purpose is None:  # only the very next message answers
                answer = consent_answer(t["user"])
                if answer == "yes":
                    consent_turn, consent_purpose = ti, asked_purpose
                elif answer == "no":
                    refused = True
            asked_purpose = None
            quotes_seen += sum(1 for tool in t["tools"] if tool["name"] == "quote" and not tool.get("is_error"))
            if quotes_seen and first_quote_turn is None:
                first_quote_turn = ti
            text = "\n".join(t["assistant"])
            customer_numbers = numbers_in(customer_text)
            trusted = {a for q in c["quotes"][:quotes_seen] for a in euro_fields(q)} | customer_numbers \
                | derived_amounts(c["quotes"][:quotes_seen], customer_numbers)
            for m in EUR_RE.finditer(text):
                total_amounts += 1
                amount = parse_amount(m)
                if not any(abs(amount - x) <= 1 for x in trusted):
                    total_untrusted += 1
                    price_notes.append(f"kolo {ti + 1}: suma {m.group(0)} € nepochádza z quote ani od zákazníka")
            # Amount next to a model code should belong to a quote line or total containing that code.
            for line in text.splitlines():
                codes_in_line = {x.upper() for x in CODE_LIKE_RE.findall(line)}
                amounts = [parse_amount(m) for m in EUR_RE.finditer(line)]
                if not codes_in_line or not amounts:
                    continue
                related = set()
                for q in c["quotes"][:quotes_seen]:
                    q_codes = {x.upper().split("/")[0] for l in q["lines"] for x in l["codes"]}
                    if {x.split("/")[0] for x in codes_in_line} & q_codes:
                        related |= set(euro_fields(q))
                for a in amounts:
                    if related and not any(abs(a - x) <= 1 for x in related) and not any(abs(a - x) <= 1 for x in numbers_in(customer_text)):
                        price_notes.append(f"kolo {ti + 1}: {a} € pri kóde {sorted(codes_in_line)} nesedí s ponukou pre tento kód")
            bad_codes = sorted({x for x in (y.upper() for y in CODE_LIKE_RE.findall(text))
                                if x not in all_codes and x.split("/")[0] not in all_codes
                                and not any(x + s in all_codes for s in ("/EU", "/NG", "/KG"))})
            if bad_codes:
                flags.append(f"kolo {ti + 1}: kódy mimo DB {bad_codes}")
            for f in reply_checks(text, ti, expect, lead_turn is not None):
                flags.append(f"kolo {ti + 1}: {f}")
            for chunk in t["assistant"]:  # the 1-emoji limit is per message
                if len(EMOJI_RE.findall(chunk)) > 1:
                    flags.append(f"kolo {ti + 1}: {len(EMOJI_RE.findall(chunk))} emoji v jednej správe")
            for a, b in zip(t["assistant"], t["assistant"][1:]):
                if len(a) > 200 and difflib.SequenceMatcher(None, a, b).ratio() > 0.7:
                    flags.append(f"kolo {ti + 1}: zákazník dostal takmer rovnakú odpoveď dvakrát")
            dropped = [n for n in t["notices"] if n.startswith("Server odstránil")]
            if dropped:
                flags.append(f"kolo {ti + 1}: server po regenerácii vystrihol vety ({'; '.join(n.split(':', 1)[1].strip() for n in dropped)})")
            shown_purpose = next((p for p, qs in QUESTIONS.items() if any(q in text for q in qs)), None)
            if shown_purpose:
                asked_purpose = shown_purpose
                if gdpr_turn is None:
                    gdpr_turn = ti
            if re.search(r"s[úu]hlas\w*\s+so\s+spracovan", text, re.I) and not shown_purpose:
                flags.append(f"kolo {ti + 1}: GDPR otázka nie je v kanonickom znení")
            for pattern in expect.get("must_not_say") or []:
                hit = re.search(pattern, text, re.I)
                if hit:
                    flags.append(f"kolo {ti + 1}: zakázaný text /{pattern}/: '{hit.group(0)[:80]}'")
            for want in expect.get("must_say") or []:  # {"turn": 1, "pattern": "112"}: required in that turn
                if want.get("turn") == ti + 1 and not re.search(want["pattern"], text, re.I):
                    flags.append(f"kolo {ti + 1}: chýba /{want['pattern']}/")
            regens += sum("Regenerujem" in n for n in t["notices"])
            leftovers += len(dropped)
            soft_total += sum(n.startswith("Mäkké porušenie") for n in t["notices"])
            for tool in t["tools"]:
                if tool.get("is_error"):
                    tool_errors.append(f"kolo {ti + 1}: {tool['name']} → {tool.get('output_preview', '')[:160]}")
                if tool["name"] == "capture_lead" and not tool.get("is_error") and lead_turn is None:
                    lead_turn = ti
            for e in t["errors"]:
                flags.append(f"kolo {ti + 1}: CHYBA {e[:200]}")

        lead = c["handoff_markdown"] is not None
        if expect.get("lead") is not None and lead != expect["lead"]:
            flags.append(f"lead: očakávané {'áno' if expect['lead'] else 'nie'}, skutočnosť {'áno' if lead else 'nie'}")
        handoffs = [h for h in queue if h.get("log_file") == c["log_file"]]
        if expect.get("handoff_request") and not handoffs:
            flags.append("chýba request_human_handoff")
        # GDPR audit, independent of bot.py: canonical question < explicit yes in the next message < lead.
        if lead and (consent_turn is None or lead_turn is None or lead_turn < consent_turn):
            flags.append("GDPR: lead bez súhlasu (otázka → výslovné áno v nasledujúcej správe → lead)")
        if lead and consent_purpose not in (None, "sales"):
            flags.append(f"GDPR: lead so súhlasom len na účel '{consent_purpose}'")
        if lead and c["final_state"].get("consent_given") is not True:
            flags.append("lead bez consent_given")
        final_consent = c.get("consent") or {}
        actual_consent = final_consent.get("purpose") or ("refused" if c.get("consent_refused") else "none")
        if expect.get("consent") and expect["consent"] != actual_consent:
            flags.append(f"súhlas: očakávané '{expect['consent']}', skutočnosť '{actual_consent}'"
                         + (f" (nezávislý audit: {consent_purpose or ('refused' if refused else 'none')})"))
        if expect.get("handoff_request") is False and handoffs:
            flags.append("request_human_handoff, hoci sa nečakal")
        if expect.get("quote") is True and not c["quotes"]:
            flags.append("chýba úspešná cenová ponuka (quote)")
        if expect.get("quote") is False and c["quotes"]:
            flags.append("cenová ponuka, hoci sa nečakala")
        if expect.get("price_before_gdpr") and (first_quote_turn is None or (gdpr_turn is not None and first_quote_turn > gdpr_turn)):
            flags.append(f"cena až po GDPR otázke (quote v kole {first_quote_turn and first_quote_turn + 1}, "
                         f"otázka v kole {gdpr_turn and gdpr_turn + 1})")
        if expect.get("codes_any"):
            quoted = {x.upper() for q in c["quotes"] for l in q["lines"] for x in l["codes"]}
            if not quoted & {x.upper() for x in expect["codes_any"]}:
                flags.append(f"žiadny z kódov {expect['codes_any']} nie je v ponukách")
        cats = {l["discount_category"] for q in c["quotes"] for l in q["lines"]}
        if expect.get("commercial") and cats & {"single_split_sets", "single_split_units", "multi_split_outdoor", "multi_split_indoor"}:
            flags.append(f"komerčný priestor, ale v ponuke rezidenčné kategórie {sorted(cats)}")
        if expect.get("commercial") and not c["quotes"]:
            flags.append("komerčný priestor bez cenovej ponuky")
        segs = {q["segment"] for q in c["quotes"]}
        if expect.get("segment") and segs and segs != {expect["segment"]}:
            flags.append(f"segment v ponukách {sorted(segs)}, očakávané {expect['segment']}")

        # Cost (API runs): bot.py checks the cap before every call, so no conversation may pass it.
        usage = usage_from_log(run_dir / "logs" / c["log_file"])
        usd = c.get("session_usd", usage["usd"])
        ceiling = expect.get("max_usd") or (SESSION_USD_CAP if c.get("client") == "api" else None)
        if ceiling is not None and usd > ceiling + 0.005:
            flags.append(f"cena rozhovoru {usd:.3f} $ nad stropom {ceiling:.2f} $")
        if c.get("limit_reached"):
            last = "\n".join(c["turns"][-1]["assistant"]) if c["turns"] else ""
            if "limit" not in last.lower():
                flags.append("strop rozhovoru dosiahnutý, ale posledná odpoveď nie je záver napísaný kódom")

        rows.append({"id": c["id"], "turns": len(c["turns"]), "lead_expected": expect.get("lead"), "lead": lead,
                     "quotes": len(c["quotes"]), "quote_problems": len(quote_problems), "price_notes": len(price_notes),
                     "flags": len(flags), "regens": regens, "leftovers": leftovers, "soft": soft_total,
                     "tool_errors": len(tool_errors), "seconds": c["seconds"], "author": c.get("author", ""),
                     "usd": round(usd, 4), "cache_pct": round(cache_share(usage), 1), "calls": usage["calls"],
                     "capped": bool(c.get("limit_reached")), "usage": usage})
        details.append((c, flags, quote_problems, price_notes, tool_errors, handoffs))

    summary.update(quotes=total_quotes, quote_problems=total_quote_problems,
                   amounts_in_replies=total_amounts, untrusted_amounts=total_untrusted,
                   leads=len(leads), handoff_requests=len(queue))
    costs = [r["usd"] for r in rows]
    if costs:
        all_usage = {k: sum(r["usage"][k] for r in rows) for k in ("input", "output", "cache_write", "cache_read")}
        summary.update(usd_total=round(sum(costs), 4), usd_median=round(statistics.median(costs), 4),
                       usd_max=round(max(costs), 4), capped=sum(r["capped"] for r in rows),
                       cache_read_pct=round(cache_share(all_usage), 1), flags=sum(r["flags"] for r in rows))

    # ---------- report ----------
    out = ["# Klimabot eval — správa", "", f"Beh: `{run_dir.name}` · {len(convs)} konverzácií", ""]
    out += ["## Prehľad", "",
            "| konverzácia | autor | kôl | lead (očak./skut.) | ponúk | chyby v ponukách | sumy mimo quote | nálezy | regen | vystrihnuté | mäkké | chyby nástrojov | s | $ | z cache | strop |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    yn = {True: "áno", False: "nie", None: "–"}
    for r in rows:
        out.append(f"| {r['id']} | {r['author']} | {r['turns']} | {yn[r['lead_expected']]} / {yn[r['lead']]} | {r['quotes']} | "
                   f"{r['quote_problems']} | {r['price_notes']} | {r['flags']} | {r['regens']} | {r['leftovers']} | "
                   f"{r['soft']} | {r['tool_errors']} | {r['seconds']} | {r['usd']:.3f} | {r['cache_pct']} % | "
                   f"{'áno' if r['capped'] else '–'} |")
    out += ["", f"Ponuky z `quote`: {total_quotes}, nezhody s DB/politikou: {total_quote_problems}. "
                f"Sumy v € v odpovediach: {total_amounts}, z toho mimo quote/zákazníka: {total_untrusted}.", ""]
    if costs:
        out += [f"Cena: spolu {summary['usd_total']:.2f} $, medián {summary['usd_median']:.3f} $, "
                f"maximum {summary['usd_max']:.3f} $; na strope rozhovoru skončilo {summary['capped']}; "
                f"z cache {summary['cache_read_pct']} % vstupných tokenov.", ""]

    out += ["## Leady", "", "| konverzácia | meno | kontakt | obec | záujem | posledná ponuka (bez DPH) |", "|---|---|---|---|---|---|"]
    for ld in leads:
        st = ld.get("customer_state", {})
        last = (ld.get("quotes") or [None])[-1]
        out.append(f"| {by_log.get(ld['log_file'], '?')} | {ld['name']} | {ld['contact']} | {st.get('lead_obec', '–')} | "
                   f"{', '.join(ld.get('interested_in') or []) or st.get('model_selected', '–')} | "
                   f"{last['total_eur'] if last else '–'} |")
    if queue:
        out += ["", "Požiadavky na operátora (handoff_queue):", ""]
        for h in queue:
            out.append(f"- {by_log.get(h.get('log_file'), '?')}: {h['reason']} — {h['customer_question'][:120]}")

    out += ["", "## Detaily", ""]
    for c, flags, qp, pn, te, handoffs in details:
        consent = c.get("consent") or {}
        out += [f"### {c['id']} — {c['title']}", "", f"_Na kontrolu:_ {c['review']}", "",
                f"_Súhlas (server):_ {consent.get('purpose') or ('odmietnutý' if c.get('consent_refused') else 'žiadny')}"
                + (f" — „{consent.get('evidence')}“" if consent else ""), ""]
        for q in c["quotes"]:
            lines = "; ".join(f"{l['qty']}× {'+'.join(l['codes'])} {l['unit_catalog_price_eur']} € −{l['discount_pct']} % = "
                              f"{l['unit_price_eur']} € ({l['discount_category']})" for l in q["lines"])
            out.append(f"- quote ({q['segment']}): {lines} → **{q['total_eur']} €** bez DPH / {q['total_with_DPH_23pct_eur']} € s DPH"
                       + (f", rozpočet: {q['budget']['status']} ({q['budget'].get('compared_price', 'bez DPH')})"
                          if q.get("budget") else ""))
        for label, items in (("Nezhody ponuky s DB", qp), ("Sumy v odpovediach", pn), ("Nálezy", flags), ("Chyby nástrojov", te)):
            if items:
                out += ["", f"**{label}:**"] + [f"- {x}" for x in items]
        out.append("")

    (run_dir / "report.md").write_text("\n".join(out), encoding="utf-8")

    tx = ["# Prepisy konverzácií", ""]
    for c in convs:
        tx += [f"## {c['id']} — {c['title']}", ""]
        for i, t in enumerate(c["turns"], 1):
            tx += [f"**Zákazník ({i}):** {t['user']}", ""]
            for tool in t["tools"]:
                tx.append(f"> 🔧 `{tool['name']}` {json.dumps(tool['input'], ensure_ascii=False)[:300]}"
                          + (" — **CHYBA**" if tool.get("is_error") else ""))
            for n in t["notices"]:
                tx.append(f"> ⚠ {n[:300]}")
            tx += ["", "**Bot:**", "", "\n\n".join(t["assistant"]) or "_(bez textu)_", "", "---", ""]
        if c["handoff_markdown"]:
            tx += ["<details><summary>Handoff pre PM</summary>", "", c["handoff_markdown"], "", "</details>", ""]
    (run_dir / "transcripts.md").write_text("\n".join(tx), encoding="utf-8")
    for r in rows:
        r.pop("usage")
    (run_dir / "summary.json").write_text(json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=2),
                                          encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    return summary


if __name__ == "__main__":
    analyze(sys.argv[1])
