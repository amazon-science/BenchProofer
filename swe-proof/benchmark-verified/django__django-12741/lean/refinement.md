# refinement.md — django__django-12741

Maps every operation in `implementation_executeFlush` to its `patch.diff`
counterpart in `BaseDatabaseOperations.execute_sql_flush`
(`django/db/backends/base/operations.py`). Tags: **R** type-refinement,
**A-consumed** proof uses a callee axiom, **A-reference** deep-modeled changed op
validated == real callee, **I** identical concrete op.

## Patch (post-patch routine)
```python
def execute_sql_flush(self, sql_list):
    """Execute a list of SQL statements to flush the database."""
    with transaction.atomic(
        using=self.connection.alias,
        savepoint=self.connection.features.can_rollback_ddl,
    ):
        with self.connection.cursor() as cursor:
            for sql in sql_list:
                cursor.execute(sql)
```
The modeled value is the OBSERVABLE TRIPLE the routine determines: the database
the transaction is bound to (`using=`), the savepoint flag, and the statements
executed (in order). The companion `flush.py` call site is updated to the new
arity (`execute_sql_flush(sql_list)`); that is a pure caller-side arity change
with no separately-observable behavior, so it is not independently modeled.

## Operation correspondence
| # | Lean op (`implementation_executeFlush`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `let database := connectionAlias` | `transaction.atomic(using=self.connection.alias, …)` | R | the transaction's bound database is the connection's own alias. `self.connection.alias : str` ↔ `connectionAlias : String`. Post-patch the routine no longer reads the dropped `using` argument; `suppliedUsing` is therefore unused (frame: result.database ≠ suppliedUsing in general). |
| 2 | `let savepoint := canRollbackDdl` | `savepoint=self.connection.features.can_rollback_ddl` | R | `self.connection.features.can_rollback_ddl : bool` ↔ `canRollbackDdl : Bool`; copied straight to the savepoint flag. |
| 3 | `let mut executed := []` | the cursor begins having run no statements | I | accumulator of executed statements starts empty. |
| 4 | `for sql in sqlList do executed := executed ++ [sql]` | `for sql in sql_list: cursor.execute(sql)` | I | each statement is executed once, in the given order; modeled as an order-preserving append accumulation (`List.execute` ≈ identity on the list). `cursor.execute` side effect's only observable here is "this statement ran, in this position". |
| 5 | `return { database, savepoint, executed }` | the transaction binding + executed statement stream | I | the observable triple the routine produces. |

Every op is R or I; **no A row** — no unchanged callee is consumed as an axiom
and there is no A-reference deep-model of an unchanged callee. `transaction.atomic`
and `cursor.execute` are side-effecting context managers whose only modeled
content is the observable triple (a pure function of the inputs). Therefore
`meta.json axioms = []`, `deep_model_references = []`, and `axiom_check.py` is a
skip stub.

## R/I legs ⇒ G-CONF
The whole impl is R/I, so `conformance_check.py` mechanically differential-tests
the impl shadow against `patch.diff` behavior over ≥10^5 fuzzed inputs.
`conf_skip = false`.

## Prepatch = the real bug
Pre-patch the signature is `execute_sql_flush(self, using, sql_list)` and the
transaction is opened with `transaction.atomic(using=using, …)` — bound to the
separately-supplied database identifier rather than the connection's own alias.
The prepatch impl (`let database := suppliedUsing`) is exactly this. It cannot
satisfy `problem_spec_executeFlush` on the discriminating clause
(`result.database = connectionAlias`) whenever `suppliedUsing ≠ connectionAlias`
— precisely the simplification the issue demands (drop `using`, infer it from
`self.connection.alias`). The carried gold proof's `rfl` for the `database`
component fails to typecheck against the buggy impl (G-DIFF). The two
FAIL_TO_PASS tests drop the redundant argument at the call sites
(`execute_sql_flush(connection.alias, sql_list)` → `execute_sql_flush(sql_list)`),
which only typechecks once the routine binds the transaction to its own alias.
