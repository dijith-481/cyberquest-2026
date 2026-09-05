# 12 — optimized_away

## Files

- `README.md` — player-facing description (2025 template)
- `meta.yaml` — 2026 minimal metadata
- `handout/` — `README.txt` + both builds (`ledgerd-prod`, `ledgerd-compat`,
  static, stripped)
- `admin/solution.md` — full writeup with excerpts from the shipped binaries
- `admin/solve.py` — scripted solve (stdlib only)
- `admin/verify.sh` — serves the mirror locally, runs the solve
- `deployment/` — source, frozen binaries, `run.sh` (plain socat, no docker), port **1337**

## Run

```sh
# copy deployment/ to the server, then:
./run.sh
```

Verify: `sh admin/verify.sh` (uses socat when present, else a python
stand-in listener).

## The mechanic

One C source (`deployment/vuln/ledgerd.c`), built twice, run in lockstep
behind one port by `dispatcher.c`:

1. `tag <text>` does `strcpy(tag, line+4)` into a 64-byte local that sits
   next to `struct session` in `handle_conn`'s frame. `session.admin`
   (compared against token `0x31415926` by a `noinline` audit function, so
   it stays a live memory load even at `-O3`) is reachable by the overflow.
2. The two builds disagree on the distance `tag -> admin`: compat (`-O0`)
   keeps a dead 32-byte scratch local between the buffers (distance 120),
   prod (`-O3`) eliminates it (distance 88). Struct *layout* is
   ABI-frozen and identical in both — `layout` honestly prints identical
   offsetof numbers plus a fake "vendor frame map" as the red herring.
3. The dispatcher releases the flag only when BOTH builds pass `audit`.
   One payload can satisfy both because the offsets differ and the token
   is printable and NUL-free: `"A"*88 + "&YA1" + "A"*28 + "&YA1"`. The
   token aimed at the other build always lands in scratch/note — harmless
   by construction.

## Design notes

- Port 1337 reserved for slot 12 (slot 15 uses 1340; same ladder).
- Binaries are **frozen** (gcc 14.2, `-static`,
  stripped). The exploit depends on frame layout, so the deployment never
  recompiles; the server needs only socat. The Makefile documents
  the offsets and warns re-builders to re-measure.
- Verified the mechanic survives both gcc 14.2 (deployment) and gcc 15.3
  (this host): distances are 120/88 on both. The `-O3` audit still reads
  `admin` from memory at audit time (`mov edi,[rsp+0x58]` before
  `session_audit.isra.0`) because the struct's address escapes into
  `noinline` open/audit helpers — no const-prop, no register caching.
- `0x31415926` ("&YA1" LE) is printable ASCII and NUL-free so the final
  payload is typeable over plain `nc` — no pwntools required.
- Cross-landings are safe by construction: in compat, prod's token at 88
  falls inside the scratch buffer; in prod, compat's token at 120 falls
  inside session `note[]`. State gets visibly garbled (`state` prints the
  junk) but nothing gated on it.
- Feedback channels are fair but not giving: `audit` is labelled per
  build, `state` shows harmless fields (never `admin`), `layout` prints
  only ABI-fixed facts and vendor fiction.
- Alternative solves accounted for: sequential three-payload ordering and
  offset scanning both converge on the combined payload; neither is a
  shortcut past understanding both frames.
- Anti-overlap vs 2025 (three socat stack overflows): the vector here is
  the *differential* — the same input means different memory in two builds
  of the same source, and the gate requires both. No ret2win, no single
  int flip.
- 600 s idle alarm per connection; dispatcher kills both children on EOF.
