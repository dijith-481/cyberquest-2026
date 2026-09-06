#!/usr/bin/env python3
"""Emojinated — reference solve (uses only player-visible files).

Intended attack path:
  1. note.txt hands over SPACE and the first line verbatim:
     "import tkinter as tk". That seeds the substitution map.
  2. Drag cribs across every line. A placement is accepted only if it
     is the UNIQUE consistent placement on that line AND anchored by
     at least two already-known emojis; repeat to a fixpoint. Cribs
     are generic Python/tkinter tokens plus standard tkinter call
     shapes (documented in solution.md as the intended guesses).
  3. The FLAG line matches the public flag wrapper
     FLAG = "cyber_quest{...}" with a [a-z0-9_]+ body.
  4. Any leftover emojis are resolved by backtracking over small
     context-derived candidate pools, keeping the single assignment
     under which the whole file parses as Python and yields a flag.

Usage:
    python3 solve.py [HANDOUT_DIR]    # default: ../handout
"""

import ast
import itertools
import os
import re
import sys

HANDOUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "handout")

# Generic tokens any player would try against a tkinter script.
TOKEN_CRIBS = [
    "tkinter", "tk", "Tk", "import", "as", "root", "canvas", "Canvas",
    "FLAG", "text", "fill", "font", "width", "height", "pack", "both",
    "expand", "True", "title", "geometry", "configure", "create_text",
    "mainloop", "CyberQuest", "Courier", "bold", "highlightthickness",
    "wallboard", "lobby", "display", "do", "not", "touch", "rev",
    "bg",
]

# Standard tkinter call shapes / boilerplate phrases. Values such as
# "both", "True", "Courier" or ("Courier", 34, "bold") are the defaults
# any tkinter user would guess; the solver only accepts placements that
# are unique on their line and anchored by known mappings.
PHRASE_CRIBS = [
    "tk.Tk()",
    "root.title(",
    "root.geometry(",
    "root.configure(",
    "tk.Canvas(",
    "canvas.pack(",
    "canvas.create_text(",
    "root.mainloop()",
    "text=FLAG",
    'fill="',
    '"CyberQuest"',
    '"both"',
    '"bold"',
    '"Courier"',
    "expand=True",
    "highlightthickness=0",
    "width=900",
    "height=260",
    "rev 1957",
    '", 34, "',
    'bg="#',
]

FLAG_RE = re.compile(r"cyber_quest\{[a-z0-9_]+\}")
MISSING = "\u2753"


class Inconsistent(Exception):
    pass


class Map:
    """Partial bijection emoji <-> char with consistency checking."""

    def __init__(self):
        self.e2c = {}
        self.c2e = {}

    def copy(self):
        m = Map()
        m.e2c = dict(self.e2c)
        m.c2e = dict(self.c2e)
        return m

    def add(self, emoji, char):
        if emoji in self.e2c and self.e2c[emoji] != char:
            raise Inconsistent(f"{emoji}: {self.e2c[emoji]} vs {char}")
        if char in self.c2e and self.c2e[char] != emoji:
            raise Inconsistent(f"{char}: {self.c2e[char]} vs {emoji}")
        self.e2c[emoji] = char
        self.c2e[char] = emoji

    def try_place(self, emojis, plain, at):
        """Align plain at position at; return new Map or None."""
        m = self.copy()
        try:
            for e, c in zip(emojis[at:at + len(plain)], plain):
                m.add(e, c)
        except Inconsistent:
            return None
        return m


def drag(lines, mapping, cribs):
    """Accept only unique, anchored (>=2 known) placements; fixpoint."""
    changed = True
    while changed:
        changed = False
        for emojis in lines:
            for crib in cribs:
                if len(crib) > len(emojis):
                    continue
                fits = []
                for at in range(len(emojis) - len(crib) + 1):
                    anchors = sum(1 for e in emojis[at:at + len(crib)]
                                  if e in mapping.e2c)
                    if anchors < 2:
                        continue
                    m = mapping.try_place(emojis, crib, at)
                    if m is not None and len(m.e2c) > len(mapping.e2c):
                        fits.append(m)
                if len(fits) == 1:
                    mapping = fits[0]
                    changed = True
    return mapping


def decode(lines, mapping):
    return ["".join(mapping.e2c.get(e, MISSING) for e in emojis)
            for emojis in lines]


def main() -> int:
    enc = open(os.path.join(HANDOUT, "wallboard.emoji"), encoding="utf-8").read()
    note = open(os.path.join(HANDOUT, "note.txt"), encoding="utf-8").read()

    # --[1] cribs straight from the handout note ---------------------------
    m = re.search(r"^\s{4}(\S+)\s*$", note, re.M)
    space_emoji = m.group(1)
    first_line = "import tkinter as tk"

    lines = [list(ln) for ln in enc.split("\n")]
    mapping = Map()
    for e, c in zip(lines[0], first_line):
        mapping.add(e, c)
    assert mapping.e2c[space_emoji] == " ", "note crib disagrees with line 1"
    print(f"[1] line-1 + space cribs -> {len(mapping.e2c)} mappings")

    # --[2] crib dragging to fixpoint --------------------------------------
    mapping = drag(lines, mapping, TOKEN_CRIBS + PHRASE_CRIBS)
    print(f"[2] crib drag -> {len(mapping.e2c)} mappings")

    # --[3] FLAG line via the public wrapper -------------------------------
    prefix, suffix = 'FLAG = "cyber_quest{', '}"'
    flag_li = None
    for li, emojis in enumerate(lines):
        m2 = mapping.try_place(emojis, prefix, 0)
        if m2 is None:
            continue
        tail = emojis[len(prefix):]
        if len(tail) < len(suffix) + 1:
            continue
        m3 = m2.try_place(tail, suffix, len(tail) - len(suffix))
        if m3 is None:
            continue
        body = tail[:len(tail) - len(suffix)]
        if any(e in m3.e2c and not re.fullmatch(r"[a-z0-9_]", m3.e2c[e])
               for e in body):
            continue
        if flag_li is None:
            flag_li, mapping = li, m3
    assert flag_li is not None, "FLAG line not found"
    print(f"[3] FLAG line is line {flag_li + 1}")

    mapping = drag(lines, mapping, TOKEN_CRIBS + PHRASE_CRIBS)
    print(f"[3b] crib drag again -> {len(mapping.e2c)} mappings")

    # --[4] resolve leftovers by constrained backtracking ------------------
    partial = decode(lines, mapping)
    unknowns = sorted({e for emojis in lines for e in emojis
                       if e not in mapping.e2c})
    print(f"[4a] residual unmapped emojis: {len(unknowns)}")

    def pool_for(emoji):
        ctx = set()
        for dl, emojis in zip(partial, lines):
            for i, e in enumerate(emojis):
                if e == emoji:
                    ctx.add(dl[max(0, i - 1):i + 2].replace(MISSING, "?"))
        txt = " ".join(ctx)
        if re.search(r"[0-9?][?0-9a-f]*[?0-9]", txt) or "?" in txt:
            pass
        # inside the flag body -> flag charset
        if any(e == emoji for emojis in [lines[flag_li]] for e in emojis):
            pass
        cands = []
        # order pools: digits first for numeric contexts, else broad
        numeric = all(re.fullmatch(r"[0-9?#, \"()=xX?]+", c or "?")
                      for c in ctx) and any(
                      re.search(r"[0-9]", c) for c in ctx)
        if numeric:
            cands += [str(d) for d in range(10)]
        cands += list("0123456789abcdef#x,()=\" ")
        return [c for c in cands if c not in mapping.c2e]

    if unknowns:
        pools = [pool_for(e) for e in unknowns]
        print(f"[4b] pool sizes: {[len(p) for p in pools]}")
        assert all(pools) and sum(len(p) for p in pools) < 200, \
            "residual search space too big"
        solutions = []
        for combo in itertools.product(*pools):
            if len(set(combo)) != len(combo):
                continue
            m2 = mapping.copy()
            try:
                for e, c in zip(unknowns, combo):
                    m2.add(e, c)
                src = "\n".join(decode(lines, m2))
                if MISSING in src:
                    continue
                ast.parse(src)
                if FLAG_RE.search(src):
                    solutions.append(m2)
            except (Inconsistent, SyntaxError):
                continue
        assert len(solutions) == 1, f"{len(solutions)} full solutions"
        mapping = solutions[0]
    print(f"[4c] full mapping -> {len(mapping.e2c)} mappings")

    # --[5] decode, verify it is real python, print flag -------------------
    src = "\n".join(decode(lines, mapping))
    assert MISSING not in src
    ast.parse(src)
    print("[5] decoded source parses as Python")
    print("---- decoded wallboard.py ----")
    print(src)
    print("------------------------------")
    print("FLAG:", FLAG_RE.search(src).group(0))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
