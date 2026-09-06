#!/usr/bin/env bash
# packet_loss — verify the challenge is solvable end to end.
# Regenerates the handout deterministically, runs the reference solve
# against a fresh copy, and checks the recovered flag.
set -euo pipefail
cd "$(dirname "$0")/.."

EXPECTED='cyber_quest{dn5_3xf1l_r34ds_l1k3_h4rm0n_l3tt3rs_2c9a71}'

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

python3 deployment/make_handout.py >/dev/null
cp handout/office_capture_0318.pcap "$TMP/"

OUT="$(python3 admin/solve.py "$TMP/office_capture_0318.pcap")"
echo "$OUT"

if echo "$OUT" | grep -q "$EXPECTED"; then
  echo "VERIFY OK — flag recovered from a fresh handout"
else
  echo "VERIFY FAILED — expected $EXPECTED" >&2
  exit 1
fi
