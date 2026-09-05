# deployment — Optimized Away (slot 12, H2)

ledgerd reconciliation mirror: one nc port, two builds of the same source
running in lockstep. Port **1337** (verify port: 13370).

## Run (bare metal, no docker)

```sh
# copy deployment/ to the server, then:
./run.sh
# needs only: socat + the frozen static binaries
# connects as: nc <host> 1337
```

## Files

- `vuln/ledgerd.c` — the shared daemon source (built twice)
- `vuln/dispatcher.c` — lockstep mirror: runs both builds per connection,
  prints the consensus, releases the flag when both builds pass the audit
- `vuln/ledgerd-prod` — production build, `-O3`, static, stripped (frozen)
- `vuln/ledgerd-compat` — compat build, `-O0`, static, stripped (frozen)
- `flag.txt` — released by the dispatcher when both builds reconcile
- `Makefile` — reference rebuild (see the warning inside)

The binaries are **frozen**: the frame-offset difference between the two
builds is the challenge, so they are built once (gcc 14.2, static) and
shipped. No compiler needed on the server — just socat.

## Verify

```sh
sh admin/verify.sh          # from the challenge root
```
