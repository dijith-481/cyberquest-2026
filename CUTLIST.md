# 2026 Release — Cut List & Replacement Slots

**Nothing is deleted.** Removed challenges are archived (repo stays intact, admin/
solutions intact). Replacements take fresh numbers from **50 upward** so nothing
renumbers and every old writeup/verify.sh keeps working.

Current: 55 challenges, 13300 base points.

---

## Confirmed cuts — 7 challenges, 1550 points freed

07 and 06 are cut **and replaced**, not merely dropped: 57 takes 07's slot at
the same 400 points, and 56 takes 06's. Both replacements are built and
mechanically verified. 07 was already cut here for fragility; 06 is cut because
its remaining purpose was to host it.

| # | Title | Cat | Pts | Why it's cut |
|---|---|---|---|---|
| 06 | Promotion Letter | Web | 100 | **Superseded by 56 Standing Order.** No independent weakness: 06 was a sound 100-pointer, but it existed in the event mainly to host 07, and 07 is gone. Its employee-console deployment has no role left once the co-hosted challenge is cut. Retained in the tree, unbuilt for the event. Replaced by **56**. |
| 07 | Clock Puncher | Web | 400 | **Timing attack over the internet is not reliable.** Needs a ~150 ms signal to survive the network path; any CDN/WAF/LB/shared-CPU host adds jitter that swamps it. Also has no rate limiting *by design* (must absorb ~2000 requests for tag recovery), so any reverse proxy will throttle or ban players mid-attack. Highest fragility in the event. |
| 14 | Safe Vault | Binary | 300 | **Same exploit shape as 13 Legacy Vault** — same "Vault" concept, both need `nm` to locate `print_flag`, both redirect a function pointer. 14 is 13 rewritten in Rust. Secondary: its `verify.sh` *overwrites* the handout with no byte-compare gate, so a rustc bump silently reshuffles the PIE delta and the offset-7 derivation with no CI signal. |
| 19 | Et Tu, Brute? | Crypto | 300 | **Same crib-drag as 21 Emojinated** — identical technique, different skin. Caesar + Vigenère is also the most well-trodden crypto in existence. 21 keeps the lesson and has the better payoff. |
| 24 | Complexity Requirements | Crypto | 250 | **Verbatim clone of 17 Hash Slinging.** Both are: read a memo -> build a password scheme -> crack the hashes -> XOR a note with the derived password. Five identical beats. 17 is the safer survivor (wordlist ships inside the zip; 24 requires deriving a 1440-candidate policy space). |
| 41 | Tracking | Stego | 200 | **Overlaps 38 Posterized** — both are "read one bit per entry from a table, in a specified order." Also the most niche stego in the set (GPOS kerning parity needs fontTools + cmap format-4 parsing). The stego family survives on 38/39/40/42 without it. |

### Why each cut preserves early retention
06 and 07 are **replaced in full** — 400 + 100 points come back as 57 and 56, so
the WebExploitation mid-tier loses nothing. The remaining three cuts are **medium
or hard**. The easy tier is otherwise untouched, so the Day 1 / Day 2
zero-install window keeps its depth. Nothing that survives moves in the first
two days.

### Deliberate pairs that survive (do NOT cut)
- **09 dino (100) + 10 dino rev 2 (400)** — intentional easy->hard escalation, two
  challenges on **one** deployment. Efficient, and the progression teaches.
- **03 Second Guess + 04 Rewind** — both "the randomness wasn't random." Different
  mechanics (UUID field vs z3 PRNG inversion) and 04 is the 500-point prize.
- **17 Hash Slinging** — survives 24's cut; now the sole password-crack->XOR challenge.

---

## Replacement slots — 5 challenges, 750 points (FINAL)

Numbering starts at 50. Two static-web (hosted, no backend), three handout,
two app-hosted. None duplicates a surviving technique cluster.

| New # | Title | Category | Type | Pts | Status |
|---|---|---|---|---|---|
| 51 | Share Card | WebExploitation | static web | 150 | **built** — `verify.sh` 20 checks / 8 negative tests |
| 53 | Payroll Photo | Forensic | handout | 150 | **built** — `verify.sh` 5 stages / 5 negative tests |
| 54 | Lobby Intercom | Steganography | handout | 200 | **built** — `verify.sh` 5 stages / 10 negative tests |
| ~~55~~ | ~~Redlined~~ | — | — | — | **CUT** — not needed |
| 56 | Standing Order | WebExploitation | app | 500 | **built + verified** — replaces 06; prototype pollution via a batch/route index desync |
| 57 | Coming of Age | WebExploitation | app | 400 | **built + verified** — replaces 07; UA gate, XML export, unowned idempotency cache, ops token |

All five carry `README.md`, `meta.yaml`, `admin/solution.md` and a
`verify.sh` that has been proven *able to fail*. None of the verifiers
regenerates-then-checks-only: each hashes the committed handout first and
fails on drift, so a mutated or staled shipped file is caught rather than
silently repaired.

52 was priced at 250 rather than the 200 first proposed, so that it lands
in the medium band and carries a first-blood bonus. At 200 it would have
been `easy` by the scoreboard's points-derived rule and paid nothing,
which is wrong for a contested solve.

### 56 · Standing Order — added separately

| New # | Title | Category | Type | Pts | Status |
|---|---|---|---|---|---|
| 56 | Standing Order | WebExploitation | app (Deno) | 500 | **built + verified** — fills the 06 slot; `verify.sh` 5 assertion groups, incl. shared-process isolation |

A hard replacement for the JWT-flavoured role-flip that sat in 06, built to
fill the gap identified in the technique audit: 2026 had **no** server-side
interpretation-conflict, prototype-pollution, deserialization or
request-smuggling challenge anywhere, having drifted toward
"read the served artifact". 2025's set was 5/5 request-crafting.

Modelled on **CVE-2026-63030** (wp2shell, WordPress Core REST batch route
confusion, CISA KEV 2026-07-21) chained with prototype pollution rather than
SQLi, so it is distinct from 2025's `Gh0st in the Query` while teaching the
same first lesson.

Numbering note: this took **56**, not 50–54 or a reuse of 06. `55` is reserved
by `55_universe_98_bridge/`, which is untracked in-progress work with no
`meta.yaml` or `README.md` — not a released slot, but not ours to renumber
either. `06_promotion_letter/` is left completely untouched; the new
challenge was added alongside it, not in its place.

### 50 · Source of Truth — CUT

Withdrawn. The mechanic is sound — a decoy flag in plain sight in an HTML
comment, the real one in the **linked stylesheet** rather than the HTML, so the
lesson is *the page you are reading is not the page that was served*.

Two reasons it goes. It duplicated the "look past the obvious surface" beat that
`51 Share Card` already runs, with a strictly harder target. And at 50 points it
was the event's only `very-easy` — a tier the scoreboard has no rule for and the
only entry below the documented 100-point floor.

`51 Share Card` is kept and redesigned onto the shared paper language.

### 56 · Standing Order — final spec
- **500 points.** Prototype pollution reached through an index desync: `serveBatch` keeps
  `validation[]` and `matches[]` index-aligned, a sub-request whose path fails to parse
  skips the `matches[]` push, and every later sub-request then executes under its
  neighbour's handler. The schema that *validates* a request belongs to a different route
  than the one that *executes* it, so a permissive route's body reaches a strict route's
  deep merge and writes `credentials.bearer` onto `Object.prototype`. The gate reads a
  config section that does not exist and is satisfied by the pollution.
- Request isolation is the hard part of the deployment: one process serves every team,
  and prototype pollution cannot be undone by an attacker, so every request runs inside
  save/restore of `Object.prototype`'s own descriptors plus the desk state. Without it the
  first team to solve leaves the gate permanently open for the next twenty.

### 57 · Coming of Age — final spec
- **400 points.** Four hops, each a misused legitimate feature rather than a named class:
  a `User-Agent` allowlist that answers a byte-identical empty 404, a second
  content-type code path that never got the ownership check its neighbour has, a
  retry-safety cache keyed on a publicly documented derivation with no binding to the
  caller, and a token check.
- The 404 that fails is the point. `verify.sh` diffs a gated 404's headers against a
  genuinely absent route, so the door cannot be accidentally one header more visible
  than a real absence.
- **The verifier fails if the challenge is hardened.** Namespacing `SYNC_CACHE` per team
  is the correct security fix and makes hop 3 unreachable; step 7 asserts both the flatness
  the puzzle needs and the namespace independence fair play needs.

### Non-duplication check
Surviving clusters after the cuts: password-crack->XOR (17), function pointer (13),
crib-drag classical cipher (21), unzip-container (46), bit-per-table stego (38/39/40/42),
dino pair (09/10), PRNG recovery (03/04), prototype pollution (56). The candidates above
sit outside all of them — 57 in particular is the first challenge built around HTTP
request semantics (a UA allowlist, `Accept` negotiation, an `Idempotency-Key` header) and
the first whose bug is an *absent condition* rather than a present mistake.

---

## Also in scope

**The Lost Year** (existing, 100 pts) — **CONFIRMED, domain access is in hand.** Build is
complete and self-contained; only the A record for `1337.excelmec.org` was missing, and
that is now solved. Static bundle, so it costs nothing to host beyond the DNS entry.

**51 Dead Letter** — skipped. The solve needs a registered subdomain, a real
DNS-01 cert and a published TXT record. `afterimage17.int.yt` is NXDOMAIN and the
repo cannot provision it.

**50 Time Traveller** — **LIVE.** Earlier this file recorded it as skipped
because its mirror account and repo both 404'd. That is a hosting problem, not a
scrap of the challenge: the build is complete in `OSINT/50_time_traveller/`
(7 files, own `admin/verify.sh`, `status: in-progress`) and only the external
mirror needs re-provisioning before it can be verified.

---

## Arithmetic
- 51 challenges before cuts (includes The Lost Year)
- minus 8 cuts (-1650 pts) -> 43 challenges
- plus 4 replacements (+550 pts) -> 47 challenges
- plus 56 (+500) and 57 (+400), which fill the vacated 06 and 07 slots
  -> **49 challenges, 13000 base**

06 and 07 are the only cuts whose points come straight back. The other four
cuts release 1150 points against 550 of replacements, `52 Reply All` (250 pts)
was withdrawn after build — its flag is a literal substring on a single line of
the handout, so `grep -a "for <"` solved it in one command — and `50 Source of
Truth` (50 pts) was withdrawn as a duplicate of `51 Share Card` and as the
event's only sub-100 pointer. The pool therefore sits ~200 below where it started, and
the *weakest* challenge in the set — a timing attack that cannot survive a CDN —
is gone. That is the intended trade: 07 Clock Puncher's 400 points were released
precisely because a timing attack over the internet is not reliable, and nothing
released since has reintroduced that fragility — 56 and 57 are both single-process
HTTP services with no network-path sensitivity, no external infrastructure and no
long-running state that a player can invalidate for the next team.

