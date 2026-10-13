import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no deep-model references. The decision the desired
   behaviour concerns — whether one alteration of a model field is superseded by
   the step that immediately follows it — is modeled directly in the `pure`
   region (`reduceDecision`) from observable booleans about that following step.
   Every situation the modeled decision does not collapse is left to the
   pre-existing combining dispatch via the abstract tag
   `ReduceResult.deferToInherited`; that dispatch's concrete outcome is
   independent of the desired behaviour and is exercised against the real
   reducer by G-CONF (conformance_check.py). Nothing is axiomatized. -/
-- axioms-end

-- pure-start
/- What the reducer observes about the step that immediately follows this
   alteration when deciding whether the two can be combined into the later one.
   * `incomingIsAlter`  — the following step is itself an alteration of a model
                          field's definition.
   * `incomingIsRemove` — the following step removes a model field.
   * `sameField`        — the following step targets the same model field (same
                          model, same field name) as this alteration. -/
structure ReduceInput where
  incomingIsAlter  : Bool
  incomingIsRemove : Bool
  sameField        : Bool
  deriving DecidableEq, Inhabited

/- The reducer's decision for one (this-alteration, following-step) pair.
   * `keepLater`        — the two collapse: this alteration is dropped and only
                          the following step is kept.
   * `deferToInherited` — no special combination applies, so the decision is
                          left to the pre-existing combining dispatch (whose
                          concrete result is independent of the desired
                          behaviour). -/
inductive ReduceResult where
  | keepLater
  | deferToInherited
  deriving DecidableEq, Inhabited

/- The desired behaviour: when the following step acts on the SAME model field
   and is either another alteration of that field or its removal, the earlier
   alteration is redundant and the pair collapses onto the later step alone; in
   every other case the decision is left to the pre-existing combining dispatch.
   The redundancy of one alteration followed by another on the same field is the
   behaviour the desired change adds. -/
def reduceDecision (op : ReduceInput) : ReduceResult :=
  if (op.incomingIsAlter || op.incomingIsRemove) && op.sameField then
    ReduceResult.keepLater
  else
    ReduceResult.deferToInherited
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decide how an alteration of a model field combines with the step that
   immediately follows it, given only what the reducer observes about that
   following step (`op`). `op` is read-only — the decision mutates nothing
   (directive 5). The pair collapses onto the later step precisely when that
   following step acts on the same field and is either another alteration of it
   or its removal; otherwise the pre-existing combining dispatch decides. -/
method reduceAlterField (op : ReduceInput) return (out : ReduceResult)
  ensures out = reduceDecision op
  do
    -- impl-start
    if (op.incomingIsAlter || op.incomingIsRemove) && op.sameField then
      return ReduceResult.keepLater
    else
      return ReduceResult.deferToInherited
    -- impl-end

prove_correct reduceAlterField by
  loom_solve <;> simp_all [reduceDecision]
