# clock_skew — solution

**Flag:** `cyber_quest{t0tp_4nd_th3_c10ck_th4t_l13d_7f30aa}`
**Difficulty:** medium

## The setup

The east stairwell door (model FAC-DOOR-4) takes a six-digit rotating
code:

- `door_spec.md` — the parameters, spelled out: HMAC-SHA1, 30 s time
  steps, standard 6-digit dynamic truncation, and the key is the door's
  **6-digit enrollment code used verbatim as the HMAC key**. Enrollment
  codes are six digits, 0–9.
- `door_log.txt` — the observation log: facilities sat by the door and
  wrote down every accepted code with **the door's own clock** as the
  timestamp.
- `maintenance_note.txt.enc` — a hex blob, XOR-sealed with a keystream
  derived from the enrollment code.

## Stage 1 — the key space

The spec says the key is the six-digit enrollment code as ASCII text.
That is 10^6 candidates — not small, but not a search, either.

## Stage 2 — recover the seed

For each candidate `000000`–`999999`, compute the code for the first
logged pair `(door-clock ts, accepted code)` with `T = floor(ts / 30)`
and check the dynamic-truncation output. The door's clock being 187
seconds slow is irrelevant: the log's timestamps are the **door's own
clock**, so `floor(door_clock / 30)` is exactly the step counter the
door used. Drift changes nothing about the attack.

One candidate matches the first code; the remaining logged pairs confirm
it:

```
enrollment code = 720903
```

(On a laptop, the sweep is about a million HMACs — a few seconds of
Python.)

## Stage 3 — unseal the note

The maintenance note is XOR against `SHA-256("fac-door/seed/" + code)`
repeated. Unsealing it yields facilities' own summary of the situation —
the clock is 187 seconds slow and holding — and:

```
Flag: cyber_quest{t0tp_4nd_th3_c10ck_th4t_l13d_7f30aa}
```

## Reference solve

`admin/solve.py` runs all three stages.
`admin/verify.sh` regenerates the handout (`deployment/make_handout.py`),
solves a fresh copy, and asserts the flag.
