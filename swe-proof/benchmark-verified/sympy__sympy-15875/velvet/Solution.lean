import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

/- One term of a commutative sum, reduced to the only four fuzzy observations the
   zero-decision reads. Each is a three-valued fact (`some true` = known true,
   `some false` = known false, `none` = undetermined):

   * `isReal`      — the term is a real quantity;
   * `isZero`      — the term equals zero (consulted only for real terms);
   * `isImaginary` — the term is a pure-imaginary quantity;
   * `iMulReal`    — multiplying the term by the imaginary unit yields a real
                     quantity (i.e. the term is "imaginary-or-zero"). -/
structure Term where
  isReal : Option Bool
  isZero : Option Bool
  isImaginary : Option Bool
  iMulReal : Option Bool
  deriving Inhabited, Repr, DecidableEq

-- axioms-start
/- The zero-decision for the residual sum of the strictly-real, definitely-nonzero
   terms. It is an UNCHANGED sub-decision the operation defers to: it inspects a
   smaller, all-real sum than the one under decision and returns the same
   three-valued verdict that the surrounding machinery would. Left OPAQUE — the
   operation refines around it, never reimplements it, so the proof claims no
   property of its value. Provenance + executable patch-invariance check:
   mapping.md §3 / axiom_check.py (G-AX). -/
opaque residualIsZero : List Term → Option Bool
-- axioms-end

-- pure-start
/- The running tally accumulated while scanning the terms:

   * `z`     — how many terms are real and known to be zero;
   * `nz`    — the terms that are real and known to be nonzero, in order;
   * `im`    — whether some term is pure-imaginary;
   * `imOrZ` — whether some term is imaginary-or-zero but not pure-imaginary;
   * `bail`  — whether some term defies classification, forcing an undetermined
               overall verdict. -/
structure Tally where
  z : Nat
  nz : List Term
  im : Bool
  imOrZ : Bool
  bail : Bool
  deriving Inhabited, Repr

/- Fold one term into the tally. Once a term has defied classification the tally
   is undetermined and stays so. A real term is counted as zero, recorded as
   nonzero, or (when its zero-ness is undetermined) forces a bail. A non-real
   term sets the imaginary or imaginary-or-zero flag, else forces a bail. -/
def classify (a : Term) (acc : Tally) : Tally :=
  if acc.bail then acc
  else if a.isReal = some true then
    if a.isZero = some true then { acc with z := acc.z + 1 }
    else if a.isZero = some false then { acc with nz := a :: acc.nz }
    else { acc with bail := true }
  else if a.isImaginary = some true then { acc with im := true }
  else if a.iMulReal = some true then { acc with imOrZ := true }
  else { acc with bail := true }

/- The tally of a whole term list. Front-recursive so a single unfold is
   available per loop step (the fold pattern, plan §5.4). -/
def tallyAll : List Term → Tally
  | []      => { z := 0, nz := [], im := false, imOrZ := false, bail := false }
  | a :: xs => classify a (tallyAll xs)

@[grind] lemma tallyAll_nil :
    tallyAll [] = { z := 0, nz := [], im := false, imOrZ := false, bail := false } := rfl
@[grind] lemma tallyAll_cons (a : Term) (xs : List Term) :
    tallyAll (a :: xs) = classify a (tallyAll xs) := rfl

/- The three-valued verdict from a completed tally over `n` terms.

   `isComm` carries the whole sum's commutativity fact: a definitely-noncommutative
   sum is undetermined outright. Otherwise: an unclassifiable term ⇒ undetermined;
   every term real-and-zero ⇒ the sum is zero; no real-nonzero term at all, OR
   every term real-nonzero ⇒ undetermined (the residual sub-decision is not
   informative here); otherwise consult the residual sub-decision over the
   real-nonzero terms and combine it with the imaginary tallies. -/
def verdict (isComm : Option Bool) (n : Nat) (acc : Tally) : Option Bool :=
  if isComm = some false then none
  else if acc.bail then none
  else if acc.z = n then some true
  else if acc.nz.length = 0 ∨ acc.nz.length = n then none
  else
    match residualIsZero acc.nz with
    | some true =>
        if !acc.imOrZ && !acc.im then some true
        else if acc.im && !acc.imOrZ then some false
        else none
    | some false => some false
    | none => none

/- The desired three-valued zero-verdict for a commutative sum of `args`. -/
def sumIsZeroSpec (isComm : Option Bool) (args : List Term) : Option Bool :=
  verdict isComm args.length (tallyAll args)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method sumIsZero (isComm : Option Bool) (args : List Term) return (out : Option Bool)
  ensures out = sumIsZeroSpec isComm args
  do
    -- impl-start
    let mut acc : Tally := { z := 0, nz := [], im := false, imOrZ := false, bail := false }
    let mut i := args.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ args.length
      invariant acc = tallyAll (args.drop i)
      done_with i = 0
      decreasing i
    do
      let a := args[i - 1]!
      acc := classify a acc
      i := i - 1
    return verdict isComm args.length acc
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `tallyAll` peels one `classify`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma tallyAll_drop_step (args : List Term) (i : Nat)
    (hi : 0 < i) (hle : i ≤ args.length) :
    tallyAll (args.drop (i - 1)) = classify args[i - 1]! (tallyAll (args.drop i)) := by
  have hlt : i - 1 < args.length := by omega
  have hcons : args.drop (i - 1) = args[i - 1]! :: args.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, tallyAll_cons]

prove_correct sumIsZero by
  loom_solve
  all_goals first
    | (rw [tallyAll_drop_step args i (by omega) (by omega)]; simp_all)
    | simp_all [sumIsZeroSpec]
