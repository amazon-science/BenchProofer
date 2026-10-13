import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No module-level `axiom` declarations. The single unchanged callee this
--  routine relies on — the constant-strategy single-pass fill helper that
--  produces the per-feature initial fill values — is an imperative callee,
--  modeled by the `:|` choice stub `constantFill` below (sound by construction)
--  whose `ensures` is the weakest contract the caller consumes (A-consumed,
--  directive 7). Its soundness against the real helper is checked by G-AX
--  (axiom_check.py); provenance in mapping.md §3.)
-- axioms-end

-- pure-start
/- Resolve the configured constant to the concrete value used for every feature.
   When a constant is supplied it is used as given; when none is supplied a
   standard numerical default of `0` applies. This mirrors the usual
   "configured value, otherwise a default" selection over a possibly-absent
   setting, for the numerical case the tests exercise (mapping.md §2). -/
@[grind] def resolveFill : Option Rat → Rat
  | none   => 0
  | some v => v

/- The choice in the callee stub below is well-posed: for any target value `v`
   the set of values equal to `v` is non-empty (`v` itself). This supplies the
   constructive existence witness so the `:|` choice elaborates. It does NOT
   weaken verification: under demonic choice the postcondition must still hold
   for every value the predicate allows — here exactly the named fill vector. -/
noncomputable instance findableEqListRat (v : List Rat) (n : Lean.Name) :
    Findable (fun e : List Rat => typeWithName (e = v) n) where
  find := fun _ => some v
  find_none := by intro h; simp at h
  find_some_p := by intro x h; simp only [Option.some.injEq] at h; subst h; rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

noncomputable section

/- The unchanged constant-strategy fill helper, reached as a callee. Given the
   constant it is configured with and the feature count, it reports one initial
   fill value per feature: every feature gets the resolved constant. This is an
   unchanged imperative callee, modeled by a `:|` choice stub — sound by
   construction; its `ensures` is the weakest contract the caller needs. G-AX
   checks it against the real helper (mapping.md §3). -/
method constantFill (fillValue : Option Rat) (nFeatures : Nat)
    return (stats : List Rat)
  ensures stats = List.replicate nFeatures (resolveFill fillValue)
  do
    -- impl-start
    let stats :| stats = List.replicate nFeatures (resolveFill fillValue)
    return stats
    -- impl-end

/- Set up the constant-strategy initialization of the missing values and report
   the per-feature initial fill values it will use.

   The desired behavior: the caller's CONFIGURED constant governs the
   initialization. The helper that produces the per-feature initial values must
   be set up with that configured constant, so that every feature's initial fill
   value is exactly the resolved constant (`stats = replicate nFeatures
   (resolveFill fillValue)`). When a constant is supplied, supplying a non-zero
   value must change every reported fill value to it — the configured constant
   must reach the helper, not be silently dropped in favour of the default.

   `fillValue` is the configured constant (read-only; `none` means none was
   configured, so the numerical default applies). `nFeatures` is the read-only
   feature count. The result is the per-feature vector of initial fill values. -/
method initialFillStatistics (fillValue : Option Rat) (nFeatures : Nat)
    return (stats : List Rat)
  ensures stats = List.replicate nFeatures (resolveFill fillValue)
  do
    -- impl-start
    -- Pre-image skeleton: the constant-strategy fill helper is set up WITHOUT
    -- the configured constant, so it always falls back to the default. The
    -- configured `fillValue` never reaches the helper, so every reported fill
    -- value is the default `0` regardless of the configured constant. The frozen
    -- spec requires the resolved configured constant, so prove_correct MUST fail.
    let stats ← constantFill none nFeatures
    return stats
    -- impl-end

end

prove_correct constantFill by
  loom_solve

prove_correct initialFillStatistics by
  loom_solve
