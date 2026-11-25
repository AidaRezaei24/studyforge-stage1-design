# Stage 2 submission checks

This checklist distinguishes implemented source from evidence still required.

| Requirement | Current evidence | Status |
| --- | --- | --- |
| Same public Stage 1 repository | Unauthenticated GitHub metadata confirms `private: false`, default `main` | Verified |
| At least 10 meaningful features | All F01-F12 mapped; final live sample workflow covers each feature | Implemented and sample validated |
| Working GUI and CLI | Shared controller; offline CLI/HTTP journeys, real provider application workflow, GUI inspection of real saved output and sources | Verified within recorded sample scope |
| At least 5 distinct patterns | Seven mapped in `architecture.md` with actual participants and methods | Source reviewed |
| LLM and meaningful agent behavior | Final live run: 23 checks, 11 real requests; source-grounded outputs, grading and checkpointed tools | Sample acceptance passed |
| Dependency and build files | Fresh virtual environment install, installed command-line entry point, `make check`, CI workflow | Passed on macOS Python 3.13; Windows timezone dependency declared |
| README and safe sample data | Setup, local key configuration, GUI/CLI commands, limitations; sample course material | Checked |
| Secret protection | Actual key stays in ignored local `.env`; `.env.example` contains placeholders; source credential scan | Passed |
| Stage 2 report PDF | `stage2-report.pdf`, rebuildable with `scripts/build_report.py`, 7 required sections | Prepared and visually checked; evidence gaps explicit |
| Feature/class/pattern/change mapping | `feature-map.md`, `architecture.md`, report | All F01-F12 accounted for |
| Updated diagrams | Class/use-case views and 9 sequence diagrams cover original 11 interaction shapes | Prepared |
| AI collaboration log and total costs | Collaboration log; runtime token ledger and explicit price estimate | Dashboard screenshot: 52,645 tokens, 59 requests, USD 0.04 displayed spend, Oct 26-Nov 16; Codex token/cost totals still unavailable |
| Weekly code commits and links | Development on October 26, October 28 and November 6 includes 5, 6 and 5 production code commits; links in report | Counts recorded; course compliance requires instructor review |
| Every feature demonstrated on video | Owner supplied [a YouTube recording](https://youtu.be/vovxVKUw2TE); all twelve owner-supplied timestamps are indexed | Selected feature frames and GUI/CLI outputs reviewed November 24; GUI-first supplement included |
| Video access and timestamps | Direct segment links recorded in `demo-index.json`; video played in a signed-out browser session | Playback verified November 24; selected-frame scope documented |
| Final course submission | Submit the repository URL through the course system | Owner action pending |

Before final submission, review the full uploaded recording for feature coverage,
both GUI and CLI, and absence of secrets. Supply measured AI usage totals, including
recording requests and development-tool usage, then rebuild the report and commit
those updates. Confirm the final local commit is present on GitHub and submit its
repository URL through the course system. The audit prepared November 15 and updated November 24 is recorded in
`final-audit.md`; weekly activity evidence remains subject to instructor review.

## November 24 follow-up status

- Twelve runtime screenshots and explicit original requirements are included in the report.
- Video GUI results and successful CLI Q&A/progress output are observed; see professor-review.md for review scope.
- CLI fixes, GUI limits and safe authentication guidance are covered by 53 passing tests.
- After private key replacement, current live AI verification passes 23 checks using 11 requests. Initial HTTP 401 evidence and prior November 12 evidence remain separate.
