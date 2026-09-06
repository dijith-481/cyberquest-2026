# two_time_pad — solution

**Flag:** `cyber_quest{0ne_t1me_p4d_pl3ase_c94d21}`
**Difficulty:** medium

## The setup

The Records Division seals every memo by XOR with "the" pad:

- `pad_protocol.txt` — the sealing protocol. Pad version 3, one pad per
  filing cabinet, "strictly single-use ... every fiscal quarter."
- `memo_register.csv` — what is in the cabinet. Memo 0049's status is
  `SEALED (DRAFT ON FILE)` — and per protocol §4, drafts live on the
  draft shelf beside the copier.
- `memos/` — four sealed memos, hex-encoded, plus `memo_0049_draft.txt`,
  the draft shelf copy of memo 0049. Unsealed. Verbatim.

## Stage 1 — notice the pad is not one-time

XOR any two sealed memos: the result is plaintext ⊕ plaintext — mostly
letters against letters, and the identical header lines cancel to zeros
at both ends. A one-time pad used once looks like random noise; this
cabinet does not.

## Stage 2 — recover the pad

The draft shelf copy of memo 0049 is the plaintext of a sealed memo.
XOR `memo_0049.hex` against `memo_0049_draft.txt`:

```
pad = sealed_0049 XOR draft_0049
```

That recovers the first `len(draft)` bytes of the pad — and the draft is
the longest memo in the cabinet, so the pad is recovered end to end.

## Stage 3 — open the cabinet

XOR every sealed memo against the recovered pad. The memos decrypt:
the fridge, the denied rotation request (memo 0067 is the protocol
memo contradicting itself), and memo 0072, Records' own review of the
quarter's sealing incidents, which closes with:

```
Flag: cyber_quest{0ne_t1me_p4d_pl3ase_c94d21}
```

## Reference solve

`admin/solve.py` runs all three stages.
`admin/verify.sh` regenerates the handout (`deployment/make_memos.py`),
solves a fresh copy, and asserts the flag.
