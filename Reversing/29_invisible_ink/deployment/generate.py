#!/usr/bin/env python3
"""Invisible Ink (slot 29, Reversing, H0) — deterministic handout generator.

Regenerates everything in ../handout/ from a seed:

    python3 deployment/generate.py [--seed oe-invisible-ink-29] [--flag ...]

Mechanic: a vendored npm-style helper package whose `index.js` looks boring
and lint-clean, but every line carries trailing whitespace. The trailing
whitespace (space = 0, tab = 1, MSB first) decodes to a hidden JS module
that unseals the flag with the package version as the key.

Nothing here is secret; the solve path is in admin/solution.md.
Requires only the Python standard library. Node is needed only to
*run* the extracted payload, not to generate it.
"""

import argparse
import base64
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
HANDOUT = os.path.join(HERE, "..", "handout")
ORGANIZER = os.path.join(HERE, "organizer")

FLAG = "cyber_quest{wh1t3sp4c3_supply_ch41n_8f3a2c}"
VERSION = "2.4.1"
DEFAULT_SEED = "oe-invisible-ink-29"
DECOY_FLAG = "cyber_quest{d3pr3c4t3d_v1_s3al_r3m0v3d}"

# Visible source lines. No line may carry trailing whitespace here — the
# generator appends the entire payload as trailing whitespace afterwards.
VISIBLE = [
    "// oe-format 2.4.1 — string helpers for the badge-printing pipeline.",
    "// Vendored from the parallel-universe npm mirror. Dependency-free.",
    "// lint: prettier --check passes — no trailing whitespace.",
    "//",
    "// v1 receipt " + DECOY_FLAG + " retired with 2.0 — do not use.",
    "'use strict';",
    "",
    "function pad2(n) {",
    "  const s = String(n);",
    "  return s.length >= 2 ? s : '0' + s;",
    "}",
    "",
    "function padEnd(s, w, ch) {",
    "  s = String(s);",
    "  ch = ch === undefined ? ' ' : String(ch);",
    "  while (s.length < w) s = s + ch;",
    "  return s.slice(0, w);",
    "}",
    "",
    "function padStart(s, w, ch) {",
    "  s = String(s);",
    "  ch = ch === undefined ? ' ' : String(ch);",
    "  while (s.length < w) s = ch + s;",
    "  return s.slice(-w);",
    "}",
    "",
    "function trimLines(text) {",
    "  return String(text)",
    "    .split('\\n')",
    "    .map(function (l) { return l.trim(); })",
    "    .join('\\n');",
    "}",
    "",
    "function slugify(text) {",
    "  return String(text)",
    "    .toLowerCase()",
    "    .replace(/[^a-z0-9]+/g, '-')",
    "    .replace(/^-+|-+$/g, '')",
    "    .slice(0, 64);",
    "}",
    "",
    "function truncate(text, n) {",
    "  const s = String(text);",
    "  if (s.length <= n) return s;",
    "  return s.slice(0, n - 1) + '…';",
    "}",
    "",
    "function initials(name) {",
    "  return String(name)",
    "    .split(/\\s+/)",
    "    .filter(Boolean)",
    "    .map(function (w) { return w[0].toUpperCase(); })",
    "    .join('');",
    "}",
    "",
    "function maskEmail(addr) {",
    "  const parts = String(addr).split('@');",
    "  if (parts.length !== 2) return '***';",
    "  const user = parts[0];",
    "  const keep = user.slice(0, 2);",
    "  return keep + '***@' + parts[1];",
    "}",
    "",
    "function capitalize(word) {",
    "  const s = String(word);",
    "  if (!s) return s;",
    "  return s[0].toUpperCase() + s.slice(1).toLowerCase();",
    "}",
    "",
    "function titleCase(text) {",
    "  return String(text).split(' ').map(capitalize).join(' ');",
    "}",
    "",
    "function countOcc(haystack, needle) {",
    "  if (!needle) return 0;",
    "  let n = 0;",
    "  let i = String(haystack).indexOf(needle);",
    "  while (i !== -1) {",
    "    n += 1;",
    "    i = String(haystack).indexOf(needle, i + needle.length);",
    "  }",
    "  return n;",
    "}",
    "",
    "function lines(text) {",
    "  return String(text).split('\\n');",
    "}",
    "",
    "function unlines(arr) {",
    "  return arr.join('\\n');",
    "}",
    "",
    "function stamp(d) {",
    "  const t = d instanceof Date ? d : new Date(d);",
    "  return t.getFullYear() + '-' + pad2(t.getMonth() + 1) + '-' + pad2(t.getDate());",
    "}",
    "",
    "module.exports = {",
    "  pad2: pad2,",
    "  padEnd: padEnd,",
    "  padStart: padStart,",
    "  trimLines: trimLines,",
    "  slugify: slugify,",
    "  truncate: truncate,",
    "  initials: initials,",
    "  maskEmail: maskEmail,",
    "  capitalize: capitalize,",
    "  titleCase: titleCase,",
    "  countOcc: countOcc,",
    "  lines: lines,",
    "  unlines: unlines,",
    "  stamp: stamp,",
    "};",
]

PACKAGE_JSON = """{
  "name": "oe-format",
  "version": "VERSION",
  "description": "String helpers for the badge-printing pipeline.",
  "main": "index.js",
  "license": "OE-PROP"
}
""".replace("VERSION", VERSION)

NOTE_TXT = """oe-format // vendored dependency

Facilities vendored oe-format at 2.4.1 into the badge-printing pipeline.
Pinned, dependency-free, passed audit. Installed with --no-audit, as usual.

package.json — the pin.
index.js — the helper. It exports fourteen string functions and nothing else.
"""


def build_payload(flag: str, version: str) -> bytes:
    """Hidden module source: XOR-sealed flag, keyed by the package version."""
    raw = flag.encode()
    key = version.encode()
    sealed = bytes(b ^ key[i % len(key)] for i, b in enumerate(raw))
    blob = base64.b64encode(sealed).decode()
    src = (
        "// oe-format internal seal -- build artifact, do not edit\n"
        'const D=Buffer.from("%s","base64");const V="%s";\n'
        "function unseal(){let o=\"\";for(let i=0;i<D.length;i++)"
        "o+=String.fromCharCode(D[i]^V.charCodeAt(i%%V.length));return o;}\n"
        "module.exports.unseal=unseal;\n"
    ) % (blob, version)
    return src.encode("ascii")


def to_bits(data: bytes) -> str:
    return "".join(format(b, "08b") for b in data)


def spread_bits(bitstr: str, nlines: int, rng: random.Random):
    """Split the bit string into per-line chunk sizes (round-robin)."""
    chunks = [0] * nlines
    order = list(range(nlines))
    rng.shuffle(order)
    i = 0
    remaining = len(bitstr)
    k = 0
    while remaining > 0:
        # 8–28 bits per stop; keeps every line's tail a plausible accident.
        take = rng.randint(8, 28)
        take = min(take, remaining)
        chunks[order[k % nlines]] += take
        remaining -= take
        k += 1
        i += 1
        if i > 10 * (len(bitstr) + nlines):
            raise SystemExit("bit spreading did not converge")
    return chunks


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate the Invisible Ink challenge")
    ap.add_argument("--seed", default=DEFAULT_SEED)
    ap.add_argument("--flag", default=FLAG)
    ap.add_argument("--version", default=VERSION)
    args = ap.parse_args()

    for ln in VISIBLE:
        assert ln == ln.rstrip(" \t"), "visible source must start whitespace-clean"

    payload = build_payload(args.flag, args.version)
    assert all(b < 128 for b in payload), "payload must stay ASCII for bit framing"
    bits = to_bits(payload)

    rng = random.Random(args.seed)
    chunks = spread_bits(bits, len(VISIBLE), rng)
    assert sum(chunks) == len(bits)

    out_lines = []
    pos = 0
    for ln, n in zip(VISIBLE, chunks):
        tail = bits[pos:pos + n]
        pos += n
        ws = "".join("\t" if b == "1" else " " for b in tail)
        out_lines.append(ln + ws)
    assert pos == len(bits)

    os.makedirs(ORGANIZER, exist_ok=True)
    with open(os.path.join(ORGANIZER, "index.visible.js"), "w") as f:
        f.write("\n".join(VISIBLE) + "\n")
    with open(os.path.join(ORGANIZER, "payload.js"), "w") as f:
        f.write(payload.decode("ascii"))

    os.makedirs(HANDOUT, exist_ok=True)
    with open(os.path.join(HANDOUT, "index.js"), "w") as f:
        f.write("\n".join(out_lines) + "\n")
    with open(os.path.join(HANDOUT, "package.json"), "w") as f:
        f.write(PACKAGE_JSON)
    with open(os.path.join(HANDOUT, "NOTE.txt"), "w") as f:
        f.write(NOTE_TXT)

    print("flag: %s (len %d)" % (args.flag, len(args.flag)))
    print("payload: %d bytes -> %d bits over %d lines"
          % (len(payload), len(bits), len(VISIBLE)))
    print("handout written to %s" % os.path.normpath(HANDOUT))


if __name__ == "__main__":
    sys.exit(main())
