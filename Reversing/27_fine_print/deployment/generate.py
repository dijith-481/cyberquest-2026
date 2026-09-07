#!/usr/bin/env python3
"""Fine Print (slot 27, Reversing, H0) — deterministic handout generator.

Regenerates everything in ../handout/ from a seed:

    python3 deployment/generate.py [--seed oe-fine-print-27]

Nothing here is secret; the solve path is documented in admin/solution.md.
The flag is fixed below. Fragments are derived deterministically from the
seed: N-1 random printable fragments, the last one solved so the byte-wise
XOR of all four lands exactly on the flag. Every fragment byte stays in a
C-string-literal-safe printable alphabet (no `"` or backslash, no spaces)
so each fragment survives `strings` as one clean token, all at exactly
FLAG length — which is also the tell that distinguishes them from decoys.

Requires gcc on PATH (or --no-build to only emit organizer source).
"""

import argparse
import os
import random
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
HANDOUT = os.path.join(HERE, "..", "handout")
ORGANIZER = os.path.join(HERE, "organizer")

FLAG = "cyber_quest{x0r_a11_th3_str1ngs_2gether_3f8a1d}"
NFRAG = 4
DEFAULT_SEED = "oe-fine-print-27"

# Printable, C-literal-safe, spaceless: 0x21..0x7e minus '"' (0x22) and
# backslash (0x5c). No spaces so `strings` never splits a fragment.
ALPHABET = bytes(b for b in range(0x21, 0x7F) if b not in (0x22, 0x5C))


def derive_fragments(flag: bytes, rng: random.Random, n: int = NFRAG):
    """N-1 random fragments; the last is solved so XOR(all) == flag.

    Sampled per byte position: draw N-1 alphabet bytes, the last byte is
    then determined, and the position is retried until it also lands in
    the alphabet (~36% per try, ~3 tries per position). Whole-fragment
    rejection would never converge (0.36**len(flag)).
    """
    L = len(flag)
    cols = []
    for i in range(L):
        for _ in range(10000):
            parts = [rng.choice(ALPHABET) for _ in range(n - 1)]
            x = flag[i]
            for p in parts:
                x ^= p
            if x in ALPHABET:
                cols.append(bytes(parts + [x]))
                break
        else:
            raise SystemExit(f"could not derive byte {i} for this flag")
    frags = [b"".join(col[j:j + 1] for col in cols) for j in range(n)]
    return [f.decode() for f in frags]


C_TEMPLATE = r'''#include <stdio.h>
#include <string.h>

/* Ordinary Engineering Inc. -- LicenseGuard v2.1
 * Internal build. Do not distribute keys.
 */

const char *decoy1  = "Usage: %s <license-key>\n";
const char *decoy2  = "Error: invalid license key length.\n";
const char *decoy3  = "Access denied. Contact sales@ordinary-eng.example\n";
const char *decoy4  = "Copyright (c) 2024 Ordinary Engineering Inc.\n";
const char *decoy5  = "Try again later.\n";
const char *decoy6  = "/etc/oe/license.d/master.lic";
const char *decoy7  = "GCC: (Ubuntu 11.4.0-1ubuntu1~22.04) 11.4.0";
const char *decoy8  = "DEBUG: build 20240311-rc7";
const char *decoy9  = "libc.so.6";
const char *decoy10 = "malloc failed, aborting\n";
const char *decoy11 = "Segmentation fault (core dumped)";
const char *decoy12 = "Thank you for using LicenseGuard.\n";

/* license key fragments -- fetched from license.d at startup, do NOT log these */
const char *frag1 = "{f1}";
const char *frag2 = "{f2}";
const char *frag3 = "{f3}";
const char *frag4 = "{f4}";

static int check_fake_license(const char *input) {{
    /* Deliberately unrelated dummy check so the real key material
     * is never combined or printed at runtime. */
    unsigned char acc = 0;
    for (size_t i = 0; frag1[i]; i++) acc ^= (unsigned char)frag1[i];
    for (size_t i = 0; input[i]; i++) acc ^= (unsigned char)input[i];
    return acc == 0x42; /* essentially never true for normal input */
}}

int main(int argc, char **argv) {{
    if (argc < 2) {{
        printf(decoy1, argv[0]);
        return 1;
    }}
    if (strlen(argv[1]) != {flen}) {{
        printf("%s", decoy2);
        return 1;
    }}
    if (check_fake_license(argv[1])) {{
        printf("%s", decoy12);
    }} else {{
        printf("%s", decoy3);
    }}
    return 0;
}}
'''

PLAYER_README = """oe-licenseguard // release build

Ordinary Engineering ships a license checker with every product line.
This build leaked on its way to the release branch. It runs, it
validates, it declines, and support insists the answer is in the
binary. Support is right, for once.

Run it locally. Read the fine print.
"""

MAKEFILE = """CC ?= gcc
CFLAGS ?= -O2 -Wall -Wextra
all: licenseguard
licenseguard: challenge.c
\t$(CC) $(CFLAGS) challenge.c -o licenseguard
strip:
\tstrip licenseguard
clean:
\trm -f licenseguard
"""


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate the Fine Print RE challenge")
    ap.add_argument("--seed", default=DEFAULT_SEED)
    ap.add_argument("--flag", default=FLAG)
    ap.add_argument("--no-build", action="store_true")
    args = ap.parse_args()

    flag = args.flag.encode()
    rng = random.Random(args.seed)
    frags = derive_fragments(flag, rng)
    assert len(set(len(f) for f in frags)) == 1
    assert all(all(c not in '"\\ ' for c in f) for f in frags)

    # Sanity: XOR(all fragments) must be the flag.
    chk = bytearray(len(flag))
    for f in frags:
        for i, b in enumerate(f.encode()):
            chk[i] ^= b
    assert bytes(chk) == flag, "fragment derivation mismatch"

    # The tell must be unique: no decoy may share the fragment length.
    decoys = [
        "Usage: %s <license-key>\n",
        "Error: invalid license key length.\n",
        "Access denied. Contact sales@ordinary-eng.example\n",
        "Copyright (c) 2024 Ordinary Engineering Inc.\n",
        "Try again later.\n",
        "/etc/oe/license.d/master.lic",
        "GCC: (Ubuntu 11.4.0-1ubuntu1~22.04) 11.4.0",
        "DEBUG: build 20240311-rc7",
        "libc.so.6",
        "malloc failed, aborting\n",
        "Segmentation fault (core dumped)",
        "Thank you for using LicenseGuard.\n",
    ]
    assert all(len(d) != len(flag) for d in decoys), "decoy collides with tell"

    src = C_TEMPLATE.format(
        f1=frags[0], f2=frags[1], f3=frags[2], f4=frags[3], flen=len(flag)
    )
    os.makedirs(ORGANIZER, exist_ok=True)
    with open(os.path.join(ORGANIZER, "challenge.c"), "w") as f:
        f.write(src)
    with open(os.path.join(ORGANIZER, "Makefile"), "w") as f:
        f.write(MAKEFILE)

    os.makedirs(HANDOUT, exist_ok=True)
    with open(os.path.join(HANDOUT, "README.txt"), "w") as f:
        f.write(PLAYER_README)

    if not args.no_build:
        out = os.path.join(HANDOUT, "licenseguard")
        subprocess.run(
            ["gcc", "-O2", "-Wall", "-Wextra",
             os.path.join(ORGANIZER, "challenge.c"), "-o", out],
            check=True,
        )
        if subprocess.run(["which", "strip"],
                           capture_output=True).returncode == 0:
            subprocess.run(["strip", out], check=True)
        os.chmod(out, 0o755)
        # Self-test: binary runs, never leaks the flag, fragments solve.
        p = subprocess.run([out, "A" * len(flag)],
                           capture_output=True, text=True, check=False)
        assert flag.decode() not in p.stdout, "binary leaks flag at runtime"
        r = subprocess.run(["strings", out],
                           capture_output=True, text=True, check=True)
        cands = [s for s in r.stdout.splitlines() if len(s) == len(flag)]
        assert len(cands) == NFRAG, f"expected {NFRAG} tells, got {len(cands)}"

    print(f"flag: {args.flag} (len {len(flag)})")
    print(f"fragments written to {os.path.normpath(ORGANIZER)}/challenge.c")
    if not args.no_build:
        print(f"binary written to {os.path.normpath(HANDOUT)}/licenseguard")


if __name__ == "__main__":
    sys.exit(main())
