#!/usr/bin/env bash
# intake listener -- one process per connection, unlimited players.
# docker: runs as /vuln/run.sh under WORKDIR /vuln (see ../Dockerfile).
# bare metal: copy deployment/ to the server and run ./vuln/run.sh here;
# needs only socat, the frozen binary, and flag.txt next to it.
#
# NOTE: no ,stderr on the EXEC address, on purpose. socat's stderr
# option dups the child's stderr onto its stdout -- i.e. onto the
# player socket. Without it the child's stderr inherits socat's, which
# is the server log. This gate's oracle is one silent bit; nothing
# except the protocol lines may ever reach the wire.
cd "$(dirname "$0")"
socat TCP-LISTEN:1340,reuseaddr,fork EXEC:"./chall"
