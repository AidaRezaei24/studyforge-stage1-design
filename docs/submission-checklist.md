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
| AI collaboration log and total costs | Collaboration log; runtime token ledger and explicit price estimate | Measured account charges and development-tool usage export still needed |
| Weekly code commits and links | Real history audited for Toronto reporting periods; current implementation links in report | Historical minimum not met; new dates not substituted |
| Every feature demonstrated on video | `demonstrations.md` gives all 12 recording scripts; `demo-index.json` has explicit pending entries | Owner recording/upload pending |
| Video access and timestamps | Verify each real uploaded link signed out; add direct segment timestamps | Pending |
| Final course submission | Submit the repository URL through the course system | Owner action pending |

Before final submission, configure the ignored local `.env`, run each AI feature
against the real provider, inspect its evidence, record the GUI and CLI, supply the
real URLs/timestamps and measured usage totals, then rebuild the report and commit
those updates. Confirm the final local commit is present on GitHub. No test fixture,
static screenshot, fabricated cost, or placeholder video is evidence of those gates.
