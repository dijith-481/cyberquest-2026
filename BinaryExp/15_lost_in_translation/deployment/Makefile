# Rebuild the deployment binary from source.
#
# NOTE: the challenge ships the FROZEN binary in vuln/chall, stripped
# (`-s`). It is dynamically linked and needs glibc >= 2.34 on whatever
# runs it (debian trixie ships 2.41, so the Dockerfile path and any
# modern bare-metal host are fine). If your build toolchain has a static
# libc available, prefer: gcc -O2 -static -s -o vuln/chall vuln/chall.c

build:
	gcc -O2 -Wall -Wextra -s -o vuln/chall vuln/chall.c

clean:
	rm -f vuln/chall
