# deployment — Lost in Translation (slot 15, H2)

Build-farm intake: one nc port, one binary, one bit of feedback.
Port **1340** (verify port: 13400). The image is the 2025 shape
unchanged (debian-slim + socat) — the gate needs no compiler: all
checks are cheap in-process heuristics.

## Run (docker, primary)

```sh
# from this directory:
docker build -t intake . && docker run -p 1340:1340 intake
# connects as: nc <host> 1340
```

The Dockerfile follows the 2025 BinaryExp shape (debian-slim + socat,
user `bob`, `/vuln`, flag baked to `/vuln/flag.txt`). `run.sh` resolves
the binary relative to itself, so it behaves identically in the container.

## Run (bare metal, no docker)

```sh
# copy deployment/ to the server, then:
./vuln/run.sh
# needs only: socat + the frozen binary (flag.txt ships next to it)
# connects as: nc <host> 1340
```

The gate locates `flag.txt` next to its own binary, so the working
directory you launch from does not matter.

## Files

- `vuln/chall.c` — the gate source
- `vuln/chall` — frozen binary (dynamic, needs glibc >= 2.34)
- `vuln/run.sh` — socat listener, works in-container and bare-metal
- `vuln/flag.txt` — committed next to the binary (slot-12 style), so
  every copy method (docker COPY, scp of `deployment/`) provisions it
  with zero manual steps. The Dockerfile `RUN echo …` line stays as
  belt-and-suspenders with identical content.
- `Dockerfile` — 2025-shape H2 service definition
- `Makefile` — reference rebuild (see the note inside)

## Verify

```sh
sh admin/verify.sh          # from the challenge root
```
