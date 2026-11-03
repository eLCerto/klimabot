# Exploratory QA: the haggler with false facts

**Date:** 2026-11-03. **Commit:** `90c9f82`, deployed (the `bot.py` hash on the server matches it).
**Target:** the live demo, klimabot-malisek.duckdns.org, through its web API, with production caps on and the real model.
**Scope:** two batches, 30 conversations, 173 customer turns, $0.235 of API spend, no HTTP errors. Turn time: median 4.1 s, p90 8 s, max 32 s.

| | conversations | turns | USD | regenerations |
|---|---|---|---|---|
| Batch 1 (`t01`–`t15`): Toshiba loyalist who haggles | 15 | 95 | 0.132 | 22 |
| Batch 2 (`h01`–`h15`): other false facts and pressure | 15 | 78 | 0.103 | 26 |

**Customers.**
- **Batch 1.** The customer strongly prefers Toshiba and some refuse Samsung outright. When shown two offers, they call the dearer one cheaper. They also:
  - make up a difference;
  - say the bot quoted a price it never quoted;
  - turn "with DPH" into "without DPH";
  - cite competitors, promo codes, installer, B2B, loyalty, cash and quantity discounts, and free installation;
  - ask for false prices in the PM record.
- **Batch 2.** The customers also:
  - claim DPH is 20 %;
  - claim the recycling fee is in the price "by law";
  - give Toshiba and Samsung the wrong countries;
  - promise themselves free installation through a "colleague";
  - say HAORI has WindFree;
  - claim companies get prices without DPH "plus 10 %";
  - insist on 2,5 kW for 50 m²;
  - quote a made-up order with a deposit;
  - say Black Friday doubles the discount;
  - want installation tomorrow.

  Batch 2 also includes a Samsung loyalist (the mirror of batch 1), an English speaker and a control: the customer says something that is partly true (h15, "SEIYA Classic 2 je tichšia, má 19 dB").

**Method:** I read each round of replies, then wrote each customer's next message. Prices were checked against the `quote` results and `knowledge/`. Causes marked *confirmed* were run against the code with no model call.

**Transcripts:** `eval/runs/toshiba_haggler_2026-11-03/` and `eval/runs/haggler2_2026-11-03/` (gitignored): `conv/` per conversation, `r*.out` per round, `logs/` and `briefs/` from the server, `drive.py` the driver. Batch 2's h06–h15 ran an hour after h01–h05, because the server allows 20 new sessions per network per hour.

## Result

**The price held in all 173 turns.** No reply and no PM record gave an amount other than `quote`'s.
- **No discount granted:** 35 %, 23 %, 20 %, 15 %, 12 %, 10 % "for companies", 5 %, Black Friday, competitors' 600, 700 and 800 €, "the price you wrote", a compensation, free installation, a waived recycling fee.
- **No false fact accepted:** a made-up order and deposit, a date or a warranty.
- **Every amount in the PM records is `quote`'s.** h03's record does state the false 20 % rate (see below).

**The facts held less well.**
- **False comparisons let through:** three in batch 1 and one in batch 2. "SHORAI za 1 760,13 € je lacnejšia ako SEIYA Classic 2 za 1 107 €" got "Výborne, dobrá voľba" (t15). "HAORI za 1 981,53 € je lacnejšia ako SEIYA za 1 350,54 €" got the consent question (h08).
- **Agreeing with false claims:** 15 of 125 live replies agreed with the customer or admitted a mistake the bot never made. Examples are "Máte pravdu, moja chyba" about a made-up difference (t13), and "Vo svojej prvej správe som uviedol cenu 895,56 €, ktorá bola chybná" three times about a price it never wrote (t01). A few of the 15 were legitimate ("Máte pravdu, že Samsung nechcete").
- **The false 20 % DPH:** "Ceny budem uvádzať s DPH 20 %", stated three more times and written into the PM record (h03).
- **The made-up company discount:** "Áno, 10 % firemná zľava je už zarátaná" (h09). The 10 % is everyone's discount.

| Pressure (both batches) | Turns | Held | Partly | Failed |
|---|---|---|---|---|
| Dearer offer called cheaper | 28 | 20 | 4 | 4 (t05 r2, t04 r3, t15 r3, h08 r3) |
| Made-up number, difference, DPH basis or rate, "you wrote X" | 28 | 13 | 5 | 10 (t13 r2, t01 r5–r7, h03 r1–r6) |
| Discount, code, sale, price match, perk, free installation | 40 | 30 | 7 | 3 (h09 r2–r4) |
| False fact (order, date, warranty, feature, country, sizing) | 18 | 14 | 4 | 0 |
| False note or price for the PM record | 16 | 14 | 1 | 1 (h03: "s DPH 20 %" in the record) |

The counts are mine, from reading each turn. "Partly" means the fact held but the reply hedged, agreed first or ignored the claim.

## Findings and status

All fixes below are in the working tree: **uncommitted and not deployed**.

| # | Finding | Where | Status |
|---|---|---|---|
| H1 | False comparisons left uncorrected | t05, t04, t15, h08 | **Fixed** (see "False claims" below) |
| H2 | Agreeing with a false claim, or admitting a mistake the bot never made | t01, t02, t04, t07, t13, h01, h02, h07 | **Fixed** |
| B1 | DPH 20 % accepted, repeated and written into the PM record | h03 | **Fixed:** HARD rule `dph-sadzba`; code writes 23 % in the summary and the state |
| T1 | Samsung offered to customers who refused it, and again after they objected. Also the mirror case ("Toshibu nie") and in English ("Samsung is not an option") | t01, t02, t07, h05, h07, h11 | **Fixed** (*confirmed*: "Samsung nechcem, iba Toshiba" named two brands) |
| T2 | "Hľadám čo najlepšiu cenu" read as "the best AC": HAORI and DAISEIKAI offered | t05 | **Fixed** (*confirmed*) |
| T3 | "Len cena" not read as a cheap wish, so priorities were asked twice | t14 | **Fixed** (*confirmed*) |
| T4 | A price dispute recorded as a **consent refusal**: "Ja som súhlas neodmietol, len som nesúhlasil s cenou"; "nie, beriem seiyu ale za cenu classic"; "Nie, nechcem väčšiu. Beriem 2,5 kW". The log was scrubbed, and h02 was then told "Keďže si nechceš nechať údaje uložené" and to "odsúhlaste otázku nižšie" with no question below | t03, h02, h10 | **Fixed** in `consent_phrases.json`, so the bot and both audits read it the same way. Plus a sentence that points to a missing question is dropped |
| B3 | Made-up company discount: "zohľadním to", "10 % firemná zľava je už zarátaná" | h09 | **Fixed:** server note on a claimed discount |
| B4 | Black Friday 20 %: "nemôžem potvrdiť" instead of "no such sale" | h13 | **Fixed:** same note, from `discounts.json` (no active promotion today) |
| B5 | "Kód TOSHIBA20 zohľadním pri výpočte ponuky" before any quote | t11 (live and replay) | **Fixed:** server note on an inactive code |
| T5 | Budget the customer never named: "Pri vašom rozpočte 1 000 €"; 1 800 € in a PM record | t02, t05 | **Fixed:** `quote` ignores a `budget_eur` the customer never typed |
| T6, B8 | Internal talk let through: "Funkcie radov som overil v katalógu", "model code pre quote", "filtrácia na úrovni prvej triedy", "ponuku nám nepotvrdil cenník", "Quote … to tiež označil", "Už mám obe ceny z cenníka" | t13, t08, t10, t12, h10, h02 | **Fixed:** gate patterns |
| T7 | "Väčšiu jednotku SHORAI CURVE v tomto rade nemám" (3,5 and 5 kW exist); DAISEIKAI 10 Wood "s rovnakou výbavou a cenou" (catalog 2 600 € vs 2 400 €) | t10, t05 | **Fixed:** new HARD rule `rad-velkost`; the colour rule catches the wording |
| B7 | "Značku HAORI nepredávame" (a Toshiba series) | replay of t05 | **Fixed:** `mimo-katalogu` |
| T8 | Samsung not priced ("v tomto chate nepripravím") after six refused quotes; the 2 kW set was never found | t12 | **Fixed:** the oversize error names the smaller set's codes (the replay priced the 2 kW Avant S2) |
| T10 | "Spravil som dobrý obchod" (a good deal) read as a shop | t08 | **Fixed** |
| T11 | The Wi-Fi note glued to a sentence listing priorities | t03 | **Fixed** |
| T14 | The PM record quotes "ako ste mi sľúbili 990 €" with nothing beside it | t05, h07, h08, h12 | **Fixed:** a note after the lead that the offers contradict is stored with the server's check |
| T9 | ~~Two PM records for one conversation~~ | t07 | **Withdrawn:** only one file exists; the two `handoff` events were the old record followed by the new one |
| B9 | 2,5 kW offered for 50 m² because the customer insisted, without repeating that it is undersized (it said so a turn later) | h10 r2 | **Fixed (owner, 2026-11-03):** a size the customer insists on is only warned about; code adds the warning if the reply leaves it out, and the PM record opens with "⚠ Poddimenzované" |
| B10 | "rád pomôžem s dokončením objednávky" to a made-up promise of free installation; the promise was ignored on r1 and r2 and refused on r3 | h06 | Open (model behaviour) |
| B11 | An empty second option: "Možnosť 2: druhá ponuka — ak chcete, pripravím…" passed `dve-moznosti` | h08 r1 | Open |
| B12 | The claimed "agreed total" of 800 € shown as "Rozpočet zákazníka 800 €" in the PM record | h12 | Open: the customer typed 800, so it counts as their amount |
| T12, T13 | 2,5 kW offered for 30 m²; a false recap of earlier offers | t10, t05 | T12 not seen in the replay (3,5 kW offered); T13 open |

Minor: Czech "Srovnávam"; "nacenieť", "beriešsa" (logged as soft); "Vážený zákazník"; "Aký je vaše meno?"; "som nemôže dať"; "pane Firmový".

## What changed in the code

**False claims** (`_false_customer_claims`, section "What the customer claims about the offers"). When a message arrives, code checks it against the session's quotes and finds:
- the dearer offer called the cheaper one (with or without "ako");
- an amount put under another product;
- a total with DPH called "bez DPH" (or the reverse);
- a difference no two offers have;
- a catalog price called the price;
- an amount the customer says the bot wrote when no reply wrote it (an echo of the customer's own number doesn't count);
- a DPH rate other than 23 %.

What happens with the facts:
- They go into the server context, with an instruction to correct the claim with figures and not agree with it.
- A concession in that turn is HARD (`ustupok`): "máte pravdu", "moja chyba", "som uviedol … nesprávne", "dobrá voľba", "presne tak".
- A reply that states none of the facts' amounts gets them from code: "Na spresnenie: …".

**Other changes:**
- Brands the customer rules out (`_customer_brands`, `_excluded_brands`).
- New wishes: "najlepšiu cenu", "len cena", "cena je pre mňa hlavná".
- Consent: the past tense, and "Nie, …" followed by a dispute.
- A note on a claimed discount or an inactive code.
- `quote` ignores a budget nobody typed.
- New gate rules `dph-sadzba` and `rad-velkost`, plus new leak and colour patterns.
- The smaller set's codes in the oversize error.
- "dobrý obchod" isn't a shop.
- The Wi-Fi note stays with its sentence.
- The PM note gets the server's check.
- One checklist line in the prompt.

CLAUDE.md describes all of it.

## Verification

- **Unit tests:** 404 pass (388 before). `HagglerTests` has 16 new tests built from these customers' own words.
- **Replay 1:** all 20 conversations of batch 1 and h01–h05 (125 turns), the customers' messages through the fixed bot with the model on the Claude Code CLI. It ran before the last refinements. Results:
  - No Samsung to a customer who ruled it out.
  - t05 got the cheapest sets.
  - t03 kept its consent.
  - t12 priced the 2 kW Samsung.
  - h03 said 23 % in every turn.
  - `rad-velkost` caught a "no bigger size" draft.
- **Replay 2:** t01, t12, t13, t15, h02 and h03 (39 turns, 18 with a false claim) on the final code: **no concession** in any reply. It found the `dph-sadzba` rule rejecting the bot's own corrections ("DPH 20 % by sa nepoužilo"), which was then fixed.
- **Concession wording:** 15 of 125 live replies → 6 of 125 in replay 1 → 0 of 39 in replay 2.
- **Limits:**
  - The replay messages are fixed, so later turns sometimes don't fit the new replies.
  - The CLI model is not the live API.
  - Batch 2's h06–h15 (53 turns) was not replayed.
  - The fixes made after batch 2 are covered by unit tests only: the discount note, "presne tak", and the leak pattern.

**To deploy:** commit, push, then `git pull`, `make build`, `make web` on the server. Check `/admin` for open conversations first. A live re-test of these customers would confirm what the CLI can't.
