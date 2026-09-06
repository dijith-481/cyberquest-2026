# 15 — lost_in_translation

## Files

- `README.md` — player-facing description (2025 template)
- `meta.yaml` — 2026 minimal metadata
- `handout/` — `README.txt`, the conformance sample (`sample.c`,
  hand-written plain C whose whole eight-mark projection is exactly
  `[.>]`), and the intake binary (`chall`, frozen, unstripped) for
  local RE + testing
- `admin/solution.md` — full writeup (RE path, no shortcuts)
- `admin/solve.py` — reference solve: submits the forged C/BF polyglot
  (K=17 baked in from the reversing step; stdlib only)
- `admin/verify.sh` — builds the gate, serves it locally, runs the solve
- `deployment/` — 2025-shape H2 service: `Dockerfile` (debian-slim +
  socat, user `bob`, `/vuln`, flag baked to `/vuln/flag.txt`, port
  **1340**), `Makefile` (`build`/`clean`), `README.md` (docker-primary
  plus bare-metal instructions), `vuln/chall.c` (gate source),
  `vuln/chall` (frozen binary, dynamic, glibc >= 2.34),
  `vuln/run.sh` (socat listener, dual-purpose; deliberately WITHOUT
  socat's `,stderr` option — that option dups child stderr onto the
  player socket, which would leak server-side diagnostics onto the
  wire; without it stderr stays on the server log),
  `vuln/flag.txt` (committed next to the binary). The gate resolves
  the flag against its own executable path, so it serves correctly
  from any working directory, wrapper, or unit file — the Dockerfile
  RUN line is the single source; the committed file provisions every
  non-docker copy for free

## Run

```sh
cd deployment
make build   # rebuilds vuln/chall (dynamic, glibc >= 2.34)
docker build -t intake . && docker run -p 1340:1340 intake   # primary
./vuln/run.sh   # bare-metal alternative: needs only socat
```

Verify: `sh admin/verify.sh` (builds via `make`, stages `chall` +
`flag.txt` in a temp dir, serves on 13400 with socat when present, else
`admin/serve.py`, then runs the scripted solve).

## The mechanic (rebuilt: no leaks, compute-not-dump)

The gate is a Brainfuck interpreter with a 1-bit oracle and a
per-connection random stamp. Nothing is handed out:

1. **Sample is a true polyglot, not a payload drop.** `sample.c`
   is short, boring, warning-free C. Its whole eight-mark projection
   is exactly `[.>]` — one bracket pair in the file, carried by a
   real string subscript (`tag[41.0 > floor]`: float literal hides
   the `.`, comparison hides the `>`). Run locally it dumps the
   stamp; pasted remotely it loses (raw stamp, not stamp+17). It
   hands over the loop shape and nothing else.
2. **No execution oracle.** Every submission returns `unit accepted`
   (win only, flag follows iff deployed) or `intake: unit rejected`
   — identical lines for bad brackets, runaway loops, and wrong
   outputs, and no instruction counts. All iteration happens against
   the player's local copy of the shipped binary.
3. **No canonical shape.** The only in-handout program avoids every
   textbook idiom (`[-]`, multiply loops). The eight ops are
   discovered by reversing, never by eyeballing.
4. **Compute, carry, and weave — not dump, not soup.** The store
   opens with 16 fresh nonzero random bytes per connection; the gate
   wants each byte plus 17 *plus the previous answer* (CBC-style
   chaining). Comments and string/char literals are stripped before
   intake reads, `#` means instant rejection, and every surviving
   mark must touch real code (word character on some side,
   `++`/`--` glued) — so bare soup under an `int main` fig leaf
   never reaches the machine, and the only win is a real
   48-character program woven from genuine C syntax: two 18-term
   sums, a float comparison, a nested subscript, with a
   drain-carry (`<[->+<]>`). Correct for every stamp by
   construction: the `]` test always lands on an untouched nonzero
   cell until the zero terminator, and a zero answer mid-chain
   safely adds zero. Honest residual, documented: mechanically
   padding every mark with dummy identifiers satisfies the letter
   of the binding rule — but that still requires the full machine
   model plus the 48-character program, so the challenge's core
   survives; only the aesthetics are soft.

## Design notes

- Port 1340 reserved for slot 15.
- Binary strings scrubbed: no `tape`/`marks`/`endorsement`/`phrase`/
  `passage`/`brainfuck`/`normaliz` anywhere (`store` replaced `tape`,
  all reject lines byte-identical). The binary ships **stripped**,
  so even function and variable names only pay off under a
  disassembler aimed at the string/call cross-references — that IS
  the intended work. (`flag.txt` appears twice in strings: the win
  path and a stderr-only missing-file alarm. Both are standard CTF
  furniture, visible only via `strings`, and say nothing about the
  machine — same as the 2025 binaries.)
- The C face of `sample.c` contributes no marks outside the
  subscript: no includes, no commas, no `==`-free comparisons, single
  `.` from the float literal only. (Checked by hand at write time and
  re-checked by extracting the file: projection must equal `[.>]`.)
- Gate pipeline per unit: `int main` presence → strip
  comments/strings → reject `#` → binding rule (every kept mark
  touches a word character modulo whitespace, `++`/`--` glued) →
  keep eight marks + bracket-balance → run (5M step cap) → exact
  16-byte chained compare. No compiler anywhere: cheap rejects
  only, so the gate stays fast under load and the image stays
  2025-pure (socat only).
- Gate constants: 16-byte stamp (bytes 1..255, never blank), KEYADD 17
  chained forward (`out[i] = key[i] + 17 + out[i-1]`), 32768-cell
  wrapping store, `,` feeds 0, 16 KiB output cap, 8 units per
  connection, 240 s idle alarm.
- `sample.c` is hand-written and checked by three commands, not by a
  generator: `cc -std=c99 -Wall -Wextra -pedantic -fsyntax-only`
  clean, whole-file mark projection equals `[.>]` exactly, and the
  projection dumps a random stamp in a local harness. As C it
  compiles, runs mute, and returns a meaningless verdict code.
