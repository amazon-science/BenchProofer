import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (no axioms: the modeled change is a pure selection over already-available
--  flags; there is no unchanged callee whose contract the proof consumes.)
-- axioms-end

-- pure-start
/- A chosen level specification. Either an automatic level *count* (a small
   integer the data-range expander later turns into that many evenly-spaced
   positions) or an *explicit* sequence of level positions (modeled as exact
   rationals so equality is decidable and order-faithful). This is the value
   the level-selection step yields before the downstream count→positions /
   positions→array processing (which the change leaves untouched). -/
inductive LevelArg where
  | count    (n : Nat)
  | explicit (levels : List Rat)
  deriving DecidableEq, Inhabited
-- pure-end

-- pre-conditions-start
-- (no preconditions: every flag combination is admissible input.)
-- pre-conditions-end

-- post-conditions-start
-- (post-conditions are stated inline on the method below.)
-- post-conditions-end

/- Select the level specification for a 2-D field plot when the caller did not
   pass an explicit `levels` keyword.

   Inputs (all already computed by the surrounding routine):
   * `levelsKwSet`  — whether a `levels` keyword was supplied (its value is
                      `levelsKw`);
   * `posGiven`     — whether a positional level argument was supplied (its
                      value is `posArg`);
   * `boolField`    — whether the field being plotted is a boolean field;
   * `filled`       — whether the plot fills regions between levels (vs. drawing
                      boundary lines only).

   The guarantee: an explicit keyword wins; otherwise a positional argument
   wins; otherwise a boolean field gets a constant boundary specification that
   depends only on `filled`; otherwise the hard-wired automatic count. -/
method chooseLevelArg
    (levelsKwSet : Bool) (levelsKw : LevelArg)
    (posGiven : Bool)    (posArg : LevelArg)
    (boolField : Bool)   (filled : Bool)
    return (out : LevelArg)
  ensures (levelsKwSet = true)  → out = levelsKw
  ensures (levelsKwSet = false) → (posGiven = true)  → out = posArg
  ensures (levelsKwSet = false) → (posGiven = false) → (boolField = true)  → (filled = true)  →
            out = LevelArg.explicit [0, 1/2, 1]
  ensures (levelsKwSet = false) → (posGiven = false) → (boolField = true)  → (filled = false) →
            out = LevelArg.explicit [1/2]
  ensures (levelsKwSet = false) → (posGiven = false) → (boolField = false) →
            out = LevelArg.count 7
  do
    -- invariants-start
    -- (no loops in this method.)
    -- invariants-end
    -- impl-start
    -- PRE-PATCH skeleton: no boolean-field autodetection. When no explicit
    -- keyword and no positional argument are given, the hard-wired automatic
    -- count is always used, regardless of whether the field is boolean. The
    -- two `boolField = true` postconditions therefore cannot hold, so
    -- prove_correct MUST fail (G-DIFF).
    if levelsKwSet then
      return levelsKw
    else
      if posGiven then
        return posArg
      else
        return (LevelArg.count 7)
    -- impl-end

prove_correct chooseLevelArg by
  loom_solve
