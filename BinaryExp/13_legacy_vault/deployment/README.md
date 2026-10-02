# deployment — LegacyVault (slot 13, H2)

Label safe, hardened after the audit: one nc port, one PIE binary, one
leftover overflow. Port **1338** (verify port: 13380). The image is
the 2025 shape unchanged (debian-slim + socat).

## Run (docker, primary)

```sh
# from this directory:
docker build -t vault1 . && docker run -p 1338:1338 vault1
# connects as: nc <host> 1338
```

## Run (bare metal, no docker)

```sh
# copy deployment/ to the server, then:
./vuln/run.sh
# needs only: socat + the frozen binary (flag.txt ships next to it)
# connects as: nc <host> 1338
```

The service locates `flag.txt` next to its own binary (falling back to
`/vuln/flag.txt`), so the working directory you launch from does not
matter. Every connection is a fresh process, so ASLR re-randomizes
per session — the solve expects exactly that.

## Files

- `vuln/vault.c` — the service source. AUTHOR-SIDE ONLY: it is
  deliberately **not** in the handout. Shipping it gave away
  `buf[64] | epoch | on_auth`, the unchecked `memcpy`, and the
  `v.on_auth = denied` init, collapsing a 200-pt RE challenge into a
  16-way guess. The player recovers all of it from the disassembly.
- `vuln/vault` — frozen binary (PIE, stack protector, symbols kept,
  dynamic, glibc >= 2.2.5). Symbols stay: the solve derives page
  offsets with `nm`, and stripping would not move the code anyway.
- `vuln/run.sh` — socat listener, works in-container and bare-metal
- `vuln/flag.txt` — committed next to the binary, so every copy method
  provisions it with zero manual steps. The Dockerfile `RUN echo …`
  line stays as belt-and-suspenders with identical content.
- `Dockerfile` — 2025-shape H2 service definition
- `Makefile` — reference rebuild (see the note inside)

## Verify

```sh
sh admin/verify.sh          # from the challenge root
```
