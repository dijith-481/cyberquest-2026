#!/usr/bin/env bash
# Nothing to Declare — verify the challenge end to end (stdlib only).
set -euo pipefail
cd "$(dirname "$0")/.."

EXPECTED='cyber_quest{th1s_p4ssp0rt_h4s_tw0_f4ces_46de17}'
SEED=46
FILE='handout/passport.png'

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# 1. generator must reproduce the handout byte-for-byte
python3 deployment/generate.py --seed "$SEED" --flag "$EXPECTED" --out "$TMP/regen.png" >/dev/null
cmp "$FILE" "$TMP/regen.png"
echo "handout reproducible from seed $SEED"

# 2. PNG side: signature + IEND present, dimensions sane
python3 - <<'EOF'
import struct, zlib
from pathlib import Path
d = Path("handout/passport.png").read_bytes()
assert d[:8] == b"\x89PNG\r\n\x1a\n", "bad PNG signature"
assert b"IEND" in d, "missing IEND"
off = 8
while off < len(d):
    (ln,) = struct.unpack(">I", d[off:off+4])
    typ = d[off+4:off+8]
    if typ == b"IHDR":
        w, h, bitd, ctyp, _, _, _ = struct.unpack(">IIBBBBB", d[off+8:off+8+ln])
        assert (w, h) == (960, 600), (w, h)
        assert bitd == 8 and ctyp == 2
        print(f"PNG {w}x{h} truecolor, IEND ok")
        break
    off += 12 + ln
EOF

# 3. ZIP side: both parsers accept the same file
python3 - <<'EOF'
import zipfile
with zipfile.ZipFile("handout/passport.png") as z:
    names = set(z.namelist())
    assert names == {"INSPECTION_FORMAT.txt", "border_control.db"}, names
    assert z.testzip() is None
    print("ZIP central directory ok:", sorted(names))
EOF

# 4. no plaintext flag anywhere in the polyglot
if grep -qF "$EXPECTED" "$FILE"; then
  echo "VERIFY FAILED — flag leaks in polyglot bytes" >&2
  exit 1
fi
echo "no plaintext flag leak"

# 5. raw document number absent from the archive side
rm -rf "$TMP/zipx" && mkdir -p "$TMP/zipx"
python3 -c "import zipfile; zipfile.ZipFile('$FILE').extractall('$TMP/zipx')"
if grep -rq "CQP0427" "$TMP/zipx"; then
  echo "VERIFY FAILED — document number leaks in archive" >&2
  exit 1
fi
echo "no document-number leak in archive"

# 6. DB shape: 64 rows, target hash present
python3 - <<'EOF'
import sqlite3
import zipfile, tempfile
db = zipfile.ZipFile("handout/passport.png").read("border_control.db")
with tempfile.NamedTemporaryFile() as t:
    t.write(db); t.flush()
    c2 = sqlite3.connect(t.name)
    n = c2.execute("SELECT COUNT(*) FROM inspection_records").fetchone()[0]
    assert n == 64, n
    r = c2.execute("SELECT sealed_note FROM inspection_records WHERE passport_hash='b3a527710297b0b3aad4c1b89b7b9251e92965e94c311e1ac6ae7744fd6d0c9c'").fetchone()
    assert r is not None
    print("DB ok: 64 rows, target hash present")
EOF

# 7. reference solve recovers the flag
OUT="$(python3 admin/solve.py "$FILE" | tail -n 1)"
echo "recovered: $OUT"
if [ "$OUT" != "$EXPECTED" ]; then
  echo "VERIFY FAILED — solver recovered $OUT" >&2
  exit 1
fi

echo "VERIFY OK — polyglot opens both ways and solves end to end"
