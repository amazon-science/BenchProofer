import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No axioms. The only repository behaviour this bundle relies on is the
-- in-place update of one entry of a settings map while every other entry is
-- preserved (a pure data-structure property), modeled directly below. There is
-- no unchanged callee whose contract must be assumed. (mapping.md §3.)
-- axioms-end

-- pure-start
-- No pure helpers are required: the modeled behaviour is the single
-- `Function.update` of a total settings map, whose frame property
-- (`Function.update_of_ne`) is library knowledge `loom_solve` discharges.
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Resetting an axis re-derives exactly one tick-keyword entry — the
   distinguished `key` (recomputed to `majorVal`/`minorVal` from the ambient
   configuration) — for each of the two tick-keyword settings maps, and leaves
   every other entry of both maps untouched. Modeling each map as a total
   function `String → Bool` from a setting name to its on/off flag: the
   per-side visibility flags that callers (e.g. linked axes) have set must
   survive a reset; only the recomputed entry changes. -/
method resetAxisTickKeywords
    (mut majorKw : String → Bool) (mut minorKw : String → Bool)
    (key : String) (majorVal : Bool) (minorVal : Bool)
    return (u : Unit)
  ensures majorKw key = majorVal
  ensures minorKw key = minorVal
  ensures ∀ k, k ≠ key → majorKw k = majorKwOld k
  ensures ∀ k, k ≠ key → minorKw k = minorKwOld k
  do
    -- impl-start
    majorKw := Function.update majorKw key majorVal
    minorKw := Function.update minorKw key minorVal
    return
    -- impl-end

prove_correct resetAxisTickKeywords by
  loom_solve <;>
    first
      | exact Function.update_self _ _ _
      | (intro k hk; exact Function.update_of_ne hk _ _)
