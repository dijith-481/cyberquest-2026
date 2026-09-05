#!/bin/sh
# ordinary engineering — ledgerd reconciliation mirror (slot 12, port 1337)
# bare metal: copy this folder to the server and run ./run.sh
cd "$(dirname "$0")"
exec socat TCP-LISTEN:1337,reuseaddr,fork EXEC:"./vuln/dispatcher ./vuln"
