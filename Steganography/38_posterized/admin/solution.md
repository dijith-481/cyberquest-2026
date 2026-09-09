# 38_posterized — solution

**Flag:** `cyber_quest{p41r_0rd3r_8f2a}`
**Difficulty:** easy

## The setup

The handout is a single file, `launch-poster.png`: a retro launch poster for
AURORA-9, exported byte-for-byte by the company's `poster-gen` tool. It opens
fine in every viewer. The trick is entirely in how an indexed-color PNG works.

## Step 1 — notice it is an indexed PNG

```bash
file launch-poster.png
# PNG image data, 480 x 600, 8-bit colormap, non-interlaced
pngcheck -v launch-poster.png
# chunks: IHDR, PLTE (256 entries), IDAT, IEND
```

No RGB pixels here: each pixel is one byte — an *index* into a 256-entry
palette (PLTE). The color you see is `PLTE[index]`. The poster text even tells
you where to look: *"Every color has its place"* and the footer annotation
*"Palette order must remain consistent."*

## Step 2 — dump the palette and spot the pairs

```python
import struct
d = open("launch-poster.png", "rb").read()
pos = 8
while pos < len(d):
    ln = struct.unpack(">I", d[pos:pos+4])[0]
    typ, data = d[pos+4:pos+8], d[pos+8:pos+8+ln]
    pos += 12 + ln
    if typ == b"PLTE":
        pal = [tuple(data[i:i+3]) for i in range(0, len(data), 3)]
print(len(pal))  # 256
```

Sort the entries by value (or diff each entry against the rest): every entry
has exactly one partner that differs by **exactly 1 in exactly one channel**,
e.g. `#183A52` vs `#193A52`. 256 entries form 128 such pairs. A 1-LSB
difference is invisible, so each pair is really one displayed color with two
names — and the *order* of the two names in the palette carries one bit:

- smaller `0xRRGGBB` value listed first → **0** (canonical order)
- larger value listed first → **1** (entries swapped)

Swapping palette entries would normally corrupt the image, but the exporter
remapped every pixel index to follow its color, so the decoded picture is
identical either way. Pixel content is a decoy (seeded print grain); the data
is in the palette structure, which is why `zsteg` and LSB tools find nothing.

## Step 3 — read the bits

Sequence the pairs by ascending min(color value) — the only order recoverable
from the palette alone — take one bit per pair, MSB first:

```bash
python3 admin/solve.py launch-poster.png
# body bytes: b'p41r_0rd3r_8f2a}'
# cyber_quest{p41r_0rd3r_8f2a}
```

128 pairs → 128 bits → 16 bytes. That fits the flag *body* (inner text plus
the closing brace); the `cyber_quest{` prefix is boilerplate shared by every
flag and is not stored — a full wrapped flag (28 bytes) cannot fit in 128
bits, which is exactly why the body ends with `}`: it confirms alignment.

## Step 4 — submit

`cyber_quest{p41r_0rd3r_8f2a}`. Done.
