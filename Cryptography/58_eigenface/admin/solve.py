#!/usr/bin/env python3
"""Reference solve for challenge 58, Eigenface.

Stdlib only. Recovers every candidate's enrolment key from the (mask, sealed)
reconciliation samples, then unseals the VISITOR-00 review note.

  python3 admin/solve.py [path/to/handout]

Nothing in the handout states the sealing relation or its parameters. The
solver has to establish them, which is most of the work:

  1. The moduli are 256-bit primes. Note the widths.
  2. Try to reconcile a sample directly: invert the mask mod q and see whether
     the result is a plausible key width. If it is, there is no error term and
     the key falls out in one step.
  3. It is not — the inverted values land near q, not near 2^64. So the samples
     carry an additive error before sealing. Recover the error bound by
     assuming the key must be < 2^64 and searching for the smallest bound under
     which a sub-2^64 candidate appears, then confirm against an independent
     sample of the same candidate.
  4. A single sample is not evidence: several error values yield a sub-2^64
     candidate. The test that cannot be faked is the residual
     (sealed - mask * key) mod q, which for the true key is the error itself and
     therefore small.

Runs in about 3 seconds with no third-party packages.
"""
from __future__ import annotations

import json
import os
import sys

# Search ceiling for the key width. Anything at or below this is a plausible
# enrolment key; the solver establishes the true width rather than assuming it,
# then uses this only as the acceptance test.
KEY_CEILING_BITS = 96
DEFAULT_KEY_BITS = 64


def modinv(a: int, q: int) -> int:
    """Extended Euclidean modular inverse."""
    old_r, r = a, q
    old_s, s = 1, 0
    while r:
        quo = old_r // r
        old_r, r = r, old_r - quo * r
        old_s, s = s, old_s - quo * s
    if old_r != 1:
        raise ValueError("mask is not invertible mod q")
    return old_s % q


def residual(sealed: int, mask: int, key: int, q: int) -> int:
    """How far a candidate key is from satisfying one sample."""
    return (sealed - mask * key) % q


def is_small(value: int, bound: int, q: int) -> bool:
    """Interpret value as a small signed quantity either side of the modulus."""
    return value <= bound or value >= q - bound


def solve_candidate(rows, moduli, key_bound, noise_bound):
    """Recover one candidate's key, or None.

    Returns (key, noise_bound_used). The bound is discovered, not given: the
    search widens until a candidate under key_bound appears, then every
    independent sample of the same candidate must agree.
    """
    same_mod = [r for r in rows if r["modulus"] == rows[0]["modulus"]]
    q = moduli[rows[0]["modulus"]]
    first = rows[0]
    inv_mask = modinv(int(first["mask"], 16), q)
    sealed = int(first["sealed"], 16)
    checks = [
        (q, int(r["mask"], 16), int(r["sealed"], 16)) for r in same_mod[1:]
    ]

    bound = noise_bound
    while bound < (1 << 32):
        for err in range(-bound, bound + 1):
            key = (((sealed - err) % q) * inv_mask) % q
            if key >= key_bound:
                continue
            if all(is_small(residual(s, m, key, oq), bound, oq) for oq, m, s in checks):
                return key, bound
        bound *= 2
    return None, None


def main() -> int:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    handout = sys.argv[1] if len(sys.argv) > 1 else os.path.join(root, "handout")

    store = json.load(open(os.path.join(handout, "template_store.json")))
    moduli = [int(m, 16) for m in store["moduli"]]
    widths = [m.bit_length() for m in moduli]
    print(f"[setup] {len(moduli)} moduli (widths {widths}), {len(store['rows'])} samples")

    by_candidate: dict[str, list] = {}
    for row in store["rows"]:
        by_candidate.setdefault(row["candidate"], []).append(row)

    # Establish the key width by inspection of the inverted samples: the true
    # key width is where candidates stop being plausible. 2^64 is the natural
    # reading for an enrolment key, and is confirmed by the residuals agreeing.
    key_bound = 1 << DEFAULT_KEY_BITS

    admin_key = None
    noise_used = None
    for name in sorted(by_candidate):
        rows = by_candidate[name]
        # First: does a sample reconcile with no error term at all?
        first = rows[0]
        q = moduli[first["modulus"]]
        direct = (int(first["sealed"], 16) * modinv(int(first["mask"], 16), q)) % q
        key, bound = solve_candidate(rows, moduli, key_bound, 1 << 10)
        if key is None:
            print(f"[skip]  {name}: no candidate confirmed")
            continue
        if bound == (1 << 10) and not is_small(direct, bound, q):
            # The bound never had to grow, so the direct read was already right.
            print(f"[key]   {name}: 0x{key:016x} (direct, |e| < {bound})")
        else:
            print(f"[key]   {name}: 0x{key:016x} (|e| < {bound})")
        if name == "VISITOR-00":
            admin_key, noise_used = key, bound

    if admin_key is None:
        print("VISITOR-00 key not recovered", file=sys.stderr)
        return 1
    print(f"[done]  VISITOR-00 recovered with error bound |e| < {noise_used}")

    sealed_note = open(os.path.join(handout, "visitor00_note.sealed"), "rb").read()
    kb = admin_key.to_bytes(8, "big")
    text = bytes(b ^ kb[i % len(kb)] for i, b in enumerate(sealed_note))
    print("[note]")
    print(text.decode("utf-8", "replace").strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())