# PROGRESS — multiverse CTF 2026

Tracking per CTF_PLAN.md §11 (50 slots). One row per challenge.

| # | Cat | Name | Slug | Diff | Tier | Status |
|---|-----|------|------|------|------|--------|
| 01 | Web | Buy One Get One | buy_one_get_one | medium | H3 | **done** (refund-race storefront; 400 ms race window, validated checkout, decoys sealed; verified: full browser E2E + `deno run -A admin/verify.ts`) |
| 02 | Web | Negative Space | negative_space | easy | H3 | **built** (shared poster-gen deployment, rev 1; verify: `admin/verify.sh`) |
| 03 | Web | Second Guess | second_guess | medium | H3 | **built** (shared poster-gen deployment, rev 2; verify: `admin/verify.sh`) |
| 04 | Web | Rewind | rewind | hard | H3 | **built** (shared poster-gen deployment, rev 3; verify: `admin/verify.sh`) |
| 05 | Web | Left in the Build | left_in_the_build | medium | H3 | todo |
| 06 | Web | Promotion Letter | promotion_letter | easy-medium | H3 | todo |
| 07 | Web | Clock Puncher | clock_puncher | hard | H3 | todo |
| 08 | Web | AI-Powered | ai_powered | easy-medium | H3 | **built** (single deno binary `open-door`; markdown-render XSS in the ghostwrite reply → memo-113 receipt → standing order + CEO sign-off) |
| 09 | Web | dino | dino | easy-medium | H3 | **built** (lobby kiosk runner; client-side HMAC run signing — beat the seeded 94187 record with a forged signed POST → flag; in-memory best-run board; verify: `python3 admin/solve_dino.py http://<host>:8034`) |
| 10 | Web | Cache Money | cache_money | medium | H3 | todo |
| 11–16 | Bin | Trust Fall … Comeback | — | — | H2 | todo |
| 17–26 | Crypto | Hash Slinging … Required Reading | — | — | H0 | todo |
| 27–30 | Rev | Fine Print … Uglified | — | — | H0 | todo |
| 31–36 | Forensic | Unsaved Changes … Incognito | — | — | H0 | todo |
| 37–42 | Stego | Pencil Test … Storyboard | — | — | H0 | todo |
| 43–48 | Misc | Lobby Cabinet … Office Map | — | — | mixed | todo |
| 49–50 | OSINT | Personnel File, Field Trip | — | — | H0+H1 | todo |
