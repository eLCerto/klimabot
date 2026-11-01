# Haiku 5.5: API vs subscription

**Date:** 2026-11-01. **Code:** the uncommitted fixes on top of `4e6f78c`, the same code on both routes.

**Test:** the 38 QA scripts (125 customer messages), run twice per route, 152 conversations in total. Scripts were fixed, so both routes received identical customer messages.

- **API:** production setup, thinking off, native tool calls, production spend caps.
- **Subscription:** Claude Code CLI, thinking on (it can't be turned off there), tool calls written as text, caps raised.

**Paid API spend:** $0.79, made up of $0.57 for the conversations and $0.22 for the blind review.

## Verdict

**The subscription's replies were slightly better, and the API was about 3 times faster.** The difference in what customers finally read is small, because the output gate cleans up more of the API's drafts.

| Question | Better route | How clear |
|---|---|---|
| Quality of first drafts | Subscription | Clear: half the regenerations, a fifth of the cut replies |
| Quality of final replies | Subscription, slightly | Modest: 3.24 vs 3.15 in the blind review |
| Getting the sale right | Tie | 8 leads each, same consent results |
| Speed | API | Clear |
| Real cost | API | $0.0076 per conversation; the subscription is not billed per message |
| Predicting production | API | It is production |

Customers get the API route, so its results are the ones that count. The subscription is a useful test tool, but it hid two API-only problems (see "What the subscription hides").

## One conversation, side by side

Customer: "Dobrý deň, koľko stojí klíma do spálne 14 m2?" Both routes offered the same two sets at the same prices.

| | API | Subscription |
|---|---|---|
| **Opening** | "pre spálňu 14 m² odporúčam jednotku s výkonom približne 2,5 – 2,6 kW" | "Pre spálňu 14 m² sme pripravili dve možnosti" |
| **Option 1** | Samsung AR35 WIFI 2,6 kW, 895,56 € s DPH | The same |
| **Option 2** | Toshiba SEIYA Classic 2, 1 107,00 € s DPH | The same |
| **Grammar** | "Radu nie sú súčasťou WindFree…" (wrong) | "Funkcie AI, WindFree ani SolarCell tento rad nemá." |
| **Comparison** | None | "lacnejší o 211,44 € s DPH" |

The prices match because code calculates them. Wording and detail vary.

## Results

Figures are averages of the two repeats per route.

| Measure | API | Subscription |
|---|---|---|
| Regenerations per customer message | 0.32 | 0.16 |
| Replies with sentences cut out | 5 | 1 |
| Failed tool calls | 36 | 16.5 |
| Turns forced to answer by the call limit | 5 | 1 |
| Text written next to tool calls and hidden | 71.5 | 9 |
| Median reply time | 4.0 s | 13.9 s |
| 90th percentile reply time | 13.4 s | 37.6 s |
| Slowest reply | 25.1 s | 105.1 s |
| Time for all 38 conversations | 3 min | 10 min |
| Average reply length | 752 characters | 749 characters |
| Spelling flags in final replies | 15.5 | 11.5 |
| Internal leaks in final replies, by the gate's own check | 0 | 0 |
| Fact checks passed, of 15 | 12.5 | 13 |
| API or CLI errors | 0 | 0 |
| Leads captured | 8 | 8 |

**Same on both routes:** withdrawal, refusal, multi-room pricing, no invented installation price, injection held, and the wine cellar sent to the PM. The conversation policy chose the same move in 117–118 of 125 turns across routes, and 118–119 within a route, so routing is not the difference.

### Blind review

An AI reviewer scored each transcript from 1 to 5 without knowing the route. Higher is better.

| Criterion | API | Subscription |
|---|---|---|
| Discovery | 3.32 | 3.41 |
| Customer's wishes | 2.96 | 3.11 |
| Sizing | 3.53 | 3.70 |
| Grounding in data | 2.72 | 2.61 |
| Language | 3.78 | 3.91 |
| Flow | 2.59 | 2.70 |
| **Overall** | **3.15** | **3.24** |

Repeats of the same route differed by 0.01 (API) and 0.05 (subscription), so 0.09 is a small but real-looking gap. By conversation, 28 were ties, the subscription won 8 and the API won 2. The API's one better criterion, grounding, is also the weakest area on both routes.

Absolute scores are low partly because fixed scripts sometimes don't fit what the bot just said. Use them to compare routes, not as a quality grade.

## Where the routes differed

1. **Price labels (API only).** The API often writes "Cena s DPH: X (bez DPH Y)". That is correct, but `_vat_mislabeled_amounts` rejects it, which caused 13 regenerations on the API and none on the subscription. In `e07` and `e28` correct price lines were cut, and code added the prices back. This is the known open bug, and it hits production more than CLI tests showed.
2. **Internal text in drafts.** The API drafted leaks about twice as often ("Reklamácie a opravy bot nerieši", "cez nástroj quote"). The gate caught them, but each one costs a regeneration or a cut sentence.
3. **Fit check refusals.** The API sent about 2.5 times as many unsuitable quotes, 25.5 against 10.5, usually the wrong size. Code refused them. That caused extra rounds, and the turn's call limit was reached 5 times against 1.
4. **Tool arguments (API only).** Twice per run the model called `lookup_product` with `model_codes` instead of `model_code`. The tool failed and the model recovered.
5. **Later price for an unknown area.** In `e17` the API priced on turn 4 and the subscription on turn 3, because the API's turn 2 wording didn't count as having asked the priorities question.
6. **Answers beyond the data.** In `e31` the API called VRF a common choice for a penzión, which isn't in the knowledge base. The gate has no rule for this.
7. **The penzión's cheapest offer.** Neither route is reliable. One subscription run reached the cheapest figure; the other subscription run and both API runs didn't.

## Why

I can't separate the two causes, because the routes differ in both thinking and tool format. **Likely, not proven:** thinking lets the subscription check itself before writing, which would explain fewer wrong sizes, fewer leaks and fewer format problems. An API run with thinking on would settle it.

## What the subscription hides

- The 13 price-label regenerations and the cut prices.
- The wrong tool argument.
- About half of the API's regeneration load.
- Real timing and cost.

Subscription runs remain a fair check of code and routing, but they are optimistic about reply quality.

## Recommendations

1. **Fix `_vat_mislabeled_amounts` first.** It removes correct prices in production and is the API's biggest single waste.
2. **Accept `model_codes` in `lookup_product`, or rename the argument.** Small change.
3. **Do one small API run before each deploy.** $0.30 covers 38 conversations, if you approve it.
4. **Decide on thinking in production.** The test would cost little, but production prices and speed with thinking on are unmeasured, so don't assume it's worth it.

## Follow-up, same day

Recommendations 1 and 2 were fixed, then the 38 scripts ran once more on the API ($0.28). Price-label regenerations went from 13 to 0, wrong tool arguments from 4 to 0, all regenerations from 40 to 30 and replies with cut sentences from 5 to 3. No errors.

## Limits

- Two repeats per route is enough for large gaps, not small ones.
- Both routes shared one machine, and CLI start-up adds time, so speed is indicative.
- Subscription spend caps were raised, while the API ran under production caps. No conversation reached its spend cap.
- The fixes aren't deployed, so production itself wasn't tested.
- The blind reviewer is one AI model, run through the API.

Transcripts, logs and reviews: `eval/runs/compare_2026-11-01/` (gitignored).
