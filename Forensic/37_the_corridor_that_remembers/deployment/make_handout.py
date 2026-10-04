#!/usr/bin/env python3
"""the_corridor_that_remembers — deterministic handout generator.

Builds handout/corridor.tar.gz: a nested archive "maze" about familiarity
bias. Every stage looks like one thing (a photograph, a door, a text file)
and is actually another thing (an archive, a loop, a clue in the bytes).

The whole maze is fiction inside the extraction directory: every symlink is
relative and resolves within wherever the player extracts. No absolute
paths, no "../" traversal out of the maze.

Design rule baked into the layout:

    trust filename          -> wrong      (photograph.jpg is a tar)
    trust visible doors     -> loop       (all of them point backward)
    trust plain display     -> garbage    (reflection.bin is padded bytes)
    inspect bytes           -> progress   (xxd / strings)
    trust the obvious pick  -> 100 doors  (exactly one is non-empty)
    inspect metadata        -> progress   (tar -tvf finds it)

Requires gcc to compile the Room 4 binary.

Nothing here is secret; the solve path is documented in admin/solution.md.
"""

import io
import os
import subprocess
import tarfile
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
HANDOUT = os.path.join(HERE, "..", "handout")
ASSETS = os.path.join(HERE, "assets")

FLAG = "cyber_quest{f4m1l14r1ty_1s_n0t_c0rr3ctn355}"

# fixed timestamp so the handout is reproducible
MTIME = 1757000000


# --------------------------------------------------------------------------
# tiny declarative tar builder
# --------------------------------------------------------------------------

class TarBuilder:
    """Builds a tar (optionally compressed) from a declarative entry list.

    Entry forms:
        ("dir", name)
        ("file", name, data[, mode])
        ("sym", name, target)
        ("tar", name, subentries)              # plain tar, stored as a file
        ("tgz", name, subentries)              # gzip
        ("txz", name, subentries)              # xz
    """

    def __init__(self, entries, mode=""):
        self.entries = entries
        self.mode = mode

    def _info(self, name, typ=tarfile.REGTYPE, linkname="", size=0, m=0o644):
        ti = tarfile.TarInfo(name)
        ti.type = typ
        ti.linkname = linkname
        ti.size = size
        ti.mtime = MTIME
        ti.mode = m
        ti.uid = ti.gid = 0
        ti.uname = ti.gname = "root"
        return ti

    def build(self) -> bytes:
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w") as tar:
            self._add(tar, self.entries)
        data = buf.getvalue()
        if self.mode == "gz":
            data = _regzip(data)
        elif self.mode == "xz":
            import lzma
            data = lzma.compress(data)
        return data

    def _add(self, tar, entries):
        for entry in entries:
            kind = entry[0]
            if kind == "dir":
                ti = self._info(entry[1].rstrip("/") + "/", tarfile.DIRTYPE, m=0o755)
                tar.addfile(ti)
            elif kind == "file":
                name, data = entry[1], entry[2]
                if isinstance(data, str):
                    data = data.encode()
                m = entry[3] if len(entry) > 3 else 0o644
                ti = self._info(name, size=len(data), m=m)
                tar.addfile(ti, io.BytesIO(data))
            elif kind == "sym":
                ti = self._info(entry[1], tarfile.SYMTYPE, linkname=entry[2], m=0o777)
                tar.addfile(ti)
            elif kind in ("tar", "tgz", "txz"):
                data = TarBuilder(entry[2], mode=kind[1:] if kind != "tar" else "").build()
                ti = self._info(entry[1], size=len(data))
                tar.addfile(ti, io.BytesIO(data))
            else:
                raise ValueError(f"unknown entry kind: {kind!r}")


def _regzip(data: bytes) -> bytes:
    import gzip
    return gzip.compress(data, mtime=MTIME)


def compile_choose() -> bytes:
    """Compile + strip the Room 4 ELF so `strings` on it is the intended solve."""
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "choose")
        subprocess.run(
            ["gcc", os.path.join(ASSETS, "choice.c"), "-O1", "-o", out],
            check=True,
        )
        subprocess.run(["strip", out], check=True)
        with open(out, "rb") as f:
            return f.read()


# --------------------------------------------------------------------------
# the maze, bottom-up
# --------------------------------------------------------------------------

def final_room() -> list:
    """The flag room. old_room / begin_again loop back to where you already are."""
    return [
        ("dir", "final"),
        ("file", "final/note.txt",
         "The maze never changed.\n\n"
         "I did.\n\n"
         "I kept mistaking familiarity for correctness.\n"
         "The way out was never a direction. It was attention.\n"),
        ("file", "final/flag.txt", FLAG + "\n"),
        ("sym", "final/old_room", ".."),
        ("sym", "final/begin_again", ".."),
    ]


def room_5_doors(choose_bin: bytes) -> list:
    """One hundred identical doors; exactly one is non-empty."""
    heavy = TarBuilder([
        ("file", "whisper.txt",
         "A hundred choices felt harder than one observation.\n\n"
         "Every door weighed the same. I stood there choosing.\n"
         "The listing knew which one was heavy. I just never read it.\n\n"
         "Take the last memory with you.\n"),
        ("tgz", "final_memory.tar.gz", final_room()),
    ]).build()

    doors = []
    for i in range(1, 101):
        name = f"door_{i:03d}"
        doors.append(("file", name, heavy if i == 73 else b""))
    return doors


def room_4(choose_bin: bytes) -> list:
    """The binary. north/ and south/ are empty; the floor is not."""
    return [
        ("dir", "room_04"),
        ("file", "room_04/README",
         "Two doors again.\n\n"
         "north felt right.\n"
         "south also felt right.\n"
         "They always did.\n\n"
         "The hallway remembers, even when I don't.\n"),
        ("file", "room_04/choose", choose_bin, 0o755),
        ("dir", "room_04/north"),
        ("dir", "room_04/south"),
        ("dir", "room_04/.floor"),
        ("txz", "room_04/.floor/session_05.tar.xz", [
            ("tar", "choices.tar", room_5_doors(choose_bin)),
        ]),
    ]


def room_3(choose_bin: bytes) -> list:
    """Garbage on the surface; the clue sits in the ASCII column."""
    reflection = (
        b"\x00" * 16
        + b"I don't trust the first thing I see.\n"
        + b".hidden/door.tar\n"
        + b"\x00" * 16
    )
    return [
        ("dir", "room_02/memory/room_03"),
        ("file", "room_02/memory/room_03/reflection.bin", reflection),
        ("dir", "room_02/memory/room_03/.hidden"),
        ("tar", "room_02/memory/room_03/.hidden/door.tar", room_4(choose_bin)),
    ]


def room_2(choose_bin: bytes) -> list:
    """Every visible door points backward; .door is the only way forward."""
    entries = [("dir", "room_02")]
    for door in ("left", "right", "home", "again", "exit"):
        entries.append(("sym", f"room_02/{door}", "../session_01"))
    entries.append(("sym", "room_02/.door", "memory"))
    entries.append(("dir", "room_02/memory"))
    entries.extend(room_3(choose_bin))
    return entries


def room_1(choose_bin: bytes) -> list:
    """The label lies: photograph.jpg is a tar archive holding room_02."""
    photograph = TarBuilder(room_2(choose_bin)).build()
    return [
        ("dir", "session_01"),
        ("file", "session_01/diary.txt",
         "Day 41.\n\n"
         "I labelled things based on what I remembered them being.\n"
         "If a file looked like a photograph, it was a photograph.\n"
         "If a corridor looked familiar, it was the way out.\n\n"
         "That was the rule. It worked until it didn't.\n\n"
         "Session 02 is filed in the usual place.\n"
         "It is not where I remember putting it. It is what it says it is.\n"),
        ("dir", "session_01/exit"),
        ("file", "session_01/exit/way_out.txt", "it isn't.\n"),
        ("tar", "session_01/photograph.jpg", room_2(choose_bin)),
    ]


def room_0(choose_bin: bytes) -> list:
    """Twenty corridors, one real archive, the rest is wallpaper."""
    decoys = [
        "familiar", "familiar_again", "north", "south", "again", "home",
        "left", "right", "memory", "exit", "hallway", "upstairs",
        "downstairs", "corridor", "room_01", "room_02", "room_03",
        "doors", "archive", "sessions",
    ]
    entries = [
        ("file", "START.txt",
         "> I kept opening doors before looking at them.\n\n"
         "Twenty corridors. One real archive. The rest is wallpaper.\n\n"
         "Sessions are in session_01.tar. Probably. Look before you walk.\n"),
    ]
    entries.extend(("dir", d) for d in decoys)
    entries.append(("tar", "session_01.tar", room_1(choose_bin)))
    return entries


def main() -> None:
    os.makedirs(HANDOUT, exist_ok=True)
    out = os.path.join(HANDOUT, "corridor.tar.gz")

    choose_bin = compile_choose()
    data = TarBuilder(room_0(choose_bin), mode="gz").build()
    with open(out, "wb") as f:
        f.write(data)
    print("wrote", os.path.normpath(out), f"({len(data)} bytes)")


if __name__ == "__main__":
    main()
