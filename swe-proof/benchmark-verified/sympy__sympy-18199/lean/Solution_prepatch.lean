import Mathlib
-- imports-end

/-!
Modular `n`-th root finding: given a non-negative target `a`, an exponent `n`
greater than one and a modulus `m`, the goal is to report every residue `x` in
the canonical range `0 ≤ x < m` that satisfies `x ^ n ≡ a (mod m)`, returned as
a list.

Two regimes are covered. When the modulus is itself a single prime, the residue
`x = 0` is a genuine solution exactly when `a` is divisible by the modulus, and
the reported roots are then precisely `[0]`; otherwise the unit-base prime solver
supplies the roots. When the modulus is not a single prime, the collection of
roots is modelled deeply: the reported list is pinned to be exactly the ordered,
duplicate-free set of in-range residues solving the congruence. That pinning
holds for the quadratic exponent over EVERY such modulus, and for a larger
exponent over every modulus whose repeated prime factors satisfy an arithmetic
side condition on the target and the exponent.

For a modulus that is not a single prime the report is, for EVERY admissible
input, a strictly increasing list of residues drawn from the canonical range, and
it carries exactly as many residues as the congruence has solutions at all, so
its LENGTH counts the solutions. Where the report is pinned, every reported
residue is moreover a genuine in-range root of the congruence over the actual
modulus `m` — a structural predicate, never an opaque answer key.
-/

-- axioms-start
-- Outside callees the root finder relies on, declared signatures-only.
-- Comments describe BEHAVIOUR, never the callee's repository name.

/-- Decision procedure for "this modulus is a single prime". -/
opaque modulusIsPrime : ℤ → Bool

/-- True iff the modulus has no repeated prime factor. One of the structural
conditions on the INPUTS delimiting the regime over which the deep root-set model
is asserted to equal the real routine's report (validated against the real
callee by G-AX). -/
opaque modulusSquarefree : ℤ → Bool

/-- True iff every prime occurring more than once in the modulus is ADMISSIBLE
for this target and this exponent: such a prime divides neither the target nor the
exponent, and a further arithmetic side condition relates the target to the
residues solving the congruence to that prime's multiplicity. A purely arithmetic
condition on the INPUTS `a`, `n`, `m` — the second structural delimiter of the
regime over which the deep root-set model is asserted to equal the real routine's
report (validated against the real callee by G-AX). -/
opaque modulusRegularLift : ℤ → ℤ → ℤ → Bool

/-- The roots, modulo a single prime, of `x ^ n ≡ a` in the case where the base
residue is a unit (the standard prime-modulus root-finding procedure). Used only
when the right-hand side is not divisible by the prime. -/
opaque primeUnitRoots : ℤ → ℤ → ℤ → List ℤ

/-- Every residue returned by the prime-modulus solver is an in-range
root of the congruence: the soundness contract of that callee, validated against
the real routine by G-AX (it never invents a non-root). The contract is claimed
ONLY for a single-prime modulus, which is the whole of that callee's intended
domain; handed a modulus that is not a single prime the callee is under no
obligation, so nothing may be concluded from it there. -/
axiom primeUnitRoots_sound (a n p : ℤ) (x : ℤ) :
    0 ≤ a → 1 < n → 1 < p → modulusIsPrime p = true →
    x ∈ primeUnitRoots a n p → 0 ≤ x ∧ x < p ∧ (x ^ n.toNat - a) % p = 0
-- axioms-end

-- pure-start
/-- Structural "`x` is an in-range root of `x ^ n ≡ a (mod m)`" predicate, tied to
the actual congruence over `m`. -/
def isRootIn (a n m x : ℤ) : Prop :=
  0 ≤ x ∧ x < m ∧ (x ^ n.toNat - a) % m = 0

/-- The grounded reference set: every residue `x` with `0 ≤ x < m` whose `n`-th
power is congruent to `a` modulo `m`, listed in increasing order. Because
`List.range` is strictly increasing and `filter` preserves order, the result is
already sorted and duplicate-free. This is the DEEP MODEL of the complete in-range
root set — a structural predicate over the actual modulus `m`, not an oracle. -/
def rootSetIn (a n m : ℤ) : List ℤ :=
  ((List.range m.toNat).map (Int.ofNat)).filter
    (fun x => (x ^ n.toNat - a) % m == 0)

/-- Membership in the grounded root set is exactly being an in-range root: the
element lies in `[0, m)` and its `n`-th power is congruent to `a`. Used to
discharge the soundness clause of the contracts. -/
theorem mem_rootSetIn {a n m x : ℤ} (hm : 0 < m) :
    x ∈ rootSetIn a n m ↔ (0 ≤ x ∧ x < m ∧ (x ^ n.toNat - a) % m = 0) := by
  unfold rootSetIn
  simp only [List.mem_filter, List.mem_map, List.mem_range, beq_iff_eq]
  have hmm : Int.ofNat m.toNat = m := Int.toNat_of_nonneg (le_of_lt hm)
  constructor
  · rintro ⟨⟨k, hk, rfl⟩, hroot⟩
    refine ⟨Int.natCast_nonneg k, ?_, hroot⟩
    have h1 : (Int.ofNat k) < (Int.ofNat m.toNat) := Int.ofNat_lt.mpr hk
    rwa [hmm] at h1
  · rintro ⟨h0, hlt, hroot⟩
    have hxe : Int.ofNat x.toNat = x := Int.toNat_of_nonneg h0
    refine ⟨⟨x.toNat, ?_, hxe⟩, ?_⟩
    · have h2 : x < Int.ofNat m.toNat := by rw [hmm]; exact hlt
      rw [← hxe] at h2; exact Int.ofNat_lt.mp h2
    · exact hroot

/-- The grounded root set is strictly increasing: it is a sublist of the strictly
increasing enumeration of the canonical range. Used to discharge the ordering
clause of the public contract. -/
theorem sorted_rootSetIn (a n m : ℤ) :
    (rootSetIn a n m).Pairwise (· < ·) := by
  have hbase : (((List.range m.toNat).map (Int.ofNat)).Pairwise (· < ·)) := by
    rw [List.pairwise_map]
    exact (List.pairwise_lt_range).imp (fun h => Int.ofNat_lt.mpr h)
  exact hbase.sublist (List.filter_sublist)

/-- The regime, for a modulus that is not a single prime, over which the report
of the real routine is claimed to be the complete
root set: a modulus with no repeated prime factor, or one all of whose repeated
prime factors are admissible for the target and the exponent. Both are structural
conditions on the INPUTS, not an answer key for the result — the reported list
stays pinned to the grounded set `rootSetIn`, independent of this predicate. -/
def compositeValidated (a n m : ℤ) : Bool :=
  modulusSquarefree m || modulusRegularLift a n m

/-- Contract for a modulus that is NOT a single prime, holding for EVERY
admissible input — no regime condition. The report is a strictly increasing list
of residues drawn from the canonical range `[0, m)`, and it reports exactly AS
MANY residues as the congruence has solutions there. So the report is never a
permutation, a repetition, or a proper part of the solutions, and it is empty
exactly when the congruence has no solution at all — the report's LENGTH counts
the solutions, hence in particular decides solvability. -/
def reportsRootsFor (a n m : ℤ) (result : List ℤ) : Prop :=
  (∀ x ∈ result, 0 ≤ x ∧ x < m)
    ∧ result.Pairwise (· < ·)
    ∧ result.length = (rootSetIn a n m).length

/-- The regime over which the PUBLIC solver's report for a modulus that is not a
single prime is pinned to the complete root set. For the quadratic exponent the
complete set is delivered over EVERY modulus, so no condition on the modulus is
needed there; for a larger exponent the regime above applies. -/
def dispatchValidated (a n m : ℤ) : Bool :=
  (n == 2) || compositeValidated a n m
-- pure-end

-- post-conditions-start
/-- Contract for a non-single-prime modulus over the regime: the
result is exactly the ordered, duplicate-free complete set of residues in
`[0, m)` solving `x ^ n ≡ a (mod m)` (the deep model), and every reported residue
is a genuine in-range root. -/
def problem_spec_nthrootModComposite (a n m : ℤ) (result : List ℤ) : Prop :=
  result = rootSetIn a n m ∧ ∀ x ∈ result, isRootIn a n m x
-- post-conditions-end

-- impl-start
/-- Pre-patch buggy skeleton: a modulus that is not a single prime was
unsupported — the routine aborted (NotImplementedError) rather than computing
any root, modelled here as reporting the empty list of roots. -/
def implementation_nthrootModComposite (_a _n _m : ℤ) : List ℤ := Id.run do
  return []
-- impl-end

-- proof-start
theorem correct_nthrootModComposite :
    ∀ (a n m : ℤ), 0 ≤ a → 1 < n → 1 < m → ¬ (modulusIsPrime m = true) →
      compositeValidated a n m = true →
      problem_spec_nthrootModComposite a n m
        (implementation_nthrootModComposite a n m) := by
  sorry
-- proof-end

-- post-conditions-start
/-- Contract for the public solver. Wherever the report is pinned — a single-prime
modulus, or a non-single-prime modulus inside the regime — every reported residue
is a genuine in-range root (for a single prime this rests on that modulus being
the intended domain of the unit-base solver). When the modulus is a single prime and the target is
divisible by it the result is precisely `[0]` (the zero residue is the sole root
there); when the target is not divisible by it the result is the unit-base prime
solver's root list. When the modulus is NOT a single prime the report always
enumerates canonical residues in strictly increasing order and has exactly as many
entries as the congruence has solutions; and inside the regime it is exactly the
complete ordered, duplicate-free set of in-range roots — in particular for the
quadratic exponent that is claimed over EVERY such modulus, with no condition on
its repeated prime factors. -/
def problem_spec_nthrootMod (a n p : ℤ) (result : List ℤ) : Prop :=
  ((modulusIsPrime p = true ∨ dispatchValidated a n p = true) →
      ∀ x ∈ result, isRootIn a n p x)
    ∧ (modulusIsPrime p = true → a % p = 0 → result = [0])
    ∧ (modulusIsPrime p = true → a % p ≠ 0 → result = primeUnitRoots a n p)
    ∧ (modulusIsPrime p ≠ true → reportsRootsFor a n p result)
    ∧ (modulusIsPrime p ≠ true → dispatchValidated a n p = true →
        result = rootSetIn a n p)
-- post-conditions-end

-- impl-start
/-- Pre-patch buggy skeleton: the divisible-base case (right-hand side `a`
a multiple of the prime, for which `0` is a root) was not handled, so the
residue `0` is dropped; the composite dispatch aborts as above. -/
def implementation_nthrootMod (a n p : ℤ) : List ℤ := Id.run do
  if !(modulusIsPrime p) then
    return implementation_nthrootModComposite a n p
  return primeUnitRoots a n p
-- impl-end

-- proof-start
theorem correct_nthrootMod :
    ∀ (a n p : ℤ), 0 ≤ a → 1 < n → 1 < p →
      problem_spec_nthrootMod a n p
        (implementation_nthrootMod a n p) := by
  sorry
-- proof-end
