#!/bin/sh
# Break Glass — reproducibility and behavior checks.
set -eu

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

EXPECTED='cyber_quest{br34k_gl4ss_l1v3_p4tch_7f3a1c}'

echo '[*] rebuilding the release from private source'
bash admin/build.sh

if ! cmp -s deployment/.build/vault handout/vault; then
    echo 'FAIL: handout/vault differs from a fresh deterministic build' >&2
    exit 1
fi
echo '[+] frozen handout matches the source build'

chmod 755 handout/vault
DECOY_1="$(./handout/vault)"
DECOY_2="$(./handout/vault)"
case "$DECOY_1" in
    cyber_quest\{*\}) ;;
    *)
    echo 'FAIL: ordinary execution did not produce a token-shaped decoy' >&2
    exit 1
    ;;
esac
case "$DECOY_2" in
    cyber_quest\{*\}) ;;
    *)
    echo 'FAIL: ordinary execution did not produce a token-shaped decoy' >&2
    exit 1
    ;;
esac
if [ "$DECOY_1" = "$EXPECTED" ] || [ "$DECOY_2" = "$EXPECTED" ]; then
    echo 'FAIL: ordinary execution reached the real flag' >&2
    exit 1
fi
echo '[+] ordinary execution stays on the decoy path'

if command -v gdb >/dev/null 2>&1; then
    echo '[*] validating the live-patch solve with GDB'
    LIVE="$(gdb -q -batch -x admin/solve.gdb ./handout/vault 2>&1)"
    if ! printf '%s\n' "$LIVE" | grep -Fq "$EXPECTED"; then
        echo 'FAIL: GDB solve did not recover the flag' >&2
        exit 1
    fi
    echo '[+] GDB recovered the real flag'
elif command -v lldb >/dev/null 2>&1; then
    echo '[*] GDB is unavailable; validating the live-patch solve with LLDB'
    LIVE="$(lldb -b -s admin/solve.lldb 2>&1)"
    if ! printf '%s\n' "$LIVE" | grep -Fq "$EXPECTED"; then
        echo 'FAIL: LLDB solve did not recover the flag' >&2
        exit 1
    fi
    echo '[+] LLDB recovered the real flag'
else
    echo '[!] no GDB or LLDB is installed here; debugger solve not exercised'
fi

echo 'ALL GOOD'
