# P2 adversarial audit — sympy__sympy-24562

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_echoA.lean`, `atk_echoB.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -34,20 +34,11 @@
 -- impl-start
 def implementation_denominatorProduct
     (pDen : Nat) (qdigits : List Nat) : Nat := Id.run do
-  -- a FRESH integer accumulator for the combined denominator, started at 1 so
-  -- that every contribution is combined numerically
-  let mut denAcc : Nat := 1
-  -- fold in the whole-number factor contributed by the first operand
-  denAcc := denAcc * pDen
-  -- the second operand is supplied as a decimal digit string: read it into the
-  -- integer it denotes
+  -- BUG: ignores pDen entirely; only reads the decimal value
   let mut c : Nat := 0
   for d in qdigits do
     c := c * 10 + d
-  -- fold the operand's integer value into the same accumulator — including a
-  -- zero value, which zeroes the combined result
-  denAcc := denAcc * c
-  return denAcc
+  return c
 -- impl-end
 
 -- proof-start
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -34,20 +34,13 @@
 -- impl-start
 def implementation_denominatorProduct
     (pDen : Nat) (qdigits : List Nat) : Nat := Id.run do
-  -- a FRESH integer accumulator for the combined denominator, started at 1 so
-  -- that every contribution is combined numerically
-  let mut denAcc : Nat := 1
-  -- fold in the whole-number factor contributed by the first operand
-  denAcc := denAcc * pDen
-  -- the second operand is supplied as a decimal digit string: read it into the
-  -- integer it denotes
+  -- BUG: when operand is empty, returns the factor alone (should be 0)
+  if qdigits.isEmpty then
+    return pDen
   let mut c : Nat := 0
   for d in qdigits do
     c := c * 10 + d
-  -- fold the operand's integer value into the same accumulator — including a
-  -- zero value, which zeroes the combined result
-  denAcc := denAcc * c
-  return denAcc
+  return pDen * c
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -34,20 +34,12 @@
 -- impl-start
 def implementation_denominatorProduct
     (pDen : Nat) (qdigits : List Nat) : Nat := Id.run do
-  -- a FRESH integer accumulator for the combined denominator, started at 1 so
-  -- that every contribution is combined numerically
-  let mut denAcc : Nat := 1
-  -- fold in the whole-number factor contributed by the first operand
-  denAcc := denAcc * pDen
-  -- the second operand is supplied as a decimal digit string: read it into the
-  -- integer it denotes
+  -- BUG: filters out zero digits before folding, changing the value
   let mut c : Nat := 0
   for d in qdigits do
-    c := c * 10 + d
-  -- fold the operand's integer value into the same accumulator — including a
-  -- zero value, which zeroes the combined result
-  denAcc := denAcc * c
-  return denAcc
+    if d != 0 then
+      c := c * 10 + d
+  return pDen * c
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -34,20 +34,14 @@
 -- impl-start
 def implementation_denominatorProduct
     (pDen : Nat) (qdigits : List Nat) : Nat := Id.run do
-  -- a FRESH integer accumulator for the combined denominator, started at 1 so
-  -- that every contribution is combined numerically
-  let mut denAcc : Nat := 1
-  -- fold in the whole-number factor contributed by the first operand
-  denAcc := denAcc * pDen
-  -- the second operand is supplied as a decimal digit string: read it into the
-  -- integer it denotes
+  -- BUG (prepatch): repeat the digit string pDen times before reading it
+  let mut digits : List Nat := []
+  for _ in [0:pDen] do
+    digits := digits ++ qdigits
   let mut c : Nat := 0
-  for d in qdigits do
+  for d in digits do
     c := c * 10 + d
-  -- fold the operand's integer value into the same accumulator — including a
-  -- zero value, which zeroes the combined result
-  denAcc := denAcc * c
-  return denAcc
+  return c
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -34,20 +34,11 @@
 -- impl-start
 def implementation_denominatorProduct
     (pDen : Nat) (qdigits : List Nat) : Nat := Id.run do
-  -- a FRESH integer accumulator for the combined denominator, started at 1 so
-  -- that every contribution is combined numerically
-  let mut denAcc : Nat := 1
-  -- fold in the whole-number factor contributed by the first operand
-  denAcc := denAcc * pDen
-  -- the second operand is supplied as a decimal digit string: read it into the
-  -- integer it denotes
+  -- BUG: adds the factor instead of multiplying
   let mut c : Nat := 0
   for d in qdigits do
     c := c * 10 + d
-  -- fold the operand's integer value into the same accumulator — including a
-  -- zero value, which zeroes the combined result
-  denAcc := denAcc * c
-  return denAcc
+  return pDen + c
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -34,20 +34,11 @@
 -- impl-start
 def implementation_denominatorProduct
     (pDen : Nat) (qdigits : List Nat) : Nat := Id.run do
-  -- a FRESH integer accumulator for the combined denominator, started at 1 so
-  -- that every contribution is combined numerically
-  let mut denAcc : Nat := 1
-  -- fold in the whole-number factor contributed by the first operand
-  denAcc := denAcc * pDen
-  -- the second operand is supplied as a decimal digit string: read it into the
-  -- integer it denotes
+  -- BUG: folds reversed digit list -> wrong decimal value
   let mut c : Nat := 0
-  for d in qdigits do
+  for d in qdigits.reverse do
     c := c * 10 + d
-  -- fold the operand's integer value into the same accumulator — including a
-  -- zero value, which zeroes the combined result
-  denAcc := denAcc * c
-  return denAcc
+  return pDen * c
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -34,20 +34,11 @@
 -- impl-start
 def implementation_denominatorProduct
     (pDen : Nat) (qdigits : List Nat) : Nat := Id.run do
-  -- a FRESH integer accumulator for the combined denominator, started at 1 so
-  -- that every contribution is combined numerically
-  let mut denAcc : Nat := 1
-  -- fold in the whole-number factor contributed by the first operand
-  denAcc := denAcc * pDen
-  -- the second operand is supplied as a decimal digit string: read it into the
-  -- integer it denotes
   let mut c : Nat := 0
   for d in qdigits do
     c := c * 10 + d
-  -- fold the operand's integer value into the same accumulator — including a
-  -- zero value, which zeroes the combined result
-  denAcc := denAcc * c
-  return denAcc
+  -- BUG: off-by-one, adds 1 to the product
+  return pDen * c + 1
 -- impl-end
 
 -- proof-start
```

Attack 8 — `atk_echoA.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -34,25 +34,16 @@
 -- impl-start
 def implementation_denominatorProduct
     (pDen : Nat) (qdigits : List Nat) : Nat := Id.run do
-  -- a FRESH integer accumulator for the combined denominator, started at 1 so
-  -- that every contribution is combined numerically
-  let mut denAcc : Nat := 1
-  -- fold in the whole-number factor contributed by the first operand
-  denAcc := denAcc * pDen
-  -- the second operand is supplied as a decimal digit string: read it into the
-  -- integer it denotes
+  -- alternative but equivalent: read the operand first, then multiply by factor
   let mut c : Nat := 0
   for d in qdigits do
     c := c * 10 + d
-  -- fold the operand's integer value into the same accumulator — including a
-  -- zero value, which zeroes the combined result
-  denAcc := denAcc * c
+  let mut denAcc : Nat := c
+  denAcc := denAcc * pDen
   return denAcc
 -- impl-end
 
 -- proof-start
-/-- The desugared `forIn` loop accumulating decimal digits equals the left fold,
-generalized over the starting accumulator (Route B helper). -/
 theorem forIn_decval (qdigits : List Nat) (init : Nat) :
     Id.run (forIn qdigits init (fun d r => do
         pure PUnit.unit
@@ -78,5 +69,5 @@
         pure (ForInStep.yield (r * 10 + d)))) =
       qdigits.foldl (fun acc d => acc * 10 + d) 0 := forIn_decval qdigits 0
   simp only [Id.run, bind, pure] at hb ⊢
-  rw [hb, Nat.one_mul]
+  rw [hb, Nat.mul_comm]
 -- proof-end
```

Attack 9 — `atk_echoB.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -34,25 +34,15 @@
 -- impl-start
 def implementation_denominatorProduct
     (pDen : Nat) (qdigits : List Nat) : Nat := Id.run do
-  -- a FRESH integer accumulator for the combined denominator, started at 1 so
-  -- that every contribution is combined numerically
-  let mut denAcc : Nat := 1
-  -- fold in the whole-number factor contributed by the first operand
-  denAcc := denAcc * pDen
-  -- the second operand is supplied as a decimal digit string: read it into the
-  -- integer it denotes
+  let mut denAcc : Nat := pDen
   let mut c : Nat := 0
   for d in qdigits do
     c := c * 10 + d
-  -- fold the operand's integer value into the same accumulator — including a
-  -- zero value, which zeroes the combined result
   denAcc := denAcc * c
   return denAcc
 -- impl-end
 
 -- proof-start
-/-- The desugared `forIn` loop accumulating decimal digits equals the left fold,
-generalized over the starting accumulator (Route B helper). -/
 theorem forIn_decval (qdigits : List Nat) (init : Nat) :
     Id.run (forIn qdigits init (fun d r => do
         pure PUnit.unit
@@ -78,5 +68,5 @@
         pure (ForInStep.yield (r * 10 + d)))) =
       qdigits.foldl (fun acc d => acc * 10 + d) 0 := forIn_decval qdigits 0
   simp only [Id.run, bind, pure] at hb ⊢
-  rw [hb, Nat.one_mul]
+  rw [hb]
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The two operations this
-- behavior relies on — interpreting a decimal digit string as an integer, and
-- combining that integer with a whole-number factor — are modeled DEEPLY below
-- (a left-fold over the digit list and exact natural-number arithmetic), rather
-- than axiomatized, so their reference behavior is validated as A-references by
-- G-AX. The proof agent may add `_prop` axioms only if stuck.
-- axioms-end

-- pure-start
/-- Value of a decimal digit string, most-significant digit first:
`decval [d₀, d₁, …, dₖ] = ((…(d₀)·10 + d₁)…)·10 + dₖ`. Left-folding the digits
this way is exactly how a decimal numeral is read into an integer. -/
def decval (ds : List Nat) : Nat :=
  ds.foldl (fun acc d => acc * 10 + d) 0
-- pure-end

-- post-conditions-start
/-- Combine two pieces into a single denominator. The first piece, `pDen`, is a
positive whole-number factor already contributed by the first operand. The
second piece, `qdigits`, is a second operand supplied as a non-negative integer
written in positional decimal notation. The combined denominator is their
arithmetic product: the factor multiplied by the integer *value* of the decimal
operand — with no other dependence on how the operand was written, and with a
zero-valued operand zeroing the product. -/
def problem_spec_denominatorProduct
    (pDen : Nat) (qdigits : List Nat) (result : Nat) : Prop :=
  result = pDen * decval qdigits
-- post-conditions-end

-- impl-start
def implementation_denominatorProduct
    (pDen : Nat) (qdigits : List Nat) : Nat := Id.run do
  -- a FRESH integer accumulator for the combined denominator, started at 1 so
  -- that every contribution is combined numerically
  let mut denAcc : Nat := 1
  -- fold in the whole-number factor contributed by the first operand
  denAcc := denAcc * pDen
  -- the second operand is supplied as a decimal digit string: read it into the
  -- integer it denotes
  let mut c : Nat := 0
  for d in qdigits do
    c := c * 10 + d
  -- fold the operand's integer value into the same accumulator — including a
  -- zero value, which zeroes the combined result
  denAcc := denAcc * c
  return denAcc
-- impl-end

-- proof-start
/-- The desugared `forIn` loop accumulating decimal digits equals the left fold,
generalized over the starting accumulator (Route B helper). -/
theorem forIn_decval (qdigits : List Nat) (init : Nat) :
    Id.run (forIn qdigits init (fun d r => do
        pure PUnit.unit
        pure (ForInStep.yield (r * 10 + d)))) =
      qdigits.foldl (fun acc d => acc * 10 + d) init := by
  induction qdigits generalizing init with
  | nil => rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    rw [List.foldl_cons]
    exact ih (init * 10 + a)

theorem correct_denominatorProduct :
    ∀ (pDen : Nat) (qdigits : List Nat),
      1 ≤ pDen → (∀ d ∈ qdigits, d < 10) →
      problem_spec_denominatorProduct pDen qdigits
        (implementation_denominatorProduct pDen qdigits) := by
  intro pDen qdigits _ _
  unfold problem_spec_denominatorProduct implementation_denominatorProduct decval
  have hb : Id.run (forIn qdigits 0 (fun d r => do
        pure PUnit.unit
        pure (ForInStep.yield (r * 10 + d)))) =
      qdigits.foldl (fun acc d => acc * 10 + d) 0 := forIn_decval qdigits 0
  simp only [Id.run, bind, pure] at hb ⊢
  rw [hb, Nat.one_mul]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC: problem_spec_denominatorProduct pDen qdigits result := result = pDen * decval qdigits, over domain 1 ≤ pDen and (∀ d ∈ qdigits, d < 10). This is a TOTAL EXACT equation pinning the combined denominator to the product of the factor and the decimal value of the operand (zero included), leaving essentially no slack.

 All same_spec checks returned True (regions byte-identical except impl; echo proofs differ only in the proof region which same_spec ignores).

COMMANDS: verify = `bash scripts/lean_verify.sh <atk>.lean`; same_spec via swebench_unified.markers.same_spec on lean backend; axioms via appended `#print axioms correct_denominatorProduct`; resolve via swebench_unified.harness.run_resolve(iid, patchtext, timeout=1800, retries=1).

WRONG IMPLS — all 7 correctly REJECTED (verify exit=1, gold proof fails to close), so none needs a resolve run:
- atk_1 (partial-domain: ignores pDen, returns decval only) exit=1
- atk_2 (boundary: empty operand returns pDen instead of 0) exit=1
- atk_3 (control-flow-effect: skips zero digits in the fold) exit=1
- atk_4 (PREPATCH BUG reproduced: textual repetition of digit string pDen times before reading — the real base_commit bug, Rational('0.5','100')=1/100100) exit=1
- atk_5 (pDen + c instead of pDen * c) exit=1
- atk_6 (reverse digit order → wrong decimal value) exit=1
- atk_7 (off-by: pDen*c + 1) exit=1
prepatch_reproduced=true (atk_4).

### VERIFYING SAME-SPEC IMPLS (both closed, exit=0, clean axioms [propext, Quot.sound], no sorry/sorryAx, no _prop axioms):
- atk_echoA (read operand value first, then multiply by factor — mul_comm reorder). #print axioms clean. MATERIALIZED faithful patch patch_echoA.diff (Q accumulator, contributions folded in reversed multiply order, commutative). git apply --check: APPLIES CLEAN. run_resolve → resolved=True completed=True flaky=False.
- atk_echoB (accumulator initialized to pDen, then *= value — the gold shape). #print axioms clean. MATERIALIZED faithful patch patch_echoB.diff. git apply --check: APPLIES CLEAN. run_resolve → resolved=True completed=True flaky=False.

POSITIVE CONTROL: gold Solution.lean verifies exit=0 with clean axioms [propext, Quot.sound].

EVERY impl with a closing clean-axiom proof (echoA, echoB) has a materialized faithful patch that RESOLVES under the official harness → no verify⇏correct witness found.

REFINEMENT.MD AUDIT: 6 legs, all R / I / A-reference — NO kind-3 legs, NO A-consumed rows (axioms region empty, only comments). Leg 4 (per-digit fold ↔ Python int(q) decimal parse) is the sole A-reference; decval = foldl (acc*10+d) MSB-first is the standard positional decimal read and correctly corresponds to Python integer parsing of the divisor string. mapping.md type bijection (p.q↔Nat≥1, divisor string↔List Nat digits, int(q)↔decval, combined denominator↔pDen*decval) is coherent; List Nat carrier is justified (needed to distinguish string-repeat prepatch from value-multiply spec). A-leg correspondence holds.

NOTE ON THE ECHO ATTACKS: per the 2026-08-06 G-PANEL-1/G-EQ policy, a same-spec verifying 'echo' whose refined patch RESOLVES is NOT a weakness — it confirms the spec forces correctness. Both echoes resolved, so they do not break the spec.

CONCLUSION: SOUND. The spec's total exact product equation admits only impls computing exactly pDen*decval qdigits over the domain; every verifying variant transliterates to a resolving patch, and every deviating impl (partial-domain, boundary, zero-skip, prepatch repeat, add-vs-mul, digit-reverse, off-by-one) fails to verify. ≥5 distinct attacks run (7 wrong + 2 verifying); none breaks the spec.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_echoA.lean`, `atk_echoB.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_echoA.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_echoB.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The two operations this
-- behavior relies on — interpreting a decimal digit string as an integer, and
-- combining that integer with a whole-number factor — are modeled DEEPLY below
-- (a left-fold over the digit list and exact natural-number arithmetic), rather
-- than axiomatized, so their reference behavior is validated as A-references by
-- G-AX. The proof agent may add `_prop` axioms only if stuck.
-- axioms-end

-- pure-start
/-- Value of a decimal digit string, most-significant digit first:
`decval [d₀, d₁, …, dₖ] = ((…(d₀)·10 + d₁)…)·10 + dₖ`. Left-folding the digits
this way is exactly how a decimal numeral is read into an integer. -/
def decval (ds : List Nat) : Nat :=
  ds.foldl (fun acc d => acc * 10 + d) 0
-- pure-end

-- post-conditions-start
/-- Combine two pieces into a single denominator. The first piece, `pDen`, is a
positive whole-number factor already contributed by the first operand. The
second piece, `qdigits`, is a second operand supplied as a non-negative integer
written in positional decimal notation. The combined denominator is their
arithmetic product: the factor multiplied by the integer *value* of the decimal
operand — with no other dependence on how the operand was written, and with a
zero-valued operand zeroing the product. -/
def problem_spec_denominatorProduct
    (pDen : Nat) (qdigits : List Nat) (result : Nat) : Prop :=
  result = pDen * decval qdigits
-- post-conditions-end

-- impl-start
def implementation_denominatorProduct
    (pDen : Nat) (qdigits : List Nat) : Nat := Id.run do
  -- a FRESH integer accumulator for the combined denominator, started at 1 so
  -- that every contribution is combined numerically
  let mut denAcc : Nat := 1
  -- fold in the whole-number factor contributed by the first operand
  denAcc := denAcc * pDen
  -- the second operand is supplied as a decimal digit string: read it into the
  -- integer it denotes
  let mut c : Nat := 0
  for d in qdigits do
    c := c * 10 + d
  -- fold the operand's integer value into the same accumulator — including a
  -- zero value, which zeroes the combined result
  denAcc := denAcc * c
  return denAcc
-- impl-end

-- proof-start
/-- The desugared `forIn` loop accumulating decimal digits equals the left fold,
generalized over the starting accumulator (Route B helper). -/
theorem forIn_decval (qdigits : List Nat) (init : Nat) :
    Id.run (forIn qdigits init (fun d r => do
        pure PUnit.unit
        pure (ForInStep.yield (r * 10 + d)))) =
      qdigits.foldl (fun acc d => acc * 10 + d) init := by
  induction qdigits generalizing init with
  | nil => rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    rw [List.foldl_cons]
    exact ih (init * 10 + a)

theorem correct_denominatorProduct :
    ∀ (pDen : Nat) (qdigits : List Nat),
      1 ≤ pDen → (∀ d ∈ qdigits, d < 10) →
      problem_spec_denominatorProduct pDen qdigits
        (implementation_denominatorProduct pDen qdigits) := by
  intro pDen qdigits _ _
  unfold problem_spec_denominatorProduct implementation_denominatorProduct decval
  have hb : Id.run (forIn qdigits 0 (fun d r => do
        pure PUnit.unit
        pure (ForInStep.yield (r * 10 + d)))) =
      qdigits.foldl (fun acc d => acc * 10 + d) 0 := forIn_decval qdigits 0
  simp only [Id.run, bind, pure] at hb ⊢
  rw [hb, Nat.one_mul]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC: problem_spec_denominatorProduct pDen qdigits result := result = pDen * decval qdigits, over domain 1 ≤ pDen and (∀ d ∈ qdigits, d < 10). This is a TOTAL EXACT equation pinning the combined denominator to the product of the factor and the decimal value of the operand (zero included), leaving essentially no slack.

 All same_spec checks returned True (regions byte-identical except impl; echo proofs differ only in the proof region which same_spec ignores).

COMMANDS: verify = `bash scripts/lean_verify.sh <atk>.lean`; same_spec via swebench_unified.markers.same_spec on lean backend; axioms via appended `#print axioms correct_denominatorProduct`; resolve via swebench_unified.harness.run_resolve(iid, patchtext, timeout=1800, retries=1).

WRONG IMPLS — all 7 correctly REJECTED (verify exit=1, gold proof fails to close), so none needs a resolve run:
- atk_1 (partial-domain: ignores pDen, returns decval only) exit=1
- atk_2 (boundary: empty operand returns pDen instead of 0) exit=1
- atk_3 (control-flow-effect: skips zero digits in the fold) exit=1
- atk_4 (PREPATCH BUG reproduced: textual repetition of digit string pDen times before reading — the real base_commit bug, Rational('0.5','100')=1/100100) exit=1
- atk_5 (pDen + c instead of pDen * c) exit=1
- atk_6 (reverse digit order → wrong decimal value) exit=1
- atk_7 (off-by: pDen*c + 1) exit=1
prepatch_reproduced=true (atk_4).

### VERIFYING SAME-SPEC IMPLS (both closed, exit=0, clean axioms [propext, Quot.sound], no sorry/sorryAx, no _prop axioms):
- atk_echoA (read operand value first, then multiply by factor — mul_comm reorder). #print axioms clean. MATERIALIZED faithful patch patch_echoA.diff (Q accumulator, contributions folded in reversed multiply order, commutative). git apply --check: APPLIES CLEAN. run_resolve → resolved=True completed=True flaky=False.
- atk_echoB (accumulator initialized to pDen, then *= value — the gold shape). #print axioms clean. MATERIALIZED faithful patch patch_echoB.diff. git apply --check: APPLIES CLEAN. run_resolve → resolved=True completed=True flaky=False.

POSITIVE CONTROL: gold Solution.lean verifies exit=0 with clean axioms [propext, Quot.sound].

EVERY impl with a closing clean-axiom proof (echoA, echoB) has a materialized faithful patch that RESOLVES under the official harness → no verify⇏correct witness found.

REFINEMENT.MD AUDIT: 6 legs, all R / I / A-reference — NO kind-3 legs, NO A-consumed rows (axioms region empty, only comments). Leg 4 (per-digit fold ↔ Python int(q) decimal parse) is the sole A-reference; decval = foldl (acc*10+d) MSB-first is the standard positional decimal read and correctly corresponds to Python integer parsing of the divisor string. mapping.md type bijection (p.q↔Nat≥1, divisor string↔List Nat digits, int(q)↔decval, combined denominator↔pDen*decval) is coherent; List Nat carrier is justified (needed to distinguish string-repeat prepatch from value-multiply spec). A-leg correspondence holds.

NOTE ON THE ECHO ATTACKS: per the 2026-08-06 G-PANEL-1/G-EQ policy, a same-spec verifying 'echo' whose refined patch RESOLVES is NOT a weakness — it confirms the spec forces correctness. Both echoes resolved, so they do not break the spec.

CONCLUSION: SOUND. The spec's total exact product equation admits only impls computing exactly pDen*decval qdigits over the domain; every verifying variant transliterates to a resolving patch, and every deviating impl (partial-domain, boundary, zero-skip, prepatch repeat, add-vs-mul, digit-reverse, off-by-one) fails to verify. ≥5 distinct attacks run (7 wrong + 2 verifying); none breaks the spec.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) attack: no divergence found between the modeled function and the real repo callee on the modeled domain. Evidence: (1) same_spec(Solution.lean, Solution_prepatch.lean, lean-backend) = True — the spec view (axioms/pure/post-conditions) is byte-identical; frozen spec is `result = pDen * decval qdigits`. (2) Lean compiles via scripts/lean_verify.sh (exit 0); `#print axioms correct_denominatorProduct` = [propext, Quot.sound] only — no sorryAx, the proof is genuine. (3) G-AX (axiom_check.py) passes on 50008 probes: decval (left-fold acc*10+d, MSB-first) == Python int() parse of the digit string, incl. leading zeros/all-zero/empty. (4) G-CONF (conformance_check.py) passes on 120010 fuzzed inputs against the real patched-repo parse callee `Rational(qstr).p`, incl. zero-valued and leading-zero operands, factors 1..1000, digit-strings len 0..8. (5) Independent probe against the real repo: for qdigits in {[0],[0,0],[0,0,7],[9]x9,[1,0,0],[8,0,...],[]}, decval == Rational(qstr).p and q.q==1 in every case, matching the patched block's `Q *= q.p` (integer-string operand) contribution exactly. The modeled domain (integer-string divisor, 1<=pDen, digits<10) is precisely where the patched denominator block computes pDen*value, and the model computes exactly pDen*decval(qdigits). The spec pins the total product (zero included) rather than only nonzero quotients, which matches the fix's unconditional accumulation — not too strong. No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Solver-visible spec view (markers.spec_view / LeanBackend) exposes ONLY: (1) empty/abstract axioms region prose; (2) pure `decval` = decimal digit-string→integer left-fold; (3) postcondition `result = pDen * decval qdigits` with an abstract doc-comment ('factor × integer VALUE of the decimal operand, no dependence on how the operand was written, zero-valued operand zeroes the product'). impl and proof regions are fully elided ('supplied by the consumer').

Leakage judged vs public problem_statement ONLY (not hints_text). The problem_statement itself already states the correct behavior: Rational('0.5','100') must be 1/200 (multiply the operand's numeric value) rather than 1/100100 (string repetition). The spec view merely encodes that correct semantics abstractly.

No gold-edit specifics leak: no accumulator variable `Q`, no `q *= p.q` / `Q *= int(q)` diff lines, no `sympy/core/numbers.py` path, no `Rational`/`__new__` symbols, no diff markers, no bug/fix/patch narration. Nothing localizes the edit within the repo or reconstructs the patch mechanism (fresh integer accumulator). Modeling the correct product is inherent to any faithful spec and is already implied by problem_statement.

Cross-checks: mechanical leakage.screen(solution, lean, gold_patch, problem_statement) → PASSED, hard_failures=[] warnings=[]. markers.same_spec(Solution.lean, Solution_prepatch.lean)=True (spec region byte-identical across the prepatch variant). Recorded G-LEAK status=pass, relaxed_leakage=None. patch_equals_gold=True. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
