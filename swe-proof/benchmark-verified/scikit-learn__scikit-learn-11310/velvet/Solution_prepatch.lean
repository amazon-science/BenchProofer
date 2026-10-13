import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- The process wall clock, read twice across one synchronous unit of work, is
   non-decreasing: a reading taken after the work is never earlier than a reading
   taken before it. The two readings are environment-provided values produced by
   an UNCHANGED callee; they enter the method as the inputs `startT` (taken
   immediately before the work) and `endT` (taken immediately after it), and the
   monotonicity contract is stated as the precondition `startT ≤ endT` — the
   axiom's domain. The postcondition must then hold for EVERY reading pair the
   real clock can produce (the proof is universally quantified over all inputs
   satisfying non-decrease), so nothing stronger than non-decrease is assumed
   (we never pin how much the clock advanced). This is the weakest fact
   sufficient to guarantee the recorded duration is non-negative. Provenance +
   executable soundness check: mapping.md §3 / axiom_check.py (G-AX). -/
-- axioms-end

-- pure-start
-- (no shared pure helpers needed)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- After a hyperparameter search selects its best configuration, it may refit
   that configuration on the whole dataset. When it does, the duration of that
   single refit is a quantity a consumer needs to be able to read back: the time
   spent refitting the best model on the full data.

   The desired behavior: a single request flag governs whether the refit happens.
   When refitting is requested, the elapsed duration of the refit — the wall
   clock read immediately after the refit minus the wall clock read immediately
   before it — is recorded as a present value; because consecutive readings are
   non-decreasing (the precondition, see the axiom note above) that recorded
   span is never negative. When refitting is NOT requested, no duration is
   recorded — the slot stays absent.

   `refit` is the read-only request flag (not `mut`): the routine decides based
   on it and never alters it (directive 5). `startT` and `endT` are the two
   wall-clock readings bracketing the refit work, environment-provided by the
   unchanged clock callee (read-only inputs). `refitTime` is the
   recorded-duration slot (`mut`, genuinely written): it comes in absent
   (`none`) for a fresh search and, when refitting is requested, is set to
   exactly the elapsed span `endT - startT` — the recorded value is pinned to
   the very subtraction of the two readings, not merely to some non-negative
   value; when refitting is not requested its post-state is pinned exactly to
   its unchanged entry value `none` (directive 5: the unchanged frame is stated
   exactly). Durations are modeled as exact rationals (`Rat`): the recorded
   observable is a single subtraction of two same-magnitude clock readings,
   which is exact (mapping.md §2), so an exact ordered carrier is faithful. -/
method recordRefitTime (refit : Bool) (startT : Rat) (endT : Rat)
    (mut refitTime : Option Rat) return (unit : Unit)
  require refitTime = none
  require startT ≤ endT
  ensures refit = true  → refitTime = some (endT - startT)
  ensures refit = true  → (∃ t : Rat, refitTime = some t ∧ t ≥ 0)
  ensures refit = false → refitTime = none
  do
    -- impl-start
    -- PRE-PATCH (buggy) skeleton: the refit is performed when requested, but its
    -- duration is never recorded — the slot is left absent in both branches.
    -- This is the base_commit behavior: no wall-clock bracketing, no attribute.
    if refit then
      return ()
    else
      return ()
    -- impl-end

prove_correct recordRefitTime by
  loom_solve
