# Ghost Glyphs — solution

**Flag:** `cyber_quest{0nly_th3_r1ght_0bserver_s33s_th3_s1gn4l_9d4e2f}`

Handout: `handout/archive_07.svg` (one file, no server).

## What the file is

A polished "Spectral Observatory" poster. Everything flag-related lives in
anonymous vector geometry — `strings`, `grep CQ{`/`grep cyber_quest{`, XML
comments and metadata reveal nothing (there is one deliberately fake
`cyber_quest{n0_s1gn4l_d3t3ct3d}` text to reward grepping).

## The layers

1. **Legitimate artwork** — observatory, telescope, moon, aurora, star map.
   Most of the file is real poster, so the secret structure blends in.
2. **Anonymous glyph alphabet** — `<defs>` holds a shuffled set of `<symbol>`
   elements with random 4-char ids (`viewBox="0 0 8 13"`, monoline paths).
   Each symbol is one character of a custom stroke font.
3. **Flag only as references** — the flag exists solely as
   `<use href="#id" transform="translate(x 0)" width="8" height="13"/>`
   (SVG2 `href`, no `xlink:href`). No `<text>`, no plaintext.
4. **Shuffled rows** — the `<use>` lines are in random XML order; the reading
   order is carried by the `translate(x 0)` offsets.
5. **Nested transforms** — each row sits inside
   `translate → matrix(inverse) → rotate → translate → scale(-1.5 1.5) → rotate`.
   The leading `matrix(...)` is the exact inverse of the chain, so browsers
   render the row upright — but raw coordinates are useless to casual reading.
6. **Two fragments + masks** — the flag is split into two glyph rows at a
   seeded cut. Each row is luminance-masked (`<mask>`) with dark blobs, so a
   browser only shows ghostly fragments: some letters visible, most eaten.
   The full flag is never fully visible in any renderer.
7. **CSS indirection** — `.sigXXXX { opacity: var(--gainXXXX); color: var(--toneXXXX); }`
   with the custom properties defined on the root `<svg>`; renderers without
   custom-property support fall back to the presentation attributes.
8. **Calibration plate** — a `data:image/svg+xml;base64,...` inner SVG on the
   observatory base lists the glyph ids in reading order (`PLATE 07 // SIGNAL
   ORDER`). It is an ordering clue, never the characters.
9. **Decoy row** — a second glyph row spelling `nothing was here` sits under
   an all-black mask: statically present, renders as nothing.

## Intended solve path

1. View the poster; the tagline ("Some signals are visible only to the right
   observer") and faint fragments around the aurora hint something is there.
2. Open the XML; find a large `<defs>` full of anonymous `<symbol>` glyphs and
   `<use href="#...">` rows.
3. Extract/render the symbols (browser DevTools, a scratch SVG, Inkscape, or
   just reading the monoline paths) → build the id → character map.
4. Order each `<use>` row by its `translate(x 0)` offset (undo the transform
   chain conceptually — the wrapper matrix guarantees left-to-right = x order).
5. Concatenate the two fragments → flag.

The calibration plate shortcut: base64-decode the `data:` URI to get the
glyph-id reading order directly, then only identify the glyph shapes.

## Organizer verification

```bash
sh admin/verify.sh
```

re-generates the handout from `--seed 43 --flag <flag>` and `cmp`s it against
the shipped file, checks well-formedness / no plaintext leak / decoy presence,
and runs `admin/solve.py` (pure static reconstruction: geometry fingerprints
from `deployment/glyphs.py` + `translate(x)` ordering + fragment join).

## Per-team randomization

```bash
python3 deployment/generate.py --seed <team-seed> --flag <flag> --out archive_07.svg
```

Randomizes glyph ids, symbol order, use order, fragment cut point, transform
constants, mask/clip/css names, blob positions, decoy placement, plate dots.
The solve concept is identical; hard-coded answers do not transfer.
