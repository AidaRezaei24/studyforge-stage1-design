"""Build a silent GUI-then-CLI excerpt from the owner's existing demo recording.

Requires Pillow and FFmpeg. Example:
python scripts/build_demo_supplement.py --source original.mp4 --ffmpeg /path/to/ffmpeg
The source is https://youtu.be/vovxVKUw2TE; original actions/results are unchanged.
"""
import argparse
from pathlib import Path
import subprocess
import tempfile

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]


def card(path, heading, instruction):
    image = Image.new('RGB', (1600, 900), '#10251b')
    draw = ImageDraw.Draw(image)
    draw.text((100, 125), 'STUDYFORGE / SAME TASK, TWO INTERFACES',
              font=ImageFont.load_default(size=32), fill='#bdd4aa')
    draw.text((100, 270), heading, font=ImageFont.load_default(size=66), fill='white')
    draw.text((100, 410), instruction, font=ImageFont.load_default(size=35), fill='white')
    draw.text((100, 680), 'Silent, reordered excerpts from the original owner recording.',
              font=ImageFont.load_default(size=27), fill='#bdd4aa')
    draw.text((100, 725), 'Only sequence, crop and title cards changed; commands/results are original.',
              font=ImageFont.load_default(size=27), fill='#bdd4aa')
    image.save(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--ffmpeg', default='ffmpeg')
    parser.add_argument('--output', type=Path, default=ROOT / 'docs/video/gui-then-cli.mp4')
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='studyforge-demo-') as directory:
        gui_card, cli_card = [Path(directory) / name for name in ('gui.png', 'cli.png')]
        card(gui_card, '1. View progress in the GUI', 'Select Progress, then click Show progress.')
        card(cli_card, '2. View the same progress in the CLI',
             'Run: python -m studyforge progress --course "$COURSE"')
        filters = (
            '[0:v]split=2[g][c];'
            '[g]trim=start=721.2:end=728.5,setpts=PTS-STARTPTS,'
            'crop=1600:820:20:135,pad=1600:900:0:40:color=0x10251b,fps=30,setsar=1[gui];'
            '[c]trim=start=698.5:end=714.5,setpts=PTS-STARTPTS,'
            'crop=1600:820:20:135,pad=1600:900:0:40:color=0x10251b,fps=30,setsar=1[cli];'
            '[1:v]fps=30,setsar=1[title1];[2:v]fps=30,setsar=1[title2];'
            '[title1][gui][title2][cli]concat=n=4:v=1:a=0[out]')
        subprocess.run([args.ffmpeg, '-hide_banner', '-loglevel', 'error', '-y',
                        '-i', str(args.source), '-loop', '1', '-t', '3', '-i', str(gui_card),
                        '-loop', '1', '-t', '3', '-i', str(cli_card),
                        '-filter_complex', filters, '-map', '[out]', '-an',
                        '-c:v', 'libx264', '-preset', 'fast', '-crf', '20',
                        '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(args.output)], check=True)
    print(f'Created {args.output} (29.3 seconds; GUI first, CLI second).')


if __name__ == '__main__':
    main()
