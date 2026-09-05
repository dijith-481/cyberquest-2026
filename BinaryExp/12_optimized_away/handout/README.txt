ledgerd — ordinary engineering reconciliation mirror
====================================================

Included:

  ledgerd-prod     the production build, exactly as deployed
  ledgerd-compat   the compat build, exactly as deployed
                   (required by the external auditors' toolchain)

The live service runs both builds in lockstep: every command you send is
executed on both builds, and the reconciliation report opens only when
both builds pass.

Protocol (one command per line):

  tag <text>    record an audit tag line
  audit         run the AU-7 separation audit
  state         print the open session
  layout        print session layout data (from the vendor header)
  quit          close the session

The frame map printed by `layout` is copied from the vendor header and
may not match local toolchains. The vendor is gone. Good luck.
