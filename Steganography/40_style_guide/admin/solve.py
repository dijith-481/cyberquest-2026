#!/usr/bin/env python3
"""Style Guide — reference solve (stdlib only).

Documented solve path, no PDF library needed:

  1. The PDF opens with an empty user password; the owner restrictions
     (no copying / editing / printing) are viewer-enforced. Confirm the
     file opens without any password at all.
  2. Parse the trailer xref, read /Encrypt, recompute the R=2 user key
     for the empty password and decrypt the content streams (RC4, V=1).
  3. Scan the decrypted streams in page order for text matrices
     "<x> <y> Tm". Carrier lines sit at x = 72.0 (= 0) or 72.5 (= 1);
     ordinary copy uses integer x positions and is ignored.
  4. First 16 bits (big-endian) give the flag byte length; the rest is
     the flag MSB first.

    python3 admin/solve.py handout/style_guide.pdf
"""

import hashlib
import re
import struct
import sys

PADDING = bytes([
    0x28, 0xBF, 0x4E, 0x5E, 0x4E, 0x75, 0x8A, 0x41, 0x64, 0x00, 0x4E, 0x56,
    0xFF, 0xFA, 0x01, 0x08, 0x2E, 0x2E, 0x00, 0xB6, 0xD0, 0x68, 0x3E, 0x80,
    0x2F, 0x0C, 0xA9, 0xFE, 0x64, 0x53, 0x69, 0x7A,
])


def rc4(key: bytes, data: bytes) -> bytes:
    s = list(range(256))
    j = 0
    for i in range(256):
        j = (j + s[i] + key[i % len(key)]) % 256
        s[i], s[j] = s[j], s[i]
    out = bytearray()
    i = j = 0
    for b in data:
        i = (i + 1) % 256
        j = (j + s[i]) % 256
        s[i], s[j] = s[j], s[i]
        out.append(b ^ s[(s[i] + s[j]) % 256])
    return bytes(out)


def read_xref(data: bytes) -> dict:
    pos = data.rfind(b"startxref")
    xref_pos = int(data[pos:].split()[1])
    assert data[xref_pos:xref_pos + 4] == b"xref"
    lines = data[xref_pos:].split(b"\n")
    assert lines[1].split() == [b"0"] or True
    count = int(lines[1].split()[1])
    table = {}
    for i in range(count):
        off = int(lines[2 + i][:10])
        if lines[2 + i][17:18] == b"n":
            table[i] = off
    return table


def get_obj(data: bytes, table: dict, num: int) -> bytes:
    off = table[num]
    end = data.index(b"endobj", off)
    return data[off:end]


def obj_stream(body: bytes) -> bytes:
    i = body.index(b"stream") + len(b"stream")
    if body[i:i + 2] == b"\r\n":
        i += 2
    elif body[i:i + 1] in (b"\n", b"\r"):
        i += 1
    j = body.index(b"endstream")
    raw = body[i:j]
    if raw.endswith(b"\r\n"):
        raw = raw[:-2]
    elif raw.endswith(b"\n") or raw.endswith(b"\r"):
        raw = raw[:-1]
    return raw


def parse_encrypt(body: bytes):
    o = re.search(rb"/O\s*<([0-9a-fA-F]+)>", body).group(1)
    u = re.search(rb"/U\s*<([0-9a-fA-F]+)>", body).group(1)
    p = int(re.search(rb"/P\s*(-?\d+)", body).group(1))
    return bytes.fromhex(o.decode()), bytes.fromhex(u.decode()), p


def solve(path: str) -> str:
    data = open(path, "rb").read()
    assert data.startswith(b"%PDF-"), "not a PDF"
    table = read_xref(data)

    trailer_m = re.search(rb"trailer\s*<<(.*?)>>\s*startxref", data, re.S)
    trailer = trailer_m.group(1)
    enc_num = int(re.search(rb"/Encrypt\s*(\d+)\s+0\s+R", trailer).group(1))
    id0 = bytes.fromhex(re.search(rb"/ID\s*\[<([0-9a-fA-F]+)>", trailer).group(1).decode())

    enc_body = get_obj(data, table, enc_num)
    O, U, P = parse_encrypt(enc_body)
    print("permissions P =", P, "(viewer-enforced restrictions)")

    # Recompute the R=2 user key for the EMPTY user password.
    user_pad = (b"" + PADDING)[:32]
    perms_u = struct.unpack("<I", struct.pack("<i", P))[0]
    key = hashlib.md5(user_pad + O + struct.pack("<I", perms_u) + id0).digest()[:5]
    check = rc4(key, PADDING)
    assert check == U, "empty-password user key mismatch — file needs a real password?"
    print("user password: empty (document opens with no password)")

    # Walk pages in /Kids order, decrypt each content stream.
    root_num = int(re.search(rb"/Root\s*(\d+)\s+0\s+R", trailer).group(1))
    catalog = get_obj(data, table, root_num)
    pages_num = int(re.search(rb"/Pages\s*(\d+)\s+0\s+R", catalog).group(1))
    pages = get_obj(data, table, pages_num)
    kids = [int(m) for m in re.findall(rb"(\d+)\s+0\s+R", pages.split(b"/Kids")[1].split(b"]")[0])]
    print("pages:", len(kids))

    bits = []
    for kn in kids:
        page = get_obj(data, table, kn)
        cn = int(re.search(rb"/Contents\s*(\d+)\s+0\s+R", page).group(1))
        body = get_obj(data, table, cn)
        stream = obj_stream(body)
        okey = hashlib.md5(key + struct.pack("<I", cn)[:3] + b"\x00\x00").digest()[:10]
        plain = rc4(okey, stream)
        for m in re.finditer(rb"([\d.]+(?:\s+[\d.]+){1,5})\s+Tm", plain):
            nums = m.group(1).split()
            # Six-operand form (1 0 0 1 x y Tm): x is the 5th; tolerate the
            # legacy two-operand form (x y Tm) the same way.
            x = float(nums[4] if len(nums) == 6 else nums[0])
            if abs(x - 72.0) < 0.06:
                bits.append(0)
            elif abs(x - 72.5) < 0.06:
                bits.append(1)
    print("carrier bits:", len(bits))

    nbytes = 0
    for b in bits[:16]:
        nbytes = (nbytes << 1) | b
    print("declared flag length:", nbytes)
    payload = bits[16:16 + nbytes * 8]
    assert len(payload) == nbytes * 8, "truncated bitstream"
    raw = bytearray()
    for i in range(nbytes):
        v = 0
        for b in payload[i * 8:(i + 1) * 8]:
            v = (v << 1) | b
        raw.append(v)
    flag = raw.decode("ascii")
    print("flag:", flag)
    assert flag.startswith("cyber_quest{") and flag.endswith("}"), "bad flag framing"
    return flag


if __name__ == "__main__":
    print(solve(sys.argv[1] if len(sys.argv) > 1 else "handout/style_guide.pdf"))
