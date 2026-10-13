import Mathlib
-- imports-end

/-!
Selecting the best result among several independent repeated attempts.

A procedure is run several times, once per entry of a given list of independent
configuration values supplied by the caller. Each value drives one self-contained
attempt that yields an *outcome* — a numeric cost together with the data the
attempt produced. The attempts do not interact: an attempt's outcome is a
function of its own configuration value alone.

The procedure keeps the single best outcome, "best" meaning lowest cost. When
several attempts tie for the lowest cost, the earliest of them (the one driven by
the configuration value appearing first in the list) is the one kept. The whole
chosen outcome is returned verbatim — both its cost and its produced data come
from one and the same attempt.

Because the selection is a deterministic function of the supplied list of
configuration values, the result does not depend on the order in which the
attempts happen to be evaluated or on how the work is distributed. The behavior
is stated abstractly as an input→output relation; the implementation and
correctness proof are supplied separately.
-/

-- axioms-start
/-- The outcome of one self-contained attempt: a numeric `cost` used to rank
attempts (lower is better) together with the `data` that attempt produced. Cost
is modeled by an exact integer because only its ORDER is observed by the
selection (the real quantity is compared with `<` / argmin only). -/
structure Outcome where
  cost : Int
  data : List Int
deriving Inhabited, DecidableEq

/-- Run one self-contained attempt for a given configuration value. This is an
UNCHANGED downstream routine: deterministic in its argument and observed only
through its returned outcome. Declared `opaque` so it can appear in the
executable implementation; the proof consumes no property of it (the selection is
correct for ANY such routine), so no `_prop` axiom is asserted. -/
opaque runTrial : Int → Outcome
-- axioms-end

-- pure-start
-- No additional pure helpers: the selection is spelled out in the impl region.
-- pure-end

-- post-conditions-start
/-- The result is the outcome of the earliest minimum-cost attempt:

* there is an index `i` into the configuration list such that the result IS the
  outcome of running attempt `i` (frame: every component of the result — cost and
  produced data — comes from this one attempt);
* no attempt has a strictly lower cost than the result (global minimum);
* every attempt strictly EARLIER than `i` has a strictly greater cost (so `i` is
  the first index attaining the minimum — the tie-break the procedure uses). -/
def problem_spec_bestTrial (trials : List Int) (result : Outcome) : Prop :=
  ∃ i : Fin trials.length,
    result = runTrial (trials.get i) ∧
    (∀ j : Fin trials.length, result.cost ≤ (runTrial (trials.get j)).cost) ∧
    (∀ j : Fin trials.length, j.val < i.val →
        result.cost < (runTrial (trials.get j)).cost)
-- post-conditions-end

-- impl-start
-- PRE-PATCH (buggy) skeleton: the repeated attempts are NOT driven by the
-- supplied configuration values. The loop runs over the attempt positions and
-- drives each attempt with the position index instead of the corresponding
-- supplied value, so the selected outcome is not `runTrial (trials.get i)` for
-- any minimum index `i` of the supplied list.
def implementation_bestTrial (trials : List Int) : Outcome := Id.run do
  let mut best : Option Outcome := none
  for p in [0:trials.length] do
    let o := runTrial (Int.ofNat p)
    match best with
    | none   => best := some o
    | some b => if o.cost < b.cost then best := some o
  return best.getD default
-- impl-end

-- proof-start
-- Gold proof body carried over; it does NOT close against the buggy impl: the
-- result comes from `runTrial (index)`, not from `runTrial (trials.get i)`, so the
-- discriminating clause `result = runTrial (trials.get i)` cannot be discharged.
theorem correct_bestTrial :
    ∀ (trials : List Int), trials ≠ [] →
      problem_spec_bestTrial trials (implementation_bestTrial trials) := by
  sorry
-- proof-end
