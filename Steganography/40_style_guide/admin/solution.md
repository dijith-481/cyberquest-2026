# Style Guide — solution

**Flag:** `cyber_quest{h4lf_p01nt_h1d3s_th3_gu1d3_9d4e2f}`
**Difficulty:** medium

Handout: `handout/style_guide.pdf` (one file, no server).

## The story

Revision 3.9 of the OE Internal Brand System for the brand refresh. The
cover says "Protected document", readers report copying / editing /
printing as not allowed, the manual names a distribution password policy
(`BrandName + revision number`), and a confidential `master-assets.zip`
travels attached to the file, password required. Every one of these is
misdirection — and every one of them points at the real mechanism.

## Step 1 — notice the protection is owner-side only

```bash
pdfinfo style_guide.pdf            # opens with no password prompt
qpdf --show-encryption style_guide.pdf
```

reveals `R = 2`, `P = -64`, and an **empty user password**. The document
was never locked against opening; only the owner/permissions password is
set, and those restrictions are viewer-enforced. There is nothing to
crack: the owner password is a random 16-character string, so `brand39`,
`house3.9`, `brand_39` and the rest of the policy guesses all fail because
they were never the key to anything. (That is also why brute-forcing with
rockyou is a waste of hardware — the intended path never needs it.)

## Step 2 — open the decoy attachment, then leave it alone

The attachments panel holds `master-assets.zip`. It really is password
protected (traditional ZipCrypto) and it really will not open with any
policy-derived guess. Its `README.txt` claims the password "is documented
in the spacing specification". That sentence is the hinge of the whole
challenge: section 2 documents no password. It documents this:

```text
Base grid: 72 pt
Optical adjustment: 0.5 pt
Never eyeball alignment. Every half-point matters.
```

If the ZIP is ever opened (the password is irrelevant to the flag), its
`wrong_direction.txt` says so outright: the spacing specification is not
a password hint, it is the extraction rule.

## Step 3 — read the coordinates

With the empty user password, any tool dumps the content streams
decrypted, e.g.:

```bash
qpdf --qdf --object-streams=disable style_guide.pdf unpacked.pdf
grep -a -o -E '1 0 0 1 [0-9]+\.[0-9]+ [0-9]+ Tm' unpacked.pdf | head
```

Body lines sit at one of two x positions:

```text
72.0  ->  0
72.5  ->  1
```

The half-point jitter is invisible on the page. Ordinary copy (headings,
cover, spec table) uses integer x positions and never collides with the
carriers.

## Step 4 — decode

In page order, carrier x positions give the bitstream. The first 16 bits
(big-endian) are the flag byte length; the rest is the flag MSB first:

```bash
python3 admin/solve.py handout/style_guide.pdf
# cyber_quest{h4lf_p01nt_h1d3s_th3_gu1d3_9d4e2f}
```

384 carrier bits total (16-bit length + 46 flag bytes), spread over the
specimen block on the spacing page and the body pages that follow.

## Why the decoy works

Following the password hunt teaches the solver the decode rule: the ZIP
sends them to section 2, section 2 teaches 72 pt / 0.5 pt, and the content
stream then shows `72.0` / `72.5` on every line. The intended reaction is
"oh — that clue was never about the password at all."

## Organizer verification

```bash
sh admin/verify.sh
```

regenerates the handout from `--seed 40 --flag <flag>` and `cmp`s it
against the shipped file, asserts the flag and decoy text never appear in
plaintext, asserts the embedded ZIP is present and password-protected,
runs `admin/solve.py` against the shipped file, and cross-checks with
pypdf when available.

## Per-team randomization

```bash
python3 deployment/generate.py --seed <team-seed> --flag <flag> --out style_guide.pdf
```

Randomizes filler sentences, carrier pagination, owner/ZIP passwords, ZIP
crypto header bytes, and file IDs. The solve concept is identical;
hard-coded answers do not transfer.
