import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The routine that turns a set of fitted parameters
--  into per-sample labels is observed only through the free input
--  `labelsFor : Params → Labels`. The spec makes no behavioural claim about that
--  routine — it holds for EVERY function it could be — so there is nothing to
--  check against a real callee (no G-AX). The behaviour under spec — WHICH
--  parameter set the labels are computed from — is modeled deeply in the `impl`
--  region, no outside contract consumed. See mapping.md §3 / refinement.md.)
-- axioms-end

-- pure-start
/- A complete set of fitted model parameters, identified abstractly: the desired
   behaviour observes only WHICH parameter set the reported labels are derived
   from, never the concrete contents of a parameter set. -/
abbrev Params := Nat

/- The per-sample labels a routine reports: identified abstractly, since the only
   thing observed here is that they are exactly the labels the label-computing
   routine yields for some parameter set. -/
abbrev Labels := List Nat

/- The labels a caller should get from this fit.

   `storedParams` is the parameter set the fitted estimator stores — the one a
   later, separate label query against the same fitted estimator reads.
   `labelsFor` maps any parameter set to the labels it implies for the given data.
   The labels reported at fit time must be EXACTLY the labels that this same
   routine yields for the estimator's stored parameter set, so that asking the
   fitted estimator for labels a second time returns the same answer (the two
   paths agree). -/
def reportedLabels (storedParams : Params) (labelsFor : Params → Labels) : Labels :=
  labelsFor storedParams
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Compute the labels this fit reports to its caller.

   `transientParams` is a parameter set that may be in force partway through
   finalization but is not the one the fitted estimator ends up storing.
   `storedParams` is the parameter set the fitted estimator stores — the one a
   later, separate label query reads. `labelsFor` maps any parameter set to the
   labels it implies for the given data.

   The result is `reportedLabels storedParams labelsFor`: the labels reported here
   must agree with the labels obtained from the estimator's stored parameter set,
   so a fit-time label and a subsequent separate query give the same answer. They
   must therefore be derived from `storedParams`, not from `transientParams`. All
   three inputs are read-only (none `mut`): the routine reads them and returns a
   result, mutating nothing it is handed (directive 5). -/
method finalizeLabels (transientParams : Params) (storedParams : Params) (labelsFor : Params → Labels) return (out : Labels)
  ensures out = reportedLabels storedParams labelsFor
  do
    -- impl-start
    -- Make the stored parameter set current FIRST, then compute the labels, so
    -- the reported labels are derived from the stored parameters and agree with a
    -- later separate query — not from the transient parameter set.
    let mut active := transientParams
    active := storedParams
    let out := labelsFor active
    return out
    -- impl-end

prove_correct finalizeLabels by
  loom_solve
  simp_all [reportedLabels]
