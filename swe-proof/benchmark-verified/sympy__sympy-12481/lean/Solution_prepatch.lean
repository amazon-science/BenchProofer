import Mathlib
-- imports-end

/-!
Building a permutation from a list of cycles given in cyclic notation.

A permutation on `{0, 1, …, n-1}` can be described by a list of cycles. Each
cycle is a list of distinct points `[a₀, a₁, …, a_{k-1}]` and denotes the rule
that sends `a₀ ↦ a₁ ↦ … ↦ a_{k-1} ↦ a₀`, leaving every other point unmoved.

When several cycles are supplied they are *composed in left-to-right order*: the
first cycle is applied first, then the second to that result, and so on. The
cycles need not move disjoint sets of points — a point may appear in more than
one cycle, in which case the successive rules simply chain through it. The size
of the resulting permutation is one more than the largest point named by any
cycle (so every point from `0` up to that maximum is listed), and the result is
returned in *array form*: the list whose `i`-th entry is the image of `i` under
the composed permutation.

A supplied-but-pointless list of cycles is the one degenerate case: if at least
one cycle is handed over yet no cycle names any point at all, the width of the
array form is not determined by the input and nothing is returned.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the action of a single
-- cycle and the left-to-right composition of several cycles are both spelled out
-- concretely (the `applyCycle` / `applyAll` helpers below), so there is nothing
-- to axiomatize — the modeled behavior is validated directly against the real
-- routine by the differential conformance check (an A-reference).
-- axioms-end

-- pure-start
/-- The image of `x` under a single cycle `c` listed as `[a₀, …, a_{k-1}]`:
if `x` occurs in `c` it is sent to the next entry cyclically (`a_{k-1} ↦ a₀`);
otherwise `x` is left unmoved. -/
def applyCycle (c : List Nat) (x : Nat) : Nat :=
  if c.contains x then c.getD ((c.idxOf x + 1) % c.length) x else x

/-- The image of `x` under the left-to-right composition of all `cycles`
(first cycle applied first). -/
def applyAll (cycles : List (List Nat)) (x : Nat) : Nat :=
  cycles.foldl (fun v c => applyCycle c v) x

/-- One past the largest point named by any cycle (`0` when no point is named).
This is the number of entries in the array form. -/
def permSize (cycles : List (List Nat)) : Nat :=
  cycles.flatten.foldl (fun m x => max m (x + 1)) 0

/-- The degenerate shape: at least one cycle was supplied, yet between them the
cycles name no point at all, so the array form has no determined width. -/
def sizeUndetermined (cycles : List (List Nat)) : Bool :=
  !cycles.isEmpty && permSize cycles == 0
-- pure-end

-- post-conditions-start
/-- Two legs, selected by whether the input determines a width.

* Degenerate leg (`sizeUndetermined cycles`): nothing is returned.
* Otherwise the construction succeeds (`result = some aform`) and `aform` is the
  array form of the left-to-right composition of `cycles`: it has
  `permSize cycles` entries (one per point from `0` to the maximum named), and
  its `i`-th entry is the image of `i` under the composed permutation. -/
def problem_spec_permFromCycles
    (cycles : List (List Nat)) (result : Option (List Nat)) : Prop :=
  (sizeUndetermined cycles = true → result = none) ∧
  (sizeUndetermined cycles = false →
    ∃ aform, result = some aform ∧
      aform.length = permSize cycles ∧
      (∀ i, i < permSize cycles → aform.getD i 0 = applyAll cycles i))
-- post-conditions-end

-- impl-start
-- PRE-PATCH (buggy) skeleton: when any point is named by more than one cycle
-- (the combined list of all named points has a repeat), the construction is
-- rejected and nothing is returned — even though the cycles compose perfectly
-- well. Only the all-distinct case is built.
def implementation_permFromCycles
    (cycles : List (List Nat)) : Option (List Nat) := Id.run do
  if ¬ cycles.flatten.Nodup then
    return none
  if sizeUndetermined cycles then
    return none
  let sz := permSize cycles
  let mut aform : List Nat := []
  for i in [0:sz] do
    let mut v := i
    for c in cycles do
      v := applyCycle c v
    aform := aform ++ [v]
  return some aform
-- impl-end


-- proof-start
-- Gold proof body carried over; it does NOT close against the buggy impl (when
-- the cycles share a point the impl returns `none`, contradicting the
-- success leg of the postcondition).
theorem correct_permFromCycles :
    ∀ (cycles : List (List Nat)),
      (∀ c ∈ cycles, c.Nodup) →
      problem_spec_permFromCycles cycles
        (implementation_permFromCycles cycles) := by
  sorry

-- proof-end
