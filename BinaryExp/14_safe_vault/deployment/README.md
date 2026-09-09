# deployment — SafeVault (slot 14, H2)

Label safe, rewritten in Rust: one nc port, one binary, one unsafe
tag flip. Port **1339** (verify port: 13390). The image is the 2025
shape unchanged (debian-slim + socat).

## Run (docker, primary)

```sh
# from this directory:
docker build -t vault2 . && docker run -p 1339:1339 vault2
# connects as: nc <host> 1339
```

## Run (bare metal, no docker)

```sh
# copy deployment/ to the server, then:
./vuln/run.sh
# needs only: socat + the frozen binary (flag.txt ships next to it)
# connects as: nc <host> 1339
```

The service reads `flag.txt` next to its own binary (falling back to
`/vuln/flag.txt`), so the working directory you launch from does not
matter. Every connection is a fresh process, so ASLR re-randomizes
per session — the solve parses `info` in-session, never hardcoded.

## Files

- `vuln/vault.rs` — the service source (also in the handout)
- `vuln/vault` — frozen binary (PIE, symbols kept, debuginfo stripped,
  dynamic, glibc >= 2.16). Symbols stay: the solve derives the
  print_flag-denied delta with plain `nm`.
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
