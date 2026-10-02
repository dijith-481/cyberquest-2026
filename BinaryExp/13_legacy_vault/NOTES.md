# 13 — legacy_vault

## Files

- `README.md` — player-facing description (2025 template)
- `meta.yaml` — 2026 minimal metadata (easy, 200 pts)
- `handout/` — `README.txt` + the service binary (`vault`, frozen,
  PIE, symbols kept). NO source is shipped: the player must recover
  the struct layout and the overflow from the disassembly. Shipping
  `vault.c` gave away `buf[64] | epoch | on_auth`, the unchecked
  `memcpy`, and the `v.on_auth = denied` init — i.e. the entire
  exploit — reducing a 200-pt RE challenge to a 16-way guess.
- `admin/solution.md` — full writeup
- `admin/solve.py` — scripted solve (stdlib only; needs `nm` for the
  local page offsets)
- `admin/verify.sh` — rebuilds via `make`, asserts the frozen copies
  match a fresh build, stages `vault` + `flag.txt` in a temp dir,
  serves on 13380 with socat when present, else `admin/serve.py`,
  then runs the scripted solve
- `deployment/` — 2025-shape H2 service: `Dockerfile` (debian-slim +
  socat, user `bob`, `/vuln`, flag baked to `/vuln/flag.txt`, port
  **1338**), `Makefile` (`build`/`clean`), `README.md`,
  `vuln/vault.c` (service source), `vuln/vault` (frozen binary),
  `vuln/run.sh` (socat listener, dual-purpose), `vuln/flag.txt`

## Run

```sh
cd deployment
make build   # gcc -O2 -fPIE -pie -fstack-protector-strong, symbols kept
docker build -t vault1 . && docker run -p 1338:1338 vault1   # primary
./vuln/run.sh   # bare-metal alternative: needs only socat
```

Verify: `sh admin/verify.sh`.

## The mechanic

Classic stack-adjacent function-pointer overwrite, hardened past the
trivial version: PIE + stack protector + no code leak. `struct vault`
is `buf[64] | epoch (u64) | on_auth (fn ptr)`, so the callback sits at
`buf+72`. `store` memcpy()s with no bounds check; a precise 74-byte
write overwrites only `on_auth`'s low 2 bytes and never reaches the
canary (which guards the return address, not the locals).

ASLR slides whole pages, so with `denied` at page offset `0x300` and
`print_flag` at `0x1e0` (same page), the target low byte is fixed at
`0xe0` and the next byte has 4 unknown ASLR bits — 16 candidates
tried across fresh connections (~16 on average). `info` still prints
a stack address: independent mapping, useless for code, kept as the
audit's missed spot.

## Design notes

- Port 1338 reserved for slot 13 (slot 14 uses 1339; same ladder).
- The `-O2` build keeps the struct split-proof: `buf` is copied to a
  local and the fields are spilled/restored around it, but the
  overflow still lands on the `on_auth` spill at `buf+72` and is
  written back — verified by disassembly AND by the live solve, not
  by reading the source alone. If a rebuilder changes flags, they
  must re-verify the offset (see the Makefile note).
- `print_flag` is kept alive by a `used` callback table (otherwise
  `-O2` discards the unreferenced function); the table doubles as a
  decoy in the binary.
- A wrong guess crashes only its own connection; socat/`serve.py`
  fork (and exec) a fresh process per session, so brute force is
  safe for the service. 300 s alarm per connection.
- Never `pkill -f` with a pattern that appears in your own shell
  command line — `pkill` matches the parent `bash -c` too and kills
  your own session. Kill by PID.
