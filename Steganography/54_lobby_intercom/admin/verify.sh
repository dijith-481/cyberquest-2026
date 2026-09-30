#!/usr/bin/env bash
# 54_lobby_intercom — verify the challenge is solvable end to end.
# Regenerates the handout, checks the RIFF/PCM shape, proves the message is
# NOT in the bit domain, cross-checks with ffmpeg that the file is valid
# audio, then runs the stdlib reference solve on a fresh copy.
set -euo pipefail
cd "$(dirname "$0")/.."

EXPECTED='cyber_quest{th3_sp3ctr0gr4m_1s_l0ud}'
HANDOUT=handout/lobby_intercom.wav

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# --- 1. deterministic regeneration + no drift from the shipped artifact ---
SHIPPED="$(sha256sum "$HANDOUT" | cut -d' ' -f1)"
python3 deployment/generate.py >/dev/null
REGEN1="$(sha256sum "$HANDOUT" | cut -d' ' -f1)"
python3 deployment/generate.py >/dev/null
REGEN2="$(sha256sum "$HANDOUT" | cut -d' ' -f1)"

[ "$REGEN1" = "$REGEN2" ] || { echo "VERIFY FAILED — generator is not deterministic" >&2; exit 1; }
echo "deterministic: $REGEN1"
[ "$SHIPPED" = "$REGEN1" ] || {
  echo "VERIFY FAILED — the shipped handout does not match a fresh regeneration." >&2
  echo "  committed: $SHIPPED" >&2
  echo "  generated: $REGEN1" >&2
  echo "  Do not hand-edit handout/ — fix the generator, or re-commit the file." >&2
  exit 1
}
echo "shipped handout matches the generator (no drift)"

# --- 2. shape: real RIFF/WAVE, mono 16-bit PCM ----------------------------
python3 - "$HANDOUT" <<'EOF'
import struct, sys, wave
p = sys.argv[1]
d = open(p, "rb").read()
assert d[:4] == b"RIFF" and d[8:12] == b"WAVE", "not a RIFF/WAVE file"
# no metadata chunks: a LIST/INFO chunk would give the game away
for cid in (b"LIST", b"id3 ", b"ID3 ", b"bext", b"cue ", b"cart"):
    assert d.find(cid) < 0, f"metadata chunk {cid!r} present in the audio"
with wave.open(p, "rb") as w:
    assert w.getnchannels() == 1, f"not mono: {w.getnchannels()}"
    assert w.getsampwidth() == 2, f"not 16-bit: {w.getsampwidth()}"
    assert w.getframerate() == 44100, f"wrong rate: {w.getframerate()}"
    print(f"RIFF ok: PCM mono 16-bit @ 44100 Hz, {w.getnframes()/44100:.2f}s")
EOF

# --- 3. negative control: the message is NOT in the bit domain ------------
# If this challenge were LSB stego the first three steps of a solve would
# be `steghide`/`binwalk`/a naive LSB dump. Prove none of those work.
python3 - "$HANDOUT" <<'EOF'
import sys, wave
with wave.open(sys.argv[1], "rb") as w:
    raw = w.readframes(w.getnframes())
for b in (1, 2, 4, 8):
    bits = "".join(str((x >> (b - 1)) & 1) for x in raw[:40000])
    data = bytes(int(bits[i:i+8], 2) for i in range(0, len(bits) - 7, 8))
    assert b"cyber_quest" not in data, f"flag leaks in bit plane {b}"
assert b"cyber_quest" not in raw, "flag is in the sample bytes"
print("no LSB/bit-plane/byte-domain leak in the first 40000 samples: ok")
EOF

# --- 4. independent decode: ffmpeg must read it as valid audio -----------
if command -v ffprobe >/dev/null 2>&1; then
  ffprobe -v error -show_entries stream=codec_name,sample_rate,channels,duration \
          -of default=noprint_wrappers=1 "$HANDOUT" >"$TMP/ff.txt" 2>&1 \
    || { echo "VERIFY FAILED — ffprobe cannot read the file:"; cat "$TMP/ff.txt"; exit 1; }
  cat "$TMP/ff.txt"
  grep -q 'sample_rate=44100' "$TMP/ff.txt" || { echo "VERIFY FAILED — wrong rate" >&2; exit 1; }
  grep -q 'channels=1'        "$TMP/ff.txt" || { echo "VERIFY FAILED — not mono"   >&2; exit 1; }
  ffmpeg -v error -i "$HANDOUT" -f null - 2>"$TMP/ffdec.txt" \
    || { echo "VERIFY FAILED — ffmpeg full decode failed:"; cat "$TMP/ffdec.txt"; exit 1; }
  [ -s "$TMP/ffdec.txt" ] && { echo "VERIFY FAILED — ffmpeg reported errors:"; cat "$TMP/ffdec.txt"; exit 1; }
  echo "ffmpeg decodes the file cleanly: ok"
else
  echo "note: ffmpeg not available, skipping the independent-decode cross-check"
fi

# --- 5. reference solve on a fresh copy ----------------------------------
cp "$HANDOUT" "$TMP/lobby_intercom.wav"
OUT="$(python3 admin/solve.py "$TMP/lobby_intercom.wav")"
echo "$OUT"

ANSWER="$(echo "$OUT" | tail -1 | sed 's/^decoded: //')"
echo "solver answer: $ANSWER"

[ "$ANSWER" = "$EXPECTED" ] || { echo "VERIFY FAILED — expected $EXPECTED, got $ANSWER" >&2; exit 1; }
case "$ANSWER" in *"?"*) echo "VERIFY FAILED — decoder produced unmatched glyphs" >&2; exit 1;; esac
echo "VERIFY OK — flag decoded from a fresh handout"
