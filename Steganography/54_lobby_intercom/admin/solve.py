#!/usr/bin/env python3
"""Reference solve for Lobby Intercom (challenge 54).

Reads the WAV, and for every cell of the message grid measures the
magnitude at that cell's frequency over that cell's time window with the
Goertzel algorithm (a single-frequency DFT). A cell whose magnitude clears
the noise floor is ink. The ink pattern is read back through the same
5x7 font the generator used, giving the flag.

There is no LSB extraction anywhere in this file, and there is no full
STFT: the solver probes only the (time, frequency) coordinates the
message band defines, which is both faster and far less ambiguous than
thresholding an FFT.

Usage:
    python3 solve.py handout/lobby_intercom.wav
"""

import math
import struct
import sys
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "deployment"))
from generate import (  # noqa: E402
    FONT, F_LO, F_HI, GLYPH_W, GLYPH_H, ADVANCE, COL_MS, RATE, SPACE,
)

START_PAD = 0.3          # seconds of lead-in before the first column
BURST = COL_MS / 1000.0 * 0.92


def goertzel(samples, start, count, freq, rate):
    """Magnitude of `freq` over samples[start:start+count]."""
    k = int(0.5 + (count * freq) / rate)
    w = (2.0 * math.pi / count) * k
    coeff = 2.0 * math.cos(w)
    s1 = s2 = 0.0
    for i in range(start, min(start + count, len(samples))):
        s0 = samples[i] + coeff * s1 - s2
        s2, s1 = s1, s0
    return math.sqrt(s1 * s1 + s2 * s2 - coeff * s1 * s2) / count


def load(path):
    with wave.open(str(path), "rb") as w:
        if w.getnchannels() != 1 or w.getsampwidth() != 2:
            raise SystemExit("expected mono 16-bit PCM")
        rate = w.getframerate()
        raw = w.readframes(w.getnframes())
    s = struct.unpack(f"<{len(raw) // 2}h", raw)
    return [v / 32768.0 for v in s], rate


def measure(samples, rate, ncols):
    """Return an ncols x GLYPH_H grid of magnitudes."""
    step = (F_HI - F_LO) / (GLYPH_H - 1)
    win = int(BURST * rate)
    grid = []
    for x in range(ncols):
        col = []
        for y in range(GLYPH_H):
            freq = F_LO + (GLYPH_H - 1 - y) * step
            start = int((START_PAD + x * COL_MS / 1000.0) * rate)
            col.append(goertzel(samples, start, win, freq, rate))
        grid.append(col)
    return grid


def probe_columns(duration):
    """Upper bound on columns from the file length alone.

    Deliberately generous. The generator's trailing silence is an internal
    detail, and an earlier version of this function subtracted a guessed
    pad, which silently clipped the last character off the message. The
    real message extent is found by trimming blank columns in `trim`.
    """
    return int((duration - START_PAD) / (COL_MS / 1000.0)) + 1


def threshold_for(grid):
    flat = sorted(v for col in grid for v in col)
    floor = flat[len(flat) // 2]          # median == the noise floor
    ceiling = flat[-1]
    if ceiling <= floor * 3:
        raise SystemExit("no message band found: dynamic range too small")
    return floor + (ceiling - floor) * 0.35, floor, ceiling


def trim(grid, thresh):
    """Drop trailing columns that contain no ink."""
    last = 0
    for x, col in enumerate(grid):
        if any(v > thresh for v in col):
            last = x + 1
    return grid[:last] if last else grid


def decode(grid):
    """Read the ink grid back into characters."""
    thresh, floor, ceiling = threshold_for(grid)
    grid = trim(grid, thresh)
    ncols = len(grid)

    out = []
    nchars = -(-ncols // ADVANCE)          # ceil
    for ci in range(nchars):
        rows = []
        for y in range(GLYPH_H):
            x0 = ci * ADVANCE
            rows.append("".join(
                "#" if (x0 + x < ncols and grid[x0 + x][y] > thresh) else " "
                for x in range(GLYPH_W)))
        pattern = tuple(rows)
        match = next((c for c, g in FONT.items() if tuple(g) == pattern), None)
        out.append(match if match else (" " if pattern == tuple(SPACE) else "?"))
    return "".join(out), thresh, floor, ceiling


def render(grid, thresh):
    step = (F_HI - F_LO) / (GLYPH_H - 1)
    for y in range(GLYPH_H):
        print(f"  {F_LO + (GLYPH_H - 1 - y) * step:7.0f} Hz |" + "".join(
            "#" if grid[x][y] > thresh else "." for x in range(len(grid))) + "|")


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    path = Path(sys.argv[1])
    samples, rate = load(path)
    if rate != RATE:
        raise SystemExit(f"expected {RATE} Hz, got {rate}")

    duration = len(samples) / rate
    ncols = probe_columns(duration)
    print(f"{duration:.2f}s @ {rate} Hz, probing up to {ncols} columns "
          f"x {GLYPH_H} rows over {F_LO:.0f}-{F_HI:.0f} Hz")

    grid = measure(samples, rate, ncols)
    thresh, floor, ceiling = threshold_for(grid)
    grid = trim(grid, thresh)
    render(grid, thresh)
    print(f"\nnoise floor {floor:.5f}  peak {ceiling:.5f}  threshold {thresh:.5f}")
    print(f"inked columns: {len(grid)}  ({len(grid) / ADVANCE:.2f} characters)")

    text, _t, _f, _c = decode(grid)
    print(f"decoded: {text}")

    if "?" in text:
        print("warning: some glyphs did not match the font", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
