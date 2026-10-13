import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The only library predicate this operation relies on — the
   "is the coordinate order monotonic?" test — is modeled DEEPLY below
   (`isMonoInc` / `isMonoDec`) and validated against the real library predicate
   by axiom_check.py (G-AX, an A-reference), so it is not an opaque axiom. -/
-- axioms-end

-- pure-start
/- A coordinate axis of a combined result. `varies` is true when the axis takes
   different values across the inputs (so the inputs are joined along it); it is
   false for an axis whose values are identical in every input. `index` is the
   axis's resulting ordered values, modeled by their rank in any total order
   (relative order is the only observable property here). -/
structure Dimension where
  varies : Bool
  index  : List Int
  deriving Inhabited, Repr

/- The values are monotonically non-decreasing: each value is ≤ its successor.
   Front-recursive so a single unfold is available per loop step. Matches the
   non-strict semantics of the library's ascending-order test (equal neighbours
   are allowed). -/
def isMonoInc : List Int → Bool
  | []           => true
  | [_]          => true
  | a :: b :: cs => decide (a ≤ b) && isMonoInc (b :: cs)

/- The values are monotonically non-increasing: each value is ≥ its successor. -/
def isMonoDec : List Int → Bool
  | []           => true
  | [_]          => true
  | a :: b :: cs => decide (a ≥ b) && isMonoDec (b :: cs)

/- An axis is acceptably ordered iff it is monotonic in either direction. -/
def isMonotonic (xs : List Int) : Bool := isMonoInc xs || isMonoDec xs

/- The ordering obligation imposed by ONE axis: a joined axis must be monotonic;
   a non-varying axis imposes no constraint. -/
def dimOK (d : Dimension) : Bool := !d.varies || isMonotonic d.index

/- The whole result is acceptable iff every axis meets its obligation.
   Front-recursive (the Velvet fold pattern): a single unfold per loop step. -/
def allDimsOK : List Dimension → Bool
  | []      => true
  | d :: ds => dimOK d && allDimsOK ds

@[grind] lemma allDimsOK_nil : allDimsOK [] = true := rfl
@[grind] lemma allDimsOK_cons (d : Dimension) (ds : List Dimension) :
    allDimsOK (d :: ds) = (dimOK d && allDimsOK ds) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decide whether a combined result is acceptable: it succeeds (no ordering
   error) exactly when every joined axis is monotonic, while non-varying axes are
   exempt from the ordering requirement. -/
method validateOrdering (dims : List Dimension) return (ok : Bool)
  ensures ok = allDimsOK dims
  do
    -- impl-start
    let mut acc : Bool := true
    let mut i := dims.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ dims.length
      invariant acc = allDimsOK (dims.drop i)
      done_with i = 0
      decreasing i
    do
      let d := dims[i - 1]!
      acc := dimOK d && acc
      i := i - 1
    return acc
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `allDimsOK` peels one `dimOK`. This is the single goal
   `loom_solve` leaves for the loop body. -/
lemma allDimsOK_drop_step (dims : List Dimension) (i : Nat)
    (hi : 0 < i) (hle : i ≤ dims.length) :
    allDimsOK (dims.drop (i - 1)) = (dimOK dims[i - 1]! && allDimsOK (dims.drop i)) := by
  have hlt : i - 1 < dims.length := by omega
  have hcons : dims.drop (i - 1) = dims[i - 1]! :: dims.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, allDimsOK_cons]

prove_correct validateOrdering by
  loom_solve
  rw [allDimsOK_drop_step dims i (by omega) (by omega)]
  simp_all
