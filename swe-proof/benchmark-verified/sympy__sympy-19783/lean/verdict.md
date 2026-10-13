# P2 adversarial audit — sympy__sympy-19783

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong impl could close its correctness proof, so no counterexample to verify⇏correct exists. Both specs are TOTAL, output-pinning functions over the finite Operand domain (4 values). problem_spec_conjugateProduct fixes result = Result.lhs on identity else Result.product; problem_spec_identityProduct fixes result = Result.rhs when isOperatorKind||isConjugateKind else Result.product. Any impl differing on ANY of the 4 operands makes correct_* a decidably-FALSE proposition. Every attack's `decide`-closed proof attempt was rejected by Lean with 'Tactic decide proved that the proposition ... is false' — machine-confirmed non-closure.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -97,10 +97,13 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 1 (conjugateProduct, control-flow-effect: branches swapped).
+-- Returns the unevaluated product when other is the identity, and the left
+-- factor otherwise — the exact inverse of the pinned dispatch.
 def implementation_conjugateProduct (other : Operand) : Result := Id.run do
   if isIdentityKind other then
-    return Result.lhs
-  return Result.product
+    return Result.product
+  return Result.lhs
 -- impl-end
 
 -- proof-start
@@ -108,9 +111,9 @@
     ∀ (other : Operand),
       problem_spec_conjugateProduct other (implementation_conjugateProduct other) := by
   intro other
-  unfold problem_spec_conjugateProduct implementation_conjugateProduct
-  simp only [Id.run]
-  by_cases h : isIdentityKind other <;> simp [h] <;> rfl
+  cases other <;>
+    simp_all [problem_spec_conjugateProduct, implementation_conjugateProduct,
+      isIdentityKind, isOperatorKind, isConjugateKind, Id.run] <;> decide
 -- proof-end
 
 -- post-conditions-start
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -97,9 +97,9 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_conjugateProduct (other : Operand) : Result := Id.run do
-  if isIdentityKind other then
-    return Result.lhs
+-- ATTACK 2 (conjugateProduct, prepatch bug #1: method absent -> always Mul).
+-- Every conjugate product is left unevaluated, so identity is never absorbed.
+def implementation_conjugateProduct (_other : Operand) : Result := Id.run do
   return Result.product
 -- impl-end
 
@@ -108,9 +108,9 @@
     ∀ (other : Operand),
       problem_spec_conjugateProduct other (implementation_conjugateProduct other) := by
   intro other
-  unfold problem_spec_conjugateProduct implementation_conjugateProduct
-  simp only [Id.run]
-  by_cases h : isIdentityKind other <;> simp [h] <;> rfl
+  cases other <;>
+    simp_all [problem_spec_conjugateProduct, implementation_conjugateProduct,
+      isIdentityKind, isOperatorKind, isConjugateKind, Id.run] <;> decide
 -- proof-end
 
 -- post-conditions-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -97,9 +97,12 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 3 (conjugateProduct, ungrounded-oracle echo: return rhs on identity).
+-- Absorbs on identity but returns the WRONG factor (rhs, the right operand)
+-- instead of lhs (self). Correct on the 3 product cases, wrong on identity.
 def implementation_conjugateProduct (other : Operand) : Result := Id.run do
   if isIdentityKind other then
-    return Result.lhs
+    return Result.rhs
   return Result.product
 -- impl-end
 
@@ -108,9 +111,9 @@
     ∀ (other : Operand),
       problem_spec_conjugateProduct other (implementation_conjugateProduct other) := by
   intro other
-  unfold problem_spec_conjugateProduct implementation_conjugateProduct
-  simp only [Id.run]
-  by_cases h : isIdentityKind other <;> simp [h] <;> rfl
+  cases other <;>
+    simp_all [problem_spec_conjugateProduct, implementation_conjugateProduct,
+      isIdentityKind, isOperatorKind, isConjugateKind, Id.run] <;> decide
 -- proof-end
 
 -- post-conditions-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -124,8 +124,11 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 4 (identityProduct, prepatch bug #2: tuple is (Operator,) only).
+-- A conjugated operator is NOT recognized as operator-like, so I*Dagger(O)
+-- is left as the unevaluated product instead of collapsing to Dagger(O).
 def implementation_identityProduct (other : Operand) : Result := Id.run do
-  if isOperatorKind other || isConjugateKind other then
+  if isOperatorKind other then
     return Result.rhs
   return Result.product
 -- impl-end
@@ -135,7 +138,7 @@
     ∀ (other : Operand),
       problem_spec_identityProduct other (implementation_identityProduct other) := by
   intro other
-  unfold problem_spec_identityProduct implementation_identityProduct
-  simp only [Id.run]
-  by_cases h : isOperatorKind other || isConjugateKind other <;> simp [h] <;> rfl
+  cases other <;>
+    simp_all [problem_spec_identityProduct, implementation_identityProduct,
+      isIdentityKind, isOperatorKind, isConjugateKind, Id.run] <;> decide
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -124,8 +124,11 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 5 (identityProduct, partial-domain: only conjugate absorbed).
+-- Handles the newly-added Dagger case but drops the pre-existing Operator/
+-- identity absorption, so I*O and I*I are wrongly left unevaluated.
 def implementation_identityProduct (other : Operand) : Result := Id.run do
-  if isOperatorKind other || isConjugateKind other then
+  if isConjugateKind other then
     return Result.rhs
   return Result.product
 -- impl-end
@@ -135,7 +138,7 @@
     ∀ (other : Operand),
       problem_spec_identityProduct other (implementation_identityProduct other) := by
   intro other
-  unfold problem_spec_identityProduct implementation_identityProduct
-  simp only [Id.run]
-  by_cases h : isOperatorKind other || isConjugateKind other <;> simp [h] <;> rfl
+  cases other <;>
+    simp_all [problem_spec_identityProduct, implementation_identityProduct,
+      isIdentityKind, isOperatorKind, isConjugateKind, Id.run] <;> decide
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -124,10 +124,11 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_identityProduct (other : Operand) : Result := Id.run do
-  if isOperatorKind other || isConjugateKind other then
-    return Result.rhs
-  return Result.product
+-- ATTACK 6 (identityProduct, boundary/over-absorption: absorb everything).
+-- Collapses EVERY product to the right factor, including the non-operator
+-- `other` case which the spec pins to the unevaluated product.
+def implementation_identityProduct (_other : Operand) : Result := Id.run do
+  return Result.rhs
 -- impl-end
 
 -- proof-start
@@ -135,7 +136,7 @@
     ∀ (other : Operand),
       problem_spec_identityProduct other (implementation_identityProduct other) := by
   intro other
-  unfold problem_spec_identityProduct implementation_identityProduct
-  simp only [Id.run]
-  by_cases h : isOperatorKind other || isConjugateKind other <;> simp [h] <;> rfl
+  cases other <;>
+    simp_all [problem_spec_identityProduct, implementation_identityProduct,
+      isIdentityKind, isOperatorKind, isConjugateKind, Id.run] <;> decide
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -124,9 +124,12 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 7 (identityProduct, control-flow-effect: wrong returned factor).
+-- Correct dispatch condition, but returns the LEFT factor (lhs=self, the
+-- identity) instead of the right factor (rhs) on the absorbing branch.
 def implementation_identityProduct (other : Operand) : Result := Id.run do
   if isOperatorKind other || isConjugateKind other then
-    return Result.rhs
+    return Result.lhs
   return Result.product
 -- impl-end
 
@@ -135,7 +138,7 @@
     ∀ (other : Operand),
       problem_spec_identityProduct other (implementation_identityProduct other) := by
   intro other
-  unfold problem_spec_identityProduct implementation_identityProduct
-  simp only [Id.run]
-  by_cases h : isOperatorKind other || isConjugateKind other <;> simp [h] <;> rfl
+  cases other <;>
+    simp_all [problem_spec_identityProduct, implementation_identityProduct,
+      isIdentityKind, isOperatorKind, isConjugateKind, Id.run] <;> decide
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Multiplication in an operator algebra and its absorption by the identity element.

The algebra has a distinguished *identity element* `I` that acts as a two-sided
multiplicative identity: for any operator-like factor `x`, both `I * x` and
`x * I` are supposed to collapse to `x` rather than being left as an unevaluated
product. Besides plain operators and the identity element, the algebra contains
the *conjugate* of an operator (its Hermitian conjugate) and ordinary scalar/other
expressions.

Two products are modeled, each deciding its result purely from the KIND of the
right-hand factor:

* **A conjugated operator times another factor.** When the right factor is the
  identity element, the product collapses to the conjugated operator itself (the
  identity is absorbed). For every other right factor the product is left as the
  unevaluated product of the two factors.

* **The identity element times another factor.** When the right factor is any
  operator-like thing — a plain operator, the identity element itself, or a
  conjugated operator — the product collapses to that right factor. Only when the
  right factor is a non-operator (a scalar or other expression) is the product
  left unevaluated.

The operator-like classification used by the second product is broader than that
used by the first: the identity element and plain operators are operators, and a
conjugated operator is also operator-like for the purpose of identity absorption,
whereas only the bare identity element triggers absorption on the left of the
first product.
-/

-- axioms-start
-- No unchanged outside callee is consumed. The dispatch — classifying the
-- right-hand factor and choosing between returning a factor unchanged and forming
-- the unevaluated product — IS the modeled behavior and is spelled out
-- structurally over the finite operand/result carriers below. The unevaluated
-- product is an opaque result shape (`Result.product`); its internal construction
-- is irrelevant to the pinned behavior, so no `opaque`/`axiom` callee contract is
-- required.
-- axioms-end

-- pure-start
/-- The kind of a right-hand factor, as far as the products care:

* `identity`  — the distinguished identity element;
* `operator`  — a plain operator (not the identity element);
* `conjugate` — the conjugate of an operator;
* `other`     — any other expression that is neither an operator nor a conjugate
                (a scalar/number/generic product). -/
inductive Operand where
  | identity
  | operator
  | conjugate
  | other
deriving DecidableEq, Repr

/-- The shape of a product result:

* `lhs`     — the left factor returned unchanged;
* `rhs`     — the right factor returned unchanged;
* `product` — the unevaluated product of the two factors. -/
inductive Result where
  | lhs
  | rhs
  | product
deriving DecidableEq, Repr

/-- Whether a factor is the identity element. -/
def isIdentityKind : Operand → Bool
  | .identity => true
  | _ => false

/-- Whether a factor is an operator (the identity element is itself an operator,
plain operators are operators; a conjugate or any other expression is not). -/
def isOperatorKind : Operand → Bool
  | .identity => true
  | .operator => true
  | .conjugate => false
  | .other => false

/-- Whether a factor is a conjugated operator. -/
def isConjugateKind : Operand → Bool
  | .conjugate => true
  | _ => false
-- pure-end

-- post-conditions-start
/-- A conjugated operator multiplied by a right factor `other`: when `other` is the
identity element the result is the conjugated operator itself (the left factor);
otherwise the result is the unevaluated product. -/
def problem_spec_conjugateProduct (other : Operand) (result : Result) : Prop :=
  if isIdentityKind other then result = Result.lhs
  else result = Result.product
-- post-conditions-end

-- impl-start
def implementation_conjugateProduct (other : Operand) : Result := Id.run do
  if isIdentityKind other then
    return Result.lhs
  return Result.product
-- impl-end

-- proof-start
theorem correct_conjugateProduct :
    ∀ (other : Operand),
      problem_spec_conjugateProduct other (implementation_conjugateProduct other) := by
  intro other
  unfold problem_spec_conjugateProduct implementation_conjugateProduct
  simp only [Id.run]
  by_cases h : isIdentityKind other <;> simp [h] <;> rfl
-- proof-end

-- post-conditions-start
/-- The identity element multiplied by a right factor `other`: when `other` is
operator-like — an operator (including the identity element) or a conjugated
operator — the result is that right factor; otherwise the result is the
unevaluated product. -/
def problem_spec_identityProduct (other : Operand) (result : Result) : Prop :=
  if isOperatorKind other || isConjugateKind other then result = Result.rhs
  else result = Result.product
-- post-conditions-end

-- impl-start
def implementation_identityProduct (other : Operand) : Result := Id.run do
  if isOperatorKind other || isConjugateKind other then
    return Result.rhs
  return Result.product
-- impl-end

-- proof-start
theorem correct_identityProduct :
    ∀ (other : Operand),
      problem_spec_identityProduct other (implementation_identityProduct other) := by
  intro other
  unfold problem_spec_identityProduct implementation_identityProduct
  simp only [Id.run]
  by_cases h : isOperatorKind other || isConjugateKind other <;> simp [h] <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL COMPLETE. same_spec(Solution.lean, atk_N.lean, lean) == True for all N=1..7 (verified with python; axioms/pure/pre/post regions left byte-identical, only impl+proof regions edited).

COMMANDS: verify = `bash scripts/lean_verify.sh <file>` (run 4 concurrently in background per parallelism directive). Each attack proof used the strongest honest closer: `cases other <;> simp_all [specs, isIdentityKind, isOperatorKind, isConjugateKind, Id.run] <;> decide` — `decide` is the complete decision procedure over this finite domain, so it closes IFF the impl truly matches the spec.

### RESULTS (exit codes):
- pos_control (gold Solution.lean) : exit 0 (VERIFIES). #print axioms correct_conjugateProduct = [propext, Quot.sound]; correct_identityProduct = [propext, Quot.sound]. CLEAN — no sorryAx.
- atk_1 conjugateProduct control-flow-effect (branches swapped: product on identity, lhs otherwise): exit 1. 'decide proved ... is false'.
- atk_2 conjugateProduct PREPATCH BUG #1 (method absent -> always Result.product; identity never absorbed): exit 1. Reproduces the reported defect (Dagger(O)*Dagger(I) not simplified). 'decide ... false'.
- atk_3 conjugateProduct ungrounded-oracle echo (absorbs on identity but returns rhs=wrong factor instead of lhs=self): exit 1. 'decide ... false'.
- atk_4 identityProduct PREPATCH BUG #2 (tuple (Operator,) only -> conjugate not absorbed; I*Dagger(O) unevaluated): exit 1. Reproduces the F2P test_identity defect. 'decide ... false'.
- atk_5 identityProduct partial-domain (only conjugate absorbed; drops Operator/identity absorption): exit 1. 'decide ... false'.
- atk_6 identityProduct boundary/over-absorption (return rhs unconditionally; wrong on `other` case): exit 1. 'decide ... false'.
- atk_7 identityProduct control-flow-effect (correct condition, returns lhs=self instead of rhs on absorbing branch): exit 1. 'decide ... false'.

7 distinct wrong impls across BOTH twin routines (partial-domain, boundary/over-absorption, control-flow-effect x2, ungrounded-oracle echo, plus both prepatch bugs). NONE closed with clean axioms => zero faithful patches to run through resolve => no run_resolve needed (protocol step 2 vacuous: no verifying wrong impl exists).

REFINEMENT.MD AUDIT: All 6 legs tagged R (type refinement). Axioms region is EMPTY; no unchanged callee is consumed as an axiom or referenced as a deep model. Therefore there are NO A-consumed / A-reference legs and NO kind-3 legs to fault — the A-leg correspondence audit is vacuously satisfied. The R/I legs are mechanically covered by G-CONF (conformance_check.py: oracle = faithful post-patch replica honoring IdentityOperator<Operator and Dagger not-<Operator subclass facts; shadow = op-for-op transliteration of impl regions; exhaustive over 4-value domain + 200k fuzz seed 19783). The Result.product opaqueness (abstracting Mul(self,other)) is sound: the pinned behavior is only WHICH result shape is produced, never the product's internal construction. mapping.md subclass analysis (IdentityOperator IS-A Operator; Dagger NOT-A Operator) is correct and is exactly what makes the widened (Operator, Dagger) tuple absorb identity/operator/conjugate but not `other`.

WHY SOUND: both problem_spec predicates pin the output exactly for every element of the finite Operand carrier, so the spec is behaviorally equivalent to gold-impl equality — verify (correct_* closes with clean axioms) provably implies correct. No verify⇏correct gap. prepatch_reproduced=true (atk_2 and atk_4 encode the two real prepatch defects and both fail to verify, matching Solution_prepatch_{1,2}.lean).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong impl could close its correctness proof, so no counterexample to verify⇏correct exists. Both specs are TOTAL, output-pinning functions over the finite Operand domain (4 values). problem_spec_conjugateProduct fixes result = Result.lhs on identity else Result.product; problem_spec_identityProduct fixes result = Result.rhs when isOperatorKind||isConjugateKind else Result.product. Any impl differing on ANY of the 4 operands makes correct_* a decidably-FALSE proposition. Every attack's `decide`-closed proof attempt was rejected by Lean with 'Tactic decide proved that the proposition ... is false' — machine-confirmed non-closure.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Multiplication in an operator algebra and its absorption by the identity element.

The algebra has a distinguished *identity element* `I` that acts as a two-sided
multiplicative identity: for any operator-like factor `x`, both `I * x` and
`x * I` are supposed to collapse to `x` rather than being left as an unevaluated
product. Besides plain operators and the identity element, the algebra contains
the *conjugate* of an operator (its Hermitian conjugate) and ordinary scalar/other
expressions.

Two products are modeled, each deciding its result purely from the KIND of the
right-hand factor:

* **A conjugated operator times another factor.** When the right factor is the
  identity element, the product collapses to the conjugated operator itself (the
  identity is absorbed). For every other right factor the product is left as the
  unevaluated product of the two factors.

* **The identity element times another factor.** When the right factor is any
  operator-like thing — a plain operator, the identity element itself, or a
  conjugated operator — the product collapses to that right factor. Only when the
  right factor is a non-operator (a scalar or other expression) is the product
  left unevaluated.

The operator-like classification used by the second product is broader than that
used by the first: the identity element and plain operators are operators, and a
conjugated operator is also operator-like for the purpose of identity absorption,
whereas only the bare identity element triggers absorption on the left of the
first product.
-/

-- axioms-start
-- No unchanged outside callee is consumed. The dispatch — classifying the
-- right-hand factor and choosing between returning a factor unchanged and forming
-- the unevaluated product — IS the modeled behavior and is spelled out
-- structurally over the finite operand/result carriers below. The unevaluated
-- product is an opaque result shape (`Result.product`); its internal construction
-- is irrelevant to the pinned behavior, so no `opaque`/`axiom` callee contract is
-- required.
-- axioms-end

-- pure-start
/-- The kind of a right-hand factor, as far as the products care:

* `identity`  — the distinguished identity element;
* `operator`  — a plain operator (not the identity element);
* `conjugate` — the conjugate of an operator;
* `other`     — any other expression that is neither an operator nor a conjugate
                (a scalar/number/generic product). -/
inductive Operand where
  | identity
  | operator
  | conjugate
  | other
deriving DecidableEq, Repr

/-- The shape of a product result:

* `lhs`     — the left factor returned unchanged;
* `rhs`     — the right factor returned unchanged;
* `product` — the unevaluated product of the two factors. -/
inductive Result where
  | lhs
  | rhs
  | product
deriving DecidableEq, Repr

/-- Whether a factor is the identity element. -/
def isIdentityKind : Operand → Bool
  | .identity => true
  | _ => false

/-- Whether a factor is an operator (the identity element is itself an operator,
plain operators are operators; a conjugate or any other expression is not). -/
def isOperatorKind : Operand → Bool
  | .identity => true
  | .operator => true
  | .conjugate => false
  | .other => false

/-- Whether a factor is a conjugated operator. -/
def isConjugateKind : Operand → Bool
  | .conjugate => true
  | _ => false
-- pure-end

-- post-conditions-start
/-- A conjugated operator multiplied by a right factor `other`: when `other` is the
identity element the result is the conjugated operator itself (the left factor);
otherwise the result is the unevaluated product. -/
def problem_spec_conjugateProduct (other : Operand) (result : Result) : Prop :=
  if isIdentityKind other then result = Result.lhs
  else result = Result.product
-- post-conditions-end

-- impl-start
def implementation_conjugateProduct (other : Operand) : Result := Id.run do
  if isIdentityKind other then
    return Result.lhs
  return Result.product
-- impl-end

-- proof-start
theorem correct_conjugateProduct :
    ∀ (other : Operand),
      problem_spec_conjugateProduct other (implementation_conjugateProduct other) := by
  intro other
  unfold problem_spec_conjugateProduct implementation_conjugateProduct
  simp only [Id.run]
  by_cases h : isIdentityKind other <;> simp [h] <;> rfl
-- proof-end

-- post-conditions-start
/-- The identity element multiplied by a right factor `other`: when `other` is
operator-like — an operator (including the identity element) or a conjugated
operator — the result is that right factor; otherwise the result is the
unevaluated product. -/
def problem_spec_identityProduct (other : Operand) (result : Result) : Prop :=
  if isOperatorKind other || isConjugateKind other then result = Result.rhs
  else result = Result.product
-- post-conditions-end

-- impl-start
def implementation_identityProduct (other : Operand) : Result := Id.run do
  if isOperatorKind other || isConjugateKind other then
    return Result.rhs
  return Result.product
-- impl-end

-- proof-start
theorem correct_identityProduct :
    ∀ (other : Operand),
      problem_spec_identityProduct other (implementation_identityProduct other) := by
  intro other
  unfold problem_spec_identityProduct implementation_identityProduct
  simp only [Id.run]
  by_cases h : isOperatorKind other || isConjugateKind other <;> simp [h] <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL COMPLETE. same_spec(Solution.lean, atk_N.lean, lean) == True for all N=1..7 (verified with python; axioms/pure/pre/post regions left byte-identical, only impl+proof regions edited).

COMMANDS: verify = `bash scripts/lean_verify.sh <file>` (run 4 concurrently in background per parallelism directive). Each attack proof used the strongest honest closer: `cases other <;> simp_all [specs, isIdentityKind, isOperatorKind, isConjugateKind, Id.run] <;> decide` — `decide` is the complete decision procedure over this finite domain, so it closes IFF the impl truly matches the spec.

### RESULTS (exit codes):
- pos_control (gold Solution.lean) : exit 0 (VERIFIES). #print axioms correct_conjugateProduct = [propext, Quot.sound]; correct_identityProduct = [propext, Quot.sound]. CLEAN — no sorryAx.
- atk_1 conjugateProduct control-flow-effect (branches swapped: product on identity, lhs otherwise): exit 1. 'decide proved ... is false'.
- atk_2 conjugateProduct PREPATCH BUG #1 (method absent -> always Result.product; identity never absorbed): exit 1. Reproduces the reported defect (Dagger(O)*Dagger(I) not simplified). 'decide ... false'.
- atk_3 conjugateProduct ungrounded-oracle echo (absorbs on identity but returns rhs=wrong factor instead of lhs=self): exit 1. 'decide ... false'.
- atk_4 identityProduct PREPATCH BUG #2 (tuple (Operator,) only -> conjugate not absorbed; I*Dagger(O) unevaluated): exit 1. Reproduces the F2P test_identity defect. 'decide ... false'.
- atk_5 identityProduct partial-domain (only conjugate absorbed; drops Operator/identity absorption): exit 1. 'decide ... false'.
- atk_6 identityProduct boundary/over-absorption (return rhs unconditionally; wrong on `other` case): exit 1. 'decide ... false'.
- atk_7 identityProduct control-flow-effect (correct condition, returns lhs=self instead of rhs on absorbing branch): exit 1. 'decide ... false'.

7 distinct wrong impls across BOTH twin routines (partial-domain, boundary/over-absorption, control-flow-effect x2, ungrounded-oracle echo, plus both prepatch bugs). NONE closed with clean axioms => zero faithful patches to run through resolve => no run_resolve needed (protocol step 2 vacuous: no verifying wrong impl exists).

REFINEMENT.MD AUDIT: All 6 legs tagged R (type refinement). Axioms region is EMPTY; no unchanged callee is consumed as an axiom or referenced as a deep model. Therefore there are NO A-consumed / A-reference legs and NO kind-3 legs to fault — the A-leg correspondence audit is vacuously satisfied. The R/I legs are mechanically covered by G-CONF (conformance_check.py: oracle = faithful post-patch replica honoring IdentityOperator<Operator and Dagger not-<Operator subclass facts; shadow = op-for-op transliteration of impl regions; exhaustive over 4-value domain + 200k fuzz seed 19783). The Result.product opaqueness (abstracting Mul(self,other)) is sound: the pinned behavior is only WHICH result shape is produced, never the product's internal construction. mapping.md subclass analysis (IdentityOperator IS-A Operator; Dagger NOT-A Operator) is correct and is exactly what makes the widened (Operator, Dagger) tuple absorb identity/operator/conjugate but not `other`.

WHY SOUND: both problem_spec predicates pin the output exactly for every element of the finite Operand carrier, so the spec is behaviorally equivalent to gold-impl equality — verify (correct_* closes with clean axioms) provably implies correct. No verify⇏correct gap. prepatch_reproduced=true (atk_2 and atk_4 encode the two real prepatch defects and both fail to verify, matching Solution_prepatch_{1,2}.lean).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on sympy__sympy-19783/lean. Spec regions byte-identical (same_spec True for both prepatch files vs gold). Gold verifies exit 0; #print axioms on both correct_* = [propext, Quot.sound] only, no sorryAx.

Exhaustively re-checked the abstraction against the REAL patched callee in a base_commit worktree with patch.diff applied, over all 4 operand classes {identity=IdentityOperator(), operator=Operator('O'), conjugate=Dagger, other=Symbol}:

Dagger.__mul__ (implementation_conjugateProduct): identity->lhs (return self, ='Dagger(O)'), operator->product, conjugate->product, other->product. Spec: if isIdentityKind then lhs else product. MATCH on all 4.

IdentityOperator.__mul__ (implementation_identityProduct): identity->rhs (return other; verified I.__mul__(I) is the right I), operator->rhs, conjugate->rhs (Dagger returned unchanged), other->product (x*I is Mul). Spec: if isOperatorKind||isConjugateKind then rhs else product. Spec table isOperatorKind(identity)=true, isOperatorKind(operator)=true, isConjugateKind(conjugate)=true, all else false -> rhs for {identity,operator,conjugate}, product for other. MATCH on all 4.

Subclass facts driving the dispatch confirmed in real source: class IdentityOperator(Operator) (operator.py:249) so isinstance(other,(Operator,Dagger)) is True for the identity operand; class Dagger(adjoint), adjoint<Expr so Dagger not-a Operator (the widening isConjugateKind disjunct the patch adds). F2P edge cases verified live: Dagger(O)*Dagger(I)==Dagger(O) (Dagger(I) reduces to an IdentityOperator instance -> identity operand -> lhs), I*Dagger(O)==Dagger(O), Dagger(O)*I==Dagger(O), isinstance(I*I,IdentityOperator), isinstance(3*I,Mul).

The abstraction of Mul(self,other) to the opaque Result.product shape is legitimate: the only behavior pinned is WHICH of the 3 result shapes (lhs/rhs/product) is produced as a function of operand class, and that matches the real callee on every input. No diverging input exists on the modeled finite/total domain. Spec neither too strong nor drifted from real repo behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes clean (no diff markers, no patched file/module path, no patched repo symbol echoed in spec-view identifiers or comments, no bug/fix narration). Verified: leakage.screen over the projected spec view returns passed=True, hard_failures=[]. same_spec holds byte-identically between Solution.lean and both prepatch variants (True/True); impl+proof regions are elided in the consumer view.

Semantic review beyond problem_statement: the public problem_statement already names Dagger, IdentityOperator, Operator and states the two observable behaviors (A*Identity==A works; Dagger(A)*Identity fails to simplify). The spec view deliberately uses an ABSTRACT model vocabulary (identity element / operator / conjugate / other; Operand/Result carriers; 'collapse to x' / 'left unevaluated') and never mentions any repo symbol, file path, __mul__, Mul, or the isinstance-tuple widening. The gold edit's localization (which file, which method added, which tuple widened from (Operator,) to (Operator, Dagger)) is not recoverable from the spec. The spec does pin the I*conjugate->conjugate post-condition (from F2P test_identity, not literally in the public statement), but that is legitimate behavioral specification of the correct outcome, not disclosure of the edit — a faithful spec must state the target behavior. No line reveals the gold patch beyond what a correct specification is licensed to assert.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
