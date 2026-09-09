# 14 — safe_vault

## Files

- `README.md` — player-facing description (2025 template)
- `meta.yaml` — 2026 minimal metadata (medium-hard, 300 pts)
- `handout/` — `README.txt` + the service binary (`vault`, frozen,
  PIE, symbols kept, debuginfo stripped) + the full Rust source
  (`vault.rs`)
- `admin/solution.md` — full writeup
- `admin/solve.py` — scripted solve (stdlib only; needs `nm` for the
  local print_flag-denied delta)
- `admin/verify.sh` — rebuilds via `make`, stages `vault` + `flag.txt`
  in a temp dir, serves on 13390 with socat when present, else
  `admin/serve.py`, then runs the scripted solve
- `deployment/` — 2025-shape H2 service: `Dockerfile` (debian-slim +
  socat, user `bob`, `/vuln`, flag baked to `/vuln/flag.txt`, port
  **1339**), `Makefile` (`build`/`clean`), `README.md`,
  `vuln/vault.rs` (service source), `vuln/vault` (frozen binary),
  `vuln/run.sh` (socat listener, dual-purpose), `vuln/flag.txt`

## Run

```sh
cd deployment
make build   # rustc -O -C strip=debuginfo
docker build -t vault2 . && docker run -p 1339:1339 vault2   # primary
./vuln/run.sh   # bare-metal alternative: needs only socat
```

Verify: `sh admin/verify.sh`. NOTE: no frozen-binary `cmp` gate —
rustc embeds build hashes, so fresh builds are not byte-identical;
verify refreshes `handout/vault` (+ `vault.rs`) from source instead.

## The mechanic

Entirely different bug class from v1's stack overflow: **type
confusion through an unsafe enum-discriminant flip**. `store`
hex-decodes into a fixed `[u8; 64]` inside `Label::Text` (heap `Vec`,
no overflow possible). `promote` flips the tag byte `0 -> 1` through
a raw pointer — bounds-checked index, broken invariant: the 64 stored
bytes are reinterpreted as `Label::Callback(fn())`, and `run` calls
whatever they decode to.

Two derivation beats, both local-binary work:

1. **PIE slide**: `info` leaks only `denied`. `nm` (length-prefixed
   Rust symbols, no demangler needed) gives the `print_flag − denied`
   delta, exact across ASLR.
2. **Rust layout**: rustc packs `Text`'s array at struct+1 but reads
   `Callback`'s pointer from struct+8, so the address sits at label
   offset 7 — found with a 20-line transmute harness, documented in
   the solution.

Payload: `store hex(P*7 + p64)`, `promote 0`, `run 0`. One
connection, fully deterministic.

## Design notes

- Port 1339 reserved for slot 14.
- The hex wire format is load-bearing, not flavor: raw binary labels
  could smuggle `\n`/`\r` inside an address and split the line
  protocol (found at 195/200 reliability — the 5 failures were all
  `0x0a`/`0x0d` bytes in ASLR addresses). Hex makes every payload
  exactly representable.
- `print_flag` survives only via a `#[used]` enterprise-callback
  table (rustc drops the otherwise-unreferenced function, and its
  own `dead_code` warning becomes a hint). Same decoy pattern as
  slot 13's C table.
- The v1 payload dies three ways here: different commands, hex
  encoding, heap storage. The pair shares a story, not a primitive.
- `show` is the intentional debugger: prints stored bytes back
  pre-promotion, `callback redacted` post-promotion — the first
  visible proof the type flipped.
- Match-on-transmuted-enum reliability: 200/200 live solves after
  the hex fix (plus 30/30 under strace). If a rebuilder changes
  rustc flags, re-run the reliability loop before redeploying.
- 300 s watchdog thread per connection (mirrors v1's `alarm(300)`).
