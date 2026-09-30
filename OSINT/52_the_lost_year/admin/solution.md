# The Lost Year — solution

**Flag:** `cyber_quest{ye_olde_leetspeak}`

**Category:** OSINT
**Difficulty:** easy
**Theme:** Excel's yearly subdomain convention, and the year the ledger skipped

The challenge is one clean aha-moment, not a chain. The player must connect
three widely known facts and one festival fact:

```text
"the truly elite"  →  leet  →  1337
EXCEL's yearly archive pages:  YEAR.excelmec.org
     →  1337.excelmec.org
          →  "The Grand Elite Tournament"
               →  /competitions/grand-elite-tournament/
                    →  Champion's Inscription
                         →  cyber_quest{ye_olde_leetspeak}
```

## Walkthrough

### 1. Read the description as a year problem

The handout says the archives go "further than anyone remembers" and that one
year is "reserved for the truly elite". The word **elite** is the intended
pivot: elite → leet → **1337**.

### 2. Confirm the yearly convention

Excel's real archive sites live at `YEAR.excelmec.org`
(`2017` … `2025`). The 2025 site's Legacy Archive lists them explicitly. The
convention is public; nothing about it is hidden.

### 3. Visit the forgotten year

The number from step 1 slots directly into the convention from step 2:

```text
1337.excelmec.org
```

The site is a full, working "medieval edition" of the fest — blackletter
headings, a schedule, guilds, and an archives page that (in character)
prophesies the years 2017–2025.

### 4. Click the tournament

The home page carries one reserved card:

```text
THE GRAND ELITE TOURNAMENT
Only the finest engineers of the kingdom may enter.
Reserved since the founding of the realm for those who
prove themselves 1337.
[ View Results → ]
```

### 5. Take the inscription

The results page (`/competitions/grand-elite-tournament/`) ends with the
**Champion's Inscription**, where the flag is printed plainly:

```text
cyber_quest{ye_olde_leetspeak}
```

There is no source-diving, no header, no robots.txt, no hash. The site is
honest; finding it was the challenge.

## Why the site can be trusted by players

- The site looks like a contemporary member of the `*.excelmec.org` family:
  same subdomain convention, same fest voice (Model Engineering College,
  Kochi), real prior years linked in its archives.
- The absurdity is self-aware ("Since before Excel remembered") so it reads
  as intentional fest lore, not a phishing page.

## Organizer setup

Deploy `deployment/` as the entire origin of `1337.excelmec.org`:

1. Provision `1337.excelmec.org` in DNS (A/CNAME) and a certificate covering
   it (wildcard `*.excelmec.org` or a per-host SAN).
2. Serve the folder at the domain root. Do **not** link it from any other
   Excel page — discoverability is the challenge.
3. Confirm from a clean browser:
   - `https://1337.excelmec.org/` renders the parchment landing page.
   - `https://1337.excelmec.org/competitions/grand-elite-tournament/`
     shows the Champion's Inscription with the flag.
4. `bash admin/setup_external.sh --check` re-checks both live pages.

Because `excelmec.org` is the fest's own domain, no third-party identity or
registration data is involved.

## Anti-shortcut and stability notes

- The flag appears **exactly once** in `deployment/` — on the Grand Elite
  Tournament page only. `admin/verify.sh` enforces this.
- The landing page only *teases* the tournament; it never prints the flag.
- No breadcrumbs in `robots.txt`, headers, image alt text, or the 404 page.
- The archives page on the 1337 site links the real years `2017`–`2025`
  out-of-character anchor text is avoided: everything is written in the
  site's in-world voice so the page never breaks character and never spells
  out the pivot.
- If the live host changes, keep the tournament URL as
  `/competitions/grand-elite-tournament/`; the handout and solution assume it.

## Verify

```bash
bash admin/verify.sh
```
