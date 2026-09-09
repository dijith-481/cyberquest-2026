vault-svc v2 (memory-safe rewrite) — ordinary engineering label safe
=====================================================================

Included:

  vault        the service binary, exactly as deployed (with symbols)
  vault.rs     the service source, in full

The rewrite added an automation tier and a hex wire format. One label
vault per connection:

  store <hex>     store a label (hex-encoded, 64 bytes max)
  promote <id>    promote a label to the automation tier
  run <id>        run a promoted callback
  show <id>       display a label (callbacks are redacted)
  info            print build info and a support diagnostic
  quit            close the session

Labels start as text. The auditors confirmed the overflow is gone.
The compiler even warns that one of the enum variants is never
constructed — surely that means it can never run.
