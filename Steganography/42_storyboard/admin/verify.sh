#!/usr/bin/env bash
# 42_storyboard — verify the challenge end to end.
# Regenerates the handout (same seed/flag/source -> same variant planes and
# scene layout; lossy bytes may differ by encoder build), checks the size
# budget, container/codec/geometry, runs the reference solver against the
# shipped file, checks the flag leaks nowhere.
set -euo pipefail
cd "$(dirname "$0")/.."

EXPECTED='cyber_quest{4scii_h4s_tw0_s1d3s_7f3a}'

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# 1. the generator must reproduce a handout the solver accepts
python3 deployment/generate.py --out "$TMP/regen.mkv" >/dev/null 2>"$TMP/regen.log" || {
  echo "VERIFY FAILED — regenerate crashed:" >&2
  tail -5 "$TMP/regen.log" >&2
  exit 1
}
OUT="$(python3 admin/solve.py "$TMP/regen.mkv" 2>/dev/null | tail -1)"
test "$OUT" = "$EXPECTED"
echo "regenerated handout solves to the flag"

# 2. size budget: the whole point — must stay under 1 MB
SIZE="$(stat -c%s handout/storyboard.mkv)"
test "$SIZE" -lt 1000000
echo "size OK (${SIZE} bytes < 1000000)"

# 3. container / codec / geometry contract
ffprobe -v error -show_entries stream=codec_name,width,height,pix_fmt \
  -show_entries format=nb_streams -of default=noprint_wrappers=1 handout/storyboard.mkv > "$TMP/probe.txt"
grep -q 'codec_name=av1' "$TMP/probe.txt"
grep -q 'width=712' "$TMP/probe.txt"
grep -q 'height=550' "$TMP/probe.txt"
grep -q 'nb_streams=1' "$TMP/probe.txt"
NFRAMES="$(ffprobe -v error -count_frames -select_streams v:0 \
  -show_entries stream=nb_read_frames -of default=noprint_wrappers=1 handout/storyboard.mkv | cut -d= -f2)"
test "$NFRAMES" -eq 58
echo "container OK (AV1 MKV, 712x550, 58 frames, video-only)"

# 4. the flag is nowhere in plaintext
if strings handout/storyboard.mkv | grep -qF "$EXPECTED"; then
  echo "VERIFY FAILED — flag leaks in plaintext" >&2
  exit 1
fi
if strings handout/storyboard.mkv | grep -q 'cyber_quest'; then
  echo "VERIFY FAILED — flag prefix leaks" >&2
  exit 1
fi
echo "no plaintext leaks"

# 5. reference solve recovers the flag from the shipped file
OUT="$(python3 admin/solve.py handout/storyboard.mkv 2>/dev/null | tail -1)"
echo "$OUT"
if [ "$OUT" = "$EXPECTED" ]; then
  echo "VERIFY OK — flag recovered from a fresh handout"
else
  echo "VERIFY FAILED — expected $EXPECTED" >&2
  exit 1
fi
