import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- The reference total of a finite sequence of real-valued coefficients, summed
   in order with each coefficient's sign preserved. Carried as `Rat` so the
   reference value is exact, and the sign of every coefficient participates in
   it (mapping.md §2). Front-recursive so a single unfold is available per loop
   step (the backward-fold pattern, plan §5.4). -/
def listSum : List Rat → Rat
  | []      => 0
  | x :: xs => x + listSum xs

@[grind] lemma listSum_nil : listSum [] = 0 := rfl
@[grind] lemma listSum_cons (x : Rat) (xs : List Rat) :
    listSum (x :: xs) = x + listSum xs := rfl

/- The magnitude scale of the same sequence, `Σ|xᵢ|`. This is the quantity the
   reported total's accuracy is measured against, and it also bounds every
   partial total; it is NOT itself a total. -/
def magSum : List Rat → Rat
  | []      => 0
  | x :: xs => (if x < 0 then -x else x) + magSum xs

@[grind] lemma magSum_nil : magSum [] = 0 := rfl
@[grind] lemma magSum_cons (x : Rat) (xs : List Rat) :
    magSum (x :: xs) = (if x < 0 then -x else x) + magSum xs := rfl

lemma magSum_nonneg (xs : List Rat) : 0 ≤ magSum xs := by
  induction xs with
  | nil => grind
  | cons a t ih =>
    have h : (0 : Rat) ≤ (if a < 0 then -a else a) := by
      by_cases ha : a < 0 <;> simp [ha] <;> grind
    grind

/- The accuracy the reported total is guaranteed to: the standard error bound
   for accumulating `n` values in an arithmetic of relative rounding `ulp`,
   `n · 2·ulp · Σ|xᵢ|`. `ulp` is a PARAMETER of the accumulating arithmetic, not
   a constant: the arithmetic that carries the accumulation is chosen by the
   caller along with the coefficients (mapping.md §2), and its relative rounding
   is what the accuracy scales with. The bound is proportional to the MAGNITUDE
   scale of the sequence, so the total of a sequence whose coefficients largely
   cancel is still pinned tightly in absolute terms. -/
def roundoffBound (ulp : Rat) (coeffs : List Rat) : Rat :=
  (coeffs.length : Rat) * (2 * ulp) * magSum coeffs

lemma roundoffBound_nonneg (ulp : Rat) (hu : 0 ≤ ulp) (coeffs : List Rat) :
    0 ≤ roundoffBound ulp coeffs := by
  have hn : (0 : Rat) ≤ (coeffs.length : Rat) := by
    exact_mod_cast Nat.zero_le coeffs.length
  have hu2 : (0 : Rat) ≤ 2 * ulp := by grind
  have hm : (0 : Rat) ≤ magSum coeffs := magSum_nonneg coeffs
  have h1 : (0 : Rat) ≤ (coeffs.length : Rat) * (2 * ulp) :=
    Rat.mul_nonneg hn hu2
  have := Rat.mul_nonneg h1 hm
  grind [roundoffBound]

/- The contract on the reported normalization total: it agrees with the
   order-preserving SIGNED total of the coefficients to within the accumulation
   error bound of the arithmetic that carries it. Every coefficient therefore
   contributes with its own sign — a negative coefficient REDUCES the total and
   is not folded in by its magnitude, a discrepancy `roundoffBound` is far too
   small to admit at any relative rounding a real arithmetic has. -/
def WithinRoundoff (ulp : Rat) (coeffs : List Rat) (out : Rat) : Prop :=
  listSum coeffs - roundoffBound ulp coeffs ≤ out ∧
    out ≤ listSum coeffs + roundoffBound ulp coeffs

@[grind] lemma withinRoundoff_exact (ulp : Rat) (hu : 0 ≤ ulp)
    (coeffs : List Rat) :
    WithinRoundoff ulp coeffs (listSum coeffs) := by
  have hb : (0 : Rat) ≤ roundoffBound ulp coeffs :=
    roundoffBound_nonneg ulp hu coeffs
  grind [WithinRoundoff]

/- The arithmetics an accumulation is actually carried in. A relative rounding
   and a finite range are not independent quantities that may be dialled to
   arbitrary values: each binary format determines BOTH at once, from its own
   significand width `p` (rounding `2⁻ᵖ`) and exponent bound `e` (range
   `2ᵉ - 2ᵉ⁻ᵖ`). The four alternatives below are the formats an accumulator
   uses, paired as those formats pair them (mapping.md §2). Quantifying over
   this set rather than over every positive `ulp` is what keeps the accuracy
   claim a statement about arithmetics that exist: an accuracy demanded at an
   arbitrarily small rounding would collapse to exactness, which no rounding
   accumulation has. -/
def RealArith (ulp maxMag : Rat) : Prop :=
  (ulp = 1 / 2 ^ 11 ∧ maxMag = 2 ^ 16    - 2 ^ 5)     ∨
  (ulp = 1 / 2 ^ 24 ∧ maxMag = 2 ^ 128   - 2 ^ 104)   ∨
  (ulp = 1 / 2 ^ 53 ∧ maxMag = 2 ^ 1024  - 2 ^ 971)   ∨
  (ulp = 1 / 2 ^ 64 ∧ maxMag = 2 ^ 16384 - 2 ^ 16320)

lemma realArith_ulp_pos (ulp maxMag : Rat) (h : RealArith ulp maxMag) :
    0 < ulp := by
  rcases h with ⟨h, _⟩ | ⟨h, _⟩ | ⟨h, _⟩ | ⟨h, _⟩ <;> subst h <;> grind

@[grind] lemma realArith_ulp_nonneg (ulp maxMag : Rat) (h : RealArith ulp maxMag) :
    0 ≤ ulp := Rat.le_of_lt (realArith_ulp_pos ulp maxMag h)

/- The sequences the accumulating arithmetic can carry at all. Every partial
   total of the sequence is bounded in magnitude by `Σ|xᵢ|`, and each partial
   total is itself carried with rounding, so what must fit the arithmetic's
   finite range is the magnitude scale TOGETHER WITH the accumulated error the
   same arithmetic incurs on it. A sequence meeting this bound accumulates to a
   real value in ANY summation order; outside it the arithmetic saturates and
   reports no real value at all, so it guarantees no accuracy there and the
   accuracy contract is stated only where it holds. The error term is
   load-bearing: `Σ|xᵢ| ≤ maxMag` alone leaves sequences whose accumulation
   still saturates. -/
def Accumulable (maxMag ulp : Rat) (coeffs : List Rat) : Prop :=
  magSum coeffs + roundoffBound ulp coeffs ≤ maxMag
-- pure-end

-- pre-conditions-start
-- (one block per modeled method; this bundle models one method)
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The normalization total used to scale a result by the coefficient sequence:
   the total of every coefficient, each contributing with its own sign, reported
   to within the accumulation error bound of the arithmetic that computes it. A
   negative coefficient must therefore reduce the total (it is NOT folded in by
   magnitude). `ulp` is that arithmetic's relative rounding and `maxMag` its
   finite range; `coeffs` is read-only — it is not declared `mut`
   (directive 5). -/
method windowSum (ulp : Rat) (maxMag : Rat) (coeffs : List Rat)
    return (out : Rat)
  require RealArith ulp maxMag
  require Accumulable maxMag ulp coeffs
  ensures WithinRoundoff ulp coeffs out
  do
    -- impl-start
    let mut acc : Rat := 0
    let mut i := coeffs.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ coeffs.length
      invariant acc = listSum (coeffs.drop i)
      done_with i = 0
      decreasing i
    do
      let x := coeffs[i - 1]!
      acc := x + acc
      i := i - 1
    return acc
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `listSum` peels one summand. This is the single goal
   `loom_solve` leaves for the loop body. -/
lemma listSum_drop_step (coeffs : List Rat) (i : Nat)
    (hi : 0 < i) (hle : i ≤ coeffs.length) :
    listSum (coeffs.drop (i - 1)) = coeffs[i - 1]! + listSum (coeffs.drop i) := by
  have hlt : i - 1 < coeffs.length := by omega
  have hcons : coeffs.drop (i - 1) = coeffs[i - 1]! :: coeffs.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, listSum_cons]

prove_correct windowSum by
  loom_solve
  rw [listSum_drop_step coeffs i (by omega) (by omega)]
  simp_all
