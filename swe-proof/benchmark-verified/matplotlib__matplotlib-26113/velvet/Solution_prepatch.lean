import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The per-bin aggregation is a FREE INPUT `reduceBin`,
--  so the spec makes no behavioural claim about it and holds for EVERY value;
--  the bin populations are free inputs too. There is nothing to check against a
--  real callee, hence no axiom and no G-AX. The only thing the spec pins is the
--  selection rule — which bins are aggregated vs left empty.)
-- axioms-end

-- pure-start
/- The aggregate emitted for one bin, given the minimum population a bin must
   reach to be aggregated. A bin is aggregated — its values collapsed to a
   single number by `reduceBin` — exactly when it holds AT LEAST that many
   values; otherwise the bin is left empty (`none`, i.e. no aggregate). -/
def binAggregate (reduceBin : List Float → Float) (minPop : Nat)
    (bin : List Float) : Option Float :=
  if bin.length ≥ minPop then some (reduceBin bin) else none

/- The aggregates emitted for a whole sequence of bins: the per-bin aggregate of
   each bin, in order, with empties left as `none`. Front-recursive so a single
   unfold is available per loop step (the backward fold pattern, plan §5.4). -/
def aggregateSeq (reduceBin : List Float → Float) (minPop : Nat) :
    List (List Float) → List (Option Float)
  | []      => []
  | b :: bs => binAggregate reduceBin minPop b :: aggregateSeq reduceBin minPop bs

@[grind] lemma aggregateSeq_nil (f : List Float → Float) (m : Nat) :
    aggregateSeq f m [] = [] := rfl
@[grind] lemma aggregateSeq_cons (f : List Float → Float) (m : Nat)
    (b : List Float) (bs : List (List Float)) :
    aggregateSeq f m (b :: bs) = binAggregate f m b :: aggregateSeq f m bs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Compute the per-bin aggregates for a sequence of bins. Each bin is aggregated
   to a single value when its population reaches the minimum, and is otherwise
   left empty. `reduceBin`, `minPop`, `bins` are read-only — the probe mutates
   nothing it is handed (directive 5). -/
method accumulateBins (reduceBin : List Float → Float) (minPop : Nat)
    (bins : List (List Float)) return (out : List (Option Float))
  ensures out = aggregateSeq reduceBin minPop bins
  do
    -- impl-start
    -- Pre-image skeleton: a bin is aggregated only when its population STRICTLY
    -- exceeds the minimum (a strict comparison), so a bin whose population
    -- equals the minimum is left empty. The frozen spec requires `aggregateSeq`
    -- (aggregate when population is AT LEAST the minimum), so prove_correct
    -- MUST fail on the boundary bin.
    let mut result : List (Option Float) := []
    let mut i := bins.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ bins.length
      invariant result = aggregateSeq reduceBin minPop (bins.drop i)
      done_with i = 0
      decreasing i
    do
      let b := bins[i - 1]!
      let agg : Option Float :=
        if b.length > minPop then some (reduceBin b) else none
      result := agg :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the bin at `i-1`
   on the front, so `aggregateSeq` peels one `binAggregate`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma aggregateSeq_drop_step (f : List Float → Float) (m : Nat)
    (bins : List (List Float)) (i : Nat) (hi : 0 < i) (hle : i ≤ bins.length) :
    aggregateSeq f m (bins.drop (i - 1))
      = binAggregate f m bins[i - 1]! :: aggregateSeq f m (bins.drop i) := by
  have hlt : i - 1 < bins.length := by omega
  have hcons : bins.drop (i - 1) = bins[i - 1]! :: bins.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, aggregateSeq_cons]

prove_correct accumulateBins by
  loom_solve
  rw [aggregateSeq_drop_step reduceBin minPop bins i (by omega) (by omega)]
  simp_all
