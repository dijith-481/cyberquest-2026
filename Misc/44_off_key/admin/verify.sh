#!/usr/bin/env bash
# Off Key -- verify the challenge is solvable end to end (stdlib only).
set -euo pipefail
cd "$(dirname "$0")/.."

EXPECTED='cyber_quest{0ff_k3y_7r4ck_736sc3}'
SEED=44

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# 1. generator must reproduce both the handout and the zip byte-for-byte
python3 deployment/generate.py --seed "$SEED" --flag "$EXPECTED" \
  --out "$TMP/transcripts.txt" --zip "$TMP/44_off_key.zip" >/dev/null
cmp handout/transcripts.txt "$TMP/transcripts.txt"
cmp 44_off_key.zip "$TMP/44_off_key.zip"
echo "handout reproducible from seed $SEED"

# 2. shape: exactly three paragraphs, line-broken, no plaintext leak
python3 - <<'EOF'
from pathlib import Path
raw = Path("handout/transcripts.txt").read_text()
paras = [p for p in raw.rstrip("\n").split("\n\n") if p.strip()]
assert len(paras) == 3, len(paras)
assert all(p.count("\n") >= 6 for p in paras), "paragraphs lost their line breaks"
assert "cyber_quest" not in raw, "flag prefix leaked"
assert "off key track" not in raw.lower(), "payload phrase leaked"
assert "736sc3" not in raw, "salt leaked in plaintext"
print(f"shape ok: {len(paras)} paragraphs, {len(raw)} bytes, no plaintext leak")
EOF

# 3. the zip carries exactly one file
python3 - <<'EOF'
import zipfile
with zipfile.ZipFile("44_off_key.zip") as z:
    assert z.namelist() == ["transcripts.txt"], z.namelist()
    assert z.testzip() is None
print("zip ok: transcripts.txt only")
EOF

# 4. reference solve recovers the flag
OUT="$(python3 admin/solve.py handout/transcripts.txt | tail -n 1)"
echo "recovered: $OUT"
if [ "$OUT" != "$EXPECTED" ]; then
  echo "VERIFY FAILED — solver recovered $OUT" >&2
  exit 1
fi

echo "VERIFY OK — 3 layout hops decoded, 3 words + 1 salt diffed, flag leetified"
