intake -- internal wire

    nc <host> 1340

Intake takes one translation unit at a time. Paste the unit, terminate it
with a line that reads __END__.

The conformance sample attached here (sample.c) is shipped to vendors who
want to pre-check their units before submitting them. It is ordinary C
that compiles cleanly and returns a verdict code. Intake still turns it
away without explanation.

The intake binary itself (chall) is attached for vendors whose toolchains
need to match its behavior exactly.
