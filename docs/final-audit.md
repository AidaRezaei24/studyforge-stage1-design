# Stage 2 requirement audit - November 15, 2026

Basis: all five pages of the supplied Project-Stage2-Instruction.pdf, the original
Stage 1 design, current source, generated report and repository evidence.

| Requirement | Evidence and result |
| --- | --- |
| GUI and CLI | All twelve GUI actions connect to the shared controller and services; all major operations have CLI commands. End-to-end CLI/HTTP persistence journeys pass. |
| At least ten meaningful features; account for every Stage 1 feature | F01-F12 implemented and individually mapped in feature-map.md; modifications and scope reductions explicitly documented. |
| Five distinct implemented patterns | Seven: MVC, Command, Facade, Strategy, Adapter, Observer and State. Architecture table gives participants, roles, actual files/methods, problems and Stage 1 differences. |
| LLM and meaningful agent behavior | Real Responses API adapter; course retrieval, conversation memory, generated planning with deterministic constraints, adaptive practice and checkpointed session tool orchestration. Prior live sample evidence: 23 checks across all twelve features, 11 requests. No new paid requests made for this audit. |
| Changes and diagrams | Consolidated original/change/reason/impact record, implemented class/use-case model and updated sequence diagrams included in report. |
| Same public repository and source publication | GitHub metadata confirms public AidaRezaei24/studyforge-stage1-design, default main. Latest existing report commit d284853 had successful main and branch CI at audit start. Audit changes require their own publication check. |
| Reproducibility and basic verification | make check passes all 50 tests; compilation and source credential scan pass. pip check reports no broken dependencies. Browser JavaScript syntax check passes. All 60 README/recording-guide CLI examples parse after removal of an unsupported plan option. |
| Seven-section PDF report | Updated report contains overview, per-feature mappings/video links, patterns with source methods, changes, collaboration log, verification/weekly summary and demonstration index. |
| Video index | Twelve owner-supplied timestamp links are present in both feature mappings and demonstration index; F11 starts at 10:40, F10 at 11:30. |
| Video access | Signed-out YouTube playback verified; duration displayed about 13 minutes 6 seconds. Owner confirms both GUI and CLI are shown. Full narration, all input/output/error demonstrations and absence of secrets throughout have not been independently verified. Transcript unavailable in the player. |
| API-key protection | Local .env ignored; example contains placeholders. Current-source scan and 67 historical text-blob scans found no supported OpenAI key pattern. This is a pattern scan, not proof about every possible credential format or video frame. |
| AI tools/models and costs | Tools/tasks and runtime model are identified. Validation-only ledger totals 15,352 input and 4,725 output tokens, estimated USD 0.0137008. Recording requests and Codex totals are excluded. Later owner-supplied dashboard screenshot shows 52,645 total tokens, 59 requests and USD 0.04 displayed spend for October 26-November 16, 2026 (Default project, all API sources/models/users), captured November 15. This supersedes the earlier USD 0.014 owner report. Displayed spend is rounded; token split/timezone are not shown, and exclusive project attribution is not independently established. Codex token/money totals remain missing. Credit top-ups are not usage charges. |
| Weekly activity | The report's original-history audit has zero qualifying code commits in each required Toronto period (October 20-26, October 27-November 2, November 3-9). Requirement unmet; current commits do not repair it. Instructions specify one total 5-point deduction when any period is deficient. |
| Due date and final submission | Instructions give November 10, 2026; this audit occurs November 15. No on-time submission or extension is established. Owner must submit repository URL in the course system. |

## Corrections made during this audit

- Replaced stale pending-video statements in feature mappings and README with actual supplied links/status.
- Removed unsupported plan --session-minutes from the recording guide; default remains 25 minutes.
- Added explicit implementation file/method references for every pattern.
- Recorded signed-out playback separately from unverified full recording coverage.
- Clarified that the validation ledger is not complete project cost accounting.

Passing tests and accessible links do not guarantee a grade. Remaining requirements
need real evidence: full recording review (including CLI), complete AI cost totals
and course submission. Historical weekly activity and elapsed deadline are reported
accurately rather than asserted complete.
