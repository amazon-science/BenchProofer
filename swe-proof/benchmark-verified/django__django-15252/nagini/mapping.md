# mapping.md — django__django-15252

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 361bb8f786f112ee275be136795c0b1ecefff928`, states the type
abstraction, and gives the provenance of each modelled callee.

Repo file under change: `django/db/migrations/executor.py` (the `migrate`
method's prologue). The callees it consults live in
`django/db/migrations/recorder.py` and `django/db/migrations/executor.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `migrate(executor, plan)` | `MigrationExecutor.migrate(self, targets, plan=None, state=None, fake=False, fake_initial=False)` — `django/db/migrations/executor.py:91` (changed prologue at body lines 98-100) | the modeled changed function (the migration-execution prologue) |
| `Executor.table_present` | result of `self.recorder.has_table()` — `MigrationRecorder.has_table`, `django/db/migrations/recorder.py:53` | read-only query: whether the bookkeeping table already exists |
| `Executor.schema_ensured` | the observable effect of `self.recorder.ensure_schema()` — `MigrationRecorder.ensure_schema`, `django/db/migrations/recorder.py:59` | mutable effect flag: whether the table-ensuring WRITE effect occurred |
| `Executor.records_read` | whether the result-assembly issued the record-reading QUERY effect (the normal tail of `migrate`, which the short-circuit `return self._create_project_state(with_applied_migrations=False)` at `django/db/migrations/executor.py:73` bypasses) | mutable effect flag: whether a record-reading query was issued; False only on the no-touch short-circuit path |
| `no_pending_records(pending)` | the guard `plan == []` (`django/db/migrations/executor.py:99` post-patch) | pure spec: the work list is present and length-zero (this connection has no migrations to record) |
| `pending` (`Optional[List[int]]`) | the `plan` keyword argument of `migrate` | the caller's supplied work list (list of `(Migration, backwards?)`); only its presence (`is None`) and emptiness (`== []`) are observed |

The pre-patch repo line the change replaces (for the refinement audit, not
referenced from the consumer spec view): the unconditional
`self.recorder.ensure_schema()` at `django/db/migrations/executor.py:100`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection / justification |
|---|---|---|
| `plan` — a `list` of `(Migration, backwards?)` tuples, or `None` | `Optional[List[int]]` | only the work list's *presence* (`plan is None`) and *emptiness* (`plan == []`) gate the behaviour; the element identities are never consulted by the changed prologue. `None ↔ None`; `[] ↔` a present zero-length list; any non-empty `list ↔` a present non-zero-length `List[int]`. Integer step tokens are an opaque faithful carrier for "the list is non-empty". |
| `self.recorder.has_table()` → `bool` | `executor.table_present: bool` (read-only) | `has_table()` issues an introspection query and returns whether `django_migrations` exists; the prologue only branches on that boolean and never changes it. Modelled as a read-only boolean field at fractional permission. |
| `self.recorder.ensure_schema()` (a side-effecting call that may create the table) | `executor.schema_ensured: bool` set True when invoked | the F2P tests observe ONLY *whether* `ensure_schema` runs (`assertNumQueries(0)` / `mocked_ensure_schema.assert_not_called()`). The faithful abstraction of the call is "the effect occurred", a monotone boolean that starts False. |
| the record-reading result assembly: the short-circuit `return self._create_project_state(with_applied_migrations=False)` vs. the normal tail of `migrate` (which reads applied-migration records) | `executor.records_read` (True on every path that reaches the normal assembly; left False only on the short-circuit `return`) | the short-circuit returns a project state built WITHOUT issuing any record-reading query (`with_applied_migrations=False` ⇒ no DB reads of the records); every other path reaches the normal result assembly, which reads records. The observable distinction is "was a record-reading query issued" — exactly what the F2P `assertNumQueries(0)` measures on the short-circuit path. |
| `MigrationExecutor` instance (`self`) | `Executor` minimal class with the three touched facets | only `recorder.has_table()`, `recorder.ensure_schema()`, and whether the assembly issues record reads are touched by the change; everything else (`self.loader`, `migration_plan`, `_migrate_all_forwards/backwards`, …) is unchanged, downstream of the prologue, and unobserved here. |

No string modelling is needed; the behaviour is a control-flow decision over a
work-list shape and one boolean query result.

## 3. Callee provenance (no consumed axiom; G-AX = decision-logic equivalence)

This bundle consumes **no `@ContractOnly` axiom**. The three primitives the
prologue consults are each *reduced to the single observation* the F2P tests
make about them, and the changed *decision logic over those observations* is
modelled DEEPLY in `model.py`'s impl region. G-AX therefore validates the
decision-logic equivalence (model observations == gold-patched observations on
every work-list-shape × table-existence combination) rather than an axiom's
over-approximation. Provenance of each reduced callee:

### 3.1 `MigrationRecorder.has_table` (`recorder.py:53`)
```python
def has_table(self):
    """Return True if the django_migrations table exists."""
    with self.connection.cursor() as cursor:
        tables = self.connection.introspection.table_names(cursor)
    return self.Migration._meta.db_table in tables
```
A pure boolean query (no state change). The prologue branches on its result;
modelled as the read-only `table_present`. The F2P test mocks it to `False`
(`@mock.patch.object(MigrationRecorder, 'has_table', return_value=False)`).

### 3.2 `MigrationRecorder.ensure_schema` (`recorder.py:59`)
```python
def ensure_schema(self):
    if self.has_table():
        return
    with self.connection.schema_editor() as editor:
        editor.create_model(self.Migration)
    ...
```
The side-effecting call the change makes conditional. When the table is absent
it issues `CREATE TABLE` (the "queries" the F2P `assertNumQueries(0)` forbids on
the short-circuit path). The faithful observation is "was this invoked",
modelled as `schema_ensured`.

### 3.3 `MigrationExecutor._create_project_state` (`executor.py:73`)
```python
def _create_project_state(self, with_applied_migrations=False):
    state = ProjectState(real_apps=self.loader.unmigrated_apps)
    if with_applied_migrations:
        ... # reads applied_migrations (DB queries)
    return state
```
With `with_applied_migrations=False` it builds the state WITHOUT reading any
applied-migration records (no DB queries). The short-circuit returns exactly
this; the faithful observation is that the record-reading QUERY effect did NOT
occur, i.e. `records_read` stays False on this path (and is True on every path
that reaches the normal record-reading assembly).

**Conformance check (G-CONF):** `conformance_check.py` runs the impl region
verbatim (contracts stripped) as the shadow against the REAL patched
`MigrationExecutor.migrate` in the instance container, bridging
`Optional[List[int]]` -> the `plan` keyword per §2 and reading back the three
pinned observations (`table_present` controlled; `schema_ensured` = whether
the table-ensuring write primitive was invoked; `records_read` = whether the
record-reading assembly tail ran), plus an end-to-end real-sqlite pass on all
six shape × table-state combinations. >= 1e5 Requires-satisfying inputs,
pinned fuzz seed **15252**.

**Soundness check (G-AX):** `axiom_check.py` re-encodes the model's observation
function (from `model.py`'s impl region) and the gold-patched `migrate`
prologue (from `patch.diff`'s body) and asserts they agree on all
`{None, [], [non-empty]} × {table absent, table present}` combinations, then
re-enacts the F2P `test_migrate_skips_schema_creation` shape against a recorder
double that counts `ensure_schema` calls: the gold prologue makes 0 calls
(short-circuits) while the pre-patch prologue makes 1 (the bug). stdlib-only;
exit 0 iff sound.
