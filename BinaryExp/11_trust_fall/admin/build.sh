#!/usr/bin/env bash
# Trust Fall — build the generation-0 trusting compiler binary.
#
# handout/tcc.c carries the trusting-trust machinery: when it recognizes its
# own source (hash match), it re-emits the next generation (bumped version,
# carried random) into the output. The shipped binary is generation 0 with
# a baked self-hash and a baked random seed target.
set -euo pipefail
cd "$(dirname "$0")"

SRC=../handout/tcc.c

# 1. bootstrap snapshot (source ships clean: gv=0, rv=0, ow=0)
cp "$SRC" _boot.c

# 2. bake a build-time random seed target (persisted for reproducible rebuilds)
if [ -f .seedr ]; then
  SEEDR=$(cat .seedr)
else
  SEEDR=$(python3 -c 'import random;print(hex(random.getrandbits(31)))')
  echo "$SEEDR" > .seedr
fi
echo "[*] seed target SEEDR=$SEEDR"
sed -i "s/static unsigned rv = 0;/static unsigned rv = ${SEEDR};/" _boot.c

# 3. compute the self-hash constants over the pristine source (the values
#    the shipped binary will use when recognizing its own source).
read -r OWNV OWN_OFF < <(python3 - "$SRC" <<'PY'
import re,sys
src=open(sys.argv[1],'rb').read()
m=re.search(rb'ow = 0x[0-9a-fA-F]{16}', src)
off=m.start()+len(b'ow = 0x')
h=0x243F6A8885A308D3
for i,b in enumerate(src):
    if off<=i<off+16: continue
    h=((h^(b&255))*0x100000001B3)&0xFFFFFFFFFFFFFFFF
    h ^= h>>17
    h &= 0xFFFFFFFFFFFFFFFF
print(f"0x{h:016x} {off}")
PY
)
echo "[*] self-hash OWNV=$OWNV OWN_OFF=$OWN_OFF"

# 4. bake the constants into the snapshot
sed -i "s/static unsigned long ow = 0x0000000000000000UL;/static unsigned long ow = ${OWNV}UL;/; s/static int oo = 0;/static int oo = $OWN_OFF;/" _boot.c

# 5. compile the generation-0 compiler, optimized, stripped of symbols
gcc -O2 -o "../handout/tcc" _boot.c
strip --strip-all "../handout/tcc" 2>/dev/null || true
chmod 755 ../handout/tcc

# 6. sanity: gen0 compiles flag.c (random looking) and self-compiles with
#    generation + random propagation into the output assembly
"../handout/tcc" ../handout/flag.c >/dev/null 2>&1
./a.out
"../handout/tcc" "$SRC" >/dev/null 2>&1
if grep -q '^gv:$' a.s && grep -A1 '^gv:$' a.s | grep -q '\.long 1'; then
  echo "[ok] self-compilation propagates next generation (gv=1)"
else
  echo "ERROR: generation propagation missing" >&2
  exit 1
fi
RDEC=$(python3 -c "print(int('$SEEDR',16))")
if grep -A1 '^rv:$' a.s | grep -q "$RDEC"; then
  echo "[ok] self-compilation carries the random ($SEEDR)"
else
  echo "ERROR: random propagation missing" >&2
  exit 1
fi
rm -f _boot.c a.out a.s
echo "[ok] generation-0 compiler ready"
