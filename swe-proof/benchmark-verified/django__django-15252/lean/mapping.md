# mapping.md — django__django-15252

## Symbol binding (file:line @ base_commit 361bb8f786f112ee275be136795c0b1ecefff928)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_provisionRecordsTable` / `problem_spec_provisionRecordsTable` | the head of `MigrationExecutor.migrate` — the bookkeeping-table provisioning decision | `django/db/migrations/executor.py:91-100` (changed block `:98-100`) |
| `plannedOps : Option (List PlannedOp)` | the `plan` parameter of `migrate(self, targets, plan=None, …)` | `executor.py:91`, branched on at the changed `:99` (`if plan == []`) and at `:102` (`if plan is None`) |
| `tableExists : Bool` | `self.recorder.has_table()` — whether the `django_migrations` table is present | `recorder.py:53-57`; called at the changed `executor.py:100` |
| `Outcome.provisionedTable` | whether `self.recorder.ensure_schema()` was invoked (the table-provisioning step) | `executor.py:100` (post-patch `else: self.recorder.ensure_schema()`); `recorder.py:59-70` |
| `Outcome.state` | the `ProjectState` value the function ultimately returns | `executor.py` return at `:103` (short-circuit, post-patch) and `:134` (normal remainder) |
| `State.projectState false` | `self._create_project_state(with_applied_migrations=False)` — the short-circuit return | post-patch `executor.py:100` (`return self._create_project_state(with_applied_migrations=False)`); `_create_project_state` at `:73-89` |
| `State.continuationResult plannedOps` | the `state` produced by the unchanged remainder of `migrate` (lines `:102-134`) for that `plan` | `executor.py:102-134` |

The modeled function is the head of `MigrationExecutor.migrate`. It is the only
behavior changed by the patch and the behavior observed by the FAIL_TO_PASS
tests:
* `test_migrate_skips_schema_creation` (tests/migrations/test_executor.py) —
  calls `executor.migrate([], plan=[])` with `has_table` mocked `False` and
  asserts **0 queries** (i.e. `ensure_schema` is NOT called — no table created).
* `test_migrate_test_setting_false_ensure_schema`
  (tests/backends/base/test_creation.py) — with `has_table` mocked `False`,
  asserts `ensure_schema` is **not called** when creating a test DB whose
  `TEST['MIGRATE']` is `False` (the syncing path calls `migrate` with an empty
  plan).

### What the function does (base_commit, pre-fix)

```python
def migrate(self, targets, plan=None, state=None, fake=False, fake_initial=False):
    # The django_migrations table must be present to record applied migrations.
    self.recorder.ensure_schema()          # <-- ALWAYS provisions, unconditionally

    if plan is None:
        plan = self.migration_plan(targets)
    full_plan = self.migration_plan(self.loader.graph.leaf_nodes(), clean_start=True)
    ...
    if not plan:
        if state is None:
            state = self._create_project_state(with_applied_migrations=True)
    ...
    self.check_replacements()
    return state
```

`ensure_schema()` (recorder.py:59-70) calls `has_table()`; if the table is
absent it issues `schema_editor.create_model(self.Migration)` — a CREATE TABLE.
Pre-fix this happens on every `migrate` call, even when the caller passes an
explicitly empty `plan=[]`, so a table is created on databases that have nothing
to record (the bug reported in the issue, and the read-only-permission failure).

### What the patch changes (`executor.py:98-100`)

```python
# The django_migrations table must be present to record applied
# migrations, but don't create it if there are no migrations to apply.
if plan == []:
    if not self.recorder.has_table():
        return self._create_project_state(with_applied_migrations=False)
else:
    self.recorder.ensure_schema()
```

* `plan == []` (an EXPLICIT empty list — distinct from `plan is None`): the
  provisioning step is skipped entirely. If additionally the table is absent
  (`not has_table()`), the function returns immediately with
  `_create_project_state(with_applied_migrations=False)` (a project state with no
  applied migrations) — it never reaches the `:102-134` remainder. If the table
  IS present, nothing is provisioned and execution falls through to the unchanged
  remainder (the empty-plan branch there builds the state).
* otherwise (`plan is None` ⇒ computed later, or a non-empty explicit `plan`):
  `ensure_schema()` is called exactly as before, then the remainder runs.

### Lean ↔ Python type bijection (used by G-CONF + G-AX)

| Python value | Lean value | notes |
|---|---|---|
| `plan is None` | `plannedOps = none` | the routine computes the batch (`migration_plan`); provisioning still occurs |
| `plan == []` | `plannedOps = some []` | EXPLICIT empty batch — the discriminating case the fix added |
| `plan == [op0, op1, …]` (non-empty) | `plannedOps = some (o0 :: o1 :: …)` | each `op` ↔ a `PlannedOp` (`Nat`); only the empty/non-empty shape is observed, so the identities are arbitrary |
| `has_table()` truth value | `tableExists : Bool` | `recorder.has_table()` (recorder.py:53-57); mocked in the F2P tests |
| `ensure_schema()` was called | `Outcome.provisionedTable = true` | the provisioning step (recorder.py:59-70); `false` ⇒ skipped |
| `_create_project_state(with_applied_migrations=False)` returned | `Outcome.state = State.projectState false` | the short-circuit return value |
| `state` from the `:102-134` remainder | `Outcome.state = State.continuationResult plan` | opaque structural carrier — the remainder is UNCHANGED by the patch |

Note the crucial distinction `plan is None` vs `plan == []`: Python's `[] == []`
is `True` but `None == []` is `False`, so only an explicit empty list triggers
the new branch. In Lean `none ≠ some []` and `some [] = some []`, preserving the
distinction exactly. The fixed comparison is `plan == []` (value equality), which
is `some []` in the model.

### Callee provenance + flag deps

* `has_table()` (recorder.py:53-57) — UNCHANGED; its boolean result enters the
  model as the input `tableExists`. It is consulted only inside the `plan == []`
  branch (post-fix). In the F2P tests it is mocked to return `False`. Captured
  directly as an input, not axiomatized.
* `ensure_schema()` (recorder.py:59-70) — UNCHANGED; its INVOCATION (not its
  internals) is the observable the test asserts on (`assert_not_called` /
  `assertNumQueries(0)`). Modeled as the boolean `Outcome.provisionedTable`.
* `_create_project_state(with_applied_migrations=False)` (executor.py:73-89) —
  UNCHANGED; reused verbatim by the new short-circuit branch. Modeled as the
  opaque outcome `State.projectState false`; the `with_applied_migrations=False`
  flag is recorded by the `false` payload.
* the unchanged remainder `:102-134` (`migration_plan`, `full_plan`,
  `_create_project_state(with_applied_migrations=True)`, `_migrate_all_forwards`
  / `_migrate_all_backwards`, `check_replacements`) — NOT touched by the patch;
  collapsed into the opaque `State.continuationResult plannedOps`. Whatever state
  it computes is outside the behavior under specification; the spec only pins
  that the remainder is reached (and provisioning happened first) in the
  non-short-circuit cases.

No consumed callee axiom is needed: the fix is a pure control-flow guard over
`plan` and `has_table()`, both modeled as plain inputs, and the two return
shapes are modeled as opaque structural carriers (the `State` constructors), not
asserted against a real callee. Hence `axiom_check.py` is a skip stub and G-AX
skips.

### G-CONF fuzz seed

Pinned seed: **15252** (also used in `conformance_check.py`).
