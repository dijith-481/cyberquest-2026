"""Minimal socat stand-in for verify.sh on hosts without socat.

Listens on 127.0.0.1:<port> and forks one <chall> per connection,
with flag.txt resolved from the child's working directory.
"""
import os
import socket
import subprocess
import sys

port, chall = int(sys.argv[1]), sys.argv[2]
srv = socket.socket()
srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
srv.bind(("127.0.0.1", port))
srv.listen(8)
while True:
    conn, _ = srv.accept()
    if os.fork() == 0:
        srv.close()
        subprocess.run([chall], stdin=conn.fileno(),
                       stdout=conn.fileno())
        conn.close()
        raise SystemExit
    conn.close()
