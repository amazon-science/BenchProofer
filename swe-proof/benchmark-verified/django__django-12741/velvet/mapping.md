# mapping.md — django__django-12741

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 537d422942b53bc0a2b6a51968f379c0de07793c`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and gives the
provenance of each modeled callee.

Repo files under change:
`django/db/backends/base/operations.py` (the function under change) and
`django/core/management/commands/flush.py` (its one real caller).

`spec_provenance: "cold"` — derived only from `problem_statement`, the gold
`patch`, and the repo source at `base_commit`, read in the provided worktree
`$SCRATCH`. No prior solution consulted; nothing
under `$HOME/swe-bench-verified-nagini/` or any other prior twin/spec for
this instance was read.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `runBatch (conn, suppliedKey, sqlList)` | `BaseDatabaseOperations.execute_sql_flush(self, using, sql_list)` — `django/db/backends/base/operations.py:403` | the modeled changed function |
| `conn : Connection` (field `ownAlias`) | `self.connection` (a `BaseDatabaseWrapper`), field `.alias` — set in `BaseDatabaseWrapper.__init__`, `django/db/backends/base/base.py:56` (`self.alias = alias`) | the connection the operations object is bound to, and its own identifier |
| `suppliedKey : List Char` | the `using` positional parameter (removed by the patch) — `operations.py:403` pre-patch | the identifier handed in alongside the statement list |
| `sqlList : List (List Char)` | the `sql_list` parameter | the list of SQL statements to replay |
| `flushSpec conn sqlList` | the observable effect of the body: the scope `transaction.atomic(using=…)` is opened under some identifier, and `sql_list` is replayed in order through the cursor | pure spec: `(identifier the scope is opened under, statements replayed)` |
| `out.1` (opened identifier) | the `using=` keyword argument actually passed to `transaction.atomic(...)` — `operations.py:405` | post-patch `self.connection.alias`; pre-patch the `using` parameter |
| `out.2` (replayed statements) | the sequence of `sql` values fed to `cursor.execute(sql)` by `for sql in sql_list:` — `operations.py:407-408` (UNCHANGED by the patch) | the replayed statement list |

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a database alias `str` (`self.connection.alias`, the `using` arg) | `List Char` | `s` (Python str) ↔ `s`-as-`List Char`; on the BMP this is total and exact |
| a single SQL statement `str` | `List Char` | as above |
| `sql_list` (a list of SQL statement `str`) | `List (List Char)` | element-wise per the row above; `len` ↔ `.length`; order preserved |
| `self.connection` (a `BaseDatabaseWrapper`) | `Connection` structure with the single touched field `ownAlias` | only `.alias` is observed by this slice; `ownAlias` ↔ `self.connection.alias` |
| the `transaction.atomic(using=K, savepoint=…)` scope | observed only through its `using=` key `K` (= `out.1`) | `savepoint=self.connection.features.can_rollback_ddl` is UNCHANGED by the patch and orthogonal to the modeled `using`-sourcing, so it is elided (identity) |
| `for sql in sql_list: cursor.execute(sql)` | the replayed list `out.2 = sqlList` | identity on the statement list — the loop is unchanged by the patch |

`mark`-style framework wrappers (`transaction.atomic`, `self.connection.cursor`)
carry no observable data return into the modeled output beyond the two facts
above; they are pure side effects and are not modeled as values.

## 3. Callee provenance (no axioms / no deep-model references)

There are **no consumed axioms and no deep-model references** in this bundle
(`meta.json axioms: []`, `deep_model_references: []`). The unchanged callees the
changed function calls are pure side effects whose only data-carrier inputs are
the inputs of the modeled operation:

- `transaction.atomic(using=K, savepoint=…)` — opens a scoped operation keyed by
  the identifier `K`. The modeled output records `K` (`out.1`); the patch changes
  **where `K` comes from** (the `using` parameter → `self.connection.alias`).
  This is the operation under change, modeled directly (not axiomatized — §0.7).
- `self.connection.cursor()` / `cursor.execute(sql)` — replay each statement in
  `sql_list`, in order, UNCHANGED by the patch. Modeled as the identity
  `out.2 = sqlList`.

### 3.1 Why `self.connection.alias == database` at the one real caller (audit only)

The single non-test caller is `flush.py:63`,
`connection.ops.execute_sql_flush(database, sql_list)`, where
`connection = connections[database]` (`flush.py:29`).
`ConnectionHandler.__getitem__(alias)` (`django/db/utils.py:214-216`) builds
`backend.DatabaseWrapper(db, alias)` and `BaseDatabaseWrapper.__init__` sets
`self.alias = alias` (`base/base.py:56`). So at that caller the supplied
`using` (`database`) equals `self.connection.alias`. **This coincidence at the
caller does NOT make the two contracts identical**: the modeled function's
contract is over *all* `(conn, suppliedKey, sqlList)`, and the patch's behavior
— "open the scope under the connection's OWN identifier, regardless of any
supplied value" — is exactly the independence-from-`suppliedKey` property the
spec pins (`out.1 = conn.ownAlias` for every `suppliedKey`). The pre-patch
contract ("open under the supplied identifier") differs precisely on
`suppliedKey ≠ conn.ownAlias`, which is why `Solution_prepatch.lean` fails on the
`out.1 = conn.ownAlias` clause (G-DIFF). This is the SPEC_GUIDE directive-5
read-only-frame / independence property, the same shape as the
`matplotlib__matplotlib-20676` "`currentSpan` deliberately unused" bundle.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`12741`** so the
consumer-side verdict (§11.3) is reproducible. The shadow transliterates the R/I
ops of `runBatch` (open under the connection's own alias; replay the statement
list unchanged) to Python and compares against `patch.diff`'s behaviour —
observed via the real patched `BaseDatabaseOperations.execute_sql_flush` with
`transaction.atomic` / `cursor` stubbed to record the `using=` key and the
replayed statements (the two observables of the modeled slice).
