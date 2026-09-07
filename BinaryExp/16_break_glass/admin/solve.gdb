# Break Glass — exact solve for the frozen handout/vault.
#
# This script intentionally uses the release's stable non-PIE call sites,
# while taking both anonymous stage bases from registers at runtime.
set pagination off
set confirm off

break *0x401614
run

# Stage A's entry pointer is returned in rax. At +0x73 the natural checksum
# is in rdx immediately before the store through rax.
set $stage_a = $rax
tbreak *($stage_a + 0x73)
continue
set $rdx = 0x442cb715d93c702d

# Stage C's entry pointer is returned in rax. At +0x6a the buggy 0x7e has
# already been written to the stage's local state at [rbp-8].
break *0x40166f
continue
set $stage_c = $rax
tbreak *($stage_c + 0x6a)
continue
set {unsigned long}($rbp - 8) = 0x7d
continue
quit
