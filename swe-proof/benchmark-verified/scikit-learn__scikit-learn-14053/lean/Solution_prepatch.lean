import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature: the per-entry label lookup is
-- modeled DEEPLY (a total list index, below) rather than axiomatized. The proof
-- agent may add `_prop` axioms only if genuinely stuck.
-- axioms-end

-- pure-start
/-- A designated sentinel index value that marks an entry having no associated
name (as opposed to a genuine, in-range position into the name list). -/
def sentinelIndex : Int := -2

/-- Resolve one index against the name list. A sentinel index yields no name
(`none`); any other index looks the name up by position, yielding `some name`
when it is in range. -/
def featureNameAt (featureNames : List String) (i : Int) : Option String :=
  if i ≠ sentinelIndex then featureNames[i.toNat]? else none

/-- Front-recursive specification fold: resolve each index in order. -/
def featureNamesSpec (featureNames : List String) : List Int → List (Option String)
  | [] => []
  | i :: rest => featureNameAt featureNames i :: featureNamesSpec featureNames rest
-- pure-end

-- post-conditions-start
/-- The result is exactly the per-entry resolution of the index list against the
name list, in order: an entry whose index is the sentinel resolves to no name
(`none`), and every other entry resolves to the name at that position. -/
def problem_spec_featureNamesByNode
    (featureNames : List String) (features : List Int)
    (result : List (Option String)) : Prop :=
  result = featureNamesSpec featureNames features
-- post-conditions-end

-- impl-start
def implementation_featureNamesByNode
    (featureNames : List String) (features : List Int) : List (Option String) :=
  Id.run do
    let mut acc : List (Option String) := []
    for i in features do
      acc := acc ++ [featureNames[i.toNat]?]
    return acc
-- impl-end

-- proof-start
theorem correct_featureNamesByNode :
    ∀ (featureNames : List String) (features : List Int),
      problem_spec_featureNamesByNode featureNames features
        (implementation_featureNamesByNode featureNames features) := by
  sorry   -- carries the gold proof obligation; UNCLOSABLE against the buggy impl (G-DIFF)
-- proof-end
