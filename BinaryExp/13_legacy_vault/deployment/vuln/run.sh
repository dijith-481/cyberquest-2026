#!/usr/bin/env bash
# vault-svc v1 listener -- one process per connection, unlimited players.
# docker: runs as /vuln/run.sh under WORKDIR /vuln (see ../Dockerfile).
# bare metal: copy deployment/ to the server and run ./vuln/run.sh here;
# needs only socat, the frozen binary, and flag.txt next to it.
cd "$(dirname "$0")"
socat TCP-LISTEN:1338,reuseaddr,fork EXEC:"./vault"
