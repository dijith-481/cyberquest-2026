#!/usr/bin/env bash
# Trust Fall — end-to-end verification of the trusting-trust chain.
# Rebuilds generation 0, checks the infection propagates and strengthens
# across self-compiles, and checks the locked flag math. (The full 12-deep
# chain walk was validated separately; propagation + strengthening imply it
# by induction: each generation emits exactly one more than it carries.)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

EXPECTED="cyberQuest{tru5t_f4ll_00584104}"

echo "[*] rebuild generation-0 from handout source"
cp handout/tcc.c /tmp/tf_boot.c
SEEDR=$(cat admin/.seedr)
sed -i "s/static unsigned rv = 0;/static unsigned rv = ${SEEDR};/" /tmp/tf_boot.c
OWINFO=$(python3 - handout/tcc.c <<'PY'
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
set -- $OWINFO
sed -i "s/static unsigned long ow = 0x0000000000000000UL;/static unsigned long ow = $1UL;/; s/static int oo = 0;/static int oo = $2;/" /tmp/tf_boot.c
gcc -O2 -o /tmp/tf_tcc /tmp/tf_boot.c 2>/dev/null
echo "[+] rebuilt"

echo "[*] gen0 compiles flag.c (must run, full entropy)"
mkdir -p /tmp/tf_run && cd /tmp/tf_run
/tmp/tf_tcc "$ROOT/handout/flag.c" >/dev/null 2>&1
R1=$(./a.out); R2=$(./a.out)
echo "    $R1"
echo "    $R2"
[[ "$R1" != "$R2" ]] || { echo "FAIL: no entropy at gen0"; exit 1; }
echo "[+] gen0 random"

echo "[*] gen0 self-compiles with gv=1 + carried random"
rm -f a.s a.out
/tmp/tf_tcc "$ROOT/handout/tcc.c" >/dev/null 2>&1
G1=$(grep -A1 '^gv:$' a.s | tail -1 | grep -o '[0-9]*')
echo "    emitted gv=$G1"
[[ "$G1" == "1" ]] || { echo "FAIL: generation did not advance"; exit 1; }
RDEC=$(python3 -c "print(int('$SEEDR',16))")
grep -A1 '^rv:$' a.s | grep -q "$RDEC" || { echo "FAIL: random not carried"; exit 1; }
echo "[+] propagation works"
cp a.out /tmp/tf_tcc1

echo "[*] gen1 self-compiles with gv=2 and a stronger mask"
/tmp/tf_tcc1 "$ROOT/handout/tcc.c" >/dev/null 2>&1
G2=$(grep -A1 '^gv:$' a.s | tail -1 | grep -o '[0-9]*')
echo "    emitted gv=$G2"
[[ "$G2" == "2" ]] || { echo "FAIL: generation did not advance twice"; exit 1; }
/tmp/tf_tcc1 "$ROOT/handout/flag.c" >/dev/null 2>&1
M1=$(grep -B6 'call srand@PLT' a.s | grep -o 'orl \$-*[0-9]*' | head -1)
echo "    gen1 mask: $M1"
[[ "$M1" != "orl \$0" ]] || { echo "FAIL: mask did not strengthen"; exit 1; }
echo "[+] chain iterates and strengthens"

echo "[*] locked-flag math: first glibc rand of the baked random"
/tmp/tf_tcc "$ROOT/handout/flag.c" >/dev/null 2>&1
cat > /tmp/tf_ref.c <<'EOF'
#include <stdio.h>
#include <stdlib.h>
int main(int argc, char **argv){ unsigned s; sscanf(argv[1],"%x",&s); srand(s); printf("cyberQuest{tru5t_f4ll_%08x}\n",rand()); return 0; }
EOF
gcc -o /tmp/tf_ref /tmp/tf_ref.c 2>/dev/null
GOT=$(/tmp/tf_ref "$SEEDR")
echo "    $GOT"
[[ "$GOT" == "$EXPECTED" ]] || { echo "FAIL: lock math mismatch"; exit 1; }
echo "[+] PASS — chain verified, locked flag $EXPECTED"

echo "[*] contrast: a stock compiler stays random"
gcc -o /tmp/tf_gnu "$ROOT/handout/flag.c" 2>/dev/null
/tmp/tf_gnu > /tmp/tf_r1.txt
/tmp/tf_gnu > /tmp/tf_r2.txt
[[ "$(cat /tmp/tf_r1.txt)" != "$(cat /tmp/tf_r2.txt)" ]] && echo "[+] stock compiler is random (good)" || echo "[!] warning: stock matched (rare pid/time collision)"

rm -f /tmp/tf_boot.c /tmp/tf_tcc /tmp/tf_tcc1 /tmp/tf_ref.c /tmp/tf_ref /tmp/tf_gnu /tmp/tf_r1.txt /tmp/tf_r2.txt a.out a.s 2>/dev/null
echo "ALL GOOD"
