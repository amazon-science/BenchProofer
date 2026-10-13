import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The shared construction-time guard that the two modeled
   aggregates route through — refuse a duplicate-elimination request for a kind
   that does not accept it, otherwise build and record the request — is modeled
   DEEPLY in the `pure` region (`construct`). The per-kind capability is concrete
   data, validated against the real classes by G-CONF; there is no module-level
   `axiom`. -/
-- axioms-end

-- pure-start
/- Refusing a construction because a duplicate-elimination request was made of a
   kind that does not accept that option. The only construction outcome the
   desired behaviour distinguishes from success. -/
inductive InitErr where
  | distinctNotAccepted
  deriving DecidableEq

/- The observable content of a constructed aggregate: which aggregate it is (its
   SQL function name) and whether it was asked to aggregate over the set of
   DISTINCT input values. These are the only fields the desired behaviour
   constrains; everything else about the aggregate is orthogonal (mapping.md
   §2). -/
structure AggState where
  function : String
  distinct : Bool
  deriving DecidableEq

/- The shared construction guard, modeled deeply. `acceptsDistinct` is the
   per-kind capability the guard consults: when a duplicate-elimination option
   is requested of a kind that does not accept it, construction is refused;
   otherwise the aggregate is built and the requested option is recorded on it
   unchanged. Pinned by each method's `ensures`. -/
def construct (function : String) (acceptsDistinct : Bool) (distinct : Bool) :
    Except InitErr AggState :=
  if distinct && !acceptsDistinct then Except.error .distinctNotAccepted
  else Except.ok { function := function, distinct := distinct }
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Construct an averaging aggregate over a source expression, optionally over
   the set of DISTINCT input values. Desired behaviour: an averaging aggregate
   accepts a duplicate-elimination request, so construction with the option set
   must SUCCEED and the built aggregate must carry that option through unchanged
   (a downstream aggregation over distinct values depends on it being recorded
   faithfully, not merely accepted). -/
method avgInit (distinct : Bool) return (out : Except InitErr AggState)
  ensures out = construct "AVG" true distinct
  do
    -- impl-start
    -- `acceptsDistinct` is this kind's capability: an averaging aggregate
    -- accepts the duplicate-elimination option.
    let acceptsDistinct : Bool := true
    if distinct && !acceptsDistinct then
      return Except.error InitErr.distinctNotAccepted
    else
      return Except.ok { function := "AVG", distinct := distinct }
    -- impl-end

prove_correct avgInit by
  loom_solve
  simp [construct]

/- Construct a summing aggregate over a source expression, optionally over the
   set of DISTINCT input values. Same desired behaviour as the averaging
   aggregate: a duplicate-elimination request must succeed and be recorded on
   the built aggregate unchanged. -/
method sumInit (distinct : Bool) return (out : Except InitErr AggState)
  ensures out = construct "SUM" true distinct
  do
    -- impl-start
    let acceptsDistinct : Bool := true
    if distinct && !acceptsDistinct then
      return Except.error InitErr.distinctNotAccepted
    else
      return Except.ok { function := "SUM", distinct := distinct }
    -- impl-end

prove_correct sumInit by
  loom_solve
  simp [construct]
