#!/bin/sh
# verifies the full two-stage solve against a locally hosted gate.
# usage: sh admin/verify.sh
set -eu

cd "$(dirname "$0")/.."
PORT="${VERIFY_PORT:-13400}"
WORK="$(mktemp -d)"
trap 'kill $SOCAT 2>/dev/null; rm -rf "$WORK"' EXIT

if command -v make >/dev/null 2>&1; then
    (cd deployment && make build)
else
    # fallback must match the Makefile recipe exactly (incl. -s)
    gcc -O2 -Wall -Wextra -s -o deployment/vuln/chall deployment/vuln/chall.c
fi
cp deployment/vuln/chall "$WORK/chall"
# guard: the frozen copies must match a fresh build from source.
# rebuilds here are reproducible, so any mismatch means someone edited
# chall.c without re-freezing (see NOTES.md).
for FROZEN in deployment/vuln/chall handout/chall; do
    if ! cmp -s deployment/vuln/chall "$FROZEN"; then
        echo "FAIL: $FROZEN differs from a fresh build -- re-freeze it"
        exit 1
    fi
done
grep -o 'cyber_quest{[^}]*}' deployment/Dockerfile > "$WORK/flag.txt"

# the gate reads flag.txt next to itself, like it does under WORKDIR /vuln
if command -v socat >/dev/null 2>&1; then
    (cd "$WORK" && socat TCP-LISTEN:$PORT,reuseaddr,fork EXEC:"$WORK/chall") &
    SOCAT=$!
else
    (cd "$WORK" && python3 "$OLDPWD/admin/serve.py" "$PORT" "$WORK/chall") &
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
