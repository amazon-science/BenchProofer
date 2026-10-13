import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The integer→text rendering is modeled deeply as
--  `toString`; the placeholder-substitution wrapper is an R-refinement identity
--  on the produced relative URL — see refinement.md / mapping.md. Nothing the
--  proof consumes is left to an axiom, so there is no axiom_check.py and G-AX
--  is skipped.)
-- axioms-end

-- pure-start
/- The relative URL, computed from a record's primary key, that locates that
   record's password-change sub-page from the record's own change page. The
   page is reached by ascending two levels (so the navigation does not depend on
   the identifier under which the change page itself was reached) and then
   descending into the keyed record's password sub-page. The key is rendered in
   its usual decimal text form. The leading and trailing literal segments are
   constant; only the keyed middle segment varies with the input. -/
@[grind] def relativeLink (key : Nat) : List Char :=
  "../../".toList ++ (toString key).toList ++ "/password/".toList
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the relative link for a record identified by `key`. The result must be
   exactly the two-levels-up, key-indexed password sub-page URL, so that the
   link resolves to the same target regardless of the identifier the record's
   change page was addressed by. `key` is a read-only input and is not mutated
   (directive 5). -/
method buildRelativeLink (key : Nat) return (link : List Char)
  ensures link = relativeLink key
  do
    -- impl-start
    return "../../".toList ++ (toString key).toList ++ "/password/".toList
    -- impl-end

prove_correct buildRelativeLink by
  loom_solve
