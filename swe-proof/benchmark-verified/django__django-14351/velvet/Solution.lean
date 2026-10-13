import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no deep-model reference to a library callee. The two
   unchanged steps this operation delegates to — asking the left operand, and the
   right operand, each for the columns it contributes to a grouping clause — are
   modeled as FREE inputs (`lhsCols`, `rhsCols`). The behaviour pinned here holds
   for EVERY value of those inputs, so they are owed no contract: the spec is
   strictly weaker than any concrete implementation of either delegated step
   (directive 7). The behaviour actually pinned — that when the right operand is a
   column-contributing sub-result that names no explicit output columns, its
   output-column list must be clamped to the single key column before it is used,
   and otherwise left exactly as it was — is stated directly in the
   postconditions. There is no module-level `axiom`. -/
-- axioms-end

-- pure-start
/- An opaque identity for a column that may appear in an output list or a
   grouping clause. Only identity matters here (whether two such columns are the
   same object); nothing about internal content is constrained, because this
   operation neither inspects nor builds column content — it only decides WHICH
   columns appear and, conditionally, rewrites the right operand's output list. -/
structure Col where
  ref : Nat
  deriving DecidableEq, Inhabited

/- Whether the right operand's output-column list must be clamped before use:
   true exactly when the right operand is a column-contributing sub-result
   (`rhsIsExpr`) that does NOT already name an explicit output-column list
   (`¬ rhsHasSelectFields`). A direct value list contributes nothing to clamp; a
   sub-result that already names its output columns is left as-is. -/
def mustClamp (rhsIsExpr rhsHasSelectFields : Bool) : Bool :=
  rhsIsExpr && !rhsHasSelectFields

/- The right operand's output-column list after the operation, given the list it
   named on entry (`selectOld`) and the single key column. When the clamp
   applies, the output list becomes exactly the one key column; otherwise it is
   preserved unchanged. -/
def clampedSelect (rhsIsExpr rhsHasSelectFields : Bool)
    (selectOld : List Col) (pkCol : Col) : List Col :=
  if mustClamp rhsIsExpr rhsHasSelectFields then [pkCol] else selectOld

/- The columns this operation contributes to the grouping clause: always the left
   operand's columns, followed — only when the right operand is a
   column-contributing sub-result — by the right operand's columns. A direct value
   right operand contributes nothing. This is independent of the clamp: clamping
   the sub-result's output list does not change WHICH column object the
   sub-result contributes to the grouping clause. -/
def contributedCols (rhsIsExpr : Bool) (lhsCols rhsCols : List Col) : List Col :=
  if rhsIsExpr then lhsCols ++ rhsCols else lhsCols
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The grouping columns a membership test against a right operand contributes,
   with the output-shape reconciliation the desired behaviour demands.

   Two effects.

   First, the contributed grouping columns are assembled: the left operand's
   columns always, extended by the right operand's columns exactly when the right
   operand is itself a column-contributing sub-result (`rhsIsExpr`). A right
   operand that is a direct list of values contributes no grouping columns. This
   is the long-standing behaviour and is independent of the clamp below.

   Second — and this is the behaviour the desired outcome demands — when the right
   operand is a column-contributing sub-result that names NO explicit output
   columns, it would otherwise expose every default output column; used as a
   single-column membership operand or placed in a grouping clause this is
   ill-formed (it would return more than one column). So its output-column list
   must be clamped to the single key column before it is used. When the right
   operand already names an explicit output-column list, or is not a
   column-contributing sub-result at all, its output-column list is preserved
   exactly.

   `rhsSelect` is the right operand's output-column list — the one mutable carrier
   the operation writes (declared `mut`). It is pinned exactly per the
   reconciliation rule: the single key column when the clamp applies, and its
   entry value `rhsSelectOld` otherwise (directive 5: the changed frame to its
   exact post-state, the preserved frame against the entry value). The contributed
   grouping columns `out` are pinned to the assembly above. The delegated column
   observations `lhsCols`, `rhsCols` are read-only free inputs (not `mut`); the
   key column `pkCol` and the shape flags `rhsIsExpr`, `rhsHasSelectFields` are
   read-only. -/
method inGroupByCols (mut rhsSelect : List Col) (rhsIsExpr : Bool)
    (rhsHasSelectFields : Bool) (lhsCols : List Col) (rhsCols : List Col)
    (pkCol : Col) return (out : List Col)
  ensures rhsSelect = clampedSelect rhsIsExpr rhsHasSelectFields rhsSelectOld pkCol
  ensures out = contributedCols rhsIsExpr lhsCols rhsCols
  do
    -- impl-start
    -- Start the contributed grouping columns from the left operand's columns.
    let mut cols : List Col := lhsCols
    -- Only when the right operand is itself a column-contributing sub-result do
    -- we reconcile its output shape and fold in its columns.
    if rhsIsExpr then
      -- A sub-result that names no explicit output columns would expose every
      -- default output column; clamp its output list to the single key column so
      -- it is a well-formed single-column operand. A sub-result that already
      -- names its output columns is left untouched.
      if !rhsHasSelectFields then
        rhsSelect := [pkCol]
      else
        rhsSelect := rhsSelect
      cols := cols ++ rhsCols
    else
      rhsSelect := rhsSelect
    return cols
    -- impl-end

prove_correct inGroupByCols by
  loom_solve
  all_goals simp_all [clampedSelect, mustClamp, contributedCols]
