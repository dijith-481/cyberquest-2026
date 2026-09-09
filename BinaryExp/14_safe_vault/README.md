### Challenge Name

```

SafeVault

```

### Challenge Description

```

vault-svc v1 had an incident, so the label safe was rewritten in Rust
as vault-svc v2. New automation tier, hex wire format, heap storage —
the overflow is gone and the auditors confirmed it. Memory-safe this
time. The v2 source and binary are attached for vendors who want to
match its behavior exactly.

```

### Difficulty

```

medium

```

### Flag

```

cyber_quest{saf3_vault_unsafe_b0undary_4d2e90}

```

### Points

#### Base Points

```

300

```

#### Submit Order Bonus (Optional)

```

[]

```

### Handout Text (Optional)

```

Connect to the vault: nc <host> 1339 — vault binary (with symbols) and its Rust source are attached. Your v1 exploit will not survive the migration.

```
