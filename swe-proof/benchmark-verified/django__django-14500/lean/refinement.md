# refinement.md — operation correspondence (django__django-14500)

Maps every op in `implementation_unapplyMigration` to its `patch.diff`
counterpart. Tags: **R** type refinement · **A-consumed** proof uses axiom
property · **A-reference** deep model validated == real callee (G-AX) · **I**
identical op.

The post-patch Python (the recording path of `unapply_migration`) is:

```python
if migration.replaces:
    for app_label, name in migration.replaces:
        self.recorder.record_unapplied(app_label, name)
self.recorder.record_unapplied(migration.app_label, migration.name)
```

We model the method's recording effect as the ordered list of identifiers
handed to `record_unapplied`. `record_unapplied` is an UNCHANGED,
order-independent/idempotent sink (mapping.md); it is framed out, not modeled or
axiomatized.

| # | Lean impl op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `let mut recorded := []` | implicit start: no identifiers recorded yet | I | concrete empty accumulator for the ordered call stream |
| 2 | `if mig.replaces ≠ []` | `if migration.replaces:` | R | falsy `replaces` (None/[]) ↔ `[]` (mapping.md type bijection) |
| 3 | `for r in mig.replaces do recorded := recorded ++ [r]` | `for app_label, name in migration.replaces: self.recorder.record_unapplied(app_label, name)` | I | per-replaced-identifier recording, in list order; `record_unapplied` framed out (R for the tuple↔pair) |
| 4 | `recorded := recorded ++ [(mig.appLabel, mig.name)]` | `self.recorder.record_unapplied(migration.app_label, migration.name)` (UNCONDITIONAL, outside the if/else) | I | the fix: the migration's own identifier is ALWAYS recorded; `record_unapplied` framed out |
| 5 | `return recorded` | end of recording path (rest of method orthogonal) | I | the ordered identifier stream is the modeled observable |

No A-consumed rows (axioms region empty): the proof discharges
`problem_spec_unapplyMigration` directly by computation. No A-reference rows: no
changed op is deeply-modeled-via-a-real-callee; the changed op is pure control
flow over identifiers. No changed-inexpressible op.

## Discriminating clause (G-DIFF)
The fix moves `record_unapplied(migration.app_label, migration.name)` OUT of the
`else` branch so it runs unconditionally. The discriminating behavior is the
**replacement case** (`mig.replaces ≠ []`): post-patch the result ends with the
migration's own identifier `(appLabel, name)`; pre-patch it does NOT (the own
identifier was recorded only in the `else` branch).

`Solution_prepatch.lean` keeps the buggy `if/else` skeleton, so for any
`mig` with `mig.replaces ≠ []` its result is `mig.replaces` with the own
identifier MISSING, which cannot equal `mig.replaces ++ [(appLabel, name)]`
(the frozen `problem_spec`). Hence `correct_unapplyMigration` is unclosable on
the prepatch — the G-DIFF signal. (On the empty-`replaces` case both impls
agree, so the bug is observable precisely in the replacement case the issue
describes.)
