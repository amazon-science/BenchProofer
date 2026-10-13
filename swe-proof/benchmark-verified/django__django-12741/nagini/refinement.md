# refinement.md — django__django-12741

The operation-by-operation correspondence between `model.py`'s implementation
(the `execute_statement_batch` impl region) and `patch.diff` (the gold patch).
Each step is tagged **R** (type refinement), **A** (axiomatized callee — split
into **A-consumed**, where the proof uses an axiom's `Ensures`, and
**A-reference**, where a deep model is validated == the real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The routine under specification — `execute_sql_flush` (`django/db/backends/base/operations.py:403`)

Gold hunk:
```
-    def execute_sql_flush(self, using, sql_list):
+    def execute_sql_flush(self, sql_list):
         """Execute a list of SQL statements to flush the database."""
-        with transaction.atomic(using=using, savepoint=self.connection.features.can_rollback_ddl):
+        with transaction.atomic(
+            using=self.connection.alias,
+            savepoint=self.connection.features.can_rollback_ddl,
+        ):
             with self.connection.cursor() as cursor:
                 for sql in sql_list:
                     cursor.execute(sql)
```

The change drops the `using` parameter and scopes the atomic block to the
routine's *own* connection identifier (`self.connection.alias`) instead of a
separately-supplied alias. The savepoint flag and the statement-execution loop
are unchanged.

| # | model.py impl op (`execute_statement_batch`) | patch.diff op (gold) | tag | justification |
|---|---|---|---|---|
| A1 | parameter `self: DatabaseOperations`, field `self.connection` | `self` (a `BaseDatabaseOperations`); `self.connection` (a `BaseDatabaseWrapper`) | R | the operations helper and its connection modelled with only the touched fields (mapping.md §1, §2). |
| A2 | signature `execute_statement_batch(self, sql_list)` — single non-self parameter | `def execute_sql_flush(self, sql_list)` — single non-self parameter (the `using` parameter dropped) | I (under R on the name) | identical arity; the dropped `using` parameter is exactly the change. The function name is refined to a behavioural one (R, no-leakage). |
| A3 | `self.connection.scoped_alias = self.connection.alias` (records the database the atomic block is scoped to) | `transaction.atomic(using=self.connection.alias, …)` | A-reference | `transaction.atomic` is an UNCHANGED callee; the patch changes only its `using=` argument to `self.connection.alias`. The model records the scope the block is opened under and the contract pins `scoped_alias == self.connection.alias`. The recorded effect (which database the block scopes to) is validated == the real callee's behaviour by axiom_check.py / G-AX. The `self.connection.alias` read is **I** under R (`str` alias ↔ `int` identity, mapping.md §2). |
| A4 | `self.connection.scoped_savepoint = self.connection.supports_rollback` | `savepoint=self.connection.features.can_rollback_ddl` (UNCHANGED across the patch) | A-reference + I | the savepoint flag is passed through unchanged; the model records it and the contract pins `scoped_savepoint == supports_rollback` (the renamed twin of `features.can_rollback_ddl`, mapping.md §1). Recorded effect validated by G-AX (§3.1). |
| A5 | the `while` loop appending each `sql_list[i]` to `executed`, in order | `with self.connection.cursor() as cursor: for sql in sql_list: cursor.execute(sql)` (UNCHANGED across the patch) | A-reference + I | the statement-execution loop is unchanged by the patch; the model records the executed sequence and the contract pins `ToSeq(executed) == ToSeq(sql_list)` (same statements, same order). The `List[int]` statement carrier ↔ `list[str]` is R (mapping.md §2); the in-order iteration is I. Recorded effect validated by G-AX (§3.2). |

The in-tree caller `flush.py:63` is refined identically: `execute_sql_flush(database, sql_list)` → `execute_sql_flush(sql_list)`. `database == connection.alias` there (`connection = connections[database]`), so dropping the redundant first argument is observationally the identity — covered by the same gold patch, no separate model construct needed.

## B. Where the spec senses the bug (G-DIFF)

`model_prepatch.py` is the pre-patch skeleton. Pre-patch,
`execute_sql_flush(self, using, sql_list)` scoped the atomic block to the
separately-supplied `using` argument
(`transaction.atomic(using=using, …)`, `operations.py:405` @ base_commit).
With the byte-identical frozen spec, the prepatch models this by scoping the
recorded block to `self.connection.caller_alias` (the modeled caller-threaded
value) instead of `self.connection.alias`. Since nothing constrains
`caller_alias == alias`, clause (1) `scoped_alias == alias` **fails**
(`model_prepatch.py:100` — *Postcondition … Assertion
(self.connection.scoped_alias == self.connection.alias) might not hold*).

That is exactly the behaviour the F2P test observes: `test_execute_sql_flush_statements`
calls `connection.ops.execute_sql_flush(sql_list)` with **no** alias argument
and then asserts the flush actually emptied the database — which requires the
block to be scoped to the connection's own database, derived internally. A
routine that takes the scope from a separately-threaded value (the pre-patch
signature) cannot satisfy the spec.

The companion clauses (2) `scoped_savepoint == supports_rollback` and (3)
`ToSeq(executed) == ToSeq(sql_list)` pin the unchanged behaviour (the savepoint
flag and the exact, in-order statement batch), keeping the spec faithful: a
wrong impl cannot satisfy the spec by dropping/adding statements, reordering
them, or flipping the savepoint flag (P2P `test_sequence_name_length_limits_flush`
exercises a real flush statement batch through the same routine).

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — the value the atomic block is scoped to — is modeled **deeply** as
a recorded effect (`scoped_alias`) and pinned by clause (1)
`scoped_alias == alias`, NOT hidden behind an axiom about the function under
change. The three callees the routine invokes (`transaction.atomic`, the
cursor's `execute`, the cursor context manager) are **unchanged** by this
behaviour; they are modeled by their observable recorded effects (A-reference)
and validated == the real callees by axiom_check.py / G-AX. There is **no
consumed `@ContractOnly` axiom** and therefore no dead axiom: the proof depends
only on the recorded-effect contract, which G-AX confirms matches reality.

## D. verify(model) ⇒ resolved

`execute_statement_batch` verifies only if (A3) the block it opens is scoped to
`self.connection.alias` — the connection's own identifier, derived internally —
and (A4/A5) the savepoint flag and the exact in-order statement batch are
preserved. By R (the operations helper/connection ↔ their touched fields; the
`str` alias ↔ `int` identity; the `list[str]` batch ↔ `List[int]`) and the I
signature change (drop `using`), the verified routine equals the gold
`execute_sql_flush(self, sql_list)` on the tested inputs. By G-AX the real
`transaction.atomic` scopes to the alias it is handed and the real cursor runs
exactly the supplied statements in order (the A-reference recorded effects).
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and the audited recorded effects — and the gold
patch resolves (G-RESOLVE). The trust points are exactly the two of PLAN §1.1:
recorded-effect (callee) soundness (G-AX) and refinement fidelity (this
document, G-EQ).
