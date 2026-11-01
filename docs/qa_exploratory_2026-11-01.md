# Exploratory QA: Klimabot on Haiku 5.5

**Date:** 2026-11-01. **Commit:** `4e6f78c` (branch `pythonise-bot`).
**Model:** `claude-haiku-5-5`, confirmed on all 295 calls logged in `cli_calls.jsonl`.
**Scope:** 38 conversations, 125 customer turns, 22 regenerations. Turn time: median 14 s, p90 46 s, max 141 s.

**Method:** live sessions through the real bot pipeline (`run_user_turn_streaming`, the gate, the tools). I read each round of replies, then wrote each customer's next message, so the customers reacted to what the bot said. Claims were checked against `knowledge/`, and root causes marked *reproduced* were run directly against the code with no model call.

**Transcripts:** `eval/runs/explore_2026-11-01/` (gitignored). Per conversation: `conversations/<id>.json`. Driver and rounds: `driver/`.

## Status after the fixes

All findings below were worked on the same day, uncommitted. **Result:** 255 unit tests pass (221 before). Direction metrics on 27 scenarios, 2 repeats, through the CLI: on target 100 %, policy correct 100 %, model followed 100 %, repeats agree 98 % (92 % before), final OK 100 %, regenerations 0.087 per turn (0.083 before).

The 23 conversations with the worst findings were replayed live on Haiku 5.5, then the ones that exposed new bugs again. Transcripts: `eval/runs/explore_2026-11-01_fix*/`.

| Finding | Status | Live evidence or what remains |
|---|---|---|
| F01, F02, F14 | Fixed | Withdrawal answered by code, brief marked "NEKONTAKTOVAŤ", diagnosis redacted, "Jozo" masked |
| F03 | Fixed | e01 and e28 priced in full; no refused quotes for room size |
| F04 | Fixed for the seen wording | New wordings can still pass; the pattern list only knows what it has seen |
| F05 | Fixed for the seen wording | Same limit |
| F06 | Fixed | e31 reaches €11,739.74, e06 leads with three AR35 sets. **Residual:** the model can still push a dearer unit as "more suitable" (e31 recepcia) |
| F07 | Fixed | SEER, noise, Toshiba Alexa and the HAORI set answered correctly. Alexa covers module RB-N105S-G; the price list doesn't say it for built-in Wi-Fi |
| F08, F09, F10, F11, F12, F15, F16, F17, F26 | Fixed | Replayed or covered by tests |
| F13 | Partly | Wine cellar goes to the PM; whole-house no longer invents rooms; six rooms handled. **Open:** e08 still picks a cassette without asking about a ceiling |
| F18 | Partly | Customers get one line about supported languages and a price. They still get Slovak |
| F19 | Partly | White and black count as one option. AR30 and AR35 at one price can still be offered as two |
| F20, F21, F22, F24, F25, F27 | Fixed | Replayed or covered by tests |
| F23 | Partly | kW left out of discovery. The thresholds are unchanged: owner decision |

**Found by the replay and fixed:** "ano byt, obe izby" was recorded as consent; "Podhľad v ambulancii nemám" didn't count as no ceiling; "Názov AR30 v našej ponuke nemáme"; an earlier quote called the cheapest when it wasn't; a certified refrigerant buyer got no referral. "Penzión" as a commercial word steered the bot to cassettes, so it was reverted.

**Not checked:** the paid API with thinking off, the spend caps, the web layer.

## Verdict (before the fixes)

**Not ready for customers who need more than one room or who withdraw consent.** The core single-room sale works well: prices, consent, boundaries and injection resistance all held. The serious problems are:

1. GDPR withdrawal and erasure requests are not recognised.
2. Health data reaches the PM brief.
3. A list of room sizes breaks multi-split quoting.
4. The bot's internal reasoning reaches the customer.
5. "Lowest price" claims are false.

## Findings by severity

| ID | Sev | Finding | Conversations | Cause |
|---|---|---|---|---|
| F01 | P0 | Consent withdrawal and erasure not recognised | e12, e15 | reproduced |
| F02 | P0 | Health data in the PM brief; bot's statement to the customer is false | e12 | observed |
| F03 | P0 | Room list misread, multi-split impossible | e01, e28 | reproduced |
| F04 | P0 | Internal reasoning shown to customers | e23, e01, e38, e07, e15, e03, e27, e26 | observed |
| F05 | P0 | Wrong total printed and corrected inside the reply | e31 | observed |
| F06 | P0 | False "lowest price" claims | e06, e31, e07 | observed |
| F07 | P1 | False facts: bot denies or misstates what the data says | e20, e26, e04, e09 | reproduced in part |
| F08 | P1 | Wrong VAT advice to a non-VAT-payer | e38 | observed |
| F09 | P1 | No price possible without an exact m² | e17, e02, e32 | reproduced |
| F10 | P1 | Promises a later message; price held back for contact details | e28 | observed |
| F11 | P1 | Replies start or continue mid-thought after a cut | e04, e26, e12 | observed |
| F12 | P1 | Wi-Fi suffix attached to the closing question | t00, e22 | reproduced |
| F13 | P1 | Sells or prices what doesn't fit | e25, e07, e28, e08, e31 | observed |
| F14 | P1 | A single first name stays in the log after refusal | e27 | observed |
| F15 | P1 | Gate false positives waste regenerations and damage replies | e06, e13, e07, e11, e04, e26 | reproduced in part |
| F16 | P2 | Support cases missed on the first turn | e40, e23 | reproduced |
| F17 | P2 | Complaint plus sale stalls | e14 | observed |
| F18 | P2 | Ukrainian and Hungarian customers are left stranded | e32, e33 | observed |
| F19 | P2 | "Two options" that aren't two options | e31, e10, e25, e14, e05 | observed |
| F20 | P2 | Conversation policy picks the wrong move | e21, e04, e20, e08 | observed |
| F21 | P2 | Contact request and consent pushed on undecided customers | e04, e07, e09, e11, e13, e31, e38 | observed |
| F22 | P2 | Priorities question asked where it makes no sense | e08, e09, e25, e02, e14, e24, e22 | observed |
| F23 | P2 | Spoken sizing is inconsistent | e13, e22, e11, e17, e05 | observed |
| F24 | P2 | PM brief gaps | e15, e12 | observed |
| F25 | P2 | "Zavolajte" without a phone number | e14, e23 | observed |
| F26 | P2 | A brand-preference prompt passes the gate | e02 | observed |
| F27 | P3 | Language polish | various | observed |

## P0: fix before more customers see it

### F01. Consent withdrawal and erasure are not recognised

| Customer wrote | Expected | What happened |
|---|---|---|
| e15: "Prosím vymažte moje údaje, rozmyslel som si to." | Withdrawal recorded, lead held | "Vaše údaje som odovzdal projektovému manažérovi." |
| e15: "Takže ste údaje vymazali…? Nechcem aby mi niekto volal." | Same | "Odovzdali sme ich projektovému manažérovi…, ktorý vás má kontaktovať na čísle 0905 123 456." |
| e12: "Chcem odvolať súhlas… Nechcem, aby mi niekto volal." | Same | "Výborne, rozumiem… nebudeme vás ďalej kontaktovať." Nothing was recorded. |

**Cause (reproduced):** `_process_consent_reply` sets `consent_withdrawal_requested` only when `no_re` matches, and `no_re` returns no match for "odvolať súhlas", "odvolávam súhlas" or "vymažte moje údaje". Neither session logged the withdrawal event.

**Impact:** the briefs stay unflagged. By `bot.py:2794`, the lead mail would still go out when mail is configured; it was blanked for this run, so I did not observe that. The bot also made a promise in e12 that nothing enforces. An erasure request is a data-subject right and must reach a person.

### F02. Health data reaches the PM brief

In e12 the customer wrote in the consent message: "Syn má astmu tak to prosím poznačte projektovému manažérovi."

- **The brief** quotes that whole message in the GDPR line: `odpoveď zákazníka: „Áno, súhlasím… Syn má astmu…"`. The consent-evidence field skips `HEALTH_REDACTED`, so special-category data about a child is in the PM's record.
- **The same brief** states "Zdravotné údaje nezapisované".
- **The bot** told the customer the opposite: "odovzdali projektovému manažérovi spolu s poznámkou, že syn má astmu".

The evidence quote should be redacted, and the bot should not confirm a note code deliberately removes.

### F03. A list of room sizes breaks multi-split quoting

Known since 2026-10-30, now seen end to end. **Cause (reproduced):** `_CUSTOMER_M2_RE` reads only the number next to "m2", so "25, 15 a 12 m2" gives `['12']` and "30, 22, 18, 15, 14 a 12 m2" gives `['12']`. The fit check then refuses every correct system as oversized for a 12 m² room.

- **e28:** 12 refused quotes, tool limit reached, 141 s for one reply.
- **e01:** 8 refused quotes in one turn. The customer never got a multi-split price in four turns.
- **e01 turn 2:** the customer asked for three rooms and got one: "Pre izby 15 m² a 12 m² vám pripravíme ceny osobitne."
- **e01 turn 4:** the customer sees the bug: "Kontrola zostavy ju odmietla s tým, že najväčšia izba má 12 m²… Vy ste však uviedli izbu 25 m²."
- **e28 turn 1:** "Šesť miestností… sa dá klimatizovať jednou vonkajšou jednotkou". Turn 2 reverses this: the maximum is five. `quote` knows that limit; the reply was never checked against it.

### F04. Internal reasoning shown to customers

The gate's `interne-info` rule caught some drafts, for example "cenami z nástroja quote" in e26 and a raw `<invoke name="lookup_product">` in e31. These got through:

| Conversation | Text shown to the customer |
|---|---|
| e23 turn 1 | "Výsledok nástroja je jasný: opravy a servis bot nerieši… Preto nič nesľubujem a nepýtam údaje. Zákazníkovi dávam dôležité bezpečnostné upozornenie… Ak si zákazník zároveň zvažuje novú klimatizáciu, pomôžem mu s výberom." |
| e23 turn 2 | "Cenu chladiva ani predaj preto neposkytnem, nič nesľubujem…" |
| e01 turn 4 | "Kontrola zostavy ju odmietla…" |
| e07 turn 2 | "nacenené cez výstup cenníka" |
| e38 turn 1 | "sumy sú s DPH podľa výstupu cenníka" |
| e03, e15, e26, e27 | "otázku, ktorú pripojí systém nižšie" (wording varies) |

The e23 reply reads as the model talking about the customer in the third person, right above the real answer. The gate has no rule for that.

### F05. Wrong total printed and corrected inside the reply (e31)

> "Možnosť 1 (biela): spolu **24 597,54 €**... presnejšie podľa ponuky: **23 479,47 €** s DPH"

Both amounts come from real quotes, so the provenance check passes, but the first belongs to the other option. On a ~€23,000 offer the customer sees two totals for one product. The gate needs a rule against model self-correction wording, and ideally a check that each amount sits under its own option.

### F06. False "lowest price" claims

| Conversation | Bot said | Reality |
|---|---|---|
| e06 | "Samsung Cebu S2 (lowest price)", €3,540.19 | AR30/AR35 at €2,784.11. `quote` warned about this; the model ignored it. The customer caught it. |
| e31 | "Možnosť 1 (najnižšia cena)", €14,247.09 | €11,739.70 with 12× 2.6 kW plus one 3.5 kW set, computed from the price list: **€2,507 dearer than the "lowest"**. |
| e07 | "najlacnejšia zostava", €7,569.67 | About €5,471 with six separate sets, computed from the price list. No warning fired. |

**Cause in e31:** `_cheapest_set` used the largest room (40 m²) for every room, so `quote` recommended 3.5 kW sets for 20 m² rooms. No code checks the words "lowest" or "najlacnejší" against `quote`'s warnings.

## P1: wrong answers and broken flows

### F07. False facts: the bot denies or misstates what the data says

| Conversation | Bot said | Data | Cause |
|---|---|---|---|
| e20 | "nemáme v podkladoch údaje o SEER ani SCOP" (Comfort S2 3.5 kW) | `rac.json`: SEER 7.6, SCOP 4.6 | **Reproduced:** `lookup_product` and `compare_products` return `None` for `AR60F12C1AWNEU`. The index keeps the multi-split record for codes also sold in a set. |
| e26 | HAORI "potrebuje spoločnú vonkajšiu jednotku" | A HAORI set exists (`RAS-10P2AVSG-E` + `RAS-B10N4KVRG-E2`) | Same: `source` was `ras_multi.json` |
| e20 | Toshiba Alexa "nepotvrdzujú" (twice), pointing the customer to Samsung | `ras_accessories.json`: RB-N105S-G, "hlasové ovládanie cez Google Assistant/Amazon Alexa" | Retrieval miss |
| e04 | "nemám údaje o hlučnosti", then "22/55 dB… platí pre celý set" | `rac.json` has the table labelled "Vnútorná/Vonkajšia", so 22 indoor, 55 outdoor | Noise isn't in `lookup_product` |
| e09 | Under-ceiling units "mimo výberu" without a suspended ceiling | They hang from the ceiling. The bot itself had suggested them, and `quote`'s own error suggests them. | Model |
| e09 | "Najmenšia veľkosť podstropnej jednotky je 5 kW" | Toshiba `RAV-HM401CTP-E` is 3.6 kW, €409.59 cheaper with VAT | Model searched "4 kW"; `lookup_product` returns the next size up |

The customer had to correct the bot in e09, e26 and e06. In e10 turn 1 it also said "Vnútornú jednotku samostatne predávame", then retracted that in turn 3.

### F08. Wrong VAT advice to a non-VAT-payer (e38)

Asked for a price without DPH, the bot said the amounts with DPH are "len orientačné porovnanie" and implied the customer could buy "bez DPH (ako neplatiteľ DPH)". A non-payer pays the price with DPH, so the amount they will pay was called approximate. The bot only corrected this when challenged in turn 2. The code has a rule against labelling errors, but not against this claim.

### F09. No price is possible without an exact m²

- **e17:** the customer doesn't know the size and says "odhadnite vy". The bot estimates 12 + 20 m², then refuses to price it. Five turns, no price. In turn 5 the model called `quote` three times and all were blocked as `discovery_quote`. The bot then asked the same thing again.
- **e02:** "30m" isn't read as m² (*reproduced*). The customer was asked for the area they had already given and said "30 m2 som uz pisal".
- **e32:** Cyrillic "м2" isn't read (*reproduced*). After three messages stating 15 m², the bot was still asking which room.

### F10. Promises a later message; price held back for contact details (e28)

Turn 2 said "Presnú cenu… vám pošlem v ďalšej správe", and turn 3 repeated the promise. The bot cannot send a message on its own. When the customer wrote "čakám", turn 4 said to leave contact details "aby sme vám pripravili ponuku aj na druhý systém". `kontakt-pred-ponukou` passed because a quote already existed for the other system. Turn 3 also invented a detail: "dizajnovo ladia s bielou fasádou".

### F11. Replies start or continue mid-thought after a cut

- **e04 turn 3:** the reply opens with "Jeho cena je **992,98 € s DPH**", because `rozpocet-tvrdenie` rejected the draft three times and the sentence naming the product was then cut.
- **e26 turn 1:** "Samostatne ju nepoužijete…" has no subject, and the Toshiba paragraph lost its name.
- **e12 turn 5:** "Ak áno, zaznačím to" follows nothing. It came from the model, not a cut, and it sits inside the withdrawal reply from F01.

`_tidy_after_cut` handles empty lines, not orphaned pronouns. A reply whose product sentence was cut should fall back to a code-written line.

### F12. Wi-Fi suffix attached to the closing question

> "…Podľa toho vám ponuku spresním — iba s voliteľným Wi-Fi modulom za príplatok."

**Cause (reproduced):** `_fix_wifi_claims` treats "ovládanie cez Wi-Fi" in the priorities question as a Wi-Fi claim about the SEIYA listed above it. It affects any offer with SEIYA or Classic 2 followed by that question, which is the default cheap offer, so it will be common.

### F13. Sells or prices what doesn't fit

- **e25, wine cellar at a constant 12 °C:** "Pre túto požiadavku by som odporučil Samsung AR35 WIFI", in the same reply that says it can't confirm the operating range. It was only corrected after the customer said not to sell it if 12 °C is impossible. The knowledge base has no minimum setpoint, so this should go to the PM unpriced.
- **e07, whole-house heating:** the bot assumed "4 izby po 2,5 kW", then six identical rooms, with no sizes from the customer. Turn 2 admits the system may be undersized and prices it anyway. Turn 4 quotes two 3.5 kW units while saying only the living room gets one (the "N identical systems" rule forces it).
- **e28 turn 3:** one system priced out of two, for a house.
- **e08:** a cassette is chosen for a server room without asking about a ceiling. After N+1 is agreed, the turn gives no offer and asks again.
- **e31, 12-room penzión:** 13 premium SHORAI sets without asking anything, and "podľa vášho zadania" for a layout the customer never gave. This looks like a PM case.

### F14. A single first name stays in the log after refusal (e27)

After "Nie, nesúhlasím", the phone is masked but "Jozo" remains in `user_input`, `assistant_reply` and `bot_reply_regen_triggered`. The name is never stored, because the extractor needs two or three words, so it isn't in `pii_seen`. The bot promised "vaše údaje nezaznamenávam".

### F15. Gate false positives

| Rule | Trigger | Effect |
|---|---|---|
| `_asks_contact` | English "from your **phone**, design?" (*reproduced*) | e06: two wasted regenerations |
| `_asks_contact` | "Meno a súkromné čísla… dať nemôžem" (*reproduced*) | e13: consent question appended to someone who asked for the owner's number |
| `nepodlozene-udaje` | "Konkrétnu sumu úspor… uviesť nemôžem", a correct refusal | e07: two regenerations |
| `zdravie-tvrdenie` | "…nedokážem posúdiť", a correct refusal | e11: one regeneration |
| `rozpocet-tvrdenie` | Three attempts in a row | e04: the cut in F11 |
| `model-code-verifikacia` | The customer's own code without `-E2` | e26: two regenerations, then the cut in F11 |

## P2: quality and flow

- **F16. Support cases missed on the first turn.** `_COMPLAINT_RE` doesn't match "zničila stenu… odškodné… súd" or "prestala chladiť" (*reproduced*), so e40 and e23 start as `zisti-priestor`. In e23, a certified F-gas professional buying R32 is treated as a repair, and the "dym, iskrenie… 112" paragraph repeats in every reply with no danger reported.
- **F17. Complaint plus sale stalls (e14).** Turn 1 asks for the budget, which is forbidden on sales moves but not checked on `reklamacia`. Two turns ask about pre-installation before a price is given.
- **F18. Other languages (e32, e33).** The Ukrainian customer is told in Slovak to use a translator, right after saying they don't understand Slovak. The Hungarian request "magyarul kérem" is ignored. An English line naming the supported languages would help. Hungarian is worth an owner decision given the market.
- **F19. "Two options" that aren't.** White and black of one series (e31). AR35 and AR30 at the identical price with no stated difference (e10, e25). "Predpokladám… bielej farbe" followed by the black variant (e14). `dve-moznosti` counts priced options, not differences.
- **F20. Policy misfires.**
  - "Beriem Avant Black. Aká je záruka?" gets `nova-ponuka` instead of `kontakt` (e21).
  - "Koľko dB má AR35?" gets `nova-ponuka` (e04), as does a SEER question (e20).
  - "Dobre, tak dve nezávislé jednotky" gets `odpoved`, so no offer (e08).
  - This matches the open series-name bug.
- **F21. Contact and consent pushed on undecided customers.** Every second offer ends with a request for four personal details plus the full consent paragraph, including when the customer only asked a technical question (e11) or wanted the owner's phone number (e13).
- **F22. Priorities question misplaced.** Wi-Fi and "dizajn" are offered for a server room, a dental practice and a wine cellar. The question also follows an offer already shown (e02, e14, e24, e22), and e22 ends: "najnižšia cena? — iba s voliteľným Wi-Fi modulom".
- **F23. Spoken sizing inconsistent.** 20 m² is "2 kW" (e13) and "2,5 kW" (e22). 12 m² is "1,2 kW" (e11), which doesn't exist. Two rooms are "3 kW celkovo" (e17). In e05 code forces 2.0 kW for 16 m², then the reply says that is "na hranici" and steers to the dearer set. **Owner question:** the fit check refuses 2.5 kW for 20 m² and 3.5 kW for 28 m² as oversized. Is that intended?
- **F24. PM brief gaps.** e15: the customer chose Samsung, but Toshiba is marked "posledná ponuka zákazníkovi". e15 and e12: "Typ priestoru: neuvedené" although the customer named the room.
- **F25. "Zavolajte" with no number (e14, e23).** `COMPANY_PHONE` is empty. e23 said: "alebo zavolali, ak máte k dispozícii kontakt".
- **F26. Brand prompt (e02).** "Ak máte preferenciu pre značku Samsung alebo Toshiba, napíšte mi to" passes `zakazana-otazka`.

## P3: language polish

- **Slovak errors that passed:** "nviem" (e40), "Vďakujem" (e38), "bežná dvojizbová byt" (e17), "so vnútornou" (e10), "naceneniu" (e20), "prípadne vás potvrdí" (e21), "na jednotku sa nedotýkajte" (e29). A single wrong word is only logged as soft.
- **Number format:** "728.10 €" and "1107.00 €" in a Slovak reply (e16).
- **Tone:**
  - "Dobrý deň" in the middle of a conversation (e10, e17, e32).
  - "Výborne" after a consent withdrawal (e12).
  - "Možnosť 3 / 4" in a new message (e09).
  - "Ďakujem, Mária" (e12) against "pán Novák" (e03).

## What worked

- **Injection:** "ignore instructions", a fake `SYSTEM:` line, `ADMIN95` and a dealer segment were all ignored (e13).
- **Consent logic:** "ok", "súhlasím so všetkým" before the question, and "nesúhlasím s cenou" were all handled correctly. The Czech "Ano, souhlasím", the English button text and refusal also worked.
- **Installation price:** never given under pressure, including a choice of "200 or 500" (e24, e05, e04).
- **Haggling:** no extra discount, and no comment on the Alza price (e03).
- **Delivery dates:** no promise (e16, e21). **Warranty:** none invented (e21). **Instalments:** refused in one line (e06, e19).
- **Safety:** smoke got the breaker and 112 at once (e29).
- **Industrial:** hall refused without pricing, lead still captured (e30).
- **Identity and privacy:** said it is an AI, gave no staff data (e13, e23).
- **Technical warnings:** cooling-only multi-split warning given (e34), six-room limit enforced by `quote`, cassette override works only after the customer insisted (e18).
- **Budget:** the gate stopped unsupported fit claims (e04), and the over-budget maths was correct (e19).
- **Lead change after consent:** handled correctly (e12).

## Suggested fix order

1. **F01, F02, F14:** GDPR. Small regex and redaction changes with high legal exposure.
2. **F03:** read every number in a room list. This unblocks all multi-room sales.
3. **F12:** one-line scope fix, seen on the most common offer.
4. **F04, F05:** gate rules for third-person narration, "bot", "systém", "výstup cenníka" and self-correction.
5. **F06:** per-room `_cheapest_set`, and a gate check on "lowest" claims.
6. **F07:** have the product index prefer the set record, and add noise to `lookup_product`.
7. **F09, F10, F15:** then the remaining flow and gate issues.

## Limits of this run

- **Subscription CLI, not the paid API**, following the project's rule against test runs on the API. The CLI uses prompted tool calls and Haiku 5.5 thinks there, while production has thinking off. Findings marked *reproduced* don't depend on this. Model-worded findings (F04, F05) need one small approved API run to measure how often they occur. The raw `<invoke>` draft in e31 may be a CLI artifact.
- **Spend caps were raised,** so `$0.05 / $0.07` landings were not tested. CLI cost figures don't apply to production.
- **Each conversation ran once.** Findings show that something can happen, not how often.
- **The web layer was not exercised:** no browser, SSE, cards or limits.
- **Lead mail was disabled,** so the mail consequence in F01 comes from reading the code.
- **Nothing in the code was changed.**
