#!/usr/bin/env python3
"""Ghost Glyphs — organizer solver (no browser, no seed needed).

Statically reconstructs the hidden glyph rows from archive_07.svg:
  1. hash every <symbol>'s path geometry back to a character (against the
     canonical vector font in deployment/glyphs.py)
  2. collect every <use> row, order it by the x offsets carried in each
     <use transform="translate(x 0)">
  3. report every decoded row; the flag row matches the flag format
"""
import importlib.util
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SVG_NS = "http://www.w3.org/2000/svg"
XLINK_HREF = "{http://www.w3.org/1999/xlink}href"


def load_font():
    """Import the canonical glyph table from deployment/glyphs.py."""
    here = Path(__file__).resolve().parent
    glyph_mod = here.parent / "deployment" / "glyphs.py"
    spec = importlib.util.spec_from_file_location("glyphs", glyph_mod)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    fp2ch = {}
    for ch in mod.GLYPHS:
        fp2ch[mod.glyph_fingerprint(ch)] = ch
    return fp2ch


def decode(svg_path: Path, fp2ch):
    ns = {"s": SVG_NS}
    root = ET.parse(svg_path).getroot()

    # symbol id -> geometry fingerprint
    sym_fp = {}
    for sym in root.iter(f"{{{SVG_NS}}}symbol"):
        sid = sym.get("id")
        ds = [d.replace(" ", "") for d in
              (p.get("d", "") for p in sym.iter(f"{{{SVG_NS}}}path"))]
        sym_fp[sid] = ";".join(ds)

    # parent map so <use> elements can be grouped per glyph row
    parent = {}
    for p in root.iter():
        for c in p:
            parent[c] = p

    rows = []
    for use in root.iter(f"{{{SVG_NS}}}use"):
        href = use.get("href") or use.get(XLINK_HREF)
        if not href or not href.startswith("#"):
            continue
        fp = sym_fp.get(href[1:])
        ch = fp2ch.get(fp, "?")
        m = re.search(r"translate\(\s*(-?[\d.]+)", use.get("transform", ""))
        x = float(m.group(1)) if m else 0.0
        rows.append((parent.get(use), x, ch))

    grouped = {}
    for grp, x, ch in rows:
        grouped.setdefault(id(grp), [grp, []])[1].append((x, ch))

    decoded = []
    for _, (grp, items) in grouped.items():
        items.sort(key=lambda t: t[0])
        text = "".join(ch for _, ch in items)
        decoded.append(text)
    return decoded


def main():
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} archive_07.svg", file=sys.stderr)
        return 2
    svg = Path(sys.argv[1])
    fp2ch = load_font()
    found = []
    rows = [t for t in decode(svg, fp2ch) if len(t) >= 4]
    for text in rows:
        print(f"[row] {text}")
    # flag may be split across several transformed fragments — try joins
    candidates = list(rows)
    for a in rows:
        for b in rows:
            if a is not b:
                candidates.append(a + b)
    for text in candidates:
        if re.fullmatch(r"cyber_quest\{.*\}", text):
            found.append(text)
    if not found:
        print("no flag-format row recovered", file=sys.stderr)
        return 1
    print(found[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
