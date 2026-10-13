import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees and no A-reference deep model of an outside callee.
--  The decision modeled here is a self-contained per-element predicate over a
--  list of coordinate observations; it is spelled out DEEPLY in the `pure`
--  region below. The queries used to obtain each coordinate's observations are
--  unchanged and are not separately modeled — their results ARE the fields of
--  `Coord`. There is no `axiom` declaration.)
-- axioms-end

-- pure-start
/- The observations the admissibility decision can make about a single
   coordinate of a candidate point. A coordinate is abstracted to three
   independent booleans:

     * `numeric`      — the coordinate is a concrete number (as opposed to a
                        symbolic/undetermined expression);
     * `imagNonzero`  — the coordinate's imaginary part is *rigorously*
                        determined to be nonzero (a strict, three-valued
                        judgement: it is true only when the imaginary part is
                        provably not zero, and false when the imaginary part is
                        provably zero OR cannot be decided);
     * `imagPresent`  — a *coarse* indicator that the coordinate carries a
                        non-trivial imaginary-part object. It can be true even
                        for a coordinate whose imaginary part is in fact zero,
                        when that zero is left in an unsimplified form rather
                        than reduced to the literal zero object.

   `imagNonzero` and `imagPresent` are deliberately distinct: a real coordinate
   whose imaginary part is carried unsimplified has `imagNonzero = false` but
   `imagPresent = true`. The admissibility decision below consults only
   `numeric` and `imagNonzero`. -/
structure Coord where
  numeric     : Bool
  imagNonzero : Bool
  imagPresent : Bool
  deriving Inhabited, DecidableEq

/- A single coordinate counts as imaginary for the admissibility check exactly
   when it is a concrete number AND its imaginary part is rigorously determined
   to be nonzero. A coordinate whose imaginary part cannot be decided, or is
   only coarsely "present" but not provably nonzero, does NOT count. -/
def coordImaginary (c : Coord) : Bool :=
  c.numeric && c.imagNonzero

/- Whether ANY coordinate of the list counts as imaginary — the disjunction the
   admissibility guard evaluates over the coordinate sequence. Front-recursive so
   a single unfold is available per loop step (the backward-fold pattern). -/
def anyImaginary : List Coord → Bool
  | []      => false
  | c :: cs => coordImaginary c || anyImaginary cs

@[grind] lemma anyImaginary_nil : anyImaginary [] = false := rfl
@[grind] lemma anyImaginary_cons (c : Coord) (cs : List Coord) :
    anyImaginary (c :: cs) = (coordImaginary c || anyImaginary cs) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decide whether a candidate point's coordinate list must be rejected as
   having an imaginary coordinate. The desired behavior: reject (return `true`)
   exactly when some coordinate is a concrete number whose imaginary part is
   rigorously determined to be nonzero; otherwise accept (return `false`). In
   particular a real coordinate must be ACCEPTED even when its imaginary part
   happens to be carried in an unsimplified, non-reduced form — a coordinate is
   never rejected merely because a coarse "imaginary part present" indicator is
   set; rejection requires the imaginary part to be provably nonzero.

   `coords` is the read-only coordinate list (not `mut`): the decision inspects
   it and mutates no input (directive 5). -/
method imaginaryCoordCheck (coords : List Coord) return (out : Bool)
  ensures out = anyImaginary coords
  do
    -- impl-start
    -- Walk the coordinate list and accumulate the disjunction of the
    -- per-coordinate imaginary test `numeric ∧ (imaginary part provably
    -- nonzero)`. A coarse "imaginary part present" flag is never consulted, so
    -- a real coordinate with an unsimplified imaginary part is accepted.
    let mut result : Bool := false
    let mut i := coords.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ coords.length
      invariant result = anyImaginary (coords.drop i)
      done_with i = 0
      decreasing i
    do
      let c := coords[i - 1]!
      result := coordImaginary c || result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `anyImaginary` peels one `coordImaginary`. This is the
   single goal `loom_solve` leaves for the loop body. -/
lemma anyImaginary_drop_step (coords : List Coord) (i : Nat)
    (hi : 0 < i) (hle : i ≤ coords.length) :
    anyImaginary (coords.drop (i - 1))
      = (coordImaginary coords[i - 1]! || anyImaginary (coords.drop i)) := by
  have hlt : i - 1 < coords.length := by omega
  have hcons : coords.drop (i - 1) = coords[i - 1]! :: coords.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, anyImaginary_cons]

prove_correct imaginaryCoordCheck by
  loom_solve
  rw [anyImaginary_drop_step coords i (by omega) (by omega)]
  simp_all
