#!/usr/bin/env bash
# Early Access — offline and live verifier.
#   bash admin/verify.sh
#   GH_USER=... GH_REPO=... GHOST_SHA=... bash admin/verify.sh --live
set -euo pipefail

CHALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SITE="$CHALL_DIR/deployment/index.html"
GH_USER="${GH_USER:-aetheria-loml}"
GH_REPO="${GH_REPO:-orbit}"
FLAG="${FLAG:-cyber_quest{3v3ry_y0u_0n3_f33d_a4f2c1}}"
LIVE=0
for arg in "$@"; do
  case "$arg" in
    --live) LIVE=1 ;;
    *) echo "usage: $0 [--live]" >&2; exit 2 ;;
  esac
done

pass() { echo "PASS: $1"; }
fail() { echo "FAIL: $1" >&2; exit 1; }

[ -f "$SITE" ] || fail "deployment/index.html missing"
[ -f "$CHALL_DIR/README.md" ] || fail "README.md missing"
[ -f "$CHALL_DIR/meta.yaml" ] || fail "meta.yaml missing"
[ -f "$CHALL_DIR/admin/solution.md" ] || fail "admin/solution.md missing"
[ -x "$CHALL_DIR/admin/setup_github.sh" ] || fail "setup_github.sh is not executable"
pass "challenge packaging present"

# The visible page is the orbit waitlist site. These checks catch accidental
# redesigns while ignoring copy edits.
grep -Fq "Every you." "$SITE" || fail "orbit hero heading missing"
grep -Fq "Join the waitlist" "$SITE" || fail "waitlist CTA missing"
grep -Fq "assets/drawably/style.css" "$SITE" || fail "drawably stylesheet missing"
grep -Fq "assets/app.js" "$SITE" || fail "app.js wiring missing"
grep -Fq "TBA" "$SITE" || fail "TBA marker missing"
pass "orbit waitlist site preserved"

# No 2025 / Book Haven / time-travel leftovers.
if grep -R -Eiq '2025|book.?haven|time.?travell' "$CHALL_DIR/deployment" "$CHALL_DIR/README.md" "$CHALL_DIR/meta.yaml"; then
  fail "2025 / Book Haven / time-travel reference remains"
fi
pass "no legacy references"

# The deployed site must be clean. The flag belongs only in the ghost mirror
# commit, not in the handout or any currently served file.
if grep -R -Fq "$FLAG" "$CHALL_DIR/deployment"; then
  fail "flag leaks into deployment/"
fi
if grep -R -Eiq 'cyber_?quest\{' "$CHALL_DIR/deployment"; then
  fail "a flag pattern leaks into deployment/"
fi
pass "no flag in the deployed site"

# The contributor handle in the page metadata must agree with the mirror the
# organizer publishes. Decoys (archive link, footer source link, staging
# TODO) must not point at the real account.
grep -Fq "<meta name=\"author\" content=\"${GH_USER}\"" "$SITE" \
  || fail "page author meta does not match GH_USER"
grep -Fq "github.com/${GH_USER}/${GH_REPO}" "$CHALL_DIR/admin/solution.md" \
  || fail "solution does not document GH_USER/GH_REPO"
pass "author handle agrees with ${GH_USER}/${GH_REPO}"

# Rehearse the complete force-push sequence locally. This catches the common
# mistake of leaving the ghost commit reachable from main.
LOCAL_OUT="$(bash "$CHALL_DIR/admin/setup_github.sh" --local-only)"
grep -Fq "LOCAL-ONLY OK" <<<"$LOCAL_OUT" || fail "local force-push rehearsal failed"
grep -Fq "force-push:" <<<"$LOCAL_OUT" || fail "setup did not report a force-push"
grep -Fq "commit-count: 100" <<<"$LOCAL_OUT" || fail "local history is not 100 commits"
grep -Fq "lure-position: 40" <<<"$LOCAL_OUT" || fail "lure commit is not at position 40"
pass "force-push mechanic simulated locally"

if [[ "$LIVE" == 1 ]]; then
  command -v curl >/dev/null || fail "curl is required for --live"
  # The repo activity page embeds the force-push with full before/after SHAs.
  # (The API events feed lags on brand-new accounts; the activity page is the
  # reliable route and the one the solution teaches.)
  ACTIVITY="$(curl -fsSL --max-time 30 "https://github.com/${GH_USER}/${GH_REPO}/activity" || true)"
  [ -n "$ACTIVITY" ] || fail "repo activity page is unreachable"
  grep -Fq '"pushType":"force_push"' <<<"$ACTIVITY" \
    || fail "no force-push visible on the activity page"
  pass "live activity page shows the force-push for ${GH_USER}/${GH_REPO}"

  MAIN_HTML="$(curl -fsSL --max-time 30 "https://raw.githubusercontent.com/${GH_USER}/${GH_REPO}/main/index.html" || true)"
  [ -n "$MAIN_HTML" ] || fail "mirror main is not readable"
  if grep -Fq "$FLAG" <<<"$MAIN_HTML"; then
    fail "flag is visible in the live main branch"
  fi
  pass "live main branch is clean"

  if [[ -n "${GHOST_SHA:-}" ]]; then
    STATUS="$(curl -L -sS -o /dev/null -w '%{http_code}' --max-time 30 \
      "https://github.com/${GH_USER}/${GH_REPO}/commit/${GHOST_SHA}" || true)"
    case "$STATUS" in
      2*|3*) pass "live ghost commit is still addressable (${STATUS})" ;;
      *) fail "live ghost commit returned HTTP ${STATUS}" ;;
    esac
  else
    echo "NOTE: set GHOST_SHA to verify the direct commit URL as well"
  fi
fi

echo "ALL CHECKS PASSED"
