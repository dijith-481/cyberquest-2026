#!/bin/sh
# verifies the full solve against a locally hosted vault.
# usage: sh admin/verify.sh
set -eu

cd "$(dirname "$0")/.."
PORT="${VERIFY_PORT:-13390}"
WORK="$(mktemp -d)"
SOCAT=""
trap 'kill $SOCAT 2>/dev/null; rm -rf "$WORK"' EXIT

if command -v make >/dev/null 2>&1; then
    (cd deployment && make build)
else
    rustc -O -C strip=debuginfo --edition 2021 -o deployment/vuln/vault deployment/vuln/vault.rs
fi
cp deployment/vuln/vault "$WORK/vault"
# NOTE: no frozen-binary cmp check here (unlike slots 12/13): rustc
# embeds build hashes, so fresh builds are not byte-identical. The
# handout binary is refreshed from the same source on every verify.
cp deployment/vuln/vault handout/vault
cp deployment/vuln/vault.rs handout/vault.rs
grep -o 'cyber_quest{[^}]*}' deployment/Dockerfile > "$WORK/flag.txt"

if command -v socat >/dev/null 2>&1; then
    (cd "$WORK" && socat TCP-LISTEN:$PORT,reuseaddr,fork EXEC:"$WORK/vault") &
    SOCAT=$!
else
    (cd "$WORK" && python3 "$OLDPWD/admin/serve.py" "$PORT" "$WORK/vault") &
    SOCAT=$!
fi
sleep 0.5

GOT="$(python3 admin/solve.py 127.0.0.1 $PORT \
      | grep -o 'cyber_quest{[^}]*}')"
WANT="$(grep -o 'cyber_quest{[^}]*}' deployment/Dockerfile)"

if [ "$GOT" != "$WANT" ]; then
    echo "FAIL: got $GOT, want $WANT"
    exit 1
fi
echo "OK: $GOT"
