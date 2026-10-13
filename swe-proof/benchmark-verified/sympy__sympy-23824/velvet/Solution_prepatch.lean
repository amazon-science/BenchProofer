import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- The restoration of a leading run in front of a core term, preserving the
   leading run's original left-to-right order: the front element of the leading
   run, followed by the restoration of the rest of the run onto the same term.
   Front-recursive (one unfold per leading element) so a backward loop that
   prepends one element per step can discharge it (the Velvet fold pattern,
   plan §5.4). This is the deep model of the leading-run restoration's net
   effect — spelled out as the order-preserving concatenation, not hidden behind
   a callee axiom. -/
def restoreSeq : List Int → List Int → List Int
  | [],      tail => tail
  | c :: cs, tail => c :: restoreSeq cs tail

@[grind] lemma restoreSeq_nil (tail : List Int) : restoreSeq [] tail = tail := rfl
@[grind] lemma restoreSeq_cons (c : Int) (cs tail : List Int) :
    restoreSeq (c :: cs) tail = c :: restoreSeq cs tail := rfl

/- The restoration is exactly the order-preserving concatenation of the leading
   run and the core term: the leading factors, in their original order, then the
   term. (Pins the postcondition to ordinary list concatenation.) -/
@[grind] lemma restoreSeq_eq_append (leading tail : List Int) :
    restoreSeq leading tail = leading ++ tail := by
  induction leading with
  | nil => rfl
  | cons c cs ih => simp [restoreSeq_cons, ih]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Restore a leading run of uncontracted factors in front of one core-result
   term, preserving the leading factors' original left-to-right order. The
   leading run is the factors that precede the first contracted factor (in the
   order they appear in the input); the core term is one additive term produced
   by the surrounding rewrite. The restored term is the leading run, in its
   original order, followed by the core term. Both inputs are read only — a
   fresh term is built and returned. -/
method restoreLeading (leading : List Int) (tail : List Int) return (out : List Int)
  ensures out = leading ++ tail
  do
    -- impl-start
    -- Pre-image skeleton: each leading factor is inserted at the FRONT of the
    -- term in turn, scanning the leading run forward (factor 0 first, then
    -- factor 1 in front of it, ...). Successively front-inserting in forward
    -- index order places the leading factors in REVERSED order ahead of the
    -- term. The frozen spec requires the original order (`leading ++ tail`), so
    -- this reversed build fails the postcondition whenever the leading run has
    -- two or more distinct factors — prove_correct MUST fail (the spec sensing
    -- the reversed insertion).
    let mut result : List Int := tail
    let mut i := 0
    while i < leading.length
      invariant 0 ≤ i ∧ i ≤ leading.length
      invariant result = restoreSeq ((leading.take i).reverse) tail
      done_with i = leading.length
      decreasing leading.length - i
    do
      let c := leading[i]!
      result := c :: result
      i := i + 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `restoreSeq` peels one head onto the front of its
   output. This is the single goal `loom_solve` leaves for the loop body. -/
lemma restoreSeq_drop_step (leading tail : List Int) (i : Nat)
    (hi : 0 < i) (hle : i ≤ leading.length) :
    restoreSeq (leading.drop (i - 1)) tail = leading[i - 1]! :: restoreSeq (leading.drop i) tail := by
  have hlt : i - 1 < leading.length := by omega
  have hcons : leading.drop (i - 1) = leading[i - 1]! :: leading.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, restoreSeq_cons]

prove_correct restoreLeading by
  loom_solve
  rw [restoreSeq_drop_step leading tail i (by omega) (by omega)]
  simp_all
