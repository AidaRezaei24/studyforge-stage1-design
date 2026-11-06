# AI collaboration, verification, and weekly development record

## Tool use and accountability

| Tool | Model | Work performed | Token and money cost |
| --- | --- | --- | --- |
| Codex desktop coding agent | GPT-6 family as described by this environment; exact billed model identifier was not exposed | Read Stage 1 and Stage 2 documents; inspect/fetch original repository; implement shared core, model adapter, GUI/CLI, tests, sample configuration, documentation and report preparation; coordinate implementation and cross-review | Unavailable in this environment. Do not interpret unavailable as zero. The account usage/billing export is needed for a final measured total. |
| Codex delegated coding agents | Same inherited model as parent; exact billed identifier unavailable | Separate learning/retrieval, application core, and interface tasks; shared source review and regression fixes | Included in unavailable agent-session accounting; no invented per-agent estimate. |
| StudyForge runtime OpenAI adapter | `gpt-4.1-mini-2025-04-14` | Real summaries, concept maps, answers, plans, cards, quizzes, free-response grading and focused-session tools using the bundled sample | Across 24 completed validation requests: 15,352 input tokens and 4,725 output tokens. Estimated standard uncached cost: USD 0.0137008, excluding discounts, taxes and unrelated activity; measured account charges remain unverified. See runtime-usage.json. Provider-reported usage is counted before status/content validation so malformed-output retries are included. |

Local Python tools, SQLite, Git, PDF extraction, and browser/HTTP checks are development tools, not additional LLM models. Unit-test fake gateways produce deterministic test fixtures only. They are dependency-injected inside tests and are not a production fallback or a claim that an LLM ran.

The student remains responsible for understanding, reviewing, integrating, validating, recording demonstrations, and submitting the result. AI-produced code does not transfer that responsibility.

## Representative collaboration record

The following are concise summaries of representative requests and outcomes from this implementation session, not fabricated full conversation transcripts.

| Interaction | Development result and review outcome |
| --- | --- |
| Read all Stage 2 requirements, retrieve Stage 1 repository, and account for all original features | Read the five-page Stage 2 PDF and the forty-page Stage 1 PDF; retained F01-F12 and recorded deviations instead of silently omitting proposed behavior. |
| Implement learning ingestion/retrieval and evidence-grounded strategies with strict contracts | Added PDF/DOCX/TXT/MD extraction, duplicate detection, scoped lexical retrieval, stable source chunks, summaries, concept graphs, Q&A memory, cards and quizzes. Strategy-specific validators reject bad structure/citations and retry once. |
| Implement one shared controller, local persistence, model adapter, plans, review, grading, analytics, scheduling and sessions | Added SQLite transactions, receiver commands, facade services, observer events, legal session states and real OpenAI Responses HTTP integration. Model failures surface safe errors rather than canned study answers. |
| Build GUI and CLI over the same requests | Added local browser workspace and CLI command parser; HTTP Host/Origin/token checks restrict local mutation requests. Single-thread HTTP handling avoids interleaving one SQLite connection's transactions. |
| Cross-review boundaries and core invariants | Found that `handle(action, **params)` collided with session parameter `action`; renamed first argument to `command_name` and added regression. |
| Cross-review adaptive practice and reminders | Found difficulty was initially metadata only; passed actual difficulty into quiz generation. Expanded calendar conflicts from one course to all local course reminders. |
| Cross-review import transaction behavior | Found that an event-observer failure after material save could report failure while leaving the material saved. Added per-file repository transaction and rollback regression. |
| Review model failure retries | Distinguished malformed model JSON (`InvalidModelOutput`) from missing-key/network/HTTP errors so the bounded schema retry does not repeat unrelated failed requests. |
| Challenge state-machine edge cases | Found expiry could bypass legal-state validation; validate state first and regression-test that an expired completed session cannot advance again. Tool failure persists pause and resume state. |
| Review planning and progress against original report | Added known graph prerequisite-order checks, rejected duplicate topics, added broad-goal planning fallback with regression, and documented omitted availability windows, trend analytics, adherence, remote calendar integration and general-purpose autonomous planning. |
| Exercise the real provider request contract | Found that JSON mode requires an explicit JSON instruction in the input message, beyond the provider instructions field. Added it to the structured input envelope and regression-tested empty and populated requests. |
| Improve actionable provider errors | Added bounded parsing of structured quota error identifiers. Credit-related failures now give an actionable local message without printing raw provider messages, secrets or retrying failed requests. |
| Inspect actual live output against course sources | Found an unsupported Command-State relationship inferred from adjacent sections. Tightened relationship grounding, then ran a targeted live regression and a complete live rerun; the final graph contains only supported concepts and asserts no unsupported edges. |
| Inspect live schedule timestamps | Found that an evening run could create earlier same-day reminders. Added an explicit start date, future default dates, rejection of new past reminders, visible interface controls and frozen-clock regressions. Approved plans never shift silently. |
| Audit runtime usage accounting | Moved API-reported usage accumulation before status/content validation and tested malformed/incomplete responses, preventing undercounted paid retries. |

## Verification evidence and limits

The repository's test suite is the executable record. Run the current suite using the README command; the exact current count should come from that run rather than a stale count in this log. Coverage includes repository transactions/course isolation, parser behavior, import failures and duplicate hashes, evidence scoping/citation validity, generation schema retry, graph relationships, card review/edit/reject, quiz schema/grading, confidence exclusion, plan feasibility/approval/prerequisites, reminder conflicts/idempotency/ICS escaping, session transitions/recovery/expiry, actual controller arguments, CLI request mapping, local HTTP contracts and adapter HTTP construction.

A fake HTTP opener verifies the production adapter sends the expected Responses request, parses provider-shaped output, counts reported tokens and redacts secret-bearing error details. This is an adapter contract test, not a live model test. Test fakes never constitute demonstration evidence for AI feature quality.

The original main branch contained documentation only, so there was no previous runnable application whose behavior could be compared. The relevant baseline comparison is Stage 1 feature/class/interaction promises against the new source. `architecture.md` records those differences explicitly. New regression tests demonstrate corrected behavior for defects found during implementation; there is no claim of Stage 3 KUMA validation.

A local API key is configured privately and remains excluded from Git. The final
live run passed 23 checks covering F01-F12 using 11 actual provider requests
(6,936 input and 2,075 output tokens). Independent AI-assisted comparison verified
the sample hash, source copies, citation scope, generated claims, grading and
future reminder times. The GUI was also inspected while displaying the saved real
summary and its source passages. These checks cover the bundled sample, not all
future user inputs. See live-verification.json for evidence and runtime-usage.json
for the full validation usage ledger. Feature videos and accessible timestamped
links remain separate requirements; tests and screenshots do not replace them.

## Weekly code activity, Toronto local dates

The fetched original public repository history contained exactly two commits, both on October 9, 2026 Toronto local time:

| Commit | Toronto date | Description | Qualifies for Stage 2 weekly code minimum? |
| --- | --- | --- | --- |
| [`b4ab728`](https://github.com/AidaRezaei24/studyforge-stage1-design/commit/b4ab728) | October 9, 2026 | `docs(stage1): publish project design report` | No: documentation-only and outside all reporting periods. |
| [`ee6d35a`](https://github.com/AidaRezaei24/studyforge-stage1-design/commit/ee6d35a) | October 9, 2026 | `docs(stage1): align design traceability` | No: documentation-only and outside all reporting periods. |

| Required reporting period, inclusive | Required meaningful code commits | Qualifying commits found in original repository history | Status |
| --- | --- | --- | --- |
| October 20-26, 2026 | 5 | 0 | Not met |
| October 27-November 2, 2026 | 5 | 0 | Not met |
| November 3-9, 2026 | 5 | 0 | Not met |

Implementation performed in this session is current work after those periods. New implementation commits retain their actual creation dates. The required historical development and contemporaneous pushes are not established by the available history. Existing history was preserved.

The Stage 2 PDF states that failure of one or more periods incurs one total five-point deduction, not five points per period. This log reports the gap; it does not claim a waiver, instructor approval, or retrospective compliance. The due date stated in the assignment was November 10, 2026. Repository preparation after that date does not establish an on-time submission. Final repository publication, report status, video links and course-portal submission must be checked independently.
