#!/usr/bin/env bash
# The Lost Year — packaging and placement verifier.
#   bash admin/verify.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
README="$ROOT/README.md"
DEPLOY="$ROOT/deployment"
FLAG="cyber_quest{ye_olde_leetspeak}"

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
require_file "$DEPLOY/guilds/index.html"
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

# Wording must not drift back to the invented-fantasy naming. The site's
# visual and ceremonial register (blackletter, parchment, the era names) is
# deliberate and must NOT be "fixed" — only these three naming choices are
# pinned.
for bad in 'Model Engineering Kingdom' 'Anno Domini' 'Excel MCCCXXXVII'; do
  if grep -R -F -q --exclude=FONTS.md --exclude=style.css -- "$bad" "$DEPLOY"; then
    fail "invented-fantasy naming crept back in: $bad"
  fi
done
pass "1337 site matches the challenge lore"

# The flag is printed plainly, but exactly once, and only on the
# tournament page.
COUNT="$(grep -R -F -o "$FLAG" "$DEPLOY" | wc -l)"
[ "$COUNT" -eq 1 ] || fail "flag appears $COUNT times in deployment/ (want exactly 1)"
pass "flag appears exactly once in deployment/"
grep -Fq "$FLAG" "$DEPLOY/competitions/grand-elite-tournament/index.html" \
  || fail "flag is not on the tournament page"
if grep -R -F -q "$FLAG" "$DEPLOY/index.html" "$DEPLOY/competitions/index.html" \
  "$DEPLOY/events/index.html" "$DEPLOY/workshops/index.html" \
  "$DEPLOY/schedule/index.html" "$DEPLOY/guilds/index.html" \
  "$DEPLOY/archives/index.html" "$DEPLOY/404.html" "$DEPLOY/assets/style.css"; then
  fail "flag leaked outside the tournament page"
fi
pass "flag is only on the tournament page"

# The solution must document the pivot honestly.
for step in 'elite' '1337.excelmec.org' 'grand-elite-tournament' 'cyber_quest{ye_olde_leetspeak}'; do
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
