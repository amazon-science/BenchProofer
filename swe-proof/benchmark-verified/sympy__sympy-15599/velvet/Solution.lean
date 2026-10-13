import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed callee contracts. The factors of the product arrive as the
--  read-only input `factors`; classifying a factor as an integer literal and
--  taking its residue are concrete arithmetic, modeled deeply below. Every
--  observable is computed from `factors` and `q`; nothing is borrowed from an
--  oracle. See refinement.md / mapping.md.)
-- axioms-end

-- pure-start
/- A single factor of a product: either a concrete integer literal (`.num n`)
   or an opaque non-numeric factor (`.sym k`, identified by a code). These are
   the two outcomes of testing whether a factor is an integer literal. -/
inductive Factor where
  | num (n : Int)
  | sym (k : Int)
  deriving DecidableEq

instance : Inhabited Factor := ⟨.num 0⟩

/- Reduce one factor against the modulus `q`: an integer literal whose residue
   modulo `q` is non-zero collapses to that residue (the residue uses the
   sign-of-divisor convention, i.e. floored remainder); an integer literal with
   zero residue and every opaque factor are left exactly as they were. -/
def reduceFactor (q : Int) : Factor → Factor
  | .num n => if Int.fmod n q ≠ 0 then .num (Int.fmod n q) else .num n
  | .sym k => .sym k

/- The reduction of a whole factor list: reduce each factor independently,
   preserving order and length. Front-recursive so a single unfold is available
   per loop step (the fold pattern, plan §5.4). -/
def reduced (q : Int) : List Factor → List Factor
  | []      => []
  | f :: fs => reduceFactor q f :: reduced q fs

@[grind] lemma reduced_nil (q : Int) : reduced q [] = [] := rfl
@[grind] lemma reduced_cons (q : Int) (f : Factor) (fs : List Factor) :
    reduced q (f :: fs) = reduceFactor q f :: reduced q fs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method reduceModFactors (factors : List Factor) (q : Int) return (out : List Factor)
  require q ≠ 0
  require q ≠ 1
  ensures out = reduced q factors
  do
    -- impl-start
    let mut result : List Factor := []
    let mut i := factors.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ factors.length
      invariant result = reduced q (factors.drop i)
      done_with i = 0
      decreasing i
    do
      let f := factors[i - 1]!
      result := reduceFactor q f :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the factor at
   `i-1` on the front, so `reduced` peels one `reduceFactor`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma reduced_drop_step (q : Int) (factors : List Factor) (i : Nat)
    (hi : 0 < i) (hle : i ≤ factors.length) :
    reduced q (factors.drop (i - 1))
      = reduceFactor q factors[i - 1]! :: reduced q (factors.drop i) := by
  have hlt : i - 1 < factors.length := by omega
  have hcons : factors.drop (i - 1) = factors[i - 1]! :: factors.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, reduced_cons]

prove_correct reduceModFactors by
  loom_solve
  rw [reduced_drop_step q factors i (by omega) (by omega)]
  simp_all
