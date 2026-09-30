#!/usr/bin/env bash
# 53_payroll_photo — verify the challenge is solvable end to end.
# Regenerates the handout deterministically, cross-checks the JPEG and its
# EXIF with an INDEPENDENT decoder (ImageMagick), then runs the stdlib
# reference solve on a fresh copy and checks the flag.
set -euo pipefail
cd "$(dirname "$0")/.."

EXPECTED='cyber_quest{th3_m3t4d4t4_1s_n0t_th3_phot0}'
HANDOUT=handout/all_hands.jpg

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# --- 1. deterministic regeneration + no drift from the shipped artifact ---
# This hashes the COMMITTED handout BEFORE regenerating. An earlier version
# regenerated and then checked, which meant it only ever proved the
# generator works: mutating or staling the shipped file was silently
# repaired and the suite still reported success. Hash, regenerate, compare.
SHIPPED="$(sha256sum "$HANDOUT" | cut -d' ' -f1)"
python3 deployment/make_handout.py >/dev/null
REGEN1="$(sha256sum "$HANDOUT" | cut -d' ' -f1)"
python3 deployment/make_handout.py >/dev/null
REGEN2="$(sha256sum "$HANDOUT" | cut -d' ' -f1)"

[ "$REGEN1" = "$REGEN2" ] || { echo "VERIFY FAILED — generator is not deterministic" >&2; exit 1; }
echo "deterministic: $REGEN1"

[ "$SHIPPED" = "$REGEN1" ] || {
  echo "VERIFY FAILED — the shipped handout does not match a fresh regeneration." >&2
  echo "  committed: $SHIPPED" >&2
  echo "  generated: $REGEN1" >&2
  echo "  The generator and the committed file have drifted. Do not hand-edit" >&2
  echo "  handout/ — fix the generator, or re-commit the regenerated file." >&2
  exit 1
}
echo "shipped handout matches the generator (no drift)"

# --- 2. independent decode: the JPEG is real, not just well-formed ------
# Our encoder wrote this file. A second, unrelated implementation has to
# agree that it is a decodable 320x240 baseline JPEG, otherwise the
# challenge ships a broken image.
if command -v identify >/dev/null 2>&1; then
  identify -format '%m %wx%h %[bit-depth]-bit\n' "$HANDOUT" >"$TMP/id.txt" 2>"$TMP/id.err" \
    || { echo "VERIFY FAILED — ImageMagick cannot parse the JPEG:"; cat "$TMP/id.err"; exit 1; }
  cat "$TMP/id.txt"
  grep -q '^JPEG 320x240 8-bit$' "$TMP/id.txt" \
    || { echo "VERIFY FAILED — expected 'JPEG 320x240 8-bit'" >&2; exit 1; }
  # a full decode must succeed and produce a non-blank image
  convert "$HANDOUT" -colorspace Gray -format '%[fx:mean]' info: >"$TMP/mean.txt" 2>/dev/null \
    || { echo "VERIFY FAILED — full pixel decode failed" >&2; exit 1; }
  MEAN="$(cat "$TMP/mean.txt")"
  echo "decoded mean luminance: $MEAN"
  awk -v m="$MEAN" 'BEGIN{exit !(m>0.05 && m<0.95)}' \
    || { echo "VERIFY FAILED — decoded image is blank or saturated (mean=$MEAN)" >&2; exit 1; }
  # the decoy must be visible to a normal viewer, in EXIF
  identify -verbose "$HANDOUT" 2>/dev/null | grep -q 'exif:ImageDescription' \
    || echo "note: ImageMagick did not surface exif:ImageDescription (solver still parses it directly)"
  echo "independent decode: ok"
else
  echo "note: ImageMagick not available, skipping the independent-decode cross-check"
fi

# --- 3. negative control: the flag is NOT in the pixels -----------------
# If the flag were encoded in the image data it would be a stego challenge.
# Strip every APPn metadata segment and confirm the flag is gone.
python3 - "$HANDOUT" <<'EOF'
import struct, sys, re
d = open(sys.argv[1], "rb").read()
out, i = bytearray(d[:2]), 2
while i < len(d) - 1 and d[i] == 0xFF:
    m = d[i + 1]
    if m in (0xD8, 0xD9) or 0xD0 <= m <= 0xD7:
        out += d[i:i + 2]; i += 2; continue
    if m == 0xDA:
        out += d[i:]; break
    ln = struct.unpack(">H", d[i + 2:i + 4])[0]
    if not (0xE0 <= m <= 0xEF):        # keep everything except APPn
        out += d[i:i + 2 + ln]
    i += 2 + ln
stripped = bytes(out)
raw = open(sys.argv[1], "rb").read()
assert b"cyber_quest{th3_m3t4d4t4" not in stripped, "flag survives metadata stripping"
# One flag in the file, and it is metadata: no decoy, nothing in the pixels.
assert raw.count(b"cyber_quest{") == 1, f"expected 1 flag-shaped string, saw {raw.count(b'cyber_quest{')}"
print("flag is metadata-only; it does not survive stripping the APPn segments: ok")
EOF

# --- 4. exactly ONE flag-shaped string in the whole file -----------------
# There is no decoy. That is deliberate and worth asserting, because a decoy
# used to live in EXIF's ImageDescription — the field viewers render — and it
# was a shortcut: every real flag in this event ends in a random hex suffix
# and the decoy did not, so "ends in hex" picked the answer out of the file
# without reading any metadata at all. One string means no such shortcut.
python3 - "$HANDOUT" <<'EOF'
import re, sys
raw = open(sys.argv[1], "rb").read().decode("latin-1")
hits = re.findall(r"cyber_quest\{[A-z0-9_!@#$%^&*+.-]+\}", raw)
assert len(hits) == 1, f"expected exactly 1 flag-shaped string, saw {len(hits)}: {hits}"
print(f"exactly 1 flag-shaped string in the file: {hits[0]}")
EOF

# --- 5. reference solve on a fresh copy ---------------------------------
cp "$HANDOUT" "$TMP/all_hands.jpg"
OUT="$(python3 admin/solve.py "$TMP/all_hands.jpg")"
echo "$OUT"

# The solve walks the EXIF IFD before reading XMP, so its output includes the
# EXIF fields. The assertion is on the final answer line only.
ANSWER="$(echo "$OUT" | tail -1)"
echo "solver answer: $ANSWER"

[ "$ANSWER" = "$EXPECTED" ] || { echo "VERIFY FAILED — expected $EXPECTED, got $ANSWER" >&2; exit 1; }
echo "VERIFY OK — flag recovered from a fresh handout"
