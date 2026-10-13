# P2 adversarial audit — django__django-14434

**Backend:** `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.lean` |

**Non-vacuity.** The positive control `pos_gold.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The frozen spec's 5 conjuncts fully pin the observable Statement to the gold value: conjunct 5 (renderedColumns = columns) pins columnsPart.columns exactly (order+multiplicity); conjunct 1 with columns != [] forces columnsPart.tableId.matchesName dbTable = true, hence tableId = .name dbTable; conjunct 4 forces tablePart.name = dbTable. No same-spec wrong impl can close the proof (7 machine-checked disproofs confirm each candidate violates the spec). The only closing same-spec impl (atk_8, columns.reverse.reverse = columns) is observationally identical to gold and its faithful patch RESOLVES.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -109,9 +109,9 @@
 -- impl-start
 def implementation__create_unique_sql
     (dbTable : String) (columns : List String) : Statement := Id.run do
-  let table : String := dbTable
-  let columnsPart : ColumnsRef := { tableId := TableId.name table, columns := columns }
-  return { tablePart := { name := table }, columnsPart := columnsPart }
+  let table : TableId := TableId.wrapped dbTable
+  let columnsPart : ColumnsRef := { tableId := table, columns := columns }
+  return { tablePart := { name := dbTable }, columnsPart := columnsPart }
 -- impl-end
 
 -- proof-start
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -109,9 +109,8 @@
 -- impl-start
 def implementation__create_unique_sql
     (dbTable : String) (columns : List String) : Statement := Id.run do
-  let table : String := dbTable
-  let columnsPart : ColumnsRef := { tableId := TableId.name table, columns := columns }
-  return { tablePart := { name := table }, columnsPart := columnsPart }
+  let columnsPart : ColumnsRef := { tableId := TableId.name dbTable, columns := columns.reverse }
+  return { tablePart := { name := dbTable }, columnsPart := columnsPart }
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -109,9 +109,8 @@
 -- impl-start
 def implementation__create_unique_sql
     (dbTable : String) (columns : List String) : Statement := Id.run do
-  let table : String := dbTable
-  let columnsPart : ColumnsRef := { tableId := TableId.name table, columns := columns }
-  return { tablePart := { name := table }, columnsPart := columnsPart }
+  let columnsPart : ColumnsRef := { tableId := TableId.name dbTable, columns := columns ++ columns }
+  return { tablePart := { name := dbTable }, columnsPart := columnsPart }
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -109,9 +109,8 @@
 -- impl-start
 def implementation__create_unique_sql
     (dbTable : String) (columns : List String) : Statement := Id.run do
-  let table : String := dbTable
-  let columnsPart : ColumnsRef := { tableId := TableId.name table, columns := columns }
-  return { tablePart := { name := table }, columnsPart := columnsPart }
+  let columnsPart : ColumnsRef := { tableId := TableId.name dbTable, columns := columns }
+  return { tablePart := { name := "" }, columnsPart := columnsPart }
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -109,9 +109,8 @@
 -- impl-start
 def implementation__create_unique_sql
     (dbTable : String) (columns : List String) : Statement := Id.run do
-  let table : String := dbTable
-  let columnsPart : ColumnsRef := { tableId := TableId.name table, columns := columns }
-  return { tablePart := { name := table }, columnsPart := columnsPart }
+  let columnsPart : ColumnsRef := { tableId := TableId.name dbTable, columns := [] }
+  return { tablePart := { name := dbTable }, columnsPart := columnsPart }
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -109,9 +109,8 @@
 -- impl-start
 def implementation__create_unique_sql
     (dbTable : String) (columns : List String) : Statement := Id.run do
-  let table : String := dbTable
-  let columnsPart : ColumnsRef := { tableId := TableId.name table, columns := columns }
-  return { tablePart := { name := table }, columnsPart := columnsPart }
+  let columnsPart : ColumnsRef := { tableId := TableId.name (dbTable ++ "_x"), columns := columns }
+  return { tablePart := { name := dbTable }, columnsPart := columnsPart }
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -109,9 +109,8 @@
 -- impl-start
 def implementation__create_unique_sql
     (dbTable : String) (columns : List String) : Statement := Id.run do
-  let table : String := dbTable
-  let columnsPart : ColumnsRef := { tableId := TableId.name table, columns := columns }
-  return { tablePart := { name := table }, columnsPart := columnsPart }
+  let columnsPart : ColumnsRef := { tableId := TableId.name dbTable, columns := columns.take 1 }
+  return { tablePart := { name := dbTable }, columnsPart := columnsPart }
 -- impl-end
 
 -- proof-start
```

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -109,9 +109,8 @@
 -- impl-start
 def implementation__create_unique_sql
     (dbTable : String) (columns : List String) : Statement := Id.run do
-  let table : String := dbTable
-  let columnsPart : ColumnsRef := { tableId := TableId.name table, columns := columns }
-  return { tablePart := { name := table }, columnsPart := columnsPart }
+  let columnsPart : ColumnsRef := { tableId := TableId.name dbTable, columns := columns.reverse.reverse }
+  return { tablePart := { name := dbTable }, columnsPart := columnsPart }
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_gold.lean`

```lean
import Mathlib
-- imports-end

/-!
Building a deferred unique-constraint `Statement` from a model's table name and
the list of constrained columns. The resulting statement answers membership
queries about which table and which columns it references.

The behavior pinned below: a statement built for table `dbTable` over a
non-empty column list must report that it references `dbTable`, must report
`references_column dbTable col` exactly for the columns it was built from, and
must render (into the generated DDL text) exactly the given column sequence,
in order.
-/

-- axioms-start
-- No unchanged callee is consumed: the reference objects are modeled deeply
-- below as Lean structures, so the axioms region is intentionally empty.
-- axioms-end

-- pure-start

/-- A table identifier as carried inside a column-reference object. It is either
a bare table-name string (`name`), or a wrapped reference object that holds the
same string but is a distinct kind of value (`wrapped`). The distinction matters
for name comparison: only a bare name string can compare equal to a query
table-name string; a wrapped reference object never does. -/
inductive TableId where
  | name (s : String)
  | wrapped (s : String)
  deriving Repr, DecidableEq

/-- Whether this table identifier compares equal to the query table-name string.
A bare name compares by string equality; a wrapped reference object is a
different kind of value and so never matches a plain string. -/
def TableId.matchesName : TableId → String → Bool
  | .name s,    t => s == t
  | .wrapped _, _ => false

/-- A reference to one or more columns of a table (the `columns` part of a
statement). It answers column-membership queries against the table identifier it
stored and the column list it holds. -/
structure ColumnsRef where
  tableId : TableId
  columns : List String

/-- This column reference references `(t, col)` iff its stored table identifier
matches `t` and `col` is among its columns. -/
def ColumnsRef.references_column (c : ColumnsRef) (t col : String) : Bool :=
  c.tableId.matchesName t && c.columns.contains col

/-- A column reference also answers table-membership (inherited behavior): it
references table `t` iff its stored table identifier matches `t`. -/
def ColumnsRef.references_table (c : ColumnsRef) (t : String) : Bool :=
  c.tableId.matchesName t

/-- A reference to a table (the `table` part of a statement): a wrapped object
holding the table name. It answers table-membership but contributes nothing to
column-membership. -/
structure TableRef where
  name : String

/-- This table reference references table `t` iff its name equals `t`. -/
def TableRef.references_table (r : TableRef) (t : String) : Bool :=
  r.name == t

/-- A deferred DDL statement, holding a table part and a columns part. Its
membership queries fold over its parts. -/
structure Statement where
  tablePart   : TableRef
  columnsPart : ColumnsRef

/-- The statement references column `(t, col)` iff some part does. The table
part contributes nothing to column queries; only the columns part can. -/
def Statement.references_column (s : Statement) (t col : String) : Bool :=
  s.columnsPart.references_column t col

/-- The statement references table `t` iff some part does: either the table part
or the columns part. -/
def Statement.references_table (s : Statement) (t : String) : Bool :=
  s.tablePart.references_table t || s.columnsPart.references_table t

/-- The sequence of column names the statement's columns part renders into the
generated DDL text: the columns part stringifies by joining its stored column
names in order (with multiplicity). This sequence is observable in the emitted
SQL, so it is part of the statement's behavior. -/
def Statement.renderedColumns (s : Statement) : List String :=
  s.columnsPart.columns
-- pure-end

-- post-conditions-start
/-- Specification of the statement built for table `dbTable` over `columns`:

* every column query against `dbTable` answers exactly column membership
  (`references_column dbTable col` ↔ `col ∈ columns`);
* a column query against any other table answers `false`;
* the statement references `dbTable` itself, and no other table;
* the statement renders into the DDL text exactly the given column sequence,
  in order (the columns part stores the given list verbatim). -/
def problem_spec__create_unique_sql
    (dbTable : String) (columns : List String) (result : Statement) : Prop :=
  (∀ col, result.references_column dbTable col = columns.contains col) ∧
  (∀ t col, t ≠ dbTable → result.references_column t col = false) ∧
  (result.references_table dbTable = true) ∧
  (∀ t, t ≠ dbTable → result.references_table t = false) ∧
  (result.renderedColumns = columns)
-- post-conditions-end

-- impl-start
def implementation__create_unique_sql
    (dbTable : String) (columns : List String) : Statement := Id.run do
  let table : String := dbTable
  let columnsPart : ColumnsRef := { tableId := TableId.name table, columns := columns }
  return { tablePart := { name := table }, columnsPart := columnsPart }
-- impl-end

-- proof-start
theorem correct__create_unique_sql :
    ∀ (dbTable : String) (columns : List String),
      columns ≠ [] →
      problem_spec__create_unique_sql dbTable columns
        (implementation__create_unique_sql dbTable columns) := by
  intro dbTable columns _
  unfold problem_spec__create_unique_sql implementation__create_unique_sql
  refine ⟨?_, ?_, ?_, ?_, ?_⟩
  · intro col
    simp [Id.run, pure, Statement.references_column, ColumnsRef.references_column,
      TableId.matchesName]
  · intro t col ht
    have hbeq : (dbTable == t) = false := by
      simp only [beq_eq_false_iff_ne]; exact fun h => ht h.symm
    simp [Id.run, pure, Statement.references_column, ColumnsRef.references_column,
      TableId.matchesName, hbeq]
  · simp [Id.run, pure, Statement.references_table, TableRef.references_table,
      ColumnsRef.references_table, TableId.matchesName]
  · intro t ht
    have hbeq : (dbTable == t) = false := by
      simp only [beq_eq_false_iff_ne]; exact fun h => ht h.symm
    simp [Id.run, pure, Statement.references_table, TableRef.references_table,
      ColumnsRef.references_table, TableId.matchesName, hbeq]
  · simp [Id.run, pure, Statement.renderedColumns]
-- proof-end

#print axioms correct__create_unique_sql
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) audit for django__django-14434 (lean).

SAME-SPEC CONFIRMED for all 8 attacks via swebench_unified.markers.same_spec (all True; only impl+proof regions edited, axioms/pure/pre/post byte-identical).

### ATTACKS (each built by editing only the impl region; verified with `bash scripts/lean_verify.sh <f>`):
- atk_1 (PREPATCH BUG, wrapped Table object -> TableId.wrapped): exit=1 (gold proof does not close). prepatch_reproduced=true. Disproof dis_1.lean compiles exit=0 => provably violates conjunct 1.
- atk_2 (columns.reverse, breaks renderedColumns): exit=1. dis_2 exit=0 (violates conjunct 5).
- atk_3 (columns++columns duplication): exit=1. dis_3 exit=0 (conjunct 5).
- atk_4 (tablePart.name := "", references wrong/no table): exit=1. dis_4 exit=0 (conjunct 4, references_table t=false fails at t="").
- atk_5 (partial-domain: columns := [] always): exit=1. dis_5 exit=0 (conjunct 1).
- atk_6 (ungrounded-oracle echo: tableId := .name (dbTable++"`_x`")): exit=1. dis_6 exit=0 (conjunct 1).
- atk_7 (control-flow-effect: columns.take 1 truncation): exit=1. dis_7 exit=0 (conjunct 5).
- atk_8 (observational-equivalence CONTROL: columns.reverse.reverse): exit=0, CLOSES with clean axioms [propext, Classical.choice, Quot.sound].

**DISPROOFS:** dis_1..dis_7 are machine-checked `example : ¬ problem_spec ... := by ...` files (, all lean_verify exit=0), rigorously proving atk_1..7 each violate the frozen spec => no closing proof can exist for any of them. Ran concurrently in batches of <=4.

Only atk_8 closes (clean axioms). Per protocol its faithful patch was MATERIALIZED (patch_atk_8.diff, applies clean to base worktree) and RUN through the official harness. run_resolve wrapper initially returned 'no report' (transient image-pull/contention artifact, empty log dir), so I ran the harness directly via `docker -c python -m swebench_unified.run_evaluation ...` (run_id sbu-atk8-14434-3613577): COMPLETED, RESOLVED=1, FAIL_TO_PASS test_unique_constraint SUCCESS, all PASS_TO_PASS success. report.json at report.json shows resolved:true. => verify => correct holds for the sole closing candidate.

**POSITIVE CONTROL:** gold Solution.lean (pos_gold.lean) lean_verify exit=0, clean axioms.

A-LEG / REFINEMENT AUDIT: axioms region is EMPTY (no A-consumed). refinement.md ledger: all impl legs tagged R (type refinements Table-object->bare-string flowing into Columns.self.table); A-consumed=none; one A-reference fact (`Table object != str => TableColumns.references_column False`, modeled as TableId.matchesName (.wrapped _) _ = false). No kind-3 (changed-inexpressible) leg. The A-reference correspondence was VALIDATED against the REAL Django callees (django.db.backends.ddl_references Table/Columns at base_commit 5e04e84d67) by axiom_check.py: exit=0, checked=300, status=pass. Mapping.md line refs consistent with the real ddl_references.py source (Table 40-57, TableColumns 60-96, Statement 166-201). Gold patch (test.jsonl) matches the modeled fix: table = model.`_meta`.db_table (bare string) into Columns, Table(table,...) only on the table= kwarg.

**CONCLUSION:** The spec pins the observable Statement uniquely to gold; every same-spec wrong impl provably fails to close (7 disproofs), and the single closing same-spec impl resolves under the official harness. No verify-but-not-correct gap. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.lean` |

**Non-vacuity.** The positive control `pos_gold.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The frozen spec's 5 conjuncts fully pin the observable Statement to the gold value: conjunct 5 (renderedColumns = columns) pins columnsPart.columns exactly (order+multiplicity); conjunct 1 with columns != [] forces columnsPart.tableId.matchesName dbTable = true, hence tableId = .name dbTable; conjunct 4 forces tablePart.name = dbTable. No same-spec wrong impl can close the proof (7 machine-checked disproofs confirm each candidate violates the spec). The only closing same-spec impl (atk_8, columns.reverse.reverse = columns) is observationally identical to gold and its faithful patch RESOLVES.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_gold.lean`

```lean
import Mathlib
-- imports-end

/-!
Building a deferred unique-constraint `Statement` from a model's table name and
the list of constrained columns. The resulting statement answers membership
queries about which table and which columns it references.

The behavior pinned below: a statement built for table `dbTable` over a
non-empty column list must report that it references `dbTable`, must report
`references_column dbTable col` exactly for the columns it was built from, and
must render (into the generated DDL text) exactly the given column sequence,
in order.
-/

-- axioms-start
-- No unchanged callee is consumed: the reference objects are modeled deeply
-- below as Lean structures, so the axioms region is intentionally empty.
-- axioms-end

-- pure-start

/-- A table identifier as carried inside a column-reference object. It is either
a bare table-name string (`name`), or a wrapped reference object that holds the
same string but is a distinct kind of value (`wrapped`). The distinction matters
for name comparison: only a bare name string can compare equal to a query
table-name string; a wrapped reference object never does. -/
inductive TableId where
  | name (s : String)
  | wrapped (s : String)
  deriving Repr, DecidableEq

/-- Whether this table identifier compares equal to the query table-name string.
A bare name compares by string equality; a wrapped reference object is a
different kind of value and so never matches a plain string. -/
def TableId.matchesName : TableId → String → Bool
  | .name s,    t => s == t
  | .wrapped _, _ => false

/-- A reference to one or more columns of a table (the `columns` part of a
statement). It answers column-membership queries against the table identifier it
stored and the column list it holds. -/
structure ColumnsRef where
  tableId : TableId
  columns : List String

/-- This column reference references `(t, col)` iff its stored table identifier
matches `t` and `col` is among its columns. -/
def ColumnsRef.references_column (c : ColumnsRef) (t col : String) : Bool :=
  c.tableId.matchesName t && c.columns.contains col

/-- A column reference also answers table-membership (inherited behavior): it
references table `t` iff its stored table identifier matches `t`. -/
def ColumnsRef.references_table (c : ColumnsRef) (t : String) : Bool :=
  c.tableId.matchesName t

/-- A reference to a table (the `table` part of a statement): a wrapped object
holding the table name. It answers table-membership but contributes nothing to
column-membership. -/
structure TableRef where
  name : String

/-- This table reference references table `t` iff its name equals `t`. -/
def TableRef.references_table (r : TableRef) (t : String) : Bool :=
  r.name == t

/-- A deferred DDL statement, holding a table part and a columns part. Its
membership queries fold over its parts. -/
structure Statement where
  tablePart   : TableRef
  columnsPart : ColumnsRef

/-- The statement references column `(t, col)` iff some part does. The table
part contributes nothing to column queries; only the columns part can. -/
def Statement.references_column (s : Statement) (t col : String) : Bool :=
  s.columnsPart.references_column t col

/-- The statement references table `t` iff some part does: either the table part
or the columns part. -/
def Statement.references_table (s : Statement) (t : String) : Bool :=
  s.tablePart.references_table t || s.columnsPart.references_table t

/-- The sequence of column names the statement's columns part renders into the
generated DDL text: the columns part stringifies by joining its stored column
names in order (with multiplicity). This sequence is observable in the emitted
SQL, so it is part of the statement's behavior. -/
def Statement.renderedColumns (s : Statement) : List String :=
  s.columnsPart.columns
-- pure-end

-- post-conditions-start
/-- Specification of the statement built for table `dbTable` over `columns`:

* every column query against `dbTable` answers exactly column membership
  (`references_column dbTable col` ↔ `col ∈ columns`);
* a column query against any other table answers `false`;
* the statement references `dbTable` itself, and no other table;
* the statement renders into the DDL text exactly the given column sequence,
  in order (the columns part stores the given list verbatim). -/
def problem_spec__create_unique_sql
    (dbTable : String) (columns : List String) (result : Statement) : Prop :=
  (∀ col, result.references_column dbTable col = columns.contains col) ∧
  (∀ t col, t ≠ dbTable → result.references_column t col = false) ∧
  (result.references_table dbTable = true) ∧
  (∀ t, t ≠ dbTable → result.references_table t = false) ∧
  (result.renderedColumns = columns)
-- post-conditions-end

-- impl-start
def implementation__create_unique_sql
    (dbTable : String) (columns : List String) : Statement := Id.run do
  let table : String := dbTable
  let columnsPart : ColumnsRef := { tableId := TableId.name table, columns := columns }
  return { tablePart := { name := table }, columnsPart := columnsPart }
-- impl-end

-- proof-start
theorem correct__create_unique_sql :
    ∀ (dbTable : String) (columns : List String),
      columns ≠ [] →
      problem_spec__create_unique_sql dbTable columns
        (implementation__create_unique_sql dbTable columns) := by
  intro dbTable columns _
  unfold problem_spec__create_unique_sql implementation__create_unique_sql
  refine ⟨?_, ?_, ?_, ?_, ?_⟩
  · intro col
    simp [Id.run, pure, Statement.references_column, ColumnsRef.references_column,
      TableId.matchesName]
  · intro t col ht
    have hbeq : (dbTable == t) = false := by
      simp only [beq_eq_false_iff_ne]; exact fun h => ht h.symm
    simp [Id.run, pure, Statement.references_column, ColumnsRef.references_column,
      TableId.matchesName, hbeq]
  · simp [Id.run, pure, Statement.references_table, TableRef.references_table,
      ColumnsRef.references_table, TableId.matchesName]
  · intro t ht
    have hbeq : (dbTable == t) = false := by
      simp only [beq_eq_false_iff_ne]; exact fun h => ht h.symm
    simp [Id.run, pure, Statement.references_table, TableRef.references_table,
      ColumnsRef.references_table, TableId.matchesName, hbeq]
  · simp [Id.run, pure, Statement.renderedColumns]
-- proof-end

#print axioms correct__create_unique_sql
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) audit for django__django-14434 (lean).

SAME-SPEC CONFIRMED for all 8 attacks via swebench_unified.markers.same_spec (all True; only impl+proof regions edited, axioms/pure/pre/post byte-identical).

### ATTACKS (each built by editing only the impl region; verified with `bash scripts/lean_verify.sh <f>`):
- atk_1 (PREPATCH BUG, wrapped Table object -> TableId.wrapped): exit=1 (gold proof does not close). prepatch_reproduced=true. Disproof dis_1.lean compiles exit=0 => provably violates conjunct 1.
- atk_2 (columns.reverse, breaks renderedColumns): exit=1. dis_2 exit=0 (violates conjunct 5).
- atk_3 (columns++columns duplication): exit=1. dis_3 exit=0 (conjunct 5).
- atk_4 (tablePart.name := "", references wrong/no table): exit=1. dis_4 exit=0 (conjunct 4, references_table t=false fails at t="").
- atk_5 (partial-domain: columns := [] always): exit=1. dis_5 exit=0 (conjunct 1).
- atk_6 (ungrounded-oracle echo: tableId := .name (dbTable++"`_x`")): exit=1. dis_6 exit=0 (conjunct 1).
- atk_7 (control-flow-effect: columns.take 1 truncation): exit=1. dis_7 exit=0 (conjunct 5).
- atk_8 (observational-equivalence CONTROL: columns.reverse.reverse): exit=0, CLOSES with clean axioms [propext, Classical.choice, Quot.sound].

**DISPROOFS:** dis_1..dis_7 are machine-checked `example : ¬ problem_spec ... := by ...` files (, all lean_verify exit=0), rigorously proving atk_1..7 each violate the frozen spec => no closing proof can exist for any of them. Ran concurrently in batches of <=4.

Only atk_8 closes (clean axioms). Per protocol its faithful patch was MATERIALIZED (patch_atk_8.diff, applies clean to base worktree) and RUN through the official harness. run_resolve wrapper initially returned 'no report' (transient image-pull/contention artifact, empty log dir), so I ran the harness directly via `docker -c python -m swebench_unified.run_evaluation ...` (run_id sbu-atk8-14434-3613577): COMPLETED, RESOLVED=1, FAIL_TO_PASS test_unique_constraint SUCCESS, all PASS_TO_PASS success. report.json at report.json shows resolved:true. => verify => correct holds for the sole closing candidate.

**POSITIVE CONTROL:** gold Solution.lean (pos_gold.lean) lean_verify exit=0, clean axioms.

A-LEG / REFINEMENT AUDIT: axioms region is EMPTY (no A-consumed). refinement.md ledger: all impl legs tagged R (type refinements Table-object->bare-string flowing into Columns.self.table); A-consumed=none; one A-reference fact (`Table object != str => TableColumns.references_column False`, modeled as TableId.matchesName (.wrapped _) _ = false). No kind-3 (changed-inexpressible) leg. The A-reference correspondence was VALIDATED against the REAL Django callees (django.db.backends.ddl_references Table/Columns at base_commit 5e04e84d67) by axiom_check.py: exit=0, checked=300, status=pass. Mapping.md line refs consistent with the real ddl_references.py source (Table 40-57, TableColumns 60-96, Statement 166-201). Gold patch (test.jsonl) matches the modeled fix: table = model.`_meta`.db_table (bare string) into Columns, Table(table,...) only on the table= kwarg.

**CONCLUSION:** The spec pins the observable Statement uniquely to gold; every same-spec wrong impl provably fails to close (7 disproofs), and the single closing same-spec impl resolves under the official harness. No verify-but-not-correct gap. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec models BaseDatabaseSchemaEditor.`_create_unique_sql` (columns!=[] / if columns: branch) at base_commit 5e04e84d67. Verified: (1) Solution.lean compiles via lean_verify.sh (exit 0), #print axioms clean = [propext, Classical.choice, Quot.sound], no sorryAx — proof genuine. (2) same_spec(Solution, Solution_prepatch, lean-backend) = True (spec region byte-identical). (3) conformance_check.py against the REAL repo ddl_references classes: 120,144 inputs, 0 disagreements. (4) Independent differential of all five spec conjuncts (references_column membership on dbTable; references_column=false for other tables; references_table(dbTable)=true; references_table=false for others; renderedColumns=columns verbatim) evaluated directly on the real Table/Columns/Statement objects across edge cases (duplicate columns, col==table name, empty strings, multiplicity, mixed case) and for BOTH name=None (IndexName part present) and name=str paths — all conjuncts hold. Faithfulness-break attempts failed: dropping the `name` part is safe because post-fix IndexName(table, columns) is a TableColumns subclass whose references_* answers coincide exactly with the columns part (same bare table string, same columns list), so no observable divergence; renderedColumns reads only the columns part. The spec is neither too strong nor drifting — no input distinguishes the model from the real callee. Not an echo/rubber-stamp: this is a genuine differential over the real repo behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage judged against public problem_statement ONLY (not hints_text). Public problem_statement: 'Statement created by `_create_unique_sql` makes references_column always false ... This is due to an instance of Table is passed as an argument to Columns when a string is expected.' — this already discloses the full fix mechanism (a Table object where a string is expected) and names `_create_unique_sql`, Statement, references_column.

Spec-view analysis (verified via markers.spec_view + same_spec):
- same_spec(Solution.lean, Solution_prepatch.lean) == True: the spec view is byte-identical between the buggy and fixed variants; the ONLY difference (impl: TableId.name table vs TableId.wrapped dbTable) lives entirely in the impl region, which the projection elides ('implementation elided — supplied by the consumer'). The proof region is also elided.
- The prepatch's narration comment ('-- Pre-fix: the columns part stores the wrapped table reference object...') sits inside the elided impl region and is NOT visible to the consumer.
- Mechanical leakage.screen() passes clean: no diff markers, no reproduced gold-patch line, no patched file path, no narration words, no spec-view identifier/comment embedding a distinctive patched symbol. Only distinctive changed symbol is 'create_unique_name' (nested helper), which does not appear in the spec view; '`_create_unique_sql`' is already public.
- The TableId model in the pure region (name = bare string that matches by string equality vs wrapped = reference object that never matches a string) encodes exactly the distinction the problem_statement already states publicly ('instance of Table ... when a string is expected'). It pins required behavior/postconditions, not the specific gold edit, and reveals nothing beyond the public task.

Gold edit (Table(...) -> bare string flowing into Columns.self.table) is not disclosed by any spec-view line beyond what problem_statement already makes public. No LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
