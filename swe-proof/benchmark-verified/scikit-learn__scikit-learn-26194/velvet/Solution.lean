import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- A decision threshold on a scoring function. A `value r` is an ordinary finite
   threshold (a score cut-off); `top` is the sentinel position that classifies
   NO instance as positive — it sits strictly above every attainable finite
   score, so the curve is anchored at the (0,0) corner. Modeling the sentinel as
   its own constructor (rather than a finite number) keeps it categorically apart
   from any real score: it can never be confused with, or compared as if it were,
   an ordinary value. Finite thresholds are carried as exact `Rat` because only
   their order/value matters here (mapping.md §2). -/
inductive Threshold where
  | value (r : Rat)
  | top
deriving DecidableEq

/- Lift a list of finite thresholds (the ordered cut-offs computed upstream) into
   the threshold domain, leaving each value untouched. -/
def finiteSeq (xs : List Rat) : List Threshold := xs.map Threshold.value
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Anchor a sequence of finite decision thresholds with one extra leading
   position so the resulting curve starts at the corner where no instance is
   predicted positive. `base` are the ordered finite thresholds produced
   upstream; the result is `base` (unchanged, in order) preceded by the sentinel
   that lies above every finite threshold. -/
method withLeadingSentinel (base : List Rat) return (out : List Threshold)
  require base ≠ []
  ensures out = Threshold.top :: finiteSeq base
  do
    -- impl-start
    let out : List Threshold := Threshold.top :: finiteSeq base
    return out
    -- impl-end

prove_correct withLeadingSentinel by loom_solve
