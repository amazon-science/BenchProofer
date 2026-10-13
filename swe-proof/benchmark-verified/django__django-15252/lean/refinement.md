# refinement.md — django__django-15252

Maps every operation in `implementation_provisionRecordsTable` to its
`patch.diff` counterpart. Tags: **R** (type refinement), **A-consumed** (proof
uses an axiom's property), **A-reference** (deep model validated == real callee
by G-AX), **I** (identical concrete op). Every step is R, A, or I.

## Modeled function: the head of `MigrationExecutor.migrate`

Post-patch repo code (`patch.diff`, `executor.py:98-100`):
```python
# The django_migrations table must be present to record applied
# migrations, but don't create it if there are no migrations to apply.
if plan == []:
    if not self.recorder.has_table():
        return self._create_project_state(with_applied_migrations=False)
else:
    self.recorder.ensure_schema()

if plan is None:
    plan = self.migration_plan(targets)
... (unchanged remainder, lines :102-134) ...
return state
```

Lean impl (`implementation_provisionRecordsTable`):
```lean
def implementation_provisionRecordsTable
    (plannedOps : Option (List PlannedOp)) (tableExists : Bool) : Outcome := Id.run do
  let mut provisioned := false
  if plannedOps = some [] then
    if !tableExists then
      return { provisionedTable := false, state := State.projectState false }
    -- table already present: leave it untouched and proceed.
  else
    provisioned := true
  return { provisionedTable := provisioned, state := State.continuationResult plannedOps }
```

| # | Lean op | patch.diff / real-code counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `plannedOps : Option (List PlannedOp)` (input carrier) | the `plan` parameter (`plan=None` default) | **R** | `none ↔ plan is None`, `some [] ↔ plan == []` (explicit empty), `some (_::_) ↔ non-empty plan`. Only the absent/empty/non-empty shape is observed; the `PlannedOp` (`Nat`) identities are irrelevant. Python's `None == [] → False` vs `[] == [] → True` ⇔ Lean `none ≠ some []`, `some [] = some []`. See mapping.md. |
| 2 | `tableExists : Bool` (input carrier) | `self.recorder.has_table()` (recorder.py:53-57) | **R** | the boolean truth value of the unchanged `has_table()` call. Mocked `False` in both F2P tests. Captured as a plain input, not axiomatized. |
| 3 | `if plannedOps = some [] then …` | `if plan == []:` (the new guard, the fix) | **I** (deep model of the changed branch) | **the fixed control-flow guard.** Value-equality test for the explicit empty plan; structurally identical to the Python `==`. |
| 4 | `if !tableExists then return { provisionedTable := false, state := State.projectState false }` | `if not self.recorder.has_table(): return self._create_project_state(with_applied_migrations=False)` | **R** | the new short-circuit: when the table is absent, return WITHOUT provisioning, yielding a no-applied project state. `State.projectState false ↔ _create_project_state(with_applied_migrations=False)`; `provisionedTable := false ↔ ensure_schema not called`. |
| 5 | (`plan == []` & table present) fall-through — `provisioned` stays `false` | `if plan == []: if not has_table(): return …` — the `has_table()`-true case falls through to the remainder, never reaching `ensure_schema()` | **R** | when the table already exists nothing is provisioned and execution proceeds to the remainder. `provisionedTable := false` and `state := State.continuationResult (some [])`. |
| 6 | `else: provisioned := true` | `else: self.recorder.ensure_schema()` | **I** (deep model of the changed branch) | the unchanged-behavior branch: for any non-empty / `None` plan the provisioning step runs exactly as pre-fix. Modeled as the boolean `provisionedTable := true` (the test observes the call, not the table internals). |
| 7 | `return { provisionedTable := provisioned, state := State.continuationResult plannedOps }` | `... (unchanged remainder :102-134) ... return state` | **R** | after the guard, the routine runs its UNCHANGED remainder and returns its state. `State.continuationResult plannedOps` is an opaque structural carrier for that remainder's result (it is not touched by the patch); the spec only pins that the remainder is reached, with provisioning recorded by `provisioned`. |

All impl-region ops are **R/I** — there is NO A-tagged (axiom) content, so the
impl is NOT all-A-tagged: `conf_skip = false`, and `conformance_check.py`
mechanically differential-tests the R/I shadow against an in-process replica of
the patched `migrate` head over the three input dimensions
(`plan ∈ {None, [], non-empty}` × `has_table ∈ {True, False}`).

## Callee provenance (no consumed axiom)

- `has_table()` (recorder.py:53-57) — UNCHANGED; its boolean result is the input
  `tableExists`. Not modeled internally; the spec does not constrain how the
  table's presence is determined.
- `ensure_schema()` (recorder.py:59-70) — UNCHANGED; the test observes only
  WHETHER it is called (`assert_not_called` / `assertNumQueries(0)`), captured by
  `Outcome.provisionedTable`. Its internal CREATE TABLE is not modeled — pinning
  it would over-claim about a callee the fix does not change.
- `_create_project_state(with_applied_migrations=False)` (executor.py:73-89) —
  UNCHANGED; reused verbatim by the new short-circuit. Modeled as the opaque
  `State.projectState false`; the spec pins which state shape is returned, not
  its internals.
- the remainder `:102-134` — UNCHANGED; collapsed into
  `State.continuationResult plannedOps`. Outside the behavior under
  specification.

## Soundness check (verify ⟹ correct)

- `problem_spec_provisionRecordsTable` pins BOTH observable components
  (`provisionedTable` and `state`) in EVERY case (directive 5 / frame): the full
  `Outcome` record is fixed by an input-grounded conditional over `plannedOps`
  and `tableExists`. No output component is left unconstrained. In particular the
  discriminating clause `plannedOps = some []` requires `provisionedTable =
  false` (provisioning skipped), and with `tableExists = false` it further
  requires the short-circuit `State.projectState false`.
- No ungrounded oracle (directive 8): the result is dischargeable only by
  actually performing the guarded decision over the two inputs; there is no
  axiomatized answer-key to echo. `State.continuationResult plannedOps` carries
  the input `plannedOps` verbatim, so it cannot be faked independently of the
  branch taken.
- The prepatch impl reproduces the PRE-FIX behavior: it unconditionally sets
  `provisioned := true` and always returns `State.continuationResult plannedOps`
  — i.e. `ensure_schema()` always called, never short-circuiting. It violates the
  spec on the discriminating clause `plannedOps = some []`: the spec demands
  `provisionedTable = false` there, but the prepatch yields `true` (and for
  `tableExists = false` the spec demands `State.projectState false`, but the
  prepatch yields `State.continuationResult (some [])`). Its carried gold proof
  cannot close (G-DIFF/G-PANEL) — confirmed: `Solution_prepatch.lean` fails
  G-VERIFY with `⊢ False` unsolved goals on exactly the `plan == []` cases.
- This discriminating case is precisely the FAIL_TO_PASS assertions:
  `test_migrate_skips_schema_creation` calls `migrate([], plan=[])` with
  `has_table → False` and asserts `assertNumQueries(0)` (no `ensure_schema`
  CREATE TABLE = `provisionedTable false` + short-circuit); and
  `test_migrate_test_setting_false_ensure_schema` asserts `ensure_schema` is not
  called. Pre-fix both fail (`ensure_schema` always runs);
  post-fix `provisionedTable = false` on the empty-plan path.
- G-CONF confirms the R/I shadow == an in-process replica of the patched
  `migrate` head across all `plan ∈ {None, [], non-empty}` × `has_table ∈
  {True, False}` combinations plus ≥1e5 fuzzed inputs.
