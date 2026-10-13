# refinement.md — django__django-15252

The operation-by-operation correspondence between `model.py`'s implementation
(the `migrate` impl region) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A** (axiomatized callee — split into
**A-consumed**, where the proof uses an axiom's `Ensures`, and **A-reference**,
where a deep model is validated == the real callee by axiom_check.py / G-AX),
or **I** (identical concrete operation). The claim: *any implementation that
verifies against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested observations, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The migration-prologue site — `MigrationExecutor.migrate` (`django/db/migrations/executor.py:91`, body lines 98-100)

Gold hunk:
```
  # The django_migrations table must be present to record applied
- # migrations.
- self.recorder.ensure_schema()
+ # migrations, but don't create it if there are no migrations to apply.
+ if plan == []:
+     if not self.recorder.has_table():
+         return self._create_project_state(with_applied_migrations=False)
+ else:
+     self.recorder.ensure_schema()
```

Note on naming: the consumer-visible spec view names its abstract facets
neutrally (`pending`, `no_pending_records`, `schema_ensured` for the
table-ensuring WRITE effect, `records_read` for the record-reading QUERY
effect) so as not to narrate the gold edit; this table binds those neutral
model names to the gold repo operations. The two flags are the two observable
effects the F2P tests measure: `mocked_ensure_schema.assert_not_called()` (no
WRITE effect) and `assertNumQueries(0)` (no further QUERY effect on the
no-touch path).

| # | model.py impl op (`migrate`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `executor: Executor` (fields `table_present`, `schema_ensured`, `records_read`) | the `self` (`MigrationExecutor`) receiver and its `recorder` | R | the minimal object carries only the touched facets; `table_present ↔ self.recorder.has_table()`, `schema_ensured ↔` the effect of `self.recorder.ensure_schema()` (the WRITE effect), `records_read ↔` whether the result-assembly issued a record-reading QUERY effect (mapping.md §1-2). |
| A2 | parameter `pending: Optional[List[int]]` | the `plan` keyword argument | R | only presence (`is None`) and emptiness (`len==0`) are observed; `None ↔ None`, `[] ↔` present zero-length, non-empty list ↔ present non-zero-length (mapping.md §2). |
| A3 | guard `if no_pending_records(pending):` where `no_pending_records(pending) == (pending is not None and len(pending) == 0)` | `if plan == []:` | R + I | `plan == []` is True exactly when `plan` is a present, length-zero list; the `@Pure` `no_pending_records` is that predicate on the `Optional[List[int]]` carrier. The branch structure is identical. |
| A4 | inner guard `if not executor.table_present:` | `if not self.recorder.has_table():` | R | `table_present` is the boolean result of the read-only `has_table()` query (mapping.md §3.1). |
| A5 | the no-touch path: `return` with neither flag set (`records_read` left False) | `return self._create_project_state(with_applied_migrations=False)` | R | the short-circuit returns a project state assembled WITHOUT issuing any record-reading query (no applied-record reads, `with_applied_migrations=False`); the faithful observation is that the record-reading QUERY effect did NOT occur, recorded by `records_read` staying False, and the early `return` matches the `return` (mapping.md §3.3). On this path NO `ensure_schema` WRITE effect occurs either — exactly as the gold code, where the `else` branch is not taken. |
| A6 | `else: executor.schema_ensured = True` | `else: self.recorder.ensure_schema()` | R | `ensure_schema()` is the table-ensuring WRITE effect; the faithful observation is that it occurred, recorded by `schema_ensured` (mapping.md §3.2). |
| A7 | the read-assembly tail `executor.records_read = True; return` reached on every non-short-circuit path (i.e. when `plan != []`, or `plan == []` but the table IS present) | the gold code falls through past the `if plan == []:` block to the rest of `migrate`, which assembles the result by reading applied-migration records (the normal `with_applied_migrations=True`-style assembly / `assertNumQueries`>0 path) | R | every path except the single short-circuit reaches the record-reading assembly; the model records that the QUERY effect occurred (`records_read = True`). When `plan == []` and the table exists, the `else` is not taken (no WRITE effect) yet the routine still reads records, so `schema_ensured` is left False and `records_read` is True — mirroring the gold exactly. |

The downstream body of `migrate` (`migration_plan`, `full_plan`,
`_migrate_all_forwards/backwards`) is UNCHANGED by the patch, is reached
identically in model and patch on every non-short-circuit path, and beyond the
single record-reading QUERY observation is unobserved by this specification; it
is therefore not part of the impl skeleton (it is the unchanged tail after the
modelled prologue).

## B. The discriminating content & the prepatch

The behavioural change is *when the table-ensuring WRITE effect runs* and
*whether the no-recording-work-and-no-table path touches the connection at
all*: the pre-patch code ran `self.recorder.ensure_schema()` **unconditionally,
first**, and then always proceeded to read records; the gold code runs the
WRITE effect only in the `else` branch (only when `plan != []`), and on an
explicitly-empty plan with no table it short-circuits without WRITE and without
the record-reading QUERY.

`model_prepatch.py` reproduces the pre-patch skeleton (`executor.schema_ensured
= True` unconditionally, then `executor.records_read = True`) with the
**byte-identical spec**. It **fails** the postcondition

```
Ensures(executor.schema_ensured == (not no_pending_records(pending)))
```

(reported at `model_prepatch.py:139`) — precisely because the bug ensures the
schema even when this connection has been determined to have no migrations to
record. (It also violates clause 2 — `records_read` — on the no-table empty
path, for the same reason: the pre-patch always reads. Either clause sensing
the change suffices for G-DIFF.) This single failing clause covers the one
independently-fixed behaviour (the conditional table-ensuring); the no-touch
record-reading effect (clause 2) is the same fix's companion effect on the same
branch, so no second `model_prepatch_<k>` is required.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R or I. There is **no axiomatized callee** (no A-consumed,
no A-reference): the three primitives the prologue consults (`has_table`,
`ensure_schema`, the result-assembly's record reads) are each reduced to the
single observation the F2P tests make about them, and the *decision over those
observations* — the changed behaviour — is modelled DEEPLY in the impl region.
The reduction's faithfulness (model observations == gold-patched observations on
every input shape, plus the F2P witness) is audited by `axiom_check.py` / G-AX
(mapping.md §3), not consumed as an axiom.

## D. verify(model) ⇒ resolved

`migrate` verifies only if (1) the table-ensuring WRITE effect is recorded as
having occurred **iff this connection was not determined to have no migrations
to record** (`schema_ensured == not no_pending_records(pending)`), and (2) the
record-reading QUERY effect is recorded as NOT having occurred **iff** this
connection was determined to have no migrations to record AND the table is
absent — and there no WRITE effect occurs either. By R (the field ↔
callee-observation bijection of mapping.md §1-3) the verified prologue is
exactly the gold prologue: `plan == []` gates skipping `ensure_schema`; `not
has_table()` gates the `_create_project_state(with_applied_migrations=False)`
short-circuit (which issues no record-reading query); otherwise `ensure_schema()`
runs and the result is assembled by reading records. G-AX confirms the
reduction is faithful on every input shape and on the F2P
`test_migrate_skips_schema_creation` witness (gold: 0 `ensure_schema` calls AND
0 queries; pre-patch: 1 `ensure_schema` call). Therefore a model satisfying
this spec, refined by the map above, is the gold patch up to the stated type
refinement — and the gold patch resolves (G-RESOLVE). The only trust point is
refinement fidelity (this document, G-EQ) plus the decision-logic-equivalence
check (G-AX); there is no axiom-soundness trust point because no axiom is
consumed.
