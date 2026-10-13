import Velvet.Std
-- imports-end

-- Total-correctness semantics: the linking loop must COMPLETE (the real
-- routine is a bounded for-loop over the fetched batch that always
-- terminates), so the spec must also rule out diverging implementations —
-- under partial correctness a non-terminating body would vacuously satisfy
-- every ensures.
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms and no A-reference deep model of an outside callee. The
--  per-element behaviour this routine pins is a pure function of its inputs: each
--  child object carries an OPTIONAL pre-existing association to a parent object
--  (`existingParent`), and a lookup maps a child's grouping key to the parent it
--  belongs to. Both the optional association and the lookup are produced by
--  UNCHANGED machinery; they enter as the free inputs `children` / `lookup`, and
--  the decision claims nothing about how either is computed — it holds for EVERY
--  value they could take. There is therefore nothing to validate against a real
--  callee: no module-level `axiom`, no G-AX. mapping.md §3 / refinement.md.)
-- axioms-end

-- pure-start
/- One child object as far as this routine observes it:
   * `key`            — the grouping key by which the child is matched to the
                        parent it belongs to (an opaque identity token);
   * `existingParent` — the parent association the child already carries, if any
                        (`some p`), or `none` when the child carries none yet.
   Everything else about the child is orthogonal (mapping.md §2). -/
structure Child where
  key            : Nat
  existingParent : Option Nat
deriving Inhabited, DecidableEq

/- The parent a single child ends up associated with. A child that ALREADY
   carries an association keeps it untouched; a child that carries none is
   associated with the parent its key maps to under `lookup`. This is the
   desired behaviour: a pre-existing, more specific association is never
   discarded in favour of the one implied by the grouping key. -/
def resolveOne (lookup : Nat → Nat) (c : Child) : Nat :=
  match c.existingParent with
  | some p => p
  | none   => lookup c.key

/- The parents the whole batch of children ends up associated with, in batch
   order. Front-recursive so a single unfold is available per loop step (the
   fold pattern, plan §5.4). -/
def resolvedSeq (lookup : Nat → Nat) : List Child → List Nat
  | []      => []
  | c :: cs => resolveOne lookup c :: resolvedSeq lookup cs

@[simp] lemma resolvedSeq_nil (lookup : Nat → Nat) : resolvedSeq lookup [] = [] := rfl
lemma resolvedSeq_cons (lookup : Nat → Nat) (c : Child) (cs : List Child) :
    resolvedSeq lookup (c :: cs) = resolveOne lookup c :: resolvedSeq lookup cs := rfl

/- Exposing the element at index `i` on the front of `drop i`. -/
lemma drop_cons_eq (cs : List Child) (i : Nat) (hi : i < cs.length) :
    cs.drop i = cs[i]! :: cs.drop (i + 1) := by
  have h := List.drop_eq_getElem_cons hi
  rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi, Option.getD_some]
  exact h

/- The per-child fold step: dropping one fewer element exposes child `i-1` on the
   front, so `resolvedSeq` peels its resolved parent. This is the single goal
   `loom_solve` leaves for the loop body. -/
lemma resolvedSeq_drop_step (lookup : Nat → Nat) (cs : List Child) (i : Nat)
    (hi : 0 < i) (hle : i ≤ cs.length) :
    resolvedSeq lookup (cs.drop (i - 1)) =
      resolveOne lookup cs[i - 1]! :: resolvedSeq lookup (cs.drop i) := by
  have hlt : i - 1 < cs.length := by omega
  have hsucc : i - 1 + 1 = i := by omega
  rw [drop_cons_eq cs (i - 1) hlt, hsucc, resolvedSeq_cons]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Associate a batch of child objects with the parent objects they belong to,
   and report, in batch order, the parent each child ends up associated with.

   `lookup` maps a child's grouping key to the parent it belongs to. The desired
   behaviour (`resolvedSeq`): a child that ALREADY carries a parent association
   keeps that association untouched; only a child carrying none is associated
   with the parent its key maps to. A pre-existing, more specific association is
   never overwritten by the one implied by the grouping key.

   `children` and `lookup` are read-only (neither `mut`): the routine consults
   the batch and the mapping and builds a fresh list of outcomes, mutating
   nothing it is handed (directive 5). -/
method linkChildrenToParents (children : List Child) (lookup : Nat → Nat) return (out : List Nat)
  ensures out = resolvedSeq lookup children
  do
    -- impl-start
    let mut result : List Nat := []
    let mut i : Nat := children.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ children.length
      invariant result = resolvedSeq lookup (children.drop i)
      done_with i = 0
      decreasing i
    do
      let c := children[i - 1]!
      -- A child carrying no association yet is associated with the parent its
      -- key maps to; a child that already carries one keeps it untouched.
      let parent : Nat :=
        match c.existingParent with
        | some p => p
        | none   => lookup c.key
      result := parent :: result
      i := i - 1
    return result
    -- impl-end

prove_correct linkChildrenToParents by
  loom_solve <;>
    first
    | -- loop-entry: drop children.length = [], the fold is nil.
      (rw [List.drop_length]; simp)
    | -- loop-body step: peel child `i-1` from the fold (and the exit i = 0
      --   case, where `drop 0 = children` makes `result = resolvedSeq`).
      (rw [resolvedSeq_drop_step lookup children i (by omega) (by omega)]; simp_all [resolveOne])
