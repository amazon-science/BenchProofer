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
