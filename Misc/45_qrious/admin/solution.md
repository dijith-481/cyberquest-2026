# QRious — solution

**Flag:** `cyber_quest{x0r_m3_1f_y0u_c4n_8f3a2c}`

Handout: `handout/IMG_001.png` … `handout/IMG_014.png` (also shipped as
`45_qrious.zip`). No server.

## What the files are

Fourteen same-size (296x296) pure black/white PNGs. Each one looks vaguely
QR-ish — correct finder squares, timing row/column, quiet zone — but every
single one fails to scan. `zbarimg --raw IMG_*.png` reports zero symbols.
That is the tell: the function pattern is real, the data modulate is not.

## The construction

The flag is a real Version-3, EC-M QR matrix T (29x29 modules, mask 0).
Five of the fourteen files are shares of T: four random data masks A, B, C,
D plus E = T XOR A XOR B XOR C XOR D over the data modules, so
A XOR B XOR C XOR D XOR E = T exactly. All function modules are copied
verbatim from T into every share, which is why each file looks almost
scannable. The other nine files are decoys with the same function pattern
and random data.

The five true files are `IMG_002, IMG_003, IMG_005, IMG_009, IMG_014`
(seed 45; per-team re-seeds move them).

## Intended solve path

1. Notice all images share dimensions and only contain pure black/white
   pixels, with repeated finder-like geometry that never quite scans.
2. Suspect XOR secret sharing: XOR is the only operation that turns
   several broken-looking bilevel images into one clean QR.
3. Brute-force every non-empty subset (2^14 - 1 = 16383 — tiny) and try to
   decode each XOR result. With `pyzbar`/`zbarimg`/`opencv`:
   ```python
   from itertools import combinations
   from PIL import Image
   import numpy as np
   from pyzbar.pyzbar import decode
   ```
   XOR the selected images (black = 1), upscale is irrelevant since all
   files share pixel geometry, and feed each result to the decoder.
4. Exactly one subset decodes — the five files above — yielding the flag.
   `admin/solve.py` does the same thing stdlib-only (finder check +
   Reed-Solomon syndromes + header parse) without any scanner library.

## Why uniqueness holds

The generator (`deployment/generate.py`, stdlib only) picks random shares
and then exhaustively tests all 16383 subsets with a real decode attempt
before writing anything. If any subset besides the true five decodes, it
throws the shares away and retries with the next attempt counter. The
shipped handout was accepted only when `number_of_decodable == 1`.
Even-sized subsets cannot decode by construction (identical function
modules XOR to zero, clearing the finders), and odd-sized pretenders carry
random data that fails the 26-byte Reed-Solomon check with probability
1 - 256^-26 each.

## Organizer verification

```bash
sh admin/verify.sh
```

Regenerates the handout from `--seed 45`, `cmp`s all 14 PNGs, checks
dimensions/purity, asserts no plaintext leak, and runs the exhaustive
reference solver.
