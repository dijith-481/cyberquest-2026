#!/usr/bin/env python3
"""payroll_photo — deterministic handout generator (stdlib only).

Builds the photograph the players receive:

  handout/all_hands.jpg   the annual all-hands snapshot, 320x240 baseline
                          JPEG, carrying one EXIF APP1 and one XMP APP1
                          and nothing else useful on the image itself

Where the flag is, and why it is not where a viewer shows it:

  EXIF  ImageDescription   the comment every phone and every image
                           viewer displays right under the photo. It is
                           a joke. It is rejected.
  XMP   dc:description     the Dublin Core description. Most viewers, and
                           most of the file's own contents, never read
                           it. The real flag is here.

Both live in APP1 segments before the image data, so nothing about the
challenge depends on decoding pixels. The pixel content is a synthetic
placeholder and is not a clue.

    python3 make_handout.py

The zip handed to players is built with:
  zip -j 53_payroll_photo.zip handout/*
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from jpeg import encode  # noqa: E402

HANDOUT = os.path.join(HERE, "..", "handout")

FLAG = "cyber_quest{th3_m3t4d4t4_1s_n0t_th3_phot0}"

# No decoy flag. There used to be a second flag-shaped string in EXIF's
# ImageDescription — the field every viewer renders — so that a player who
# checked the obvious place got a plausible-looking rejection. It was cut
# because it undermined the challenge: every real flag in this event ends in
# a random hex suffix and the decoy did not, so "does it end in hex" became a
# shortcut that gave the answer away without reading any metadata.
#
# ImageDescription keeps a real, truthful value instead. The lesson is
# unchanged and is the actual point of the challenge: a viewer renders EXIF
# and shows you this line, and shows you nothing at all about the XMP packet
# sitting a few hundred bytes later in the same file.
DESCRIPTION = "Annual all-hands, College Ground. Badge photo, do not circulate."

W, H = 320, 240

# --- byte order helpers --------------------------------------------------
# JPEG *segment* lengths are always big-endian. Everything inside the
# EXIF TIFF structure is little-endian, because the TIFF header below
# declares "II" (Intel). Mixing the two is the classic way to produce a
# segment that ImageMagick shrugs at and every other reader rejects, so
# the two families are kept visibly separate.

def _u16(v):
    return bytes([(v >> 8) & 0xFF, v & 0xFF])      # JPEG segment length


def _u32(v):
    return bytes([(v >> 24) & 0xFF, (v >> 16) & 0xFF, (v >> 8) & 0xFF, v & 0xFF])


def _le16(v):
    return bytes([v & 0xFF, (v >> 8) & 0xFF])      # TIFF


def _le32(v):
    return bytes([v & 0xFF, (v >> 8) & 0xFF, (v >> 16) & 0xFF, (v >> 24) & 0xFF])


# --- the synthetic photograph --------------------------------------------

def _pixels():
    """A dark room, a lit board, a few heads. Deterministic, no randomness."""
    px = bytearray(W * H * 3)
    for y in range(H):
        for x in range(W):
            r, g, b = 22, 24, 30
            # back wall gradient
            v = 14 + (y * 10) // H
            r, g, b = v, v, v + 4
            # the whiteboard
            if 30 <= x < 290 and 24 <= y < 150:
                edge = (x in (30, 289)) or (y == 24)
                if edge:
                    r, g, b = 120, 122, 128
                else:
                    r, g, b = 236, 238, 240
                # ruled lines on the board
                if y % 18 == 6 and 40 <= x < 280:
                    r, g, b = 150, 168, 196
            # a row of head silhouettes
            if 176 <= y < 240:
                cx = (x - 40) % 56
                if 0 <= cx < 34 and 198 <= y < 240 and (cx - 17) ** 2 + (y - 226) ** 2 < 15 ** 2:
                    r, g, b = 38, 34, 40
            i = (y * W + x) * 3
            px[i], px[i + 1], px[i + 2] = r, g, b
    return bytes(px)


# --- EXIF APP1 -----------------------------------------------------------

def _exif_segment():
    # TIFF layout:
    #   0  "II" + 42 + u32(8)          header, 8 bytes
    #   8  u16(count) + count*12 + u32(0)   IFD0, 2 + 12n + 4 bytes
    #   .. data area (values longer than 4 bytes)
    #
    # Offsets in the IFD are absolute from the start of the TIFF header, so
    # the data area begins at 8 + 2 + 12*count + 4. Getting that +4 wrong
    # (the next-IFD pointer) is the easy mistake and yields a segment that
    # every reader rejects, so it is computed here rather than by hand.
    entries = []   # (tag, type, count, payload_bytes) — payload is the full value
    data = bytearray()

    def add_ascii(tag, s):
        entries.append((tag, 2, len(s) + 1, s.encode("ascii") + b"\x00"))

    add_ascii(0x010E, DESCRIPTION)                            # ImageDescription
    add_ascii(0x0131, "FacilitiesPhone 2.1 (build 0918)")     # Software
    add_ascii(0x0132, "2026:09:18 09:14:11")                  # DateTime
    add_ascii(0x9003, "2026:09:18 09:14:11")                  # DateTimeOriginal
    entries.append((0xA002, 4, 1, _le32(W)))                  # PixelXDimension
    entries.append((0xA003, 4, 1, _le32(H)))                  # PixelYDimension

    entries.sort(key=lambda e: e[0])
    ifd_size = 2 + 12 * len(entries) + 4
    data_start = 8 + ifd_size

    ifd = _le16(len(entries))
    for tag, typ, count, payload in entries:
        if len(payload) <= 4:
            value = payload.ljust(4, b"\x00")
        else:
            value = _le32(data_start + len(data))
            data += payload
        ifd += _le16(tag) + _le16(typ) + _le32(count) + value
    ifd += _le32(0)   # no IFD1

    tiff = b"II" + _le16(42) + _le32(8) + ifd + bytes(data)
    return b"Exif\x00\x00" + tiff


# --- XMP APP1 ------------------------------------------------------------

XMP = (
    '<?xpacket begin="" id="W5M0MpCehiHzreSzNTczkc9d"?>'
    '<x:xmpmeta xmlns:x="adobe:ns:meta/">'
    '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
    '<rdf:Description rdf:about=""'
    ' xmlns:dc="http://purl.org/dc/elements/1.1/"'
    ' xmlns:xmp="http://ns.adobe.com/xap/1.0/"'
    ' xmlns:photoshop="http://ns.adobe.com/photoshop/1.0/">'
    '<dc:format>image/jpeg</dc:format>'
    '<dc:creator><rdf:Seq><rdf:li>Facilities</rdf:li></rdf:Seq></dc:creator>'
    '<xmp:CreatorTool>FacilitiesPhone 2.1 (build 0918)</xmp:CreatorTool>'
    '<xmp:CreateDate>2026-09-18T09:14:11Z</xmp:CreateDate>'
    '<photoshop:DateCreated>2026-09-18T09:14:11Z</photoshop:DateCreated>'
    f'<dc:description><rdf:Alt><rdf:li xml:lang="x-default">{FLAG}'
    '</rdf:li></rdf:Alt></dc:description>'
    '</rdf:Description></rdf:RDF></x:xmpmeta>'
    '<?xpacket end="w"?>'
)


def _xmp_segment():
    pad = b" " * (4 - (len(XMP) % 4)) if len(XMP) % 4 else b""
    return b"http://ns.adobe.com/xap/1.0/\x00" + XMP.encode("ascii") + pad


# --- assembly ------------------------------------------------------------

def main():
    os.makedirs(HANDOUT, exist_ok=True)
    out = os.path.join(HANDOUT, "all_hands.jpg")

    jpg = encode(W, H, _pixels())
    # Splice the metadata in immediately after SOI, which is where a
    # camera puts it and where every reader looks first.
    data = jpg[:2] + b"\xff\xe1" + _u16(len(_exif_segment()) + 2) + _exif_segment() \
        + b"\xff\xe1" + _u16(len(_xmp_segment()) + 2) + _xmp_segment() + jpg[2:]

    with open(out, "wb") as f:
        f.write(data)
    size = os.path.getsize(out)

    # --- guards: the challenge must not be solvable the easy way ---------
    assert data[:2] == b"\xff\xd8", "no SOI"
    assert data[-2:] == b"\xff\xd9", "no EOI"
    # exactly two APP1 segments, both before the frame header
    soi, sos = data.index(b"\xff\xda"), len(data)
    head = data[:sos]
    assert head.count(b"\xff\xe1") == 2, f"expected 2 APP1, saw {head.count(b'\\xff\\xe1')}"
    assert b"\xff\xc0" in head, "frame header must follow the APP1 segments"
    # The flag lives in XMP and nowhere else. Exactly one flag-shaped string in
    # the whole file, so there is no decoy for a player to trip over and no
    # shape-based shortcut to picking the right one.
    assert FLAG.encode() in XMP.encode(), "flag missing from XMP"
    assert FLAG.encode() not in _exif_segment(), "flag leaked into EXIF"
    assert b"cyber_quest{" not in _exif_segment(), \
        "a flag-shaped string is still present in EXIF"
    assert _pixels().count(b"cyber_quest{") == 0, "flag is in the pixel data"
    # the EXIF description is still there, because it is the visible half of
    # the lesson: a viewer shows this and shows nothing about the XMP.
    assert DESCRIPTION.encode() in _exif_segment(), \
        "ImageDescription missing — the visible half of the lesson"

    print(f"wrote {out} ({size} bytes, {W}x{H}, 2 APP1 segments)")


if __name__ == "__main__":
    main()
