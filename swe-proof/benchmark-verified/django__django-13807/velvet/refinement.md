# refinement.md — django__django-13807

Operation-by-operation correspondence between `Solution.lean`'s impl regions (the
`buildCheckStatements` and `buildViolationStatements` `do` blocks, the deep
`quoteIdent` model, and the statement builders) and `patch.diff` (the gold
patch). Each step is tagged **R** (type refinement), **A-reference** (a deep model
validated == the real callee by G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A-reference leg and this narrative are audited by **G-EQ**. Claim: any
impl verifying against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. Site 1 — the per-table integrity check (`buildCheckStatements`)

Gold hunk:
```
-                        cursor.execute('PRAGMA foreign_key_check(%s)' % table_name).fetchall()
+                        cursor.execute(
+                            'PRAGMA foreign_key_check(%s)'
+                            % self.ops.quote_name(table_name)
+                        ).fetchall()
                         for table_name in table_names
```

| # | Solution.lean impl op (`buildCheckStatements`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `tables : List (List Char)` | `table_names` (list of `str`) | R | `list[str]` ↔ `List (List Char)` (mapping.md §2). |
| A2 | `quoteIdent t` inside `fkCheckSql` | `self.ops.quote_name(table_name)` | A-reference | the identifier quoter is modeled **deeply** (`quoteIdent`, pure region); G-AX validates `quoteIdent == quote_name`. No consumed axiom. mapping.md §3.1. |
| A3 | `"PRAGMA foreign_key_check(".toList ++ quoteIdent t ++ ")".toList` | `'PRAGMA foreign_key_check(%s)' % self.ops.quote_name(table_name)` | I | the literal fragments and the single identifier position are transliterated 1:1 by G-CONF (`shadow_check_sql` vs `oracle_check_sql`). |
| A4 | result is `checkStmts tables`: one `fkCheckSql` per table in order, by the backward `while` fold | the `chain.from_iterable(… for table_name in table_names)` generator | I | the per-element expansion of the input list; the fold ops (`fkCheckSql t`, `::`, the loop) are concrete and G-CONF-checked element-wise. `chain.from_iterable` flattens the per-table results; order preserved. |

## B. Sites 2+3 — the per-row listing and value-fetch (`buildViolationStatements`)

Gold hunks:
```
-                        'PRAGMA foreign_key_list(%s)' % table_name
+                        'PRAGMA foreign_key_list(%s)' % self.ops.quote_name(table_name)
...
-                        'SELECT %s, %s FROM %s WHERE rowid = %%s' % (
-                            primary_key_column_name, column_name, table_name
+                            self.ops.quote_name(primary_key_column_name),
+                            self.ops.quote_name(column_name),
+                            self.ops.quote_name(table_name),
                         ),
```

| # | Solution.lean impl op (`buildViolationStatements`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | parameter `violations : List Violation`, `Violation { table, pk, col }` | the rows iterated by `for table_name, rowid, referenced_table_name, foreign_key_index in violations`, plus the per-row `primary_key_column_name` / `column_name` identifiers | R | each row's three SQL-identifier positions ↔ the `Violation` fields (mapping.md §2). `rowid`/`foreign_key_index`/`referenced_table_name` are not identifiers embedded in SQL text, so out of scope. |
| B2 | `quoteIdent v.table` in `fkListSql` | `self.ops.quote_name(table_name)` | A-reference | site 2 quoter; same deep model as A2 (G-AX). |
| B3 | `quoteIdent v.pk`, `quoteIdent v.col`, `quoteIdent v.table` in `selectSql` | the three `self.ops.quote_name(...)` of the SELECT | A-reference | site 3 quoter; same deep model (G-AX). |
| B4 | `fkListSql v.table` then `selectSql v.pk v.col v.table` literal assembly | `'PRAGMA foreign_key_list(%s)' % …` then `'SELECT %s, %s FROM %s WHERE rowid = %%s' % (…)` | I | literal fragments + identifier positions transliterated 1:1 by G-CONF (`shadow_list_sql`/`shadow_select_sql` vs the oracles). The SELECT's `%%s` → literal ` rowid = %s` (a bound-parameter placeholder, not an identifier). Order `pk, col, table` matches the gold tuple. |
| B5 | result is `violationStmts violations`: per row, listing then value-fetch, in order, by the backward `while` fold | the `for … in violations:` body building the two statements per row | I | per-element expansion (two statements per row); fold ops concrete, G-CONF-checked. |

## C. The discriminator — why the spec sees the bug

The changed operation is: **every identifier embedded in a constructed SQL
statement is routed through the quoter** instead of inserted raw. The frozen spec
pins each statement to `fkCheckSql`/`fkListSql`/`selectSql`, all of which apply
`quoteIdent`. An impl that inserts an identifier raw produces
`"PRAGMA foreign_key_check(" ++ t ++ ")"`, which is **not** equal to
`fkCheckSql t = "PRAGMA foreign_key_check(" ++ quoteIdent t ++ ")"` (they differ
exactly by the surrounding double quotes). `Solution_prepatch_1.lean` (site 1
raw) and `Solution_prepatch_2.lean` (sites 2+3 raw) each reproduce that and
**fail** `out = checkStmts …` / `out = violationStmts …` on the unsolved
`… ++ t ++ … = … ++ quoteIdent t ++ …` goal (G-DIFF). Two prepatches because the
two methods are independently-observable fixed behaviors (SPEC_GUIDE §3); the F2P
test's table (`order`), pk column (`select`), and fk column (`where`) are all SQL
keywords, so any unquoted site raises `OperationalError` instead of the expected
`IntegrityError`.

## C2. Termination semantics

The file uses `loom.semantics.termination "total"` (total correctness), with
`decreasing i` on both backward folds. The real `check_constraints` statement
construction is a finite pass over the input lists (`table_names` /
`violations`) that always terminates and returns its statement sequence, and
the F2P test observes those returned statements being executed, so total
correctness is the faithful semantics. Partial correctness would admit a
same-spec implementation that diverges (an infinite loop vacuously satisfies
every `ensures`) — a wrong impl the tests would fail — so it would leave the
spec too weak.

## D. No kind-3 (inexpressible-changed-op) steps

Every step is R, A-reference, or I. The operation that genuinely *changed* — the
addition of identifier quoting — is modeled **deeply** (`quoteIdent` + the
spelled-out statement builders, A-reference + I), not hidden behind an axiom
about the function under change (`check_constraints` is never axiomatized). The
only foreign callee, the quoter, is **unchanged** and validated == its model by
G-AX. There are no consumed axioms.

## E. verify(Solution) ⇒ resolved

`buildCheckStatements` / `buildViolationStatements` verify only if their outputs
equal the statement sequences in which every identifier is `quoteIdent`-wrapped
(A2/B2/B3) and the literal fragments and order are exactly the gold templates
(A3/A4/B4/B5). By R (`list[str] ↔ List (List Char)`, the row-fields bijection) the
verified builders equal the SQL `check_constraints` constructs post-patch; by G-AX
the deep model `quoteIdent` equals the real `quote_name` (A-reference); by G-CONF
the R/I transliteration of the builders agrees with `patch.diff`'s `%`-format
assembly on ≥10⁵ inputs. Therefore a model satisfying this spec, refined by the
map above, is the gold patch up to type refinement and the audited quoter — and
the gold patch resolves (G-RESOLVE). Trust points are exactly the two of plan
§1.1: A-reference soundness (G-AX) and refinement fidelity (this doc, G-EQ +
G-CONF).
