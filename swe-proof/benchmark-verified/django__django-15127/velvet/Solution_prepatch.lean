import Velvet.Std
-- imports-end

-- Total-correctness semantics: the change-notification handler must COMPLETE
-- (the real receiver is straight-line code that always terminates), so the
-- spec must also rule out diverging implementations — under partial
-- correctness a non-terminating body would vacuously satisfy every ensures.
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms: the only callee this operation invokes — the table
--  recompute — is modeled DEEPLY as `recomputeTable` in the `pure` region and
--  validated against the real callee by G-AX, an A-reference, not a consumed
--  axiom. See mapping.md §3 / refinement.md.)
-- axioms-end

-- pure-start
/- Lookup the value bound to `key` in an association list (first binding wins;
   the carriers come from real dictionaries, whose keys are unique). -/
def lookupEntry : List (Int × String) → Int → Option String
  | [],            _   => none
  | (k, v) :: rest, key => if k = key then some v else lookupEntry rest key

/- The recomputed lookup table: the override entries, overlaid on the base
   entries (an entry of `base` survives only when its key is not overridden).
   As a key→value mapping this is exactly "base defaults updated by overrides"
   (overrides win). Deep model of the unchanged community callee that derives
   the table; validated equal to that callee by G-AX (A-reference, mapping.md
   §3.1), so no axiom about it is consumed by the proof. -/
def recomputeTable (base overrides : List (Int × String)) : List (Int × String) :=
  overrides ++ base.filter (fun kv => (lookupEntry overrides kv.1).isNone)
-- pure-end

-- pre-conditions-start
-- (refreshCachedTable takes no `require`: it is total on every changed key.)
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A change-notification handler that keeps a cached lookup table in sync with
   configuration. The handler watches one configuration key (`watchedKey`).
   When the key that just changed (`changedKey`) is the watched one, the cached
   table is recomputed from its base entries overlaid with the current override
   entries; for any other key, the cached table is left exactly as it was. -/
method refreshCachedTable
    (mut cached : List (Int × String))
    (changedKey : String) (watchedKey : String)
    (base : List (Int × String)) (overrides : List (Int × String))
    return (u : Unit)
  ensures changedKey = watchedKey → cached = recomputeTable base overrides
  ensures changedKey ≠ watchedKey → cached = cachedOld
  do
    -- impl-start
    -- Pre-patch skeleton: there is NO change-notification receiver, so the
    -- cached table is never recomputed — it keeps its import-time value on
    -- every changed key. The frozen spec requires a recompute when the watched
    -- key changes, so prove_correct MUST fail on the first `ensures`.
    cached := cached
    return
    -- impl-end

prove_correct refreshCachedTable by
  loom_solve
