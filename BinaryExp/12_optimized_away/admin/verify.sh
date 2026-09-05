#!/bin/sh
# Optimized Away — verify the full solve against a locally hosted mirror.
# usage: sh admin/verify.sh
set -eu

cd "$(dirname "$0")/.."
PORT="${VERIFY_PORT:-13370}"
WORK="$(mktemp -d)"

# the deployment binaries are frozen; copy them out with a local flag file
cp deployment/vuln/ledgerd-prod deployment/vuln/ledgerd-compat \
   deployment/vuln/dispatcher "$WORK/"
chmod 755 "$WORK"/ledgerd-prod "$WORK"/ledgerd-compat "$WORK"/dispatcher
cp deployment/flag.txt "$WORK/"

if command -v socat >/dev/null 2>&1; then
    (cd "$WORK" && exec socat TCP-LISTEN:$PORT,reuseaddr,fork EXEC:"$WORK/dispatcher") &
    SOCAT=$!
else
    # no socat on this host -- a 15-line python stand-in with the same shape
    (cd "$WORK" && exec python3 - "$PORT" "$WORK/dispatcher" <<'PY' ) &
import os, socket, subprocess, sys
srv = socket.socket()
srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
srv.bind(("127.0.0.1", int(sys.argv[1])))
srv.listen(8)
while True:
    conn, _ = srv.accept()
    if (pid := os.fork()) == 0:
        srv.close()
        os.chdir(os.path.dirname(sys.argv[2]))
        subprocess.run([sys.argv[2]], stdin=conn.fileno(),
                       stdout=conn.fileno(), stderr=conn.fileno())
        conn.close()
        raise SystemExit
    conn.close()
PY
    SOCAT=$!
fi
trap 'kill $SOCAT 2>/dev/null; rm -rf "$WORK"' EXIT
sleep 0.5

WANT="$(cat deployment/flag.txt)"
GOT="$(python3 admin/solve.py 127.0.0.1 $PORT | grep -o 'cyber_quest{[^}]*}' | head -1)"

if [ "$GOT" != "$WANT" ]; then
    echo "FAIL: got '$GOT', want '$WANT'"
    exit 1
fi
echo "OK: $GOT"
