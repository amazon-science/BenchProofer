# P2 adversarial audit — astropy__astropy-14369

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No same-spec wrong impl verifies. The frozen spec `problem_spec_divChain head rest result := result = head / rest.prod` is a TOTAL FUNCTIONAL EQUALITY: it pins the result exactly for every (head, rest) over an arbitrary CommGroup G. Any impl proving `correct_divChain` is therefore provably extensionally equal to the gold function `head / rest.prod`; a behaviorally-wrong impl yields a provably-false theorem, so its proof cannot close (no admissible slack). No counterexample impl found.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -39,29 +39,15 @@
 
 -- impl-start
 def implementation_divChain {G : Type*} [CommGroup G]
-    (head : G) (rest : List G) : G := Id.run do
-  let mut acc := head
-  for u in rest do
-    acc := acc / u
-  return acc
+    (head : G) (rest : List G) : G :=
+  head / rest.foldr (fun u acc => u / acc) 1
 -- impl-end
 
 -- proof-start
 theorem correct_divChain {G : Type*} [CommGroup G] :
     ∀ (head : G) (rest : List G),
       problem_spec_divChain head rest (implementation_divChain head rest) := by
-  have helper : ∀ (rest : List G) (acc : G),
-      Id.run (forIn rest acc (fun u r => (pure (.yield (r / u)) : Id (ForInStep G)))) = acc / rest.prod := by
-    intro rest
-    induction rest with
-    | nil => intro acc; simp [Id.run, pure]
-    | cons a as ih =>
-      intro acc
-      rw [List.forIn_cons]
-      simp only [Id.run, bind] at ih ⊢
-      rw [ih]
-      simp [div_div]
   intro head rest
   unfold problem_spec_divChain implementation_divChain
-  exact helper rest head
+  simp [div_eq_mul_inv, mul_comm, mul_assoc, mul_left_comm]
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -42,7 +42,7 @@
     (head : G) (rest : List G) : G := Id.run do
   let mut acc := head
   for u in rest do
-    acc := acc / u
+    acc := acc * u
   return acc
 -- impl-end
 
@@ -50,18 +50,7 @@
 theorem correct_divChain {G : Type*} [CommGroup G] :
     ∀ (head : G) (rest : List G),
       problem_spec_divChain head rest (implementation_divChain head rest) := by
-  have helper : ∀ (rest : List G) (acc : G),
-      Id.run (forIn rest acc (fun u r => (pure (.yield (r / u)) : Id (ForInStep G)))) = acc / rest.prod := by
-    intro rest
-    induction rest with
-    | nil => intro acc; simp [Id.run, pure]
-    | cons a as ih =>
-      intro acc
-      rw [List.forIn_cons]
-      simp only [Id.run, bind] at ih ⊢
-      rw [ih]
-      simp [div_div]
   intro head rest
   unfold problem_spec_divChain implementation_divChain
-  exact helper rest head
+  simp [div_eq_mul_inv, mul_comm, mul_assoc, mul_left_comm]
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -39,29 +39,14 @@
 
 -- impl-start
 def implementation_divChain {G : Type*} [CommGroup G]
-    (head : G) (rest : List G) : G := Id.run do
-  let mut acc := head
-  for u in rest do
-    acc := acc / u
-  return acc
+    (head : G) (rest : List G) : G := head
 -- impl-end
 
 -- proof-start
 theorem correct_divChain {G : Type*} [CommGroup G] :
     ∀ (head : G) (rest : List G),
       problem_spec_divChain head rest (implementation_divChain head rest) := by
-  have helper : ∀ (rest : List G) (acc : G),
-      Id.run (forIn rest acc (fun u r => (pure (.yield (r / u)) : Id (ForInStep G)))) = acc / rest.prod := by
-    intro rest
-    induction rest with
-    | nil => intro acc; simp [Id.run, pure]
-    | cons a as ih =>
-      intro acc
-      rw [List.forIn_cons]
-      simp only [Id.run, bind] at ih ⊢
-      rw [ih]
-      simp [div_div]
   intro head rest
   unfold problem_spec_divChain implementation_divChain
-  exact helper rest head
+  simp [div_eq_mul_inv, mul_comm, mul_assoc, mul_left_comm]
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -39,29 +39,14 @@
 
 -- impl-start
 def implementation_divChain {G : Type*} [CommGroup G]
-    (head : G) (rest : List G) : G := Id.run do
-  let mut acc := head
-  for u in rest do
-    acc := acc / u
-  return acc
+    (head : G) (rest : List G) : G := head / rest.tail.prod
 -- impl-end
 
 -- proof-start
 theorem correct_divChain {G : Type*} [CommGroup G] :
     ∀ (head : G) (rest : List G),
       problem_spec_divChain head rest (implementation_divChain head rest) := by
-  have helper : ∀ (rest : List G) (acc : G),
-      Id.run (forIn rest acc (fun u r => (pure (.yield (r / u)) : Id (ForInStep G)))) = acc / rest.prod := by
-    intro rest
-    induction rest with
-    | nil => intro acc; simp [Id.run, pure]
-    | cons a as ih =>
-      intro acc
-      rw [List.forIn_cons]
-      simp only [Id.run, bind] at ih ⊢
-      rw [ih]
-      simp [div_div]
   intro head rest
   unfold problem_spec_divChain implementation_divChain
-  exact helper rest head
+  simp [div_eq_mul_inv, mul_comm, mul_assoc, mul_left_comm]
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -42,7 +42,7 @@
     (head : G) (rest : List G) : G := Id.run do
   let mut acc := head
   for u in rest do
-    acc := acc / u
+    acc := head / u
   return acc
 -- impl-end
 
@@ -50,18 +50,7 @@
 theorem correct_divChain {G : Type*} [CommGroup G] :
     ∀ (head : G) (rest : List G),
       problem_spec_divChain head rest (implementation_divChain head rest) := by
-  have helper : ∀ (rest : List G) (acc : G),
-      Id.run (forIn rest acc (fun u r => (pure (.yield (r / u)) : Id (ForInStep G)))) = acc / rest.prod := by
-    intro rest
-    induction rest with
-    | nil => intro acc; simp [Id.run, pure]
-    | cons a as ih =>
-      intro acc
-      rw [List.forIn_cons]
-      simp only [Id.run, bind] at ih ⊢
-      rw [ih]
-      simp [div_div]
   intro head rest
   unfold problem_spec_divChain implementation_divChain
-  exact helper rest head
+  simp [div_eq_mul_inv, mul_comm, mul_assoc, mul_left_comm]
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -39,29 +39,14 @@
 
 -- impl-start
 def implementation_divChain {G : Type*} [CommGroup G]
-    (head : G) (rest : List G) : G := Id.run do
-  let mut acc := head
-  for u in rest do
-    acc := acc / u
-  return acc
+    (head : G) (rest : List G) : G := head⁻¹ / rest.prod
 -- impl-end
 
 -- proof-start
 theorem correct_divChain {G : Type*} [CommGroup G] :
     ∀ (head : G) (rest : List G),
       problem_spec_divChain head rest (implementation_divChain head rest) := by
-  have helper : ∀ (rest : List G) (acc : G),
-      Id.run (forIn rest acc (fun u r => (pure (.yield (r / u)) : Id (ForInStep G)))) = acc / rest.prod := by
-    intro rest
-    induction rest with
-    | nil => intro acc; simp [Id.run, pure]
-    | cons a as ih =>
-      intro acc
-      rw [List.forIn_cons]
-      simp only [Id.run, bind] at ih ⊢
-      rw [ih]
-      simp [div_div]
   intro head rest
   unfold problem_spec_divChain implementation_divChain
-  exact helper rest head
+  simp [div_eq_mul_inv, mul_comm, mul_assoc, mul_left_comm]
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an `opaque` signature here. The only operation the
-- modeled routine performs is combining unit terms under multiplication and the
-- quotient operator. Those terms live in an algebra that is a commutative group
-- under multiplication (each term is invertible; multiplication is associative
-- and commutative; the quotient `a / b` is `a * b⁻¹`). We model that algebra
-- DEEPLY as an arbitrary `CommGroup`, so the term-combining operators are the
-- group's own `*`, `⁻¹`, `/`. That `CommGroup` structure is validated as an
-- A-reference against the real unit algebra by G-AX (associativity/commutativity
-- of `*`, the `a / b = a * b⁻¹` law, equality by combined exponents). No custom
-- `axiom` is consumed; the proof uses Mathlib's `CommGroup` laws. The proof
-- agent may add `_prop` axioms only if genuinely stuck.
-- axioms-end

-- pure-start
-- (No extra functional helpers: the spec is a direct relation built from the
-- group's product over the trailing terms.)
-- pure-end

-- post-conditions-start
/-- Combining a sequence of unit terms under the quotient operator.

The terms form a left-associated chain: starting from the leading term `head`,
each subsequent term in `rest` (in order) divides the running result. Read as a
single closed form, the result is therefore the leading term divided by the
product of all the following terms:

  `head / (rest₀ * rest₁ * … * restₙ)`.

Frame discipline: the result is pinned entirely to the inputs — it is fully
determined by `head` and the ordered list `rest`, with no other freedom. -/
def problem_spec_divChain {G : Type*} [CommGroup G]
    (head : G) (rest : List G) (result : G) : Prop :=
  result = head / rest.prod
-- post-conditions-end

-- impl-start
def implementation_divChain {G : Type*} [CommGroup G]
    (head : G) (rest : List G) : G := Id.run do
  let mut acc := head
  for u in rest do
    acc := acc / u
  return acc
-- impl-end

-- proof-start
theorem correct_divChain {G : Type*} [CommGroup G] :
    ∀ (head : G) (rest : List G),
      problem_spec_divChain head rest (implementation_divChain head rest) := by
  have helper : ∀ (rest : List G) (acc : G),
      Id.run (forIn rest acc (fun u r => (pure (.yield (r / u)) : Id (ForInStep G)))) = acc / rest.prod := by
    intro rest
    induction rest with
    | nil => intro acc; simp [Id.run, pure]
    | cons a as ih =>
      intro acc
      rw [List.forIn_cons]
      simp only [Id.run, bind] at ih ⊢
      rw [ih]
      simp [div_div]
  intro head rest
  unfold problem_spec_divChain implementation_divChain
  exact helper rest head
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL & RESULTS (all; same_spec=True verified for all 8 files via swebench_unified.markers.same_spec on lean backend).

Command template: `bash scripts/lean_verify.sh <file>`. Runs launched concurrently in ≤4-job background batches.

Positive controls (must verify):
- pos_control.lean (byte-identical gold impl: for-loop acc/u): exit 0. `#print axioms correct_divChain` -> [propext, Quot.sound] (clean, no sorryAx/custom axiom). File pos_control_ax.lean, exit 0.
- atk_echo.lean (correct alternative form `head * rest.prod⁻¹`): exit 0. axioms [propext] (clean). File atk_echo_ax.lean, exit 0. This is a same-spec VERIFYING candidate; being behaviorally correct it needs no resolve-run to break the spec (an echo that resolves is not a weakness per G-EQ policy).

6 DISTINCT same-spec WRONG impls, each with best-effort closing proof — ALL FAIL to verify:
- atk_1 (PREPATCH BUG, right-assoc `head / foldr (u/acc)`): exit 1, unsolved goals @49:77. Prepatch bug reproduced (does not satisfy frozen post-patch spec).
- atk_2 (control-flow-effect, `acc := acc * u` multiply not divide): exit 1, unsolved goals @52:77.
- atk_3 (partial-domain, returns `head`; correct only when rest.prod=1): exit 1, unsolved goals @48:77.
- atk_4 (boundary/off-by-one, `head / rest.tail.prod` drops first trailing term): exit 1, unsolved goals @48:77.
- atk_5 (control-flow-effect, `acc := head / u` overwrites each iter): exit 1, unsolved goals @52:77.
- atk_6 (ungrounded, `head⁻¹ / rest.prod` wrong head sign): exit 1, unsolved goals @48:77.

No wrong impl closed with clean axioms, so there is NO verifying-wrong-impl requiring a faithful-patch resolve run (patches={} accordingly). The resolve-run mandate applies only to same-spec wrong impls whose proof closes; none did.

REFINEMENT.md AUDIT: 4 legs. Row1 R (input type refinement, parsed unit ↔ CommGroup element). Row2 I (acc init). Row3 A-reference (THE FIX: left-assoc `/` chain; unit *,/,⁻¹ modeled as CommGroup ops, validated by axiom_check.py/G-AX). Row4 I (return). NO kind-3 (changed-inexpressible) legs — the associativity fix is modeled exactly as `head / rest.prod`. A-reference correspondence is SOUND: axiom_check.py reconstructs the real callee (free abelian group on base units as exponent-vectors; core.CompositeUnit __mul__/__truediv__/__pow__) and asserts EXACTLY the CommGroup laws the proof uses (assoc, comm, identity, inverse, quotient law a/b=a*b⁻¹, left-assoc a/(b*c)=(a/b)/c) over 350k checks, seed 14369. axioms region is empty (no A-consumed). Correspondence holds. mapping.md type bijection is consistent (leading combined_units↔head, ordered trailing unit_expression terms↔rest, reduced value↔head/rest.prod).

VERDICT: SOUND. Spec is a tight total functional equality with no admissible wrongness; ≥6 distinct wrong impls (incl. prepatch bug) all rejected by lean_verify; both correct forms verify with clean axioms; refinement A-reference legs are faithful.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No same-spec wrong impl verifies. The frozen spec `problem_spec_divChain head rest result := result = head / rest.prod` is a TOTAL FUNCTIONAL EQUALITY: it pins the result exactly for every (head, rest) over an arbitrary CommGroup G. Any impl proving `correct_divChain` is therefore provably extensionally equal to the gold function `head / rest.prod`; a behaviorally-wrong impl yields a provably-false theorem, so its proof cannot close (no admissible slack). No counterexample impl found.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an `opaque` signature here. The only operation the
-- modeled routine performs is combining unit terms under multiplication and the
-- quotient operator. Those terms live in an algebra that is a commutative group
-- under multiplication (each term is invertible; multiplication is associative
-- and commutative; the quotient `a / b` is `a * b⁻¹`). We model that algebra
-- DEEPLY as an arbitrary `CommGroup`, so the term-combining operators are the
-- group's own `*`, `⁻¹`, `/`. That `CommGroup` structure is validated as an
-- A-reference against the real unit algebra by G-AX (associativity/commutativity
-- of `*`, the `a / b = a * b⁻¹` law, equality by combined exponents). No custom
-- `axiom` is consumed; the proof uses Mathlib's `CommGroup` laws. The proof
-- agent may add `_prop` axioms only if genuinely stuck.
-- axioms-end

-- pure-start
-- (No extra functional helpers: the spec is a direct relation built from the
-- group's product over the trailing terms.)
-- pure-end

-- post-conditions-start
/-- Combining a sequence of unit terms under the quotient operator.

The terms form a left-associated chain: starting from the leading term `head`,
each subsequent term in `rest` (in order) divides the running result. Read as a
single closed form, the result is therefore the leading term divided by the
product of all the following terms:

  `head / (rest₀ * rest₁ * … * restₙ)`.

Frame discipline: the result is pinned entirely to the inputs — it is fully
determined by `head` and the ordered list `rest`, with no other freedom. -/
def problem_spec_divChain {G : Type*} [CommGroup G]
    (head : G) (rest : List G) (result : G) : Prop :=
  result = head / rest.prod
-- post-conditions-end

-- impl-start
def implementation_divChain {G : Type*} [CommGroup G]
    (head : G) (rest : List G) : G := Id.run do
  let mut acc := head
  for u in rest do
    acc := acc / u
  return acc
-- impl-end

-- proof-start
theorem correct_divChain {G : Type*} [CommGroup G] :
    ∀ (head : G) (rest : List G),
      problem_spec_divChain head rest (implementation_divChain head rest) := by
  have helper : ∀ (rest : List G) (acc : G),
      Id.run (forIn rest acc (fun u r => (pure (.yield (r / u)) : Id (ForInStep G)))) = acc / rest.prod := by
    intro rest
    induction rest with
    | nil => intro acc; simp [Id.run, pure]
    | cons a as ih =>
      intro acc
      rw [List.forIn_cons]
      simp only [Id.run, bind] at ih ⊢
      rw [ih]
      simp [div_div]
  intro head rest
  unfold problem_spec_divChain implementation_divChain
  exact helper rest head
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL & RESULTS (all; same_spec=True verified for all 8 files via swebench_unified.markers.same_spec on lean backend).

Command template: `bash scripts/lean_verify.sh <file>`. Runs launched concurrently in ≤4-job background batches.

Positive controls (must verify):
- pos_control.lean (byte-identical gold impl: for-loop acc/u): exit 0. `#print axioms correct_divChain` -> [propext, Quot.sound] (clean, no sorryAx/custom axiom). File pos_control_ax.lean, exit 0.
- atk_echo.lean (correct alternative form `head * rest.prod⁻¹`): exit 0. axioms [propext] (clean). File atk_echo_ax.lean, exit 0. This is a same-spec VERIFYING candidate; being behaviorally correct it needs no resolve-run to break the spec (an echo that resolves is not a weakness per G-EQ policy).

6 DISTINCT same-spec WRONG impls, each with best-effort closing proof — ALL FAIL to verify:
- atk_1 (PREPATCH BUG, right-assoc `head / foldr (u/acc)`): exit 1, unsolved goals @49:77. Prepatch bug reproduced (does not satisfy frozen post-patch spec).
- atk_2 (control-flow-effect, `acc := acc * u` multiply not divide): exit 1, unsolved goals @52:77.
- atk_3 (partial-domain, returns `head`; correct only when rest.prod=1): exit 1, unsolved goals @48:77.
- atk_4 (boundary/off-by-one, `head / rest.tail.prod` drops first trailing term): exit 1, unsolved goals @48:77.
- atk_5 (control-flow-effect, `acc := head / u` overwrites each iter): exit 1, unsolved goals @52:77.
- atk_6 (ungrounded, `head⁻¹ / rest.prod` wrong head sign): exit 1, unsolved goals @48:77.

No wrong impl closed with clean axioms, so there is NO verifying-wrong-impl requiring a faithful-patch resolve run (patches={} accordingly). The resolve-run mandate applies only to same-spec wrong impls whose proof closes; none did.

REFINEMENT.md AUDIT: 4 legs. Row1 R (input type refinement, parsed unit ↔ CommGroup element). Row2 I (acc init). Row3 A-reference (THE FIX: left-assoc `/` chain; unit *,/,⁻¹ modeled as CommGroup ops, validated by axiom_check.py/G-AX). Row4 I (return). NO kind-3 (changed-inexpressible) legs — the associativity fix is modeled exactly as `head / rest.prod`. A-reference correspondence is SOUND: axiom_check.py reconstructs the real callee (free abelian group on base units as exponent-vectors; core.CompositeUnit __mul__/__truediv__/__pow__) and asserts EXACTLY the CommGroup laws the proof uses (assoc, comm, identity, inverse, quotient law a/b=a*b⁻¹, left-assoc a/(b*c)=(a/b)/c) over 350k checks, seed 14369. axioms region is empty (no A-consumed). Correspondence holds. mapping.md type bijection is consistent (leading combined_units↔head, ordered trailing unit_expression terms↔rest, reduced value↔head/rest.prod).

VERDICT: SOUND. Spec is a tight total functional equality with no admissible wrongness; ≥6 distinct wrong impls (incl. prepatch bug) all rejected by lean_verify; both correct forms verify with clean axioms; refinement A-reference legs are faithful.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec: problem_spec_divChain head rest result := result = head / rest.prod, over an arbitrary CommGroup G, modeling the CDS unit-parser division-chain reduction that the patch changes (right-recursive `unit_expression DIVISION combined_units` -> left-recursive `combined_units DIVISION unit_expression`).

FAITHFULNESS CHECK vs real callee:
- Real post-patch behavior confirmed against installed astropy 8.0.1, whose cds.py already carries the post-patch left-recursive `division_of_units : combined_units DIVISION unit_expression` production. Manual cases: 'm/s/kg'->m/(kg s), 'J/m/s/kpc2'->J/(m s kpc2), 'km/s/kg/A'->km/(A kg s), '/m/s'->1/(m s), 'km/(s/kg)'->kg km/s, all == head / prod(trailing terms).
- Fuzzed 4000 random division chains (length 0-5, head+rest) with seed 14369: 4000 checked, 0 divergence from head / rest.prod (compared via decompose ratio == dimensionless scale 1).
- Fuzzed 2000 leading-division chains ('/a/b/...', head=dimensionless 1): 2000 checked, 0 divergence. This covers the len(p)==3 `p[2]**-1` case as head=1 / rest.prod.
- Model deliberately abstracts orthogonal, patch-unchanged machinery (lexing, numeric factor, products, powers, parens). Parenthesized sub-chains reduce to a single G element before entering the chain (verified: 'km/(s.kg)'->km/(kg s), '(km/s)/kg'->km/(kg s)), consistent with a term of rest/head. This abstraction does not make the spec too strong: on the changed surface (flat division chains) the spec agrees exactly with the real callee. Mixed forms like 'm/s.kg' are grammar syntax errors post-patch (not modeled inputs).

### Spec integrity
- same_spec(Solution, Solution_prepatch, LeanBackend.language) = True (spec region byte-identical; only impl/proof differ).
- Solution.lean compiles under lean_verify.sh (exit 0, no sorry/error).
- #print axioms correct_divChain => [propext, Quot.sound] only: NO sorryAx, no bespoke _prop axioms. Proof is genuine (forIn accumulator induction via List.forIn_cons + div_div).
- G-DIFF holds: prepatch impl (right-nesting) cannot close against the frozen spec for chains length>=2, matching the real bug (sign-flip of trailing terms).

The modeled function agrees with the real repo callee on every tested input across the patch's affected surface. No divergence found; spec is neither too strong nor drifting.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen (leakage.screen, lean flavor) PASSES with zero hard failures. same_spec(post, prepatch)=True; spec view compiles conceptually and post-conditions region is byte-identical across variants.

Spec view (post-conditions): `problem_spec_divChain ... result = head / rest.prod` modeled over an arbitrary CommGroup. It contains NONE of the gold-edit specifics: no `astropy/units/format/cds.py` path, no grammar-production identifiers (`p_division_of_units`, `combined_units`, `unit_expression`, `_make_parser`), no YACC/grammar/recursion/parser terminology, no diff markers, and no reproduced gold-patch lines. The gold edit flips the `division_of_units` production from right-recursive `unit_expression DIVISION combined_units` to left-recursive `combined_units DIVISION unit_expression` — none of that syntactic detail surfaces in the spec.

The spec necessarily encodes the CORRECT behavior (left-association => head divided by product of trailing terms). That behavior is ALREADY public in problem_statement, which supplies the concrete expected result: `10+3J/m/s/kpc2` must parse as J/(m·s·kpc2), not the jumbled `J·s/(kpc2·m)`, and states the order of division is wrong and output should match input. The spec-view comment phrase 'left-associated chain' / `head / (rest0 * rest1 * ...)` merely restates that publicly-derivable correct semantics; it does not reveal the grammar-recursion-side flip that IS the gold edit. Encoding correct behavior derivable from the public expected-output example is not leakage.

No narration words (bug/fix/wrong/incorrectly) appear in spec-view comments; rationale comments are abstract (CommGroup/G-AX modeling). Judged against problem_statement only, not hints_text.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
