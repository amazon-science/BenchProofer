# mapping.md — symbol binding & type bijection (django__django-14500)

## Modeled function
- **Lean** `implementation_unapplyMigration : Migration → List MigrationId`
- **Python** `MigrationExecutor.unapply_migration(self, state, migration, fake=False)`
  — `django/db/migrations/executor.py:245-262 @ 8c3bd0b` (post-patch records the
  migration's own identifier unconditionally, in addition to each replaced
  identifier).

The function under spec is `unapply_migration`. The observable behavior modeled
is the **ordered sequence of `recorder.record_unapplied(app_label, name)`
calls** the method makes — i.e. which migration identifiers are marked as
no-longer-applied, and in what order. The schema-editor / state-mutation /
progress-callback side of the method is unchanged and orthogonal; it is framed
out (the conformance harness exercises the recording path with `fake=True`).

## Type bijection (used by G-CONF + G-AX)
| Python | Lean | notes |
|---|---|---|
| `migration.app_label : str` | `Migration.appLabel : String` | identifier component |
| `migration.name : str` | `Migration.name : String` | identifier component |
| `migration.replaces : list[(str, str)]` (possibly empty / falsy) | `Migration.replaces : List MigrationId` | `MigrationId := String × String`; empty list ⇔ falsy `replaces` |
| `(app_label, name)` tuple passed to `record_unapplied` | `MigrationId = String × String` | one recorded identifier |
| the ordered stream of `record_unapplied(app, name)` calls | `List MigrationId` (result) | append-order = call-order |

`migration.replaces` in real Django is either `None`/`[]` (falsy → the
non-replacement branch) or a non-empty list of `(app_label, name)` tuples. The
Lean model collapses the falsy cases to the empty list; `mig.replaces ≠ []`
mirrors the Python truthiness test `if migration.replaces:`.

## Callee provenance
- `recorder.record_unapplied(app, name)` — `django/db/migrations/recorder.py:89`
  — is an UNCHANGED callee. It removes the `(app, name)` row from the applied
  set (`migration_qs.filter(app=app, name=name).delete()`). It is **not**
  axiomatized: its effect is order-independent and idempotent, and the fix only
  changes WHICH identifiers are passed and in what order. We therefore model the
  method's effect as the ordered sequence of identifiers handed to this sink,
  and frame the sink itself out. No `opaque`/`axiom` is consumed (axioms region
  empty).
- `migration.unapply(state, schema_editor)`, `schema_editor`, `progress_callback`
  — UNCHANGED and orthogonal to the recording decision; framed out (exercised
  with `fake=True`, no progress callback).

## Flag dependency
The branch selector is the truthiness of `migration.replaces`. The pre-/post-
patch difference is observable ONLY when `migration.replaces` is non-empty (a
squashed/replacement migration): post-patch additionally records the migration's
own identifier. G-CONF fuzzes both empty and non-empty `replaces`.

## G-CONF fuzz seed
Pinned seed: **14500**. ≥10^5 fuzzed inputs over random identifier strings and
`replaces` lists of varied length (including empty).
