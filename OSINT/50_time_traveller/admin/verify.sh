#!/usr/bin/env bash
# Time Traveller — offline and live verifier.
#   bash admin/verify.sh
#   GH_USER=... GH_REPO=... GHOST_SHA=... bash admin/verify.sh --live
set -euo pipefail

CHALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SITE="$CHALL_DIR/deployment/index.html"
GH_USER="${GH_USER:-oe-mira-doodle-0417}"
GH_REPO="${GH_REPO:-book-haven}"
FLAG="${FLAG:-cyber_quest{t1m3_tr4v3ll3r_r3v1v3d_9e4c7a}}"
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

# The visible page is the 2025 Book Haven page, with only a source breadcrumb
# added. These checks catch accidental redesigns while ignoring the CDN.
grep -Fq "Book Haven Book Shop" "$SITE" || fail "Book Haven heading missing"
grep -Fq "The Time Traveler's Library" "$SITE" || fail "time-traveler book missing"
grep -Fq "1984" "$SITE" || fail "1984 card missing"
grep -Fq "Pride and Prejudice" "$SITE" || fail "Pride and Prejudice card missing"
grep -Fq "cdn.jsdelivr.net/npm/tailwindcss@2.2.19" "$SITE" || fail "2025 Tailwind page marker missing"
pass "2025 Book Haven website preserved"

# The deployed site must be clean. The flag belongs only in the ghost mirror
# commit, not in the handout or any currently served file.
if grep -R -Fq "$FLAG" "$CHALL_DIR/deployment"; then
  fail "flag leaks into deployment/"
fi
if grep -R -Eiq 'cyber_?quest\{' "$CHALL_DIR/deployment"; then
  fail "a flag pattern leaks into deployment/"
fi
pass "no flag in the deployed site"

# The source breadcrumb must agree with the mirror the organizer publishes.
grep -Fq "github.com/${GH_USER}/${GH_REPO}" "$SITE" \
  || fail "GitHub mirror breadcrumb does not match GH_USER/GH_REPO"
pass "mirror breadcrumb agrees with ${GH_USER}/${GH_REPO}"

# Rehearse the complete force-push sequence locally. This catches the common
# mistake of leaving the ghost commit reachable from main.
LOCAL_OUT="$(bash "$CHALL_DIR/admin/setup_github.sh" --local-only)"
grep -Fq "LOCAL-ONLY OK" <<<"$LOCAL_OUT" || fail "local force-push rehearsal failed"
grep -Fq "force-push:" <<<"$LOCAL_OUT" || fail "setup did not report a force-push"
pass "force-push mechanic simulated locally"

if [[ "$LIVE" == 1 ]]; then
  command -v curl >/dev/null || fail "curl is required for --live"
  EVENTS="$(curl -fsSL --max-time 30 "https://api.github.com/users/${GH_USER}/events/public?per_page=100" || true)"
  [ -n "$EVENTS" ] || fail "GitHub events API is unreachable"
  grep -Fq "\"name\":\"${GH_REPO}\"" <<<"$EVENTS" \
    || fail "no recent PushEvent for ${GH_USER}/${GH_REPO}"
  pass "live activity contains a push for ${GH_USER}/${GH_REPO}"

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
