#!/usr/bin/env python3
"""the_corridor_that_remembers — reference solve.

Walks the archive maze the way a player is meant to: inspect before
trusting, follow what things ARE rather than what they are named.

    python3 admin/solve.py handout/corridor.tar.gz
"""

import io
import os
import re
import subprocess
import sys
import tarfile
import tempfile


def open_tar(data_or_path):
    if isinstance(data_or_path, (bytes, bytearray)):
        return tarfile.open(fileobj=io.BytesIO(data_or_path))
    return tarfile.open(data_or_path)


def extract(obj, dest):
    try:
        obj.extractall(dest, filter="data")
    except TypeError:  # python < 3.12
        obj.extractall(dest)


def solve(path: str) -> str:
    with tempfile.TemporaryDirectory() as d:
        # ---- room 0: list the archive, don't blind-extract ----------------
        with open_tar(path) as t:
            members = t.getmembers()
        decoys = [m for m in members if m.isdir()]
        real = [m.name for m in members if m.isfile()]
        print(f"room 0: {len(decoys)} empty corridors, one real file: {real}")
        with open_tar(path) as t:
            extract(t, d)

        # ---- room 1: the label lies --------------------------------------
        extract(open_tar(os.path.join(d, "session_01.tar")), d)
        photo = os.path.join(d, "session_01", "photograph.jpg")
        print("room 1: photograph.jpg is really a tar:", tarfile.is_tarfile(photo))
        extract(open_tar(photo), d)

        # ---- room 2: familiar doors loop; .door is real -------------------
        room2 = os.path.join(d, "room_02")
        links = sorted(n for n in os.listdir(room2)
                       if os.path.islink(os.path.join(room2, n)))
        print("room 2: doors:", {n: os.readlink(os.path.join(room2, n)) for n in links})
        room3 = os.path.join(room2, os.readlink(os.path.join(room2, ".door")), "room_03")

        # ---- room 3: garbage on the surface, clue in the bytes ------------
        blob = open(os.path.join(room3, "reflection.bin"), "rb").read()
        printable = blob.replace(b"\x00", b"")
        clue = re.search(rb"(\S+\.tar)", printable).group(1).decode()
        print(f"room 3: reflection.bin says: {clue!r}")

        # ---- room 4: the binary ------------------------------------------
        extract(open_tar(os.path.join(room3, clue)), d)
        room4 = os.path.join(d, "room_04")
        choose = os.path.join(room4, "choose")
        out = subprocess.run([choose, "--remember"], capture_output=True, text=True)
        hint = out.stdout.strip()
        print(f"room 4: ./choose --remember -> {hint!r}  (floor it is)")
        room5 = os.path.join(room4, ".floor")

        # ---- room 5: one heavy door among a hundred ----------------------
        with open_tar(os.path.join(room5, "session_05.tar.xz")) as t:
            extract(t, room5)
        with open_tar(os.path.join(room5, "choices.tar")) as t:
            heavy = [m.name for m in t.getmembers() if m.isfile() and m.size > 0]
        print(f"room 5: 100 doors, exactly one non-empty: {heavy}")
        extract(open_tar(os.path.join(room5, "choices.tar")), room5)
        heavy_name = heavy[0]
        with open_tar(os.path.join(room5, heavy_name)) as t:  # a door that is an archive
            extract(t, room5)

        # ---- final: the maze never changed -------------------------------
        memory = os.path.join(room5, "final_memory.tar.gz")
        extract(open_tar(memory), room5)
        flag = open(os.path.join(room5, "final", "flag.txt")).read().strip()
        print(f"final: flag.txt -> {flag}")
        return flag


if __name__ == "__main__":
    print()
    print(solve(sys.argv[1] if len(sys.argv) > 1 else
                os.path.join(os.path.dirname(__file__), "..", "handout", "corridor.tar.gz")))
