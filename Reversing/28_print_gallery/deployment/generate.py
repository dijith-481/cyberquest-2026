#!/usr/bin/env python3
"""Approved CindyJS artwork: straight text mask -> public spiral map -> PNG."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from geometry import pixel_plane, texture_sample, straight_from_curled, sample_mask

ROOT = Path(__file__).resolve().parents[1]
FLAG = "cyber_quest{l0g_unw1nds_th3_g4ll3ry_7a3c9e}"
SIZE = 4096
PROOF_SIZE = 2048


def text_mask(flag):
    if not (flag.startswith("cyber_quest{") and flag.endswith("}")):
        raise ValueError("expected cyber_quest{...}")
    if len(flag) > 44 or any(ord(c) < 33 or ord(c) > 126 for c in flag):
        raise ValueError("flag must fit in 44 printable non-space ASCII characters")
    image = Image.new("L", (PROOF_SIZE, PROOF_SIZE), 0)
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=64)
    for index, char in enumerate(flag):
        row, col = divmod(index, 22)
        draw.text((492 + col*44, 1470 + row*90), char, font=font, fill=255)
    return np.array(image) > 0


def save_png(array, path):
    Image.fromarray(np.asarray(array, dtype=np.uint8)).save(path, compress_level=6)


def render(texture, mask, size, curled):
    result = np.empty((size, size, 3), np.uint8)
    for first in range(0, size, 64):
        z = pixel_plane(size, first, 64)
        rgb = np.uint8(np.clip(np.rint(texture_sample(texture, z, curled)), 0, 255))
        # Artwork and text use identical coordinates. Preserve the discrete
        # bit-plane with nearest-neighbour sampling; interpolate artwork only.
        straight_z = straight_from_curled(z) if curled else z
        ink = sample_mask(mask, straight_z).astype(np.uint8)
        rgb[:, :, 2] = (rgb[:, :, 2] & 254) | ink
        result[first:first + len(z)] = rgb
    return result


def build(output, source, flag, proofs=False):
    with Image.open(source) as original:
        if original.size != (1196, 1360):
            raise ValueError("use the approved unmodified CindyJS Own2.png texture")
        texture = np.array(original.convert("RGB"), dtype=float)
    mask = text_mask(flag)
    handout = output / "handout"
    handout.mkdir(parents=True, exist_ok=True)
    (handout / "RESTORATION.txt").unlink(missing_ok=True)
    extra = [p.name for p in handout.iterdir() if p.name != "print-gallery.png"]
    if extra:
        raise ValueError(f"unexpected files in player handout: {extra}")
    save_png(render(texture, mask, SIZE, True), handout / "print-gallery.png")
    archive = output / "28_print_gallery.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        entry = zipfile.ZipInfo("print-gallery.png", (2026, 1, 1, 0, 0, 0))
        entry.compress_type = zipfile.ZIP_DEFLATED
        entry.external_attr = 0o100644 << 16
        zf.writestr(entry, (handout / "print-gallery.png").read_bytes())
    admin = output / "admin"
    admin.mkdir(exist_ok=True)
    paths = [source, handout / "print-gallery.png", archive]
    manifest = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    (admin / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    if proofs:
        images = admin / "images"
        images.mkdir(exist_ok=True)
        save_png(mask.astype(np.uint8)*255, images / "straight-flag-source.png")
        save_png(render(texture, mask, PROOF_SIZE, False), images / "straight-with-hidden-flag.png")
        # Exact approved 1000px view, independent of the hidden bit-plane.
        clean = texture_sample(texture, pixel_plane(1000), False)
        save_png(np.clip(clean, 0, 255), images / "approved-straight.png")
    return archive


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT)
    parser.add_argument("--source", type=Path, default=ROOT / "deployment/assets/Own2.png")
    parser.add_argument("--flag", default=FLAG)
    parser.add_argument("--proofs", action="store_true")
    args = parser.parse_args()
    print(build(args.output, args.source, args.flag, args.proofs))
