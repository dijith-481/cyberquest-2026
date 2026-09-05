# hash_slinging — solution

**Flag:** `cyber_quest{n0_s4lt_n0_p3pp3r_ju5t_v4lue_c81d43}`
**Difficulty:** medium

## The setup

The handout is a "credential audit export":

- `credential_audit.csv` — 39 employees, an unsalted MD5 column, a
  `last_changed` date, and (for one row) a telling note.
- `corporate_wordlist.txt` — the "approved" 60-word password list.
- `it_policy_memo.txt` — Kevin's annual hygiene memo. It documents three
  policies: staff passwords are just wordlist words (optionally with digits),
  **executive** passwords follow a rotation scheme
  `<BaseWord><Season><YY><symbol>` keyed to the `last_changed` date, and
  vault notes are "sealed" by XOR with the owner's password (policy EX-3).
- `vault_note.txt` — hex blob.

## Stage 1 — the easy wins

Most of the CSV is plain `md5(password)`. A trivial rule set over the wordlist
(word, lowercased, word + 00–99, word + digits + `!`) cracks **28 of 39**
rows in well under a second. Hashcat rules `best64` or a two-line Python
loop both work.

## Stage 2 — the executive row

One row stays standing: `OE-0451, Marguerite Vale, Executive`. Her
`last_changed` is `2026-01-05` and the memo says exec passwords are

```
<BaseWord><Season><YY><symbol>
```

with Season taken from the change date (Dec/Jan/Feb → Winter), YY the
two-digit year, symbol ∈ {`!`, `@`, `#`}, and BaseWord from the *same
wordlist that is already attached to the memo*.

Candidate space: 60 words × 4 seasons × symbol × year — a few thousand
hashes. The hit:

```
md5("LedgerlineWinter26#") = e394dd181671339b80eb91acd15cbb12
```

The lesson the challenge is built around: unsalted MD5 plus a *documented,
low-entropy generation policy* means the policy is the wordlist. Nothing in
the dump needed to be secret for it to fall.

## Stage 3 — policy EX-3

The CSV note on the CFO's row says `vault seal = personal password`, and the
memo says vault notes are XOR-sealed with the owner's password. Repeating-key
XOR with `LedgerlineWinter26#` over the hex-decoded note yields plaintext:

```
Flag: cyber_quest{n0_s4lt_n0_p3pp3r_ju5t_v4lue_c81d43}
```

## Reference solve

`admin/solve.py` does all three stages. `admin/verify.sh` regenerates the
handout deterministically (`deployment/make_handout.py`), solves a fresh
copy, and asserts the flag — proving the challenge ships in a solvable state.
