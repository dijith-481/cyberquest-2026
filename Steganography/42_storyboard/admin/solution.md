# 42_storyboard — solution

**Flag:** `cyber_quest{4scii_h4s_tw0_s1d3s_7f3a}`
**Difficulty:** hard

## The setup

The handout is `storyboard.mkv`: a ~2.4 second ASCII-art dance clip, 58
frames, under 1 MB, with terminal chrome around it. The footage is real:
"Budots Dance Video" by Sherwin Tuna (CC BY 3.0, via Wikimedia Commons),
converted cell by cell into neon ASCII. `ffprobe` says the rest:

```bash
ffprobe storyboard.mkv
# av1, 712x550, 58 frames, 24 fps, one video stream, no audio
```

AV1 at this size is visibly lossy — that is the second trap. The codec
blurs a few pixels per glyph, so exact template matching fails. The
challenge is built to survive it: every decision is backed by hundreds of
votes. `strings` and metadata give nothing (besides the footage credit).
Pixel LSBs give nothing. The chrome (`STORYBOARD PLAYER`, `SHOT xx/29`,
`EVERY SHOT GETS TWO TAKES`) is flavor — and the last two phrases are the
whole brief.

## Step 1 — find the 29 scenes

Decode small thumbnails and diff consecutive frames:

```bash
ffmpeg -i storyboard.mkv -vf scale=120:114,format=gray -f rawvideo -pix_fmt gray thumbs.raw
python3 -c "... mean(abs(f[n]-f[n-1])) ..."
```

28 transitions spike (~13–33); everything else sits at ~8 or below. The
scenes start at frames 0, 2, 4, …, 56: 29 scenes, 2 frames each — every shot
really does get exactly two takes. The chrome's shot counter
(`SHOT 01/29` … `SHOT 29/29`) confirms it.

## Step 2 — the twin takes

The two frames of every scene show the same source moment: same shapes,
slightly different glyphs. Crop the grid (origin (8, 20), cells 6x8 px,
116x64) and binarize each cell (`max(r,g,b) > 40` → ink; background is
`(5,5,8)`, glyphs are neon or white) into a 35-bit mask. A single frame's
masks look random. But compare twins with Hamming distance: most cells
differ by 0–5 bits (codec blur), the rest by 13+ bits — and every large
difference is a swap between two fixed glyph shapes. Five swapping pairs
emerge, e.g. `{@, M}`, `{#, 8}`, `{+, =}`, each rendered at the same
brightness, so the swap is invisible at playback speed: the luminance class
picks the pair, and the *variant within the pair* carries one hidden bit
per cell. (The two lightest candidate pairs were cut from the alphabet for
exactly this reason: their masks differ by 1–3 bits, which the codec
erases.)

## Step 3 — one QR row per scene

116 columns / 29 = 4: each scene's twin comparison is a set of vertical
stripes 4 cells wide. For each of the 29 bands, count cells with Hamming
distance > 5 over all 64 rows (256 votes). Unflipped bands read near 0.00,
flipped bands near 1.00 (worst case 0.06/0.96 across the whole video) —
keep (0) or flip (1). That is one 29-bit row. Do it for all 29 scenes:

```bash
python3 admin/solve.py storyboard.mkv
```

which prints the 29x29 bitmap. It has finder patterns in three corners: it
is a QR code (Version 3, 29x29). Add a 4-module white quiet zone and any
phone scanner reads it; the reference solver instead unmasks (mask 0), checks
the Reed-Solomon parity, and parses byte mode directly.

## Step 4 — submit

`cyber_quest{4scii_h4s_tw0_s1d3s_7f3a}`. Done.

## Credit

Source footage: "Budots Dance Video" by Sherwin Tuna, CC BY 3.0, via
Wikimedia Commons (see `deployment/ATTRIBUTION.txt`). The ASCII rendering,
twin-glyph channel, QR payload, and chrome are original to this challenge.
