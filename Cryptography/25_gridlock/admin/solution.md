# gridlock — solution

**Flag:** `cyber_quest{3cb_k33ps_3v3ry_sh4p3_7e4a19}`
**Difficulty:** easy

## The setup

Brand encrypts the company logo at rest. The pipeline (`pipeline.py`)
keeps the 54-byte BMP header intact so thumbnailers keep working and
encrypts the pixel bytes with AES-128 in **ECB mode** under a brand key
that lives in the vault:

- `brand_memo.txt` — the memo describing the pipeline, deadpan.
- `pipeline.py` — the sealing script, key redacted.
- `logo.enc.bmp` — the sealed logo. Opens in any image viewer.

## The bug

ECB encrypts every 16-byte block independently with no chaining, so
identical plaintext blocks produce identical ciphertext blocks. The
logo is mostly long runs of identical bytes (white background, the
grid fills, the letter interiors), so the shapes survive encryption as
a blocky ghost in false colors — the classic ECB penguin effect. Only
7 distinct 16-byte blocks appear in the entire 86400-block file.

## The solve (two paths)

**Path 1 — just open it.** `logo.enc.bmp` is a valid BMP. Open it in
any viewer: the header bar, the checkerboard grid, and seven rows of
giant block letters spell the flag directly:

```
cyber_
quest{
3cb_k3
3ps_3v
3ry_sh
4p3_7e
4a19}
```

i.e. `cyber_quest{3cb_k33ps_3v3ry_sh4p3_7e4a19}`.

**Path 2 — scripted.** Count distinct blocks to confirm the ECB tell,
re-render the layout, and build a ciphertext→plaintext codebook from
the 7 repeated values — no key needed. Every block in the file is then
decodable, and the glyphs template-match exactly against the 5x7 font.

## Reference solve

`admin/solve.py` runs path 2 (re-render + codebook + glyph match).
`admin/verify.sh` regenerates the handout (`deployment/make_handout.py`),
solves a fresh copy, and asserts the flag.
