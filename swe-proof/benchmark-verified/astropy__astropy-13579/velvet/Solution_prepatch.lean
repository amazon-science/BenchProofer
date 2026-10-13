import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed callee contracts. Two callees are involved and BOTH are
--  unchanged: the routine that produces the per-axis reference
--  coordinates, and the lower-level inverse transform. The first supplies a
--  read-only per-axis value carried here as the `.2` component of each axis
--  descriptor; the second consumes the assembled vector and is downstream of
--  the modeled construction. The transformation under spec — assembling the
--  full-dimensional input vector — is modeled DEEPLY below; every observable is
--  computed from the read-only inputs, nothing is borrowed from an oracle.
--  See refinement.md / mapping.md.)
-- axioms-end

-- pure-start
/- One axis descriptor: a flag saying whether this axis is present in the
   lower-dimensional view (`.1`), paired with that axis's reference coordinate
   (`.2`). The reference coordinate is the value the axis takes at the chosen
   reference position; it is meaningful only for axes absent from the view. -/
abbrev Axis := Bool × Float

/- Fold one axis into the (assembled-vector, remaining-supplied-values) state.
   - a present axis emits the next caller-supplied value and consumes it;
   - an absent axis emits that axis's own reference coordinate and consumes
     nothing.
   This threads the supplied values as a stream so each present axis takes the
   next one in order. -/
def scatterStep (acc : List Float × List Float) (a : Axis) : List Float × List Float :=
  (acc.1 ++ [if a.1 then acc.2.headD 0 else a.2],
   if a.1 then acc.2.tail else acc.2)

/- The full-dimensional vector assembled from the axis descriptors and the
   supplied values: present axes are filled, in order, from `supplied`; absent
   axes are filled with their own reference coordinate. Front-recursive via a
   left fold so a single unfold is available per loop step (the fold pattern). -/
def scatter (axes : List Axis) (supplied : List Float) : List Float :=
  (axes.foldl scatterStep (([] : List Float), supplied)).1

/- Forward-fold step: extending the consumed prefix by one axis applies one
   `scatterStep` to the state built from the shorter prefix. The single goal the
   loop body must discharge. -/
lemma scatter_fold_step (axes : List Axis) (supplied : List Float) (i : Nat)
    (hi : i < axes.length) :
    (axes.take (i + 1)).foldl scatterStep (([] : List Float), supplied)
      = scatterStep ((axes.take i).foldl scatterStep (([] : List Float), supplied)) axes[i]! := by
  have hcons : axes.take (i + 1) = axes.take i ++ [axes[i]!] := by
    rw [List.take_succ, List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
    simp
  rw [hcons, List.foldl_append, List.foldl_cons, List.foldl_nil]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Assemble the full-dimensional coordinate vector consumed by the inverse
   transform. The lower-dimensional view exposes only the axes flagged present;
   the caller supplies one value per present axis, in order. The result is the
   full vector: each present axis takes the next supplied value; each absent
   axis takes its own reference coordinate (`.2`), the value that axis holds at
   the chosen reference position. `axes` and `supplied` are read-only (not
   `mut`): the loop builds a fresh result and never mutates its inputs. -/
method assembleWorldVector (axes : List Axis) (supplied : List Float)
    return (out : List Float)
  require (axes.filter (·.1)).length = supplied.length
  ensures out = scatter axes supplied
  do
    -- impl-start
    -- Pre-image skeleton: an absent axis is filled with the constant 1.0 — a
    -- fixed placeholder — instead of that axis's own reference coordinate
    -- (a.2). The frozen spec requires `scatter`, which fills absent axes with
    -- a.2, so prove_correct MUST fail whenever a.2 ≠ 1.0 for some absent axis.
    let mut result : List Float := []
    let mut remaining : List Float := supplied
    let mut i := 0
    while i < axes.length
      invariant i ≤ axes.length
      invariant result = ((axes.take i).foldl scatterStep (([] : List Float), supplied)).1
      invariant remaining = ((axes.take i).foldl scatterStep (([] : List Float), supplied)).2
      done_with i = axes.length
      decreasing axes.length - i
    do
      let a := axes[i]!
      let v : Float := if a.1 then remaining.headD 0 else 1.0
      result := result ++ [v]
      remaining := if a.1 then remaining.tail else remaining
      i := i + 1
    return result
    -- impl-end

prove_correct assembleWorldVector by
  loom_solve
  all_goals
    first
      | (rw [scatter_fold_step axes supplied i (by omega)]; simp_all [scatterStep])
      | simp_all [scatter, List.take_length]
