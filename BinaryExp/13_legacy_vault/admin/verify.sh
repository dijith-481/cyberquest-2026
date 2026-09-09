#!/bin/sh
# verifies the full solve against a locally hosted vault.
# usage: sh admin/verify.sh
set -eu

cd "$(dirname "$0")/.."
PORT="${VERIFY_PORT:-13380}"
WORK="$(mktemp -d)"
SOCAT=""
trap 'kill $SOCAT 2>/dev/null; rm -rf "$WORK"' EXIT

if command -v make >/dev/null 2>&1; then
    (cd deployment && make build)
else
    gcc -O2 -fPIE -pie -fstack-protector-strong -o deployment/vuln/vault deployment/vuln/vault.c
fi
cp deployment/vuln/vault "$WORK/vault"
for FROZEN in deployment/vuln/vault handout/vault; do
    if ! cmp -s deployment/vuln/vault "$FROZEN"; then
        echo "FAIL: $FROZEN differs from a fresh build -- re-freeze it"
        exit 1
    fi
done
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
