# Pending Deployment — challenges not yet hosted

Everything else is deployed. This is the only remaining hosting work.

Excludes all cuts (06 Promotion Letter, 07 Clock Puncher, 14 Safe Vault, 19 Et Tu Brute?, 24 Complexity Requirements, 41 Tracking).

---

## 1. Web / app challenges (need a server — Cloud Run or VM) — 9

| # | Title | Cat | Pts | Notes |
|---|---|---|---|---|
| 01 | Buy One Get One | WebExploitation | 200 | store app |
| 02 | Negative Space | WebExploitation | 100 | poster-gen; also serves 03, 04 |
| 03 | Second Guess | WebExploitation | 300 | served via 02 |
| 04 | Rewind | WebExploitation | 500 | served via 02 |
| 08 | AI-Powered | WebExploitation | 300 | open-door app |
| 09 | dino | WebExploitation | 100 | kiosk app; also serves 10 |
| 10 | dino rev 2 | WebExploitation | 400 | served via 09 |
| 56 | Standing Order | WebExploitation | 500 | Deno single-process app |
| 57 | Coming of Age | WebExploitation | 400 | single-process app |

Deployment: 5 app processes (01, 02, 08, 09, 56/57) — some pair up. Run on VM behind Cloudflare proxy, or Cloud Run per service.

## 2. NC challenges (raw TCP — need a VM) — 3

| # | Title | Cat | Pts | Port |
|---|---|---|---|---|
| 12 | Optimized Away | BinaryExp | 300 | 1337 |
| 13 | Legacy Vault | BinaryExp | 200 | 1338 |
| 15 | Lost in Translation | BinaryExp | 400 | 1340 |

Deployment: one VM, socat per challenge. Cannot use Cloud Run (no raw TCP).

## 3. Remaining static — needs domain / external — 2

| # | Title | Cat | Pts | Blocker |
|---|---|---|---|---|
| 50 | Time Traveller | OSINT | 100 | needs external mirror with rewritten history |
| 52 | The Lost Year | OSINT | 100 | needs `1337.excelmec.org` DNS record |

Deployment: Cloudflare Pages (same as 05/48/51) once the domain/mirror is ready.

---

## Already deployed (for reference)

- **33 handouts** — in the CyberQuest database, scheduled Oct 2–5.
- **05 Left in the Build** — https://theordinarywire.pages.dev
- **48 Office Map** — https://ordinary-engineering.pages.dev
- **51 Share Card** — https://the-ordinary-wire.pages.dev

## Total pending

| Group | Count |
|---|---|
| Web / app | 9 |
| NC | 3 |
| Static (domain/mirror) | 2 |
| **Total** | **14** |
