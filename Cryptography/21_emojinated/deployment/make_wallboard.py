#!/usr/bin/env python3
"""Emojinated (slot 21) — deterministic handout generator.

Takes the ordinary tkinter wallboard script, maps every character except
newline to an emoji (one-to-one substitution, seeded), and writes the
player handout. Newlines are preserved so the file still looks like
source code; the SPACE mapping is revealed in note.txt as the intended
crib. The organizer-only key goes to admin/ and must never ship.

Outputs (relative to the challenge root):
  handout/wallboard.emoji
  handout/note.txt
  admin/emoji_key.json
"""

import hashlib
import json
import random
import sys
from pathlib import Path

CHALLENGE_DIR = Path(__file__).resolve().parent.parent
HANDOUT_DIR = CHALLENGE_DIR / "handout"
ADMIN_DIR = CHALLENGE_DIR / "admin"

SEED = 0xC0FFEE

FLAG_SUFFIX = hashlib.sha256(b"emojinated-wallboard-v1").hexdigest()[:8]
FLAG = f"cyber_quest{{3m0t1c0ns_w4llb04rd_{FLAG_SUFFIX}}}"

SOURCE_TEMPLATE = '''import tkinter as tk

FLAG = "{flag}"

# wallboard rev 1957, lobby display, do not touch
root = tk.Tk()
root.title("CyberQuest")
root.geometry("900x260")
root.configure(bg="#080c14")

canvas = tk.Canvas(
    root,
    width=900,
    height=260,
    bg="#080c14",
    highlightthickness=0
)
canvas.pack(fill="both", expand=True)

canvas.create_text(
    450,
    130,
    text=FLAG,
    fill="#39ff88",
    font=("Courier", 34, "bold")
)

root.mainloop()
'''


def build_source(flag: str = FLAG) -> str:
    return SOURCE_TEMPLATE.format(flag=flag)


EMOJIS = [
    "😀", "😃", "😄", "😁", "😆", "😅", "😂", "🙂",
    "🙃", "😉", "😊", "😎", "🤓", "🧐", "🤨", "😐",
    "😑", "😶", "🙄", "😏", "😣", "😥", "😮", "🤐",
    "😯", "😪", "😫", "🥱", "😴", "😌", "🤥", "😵",
    "🤯", "🤠", "🥳", "🥸", "😈", "👿", "👻", "💀",
    "☠", "👽", "🤖", "🎃", "😺", "😸", "😹", "😻",
    "😼", "😽", "🙀", "😿", "😾", "🙈", "🙉", "🙊",
    "🐵", "🐶", "🐺", "🦊", "🐱", "🦁", "🐯", "🐴",
    "🦄", "🐮", "🐷", "🐭", "🐹", "🐰", "🐻", "🐼",
    "🐨", "🐸", "🐙", "🦋", "🐛", "🐝", "🐞", "🦗",
    "🕷", "🦂", "🐢", "🐍", "🦎", "🦖", "🦕", "🐬",
    "🐳", "🐋", "🦈", "🐊", "🐅", "🐆", "🦓", "🦍",
    "🐘", "🦛", "🦏", "🐪", "🐫", "🦒", "🦘", "🐃",
    "🐂", "🐄", "🐎", "🐖", "🐏", "🐑", "🦙", "🐐",
    "🦌", "🐕", "🐩", "🐈", "🐓", "🦃", "🦚", "🦜",
    "🦢", "🦩", "🕊", "🐇", "🦝", "🦨", "🦡", "🦦",
    "🦥", "🐁", "🐀", "🐿", "🦔", "🐉", "🐲", "🌵",
    "🎄", "🌲", "🌳", "🌴", "🌱", "🌿", "☘", "🍀",
    "🎍", "🎋", "🍃", "🍂", "🍁", "🍄", "🐚", "🌾",
    "💐", "🌷", "🌹", "🥀", "🌺", "🌸", "🌼", "🌻",
    "🌞", "🌝", "🌚", "🌕", "🌖", "🌗", "🌘", "🌑",
    "🌒", "🌓", "🌔", "🌙", "🌎", "🌍", "🌏", "💫",
    "⭐", "🌟", "✨", "⚡", "🔥", "🌪", "🌈", "☀",
    "☁", "❄", "☃", "⛄", "💧", "💦", "☔", "🍏",
    "🍎", "🍐", "🍊", "🍋", "🍌", "🍉", "🍇", "🍓",
    "🫐", "🍈", "🍒", "🍑", "🥭", "🍍", "🥥", "🥝",
    "🍅", "🍆", "🥑", "🥦", "🥬", "🥒", "🌶", "🫑",
    "🌽", "🥕", "🫒", "🧄", "🧅", "🥔", "🍠", "🥐",
    "🥯", "🍞", "🥖", "🥨", "🧀", "🥚", "🍳", "🥞",
    "🧇", "🥓", "🍔", "🍟", "🍕", "🌭", "🥪", "🌮",
    "🌯", "🫔", "🥙", "🧆", "🍝", "🍜", "🍲", "🍛",
]

# Every mapping value must be a single code point so encode/decode
# is unambiguous by simple iteration.
EMOJIS = [e for e in EMOJIS if len(e) == 1]

NOTE_TEMPLATE = """FACILITIES — LOBBY WALLBOARD INCIDENT

The universe 7-B locale exporter converted wallboard.py to wallboard.emoji.
Every character is now an emoji. Line breaks survived. Nothing else did.

What we know:
- the file was a normal Python script that draws the status line
  on the lobby display
- its first line was:

    import tkinter as tk

- the sticky note on the monitor says the SPACE character became:

    {space_emoji}

The wallboard team would like their script back.
"""


def build_mapping(source: str) -> dict:
    chars = sorted(set(source) - {"\n"})
    if len(chars) > len(EMOJIS):
        raise RuntimeError(f"Need {len(chars)} emojis, only have {len(EMOJIS)}")
    rng = random.Random(SEED)
    available = EMOJIS.copy()
    rng.shuffle(available)
    return {c: e for c, e in zip(chars, available)}


def main() -> int:
    source = build_source()

    # Solvability invariant: every flag-body character must already occur
    # outside the flag string (or in the public cyber_quest{...} wrapper),
    # so the full mapping is recoverable from cribs + code structure.
    body = FLAG[len("cyber_quest{"):-len("}")]
    stripped = SOURCE_TEMPLATE.format(flag="")
    assert set(body) <= set(stripped) | set("cyber_quest{}"), (
        "flag body uses chars unrecoverable outside the flag: "
        + sorted(set(body) - set(stripped) - set("cyber_quest{}"))
    )

    mapping = build_mapping(source)
    encoded = "".join(mapping.get(c, c) for c in source)

    HANDOUT_DIR.mkdir(parents=True, exist_ok=True)
    ADMIN_DIR.mkdir(parents=True, exist_ok=True)

    (HANDOUT_DIR / "wallboard.emoji").write_text(encoded, encoding="utf-8")
    (HANDOUT_DIR / "note.txt").write_text(
        NOTE_TEMPLATE.format(space_emoji=mapping[" "]), encoding="utf-8"
    )
    (ADMIN_DIR / "emoji_key.json").write_text(
        json.dumps({repr(c): e for c, e in mapping.items()},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"[+] Source characters: {len(source)}")
    print(f"[+] Unique symbols (excl. newline): {len(mapping)}")
    print(f"[+] Flag: {FLAG}")
    print(f"[+] Written: handout/wallboard.emoji, handout/note.txt")
    print(f"[+] Organizer key: admin/emoji_key.json (do not ship)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
