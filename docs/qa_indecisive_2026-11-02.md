# Exploratory QA: the customer who keeps changing their mind

**Date:** 2026-11-02. **Commit:** `1ebaf4b`, deployed (the `bot.py` hash on the server matches the checkout).
**Target:** the live demo, klimabot-malisek.duckdns.org, through its web API (`/api/session`, `/api/chat`, `/api/handoff`, `/api/state`, `/api/end`), with production caps on and the real model.
**Scope:** 10 conversations, 91 customer turns, 28 regenerations, $0.20 of API spend. Turn time: median 4.8 s, p90 20.6 s, max 36.6 s.

**Method:** I read each round of replies, then wrote each customer's next message, so the customers reacted to what the bot said. Claims were checked against `knowledge/`. Causes marked *reproduced* were run against the code with no model call.

**Transcripts:** `eval/runs/indecisive_2026-11-02/` (gitignored): `conv/` per conversation, `logs/` from the server, `drive.py` the driver.

## Status after the fixes

All findings were worked on the same day, uncommitted and **not deployed**. 371 unit tests pass (326 before), 45 of them new.

Direction metrics on 31 scenarios (4 new, from these customers), 2 repeats, through the CLI, on the final code:

| metric | `1ebaf4b` | after |
|---|---|---|
| policy correct | 100 % | 100 % |
| final OK | 100 % | 100 % |
| regenerations per turn | 0.146 | 0.034 |
| calls per turn | 1.81 | 1.87 |
| on target | 98 % | 96 % |
| repeats agree | 92 % | 88 % |

The two lower rows are the metric's reader, not the bot: I read all five off-target turns and each reply is right. Four end on a list with no "?", which the reader takes for an answer. The scenario sets differ, so the columns compare only roughly.

The ten conversations were replayed with the customers' own messages through the real model on the CLI. The messages are fixed, so they don't react to the new replies, and some later turns no longer fit. d07, d09 and d10 ran on the final code; the other seven ran just before the last fixes (the "reason, not condition" rule, the cheap-wish word, the no-amount rule, the salon note). Across the 91 turns no reply blamed the system, named a tool or came in English. Transcripts: `eval/runs/indecisive_2026-11-02/replay_after/`.

| Finding | Status | Evidence, or what remains |
|---|---|---|
| I01 | Fixed for the seen wording | d07 gets a price on turn 2 instead of 8, and d09 prices both rooms on turn 4 instead of 7. d01, d06, d08 and d10 read the right rooms. **Limit:** code recognises the wordings it knows; the rest stays as before |
| I02 | Fixed | The false promise is gone. A take-back gets the canonical question; a yes clears the flag. **Needs the DPO**, see below |
| I03 | Fixed | Override runs after a refusal; repeats count towards the cap |
| I04 | Fixed for the seen wording | No such reply in the replay. A new wording can still pass |
| I05, I15, I16 | Fixed | Reproduced cases covered by tests |
| I06 | Fixed | Regenerated, and replaced if it survives |
| I07 | Fixed | d03, d06, d10 are no longer told they chose |
| I08 | Fixed | Offer moves with no amount regenerate with a tool |
| I09 | Fixed | **Found by the replay:** "čo najnižšia cena", the bot's own priorities option, wasn't read as a cheap wish |
| I10 | Fixed | "Tichší" needs figures. **Second cause of d08:** "Première" with the accent matched no series |
| I11 | Fixed | Noise is two named figures |
| I12 | Fixed | Code reads a return to a quoted model. A size change still needs the model to update the state |
| I13 | Partly | One line in the checklist. Nothing checks it |
| I14 | Fixed | A note on the sales moves. Not on complaints, which already collect the contact |
| I17 | Partly | No kW on discovery moves. The sizing thresholds stay an owner question (F23) |
| I18 | Fixed for the seen wording | `klimabot_sk.txt` got four words |

**Owner decisions:** the consent path after a withdrawal follows the rule for refusals (2026-11-02), but it is a data-subject right, so the DPO should approve it. Two options at one price (AR35 and AR30, F19) are still offered, as in d05.

## Re-test on the real API, after the deploy

**Commit:** `6bb4076`, live. **Scope:** the same ten customers on the live demo, new messages written round by round: 61 turns, $0.104, no HTTP errors. Turn time: median 4.1 s, p90 11.6 s, max 31.4 s.

**Transcripts:** `eval/runs/indecisive_2026-11-02/live_after/`.

| | live, before | live, after |
|---|---|---|
| USD per customer turn | 0.0022 | 0.0017 |
| Repeated refused quotes | 55 | 5 |
| Regenerations per turn | 0.31 | 0.28 |
| Worst turn | 36.6 s | 31.4 s |

**Regenerations stay high:** 0.28 per turn live against 0.034 on the CLI. The CLI metrics don't predict them, so the 0.146 to 0.034 improvement above doesn't carry over to production.

**Confirmed live:** a dropped room leaves the offer on the first message (d01, d06, d10) and comes back when asked (d01). "Žiadny salón" gets a price at once (d07). "Čo najnižšia cena" leads with the separate sets (d10). A hesitant customer isn't told they chose (d03). A withdrawal taken back asked the canonical question, and the yes removed NEKONTAKTOVAŤ (d04). A return to a quoted model reaches the brief by code (d01, d04). The GDPR audit passed 5 of 5, with 0 violations. No reply came in English.

### New findings

| ID | Sev | Finding | Conversation | Cause |
|---|---|---|---|---|
| R1 | P0 | A wrong price: DAISEIKAI 10 Wood 2.5 kW at €2,656.80, the White price. It costs €2,878.20 | d03 t4 | code read: `_quote_identity` drops White / Black / Wood, so `cena-iny-produkt` sees one series |
| R2 | P0 | Comparisons backwards: a €3,990.74 multi-split "lacnejší o 1 304,05 €" than €2,686.69 sets, and "drahší o 9,96 €" than a €4,000.70 one | d06 t5 | code read: `_wrong_comparisons` needs two names in the clause; "tento variant… oproti X" has one |
| R3 | P1 | A wrong difference: "lacnejšie o 895,57 €" next to "882,27 € drahšie" in one sentence. 895,57 is one set against two | d06 t2 | observed: any quote difference passes provenance |
| R4 | P1 | Salon: no price on the first turn, while the note said not to price residential units | d07 t2 | code read: `_suggested_sets` has no commercial check, so code's picks contradict the note |
| R5 | P1 | False: "Cena… zahŕňa aj recyklačný poplatok" | d03 t2 | `_INCL_FEE_RE` knows "vrátane", not "zahŕňa" |
| R6 | P1 | Leaks: `recycling_fee_per_unit`, "Tu systém kontroluje veľkosť vonkajšej jednotky" | d07 t4, d10 t5 | observed: no rule for field names; the wording isn't known |
| R7 | P1 | Price still put off: "Pred cenou musím overiť kompatibilitu", "cenu ešte nemám overenú", no price after a refused cassette | d06 t4, d10 t5, d07 t6 | observed: `odpoved` and `pokracuj` moves, and wordings the rule doesn't know |
| R8 | P1 | Design wish lost: "skôr dizajn" got AR35 and Classic 2, and "podklady neobsahujú… farebné varianty", which is false | d02 t2, t3 | observed: "nestojí majland" wins as a cheap wish |
| R9 | P2 | Garbled and false: "s tichším chodom o niečo menej výkonnú" | d05 t2 | code read: `_unbacked_comparatives` exempts "ak" and needs a name |
| R10 | P2 | The brief keeps 20 m² after "25 m2, nie 20" | d08 | code read: the model's `place_m2` wins over the customer's words |
| R11 | P2 | Amounts: "728.1 €", "1217.7 €", "2520 €" | d07 t3, t4 | code read: `_SK_EUR_RE` needs two decimals |
| R12 | P2 | The same two quotes three times in one turn | d10 t4 | observed: repeats are guarded for refused quotes only |
| R13 | P3 | Invented: "môžem vás prepojiť s predajcom", "jednoduchší na montáž", "projektový manažér môže ukázať reálne kusy", "príjemné leto" in November | d05, s1, d02, d09 | observed |

In R1 and R2 the customer caught the error and the bot admitted it. A customer who doesn't check would keep the wrong figure.

### Status of R1–R13 after the fixes

**Not deployed yet.** Checked three ways: 388 unit tests (17 new), all 59 live replies through the new gate with their quotes re-run locally (no model), and d02, d03, d05, d06, d07, d08 and d10 replayed through the CLI model (43 turns). The replay ran before two narrowing changes to `farba` and `porovnanie-smer`, which only remove false positives. It wasn't repeated on the real API, and the CLI doesn't predict live regenerations.

| ID | Status | What changed |
|---|---|---|
| R1 | Fixed | `_quote_identity` keeps colours per line. The replay gave the wood set its own price, and d03 t6 corrected the earlier figure |
| R2 | Fixed | A clause naming one product is read through the quote pair at that difference. `quote` also says the comparison in words (`reads`) |
| R3 | Fixed | New HARD rule `porovnanie-suma` |
| R4 | Fixed | No code picks for a salon or practice. d07 t2 priced under-ceiling sets on the first try |
| R5 | Fixed | "zahŕňa aj…" and "…je v cene" are rewritten |
| R6 | Fixed | Any snake_case name is a leak, and so is "systém kontroluje / navrhuje" |
| R7 | Fixed for the seen wordings | New wordings, and "čo keby…", "koľko je nástenná" are `nova-ponuka`. d07 t6 now says why a cassette doesn't fit |
| R8 | Fixed | "Skôr dizajn" beats a cheap ceiling. d02 t2 offered HAORI and a black Samsung, priced |
| R9 | Fixed | A wish exempts its own clause only; "druhá" counts as a name |
| R10 | Fixed for the size line | The model's own note can still say the old size (d08: "Poznámky z rozhovoru") |
| R11 | Fixed | One decimal, a dot and no thousands space are normalised |
| R12 | Fixed | A successful identical `quote` doesn't run again in a turn |
| R13 | Fixed for the seen wordings | Only the phrases seen; the model can invent others |

**New in the replay:** d07 t6 told an office customer that wall sets don't suit an office, "preto ich necením". `quote` doesn't refuse them there, so this is a false limit from the model. Not fixed.

**Regenerations:** the replay shows no fall: 13 rule hits in 43 turns, and 9 of them came from five new or wider rules (`cena-iny-produkt`, `farba`, `porovnanie-bez-cisel`, `porovnanie-smer`, `porovnanie-suma`). These fixes catch wrong replies; they don't lower the 0.28 per turn.

## Verdict (before the fixes)

**The bot isn't ready for this customer.** It handles a change of mind only when the model happens to. Code reads every message the customer ever wrote and adds it up, so nothing can be taken back. That one design fact causes the worst results below. The legal and pricing guarantees held; the sale didn't.

| Conversation | Customer's behaviour | Outcome |
|---|---|---|
| d01 | Bedroom, maybe living room, then only bedroom | Said "only the bedroom" twice, heard on the third try. Lead OK |
| d02 | Samsung or Toshiba, price or design | Refused, reconsidered, lead OK |
| d03 | Cheapest, then the best, then back | Called "chosen" twice. Price given only at turn 8 |
| d04 | Cheap, dear, cheap, withdraws, takes it back | **Told the PM will call; the brief says do not contact** |
| d05 | Lets the bot choose, haggles, changes room | Lead OK. Chose Toshiba on a false "quieter" |
| d06 | Three rooms, two, three again | Dropped room ignored once. Crash in a lookup |
| d07 | Home, office, salon, office, home, salon, office | **No price for six turns.** Reached the spend cap |
| d08 | Black, any colour, budget, new size, lead, changes | Lead OK, but the brief has two rooms that don't exist |
| d09 | Fan or AC, one or two units, buys nothing | Seven turns to the price of one bedroom |
| d10 | Vague, then cheapest, then one outdoor unit | "Cheapest" got a €5,874 system with a fourth room |

## Findings

| ID | Sev | Finding | Conversations | Cause |
|---|---|---|---|---|
| I01 | P0 | Nothing the customer says can be taken back | d07, d06, d01, d10, d08 | reproduced |
| I02 | P0 | A taken-back withdrawal: bot promises contact, brief forbids it | d04 | observed, code read |
| I03 | P0 | The override can't run after a refusal; the refusal cap misses repeats | d07, d03 | code read, live evidence |
| I04 | P0 | The bot blames "the system" to customers | d07, d09, d03, d06 | reproduced |
| I05 | P1 | `lookup_product` crashes on a bare size | d06 | reproduced |
| I06 | P1 | Reply in English to a Slovak customer | d07 | observed |
| I07 | P1 | A hesitant sentence is read as a choice | d03, d10, d02 | reproduced in part |
| I08 | P1 | A price question is answered with an offer to price it | d09, d03, d06, d08, d10 | observed |
| I09 | P1 | False "cheapest"; cheap wishes ignored | d10, d01 | observed |
| I10 | P1 | False comparisons the customer relied on | d05, d02, d06, d08 | observed |
| I11 | P1 | Outdoor noise shown as indoor | d04, d02 | data confirmed |
| I12 | P1 | The brief goes stale when the model skips `capture_lead` | d04, d08 | observed |
| I13 | P2 | Invented explanations of the bot's own mistakes | d10, d02, d09, d07 | observed |
| I14 | P2 | "I want a person" isn't acted on | d07 | observed |
| I15 | P2 | Series lookups find nothing for "Samsung WindFree 2,5" | d02, d05 | reproduced |
| I16 | P2 | The chosen series is swapped in a later offer | d06 | observed |
| I17 | P2 | Spoken sizing still inconsistent | d05, d08 | observed |
| I18 | P3 | Language polish | various | observed |

## P0

### I01. Nothing the customer says can be taken back

`_fit_check` searches `_all_user_text()`, and `_customer_m2()` and `_room_sizes()` collect every number from every message. A retraction just adds more text.

| Customer wrote | Code still reads |
|---|---|
| d07: "Tak nie, žiadny salón" and three later denials | A salon, so `quote` refuses every wall unit |
| d06: "detskú vynecháme, stačí spálňa a obývačka" | `[13, 11, 24]` |
| d01: "Zabudnite na obývačku. Len spálňa 14 m2" | `[14, 28]` |
| d08: "obývačka má vlastne 25 m2, nie 20" | `[20, 25]`, and the brief says "20 m² + 25 m²" |
| d10: "možno 60 m2", then three rooms of 25, 15, 12 | `[12, 15, 25, 60]`, a fourth room |
| d10: "Detskú nechám tak, len obývačka 25 a spálňa 15" | `[12, 15, 25, 60]` |

- **d07:** the customer asked for a price on turns 2 to 7 and got none. It worked on turn 8 only because the model passed `override_reason` on its first call (see I03).
- **d10:** the multi-split was priced with units for 2, 2, 2.5 and 6.5 kW: €5,873.74 as the answer to "čo najlacnejšie". Asked "kde ste zobrali štvrtú?", the bot said it wasn't a mistake.
- **d10, later:** "tento set je pri 60 m² poddimenzovaný" appears twice, for a customer who is now cooling two rooms.
- The model often handles a dropped room itself. d06 turn 3 and d01 turn 4 came out right, but only after the customer repeated it.

### I02. A withdrawal taken back: the bot promises contact, the brief forbids it

d04 wrote: "zrušte to celé a vymažte moje údaje. Počkajte, nie, nechajte to tak, beriem tú bielu AR35." Code treated it as a withdrawal. That's the safe reading, and I'd keep it. The next message was: "Nie nie, nerušte to! … nech sa mi ozvú."

- **Bot:** "Údaje sú odovzdané, ako ste si želali." Then, asked directly: "Vaša žiadosť je zaznamenaná a údaje sú odovzdané projektovému manažérovi."
- **Brief:** "⛔ NEKONTAKTOVAŤ".
- **Record:** the retraction is stored nowhere. `_note_after_lead` skips withdrawn leads (`bot.py:7996`), and `reconsider_re` only applies after a refusal.

The customer waits for a call that won't come. No consent path exists after a withdrawal. It should work like the refusal path: the canonical question, an explicit yes, and an operator clearing the flag. Until then, code should answer that the case stays with an operator.

### I03. The override can't run after a refusal, and the refusal cap misses repeats

The guard's key is the items alone (`bot.py:8569`), so the same quote with `override_reason` counts as a repeat, and the tool never runs. `_fit_check`'s documented escape is therefore closed in any turn where the plain call came first.

- **Evidence:** d07 turns 4 to 7 sent the override after a refused plain call and all were blocked. Turn 8 sent it first and it passed. d03 turn 8 did the same.
- **Cap:** `refused_quotes` is a set of keys, so two refused options repeated stay at 2, and `TURN_MAX_REFUSED_QUOTES` (5) never fires. Only `TURN_MAX_TOOL_CALLS` stops it.
- **Cost:** d07 made 54 `repeat_refused_quote` calls, and its $0.055 is 2.5 times the next conversation.

### I04. The bot blames "the system" to customers

12 of 91 replies did this, and `_INTERNAL_LEAK_RE` matches none of the four strings I tested.

| Conversation | Shown to the customer |
|---|---|
| d07 t4 | "Quote odmieta obe zostavy, lebo systém stále vidí priestor ako salón… Chybu rieši systém a nie vaše údaje." |
| d07 t5 | "tento údaj sa mi nepodarilo zrušiť" |
| d07 t9 | "túto položku sa mi nedarí vyčistiť" |
| d07 t10 | "Lookup potvrdil iba veľkosť 5,0 kW." |
| d07 t6 | "Both quote requests keep being rejected by the system" |
| d09 t6 | "systém zostavu 2,5 kW pre 12 m² odmieta", which never happened |
| d06 t6 | "z ponuky, ktorú mi vrátil systém, no neviem ju presne uviesť" |

## P1

### I05. `lookup_product` crashes on a bare size

*Reproduced:* "Toshiba multi-split 2,0" raises `RecursionError` at `bot.py:2098`. `_SIZE_KW_RE.sub` strips "2.0 kW" but not the bare size, so `_type_units` calls itself with the same text. The tool returned "maximum recursion depth exceeded". "Toshiba multi-split 2.0 kW" works. d06 turn 5 took 36.6 s and gave no price.

### I06. Reply in English to a Slovak customer

d07 turn 6 came out fully in English after two regenerations. `_session_language()` returned `sk`, so the model flipped on its own. The gate catches Czech but has no rule for English in a Slovak session. The customer had to ask for Slovak. The trigger may be specific to this stuck turn.

### I07. A hesitant sentence is read as a choice

- **d03 t2:** "Vlastne nie, rozmyslel som si to, chcem tú najlepšiu čo máte" is `kontakt` (*reproduced*). The bot replied "Vybrali ste si Toshibu DAISEIKAI 10" with the consent question. Only one series was offered.
- **d03 t6:** the customer asks for wood at 3.5 kW. The bot says "Vybrali ste si" and "Cenu zatiaľ neuvediem", and asks for consent first.
- **d10 t9:** "Beriem Luzon. Vlastne nie." gets "Vybrali ste si zostavu" and the consent question, for the system the customer had just rejected.
- **d02 t4:** a consent request on the `odpoved` move. `_drop_contact_requests` covers only the offer moves.

"Vybrali ste si" is the failure the customer sees. d03 had to say "ja som si ešte nič nevybral".

### I08. A price question is answered with an offer to price it

- **d09:** bedroom price asked on t3, t4, t5 and t6, shown on t7. The moves on t3 and t6 were `odpoved`, and no quote was tried on t6. The model kept trying a 3.5 kW set, and the error always spoke of 20 m².
- **d08 t2:** an offer move with no quote: "Nacenil som pre vás setu AR35" and, three lines on, "lebo som ju ešte nenacenil".
- **d06 t6:** "Ak chcete presnú sumu, pripravím ju", after the customer asked for the cheapest.
- **d10 t7:** the quote ran, the amount was cut, and the reply says "uvediem len z cenovej ponuky". `_offer_prices_text` only runs on offer moves, and this was `odpoved`.
- **d10 t10:** "Dve samostatné?" gets "Cenu takejto zostavy som zatiaľ nepripravil".

### I09. False "cheapest"; cheap wishes ignored

- **d10 t10:** "Najlacnejšia je Toshiba SEIYA Classic 2" at €2,645.73. Two AR35 sets for those rooms cost €1,791.13 (d06's quote for the same two sets).
- **d10 t4:** "Čo najnižšia cena" got a €5,045.71 WindFree Premiere system. `_cheapest_room_sets` should have led, and the customer had to complain.
- **d01 t2:** "nie drahá" got SHORAI CURVE and Premiere Plus at €3,564 and €3,854.

### I10. False comparisons the customer relied on

- **d05 t2:** SHORAI CURVE "tichší a výkonnejší" than AR35. It has 2.5 kW against 2.6 kW and 22 dB against 20 dB indoors. The reply's own figures contradict it. **The customer chose Toshiba "keď je tichšia"** and later caught it.
- **d02 t4:** the same "tichšia" claim, unprompted, pushing a set €947.59 dearer.
- **d06 t2:** the multi-split has "vyššie výkony vnútorných jednotiek". It has 2, 2 and 2.5 kW against 2.6 kW.
- **d08 t4:** "SHORAI CURVE Black lacnejší než WindFree Première Black… o 61,20 €". It's dearer (€1,498.50 against €1,437.30). `porovnanie-smer` passed it. My local test of the rule was inconclusive, so the cause isn't isolated.

### I11. Outdoor noise shown as indoor

`sound_pressure_dB: "20/55"` in `rac.json` is indoor / outdoor. d04 t1 says "20 dB(A) na minime a 55 dB(A) pri plnom výkone". d02 t3 says "20 až 55 dB(A) podľa režimu". In d04 the customer asked for a quiet child's room. d07 t9 (AR35) and d06 t7 (SEIYA Classic 2) also said the figures were missing, though the data has them and d10 quoted the Classic 2's.

### I12. The brief goes stale when the model skips `capture_lead`

`_refresh_lead_brief` only reacts to a new `quote`, so a switch to an already-quoted model depends on the model.

- **d04 t4:** the customer switched to Premiere and was told the PM gets the change. The brief still marked AR35 as "variant, ktorý si zákazník vybral". The change was only in the word-for-word note.
- **d08 t9:** "Záujem" says Avant 2.0 kW "finálna voľba", while the last quote is 2.5 kW, and the size reads "20 m² + 25 m²".
- **Worked:** d01, d05 t9 and d08 t7, where the model called `capture_lead`.

## P2 and P3

- **I13. Invented explanations.** d10: "Štvrtú jednotku sme nepridali omylom". d02: "Samsung tam bol pôvodne len preto, že ste sa spýtali na Toshibu", though the customer opened with Samsung. d07 t11: "Tieto sumy platia pre byt", and panel and controller "sú súčasťou ponuky".
- **I14. "Chcem hovoriť s človekom" (d07 t6, t7).** Twice in the same message as a price request, and the customer got only the e-mail address. Nothing offers the PM callback. The first message also logged `jailbreak_suspected` for "Zabudnite na všetko čo som písal predtým", a harmless false positive.
- **I15. "Samsung WindFree 2,5" finds nothing** (*reproduced*), though it's the name customers use. d02 t2 then offered two Toshibas to a customer who opened with Samsung.
- **I16. d06 t9.** The customer chose Classic 2, and the offer swapped in SEIYA. `_fix_wifi_claims` added "iba s voliteľným Wi-Fi modulom za príplatok" to a line whose price includes the modules. t8 said the module has no price; t9 gave €115, the catalogue figure before discount.
- **I17. Sizing (F23 still open).** d05 t1: "okolo 2,5 kW" for 16 m² on a discovery move. d05 t8: "okolo 2,5 kW" for 12 m². d08 t8 tells the customer the "1 kW na 10 m²" rule.
- **I18. Language.** "Vaše rozpočtu" (d08), "voveľkosti" (d03), "nacenením ho" (d04), "táto variant" (d08), "4 775,4 €" (d10), the orphan "Pani Testová." (d04 t4), "Osobne by som vybral" and "pripravím záväznú ponuku" (d10).

## What worked

- **GDPR audit:** 5 of 5 handovers OK, 0 violations. Phone and e-mail stayed masked before consent, and "súhlas zatiaľ nedávam" recorded nothing.
- **Refuse, then reconsider (d02):** code asked the canonical question and the next yes counted.
- **Spend cap, first test on the real API (d07):** code wrote the landing at $0.055 without a model call. `turn_final_call` fired five times. The daily budgets were never reached, so they weren't tested.
- **Money:** no invented amount in 91 turns, no installation price under pressure, no extra discount for the 15 % haggle. The budget without DPH was compared correctly (d08).
- **Honest correction:** d05 t4 admitted the error when challenged.
- **Leaving:** d03 and d09 got no pressure. **Override:** d03's explicit "chcem rezervu" priced the 3.5 kW set.
- **Notes after the lead:** "volať po 17:00" reached the brief (d02).
- **A flip back:** d06 "všetky tri izby" worked, and d07's salon on turn 10 got under-ceiling units priced with a controller.

## Suggested fix order

1. **I05:** one line, a crash.
2. **I03:** add `override_reason` to the key, and count repeats towards the cap.
3. **I02:** stop the false promise, then decide the path after a withdrawal.
4. **I01:** the big one. Read the room and place from the latest statement, or let `update_customer_state` hold the current values and have code trust them over old text. Add a test per row of the table above.
5. **I04, I06:** gate rules for "systém odmieta", tool names and English in a Slovak session.
6. **I07, I08:** treat "vlastne nie" and a new size or colour as not a choice; no "Vybrali ste si" unless code agrees; a price question stays an offer move.
7. **I12:** refresh the brief from code when a customer names another quoted model.

## Limits of this run

- **One run per conversation.** Findings show what can happen, not how often.
- **API only:** no browser, so cards, buttons and the UI weren't seen. `/api/end` was called like a closing tab.
- **Made-up customers, one network.** The per-network limits were never reached.
- **Left on the server:** five test leads (Testová, Testovič, Skúška, Skúšobný, Test) in `leads.jsonl` and `handoff_records/`. They show in `/admin` and were not deleted.
- **Nothing in the code was changed.**
