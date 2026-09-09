#!/usr/bin/env bash
# Style Guide — verify the challenge end to end (stdlib only).
# Regenerates the handout deterministically, checks the PDF leaks nothing
# in plaintext, and runs the reference solver against the shipped file.
set -euo pipefail
cd "$(dirname "$0")/.."

EXPECTED='cyber_quest{h4lf_p01nt_h1d3s_th3_gu1d3_9d4e2f}'
SEED=40

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# 1. the generator must reproduce the handout byte-for-byte
python3 deployment/generate.py --seed "$SEED" --flag "$EXPECTED" --out "$TMP/regen.pdf" >/dev/null
cmp handout/style_guide.pdf "$TMP/regen.pdf"
echo "handout reproducible"

# 2. encryption markers are visible, the flag is not
grep -a -q '/Encrypt' handout/style_guide.pdf
grep -a -q '/EmbeddedFile' handout/style_guide.pdf
grep -a -q '/P -64' handout/style_guide.pdf
echo "owner restrictions + embedded file markers present"
if grep -a -qF "$EXPECTED" handout/style_guide.pdf; then
  echo "VERIFY FAILED — real flag leaks in plaintext" >&2
  exit 1
fi
if grep -a -q 'wrong_direction' handout/style_guide.pdf; then
  echo "VERIFY FAILED — decoy text leaks in plaintext" >&2
  exit 1
fi
echo "no plaintext leaks"

# 3. embedded ZIP exists, lists the decoy files, and is encrypted
python3 - "$TMP" <<'EOF'
import re, sys
sys.path.insert(0, "admin")
from solve import read_xref, get_obj, obj_stream, rc4, PADDING, parse_encrypt
import hashlib, struct, zipfile, io

data = open("handout/style_guide.pdf", "rb").read()
table = read_xref(data)
trailer = re.search(rb"trailer\s*<<(.*?)>>\s*startxref", data, re.S).group(1)
enc_num = int(re.search(rb"/Encrypt\s*(\d+)\s+0\s+R", trailer).group(1))
O, U, P = parse_encrypt(get_obj(data, table, enc_num))
assert P == -64, P
id0 = bytes.fromhex(re.search(rb"/ID\s*\[<([0-9a-fA-F]+)>", trailer).group(1).decode())
user_pad = (b"" + PADDING)[:32]
perms_u = struct.unpack("<I", struct.pack("<i", P))[0]
key = hashlib.md5(user_pad + O + struct.pack("<I", perms_u) + id0).digest()[:5]
assert rc4(key, PADDING) == U, "empty-password key mismatch"

root = int(re.search(rb"/Root\s*(\d+)\s+0\s+R", trailer).group(1))
catalog = get_obj(data, table, root)
assert b"/EmbeddedFiles" in catalog, "no embedded-files name tree"
fs_num = None
for num in table:
    try:
        body = get_obj(data, table, num)
    except Exception:
        continue
    if b"/Type /Filespec" in body:
        fs_num = num
        break
assert fs_num is not None, "no Filespec object"
fs = get_obj(data, table, fs_num)
zip_num = int(re.search(rb"/EF\s*<<\s*/F\s*(\d+)\s+0\s+R", fs).group(1))
zbody = get_obj(data, table, zip_num)
okey = hashlib.md5(key + struct.pack("<I", zip_num)[:3] + b"\x00\x00").digest()[:10]
zdata = rc4(okey, obj_stream(zbody))
assert zdata.startswith(b"PK\x03\x04"), "embedded file is not a zip"
z = zipfile.ZipFile(io.BytesIO(zdata))
names = sorted(z.namelist())
assert names == ["README.txt", "wrong_direction.txt"], names
for info in z.infolist():
    assert info.flag_bits & 0x1, "zip entry %s is not password-protected" % info.filename
print("embedded decoy zip present, encrypted:", names)
EOF

# 4. reference solve: recover the flag from the shipped file
OUT="$(python3 admin/solve.py handout/style_guide.pdf | tail -n 1)"
echo "recovered: $OUT"
if [ "$OUT" != "$EXPECTED" ]; then
  echo "VERIFY FAILED — solver recovered $OUT" >&2
  exit 1
fi

# 5. third-party cross-check when pypdf happens to be installed (optional)
if python3 -c 'import pypdf' 2>/dev/null; then
  python3 - <<'EOF'
from pypdf import PdfReader
r = PdfReader("handout/style_guide.pdf")
assert r.is_encrypted
assert r.decrypt("") != 0, "empty password rejected by pypdf"
assert len(r.pages) == 12, len(r.pages)
assert "INTERNAL BRAND SYSTEM" in r.pages[0].extract_text()
assert "master-assets.zip" in list(r.attachments.keys())
print("pypdf cross-check: opens with empty password, 12 pages, attachment ok")
EOF
else
  echo "pypdf not installed — skipping third-party cross-check"
fi

echo "VERIFY OK — locked-looking PDF opens passwordless, decoy ZIP is a dead end, coordinates decode"
