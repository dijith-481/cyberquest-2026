#!/usr/bin/env bash
# Build Break Glass from its private source and generated material.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD="$ROOT/deployment/.build"
GENERATED="$ROOT/deployment/generated"
SRC="$ROOT/deployment/src"
TOOLS="$ROOT/deployment/tools"

CC="${CC:-gcc}"
OBJCOPY="${OBJCOPY:-objcopy}"
PYTHON="${PYTHON:-python3}"

rm -rf "$BUILD"
mkdir -p "$BUILD" "$GENERATED"

"$CC" -O0 -fno-pie -fno-stack-protector \
    -fno-asynchronous-unwind-tables -fno-unwind-tables \
    -c "$SRC/stage_a.c" -o "$BUILD/stage_a.o"
"$OBJCOPY" --only-section=.text -O binary \
    "$BUILD/stage_a.o" "$BUILD/stage_a.bin"

"$CC" -O0 -fno-pie -fno-stack-protector \
    -fno-asynchronous-unwind-tables -fno-unwind-tables \
    -c "$SRC/stage_c.c" -o "$BUILD/stage_c.o"
"$OBJCOPY" --only-section=.text -O binary \
    "$BUILD/stage_c.o" "$BUILD/stage_c.bin"

"$PYTHON" "$TOOLS/gen_stages.py" \
    --stage-a "$BUILD/stage_a.bin" \
    --stage-c "$BUILD/stage_c.bin" \
    --output "$GENERATED/stages.h"
"$PYTHON" "$TOOLS/gen_frag.py" \
    --output "$GENERATED/frag_arrays.h"

"$CC" -O0 -Wall -Wextra -Wpedantic -fno-pie -fno-stack-protector \
    -I"$GENERATED" "$SRC/main.c" \
    -no-pie -Wl,--build-id=none -Wl,-z,relro,-z,now -s \
    -o "$BUILD/vault"
chmod 755 "$BUILD/vault"

if [[ "${1:-}" == "--freeze" ]]; then
    cp "$BUILD/vault" "$ROOT/handout/vault"
    chmod 755 "$ROOT/handout/vault"
fi

echo "release: $BUILD/vault"
