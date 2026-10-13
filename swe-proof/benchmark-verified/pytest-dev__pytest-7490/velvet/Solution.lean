import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The marker-evaluation callee that produces an xfail
   determination from the item's current markers is taken as a given primitive
   and modeled parametrically: its result is the abstract `Option Xfail`
   value (`none` = no xfail determination, `some _` = an xfail determination),
   so the spec holds for every possible result of that callee. Its relevant
   behaviour (deterministic in the marker set; yields `some _` exactly when an
   xfail marker is present) is validated against the real callee by G-AX
   (axiom_check.py). There is no module-level `axiom`. -/
-- axioms-end

-- pure-start
/- The observable content of an xfail determination: the reason to report, and
   the two flags downstream reporting consults. These are the only fields the
   desired behaviour carries through; everything else about the determination is
   orthogonal (mapping.md §2). The determination is passed through UNCHANGED, so
   its content is pinned by exact equality, not merely by presence. -/
structure Xfail where
  reason : String
  run    : Bool
  strict : Bool
  deriving DecidableEq

/- One determination step: keep an already-made determination; otherwise adopt a
   freshly-evaluated one. Mirrors the "evaluate only if not already known" guard
   the reporting machinery relies on (a determination, once made, is stable). -/
def refresh (current fresh : Option Xfail) : Option Xfail :=
  match current with
  | some x => some x
  | none   => fresh

/- The determination the reporting machinery must observe. Starting from the
   determination known on entry, it is refreshed once against the markers present
   when the body is entered, and AGAIN against the markers present once the body
   has finished — so a determination that only becomes available while the body
   runs (e.g. a marker added dynamically during the run) is still observed and
   not lost. Pinned by the method `ensures`. -/
def finalXfail (entry evalBefore evalAfter : Option Xfail) : Option Xfail :=
  refresh (refresh entry evalBefore) evalAfter

@[grind] lemma refresh_some (x : Xfail) (f : Option Xfail) :
    refresh (some x) f = some x := rfl
@[grind] lemma refresh_none (f : Option Xfail) :
    refresh none f = f := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Resolve the xfail determination across a single test body's execution.
   `entry` is the determination known before the body is scheduled; `evalBefore`
   is the determination from the markers present as the body is entered;
   `evalAfter` is the determination from the markers present once the body has
   finished (which may now include a marker added dynamically while the body
   ran). The determination handed to reporting must reflect the markers present
   AFTER the body finished whenever none was established earlier — otherwise a
   dynamically-added xfail determination is silently dropped. -/
method resolveDynamicXfail
    (entry : Option Xfail) (evalBefore : Option Xfail) (evalAfter : Option Xfail)
    return (stored : Option Xfail)
  ensures stored = finalXfail entry evalBefore evalAfter
  do
    -- impl-start
    let mut xfailed : Option Xfail := entry
    -- Before the body is entered: settle the determination if not already known.
    xfailed := match xfailed with
      | some x => some x
      | none   => evalBefore
    -- The body runs here; it may establish a determination dynamically.
    -- After the body has finished: settle again against the markers now present,
    -- so a determination established while the body ran is observed.
    xfailed := match xfailed with
      | some x => some x
      | none   => evalAfter
    return xfailed
    -- impl-end

prove_correct resolveDynamicXfail by
  loom_solve
  simp [finalXfail, refresh]
