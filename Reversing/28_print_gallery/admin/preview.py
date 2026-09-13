#!/usr/bin/env python3
"""Show the approved scene, final curled PNG, and PNG-only recovered result."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
IMAGES = ROOT/'admin/images'
canvas = Image.new('RGB', (1800, 720), '#f5f3ef')
draw = ImageDraw.Draw(canvas)
title, label, small = (ImageFont.load_default(size=n) for n in (28, 20, 16))
draw.text((32, 24), 'PRINT GALLERY / APPROVED ARTWORK', fill='#242424', font=title)
draw.text((32, 65), 'Same CindyJS geometry | Hidden readable text | Player ZIP contains one PNG', fill='#555555', font=small)
panels = [
    (IMAGES/'straight-with-hidden-flag.png', '01  Straight view', 'Flag painted into the blue low bit'),
    (ROOT/'handout/print-gallery.png', '02  Player export', 'The same artwork, curled back'),
    (IMAGES/'straightened.png', '03  Recovered view', 'Reversed from the released PNG'),
    (IMAGES/'flag-crop.png', '04  Recovered flag', 'Read the text and join the two lines'),
]
for i, (path, heading, caption) in enumerate(panels):
    left = 32+i*442
    draw.text((left, 117), heading, fill='#242424', font=label)
    image = ImageOps.contain(Image.open(path).convert('RGB'), (410, 490), Image.Resampling.LANCZOS)
    canvas.paste(image, (left+(410-image.width)//2, 165+(490-image.height)//2))
    draw.text((left, 678), caption, fill='#555555', font=small)
canvas.save(IMAGES/'overview.png')
