"""Tile a folder of stills into one contact sheet, so a whole reel can be checked in one look.
`sheet.py STILLS_DIR OUT.jpg [--cols 6] [--width 320]`. Each tile is labelled with its file name, which render.py sets to the time."""
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ap = argparse.ArgumentParser()
ap.add_argument("dir"); ap.add_argument("out")
ap.add_argument("--cols", type=int, default=6); ap.add_argument("--width", type=int, default=320)
a = ap.parse_args()

files = sorted(p for p in Path(a.dir).iterdir() if p.suffix.lower() in (".png", ".jpg", ".jpeg"))
if not files: raise SystemExit(f"no stills in {a.dir}")
first = Image.open(files[0]); w = a.width; h = round(first.height * w / first.width)
pad, lab, cols = 10, 30, min(a.cols, len(files)); rows = -(-len(files) // cols)
sheet = Image.new("RGB", (cols * (w + pad) + pad, rows * (h + lab + pad) + pad), (24, 22, 20))
try: font = ImageFont.load_default(size=18)
except TypeError: font = ImageFont.load_default()
d = ImageDraw.Draw(sheet)
for k, p in enumerate(files):
    x, y = pad + (k % cols) * (w + pad), pad + (k // cols) * (h + lab + pad)
    d.text((x + 2, y + 5), p.stem, fill=(255, 200, 160), font=font)
    sheet.paste(Image.open(p).convert("RGB").resize((w, h)), (x, y + lab))
sheet.save(a.out, quality=88)
print(f"wrote {a.out}  {len(files)} stills, {sheet.width}x{sheet.height}")
