import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

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
    -- Pre-image skeleton: the carrier threaded into the columns reference is the
    -- opaque table-WRAPPER object, not the bare table name. The columns
    -- reference then compares that object against a plain queried name by
    -- identity, which never holds, so referencesColumn is always false. The
    -- frozen spec demands referencesColumn = (dbTable == t) ∧ col ∈ columns, so
    -- prove_correct MUST fail.
    let tableForColumns : TableSlot := TableSlot.wrapped dbTable
    let cols : ColumnsRef := { tableSlot := tableForColumns, columns := columns }
    let out : Stmt := { tableName := dbTable, cols := cols }
    return out
    -- impl-end

prove_correct buildUniqueStatement by
  loom_solve
