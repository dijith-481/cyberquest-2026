# Rebuild the deployment binary from source.
#
# NOTE: the challenge ships the FROZEN binary in vuln/vault (and the same
# file in handout/). The exploit is a property of this exact build:
# PIE + stack protector, symbols kept. denied and print_flag share a
# page (page offsets 0x300 / 0x1e0), which is what the partial-overwrite
# solve relies on. If you rebuild with a different toolchain, re-check
# `nm vault` and update ../admin/solution.md accordingly.

build:
	gcc -O2 -fPIE -pie -fstack-protector-strong -o vuln/vault vuln/vault.c

clean:
	rm -f vuln/vault
