# P2 adversarial audit — sympy__sympy-13757

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_ctrl.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -64,7 +64,7 @@
 def implementation_polyMul (side : Side) (coercible : Bool) : MulResult := Id.run do
   -- Operator precedences advertised by the two operand kinds.
   let exprPriority : Rat := 10            -- a plain expression
-  let polyPriority : Rat := 10.001        -- a polynomial object
+  let polyPriority : Rat := 11            -- ATTACK V=11 (ties MatrixExpr/Boolean)
   match side with
   | Side.polyLeft =>
     -- The polynomial's own multiplication routine runs directly: it coerces the
@@ -97,6 +97,6 @@
   cases side
   · cases coercible <;> rfl
   · simp only [Id.run]
-    rw [if_pos (by norm_num : (10.001 : Rat) > 10)]
+    rw [if_pos (by norm_num : (11 : Rat) > 10)]
     cases coercible <;> rfl
 -- proof-end
```

Attack 2 — `atk_2.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -64,7 +64,7 @@
 def implementation_polyMul (side : Side) (coercible : Bool) : MulResult := Id.run do
   -- Operator precedences advertised by the two operand kinds.
   let exprPriority : Rat := 10            -- a plain expression
-  let polyPriority : Rat := 10.001        -- a polynomial object
+  let polyPriority : Rat := 100            -- ATTACK V=100 (dominates all types)
   match side with
   | Side.polyLeft =>
     -- The polynomial's own multiplication routine runs directly: it coerces the
@@ -97,6 +97,6 @@
   cases side
   · cases coercible <;> rfl
   · simp only [Id.run]
-    rw [if_pos (by norm_num : (10.001 : Rat) > 10)]
+    rw [if_pos (by norm_num : (100 : Rat) > 10)]
     cases coercible <;> rfl
 -- proof-end
```

Attack 3 — `atk_3.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -64,7 +64,7 @@
 def implementation_polyMul (side : Side) (coercible : Bool) : MulResult := Id.run do
   -- Operator precedences advertised by the two operand kinds.
   let exprPriority : Rat := 10            -- a plain expression
-  let polyPriority : Rat := 10.001        -- a polynomial object
+  let polyPriority : Rat := 10.01            -- ATTACK V=10.01 (matches DenseMatrix)
   match side with
   | Side.polyLeft =>
     -- The polynomial's own multiplication routine runs directly: it coerces the
@@ -97,6 +97,6 @@
   cases side
   · cases coercible <;> rfl
   · simp only [Id.run]
-    rw [if_pos (by norm_num : (10.001 : Rat) > 10)]
+    rw [if_pos (by norm_num : (10.01 : Rat) > 10)]
     cases coercible <;> rfl
 -- proof-end
```

Attack 4 — `atk_4.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -64,7 +64,7 @@
 def implementation_polyMul (side : Side) (coercible : Bool) : MulResult := Id.run do
   -- Operator precedences advertised by the two operand kinds.
   let exprPriority : Rat := 10            -- a plain expression
-  let polyPriority : Rat := 10.001        -- a polynomial object
+  let polyPriority : Rat := 12            -- ATTACK V=12 (exceeds tensor priority)
   match side with
   | Side.polyLeft =>
     -- The polynomial's own multiplication routine runs directly: it coerces the
@@ -97,6 +97,6 @@
   cases side
   · cases coercible <;> rfl
   · simp only [Id.run]
-    rw [if_pos (by norm_num : (10.001 : Rat) > 10)]
+    rw [if_pos (by norm_num : (12 : Rat) > 10)]
     cases coercible <;> rfl
 -- proof-end
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -67,13 +67,15 @@
   let polyPriority : Rat := 10.001        -- a polynomial object
   match side with
   | Side.polyLeft =>
-    -- The polynomial's own multiplication routine runs directly: it coerces the
-    -- expression into a polynomial when convertible and multiplies; otherwise
-    -- it falls back to the plain symbolic product of expressions.
-    if coercible then
-      return MulResult.evaluated
+    -- ATTACK (control-flow echo): route polyLeft through the SAME precedence
+    -- guard as polyRight (redundant here); outputs are identical to gold.
+    if polyPriority > exprPriority then
+      if coercible then
+        return MulResult.evaluated
+      else
+        return MulResult.symbolic
     else
-      return MulResult.symbolic
+      return (if coercible then MulResult.evaluated else MulResult.symbolic)
   | Side.polyRight =>
     -- The precedence dispatch hands the product to the operand advertising the
     -- strictly greater precedence; only then does the polynomial's reflected
@@ -95,7 +97,9 @@
   intro side coercible
   unfold problem_spec_polyMul implementation_polyMul
   cases side
-  · cases coercible <;> rfl
+  · simp only [Id.run]
+    rw [if_pos (by norm_num : (10.001 : Rat) > 10)]
+    cases coercible <;> rfl
   · simp only [Id.run]
     rw [if_pos (by norm_num : (10.001 : Rat) > 10)]
     cases coercible <;> rfl
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -64,7 +64,7 @@
 def implementation_polyMul (side : Side) (coercible : Bool) : MulResult := Id.run do
   -- Operator precedences advertised by the two operand kinds.
   let exprPriority : Rat := 10            -- a plain expression
-  let polyPriority : Rat := 10.001        -- a polynomial object
+  let polyPriority : Rat := 10.5            -- ATTACK V=10.5 (distinct mid value)
   match side with
   | Side.polyLeft =>
     -- The polynomial's own multiplication routine runs directly: it coerces the
@@ -97,6 +97,6 @@
   cases side
   · cases coercible <;> rfl
   · simp only [Id.run]
-    rw [if_pos (by norm_num : (10.001 : Rat) > 10)]
+    rw [if_pos (by norm_num : (10.5 : Rat) > 10)]
     cases coercible <;> rfl
 -- proof-end
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -64,7 +64,7 @@
 def implementation_polyMul (side : Side) (coercible : Bool) : MulResult := Id.run do
   -- Operator precedences advertised by the two operand kinds.
   let exprPriority : Rat := 10            -- a plain expression
-  let polyPriority : Rat := 10.001        -- a polynomial object
+  let polyPriority : Rat := 10.0001            -- ATTACK V=10.0001 (near-gold distinct)
   match side with
   | Side.polyLeft =>
     -- The polynomial's own multiplication routine runs directly: it coerces the
@@ -97,6 +97,6 @@
   cases side
   · cases coercible <;> rfl
   · simp only [Id.run]
-    rw [if_pos (by norm_num : (10.001 : Rat) > 10)]
+    rw [if_pos (by norm_num : (10.0001 : Rat) > 10)]
     cases coercible <;> rfl
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_ctrl.lean`

```lean
import Mathlib
-- imports-end

/-!
Multiplying a plain expression by a polynomial object.

A polynomial object and a plain (non-polynomial) expression can be multiplied in
either order. Whether the product is carried out depends on whether the plain
expression is CONVERTIBLE into a polynomial over the polynomial operand's
generators:

* convertible (e.g. a generator, a number): the product is ALWAYS carried out —
  a polynomial value is produced — regardless of which side the polynomial is
  on; it is never left as an unevaluated symbolic product.
* not convertible (e.g. it involves a generator non-polynomially): the product
  is expressed as a plain symbolic expression instead — no polynomial value is
  produced, for either operand order.

The outcome is modeled as `evaluated` (a polynomial value is produced) versus
`symbolic` (a plain, non-polynomial expression results). The contract below
pins the outcome for both operand orders, `poly * expr` and `expr * poly`, as a
function of convertibility.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The dispatch
-- decision (which operand performs the product, and hence whether the product is
-- carried out or left symbolic) is modeled DEEPLY over the operands' numeric
-- operator precedences, so no `opaque`/`axiom` callee contract is needed. The
-- polynomial's own multiplication routine (coerce the other factor when
-- convertible, else fall back to a plain symbolic product) is an UNCHANGED
-- callee whose net effect is folded into the `coercible` input and the
-- `MulResult` observable; it is validated against the real repo by G-AX.
-- axioms-end

-- pure-start
/-- Which factor of the product is the polynomial. `polyLeft` is `poly * expr`;
`polyRight` is `expr * poly`. -/
inductive Side where
  | polyLeft
  | polyRight
deriving DecidableEq, Repr

/-- The observable outcome of the product: `evaluated` means a polynomial value
is produced; `symbolic` means a plain, non-polynomial expression results. -/
inductive MulResult where
  | evaluated
  | symbolic
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- A product mixing a plain expression and a polynomial is always carried out
when the expression is convertible into a polynomial over the polynomial's
generators (`coercible = true`): the outcome is `evaluated` for either operand
order. When the expression is not convertible (`coercible = false`), the
product is expressed as a plain symbolic expression: the outcome is `symbolic`
for either operand order. -/
def problem_spec_polyMul (side : Side) (coercible : Bool) (result : MulResult) : Prop :=
  result = (if coercible then MulResult.evaluated else MulResult.symbolic)
-- post-conditions-end

-- impl-start
def implementation_polyMul (side : Side) (coercible : Bool) : MulResult := Id.run do
  -- Operator precedences advertised by the two operand kinds.
  let exprPriority : Rat := 10            -- a plain expression
  let polyPriority : Rat := 10.001        -- a polynomial object
  match side with
  | Side.polyLeft =>
    -- The polynomial's own multiplication routine runs directly: it coerces the
    -- expression into a polynomial when convertible and multiplies; otherwise
    -- it falls back to the plain symbolic product of expressions.
    if coercible then
      return MulResult.evaluated
    else
      return MulResult.symbolic
  | Side.polyRight =>
    -- The precedence dispatch hands the product to the operand advertising the
    -- strictly greater precedence; only then does the polynomial's reflected
    -- multiplication run (coerce when convertible, else fall back symbolic).
    if polyPriority > exprPriority then
      if coercible then
        return MulResult.evaluated
      else
        return MulResult.symbolic
    else
      -- No delegation: the unevaluated symbolic product is returned.
      return MulResult.symbolic
-- impl-end

-- proof-start
theorem correct_polyMul :
    ∀ (side : Side) (coercible : Bool),
      problem_spec_polyMul side coercible (implementation_polyMul side coercible) := by
  intro side coercible
  unfold problem_spec_polyMul implementation_polyMul
  cases side
  · cases coercible <;> rfl
  · simp only [Id.run]
    rw [if_pos (by norm_num : (10.001 : Rat) > 10)]
    cases coercible <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC STRUCTURE: problem_spec_polyMul(side, coercible, result) := result = (if coercible then evaluated else symbolic). This is a TOTAL function pinning the observable over the ENTIRE finite input domain (Side x Bool = 4 cases), independent of side. Therefore EVERY same-spec verifying impl is I/O-identical to gold on the observable; the R/I legs are mechanically locked (G-CONF territory). The only patch-relevant degree of freedom is the tag-I constant polyPriority, whose faithful patch is the literal line `Poly._op_priority = V` (mapping.md row: polyPriority<->Poly._op_priority). Verification requires exactly V > exprPriority(=10) to make (polyRight, coercible)->evaluated close via norm_num. So the real falsification axis is: is there a V>10 that closes the Lean proof but whose patch `Poly._op_priority=V` fails resolve? Gold chose 10.001 deliberately (just above Expr 10.0, below MatrixExpr/Boolean 11.0, tensor 12).

ATTACKS (all same_spec=True verified via swebench_unified.markers.same_spec; all lean_verify.sh exit 0; #print axioms clean = [propext, Classical.choice, Quot.sound], no sorryAx):
- atk_1: polyPriority=11 (ties MatrixExpr/Boolean _op_priority). verify exit 0; patch `_op_priority=11` -> RESOLVED (completed=true).
- atk_2: polyPriority=100 (DOMINATES every sympy _op_priority: Boolean 11, tensor 12, dyadic 13, holonomic 20). verify exit 0; patch `_op_priority=100` -> RESOLVED. This is the strongest priority-value attack; it resolving proves the P2P suite contains no cross-type Poly*Matrix/Boolean/tensor product that a higher priority would steal dispatch from.
- atk_3: polyPriority=10.01 (== DenseMatrix/MatrixCommon). verify exit 0; patch -> RESOLVED.
- atk_4: polyPriority=12 (== TensAdd, exceeds tensor). verify exit 0; patch -> RESOLVED.
- atk_5: control-flow echo -- polyLeft ALSO routed through the redundant precedence guard (distinct control flow, proof adapted for both branches), value 10.001. verify exit 0; patch identical to gold -> RESOLVED.
- atk_6: polyPriority=10.5 (distinct mid value). verify exit 0; patch -> RESOLVED.
- atk_7: polyPriority=10.0001 (near-gold distinct). verify exit 0; patch -> RESOLVED.

RESOLVE PROTOCOL: run_resolve (official Docker harness, swebench_unified.harness.run_resolve, timeout 1800). Baseline: gold patch (_op_priority=10.001) RESOLVED. Command: python resolve_run.py <label> <patchfile>. NOTE ON CONTENTION: 4-way concurrent Docker resolve produced completed=false / 'no report ... harness error' for atk_1/3/4/7 on first pass -- these are Docker contention artifacts (image-pull/report races), NOT non-resolution. Re-running 2-at-a-time (matching the successful gold+atk_2 pair) or alone yielded completed=true RESOLVED for every one. Every reported verdict below is from a completed=true run.

FINAL RESOLVE RESULTS (all completed=true): gold=RESOLVED, atk_1=RESOLVED, atk_2=RESOLVED, atk_3=RESOLVED, atk_4=RESOLVED, atk_5=RESOLVED, atk_6=RESOLVED, atk_7=RESOLVED.

PREPATCH: Solution_prepatch.lean (polyPriority=10) is same_spec=True but FAILS verification (lean_verify.sh exit 1, unsolved goal at proof line `norm_num : (10:Rat) > 10` which is false) -- the spec's discriminating clause (polyRight, coercible=true must be evaluated) correctly rejects the buggy prepatch impl. Bug reproduced.

REFINEMENT.MD AUDIT: legs tagged R (rows 3,5,6), A-reference (rows 1,3,4,5), I (row 2). NO kind-3 legs, NO A-consumed axiom, NO opaque decl. A-reference correspondences VERIFIED against the real repo at base_commit a5e6a101: Expr._op_priority=10.0 UNCHANGED (expr.py:105); call_highest_priority delegates iff other._op_priority > self._op_priority STRICT (decorators.py:126); Poly.__mul__/__rmul__ coerce-or-fallback, __mul__ NOT priority-decorated so polyLeft runs directly (polytools.py:4041-4059). All hold. Tag-I row 2 (Poly._op_priority=10.001) matches the gold patch line exactly.

CONCLUSION: The spec is a total observable function; all same-spec verifying impls are I/O-equivalent to gold, and every faithful patch across the full verifying priority range (including the dominating V=100) RESOLVES under the official harness. No verify->correct break found. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_ctrl.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 2 — `atk_2.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_3.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 4 — `atk_4.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_ctrl.lean`

```lean
import Mathlib
-- imports-end

/-!
Multiplying a plain expression by a polynomial object.

A polynomial object and a plain (non-polynomial) expression can be multiplied in
either order. Whether the product is carried out depends on whether the plain
expression is CONVERTIBLE into a polynomial over the polynomial operand's
generators:

* convertible (e.g. a generator, a number): the product is ALWAYS carried out —
  a polynomial value is produced — regardless of which side the polynomial is
  on; it is never left as an unevaluated symbolic product.
* not convertible (e.g. it involves a generator non-polynomially): the product
  is expressed as a plain symbolic expression instead — no polynomial value is
  produced, for either operand order.

The outcome is modeled as `evaluated` (a polynomial value is produced) versus
`symbolic` (a plain, non-polynomial expression results). The contract below
pins the outcome for both operand orders, `poly * expr` and `expr * poly`, as a
function of convertibility.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The dispatch
-- decision (which operand performs the product, and hence whether the product is
-- carried out or left symbolic) is modeled DEEPLY over the operands' numeric
-- operator precedences, so no `opaque`/`axiom` callee contract is needed. The
-- polynomial's own multiplication routine (coerce the other factor when
-- convertible, else fall back to a plain symbolic product) is an UNCHANGED
-- callee whose net effect is folded into the `coercible` input and the
-- `MulResult` observable; it is validated against the real repo by G-AX.
-- axioms-end

-- pure-start
/-- Which factor of the product is the polynomial. `polyLeft` is `poly * expr`;
`polyRight` is `expr * poly`. -/
inductive Side where
  | polyLeft
  | polyRight
deriving DecidableEq, Repr

/-- The observable outcome of the product: `evaluated` means a polynomial value
is produced; `symbolic` means a plain, non-polynomial expression results. -/
inductive MulResult where
  | evaluated
  | symbolic
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- A product mixing a plain expression and a polynomial is always carried out
when the expression is convertible into a polynomial over the polynomial's
generators (`coercible = true`): the outcome is `evaluated` for either operand
order. When the expression is not convertible (`coercible = false`), the
product is expressed as a plain symbolic expression: the outcome is `symbolic`
for either operand order. -/
def problem_spec_polyMul (side : Side) (coercible : Bool) (result : MulResult) : Prop :=
  result = (if coercible then MulResult.evaluated else MulResult.symbolic)
-- post-conditions-end

-- impl-start
def implementation_polyMul (side : Side) (coercible : Bool) : MulResult := Id.run do
  -- Operator precedences advertised by the two operand kinds.
  let exprPriority : Rat := 10            -- a plain expression
  let polyPriority : Rat := 10.001        -- a polynomial object
  match side with
  | Side.polyLeft =>
    -- The polynomial's own multiplication routine runs directly: it coerces the
    -- expression into a polynomial when convertible and multiplies; otherwise
    -- it falls back to the plain symbolic product of expressions.
    if coercible then
      return MulResult.evaluated
    else
      return MulResult.symbolic
  | Side.polyRight =>
    -- The precedence dispatch hands the product to the operand advertising the
    -- strictly greater precedence; only then does the polynomial's reflected
    -- multiplication run (coerce when convertible, else fall back symbolic).
    if polyPriority > exprPriority then
      if coercible then
        return MulResult.evaluated
      else
        return MulResult.symbolic
    else
      -- No delegation: the unevaluated symbolic product is returned.
      return MulResult.symbolic
-- impl-end

-- proof-start
theorem correct_polyMul :
    ∀ (side : Side) (coercible : Bool),
      problem_spec_polyMul side coercible (implementation_polyMul side coercible) := by
  intro side coercible
  unfold problem_spec_polyMul implementation_polyMul
  cases side
  · cases coercible <;> rfl
  · simp only [Id.run]
    rw [if_pos (by norm_num : (10.001 : Rat) > 10)]
    cases coercible <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC STRUCTURE: problem_spec_polyMul(side, coercible, result) := result = (if coercible then evaluated else symbolic). This is a TOTAL function pinning the observable over the ENTIRE finite input domain (Side x Bool = 4 cases), independent of side. Therefore EVERY same-spec verifying impl is I/O-identical to gold on the observable; the R/I legs are mechanically locked (G-CONF territory). The only patch-relevant degree of freedom is the tag-I constant polyPriority, whose faithful patch is the literal line `Poly._op_priority = V` (mapping.md row: polyPriority<->Poly._op_priority). Verification requires exactly V > exprPriority(=10) to make (polyRight, coercible)->evaluated close via norm_num. So the real falsification axis is: is there a V>10 that closes the Lean proof but whose patch `Poly._op_priority=V` fails resolve? Gold chose 10.001 deliberately (just above Expr 10.0, below MatrixExpr/Boolean 11.0, tensor 12).

ATTACKS (all same_spec=True verified via swebench_unified.markers.same_spec; all lean_verify.sh exit 0; #print axioms clean = [propext, Classical.choice, Quot.sound], no sorryAx):
- atk_1: polyPriority=11 (ties MatrixExpr/Boolean _op_priority). verify exit 0; patch `_op_priority=11` -> RESOLVED (completed=true).
- atk_2: polyPriority=100 (DOMINATES every sympy _op_priority: Boolean 11, tensor 12, dyadic 13, holonomic 20). verify exit 0; patch `_op_priority=100` -> RESOLVED. This is the strongest priority-value attack; it resolving proves the P2P suite contains no cross-type Poly*Matrix/Boolean/tensor product that a higher priority would steal dispatch from.
- atk_3: polyPriority=10.01 (== DenseMatrix/MatrixCommon). verify exit 0; patch -> RESOLVED.
- atk_4: polyPriority=12 (== TensAdd, exceeds tensor). verify exit 0; patch -> RESOLVED.
- atk_5: control-flow echo -- polyLeft ALSO routed through the redundant precedence guard (distinct control flow, proof adapted for both branches), value 10.001. verify exit 0; patch identical to gold -> RESOLVED.
- atk_6: polyPriority=10.5 (distinct mid value). verify exit 0; patch -> RESOLVED.
- atk_7: polyPriority=10.0001 (near-gold distinct). verify exit 0; patch -> RESOLVED.

RESOLVE PROTOCOL: run_resolve (official Docker harness, swebench_unified.harness.run_resolve, timeout 1800). Baseline: gold patch (_op_priority=10.001) RESOLVED. Command: python resolve_run.py <label> <patchfile>. NOTE ON CONTENTION: 4-way concurrent Docker resolve produced completed=false / 'no report ... harness error' for atk_1/3/4/7 on first pass -- these are Docker contention artifacts (image-pull/report races), NOT non-resolution. Re-running 2-at-a-time (matching the successful gold+atk_2 pair) or alone yielded completed=true RESOLVED for every one. Every reported verdict below is from a completed=true run.

FINAL RESOLVE RESULTS (all completed=true): gold=RESOLVED, atk_1=RESOLVED, atk_2=RESOLVED, atk_3=RESOLVED, atk_4=RESOLVED, atk_5=RESOLVED, atk_6=RESOLVED, atk_7=RESOLVED.

PREPATCH: Solution_prepatch.lean (polyPriority=10) is same_spec=True but FAILS verification (lean_verify.sh exit 1, unsolved goal at proof line `norm_num : (10:Rat) > 10` which is false) -- the spec's discriminating clause (polyRight, coercible=true must be evaluated) correctly rejects the buggy prepatch impl. Bug reproduced.

REFINEMENT.MD AUDIT: legs tagged R (rows 3,5,6), A-reference (rows 1,3,4,5), I (row 2). NO kind-3 legs, NO A-consumed axiom, NO opaque decl. A-reference correspondences VERIFIED against the real repo at base_commit a5e6a101: Expr._op_priority=10.0 UNCHANGED (expr.py:105); call_highest_priority delegates iff other._op_priority > self._op_priority STRICT (decorators.py:126); Poly.__mul__/__rmul__ coerce-or-fallback, __mul__ NOT priority-decorated so polyLeft runs directly (polytools.py:4041-4059). All hold. Tag-I row 2 (Poly._op_priority=10.001) matches the gold patch line exactly.

CONCLUSION: The spec is a total observable function; all same-spec verifying impls are I/O-equivalent to gold, and every faithful patch across the full verifying priority range (including the dominating V=100) RESOLVES under the official harness. No verify->correct break found. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness attack found no divergence. Spec: result = (if coercible then evaluated else symbolic) for both Side orders. Verified against real repo at base_commit a5e6a101 + gold patch (Poly._op_priority=10.001), py3.8+mpmath. Differential fuzz over 4 Poly objects x 24 exprs (generators, numbers, pi, I, exp, sin, cos, sqrt, 1/x, log, sin(y), sums, rationals, floats) x 2 operand orders (~192 probes): 0 mismatches. `coercible` computed exactly as the Poly(e,*p.gens) try/except-PolynomialError guard used by Poly.__mul__/__rmul__ (polytools.py:4041-4059), matching mapping.md's definition. polyLeft: Poly.__mul__ has @_sympifyit only (no priority dispatch), evaluates iff coercible always. polyRight: Expr.__mul__ binary_op_wrapper (decorators.py:123-132) delegates to Poly.__rmul__ iff 10.001>10.0 (true post-patch), which itself evaluates iff coercible else falls back to g*f.as_expr() (symbolic). Tricky cases confirmed: sin(y)*Poly(x,x)->evaluated (y not a generator, coercible), sin(x)/sqrt(x)/(1/x)*Poly(x,x)->symbolic both orders. Non-PolynomialError coercion errors: none observed in the probe set. Mechanical: lean_verify.sh exit 0 (only benign unused-var `side` warning); #print axioms correct_polyMul = [propext, Classical.choice, Quot.sound] clean, no sorryAx; same_spec(Solution, Solution_prepatch)=True (patch confined to elided impl region); prepatch (polyPriority:=10) genuinely fails to close (if_pos 10>10). Spec does not over-claim: coercible is a free input, MulResult observable is exactly Poly-vs-non-Poly. No diverging input on the modeled domain.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `mapping.md`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Verified the spec view via markers.spec_view with the real LeanBackend tables: impl and proof regions are BOTH fully elided ('implementation elided — supplied by the consumer' / 'proof elided'), same_spec(Solution.lean, Solution_prepatch.lean)=True, and the rendered spec_view sha 6c82ed4c… matches meta.json G-HYGIENE region_hashes.spec_view (clean). The entire fix mechanism is outside the spec view.

Gold edit (patch.diff): a single added line `Poly._op_priority = 10.001` at polytools.py:109 — raises Poly's operator precedence so the `expr * poly` (rmul) precedence dispatch delegates to Poly.__rmul__ and evaluates. hints_text is EMPTY, so no hint-based comparison is needed; the only public baseline is problem_statement.

The PUBLIC problem_statement already discloses the observable asymmetry the patch removes: it literally shows `Poly(x)*x` -> `Poly(x**2, x, domain='ZZ')` (evaluates) while `x*Poly(x)` stays unevaluated `x*Poly(x, x, domain='ZZ')`, plus `-2*Poly(x)`, `S(-2)*Poly(x)`, `Poly(x)*S(-2)`. So the target post-fix behavior (symmetric evaluation for coercible operands, both orders) is fully grounded in the public statement.

Spec-view lines examined for leakage beyond problem_statement:

(1) Docstring + post-condition `problem_spec_polyMul := result = (if coercible then evaluated else symbolic)` — pins only the post-fix OBSERVABLE outcome (evaluate iff coercible, both operand orders). That is exactly the asymmetry-removal already visible in the public bug report; no mechanism, value, or edit location disclosed.

(2) pure types Side/MulResult — abstract observables (operand order, evaluated-vs-symbolic), not patch specifics.

(3) axioms-region comment: 'the dispatch decision ... is modeled DEEPLY over the operands' numeric operator precedences'. This names the mechanism DOMAIN only. The public asymmetric `__mul__`/`__rmul__` symptom already implies operator-precedence dispatch to any sympy reader (the standard way one operand overrides the other's __mul__ is _op_priority). The comment does NOT reveal: the value 10.001 (or 10), that Poly lacked/inherited _op_priority, that the fix is 'add a priority constant to Poly', the class touched, the file/line, or the precedence comparison polyPriority>exprPriority — all of that lives ONLY in the elided impl/proof regions.
The `coercible` axis models the UNCHANGED coercion callee (Poly.__mul__/__rmul__ coerce-or-fallback), orthogonal to the gold edit, so it is not patch reconstruction either.

No spec-view line reveals the concrete gold edit beyond what the public problem_statement already implies. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.