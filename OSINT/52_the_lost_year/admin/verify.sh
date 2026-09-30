#!/usr/bin/env bash
# The Lost Year — packaging and placement verifier.
#   bash admin/verify.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
README="$ROOT/README.md"
DEPLOY="$ROOT/deployment"
FLAG="cyber_quest{y3_0ld3_l33tsp34k}"

pass() { printf 'PASS: %s\n' "$1"; }
fail() { printf 'FAIL: %s\n' "$1" >&2; exit 1; }
require_file() { [ -f "$1" ] || fail "missing ${1#"$ROOT/"}"; }

require_file "$README"
require_file "$ROOT/meta.yaml"
require_file "$ROOT/admin/solution.md"
require_file "$ROOT/admin/hints.md"
require_file "$ROOT/admin/setup_external.sh"
require_file "$DEPLOY/index.html"
require_file "$DEPLOY/competitions/index.html"
require_file "$DEPLOY/competitions/grand-elite-tournament/index.html"
require_file "$DEPLOY/events/index.html"
require_file "$DEPLOY/workshops/index.html"
require_file "$DEPLOY/schedule/index.html"
require_file "$DEPLOY/departments/index.html"
require_file "$DEPLOY/archives/index.html"
require_file "$DEPLOY/404.html"
require_file "$DEPLOY/assets/style.css"
pass "challenge package is present"

grep -Fq 'id: "52"' "$ROOT/meta.yaml" || fail "metadata id is not 52"
grep -Fq 'title: The Lost Year' "$ROOT/meta.yaml" || fail "metadata title mismatch"
grep -Fq 'difficulty: "easy"' "$ROOT/meta.yaml" || fail "metadata difficulty mismatch"
grep -Fq 'points: 100' "$ROOT/meta.yaml" || fail "metadata points mismatch"
pass "metadata matches the easy challenge"

# Player-facing copy must tease the year without naming it or the host.
grep -Fq 'reserved for the truly elite' "$README" || fail "elite clue missing"
grep -Fq 'Flag format: cyber_quest{...}' "$README" || fail "flag format missing"
if grep -Fq '1337' "$README"; then
  fail "player README names the year"
fi
if grep -Fq 'excelmec.org' "$README"; then
  fail "player README names the fest host"
fi
pass "player copy keeps the pivot soft"

# The deployment must stay in character: 1337 is the edition, the real
# college is named, and the solve path is intact.
# Pinned to the <title>, not the whole file: "EXCEL 1337" also appears in the
# nav and footer, so a whole-file grep for the brand can never fail.
grep -Eq '<title>EXCEL 1337' "$DEPLOY/index.html" || fail "brand missing from the title"
grep -Fq '1337' "$DEPLOY/index.html" || fail "the year lore missing"
grep -Fq 'The Grand Elite Tournament' "$DEPLOY/index.html" || fail "tournament tease missing"
grep -Fq 'Model Engineering College, Kochi' "$DEPLOY/index.html" || fail "college identity missing"
grep -Fq 'excelmec.org' "$DEPLOY/archives/index.html" || fail "archive convention missing"
grep -Fq "Champion" "$DEPLOY/competitions/grand-elite-tournament/index.html" \
  || fail "champion's inscription missing"

# This is a real college fest that happens to claim the year 1337. The only
# thing wrong with it is the year. So no invented-medieval vocabulary may
# appear in the player-facing copy: no kingdom, realm, crown, guild, oracle,
# parchment-lore, or era names. The blackletter typeface, the parchment
# PALETTE and the sword cursor are a deliberate visual skin over that copy
# and are not policed here — style.css is excluded for that reason.
for bad in kingdom realm crown royal seal decree scrollkeep scriptorium \
           oracle trebuchet alchemist tierce vespers compline worshipful \
           'Anno Domini' MCCCXXXVII 'Forbidden Arts' 'Kingdom of' \
           'the King' 'peasant' 'knight' 'chivalry' ; do
  # Only VISIBLE copy is checked. `class="royal"` on the <footer> is a
  # presentational name that collides with the vocabulary but is never rendered
  # as text, so the tags are stripped before scanning. Without this the check
  # fires on our own class attribute and is useless.
  if grep -R -i -h --exclude=FONTS.md --exclude=style.css -- "$bad" "$DEPLOY" \
     | sed -e 's/<[^>]*>//g' | grep -F -i -q -- "$bad"; then
    fail "invented-medieval vocabulary crept back into the copy: $bad"
  fi
done

# ...and the real fest's own facts must be present, so the site stays
# recognisably Excel and not a generic fantasy.
#
# These are pinned to the HOMEPAGE, not scanned across deployment/. A
# site-wide grep passes as long as the fact survives on any single page, so it
# cannot tell "the homepage identifies the fest" from "some page somewhere
# mentions it" — which is the thing that actually matters, because the
# homepage is what a player lands on and skims.
for good in 'Model Engineering College, Kochi' 'techno-managerial' '2001' \
            'Reverse Coding' 'Hack For Tomorrow' 'Lumiere' \
            'INSPIRE | INNOVATE | ENGINEER' ; do
  grep -Fq -- "$good" "$DEPLOY/index.html" || fail "real fest fact missing from the homepage: $good"
done
pass "site is a real college fest; 1337 is the only thing wrong with it"

# The flag is printed plainly, but exactly once, and only on the
# tournament page.
COUNT="$(grep -R -F -o "$FLAG" "$DEPLOY" | wc -l)"
[ "$COUNT" -eq 1 ] || fail "flag appears $COUNT times in deployment/ (want exactly 1)"
pass "flag appears exactly once in deployment/"
grep -Fq "$FLAG" "$DEPLOY/competitions/grand-elite-tournament/index.html" \
  || fail "flag is not on the tournament page"
if grep -R -F -q "$FLAG" "$DEPLOY/index.html" "$DEPLOY/competitions/index.html" \
  "$DEPLOY/events/index.html" "$DEPLOY/workshops/index.html" \
  "$DEPLOY/schedule/index.html" "$DEPLOY/departments/index.html" \
  "$DEPLOY/archives/index.html" "$DEPLOY/404.html" "$DEPLOY/assets/style.css"; then
  fail "flag leaked outside the tournament page"
fi
pass "flag is only on the tournament page"

# House style: the flag body is leetspeak. This one was once "ye_olde_leetspeak",
# which spelled the joke out in plain English — 51 of the event's 61 flags are
# leet, and this was one of only two that were not.
#
# The optional trailing hex suffix is stripped FIRST. Without that, any flag
# with a suffix passes on the strength of its own hex digits alone, which is
# not what is being asserted: "ye_olde_leetspeak_9f3a1c4" is plain English
# wearing a leet costume and must not satisfy this.
BODY="${FLAG#cyber_quest{}"
BODY="${BODY%_*}"   # drop a trailing _hexsuffix if present
if ! printf '%s' "$BODY" | grep -Eq '[a-z][0-9]|[0-9][a-z]'; then
  fail "flag body is not in leetspeak: $FLAG"
fi
pass "flag body is leetspeak"

# The solution must document the pivot honestly.
for step in 'elite' '1337.excelmec.org' 'grand-elite-tournament' 'cyber_quest{y3_0ld3_l33tsp34k}'; do
  grep -Fq "$step" "$ROOT/admin/solution.md" || fail "solution pivot missing: $step"
done
grep -Fq 'no robots.txt' "$ROOT/admin/solution.md" || fail "no-crumbs promise missing"
pass "solution documents every step of the pivot"

grep -Fq '1337.excelmec.org' "$ROOT/admin/setup_external.sh" || fail "default host missing"
grep -Fq "$FLAG" "$ROOT/admin/setup_external.sh" || fail "external setup flag missing"
bash -n "$ROOT/admin/setup_external.sh"
bash -n "$ROOT/admin/verify.sh"
pass "shell scripts parse"

echo "ALL CHECKS PASSED"
