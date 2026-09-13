# Print Gallery — organizer build

This release uses the user-approved CindyJS artwork and the demo's actual
geometry settings: straight `(1,0)` and curled `(1,-1)`. The flag is ordinary
readable text hidden in the blue least significant bit of the straight
view. The same public coordinate transform curls the artwork and its text.

Upload **only `28_print_gallery.zip`**. It contains exactly:

```text
print-gallery.png
```

The handout has no notes, hints, URLs, parameters, source, metadata, or
trailing payload. The scoreboard README follows the repository template;
its Flag field is organizer configuration, not a player attachment.
The original `print-gallery.jpg` is preserved but is no longer a build input.

## Build

From the challenge directory, using Python 3.11 or newer:

```sh
python3 -m venv /tmp/print-gallery-venv
/tmp/print-gallery-venv/bin/pip install -r deployment/requirements.txt
/tmp/print-gallery-venv/bin/python deployment/generate.py --proofs
/tmp/print-gallery-venv/bin/python admin/solve.py handout/print-gallery.png --output admin/images
/tmp/print-gallery-venv/bin/python admin/preview.py
PYTHON=/tmp/print-gallery-venv/bin/python bash admin/verify.sh
```

Builds are offline once the pinned dependencies are installed. The source
texture is vendored in `deployment/assets/Own2.png`, unchanged at 1196×1360.
Its SHA-256 and provenance are recorded in `deployment/assets/README.md`.
The generator creates a 4096×4096 RGB PNG and a ZIP with fixed timestamps.
`admin/manifest.json` records the exact release hashes. Verification rebuilds
in temporary directories and checks byte-identical output on the pinned
runtime; cross-platform floating-point/zlib changes can affect file hashes.

`admin/solve.py` reads only the released PNG and writes:

- `straightened.png`: the recovered gallery view.
- `flag.png`: its blue LSB, displaying ordinary flag text.
- `flag-crop.png`: an automatically bounded close-up of that text.
- `curled-blue-lsb.png`: the uncorrected bit plane for comparison.

The solver does not print a hardcoded flag or perform OCR. Players read
`flag.png` and join its two lines. A full manual walkthrough that does not
import the solver is in `admin/manual-solve.md`.

## Change the flag

```sh
python3 deployment/generate.py --output /tmp/gallery-variant \
  --flag 'cyber_quest{str41ght_v13w_92ab}' --proofs
python3 admin/solve.py /tmp/gallery-variant/handout/print-gallery.png \
  --output /tmp/gallery-variant/recovered
```

Flags must fit in 44 printable, non-space ASCII characters, using the
`cyber_quest{...}` format. Text wraps at 22 characters with no extra encoding.
Update the scoreboard Flag field and the verification expectation when
adopting a variant as the release.

## What verification establishes

Checks cover the unchanged source asset, pixel equality with the approved
straight-view preview, PNG-only handout and ZIP membership, PNG structure
and CRCs, absence of metadata/trailers/plaintext bytes, independent recovery
from the extracted release, text-mask overlap overall and for every glyph,
negative controls, deterministic rebuilding, and a different flag variant.
The overlap test measures raster recovery against the organizer's text
stencil; it is not OCR. The generated glyphs are also visually inspected.

The transform is analytically reversible up to the public texture periods.
Finite raster sampling is not byte-for-byte reversible: artwork and glyph
edges may lose detail. The flag uses large enough strokes to remain readable.
Nearest-neighbour sampling is required for the hidden bit plane; bilinear
interpolation is used only when rendering the underlying artwork.

Artwork provenance and source links are organizer-only in
`deployment/assets/README.md`. The player attachment remains PNG-only.
