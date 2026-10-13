import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed axiom: the per-operand exponent of a division chain is modelled
--  deeply by the pure rule `chainPower` below. There is no opaque unchanged
--  callee the proof leans on. Soundness of this deep model against the real
--  parser is checked by axiom_check.py / G-AX.)
-- axioms-end

-- pure-start
/- The resulting exponent of the operand at position `i` in a division chain
   written left to right as `u(0) / u(1) / … / u(n-1)`, interpreted as repeated
   division grouped to the LEFT: `(((u(0)/u(1))/u(2))/…)/u(n-1)`. The leading
   operand contributes exponent +1; every following operand contributes -1,
   independent of how deep it sits in the chain. -/
def chainPower (i : Nat) : Int :=
  if i = 0 then 1 else -1

/- The exponent vector of a chain of `n` operand positions, in textual order:
   element `k` is `chainPower k`. Built tail-recursively from a base offset `b`
   so the backward loop can peel one position per step. `expVecFrom b m` is the
   powers of positions `b, b+1, …, b+m-1`. -/
def expVecFrom (b : Nat) : Nat → List Int
  | 0     => []
  | m + 1 => chainPower b :: expVecFrom (b + 1) m

def expVec (n : Nat) : List Int := expVecFrom 0 n

@[grind] lemma expVecFrom_zero (b : Nat) : expVecFrom b 0 = [] := rfl
@[grind] lemma expVecFrom_succ (b m : Nat) :
    expVecFrom b (m + 1) = chainPower b :: expVecFrom (b + 1) m := rfl

@[grind] lemma expVecFrom_length (b m : Nat) : (expVecFrom b m).length = m := by
  induction m generalizing b with
  | zero => rfl
  | succ k ih => simp [expVecFrom_succ, ih]

@[grind] lemma expVec_length (n : Nat) : (expVec n).length = n := by
  simp [expVec, expVecFrom_length]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method reduceDivisionChain (n : Nat) return (out : List Int)
  ensures out = expVec n
  ensures out.length = n
  do
    -- impl-start
    -- Pre-image skeleton: the chain reduces with the OTHER grouping —
    -- `u(0) / (u(1) / (u(2) / …))` (right-nested: a single operand divides the
    -- recursively reduced remainder of the chain). Each nesting level negates
    -- everything below it, so position k receives the ALTERNATING exponent
    -- `(-1)^k` instead of the left-grouped +1 / -1 / -1 / …. The frozen spec
    -- demands `expVec` (+1 then all -1), so prove_correct MUST fail at the first
    -- position ≥ 2, where parity yields +1 but left-grouping demands -1.
    let mut result : List Int := []
    let mut i := n
    while i > 0
      invariant 0 ≤ i ∧ i ≤ n
      invariant result = expVecFrom i (n - i)
      done_with i = 0
      decreasing i
    do
      let e : Int := if (i - 1) % 2 = 0 then 1 else -1
      result := e :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: shrinking `i` by one exposes operand position `i-1`
   on the front, so `expVecFrom (i-1) (n-(i-1))` peels one `chainPower (i-1)`.
   This is the single goal `loom_solve` leaves for the loop body. -/
lemma expVecFrom_drop_step (n i : Nat) (hi : 0 < i) (hle : i ≤ n) :
    expVecFrom (i - 1) (n - (i - 1)) = chainPower (i - 1) :: expVecFrom i (n - i) := by
  have hk : n - (i - 1) = (n - i) + 1 := by omega
  rw [hk, expVecFrom_succ]
  have hb : (i - 1) + 1 = i := by omega
  rw [hb]

prove_correct reduceDivisionChain by
  loom_solve
  · rw [invariant_2, ← expVecFrom_drop_step n i (by omega) (by omega)]
  · injection i_2 with hi1 hr1
    subst hr1
    rw [invariant_2]; simp only [expVec, done_1, Nat.sub_zero]
