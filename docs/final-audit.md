# Stage 2 requirement audit - November 15, 2026

Updated November 24, 2026. See project-timeline.md for development, validation and reporting events.

Basis: all five pages of the supplied Project-Stage2-Instruction.pdf, the original
Stage 1 design, current source, generated report and repository evidence.

| Requirement | Evidence and result |
| --- | --- |
| GUI and CLI | All twelve GUI actions connect to the shared controller and services; all major operations have CLI commands. End-to-end CLI/HTTP persistence journeys pass. |
| At least ten meaningful features; account for every Stage 1 feature | F01-F12 implemented and individually mapped in feature-map.md; modifications and scope reductions explicitly documented. |
| Five distinct implemented patterns | Seven: MVC, Command, Facade, Strategy, Adapter, Observer and State. Architecture table gives participants, roles, actual files/methods, problems and Stage 1 differences. |
| LLM and meaningful agent behavior | Real Responses API adapter; course retrieval, conversation memory, generated planning with deterministic constraints, adaptive practice and checkpointed session tool orchestration. Prior live sample evidence: 23 checks across all twelve features, 11 requests. The initial November 24 attempt stopped with HTTP 401. After owner key replacement, the current live run passed 23 checks / 11 actual requests; see nov24-live-verification.json. |
| Changes and diagrams | Consolidated original/change/reason/impact record, implemented class/use-case model and updated sequence diagrams included in report. |
| Same public repository and source publication | Public repository: AidaRezaei24/studyforge-stage1-design, default main. Review-branch CI passed on Python 3.11, 3.12 and 3.13. Final publication and merge status must be checked before submission. |
| Reproducibility and basic verification | make check passes all 59 tests; compilation and source credential scan pass. pip check reports no broken dependencies. Browser JavaScript syntax check passes. All 60 README/recording-guide CLI examples parse after removal of an unsupported plan option. |
| Seven-section PDF report | Updated report contains overview, per-feature mappings/video links, patterns with source methods, changes, collaboration log, verification/weekly summary and demonstration index. |
| Video index | Twelve owner-supplied timestamp links are present in both feature mappings and demonstration index; F11 starts at 10:40, F10 at 11:30. |
| Video access | Signed-out YouTube playback verified; duration displayed about 13 minutes 6 seconds. Both GUI and CLI task output were observed. Full-frame semantic correctness and absence of secrets throughout have not been independently verified. November 24: playback and selected feature frames inspected, terminal Q&A/progress output and GUI results observed; transcript reviewed separately. See professor-review.md for exact scope and edited GUI-first supplement. |
| API-key protection | Local .env ignored; example contains placeholders. Current-source scan and 67 historical text-blob scans found no supported OpenAI key pattern. This is a pattern scan, not proof about every possible credential format or video frame. |
| AI tools/models and costs | Recovered 127,032,805 Codex tokens across 13 explicitly scoped project chats/agents; hashed read-only snapshot in codex-usage.json. Owner confirms subscription access without extra Codex credits (US$0 additional credit spend). Published Plus base access is US$20/month, shared with other use. Recorded API validation totals 29,131 tokens / 35 requests, estimated US$0.0199456. Owner explicitly requested API estimates. Historical broader US$0.04 / 52,645-token account record is overlapping and not added. Full basis and limitations: ai-usage-accounting.md. |
| Weekly activity | Development on October 26, October 28 and November 6 includes 5, 6 and 5 production code commits, respectively. The development log lists reporting periods and commit counts; course compliance requires instructor review. Instructions specify one total 5-point deduction when any period is deficient. |
| Due date and final submission | Original instructions give November 10, 2026; the professor's supplied follow-up gives November 24 for missing items. This audit was updated November 24. No on-time submission or extension is established. Owner must submit repository URL in the course system. |

## Corrections made during this audit

- Replaced stale pending-video statements in feature mappings and README with actual supplied links/status.
- Added plan --session-minutes to the CLI, matching the existing GUI/shared service option.
- Added explicit implementation file/method references for every pattern.
- Recorded signed-out playback separately from unverified full recording coverage.
- Clarified that the validation ledger is not complete project cost accounting.

Passing tests and accessible links do not guarantee a grade. Remaining requirements
need owner action: course submission. Usage accounting now provides recovered counters, subscription access and explicitly authorized API estimates. Historical weekly activity and elapsed deadline are reported
accurately rather than asserted complete.

## Professor follow-up

All F01-F12 entries now state original requirements and have actual runtime screenshots embedded in the report. CLI examples, short-session support, failed-import exit status, GUI numeric bounds and HTTP 401 guidance were corrected. Report generation executes tests before claiming a passing count. See professor-review.md for the evidence, video observations, screenshot provenance and initial authentication failure and successful current retry.
