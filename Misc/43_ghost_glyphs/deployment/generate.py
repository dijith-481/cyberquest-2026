#!/usr/bin/env python3
"""Ghost Glyphs — seeded generator for archive_07.svg.

Builds the Spectral Observatory poster with the hidden signal layer:
  * custom vector glyph alphabet in anonymous <symbol> defs (shuffled, random ids)
  * flag assembled only through SVG2 <use href="#..."> references
  * <use> elements shuffled in XML; reading order carried by x offsets
  * nested rotate/translate/mirror transforms, cancelled by an inverse
    matrix wrapper so browsers render the row upright
  * mask fragments (moonlight-band blobs), CSS custom-property indirection
  * a fully masked decoy glyph row ("nothing was here")
  * a base64-embedded calibration plate (inner SVG) that reveals the
    glyph-id reading order — never the characters themselves

Deterministic for a given (seed, flag). See admin/solution.md.
"""

import argparse
import base64
import math
import random
import string
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from glyphs import GLYPHS, GLYPH_BOX_W, GLYPH_BOX_H  # noqa: E402

DECOY_ROW = "nothing was here"
DECOY_TEXT_FLAG = "cyber_quest{n0_s1gn4l_d3t3ct3d}"

# ---------------------------------------------------------------- matrices
# affine transform as (a, b, c, d, e, f) — SVG matrix() order:
#   x' = a*x + c*y + e ; y' = b*x + d*y + f


def m_mul(m, n):
    a1, b1, c1, d1, e1, f1 = m
    a2, b2, c2, d2, e2, f2 = n
    return (
        a1 * a2 + c1 * b2,
        b1 * a2 + d1 * b2,
        a1 * c2 + c1 * d2,
        b1 * c2 + d1 * d2,
        a1 * e2 + c1 * f2 + e1,
        b1 * e2 + d1 * f2 + f1,
    )


def m_inv(m):
    a, b, c, d, e, f = m
    det = a * d - b * c
    ia, id_ = d / det, a / det
    ib, ic = -b / det, -c / det
    return (ia, ib, ic, id_, -(ia * e + ic * f), -(ib * e + id_ * f))


def m_str(m):
    return "matrix(%g %g %g %g %g %g)" % m


def m_rot(deg):
    r = math.radians(deg)
    return (math.cos(r), math.sin(r), -math.sin(r), math.cos(r), 0, 0)


def m_translate(tx, ty):
    return (1, 0, 0, 1, tx, ty)


def m_scale(sx, sy):
    return (sx, 0, 0, sy, 0, 0)


IDENTITY = (1, 0, 0, 1, 0, 0)

# ---------------------------------------------------------------- helpers


def rand_id(rng, taken, length=4):
    while True:
        gid = "".join(rng.choice(string.ascii_lowercase + string.digits) for _ in range(length))
        if gid[0].isalpha() and gid not in taken:
            taken.add(gid)
            return gid


def build_glyph_row(rng, text, ids, step, scale):
    """Build a glyph row: shuffled <use> lines + cancelling transform chain.

    Returns (body_xml, chain_ops, wrapper_str). chain_ops is the inner
    obfuscation applied outer->inner; wrapper is its exact inverse, so the
    net transform on the glyphs is identity and browsers render the row
    upright at the position of the outer translate group.
    """
    items = []
    for k in range(len(text)):
        items.append(
            f'<use href="#{ids[text[k]]}" transform="translate({k * step} 0)" '
            f'width="{GLYPH_BOX_W}" height="{GLYPH_BOX_H}"/>'
        )
    rng.shuffle(items)
    body = "\n".join(items)

    a = rng.choice([v for v in range(-25, 26) if abs(v) > 6])
    b = rng.choice([v for v in range(-20, 21) if abs(v) > 5])
    tx, ty = rng.randint(-40, 40), rng.randint(-30, 30)
    chain = [
        f"rotate({a})",
        f"translate({tx} {ty})",
        f"scale({-scale:g} {scale:g})",
        f"rotate({b})",
    ]
    inner = m_mul(m_mul(m_rot(a), m_translate(tx, ty)), m_scale(-scale, scale))
    inner = m_mul(inner, m_rot(b))
    wrapper = m_inv(inner)
    prod = m_mul(wrapper, inner)
    assert all(abs(prod[i] - IDENTITY[i]) < 1e-9 for i in range(6)), prod
    return body, chain, m_str(wrapper)


def symbol_xml(gid, ch):
    paths = "\n".join(f'      <path d="{d}"/>' for d in GLYPHS[ch])
    return (
        f'    <symbol id="{gid}" viewBox="0 0 {GLYPH_BOX_W} {GLYPH_BOX_H}">\n'
        f'      <g fill="none" stroke="currentColor" stroke-width="1.15" '
        f'stroke-linecap="round" stroke-linejoin="round">\n{paths}\n      </g>\n'
        f"    </symbol>"
    )


def row_group_xml(indent, cls, color, opacity, mask_ref, x0, y0, scale, body, chain, wrapper, extra=()):
    pad = " " * indent
    lines = [
        f'{pad}<g class="{cls}" mask="url(#{mask_ref})" opacity="{opacity}" color="{color}">',
        f'{pad}  <g transform="translate({x0} {y0}) scale({scale:g})">',
        f'{pad}    <g transform="{wrapper}">',
    ]
    depth = 3
    for op in chain:
        lines.append(f'{pad}{"  " * depth}<g transform="{op}">')
        depth += 1
    lines.append(f'{pad}{"  " * depth}{body}')
    for op in reversed(chain):
        depth -= 1
        lines.append(f'{pad}{"  " * depth}</g>')
    lines.append(f'{pad}    </g>')
    lines.append(f'{pad}  </g>')
    lines.append(f'{pad}</g>')
    lines.extend(extra)
    return "\n".join(lines)


def plaque_svg(ids_in_order):
    per_row = 6
    entries = [f"{i + 1:02d} {gid}" for i, gid in enumerate(ids_in_order)]
    lines = [entries[i:i + per_row] for i in range(0, len(entries), per_row)]
    h = 30 + len(lines) * 11 + 6
    dots = []
    for i in range(len(ids_in_order)):
        dx = 15 + (i % per_row) * 38
        dy = 30.5 + (i // per_row) * 11
        dots.append(f'<circle cx="{dx:.1f}" cy="{dy:.1f}" r="1" fill="#3d6f8c"/>')
    rows = "\n".join(
        f'  <text x="26" y="{34 + li * 11}" font-family="monospace" font-size="9" '
        f'fill="#9fe8ff" letter-spacing="1.5">{"   ".join(line)}</text>'
        for li, line in enumerate(lines)
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="240" height="{h}" '
        f'viewBox="0 0 240 {h}">\n'
        f'  <rect width="240" height="{h}" fill="#0a121c"/>\n'
        f'  <rect x="4" y="4" width="232" height="{h - 8}" fill="none" stroke="#2c4a5e"/>\n'
        f'  <text x="14" y="20" font-family="monospace" font-size="9" fill="#7fc8ff" '
        f'letter-spacing="2">PLATE 07 // SIGNAL ORDER</text>\n'
        f"  {'' .join(dots)}\n{rows}\n</svg>"
    )


# ---------------------------------------------------------------- generator


def generate(seed: int, flag: str) -> str:
    rng = random.Random(f"{seed}|{flag}")
    template = (Path(__file__).parent / "art_template.svg").read_text()

    charset = sorted(set(flag))
    missing = [c for c in charset if c not in GLYPHS]
    if missing:
        raise SystemExit(f"flag has glyphs outside the vector font: {missing!r}")

    taken = set()
    ids = {ch: rand_id(rng, taken) for ch in GLYPHS}  # full alphabet as camouflage

    # ---- defs: symbols in shuffled order ---------------------------------
    order = list(GLYPHS)
    rng.shuffle(order)
    defs_out = "\n".join(symbol_xml(ids[ch], ch) for ch in order)

    # ---- signal layer: two transformed fragments ---------------------------
    step, scale = 10, 1.5
    sig_cls = "sig" + rand_id(rng, taken)
    gain_var = "gain" + rand_id(rng, taken)
    tone_var = "tone" + rand_id(rng, taken)
    mute_var = "mute" + rand_id(rng, taken)
    decoy_cls = "res" + rand_id(rng, taken)

    def fragment(text, x_range, y_range, taken):
        span = (len(text) - 1) * step * scale + GLYPH_BOX_W * scale
        xf = rng.randint(*x_range)
        yf = rng.randint(*y_range)
        fbody, fchain, fwrapper = build_glyph_row(rng, text, ids, step, scale)
        fmask = "mk" + rand_id(rng, taken)
        blobs = []
        for _ in range(rng.randint(4, 6)):
            bx = rng.randint(int(xf + 30), int(xf + span - 30))
            by = yf + scale * rng.randint(3, 14)
            blobs.append(
                f'      <ellipse cx="{bx}" cy="{by:.0f}" rx="{rng.randint(26, 50)}" '
                f'ry="{rng.randint(10, 19)}" fill="#04070d"/>'
            )
        blobs.append(
            f'      <ellipse cx="{xf + span - 18:.0f}" cy="{yf + 9}" rx="34" '
            f'ry="17" fill="#04070d"/>'
        )
        xml = row_group_xml(
            2, sig_cls, "#8fd4ff", "0.42", fmask, xf, yf, 1.0, fbody, fchain, fwrapper
        )
        mask = (
            f'  <mask id="{fmask}" maskUnits="userSpaceOnUse" x="0" y="0" width="1200" height="800">\n'
            f'      <rect x="{xf - 22}" y="{yf - 24}" width="{span + 44:.0f}" height="60" fill="#ffffff"/>\n'
            + "\n".join(blobs)
            + "\n  </mask>"
        )
        return xml + "\n" + mask

    cut = rng.randint(len(flag) // 3, len(flag) // 2)
    taken = taken  # same id pool
    signal_parts = [
        fragment(flag[:cut], (100, 170), (288, 308), taken),
        fragment(flag[cut:], (330, 430), (336, 358), taken),
    ]
    signal = "\n".join(signal_parts)

    # ---- decoy glyph row (fully masked away) ------------------------------
    dstep, dscale = 11, 1.2
    dspan = (len(DECOY_ROW) - 1) * dstep * dscale
    dx0 = rng.randint(60, 1180 - int(dspan))
    dy0 = rng.randint(600, 640)
    dbody, dchain, dwrapper = build_glyph_row(rng, DECOY_ROW, ids, dstep, dscale)
    dmask_id = "mk" + rand_id(rng, taken)
    decoy = row_group_xml(
        2, decoy_cls, "#83d7ff", "0.9", dmask_id, dx0, dy0, 1.0, dbody, dchain, dwrapper,
        extra=[
            f'  <mask id="{dmask_id}" maskUnits="userSpaceOnUse" x="0" y="0" width="1200" height="800">',
            f'    <rect width="1200" height="800" fill="#04070d"/>',
            f'    <circle cx="{rng.randint(60, 1140)}" cy="{rng.randint(40, 520)}" r="1.1" fill="#ffffff"/>',
            f'  </mask>',
        ],
    )

    # ---- calibration plaque (inner SVG, base64) ----------------------------
    ids_in_order = [ids[ch] for ch in flag]
    plate = plaque_svg(ids_in_order)
    data_uri = "data:image/svg+xml;base64," + base64.b64encode(plate.encode()).decode()
    plaque = (
        "  <!-- calibration plate -->\n"
        "  <g>\n"
        '    <rect x="599" y="603" width="82" height="36" rx="2" fill="#0a121c" '
        'stroke="#2c4a5e" stroke-opacity="0.7"/>\n'
        f'    <image x="602" y="606" width="76" height="30" href="{data_uri}"/>\n'
        "  </g>"
    )

    # ---- labels / lore -----------------------------------------------------
    decoy_x, decoy_y = rng.randint(760, 980), rng.randint(470, 560)
    labels = (
        f'  <text x="58" y="756" font-family="monospace" font-size="11" letter-spacing="2" '
        f'fill="#7fc8ff" opacity="0.55">OBSERVER COMPATIBILITY: 2/5 · CALIBRATION: OK · GAIN NOMINAL</text>\n'
        f'  <text x="1176" y="470" font-family="monospace" font-size="9" fill="#7fc8ff" opacity="0.3" '
        f'transform="rotate(-90 1176 470)">archived note: every instrument agreed that nothing was there. '
        f'they only disagreed about what nothing looked like.</text>\n'
        f'  <text x="{decoy_x}" y="{decoy_y}" font-family="monospace" font-size="12" fill="#9fe8ff" '
        f'opacity="0.13" transform="rotate(-8 {decoy_x} {decoy_y})">{DECOY_TEXT_FLAG}</text>'
    )

    style = (
        "  <style>\n"
        f"    .{sig_cls} {{ opacity: var(--{gain_var}, 0.85); color: var(--{tone_var}, #9fe8ff); }}\n"
        f"    .{decoy_cls} {{ opacity: var(--{mute_var}, 0.12); }}\n"
        "  </style>"
    )
    root_vars = f"--{gain_var}:0.42;--{tone_var}:#8fd4ff;--{mute_var}:0.12"

    out = template
    out = out.replace("<!--@DEFS@-->", defs_out)
    out = out.replace("<!--@STYLE@-->", style)
    out = out.replace('viewBox="0 0 1200 800">', f'viewBox="0 0 1200 800" style="{root_vars}">', 1)
    out = out.replace("<!--@SIGNAL@-->", signal)
    out = out.replace("<!--@PLAQUE@-->", plaque)
    out = out.replace("<!--@LABELS@-->", labels)
    out = out.replace("<!--@DECOY@-->", decoy)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--flag", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    svg = generate(args.seed, args.flag)
    Path(args.out).write_text(svg)
    print(f"wrote {args.out} ({len(svg)} bytes)")


if __name__ == "__main__":
    main()
