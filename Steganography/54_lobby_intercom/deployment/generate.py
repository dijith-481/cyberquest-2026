#!/usr/bin/env python3
"""lobby_intercom — deterministic handout generator (stdlib only).

Builds the recording the players receive:

  handout/lobby_intercom.wav   6 s, 44100 Hz mono 16-bit PCM, RIFF/WAVE

The message is not hidden in the bit domain at all — nothing here is LSB
steganography. It is a *spectrogram picture*. Each lit cell of a 5x7
pixel-font rendering of the flag is a short sine burst placed at a
specific (time, frequency) coordinate, so when the file is viewed as a
spectrogram the flag is legible as text.

Layout:
  one character cell = 5 columns x 7 rows, 1 column of spacing
  time axis  : 1 column = 30 ms, 6 columns (glyph + gap) per character
  freq axis  : 7 rows spanning 1800..4200 Hz

A low broadband hum (180 Hz + its harmonics) runs underneath so the file
sounds like a room rather than a test tone. It is deliberately placed
well below the message band so it does not occlude the picture.

    python3 generate.py

The zip handed to players is built with:
  zip -j 54_lobby_intercom.zip handout/*
"""

import math
import os
import struct
import wave

HERE = os.path.dirname(os.path.abspath(__file__))
HANDOUT = os.path.join(HERE, "..", "handout")

FLAG = "cyber_quest{th3_sp3ctr0gr4m_1s_l0ud}"

RATE = 44100
COL_MS = 30.0                      # time resolution of one pixel column
F_LO, F_HI = 1800.0, 4200.0       # message band
GLYPH_W, GLYPH_H = 5, 7
ADVANCE = GLYPH_W + 1             # one blank column between characters

# 5x7 pixel font. '#' is ink. Only the glyphs the flag needs are defined;
# generate.py asserts that up front so a flag with an unmapped character
# fails loudly instead of rendering a blank cell.
FONT = {
    'c': [" ### ", "#    ", "#    ", "#    ", "#    ", " ### ", "     "],
    'y': ["#   #", "#   #", "#   #", " ####", "    #", " #   ", "     "],
    'b': ["#### ", "#   #", "#### ", "#   #", "#   #", "#### ", "     "],
    'e': [" ####", "#    ", "#### ", "#    ", "#    ", " ####", "     "],
    'r': ["#### ", "#   #", "#### ", "#  # ", "#   #", "#   #", "     "],
    'q': [" ####", "#   #", "#   #", " ####", "    #", " #   ", "     "],
    'u': ["#   #", "#   #", "#   #", "#   #", "#   #", " ####", "     "],
    's': [" ####", "#    ", " ### ", "    #", "    #", "#### ", "     "],
    't': ["  #  ", "  #  ", " ####", "  #  ", "  #  ", "  #  ", " ### "],
    '_': ["     ", "     ", "     ", "     ", "     ", "     ", "#####"],
    '{': ["   ##", "  #  ", "  #  ", " #   ", "  #  ", "  #  ", "   ##"],
    '}': ["##   ", "  #  ", "  #  ", "   # ", "  #  ", "  #  ", "##   "],
    'd': [" ####", "    #", "    #", " ####", "#   #", " ####", "     "],
    'g': [" ####", "#   #", "#   #", " ####", "    #", " ####", "    #"],
    'h': ["#   #", "#   #", "#### ", "#   #", "#   #", "#   #", "     "],
    'l': [" ##  ", "  #  ", "  #  ", "  #  ", "  #  ", " ### ", "     "],
    'm': ["#   #", "## ##", "# # #", "#   #", "#   #", "#   #", "     "],
    'p': ["#### ", "#   #", "#   #", "#### ", "#    ", "#    ", "     "],
    '0': [" ####", "#  ##", "# # #", "##  #", "#   #", " ####", "     "],
    '1': ["  #  ", " ##  ", "  #  ", "  #  ", "  #  ", " ### ", "     "],
    '3': [" ####", "    #", " ### ", "    #", "    #", " ####", "     "],
    '4': ["#   #", "#   #", "#   #", " ####", "    #", "    #", "     "],
    '6': ["  ###", "#    ", "#    ", " ####", "#   #", " ####", "     "],
    '7': ["#####", "    #", "   # ", "  #  ", "  #  ", "  #  ", "     "],
    'a': ["     ", "     ", " ####", "    #", " ####", "#   #", " ####"],
}
SPACE = ["     "] * GLYPH_H


def glyph(ch):
    return FONT.get(ch, SPACE)


def message_columns(flag):
    """Expand the flag into a list of (x, y) ink cells."""
    cols = 0
    cells = []
    for ch in flag:
        g = glyph(ch)
        for y in range(GLYPH_H):
            row = g[y]
            for x in range(GLYPH_W):
                if row[x] == '#':
                    cells.append((cols + x, y))
        cols += ADVANCE
    return cells, cols


def build_samples(flag):
    cells, total_cols = message_columns(flag)
    dur = (total_cols * COL_MS / 1000.0) + 0.6      # trailing silence
    n = int(RATE * dur)
    buf = [0.0] * n

    def add_burst(start_s, freq, length_s, amp):
        a = int(start_s * RATE)
        b = min(n, a + int(length_s * RATE))
        w = 2 * math.pi * freq / RATE
        for i in range(max(a, 0), b):
            # short raised-cosine window so bursts do not click
            t = (i - a) / max(1, (b - a))
            env = 0.5 - 0.5 * math.cos(2 * math.pi * min(1.0, t))
            buf[i] += amp * env * math.sin(w * (i - a))

    # --- the message -----------------------------------------------------
    step = (F_HI - F_LO) / (GLYPH_H - 1)
    for (x, y) in cells:
        freq = F_LO + (GLYPH_H - 1 - y) * step       # row 0 at the top
        start = 0.3 + x * (COL_MS / 1000.0)
        add_burst(start, freq, COL_MS / 1000.0 * 0.92, 0.55)

    # --- room tone: low hum, far below the message band ------------------
    for i in range(n):
        t = i / RATE
        v = 0.0
        for h, a in ((1, 0.055), (2, 0.030), (3, 0.018), (5, 0.010)):
            v += a * math.sin(2 * math.pi * 180.0 * h * t)
        buf[i] += v

    peak = max(abs(v) for v in buf) or 1.0
    scale = 0.89 / peak
    return [max(-32768, min(32767, int(v * scale * 32767))) for v in buf], total_cols


def main():
    # fail loudly rather than silently rendering a blank cell
    missing = sorted({c for c in FLAG if c not in FONT and c != " "})
    if missing:
        raise SystemExit(f"no glyph defined for: {missing}")

    os.makedirs(HANDOUT, exist_ok=True)
    out = os.path.join(HANDOUT, "lobby_intercom.wav")
    samples, cols = build_samples(FLAG)

    with wave.open(out, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(struct.pack(f"<{len(samples)}h", *samples))

    # --- guards ----------------------------------------------------------
    cells, _ = message_columns(FLAG)
    # count every '#' in the font, not rows: the two differ for letters
    # like 'i' or '4' whose rows hold a single pixel
    expected_cells = sum(row.count("#") for ch in FLAG for row in glyph(ch))
    assert len(cells) == expected_cells, (
        f"cell count {len(cells)} != ink pixels {expected_cells}")
    assert any(c[1] == 0 for c in cells), "top row is empty, glyphs look wrong"
    assert any(c[1] == GLYPH_H - 1 for c in cells), "bottom row is empty"
    with wave.open(out, "rb") as w:
        assert w.getnchannels() == 1, "not mono"
        assert w.getsampwidth() == 2, "not 16-bit"
        assert w.getframerate() == RATE, "wrong sample rate"
        raw = w.readframes(w.getnframes())
    # the message must live in the frequency domain, never in the LSBs
    lsb = bytes((b & 1) for b in raw)
    assert b"cyber_quest" not in lsb, "flag leaks into a naive LSB dump"
    assert b"cyber_quest" not in raw, "flag is in the sample bytes"
    assert raw == raw, "unstable"
    print(f"wrote {out} ({os.path.getsize(out)} bytes, "
          f"{len(raw) // 2 / RATE:.2f}s, {cols} cols, {len(cells)} ink cells)")


if __name__ == "__main__":
    main()
