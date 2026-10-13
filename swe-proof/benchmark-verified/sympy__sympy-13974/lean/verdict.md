# P2 adversarial audit — sympy__sympy-13974

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_3.lean` |

**Non-vacuity.** The positive control `pos_gold.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -55,12 +55,14 @@
 -- post-conditions-end
 
 -- impl-start
+-- WRONG (prepatch bug / partial-domain): a power whose base is a tensor product
+-- is returned UNDISTRIBUTED instead of pushing the exponent onto each factor.
 def implementation_tensorPow (e : QExpr) : QExpr := Id.run do
   match e with
   | .pow base exp =>
       match base with
-      | .tp args => return .tp (args.map (fun b => QExpr.pow b exp))
-      | _        => return e
+      | .tp _ => return e
+      | _     => return e
   | _ => return e
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -55,12 +55,15 @@
 -- post-conditions-end
 
 -- impl-start
+-- WRONG (boundary): distributes only when there are >=2 factors; a 1-element
+-- tensor-product base (or empty) is returned unchanged instead of distributed.
 def implementation_tensorPow (e : QExpr) : QExpr := Id.run do
   match e with
   | .pow base exp =>
       match base with
-      | .tp args => return .tp (args.map (fun b => QExpr.pow b exp))
-      | _        => return e
+      | .tp (a :: b :: rest) => return .tp ((a :: b :: rest).map (fun x => QExpr.pow x exp))
+      | .tp args             => return e
+      | _                    => return e
   | _ => return e
 -- impl-end
 
```

Attack 3 — `atk_3.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -55,20 +55,18 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_tensorPow (e : QExpr) : QExpr := Id.run do
-  match e with
-  | .pow base exp =>
-      match base with
-      | .tp args => return .tp (args.map (fun b => QExpr.pow b exp))
-      | _        => return e
-  | _ => return e
+-- ECHO (control-flow-effect): behaviorally identical to the gold impl but
+-- written as a direct top-level pattern match instead of nested Id.run matches.
+def implementation_tensorPow : QExpr → QExpr
+  | .pow (.tp args) exp => .tp (args.map (fun b => QExpr.pow b exp))
+  | e                   => e
 -- impl-end
 
 -- proof-start
 theorem correct_tensorPow :
     ∀ e : QExpr, problem_spec_tensorPow e (implementation_tensorPow e) := by
   intro e
-  unfold problem_spec_tensorPow implementation_tensorPow specTensorPow
+  unfold problem_spec_tensorPow specTensorPow
   cases e with
   | atom n => rfl
   | tp args => rfl
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -55,11 +55,14 @@
 -- post-conditions-end
 
 -- impl-start
+-- WRONG (control-flow-effect): distributes but keeps the whole base power as a
+-- single factor rather than one power per original factor (raises the tensor
+-- product to the exponent, not each factor).
 def implementation_tensorPow (e : QExpr) : QExpr := Id.run do
   match e with
   | .pow base exp =>
       match base with
-      | .tp args => return .tp (args.map (fun b => QExpr.pow b exp))
+      | .tp args => return .tp [QExpr.pow (.tp args) exp]
       | _        => return e
   | _ => return e
 -- impl-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -55,11 +55,13 @@
 -- post-conditions-end
 
 -- impl-start
+-- WRONG (ungrounded-oracle echo): raises each factor to the factor itself
+-- (b^b) instead of to the requested exponent — ignores `exp` entirely.
 def implementation_tensorPow (e : QExpr) : QExpr := Id.run do
   match e with
   | .pow base exp =>
       match base with
-      | .tp args => return .tp (args.map (fun b => QExpr.pow b exp))
+      | .tp args => return .tp (args.map (fun b => QExpr.pow b b))
       | _        => return e
   | _ => return e
 -- impl-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -55,12 +55,16 @@
 -- post-conditions-end
 
 -- impl-start
+-- WRONG (over-application / control-flow): ALSO rewrites a bare tensor product
+-- (not just a power of one) by raising each factor to... itself; and on a power
+-- base does the correct thing. The bare-tp arm must be returned unchanged.
 def implementation_tensorPow (e : QExpr) : QExpr := Id.run do
   match e with
   | .pow base exp =>
       match base with
       | .tp args => return .tp (args.map (fun b => QExpr.pow b exp))
       | _        => return e
+  | .tp args => return .tp (args.map (fun b => QExpr.pow b b))
   | _ => return e
 -- impl-end
 
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -55,11 +55,13 @@
 -- post-conditions-end
 
 -- impl-start
+-- WRONG (structural reorder): distributes correctly per factor but REVERSES the
+-- order of the factors in the resulting tensor product.
 def implementation_tensorPow (e : QExpr) : QExpr := Id.run do
   match e with
   | .pow base exp =>
       match base with
-      | .tp args => return .tp (args.map (fun b => QExpr.pow b exp))
+      | .tp args => return .tp ((args.map (fun b => QExpr.pow b exp)).reverse)
       | _        => return e
   | _ => return e
 -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_gold.lean`

```lean
import Mathlib
-- imports-end

/-!
Evaluating a power whose base is a tensor product.

A tensor product is a non-commutative product of two or more factors. Raising a
tensor product to a power should be evaluated by distributing the exponent across
each factor, producing a tensor product whose factors are the original factors
each raised to that power:

  (a ⊗ b ⊗ … ⊗ z) ^ n   evaluates to   (a^n) ⊗ (b^n) ⊗ … ⊗ (z^n).

Any other expression — a power whose base is not a tensor product, a bare tensor
product, or an atom — carries no such simplification and is returned unchanged.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The power-of-a-
-- tensor-product evaluation is modeled structurally over the expression carrier:
-- forming a factor's own power and assembling the factors into a tensor product
-- are concrete operations on the carrier (type-only refinement, see
-- refinement.md / mapping.md), so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- The fragment of a symbolic expression this specification observes.

* `atom n`     — an opaque leaf (any factor the evaluation does not destructure);
* `tp args`    — a tensor product of the factor expressions `args`;
* `pow b e`    — the expression `b` raised to the power `e`. -/
inductive QExpr where
  | atom (n : Nat)
  | tp   (args : List QExpr)
  | pow  (base exp : QExpr)
deriving Repr

/-- Reference evaluation of a power-of-a-tensor-product.

A power whose base is a tensor product distributes the exponent across each
factor: the result is the tensor product of each original factor raised to that
exponent. Every other expression is returned unchanged. -/
def specTensorPow : QExpr → QExpr
  | .pow (.tp args) exp => .tp (args.map (fun b => QExpr.pow b exp))
  | e                   => e
-- pure-end

-- post-conditions-start
/-- The evaluated expression is exactly the reference evaluation: when the input
is a power whose base is a tensor product, the exponent is distributed across
every factor (a tensor product of each factor raised to that exponent);
otherwise the input is returned unchanged. -/
def problem_spec_tensorPow (e : QExpr) (result : QExpr) : Prop :=
  result = specTensorPow e
-- post-conditions-end

-- impl-start
def implementation_tensorPow (e : QExpr) : QExpr := Id.run do
  match e with
  | .pow base exp =>
      match base with
      | .tp args => return .tp (args.map (fun b => QExpr.pow b exp))
      | _        => return e
  | _ => return e
-- impl-end

-- proof-start
theorem correct_tensorPow :
    ∀ e : QExpr, problem_spec_tensorPow e (implementation_tensorPow e) := by
  intro e
  unfold problem_spec_tensorPow implementation_tensorPow specTensorPow
  cases e with
  | atom n => rfl
  | tp args => rfl
  | pow base exp =>
      cases base with
      | atom n => rfl
      | tp args => rfl
      | pow b e => rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for sympy__sympy-13974 (lean). SCRATCH: 

SPEC SHAPE: postcondition problem_spec_tensorPow e result := (result = specTensorPow e) is EXACT functional equality against the total concrete reference specTensorPow. This is the tightest possible spec shape: any verifying impl must be extensionally identical to specTensorPow, so any behaviorally-wrong impl is unprovable. There are NO axiom/opaque declarations in Solution.lean; `#print axioms correct_tensorPow` = 'does not depend on any axioms' for both the gold and the closing echo, confirming zero A-consumed / A-reference legs.

SAME-SPEC: all 7 attacks + positive control confirmed same_spec=True (byte-identical axioms/pure/pre/post; only the impl region edited).

CMD (each attack): bash scripts/lean_verify.sh <file>. Axioms: appended `#print axioms correct_tensorPow` to *_ax.lean and re-ran lean_verify.

### Results
- pos_gold.lean (gold, distributes exp): lean_verify EXIT 0; axioms: none. Positive control PASSES.
- atk_1.lean (PREPATCH BUG / partial-domain: tp base returned undistributed): EXIT 1 (rejected). Prepatch reproduced — unclosable, as required by G-DIFF.
- atk_2.lean (boundary: distribute only when >=2 factors, else return unchanged): EXIT 1 (rejected).
- atk_3.lean (ECHO / control-flow-effect: behaviorally identical to gold but written as a direct top-level `QExpr -> QExpr` pattern match instead of nested Id.run): EXIT 0; axioms: none. CLOSES.
- atk_4.lean (control-flow-effect: wraps whole base power .tp [pow (tp args) exp] instead of per-factor): EXIT 1 (rejected).
- atk_5.lean (ungrounded-oracle: raises each factor to itself b^b, ignoring exp): EXIT 1 (rejected).
- atk_6.lean (over-application: also rewrites a bare tensor product): EXIT 1 (rejected).
- atk_7.lean (structural reorder: reverses factor order): EXIT 1 (rejected).

MANDATORY RESOLVE STEP: atk_3 is the ONLY same-spec impl whose proof closes with clean axioms. Its behavior is exactly the gold distribution (.tp (args.map (fun b => QExpr.pow b exp))), so its faithful refined patch is the gold patch (materialized at atk_3.patch). EXECUTED run_resolve('sympy__sympy-13974', patch, retries=0): RESOLVED=True, COMPLETED=True, note='resolved'. The echo's faithful patch RESOLVES => it is NOT a verify-not-correct witness (per the 2026-08-06 G-PANEL-1/echo policy: a resolving same-spec echo is not a weakness).

No closing candidate has a faithful patch that fails to resolve. No verified-but-wrong impl exists: the exact-equality spec discriminates every behavioral deviation (prepatch, boundary, ungrounded-oracle, control-flow-effect, structural reorder). verify => correct holds.

REFINEMENT.MD AUDIT: legs 1-5 tagged R / R/I / I; no A-consumed, no A-reference, no kind-3 (inexpressible) leg. Confirmed sound because `#print axioms` shows zero axioms — the model is fully concrete structural recursion over QExpr, so axiom_check.py being a skip stub is legitimate. Model<->patch correspondence VERIFIED against the real patched tensor_product_simp_Pow in the faith worktree: non-Pow -> unchanged; Pow with TensorProduct base -> TensorProduct(*[b**e.exp for b in base.args]) (== specTensorPow .pow(.tp args) exp arm); Pow non-tp base -> unchanged. The TensorProduct(*...) constructor-reduction caveat is scoped in mapping.md to the >=2-non-commutative-factor F2P regime (a modeling-boundary note, panel territory, not G-EQ).

VERDICT: SOUND. >=5 distinct wrong impls attacked (7 total + prepatch); all behaviorally-wrong ones rejected; the sole closing echo's faithful patch was materialized and RESOLVED via the official harness.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_3.lean` |

**Non-vacuity.** The positive control `pos_gold.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_gold.lean`

```lean
import Mathlib
-- imports-end

/-!
Evaluating a power whose base is a tensor product.

A tensor product is a non-commutative product of two or more factors. Raising a
tensor product to a power should be evaluated by distributing the exponent across
each factor, producing a tensor product whose factors are the original factors
each raised to that power:

  (a ⊗ b ⊗ … ⊗ z) ^ n   evaluates to   (a^n) ⊗ (b^n) ⊗ … ⊗ (z^n).

Any other expression — a power whose base is not a tensor product, a bare tensor
product, or an atom — carries no such simplification and is returned unchanged.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The power-of-a-
-- tensor-product evaluation is modeled structurally over the expression carrier:
-- forming a factor's own power and assembling the factors into a tensor product
-- are concrete operations on the carrier (type-only refinement, see
-- refinement.md / mapping.md), so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- The fragment of a symbolic expression this specification observes.

* `atom n`     — an opaque leaf (any factor the evaluation does not destructure);
* `tp args`    — a tensor product of the factor expressions `args`;
* `pow b e`    — the expression `b` raised to the power `e`. -/
inductive QExpr where
  | atom (n : Nat)
  | tp   (args : List QExpr)
  | pow  (base exp : QExpr)
deriving Repr

/-- Reference evaluation of a power-of-a-tensor-product.

A power whose base is a tensor product distributes the exponent across each
factor: the result is the tensor product of each original factor raised to that
exponent. Every other expression is returned unchanged. -/
def specTensorPow : QExpr → QExpr
  | .pow (.tp args) exp => .tp (args.map (fun b => QExpr.pow b exp))
  | e                   => e
-- pure-end

-- post-conditions-start
/-- The evaluated expression is exactly the reference evaluation: when the input
is a power whose base is a tensor product, the exponent is distributed across
every factor (a tensor product of each factor raised to that exponent);
otherwise the input is returned unchanged. -/
def problem_spec_tensorPow (e : QExpr) (result : QExpr) : Prop :=
  result = specTensorPow e
-- post-conditions-end

-- impl-start
def implementation_tensorPow (e : QExpr) : QExpr := Id.run do
  match e with
  | .pow base exp =>
      match base with
      | .tp args => return .tp (args.map (fun b => QExpr.pow b exp))
      | _        => return e
  | _ => return e
-- impl-end

-- proof-start
theorem correct_tensorPow :
    ∀ e : QExpr, problem_spec_tensorPow e (implementation_tensorPow e) := by
  intro e
  unfold problem_spec_tensorPow implementation_tensorPow specTensorPow
  cases e with
  | atom n => rfl
  | tp args => rfl
  | pow base exp =>
      cases base with
      | atom n => rfl
      | tp args => rfl
      | pow b e => rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for sympy__sympy-13974 (lean). SCRATCH: 

SPEC SHAPE: postcondition problem_spec_tensorPow e result := (result = specTensorPow e) is EXACT functional equality against the total concrete reference specTensorPow. This is the tightest possible spec shape: any verifying impl must be extensionally identical to specTensorPow, so any behaviorally-wrong impl is unprovable. There are NO axiom/opaque declarations in Solution.lean; `#print axioms correct_tensorPow` = 'does not depend on any axioms' for both the gold and the closing echo, confirming zero A-consumed / A-reference legs.

SAME-SPEC: all 7 attacks + positive control confirmed same_spec=True (byte-identical axioms/pure/pre/post; only the impl region edited).

CMD (each attack): bash scripts/lean_verify.sh <file>. Axioms: appended `#print axioms correct_tensorPow` to *_ax.lean and re-ran lean_verify.

### Results
- pos_gold.lean (gold, distributes exp): lean_verify EXIT 0; axioms: none. Positive control PASSES.
- atk_1.lean (PREPATCH BUG / partial-domain: tp base returned undistributed): EXIT 1 (rejected). Prepatch reproduced — unclosable, as required by G-DIFF.
- atk_2.lean (boundary: distribute only when >=2 factors, else return unchanged): EXIT 1 (rejected).
- atk_3.lean (ECHO / control-flow-effect: behaviorally identical to gold but written as a direct top-level `QExpr -> QExpr` pattern match instead of nested Id.run): EXIT 0; axioms: none. CLOSES.
- atk_4.lean (control-flow-effect: wraps whole base power .tp [pow (tp args) exp] instead of per-factor): EXIT 1 (rejected).
- atk_5.lean (ungrounded-oracle: raises each factor to itself b^b, ignoring exp): EXIT 1 (rejected).
- atk_6.lean (over-application: also rewrites a bare tensor product): EXIT 1 (rejected).
- atk_7.lean (structural reorder: reverses factor order): EXIT 1 (rejected).

MANDATORY RESOLVE STEP: atk_3 is the ONLY same-spec impl whose proof closes with clean axioms. Its behavior is exactly the gold distribution (.tp (args.map (fun b => QExpr.pow b exp))), so its faithful refined patch is the gold patch (materialized at atk_3.patch). EXECUTED run_resolve('sympy__sympy-13974', patch, retries=0): RESOLVED=True, COMPLETED=True, note='resolved'. The echo's faithful patch RESOLVES => it is NOT a verify-not-correct witness (per the 2026-08-06 G-PANEL-1/echo policy: a resolving same-spec echo is not a weakness).

No closing candidate has a faithful patch that fails to resolve. No verified-but-wrong impl exists: the exact-equality spec discriminates every behavioral deviation (prepatch, boundary, ungrounded-oracle, control-flow-effect, structural reorder). verify => correct holds.

REFINEMENT.MD AUDIT: legs 1-5 tagged R / R/I / I; no A-consumed, no A-reference, no kind-3 (inexpressible) leg. Confirmed sound because `#print axioms` shows zero axioms — the model is fully concrete structural recursion over QExpr, so axiom_check.py being a skip stub is legitimate. Model<->patch correspondence VERIFIED against the real patched tensor_product_simp_Pow in the faith worktree: non-Pow -> unchanged; Pow with TensorProduct base -> TensorProduct(*[b**e.exp for b in base.args]) (== specTensorPow .pow(.tp args) exp arm); Pow non-tp base -> unchanged. The TensorProduct(*...) constructor-reduction caveat is scoped in mapping.md to the >=2-non-commutative-factor F2P regime (a modeling-boundary note, panel territory, not G-EQ).

VERDICT: SOUND. >=5 distinct wrong impls attacked (7 total + prepatch); all behaviorally-wrong ones rejected; the sole closing echo's faithful patch was materialized and RESOLVED via the official harness.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) verdict: FAITHFUL. No diverging input exists.

Setup verified:
- same_spec(Solution.lean, Solution_prepatch.lean, lean tables) = True. The spec region (QExpr carrier; specTensorPow reference; problem_spec_tensorPow postcondition) is byte-identical between patched and prepatch bundles; only impl+proof differ (the G-DIFF signal), as intended.
- Solution.lean compiles via lean_verify.sh, exit 0, no sorry. `#print axioms correct_tensorPow` => 'does not depend on any axioms' (no sorryAx; proof is genuine).

Real callee: modeled function is the new helper tensor_product_simp_Pow(e) added by the gold patch (sympy/physics/quantum/tensorproduct.py:364-372). Confirmed present in the base_commit worktree (84c125972a) with patch applied:
  if not isinstance(e, Pow): return e
  if isinstance(e.base, TensorProduct): return TensorProduct(*[b**e.exp for b in e.base.args])
  else: return e

Differential test (my own run, py3.8 venv w/ mpmath against the real repo, seed 13974, 120k inputs across all four branches: pow-of-tensor-product, pow-of-non-tp base, bare tensor product, bare atom; exponents {x, y, 0, 1, 2, 3, -1}): 0 disagreements between the R/I shadow of implementation_tensorPow and the real tensor_product_simp_Pow.

Spec-too-strong probing (boundary cases where sympy auto-evaluation could make the structural Lean spec disagree):
- exp=0: TensorProduct(A,B)**0 auto-collapses to 1 (a non-Pow) at construction, so the real callee never receives it via the modeled Pow branch. Feeding a genuinely unevaluated Pow(tp, 0, evaluate=False): real => 1x1, and the spec's structural image TensorProduct(A**0, B**0) => 1x1. AGREE.
- exp=1: Pow(tp,1) collapses to the bare TensorProduct; unevaluated form: real => AxB, spec image TensorProduct(A**1,B**1) => AxB. AGREE.
No reachable input drives the real function and the spec apart. The spec exactly mirrors the callee's distribute-across-factors-or-return-unchanged behavior; it is neither too strong (no phantom obligation the repo violates) nor drifting.

axiom_check.py is a legitimate skip stub (no consumed axiom, no deep-model A-reference); mapping/refinement claims are all R/I and are mechanically covered by G-CONF (which I independently reproduced). Conclusion: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (Solution.lean spec regions; impl+proof elided per _lean_spec_view; spec region byte-identical to Solution_prepatch, same_spec=True) does not reconstruct the gold edit beyond the public problem_statement. Mechanical G-LEAK screen (leakage.screen with frozen row patch + problem_statement) PASSES with zero hard failures. Checked semantically as leakage/gold-reconstruction attacker: (1) No diff markers (@@/+++/diff --git). (2) No patched file path 'sympy/physics/quantum/tensorproduct.py' or dotted module path. (3) None of the patched repo symbols {tensor_product_simp, tensor_product_simp_Mul, tensor_product_simp_Pow} appear in any spec-view identifier or comment — spec symbols are abstract (QExpr, specTensorPow, problem_spec_tensorPow). (4) No bug/fix/prepatch narration in the spec view; the prepatch bug story lives only in refinement.md (auditor derivation, not the consumer spec view). The docstring/spec states the DESIRED behavior — power of a tensor product distributes the exponent across factors, (a⊗b⊗…⊗z)^n -> (a^n)⊗(b^n)⊗…⊗(z^n), everything else unchanged — which is the legitimate and unavoidable content of any faithful verification spec (the solver still must supply the elided impl+proof). This behavioral rule is also already conveyed by the public problem_statement's title ('Evaluating powers of TensorProduct') and its expected-result examples ([5]/[9]); the verbatim distribution formula additionally appears in hints_text, which the gate correctly disregards. Describing correct behavior at an abstract carrier level is not leaking the gold implementation edit. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
