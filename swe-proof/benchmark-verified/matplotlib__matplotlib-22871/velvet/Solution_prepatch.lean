import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees and no `:|` callee stubs. The behaviour under spec is a
--  pure high-to-low scan over a given list of per-component observations: at each
--  date component (from the finest to the coarsest) the scan reads the integer
--  column of that component across the ticks and observes two facts about it —
--  whether the component takes more than one distinct value across the ticks, and
--  whether the integer one occurs among those values. How each integer column is
--  obtained from the tick values is the identical, unchanged upstream computation
--  and is not modeled here (refinement.md §B / mapping.md §3); it is reproduced
--  verbatim by the conformance bridge. Everything observable is computed from the
--  input columns, so there is no consumed axiom.)
-- axioms-end

-- pure-start
/- Whether a component's integer column takes more than one distinct value across
   the ticks: true exactly when some entry differs from the first. An empty or
   one-element column is constant. This is the "this component changes over the
   ticks" observation the scan keys on. -/
def colVaries (col : List Int) : Bool :=
  col.any (fun v => v != col.headD 0)

/- Whether the integer one occurs among a component's values. The start of a
   calendar component (e.g. the first month or first day) is numbered one, so a
   column containing one means a tick sits at that component's starting boundary. -/
def colHasOne (col : List Int) : Bool :=
  col.contains 1

/- Whether the running offset label must be suppressed at a given scan position:
   only at one of the two coarsest components (numbered below two) AND only when
   that component's column includes the starting-boundary value one. At any finer
   component, or when the value one is absent, the offset is NOT suppressed — this
   is the precise condition under which a coarser part of the date is still worth
   surfacing in the offset even though a finer part varies. -/
def suppressOffset (level : Nat) (col : List Int) : Bool :=
  decide (level < 2) && colHasOne col

/- The offset-display decision, scanning the components from finest to coarsest.
   `initShow` is whether the offset would be shown absent any suppression; the
   list pairs each component's number with its integer column, in scan order
   (finest component first, coarsest last). The result is the chosen component
   number together with whether the offset is shown.

   Walk the components: the FIRST one that changes over the ticks determines the
   chosen component number; at that component the offset is hidden exactly when
   `suppressOffset` holds, otherwise it keeps `initShow`, and the scan stops. If no
   component changes over the ticks, the chosen component is the coarsest-but-one
   default (number five) and the offset keeps `initShow`. Front-recursive so a
   single unfold is available per scan step (the scan/fold pattern, plan §5.4). -/
def offsetDecision (initShow : Bool) : List (Nat × List Int) → Nat × Bool
  | []             => (5, initShow)
  | (lvl, col) :: rest =>
      if colVaries col then
        (lvl, if suppressOffset lvl col then false else initShow)
      else
        offsetDecision initShow rest

@[grind] lemma offsetDecision_nil (s : Bool) :
    offsetDecision s [] = (5, s) := rfl

@[grind] lemma offsetDecision_cons (s : Bool) (lvl : Nat) (col : List Int)
    (rest : List (Nat × List Int)) :
    offsetDecision s ((lvl, col) :: rest) =
      (if colVaries col then (lvl, if suppressOffset lvl col then false else s)
       else offsetDecision s rest) := rfl

/- The cons unfold for an arbitrary leading pair (not split into its
   projections): reads the pair's two fields directly. -/
@[grind] lemma offsetDecision_cons' (s : Bool) (p : Nat × List Int)
    (rest : List (Nat × List Int)) :
    offsetDecision s (p :: rest) =
      (if colVaries p.2 then (p.1, if suppressOffset p.1 p.2 then false else s)
       else offsetDecision s rest) := by
  obtain ⟨lvl, col⟩ := p; rfl

/- Exposing the element at index `i` on the front of `drop i`. -/
lemma drop_cons_eq (xs : List (Nat × List Int)) (i : Nat) (hi : i < xs.length) :
    xs.drop i = xs[i]! :: xs.drop (i + 1) := by
  have h := List.drop_eq_getElem_cons hi
  rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi, Option.getD_some]
  exact h

/- The per-step scan equation: scanning the remaining components from index `i`
   peels off component `i` and either stops there (when it changes over the ticks)
   or continues from `i + 1`. This is the single per-step goal the loop body
   leaves. -/
lemma offsetDecision_step (s : Bool) (xs : List (Nat × List Int)) (i : Nat)
    (hi : i < xs.length) :
    offsetDecision s (xs.drop i) =
      (if colVaries (xs[i]!).2 then
         ((xs[i]!).1, if suppressOffset (xs[i]!).1 (xs[i]!).2 then false else s)
       else offsetDecision s (xs.drop (i + 1))) := by
  rw [drop_cons_eq xs i hi, offsetDecision_cons']
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decide how the running offset label is chosen for a set of ticks. `initShow`
   is whether the offset would be displayed absent any suppression; `stats` pairs
   each date component's number with its integer column across the ticks, listed
   from the finest component to the coarsest. Both inputs are read-only (not
   `mut`): the decision reads them and returns a fresh pair (directive 5).

   Desired behaviour: scan the components from finest to coarsest and stop at the
   first one that changes over the ticks; that component's number is reported, and
   the offset is hidden only at one of the two coarsest components and only when
   that component's column includes the starting-boundary value one — otherwise
   the offset keeps `initShow`. When no component changes over the ticks, the
   coarsest-but-one default component is reported and the offset keeps `initShow`.
   In particular, when a coarse component varies but never sits at its starting
   boundary, the offset must remain available so the unchanging coarser part of
   the date is still surfaced. -/
method offsetSelection (initShow : Bool) (stats : List (Nat × List Int))
    return (out : Nat × Bool)
  ensures out = offsetDecision initShow stats
  do
    -- impl-start
    -- Pre-image skeleton: at one of the two coarsest components the offset is
    -- suppressed using only the component number, ignoring whether the component
    -- sits at its starting boundary (the `colHasOne` reading of `suppressOffset`
    -- is dropped). The frozen spec requires the full `offsetDecision`, so
    -- prove_correct MUST fail.
    let mut showOffset := initShow
    let mut chosenLevel : Nat := 5
    let mut stopped := false
    let mut i := 0
    while i < stats.length ∧ stopped = false
      invariant i ≤ stats.length
      invariant if stopped then (chosenLevel, showOffset) = offsetDecision initShow stats
                else showOffset = initShow ∧ chosenLevel = 5 ∧
                     offsetDecision initShow stats = offsetDecision initShow (stats.drop i)
      done_with stopped = true ∨ i = stats.length
      decreasing (stats.length - i) + (if stopped then 0 else 1)
    do
      let lvl := (stats[i]!).1
      let col := (stats[i]!).2
      if colVaries col then
        chosenLevel := lvl
        if decide (lvl < 2) then
          showOffset := false
        stopped := true
      else
        i := i + 1
    return (chosenLevel, showOffset)
    -- impl-end

prove_correct offsetSelection by
  loom_solve
  all_goals
    rw [offsetDecision_step initShow stats i (by omega)] at invariant_2
    simp_all
