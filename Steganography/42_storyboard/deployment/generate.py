#!/usr/bin/env python3
"""42_storyboard — generate handout/storyboard.mkv.

Flagship stego: a retro ASCII-art dance clip (116x64 cells) in a sub-megabyte
MKV (AV1). The hidden channel is the CHOICE of ASCII glyph: every
brightness level has two near-equal-ink twins; variant 0 vs 1 carries a bit.

Normal frames use random variants (noise). Every one of the 29 scenes starts
with the same source image rendered twice (frame A with random mask R, frame
B with R XOR the QR row mask). Comparing the twins yields one QR row per
scene; 29 scenes -> 29x29 (Version 3) QR -> flag.

Geometry: 116 ascii cols / 29 qr cols = 4 ascii cols per module.
Every cell in a vertical band carries the same row bit (majority vote).

Stdlib only. Deterministic (sha256-counter PRNG). Pixels piped to ffmpeg
(AV1 via libsvtav1, yuv420p, MKV). No copyrighted footage: the "dance clip" is real licensed
footage, "Budots Dance Video" by Sherwin Tuna, CC BY 3.0,
via Wikimedia Commons (deployment/source.mp4 is a trimmed, downscaled
derivative; see deployment/ATTRIBUTION.txt). The clip's luminance selects
the glyph class and its hue selects the neon color.
"""
import argparse
import colorsys
import hashlib
import os
import subprocess
import sys

# ------------------------------------------------------------------ constants
COLS, ROWS = 116, 64          # ascii cells
CELL_W, CELL_H = 6, 8         # pixels per cell (5x7 glyph + 1px pad)
GW, GH = COLS * CELL_W, ROWS * CELL_H   # grid pixels
ML, MR, MT, MB = 8, 8, 20, 18
FW, FH = GW + ML + MR, GH + MT + MB     # 712 x 550 frame
FPS = 24
SCENES = 29
QR_N = 29                     # version 3
BAND_W = COLS // QR_N         # 4
assert COLS % QR_N == 0

BG = (5, 5, 8)
NEON = [  # retro terminal palette (all safely above the solver threshold)
    (0, 220, 230),    # cyan
    (255, 90, 200),   # pink
    (255, 220, 80),   # yellow
    (80, 255, 140),   # green
    (235, 235, 240),  # white
]

# brightness twins: (variant0, variant1); class k <-> PAIRS[k]
NCLS = 5
PAIRS = [('@', 'M'), ('%', 'W'), ('#', '8'), ('*', 'o'), ('+', '=')]
# NOTE: the lightest pairs (':',';') and ('.',',') were cut: their twin
# masks differ by only 1-3 bits, which lossy encoding erases. Minimum
# twin Hamming distance below is 13 bits.
FONT = {
    '@': (".###.", "#...#", "#.###", "#.#.#", "#.###", "#....", ".###."),
    'M': ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    '%': ("##..#", "#...#", "..#..", "..#..", ".#...", "#...#", "#..##"),
    'W': ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    '#': (".#.#.", "..#..", "#####", "..#..", ".#.#.", "#####", "..#.."),
    '8': (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    '*': (".....", ".#.#.", "..#..", "#####", "..#..", ".#.#.", "....."),
    'o': (".....", ".....", ".###.", "#...#", "#...#", "#...#", ".###."),
    '+': (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    '=': (".....", ".....", "#####", ".....", "#####", ".....", "....."),
    ':': (".....", ".....", "..#..", ".....", ".....", "..#..", "....."),
    ';': (".....", ".....", "..#..", ".....", ".....", "..#..", ".#..."),
    '.': (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ',': (".....", ".....", ".....", ".....", "..#..", "..#..", ".#..."),
    # --- chrome-only capitals/digits (terminal margins; never used in the grid)
    'A': (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    'B': ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    'D': ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    'E': ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    'F': ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    'G': (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    'H': ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    'K': ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    'L': ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    'O': (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    'P': ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    'R': ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    'S': (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    'T': ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    'V': ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    'X': ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    'Y': ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    '0': (".###.", "#..##", "#.#.#", "#.#.#", "##..#", "#...#", ".###."),
    '1': ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    '2': (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    '3': ("#####", "...#.", "..#..", "...#.", "....#", "#...#", ".###."),
    '4': ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    '5': (".####", "#....", "#....", "####.", "....#", "....#", "####."),
    '6': ("..###", ".#...", "#....", "#.###", "#...#", "#...#", ".###."),
    '7': ("#####", "....#", "...#.", "..#..", "..#..", "..#..", "..#.."),
    '9': (".###.", "#...#", "#...#", ".####", "....#", "...#.", "###.."),
    '/': ("....#", "....#", "...#.", "...#.", "..#..", ".#...", ".#..."),
}
GLYPH_OX, GLYPH_OY = 0, 0  # 5x7 glyph placement inside the 6x8 cell
# Ordered dither (Bayer 4x4): spreads class thresholds so flat regions cross
# brightness bands as stable stipple instead of flipping all at once. Pure
# per-cell function of luminance, so twin frames still match exactly and the
# mask set stays exactly 14 glyphs. Kills intra-scene diff spikes.
BAYER4 = (0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5)
DITHER_AMP = 0.6  # +-4.5 luminance units: enough to break up band-flip
# cliffs, small enough to stay inter-prediction friendly


def check_font():
    masks = {}
    for ch, rows in FONT.items():
        assert len(rows) == 7 and all(len(r) == 5 for r in rows), ch
        m = tuple(1 if c == '#' else 0 for r in rows for c in r)
        assert m not in masks.values(), f"duplicate mask: {ch}"
        masks[ch] = m
    for a, b in PAIRS:
        ia = sum(masks[a])
        ib = sum(masks[b])
        assert abs(ia - ib) <= 5, f"twins too far apart: {a}={ia} {b}={ib}"
    return masks


MASKS = check_font()

# ------------------------------------------------------------------- QR core
EXP = [0] * 512
LOG = [0] * 256
_x = 1
for _i in range(255):
    EXP[_i] = _x
    LOG[_x] = _i
    _x <<= 1
    if _x & 0x100:
        _x ^= 0x11D
for _i in range(255, 512):
    EXP[_i] = EXP[_i - 255]


def gf_mul(a, b):
    return 0 if a == 0 or b == 0 else EXP[LOG[a] + LOG[b]]


def rs_generator(nsym):
    # Standard QR generator: g[0] is the x^nsym coefficient (=1).
    g = [1]
    for i in range(nsym):
        ng = [0] * (len(g) + 1)
        for j in range(len(g)):
            ng[j] ^= gf_mul(g[j], EXP[i])
            ng[j + 1] ^= g[j]
        g = ng
    return g[::-1]


def rs_encode(data, nsym):
    gen = rs_generator(nsym)
    out = list(data) + [0] * nsym
    for i in range(len(data)):
        coef = out[i]
        if coef:
            for j in range(len(gen)):
                out[i + j] ^= gf_mul(gen[j], coef)
    return out[len(data):]


def format_bits(ec, mask):
    ec_map = {'L': 0b01, 'M': 0b00, 'Q': 0b11, 'H': 0b10}
    data = (ec_map[ec] << 3) | mask
    v = data << 10
    for i in range(14, 9, -1):
        if (v >> i) & 1:
            v ^= 0x537 << (i - 10)
    return ((data << 10) | (v & 0x3FF)) ^ 0x5412


SIZE = QR_N
ALIGN = 22  # version 3 alignment pattern center


def build_base():
    m = [[None] * SIZE for _ in range(SIZE)]
    func = [[False] * SIZE for _ in range(SIZE)]

    def finder(r, c):
        pat = ["1111111", "1000001", "1011101", "1011101",
               "1011101", "1000001", "1111111"]
        for dr in range(-1, 8):
            for dc in range(-1, 8):
                rr, cc = r + dr, c + dc
                if 0 <= rr < SIZE and 0 <= cc < SIZE:
                    if 0 <= dr < 7 and 0 <= dc < 7:
                        m[rr][cc] = int(pat[dr][dc])
                    else:
                        m[rr][cc] = 0
                    func[rr][cc] = True

    finder(0, 0)
    finder(0, SIZE - 7)
    finder(SIZE - 7, 0)
    for i in range(8, SIZE - 8):
        m[6][i] = (i + 1) % 2
        func[6][i] = True
        m[i][6] = (i + 1) % 2
        func[i][6] = True
    for dr in range(-2, 3):
        for dc in range(-2, 3):
            m[ALIGN + dr][ALIGN + dc] = 1 if max(abs(dr), abs(dc)) != 1 else 0
            func[ALIGN + dr][ALIGN + dc] = True
    m[4 * 3 + 9][8] = 1
    func[4 * 3 + 9][8] = True
    for i in range(6):
        m[8][i] = 0
        func[8][i] = True
    m[8][7] = 0
    func[8][7] = True
    m[8][8] = 0
    func[8][8] = True
    m[7][8] = 0
    func[7][8] = True
    for i in range(6):
        m[5 - i][8] = 0
        func[5 - i][8] = True
    for i in range(8):
        m[8][SIZE - 1 - i] = 0
        func[8][SIZE - 1 - i] = True
    for i in range(7):
        m[SIZE - 1 - i][8] = 0
        func[SIZE - 1 - i][8] = True
    return m, func


def set_format(m, ec, mask):
    fb = format_bits(ec, mask)
    pos1 = [(8, i) for i in range(6)] + [(8, 7), (8, 8), (7, 8)] + [(5 - i, 8) for i in range(6)]
    pos2 = [(SIZE - 1 - i, 8) for i in range(7)] + [(8, SIZE - 8 + i) for i in range(8)]
    for k in range(15):
        b = (fb >> (14 - k)) & 1
        m[pos1[k][0]][pos1[k][1]] = b
        m[pos2[k][0]][pos2[k][1]] = b


def data_positions(func):
    pos = []
    col = SIZE - 1
    upward = True
    while col > 0:
        if col == 6:
            col -= 1
        for i in range(SIZE):
            r = SIZE - 1 - i if upward else i
            for c in (col, col - 1):
                if not func[r][c]:
                    pos.append((r, c))
        upward = not upward
        col -= 2
    return pos


def encode_qr(data_bytes, ec='M', mask=0):
    assert len(data_bytes) <= 44, len(data_bytes)
    bits = [0, 1, 0, 0]
    bits += [(len(data_bytes) >> i) & 1 for i in range(7, -1, -1)]
    for b in data_bytes:
        bits += [(b >> i) & 1 for i in range(7, -1, -1)]
    cap = 44 * 8
    bits += [0] * min(4, cap - len(bits))
    while len(bits) % 8:
        bits.append(0)
    codewords = [int(''.join(map(str, bits[i:i + 8])), 2) for i in range(0, len(bits), 8)]
    k = 0
    while len(codewords) < 44:
        codewords.append((0xEC, 0x11)[k % 2])
        k += 1
    allbits = []
    for w in codewords + rs_encode(codewords, 26):
        allbits += [(w >> i) & 1 for i in range(7, -1, -1)]
    allbits += [0] * 7
    m, func = build_base()
    set_format(m, ec, mask)
    pos = data_positions(func)
    assert len(pos) == len(allbits), (len(pos), len(allbits))
    for (r, c), b in zip(pos, allbits):
        m[r][c] = b ^ (1 if (r + c) % 2 == 0 else 0)
    return m


# ------------------------------------------------------------------- PRNG
def prng_bits(tag, n):
    """Deterministic bit stream from sha256(tag || counter)."""
    out = []
    ctr = 0
    while len(out) < n:
        h = hashlib.sha256(f"{tag}:{ctr}".encode()).digest()
        for byte in h:
            for i in range(7, -1, -1):
                out.append((byte >> i) & 1)
                if len(out) == n:
                    return out
        ctr += 1
    return out


# ------------------------------------------------------- source footage
# Vendored source: 464x256 h264 (4x4 pixels per ASCII cell), ~30 fps.
# Scene s consumes source frames BASES[s] .. BASES[s]+4 (first one twice).
# Bases are picked by pick_bases(): each starts a calm 5-frame run, spread
# across the clip, with every scene boundary much larger than any
# inside-scene step — so the 29 scenes pop out of a frame-difference plot.
SRC_W, SRC_H = 464, 256
SRC_RUN = 5
INTRA_TH = 7.0
BOUND_TH = 14.0
OUT_INTRA_OK = 11.0  # output-level margins at the solver's 120x114 scale
OUT_BOUND_OK = 15.0
NUDGE_RANGE = 12
assert SRC_W == COLS * 4 and SRC_H == ROWS * 4


def load_source(source_path):
    """Decode the source clip once; per frame return (lum, col) byte strings
    at grid resolution (116x64 box average)."""
    cmd = ["ffmpeg", "-v", "error", "-i", source_path,
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    fs = SRC_W * SRC_H * 3
    frames = []
    while True:
        raw = proc.stdout.read(fs)
        if len(raw) < fs:
            break
        lum = bytearray(COLS * ROWS)
        col = bytearray(COLS * ROWS)
        for y in range(ROWS):
            for x in range(COLS):
                sr = sg = sb = 0
                for dy in range(4):
                    o = ((y * 4 + dy) * SRC_W + x * 4) * 3
                    for dx in range(4):
                        oo = o + dx * 3
                        sr += raw[oo]
                        sg += raw[oo + 1]
                        sb += raw[oo + 2]
                r, g, b = sr >> 4, sg >> 4, sb >> 4
                lum[y * COLS + x] = (77 * r + 150 * g + 29 * b) >> 8
                col[y * COLS + x] = neon_for_rgb(r, g, b)
        frames.append((bytes(lum), bytes(col)))
    proc.stdout.close()
    if proc.wait() != 0:
        raise RuntimeError("source decode failed")
    assert frames, "empty source"
    return frames


def bdiff(a, b):
    return sum(abs(x - y) for x, y in zip(a, b)) / len(a)


def pick_bases(src, scenes):
    n = len(src)
    lum = [f[0] for f in src]
    diffs = [0.0] * n
    for i in range(1, n):
        diffs[i] = bdiff(lum[i - 1], lum[i])

    def lively(b, th):
        ds = diffs[b + 1:b + SRC_RUN]
        return max(ds) < th and sum(ds) / len(ds) > 1.0
    calm = [b for b in range(n - SRC_RUN) if lively(b, INTRA_TH)]
    calm_set = set(calm)
    bases = []
    for s in range(scenes):
        lo = int(s * n / scenes)
        hi = int((s + 1) * n / scenes) - SRC_RUN
        lo = max(lo, (bases[-1] + 9) if bases else 0)
        cands = [b for b in range(lo, max(lo, hi) + 1) if b in calm_set]
        for th in (8.5, 10.0, 1e9):
            if cands:
                break
            cands = [b for b in range(lo, max(lo, hi) + 1) if lively(b, th)]
        assert cands, f"no usable base in slot {s}"
        if not bases:
            bases.append(min(cands))
            continue
        prev = lum[bases[-1] + SRC_RUN - 1]
        best, bestd = cands[0], -1.0
        for b in cands:
            d = bdiff(prev, lum[b])
            if d > bestd:
                best, bestd = b, d
        bases.append(best)
    for s in range(1, scenes):
        d = bdiff(lum[bases[s - 1] + SRC_RUN - 1], lum[bases[s]])
        assert d > BOUND_TH, f"weak source boundary {s}: {d:.2f}"
    return bases


def thumb_pipe(frames):
    """Downscale rendered RGB frames to 120x114 gray exactly like a solver."""
    assert frames and len(frames[0]) == FW * FH * 3
    cmd = ["ffmpeg", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{FW}x{FH}", "-i", "-",
           "-vf", "scale=120:114,format=gray",
           "-f", "rawvideo", "-pix_fmt", "gray", "-"]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    raw, _ = proc.communicate(b"".join(frames))
    assert proc.returncode == 0, "thumb pipe failed"
    fs = 120 * 114
    assert len(raw) % fs == 0
    return [raw[i * fs:(i + 1) * fs] for i in range(len(raw) // fs)]


def scene_starts(thumbs, scenes):
    diffs = [bdiff(thumbs[i - 1], thumbs[i]) for i in range(1, len(thumbs))]
    order = sorted(range(len(diffs)), key=lambda i: -diffs[i])
    cuts = sorted(order[:scenes - 1])
    return [0] + [c + 1 for c in cuts], diffs


def neon_for_rgb(r, g, b):
    """Original hue -> neon text color (low saturation -> white)."""
    h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
    if s < 0.25:
        return 4
    if h < 0.08 or h >= 0.92:
        return 1  # reds -> pink
    if h < 0.20:
        return 2  # oranges/yellows -> yellow
    if h < 0.45:
        return 3  # greens -> green
    if h < 0.72:
        return 0  # cyans/blues -> cyan
    return 1  # purples -> pink


def render_scene(src, s, base, row_bits, seed, anim, start_no):
    """Render one scene (anim+2 frames) from cached source grids."""
    r_bits = prng_bits(f"sb{seed}:R:{s}", COLS * ROWS)
    band_bit = [row_bits[x // BAND_W] for x in range(COLS)]
    b_bits = [r ^ band_bit[i % COLS] for i, r in enumerate(r_bits)]
    out = []
    for f in range(anim + 2):
        if f == 0:
            var = r_bits
        elif f == 1:
            var = b_bits
        else:
            var = prng_bits(f"sb{seed}:N:{s}:{f}", COLS * ROWS)
        lum, col = src[base + (0 if f <= 1 else f - 1)]
        out.append(render_frame(lum, col, var, s, start_no + f))
    return out


MONO = False


def render_frame(lum, col, variants, scene, frame_no):
    """lum/col are flat bytes at grid resolution; variants a bit list."""
    px = bytearray(BG * (FW * FH))
    for y in range(ROWS):
        for x in range(COLS):
            i = y * COLS + x
            adj = (BAYER4[(y & 3) * 4 + (x & 3)] - 7.5) * DITHER_AMP
            v = lum[i] + adj
            if v < 0:
                v = 0.0
            elif v > 255:
                v = 255.0
            cls = int((255 - v) * NCLS // 256)
            ch = PAIRS[cls][variants[i]]
            fg = (235, 235, 240) if MONO else NEON[col[i]]
            rows = FONT[ch]
            base_x = ML + x * CELL_W
            base_y = MT + y * CELL_H
            for r in range(7):
                row = rows[r]
                for c in range(5):
                    if row[c] == '#':
                        o = ((base_y + GLYPH_OY + r) * FW + base_x + GLYPH_OX + c) * 3
                        px[o] = fg[0]
                        px[o + 1] = fg[1]
                        px[o + 2] = fg[2]
    draw_text(px, FW, FH, f"STORYBOARD PLAYER  SHOT {scene + 1:02d}/29", ML, 2, 2, (240, 240, 235))
    draw_text(px, FW, FH,
              f"FRAME {frame_no:06d}  24FPS  116X64  EVERY SHOT GETS TWO TAKES",
              ML, FH - MB + 3, 2, (240, 240, 235))
    return bytes(px)


# ------------------------------------------------------------------ render
def draw_text(px, fw, fh, s, x, y, scale, color):
    for ch in s:
        rows = FONT.get(ch)
        if rows is None:
            x += 6 * scale
            continue
        for r in range(7):
            for c in range(5):
                if rows[r][c] == '#':
                    for dy in range(scale):
                        for dx in range(scale):
                            xx, yy = x + c * scale + dx, y + r * scale + dy
                            if 0 <= xx < fw and 0 <= yy < fh:
                                o = (yy * fw + xx) * 3
                                px[o] = color[0]
                                px[o + 1] = color[1]
                                px[o + 2] = color[2]
        x += 6 * scale


def nudge_bases(src, bases, scenes, anim, seed, qr):
    """Ensure output-level scene margins: render, measure at solver scale,
    nudge bases away from class-boundary flicker until the top-28 frame
    diffs are exactly the 28 true scene cuts."""
    perscene = anim + 2
    expected = [s * perscene for s in range(scenes)]
    rows = [qr[s] for s in range(scenes)]
    rendered = []
    for s in range(scenes):
        rendered.extend(render_scene(src, s, bases[s], rows[s], seed, anim, s * perscene))
    for it in range(40):
        thumbs = thumb_pipe(rendered)
        starts, diffs = scene_starts(thumbs, scenes)
        if starts == expected:
            break
        top = set(sorted(range(len(diffs)), key=lambda i: -diffs[i])[:scenes - 1])
        intra = {}
        for s in range(scenes):
            for t in range(s * perscene + 1, (s + 1) * perscene):
                if t - 1 in top:
                    intra[s] = max(intra.get(s, 0.0), diffs[t - 1])
        # nudge the scene with the worst intra spike (else weakest boundary)
        if intra:
            s = max(intra, key=lambda k: intra[k])
        else:
            weak = [(diffs[m - 1], m // perscene) for m in expected[1:]]
            s = min(weak)[1]
        lo = (bases[s - 1] + SRC_RUN) if s > 0 else 0
        hi = (bases[s + 1] - SRC_RUN) if s < scenes - 1 else len(src) - SRC_RUN
        ds = [d for d in range(-NUDGE_RANGE, NUDGE_RANGE + 1) if lo <= bases[s] + d <= hi]
        # batch all candidates through one thumb pipe
        segs, marks = [], []
        for d in ds:
            cand = render_scene(src, s, bases[s] + d, rows[s], seed, anim, s * perscene)
            seg = []
            if s > 0:
                seg.append(rendered[(s - 1) * perscene + perscene - 1])
            seg.extend(cand)
            if s < scenes - 1:
                seg.append(rendered[(s + 1) * perscene])
            marks.append((d, cand, len(seg)))
            segs.extend(seg)
        th = thumb_pipe(segs)
        best, bestscore, bestcand = bases[s], None, None
        pos = 0
        for d, cand, ln in marks:
            t = th[pos:pos + ln]
            pos += ln
            td = [bdiff(t[i - 1], t[i]) for i in range(1, len(t))]
            off = 1 if s > 0 else 0
            intra_max = max(td[off:off + perscene - 1])
            b1 = td[0] if s > 0 else 99.0
            b2 = td[-1] if s < scenes - 1 else 99.0
            score = (0 if (intra_max < OUT_INTRA_OK and b1 > OUT_BOUND_OK
                           and b2 > OUT_BOUND_OK) else 1000) + intra_max - 0.1 * min(b1, b2)
            if bestscore is None or score < bestscore:
                best, bestscore, bestcand = bases[s] + d, score, cand
        print(f"nudge {it}: scene {s} base {bases[s]} -> {best} (score {bestscore:.1f})",
              file=sys.stderr)
        bases[s] = best
        rendered[s * perscene:(s + 1) * perscene] = bestcand
    thumbs = thumb_pipe(rendered)
    starts, diffs = scene_starts(thumbs, scenes)
    assert starts == expected, f"scene detection not clean: {starts}"
    # fortify: every true cut must clear every non-cut by a wide margin.
    # Scene order need not follow source chronology (players never see the
    # source), so a weak scene may take content from anywhere.
    lum_all = [f[0] for f in src]
    nsrc = len(src)
    sdiff = [0.0] * nsrc
    for i in range(1, nsrc):
        sdiff[i] = bdiff(lum_all[i - 1], lum_all[i])

    def lively_at(b, th):
        ds = sdiff[b + 1:b + SRC_RUN]
        return max(ds) < th and sum(ds) / len(ds) > 1.0
    calm_all = [b for b in range(nsrc - SRC_RUN) if lively_at(b, INTRA_TH)]
    if len(calm_all) < 60:
        calm_all = [b for b in range(nsrc - SRC_RUN) if lively_at(b, 8.5)]
    for _ in range(12):
        thumbs = thumb_pipe(rendered)
        starts, diffs = scene_starts(thumbs, scenes)
        assert starts == expected, f"scene detection not clean: {starts}"
        order = sorted(range(len(diffs)), key=lambda i: -diffs[i])
        cuts = sorted(order[:scenes - 1])
        weakest = min(cuts, key=lambda c: diffs[c])
        noncut_max = max(diffs[i] for i in range(len(diffs)) if i not in set(cuts))
        print(f"fortify check: weakest cut {weakest}={diffs[weakest]:.1f} "
              f"noncut_max={noncut_max:.1f}", file=sys.stderr)
        if diffs[weakest] >= 13.0 and diffs[weakest] - noncut_max >= 4.0:
            break
        s = (weakest + 1) // perscene  # scene starting at this cut
        ds = calm_all
        segs = []
        for b in ds:
            cand = render_scene(src, s, b, rows[s], seed, anim, s * perscene)
            seg = []
            if s > 0:
                seg.append(rendered[(s - 1) * perscene + perscene - 1])
            seg.extend(cand)
            if s < scenes - 1:
                seg.append(rendered[(s + 1) * perscene])
            segs.append((b, cand, seg))
        flat = [f for _, _, seg in segs for f in seg]
        th = thumb_pipe(flat)
        best, bestscore, bestcand = bases[s], None, None
        pos = 0
        for b, cand, seg in segs:
            t = th[pos:pos + len(seg)]
            pos += len(seg)
            td = [bdiff(t[i - 1], t[i]) for i in range(1, len(t))]
            off = 1 if s > 0 else 0
            intra_max = max(td[off:off + perscene - 1])
            b1 = td[0] if s > 0 else 99.0
            b2 = td[-1] if s < scenes - 1 else 99.0
            if intra_max < OUT_INTRA_OK and b1 > OUT_BOUND_OK and b2 > OUT_BOUND_OK:
                score = min(b1, b2) - intra_max
            else:
                score = -1000 + min(b1, b2) - intra_max
            if bestscore is None or score > bestscore:
                best, bestscore, bestcand = b, score, cand
        print(f"fortify: scene {s} base {bases[s]} -> {best} (score {bestscore:.1f})",
              file=sys.stderr)
        if best == bases[s]:
            print("fortify: no improving move, stop", file=sys.stderr)
            break
        bases[s] = best
        rendered[s * perscene:(s + 1) * perscene] = bestcand
    thumbs = thumb_pipe(rendered)
    starts, diffs = scene_starts(thumbs, scenes)
    assert starts == expected, f"scene detection not clean: {starts}"
    order = sorted(range(len(diffs)), key=lambda i: -diffs[i])
    assert diffs[order[scenes - 2]] >= 13.0, "weakest cut too small"
    assert diffs[order[scenes - 2]] - diffs[order[scenes - 1]] >= 4.0, "cut margin too thin"
    return rendered, bases, diffs


def encode_av1(rendered, out, fps, crf, preset=8, svtparams=""):
    cmd = ["ffmpeg", "-y", "-v", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{FW}x{FH}",
           "-framerate", str(fps), "-i", "-",
           "-c:v", "libsvtav1", "-preset", str(preset), "-crf", str(crf),
           "-pix_fmt", "yuv420p", ] + (["-svtav1-params", svtparams] if svtparams else []) + [
           "-metadata", "title=storyboard export",
           "-metadata", "comment=29 shots, 116x64 cells; source: Budots Dance Video by Sherwin Tuna, CC BY 3.0, via Wikimedia Commons",
           out]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    try:
        for fr in rendered:
            proc.stdin.write(fr)
    finally:
        proc.stdin.close()
        rc = proc.wait()
    if rc != 0:
        raise RuntimeError(f"ffmpeg exited {rc}")


def encode_hevc(rendered, out, fps, crf, xparams=""):
    cmd = ["ffmpeg", "-y", "-v", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{FW}x{FH}",
           "-framerate", str(fps), "-i", "-",
           "-c:v", "libx265", "-preset", "slow", "-crf", str(crf),
           "-pix_fmt", "yuv420p", ] + (["-x265-params", xparams] if xparams else []) + [
           "-metadata", "title=storyboard export",
           "-metadata", "comment=29 shots, 116x64 cells; source: Budots Dance Video by Sherwin Tuna, CC BY 3.0, via Wikimedia Commons",
           out]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    try:
        for fr in rendered:
            proc.stdin.write(fr)
    finally:
        proc.stdin.close()
        rc = proc.wait()
    if rc != 0:
        raise RuntimeError(f"ffmpeg exited {rc}")


HAMM_T = 5  # cell "changed" threshold (twin masks differ by >=13 bits)


def cell_hamm(frame, cx, cy, other):
    d = 0
    for r in range(7):
        for c in range(5):
            xx = ML + cx * CELL_W + GLYPH_OX + c
            yy = MT + cy * CELL_H + GLYPH_OY + r
            o = (yy * FW + xx) * 3
            a = 1 if max(frame[o], frame[o + 1], frame[o + 2]) > 40 else 0
            b = 1 if max(other[o], other[o + 1], other[o + 2]) > 40 else 0
            d += (a != b)
    return d


def lossy_check(path, scenes, anim, qr):
    """Decode the ENCODED file and verify extraction margins end to end."""
    perscene = anim + 2
    cmd = ["ffmpeg", "-v", "error", "-i", path, "-vf", "scale=120:114,format=gray",
           "-f", "rawvideo", "-pix_fmt", "gray", "-"]
    raw = subprocess.run(cmd, capture_output=True).stdout
    fs = 120 * 114
    thumbs = [raw[i * fs:(i + 1) * fs] for i in range(len(raw) // fs)]
    starts, diffs = scene_starts(thumbs, scenes)
    assert starts == [s * perscene for s in range(scenes)], f"bad starts: {starts}"
    cmd = ["ffmpeg", "-v", "error", "-i", path, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    raw = subprocess.run(cmd, capture_output=True).stdout
    fs = FW * FH * 3
    full = [raw[i * fs:(i + 1) * fs] for i in range(len(raw) // fs)]
    assert len(full) == len(thumbs)
    worst0, worst1 = 0.0, 1.0
    for s in range(scenes):
        A, B = full[starts[s]], full[starts[s] + 1]
        for band in range(QR_N):
            ch = to = 0
            for cx in range(band * BAND_W, (band + 1) * BAND_W):
                for cy in range(ROWS):
                    to += 1
                    if cell_hamm(A, cx, cy, B) > HAMM_T:
                        ch += 1
            f = ch / to
            if qr[s][band] == 0:
                worst0 = max(worst0, f)
            else:
                worst1 = min(worst1, f)
    return worst0, worst1


def generate(flag, seed, out, source, scenes=SCENES, anim=0, fps=FPS, crf=30,
           xparams="", codec="hevc", av1preset=8, svtparams=""):
    import tempfile
    if isinstance(flag, str):
        flag = flag.encode()
    qr = encode_qr(flag, ec='M', mask=0)
    assert len(qr) == QR_N and len(qr[0]) == QR_N
    src = load_source(source)
    bases = pick_bases(src, scenes)
    rendered, bases, diffs = nudge_bases(src, bases, scenes, anim, seed, qr)
    order = sorted(range(len(diffs)), key=lambda i: -diffs[i])
    print(f"scene cuts: {[round(diffs[i], 1) for i in order[:scenes]]}", file=sys.stderr)
    print(f"next diffs: {[round(diffs[i], 1) for i in order[scenes - 1:scenes + 2]]}", file=sys.stderr)
    tmp = tempfile.mkdtemp(prefix="storyboard")
    try:
        steps = (crf, crf - 2, crf - 4, crf - 6) if codec == "hevc" else (crf, crf - 3, crf - 6, crf - 9)
        for c in steps:
            probe = os.path.join(tmp, f"probe{c}.mkv")
            if codec == "hevc":
                encode_hevc(rendered, probe, fps, c, xparams)
            else:
                encode_av1(rendered, probe, fps, c, av1preset, svtparams)
            worst0, worst1 = lossy_check(probe, scenes, anim, qr)
            size = os.path.getsize(probe)
            print(f"crf {c}: {size} bytes, worst0={worst0:.3f} worst1={worst1:.3f}",
                  file=sys.stderr)
            if worst0 < 0.35 and worst1 > 0.65 and size < 1000000:
                import shutil as _sh
                _sh.move(probe, out)
                return len(rendered)
        raise RuntimeError("no CRF met the size+margin budget")
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--flag", default="cyber_quest{4scii_h4s_tw0_s1d3s_7f3a}")
    ap.add_argument("--seed", default="42")
    ap.add_argument("--out", required=True)
    ap.add_argument("--source", default=None,
                    help="source clip (default: source.mp4 next to this script)")
    ap.add_argument("--scenes", type=int, default=SCENES)
    ap.add_argument("--anim", type=int, default=0)
    ap.add_argument("--crf", type=int, default=60)
    ap.add_argument("--x265-params", default="")
    ap.add_argument("--codec", default="av1", choices=["hevc", "av1"])
    ap.add_argument("--av1-preset", type=int, default=4)
    ap.add_argument("--svt-params", default="")
    ap.add_argument("--mono", action="store_true",
                    help="render grid glyphs white-only (smaller chroma cost)")
    args = ap.parse_args()
    src = args.source or os.path.join(os.path.dirname(os.path.abspath(__file__)), "source.mp4")
    global MONO
    MONO = args.mono
    n = generate(args.flag, args.seed, args.out, src, args.scenes, args.anim,
               crf=args.crf, xparams=args.x265_params, codec=args.codec,
               av1preset=args.av1_preset, svtparams=args.svt_params)
    print(f"wrote {args.out} ({n} frames)")


if __name__ == "__main__":
    main()
