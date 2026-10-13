import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The per-segment facts the step decision consults are
--  read-only per-hop inputs (tagged R in refinement.md), not contracts the proof
--  consumes, so no axiom and no axiom_check are needed. Their repo provenance is
--  in mapping.md. Only the way these facts are COMBINED into the keep decision is
--  modeled below.)
-- axioms-end

-- pure-start
/- The per-segment facts a step of the lookup path exposes, as it is walked one
   hop at a time. Each field is a single read-only boolean about the segment; the
   repo introspection each abstracts is recorded in mapping.md. They are exposed
   here only so the keep decision can be stated structurally.

   * `isFirst`            — this is the first segment of the path (no prior step
                            yet).
   * `priorIsRelation`    — the prior step entered a further record.
   * `concreteParentLink` — the segment merely re-reaches a concrete ancestor
                            record (the PS concrete-inheritance shortcut case).
   * `redundantLocalValue`     — an opaque per-segment redundancy flag (A).
   * `hasRedundantLocalValue`  — an opaque per-record flag enabling clause (C) (B).
   * `priorAlreadyCovers`      — an opaque per-segment redundancy flag (C).
   * `targetOfPrior`      — an alternative, coarser redundancy flag (consulted
                            only by the pre-image skeleton, not by the rule
                            below). -/
structure Hop where
  isFirst               : Bool
  priorIsRelation       : Bool
  concreteParentLink    : Bool
  redundantLocalValue   : Bool
  hasRedundantLocalValue: Bool
  priorAlreadyCovers    : Bool
  targetOfPrior         : Bool
deriving DecidableEq, Inhabited, Repr

/- Whether a single segment is RECORDED as a real step of the lookup path.

   A segment is recorded exactly when it is the first segment, OR the prior step
   entered a further record and the segment is NOT locally redundant. The segment
   is locally redundant precisely when ANY of three opaque conditions holds:
   `concreteParentLink` (the concrete-inheritance shortcut case from the PS),
   `redundantLocalValue`, or (`hasRedundantLocalValue` AND `priorAlreadyCovers`).
   Otherwise the segment is recorded. The repo meaning of each flag is in
   mapping.md; here only their Boolean combination is pinned. -/
def keepSegment (h : Hop) : Bool :=
  h.isFirst ||
  (h.priorIsRelation
    && !h.concreteParentLink
    && !h.redundantLocalValue
    && (!h.hasRedundantLocalValue || !h.priorAlreadyCovers))

/- The recorded/not-recorded flag of every segment of a walked path: the
   per-segment expansion of the input hops via `keepSegment`. Front-recursive so a
   single unfold is available per loop step (the backward-fold pattern, plan §5.4). -/
def keepMask : List Hop → List Bool
  | []      => []
  | h :: hs => keepSegment h :: keepMask hs

@[grind] lemma keepMask_nil : keepMask [] = [] := rfl
@[grind] lemma keepMask_cons (h : Hop) (hs : List Hop) :
    keepMask (h :: hs) = keepSegment h :: keepMask hs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decide, for each segment of an already-walked lookup path, whether that
   segment is recorded as a real step. The frozen guarantee is that the result is
   exactly the per-segment expansion `keepMask hops`: each flag is the keep
   decision for the corresponding hop, computed by the rule in `keepSegment`.
   `hops` is read-only — the method builds and returns a fresh flag list and
   never mutates its input. -/
method keptSegments (hops : List Hop) return (out : List Bool)
  ensures out = keepMask hops
  do
    -- impl-start
    -- Pre-image skeleton: the coarse redundancy criterion records a segment when
    -- it is the first segment OR the prior step crossed a relation and the field
    -- is NOT one of the prior relation's target fields. This treats a field that
    -- targets the prior relation as redundant outright — including a record's own
    -- primary key reached through a relation — so it DROPS a genuine descent the
    -- frozen `keepMask` (which records it) keeps. `prove_correct` MUST fail.
    let mut result : List Bool := []
    let mut i := hops.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ hops.length
      invariant result = keepMask (hops.drop i)
      done_with i = 0
      decreasing i
    do
      let h := hops[i - 1]!
      let keep : Bool := h.isFirst || (h.priorIsRelation && !h.targetOfPrior)
      result := keep :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer hop exposes the segment at `i-1`
   on the front, so `keepMask` peels one flag. The single goal `loom_solve`
   leaves for the loop body. -/
lemma keepMask_drop_step (hops : List Hop) (i : Nat)
    (hi : 0 < i) (hle : i ≤ hops.length) :
    keepMask (hops.drop (i - 1))
      = keepSegment hops[i - 1]! :: keepMask (hops.drop i) := by
  have hlt : i - 1 < hops.length := by omega
  have hcons : hops.drop (i - 1) = hops[i - 1]! :: hops.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, keepMask_cons]

prove_correct keptSegments by
  loom_solve
  rw [keepMask_drop_step hops i (by omega) (by omega)]
  simp_all
