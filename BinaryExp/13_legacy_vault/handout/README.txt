vault-svc v1 (legacy) — ordinary engineering label safe
==========================================================

Included:

  vault        the service binary, exactly as deployed (PIE, with symbols)
  vault.c      the service source, as legacy tools ship it

The auditors hardened this build (PIE, stack protector) and removed
the debug output. One service, one label vault per connection:

  store <text>    store a label (labels are short, says the manual)
  run             run the authorization callback
  info            print a support diagnostic (no addresses, they checked)
  quit            close the session

The callback starts as denied(). Somewhere in the binary there is a
function that prints the flag. ASLR is on, the canary is on, and there
is nothing left to leak. The manual wishes you luck.
