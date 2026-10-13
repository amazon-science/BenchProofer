# mapping.md — django__django-12741

## Symbol binding (file:line @ base_commit 537d422942)
Modeled function: the database-flush execution routine
`BaseDatabaseOperations.execute_sql_flush`,
`django/db/backends/base/operations.py:403-408` (@ base_commit). It opens an
atomic transaction bound to a database, with a savepoint flag taken from the
backend feature `can_rollback_ddl`, then runs each SQL statement of `sql_list`
in order through a cursor.

Pre-patch the transaction's database came from a separately-supplied `using`
argument; post-patch the routine no longer accepts that argument and binds the
transaction to the connection's own alias (`self.connection.alias`). The
companion call site in `flush.py` is updated to the new arity.

Lean modeled-function name: `executeFlush` (neutral — names the behavior "run
the flush statements inside a transaction", not the patched symbol; see G-LEAK
note). The modeled value is the OBSERVABLE TRIPLE the routine determines: the
database the transaction is bound to, the savepoint flag, and the sequence of
SQL statements executed (in order).

| Lean symbol | Python binding (file:line @ base) |
|---|---|
| `executeFlush` (modeled routine) | `BaseDatabaseOperations.execute_sql_flush`, `operations.py:403-408` |
| `connectionAlias` | `self.connection.alias` (the connection's own database identifier) |
| `suppliedUsing` | the externally-supplied database identifier — pre-patch the `using` parameter (`operations.py:403`); post-patch this is no longer a parameter and the routine does not consult it |
| `canRollbackDdl` | `self.connection.features.can_rollback_ddl` → the `savepoint=` argument of the transaction (`operations.py:405`) |
| `sqlList` | `sql_list` — the list of SQL statements to run (`operations.py:407-408`) |
| `result.database` | the database the opened transaction is bound to (`transaction.atomic(using=…)`) |
| `result.savepoint` | the savepoint flag the transaction is opened with |
| `result.executed` | the SQL statements actually executed through the cursor, in order |

## Lean ↔ Python type bijection (used by G-CONF and G-AX)
| Python | Lean |
|---|---|
| `self.connection.alias` — a database alias `str` | `connectionAlias : String` |
| supplied database identifier `str` (the dropped argument) | `suppliedUsing : String` |
| `self.connection.features.can_rollback_ddl` — a `bool` | `canRollbackDdl : Bool` |
| `sql_list` — a `list[str]` of SQL statements | `sqlList : List String` |
| the observed `(using, savepoint, executed-statements)` of the transaction | `FlushExecution` record `{ database : String, savepoint : Bool, executed : List String }` |

### `using` argument modeling note
The refactor removes the `using` parameter. To keep the spec able to *observe*
the discriminating behavior — that the transaction binds to the connection's own
alias and NOT to any externally-supplied value — `suppliedUsing` is carried as an
input that the post-patch routine simply ignores. This is faithful: a removed
parameter is modeled as an input the result no longer depends on (directive-5
frame: `result.database` is pinned to `connectionAlias`, never `suppliedUsing`).
The pre-patch leg binds the transaction to `suppliedUsing`, so the two legs
diverge exactly when `suppliedUsing ≠ connectionAlias`.

## Callee provenance + flag deps
- No unchanged callee is *consumed* as an axiom. `transaction.atomic` and
  `cursor.execute` are side-effecting context managers; the bundle models only
  the OBSERVABLE triple the routine determines (which database, which savepoint
  flag, which statements in which order), which is a pure function of the four
  inputs. The statement execution is modeled deeply as an order-preserving
  accumulation over `sqlList` (an I op, not an axiom).
- No flag-dependent callee: `canRollbackDdl` enters as plain `Bool` data and is
  copied straight to `result.savepoint`.

## G-LEAK
The `problem_statement` publicly names `execute_sql_flush`, `using`, `sql_list`,
and `connection.alias`, so those concepts are not secret. The spec view
nonetheless uses neutral behavioral vocabulary and a neutral modeled-function
identifier `executeFlush`, which shares no patched def/class name
(`execute_sql_flush`, `sql_flush`, `handle`) as a substring. No patched file
path, dotted module path, or gold-diff line appears in the spec view; comments
describe behavior, never the edit.

## Pinned G-CONF fuzz seed
`12741`.
