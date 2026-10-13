import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No axioms. This operation's behaviour is a decision over the values produced
   by its helper calls: the set of candidate identifiers discovered for the
   target columns, and the canonical identifier the same naming scheme would
   assign. Those helper results are taken as opaque method inputs, so the
   contract holds for every possible helper output and assumes no callee
   property. Helper provenance is recorded in mapping.md §3; G-AX is vacuous. -/
-- axioms-end

-- pure-start
/- Narrow a set of candidate identifiers to a single canonical one exactly when:
   the selection is by uniqueness, the candidate set is non-empty, several
   co-located selectors are permitted at once, and the canonical identifier is
   itself among the candidates. Otherwise the candidate set is returned as-is. -/
def narrowed (names : List String) (uniqueSel allowMultiple : Bool)
    (canonical : String) : List String :=
  if uniqueSel = true ∧ names ≠ [] ∧ allowMultiple = true then
    if canonical ∈ names then [canonical] else names
  else
    names

/- The single target the operation may act on: defined precisely when the
   narrowed candidate set is a singleton (its element); otherwise no unique
   target exists and the operation cannot proceed. -/
def selectedTarget (names : List String) (uniqueSel allowMultiple : Bool)
    (canonical : String) : Option String :=
  let ns := narrowed names uniqueSel allowMultiple canonical
  if ns.length = 1 then ns[0]? else none
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method chooseTarget (names : List String) (uniqueSel : Bool) (allowMultiple : Bool)
    (canonical : String) return (out : Option String)
  ensures out = selectedTarget names uniqueSel allowMultiple canonical
  do
    -- impl-start
    -- Pre-image skeleton: the candidate set is used as discovered, with no
    -- narrowing step, so several co-located candidates leave no unique target
    -- even when the canonical one is present. The frozen spec demands the
    -- narrowing (selectedTarget), so prove_correct MUST fail.
    let ns := names
    let result : Option String := if ns.length = 1 then ns[0]? else none
    return result
    -- impl-end

prove_correct chooseTarget by
  loom_solve <;>
    simp_all [narrowed, selectedTarget] <;>
    split_ifs <;>
    simp_all
