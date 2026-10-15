# Brief: test scenarios for eval round 2

You took part in the four-person review of the Klimabot chatbot (Slovak AC sales bot, Samsung + Toshiba only). The agreed fix plan is in `eval/runs/full/agent_discussion/SYNTHESIS.md` §4. Your own round-2 paper is `eval/runs/full/agent_discussion/round2_<role>.md`.

**What is being fixed now** (another engineer is editing `bot.py` while you write — do not touch it):
- P0 items 1–9 of SYNTHESIS §4.
- From the P1 items:
  - `quote` returns an all-in range with DPH;
  - code-verified differences between quotes are allowed in replies;
  - "25 %" is removed from the prompt;
  - the rule changes of item 13 (answer price/stock questions in the same turn, never make a price conditional on contacts or consent).

**Your task.** Write **5 scripted customer conversations** that test whether the fixes work and whether anything regressed. Focus on the risks *your* role cares about most. Then this happens:
1. The bot runs every scenario with Haiku.
2. `eval/analyze.py` checks the `expect` block automatically.
3. A human reads each transcript against your `review` text.

Write the file `eval/scenarios/round2_<role>.json`: a JSON array of 5 objects. Do not create or edit any other file.

```json
{
  "id": "q01_short_slug",
  "author": "qa",
  "title": "Short Slovak title",
  "targets": ["P0-1 consent window", "c01 regression"],
  "review": "What a human must check in the transcript (Slovak or English, 1–3 sentences).",
  "expect": {
    "lead": true,
    "consent": "sales",
    "handoff_request": false,
    "quote": true,
    "price_before_gdpr": true,
    "commercial": false,
    "segment": "retail_B2C",
    "language": "sk",
    "codes_any": [],
    "must_not_say": []
  },
  "messages": ["…", "…"]
}
```

**ID prefixes:** QA `q01`–`q05`, developer `d01`–`d05`, architect `a01`–`a05`, sales `s01`–`s05`.

**`expect` keys** (all are machine-checked; use `null` or leave a key out when it doesn't apply):

| key | meaning |
|---|---|
| `lead` | a sales lead (`capture_lead` → handoff record) must / must not exist at the end |
| `consent` | final consent recorded by code: `"sales"`, `"support"`, `"refused"` or `"none"` |
| `handoff_request` | `request_human_handoff` must be called |
| `quote` | at least one successful `quote` call is expected |
| `price_before_gdpr` | `true` when the customer asks for a price before giving contacts: the first successful quote must come before the first GDPR question |
| `commercial` | commercial space: no residential single/multi-split lines may be quoted |
| `segment` | `retail_B2C` or `B2B_firma` (`partner_dealer`, `instalator_certifikovany` and `velkoobchodny_odber` are refused by `quote`) |
| `language` | `sk` or `en`: the language the bot must answer in (Czech customers get Slovak) |
| `codes_any` | optional: at least one of these exact codes must appear in some quote (only real codes from `knowledge/samsung/` or `knowledge/toshiba/`) |
| `must_not_say` | optional: Python regexes (case-insensitive) the shown bot text must never match |

**Rules for the scripts.** The customer is scripted and does not adapt to the bot. So:
- Each message must make sense whatever the bot asked last: volunteer the facts, don't answer questions you can't foresee.
- Use 3–8 messages. Write as real Slovak customers do: informal, typos and missing diacritics allowed. Use English only for an English-speaking customer, and Czech only for a Czech one.
- Contact details must be obviously fake: phones `09xx 000 xxx`, e-mails `@example.com`, made-up names.
- Give consent as the customer would, e.g. „áno, súhlasím“, together with contacts or as its own message. Remember the agreed rule: consent counts only in the customer message right after the bot's latest GDPR question.
- Cover all of these across your 5 scenarios:
  - at least 2 that should end in a sales lead;
  - at least 1 that must **not** produce a lead;
  - at least 1 regression of an old failure from the round-1 eval, by conversation id (c01–c20; see `eval/conversations.json` and `eval/runs/full/report.md`).
- Do not duplicate the old 20 scenarios word for word; vary them so the fix is tested, not memorised.
- Keep it cheap: read SYNTHESIS.md, your round-2 paper, `eval/conversations.json` and only the data files you need to pick real codes. Don't re-read whole transcripts.

Finish with a short reply (≤ 10 lines): the 5 ids, and one line each on what each scenario targets.
