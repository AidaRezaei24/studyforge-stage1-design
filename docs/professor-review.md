# Professor follow-up review - November 24, 2026

## Required submission items

The standalone CLI accepts document paths and task arguments, runs without the GUI server, and prints structured JSON. README includes setup, supported-option discovery and a complete file-import/Q&A example. The installed `studyforge` entry point and `python -m studyforge` use the same controller as the GUI.

All twelve features now have an explicit original requirement, implementation description and deviation record in `feature-map.md`. Twelve screenshots from the running GUI are embedded in the report and available at full resolution in `docs/screenshots/`.

## Video review

Recording: [StudyForge demonstration](https://youtu.be/vovxVKUw2TE), approximately 13:06. Signed-out playback and selected frames across all twelve feature segments were inspected on November 24. A separate transcript review covered the narration. This is a feature and interface coverage review, not a frame-by-frame audit or proof of every generated claim.

The GUI visibly displays imported/duplicate materials, a generated summary, a concept map, a study plan, flashcards, quizzes, grading, adaptive practice, reminders, progress and a focused-session record. The terminal visibly returns a grounded Q&A result around [3:40](https://youtu.be/vovxVKUw2TE?t=220). Progress is shown in the terminal around [11:35-11:50](https://youtu.be/vovxVKUw2TE?t=695) and in the GUI around [12:00](https://youtu.be/vovxVKUw2TE?t=720). The recording therefore contains completed tasks in both interfaces; it does not demonstrate every feature twice. In the recording, reminders precede progress; repository IDs remain F11 reminders and F10 progress.

The study-plan segment includes a saved draft around 5:00 and a replacement-protection error around 5:15. This is an expected approval safeguard, not evidence that replacement succeeded. The unrelated photosynthesis question illustrates an evidence-gap response. The transcript's automatic rendering of grading numbers is not reliable enough to establish a grading defect; actual objective scoring is covered by automated tests. Exact GUI-then-CLI ordering for one identical task is not established by this review; the progress example uses CLI then GUI. If the professor interprets that order strictly, add a short GUI-first progress demonstration followed by the equivalent CLI command.

## Screenshot provenance

Captured November 24 using the actual local browser application and the saved November 12 real-provider acceptance workspace. F01-F08, F11 and F12 reopen saved records through the GUI's Saved work controls. F09 and F10 run fresh deterministic calculations over that same saved history. These are not newly generated AI responses and are not test-model fixtures. The associated source/output evidence is `live-verification.json`; review ratings and reference answers are explicitly synthetic test-learner inputs. Historical reminder/plan dates are preserved, not shifted. No current successful AI connection is implied by the screenshots.

## Fixes and verification

- Exposed `plan --session-minutes` so terminal users can choose the same short study sessions as GUI users.
- Material-import failures now return a nonzero CLI status while preserving successful per-file results and duplicate detection.
- Aligned GUI numeric limits with the shared service validators.
- Added actionable HTTP 401 guidance without exposing credentials or provider response bodies.
- Corrected report verification: report generation now runs the actual tests and stops if they fail, instead of counting discovery-error placeholders as passing tests.

The full suite passes 53 tests. Compilation, JavaScript syntax, submission-file/credential-pattern scan and diff whitespace checks pass. Browser capture reported no JavaScript errors.

A fresh isolated live run on November 24 passed file ingestion and duplicate detection, then stopped at its first AI request with HTTP 401. A separate diagnostic confirmed the safe authentication error. No response tokens were reported; this does not establish billing charges. The original successful live evidence remains unchanged; the failed new run is recorded separately in `nov24-live-check.json`. Update `OPENAI_API_KEY` privately in `.env` or the environment and restart before retrying generation. This credential cannot be repaired from repository code.

## Remaining owner actions

Replace the rejected API credential locally and rerun the live verification command before claiming current live acceptance. If literal GUI-first ordering is required, add the short supplemental clip described above. Verify final publication and submit the repository URL through the course system. Historical development and billing evidence are outside the three follow-up fixes and have not been rewritten.
