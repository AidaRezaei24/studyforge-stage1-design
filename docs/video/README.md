# GUI then CLI demonstration supplement

[Download/play the 29.3-second supplement](gui-then-cli.mp4).

Task: view the existing course's learning progress. First, the GUI's Progress tab and Show progress action display the saved metrics. Then the real terminal runs `python -m studyforge progress --course "$COURSE"` and displays the same course's metrics. `COURSE` is the shell variable containing the existing course ID in the original recording.

This silent supplement reorders two excerpts from the [owner's original recording](https://youtu.be/vovxVKUw2TE). It adds explanatory title cards and crops the app/terminal area for readability. It does not alter commands, application output, execution speed or source data. It is an edited recording, not a newly executed session. The original full video remains linked for all twelve feature demonstrations and narration.

Edit sequence (original source times, seconds):

1. GUI title card: 3 seconds.
2. GUI action and results: 721.2-728.5.
3. CLI title card: 3 seconds.
4. Terminal command and results: 698.5-714.5.

The source dimensions are 1662 x 1080. Both excerpts crop the same 1600 x 820 application region at (20, 135), then pad to 1600 x 900. Output: H.264, 30 fps, MP4 with fast-start metadata, no audio. Source and output hashes are in `edit-manifest.json`. Complete video decoding and representative frames were checked after export.

To rebuild with an authorized local copy of the original video, install Pillow, provide FFmpeg, and run:

```sh
python scripts/build_demo_supplement.py --source original.mp4 --ffmpeg /path/to/ffmpeg
```
