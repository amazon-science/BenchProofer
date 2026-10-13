# mapping.md — django__django-12741

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 537d422942b53bc0a2b6a51968f379c0de07793c`, states the type
abstraction, and gives the provenance of each callee (source + the exact
behaviour the model relies on).

Repo files under change:
- `django/db/backends/base/operations.py` (the routine under specification)
- `django/core/management/commands/flush.py` (the one in-tree caller)

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `execute_statement_batch(self, sql_list)` | `BaseDatabaseOperations.execute_sql_flush(self, sql_list)` — `django/db/backends/base/operations.py:403` (post-patch signature) | the modeled changed routine: run a prepared batch of flush statements scoped to the helper's own connection |
| `DatabaseOperations` | `BaseDatabaseOperations` (the `connection.ops` object) — `django/db/backends/base/operations.py` | minimal twin holding only the touched field, `connection` |
| `Connection` | the backend connection `self.connection` (a `BaseDatabaseWrapper`) | minimal twin holding only the touched facets (see §2) |
| `Connection.alias` | `self.connection.alias` — the connection's own database identifier (a `BaseDatabaseWrapper` attribute) | the database the routine now derives the atomic block's scope from |
| `Connection.supports_rollback` | `self.connection.features.can_rollback_ddl` — `django/db/backends/base/features.py` | the savepoint capability passed to `transaction.atomic(savepoint=...)` (model field renamed to a behavioural name to avoid echoing the repo symbol in the spec view) |
| `Connection.caller_alias` | (pre-patch only) the `using` parameter of the OLD signature `execute_sql_flush(self, using, sql_list)` — `operations.py:403` @ base_commit | the externally-threaded database identifier the pre-patch code scoped the block to; modeled for the differential witness, never used by `model.py`'s impl |
| `Connection.scoped_alias` | observation recorder: the `using=` argument actually handed to `transaction.atomic(...)` (`operations.py:405` pre / `:404-407` post) | which database the opened atomic block ran under |
| `Connection.scoped_savepoint` | observation recorder: the `savepoint=` argument handed to `transaction.atomic(...)` | which savepoint behaviour the block opened with |
| `Connection.executed` | observation recorder: the ordered list of statements `cursor.execute(sql)` ran (`operations.py:408` pre / `:408` post — the `for sql in sql_list: cursor.execute(sql)` loop) | the statements the cursor executed, in order |

The in-tree caller `django/core/management/commands/flush.py:63` is updated by
the same gold patch (`execute_sql_flush(database, sql_list)` →
`execute_sql_flush(sql_list)`); `database` there equals `connection.alias`
(`connection = connections[database]`, `flush.py:29`), so the call's effect is
unchanged — the redundant first positional argument is simply dropped.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `BaseDatabaseOperations` (`connection.ops`) | `DatabaseOperations` with only `connection` | the only facet the routine touches is `self.connection`; all other operations attributes are irrelevant to this behaviour |
| `BaseDatabaseWrapper` (`self.connection`) | `Connection` with `alias`, `can_rollback_ddl`, recorders | only the connection's database identifier and DDL-rollback capability are read by the routine |
| `self.connection.alias` (a `str` database alias, e.g. `"default"`) | `int` identifier | the alias is observed only by *identity* (which database the block is scoped to); two aliases are equal iff they denote the same database. An opaque integer identifier preserves exactly this equality. The F2P tests use a single connection, so the relevant fact is `scoped_alias == alias`. |
| `self.connection.features.can_rollback_ddl` (`bool`) | `bool` | identical. |
| `sql_list` (a `list[str]` of SQL statements) | `List[int]` of opaque statement identifiers | each statement is observed only by being executed in order; its text is opaque to this routine (the cursor runs it). `int` tokens preserve identity + order; the spec is carried by `PSeq[int]` via `ToSeq`. |
| `transaction.atomic(using=a, savepoint=s)` context manager (`operations.py:404-405`) | recorded effect: `scoped_alias = a`, `scoped_savepoint = s` | unchanged callee; its only behaviour this routine's contract pins is *which database it scopes to* and *whether it uses a savepoint* — recorded so the contract can assert clauses (1),(2). (§3.1) |
| `with self.connection.cursor() as cursor: cursor.execute(sql)` loop (`operations.py:406-408`) | recorded effect: append each `sql` to `executed`, in order | unchanged callee; its only behaviour the contract pins is *which statements ran, in what order* — clause (3). (§3.2) |

`str` indexing/iteration is banned in Nagini; the statement carrier is
`List[int]`, the alias carrier `int`. The specification is phrased over
`PSeq[int]` (statements) and integer equality (alias) via `ToSeq`.

## 3. Callee provenance (unchanged callees — modeled by recorded effect, checked by G-AX)

No `@ContractOnly` axiom is consumed by the proof: the two callees the routine
invokes are unchanged by this behaviour and are modeled by their *observable
effects* on recorders, then validated against the real callees out-of-band by
`axiom_check.py` (G-AX). There is therefore no A-consumed axiom and no dead
axiom in `model.py`.

### 3.1 `transaction.atomic(using=…, savepoint=…)` (unchanged callee)
**Callee:** `django.db.transaction.atomic` — `django/db/transaction.py`. A
context manager that opens an atomic block on the database named by `using`,
with savepoint behaviour controlled by `savepoint`. The patch changes *only*
the value passed for `using`: from the dropped `using` parameter to
`self.connection.alias`. `atomic` itself is not changed. The contract pins the
*scope* of the opened block (`scoped_alias == alias`) and the savepoint flag
(`scoped_savepoint == can_rollback_ddl`).
**G-AX evidence:** `axiom_check.py` runs the REAL `execute_sql_flush` (post-patch
form) under a real connection and asserts the atomic block it opens is scoped to
`connection.alias` (it observes the connection state the block manipulates and
that no caller-supplied alias is consulted), and that the savepoint flag equals
`connection.features.can_rollback_ddl`.

### 3.2 cursor `execute(sql)` over the batch (unchanged callee)
**Callee:** `self.connection.cursor().execute(sql)` — the DB-API cursor. The
patch does not change the execution loop `for sql in sql_list: cursor.execute(sql)`
(`operations.py:406-408`); it runs exactly the supplied statements, in order.
The contract pins this as `ToSeq(executed) == ToSeq(sql_list)`.
**G-AX evidence:** `axiom_check.py` runs the real `execute_sql_flush` with a
recording cursor / recording connection and asserts the executed statement
sequence equals the input `sql_list` (same statements, same order, none added or
dropped).

## 4. Pre-patch correspondence (the differential witness)

Pre-patch, `execute_sql_flush(self, using, sql_list)` scoped the atomic block to
the separately-supplied `using` argument (`operations.py:405`,
`transaction.atomic(using=using, …)`). `model_prepatch.py` reproduces this by
scoping the recorded block to `self.connection.caller_alias` (the modeled
caller-threaded value, §1) instead of `self.connection.alias`. Since
`caller_alias` is not constrained to equal `alias`, the byte-identical spec's
clause (1) `scoped_alias == alias` FAILS — exactly the behaviour the F2P test
`test_execute_sql_flush_statements` observes when it calls
`execute_sql_flush(sql_list)` with no alias argument and the flush must still
target the connection's own database.
