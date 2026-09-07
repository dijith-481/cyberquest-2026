# deployment — Break Glass (slot 16, H0)

Break Glass is a local reverse-engineering handout. It has no listener and
no runtime service: the player downloads `handout/vault` and debugs it on an
x86-64 Linux host. The source and deterministic build pipeline in this
directory are maintainer-only.

## Build

```sh
bash admin/build.sh
```

The reproducible build is written to `deployment/.build/vault`. To refresh
the frozen handout after an intentional source or flag change:

```sh
bash admin/build.sh --freeze
```

The equivalent `make -C deployment build` and `make -C deployment freeze`
targets are provided for hosts with Make installed.

The release is stripped, non-PIE, and uses anonymous executable mappings for
the two runtime stages. No compiler or source files are required by players.

## Verify

```sh
sh admin/verify.sh
```
