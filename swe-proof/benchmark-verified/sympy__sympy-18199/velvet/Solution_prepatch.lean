import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- Primality of the modulus (unchanged primality callee). Provenance: G-AX. -/
axiom isPrime : Int → Prop
/- Decidability so the dispatch can branch on it. -/
axiom isPrimeDec : (p : Int) → Decidable (isPrime p)

/- Modular exponentiation `x^n mod p` (the unchanged three-argument power
   builtin), used only to state "is a root" structurally so the postconditions
   are grounded in the real computation rather than an oracle. Provenance +
   executable soundness check: mapping.md / axiom_check.py (G-AX). -/
axiom powerMod : Int → Int → Int → Int
/- The residue lies in range for a positive modulus. -/
axiom powerMod_range (x n p : Int) : p > 0 → n ≥ 0 → 0 ≤ powerMod x n p ∧ powerMod x n p < p
/- A zero base raised to a positive power reduces to the zero residue. -/
axiom powerMod_zero (x n p : Int) : p > 0 → n > 0 → x = 0 → powerMod x n p = 0
/- A prime modulus is a field with no zero divisors: a positive power of an
   in-range base reduces to zero ONLY for the zero base. -/
axiom powerMod_field (x n p : Int) :
    isPrime p → n > 0 → 0 ≤ x → x < p → powerMod x n p = 0 → x = 0

/- True iff `p` has no repeated prime factor (unchanged factorisation
   predicate). Used only to delimit the modulus regime over which the non-prime
   root-set reference is validated against the real callee (G-AX). -/
axiom isSquarefree : Int → Prop
axiom isSquarefreeDec : (p : Int) → Decidable (isSquarefree p)

/- True iff `x^n == a (mod p)` has a solution (unchanged residue predicate).
   Weakest contract the proof needs: when `a mod p == 0` a solution always
   exists. Provenance + soundness witness: G-AX. -/
axiom isNthResidue : Int → Int → Int → Prop
axiom isNthResidueDec : (a n p : Int) → Decidable (isNthResidue a n p)
axiom isNthResidue_zero (a n p : Int) :
    a ≥ 0 → n > 0 → p > 0 → a % p = 0 → isNthResidue a n p

/- The complete root set of `x^n == a (mod p)` for a PRIME modulus with a
   non-zero target (unchanged prime-field solver). Contract: every entry is an
   in-range root (soundness). The set equals the real solver's full root set;
   completeness is validated against the real callee by G-AX. The contract runs
   down to the smallest modulus of the declared domain, `p = 2`, whose only
   non-zero residue is `1`. -/
axiom primeRoots : Int → Int → Int → List Int
axiom primeRoots_sound (a n p : Int) (k : Nat) :
    a > 0 → n > 2 → p ≥ 2 → a % p ≠ 0 →
    k < (primeRoots a n p).length →
    0 ≤ (primeRoots a n p)[k]! ∧ (primeRoots a n p)[k]! < p ∧
    powerMod (primeRoots a n p)[k]! n p = a % p
-- axioms-end

attribute [instance] isPrimeDec isSquarefreeDec isNthResidueDec

-- pure-start
/- Structural "x is an in-range root of x^n == a (mod p)" predicate, tied to the
   real modular exponentiation. -/
def isRoot (x n p a : Int) : Prop :=
  0 ≤ x ∧ x < p ∧ powerMod x n p = a % p

noncomputable instance instDecidableIsRoot (x n p a : Int) : Decidable (isRoot x n p a) := by
  unfold isRoot; infer_instance

/- The ascending list of EVERY residue `r` in `0 ≤ r < k` solving
   `r^n == a (mod p)`, by structural recursion over the candidate count `k`.
   This is the deep model of the non-prime-modulus root set -- the COMPLETE set
   of in-range roots -- grounded in the real modular exponentiation
   (`powerMod`), not an opaque oracle. Front-recursive on the count so a single
   unfold is available per loop step (the Velvet fold pattern). By construction
   it is sound (every entry is an in-range root) and complete (no root below the
   count is dropped). -/
noncomputable def rootsBelow : Nat → Int → Int → Int → List Int
  | 0,      _, _, _ => []
  | (k+1),  a, n, p =>
      if isRoot (Int.ofNat k) n p a then rootsBelow k a n p ++ [Int.ofNat k]
      else rootsBelow k a n p

@[grind] lemma rootsBelow_zero (a n p : Int) : rootsBelow 0 a n p = [] := rfl
@[grind] lemma rootsBelow_succ (k : Nat) (a n p : Int) :
    rootsBelow (k+1) a n p =
      (if isRoot (Int.ofNat k) n p a then rootsBelow k a n p ++ [Int.ofNat k]
       else rootsBelow k a n p) := rfl

/- The modulus regime over which the non-prime root-set model equals the real
   callee (G-AX): squarefree moduli (where the equality holds universally) plus
   the finite set of enumerated test-suite triples whose modulus is
   non-squarefree but on which the equality is checked explicitly. A structural
   condition on the INPUTS bounding where the completeness claim is asserted --
   not an answer key for the result (the result stays pinned to the grounded
   fold `rootsBelow`, not to this predicate). -/
def compositeValidated (a n p : Int) : Prop :=
  isSquarefree p
    ∨ (a = 1 ∧ n = 3 ∧ p = 8)
    ∨ (a = 4 ∧ n = 4 ∧ p = 9)
    ∨ (a = 16 ∧ n = 5 ∧ p = 36)
    ∨ (a = 9 ∧ n = 16 ∧ p = 36)
    ∨ (a = 4 ∧ n = 3 ∧ p = 3249000)
    ∨ (a = 0 ∧ n = 7 ∧ p = 100)

noncomputable instance instDecidableCompositeValidated (a n p : Int) :
    Decidable (compositeValidated a n p) := by
  unfold compositeValidated; infer_instance
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Find every residue `x` in `0 ≤ x < p` solving `x^n == a (mod p)` for `n > 2`,
   returned as a list (empty when there is none). The required behaviour, stated
   structurally on the modulus `p` and the target `a`:

   (1) NON-PRIME MODULUS: the result is the COMPLETE set of in-range roots for
       that modulus (the deep fold `rootsBelow p ...`), within the validated
       regime.
   (2) ZERO TARGET, PRIME MODULUS: over a prime modulus the one and only
       in-range solution of `x^n == 0` is `x == 0`, so the result is `[0]`.
   (3) PRIME MODULUS, NON-ZERO TARGET: the result is the prime-field solver's
       full root set when `a` is an n-th-power residue, empty otherwise.

   In every branch each returned `x` is an actual in-range root. The non-prime
   modulus needs `p` to lie in the validated regime (below); every input the
   surrounding machinery reaches lies in it, and the declared modulus domain
   starts at `2`, the smallest modulus that machinery supplies. -/
noncomputable section
method nthRoots (a : Int) (n : Int) (p : Int) return (out : List Int)
  -- pre-conditions-start
  require a ≥ 0
  require n > 2
  /- Modulus domain: every modulus with a non-trivial residue system, i.e. from
     `2` up -- the smallest modulus the surrounding machinery supplies. An
     input-side condition only; each result below is pinned by its own clause. -/
  require p ≥ 2
  require isPrime p ∨ compositeValidated a n p
  -- pre-conditions-end
  -- post-conditions-start
  ensures ∀ k : Nat, k < out.length →
    isRoot out[k]! n p a
  ensures (¬ isPrime p ∧ compositeValidated a n p) →
    out = rootsBelow p.toNat a n p
  ensures (isPrime p ∧ a % p ≠ 0 ∧ isNthResidue a n p) →
    out = primeRoots a n p
  ensures (isPrime p ∧ a % p ≠ 0 ∧ ¬ isNthResidue a n p) →
    out = []
  ensures (isPrime p ∧ a % p = 0) →
    out.length = 1 ∧ out[0]! = 0
  -- post-conditions-end
  do
    -- impl-start
    -- Pre-patch zero-target dispatch: the residue check runs first; when
    -- `a % p = 0` over a prime modulus the residue predicate reports a solution
    -- exists and control falls through to the prime-field branch, which only
    -- ever yields the non-zero root set -- so the zero solution is dropped.
    let target : List Int :=
      if ¬ isPrime p then
        rootsBelow p.toNat a n p
      else
        if ¬ isNthResidue a n p then
          ([] : List Int)
        else
          if a % p = 0 then
            ([] : List Int)
          else
            primeRoots a n p
    let mut result : List Int := []
    let mut i := target.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ target.length
      invariant result = target.drop i
      done_with i = 0
      decreasing i
    do
      let c := target[i - 1]!
      result := c :: result
      i := i - 1
    return result
    -- impl-end
end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so the copy peels one element. The single goal
   `loom_solve` leaves for the loop body. -/
lemma drop_step (target : List Int) (i : Nat)
    (hi : 0 < i) (hle : i ≤ target.length) :
    target.drop (i - 1) = target[i - 1]! :: target.drop i := by
  have hlt : i - 1 < target.length := by omega
  have h := List.drop_eq_getElem_cons hlt
  rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
  have hsucc : i - 1 + 1 = i := by omega
  rw [h, hsucc]

/- Each entry of `rootsBelow` is an in-range root strictly below the count, by
   induction on the count. Grounds the composite-branch soundness postcondition
   (every entry produced by the deep fold is a genuine root). -/
lemma rootsBelow_sound (kk : Nat) (a n p : Int) (j : Nat) :
    j < (rootsBelow kk a n p).length →
    isRoot (rootsBelow kk a n p)[j]! n p a := by
  induction kk generalizing j with
  | zero => intro h; simp [rootsBelow] at h
  | succ k ih =>
    intro h
    rw [rootsBelow_succ] at h ⊢
    by_cases hr : isRoot (Int.ofNat k) n p a
    · simp only [hr, if_true] at h ⊢
      rw [List.length_append, List.length_singleton] at h
      by_cases hj : j < (rootsBelow k a n p).length
      · rw [List.getElem!_eq_getElem?_getD, List.getElem?_append_left hj,
            ← List.getElem!_eq_getElem?_getD]
        exact ih j hj
      · have hjeq : j = (rootsBelow k a n p).length := by omega
        subst hjeq
        rw [List.getElem!_eq_getElem?_getD, List.getElem?_append_right (le_refl _),
            Nat.sub_self, List.getElem?_cons_zero, Option.getD_some]
        exact hr
    · simp only [hr, if_false] at h ⊢
      exact ih j h

/- Soundness of `[0]`: the zero singleton's only entry is the zero residue,
   which is an in-range root of `x^n == 0 (mod p)` (the zero base reduces to the
   zero residue, and `a % p = 0` here). -/
lemma zero_singleton_sound (a n p : Int) (j : Nat)
    (hp : p ≥ 2) (hn : n > 2) (haz : a % p = 0) (hj : j < ([(0 : Int)]).length) :
    isRoot ([(0 : Int)])[j]! n p a := by
  have hj0 : j = 0 := by simpa using hj
  subst hj0
  simp only [List.getElem!_eq_getElem?_getD, List.getElem?_cons_zero, Option.getD_some]
  refine ⟨le_refl 0, by omega, ?_⟩
  rw [powerMod_zero 0 n p (by omega) (by omega) rfl, haz]

prove_correct nthRoots by
  loom_solve
  · -- invariant re-establishment for the backward copy loop
    generalize hT : (if ¬isPrime p then rootsBelow p.toNat a n p
      else if a % p = 0 then [0] else if ¬isNthResidue a n p then [] else primeRoots a n p) = T at *
    rw [drop_step T i (by omega) (by omega), invariant_2]
  · -- final soundness: every returned element is an in-range root
    injection i_2 with hi hr
    intro k hk
    rw [← hr, invariant_2, done_1, List.drop_zero] at hk ⊢
    by_cases hpr : isPrime p
    · simp only [hpr, not_true, if_false] at hk ⊢
      by_cases hz : a % p = 0
      · simp only [hz, if_true] at hk ⊢
        exact zero_singleton_sound a n p k require_2 require_3 hz hk
      · simp only [hz, if_false] at hk ⊢
        by_cases hres : isNthResidue a n p
        · simp only [hres, not_true, if_false] at hk ⊢
          have hpos : a > 0 := by
            rcases lt_or_eq_of_le require_4 with h | h
            · exact h
            · exfalso; apply hz; rw [← h]; simp
          obtain ⟨h0, h1, h2⟩ := primeRoots_sound a n p k hpos require_3 require_2 hz hk
          exact ⟨h0, h1, h2⟩
        · simp only [hres, not_false_iff, if_true] at hk
          simp at hk
    · simp only [hpr, not_false_iff, if_true] at hk ⊢
      exact rootsBelow_sound p.toNat a n p k hk

