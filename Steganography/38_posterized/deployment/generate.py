#!/usr/bin/env python3
"""38_posterized — generate handout/launch-poster.png.

Indexed-color PNG stego: the 256-entry PLTE consists of 128 near-identical
pairs (mates differ by exactly 1 in exactly one channel). Each pair encodes
one bit via palette ORDER:

    smaller RGB value listed first -> 0
    larger  RGB value listed first -> 1   (entries swapped)

When entries are swapped the pixel indices are remapped to match, so the
decoded image is pixel-for-pixel identical to the canonical layout — there
is no visible corruption. The payload is the flag BODY (inner text + "}",
16 bytes = 128 bits, MSB first); the standard `cyber_quest{` prefix is
boilerplate and is not stored (a full wrapped flag cannot fit in 128 bits).

Pairs are sequenced by ascending min(color value) so the solver can recover
bit order from the palette alone. Every entry has exactly one partner at
distance 1; the generator asserts this (and min base spacing) loudly.

Stdlib only. Deterministic (seed 38).
"""
import random
import struct
import zlib
import os

SEED = 38
W, H = 480, 600

FLAG_INNER = "p41r_0rd3r_8f2a"            # 15 chars
BODY = (FLAG_INNER + "}").encode()       # 16 bytes -> 128 bits -> 128 pairs
assert len(BODY) == 16
FULL_FLAG = "cyber_quest{" + FLAG_INNER + "}"
BITS = [(b >> (7 - i)) & 1 for b in BODY for i in range(8)]
assert len(BITS) == 128

rng = random.Random(SEED)

# ---------------------------------------------------------------- palette
def ramp(a, b, n):
    """Linear ramp of n RGB triples from a to b (inclusive)."""
    out = []
    for i in range(n):
        t = i / (n - 1) if n > 1 else 0.0
        out.append(tuple(int(round(a[c] + (b[c] - a[c]) * t)) for c in range(3)))
    return out

def dist2(p, q):
    return (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 + (p[2] - q[2]) ** 2

SKY_N = 52
sky = ramp((24, 16, 64), (250, 170, 90), SKY_N)          # indigo -> amber
sun = ramp((255, 244, 214), (228, 108, 36), 10)          # cream -> ember
halo = [(248, 170, 110), (240, 150, 112), (232, 130, 116), (224, 110, 122),
        (216, 92, 130), (208, 76, 138), (200, 62, 146), (192, 50, 154)]
moon = ramp((238, 238, 246), (176, 178, 200), 9)
stars = [(235, 235, 250), (250, 250, 235), (220, 228, 252),
         (255, 240, 240), (210, 235, 255)]
ground = ramp((12, 20, 34), (44, 40, 70), 10)
grid = [(255, 84, 168), (255, 140, 200), (140, 240, 245)]  # pink, lt pink, cyan
horizon = [(110, 230, 235)]
mtn_far = [(52, 32, 92), (44, 26, 80), (36, 20, 68)]
mtn_near = [(40, 22, 78), (32, 16, 66), (24, 12, 54)]
plate = [(14, 12, 30)]
cream = [(246, 238, 220)]
ink = [(12, 10, 18)]
keyline = [(120, 220, 230)]
border = [(8, 8, 14)]

# Confetti: bright accents, rejection-sampled far from everything so far.
fixed = sky + sun + halo + moon + stars + ground + grid + horizon + \
    mtn_far + mtn_near + plate + cream + ink + keyline + border
confetti = []
tries = 0
while len(confetti) < 19:
    tries += 1
    assert tries < 100000, "confetti sampling failed"
    c = (rng.randint(150, 255), rng.randint(60, 255), rng.randint(60, 255))
    if all(dist2(c, o) >= 100 for o in fixed + confetti):
        confetti.append(c)

bases = fixed + confetti
assert len(bases) == 128, f"need exactly 128 base colors, have {len(bases)}"

# Min spacing between bases: guarantees mates (d=1) can never create
# ambiguous pairings. Need >= 4 Euclidean (see module docstring logic).
for i in range(len(bases)):
    for j in range(i + 1, len(bases)):
        assert dist2(bases[i], bases[j]) >= 16, \
            f"bases too close: {bases[i]} vs {bases[j]}"
assert len(set(bases)) == 128, "duplicate base color"

# Mates: same color +/-1 in one channel (seeded choice).
mates = []
for b in bases:
    opts = []
    for ch in range(3):
        if b[ch] > 0:
            opts.append((ch, -1))
        if b[ch] < 255:
            opts.append((ch, +1))
    ch, d = opts[rng.randrange(len(opts))]
    m = list(b)
    m[ch] += d
    mates.append(tuple(m))

entries = bases + mates
assert len(set(entries)) == 256, "palette entries must all be distinct"

# Every entry must have EXACTLY ONE partner at distance 1 (its mate).
def partners_of(i):
    out = []
    for j in range(256):
        if i == j:
            continue
        d = [abs(entries[i][c] - entries[j][c]) for c in range(3)]
        if sum(1 for v in d if v) == 1 and sum(d) == 1:
            out.append(j)
    return out

for i in range(256):
    p = partners_of(i)
    assert len(p) == 1, f"entry {i} {entries[i]} has partners {p}"
# symmetry implied by construction; verify pairing covers all entries
seen, pairs = set(), []
for i in range(256):
    if i in seen:
        continue
    j = partners_of(i)[0]
    assert j not in seen
    seen.add(i)
    seen.add(j)
    pairs.append((i, j))
assert len(pairs) == 128

val = lambda c: (c[0] << 16) | (c[1] << 8) | c[2]
# Sequence pairs by ascending min color value (permutation-invariant order).
pairs.sort(key=lambda pr: min(val(entries[pr[0]]), val(entries[pr[1]])))

# Encode bits: 0 -> canonical (smaller first), 1 -> swapped.
final_palette = []
pair_slots = []      # (slot_a, slot_b) per payload pair, for usage fixups
for (i, j), bit in zip(pairs, BITS):
    ci, cj = entries[i], entries[j]
    lo, hi = (ci, cj) if val(ci) < val(cj) else (cj, ci)
    first, second = (lo, hi) if bit == 0 else (hi, lo)
    pair_slots.append((len(final_palette), len(final_palette) + 1))
    for rgb in (first, second):
        final_palette.append(rgb)

rgb_to_slot = {rgb: s for s, rgb in enumerate(final_palette)}
assert len(rgb_to_slot) == 256
mate_of_base = {b: m for b, m in zip(bases, mates)}

# ------------------------------------------------------------------ canvas
# Art is painted with BASE colors; per-pixel grain (10%) substitutes the
# mate (visually identical, +/-1). All 256 indices end up used.
SKY, SUN, HALO, MOON, STARS, GROUND = 0, 52, 62, 70, 79, 84
GRID, HOR, MF, MN = 94, 97, 98, 101
PLATE, CREAM, INK, KEY, BORD = 104, 105, 106, 107, 108
CONF = 109  # confetti bases: indices 109..127

sky_h = 340            # sky rows 0..339
gnd_y0 = 440           # ground starts here

canvas = [[None] * W for _ in range(H)]

def rect(x0, y0, x1, y1, base_idx):
    for y in range(max(0, y0), min(H, y1)):
        row = canvas[y]
        for x in range(max(0, x0), min(W, x1)):
            row[x] = base_idx

def disc(cx, cy, r, base_idx):
    for y in range(max(0, cy - r), min(H, cy + r + 1)):
        for x in range(max(0, cx - r), min(W, cx + r + 1)):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                canvas[y][x] = base_idx

def line(x0, y0, x1, y1, base_idx, w=2):
    steps = max(abs(x1 - x0), abs(y1 - y0)) * 2 + 1
    for i in range(steps + 1):
        t = i / steps
        x = int(round(x0 + (x1 - x0) * t))
        y = int(round(y0 + (y1 - y0) * t))
        for dy in range(-w // 2 + 1, w // 2 + 1):
            for dx in range(-w // 2 + 1, w // 2 + 1):
                if 0 <= x + dx < W and 0 <= y + dy < H:
                    canvas[y + dy][x + dx] = base_idx

# Sky bands (mapped below the top border so every band stays visible).
for y in range(sky_h):
    b = min(SKY_N - 1, max(0, y - 10) * SKY_N // (sky_h - 10))
    for x in range(W):
        canvas[y][x] = SKY + b

# Horizon haze between sky bands and ridges (overdrawn by mountains).
rect(0, sky_h, W, gnd_y0, SKY + SKY_N - 1)

# Stars (before sun/text so they sit behind).
for k in range(50):
    x = rng.randrange(4, W - 4)
    y = rng.randrange(4, 175)
    rect(x, y, x + 2, y + 2, STARS + (k % 5))

# Halo rings around the sun.
for k in range(8):
    disc(240, 300, 146 - k * 3, HALO + k)

# Moon with shaded rings.
for k in range(9):
    disc(395, 95, 30 - k * 2, MOON + k)

# Sun disc (10 radial bands, bright core).
for k in range(10):
    disc(240, 300, 120 - k * 9, SUN + min(9, k))

# Sun slits: horizontal cuts showing the sky behind (widen downward).
for (sy, sh) in ((336, 3), (352, 4), (368, 5), (384, 6)):
    sb = min(SKY_N - 1, max(0, sy - 10) * SKY_N // (sky_h - 10))
    for y in range(sy, min(sy + sh, H)):
        for x in range(W):
            if canvas[y][x] is not None and SUN <= canvas[y][x] < SUN + 10:
                canvas[y][x] = SKY + sb

# Confetti sparkles in the upper sky band.
for k in range(19):
    for _ in range(5):
        x = rng.randrange(14, W - 14)
        y = rng.randrange(130, 178)
        rect(x, y, x + 3, y + 3, CONF + k)

# Mountain ridges (shade by height thirds).
far_peaks = [(0, 400), (90, 356), (180, 396), (280, 362), (370, 398), (480, 372)]
near_peaks = [(0, 428), (120, 384), (240, 424), (360, 390), (480, 420)]

def ridge_h(peaks, x):
    for (x0, y0), (x1, y1) in zip(peaks, peaks[1:]):
        if x0 <= x <= x1:
            t = (x - x0) / (x1 - x0)
            return y0 + (y1 - y0) * t
    return peaks[-1][1]

for x in range(W):
    hf = ridge_h(far_peaks, x)
    for y in range(int(hf), gnd_y0):
        f = (y - hf) / max(1, gnd_y0 - hf)
        canvas[y][x] = MF + min(2, int(f * 3))
    hn = ridge_h(near_peaks, x)
    for y in range(int(hn), gnd_y0):
        f = (y - hn) / max(1, gnd_y0 - hn)
        canvas[y][x] = MN + min(2, int(f * 3))

# Ground bands.
for y in range(gnd_y0, H):
    b = min(9, (y - gnd_y0) * 10 // (H - gnd_y0))
    for x in range(W):
        canvas[y][x] = GROUND + b

# Perspective grid + horizon glow.
line(240, gnd_y0, -320, H, GRID, 2)
line(240, gnd_y0, 800, H, GRID, 2)
for bx in range(-240, 721, 80):
    line(240, gnd_y0, bx, H - 1, GRID, 2)
for gy in (462, 488, 518, 552):
    line(0, gy, W, gy, GRID + 2, 2)
rect(0, gnd_y0 - 2, W, gnd_y0 + 2, HOR)

# Tagline plate.
rect(40, 466, 440, 538, PLATE)
rect(40, 466, 440, 470, KEY)
rect(40, 534, 440, 538, GRID + 1)

# -------------------------------------------------------------------- font
FONT = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'C': ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'G': ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    '0': ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '4': ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '7': ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    '9': ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    '.': ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    '/': ("00001", "00001", "00010", "00010", "00100", "01000", "01000"),
    '-': ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
}

def text(s, cx, y, scale, base_idx):
    for ch in s:
        assert ch in FONT, f"missing glyph for {ch!r}"
    w = len(s) * 6 * scale - scale
    x = cx - w // 2
    for ch in s:
        g = FONT[ch]
        for r in range(7):
            for c in range(5):
                if g[r][c] == '1':
                    rect(x + c * scale, y + r * scale,
                         x + c * scale + scale, y + r * scale + scale,
                         base_idx)
        x += 6 * scale

text("ORDINARY ENGINEERING PRESENTS", 240, 20, 1, INK)
text("AURORA-9", 240, 44, 5, INK)
text("LAUNCH DAY", 240, 100, 3, INK)
text("EVERY COLOR HAS ITS PLACE.", 240, 478, 2, CREAM)
text("LOT 7 / GATES AT DUSK", 240, 512, 1, CREAM)
text("PALETTE ORDER MUST REMAIN CONSISTENT.", 240, 552, 1, CREAM)
text("POSTER-GEN EXPORT 0417", 240, 572, 1, CREAM)

# Frame.
rect(0, 0, W, 10, BORD)
rect(0, H - 10, W, H, BORD)
rect(0, 0, 10, H, BORD)
rect(W - 10, 0, W, H, BORD)
rect(14, 14, W - 14, 16, KEY)
rect(14, H - 16, W - 14, H - 14, KEY)

assert all(all(px is not None for px in row) for row in canvas), "unpainted pixel"

# ------------------------------------------------- indices + grain + write
index_rows = []
used = set()
for row in canvas:
    idx = []
    for b in row:
        base_rgb = bases[b]
        if rng.random() < 0.10:
            rgb = mate_of_base[base_rgb]
        else:
            rgb = base_rgb
        s = rgb_to_slot[rgb]
        used.add(s)
        idx.append(s)
    index_rows.append(idx)

assert len(used) <= 256
# Guarantee every slot is used at least once: point one partner pixel at
# each unused slot (same near-identical pair, no visible change).
if len(used) < 256:
    partner = {}
    for a, b in pair_slots:
        partner[a] = b
        partner[b] = a
    first_at = {}
    for y in range(H):
        for x in range(W):
            s = index_rows[y][x]
            if s not in first_at:
                first_at[s] = (x, y)
    for s in range(256):
        if s not in used:
            x, y = first_at[partner[s]]
            index_rows[y][x] = s
            used.add(s)
assert len(used) == 256, f"only {len(used)} palette slots used"

def chunk(typ, data):
    return (struct.pack(">I", len(data)) + typ + data +
            struct.pack(">I", zlib.crc32(typ + data) & 0xffffffff))

png = bytearray(b"\x89PNG\r\n\x1a\n")
png += chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 3, 0, 0, 0))
png += chunk(b"PLTE", b"".join(bytes(c) for c in final_palette))
raw = b"".join(b"\x00" + bytes(r) for r in index_rows)
png += chunk(b"IDAT", zlib.compress(raw, 9))
png += chunk(b"IEND", b"")

out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "..", "handout", "launch-poster.png")
os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, "wb") as f:
    f.write(bytes(png))

print(f"wrote {out} ({len(png)} bytes)")
print(f"flag: {FULL_FLAG}")

# ASCII preview (luminance) to eyeball composition.
CH = " .:-=+*#%@"
for y in range(0, H, 15):
    line_s = ""
    for x in range(0, W, 5):
        r, g, b = bases[canvas[y][x]]
        lum = (r * 30 + g * 59 + b * 11) // 100
        line_s += CH[lum * len(CH) // 256]
    print(line_s)
