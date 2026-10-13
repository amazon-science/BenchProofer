import Mathlib
-- imports-end

/-!
Assembling the keyword-argument mapping handed to the histogram-count routine.

Before the counts are computed, a small keyword mapping is built up from the
plotting call's options. Two entries are relevant here:

* a `range` entry, which sets the lower/upper bounds of the histogram. It is
  added exactly when the call follows the single-or-empty-dataset path (the path
  that does not pre-compute shared bin edges);
* a `density` entry, which requests that the counts be normalised to a
  probability density. It is added exactly when a density result is requested and
  the datasets are not being stacked.

The desired behaviour is that these two entries are assembled independently:
adding the `density` entry must NOT disturb a `range` entry that was already
placed in the mapping. Equivalently, the final mapping carries the `range` entry
whenever the single-or-empty-dataset path requested explicit bounds, regardless of
whether a `density` entry was also added; and it carries the `density` entry
whenever a non-stacked density result was requested, regardless of whether bounds
were also requested.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The modeled
-- behaviour is the pure assembly of a small keyword mapping from already-resolved
-- option values, so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- The small keyword mapping handed to the histogram-count routine. Each entry
is optional: `none` means the key is absent from the mapping, `some v` means the
key is present with value `v`.

* `range` — optional explicit `(lower, upper)` bounds (exact rationals stand in
  for the float bounds, which are only stored and passed through);
* `density` — optional normalise-to-density request. -/
structure HistKeywordArgs where
  range : Option (Rat × Rat)
  density : Option Bool
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- The assembled mapping carries the `range` entry exactly when explicit bounds
were requested (and then equal to those bounds), and the `density` entry exactly
when a non-stacked density result was requested (and then equal to that request).
Both components are pinned to the inputs, so adding one entry can never silently
drop or alter the other. -/
def problem_spec_assembleHistKeywordArgs
    (setRange : Bool) (binRange : Rat × Rat)
    (densityFlag stacked : Bool) (result : HistKeywordArgs) : Prop :=
  result.range = (if setRange then some binRange else none) ∧
  result.density = (if densityFlag && !stacked then some densityFlag else none)
-- post-conditions-end

-- impl-start
def implementation_assembleHistKeywordArgs
    (setRange : Bool) (binRange : Rat × Rat)
    (densityFlag stacked : Bool) : HistKeywordArgs := Id.run do
  let mut hk : HistKeywordArgs := { range := none, density := none }
  if setRange then
    hk := { hk with range := some binRange }
  if densityFlag && !stacked then
    hk := { hk with density := some densityFlag }
  return hk
-- impl-end

-- proof-start
theorem correct_assembleHistKeywordArgs :
    ∀ (setRange : Bool) (binRange : Rat × Rat) (densityFlag stacked : Bool),
      problem_spec_assembleHistKeywordArgs setRange binRange densityFlag stacked
        (implementation_assembleHistKeywordArgs setRange binRange densityFlag stacked) := by
  intro setRange binRange densityFlag stacked
  unfold problem_spec_assembleHistKeywordArgs implementation_assembleHistKeywordArgs
  cases setRange <;> cases densityFlag <;> cases stacked <;> exact ⟨rfl, rfl⟩
-- proof-end
