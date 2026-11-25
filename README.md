# StudyForge

A local-first study workspace that turns your course materials into grounded
explanations, practice, plans, and checkpointed study sessions. The browser GUI
and CLI share the same controller and services. Course data is stored in SQLite;
only retrieved excerpts and necessary learning context are sent to the LLM.

## Set up

Requires Python 3.11+ with `pip` and an internet connection for AI generation.

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
cp .env.example .env
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1` and copy with
`Copy-Item .env.example .env`.

Create an API key in your own [OpenAI API account](https://platform.openai.com/api-keys).
Open `.env` in a text editor and replace `YOUR_LOCAL_API_KEY_HERE` with your key.
Keep the key on your computer; never paste it into the application, chat, report,
recordings, or GitHub. API access may require separate billing/credits. The model
defaults to the Stage 1 snapshot `gpt-4.1-mini-2025-04-14`; `OPENAI_MODEL` can select
another Responses-compatible model if your account cannot access that snapshot.
This is a documented configuration change, not a silent fallback.

The application reads `.env` from your current directory. Environment variables
take precedence. It never executes the file as a shell script. `.env` is ignored
by Git before any application files are committed. Ingestion, saved data,
objective scoring, progress, and local scheduling work without a key; generation
shows an actionable configuration error until a key is supplied.

## Graphical workspace

```sh
python -m studyforge serve
```

Open **http://127.0.0.1:8765**. Create a course, then import
`samples/design-patterns.md` using its local path. Use the workspace tabs to
access all twelve feature workflows. The server accepts only loopback requests
with a per-run request token. Close it with Ctrl+C. To change the port:
`python -m studyforge serve --port 8766`.

This browser GUI replaces the proposed native desktop window. It runs on your
computer and serves local assets without a frontend build or external CDN.

## Command line

Run commands from the project directory. Replace `COURSE`, `MATERIAL`, `PLAN`,
`DECK`, `CARD`, `QUIZ`, `ITEM`, and `SESSION` with IDs returned by earlier commands.
The optional global `--db PATH` belongs **before** the subcommand. GUI and CLI
use the same default database, `.studyforge/studyforge.sqlite3`.

The CLI runs directly in the terminal; it does not require the GUI server.
It accepts document filenames and task text as command arguments, and prints
JSON to standard output. After activating the environment and configuring your
API key, this complete example imports a file and answers a question about it
(macOS/Linux shell):

```sh
COURSE=$(python -m studyforge course create "CLI demonstration" | python -c 'import json,sys; print(json.load(sys.stdin)["id"])')
python -m studyforge material import samples/design-patterns.md --course "$COURSE"
python -m studyforge ask --course "$COURSE" "How does Strategy differ from Observer?"
```

Use `python -m studyforge SUBCOMMAND --help` for the supported options, for
example `python -m studyforge plan --help` or
`python -m studyforge material import --help`. Installation also provides the
equivalent `studyforge` command. Commands exit with status 0 on success and
nonzero on failure. A material batch with any failed files exits with status 1;
its JSON still identifies successful imports, duplicates, and per-file errors.
Importing an already indexed file succeeds without adding a duplicate.

The following reference covers all twelve workflows; replace the example IDs
as described above:

```sh
python -m studyforge --help
python -m studyforge course create "EECS3311"
python -m studyforge course list
python -m studyforge material import samples/design-patterns.md --course COURSE
python -m studyforge material import notes.pdf notes.docx --course COURSE
python -m studyforge list material --course COURSE
python -m studyforge summarize --course COURSE --material MATERIAL --detail detailed --focus "What problem does Strategy solve?"
python -m studyforge concepts --course COURSE --material MATERIAL --topic "design patterns"
python -m studyforge ask --course COURSE "How does Strategy differ from State?"
DEADLINE=$(python -c 'from datetime import date,timedelta; print(date.today()+timedelta(days=7))')
FUTURE_START=$(python -c 'from datetime import date,timedelta; print(date.today()+timedelta(days=1))')
python -m studyforge plan --course COURSE --goal "Understand design patterns" --deadline "$DEADLINE" --start-date "$FUTURE_START"
python -m studyforge plan-approve --plan-id PLAN
python -m studyforge flashcards --course COURSE --topic "Strategy" --count 3 --difficulty introductory
python -m studyforge due-cards --course COURSE --deck-id DECK
python -m studyforge edit-card --course COURSE --deck-id DECK --card-id CARD --front "What does Strategy encapsulate?"
python -m studyforge review --card-id CARD --rating 2
python -m studyforge quiz --course COURSE --topic "Strategy" --count 3 --difficulty intermediate
python -m studyforge grade --quiz-id QUIZ --answers '{"ITEM":"your answer"}'
python -m studyforge progress --course COURSE
python -m studyforge adapt --course COURSE --minutes 20
python -m studyforge adapt --course COURSE --minutes 20 --confirm
python -m studyforge reminder --plan-id PLAN --start-time 18:00
python -m studyforge reminder --plan-id PLAN --start-time 18:00 --timezone America/Toronto --confirm --export-path .studyforge/schedule.ics
python -m studyforge session --course COURSE --goal "Explain Strategy" --minutes 25
python -m studyforge session-action --session-id SESSION advance
python -m studyforge session-action --session-id SESSION pause
python -m studyforge session-action --session-id SESSION resume
python -m studyforge list session --course COURSE
```

`--start-date` is optional and accepts an ISO date (`YYYY-MM-DD`) from today
through the deadline. The GUI offers the same **First study date** input. Leaving
it blank starts tomorrow when the deadline is in the future, or today when the
deadline is today. The approved plan stores these dates. Reminder preview and
confirmation reject a new event whose start time is already past; choose a later
time or create and approve a plan with a future start date. Scheduling never
silently shifts an approved plan's dates.

Plans default to 30 available minutes per day and 25 minutes per session.
Set `--minutes-per-day` and `--session-minutes` together for another schedule;
for example, `--minutes-per-day 10 --session-minutes 5` allows two five-minute
sessions per day. Session length must be at least five minutes and fit within
the daily availability.

Use a future deadline appropriate to the day you run the application. A quiz
submission must include **every** item ID, with no extra IDs. For multiple-choice
questions, submit the exact answer text from one option. Use `edit-card --reject` to exclude a card, and `--back` to edit its answer.
Difficulty can be `mixed`, `introductory`, `intermediate`, or `advanced`.
Use `grade --attempt-id ID` to identify a submission and reject accidental retries.
Flashcard ratings are
0 (forgot), 1 (hard), 2 (good), and 3 (easy). New learners receive an honest
insufficient-evidence response from adaptation until at least two accepted
observations exist on a weak topic.

## Feature index

| ID | Workflow | Main implementation |
|---|---|---|
| F01 | Import PDF, DOCX, TXT, Markdown; deduplicate and isolate per-file errors | `DocumentIngestTool` |
| F02 | Summarize retrieved material with resolvable sources | `SummaryStrategy` |
| F03 | Extract, merge, validate, and save concept graphs | `ConceptGraphStrategy` |
| F04 | Course-scoped Q&A with evidence and conversation memory | `GroundedAnswerStrategy` |
| F05 | Generate feasible study plans and approve replacements | `StudyAgentFacade.plan_create` |
| F06 | Generate flashcards, record recall, schedule next review | `FlashcardStrategy`, `ReviewScheduler` |
| F07 | Generate validated objective and free-response quizzes | `QuizStrategy` |
| F08 | Grade answers, retain rubrics, flag uncertain free-text grades | `AssessmentService` |
| F09 | Diagnose sufficiently measured weak topics and generate practice | `StudyAgentFacade.adapt` |
| F10 | Compute mastery with sample counts and saved learning activity | `ProgressService` |
| F11 | Preview, confirm, and persist conflict-checked reminders | `StudyAgentFacade.schedule`, `CalendarAdapter` |
| F12 | Run grounded learn/practice/review tools with persisted state | `AgentOrchestrator` |

## Verification and design

```sh
python -m unittest discover -s tests -v
make check
python scripts/activity_audit.py
```

After configuring local API access and credit, run the optional paid live check:

```sh
python scripts/verify_live.py --output tmp/live-verification.json
```

This makes real provider requests using only the bundled sample course, runs in an
isolated temporary database, and stops on the first provider/configuration failure.
Its report labels synthetic learner inputs and records API-reported token counts.
Review generated claims against their sources; a passing script does not replace
feature demonstration videos or human evaluation of answer quality.

Tests inject fake model responses **only in tests** to verify deterministic
constraints, citation validation, persistence, failure recovery, and provider
contracts without incurring API charges. Production never substitutes canned
responses for a failed or unconfigured LLM. Automated tests do not establish live
model quality. Before recording, run the GUI and CLI with your actual API key,
inspect grounding, and follow [the demonstration guide](docs/demonstrations.md).

See [implemented architecture and diagrams](docs/architecture.md),
[Stage 2 implementation report](stage2-report.pdf), and
[AI collaboration and verification log](docs/development-log.md).
The original Stage 1 report remains unchanged in this repository.
See the [final requirement audit](docs/final-audit.md) for the latest checks and remaining submission items.

## Submission status and limits

Development took place on October 26, October 28 and November 6, 2026.
The [project timeline](docs/project-timeline.md) lists development, validation,
recording verification and usage reporting events. The owner supplied a [demonstration recording with all twelve feature timestamps](docs/demonstrations.md);
signed-out playback and selected frames across all twelve feature segments were reviewed November 24; GUI results and terminal Q&A/progress output were observed. See [the follow-up review](docs/professor-review.md) for scope and ordering details. The
final live sample run passed 23 checks across all twelve features using 11 actual provider requests;
see [live evidence](docs/live-verification.json) and the
[runtime usage ledger](docs/runtime-usage.json). Do not treat the repository as
ready for submission until the current authentication issue, measured usage accounting and final
submission steps are complete.

Retrieval is a deterministic local lexical index instead of embeddings; scanned
PDFs require OCR before import. Citation validation verifies source identity, not
the truth of every generated claim. The calendar adapter exports local calendar
data; it does not connect to Google Calendar or send notifications by itself.
The implementation simplifies some Stage 1 options; all changes and remaining
limitations are recorded in the report.

## November 24 professor follow-up

The report now includes screenshots for F01-F12 and explicit original requirements.
The [follow-up review](docs/professor-review.md) records fixes, video observations
and evidence provenance. All 53 automated tests pass. The latest live attempt
failed with HTTP 401: update your local `OPENAI_API_KEY` with a valid credential
and restart before generating new AI output. Prior successful acceptance evidence
is retained separately from [the failed current check](docs/nov24-live-check.json).
