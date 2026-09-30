#!/usr/bin/env bash
# The Lost Year — external infrastructure checklist.
#
# The challenge site lives at the host below; nothing links to it. This
# script prints the organizer checklist and can re-check the live pages
# after deployment.
#
#   bash admin/setup_external.sh
#   HOST=1337.excelmec.org bash admin/setup_external.sh --check
set -euo pipefail

HOST="${HOST:-1337.excelmec.org}"
TOURNAMENT_URL="https://${HOST}/competitions/grand-elite-tournament/"
HOME_URL="https://${HOST}/"
DEFAULT_FLAG='cyber_quest{ye_olde_leetspeak}'
FLAG="${FLAG:-$DEFAULT_FLAG}"
CHECK=0

for arg in "$@"; do
  case "$arg" in
    --check) CHECK=1 ;;
    -h|--help)
      sed -n '2,12p' "$0"
      exit 0
      ;;
    *) echo "unknown option: $arg" >&2; exit 2 ;;
  esac
done

cat <<EOF
The Lost Year — organizer setup

Year hostname     : ${HOST}
Landing page      : ${HOME_URL}
Inscription page  : ${TOURNAMENT_URL}
Flag              : ${FLAG}

1. Provision ${HOST} in DNS (A or CNAME) for the fest origin.
2. Issue a certificate covering ${HOST} — wildcard *.excelmec.org or a
   per-host SAN. Do not ship the cert for other years.
3. Serve the challenge's deployment/ folder as the entire origin of the
   host. It must be the domain root; no path prefix.
4. Link NOTHING to ${HOST} from any other Excel page. Discoverability is
   the challenge: the player must invent elite -> leet -> the year
   themselves.
5. Test from a clean browser: the landing page shows the parchment hero,
   the "Grand Elite Tournament" card links to /competitions/grand-elite-tournament/
   and that page ends with the Champion's Inscription carrying the flag.
6. Optional cross-check: the real archives (2017–2025) and the main fest
   site must stay up and unchanged. They validate the player's pivot but
   are not ours to modify.
EOF

if [ "$CHECK" -eq 0 ]; then
  exit 0
fi

printf '\nChecking the live pages for %s...\n' "$HOST"
command -v curl >/dev/null 2>&1 || {
  echo "curl is required for --check" >&2
  exit 1
}

LH="$(curl -fsSL --max-time 30 "$HOME_URL" || true)"
[ -n "$LH" ] || { echo "landing page is unreachable: ${HOME_URL}" >&2; exit 1; }
case "$LH" in
  *'EXCEL 1337'*) ;;
  *) echo "landing page does not look like the 1337 site" >&2; exit 1 ;;
esac
case "$LH" in
  *'grand-elite-tournament'*) ;;
  *) echo "landing page does not tease the tournament" >&2; exit 1 ;;
esac
echo "landing page OK"

LT="$(curl -fsSL --max-time 30 "$TOURNAMENT_URL" || true)"
[ -n "$LT" ] || { echo "tournament page is unreachable: ${TOURNAMENT_URL}" >&2; exit 1; }
case "$LT" in
  *'Champion'*) ;;
  *) echo "tournament page missing the Champion's Inscription" >&2; exit 1 ;;
esac
case "$LT" in
  *"${FLAG}"*) ;;
  *) echo "tournament page does not carry the flag" >&2; exit 1 ;;
esac
echo "tournament page OK"
echo "EXTERNAL CHECK PASSED"
