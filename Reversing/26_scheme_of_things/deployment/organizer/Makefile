CC ?= gcc
CFLAGS ?= -std=c11 -O1 -fno-inline -fno-ident -Wall -Wextra
all: evaluator
evaluator: challenge.c
	$(CC) $(CFLAGS) challenge.c -o evaluator
strip:
	strip evaluator
clean:
	rm -f evaluator
