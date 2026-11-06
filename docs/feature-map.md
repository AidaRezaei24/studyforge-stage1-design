# Feature to implementation mapping

All feature IDs refer to the original Stage 1 feature with the same ID and UC number.
Each has an implemented path, with modifications listed below and in architecture.md.
Offline acceptance uses a model test double. The final live sample run passed all
twelve feature workflows; evidence is recorded in live-verification.json. This
does not guarantee semantic correctness for every future input.
Every video entry is awaiting owner recording, as indexed in demo-index.json.

Provider accounting: the adapter records nonnegative integer token counts reported
in a parsed provider response envelope before checking completion or generated JSON.
Incomplete or malformed billed responses therefore still contribute reported usage.
Missing/invalid usage is not invented; these counts do not establish money charges.

## F01 Material ingestion and indexing / UC01

Status: Modified; deterministic implementation.

Files/classes: learning.py DocumentIngestTool extracts and chunks supported files;
RetrievalTool ranks saved chunks; core.py SQLiteRepository persists material records;
EventBus publishes MaterialIndexed to ProgressProjector.

Methods: DocumentIngestTool.execute(), _extract(); RetrievalTool.execute();
SQLiteRepository.save(), transaction(); EventBus.publish().

Collaboration: GUI or CLI sends import_materials through StudyController and
StudyCommand. The tool validates each path and 20 MiB limit, hashes bytes, extracts
text, creates overlapping chunks with stable locations, saves, and emits an event
in a per-file transaction. One rejected file does not discard other successes.

Patterns: MVC, Command, Adapter (format parsing), Observer. Changes: filename-derived
metadata and lexical index replace AI tagging and vector embeddings. OCR is absent.
Video: F01 segment pending; show valid file, duplicate, unsupported file and sources.

## F02 Grounded summaries / UC02

Status: Modified; hybrid.

Files/classes: learning.py LearningService coordinates RetrievalTool and SummaryStrategy;
CitationVerifier checks IDs; model.py OpenAIModelAdapter performs generation;
core.py SQLiteRepository saves summary and evidence.

Methods: LearningService.summarize(), _generate(); GenerationStrategy.generate();
SummaryStrategy.validate(); CitationVerifier.verify(); ModelGateway.generate().

Collaboration: material/detail/focus input selects scoped chunks, constructs the
strategy contract, calls the provider, validates nonempty text and citations,
retries malformed output once, then saves the result and source trail. No evidence
produces an error before generation. Coverage reports bounded retrieval explicitly.

Patterns: Strategy, Adapter, Command, MVC. Changes: no section-domain selector or
exhaustive whole-course summary; source-ID validity does not prove semantic entailment.
Video: F02 pending; show detail/focus, source resolution and missing evidence behavior.

## F03 Concept extraction and knowledge map / UC03

Status: Modified; hybrid.

Files/classes: learning.py ConceptGraphStrategy validates and normalizes nodes/edges;
LearningService retrieves and persists; web/app.js renders the SVG graph and evidence.

Methods: LearningService.concepts(); ConceptGraphStrategy.validate();
CitationVerifier.verify(); browser renderGraph().

Collaboration: selected course/material/topic supplies evidence to the model; names
are merged case-insensitively, confidence values and edge endpoints/types are checked,
and the saved graph is rendered with relationships and source records.

Patterns: Strategy, Adapter, MVC. Changes: invalid graph rejects and retries rather
than quarantining individual edges; regeneration creates a new record without a
version comparison service. Video: F03 pending; show graph and supporting evidence.

## F04 Grounded question answering / UC04

Status: Modified; hybrid.

Files/classes: LearningService, RetrievalTool, GroundedAnswerStrategy,
CitationVerifier (learning.py); OpenAIModelAdapter (model.py); SQLiteRepository.

Methods: ask(); RetrievalTool.execute(); GenerationStrategy.generate();
GroundedAnswerStrategy.validate(); SQLiteRepository.list(), save().

Collaboration: the controller validates course scope, retrieval ranks only that
course's chunks, and the model receives current question and the latest four saved
conversation turns. Verified text/citations/confidence and evidence are saved.
Lexical misses return an evidence-gap error, without inventing an answer.

Patterns: Strategy, Facade, Command, Adapter, MVC. Changes: explicit commands replace
IntentRouter and multi-query TaskPlanner; pronoun-only questions may need rephrasing.
Video: F04 pending; show answer/citations, follow-up and unrelated question error.

## F05 Personalized study plan / UC05

Status: Modified; hybrid.

Files/classes: core.py StudyAgentFacade handles plan generation, feasibility and
approval; ProgressService supplies mastery; model.py OpenAIModelAdapter orders topics.

Methods: plan_create(); plan_approve(); get_snapshot(); SQLiteRepository.transaction().

Collaboration: goal and mastery go to the planner model; deadline, optional
start_date and daily availability are enforced locally. Start defaults to tomorrow
for a future deadline, otherwise today; an explicit date must be today through the
deadline. Scoped course evidence is used even for broad goals. Deterministic rules
validate topic uniqueness, known graph prerequisite order and capacity over the
inclusive start-to-deadline interval. Dated sessions and the resolved start_date are
saved and displayed as a draft. Approval is separate; active replacement is explicit.
Approved session dates are never shifted silently.

Patterns: Facade, Command, Adapter, MVC. Changes: daily-minute capacity replaces
arbitrary availability windows/profile priorities; activities and checkpoints are
not richly generated. Video: F05 pending; show draft, approval, infeasible capacity
and replacement guard.

## F06 Flashcard generation and review / UC06

Status: Modified; hybrid generation with deterministic review.

Files/classes: FlashcardStrategy and LearningService (learning.py) generate, edit,
reject and queue cards; ReviewScheduler and StudyAgentFacade (core.py) record reviews;
EventBus and ProgressProjector preserve activity.

Methods: flashcards(); card_update(); due_queue(); review(); schedule_next().

Collaboration: topic/count/difficulty retrieve evidence and generate unique cited
cards. Reviewing a card with rating 0-3 saves its next interval/due date and publishes
CardReviewed. Queue excludes rejected/not-yet-due cards. Edits are marked user_edited.

Patterns: Strategy, Command, Observer, Adapter, MVC. Changes: simple documented
rating multiplier; user edits are not AI-reverified. Video: F06 pending; show deck,
review, due schedule and edit/reject alternatives.

## F07 Quiz generation / UC07

Status: Modified; hybrid.

Files/classes: learning.py QuizStrategy supplies generation and validation contract;
LearningService retrieves and stores quiz; ModelGateway supplies generation.

Methods: quiz(); QuizStrategy.validate(); GenerationStrategy.generate().

Collaboration: the user chooses topic/count/difficulty; model creates choice/free
questions. Rules require unique questions, count, valid objective options/keys,
free-response rubrics and resolvable citations. Saved quiz includes answer key and
evidence. Invalid output retries once, then fails without a partial saved quiz.

Patterns: Strategy, Command, Adapter, MVC. Changes: no explicit objective coverage
validator, user-selected format mix or partial-quiz fallback. Video: F07 pending;
show saved questions/rubrics/citations and invalid count.

## F08 Automatic grading and explanations / UC08

Status: Modified; hybrid.

Files/classes: core.py AssessmentService grades; OpenAIModelAdapter evaluates free
text against a rubric; SQLiteRepository stores attempt/rubric snapshot; EventBus
and ProgressProjector record accepted activity.

Methods: grade(); ModelGateway.generate(); EventBus.publish(); get_snapshot().

Collaboration: all item IDs must have nonempty answers. Exact normalized option
text is scored deterministically; free answers receive model score, feedback and
confidence. Total, per-item citations, rubric and evidence are persisted atomically.
Low-confidence item scores are flagged and excluded from mastery.

Patterns: Command, Adapter, Observer, Facade. Changes: no human grade-override UI;
duplicate protection uses a supplied stable attempt ID, while new IDs denote new
attempts. Video: F08 pending; show mixed scoring, feedback, incomplete submission
and duplicate ID rejection.

## F09 Weak-topic diagnosis and adaptive practice / UC09

Status: Modified; hybrid with deterministic recommendation.

Files/classes: core.py ProgressService and StudyAgentFacade; learning.py QuizStrategy.

Methods: get_snapshot(); adapt(); LearningService.quiz().

Collaboration: accepted evidence is aggregated. At least two observations and
mastery below 0.7 are required; the lowest topic is proposed with its sample count
and an introductory/intermediate difficulty. Confirmation generates bounded practice
with that actual difficulty, saving a quiz and adaptation record.

Patterns: Facade, Command, Strategy (reused quiz generator), Adapter. Changes: no
prerequisite remediation traversal, AI narrative or insertion into active plan.
Sparse evidence is reported honestly. Video: F09 pending; show insufficient evidence,
then weak-topic proposal and confirmed practice.

## F10 Progress and mastery analytics / UC10

Status: Modified; deterministic.

Files/classes: core.py ProgressProjector stores domain events; ProgressService
computes metrics; browser/CLI render results.

Methods: EventBus.subscribe(), publish(); ProgressProjector.update(); get_snapshot().

Collaboration: quiz/card/session events are saved independently of presentation.
Snapshot reads accepted item scores and review ratings, computes means/sample sizes,
and returns attempt/session/plan/event counts with an as-of timestamp.

Patterns: Observer, MVC. Changes: date ranges, trend charts, plan adherence and
optional AI narrative are absent. Metrics are descriptive means, not calibrated
probabilities of mastery. Video: F10 pending; contrast empty data and measured results.

## F11 Study scheduling and reminders / UC11

Status: Replaced remote integration with local calendar export; deterministic.

Files/classes: core.py StudyAgentFacade validates reminders; CalendarAdapter formats
RFC5545 ICS; SQLiteRepository persists stable session-based reminder IDs.

Methods: schedule(); CalendarAdapter.export(); SQLiteRepository.save().

Collaboration: approved plan and local time/timezone generate candidates. Rules check
midnight, DST, overlaps across all local courses, and require every new reminder to
start strictly after the captured current time. Preview and confirmation reject past
new starts before writes; the user must choose a later time or approve a new future
plan. Approved plan dates never shift automatically. Existing reminder IDs remain
reusable, including historical records, so retries stay idempotent. Optional ICS
export supplies events and a ten-minute alarm for manual calendar import. Failed
export leaves confirmed local records available for retry.

Patterns: Command, Adapter, Facade, MVC. Changes: no live calendar authorization,
remote conflict reads, remote retries, AI rescheduling or notification daemon.
Video: F11 pending; show preview, confirmation, duplicate prevention, conflict and ICS.

## F12 Orchestrated focused study session / UC12

Status: Modified; hybrid multi-step orchestration.

Files/classes: core.py AgentOrchestrator coordinates ToolRegistry, SessionState,
ActiveState, PausedState, TerminalState, ProgressService and SQLiteRepository;
learning.py provides grounded Q&A and quiz tools.

Methods: start(); run(); SessionState.handle(); ToolRegistry.execute();
LearningService.ask(), quiz(); get_snapshot().

Collaboration: course/goal and 5-120 minute budget create a saved learn checkpoint.
Advance executes grounded explanation, then generates a quiz selected using measured
weakness/difficulty, then saves review/progress. Each result is checkpointed. A failed
tool pauses recoverably; pause/resume/skip/stop and expiry obey explicit legal states.
The user can grade the generated quiz before advancing review.

Patterns: State, Facade, Command, Observer, Strategy, Adapter. Changes: bounded three
stages replace arbitrary plans/Setup/activity mixes and continuous per-answer replanning.
Paused time counts toward budget. Video: F12 pending; show actual tools, pause/restart,
resume, review and terminal-state error.
