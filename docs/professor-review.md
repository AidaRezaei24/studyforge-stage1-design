# Professor follow-up review - November 24, 2026

## Required submission items

The standalone CLI accepts document paths and task arguments, runs without the GUI server, and prints structured JSON. README includes setup, supported-option discovery and a complete file-import/Q&A example. The installed `studyforge` entry point and `python -m studyforge` use the same controller as the GUI.

All twelve features now have an explicit original requirement, implementation description and deviation record in `feature-map.md`. Twelve screenshots from the running GUI are embedded in the report and available at full resolution in `docs/screenshots/`.

## Video review

Recording: [StudyForge demonstration](https://youtu.be/vovxVKUw2TE), approximately 13:06. Signed-out playback and selected frames across all twelve feature segments were inspected on November 24. A separate transcript review covered the narration. This is a feature and interface coverage review, not a frame-by-frame audit or proof of every generated claim.

The GUI visibly displays imported/duplicate materials, a generated summary, a concept map, a study plan, flashcards, quizzes, grading, adaptive practice, reminders, progress and a focused-session record. The terminal visibly returns a grounded Q&A result around [3:40](https://youtu.be/vovxVKUw2TE?t=220). Progress is shown in the terminal around [11:35-11:50](https://youtu.be/vovxVKUw2TE?t=695) and in the GUI around [12:03](https://youtu.be/vovxVKUw2TE?t=723). The recording therefore contains completed tasks in both interfaces; it does not demonstrate every feature twice. In the recording, reminders precede progress; repository IDs remain F11 reminders and F10 progress.

The study-plan segment includes a saved draft around 5:00 and a replacement-protection error around 5:15. This is an expected approval safeguard, not evidence that replacement succeeded. The unrelated photosynthesis question illustrates an evidence-gap response. The transcript's automatic rendering of grading numbers is not reliable enough to establish a grading defect; actual objective scoring is covered by automated tests. The original progress example uses CLI then GUI. The new [GUI-then-CLI supplement](https://github.com/AidaRezaei24/studyforge-stage1-design/raw/refs/heads/main/docs/video/gui-then-cli.mp4) reorders two unaltered progress excerpts into the requested sequence, with explanatory title cards. It is a silent 29.3-second edited excerpt, not a new execution. Source times, hashes and rebuild instructions are in docs/video/.

## Screenshot provenance

Captured November 24 using the actual local browser application and the successful November 24 real-provider acceptance workspace. F01-F08, F11 and F12 reopen saved records through the GUI's Saved work controls. F09 and F10 run fresh deterministic calculations over that same saved history. The generated outputs come from the current live run, not test-model fixtures. The associated source/output evidence is `nov24-live-verification.json`; review ratings and reference answers are explicitly synthetic test-learner inputs. Plan and reminder dates are the actual future dates approved by the live run, not shifted for screenshots.

## Fixes and verification

- Exposed `plan --session-minutes` so terminal users can choose the same short study sessions as GUI users.
- Material-import failures now return a nonzero CLI status while preserving successful per-file results and duplicate detection.
- Aligned GUI numeric limits with the shared service validators.
- Added actionable HTTP 401 guidance without exposing credentials or provider response bodies.
- Corrected report verification: report generation now runs the actual tests and stops if they fail, instead of counting discovery-error placeholders as passing tests.

The full suite passes 53 tests. Compilation, JavaScript syntax, submission-file/credential-pattern scan and diff whitespace checks pass. Browser capture reported no JavaScript errors.

The initial November 24 run passed ingestion and duplicate detection, then stopped at the first AI request with HTTP 401. Its evidence remains in `nov24-live-check.json`. After the owner replaced the credential privately, the fresh isolated retry passed all 23 checks across F01-F12 with 11 actual provider requests (6,868 input and 2,186 output tokens), recorded in `nov24-live-verification.json`. Source comparison confirms the sampled summary and Strategy explanation are supported; the concept graph contains seven source-backed concepts and no invented relationships. Future reminders preserve their IDs on retry, and the focused session completes with three saved tool results. This sample does not establish correctness for arbitrary future inputs. The earlier November 12 evidence is unchanged.

Four real standalone CLI subprocess checks also pass: course listing, file import/duplicate detection, saved summary retrieval and progress. See `nov24-cli-verification.json`; these commands require no GUI server and make no additional model requests. Provider token counts are recorded; actual billed charges require account billing evidence.

## Remaining owner actions

Verify final publication and submit the repository URL through the course system. Historical development and billing evidence are outside the three follow-up fixes and have not been rewritten.
