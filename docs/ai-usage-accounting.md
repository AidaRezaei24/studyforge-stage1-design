# AI token usage and money accounting

Accounting snapshot: November 24, 2026 at 23:53:42 Toronto (2026-11-25 04:53:42 UTC). Later work is outside this fixed snapshot. The owner authorized recorded API estimates instead of a dashboard billing export.

## Recorded totals

| Tool and recorded model | Token total | Money cost and basis |
| --- | --- | --- |
| Codex main project chats; gpt-6.1-sol in thread metadata | 96,238,069 | Included in the existing ChatGPT Plus subscription. Owner reports no additional Codex credits or separate Codex usage charge. |
| Codex delegated project agents; gpt-6.1-sol in thread metadata | 30,794,736 | Same subscription; no second subscription or additional Codex credit charge. |
| **Codex development total: 13 scoped chats/agents** | **127,032,805** | **US$0 additional Codex credit spend**, per owner confirmation. This does not mean the subscription itself is free. |
| StudyForge API validation; gpt-4.1-mini-2025-04-14 | **29,131** (22,220 input; 6,911 output), 35 completed requests | **Estimated US$0.0199456**, standard uncached token rates. Paid from separate API credits; actual billed charge is not measured here. |
| **Recorded development plus validation total** | **127,061,936** | Keep subscription access and API estimates separate; do not treat API token rates as a Codex subscription bill. |

ChatGPT Plus's published base price is US$20/month, shared with other ChatGPT use. The owner's actual subscription receipt, local currency, tax and project allocation were not supplied; the report therefore gives the published access price and the confirmed US$0 additional Codex credit spend separately. The subscription is counted once, including delegated agents. This table records token consumption and money basis; it does not invent a combined project invoice.

## Codex evidence and counting method

`codex-usage.json` is a read-only export of local Codex `state_5.sqlite` per-thread cumulative token counters. Three confirmed project roots and their transitive spawned agents produce 13 distinct selected threads. Every selected counter is added once, including when roots overlap. Other tasks sharing the same folder, unrelated chats and platform permission-review agents are excluded. Thread IDs are hashed; prompts, chat titles, local paths, credentials and account identifiers are not exported.

These counters include repeated context and cached input across requests. They are not a count of unique words, lines of code or newly generated content. The large token total must not be multiplied by ordinary API prices to invent a subscription charge. Some historical raw request logs are absent, so a full historical input/output/cache split cannot be reconstructed; the retained per-thread totals are still available. Recorded thread model names are not proof of a historical billing SKU for each request.

Reproduce a new scoped snapshot using the project root chat IDs privately:

```sh
python scripts/export_codex_usage.py --root-thread ROOT_1 --root-thread ROOT_2 --root-thread ROOT_3 --output docs/codex-usage.json
```

Do not select all chats by folder: an unrelated task can share the workspace. Current counters continue increasing as development continues; the checked-in export is a fixed, dated snapshot. Synthetic tests cover attribution, transitive agents, deduplication, invalid counters and omission of private conversation fields.

## API evidence and arithmetic

The original four validation runs total 24 completed requests, 15,352 input and 4,725 output tokens. The November 24 successful run adds 11 requests, 6,868 input and 2,186 output tokens. The original final acceptance run is already within those 24 requests; it is not added twice.

Combined: 22,220 input + 6,911 output = 29,131 tokens across 35 completed validation requests. At US$0.40 per million input tokens and US$1.60 per million output tokens:

Estimated cost = (22,220 x 0.40 + 6,911 x 1.60) / 1,000,000 = US$0.0199456 (about two cents).

Cached-token discounts were not captured in the saved application usage ledger, so this is explicitly the standard uncached estimate, not an invoice. The initial HTTP 401 attempt reported no tokens; it is not treated as a successful completed request or assumed to have a known charge. Evidence: `runtime-usage.json`, `live-verification.json` and `nov24-live-verification.json`.

## Historical account dashboard

The earlier owner-supplied dashboard record reports 52,645 tokens, 59 requests and US$0.04 displayed spend for October 26-November 16, Default project, all API sources/models/users. This is a broader rounded account aggregate that overlaps the original validation runs. It is retained separately and is not added to the validation totals or attributed wholly to StudyForge without evidence. Demonstration requests outside the validation ledger are not silently assigned an invented token count. Buying API credits adds prepaid balance; it is not itself evidence of usage cost.

## Pricing sources

- [OpenAI Codex/ChatGPT pricing](https://learn.chatgpt.com/docs/pricing): Plus base price and included usage versus separate API-key billing. Checked November 24, 2026.
- [OpenAI GPT-4.1 mini pricing](https://developers.openai.com/api/docs/models/gpt-4.1-mini): standard input/output rates. Checked November 24, 2026.

No billing receipts, raw conversations or credentials are published. Recorded API estimates are used at the owner's explicit request.
