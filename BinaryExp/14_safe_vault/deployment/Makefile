# Rebuild the deployment binary from source.
#
# NOTE: the challenge ships the FROZEN binary in vuln/vault (and the same
# file in handout/). rustc layout decisions are part of the challenge:
# repr(u8) Text payload at struct+1 vs Callback fn at struct+8 (the
# label-offset-7 solve), and the print_flag-denied delta the solve
# derives with nm. ANY source change can reshuffle both — after
# rebuilding, re-derive the delta and re-run admin/verify.sh before
# redeploying (see ../admin/solution.md).

build:
	rustc -O -C strip=debuginfo --edition 2021 -o vuln/vault vuln/vault.rs

clean:
	rm -f vuln/vault
