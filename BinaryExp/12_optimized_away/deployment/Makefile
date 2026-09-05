# Rebuild the deployment binaries from source.
#
# NOTE: the challenge ships the FROZEN binaries in vuln/ (and the same
# files in handout/). The exploit offsets are a property of the exact
# toolchain they were built with — gcc 14.2, static:
#
#   compat (-O0): session.admin sits at tag + 120
#   prod   (-O3): session.admin sits at tag + 88
#
# A different gcc may lay the frames out differently — that IS the
# challenge. If you rebuild, re-measure before redeploying (see
# ../admin/solution.md for the measurement procedure).

build:
	gcc -O0 -static -s -o vuln/ledgerd-compat vuln/ledgerd.c
	gcc -O3 -static -s -o vuln/ledgerd-prod vuln/ledgerd.c
	gcc -O2 -static -s -o vuln/dispatcher vuln/dispatcher.c

clean:
	rm -f vuln/ledgerd-compat vuln/ledgerd-prod vuln/dispatcher
