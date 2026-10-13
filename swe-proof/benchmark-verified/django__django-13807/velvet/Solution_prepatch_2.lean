import Velvet.Std
-- imports-end

-- Total-correctness semantics: the real statement builders are finite passes
-- over the input lists that always return their statement sequences (the F2P
-- test observes those return values), so the spec must also rule out
-- implementations that diverge — under partial correctness a non-terminating
-- body would vacuously satisfy every postcondition.
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No unchanged callee is axiomatized. The one routine the construction below
   relies on — the backend's SQL identifier quoter — is modeled DEEPLY by
   `quoteIdent` (pure region), validated `quoteIdent == the real quoter` by
   axiom_check.py (G-AX). It is therefore an A-reference, not a consumed axiom
   (mapping.md §3). Everything observable is computed from the inputs; nothing
   is borrowed from an oracle. -/
-- axioms-end

-- pure-start
/- The backend's SQL identifier quoter (deep model, A-reference). A bare
   identifier is wrapped in double quotes so it cannot collide with reserved
   words; an identifier that is already double-quoted is returned unchanged
   (quoting once is enough). This is the per-identifier transform the statement
   builders below apply at every position where an identifier is embedded in a
   statement. Soundness vs the real quoter: mapping.md §3 / axiom_check.py. -/
def quoteIdent (name : List Char) : List Char :=
  if name.head? = some '"' ∧ name.getLast? = some '"' then name
  else '"' :: (name ++ ['"'])

/- The integrity-check statement for one table: a constant prefix, the table
   identifier (quoted), and the closing parenthesis. -/
def fkCheckSql (table : List Char) : List Char :=
  "PRAGMA foreign_key_check(".toList ++ quoteIdent table ++ ")".toList

/- The foreign-key-listing statement for one table (quoted identifier). -/
def fkListSql (table : List Char) : List Char :=
  "PRAGMA foreign_key_list(".toList ++ quoteIdent table ++ ")".toList

/- The value-fetch statement for one offending row: a SELECT of the primary-key
   column and the referencing column from the table, all three identifiers
   quoted, with the row addressed by a bound parameter. -/
def selectSql (pk col table : List Char) : List Char :=
  "SELECT ".toList ++ quoteIdent pk ++ ", ".toList ++ quoteIdent col
    ++ " FROM ".toList ++ quoteIdent table ++ " WHERE rowid = %s".toList

/- The list of integrity-check statements produced for a list of table names:
   one statement per table, in order. Front-recursive so a single unfold is
   available per loop step (the fold pattern, plan §5.4). -/
def checkStmts : List (List Char) → List (List Char)
  | []      => []
  | t :: ts => fkCheckSql t :: checkStmts ts

@[grind] lemma checkStmts_nil : checkStmts [] = [] := rfl
@[grind] lemma checkStmts_cons (t : List Char) (ts : List (List Char)) :
    checkStmts (t :: ts) = fkCheckSql t :: checkStmts ts := rfl

/- One offending row, identified by the three identifiers the value-fetch needs:
   the table, its primary-key column, and the referencing column. -/
structure Violation where
  table : List Char
  pk : List Char
  col : List Char
deriving Inhabited, DecidableEq

/- The statements produced while processing a list of offending rows: per row,
   first its foreign-key-listing statement, then its value-fetch statement, in
   that order. Front-recursive (two statements peeled per row). -/
def violationStmts : List Violation → List (List Char)
  | []      => []
  | v :: vs => fkListSql v.table :: selectSql v.pk v.col v.table :: violationStmts vs

@[grind] lemma violationStmts_nil : violationStmts [] = [] := rfl
@[grind] lemma violationStmts_cons (v : Violation) (vs : List Violation) :
    violationStmts (v :: vs)
      = fkListSql v.table :: selectSql v.pk v.col v.table :: violationStmts vs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build, in order, the integrity-check statement for each table name. The input
   `tables` is read-only (not `mut`): the method threads a fresh accumulator and
   never mutates what it is handed (directive 5). Each table identifier embedded
   in a statement is the quoted form, so a reserved word used as a table name is
   safe. -/
method buildCheckStatements (tables : List (List Char)) return (out : List (List Char))
  ensures out = checkStmts tables
  do
    -- impl-start
    let mut result : List (List Char) := []
    let mut i := tables.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ tables.length
      invariant result = checkStmts (tables.drop i)
      done_with i = 0
      decreasing i
    do
      let t := tables[i - 1]!
      result := fkCheckSql t :: result
      i := i - 1
    return result
    -- impl-end

/- Build, in order, the per-row statements (listing then value-fetch) for each
   offending row. `violations` is read-only (not `mut`). Every identifier — the
   table, the primary-key column, the referencing column — embedded in a
   statement is the quoted form. -/
method buildViolationStatements (violations : List Violation) return (out : List (List Char))
  ensures out = violationStmts violations
  do
    -- impl-start
    let mut result : List (List Char) := []
    let mut i := violations.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ violations.length
      invariant result = violationStmts (violations.drop i)
      done_with i = 0
      decreasing i
    do
      let v := violations[i - 1]!
      -- Pre-image skeleton: the table/column identifiers are embedded raw, NOT
      -- through the identifier quoter, in both the listing statement and the
      -- value-fetch SELECT. The frozen spec requires `violationStmts` (which
      -- quotes via fkListSql/selectSql), so prove_correct MUST fail.
      let rawList := "PRAGMA foreign_key_list(".toList ++ v.table ++ ")".toList
      let rawSelect := "SELECT ".toList ++ v.pk ++ ", ".toList ++ v.col
        ++ " FROM ".toList ++ v.table ++ " WHERE rowid = %s".toList
      result := rawList :: rawSelect :: result
      i := i - 1
    return result
    -- impl-end

/- Backward-fold step: dropping one fewer table exposes the table at `i-1` on the
   front, so `checkStmts` peels one statement. The single goal `loom_solve`
   leaves for the loop body. -/
lemma checkStmts_drop_step (tables : List (List Char)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ tables.length) :
    checkStmts (tables.drop (i - 1)) = fkCheckSql tables[i - 1]! :: checkStmts (tables.drop i) := by
  have hlt : i - 1 < tables.length := by omega
  have hcons : tables.drop (i - 1) = tables[i - 1]! :: tables.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, checkStmts_cons]

/- Backward-fold step for the per-row statements: dropping one fewer row exposes
   the row at `i-1`, so `violationStmts` peels its two statements. -/
lemma violationStmts_drop_step (violations : List Violation) (i : Nat)
    (hi : 0 < i) (hle : i ≤ violations.length) :
    violationStmts (violations.drop (i - 1))
      = fkListSql violations[i - 1]!.table
          :: selectSql violations[i - 1]!.pk violations[i - 1]!.col violations[i - 1]!.table
          :: violationStmts (violations.drop i) := by
  have hlt : i - 1 < violations.length := by omega
  have hcons : violations.drop (i - 1) = violations[i - 1]! :: violations.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, violationStmts_cons]

prove_correct buildCheckStatements by
  loom_solve
  rw [checkStmts_drop_step tables i (by omega) (by omega)]
  simp_all

prove_correct buildViolationStatements by
  loom_solve
  rw [violationStmts_drop_step violations i (by omega) (by omega)]
  simp_all
