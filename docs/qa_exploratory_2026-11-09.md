# Exploratory QA on the real API, 2026-11-09

**Commit:** `6ecb5b1` (deployed). **Model:** `claude-haiku-5-5`, production settings and spend caps, real Anthropic API, run through the local web app (`/api/chat`, `KLIMABOT_DEMO=0`, lead e-mail off).
**Scope:** 10 conversations, 56 customer turns. **Cost:** $0.12 in total ($0.007–$0.026 per conversation; the cap is $0.07). No API errors, no cap hit.
**Method:** as on 2026-11-01. I played ten customers, each with a goal and a mood, read every reply and wrote the next message in reaction to it. Product claims were checked against `knowledge/` through `lookup_product`; causes marked CONFIRMED were seen in the logs or the code.
**Transcripts:** `eval/runs/qa_2026-11-09/` (gitignored): `conversations/<id>.json`, `data/logs/`, `data/handoff_records/`, and the driver `say.py`.

## Verdict

**Average 3.0 out of 5, up from 2.5 on 2026-11-01. 9 of 10 conversations ended in a lead, 6 of the customers would leave satisfied.** The personas differ from 2026-11-01, so the comparison is indicative only.

- **The hard guarantees held.** Every amount came from `quote`, no installation price was given, no delivery date was promised, and all 9 leads pass the GDPR audit.
- **Two P0 bugs remain.** One customer never got a price because code didn't read sizes typed without "m2". One complaint was recorded as a sales lead.
- **Most of the damage is in advice, not mechanics.** "Nothing quieter exists" when three Samsung series are quieter. "No commercial wall unit" when the price list has one. A cheaper option with good filtration that was never shown.

## Scorecard

Each score is how the customer would feel at the end: 5 delighted, 4 satisfied, 3 got there with effort, 2 would probably have left, 1 left with nothing. Errors the customer couldn't see are listed under Findings and don't lower the score.

| ID | Customer | Turns | First price | Outcome | Score | Why |
|---|---|---|---|---|---|---|
| p02 | Senior, one bedroom, not technical | 6 | Turn 3 | Lead | **5** | One question about priorities, two cheap and quiet options, callback put as a condition, lead |
| p04 | Family, 3 rooms, cheapest | 5 | Turn 1 | Lead | **4** | "Vyberte nám" got one recommendation. The note "volajte po 17:00" reached the brief. First turn took 27 s |
| p09 | Undecided, 2–3 rooms, multi vs separate | 6 | Turn 3 | Lead | **4** | Both variants priced and compared, the dropped room recalculated. Two dangling sentences (F6) |
| p03 | English-speaking expat | 5 | Turn 1 | Lead | **3** | Language notice, then Slovak. "Yes, I agree" counted. The reply to "write in English" said the *English* version was hard for them |
| p05 | Asthmatic child, filtration | 5 | Turn 2 | Lead | **3** | Best-filtration offers at once. "Something cheaper with good filtration" took 26 s and re-offered the same set as if new |
| p06 | €1 500 budget incl. installation | 6 | Turn 2 | Lead | **3** | No price for "Dá sa to?". "Najdôležitejšia je cena" was answered with "you haven't said what matters" |
| p08 | Angry complaint, then a new unit | 5 | Turn 4 | Recorded as a sales lead | **3** | Felt handled ("odovzdal som"), but internally it is a sales lead under sales consent (F2) |
| p07 | Light sleeper, quiet bedroom | 6 | Turn 1 | Lead | **2** | Told nothing was quieter than 19 dB(A). It took the customer quoting 16 dB to get WindFree |
| p10 | Office, s.r.o., 30 m², 4 people | 6 | Turn 2 | Lead | **2** | Prices given and then disowned, "no commercial wall unit" (false), RAV only after naming it. 23 s, 8 tools |
| p01 | Young tenant who tyká, 2 rooms | 6 | **Never** | Refused and left | **1** | Gave the sizes three times without "m2". The bot never knew them, the quotes were refused, and it gave up |

**Speed:** median turn 6.0 s, p90 15.2 s, max 27.1 s. The slow turns are all model-built offers: p04 27.1 s (a regeneration), p05 25.9 s (two regenerations), p10 23.3 s (8 tools, 2 searches), p08 19.9 s (a search and two refused quotes).
**Gate:** 4 regenerations in 56 turns (`cena-iny-produkt`, `nepodlozene-udaje`, `najlacnejsie-tvrdenie`, `porovnanie-bez-cisel`), no sentence cut, 11 repeated explanations dropped.

## Findings

| ID | Sev | Finding | Conversations | Status |
|---|---|---|---|---|
| F1 | P0 | Room sizes typed without a unit are never read: no price, the conversation is lost | p01 | CONFIRMED |
| F2 | P0 | A complaint about a unit we installed isn't recognised: sales consent, sales lead, sales brief | p08 | CONFIRMED |
| F3 | P1 | "Nothing quieter" is claimed when three series are quieter | p07 | CONFIRMED |
| F4 | P1 | An office over 25 m² gets residential prices disowned and a false "no commercial wall unit" | p10 | CONFIRMED |
| F5 | P1 | A budget question gets no price, and "najdôležitejšia je cena" isn't a price wish | p06 | CONFIRMED |
| F6 | P1 | Dropped repeats leave dangling sentences, and an installation question loses its answer | p09, p07 | CONFIRMED |
| F7 | P2 | "Cheaper, but still good filtration" re-offers the same set and skips the next filtration tier | p05 | CONFIRMED |
| F8 | P2 | Smaller wording and routing slips | p03, p06, p08, p09, p10 | CONFIRMED |

### F1. Sizes without "m2" (p01)

The customer wrote "spalna 12 a obyvacka 20", then "pardon, spalna ma 14 a obyvacka 22", then "uz som ti to pisal, spalna 14 a obyvacka 22. kolko to bude stat?". The policy stayed on `zisti-priestor` for all five turns, and the model's four quote calls were refused as `discovery_quote`. The bot's replies show it understood the sizes ("spálňa (14 m²)"), so the refusals looked absurd to the customer: "Potvrď mi prosím, že tieto údaje sú správne." Turn 5 ended with "Cenovú ponuku sa mi tu teraz nepodarilo pripraviť" and the customer left.

**Cause:** `_m2_in()` counts a bare number beside a room word (`_ROOM_BARE_M2_RE`) only when another area with a unit was stated (`if values:`). This guard protects "kuchyňa má 15m obývačka 20", but with no unit anywhere nothing is counted, so `_size_known()` stays false.
**Fix:** also count bare room areas when there are two or more of them in the range 6–80, or when the bot's last reply asked for the m². "Izba 3" and "obývačka na 2. poschodí" stay out: they fall outside the range or are caught by the existing unit lookahead.

### F2. A complaint recorded as a sales lead (p08)

"Vaša firma mi minulé leto montovala klimatizáciu a teraz z nej kvapká voda do izby. Už som to raz hlásil a nič." got the **sales** consent question ("za účelom prípravy cenovej ponuky… vybraný model"). The customer objected ("prečo sa ma pýtate na cenovú ponuku? Ja chcem opravu!"). The bot apologised, said "Ďakujem, máme meno a telefónne číslo" and "Váš podnet na opravu odovzdám… aby sa vám ozval projektový manažér" before consent, and showed the sales question again. The customer said yes. The result:
- `consent` purpose `sales`;
- `lead_captured`, not `complaint_captured`;
- the brief "Handoff záznam pre projektového manažéra", not "# Reklamácia";
- the GDPR audit marks it "ok", because the purpose matches the sales handover.

The data was collected for a quote and is used for a repair.

**Cause:** `_OUR_INSTALL_RE` only knows "ste … montovali" / "montovali ste" / "od vás", not "vaša firma mi … montovala". `_COMPLAINT_RE` doesn't know "už som to hlásil a nič". So `_support_case()` stays false and `_consent_purpose()` is `sales`.
**Fix:**
- `_OUR_INSTALL_RE`: add "vaš(a|e|i) (firma|spoločnosť|technik|montér…) … (montoval|inštaloval|dodal|predal)".
- `_COMPLAINT_RE`: add "už som to (raz) hlásil" and "chcem opravu".
- `_fix_have_data` should also cover "máme meno a telefónne číslo".

### F3. "Nothing quieter" (p07)

"Tá Toshiba sa mi páči, ale nemáte niečo ešte tichšie? Cena až taká dôležitá nie je." The model ran one search and looked up DAISEIKAI 10 and SHORAI, both Toshiba. It answered: "Tichšiu nástennú jednotku v našej ponuke som nenašiel", recommending the 19 dB(A) SEIYA Classic 2 (17.7 s). The price lists give **16 dB(A)** for Samsung WindFree Comfort S2, Avant S2 and Premiere. The customer only got them by saying "Čítal som, že má 16 dB".

**Cause:** a quiet wish after an offer isn't one of the re-pick wishes (`_REPICK_WISH_RES`), so the model searches on its own. Nothing gives it a ranking by dB.
**Fix:**
- A quiet request after an offer ("tichšie", "najtichšie", "nehučí") goes to `nova-ponuka`. Code ranks the wall sets that cover the room by `indoor_noise_min_dB` and prices the quietest per brand, as `_suggested_sets` does for other wishes.
- Optionally, the server context lists the quietest series by dB whenever the customer wants quiet.

### F4. An office over 25 m² (p10)

"Kancelária 30 m², s.r.o., 4 ľudia, bez podhľadu, tiché." The model priced two residential sets, then wrote "by som vám nemal ponúkať rezidenčné sety… Ich ceny… neodporúčam". It added "V podkladoch… nemám nástennú komerčnú zostavu" and offered a handoff instead of a price (23.3 s, 8 tools, 2 searches). `RAV-HM401KRTP-E` (Toshiba RAV wall unit, 3.6 kW, 30/36/41 dB) is in `rav_indoor.json`, and it was priced without trouble once the customer asked "A RAV od Toshiby nemáte nástennú?".

**Cause:** an office over `office_residential_ok_up_to_m2` only gets a `quote` warning ("over, či nepatrí Samsung CAC alebo Toshiba RAV"). `_commercial_units_note()` covers only salons and practices, so the model doesn't know where the commercial wall units are.
**Owner question:** should an office over 25 m² get one residential and one commercial (RAV/CAC wall) option, priced by code? Or the residential sets with the note that the PM checks the office at the visit? Today it gets neither cleanly.

### F5. Budget and price wishes (p06)

- "Mám rozpočet 1500 eur aj s montážou… Dá sa to?" got no price in turn 1, only the priorities question. A budget question is a price question. The direction scenario `rozpocet_900` passes only because it says "Zmestím sa do toho?".
- "Najdôležitejšia je cena. Tak koľko by stála?" got the prices, opened with "Keďže ste zatiaľ neuviedli, čo je pre vás dôležité, vybral som možnosti podľa ceny". That is today's opening for customers who stated no priority, and here it contradicts what the customer had just said.
- Turn 3: "Z 1 500 € vám teda pri Samsungu zostane 507,02 € na montáž a poplatok." The amount passes the provenance check (customer amount minus quote total), but it invites the customer to treat it as the installation budget.

**Cause:**
- `_PRICE_QUESTION_RE` has no "dá sa to / vyjde to" next to a budget.
- `_CHEAP_WISH_RE` and `_PREFERENCE_RE` don't know "najdôležitejšia je cena" or "cena je najdôležitejšia".

**Fix:** add these phrases. The "zostane … na montáž" sentence is an owner question: forbid it as an installation-budget hint, or leave it.

### F6. Dangling sentences after a dropped repeat (p09, p07)

- **p09** (`pokracuj`) ended with "Presnú sumu určíme pri objednávke. Jej cenu určí projektový manažér po bezplatnej obhliadke." `_drop_repeats` removed the sentences that named the recycling fee and the installation and kept their follow-ups.
- **p07, turn 4:** "Beriem ten Comfort S2. Kedy by ste to vedeli namontovať?" got "Cenu montáže určí rovnako on." and no answer about the date. The date sentence was dropped as a repeated installation explanation, because "namontovať" isn't read as a question about installation. The answer came a turn later, after the customer asked again.

Dropping on answer moves existed before; `4d96951` extended it to `nova-ponuka`.
**Fix:**
- In `_drop_repeats`, drop a sentence that follows a dropped one when it opens with a pointer (`_ORPHAN_START_RE`, "Presnú sumu", "… rovnako on").
- Read "montov / inštal / termín" in the customer's message as asking about installation.

### F7. "Cheaper, but still good filtration" (p05)

After two best-filtration offers (Avant S2 and HAORI) the customer asked "Máte niečo lacnejšie, ale stále s dobrou filtráciou?". The reply (25.9 s, 6 tools, 2 regenerations) said "Áno, máme ponuku pod sumou, ktorú ste videli pri vyšších variantoch" and presented the **same** Avant S2 at the same price as the answer. It never offered SHORAI CURVE, the next filtration tier ("o stupeň slabšia"), which `filtration_policy.json` names.
**Fix:** after an offer, "lacnejšie" together with a filtration wish goes to `nova-ponuka`, with the cheapest suitable set of the next tier down priced by code. The reply should say plainly that the cheapest best-filtration set is the one already shown.

### F8. Smaller slips

- **p03:** "Could you please write in English?" got "Rozumiem, že anglická verzia je pre vás ťažšia", the wrong language named. A fixed server sentence for this request would be safer: "Odpovedám iba po slovensky; píšem krátkymi a jednoduchými vetami."
- **p09:** "Áno, prepočítajte to bez pracovne" was routed `pokracuj`, not `nova-ponuka` (the model priced it anyway). `_NEW_VARIANT_RE` lacks "prepočítať / prerátať".
- **p08:** SEIYA Classic 2 was called "cenovo najvýhodnejšia" while AR35 is cheaper. `najlacnejsie-tvrdenie` doesn't know that wording.
- **p10:** "zoSEIYA" (a missing space); "Názov radu uvádza Wi-Fi ovládanie" (p04) reads oddly.
- **p01:** the canonical consent question uses vykanie to a customer who tyká. That is by design (the question is fixed), but it stands out in a tykanie chat.

## What worked

- **Today's changes, live:**
  - "Vyberte nám tú, ktorá je pre nás lepšia" got one recommendation, its price and "Chcete túto možnosť?" (p04, 2.7 s).
  - The English customer got the one-line notice and Slovak throughout, and "Yes, I agree" counted (p03).
  - Offers named at most three features per option in most replies.
  - The re-ask after a size correction wasn't exercised: p01's sizes were never read (F1), and nobody else corrected sizes after the question.
- **Consent and leads:**
  - 9 leads, all with the canonical question and an explicit yes in the very next message.
  - A message with details but no yes got the question again (p02, p07, p09, p10).
  - The refusal in p01 stored nothing.
  - The after-lead note "volajte po 17:00" is in the brief word for word (p04).
  - The IČO is in the brief and the segment is B2B (p10).
- **Boundaries:**
  - No installation price anywhere.
  - Installation dates and repair dates were left to the PM (p07, p08, p10).
  - No cash discount: "Zľavu za platbu v hotovosti neposkytujeme" (p06).
  - Safety advice for water near electricity came first (p08).
- **Offers:**
  - Single-room buyers got two priced options on their first or second turn.
  - Multi-room buyers got separate sets and a multi-split compared with the difference (p04, p09).
  - p02, a senior who knew nothing about air conditioning, got through in six short turns.

## Recommended order

1. **F1** and **F2**: small regex changes in `_m2_in`, `_OUR_INSTALL_RE` and `_COMPLAINT_RE`, each with a test. They lose sales and mis-file complaints.
2. **F6** and **F5**: small, and they make replies read broken or deaf.
3. **F3** and **F7**: re-picks by code for "quieter" and "cheaper with good filtration", the same mechanism as today's filtration re-pick.
4. **F4** needs the owner's decision first.

Then a CLI run of `eval/stability.py`, with p01, p06 and p08 added to `direction.json` as scripted conversations.
