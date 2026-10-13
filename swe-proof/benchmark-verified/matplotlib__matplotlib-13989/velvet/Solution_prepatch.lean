import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The operation under specification is the pure
--  assembly of the keyword-option mapping handed to the histogram routine; it
--  is modeled DEEPLY in the `pure` region below. The downstream histogram
--  computation that consumes these options is unchanged and is not modeled —
--  it owes no contract here.)
-- axioms-end

-- pure-start
/- The keyword-option mapping assembled for a single histogram computation,
   reduced to the two entries this assembly decides:
     * `boundsOpt`  — the explicit lower/upper data bounds entry, present
                      (`some`) when bounds were determined for this computation
                      and absent (`none`) otherwise;
     * `densityOpt` — the normalize-to-a-density entry, present (`some b`) when
                      the assembly records the density choice and absent
                      (`none`) when it does not.
   The two bounds are carried opaquely (their numeric values are never inspected
   here); only their presence and identity matter to this assembly. -/
structure HistOptions where
  boundsOpt  : Option (Float × Float)
  densityOpt : Option Bool
  deriving Inhabited

/- Assemble the option mapping. The mapping starts carrying whatever bounds
   entry was already determined (`boundsOpt`) and no density entry. When the
   density choice is recorded for a non-accumulated computation, the density
   entry is ADDED to that same mapping — the already-present bounds entry is
   carried through unchanged, never discarded. In every other case the mapping
   is left as it began. -/
def buildHistOptions
    (boundsOpt : Option (Float × Float)) (density accumulate : Bool) : HistOptions :=
  let base : HistOptions := { boundsOpt := boundsOpt, densityOpt := none }
  if density && !accumulate then { base with densityOpt := some density } else base

@[grind] lemma buildHistOptions_bounds
    (boundsOpt : Option (Float × Float)) (density accumulate : Bool) :
    (buildHistOptions boundsOpt density accumulate).boundsOpt = boundsOpt := by
  unfold buildHistOptions
  cases density <;> cases accumulate <;> simp
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Assemble the keyword-option mapping for a single histogram computation.

   The desired behaviour the issue demands: recording the density choice must
   NOT cause the explicitly-determined bounds entry to be lost. Concretely:

   - the bounds entry of the assembled mapping is ALWAYS exactly the bounds
     entry that was already determined (`out.boundsOpt = boundsOpt`) — adding
     the density entry never discards or alters it;
   - the density entry is present and records the density choice exactly when
     the density choice applies to this computation (a density computation that
     is not accumulated); otherwise the density entry is absent.

   None of the inputs are mutated (directive 5): `boundsOpt`, `density`, and
   `accumulate` are read-only carriers and the assembly returns a fresh mapping. -/
method buildHistOptionsM
    (boundsOpt : Option (Float × Float)) (density : Bool) (accumulate : Bool)
    return (out : HistOptions)
  ensures out = buildHistOptions boundsOpt density accumulate
  ensures out.boundsOpt = boundsOpt
  ensures (density = true ∧ accumulate = false) → out.densityOpt = some density
  ensures ¬(density = true ∧ accumulate = false) → out.densityOpt = none
  do
    -- impl-start
    let base : HistOptions := { boundsOpt := boundsOpt, densityOpt := none }
    let result : HistOptions :=
      if density && !accumulate then
        { boundsOpt := none, densityOpt := some density }
      else
        base
    return result
    -- impl-end

prove_correct buildHistOptionsM by
  loom_solve
  cases density <;> cases accumulate <;> simp_all [buildHistOptions]
