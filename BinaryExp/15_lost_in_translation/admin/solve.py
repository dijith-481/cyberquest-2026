#!/usr/bin/env python3
"""lost_in_translation -- reference solve (stdlib only).

usage: python3 solve.py [host] [port]

The intake binary (handout/chall, stripped) was reversed to learn the
machine (see solution.md). Findings:

- intake strips C comments and string/char literals first, then keeps
  only +-<>[]., and runs them as Brainfuck. Smuggling the program in
  comments or strings is dead: it is removed before intake reads.
- per connection it stamps 16 nonzero bytes onto a zeroed store and
  accepts only a chained transform: out[0] is stamp[0] plus K, each
  further byte adds its stamp byte, K, and the previous answer.
- the stamp is fresh randomness per connection: nothing hardcoded.

So the forged unit weaves the 48-character program out of real C
operators -- two 18-term sums for the +17 runs, a float comparison
and a nested subscript for the loop bones:

    + x K . > [ < [->+<] > + x K . > ]

draining each previous answer into the next cell at runtime, inside
the only C the gate checks for: int main.
"""
import re
import socket
import sys
import time

K = 17  # recovered by reversing chall (ADD immediate in main)

NAMES = list("abcdefghijklmnopqr")  # 18 summands -> 17 pluses per sum

FORGE = """int main(void)
{
%s
    int v;
    int w;
    int *s;
    int *t;
    v = %s;
    w = 0.5;
    if (w > v)
        w = s[a < t[b-c>d+e<f] > w+%s+0.5 > w];
    return w;
}
""" % ("\n".join("    int %s = 1;" % n for n in NAMES),
       "+".join(NAMES),
       "+".join([n for n in NAMES if n <= "p"]))

END = b"__END__\n"


def main():
    host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 1340

    s = socket.create_connection((host, port), timeout=15)
    buf = b""
    s.sendall(FORGE.encode() + END)

    deadline = time.time() + 20
    while re.search(rb"cyber_quest\{[^}]+\}", buf) is None:
        if time.time() > deadline:
            raise TimeoutError("no flag; gate said:\n%s"
                               % buf[-2000:].decode("utf-8", "replace"))
        s.settimeout(max(0.2, deadline - time.time()))
        chunk = s.recv(4096)
        if not chunk:
            break
        buf += chunk
    print(re.search(rb"cyber_quest\{[^}]+\}", buf).group(0).decode())


if __name__ == "__main__":
    main()
