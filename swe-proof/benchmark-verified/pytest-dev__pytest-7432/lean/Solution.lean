import Mathlib
-- imports-end

/-!
Reporting the source location of a test that was skipped by a skip mark.

When a test is skipped because it carries a skip mark, the location shown in the
skip summary should point at the test's own definition, rather than at the
internal framework site where the skip was raised. Concretely, the framework
rewrites the reported location of such a skip to the test item's own location.

This location rewrite is governed solely by the conditions that identify a
mark-skipped result whose reported location is a structured (filename, line,
reason) triple:

* the result was skipped by a skip mark;
* the reported outcome is "skipped";
* the reported location is the structured triple form.

Crucially, this rewrite is an independent decision: it must happen whenever those
conditions hold, regardless of how the result was handled by the separate
expected-failure dispatch (including the option that only governs expected
failures). The expected-failure dispatch — handling an unexpected success on the
call phase, the option that suppresses expected-failure treatment, a raised
expected-failure signal, or a non-skipped result carrying an expected-failure
mark — selects among mutually exclusive cases but does not gate the location
rewrite.

The decision modeled here is exactly: was the skip location rewritten to point at
the test item?
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The decision is
-- modeled structurally over the observable conditions of the reported result —
-- which dispatch case the expected-failure handling selects, and whether the
-- result is a mark-skipped result whose location is a structured triple — each of
-- which enters as a plain Boolean observation. The unchanged computation of the
-- rewritten location itself (deriving the item's own filename and line) is not
-- altered and is out of scope here. Hence no `opaque`/`axiom` callee contract is
-- needed.
-- axioms-end

-- pure-start
/-- The conditions that identify a mark-skipped result whose reported location is
the structured (filename, line, reason) triple form:

* `skippedByMark` — the result was skipped by a skip mark;
* `repSkipped` — the reported outcome is "skipped";
* `longreprIsTuple` — the reported location is the structured triple.

The location rewrite is arranged exactly when all three hold. -/
def skipLocationCondition (skippedByMark repSkipped longreprIsTuple : Bool) : Bool :=
  skippedByMark && repSkipped && longreprIsTuple
-- pure-end

-- post-conditions-start
/-- The skip-location rewrite decision is exactly the mark-skipped-triple
condition, and nothing else: the rewrite happens precisely when the result is a
mark-skipped result whose reported location is the structured triple. In
particular the decision is independent of the expected-failure dispatch inputs —
including the option that only governs expected-failure handling. -/
def problem_spec_skipLocationRewrite
    (unexpSuccess runxfail xfailRaised notSkippedXfail
     skippedByMark repSkipped longreprIsTuple : Bool) (result : Bool) : Prop :=
  result = skipLocationCondition skippedByMark repSkipped longreprIsTuple
-- post-conditions-end

-- impl-start
def implementation_skipLocationRewrite
    (unexpSuccess runxfail xfailRaised notSkippedXfail
     skippedByMark repSkipped longreprIsTuple : Bool) : Bool := Id.run do
  let mut locationRewritten := false
  -- Expected-failure dispatch: select among mutually exclusive cases (an
  -- unexpected success on the call phase; the option that suppresses
  -- expected-failure treatment; a raised expected-failure signal; a non-skipped
  -- result carrying an expected-failure mark). None of these arms touch the skip
  -- location.
  if unexpSuccess then
    pure ()
  else if runxfail then
    pure ()
  else if xfailRaised then
    pure ()
  else if notSkippedXfail then
    pure ()
  -- Independent of the dispatch above: rewrite the reported location of a
  -- mark-skipped, structured-triple result to point at the test item.
  if skippedByMark && repSkipped && longreprIsTuple then
    locationRewritten := true
  return locationRewritten
-- impl-end

-- proof-start
theorem correct_skipLocationRewrite :
    ∀ (unexpSuccess runxfail xfailRaised notSkippedXfail
       skippedByMark repSkipped longreprIsTuple : Bool),
      problem_spec_skipLocationRewrite
        unexpSuccess runxfail xfailRaised notSkippedXfail
        skippedByMark repSkipped longreprIsTuple
        (implementation_skipLocationRewrite
          unexpSuccess runxfail xfailRaised notSkippedXfail
          skippedByMark repSkipped longreprIsTuple) := by
  intro unexpSuccess runxfail xfailRaised notSkippedXfail
        skippedByMark repSkipped longreprIsTuple
  unfold problem_spec_skipLocationRewrite implementation_skipLocationRewrite skipLocationCondition
  cases unexpSuccess <;> cases runxfail <;> cases xfailRaised <;> cases notSkippedXfail <;>
    cases skippedByMark <;> cases repSkipped <;> cases longreprIsTuple <;> rfl
-- proof-end
