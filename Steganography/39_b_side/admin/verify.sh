#!/usr/bin/env bash
# 39_b_side — verify the challenge is solvable end to end.
# Regenerates the handout deterministically, checks RIFF/PCM properties,
# confirms a naive LSB dump is garbage, runs the reference solve, checks flag+CRC.
set -euo pipefail
cd "$(dirname "$0")/.."

EXPECTED='cyber_quest{cr0ss_0v3r_t0_th3_b_s1d3_7f3a}'

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

python3 deployment/generate.py >/dev/null
cp handout/support_hold.wav "$TMP/support_hold.wav"

python3 - <<'EOF' "$TMP/support_hold.wav"
import struct, sys
d = open(sys.argv[1], "rb").read()
assert d[:4] == b"RIFF" and d[8:12] == b"WAVE", "not a RIFF/WAVE file"
# walk chunks to fmt + data
pos, fmt = 12, None
while pos + 8 <= len(d):
    cid, ln = d[pos:pos+4], struct.unpack("<I", d[pos+4:pos+8])[0]
    body = d[pos+8:pos+8+ln]
    if cid == b"fmt ":
        fmt = struct.unpack("<HHIIHH", body[:16])
    pos += 8 + ln + (ln & 1)
audio, ch, sr, _, _, bits = fmt
assert audio == 1, f"not PCM: {audio}"
assert ch == 2, f"not stereo: {ch}"
assert bits == 16, f"not 16-bit: {bits}"
print(f"RIFF ok: PCM stereo 16-bit @ {sr} Hz")
EOF

# naive LSB-of-every-left-sample dump must NOT reveal the flag
python3 - "$TMP/support_hold.wav" <<'EOF'
import struct, sys, wave
w = wave.open(sys.argv[1], "rb")
raw = w.readframes(w.getnframes())
s = struct.unpack("<%dh" % (w.getnframes() * 2), raw)
left = s[0::2]
bits = "".join(str(x & 1) for x in left)
data = bytes(int(bits[i:i+8], 2) for i in range(0, len(bits) - len(bits) % 8, 8))
assert b"cyber_quest" not in data, "naive LSB dump leaks the flag"
assert b"CQ" not in data[:200], "framing magic visible without the selector"
print("naive LSB dump is garbage: ok")
EOF

OUT="$(python3 admin/solve.py "$TMP/support_hold.wav")"
echo "$OUT"
if echo "$OUT" | grep -q "$EXPECTED"; then
  echo "VERIFY OK — flag recovered from a fresh handout"
else
  echo "VERIFY FAILED — expected $EXPECTED" >&2
  exit 1
fi
