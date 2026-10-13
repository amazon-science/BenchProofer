# refinement.md — django__django-12741

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`runBatch` `do` block + the `flushSpec` pure model) and `patch.diff` (the gold
patch). Each step is tagged **R** (type refinement; state the bijection),
**A-consumed** (proof uses an axiom's `ensures`), **A-reference** (deep model
validated == real callee by G-AX), or **I** (identical concrete op). EVERY step
is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs + this narrative are audited by **G-EQ**. There are **no A
legs** in this bundle (`meta.json axioms: []`, `deep_model_references: []`).

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The function under change — `execute_sql_flush` (`operations.py:403`)

Gold hunk (site A):
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

| # | Solution.lean impl op (`runBatch`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `conn : Connection` (field `ownAlias`) | `self.connection` (a `DatabaseWrapper`), field `.alias` | R | `self.connection` ↔ `Connection`; only the touched field `.alias` is modeled, as `ownAlias : List Char` (mapping.md §1, §2). |
| A2 | param `suppliedKey : List Char` | the `using` positional parameter | R | `str` ↔ `List Char` (mapping.md §2). Post-patch this parameter no longer exists; the spec keeps it as a read-only input the result must be independent of (directive 5). |
| A3 | param `sqlList : List (List Char)` | the `sql_list` parameter | R | `list[str]` ↔ `List (List Char)`, element-wise per mapping.md §2. |
| A4 | `let openedUnder := conn.ownAlias`; result `out.1 = conn.ownAlias` | `with transaction.atomic(using=self.connection.alias, …)` | I | the changed `using`-source is the concrete op `self.connection.alias`, transliterated by G-CONF as the identifier the scope is opened under. The `savepoint=…` keyword is unchanged and orthogonal (mapping.md §2), elided. |
| A5 | `let replayed := sqlList`; result `out.2 = sqlList` | `with self.connection.cursor() as cursor: for sql in sql_list: cursor.execute(sql)` | I | UNCHANGED by the patch: each statement replayed once, in order. Modeled as the identity on the statement list; G-CONF observes the replayed sequence. |

Discriminating content of the change — the `using=` key the scope is opened
under is the connection's OWN identifier (`self.connection.alias`), independent
of any supplied value — lives in `out.1 = conn.ownAlias` (model) ⇔ the
`using=self.connection.alias` of `transaction.atomic` (real). The pre-patch code
sourced it from the supplied `using` parameter; `Solution_prepatch.lean`
reproduces that (`openedUnder := suppliedKey`) and **fails** the
`out.1 = conn.ownAlias` clause for `suppliedKey ≠ conn.ownAlias` (G-DIFF).

## B. The one real caller — `flush.py:63` (kind R, no separate prepatch)

Gold hunk (site B):
```
-                connection.ops.execute_sql_flush(database, sql_list)
+                connection.ops.execute_sql_flush(sql_list)
```

| # | Solution.lean construct | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | (no node) — the caller is not separately modeled | drop the `database` positional at the call | R | the caller previously supplied `database == connection.alias` (mapping.md §3.1). Post-patch it supplies nothing and the callee sources the identifier itself. Because `database == connection.alias` at this caller, the observable behaviour is unchanged at the call site; the *contract* change is captured by site A's `runBatch` spec. No independently-observable second behaviour ⇒ no `Solution_prepatch_2.lean`. |

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The one operation that genuinely *changed* — the SOURCE of
the `transaction.atomic(using=…)` key — is modeled **directly** as
`out.1 = conn.ownAlias` (step A4), an `I` op over the modeled `Connection`. It is
NOT hidden behind an axiom about the function under change (forbidden, §0.7), and
it is NOT an ungrounded oracle (§0.8): the postcondition pins the result to an
actual input field (`conn.ownAlias`), so only an impl that reads the connection's
own identifier — not the supplied key — can satisfy it. There are no consumed
axioms and no deep-model references.

## D. verify(Solution) ⇒ resolved

`runBatch` verifies only if (A4) the opened identifier equals the connection's
own `ownAlias` for EVERY `suppliedKey` and (A5) the statement list is replayed
unchanged in order. By R (`str ↔ List Char`, `self.connection ↔ Connection`,
`sql_list ↔ List (List Char)`) the verified `runBatch` equals the patched
`execute_sql_flush` on the modeled observables. The F2P tests
(`test_execute_sql_flush_statements`, `test_sequence_name_length_limits_flush`)
call `execute_sql_flush(sql_list)` (one positional) and observe the flush effect
under the connection's own alias; the patched code resolves them (G-RESOLVE). By
G-CONF the R/I transliteration agrees with `patch.diff`'s behaviour on ≥10⁵
fuzzed inputs (including `suppliedKey ≠ conn.ownAlias`, where the legs diverge
exactly as the prepatch fails). Therefore a model satisfying this spec, refined
by the map above, is the gold patch up to type refinement — and the gold patch
resolves.
