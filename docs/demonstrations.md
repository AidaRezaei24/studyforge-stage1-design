# Recording the Stage 2 demonstrations

**Status: awaiting owner recording and upload.** No video has been recorded or
verified by the implementation agent. The segment order below is a recording
plan, not an assertion that a demonstration exists. Populate
[`demo-index.json`](demo-index.json) with actual public or instructor-accessible
video URLs and actual start timestamps after recording. One combined recording
is acceptable if every feature has a clearly identified segment.

Use the submitted application with the real configured LLM provider. Test-only
model fixtures are not demonstration responses. Read and assess generated output
before recording; a resolved citation identifies its source but does not prove
that a model claim follows from it. Keep the `.env` editor, environment listings,
API credentials, billing pages, and unrelated personal documents off screen.

## Prepare once

Follow the README setup, configure `.env` privately, and start the GUI:

```sh
python -m studyforge serve
```

Open `http://127.0.0.1:8765`. In a second terminal, verify the CLI and create a
course. GUI and CLI use the same default database.

```sh
python -m studyforge --help
python -m studyforge course create "Stage 2 demonstration"
python -m studyforge course list
```

Replace `COURSE` with the actual returned course ID throughout. Replace
`MATERIAL`, `PLAN`, `DECK`, `CARD`, `QUIZ`, `ITEM`, and `SESSION` with actual IDs
shown in results or the GUI's **Saved work** panel. Do not type these placeholders
literally. Prepare a genuinely future deadline, within the next year:

```sh
DEADLINE=$(python -c 'from datetime import date,timedelta; print(date.today()+timedelta(days=7))')
FUTURE_START=$(python -c 'from datetime import date,timedelta; print(date.today()+timedelta(days=1))')
```

The sample source is `samples/design-patterns.md`; use its absolute local path in
the GUI Materials form. Do not show or import secret files. If AI generation
reports `Set OPENAI_API_KEY`, stop recording, configure the local key privately,
restart the server, and repeat the feature. A missing-key error is useful error
behavior, but does not demonstrate working LLM integration.

## Suggested segment order

For each segment, speak or display the feature ID/name, show the input, run it,
inspect the output, and briefly explain AI involvement. Show both interfaces over
the recording as a whole; the steps below provide equivalent commands so either
boundary can be shown. Reopen saved records where needed to display IDs and
citations. Use the graphical concept graph for F03 and a CLI command visibly for
at least one generated feature.

### Segment 1 — F01 Material Ingestion and Indexing

**GUI:** Select the course → Materials → enter the sample file's absolute path →
Import & index materials. Show the imported filename/material ID. Import it again
to show duplicate detection; include a nonexistent file in a batch to show that
valid imports survive individual errors.

```sh
python -m studyforge material import samples/design-patterns.md --course COURSE
python -m studyforge material import samples/design-patterns.md missing.md --course COURSE
python -m studyforge list material --course COURSE
```

**Output / AI:** Parsing, hashing, chunking, filename metadata and lexical indexing
are deterministic. Import does not call the LLM. Explain that PDF, DOCX, UTF-8
TXT and Markdown are supported; scanned PDFs require OCR outside the app.

### Segment 2 — F02 Grounded Material Summaries

**GUI:** Summaries → optional material ID, focus question, and detail → Generate
summary. Expand source evidence and resolve a citation to the imported source.

```sh
python -m studyforge summarize --course COURSE --material MATERIAL --detail detailed --focus "What problem does Strategy solve?"
```

**Output / AI:** The LLM synthesizes retrieved source text. Deterministic schema
and citation checks gate persistence. Show concise detail as an alternative; an
invalid material ID or missing source produces an evidence error rather than an
invented summary.

### Segment 3 — F03 Concept Extraction and Knowledge Map

**GUI:** Concept map → optional material/topic filter → Extract concepts &
connections. Show the actual SVG node/edge graph, then the typed relationships,
confidence/review flags and citation IDs below it.

```sh
python -m studyforge concepts --course COURSE --material MATERIAL --topic "design patterns"
```

**Output / AI:** AI proposes concepts and relationships. The application merges
normalized duplicate names and validates edge endpoints, relation types,
confidence and citations. An unrelated topic should produce an evidence error;
low-confidence relationships remain visibly flagged for review when returned.

### Segment 4 — F04 Grounded Question Answering

**GUI:** Ask your sources → enter a course question → Find an answer. Show the
answer, confidence, source evidence, and saved conversation record.

```sh
python -m studyforge ask --course COURSE "How does Strategy differ from State?"
python -m studyforge ask --course COURSE "Explain photosynthesis"
```

**Output / AI:** Retrieval selects course evidence; the model uses bounded
conversation context and synthesizes the answer. The second question illustrates
insufficient course evidence. Do not characterize source validation as a
mathematical guarantee of answer truth.

### Segment 5 — F05 Personalized Study Plan

**GUI:** Study planner → goal, future deadline, optional First study date, and
daily minutes/session length → Build study plan. Keep approval unchecked initially. Inspect the draft, then use
Approve a saved draft. Show replacement protection by attempting approval of a
second plan without confirming replacement.

```sh
python -m studyforge plan --course COURSE --goal "Understand design patterns" --deadline "$DEADLINE" --start-date "$FUTURE_START" --minutes-per-day 60 --session-minutes 25
python -m studyforge plan-approve --plan-id PLAN
```

The optional `--start-date` accepts an ISO date (`YYYY-MM-DD`) between today and
the deadline. Leave the GUI date blank, or omit the CLI option, to start tomorrow
when the deadline is in the future. A same-day deadline starts today. Show the
saved `start_date` and session dates in the plan record before approving it.

**Output / AI:** AI orders proposed topics with learner state. Deterministic
checks enforce dates, available slots and known prerequisites; approval controls
which plan becomes active. An expired deadline or session length exceeding daily
availability is rejected. `--replace` explicitly permits replacing an active
plan; use it only after reviewing the new draft.

### Segment 6 — F06 Flashcard Generation and Review

**GUI:** Flashcards → topic/count/difficulty → Create flashcards. Show question,
answer and citations. Record a review using a returned card ID and rating 0–3;
show the updated due date/interval. Also show the due queue and edit/reject forms.

```sh
python -m studyforge flashcards --course COURSE --topic "Strategy" --count 3 --difficulty introductory
python -m studyforge due-cards --course COURSE --deck-id DECK
python -m studyforge review --card-id CARD --rating 2
python -m studyforge edit-card --course COURSE --deck-id DECK --card-id CARD --front "What does Strategy encapsulate?"
python -m studyforge edit-card --course COURSE --deck-id DECK --card-id CARD --reject
```

**Output / AI:** AI drafts evidence-linked cards; deterministic validation,
deduplication and spacing set review behavior. User edits are labeled. Show that
a rejected card cannot be reviewed. Editing preserves source IDs but requires the
learner to check that new wording remains supported.

### Segment 7 — F07 Quiz Generation

**GUI:** Practice quizzes → topic/count/difficulty → Create quiz. Inspect item
IDs, choice options or free-response rubrics, answer key, and citations. This is a
study tool and its preview deliberately exposes the key.

```sh
python -m studyforge quiz --course COURSE --topic "Strategy" --count 3 --difficulty intermediate
```

**Output / AI:** The model proposes questions, keys and rubrics; deterministic
checks enforce count, unique questions, supported citations and valid choice
answers. Change the difficulty to show the alternate input. A zero count is
rejected. Record an actual free-response item if demonstrating AI grading next;
regenerate or use a larger count if the provider returns only choice items.

### Segment 8 — F08 Automatic Grading and Explanations

**GUI:** Grade & feedback → quiz ID and a JSON object keyed by **every** actual
item ID → Grade my answers. Include one deliberately incorrect objective answer.
Show per-item scores, total score, confidence/review flags and saved rubric.

```sh
python -m studyforge grade --quiz-id QUIZ --answers '{"ITEM":"answer text"}' --attempt-id recording-attempt-1
```

Replace the example object with all actual quiz items; it is only a one-item
syntax illustration. Choice answers must match the selected option's exact text.

**Output / AI:** Objective marking is deterministic. Free-response marking uses
the model against its saved rubric and flags confidence below the threshold.
Repeat the same attempt ID to show duplicate-submission protection; omit an item
to demonstrate completeness validation. Use a new ID for a genuinely new attempt.

### Segment 9 — F09 Weak-Topic Diagnosis and Adaptive Practice

**GUI:** Adaptive practice → available minutes → Recommend practice, first without
confirmation. With no history, show the honest insufficient-evidence response.
Then record at least two accepted low scores/review ratings for the **same topic**
and rerun. Inspect the recommendation, then confirm generated practice.

```sh
python -m studyforge adapt --course COURSE --minutes 20
python -m studyforge adapt --course COURSE --minutes 20 --confirm
```

**Output / AI:** Diagnosis and difficulty thresholds are deterministic; confirmed
practice is AI-generated through the existing quiz strategy. Low-confidence
free-response grades do not count as accepted mastery evidence. Do not fabricate
history by modifying the database; create genuine attempts/reviews on screen or
explain the earlier recorded practice used.

### Segment 10 — F10 Progress and Mastery Analytics

**GUI:** Progress → Show progress. Show topic mastery, sample sizes, attempt/event
counts and completed sessions. Explain exactly how the recorded practice changed
the metrics. Compare an empty course to show the no-data behavior.

```sh
python -m studyforge progress --course COURSE
```

**Output / AI:** Metrics are deterministic means of accepted item scores and
card ratings. This implementation does not call AI for a narrative or predict
unmeasured mastery. Repeated observations are shown as samples, not independent
scientific evidence of learning.

### Segment 11 — F11 Study Scheduling and Reminders

**GUI:** Reminders → approved plan ID, start time and timezone → preview with
confirmation unchecked. Confirm to persist reminders. Enter a local `.ics`
export path to create the calendar file. Open/import it in a calendar application
if available, without exposing personal calendar details.

```sh
python -m studyforge reminder --plan-id PLAN --start-time 18:00 --timezone America/Toronto
python -m studyforge reminder --plan-id PLAN --start-time 18:00 --timezone America/Toronto --confirm --export-path .studyforge/demo-schedule.ics
```

**Output / AI:** Local time/overlap checks, confirmation, reminder IDs and ICS
export are deterministic. Repeat confirmation to show idempotency. An unapproved
plan is rejected. Preview and confirmation also reject a new reminder that would
start in the past. Choose a later time or create and approve a plan with a future
start date; the scheduler never silently shifts approved dates. This adapter does not write to an external calendar account or
send background notifications; importing the file is a separate user action.

### Segment 12 — F12 Orchestrated Focused Study Session

**GUI:** Focus session → goal and 25-minute budget → Start focused session. Use the
returned session ID with advance, pause and resume controls. Show saved output
from learning, the generated practice quiz, review summary and final state. For
practice feedback, submit the generated quiz through F08.

```sh
python -m studyforge session --course COURSE --goal "Explain Strategy" --minutes 25
python -m studyforge session-action --session-id SESSION advance
python -m studyforge session-action --session-id SESSION pause
python -m studyforge session-action --session-id SESSION resume
python -m studyforge session-action --session-id SESSION advance
python -m studyforge session-action --session-id SESSION advance
python -m studyforge list session --course COURSE
```

**Output / AI:** The state machine deterministically selects permitted tools and
persists checkpoints; AI supplies grounded explanation and adaptive practice.
Start another session to demonstrate skip or stop if desired. Advance after
completion is rejected. A provider failure pauses the activity, preserving prior
results; after fixing configuration privately, resume and advance to retry.

## Upload and link verification

1. Watch the recording and confirm every feature genuinely runs. Re-record failed
   generation or inaccurate explanations rather than substituting fixture data.
2. Upload the actual recording(s) to an accessible hosting location, verify access
   without requesting permissions, and copy each feature's direct URL with the
   actual timestamp.
3. Update all twelve entries in `demo-index.json` with `status: "recorded"`, a
   non-null `video_url` and `timestamp`. Keep unrecorded features explicitly
   pending. Replace the report's pending entries and regenerate its PDF.
4. Check the final report and every video link while signed out or in a browser
   context that approximates the instructor's access. Submit the repository URL
   through the course system yourself.

Screen captures and this guide are not substitutes for the required videos.
