# Break Glass — solution

**Flag:** `cyber_quest{br34k_gl4ss_l1v3_p4tch_7f3a1c}`  
**Difficulty:** hard

## Intended solve

Break Glass is a live-debugging challenge. The release binary has no symbols
and does not contain the flag as plaintext. On an ordinary run it executes
two broken runtime stages, derives the wrong key, and prints a fresh decoy.
The real flag appears only after repairing both stage outputs in memory.

The handout is deliberately only `vault` and `README.txt`. The source,
stage generators, and the frozen-build checks are kept under `deployment/`
and `admin/` for challenge maintenance.

## 1. Find the entry point

The binary is stripped, but the first call into libc still passes `main` as
the first argument to `__libc_start_main`:

```text
$ gdb ./vault
(gdb) set pagination off
(gdb) break __libc_start_main
(gdb) run
(gdb) p/x $rdi
$1 = 0x4015d1
(gdb) disassemble /r $rdi, $rdi+0x180
```

The exact addresses below describe the frozen handout. They are not stage
addresses: the two stages are mapped anonymously and their bases change at
runtime.

The first indirect call is at `0x401614`; the second is at `0x40166f`.
The target master key is loaded immediately before the final comparison as
`0x84d359f8ed6a08bd`. The nearby salt is `0xc0ffee1234567890`.

## 2. Recover the target checksum

At the first call site, `rax` holds the base address of the freshly decoded
stage A:

```text
(gdb) break *0x401614
(gdb) continue
(gdb) set $stage_a = $rax
(gdb) x/40i $stage_a
```

The anonymous code is a short rotate/xor/add checksum routine. Its final
store is at `$stage_a+0x73`. Stop immediately before that store:

```text
(gdb) tbreak *($stage_a+0x73)
(gdb) continue
(gdb) p/x $rdx
$2 = 0x442cb715d93c7026
```

The natural value is seven short. The intended checksum is therefore
`0x442cb715d93c702d`. Patch the result register before the store executes:

```text
(gdb) set $rdx = 0x442cb715d93c702d
```

The `+7` is also independently recoverable from the final key equation. If
the state reaches `0xff`, then:

```text
checksum = target_key ^ (0xff << 32) ^ salt
         = 0x442cb715d93c702d
```

## 3. Repair the state machine

The second call enters stage C. Inspect it after stopping at the call site:

```text
(gdb) break *0x40166f
(gdb) continue
(gdb) set $stage_c = $rax
(gdb) x/80i $stage_c
```

The state machine starts at `0x11`, advances to `0x59`, then writes the
wrong `0x7e` for the next state. `0x7e` is a dead-end case. In this frozen
build, the instruction after the buggy immediate store is at
`$stage_c+0x6a`. At that point the state local is already `0x7e` at
`[rbp-8]`, so patch the local before the stage stores it back to the caller:

```text
(gdb) tbreak *($stage_c+0x6a)
(gdb) continue
(gdb) p/x *(unsigned long*)($rbp-8)
$3 = 0x7e
(gdb) set {unsigned long}($rbp-8) = 0x7d
(gdb) continue
```

The repaired path is now `0x11 -> 0x59 -> 0x7d -> 0xff`, and the stage
returns normally.

## 4. Let the key decode the flag

The program now computes the exact target key and XOR-decodes the encrypted
fragment. The output is:

```text
cyber_quest{br34k_gl4ss_l1v3_p4tch_7f3a1c}
```

The status variable written by stage C is intentionally not the real gate.
Changing a branch or forcing that convenience value would still leave the
wrong checksum/state pair and therefore the wrong keystream key.

## Why static shortcuts fail

- The flag fragment is encrypted in the binary; the release has no plaintext
  `cyber_quest{...}` string.
- Both stage blobs are XOR-encrypted and only exist as executable anonymous
  pages while the program runs.
- The checksum is exact, not merely nonzero, and the final state must be
  exactly `0xff`.
- Running the file repeatedly produces different token-shaped decoys. That
  behavior is intentional and does not indicate a broken handout.

## Maintainer verification

From the challenge root:

```sh
sh admin/verify.sh
```

The exact frozen solve is also captured in `admin/solve.gdb`.
