# 41_tracking — solution

**Flag:** `cyber_quest{k3rn1ng_0n3_un1t_m4tt3rs_c41f}`
**Difficulty:** easy

## The setup

Design shipped the unreleased Brand Display typeface ahead of schedule:
`brand-display.ttf` plus the `specimen.html` page they used for sign-off.
The specimen's note is the first hint: "Tracking is precise. Even one
unit matters." Tracking = kerning. One unit = one font unit.

## Step 1 — look at the font the way a type person would

```bash
fc-scan --format '%{family} %{style}\n' brand-display.ttf
# Brand Display Regular
ttx -t GPOS brand-display.ttf
```

One `kern` feature, one PairPos lookup, format 1, XAdvance-only values —
but 676 pairs in scrambled file order, values all plausible tightenings.
Reading parity down the file gives garbage (`ba 86 …`, no magic). The
table alone does not define an order, so something else must.

## Step 2 — rule out the decoy channels

Every advance width is identical (600, space 300), every outline is a
plain bar, cmap is a straight mapping. `hmtx`/`cmap`/`glyf` parity carries
nothing — one mechanism, and the specimen sentence says which one.

## Step 3 — the specimen defines the order

The sign-off page carries a tracking proof: 400 cap pairs "set in reading
order", with "proof order is binding". That list IS the bit order — the
font holds every cap pair (message + decoys, same value distribution),
and only the proof sequence selects the message:

```
proof pair  ->  GPOS XAdvance & 1  ->  bits, MSB first
even value -> 0, odd value -> 1
```

```bash
python3 admin/solve.py handout/brand-display.ttf handout/specimen.html
# cyber_quest{k3rn1ng_0n3_un1t_m4tt3rs_c41f}
```

## Step 4 — framed bitstream confirms the decode

```
43 51            magic "CQ"
00 2A            u16-BE payload length (42)
<42 payload>     the full flag, ASCII
<4 crc32>        u32-BE zlib CRC32 of the payload
```

The solver checks the magic, slices exactly `length` bytes, and verifies
the CRC before printing.

## Step 5 — submit

`cyber_quest{k3rn1ng_0n3_un1t_m4tt3rs_c41f}`. Done.
