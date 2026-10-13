import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The construction-time behaviour the modeled estimator
   routes through — when retention of the per-alpha cross-validation values is
   requested of an estimator that supports that option, build the estimator and
   record the request faithfully; refuse only when the option is unsupported —
   is modeled DEEPLY in the `pure` region (`construct`). The per-estimator
   capability is concrete data, validated against the real class by G-CONF;
   there is no module-level `axiom`. -/
-- axioms-end

-- pure-start
/- Refusing a construction because retention of the cross-validation values was
   requested of an estimator that does not support that option. The only
   construction outcome the desired behaviour distinguishes from success. -/
inductive InitErr where
  | storeNotAccepted
  deriving DecidableEq

/- The observable content of a constructed estimator that the desired behaviour
   constrains: whether it was asked to retain the per-alpha cross-validation
   values (the `cv_values_` attribute the user later reads). Every other aspect
   of the estimator is orthogonal here (mapping.md §2). -/
structure EstimatorState where
  storeCvValues : Bool
  deriving DecidableEq

/- The construction outcome, modeled deeply. `acceptsStore` is the capability
   the construction consults: when retention of the cross-validation values is
   requested of an estimator that does not support it, construction is refused;
   otherwise the estimator is built and the requested option is recorded on it
   unchanged. Pinned by the method's `ensures`. -/
def construct (acceptsStore : Bool) (storeCvValues : Bool) :
    Except InitErr EstimatorState :=
  if storeCvValues && !acceptsStore then Except.error .storeNotAccepted
  else Except.ok { storeCvValues := storeCvValues }
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Construct a cross-validated estimator, optionally requesting that the
   per-alpha cross-validation values be retained for later inspection. Desired
   behaviour: this estimator supports retaining those values, so construction
   with the option set must SUCCEED and the built estimator must carry the
   requested option through unchanged — a later fit reads the recorded option to
   decide whether to populate the retained-values attribute, so the option must
   be recorded faithfully, not merely accepted. -/
method initEstimator (storeCvValues : Bool) return (out : Except InitErr EstimatorState)
  ensures out = construct true storeCvValues
  do
    -- impl-start
    -- `acceptsStore` is this estimator's capability: it supports retaining the
    -- per-alpha cross-validation values.
    let acceptsStore : Bool := true
    if storeCvValues && !acceptsStore then
      return Except.error InitErr.storeNotAccepted
    else
      return Except.ok { storeCvValues := storeCvValues }
    -- impl-end

prove_correct initEstimator by
  loom_solve
  simp [construct]
