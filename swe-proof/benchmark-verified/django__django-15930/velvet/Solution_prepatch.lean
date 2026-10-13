import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms. The always-true predicate that the empty-condition case
--  falls back to is modeled DEEPLY as its concrete compiled form — a constant,
--  non-empty placeholder fragment binding one literal-true parameter. That form
--  is validated == the real callee out-of-band by axiom_check.py (G-AX) as an
--  A-reference, not consumed here.)
-- axioms-end

-- pure-start
/- A compiled SQL fragment: the fragment text together with the ordered list of
   parameters it binds. Both an incoming branch condition and the always-true
   substitute are carried in this one shape. Text is modeled per byte as
   `List Char`; a bound parameter is carried by an integer identity
   (mapping.md §2). -/
structure Compiled where
  sql : List Char
  params : List Int
  deriving DecidableEq

/- The compiled form of the always-true predicate the branch falls back to when
   its own condition compiles to nothing: a single non-empty placeholder
   fragment binding one literal-true parameter (the integer identity `1` carries
   the literal true, mapping.md §2). Concrete data, validated == the real callee
   by axiom_check.py (G-AX) as an A-reference. -/
def truePredicate : Compiled := { sql := "%s".toList, params := [1] }

/- Assemble one conditional branch from a compiled condition and a compiled
   consequent: the branch text splices both fragments into the constant
   "WHEN <condition> THEN <result>" template, and the branch binds the
   condition's parameters followed by the consequent's. -/
def branchClause (cond : Compiled) (res : Compiled) : Compiled :=
  { sql := "WHEN ".toList ++ cond.sql ++ " THEN ".toList ++ res.sql,
    params := cond.params ++ res.params }
-- pure-end

/- Assemble one conditional branch of a multi-branch selection expression from
   its already-compiled condition and consequent fragments.

   Desired behaviour: a condition that matches every row compiles to EMPTY
   fragment text. Splicing that empty text into the branch template would yield
   a branch with no predicate between the keywords — invalid syntax. So when the
   incoming condition's text is empty, the assembled branch must instead use a
   NON-EMPTY always-true predicate as its condition (text and bound parameters
   both taken from that predicate); a condition whose text is non-empty is used
   unchanged. The consequent fragment is always used as-is.

   The two input fragments are read-only (neither is `mut`); nothing is mutated
   (directive 5). -/
-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method assembleConditionalBranch (cond : Compiled) (res : Compiled)
    return (out : Compiled)
  ensures cond.sql ≠ [] → out = branchClause cond res
  ensures cond.sql = []  → out = branchClause truePredicate res
  do
    -- impl-start
    -- Pre-image skeleton: the incoming condition is spliced into the branch
    -- template directly, with no special handling of an empty condition. When
    -- the condition's text is empty this assembles a branch whose predicate
    -- slot is empty — the frozen spec requires the always-true substitute in
    -- that case, so prove_correct MUST fail.
    return branchClause cond res
    -- impl-end

prove_correct assembleConditionalBranch by
  loom_solve
