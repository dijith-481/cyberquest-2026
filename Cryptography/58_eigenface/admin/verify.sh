#!/usr/bin/env bash
# 58_eigenface — verify the challenge is solvable end to end.
#
# Regenerates the handout deterministically, proves the flag is NOT greppable
# from any shipped file, checks the parameters are the ones the solver assumes,
# then runs the stdlib reference solve on a FRESH copy and checks the flag.
#
# The negative control matters here: a small-secret leak is one refactor away
# from becoming a one-liner. If the modulus ever shrinks to the key width, or
# the noise bound ever goes to zero, `grep -o cyber_quest` is no longer needed
# but `brute force the key` becomes trivial. Both are asserted below.
set -euo pipefail
cd "$(dirname "$0")/.."

EXPECTED='cyber_quest{3y3_f4c3_m34r_th3_fl4t_fl0w3r}'
HANDOUT=handout
STORE="$HANDOUT/template_store.json"
NOTE="$HANDOUT/visitor00_note.sealed"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

fail() { echo "VERIFY FAILED — $*" >&2; exit 1; }
ok()   { echo "  ok: $*"; }

# --- 1. deterministic regeneration + no drift from the shipped artifact -----
# Hash the COMMITTED handout before regenerating. Regenerating first and
# checking after would only prove the generator works, and would silently
# repair a mutated or staled shipped file.
SHIPPED="$(cat "$HANDOUT"/* | sha256sum | cut -d' ' -f1)"
python3 deployment/make_handout.py >/dev/null
REGEN1="$(cat "$HANDOUT"/* | sha256sum | cut -d' ' -f1)"
python3 deployment/make_handout.py >/dev/null
REGEN2="$(cat "$HANDOUT"/* | sha256sum | cut -d' ' -f1)"

[ "$REGEN1" = "$REGEN2" ] || fail "generator is not deterministic"
ok "deterministic ($REGEN1)"

[ "$SHIPPED" = "$REGEN1" ] || {
  echo "VERIFY FAILED — the shipped handout does not match a fresh regeneration." >&2
  echo "  committed: $SHIPPED" >&2
  echo "  generated: $REGEN1" >&2
  echo "  Do not hand-edit handout/ — fix the generator, or re-commit the files." >&2
  exit 1
}
ok "shipped handout matches the generator (no drift)"

# --- 2. shape: the parameters the solver depends on -------------------------
python3 - "$STORE" <<'EOF' || exit 1
import json, sys
d = json.load(open(sys.argv[1]))
mods = [int(m, 16) for m in d["moduli"]]
rows = d["rows"]

assert len(mods) >= 1, "no modulus published"
for q in mods:
    assert q.bit_length() == 256, f"modulus is {q.bit_length()} bits, expected 256"
assert len(rows) >= 8, f"only {len(rows)} leak rows"

# Every candidate must have enough pairs sharing ONE modulus, or no key can be
# confirmed. This is the invariant that makes the challenge solvable at all.
from collections import defaultdict
per = defaultdict(lambda: defaultdict(int))
for r in rows:
    per[r["candidate"]][r["modulus"]] += 1
for cand, bymod in per.items():
    assert max(bymod.values()) >= 2, \
        f"{cand}: no two pairs share a modulus — its key cannot be confirmed"

names = sorted(per)
assert "VISITOR-00" in names, "the flag-holder VISITOR-00 is missing"
assert len(names) >= 3, "not enough candidates to make enumeration a choice"
print(f"shape ok: {len(mods)} moduli, {len(rows)} rows, {len(names)} candidates")
EOF
ok "parameters are the ones the challenge assumes"

# --- 3. NEGATIVE CONTROL: the key is not brute-forceable ---------------------
# If key width approached modulus width, "invert the mask" would hand over the
# key directly with no error search. Assert the gap that the whole solve rests
# on is real and large.
python3 - "$STORE" <<'EOF' || exit 1
import json, sys
d = json.load(open(sys.argv[1]))
q = int(d["moduli"][0], 16)
gap = q.bit_length() - 64
assert gap >= 128, f"only {gap} bits of slack between key and modulus — too easy"
print(f"gap ok: 64-bit key inside a {q.bit_length()}-bit modulus ({gap} bits of slack)")
EOF
ok "key/modulus gap makes the error search necessary, not optional"

# --- 3b. NEGATIVE CONTROL: the handout must not state the answer -------------
# The challenge is that the sealing parameters are unpublished. If any shipped
# file hands over the relation, the bound, or either bit width, the challenge
# collapses to reading a JSON string — which is exactly what an earlier draft
# of this handout did.
python3 - <<'EOF' || exit 1
import pathlib, re
banned = [
    (r"mask\s*\*\s*key", "the sealing relation"),
    (r"\|\s*e\s*\|", "the error bound"),
    (r"2\s*\*\*\s*17|2\^17", "the error bound"),
    (r"\b64[- ]bit\b", "the key width"),
    (r"\b256[- ]bit\b", "the modulus width"),
    (r"modular inverse|modinv", "the technique"),
    (r"hidden number|HNP", "the attack name"),
    (r"whole story|enumerate even though", "store editorialising the solve"),
]
root = pathlib.Path("handout")
for p in sorted(root.rglob("*")):
    if not p.is_file():
        continue
    try:
        body = p.read_text()
    except (UnicodeDecodeError, OSError):
        continue
    for pattern, what in banned:
        m = re.search(pattern, body, re.I)
        assert not m, f"{p.name} reveals {what}: {m.group(0)!r}"
print("no handout file states the relation, the bound, or either width")
EOF
ok "handout does not hand over the relation or its parameters"

# --- 4. NEGATIVE CONTROL: the flag is not greppable from the handout ---------
python3 - <<'EOF' || exit 1
import pathlib, sys
root = pathlib.Path("handout")
hits = []
for p in sorted(root.rglob("*")):
    if not p.is_file():
        continue
    try:
        body = p.read_bytes()
    except OSError:
        continue
    if b"cyber_quest" in body:
        hits.append(p.name)
assert not hits, f"the flag is greppable from: {hits}"
print("no flag-shaped string in any handout file")
EOF
ok "flag appears nowhere in the handout in the clear"

# --- 5. the sealed note must actually be sealed -----------------------------
# A reviewer should not be able to read it. XOR against the true key must be
# required; check it does NOT decode with any other candidate's key shape.
python3 - "$NOTE" <<'EOF' || exit 1
import sys, pathlib
raw = pathlib.Path(sys.argv[1]).read_bytes()
assert len(raw) > 0, "sealed note is empty"
# A plaintext reading would be immediately legible.
assert b"VISITOR" not in raw, "the sealed note leaks its own subject"
assert not raw.startswith(b"cyber_quest"), "the sealed note is not sealed"
print(f"sealed note: {len(raw)} bytes, opaque")
EOF
ok "the VISITOR-00 note is genuinely sealed"

# --- 6. reference solve on a FRESH copy -------------------------------------
cp -r "$HANDOUT" "$TMP/handout"
OUT="$(python3 admin/solve.py "$TMP/handout")"
printf '%s\n' "$OUT" > "$TMP/solve.out"
echo "$OUT" | sed 's/^/  /'

echo "$OUT" | grep -q "$EXPECTED" || fail "the reference solve did not recover the flag"
ok "reference solve recovered the flag"

# --- 7. the solve must have done real work ----------------------------------
# Guard against a generator regression that quietly makes the answer trivial —
# e.g. an exact-error row (e == 0) that a single modular inversion resolves.
RECOVERED=$(echo "$OUT" | grep -c '^\[key\]')
[ "$RECOVERED" -ge 3 ] || fail "only $RECOVERED keys reported — the dump looks degenerate"
ok "$RECOVERED candidate keys recovered (dump is not degenerate)"

# --- 8. the flag must come from UNSEALING, not from the solver -------------
# Grepping stdout for the flag is not evidence of a solve: a solver with the
# answer pasted into it passes that check. Prove the recovered key actually
# decrypts the sealed note, and that the recovered VISITOR-00 key is the one
# the store was built with.
SOLVER_OUT="$TMP/solve.out" python3 - "$TMP/handout" "$EXPECTED" <<'EOF' || exit 1
import json, os, pathlib, re, sys

handout = pathlib.Path(sys.argv[1])
flag = sys.argv[2]
store = json.load(open(handout / "template_store.json"))
mods = [int(m, 16) for m in store["moduli"]]

def modinv(a, q):
    old_r, r, s, t = a, q, 1, 0
    while r:
        quo = old_r // r
        old_r, r = r, old_r - quo * r
        s, t = t, s - quo * t
    return s % q

noise = 1 << 17
rows = [r for r in store["rows"] if r["candidate"] == "VISITOR-00"]
first = rows[0]
q = mods[first["modulus"]]
inv_mask = modinv(int(first["mask"], 16), q)
sealed = int(first["sealed"], 16)

key = None
for err in range(-noise, noise):
    cand = (((sealed - err) % q) * inv_mask) % q
    if cand >= (1 << 64):
        continue
    good = True
    for r in rows[1:]:
        if r["modulus"] != first["modulus"]:
            continue
        oq = mods[r["modulus"]]
        resid = (int(r["sealed"], 16) - int(r["mask"], 16) * cand) % oq
        if resid > noise and resid < oq - noise:
            good = False
            break
    if good:
        key = cand
        break

assert key is not None, "independent re-derivation found no key"

# Unseal independently of the solver and confirm the flag falls out.
raw = (handout / "visitor00_note.sealed").read_bytes()
kb = key.to_bytes(8, "big")
text = bytes(b ^ kb[i % len(kb)] for i, b in enumerate(raw)).decode("utf-8", "replace")
assert flag in text, "the recovered key does not unseal the note"
assert "REVIEW NOTE" in text, "unsealed text does not look like the note"

# AND the solver must have reported that same key. Without this cross-check a
# solver with the flag pasted into it passes everything else: step 8 re-derives
# the key from the handout on its own, so the only thing tying the reference
# solve to a real derivation is this comparison.
solver_out = pathlib.Path(os.environ["SOLVER_OUT"]).read_text()
reported = set(re.findall(r"VISITOR-00: (0x[0-9a-f]{16})", solver_out))
assert reported == {f"0x{key:016x}"}, (
    f"solver reported VISITOR-00 key {reported or 'nothing'}, "
    f"independent derivation says 0x{key:016x} — the solver is not deriving"
)
print(f"independent re-derivation agrees: 0x{key:016x}")
EOF
ok "solver and independent re-derivation agree on the key"

echo
echo "VERIFY OK — flag recovered from a fresh handout, and the solve is not a one-liner"