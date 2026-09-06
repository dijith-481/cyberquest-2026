# complexity_requirements — solution

**Flag:** `cyber_quest{c0mpli4nt_bu7_pr3dict4bl3_5e8817}`
**Difficulty:** easy-medium

## The setup

Security memo 2026-04 mandates "strong" passwords — and documents
exactly how they are stored:

- `security_memo_2026.txt` — the policy. Stored credentials are
  SHA-256 over `salt:password`, and salts are **derived, not random**:
  `<DEPT>-<EMPID>-Q<QUARTER>-<YY>` from department code, employee
  number, and rotation date. Break-glass notes are XOR-sealed with the
  owner's password (policy EX-3).
- `helpdesk_card.txt` — the helpdesk's compliant pattern:
  `<BaseWord><Season><YY><symbol>`, BaseWord from the attached
  60-word approved wordlist, Season aesthetic, symbol from `! @ #`.
- `password_export.csv` — 24 employees: department, salt, SHA-256
  hash, rotation date. The Director's row (EX-0007) has salt `#N/A`.
- `break_glass_note.txt.enc` — the escrow note, EX-3 sealed.

## Stage 1 — enumerate the compliant space

The card turns the policy into a generator:

```
60 words x 4 seasons x {25, 26} x {!, @, #} = 1,440 candidates
```

The complexity policy was meant to widen the space; the laminated card
narrows it back down. Hash each candidate against each exported salt —
a few thousand SHA-256s, instant.

## Stage 2 — crack the export

**19 of 24 rows** fall to the card pattern. The other five are actually
strong random passwords — the policy works, in exactly one direction.

## Stage 3 — the Director's salt

EX-0007 exported with salt `#N/A`. The memo's derivation rule
reconstructs it: department `EX`, employee number `0007`, rotation date
`2026-04-14` → Q2, YY 26:

```
salt = EX-0007-Q2-26
```

Hashing the same 1,440 candidates against the derived salt cracks the
Director too: `VaultAutumn26!` — 14 characters, four classes, fully
compliant, and chosen from a laminated list.

## Stage 4 — the break-glass note

Policy EX-3: the note is XOR with the owner's password. Unsealing it
with `VaultAutumn26!` yields the escrow note and:

```
Flag: cyber_quest{c0mpli4nt_bu7_pr3dict4bl3_5e8817}
```

## Reference solve

`admin/solve.py` runs all four stages.
`admin/verify.sh` regenerates the handout (`deployment/make_export.py`),
cracks a fresh copy, and asserts the flag.
