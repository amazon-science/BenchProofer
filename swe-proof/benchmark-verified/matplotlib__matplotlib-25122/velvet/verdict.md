# P2 adversarial audit — matplotlib__matplotlib-25122

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 10 admissible attacks re-run of 10 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_2.lean`, `atk_3.lean`, `atk_4.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No spec-breaking counterexample found. THREE same-spec wrong impls verify (atk_2 = listSum+roundoffBound, atk_3 = listSum-roundoffBound, atk_4 = partial-domain magSum fold guarded by `magSum <= listSum + roundoffBound`), but each one's FAITHFUL refined patch RESOLVES under the official harness, so none of them witnesses verify=>/=>correct. The reason is quantitative: the tolerance the postcondition admits is roundoffBound = n*2*ulp*magSum, which at the binary64 arithmetic the F2P test uses (flattop n=256, magSum=64.117) is 3.64e-12 absolute = 6.6e-14 relative on the total. Propagated through the scale_by_freq=False site (division by total**2) that perturbs `spec` by ~1.3e-13 relative, against an F2P assertion of atol=1e-8 on values of magnitude ~1e3 -- some 5 orders of magnitude of headroom. The real defect's margin is (magSum-listSum)/roundoffBound = 2.5e12 at n=256, i.e. the prepatch magnitude total sits 12 orders OUTSIDE the same interval. So the tolerance is wide enough to be true of the real rounding reduction and still far too narrow to admit the bug. Nearest miss recorded: atk_4 is a genuine partial-domain magnitude fold that VERIFIES, and it resolves precisely because its guard `magSum <= listSum + roundoffBound` is unsatisfiable at binary64 on every discriminating window -- the guard is infeasible exactly where the F2P test looks, so the impl degrades to the signed total there.
```

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -139,6 +139,11 @@
   ensures WithinRoundoff ulp coeffs out
   do
     -- impl-start
+    -- Pre-image skeleton: each coefficient is folded in by its MAGNITUDE
+    -- (|x|), so a negative coefficient ADDS instead of subtracting. The frozen
+    -- spec requires the signed total `listSum` (to within the accumulation
+    -- error bound, a tolerance far too small to absorb a flipped sign), so
+    -- prove_correct MUST fail on any sequence containing a negative coefficient.
     let mut acc : Rat := 0
     let mut i := coeffs.length
     while i > 0
@@ -148,7 +153,8 @@
       decreasing i
     do
       let x := coeffs[i - 1]!
-      acc := x + acc
+      let mag : Rat := if x < 0 then -x else x
+      acc := mag + acc
       i := i - 1
     return acc
     -- impl-end
```

Attack 2 — `atk_2.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -150,7 +150,7 @@
       let x := coeffs[i - 1]!
       acc := x + acc
       i := i - 1
-    return acc
+    return acc + roundoffBound ulp coeffs
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -169,5 +169,16 @@
 
 prove_correct windowSum by
   loom_solve
-  rw [listSum_drop_step coeffs i (by omega) (by omega)]
-  simp_all
+  case _ =>
+    rw [listSum_drop_step coeffs i (by omega) (by omega)]
+    simp_all
+  case _ =>
+    simp at i_3
+    obtain ⟨h1, h2⟩ := i_3
+    subst h1
+    subst done_1
+    simp at invariant_2
+    subst invariant_2
+    have hu : (0:Rat) ≤ ulp := realArith_ulp_nonneg ulp maxMag require_2
+    have hb : (0:Rat) ≤ roundoffBound ulp coeffs := roundoffBound_nonneg ulp hu coeffs
+    exact ⟨by grind [WithinRoundoff], by grind [WithinRoundoff]⟩
```

Attack 3 — `atk_3.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -150,7 +150,7 @@
       let x := coeffs[i - 1]!
       acc := x + acc
       i := i - 1
-    return acc
+    return acc - roundoffBound ulp coeffs
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -169,5 +169,16 @@
 
 prove_correct windowSum by
   loom_solve
-  rw [listSum_drop_step coeffs i (by omega) (by omega)]
-  simp_all
+  case _ =>
+    rw [listSum_drop_step coeffs i (by omega) (by omega)]
+    simp_all
+  case _ =>
+    simp at i_3
+    obtain ⟨h1, h2⟩ := i_3
+    subst h1
+    subst done_1
+    simp at invariant_2
+    subst invariant_2
+    have hu : (0:Rat) ≤ ulp := realArith_ulp_nonneg ulp maxMag require_2
+    have hb : (0:Rat) ≤ roundoffBound ulp coeffs := roundoffBound_nonneg ulp hu coeffs
+    exact ⟨by grind [WithinRoundoff], by grind [WithinRoundoff]⟩
```

Attack 4 — `atk_4.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -150,7 +150,10 @@
       let x := coeffs[i - 1]!
       acc := x + acc
       i := i - 1
-    return acc
+    if magSum coeffs ≤ listSum coeffs + roundoffBound ulp coeffs then
+      return magSum coeffs
+    else
+      return acc
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -169,5 +172,16 @@
 
 prove_correct windowSum by
   loom_solve
-  rw [listSum_drop_step coeffs i (by omega) (by omega)]
-  simp_all
+  all_goals (
+    first
+      | (rw [listSum_drop_step coeffs i (by omega) (by omega)]; simp_all)
+      | (have hu : (0:Rat) ≤ ulp := realArith_ulp_nonneg ulp maxMag require_2
+         have hb : (0:Rat) ≤ roundoffBound ulp coeffs := roundoffBound_nonneg ulp hu coeffs
+         have hml : ∀ xs : List Rat, listSum xs ≤ magSum xs := by
+           intro xs
+           induction xs with
+           | nil => grind
+           | cons a t ih => by_cases ha : a < 0 <;> simp_all [listSum, magSum] <;> grind
+         simp_all [WithinRoundoff]
+         grind)
+      | simp_all)
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -141,10 +141,10 @@
     -- impl-start
     let mut acc : Rat := 0
     let mut i := coeffs.length
-    while i > 0
+    while i > 1
       invariant 0 ≤ i ∧ i ≤ coeffs.length
       invariant acc = listSum (coeffs.drop i)
-      done_with i = 0
+      done_with i ≤ 1
       decreasing i
     do
       let x := coeffs[i - 1]!
@@ -169,5 +169,13 @@
 
 prove_correct windowSum by
   loom_solve
-  rw [listSum_drop_step coeffs i (by omega) (by omega)]
-  simp_all
+  all_goals (
+    first
+      | (rw [listSum_drop_step coeffs i (by omega) (by omega)]; simp_all)
+      | (have hu : (0:Rat) ≤ ulp := realArith_ulp_nonneg ulp maxMag require_2
+         have hb : (0:Rat) ≤ roundoffBound ulp coeffs := roundoffBound_nonneg ulp hu coeffs
+         simp_all [WithinRoundoff]
+         grind)
+      | grind [WithinRoundoff, listSum, magSum, roundoffBound]
+      | simp_all
+      | omega)
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -150,7 +150,7 @@
       let x := coeffs[i - 1]!
       acc := x + acc
       i := i - 1
-    return acc
+    return magSum coeffs
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -169,5 +169,16 @@
 
 prove_correct windowSum by
   loom_solve
-  rw [listSum_drop_step coeffs i (by omega) (by omega)]
-  simp_all
+  case _ =>
+    rw [listSum_drop_step coeffs i (by omega) (by omega)]
+    simp_all
+  case _ =>
+    simp at i_3
+    obtain ⟨h1, h2⟩ := i_3
+    subst h1
+    subst done_1
+    simp at invariant_2
+    subst invariant_2
+    have hu : (0:Rat) ≤ ulp := realArith_ulp_nonneg ulp maxMag require_2
+    have hb : (0:Rat) ≤ roundoffBound ulp coeffs := roundoffBound_nonneg ulp hu coeffs
+    exact ⟨by grind [WithinRoundoff], by grind [WithinRoundoff]⟩
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -140,16 +140,10 @@
   do
     -- impl-start
     let mut acc : Rat := 0
-    let mut i := coeffs.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ coeffs.length
-      invariant acc = listSum (coeffs.drop i)
-      done_with i = 0
-      decreasing i
+    while true
+      invariant True
     do
-      let x := coeffs[i - 1]!
-      acc := x + acc
-      i := i - 1
+      acc := acc + 1
     return acc
     -- impl-end
 
@@ -169,5 +163,13 @@
 
 prove_correct windowSum by
   loom_solve
-  rw [listSum_drop_step coeffs i (by omega) (by omega)]
-  simp_all
+  all_goals (
+    first
+      | (rw [listSum_drop_step coeffs i (by omega) (by omega)]; simp_all)
+      | (have hu : (0:Rat) ≤ ulp := realArith_ulp_nonneg ulp maxMag require_2
+         have hb : (0:Rat) ≤ roundoffBound ulp coeffs := roundoffBound_nonneg ulp hu coeffs
+         simp_all [WithinRoundoff]
+         grind)
+      | grind [WithinRoundoff, listSum, magSum, roundoffBound]
+      | simp_all
+      | omega)
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -150,7 +150,7 @@
       let x := coeffs[i - 1]!
       acc := x + acc
       i := i - 1
-    return acc
+    return acc + roundoffBound ulp coeffs / 2
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -169,5 +169,20 @@
 
 prove_correct windowSum by
   loom_solve
-  rw [listSum_drop_step coeffs i (by omega) (by omega)]
-  simp_all
+  case _ =>
+    rw [listSum_drop_step coeffs i (by omega) (by omega)]
+    simp_all
+  case _ =>
+    simp at i_3
+    obtain ⟨h1, h2⟩ := i_3
+    subst h1
+    subst done_1
+    simp at invariant_2
+    subst invariant_2
+    have hu : (0:Rat) ≤ ulp := realArith_ulp_nonneg ulp maxMag require_2
+    have hb : (0:Rat) ≤ roundoffBound ulp coeffs := roundoffBound_nonneg ulp hu coeffs
+    have hhalf : (0:Rat) ≤ roundoffBound ulp coeffs / 2 := by
+      exact div_nonneg hb (by norm_num)
+    have hle : roundoffBound ulp coeffs / 2 ≤ roundoffBound ulp coeffs := by
+      exact half_le_self hb
+    exact ⟨by grind [WithinRoundoff], by grind [WithinRoundoff]⟩
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

```diff
@@ -150,7 +150,7 @@
       let x := coeffs[i - 1]!
       acc := x + acc
       i := i - 1
-    return acc
+    return acc + roundoffBound ulp coeffs / 3
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -169,5 +169,22 @@
 
 prove_correct windowSum by
   loom_solve
-  rw [listSum_drop_step coeffs i (by omega) (by omega)]
-  simp_all
+  case _ =>
+    rw [listSum_drop_step coeffs i (by omega) (by omega)]
+    simp_all
+  case _ =>
+    simp at i_3
+    obtain ⟨h1, h2⟩ := i_3
+    subst h1
+    subst done_1
+    simp at invariant_2
+    subst invariant_2
+    have hu : (0:Rat) ≤ ulp := realArith_ulp_nonneg ulp maxMag require_2
+    have hb : (0:Rat) ≤ roundoffBound ulp coeffs := roundoffBound_nonneg ulp hu coeffs
+    have h3 : (0:Rat) ≤ roundoffBound ulp coeffs / 3 := by
+      exact div_nonneg hb (by norm_num)
+    have hle : roundoffBound ulp coeffs / 3 ≤ roundoffBound ulp coeffs := by
+      have h4 : roundoffBound ulp coeffs / 3 ≤ roundoffBound ulp coeffs / 1 := by
+        exact div_le_div_of_nonneg_left hb (by norm_num) (by norm_num)
+      simpa using h4
+    exact ⟨by grind [WithinRoundoff], by grind [WithinRoundoff]⟩
```

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

```diff
@@ -150,7 +150,7 @@
       let x := coeffs[i - 1]!
       acc := x + acc
       i := i - 1
-    return acc
+    return acc + (2 * ulp) * magSum coeffs
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -169,5 +169,41 @@
 
 prove_correct windowSum by
   loom_solve
-  rw [listSum_drop_step coeffs i (by omega) (by omega)]
-  simp_all
+  case _ =>
+    rw [listSum_drop_step coeffs i (by omega) (by omega)]
+    simp_all
+  case _ =>
+    simp at i_3
+    obtain ⟨h1, h2⟩ := i_3
+    subst h1
+    subst done_1
+    simp at invariant_2
+    subst invariant_2
+    have hu : (0:Rat) ≤ ulp := realArith_ulp_nonneg ulp maxMag require_2
+    have hb : (0:Rat) ≤ roundoffBound ulp coeffs := roundoffBound_nonneg ulp hu coeffs
+    have hm : (0:Rat) ≤ magSum coeffs := magSum_nonneg coeffs
+    have hlo : (0:Rat) ≤ (2 * ulp) * magSum coeffs := by
+      have h2 : (0:Rat) ≤ 2 * ulp := by grind
+      exact Rat.mul_nonneg h2 hm
+    have hhi : (2 * ulp) * magSum coeffs ≤ roundoffBound ulp coeffs := by
+      unfold roundoffBound
+      rcases Nat.eq_zero_or_pos coeffs.length with h0 | hpos
+      · have hz : magSum coeffs = 0 := by
+          cases coeffs with
+          | nil => grind
+          | cons a t => simp at h0
+        rw [hz]
+        simp
+      · have h1 : (1:Rat) ≤ (coeffs.length : Rat) := by
+          exact_mod_cast hpos
+        have h2 : (0:Rat) ≤ 2 * ulp := by grind
+        calc (2 * ulp) * magSum coeffs
+            = 1 * (2 * ulp) * magSum coeffs := by ring
+          _ ≤ (coeffs.length : Rat) * (2 * ulp) * magSum coeffs := by
+              have hstep : 1 * (2 * ulp) ≤ (coeffs.length : Rat) * (2 * ulp) := by
+                exact mul_le_mul_of_nonneg_right h1 h2
+              exact mul_le_mul_of_nonneg_right hstep hm
+    unfold WithinRoundoff
+    constructor
+    · grind
+    · grind
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
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
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL. Scratch dir (all files there). same_spec True for pos_control + all 10 attacks (only the impl region and the prove_correct body were edited): PYTHONPATH=src python3 -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('velvet'); print(same_spec(SOL, ATK, b.language))". Verify cmd for each: `bash scripts/lean_verify.sh <D>/atk_N.lean`. Every attack is sorry-free (grep -c sorry = 0 on all 10).

### VERIFY LEDGER (exit 0 = verifies).
- pos_control.lean (frozen gold impl) -> EXIT=0. Positive control holds.
- atk_1 = Solution_prepatch.lean, the PREPATCH BUG (magnitude fold) -> EXIT=1. Fails on the exact invariant, goal literally `(if coeffs[i-1]! < 0 then -... else...) + listSum (drop i) = coeffs[i-1]! + listSum (drop i)`. prepatch_reproduced=True.
- atk_2 = return listSum + roundoffBound (UPPER tolerance endpoint) -> EXIT=0 VERIFIES.
- atk_3 = return listSum - roundoffBound (LOWER tolerance endpoint) -> EXIT=0 VERIFIES.
- atk_4 = PARTIAL-DOMAIN: `if magSum coeffs <= listSum coeffs + roundoffBound ulp coeffs then return magSum coeffs else return acc` -> EXIT=0 VERIFIES.
- atk_5 = BOUNDARY/off-by-one, fold stops at i>1 so coeffs[0] is dropped -> EXIT=1 (rejected).
- atk_6 = UNGROUNDED-ORACLE ECHO, unconditional `return magSum coeffs` -> EXIT=1 (rejected; the tolerance genuinely discriminates the wrong quantity).
- atk_7 = CONTROL-FLOW-EFFECT, diverging `while true` with trivial invariant -> EXIT=1, and notably the FIRST error is `Decreasing annotations are required in total correctness semantics`. The `termination "total"` setting is load-bearing exactly as refinement.md claims.
- atk_8 = return listSum + roundoffBound/2 -> EXIT=1, atk_9 = +roundoffBound/3 -> EXIT=1, atk_10 = + (2*ulp)*magSum (per-element error model) -> EXIT=1. These are all mathematically INSIDE the admitted interval, so they are proof-engineering failures on my side (`linarith` is unavailable in this Velvet/Mathlib workspace and `grind` would not do the Rat division/multiplication monotonicity step), NOT evidence about the spec. I report them as rejected-as-run and do NOT count them as spec strength; atk_2/atk_3 already realize the two EXTREME endpoints of that same family, which is the strictly stronger probe, and both were carried all the way through resolve.

### MANDATORY RESOLVE RUNS (the decisive step; every verifying impl was materialized and executed).
Driver: PYTHONPATH=src python3 doresolve.py <name>, calling swebench_unified.harness.run_resolve('matplotlib__matplotlib-25122', patch, timeout=1800, retries=1).
First materialization (atk_N_faithful.patch) applied _window_total at ALL FOUR touched sites, including the squared one:
- atk_2 -> resolved=False, completed=True, "patch did not resolve in 2 attempts (consistent - not flaky)"
- atk_3 -> resolved=False, completed=True, same
- atk_4 -> resolved=True
I did NOT stop there and call BROKEN, because the non-resolve had to be attributed. Running the suite directly (`git apply` then pytest lib/matplotlib/tests/test_mlab.py) named the failure: TestSpectral::test_csd_padding[FsAll-default-complex], a PASS_TO_PASS test, asserting assert_almost_equal to 7 decimals on ~1.25e7 (ACTUAL 12501250.1249994 vs DESIRED 12501250.124998845). That test runs csd with window=mlab.window_none, i.e. an ALL-ONES window, where listSum == magSum exactly and the gold patch changes NOTHING; and it reaches the SQUARED site `(np.abs(window)**2).sum()`.

Both mapping.md sec.2 and refinement.md ("Why only the linear sum is the observable discriminator") state that this site changes no value because (|w|)^2 == w^2, and the shipped model binds `coeffs` to `window` (the LINEAR total) only -- there is no model node for the squared reduction. So applying windowSum's tolerance there was MY over-application of the refinement map, not a consequence of it. Second materialization (atk_Nlin_faithful.patch), the FAITHFUL one: perturb only the linear-total sites (magnitude, complex, and the `.sum()**2` site, which is a function of the linear total) and leave `(window**2).sum()` exactly as the GOLD patch leaves it. Re-run through the SAME official harness:
- atk_2lin -> resolved=True, completed=True ("resolved on attempt 2/2 (flaky: earlier attempt failed or did not complete)")
- atk_3lin -> resolved=True, completed=True ("resolved")
- atk_4lin -> resolved=True, completed=True ("resolved on attempt 2/2 (flaky)")
Cross-checked outside the harness: full test_mlab.py suite = 2424 passed for the atk_2lin, atk_3lin and atk_4lin patches (0 failures), vs 1 failed / 357 passed for the over-applied atk_2 patch. The patch texts submitted in `patches` are the FAITHFUL (linear-only) ones, which is what the refinement map licenses; all three apply cleanly to the base_commit worktree (git apply --check OK).

### WHY THE TOLERANCE IS NOT A HOLE (quantified in-container, numpy 1.26.4 / testbed image).
flattop windows built exactly as the F2P test builds them: n=33 bound=5.88e-14 vs (magSum-listSum)/bound=1.91e13; n=100 5.53e-13 vs 6.42e12; n=256 3.64e-12 vs 2.51e12; n=512 1.46e-11 vs 1.25e12. Propagating the endpoint perturbation through the scale_by_freq=False site gives a relative error on spec*win.sum()**2 of -1.71e-14 (n=33), -5.20e-14 (n=100), -1.33e-13 (n=256), -2.65e-13 (n=512) -- all ~5 orders inside the F2P atol=1e-8. The interval is therefore simultaneously (a) true of the real pairwise rounding reduction and (b) 12 orders too tight to admit the magnitude total. That is the exact property a tolerance postcondition needs, and it is why atk_2/atk_3/atk_4 verify AND resolve rather than breaking the bundle.

### A-LEG AUDIT (the assignment's focus; refinement.md has no kind-3 and no consumed axioms).
Legs are A0=R, A1=R, A2=A-reference + I, A3=I (deletion). No kind-3 step; the single occurrence of the string "kind-3" is the section heading asserting their absence, which the table bears out. I independently re-derived the A2 A-reference against the REAL callee rather than trusting the doc: axaudit.py rebuilds 8 windows (4 flattops, hanning2048, blackman8192, the [1,2^53,1,-2^53] cancellation witness, ones256) in float16/float32/float64/longdouble, reads coefficients BACK OFF the built array, builds each (ulp,maxMag) pair from np.finfo as the doc specifies, skips pairs Accumulable rejects, and checks in exact Fraction arithmetic that the real w.sum() satisfies WithinRoundoff. Result: 0 A-reference violations, 0 saturations on Accumulable-admitted inputs.

Note my own first run reported 3 longdouble "violations" -- that was my bug, plain float() truncating np.longdouble, precisely the trap mapping.md warns about; using frexp/ldexp to get the exact 64-bit-significand rational cleared all three. The doc's self-reported float16 limitation reproduces honestly and is correctly disclosed: at float16 the magnitude total falls INSIDE the interval for flattop256 (gap/bound=0.571) and flattop512 (0.285).

That is not exploitable, and I confirmed why rather than assuming: RealArith is a `require` on the arguments, not a disjunction the impl may select, so a verifying impl owes the postcondition on the SAME coeffs at binary64 too, where the margin is 2.5e12 -- which is exactly why atk_6's unconditional magSum fold is REJECTED (EXIT=1) and why atk_4 had to guard its magnitude branch with a predicate that is infeasible at binary64.

VERDICT SOUND, advisory. 10 attacks encoded and run (>=5 required), all same-spec and sorry-free, covering prepatch-bug re-encode, both tolerance extremes, partial-domain, boundary/off-by-one, control-flow-effect/divergence, ungrounded-oracle echo, and three interior-point error models. Positive control verifies; prepatch reproduced as a failure. Three wrong impls verify and ALL THREE had their faithful patches materialized and EXECUTED through run_resolve -- every one resolved, so no verify=>/=>correct witness exists here. Caveat for the re-runner: atk_8/9/10 are inside-interval impls that my tactics could not close (no linarith in this workspace); if a stronger proof closes them their faithful patches would be even smaller perturbations than atk_2/atk_3, which already resolve, so the conclusion is unchanged.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 10 admissible attacks re-run of 10 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_2.lean`, `atk_3.lean`, `atk_4.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No spec-breaking counterexample found. THREE same-spec wrong impls verify (atk_2 = listSum+roundoffBound, atk_3 = listSum-roundoffBound, atk_4 = partial-domain magSum fold guarded by `magSum <= listSum + roundoffBound`), but each one's FAITHFUL refined patch RESOLVES under the official harness, so none of them witnesses verify=>/=>correct. The reason is quantitative: the tolerance the postcondition admits is roundoffBound = n*2*ulp*magSum, which at the binary64 arithmetic the F2P test uses (flattop n=256, magSum=64.117) is 3.64e-12 absolute = 6.6e-14 relative on the total. Propagated through the scale_by_freq=False site (division by total**2) that perturbs `spec` by ~1.3e-13 relative, against an F2P assertion of atol=1e-8 on values of magnitude ~1e3 -- some 5 orders of magnitude of headroom. The real defect's margin is (magSum-listSum)/roundoffBound = 2.5e12 at n=256, i.e. the prepatch magnitude total sits 12 orders OUTSIDE the same interval. So the tolerance is wide enough to be true of the real rounding reduction and still far too narrow to admit the bug. Nearest miss recorded: atk_4 is a genuine partial-domain magnitude fold that VERIFIES, and it resolves precisely because its guard `magSum <= listSum + roundoffBound` is unsatisfiable at binary64 on every discriminating window -- the guard is infeasible exactly where the F2P test looks, so the impl degrades to the signed total there.
```

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 10 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_3.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 4 — `atk_4.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
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
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL. Scratch dir (all files there). same_spec True for pos_control + all 10 attacks (only the impl region and the prove_correct body were edited): PYTHONPATH=src python3 -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('velvet'); print(same_spec(SOL, ATK, b.language))". Verify cmd for each: `bash scripts/lean_verify.sh <D>/atk_N.lean`. Every attack is sorry-free (grep -c sorry = 0 on all 10).

### VERIFY LEDGER (exit 0 = verifies).
- pos_control.lean (frozen gold impl) -> EXIT=0. Positive control holds.
- atk_1 = Solution_prepatch.lean, the PREPATCH BUG (magnitude fold) -> EXIT=1. Fails on the exact invariant, goal literally `(if coeffs[i-1]! < 0 then -... else...) + listSum (drop i) = coeffs[i-1]! + listSum (drop i)`. prepatch_reproduced=True.
- atk_2 = return listSum + roundoffBound (UPPER tolerance endpoint) -> EXIT=0 VERIFIES.
- atk_3 = return listSum - roundoffBound (LOWER tolerance endpoint) -> EXIT=0 VERIFIES.
- atk_4 = PARTIAL-DOMAIN: `if magSum coeffs <= listSum coeffs + roundoffBound ulp coeffs then return magSum coeffs else return acc` -> EXIT=0 VERIFIES.
- atk_5 = BOUNDARY/off-by-one, fold stops at i>1 so coeffs[0] is dropped -> EXIT=1 (rejected).
- atk_6 = UNGROUNDED-ORACLE ECHO, unconditional `return magSum coeffs` -> EXIT=1 (rejected; the tolerance genuinely discriminates the wrong quantity).
- atk_7 = CONTROL-FLOW-EFFECT, diverging `while true` with trivial invariant -> EXIT=1, and notably the FIRST error is `Decreasing annotations are required in total correctness semantics`. The `termination "total"` setting is load-bearing exactly as refinement.md claims.
- atk_8 = return listSum + roundoffBound/2 -> EXIT=1, atk_9 = +roundoffBound/3 -> EXIT=1, atk_10 = + (2*ulp)*magSum (per-element error model) -> EXIT=1. These are all mathematically INSIDE the admitted interval, so they are proof-engineering failures on my side (`linarith` is unavailable in this Velvet/Mathlib workspace and `grind` would not do the Rat division/multiplication monotonicity step), NOT evidence about the spec. I report them as rejected-as-run and do NOT count them as spec strength; atk_2/atk_3 already realize the two EXTREME endpoints of that same family, which is the strictly stronger probe, and both were carried all the way through resolve.

### MANDATORY RESOLVE RUNS (the decisive step; every verifying impl was materialized and executed).
Driver: PYTHONPATH=src python3 doresolve.py <name>, calling swebench_unified.harness.run_resolve('matplotlib__matplotlib-25122', patch, timeout=1800, retries=1).
First materialization (atk_N_faithful.patch) applied _window_total at ALL FOUR touched sites, including the squared one:
- atk_2 -> resolved=False, completed=True, "patch did not resolve in 2 attempts (consistent - not flaky)"
- atk_3 -> resolved=False, completed=True, same
- atk_4 -> resolved=True
I did NOT stop there and call BROKEN, because the non-resolve had to be attributed. Running the suite directly (`git apply` then pytest lib/matplotlib/tests/test_mlab.py) named the failure: TestSpectral::test_csd_padding[FsAll-default-complex], a PASS_TO_PASS test, asserting assert_almost_equal to 7 decimals on ~1.25e7 (ACTUAL 12501250.1249994 vs DESIRED 12501250.124998845). That test runs csd with window=mlab.window_none, i.e. an ALL-ONES window, where listSum == magSum exactly and the gold patch changes NOTHING; and it reaches the SQUARED site `(np.abs(window)**2).sum()`.

Both mapping.md sec.2 and refinement.md ("Why only the linear sum is the observable discriminator") state that this site changes no value because (|w|)^2 == w^2, and the shipped model binds `coeffs` to `window` (the LINEAR total) only -- there is no model node for the squared reduction. So applying windowSum's tolerance there was MY over-application of the refinement map, not a consequence of it. Second materialization (atk_Nlin_faithful.patch), the FAITHFUL one: perturb only the linear-total sites (magnitude, complex, and the `.sum()**2` site, which is a function of the linear total) and leave `(window**2).sum()` exactly as the GOLD patch leaves it. Re-run through the SAME official harness:
- atk_2lin -> resolved=True, completed=True ("resolved on attempt 2/2 (flaky: earlier attempt failed or did not complete)")
- atk_3lin -> resolved=True, completed=True ("resolved")
- atk_4lin -> resolved=True, completed=True ("resolved on attempt 2/2 (flaky)")
Cross-checked outside the harness: full test_mlab.py suite = 2424 passed for the atk_2lin, atk_3lin and atk_4lin patches (0 failures), vs 1 failed / 357 passed for the over-applied atk_2 patch. The patch texts submitted in `patches` are the FAITHFUL (linear-only) ones, which is what the refinement map licenses; all three apply cleanly to the base_commit worktree (git apply --check OK).

### WHY THE TOLERANCE IS NOT A HOLE (quantified in-container, numpy 1.26.4 / testbed image).
flattop windows built exactly as the F2P test builds them: n=33 bound=5.88e-14 vs (magSum-listSum)/bound=1.91e13; n=100 5.53e-13 vs 6.42e12; n=256 3.64e-12 vs 2.51e12; n=512 1.46e-11 vs 1.25e12. Propagating the endpoint perturbation through the scale_by_freq=False site gives a relative error on spec*win.sum()**2 of -1.71e-14 (n=33), -5.20e-14 (n=100), -1.33e-13 (n=256), -2.65e-13 (n=512) -- all ~5 orders inside the F2P atol=1e-8. The interval is therefore simultaneously (a) true of the real pairwise rounding reduction and (b) 12 orders too tight to admit the magnitude total. That is the exact property a tolerance postcondition needs, and it is why atk_2/atk_3/atk_4 verify AND resolve rather than breaking the bundle.

### A-LEG AUDIT (the assignment's focus; refinement.md has no kind-3 and no consumed axioms).
Legs are A0=R, A1=R, A2=A-reference + I, A3=I (deletion). No kind-3 step; the single occurrence of the string "kind-3" is the section heading asserting their absence, which the table bears out. I independently re-derived the A2 A-reference against the REAL callee rather than trusting the doc: axaudit.py rebuilds 8 windows (4 flattops, hanning2048, blackman8192, the [1,2^53,1,-2^53] cancellation witness, ones256) in float16/float32/float64/longdouble, reads coefficients BACK OFF the built array, builds each (ulp,maxMag) pair from np.finfo as the doc specifies, skips pairs Accumulable rejects, and checks in exact Fraction arithmetic that the real w.sum() satisfies WithinRoundoff. Result: 0 A-reference violations, 0 saturations on Accumulable-admitted inputs.

Note my own first run reported 3 longdouble "violations" -- that was my bug, plain float() truncating np.longdouble, precisely the trap mapping.md warns about; using frexp/ldexp to get the exact 64-bit-significand rational cleared all three. The doc's self-reported float16 limitation reproduces honestly and is correctly disclosed: at float16 the magnitude total falls INSIDE the interval for flattop256 (gap/bound=0.571) and flattop512 (0.285).

That is not exploitable, and I confirmed why rather than assuming: RealArith is a `require` on the arguments, not a disjunction the impl may select, so a verifying impl owes the postcondition on the SAME coeffs at binary64 too, where the margin is 2.5e12 -- which is exactly why atk_6's unconditional magSum fold is REJECTED (EXIT=1) and why atk_4 had to guard its magnitude branch with a predicate that is infeasible at binary64.

VERDICT SOUND, advisory. 10 attacks encoded and run (>=5 required), all same-spec and sorry-free, covering prepatch-bug re-encode, both tolerance extremes, partial-domain, boundary/off-by-one, control-flow-effect/divergence, ungrounded-oracle echo, and three interior-point error models. Positive control verifies; prepatch reproduced as a failure. Three wrong impls verify and ALL THREE had their faithful patches materialized and EXECUTED through run_resolve -- every one resolved, so no verify=>/=>correct witness exists here. Caveat for the re-runner: atk_8/9/10 are inside-interval impls that my tactics could not close (no linarith in this workspace); if a stronger proof closes them their faithful patches would be even smaller perturbations than atk_2/atk_3, which already resolve, so the conclusion is unchanged.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** G-PANEL-2 (faithfulness-break): attempted to show the spec is TOO STRONG / drifts from real repo behavior. Could not. No diverging input found.

REFERENCE DISCIPLINE: modeled function's reference = worktree WITH patch.diff applied (post-patch `window.sum()` = signed total). I did NOT report the signed-vs-magnitude delta as a divergence -- that IS the patch. Base commit used only for untouched callees (numpy's reduction), which is what the A-reference models.

SPEC REGION INTEGRITY: swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend()) = True -- spec region byte-identical, so the prepatch twin is refuted by the SAME frozen spec (no spec-side cheating). Solution.lean verifies via scripts/lean_verify.sh, exit 0, no sorry/error. Semantics are total (`loom.semantics.termination "total"`), so a `while true` diverging rival is excluded (the G-PANEL-1 finding is genuinely repaired).

WHAT THE SPEC CLAIMS: out is within n*2*ulp*Sum|w_i| of the exact SIGNED total listSum, for (ulp,maxMag) in RealArith's four format pairs, on inputs Accumulable admits. The falsifiable content is (a) is the bound TRUE of real numpy, (b) are the RealArith constants real, (c) does Accumulable admit an input whose real reduction saturates.

MY INDEPENDENT TESTING (own reimplementation of the pure region from Solution.lean; did NOT reuse bundle oracle code; exact Fraction arithmetic throughout; coefficients read BACK OFF the built array per format; width-safe rational extraction via frexp, never float() on a longdouble):

1. RealArith constants vs np.finfo -- all four pairs match EXACTLY: float16 (u=2^-11, 2^16-2^5), float32 (2^-24, 2^128-2^104), float64 (2^-53, 2^1024-2^971), longdouble (2^-64, 2^16384-2^16320), verified p=nmant+1, e=maxexp. No drift from the formats numpy actually reduces in.

2. Structured families (real window fns hann/hamming/blackman/bartlett/kaiser x 22 lengths to 8192, cosine-sum flattop, boundary/sentinel cases, catastrophic cancellation [1,2^53,1,-2^53], the [32768]+[17]*1024 float16 bias-climb, near-maxMag edges): 1256 (window,arith) observations, 0 violations, 0 saturations.

3. Long-window fuzz (float16-focused large n up to 6000, wide-dynamic-range +-60 exponents, cancellation pairs, per-format Accumulable-edge saturation hunt): 35584 observations, 0 violations, 0 saturations. Worst err/bound: f16 0.162, f32 0.241, f64 0.267, ld 0.283.

4. SUBNORMAL / gradual-underflow attack -- the classic break point for a RELATIVE error bound, since near the underflow threshold add error is ABSOLUTE (subnormal spacing) not relative to operands. 12000 observations in the subnormal zones of all four formats: 0 violations. Worst f16 0.154, f32 0.011, f64 0.0, ld 0.0 (subnormal-grid adds are exact, so error is genuinely zero there).

5. High-volume mixed fuzz incl. all three narrow formats' subnormal zones and near-f64-max: 21001 observations, 0 violations, worst ratio 0.284 (>3.5x margin).

6. Targeted saturation attack (finite coeffs, Accumulable admits, force.sum() non-finite via front-load-then-cancel, peak-then-cancel, bias-climb, alternating-big at the exact Accumulable cap per format): 0 saturations. The error term in Accumulable does the work claimed for it.

7. VERSION ROBUSTNESS: identical results (21001 obs, 0 violations, same worst ratios) under numpy 1.26.4 and numpy 2.2.6. The bound is the order-independent sequential one and dominates numpy's pairwise error (~log2(n)*u vs n*2u), so it is not fitted to one version's blocking scheme -- a real soundness property, not a coincidence.

8. NON-VACUITY: preconditions jointly admit the real domain (hann n=32..8192 admitted at both float64 and float16). Tolerance is a real tolerance, not disguised exactness: 1+2^-64 != listSum [1] yet satisfies WithinRoundoff at all four ariths. And withinRoundoff_exact is not the whole story -- the interval is two-sided and finite.

9. NOT TOO WEAK EITHER (checked, since a too-weak spec is the dual failure): the prepatch magnitude total is REJECTED by the postcondition at 14 of 16 (window,arith) cells I measured, with gap/bound = 5.1e13 (f64,n=8), 1.0e13 (f64,n=64), 1.25e12 (f64,n=512), 3.1e11 (f64,n=2048) -- reproducing mapping.md's disclosed figures. The only cells where the interval admits the magnitude total are float16 at n>=512 (gap/bound 0.285 and 0.0713), which mapping.md DISCLOSES explicitly rather than hiding. That is not a hole: RealArith is a precondition on ARGUMENTS, not a disjunction the impl may pick, so a verifying impl owes the postcondition on the same coeffs at the float64 arithmetic where the gap is 1.25e12x the bound. Independently, the prepatch twin fails structurally on its exact loop invariant `acc = listSum (coeffs.drop i)` for EVERY ulp.

10. Bundle's own axiom_check.py run independently: G-AX OK (40000 fuzz + 21939 (window,arith) observations, Accumulable never admitted a saturating input). Consistent with my independent numbers.

CONCLUSION: the postcondition states what the callee GUARANTEES rather than asserting exactness (which mapping.md correctly measures to be FALSE of the callee -- pairwise reduction, and [1,2^53,1,-2^53] -> 0.0 vs exact 2.0). ulp is parameterized because _spectral_helper propagates the caller's dtype unnormalized (mlab.py:377), and is confined to RealArith's four real format pairs so it cannot be driven toward 0 to recover exactness. Across ~70k independent (input, arithmetic) observations on two numpy versions I found no input where the modeled function disagrees with the real callee. Spec is faithful; no divergence to cite.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** SCOPE. No relaxation in this bundle, measured not assumed: no RELAXED_LEAKAGE.md anywhere under the instance dir (`find -iname '*RELAX*'` = empty), and no top-level `relaxed_leakage` key in meta.json (`'relaxed_leakage' in meta` = False; the only substring hits in meta.json are inside the ARCHIVED G-PANEL-3 prose of a prior run, which itself says the key is absent). So this is a standard strict leakage review with no inherited disposition and no unavoidability argument to re-derive.

ARTIFACT IDENTITY. Judged the frozen live artifact: sha256(Solution.lean)=307084b25cb82fe8a302071dcfb102cd42cf07c783407993daea61e4817d9ca0, byte-identical to meta.json gates['G-LEAK'].sources['Solution.lean']. Derived the spec view myself via swebench_unified.markers.spec_view(VelvetBackend()) (I loaded the real VelvetBackend LanguageTables rather than passing a flavor string, which the harness rejects). markers.same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend) = True, and the two projected views are BYTE-IDENTICAL at 7562 bytes, sha256 cab155b6d3e1935675cf85a9f079a04248d9a5954951ce3eb3b329fb48614e68 == meta G-HYGIENE region_hashes.spec_view. spec_view is idempotent (spec_view(view)==view). Not stale: `bash scripts/lean_verify.sh Solution.lean` exits 0 (real exit code captured); Solution_prepatch.lean exits 1 with `unsolved goals` on `invariant_2: acc = listSum (coeffs.drop i)`, the magnitude-vs-signed goal — so the elided impl really is where the gold/prepatch delta lives, and same_spec holds across it.

ELISION. impl region collapses to `-- implementation elided — supplied by the consumer`; the prove_correct body collapses to `-- proof elided`, header retained. The entire discriminating impl delta (magnitude fold vs `acc:= x + acc`) is inside the elided impl and absent from the consumer view.

MECHANICAL SCREEN, LIVE NOT VACUOUS. leakage.screen(Solution.lean, VelvetBackend, patch, problem_statement, test_patch): passed=True, hard_failures=[], warnings=[]. I re-ran each rule by hand on the view rather than trusting the aggregate: narration regex hits = [], lean diff markers present = [], gold-patch changed lines reproduced (normalized, len>=8) = [], patched file paths/module paths in view = []. Patch changed symbols = ['spectral_helper'] — absent from the view's 91 identifiers and from its comment text. POSITIVE CONTROL: injecting `/- Fixes mlab._spectral_helper: replace np.abs(window).sum() with window.sum(). -/` into the pure region flips passed to False with "L3: narration 'Fixes'", so the screen fires on this bundle.

CONTENT SWEEP BEYOND THE MECHANICAL RULES. Grepped the view for np.abs / numpy / mlab / _spectral_helper / spectral / matplotlib / flattop / scipy / psd / scale_by_freq / conj / angle / NFFT / noverlap / Fs / detrend / dtype: zero hits. The only 'abs' occurrence is the English 'absolute terms' (L52); 'window' occurs only inside the model name `windowSum`; 'sum' only inside listSum/magSum/windowSum.

DISCRIMINATOR IS PUBLIC. The view names the signed-vs-magnitude distinction (`listSum` signed total, `magSum` = Σ|xᵢ|, 'a negative coefficient REDUCES the total and is not folded in by its magnitude'). That is fully derivable from problem_statement ALONE, which states "The `np.abs` is not needed, and give wrong result for window with negative value, such as `flattop`" and ships the repro `np.abs(window).sum()**2-window.sum()**2`. Checked term-by-term against the public statement: 'sign', 'negative', 'abs', 'window', 'sum' all appear in problem_statement; 'signed'/'magnitude'/'total' are ordinary paraphrases of the public np.abs-vs-plain contrast, not new information. I screened against problem_statement only and did NOT use hints_text (which additionally names PR #22828) — echoing hints would be leakage, and nothing in the view echoes it.

NO REVIEWER-DIRECTED TEXT. leakage.reviewer_directed() = [] on every bundle file (Solution.lean, Solution_prepatch.lean, mapping.md, refinement.md, meta.json, verdict.md, axiom_check.py, conformance_check.py, properties.py). No file instructs me how to record or which verdict is honest. Note for the record: meta.json/verdict.md carry a PRIOR run's G-PANEL-3 entry with agent_verdict 'NO-LEAKAGE' and its full note. That is an archived record, not an instruction addressed to me, so I do not score it as bundle-steers-reviewer — but I did not inherit it: every hash and gate result above is my own measurement, and I note the archived verdict.md entry cites a stale 5860-byte view sha 76efcfc0..., i.e. an earlier pure region, whereas the current view is 7562 bytes / cab155b6.... The prior note's own grep excluded verdict.md; I grepped verdict.md too and found only its own self-description.

RECORDED, NOT FINDINGS (out of this gate). (1) meta.json modeled_functions[0].repo_location = 'lib/matplotlib/mlab.py:291 (changed exprs at 398,403,427,430)', and modeled_functions IS shipped in MODES_WITH_SPEC (read src/swebench_unified/eval/dataset.py: WITHHELD_FIELDS blocks patch/test_patch/F2P/P2P, but modeled_functions and spec_view ship). Lines 398/403 sit outside the public L423-L430 deep link, so that parenthetical is strictly more localizing than problem_statement. Not spec-view leakage — localization is a deliberate benchmark channel and it discloses WHERE, not the WHAT, which is public anyway — but a curator may want to trim the line list. (2) The view carries dangling internal refs the consumer never receives ('mapping.md §2', 'plan §5.4', 'directive 5'); hygiene noise, no disclosure. (3) G-EQ, G-PANEL, G-PANEL-1 are recorded FAIL in meta (inconclusive attacks). Those are other gates' business and no leakage disposition leans on them; the gates my verdict actually rests on — G-LEAK (pass), G-HYGIENE spec_view hash, G-VERIFY/G-DIFF — I re-ran or re-hashed myself.

VERDICT: the spec view reveals nothing about the gold edit beyond what the public problem_statement already states.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
