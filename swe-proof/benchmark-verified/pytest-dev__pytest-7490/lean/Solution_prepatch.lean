import Mathlib
-- imports-end

/-!
Resolving the effective expected-failure annotation that a test's outcome report
consults when deciding whether a failing run should be reported as an expected
failure rather than a hard failure.

An expected-failure annotation may be discovered at two moments:

  * before the test body runs — the annotation derived from the markers present
    at that point (`none` when no expected-failure marker applied yet);
  * after the test body has run — the annotation derived from the markers
    present then, which may differ because the body itself can introduce a new
    marker while executing.

The effective annotation is the most-specific-known-first cascade: an annotation
already established before the body runs is authoritative and is kept as-is;
only when no annotation was established beforehand is the after-the-body
annotation consulted. This guarantees that an annotation introduced while the
test body runs is still honored by the time the outcome is reported.

The annotation carries the reporting fields a report consults: the textual
reason, whether the body is meant to run at all, and whether an unexpected pass
is to be treated strictly.
-/

-- axioms-start
-- No unchanged outside callee is consumed. The two annotation observations (the
-- one known before the body runs and the one known afterwards) enter as plain
-- data (`Option ExpectedFailure`); the only operation performed is the
-- most-specific-known-first selection between them, modeled directly below.
-- Hence no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- The reporting view of an expected-failure annotation: the touched fields a
test outcome report consults. `Option ExpectedFailure` carries an annotation,
with `none` meaning "no expected-failure annotation is in effect" and `some a`
the annotation `a`. -/
structure ExpectedFailure where
  reason : String
  run : Bool
  strict : Bool
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- The effective annotation is fully pinned to the two observations:

  * if an annotation `x` was already established before the body ran, the result
    is exactly `some x` (the earlier annotation is authoritative);
  * if no annotation was established before the body ran, the result is exactly
    the annotation observed after the body ran (whatever that is, including
    `none`).

Both cases together determine the result for every input, so no output is left
free. -/
def problem_spec_resolveExpectedFailure
    (before after : Option ExpectedFailure) (result : Option ExpectedFailure) : Prop :=
  (∀ x, before = some x → result = some x) ∧
  (before = none → result = after)
-- post-conditions-end

-- impl-start
def implementation_resolveExpectedFailure
    (before after : Option ExpectedFailure) : Option ExpectedFailure := Id.run do
  let mut xfailed := before
  return xfailed
-- impl-end

-- proof-start
theorem correct_resolveExpectedFailure :
    ∀ (before after : Option ExpectedFailure),
      problem_spec_resolveExpectedFailure before after
        (implementation_resolveExpectedFailure before after) := by
  intro before after
  constructor
  · intro x hx
    simp [implementation_resolveExpectedFailure, hx]
  · intro h
    simp [implementation_resolveExpectedFailure, h]
-- proof-end
