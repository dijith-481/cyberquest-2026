#!/usr/bin/env python3
"""onion_pattern — deterministic handout generator.

Builds handout/onion.txt: one hex blob that encodes a chain of JSON
envelopes. Every envelope declares the op its `data` field was encoded
with and a deadpan hint. The two XOR layers are keyed; the key is only
findable by actually reading the previous layer's hint.

    python3 deployment/make_onion.py
"""

import base64
import codecs
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
HANDOUT = os.path.join(HERE, "..", "handout")

FLAG = "cyber_quest{p33l_p4t13ntly_4ll_th3_w4y_d0wn_5e2b19}"

HINT_XOR_INNER = (
    "Final seal. The pipeline XORs the core with the key 0n10n. "
    "Kevin proposed an actual cipher again and was told the pipeline "
    "is not a democracy. Data is hex."
)
HINT_B64_OUTER = (
    "Transport wrapper: Base64. The pipeline reuses wrappers; that is "
    "what makes it a pipeline and not, say, a system."
)
HINT_A85 = (
    "This hop is Ascii85, the plain flavor — no adobe brackets, no "
    "adjectives. Corporate standard OSC-115 was ratified in a meeting "
    "nobody attended."
)
HINT_REVERSE = (
    "Archive wrote this layer back-to-front to save tape. Compliance "
    "reviewed the practice and approved it in both directions."
)
HINT_B32 = (
    "Base32 this hop. A-Z and 2-7 only; the pipeline does not trust "
    "the rest of the alphabet and, honestly, the alphabet has given "
    "it reasons to."
)
HINT_XOR_MID = (
    "Sealed hop. XOR the hex-decoded bytes with the key p34r1. Kevin "
    "picked it; it is 'pearl' with fewer vetoes than his last key."
)
HINT_ROT13 = (
    "The rotation hop. Caesar shift of 13, letters only. The pipeline "
    "classifies this as encryption and legal has stopped returning "
    "emails about it."
)
HINT_B64_INNER = (
    "Base64 again. Decode it. Every onion has layers and every layer "
    "here has a decoder ring; the rings are all in the same drawer."
)

CORE_NOTE = (
    "You are reading the core of an asset-transfer-pipeline export. "
    "Nine hops from the outside, counting the file format itself. "
    "The pipeline was designed by committee and sealed by Kevin. "
    "Below is the payload the exec floor keeps referring to as "
    "'the pattern'."
)


def xor_bytes(data: bytes, key: str) -> bytes:
    k = key.encode()
    return bytes(b ^ k[i % len(k)] for i, b in enumerate(data))


def rot13(s: str) -> str:
    return codecs.encode(s, "rot13")


def envelope(layer: int, total: int, op: str, hint: str, data: str) -> str:
    return json.dumps(
        {"onion": "asset-transfer-pipeline", "layer": layer, "of": total,
         "op": op, "hint": hint, "data": data},
        indent=2,
    )


def main() -> None:
    os.makedirs(HANDOUT, exist_ok=True)

    core = json.dumps({"pattern": FLAG, "note": CORE_NOTE}, indent=2)

    # innermost -> outermost; layer k's `data` is envelope k-1 encoded
    l1 = envelope(1, 8, "xor-hex", HINT_XOR_INNER,
                  xor_bytes(core.encode(), "0n10n").hex())
    l2 = envelope(2, 8, "base64", HINT_B64_INNER,
                  base64.b64encode(l1.encode()).decode())
    l3 = envelope(3, 8, "rot13", HINT_ROT13, rot13(l2))
    l4 = envelope(4, 8, "xor-hex", HINT_XOR_MID,
                  xor_bytes(l3.encode(), "p34r1").hex())
    l5 = envelope(5, 8, "base32", HINT_B32,
                  base64.b32encode(l4.encode()).decode())
    l6 = envelope(6, 8, "mirror", HINT_REVERSE, l5[::-1])
    l7 = envelope(7, 8, "ascii85", HINT_A85,
                  base64.a85encode(l6.encode()).decode())
    l8 = envelope(8, 8, "base64", HINT_B64_OUTER,
                  base64.b64encode(l7.encode()).decode())

    blob = l8.encode().hex()
    with open(os.path.join(HANDOUT, "onion.txt"), "w") as f:
        # wrapped at 120 columns, because even onions have a style guide
        for i in range(0, len(blob), 120):
            f.write(blob[i:i + 120] + "\n")

    print("onion.txt written:", len(blob), "hex chars,", 9, "hops deep")


if __name__ == "__main__":
    main()
