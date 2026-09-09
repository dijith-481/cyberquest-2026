#!/usr/bin/env python3
"""Uglified (slot 30, Reversing, H0) — deterministic handout generator.

Regenerates everything in ../handout/ from a seed:

    python3 deployment/generate.py [--seed oe-uglified-30] [--flag ...]

Mechanic: a warranty-claim validator shipped as a minified, obfuscated
Node bundle. `node bundle.js <receipt-key>` accepts exactly one input —
the flag. The check XORs the candidate body against a key schedule plus a
position mask and compares it to an embedded target; strings live in a
rotated base64 table, identifiers are hex noise, dead code and a retired
receipt string round out the camouflage.

Nothing here is secret; the solve path is in admin/solution.md.
Requires node on PATH (the generator self-tests the bundle).
"""

import argparse
import base64
import os
import random
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
HANDOUT = os.path.join(HERE, "..", "handout")
ORGANIZER = os.path.join(HERE, "organizer")

FLAG = "cyber_quest{m1n1f13d_n0t_h1dd3n_5d7e1a}"
DEFAULT_SEED = "oe-uglified-30"
FAKE_FLAG = "cyber_quest{fr33_w4rr4nty_cl41m_4ppr0v3d}"

PREFIX = "cyber_quest{"
KEY_LEN = 16
MASK_A = 0x1F
MASK_B = 0x03


def b64(data: bytes) -> str:
    return base64.b64encode(data).decode()


def hexname(rng: random.Random, taken: set) -> str:
    while True:
        name = "_0x%04x" % rng.randint(0, 0xFFFF)
        if name not in taken:
            taken.add(name)
            return name


def target_for(body: bytes, key: bytes) -> bytes:
    return bytes(
        b ^ key[i % len(key)] ^ ((i * MASK_A + MASK_B) & 0xFF)
        for i, b in enumerate(body)
    )


def build_bundle(flag: str, rng: random.Random) -> str:
    assert flag.startswith(PREFIX) and flag.endswith("}")
    body = flag[len(PREFIX):-1].encode()
    assert body.isascii() and len(body) >= 8
    key = bytes(rng.randint(0, 255) for _ in range(KEY_LEN))
    tgt = target_for(body, key)

    # Named string-table slots; shuffled + rotated below.
    slots = {
        "TGT": b64(tgt),
        "KEY": b64(key),
        "PFX": b64(PREFIX.encode()),
        "USE": b64(b"usage: node bundle.js <receipt-key>"),
        "OK": b64(b"warranty honored. receipt:"),
        "NO": b64(b"claim denied."),
        "D1": b64(b"claim queued for review"),
        "D2": b64(b"oe-warranty 1.3.0 (build 4417) - all claims subject "
                  b"to review by the multiverse standards board. "
                  b"allow 6-8 business days."),
        "VER": b64(b"1.3.0"),
    }
    order = list(slots)
    rng.shuffle(order)
    entries = [slots[k] for k in order]
    pos = {k: i for i, k in enumerate(order)}
    n = len(entries)
    count = rng.randint(1, 3 * n)
    # Emitted in shuffled order; the runtime IIFE rotates it once by count.
    # Final runtime position of the slot shuffled to p: (p - count) mod n.
    idx = {k: "0x%x" % ((p - count) % n) for k, p in pos.items()}

    taken = set()
    ARR = hexname(rng, taken)
    DEC = hexname(rng, taken)
    CHK = hexname(rng, taken)
    DEAD = hexname(rng, taken)
    P, Q, I, J, S, K, B, T, N, G, H, M, IN = (
        hexname(rng, taken) for _ in range(13)
    )
    full_len = "0x%x" % len(flag)

    lines = []
    lines.append("// oe-warranty 1.3.0 -- production bundle (minified). do not edit.")
    lines.append("var %s=[%s];" % (ARR, ",".join("'%s'" % e for e in entries)))
    lines.append("(function(%s,%s){for(var %s=0;%s<%s;%s++){%s.push(%s.shift());}})(%s,0x%x);"
                 % (P, Q, I, I, Q, I, P, P, ARR, count))
    lines.append("function %s(%s){return Buffer.from(%s[%s],'base64').toString('utf8');}"
                 % (DEC, J, ARR, J))
    lines.append("function %s(%s){var %s='%s';var %s=%s(%s);var %s=0;"
                 "for(var %s=0;%s<%s.length;%s++){%s=(%s*%s+%s.charCodeAt(%s))&0xffff;}"
                 "return %s===0xbeef&&%s===%s;}"
                 % (DEAD, S, M, FAKE_FLAG, H, DEC, idx["D2"], H,
                    I, I, S, I, H, H, I, S, I, H, S, M))
    lines.append("function %s(%s){if(typeof %s!=='string'){return false;}"
                 "if(%s.length!==%s){return false;}"
                 "if(%s.slice(0,0x0c)!==%s(%s)){return false;}"
                 "if(%s.slice(-1)!=='}'){return false;}"
                 "var %s=%s.slice(0x0c,-1);"
                 "var %s=Buffer.from(%s[%s],'base64');"
                 "var %s=Buffer.from(%s[%s],'base64');"
                 "if(%s.length!==%s.length){return false;}"
                 "for(var %s=0;%s<%s.length;%s++){"
                 "var %s=%s.charCodeAt(%s)^%s[%s%%%s.length]^((%s*0x%x+0x%02x)&0xff);"
                 "if(%s!==%s[%s]){return false;}}return true;}"
                 % (CHK, K, K, K, full_len, K, DEC, idx["PFX"], K,
                    B, K, T, ARR, idx["TGT"], N, ARR, idx["KEY"],
                    B, T, I, I, B, I,
                    G, B, I, N, I, N, I, MASK_A, MASK_B, G, T, I))
    lines.append("var %s=process.argv[2]||'';if(!%s){console.log(%s(%s));process.exit(1);}"
                 "if(%s(%s)){console.log(%s(%s)+' '+%s);}else{console.log(%s(%s));process.exit(2);}"
                 % (IN, IN, DEC, idx["USE"], CHK, IN, DEC, idx["OK"], IN, DEC, idx["NO"]))
    return "\n".join(lines) + "\n"


CLEAN_SOURCE = """// oe-warranty — claim validator (reference source, NOT shipped)
// The production bundle is minified from this logic.

const PREFIX = "cyber_quest{";
const KEY = Buffer.from("<key-hex>", "hex");   // per-build secret
const TARGET = Buffer.from("<target-b64>", "base64");

function mask(i) { return ((i * 0x1f + 0x03) & 0xff); }

function check(candidate) {
  if (typeof candidate !== "string") return false;
  if (!candidate.startsWith(PREFIX) || !candidate.endsWith("}")) return false;
  const body = candidate.slice(PREFIX.length, -1);
  if (body.length !== TARGET.length) return false;
  for (let i = 0; i < body.length; i++) {
    const g = body.charCodeAt(i) ^ KEY[i % KEY.length] ^ mask(i);
    if (g !== TARGET[i]) return false;
  }
  return true;
}

const input = process.argv[2] || "";
if (!input) { console.log("usage: node bundle.js <receipt-key>"); process.exit(1); }
if (check(input)) { console.log("warranty honored. receipt: " + input); }
else { console.log("claim denied."); process.exit(2); }
"""

NOTE_TXT = """oe-warranty // claim validator

Warranty claims moved to the self-service validator. Run it locally:

  node bundle.js <receipt-key>

One receipt is still honored. The bundle is minified, which is not the
same as secure, according to the one engineer who read the invoice.
"""


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate the Uglified challenge")
    ap.add_argument("--seed", default=DEFAULT_SEED)
    ap.add_argument("--flag", default=FLAG)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    bundle = build_bundle(args.flag, rng)

    os.makedirs(ORGANIZER, exist_ok=True)
    with open(os.path.join(ORGANIZER, "claim.js"), "w") as f:
        f.write(CLEAN_SOURCE)

    os.makedirs(HANDOUT, exist_ok=True)
    out = os.path.join(HANDOUT, "bundle.js")
    with open(out, "w") as f:
        f.write(bundle)
    with open(os.path.join(HANDOUT, "NOTE.txt"), "w") as f:
        f.write(NOTE_TXT)

    # Self-test: the bundle must accept the flag and reject anything else.
    ok = subprocess.run(["node", out, args.flag],
                        capture_output=True, text=True)
    assert ok.returncode == 0 and args.flag in ok.stdout, "bundle rejects flag"
    bad = subprocess.run(["node", out, "nope"], capture_output=True, text=True)
    assert bad.returncode == 2 and "denied" in bad.stdout, "bundle accepts junk"
    empty = subprocess.run(["node", out], capture_output=True, text=True)
    assert empty.returncode == 1 and "usage" in empty.stdout, "usage broken"
    assert args.flag not in bundle, "bundle leaks the flag in plaintext"
    assert FAKE_FLAG in bundle, "decoy receipt missing from bundle"

    print("flag: %s (len %d)" % (args.flag, len(args.flag)))
    print("bundle: %d bytes, %d lines" % (len(bundle), bundle.count("\n")))
    print("handout written to %s" % os.path.normpath(HANDOUT))


if __name__ == "__main__":
    sys.exit(main())
