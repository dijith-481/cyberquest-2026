#!/usr/bin/env python3
"""Style Guide — seeded handout generator for style_guide.pdf.

Builds the "OE Internal Brand System (Rev 3.9)" manual as a hand-assembled
PDF (no third-party libraries) with:

  * coordinate stego: every payload bit is one body line whose text matrix
    x is 72.0 (= 0) or 72.5 (= 1). The 0.5 pt shift is invisible on the
    page. Decoy text always uses integer x positions, so a Tm scan only
    ever matches carriers.
  * bitstream: 16-bit big-endian byte length of the flag, then the flag
    bytes MSB first.
  * owner-password encryption (PDF V=1 / R=2, 40-bit RC4, empty user
    password): the document opens with no password at all, but viewers
    report copying / editing / printing as "Not allowed". The owner
    password is random per seed and never shipped — there is nothing to
    crack; the restrictions are the misdirection.
  * embedded decoy: master-assets.zip (traditional ZipCrypto, random per
    seed password, deterministic bytes) holding wrong_direction.txt.
    The manual claims the ZIP password is "documented in the spacing
    specification" — the spacing page documents 72 pt / 0.5 pt, which is
    the decode rule, not a password.

Deterministic for a given (seed, flag). Nothing here is secret beyond the
flag itself; the solve path is documented in admin/solution.md.

    python3 deployment/generate.py --seed 40 --flag 'cyber_quest{...}' --out style_guide.pdf
"""

import argparse
import hashlib
import random
import struct
import zlib

# ---------------------------------------------------------------- constants

FLAG_DEFAULT = "cyber_quest{h4lf_p01nt_h1d3s_th3_gu1d3_9d4e2f}"
SEED_DEFAULT = 40

X_ZERO = "72.0"
X_ONE = "72.5"

# Standard PDF padding string (PDF Reference, Algorithm 3.2).
PADDING = bytes([
    0x28, 0xBF, 0x4E, 0x5E, 0x4E, 0x75, 0x8A, 0x41, 0x64, 0x00, 0x4E, 0x56,
    0xFF, 0xFA, 0x01, 0x08, 0x2E, 0x2E, 0x00, 0xB6, 0xD0, 0x68, 0x3E, 0x80,
    0x2F, 0x0C, 0xA9, 0xFE, 0x64, 0x53, 0x69, 0x7A,
])

# Deny print / modify / copy / annot-fill (bits 3-6 clear, bits 7+ set).
# 0xFFFFFFC0: viewers report printing / copying / editing as not allowed.
PERMS = -64

FIXED_DATE = "D:20260115000000Z"

SENTENCES = [
    "The mark always sits clear of competing shapes and photography.",
    "Clearspace equals the height of the wordmark block on all four sides.",
    "Never redraw the mark from memory or from a screenshot.",
    "Headlines set in the house grotesk, sentence case, never all caps.",
    "Body copy sets at nine point with thirteen point leading.",
    "Captions may set one size down and in the secondary ink.",
    "Approved inks are black, paper white, and the single accent.",
    "The accent is a signal, not a decoration, so spend it sparingly.",
    "One accent per spread is plenty; two is a meeting about it.",
    "Photography should look found, never staged, never glossy.",
    "Screenshots ship at native resolution with the chrome cropped out.",
    "Diagrams use the same stroke weight as the surrounding text.",
    "Arrowheads match the line weight; nothing here is clip art.",
    "Tables rule with hairlines only; zebra striping is not approved.",
    "Numbers align on the decimal; units sit in the same column.",
    "Dates render as 2026-01-15, never with slashes, never spelled out.",
    "Internal memos carry the revision number in the footer of page one.",
    "Draft watermarks read DRAFT in forty point outline, diagonal.",
    "Final documents remove the watermark before they leave the drive.",
    "File names use lower snake case with the revision appended.",
    "Archive every superseded revision; never overwrite a released file.",
    "The release branch is the only source of truth for print vendors.",
    "Proofs are checked against the release branch, not against email.",
    "If the proof disagrees with the screen, trust the proof and ask.",
    "Color values are specified, not sampled, from any contractor file.",
    "Coated and uncoated stocks use their own approved conversions.",
    "Large areas of accent ink require a drawdown before the full run.",
    "Registration tolerance is tighter than the vendor thinks is funny.",
    "Paper is specified by weight first and by brightness second.",
    "Recycled stock is preferred wherever the run length allows it.",
    "Voice of the brand is plain, dry, and slightly tired, like staff.",
    "Short sentences are preferred; fragments are tolerated in signage.",
    "Exclamation points are not approved for internal documentation.",
    "Jargon must earn its place; define it once, then use it plainly.",
    "Placeholder copy never ships; lorem ipsum is a release blocker.",
    "Every chart needs a title that states the conclusion in words.",
    "Axes start at zero unless engineering signs off on the exception.",
    "Legends sit outside the plot area, ordered by final value.",
    "Footnotes set smaller and carry the doubts the headline cannot.",
    "Motion, where used, eases out and settles within three hundred ms.",
    "Loading states describe the step; spinners never spin without text.",
    "Error copy names the problem and the next step, in that order.",
    "Empty states suggest one action, not a tour of the product.",
    "Icons are line drawn at two pixels and never filled without review.",
    "Corners round at two radii only: small for controls, large for cards.",
    "Shadows are shallow and neutral; floating interfaces do not soar.",
    "Focus states are always visible; keyboard staff are staff too.",
    "Contrast minimums apply to placeholder text exactly as to labels.",
    "Touch targets measure no less than forty four points on the short side.",
    "Forms ask for the minimum and explain every optional field.",
    "Defaults respect the user; preselected consent is not consent.",
    "Confirmations state what happened and where to find the record.",
    "Undo is preferred over a confirmation dialog wherever feasible.",
    "Session timeouts warn twice before they sign anyone out.",
    "Exports include the revision number so archives stay sortable.",
    "Imports validate first and report every rejected row by number.",
    "Backups run before migrations, not after the incident review.",
    "Access grants expire; standing access requires a named approver.",
    "Incident notes record what was true at the time, not what is now.",
    "Postmortems name systems and sequences, never individual staff.",
    "Vendor demos are evaluated against the checklist, not the catering.",
    "Procurement prefers boring tools with boring release notes.",
    "Renewals need a usage printout attached before anyone countersigns.",
    "Travel decks use the title slide and the agenda slide only.",
    "All hands slides are due the day before, without exception noted.",
    "Questions in meetings are documented with the answer or the owner.",
    "Decisions record the options considered, not just the winner.",
    "The office map by the lift is the current one; the wiki map is not.",
    "Desk plants are real where possible; fake where the light says so.",
    "The hold music is a separate system and nobody here maintains it.",
]

SPECIMEN_LABEL = "Figure 3.9 -- alignment specimens (do not re-set)"

# ---------------------------------------------------------------- pure-python RC4


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


# ---------------------------------------------------------------- PDF string helpers


def pdf_escape(data: bytes) -> bytes:
    out = bytearray()
    for b in data:
        if b == 0x5C:
            out += b"\\\\"
        elif b == 0x28:
            out += b"\\("
        elif b == 0x29:
            out += b"\\)"
        elif 32 <= b <= 126:
            out.append(b)
        else:
            out += ("\\%03o" % b).encode("ascii")
    return bytes(out)


def object_key(file_key: bytes, objnum: int) -> bytes:
    """Per-object RC4 key (Algorithm 3.1): MD5(file_key + objnum + gen),
    first n+5 = 10 bytes for the 40-bit file key."""
    return hashlib.md5(file_key + struct.pack("<I", objnum)[:3] + b"\x00\x00").digest()[:10]


def lit(data: bytes, objnum: int, user_key: bytes) -> bytes:
    """Encrypt a literal-string payload with the object's key, then escape."""
    return b"(" + pdf_escape(rc4(object_key(user_key, objnum), data)) + b")"


# ---------------------------------------------------------------- deterministic ZipCrypto (traditional PKWARE)
# NOTE: this must use the *raw* CRC register primitive
#   crc(ch, reg) = (reg >> 8) ^ table[(reg ^ ch) & 0xFF]
# and NOT zlib.crc32 (which folds the init/final XOR in and out and
# produces a different keystream). Mirrors CPython's zipfile._ZipDecrypter.


def _make_crctable():
    table = []
    for i in range(256):
        c = i
        for _ in range(8):
            c = (0xEDB88320 ^ (c >> 1)) if (c & 1) else (c >> 1)
        table.append(c & 0xFFFFFFFF)
    return table


_CRCTABLE = _make_crctable()


def _crc_byte(reg: int, c: int) -> int:
    return ((reg >> 8) ^ _CRCTABLE[(reg ^ c) & 0xFF]) & 0xFFFFFFFF


def zipcrypto_init(password: bytes):
    keys = [0x12345678, 0x23456789, 0x34567890]
    for c in password:
        keys[0] = _crc_byte(keys[0], c)
        keys[1] = ((keys[1] + (keys[0] & 0xFF)) * 134775813 + 1) & 0xFFFFFFFF
        keys[2] = _crc_byte(keys[2], (keys[1] >> 24) & 0xFF)
    return keys


def zipcrypto_stream_byte(keys) -> int:
    k = keys[2] | 2
    return (((k * (k ^ 1)) >> 8) & 0xFF)


def zipcrypto_update(keys, c: int):
    keys[0] = _crc_byte(keys[0], c)
    keys[1] = ((keys[1] + (keys[0] & 0xFF)) * 134775813 + 1) & 0xFFFFFFFF
    keys[2] = _crc_byte(keys[2], (keys[1] >> 24) & 0xFF)


def build_encrypted_zip(files: dict, password: bytes, rng: random.Random) -> bytes:
    """Minimal deterministic ZipCrypto archive. Fixed DOS timestamp."""
    dos_time = (12 << 11) | (0 << 5) | 0  # 12:00:00
    dos_date = ((2026 - 1980) << 9) | (1 << 5) | 15  # 2026-01-15
    central = bytearray()
    offset = 0
    out = bytearray()
    for name in sorted(files):
        raw = files[name]
        crc = zlib.crc32(raw) & 0xFFFFFFFF
        # Raw deflate stream (strip the zlib wrapper) for the file data.
        comp = zlib.compress(raw, 6)[2:-4]
        keys = zipcrypto_init(password)
        header_plain = bytes(rng.randrange(256) for _ in range(11)) + bytes([(crc >> 24) & 0xFF])
        enc = bytearray()
        for b in header_plain:
            enc.append(b ^ zipcrypto_stream_byte(keys))
            zipcrypto_update(keys, b)
        for b in comp:
            enc.append(b ^ zipcrypto_stream_byte(keys))
            zipcrypto_update(keys, b)
        enc = bytes(enc)
        name_b = name.encode("ascii")
        local = struct.pack("<IHHHHHIIIHH", 0x04034B50, 20, 0x1, 8,
                            dos_time, dos_date, crc, len(enc), len(raw),
                            len(name_b), 0)
        out += local + name_b + enc
        central += struct.pack("<IHHHHHHIIIHHHHHII", 0x02014B50, 0, 20, 0x1, 8,
                               dos_time, dos_date, crc, len(enc), len(raw),
                               len(name_b), 0, 0, 0, 0, 0, offset)
        central += name_b
        offset += len(local) + len(name_b) + len(enc)
    cd_start = len(out)
    out += central
    out += struct.pack("<IHHHHIIH", 0x06054B50, 0, 0, len(files), len(files),
                       len(central), cd_start, 0)
    return bytes(out)


# ---------------------------------------------------------------- payload bits


def flag_bits(flag: str) -> list:
    raw = flag.encode("ascii")
    if len(raw) > 65535:
        raise ValueError("flag too long")
    bits = []
    for i in range(16):
        bits.append((len(raw) >> (15 - i)) & 1)
    for byte in raw:
        for i in range(8):
            bits.append((byte >> (7 - i)) & 1)
    return bits


# ---------------------------------------------------------------- content streams (plaintext, encrypted later)


def text_line(x: str, y: int, size: int, s: str) -> bytes:
    # Tm takes all six matrix operands: identity plus translation (x, y).
    return b"BT /F1 %d Tf 1 0 0 1 %s %d Tm (%s) Tj ET\n" % (size, x.encode(), y, pdf_escape(s.encode()))


def decoy(x: int, y: int, size: int, s: str) -> bytes:
    return text_line(str(x), y, size, s)


def carrier(bit: int, y: int, s: str) -> bytes:
    return text_line(X_ONE if bit else X_ZERO, y, 9, s)


def rule(y: int) -> bytes:
    return b"0.5 w 90 %d m 522 %d l S\n" % (y, y)


def build_pages(bits: list, rng: random.Random):
    """Return a list of plaintext content streams, in reading order."""
    pages = []
    pool = SENTENCES[:]
    rng.shuffle(pool)
    words = iter(pool * ((len(bits) // len(pool)) + 2))

    def fill(n: int, start_y: int = 700, step: int = 14):
        nonlocal bits
        chunk, bits = bits[:n], bits[n:]
        body = b""
        y = start_y
        for b in chunk:
            body += carrier(b, y, next(words))
            y -= step
        return body

    # Page 1: cover (decoys only, integer x).
    cover = b""
    cover += decoy(90, 640, 22, "INTERNAL BRAND SYSTEM")
    cover += decoy(90, 612, 13, "Style guide for staff and vendors")
    cover += rule(596)
    cover += decoy(90, 566, 12, "Protected document -- do not modify or redistribute.")
    cover += decoy(90, 548, 12, "Revision 3.9")
    cover += rule(512)
    cover += decoy(90, 482, 11, "Distribution password policy:")
    cover += decoy(110, 464, 10, "Passwords follow BrandName + revision number.")
    cover += decoy(110, 448, 10, "Example format only. Ask brand ops for the current one.")
    cover += decoy(90, 414, 10, "This copy is assigned to universe B imports, dock 4.")
    pages.append(cover)

    # Page 2: spacing system (the clue page) + first carriers as specimens.
    spacing = b""
    spacing += decoy(90, 720, 16, "2  SPACING SYSTEM")
    spacing += rule(706)
    spacing += decoy(90, 682, 11, "Base grid: 72 pt. All text aligns to the grid.")
    spacing += decoy(90, 664, 11, "Optical adjustment: 0.5 pt where the eye demands it.")
    spacing += decoy(90, 646, 11, "Never eyeball alignment. Every half-point matters.")
    spacing += decoy(90, 622, 10, "Attachment: master-assets.zip (confidential source package).")
    spacing += decoy(90, 606, 10, "The ZIP password is documented in this section. Read closely.")
    spacing += decoy(90, 578, 10, SPECIMEN_LABEL)
    pages.append(spacing + fill(20, 556, 14))

    # Body pages: manual filler, every line a carrier.
    headings = ["3  COLOR", "4  TYPE", "5  LOGO CLEARSPACE", "6  VOICE",
                "7  IMAGERY", "8  MOTION", "9  TABLES AND NUMBERS",
                "10  FILES AND ARCHIVE", "11  REVISION LOG"]
    hi = 0
    while bits:
        head = headings[hi % len(headings)]
        hi += 1
        page = decoy(90, 730, 14, head) + rule(716)
        n = min(44, len(bits))
        page += fill(n, 692, 14)
        pages.append(page)

    # Back page: attachment note (decoys only) + file-attachment annot target.
    back = b""
    back += decoy(90, 720, 14, "12  SOURCE PACKAGE")
    back += rule(706)
    back += decoy(90, 682, 11, "master-assets.zip travels with this guide.")
    back += decoy(90, 664, 11, "Confidential source package. Password required.")
    back += decoy(90, 646, 11, "If the password memo is missing, brand ops will not reissue it.")
    back += decoy(90, 618, 10, "Open the attachment from theAttachments panel of your reader.")
    pages.append(back)
    return pages


# ---------------------------------------------------------------- PDF assembly


def build_pdf(flag: str, seed: int) -> bytes:
    rng = random.Random(seed)
    bits = flag_bits(flag)

    owner_pwd = "".join(rng.choice("ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789")
                        for _ in range(16)).encode("ascii")
    file_id = bytes(rng.randrange(256) for _ in range(16))

    user_pad = (b"" + PADDING)[:32]
    owner_pad = (owner_pwd + PADDING)[:32]
    o_key = hashlib.md5(owner_pad).digest()[:5]
    O = rc4(o_key, user_pad)
    perms_u = struct.unpack("<I", struct.pack("<i", PERMS))[0]
    enc_key = hashlib.md5(user_pad + O + struct.pack("<I", perms_u) + file_id).digest()[:5]
    U = rc4(enc_key, PADDING)

    zip_pwd = "".join(rng.choice("abcdefghijkmnopqrstuvwxyz23456789") for _ in range(14)).encode("ascii")
    zip_bytes = build_encrypted_zip({
        "README.txt": b"master assets for the brand refresh.\n"
                      b"Password policy: BrandName + revision number.\n"
                      b"If this file confuses you, re-read section 2 closely.\n",
        "wrong_direction.txt": b"Wrong direction.\n"
                               b"\n"
                               b"This package was never the point. The spacing\n"
                               b"specification is not a password hint -- it is the\n"
                               b"extraction rule. Every half-point matters.\n",
    }, zip_pwd, rng)

    streams_plain = build_pages(bits, rng)

    # Object numbering.
    objects = {}
    nxt = [1]

    def newnum():
        n = nxt[0]
        nxt[0] += 1
        return n

    catalog_n = newnum()   # 1
    pages_n = newnum()     # 2
    font_n = newnum()      # 3
    info_n = newnum()      # 4
    encrypt_n = newnum()   # 5
    filespec_n = newnum()  # 6
    zip_n = newnum()       # 7
    page_ns = []
    content_ns = []
    for _ in streams_plain:
        page_ns.append(newnum())
        content_ns.append(newnum())

    def L(data: bytes, objnum: int) -> bytes:
        return lit(data, objnum, enc_key)

    # Content stream objects (encrypt stream data with object key).
    for cn, plain in zip(content_ns, streams_plain):
        enc = rc4(object_key(enc_key, cn), plain)
        objects[cn] = b"<< /Length %d >>\nstream\n" % len(enc) + enc + b"\nendstream"

    # Embedded zip stream.
    zenc = rc4(object_key(enc_key, zip_n), zip_bytes)
    objects[zip_n] = (b"<< /Type /EmbeddedFile /Length %d /Params << /Size %d >> >>\nstream\n"
                      % (len(zenc), len(zip_bytes))) + zenc + b"\nendstream"

    # File specification.
    objects[filespec_n] = (b"<< /Type /Filespec /F " + L(b"master-assets.zip", filespec_n)
                           + b" /UF " + L(b"master-assets.zip", filespec_n)
                           + b" /Desc " + L(b"Confidential source package. Password required.", filespec_n)
                           + b" /EF << /F %d 0 R >> >>" % zip_n)

    # Font.
    objects[font_n] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>"

    # Info.
    objects[info_n] = (b"<< /Title " + L(b"OE Internal Brand System -- Style Guide (Rev 3.9)", info_n)
                       + b" /Author " + L(b"ordinary engineering, brand ops", info_n)
                       + b" /Creator " + L(b"brand ops doc pipeline", info_n)
                       + b" /Producer " + L(b"brand ops doc pipeline", info_n)
                       + b" /CreationDate " + L(FIXED_DATE.encode(), info_n) + b" >>")

    # Encrypt dict (never encrypted itself).
    objects[encrypt_n] = (b"<< /Filter /Standard /V 1 /R 2 /Length 40 /O <%s> /U <%s> /P %d >>"
                          % (O.hex().encode(), U.hex().encode(), PERMS))

    # Page objects.
    back_annot = (b"<< /Type /Annot /Subtype /FileAttachment /Rect [90 560 140 600] "
                  b"/Contents " + L(b"master-assets.zip", page_ns[-1])
                  + b" /FS %d 0 R /Name /Paperclip >>" % filespec_n)
    for i, (pn, cn) in enumerate(zip(page_ns, content_ns)):
        if i == len(page_ns) - 1:
            objects[pn] = (b"<< /Type /Page /Parent %d 0 R /MediaBox [0 0 612 792] "
                           b"/Resources << /Font << /F1 %d 0 R >> >> /Contents %d 0 R "
                           b"/Annots [%s] >>" % (pages_n, font_n, cn, back_annot))
        else:
            objects[pn] = (b"<< /Type /Page /Parent %d 0 R /MediaBox [0 0 612 792] "
                           b"/Resources << /Font << /F1 %d 0 R >> >> /Contents %d 0 R >>"
                           % (pages_n, font_n, cn))

    # Pages tree.
    objects[pages_n] = (b"<< /Type /Pages /Kids [" + b" ".join(b"%d 0 R" % p for p in page_ns)
                        + b"] /Count %d >>" % len(page_ns))

    # Catalog with embedded-file names.
    objects[catalog_n] = (b"<< /Type /Catalog /Pages %d 0 R /PageMode /UseAttachments /Names "
                          b"<< /EmbeddedFiles << /Names [" % pages_n
                          + L(b"master-assets.zip", catalog_n) + b" %d 0 R] >> >> >>" % filespec_n)

    # Serialize.
    out = bytearray()
    out += b"%PDF-1.4\n%\xE2\xE3\xCF\xD3\n"
    offsets = {}
    for n in range(1, nxt[0]):
        offsets[n] = len(out)
        out += b"%d 0 obj\n" % n + objects[n] + b"\nendobj\n"
    xref_pos = len(out)
    out += b"xref\n0 %d\n" % nxt[0]
    out += b"0000000000 65535 f \n"
    for n in range(1, nxt[0]):
        out += b"%010d 00000 n \n" % offsets[n]
    out += (b"trailer\n<< /Size %d /Root %d 0 R /Encrypt %d 0 R /Info %d 0 R "
            b"/ID [<%s> <%s>] >>\nstartxref\n%d\n%%%%EOF\n"
            % (nxt[0], catalog_n, encrypt_n, info_n, file_id.hex().encode(), file_id.hex().encode(), xref_pos))
    return bytes(out)


# ---------------------------------------------------------------- main


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=SEED_DEFAULT)
    ap.add_argument("--flag", default=FLAG_DEFAULT)
    ap.add_argument("--out", default="style_guide.pdf")
    args = ap.parse_args()
    data = build_pdf(args.flag, args.seed)
    with open(args.out, "wb") as f:
        f.write(data)
    print("wrote %s (%d bytes, %d carrier bits)" % (args.out, len(data), len(flag_bits(args.flag))))


if __name__ == "__main__":
    main()
