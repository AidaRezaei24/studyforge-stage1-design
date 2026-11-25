# Runtime screenshots

F01-gui.png through F12-gui.png are actual browser captures from the running StudyForge GUI, captured November 24, 2026 at 1200 x 1000 pixels. The report embeds one image per feature; open the PNGs for full-resolution text.

Source: the saved November 12 real-provider acceptance workspace, corresponding to `../live-verification.json`. F01-F08, F11 and F12 reopen persisted records through Saved work. F09 and F10 calculate a fresh recommendation and progress over that history. These images preserve historical dates and synthetic test-learner inputs; they do not assert a new successful provider request. No model response was fabricated or substituted during capture.

To reproduce with your own workspace, start `python -m studyforge --db PATH serve`, navigate each feature, run the task or reopen the corresponding saved record, and capture the browser window. For AI generation configure a valid key privately first. See `../professor-review.md` for current authentication status and video review.
