# Break Glass — deterministic maintainer build.
#
# The player only receives handout/vault. Stage code is compiled separately,
# copied out of .text, XOR-encrypted, and embedded into the release together
# with the encrypted flag fragment.

ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/..)
.PHONY: all build freeze clean

all: build

build:
	bash "$(ROOT)/admin/build.sh"

freeze:
	bash "$(ROOT)/admin/build.sh" --freeze

clean:
	rm -rf "$(ROOT)/deployment/.build"
	rm -f "$(ROOT)/deployment/generated/stages.h" "$(ROOT)/deployment/generated/frag_arrays.h"
