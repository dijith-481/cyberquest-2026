#!/usr/bin/env python3
"""Reference solve for Payroll Photo (challenge 53).

Reads the JPEG, walks its APP1 segments, prints the EXIF IFD, then
parses the XMP packet and returns the flag.

There is no dependency on exiftool or Pillow: everything here is stdlib,
so the reference solve proves the flag is reachable from the bytes alone
on a machine with nothing installed.

Usage:
    python3 solve.py handout/all_hands.jpg
"""

import re
import struct
import sys
from pathlib import Path

FLAG_RE = re.compile(r"cyber_quest\{[A-z0-9_!@#$%^&*+.-]+\}")

TAG_NAMES = {
    0x010E: "ImageDescription",
    0x0131: "Software",
    0x0132: "DateTime",
    0x9003: "DateTimeOriginal",
    0xA002: "PixelXDimension",
    0xA003: "PixelYDimension",
}
TYPE_SIZE = {1: 1, 2: 1, 3: 2, 4: 4, 5: 8, 7: 1}


def segments(data: bytes):
    """Yield (marker, payload) for every marker segment after SOI."""
    if data[:2] != b"\xff\xd8":
        raise SystemExit("not a JPEG (no SOI)")
    i = 2
    while i < len(data) - 1 and data[i] == 0xFF:
        marker = data[i + 1]
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            i += 2
            continue
        if marker == 0xDA:          # SOS: entropy data follows
            break
        length = struct.unpack(">H", data[i + 2:i + 4])[0]
        yield marker, data[i + 4:i + 2 + length]
        i += 2 + length


def parse_exif(tiff: bytes):
    """Parse a little-endian TIFF IFD0. Returns [(tag, tagname, value)]."""
    if tiff[:2] != b"II":
        raise SystemExit("expected a little-endian TIFF header")
    magic, ifd0 = struct.unpack("<HI", tiff[2:8])
    if magic != 42:
        raise SystemExit(f"bad TIFF magic {magic}")
    out = []
    count = struct.unpack("<H", tiff[ifd0:ifd0 + 2])[0]
    for k in range(count):
        e = tiff[ifd0 + 2 + k * 12: ifd0 + 14 + k * 12]
        tag, typ, cnt = struct.unpack("<HHI", e[:8])
        size = TYPE_SIZE.get(typ, 1) * cnt
        if size > 4:
            off = struct.unpack("<I", e[8:12])[0]
            raw = tiff[off:off + size]
        else:
            raw = e[8:12][:size]
        if typ == 2:
            value = raw.rstrip(b"\x00").decode("ascii", "replace")
        elif typ == 4:
            value = struct.unpack("<I", raw)[0]
        else:
            value = raw.hex()
        out.append((tag, TAG_NAMES.get(tag, hex(tag)), value))
    return out


def xmp_text(packet: bytes) -> str:
    return packet.decode("utf-8", "replace")


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    path = Path(sys.argv[1])
    data = path.read_bytes()

    exif_fields, xmp = [], ""
    for marker, payload in segments(data):
        if payload.startswith(b"Exif\x00\x00"):
            exif_fields = parse_exif(payload[6:])
        elif payload.startswith(b"http://ns.adobe.com/xap/1.0/"):
            xmp = xmp_text(payload.split(b"\x00", 1)[1])

    print("EXIF (this is what a viewer shows you):")
    for _tag, name, value in exif_fields:
        print(f"  {name:<20} {value}")

    if not xmp:
        print("\nno XMP packet in this file", file=sys.stderr)
        return 1
    print(f"\nXMP packet: {len(xmp)} bytes, dc:description present: "
          f"{'<dc:description>' in xmp}")

    hits = [h for h in FLAG_RE.findall(xmp)]
    if len(hits) != 1:
        print(f"expected exactly 1 flag in XMP, found {len(hits)}", file=sys.stderr)
        return 1

    # Guard: the EXIF decoy must not be the one we return.
    exif_hits = FLAG_RE.findall(" ".join(str(v) for _t, _n, v in exif_fields))
    if hits[0] in exif_hits:
        print("XMP and EXIF agree — challenge is ambiguous", file=sys.stderr)
        return 1

    print(f"\n{hits[0]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
