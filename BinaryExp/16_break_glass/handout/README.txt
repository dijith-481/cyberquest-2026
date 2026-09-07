break_glass — vault release binary

    ./vault

The release binary prints a plausible-looking access token on an ordinary
run. The vault team says the real token is reconstructed only while the
unlock checks are alive. The source is intentionally not included.

Use a debugger. The binary is an x86-64 Linux executable and was built
without debug symbols. GDB is the reference tool; LLDB can be used when its
Linux process support is available.
