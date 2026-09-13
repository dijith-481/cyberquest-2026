# Nothing to Declare — solution

**Flag:** `cyber_quest{th1s_p4ssp0rt_h4s_tw0_f4ces_46de17}`

Handout: `handout/passport.png` (one file, no server).

## What the file is

A PNG/ZIP polyglot. The PNG decoder stops at `IEND`; the ZIP central
directory lives at the tail, so `zipfile` / `unzip -l` opens the exact
same bytes as an archive containing:

```
INSPECTION_FORMAT.txt
border_control.db
```

`file` still reports `PNG image data`. `strings | grep cyber_quest`
finds nothing. `binwalk` / `xxd` (`PK\x03\x04`) / `unzip -l` all give
the game away — that is the intended first discovery.

## The construction

- Image side: a Cyberland passport — the new hire's travel document,
  scanned at receiving — for ALICE PACKET. The only
  value that matters is the document number from the machine-readable
  zone: `CQP0427` (line 2, before the first `<`).
- Archive side: receiving's entry-desk SQLite database with 64
  inspection records:

```sql
CREATE TABLE inspection_records (
    passport_hash TEXT PRIMARY KEY,
    checkpoint TEXT NOT NULL,
    status TEXT NOT NULL,
    sealed_note BLOB NOT NULL
);
```

- Lookup: `passport_hash = SHA256(document_number)`. The raw number
  never appears in the ZIP (verify with `grep -r CQP0427` on the
  extracted archive — no hits).
- Sealing: `key = SHA256(b"border-control:" + document_number)`,
  `plaintext[i] = sealed_note[i] XOR key[i % 32]`. The other 63 rows
  are seeded random blobs. Only the target row XORs to readable text.
- `INSPECTION_FORMAT.txt` documents both steps, so no crypto guessing
  is required.

## Intended solve path

1. Open the image normally, read the passport, note `CQP0427` in the
   MRZ (the format doc declares the MRZ authoritative).
2. Notice the second interpretation:
   `unzip -l passport.png` → `border_control.db`.
3. Read `INSPECTION_FORMAT.txt`, hash the document number:
   `echo -n CQP0427 | sha256sum` → `b3a52771…`.
4. Query the matching row, XOR with the derived key:
   `python3 admin/solve.py handout/passport.png` does all of it
   (stdlib-only MRZ OCR + sqlite + XOR) and prints:

```
SECONDARY INSPECTION REPORT

Subject: ALICE PACKET
Document: CQP0427
Checkpoint: TERMINAL-07
Status: CLEARED
Importer: ORDINARY ENGINEERING

Recovered evidence:
cyber_quest{th1s_p4ssp0rt_h4s_tw0_f4ces_46de17}
```

## Why shortcuts fail

- `strings` on the polyglot or the extracted DB never shows the flag
  (it is XOR-sealed) or the document number (only its hash is stored).
- Brute-forcing `CQP0000…9999` is possible but strictly more work than
  reading the image, which is the point: neither interpretation alone
  contains the solution.

## Organizer verification

```bash
sh admin/verify.sh
```

Regenerates the handout from `--seed 46`, `cmp`s it, checks PNG + ZIP
parsers both accept it, asserts no plaintext leak on either side, and
runs the reference solver.
