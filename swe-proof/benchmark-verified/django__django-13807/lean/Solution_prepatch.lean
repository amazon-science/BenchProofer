import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature: the identifier-quoting helper
-- is a tiny, total string operation, so it is modeled DEEPLY (`quoteIdentifier`,
-- below) and validated against the real callee by G-AX (A-reference) rather than
-- axiomatized. The proof agent may add `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- Render a SQL identifier so that a reserved word is treated as a name rather
than as syntax: the identifier is wrapped in double quotes. If it is already
double-quoted (it both begins and ends with a double-quote character) it is left
unchanged, so quoting is idempotent. -/
def quoteIdentifier (name : List Char) : List Char :=
  if name.head? = some '"' ∧ name.getLast? = some '"' then
    name
  else
    ['"'] ++ name ++ ['"']
-- pure-end

-- post-conditions-start
/-- The three constraint-check query strings built for a single table from its
table name and the relevant primary-key / foreign-key column names. Every
identifier that is substituted into a query is rendered with `quoteIdentifier`;
all surrounding literal SQL text (PRAGMA names, parentheses, separators, the
`SELECT … FROM … WHERE rowid = %s` skeleton) is pinned exactly. -/
def problem_spec_fkCheckQueries
    (table primaryKey column : List Char)
    (result : List Char × List Char × List Char) : Prop :=
  result.1 =
      "PRAGMA foreign_key_check(".toList ++ quoteIdentifier table ++ [')'] ∧
  result.2.1 =
      "PRAGMA foreign_key_list(".toList ++ quoteIdentifier table ++ [')'] ∧
  result.2.2 =
      "SELECT ".toList ++ quoteIdentifier primaryKey ++ ", ".toList
        ++ quoteIdentifier column ++ " FROM ".toList ++ quoteIdentifier table
        ++ " WHERE rowid = %s".toList
-- post-conditions-end

-- impl-start
def implementation_fkCheckQueries
    (table primaryKey column : List Char) :
    List Char × List Char × List Char := Id.run do
  -- Pre-patch (buggy): the identifiers are interpolated RAW (no quoting), so a
  -- reserved-word name is parsed as SQL syntax instead of as an identifier.
  let fkCheck :=
    "PRAGMA foreign_key_check(".toList ++ table ++ [')']
  let fkList :=
    "PRAGMA foreign_key_list(".toList ++ table ++ [')']
  let selectRow :=
    "SELECT ".toList ++ primaryKey ++ ", ".toList
      ++ column ++ " FROM ".toList ++ table
      ++ " WHERE rowid = %s".toList
  return (fkCheck, fkList, selectRow)
-- impl-end

-- proof-start
theorem correct_fkCheckQueries :
    ∀ (table primaryKey column : List Char),
    problem_spec_fkCheckQueries table primaryKey column
      (implementation_fkCheckQueries table primaryKey column) := by
  sorry   -- carries the gold proof body; UNCLOSABLE against the buggy impl (G-DIFF)
-- proof-end
