# CTF Challenge Index — Excel 2026

56 challenge directories live in the tree. 6 are cut (`06`, `07`, `14`, `19`,
`24`, `41` — see `CUTLIST.md`); the remaining **50 are the event set, all
built and released**. There is no `49` in the tree.

## Scoring rules

- **Base points** are the source of truth in each challenge's `README.md` (Base Points) and mirror in its `meta.yaml` (`points`).
- **Difficulty** is derived from base points only:
  - `<= 200` → `easy`
  - `<= 350` → `medium`
  - `<= 500` → `hard`
- **First-blood bonus** (Submit Order Bonus in each README) is awarded on `medium` and `hard` challenges only. Easy challenges pay `[]`.
  - Rationale: a first blood on a low-value challenge is nearly worthless to a team and mostly rewards whoever solved the warm-up first. The bonus is reserved for the solves that are actually contested.
  - Where awarded, it is relative to base points: 1st solve gets 10%, 2nd gets 7%, 3rd gets 5%, each rounded half-up to the nearest multiple of 5 (minimum 5). Example: a 300-point challenge pays `[30, 20, 15]`, a 250-point challenge pays `[25, 20, 15]`.
  - This follows the 2025 convention, where the bonus was opt-in and concentrated on the harder tiers (0/5 very-easy, 1/11 easy, 4/8 medium, 2/2 hard). We kept the 2025 *eligibility* rule but replaced the hand-picked 2025 amounts with a formula.
- Total available points across the 50 live challenges: **11400** base. The 30 easy challenges pay no bonus.
- One exception to the bonus rule: `11` Trust Fall is medium (300) but pays no bonus — `[]` in the board, the challenge README and the meta.

`06`, `07`, `14`, `19`, `24` and `41` are cut (1550 points freed). `56` (500)
and `57` (400) return `06`/`07`'s points in full; the other four cuts are
covered by the 50+ slots (`50`, `51`, `53`, `54`, `58`) — see `CUTLIST.md`
for the full arithmetic.

## Hosting / deployment

- **app** — hosted web service the player connects to over HTTP. 6 deployments serve 9 challenges: `01` (store), `02` (poster-gen, also serves `03` + `04`), `08` (open-door), `09` (dino kiosk, also serves `10`), `56` (procurement desk), `57` (interop bridge, port 8055). `06`'s deployment is retired — it existed to host `07`, which is cut.
- **nc** — TCP service, one container each: `12` (port 1337), `13` (1338), `15` (1340). `14` is cut, so port 1339 is retired.
- **static** — no backend; open in a browser: `05` (news site build), `48` (HQ map page), `50` (waitlist site plus its ghost-history mirror), `51` (continuity note plus its share card).
- **handout** — download the files, solve offline, no server: everything else (32 challenges: `11`, `16`, all of live Cryptography / Reversing / Forensic, live Steganography except `54`, and Misc `43`–`47`). `52` is a static bundle.

Runtime footprint: 6 app processes + 3 nc listeners + 4 static pages; the remaining 32 challenges need no hosting at all.

## WebExploitation — 3250 pts (06 and 07 cut, superseded by 56/57)

| #   | Challenge         | Difficulty | Base | 1st | 2nd | 3rd | Hosting           | Exploit                         |
| --- | ----------------- | ---------- | ---- | --- | --- | --- | ----------------- | ------------------------------- |
| 01  | Buy One Get One   | easy       | 200  |  [] |  [] |  [] | app               | double refund via race          |
| 02  | Negative Space    | easy       | 100  |  [] |  [] |  [] | app (hosts 02–04) | fetch negative index poster     |
| 03  | Second Guess      | medium     | 300  | 30  | 20  | 15  | app (via 02)      | predict UUIDv1 from boot time   |
| 04  | Rewind            | hard       | 500  | 50  | 35  | 25  | app (via 02)      | rewind PRNG state backwards     |
| 05  | Left in the Build | medium     | 300  | 30  | 20  | 15  | static            | reassemble keys from sourcemaps |
| 08  | AI-Powered        | medium     | 300  | 30  | 20  | 15  | app               | quote exact ritual phrase       |
| 09  | dino              | easy       | 100  |  [] |  [] |  [] | app (hosts 09–10) | forge signed score client-side  |
| 10  | dino rev 2        | hard       | 400  | 40  | 30  | 20  | app (via 09)      | fake score after inspection     |
| ~~06~~ | ~~Promotion Letter~~ | — | — | — | — | — | **cut** — superseded by 56; retained in tree |
| ~~07~~ | ~~Clock Puncher~~ | — | — | — | — | — | **cut** — timing attack not survivable over a real network path; replaced by 57 |
| 51  | Share Card        | easy       | 150  |  [] |  [] |  []  | static            | read the flag in an SVG `<desc>`; paper redesign |
| 56  | Standing Order    | hard       | 500  | 50  | 35  | 25  | app               | prototype pollution via batch desync |
| 57  | Coming of Age      | hard       | 400  | 40  | 30  | 20  | app               | UA gate, XML export, unowned idempotency cache, ops token |

## BinaryExp (11–16) — 1500 pts (14 cut: same exploit shape as 13)

| #   | Challenge           | Difficulty | Base | 1st | 2nd | 3rd | Hosting  | Exploit                       |
| --- | ------------------- | ---------- | ---- | --- | --- | --- | -------- | ----------------------------- |
| 11  | Trust Fall          | medium     | 300  |  [] |  [] |  [] | handout  | self-compile to fixed point   |
| 12  | Optimized Away      | medium     | 300  | 30  | 20  | 15  | nc :1337 | overflow both builds once     |
| 13  | Legacy Vault        | easy       | 200  |  [] |  [] |  [] | nc :1338 | partial overwrite, guess ASLR |
| ~~14~~ | ~~Safe Vault~~   | —          | —    | —   | —   | —   | **cut** — same function-pointer redirect as 13; retained in tree |
| 15  | Lost in Translation | hard       | 400  | 40  | 30  | 20  | nc :1340 | hide Brainfuck inside C       |
| 16  | Break Glass         | medium     | 300  | 30  | 20  | 15  | handout  | patch running binary live     |

## Cryptography (17–25, 58) — 1450 pts (19 and 24 cut: duplicates of 21 and 17)

| #   | Challenge               | Difficulty | Base | 1st | 2nd | 3rd | Hosting | Exploit                            |
| --- | ----------------------- | ---------- | ---- | --- | --- | --- | ------- | ---------------------------------- |
| 17  | Hash Slinging           | easy       | 150  |  [] |  [] |  [] | handout | crack hashes, reuse password       |
| 18  | Onion Pattern           | easy       | 200  |  [] |  [] |  [] | handout | peel nested encoded layers         |
| ~~19~~ | ~~Et Tu, Brute?~~    | —          | —    | —   | —   | —   | **cut** — same crib-drag as 21; retained in tree |
| 20  | Single Use              | easy       | 100  |  [] |  [] |  [] | handout | reuse draft as pad                 |
| 21  | Emojinated              | medium     | 350  | 35  | 25  | 20  | handout | substitute emoji for code          |
| 22  | Required Reading        | easy       | 100  |  [] |  [] |  [] | handout | index handbook by offsets          |
| 23  | Clock Skew              | easy       | 200  |  [] |  [] |  [] | handout | brute-force rotating door code     |
| ~~24~~ | ~~Complexity Requirements~~ | —     | —    | —   | —   | —   | **cut** — verbatim clone of 17; retained in tree |
| 25  | Gridlock                | easy       | 150  |  [] |  [] |  [] | handout | ECB leaks logo shapes              |
| 58  | Eigenface               | easy       | 200  |  [] |  [] |  [] | handout | recover face from eigenface dump   |

## Reversing (26–30) — 1050 pts

| #   | Challenge        | Difficulty | Base | 1st | 2nd | 3rd | Hosting | Exploit                           |
| --- | ---------------- | ---------- | ---- | --- | --- | --- | ------- | --------------------------------- |
| 26  | Scheme of Things | hard       | 400  | 40  | 30  | 20  | handout | solve chained grammar constraints |
| 27  | Fine Print       | easy       | 100  |  [] |  [] |  [] | handout | XOR hidden string fragments       |
| 28  | Print Gallery    | medium     | 350  | 35  | 25  | 20  | handout | uncurl image, read LSB            |
| 29  | Invisible Ink    | easy       | 100  |  [] |  [] |  [] | handout | read hidden whitespace bits       |
| 30  | Uglified         | easy       | 100  |  [] |  [] |  [] | handout | invert obfuscated receipt check   |

## Forensic (31–37, 53) — 1400 pts

| #   | Challenge                   | Difficulty | Base | 1st | 2nd | 3rd | Hosting | Exploit                           |
| --- | --------------------------- | ---------- | ---- | --- | --- | --- | ------- | --------------------------------- |
| 31  | Unsaved Changes             | easy       | 150  |  [] |  [] |  [] | handout | replay editor undo history        |
| 32  | Dig Site                    | medium     | 350  | 35  | 25  | 20  | handout | revive orphaned git objects       |
| 33  | Packet Loss                 | easy       | 150  |  [] |  [] |  [] | handout | reassemble DNS TXT exfiltration   |
| 34  | Core Values                 | medium     | 250  | 25  | 20  | 15  | handout | reorder scattered heap records    |
| 35  | Q3 Numbers                  | easy       | 100  |  [] |  [] |  [] | handout | unhide concealed workbook sheet   |
| 36  | Incognito                   | easy       | 200  |  [] |  [] |  [] | handout | carve deleted browser history     |
| 37  | The Corridor That Remembers | easy       | 100  |  [] |  [] |  [] | handout | distrust filenames, inspect files |
| 53  | Payroll Photo               | easy       | 100  |  [] |  [] |  [] | handout | read the metadata, not the pixels |

## Steganography (38–42, 54) — 1500 pts (41 cut: same bit-per-table shape as 38)

| #   | Challenge   | Difficulty | Base | 1st | 2nd | 3rd | Hosting | Exploit                     |
| --- | ----------- | ---------- | ---- | --- | --- | --- | ------- | --------------------------- |
| 38  | Posterized  | medium     | 300  | 30  | 20  | 15  | handout | read palette order bits     |
| 39  | B-Side      | easy       | 200  |  [] |  [] |  [] | handout | sample audio zero crossings |
| 40  | Style Guide | medium     | 300  | 30  | 20  | 15  | handout | read PDF half-point shifts  |
| ~~41~~ | ~~Tracking~~ | —       | —    | —   | —   | —   | **cut** — same bit-per-table read as 38; retained in tree |
| 42  | Storyboard  | hard       | 500  | 50  | 35  | 25  | handout | diff video frames to QR     |
| 54  | Lobby Intercom | easy    | 200  |  [] |  [] |  [] | handout | read the flag off the spectrogram |

## Misc (43–48) — 900 pts

| #   | Challenge          | Difficulty | Base | 1st | 2nd | 3rd | Hosting | Exploit                      |
| --- | ------------------ | ---------- | ---- | --- | --- | --- | ------- | ---------------------------- |
| 43  | Ghost Glyphs       | easy       | 100  |  [] |  [] |  [] | handout | reorder SVG glyph rows       |
| 44  | Off Key            | easy       | 200  |  [] |  [] |  [] | handout | decode layouts, diff lyrics  |
| 45  | QRious             | easy       | 200  |  [] |  [] |  [] | handout | XOR image subsets to QR      |
| 46  | Nothing to Declare | easy       | 200  |  [] |  [] |  [] | handout | unzip image, decrypt row     |
| 47  | No Refunds         | easy       | 100  |  [] |  [] |  [] | handout | rotate receipt, scan barcode |
| 48  | Office Map         | easy       | 100  |  [] |  [] |  [] | static  | walk every room once         |

## OSINT (50, 52) — 350 pts

| #   | Challenge    | Difficulty | Base | 1st | 2nd | 3rd | Hosting | Exploit                                  |
| --- | ------------ | ---------- | ---- | --- | --- | --- | ------- | ---------------------------------------- |
| 50  | Early Access | medium     | 250  | 25  | 20  | 15  | static  | waitlist form plus ghost-history mirror  |
| 52  | The Lost Year | easy      | 100  |  [] |  [] |  [] | static  | rebuild the missing year from archives |

## Difficulty spread (live set)

| Difficulty | Count | First-blood bonus | Challenges |
|---|---|---|---|
| easy | 30 | none | 01, 02, 09, 13, 17, 18, 20, 22, 23, 25, 27, 29, 30, 31, 33, 35, 36, 37, 39, 43, 44, 45, 46, 47, 48, 51, 52, 53, 54, 58 |
| medium | 13 | 10 / 7 / 5 %, except 11 | 03, 05, 08, 11, 12, 16, 21, 28, 32, 34, 38, 40, 50 |
| hard | 7 | 10 / 7 / 5 % | 04, 10, 15, 26, 42, 56, 57 |

`11` Trust Fall is the exception: medium on points (300) but pays no bonus.
Difficulty is otherwise derived from base points alone: `<= 200` easy,
`<= 350` medium, `<= 500` hard. No challenge is `very-easy` — the lowest base
value in the event is 100.
