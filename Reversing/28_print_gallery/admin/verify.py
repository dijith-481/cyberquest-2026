#!/usr/bin/env python3
"""Verify the approved artwork, PNG-only release, and visible-text recovery."""
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import zipfile
import zlib

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from solve import recover

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = 'cyber_quest{l0g_unw1nds_th3_g4ll3ry_7a3c9e}'
APPROVED_PIXELS = '407d60e33869fd7e66864af23c29f9790e9916e2499a5a4f99285b42c0b047f1'
SOURCE_HASH = 'bed9e3b0dd0fe99b2dc469151b19ad95191797c856134425ac221f94dd98b3b0'


def expected_ink(text):
    """Organizer-only target for checking the image, not a player decoder."""
    image = Image.new('L', (2048, 2048))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=64)
    for i, char in enumerate(text):
        row, col = divmod(i, 22)
        draw.text((492+44*col, 1470+90*row), char, font=font, fill=255)
    return np.array(image) > 0


def intersection_over_union(a, b):
    return float(np.count_nonzero(a & b) / max(1, np.count_nonzero(a | b)))


def check_text(straight, text):
    expected = expected_ink(text)
    recovered = (straight[:, :, 2] & 1).astype(bool)
    score = intersection_over_union(expected, recovered)
    assert score > .97, f'text geometry damaged: IoU={score:.4f}'
    glyph_scores = []
    for i in range(len(text)):
        row, col = divmod(i, 22)
        x, y = 492+44*col, 1470+90*row
        glyph_scores.append(intersection_over_union(expected[y:y+85, x:x+44], recovered[y:y+85, x:x+44]))
    assert min(glyph_scores) > .90, f'one or more glyphs damaged: {glyph_scores}'
    return score, min(glyph_scores)


def check_png(data):
    assert data[:8] == b'\x89PNG\r\n\x1a\n'
    pos, kinds, compressed = 8, [], bytearray()
    while pos < len(data):
        length = struct.unpack('>I', data[pos:pos+4])[0]
        kind = data[pos+4:pos+8]
        payload = data[pos+8:pos+8+length]
        crc = struct.unpack('>I', data[pos+8+length:pos+12+length])[0]
        assert zlib.crc32(kind+payload) & 0xffffffff == crc
        kinds.append(kind)
        if kind == b'IHDR':
            assert struct.unpack('>IIBBBBB', payload) == (4096, 4096, 8, 2, 0, 0, 0)
        elif kind == b'IDAT':
            compressed.extend(payload)
        pos += 12+length
        if kind == b'IEND':
            break
    assert pos == len(data), 'trailing payload'
    assert kinds[0] == b'IHDR' and kinds[-1] == b'IEND'
    assert all(k == b'IDAT' for k in kinds[1:-1]), 'metadata/extra chunks'
    assert EXPECTED.encode() not in data
    assert EXPECTED.encode() not in zlib.decompress(compressed)


def main():
    assert [p.name for p in (ROOT/'handout').iterdir()] == ['print-gallery.png']
    source = ROOT/'deployment/assets/Own2.png'
    assert hashlib.sha256(source.read_bytes()).hexdigest() == SOURCE_HASH
    manifest = json.loads((ROOT/'admin/manifest.json').read_text())
    for p in [source, ROOT/'handout/print-gallery.png', ROOT/'28_print_gallery.zip']:
        assert hashlib.sha256(p.read_bytes()).hexdigest() == manifest[p.name]
    approved = np.array(Image.open(ROOT/'admin/images/approved-straight.png').convert('RGB'))
    assert hashlib.sha256(approved.tobytes()).hexdigest() == APPROVED_PIXELS
    print('PASS: unchanged CindyJS source; straight artwork matches the approved preview pixel for pixel', flush=True)

    with tempfile.TemporaryDirectory(prefix='print-gallery-verify-') as temp:
        tmp = Path(temp)
        with zipfile.ZipFile(ROOT/'28_print_gallery.zip') as zf:
            assert zf.namelist() == ['print-gallery.png']
            assert zf.testzip() is None
            raw = zf.read('print-gallery.png')
            assert raw == (ROOT/'handout/print-gallery.png').read_bytes()
            (tmp/'print-gallery.png').write_bytes(raw)
        check_png(raw)
        rgb = np.array(Image.open(tmp/'print-gallery.png'))
        # Execute the independent solver with only the released image in its cwd.
        subprocess.run([sys.executable, str(ROOT/'admin/solve.py'), str(tmp/'print-gallery.png'),
                        '--output', str(tmp/'recovered')], cwd=tmp, check=True, stdout=subprocess.DEVNULL)
        straight = np.array(Image.open(tmp/'recovered/straightened.png'))
        score, worst = check_text(straight, EXPECTED)
        print(f'PASS: independent PNG-only recovery; text IoU {score:.4%}; worst glyph {worst:.4%}', flush=True)
        assert Image.open(tmp/'recovered/flag.png').getbbox() is not None

        # Straightening is essential to this comparison; absence of ink must fail.
        raw_small = np.array(Image.fromarray((rgb[:, :, 2]&1)*255).resize((2048, 2048), Image.Resampling.NEAREST)) > 0
        assert intersection_over_union(raw_small, expected_ink(EXPECTED)) < .20
        blank = straight.copy()
        blank[:, :, 2] &= 254
        try:
            check_text(blank, EXPECTED)
        except AssertionError:
            pass
        else:
            raise AssertionError('removed payload passed verification')
        print('PASS: PNG CRCs, no notes/metadata/trailer/plaintext; curled and erased-text controls fail', flush=True)

        fresh = tmp/'fresh'
        subprocess.run([sys.executable, str(ROOT/'deployment/generate.py'), '--output', str(fresh)],
                       check=True, stdout=subprocess.DEVNULL)
        assert [p.name for p in (fresh/'handout').iterdir()] == ['print-gallery.png']
        assert (fresh/'28_print_gallery.zip').read_bytes() == (ROOT/'28_print_gallery.zip').read_bytes()
        assert (fresh/'handout/print-gallery.png').read_bytes() == raw
        print('PASS: fresh offline build is byte-identical', flush=True)

        variant = 'cyber_quest{str41ght_v13w_92ab}'
        subprocess.run([sys.executable, str(ROOT/'deployment/generate.py'), '--output', str(tmp/'variant'),
                        '--flag', variant], check=True, stdout=subprocess.DEVNULL)
        other = np.array(Image.open(tmp/'variant/handout/print-gallery.png'))
        check_text(recover(other), variant)
        print('PASS: unchanged independent inverse recovers a different flag as visible text', flush=True)
    print('VERIFY OK - approved artwork and readable flag recovered from the PNG-only release')


if __name__ == '__main__':
    main()
