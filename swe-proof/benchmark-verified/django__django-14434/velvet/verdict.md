# P2 adversarial audit — django__django-14434

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_2.lean`, `atk_3.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec verifying wrong impl produces a faithful refined patch that fails to resolve. The spec's three postconditions fully pin all behavioral observables on the modeled (non-empty column-list) domain the F2P test exercises: post2 pins tableName=dbTable; post3 (renderedColumns=columns) pins cols.columns=columns verbatim; post1 together with post3 forces cols.tableSlot=TableSlot.name dbTable (value-comparable). The only residual slack is columns=[], which is (a) outside the method's declared domain (non-empty column-list form) and (b) unreachable in the refined patch, where _index_columns/Columns is guarded by `if columns:` and the empty case routes to the Expressions branch. Thus every verifying impl refines to the gold patch on all reachable/tested inputs.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No consumed axioms: every callee on the modeled path is an unchanged pure
@@ -87,9 +87,7 @@
   ensures out.renderedColumns = columns
   do
     -- impl-start
-    -- The table carrier threaded into the columns reference is the bare table
-    -- *name*, so the columns reference compares it by value.
-    let tableForColumns : TableSlot := TableSlot.name dbTable
+    let tableForColumns : TableSlot := TableSlot.wrapped dbTable
     let cols : ColumnsRef := { tableSlot := tableForColumns, columns := columns }
     let out : Stmt := { tableName := dbTable, cols := cols }
     return out
```

Attack 2 — `atk_2.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No consumed axioms: every callee on the modeled path is an unchanged pure
@@ -87,9 +87,8 @@
   ensures out.renderedColumns = columns
   do
     -- impl-start
-    -- The table carrier threaded into the columns reference is the bare table
-    -- *name*, so the columns reference compares it by value.
-    let tableForColumns : TableSlot := TableSlot.name dbTable
+    let tableForColumns : TableSlot :=
+      if columns.isEmpty then TableSlot.wrapped dbTable else TableSlot.name dbTable
     let cols : ColumnsRef := { tableSlot := tableForColumns, columns := columns }
     let out : Stmt := { tableName := dbTable, cols := cols }
     return out
```

Attack 3 — `atk_3.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No consumed axioms: every callee on the modeled path is an unchanged pure
@@ -87,9 +87,8 @@
   ensures out.renderedColumns = columns
   do
     -- impl-start
-    -- The table carrier threaded into the columns reference is the bare table
-    -- *name*, so the columns reference compares it by value.
-    let tableForColumns : TableSlot := TableSlot.name dbTable
+    let tableForColumns : TableSlot :=
+      if columns.isEmpty then TableSlot.wrapped "GARBAGE_TABLE" else TableSlot.name dbTable
     let cols : ColumnsRef := { tableSlot := tableForColumns, columns := columns }
     let out : Stmt := { tableName := dbTable, cols := cols }
     return out
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No consumed axioms: every callee on the modeled path is an unchanged pure
@@ -87,10 +87,8 @@
   ensures out.renderedColumns = columns
   do
     -- impl-start
-    -- The table carrier threaded into the columns reference is the bare table
-    -- *name*, so the columns reference compares it by value.
     let tableForColumns : TableSlot := TableSlot.name dbTable
-    let cols : ColumnsRef := { tableSlot := tableForColumns, columns := columns }
+    let cols : ColumnsRef := { tableSlot := tableForColumns, columns := columns.reverse }
     let out : Stmt := { tableName := dbTable, cols := cols }
     return out
     -- impl-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No consumed axioms: every callee on the modeled path is an unchanged pure
@@ -87,10 +87,8 @@
   ensures out.renderedColumns = columns
   do
     -- impl-start
-    -- The table carrier threaded into the columns reference is the bare table
-    -- *name*, so the columns reference compares it by value.
     let tableForColumns : TableSlot := TableSlot.name dbTable
-    let cols : ColumnsRef := { tableSlot := tableForColumns, columns := columns }
+    let cols : ColumnsRef := { tableSlot := tableForColumns, columns := columns ++ columns }
     let out : Stmt := { tableName := dbTable, cols := cols }
     return out
     -- impl-end
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No consumed axioms: every callee on the modeled path is an unchanged pure
@@ -87,11 +87,11 @@
   ensures out.renderedColumns = columns
   do
     -- impl-start
-    -- The table carrier threaded into the columns reference is the bare table
-    -- *name*, so the columns reference compares it by value.
-    let tableForColumns : TableSlot := TableSlot.name dbTable
-    let cols : ColumnsRef := { tableSlot := tableForColumns, columns := columns }
-    let out : Stmt := { tableName := dbTable, cols := cols }
+    -- Echo of the gold: same values via extra intermediate bindings.
+    let unused : String := dbTable
+    let slot : TableSlot := TableSlot.name dbTable
+    let cols : ColumnsRef := { tableSlot := slot, columns := columns }
+    let out : Stmt := { tableName := unused, cols := cols }
     return out
     -- impl-end
 
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No consumed axioms: every callee on the modeled path is an unchanged pure
@@ -87,11 +87,9 @@
   ensures out.renderedColumns = columns
   do
     -- impl-start
-    -- The table carrier threaded into the columns reference is the bare table
-    -- *name*, so the columns reference compares it by value.
     let tableForColumns : TableSlot := TableSlot.name dbTable
     let cols : ColumnsRef := { tableSlot := tableForColumns, columns := columns }
-    let out : Stmt := { tableName := dbTable, cols := cols }
+    let out : Stmt := { tableName := "", cols := cols }
     return out
     -- impl-end
 
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No consumed axioms: every callee on the modeled path is an unchanged pure
@@ -87,9 +87,7 @@
   ensures out.renderedColumns = columns
   do
     -- impl-start
-    -- The table carrier threaded into the columns reference is the bare table
-    -- *name*, so the columns reference compares it by value.
-    let tableForColumns : TableSlot := TableSlot.name dbTable
+    let tableForColumns : TableSlot := TableSlot.name "X"
     let cols : ColumnsRef := { tableSlot := tableForColumns, columns := columns }
     let out : Stmt := { tableName := dbTable, cols := cols }
     return out
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms: every callee on the modeled path is an unchanged pure
--  reference class, modeled deeply in the `pure` region below and validated
--  against the real classes by G-AX. See mapping.md §3.)
-- axioms-end

-- pure-start
/- A deferred-DDL reference stores, for the table it talks about, one of two
   carriers: the table *name* itself, or an opaque table-reference object that
   merely *wraps* a name (it carries a render callback and does not expose the
   name for value comparison). The two are observationally different when the
   reference is later asked whether it talks about a given table name: a stored
   name compares by value; a stored wrapper compares by object identity and so
   never equals a plain name. mapping.md §2 gives the bijection to the repo. -/
inductive TableSlot where
  | name    : String → TableSlot   -- the bare table name (value-comparable)
  | wrapped : String → TableSlot   -- an opaque object wrapping the name
  deriving Inhabited, Repr

/- Whether a stored table-slot matches a queried table name. A stored name
   matches iff it equals the query; a stored wrapper never matches a plain name
   (object-identity comparison against a value is always false). -/
@[grind] def slotMatches : TableSlot → String → Bool
  | .name s,    t => s == t
  | .wrapped _, _ => false

/- A multi-column reference: the table-slot it talks about plus the column
   names it covers. Mirrors the repo's column-reference object whose membership
   test is `stored_table == queried_table ∧ queried_column ∈ columns`. -/
structure ColumnsRef where
  tableSlot : TableSlot
  columns   : List String
  deriving Inhabited, Repr

@[grind] def ColumnsRef.referencesColumn (c : ColumnsRef) (t col : String) : Bool :=
  slotMatches c.tableSlot t && c.columns.contains col

/- A deferred statement, restricted to its two reference-bearing parts: the
   table part (always a wrapper holding the table name, used for table queries)
   and the columns part (used for column queries). A statement references a
   table if any part does; it references a column if any part does — and only
   the columns part can answer a column query. -/
structure Stmt where
  tableName : String        -- the table part: a wrapper over this name
  cols      : ColumnsRef     -- the columns part
  deriving Inhabited, Repr

@[grind] def Stmt.referencesColumn (s : Stmt) (t col : String) : Bool :=
  s.cols.referencesColumn t col

@[grind] def Stmt.referencesTable (s : Stmt) (t : String) : Bool :=
  (s.tableName == t) || slotMatches s.cols.tableSlot t

/- The sequence of column names the statement's columns part renders into the
   generated DDL text: the columns part stringifies by joining its stored
   column names in order (with multiplicity). This sequence is observable in
   the emitted SQL, so it is part of the statement's behavior. -/
@[grind] def Stmt.renderedColumns (s : Stmt) : List String :=
  s.cols.columns
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the deferred unique-constraint statement for the column-list form
   (a named constraint over a non-empty list of column names). The result must
   answer table/column reference queries grounded in the inputs:
     • it references exactly the constraint's own table;
     • for that table, it references exactly the constraint's listed columns;
     • and it renders into the generated DDL text exactly the given column
       sequence, in order (the columns part stores the given list verbatim). -/
method buildUniqueStatement (dbTable : String) (columns : List String)
    return (out : Stmt)
  ensures ∀ t col, out.referencesColumn t col = ((dbTable == t) && columns.contains col)
  ensures ∀ t, out.referencesTable t = (dbTable == t)
  ensures out.renderedColumns = columns
  do
    -- impl-start
    -- The table carrier threaded into the columns reference is the bare table
    -- *name*, so the columns reference compares it by value.
    let tableForColumns : TableSlot := TableSlot.name dbTable
    let cols : ColumnsRef := { tableSlot := tableForColumns, columns := columns }
    let out : Stmt := { tableName := dbTable, cols := cols }
    return out
    -- impl-end

prove_correct buildUniqueStatement by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

All commands run from there with SBU_PYTHON=python.

PROTOCOL: 8 same-spec (same_spec==True for all) wrong impls encoded, editing ONLY the impl region (axioms/pure/pre/post byte-identical). Verifications run concurrently in batches of <=4 via `bash scripts/lean_verify.sh <f>`.

### VERIFY RESULTS (exit 0=verifies, 1=error/refuted):
  pos_control.lean = 0 (gold impl verifies) [POSITIVE CONTROL PASS]
  prepatch.lean    = 1 (prepatch bug reproduced: wrapped slot fails post1) [PREPATCH REPRODUCED]
  atk_1 (prepatch bug, TableSlot.wrapped dbTable unconditional)        = 1 refuted
  atk_2 (partial-domain: wrapped dbTable when columns.isEmpty)         = 0 VERIFIES
  atk_3 (partial-domain: wrapped "GARBAGE_TABLE" when columns.isEmpty) = 0 VERIFIES
  atk_4 (boundary: cols.columns := columns.reverse)                    = 1 refuted (post3)
  atk_5 (control-flow-effect: cols.columns := columns ++ columns)      = 1 refuted (post3)
  atk_6 (ungrounded-oracle echo: gold values via extra bindings)       = 0 VERIFIES
  atk_7 (tableName := "")                                              = 1 refuted (post2)
  atk_8 (ungrounded slot: TableSlot.name "X")                          = 1 refuted (post1/post2)
Commands: `bash scripts/lean_verify.sh <f>.lean`.
Note: an earlier atk_6 draft using `columns.map id` left an unsolved goal (List.map id columns = columns not closed by loom_solve); it was replaced with a genuine echo (extra let-bindings, identical values) which verifies (exit 0). same_spec==True re-confirmed after the rewrite.

RESOLVE (mandatory for every verifying wrong impl): the faithful refined patch of each of atk_2, atk_3, atk_6 is byte-identical to the gold patch.diff (sha1 7daecef3ef73f89cc28bc7faf1e7217e45619154) because each verifying impl coincides with the gold impl on the entire modeled/reachable domain (the divergences are confined to columns=[], which is unreachable under the patch's `if columns:` guard and outside the declared non-empty-column-list domain). Executed:
  swebench_unified.harness.run_resolve('django__django-14434', <gold==faithful patch>, run_id='sbu-audit-eq-14434-qwxg37u-faithful', timeout=1800, retries=1)
  OBSERVED: RESOLVED=True, RAN=True, NOTE='resolved'.
Since all three faithful patches are identical, the single content-addressed resolve run is authoritative for all three. NONE of the verifying wrong impls' faithful patches fails to resolve => spec is NOT broken (verify => correct holds on this bundle).

REFINEMENT.MD AUDIT (A-legs focus): legs A1..A6 + A5b are tagged R / R+I / A-reference / I only; §C correctly certifies no kind-3 (inexpressible-changed-op) step. The single genuinely-changed op (which carrier the columns reference stores) is modeled directly in the impl region as an R step (TableSlot choice), not behind an axiom about the function under change. axioms region is EMPTY (no dead/unused axiom). A-reference correspondence VERIFIED against the real callees: axiom_check.py (G-AX) constructs the REAL django.db.backends.ddl_references Columns/Table/Statement BOTH ways (bare-string slot == TableSlot.name, and Table-wrapper slot == TableSlot.wrapped) over boundary + 20000 fuzz and asserts model==real for references_column/references_table; mapping.md §2/§3.1 correctly captures the crux (Table.__eq__ is object.__eq__ so Table(name)==name is always False). conformance_check.py (G-CONF) shadows the R/I wiring against the patched data-flow over the real classes (seed 14434, 1e5 fuzz) including the rendered-columns observable. The model<->patch correspondence holds.

CONCLUSION: >=5 same-spec attacks run (8 total; 3 verifying, 5 refuted), the prepatch bug reproduced, positive control passes, and every verifying wrong impl's materialized faithful patch was RUN through the official harness and RESOLVED. No falsification found. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_2.lean`, `atk_3.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec verifying wrong impl produces a faithful refined patch that fails to resolve. The spec's three postconditions fully pin all behavioral observables on the modeled (non-empty column-list) domain the F2P test exercises: post2 pins tableName=dbTable; post3 (renderedColumns=columns) pins cols.columns=columns verbatim; post1 together with post3 forces cols.tableSlot=TableSlot.name dbTable (value-comparable). The only residual slack is columns=[], which is (a) outside the method's declared domain (non-empty column-list form) and (b) unreachable in the refined patch, where _index_columns/Columns is guarded by `if columns:` and the empty case routes to the Expressions branch. Thus every verifying impl refines to the gold patch on all reachable/tested inputs.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_3.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms: every callee on the modeled path is an unchanged pure
--  reference class, modeled deeply in the `pure` region below and validated
--  against the real classes by G-AX. See mapping.md §3.)
-- axioms-end

-- pure-start
/- A deferred-DDL reference stores, for the table it talks about, one of two
   carriers: the table *name* itself, or an opaque table-reference object that
   merely *wraps* a name (it carries a render callback and does not expose the
   name for value comparison). The two are observationally different when the
   reference is later asked whether it talks about a given table name: a stored
   name compares by value; a stored wrapper compares by object identity and so
   never equals a plain name. mapping.md §2 gives the bijection to the repo. -/
inductive TableSlot where
  | name    : String → TableSlot   -- the bare table name (value-comparable)
  | wrapped : String → TableSlot   -- an opaque object wrapping the name
  deriving Inhabited, Repr

/- Whether a stored table-slot matches a queried table name. A stored name
   matches iff it equals the query; a stored wrapper never matches a plain name
   (object-identity comparison against a value is always false). -/
@[grind] def slotMatches : TableSlot → String → Bool
  | .name s,    t => s == t
  | .wrapped _, _ => false

/- A multi-column reference: the table-slot it talks about plus the column
   names it covers. Mirrors the repo's column-reference object whose membership
   test is `stored_table == queried_table ∧ queried_column ∈ columns`. -/
structure ColumnsRef where
  tableSlot : TableSlot
  columns   : List String
  deriving Inhabited, Repr

@[grind] def ColumnsRef.referencesColumn (c : ColumnsRef) (t col : String) : Bool :=
  slotMatches c.tableSlot t && c.columns.contains col

/- A deferred statement, restricted to its two reference-bearing parts: the
   table part (always a wrapper holding the table name, used for table queries)
   and the columns part (used for column queries). A statement references a
   table if any part does; it references a column if any part does — and only
   the columns part can answer a column query. -/
structure Stmt where
  tableName : String        -- the table part: a wrapper over this name
  cols      : ColumnsRef     -- the columns part
  deriving Inhabited, Repr

@[grind] def Stmt.referencesColumn (s : Stmt) (t col : String) : Bool :=
  s.cols.referencesColumn t col

@[grind] def Stmt.referencesTable (s : Stmt) (t : String) : Bool :=
  (s.tableName == t) || slotMatches s.cols.tableSlot t

/- The sequence of column names the statement's columns part renders into the
   generated DDL text: the columns part stringifies by joining its stored
   column names in order (with multiplicity). This sequence is observable in
   the emitted SQL, so it is part of the statement's behavior. -/
@[grind] def Stmt.renderedColumns (s : Stmt) : List String :=
  s.cols.columns
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the deferred unique-constraint statement for the column-list form
   (a named constraint over a non-empty list of column names). The result must
   answer table/column reference queries grounded in the inputs:
     • it references exactly the constraint's own table;
     • for that table, it references exactly the constraint's listed columns;
     • and it renders into the generated DDL text exactly the given column
       sequence, in order (the columns part stores the given list verbatim). -/
method buildUniqueStatement (dbTable : String) (columns : List String)
    return (out : Stmt)
  ensures ∀ t col, out.referencesColumn t col = ((dbTable == t) && columns.contains col)
  ensures ∀ t, out.referencesTable t = (dbTable == t)
  ensures out.renderedColumns = columns
  do
    -- impl-start
    -- The table carrier threaded into the columns reference is the bare table
    -- *name*, so the columns reference compares it by value.
    let tableForColumns : TableSlot := TableSlot.name dbTable
    let cols : ColumnsRef := { tableSlot := tableForColumns, columns := columns }
    let out : Stmt := { tableName := dbTable, cols := cols }
    return out
    -- impl-end

prove_correct buildUniqueStatement by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

All commands run from there with SBU_PYTHON=python.

PROTOCOL: 8 same-spec (same_spec==True for all) wrong impls encoded, editing ONLY the impl region (axioms/pure/pre/post byte-identical). Verifications run concurrently in batches of <=4 via `bash scripts/lean_verify.sh <f>`.

### VERIFY RESULTS (exit 0=verifies, 1=error/refuted):
  pos_control.lean = 0 (gold impl verifies) [POSITIVE CONTROL PASS]
  prepatch.lean    = 1 (prepatch bug reproduced: wrapped slot fails post1) [PREPATCH REPRODUCED]
  atk_1 (prepatch bug, TableSlot.wrapped dbTable unconditional)        = 1 refuted
  atk_2 (partial-domain: wrapped dbTable when columns.isEmpty)         = 0 VERIFIES
  atk_3 (partial-domain: wrapped "GARBAGE_TABLE" when columns.isEmpty) = 0 VERIFIES
  atk_4 (boundary: cols.columns := columns.reverse)                    = 1 refuted (post3)
  atk_5 (control-flow-effect: cols.columns := columns ++ columns)      = 1 refuted (post3)
  atk_6 (ungrounded-oracle echo: gold values via extra bindings)       = 0 VERIFIES
  atk_7 (tableName := "")                                              = 1 refuted (post2)
  atk_8 (ungrounded slot: TableSlot.name "X")                          = 1 refuted (post1/post2)
Commands: `bash scripts/lean_verify.sh <f>.lean`.
Note: an earlier atk_6 draft using `columns.map id` left an unsolved goal (List.map id columns = columns not closed by loom_solve); it was replaced with a genuine echo (extra let-bindings, identical values) which verifies (exit 0). same_spec==True re-confirmed after the rewrite.

RESOLVE (mandatory for every verifying wrong impl): the faithful refined patch of each of atk_2, atk_3, atk_6 is byte-identical to the gold patch.diff (sha1 7daecef3ef73f89cc28bc7faf1e7217e45619154) because each verifying impl coincides with the gold impl on the entire modeled/reachable domain (the divergences are confined to columns=[], which is unreachable under the patch's `if columns:` guard and outside the declared non-empty-column-list domain). Executed:
  swebench_unified.harness.run_resolve('django__django-14434', <gold==faithful patch>, run_id='sbu-audit-eq-14434-qwxg37u-faithful', timeout=1800, retries=1)
  OBSERVED: RESOLVED=True, RAN=True, NOTE='resolved'.
Since all three faithful patches are identical, the single content-addressed resolve run is authoritative for all three. NONE of the verifying wrong impls' faithful patches fails to resolve => spec is NOT broken (verify => correct holds on this bundle).

REFINEMENT.MD AUDIT (A-legs focus): legs A1..A6 + A5b are tagged R / R+I / A-reference / I only; §C correctly certifies no kind-3 (inexpressible-changed-op) step. The single genuinely-changed op (which carrier the columns reference stores) is modeled directly in the impl region as an R step (TableSlot choice), not behind an axiom about the function under change. axioms region is EMPTY (no dead/unused axiom). A-reference correspondence VERIFIED against the real callees: axiom_check.py (G-AX) constructs the REAL django.db.backends.ddl_references Columns/Table/Statement BOTH ways (bare-string slot == TableSlot.name, and Table-wrapper slot == TableSlot.wrapped) over boundary + 20000 fuzz and asserts model==real for references_column/references_table; mapping.md §2/§3.1 correctly captures the crux (Table.__eq__ is object.__eq__ so Table(name)==name is always False). conformance_check.py (G-CONF) shadows the R/I wiring against the patched data-flow over the real classes (seed 14434, 1e5 fuzz) including the rendered-columns observable. The model<->patch correspondence holds.

CONCLUSION: >=5 same-spec attacks run (8 total; 3 verifying, 5 refuted), the prepatch bug reproduced, positive control passes, and every verifying wrong impl's materialized faithful patch was RUN through the official harness and RESOLVED. No falsification found. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical (same_spec True for Solution vs itself and vs prepatch; impl elided). Solution.lean verifies clean (lean_verify exit 0). Faithfulness confirmed against the REAL django.db.backends.ddl_references classes for the patched _create_unique_sql given-name/non-empty-column F2P path: (1) referencesTable t = (dbTable==t) matches any(part.references_table) over Table(dbTable) + Columns(dbTable); (2) referencesColumn t col = (dbTable==t)&&col∈columns matches Columns.references_column (Table part contributes base False); (3) renderedColumns=columns faithful to Columns.__str__ under mapping.md's injective per-column quote_name bijection; omitted condition/deferrable/include parts are '' plain strings excluded by hasattr. Differential over 200k randomized (db_table,columns) inputs x query tuples + boundary cases: 0 disagreements between spec and real classes. The renderedColumns postcondition is a legitimate strengthening (closes the audit weakness of a mutated column payload), not a drift. Prepatch bug (TableSlot.wrapped -> always-False references_column) is correctly excluded. No diverging input found; spec is neither too strong nor unfaithful.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Rigorous G-PANEL-3 leakage/gold-reconstruction check for django__django-14434 (velvet). Findings:

1. Mechanical screen (leakage.screen over spec_view, judged vs problem_statement only): PASSES with zero hard failures. Confirmed by running src/swebench_unified/gates/leak.py path directly. No diff markers, no reproduced gold-patch line, no patched file path (schema.py / ddl_references.py) or module path, no spec-view identifier embedding the only distinctive changed symbol (create_unique_name), no narration terms. meta G-LEAK=pass; no relaxed_leakage flag / RELAXED_LEAKAGE.md.

2. same_spec(Solution.lean, Solution_prepatch.lean) = True — spec region byte-identical; only the elided impl region differs (TableSlot.name vs TableSlot.wrapped). The spec view elides both impl and prove_correct bodies, so the actual gold discriminator (choice of carrier) is NOT in the consumer view.

3. Semantic gold-reconstruction beyond problem_statement: the public problem_statement already discloses the site (_create_unique_sql), the symptom (references_column always false), and the exact root cause ('an instance of Table is passed as an argument to Columns when a string is expected'). The spec view's value-comparable name vs opaque wrapper distinction (TableSlot.name/.wrapped, slotMatches) is a faithful abstract re-expression of the Table-object-vs-string distinction ALREADY public in the problem statement — it does not reveal the gold edit beyond it. The model uses invented abstract symbols (buildUniqueStatement, TableSlot, ColumnsRef, Stmt), none of which are patched repo symbols. Gold-patch specifics (Table(model._meta.db_table, self.quote_name), _index_columns, the local `table` rebinding) appear only in auditor docs (mapping.md / refinement.md), not in the consumer spec view. The renderedColumns postcondition is spec-hardening against an audit weakness and does not correspond to any part of the gold edit, so aids no reconstruction.

Conclusion: spec view leaks nothing about the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
