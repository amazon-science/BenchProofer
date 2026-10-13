# mapping.md — django__django-14500

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 8c3bd0b708b488a1f6e8bd8cc6b96569904605be`, states the type
abstraction, and gives the provenance of the deep-model reference (there are no
axiomatized library callees).

Repo file under change: `django/db/migrations/executor.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `keys_leaving_applied_set(own_key, replaced_keys)` | `MigrationExecutor.unapply_migration(self, state, migration, fake=False)` — `django/db/migrations/executor.py:246` (the recording branch at body lines 253-258) | the modeled changed function, reduced to its observable: the ordered list of bookkeeping keys it records as no-longer-applied |
| `own_key` (int) | `(migration.app_label, migration.name)` — `migration.app_label`/`migration.name` set in `Migration.__init__` (`django/db/migrations/migration.py:53-54`) | the migration's own bookkeeping key |
| `replaced_keys` (`PSeq[int]`) | `migration.replaces` — a list of `(app_label, name)` pairs (`Migration.replaces`, class default `[]` at `migration.py:39`, instance copy at `migration.py:59`) | the keys of the migrations this one stands in for; empty for a non-replacement migration |
| `Result()` (`List[int]`) | the sequence of `self.recorder.record_unapplied(app_label, name)` calls issued by the branch | the keys recorded as no-longer-applied, in issue order |

The unchanged callee invoked by the branch — `MigrationRecorder.record_unapplied(app, name)` (`django/db/migrations/recorder.py:89`, body `self.migration_qs.filter(app=app, name=name).delete()`) — is a removal of the key from the recorder's applied set. It is **not axiomatized**: each call is modelled as appending that key to the recorded-key sequence (`Result()`), and the test-observable applied set is the starting set minus the recorded keys (`record_unapplied` is an idempotent set removal). The companion read side `MigrationRecorder.applied_migrations()` (`recorder.py:72`) returns a dict keyed by `(app, name)`; the F2P test reads membership of the squash key in it.

The apply-side sibling `MigrationExecutor.record_migration` (`executor.py:238`) is **unchanged** by this patch and is deliberately NOT modeled: on *apply* a replacement records only its replaced keys (its own key is re-derived by `check_replacements`), whereas on *unapply* the fix makes the own key recorded explicitly. The asymmetry is the substance of the change; conflating the two would be unfaithful.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a migration bookkeeping key `(app_label, name)` (a pair of `str`) | `int` code | each distinct `(app_label, name)` pair ↔ a distinct integer; equality of keys ↔ integer equality. The branch never inspects the *content* of a key, only records it, so an injective code suffices. |
| `migration.replaces` (a `list` of key pairs) | `PSeq[int]` of the corresponding key codes | `replaces[k]` ↔ the code of the k-th replaced pair; `len` ↔ list length; listed order preserved (the `for app_label, name in migration.replaces` loop visits in order). |
| the sequence of `record_unapplied(...)` calls (a side effect on the recorder) | `List[int]` result of recorded key codes | each `record_unapplied(app_label, name)` call ↔ appending that key's code to the result; the recorder's applied-set delta is determined exactly by the set of recorded keys. |
| `migration.replaces` truthiness (`if migration.replaces:`) | `len(replaces) > 0` | a Python list is truthy iff non-empty. |

`str`/object keys are abstracted to integer codes because the branch's behaviour
is purely structural (which keys are recorded, and in what order); it does not
depend on key contents. This is the §2 "rich object → minimal parallel type"
modeling.

## 3. Deep-model reference (kind A-reference — checked by G-AX / axiom_check.py)

### 3.1 `keys_leaving_applied_set` deep model ↔ the fixed `unapply_migration` recording branch (A-reference)

**There is no axiomatized library callee.** The changed operation — *which keys
are recorded as no-longer-applied when a migration is rolled back* — is modelled
**deeply** by `keys_leaving_applied_set` (the verified loop + final append in
`model.py`). It is **not** a consumed `@ContractOnly` axiom; the Nagini proof
depends on no axiom. Instead the deep model is validated **equal to the real
fixed control flow** out-of-band by `axiom_check.py` (G-AX).

The real post-patch branch (`django/db/migrations/executor.py`, after the gold
patch):

```python
# For replacement migrations, also record individual statuses.
if migration.replaces:
    for app_label, name in migration.replaces:
        self.recorder.record_unapplied(app_label, name)
self.recorder.record_unapplied(migration.app_label, migration.name)
```

records each replaced key (in `migration.replaces` order) and **then the
migration's own key, unconditionally** — whether or not `migration.replaces` is
truthy. That is exactly the `keys_leaving_applied_set` build:
`ToSeq(Result()) == replaced_keys + PSeq(own_key)`.

The pre-patch branch had the own-key recording inside an `else:`:

```python
if migration.replaces:
    for app_label, name in migration.replaces:
        self.recorder.record_unapplied(app_label, name)
else:
    self.recorder.record_unapplied(migration.app_label, migration.name)
```

so a rolled-back *replacement* migration's own key was never recorded as
no-longer-applied — the squash migration stayed in `applied_migrations()`. This
is the single behavioural change the F2P test
`test_migrate_marks_replacement_unapplied` observes (it migrates
`0001_squashed_0002`, then unapplies and asserts the squash key is no longer in
`applied_migrations()`).

**Soundness check (G-AX):** `axiom_check.py` transcribes the real post-patch
branch (each `record_unapplied(app_label, name)` call as it would be issued) and
the abstract model, and asserts they record the **same ordered key sequence** on
8 boundary cases (incl. the issue's squash-rollback witness), an exhaustive
small enumeration (own key and replaced lists of length 0–4 over a 5-key
universe), and 40 000 randomized fuzz inputs. It also confirms the pre-patch
differential: on the squash-rollback witness the buggy branch leaves the own
key in the applied set while the fixed branch removes it. stdlib-only imports
(`itertools`, `random`, `sys`); exit 0 iff every observation matches.
