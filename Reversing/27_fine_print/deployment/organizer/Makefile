CC ?= gcc
CFLAGS ?= -O2 -Wall -Wextra
all: licenseguard
licenseguard: challenge.c
	$(CC) $(CFLAGS) challenge.c -o licenseguard
strip:
	strip licenseguard
clean:
	rm -f licenseguard
