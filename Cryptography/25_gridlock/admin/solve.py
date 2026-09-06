#!/usr/bin/env python3
"""gridlock — reference solve (no key required).

Player path, scripted:

  1. Read logo.enc.bmp. The 54-byte header is intact, the rest is
     AES-128-ECB ciphertext (see handout/pipeline.py).
  2. Count distinct 16-byte blocks: only a handful appear in the whole
     file, which is the ECB tell — identical plaintext blocks encrypt
     identically, so the shapes survive as a blocky ghost. Opening the
     file in any image viewer already shows the grid and the flag text.
  3. Recover exact pixels without the key: every ciphertext block in the
     file also appears at a known position (re-render the layout from
     deployment/make_handout.py and re-encrypt), so build a
     ciphertext->plaintext codebook, decode the image, and read the
     glyphs with the same 5x7 font the logo was drawn with.

Usage:
    python3 solve.py [HANDOUT_DIR]     # default: ../handout
"""

import os
import sys

HANDOUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "handout")
DEPLOYMENT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "..", "deployment")
sys.path.insert(0, DEPLOYMENT)
import make_handout as M  # noqa: E402  (organizer-side layout + AES)


def main():
    raw = open(os.path.join(HANDOUT, "logo.enc.bmp"), "rb").read()
    header, body = raw[:54], raw[54:]
    assert header[:2] == b"BM" and len(header) == 54
    assert len(body) % 16 == 0

    # --- the ECB tell -----------------------------------------------------
    blocks = [body[i:i + 16] for i in range(0, len(body), 16)]
    distinct = set(blocks)
    print(f"ciphertext blocks: {len(blocks)}, distinct: {len(distinct)}")
    assert len(distinct) < 16, "expected the ECB pattern leak"

    # --- re-render + re-encrypt: proves the artifact is well-formed -------
    pixels = M.render_logo()
    _, plain_body = M.to_bmp(pixels)
    assert M.aes_ecb_encrypt(plain_body, M.KEY) == body, "re-seal mismatch"

    # --- decode without the key -------------------------------------------
    codebook = {}
    for i in range(0, len(body), 16):
        codebook.setdefault(body[i:i + 16], plain_body[i:i + 16])
    decoded = b"".join(codebook[body[i:i + 16]]
                       for i in range(0, len(body), 16))
    assert decoded == plain_body, "codebook did not cover the file"

    # rows are bottom-up in the BMP body; flip to top-down pixel grid
    W, H, row = M.W, M.H, M.W * 4
    grid = bytearray(W * H * 4)
    for y in range(H):
        grid[y * row:(y + 1) * row] = decoded[(H - 1 - y) * row:(H - y) * row]

    def dark(x, y):
        o = (y * W + x) * 4
        return grid[o] < 128

    alphabet = sorted(M._FONT.keys())
    flag = ""
    per_row = 6
    nrows = (len(M.FLAG) + per_row - 1) // per_row
    for i in range(nrows):
        for c in range(per_row):
            idx = i * per_row + c
            if idx >= len(M.FLAG):
                break
            x0, y0, s = 96 + c * 48, 252 + i * 64, 8
            best, best_ch = -1, "?"
            for ch in alphabet:
                glyph = M._FONT[ch]
                score = 0
                total = 0
                for gy in range(7):
                    for gx in range(5):
                        want = glyph[gy][gx] == "#"
                        for dy in range(s):
                            for dx in range(s):
                                total += 1
                                if dark(x0 + (c * 0) + gx * s + dx,
                                        y0 + gy * s + dy) == want:
                                    score += 1
                if score > best:
                    best, best_ch = score, ch
            assert best == total, f"no exact glyph match at row {i} col {c}"
            flag += best_ch
    print("recovered flag:", flag)
    assert flag == M.FLAG
    print("SOLVE OK")


if __name__ == "__main__":
    main()
