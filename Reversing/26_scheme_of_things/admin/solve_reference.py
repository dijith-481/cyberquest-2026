#!/usr/bin/env python3
# Organizer reference solve. Reconstructs the passphrase from the generated
# constraints (deployment/organizer/metadata.json). Not distributed to players.

import json
import sys


def ror8(v, r):
    r &= 7
    return ((v >> r) | ((v << (8-r)) & 0xff)) & 0xff if r else v & 0xff


meta = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "metadata.json"))
rows = meta["per_char"]
out = []
for row in sorted(rows, key=lambda x: x["index"]):
    y = (row["target"] - row["bias"]) & 0xff
    y ^= row["mask"]
    out.append(ror8(y, row["shift"]))
print(bytes(out).decode("utf-8"))
