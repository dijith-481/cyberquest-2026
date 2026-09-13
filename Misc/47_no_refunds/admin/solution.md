# No Refunds — solution

**Flag:** `cyber_quest{sc4n_th3_r3ce1pt_47c1d4}`

Handout: `handout/receipt.png` (one file, no server).

## What the file is

A Byte Mart Express shop receipt with a real Code 128-B barcode at
the bottom encoding the flag. The entire receipt image ships rotated
180 degrees, so both the text and the barcode arrive upside down.

## Intended solve path

1. Open `receipt.png`. Everything is upside down — that is the whole
   puzzle.
2. Rotate the image 180 degrees (any viewer, `convert -rotate 180`,
   a phone's photo editor). The receipt becomes readable and the
   barcode becomes upright.
3. Scan the barcode with any Code 128 reader (phone app works) — or
   run the reference decoder:
   `python3 admin/solve.py handout/receipt.png`.

The receipt hints at this itself: `IF THIS DOES NOT SCAN / TRY
ANOTHER ANGLE` and `ORIENTATION : ???`.

## Why it is built this way

- The barcode is generated undistorted (exact 2px modules, proper
  quiet zones, valid Start B / mod-103 checksum / 13-module stop),
  so once upright it scans immediately. Orientation is the only
  obstacle.
- Rotating the whole receipt (rather than just the barcode) keeps the
  puzzle real even for scanners with auto-rotate: the player still has
  to turn the image to read it.
- The flag lives only in the bars: no PNG text chunks, no EXIF, no
  readable copy under the barcode (`strings | grep cyber_quest`
  finds nothing).

## Organizer verification

```bash
sh admin/verify.sh
```

Regenerates the handout from `--seed 47`, `cmp`s it, checks PNG
sanity and no plaintext leak, and runs the reference solver.
