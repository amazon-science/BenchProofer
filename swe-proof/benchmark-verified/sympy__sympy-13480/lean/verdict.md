# P2 adversarial audit — sympy__sympy-13480

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -78,9 +78,9 @@
 def implementation_cothReduce (x m : Expr) : Except Unit Expr := Id.run do
   let cothm := cothFn m
   if cothm = complexInfinity then
+    return Except.ok (tanhFn x)
+  else
     return Except.ok (cothFn x)
-  else
-    return Except.ok (tanhFn x)
 -- impl-end
 
 -- proof-start
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -76,11 +76,7 @@
 
 -- impl-start
 def implementation_cothReduce (x m : Expr) : Except Unit Expr := Id.run do
-  let cothm := cothFn m
-  if cothm = complexInfinity then
-    return Except.ok (cothFn x)
-  else
-    return Except.ok (tanhFn x)
+  return Except.ok (cothFn x)
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -76,11 +76,7 @@
 
 -- impl-start
 def implementation_cothReduce (x m : Expr) : Except Unit Expr := Id.run do
-  let cothm := cothFn m
-  if cothm = complexInfinity then
-    return Except.ok (cothFn x)
-  else
-    return Except.ok (tanhFn x)
+  return Except.ok (tanhFn x)
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -76,11 +76,7 @@
 
 -- impl-start
 def implementation_cothReduce (x m : Expr) : Except Unit Expr := Id.run do
-  let cothm := cothFn m
-  if cothm = complexInfinity then
-    return Except.ok (cothFn x)
-  else
-    return Except.ok (tanhFn x)
+  return Except.error ()
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -76,8 +76,8 @@
 
 -- impl-start
 def implementation_cothReduce (x m : Expr) : Except Unit Expr := Id.run do
-  let cothm := cothFn m
-  if cothm = complexInfinity then
+  let cothx := cothFn x
+  if cothx = complexInfinity then
     return Except.ok (cothFn x)
   else
     return Except.ok (tanhFn x)
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -78,9 +78,9 @@
 def implementation_cothReduce (x m : Expr) : Except Unit Expr := Id.run do
   let cothm := cothFn m
   if cothm = complexInfinity then
-    return Except.ok (cothFn x)
+    return Except.ok (cothFn m)
   else
-    return Except.ok (tanhFn x)
+    return Except.ok (tanhFn m)
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,7 +77,7 @@
 -- impl-start
 def implementation_cothReduce (x m : Expr) : Except Unit Expr := Id.run do
   let cothm := cothFn m
-  if cothm = complexInfinity then
+  if cothm ≠ complexInfinity then
     return Except.ok (cothFn x)
   else
     return Except.ok (tanhFn x)
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -76,8 +76,8 @@
 
 -- impl-start
 def implementation_cothReduce (x m : Expr) : Except Unit Expr := Id.run do
-  let cothm := cothFn m
-  if cothm = complexInfinity then
+  let tanm := tanhFn m
+  if tanm = complexInfinity then
     return Except.ok (cothFn x)
   else
     return Except.ok (tanhFn x)
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Reducing the hyperbolic cotangent of a sum one of whose summands is a nonzero
multiple of the imaginary half-period.

When the argument of the hyperbolic cotangent is an additive expression, it is
split into a remaining part `x` and a part `m` that is a multiple of the
imaginary half-period. In the case that this multiple part is nonzero, the value
of the whole is determined by the hyperbolic cotangent of `m`:

  * if the hyperbolic cotangent of `m` is the distinguished point at (complex)
    infinity, the result is the hyperbolic cotangent of `x`;
  * otherwise the result is the hyperbolic tangent of `x`.

The reduction always produces a value for this case (it never fails to
complete). We model the outcome as `Except Unit Expr`: `Except.ok v` is a
completed reduction yielding the value `v`; `Except.error ()` denotes a
computation that does not complete and yields no value. A correct reduction of
this case is always `Except.ok …`.

The splitting of the argument and the test that the multiple part is nonzero are
unchanged surrounding context; the behavior specified here is the reduction
reached once `x` and the nonzero multiple `m` are in hand. The two hyperbolic
evaluators and the point at infinity are unchanged outside operations, left
abstract — the specification constrains none of their internals, only how the
reduction selects among their results.
-/

-- axioms-start
/-- A symbolic expression, identified by its canonical representation. The
behavior under specification observes expressions only through equality and as
the arguments threaded to the two hyperbolic evaluators below, so a
representation-tagged carrier is a faithful model. -/
structure Expr where
  repr : String
deriving DecidableEq, Inhabited, Repr

/-- The distinguished point at (complex) infinity — the sentinel expression the
reduction tests its dispatch value against. An unchanged outside value, left
abstract; observed only through equality. -/
opaque complexInfinity : Expr

/-- The (unchanged) hyperbolic cotangent evaluator applied to a subterm. Its
internal algorithm lies outside the behavior under specification and is left
abstract: the specification constrains none of its inner workings, only how its
result is used. -/
opaque cothFn : Expr → Expr

/-- The (unchanged) hyperbolic tangent evaluator applied to a subterm. Left
abstract for the same reason as `cothFn`. -/
opaque tanhFn : Expr → Expr
-- axioms-end

-- pure-start
-- No additional functional helpers are needed: the behavior is the control flow
-- selecting between the two unchanged evaluators above.
-- pure-end

-- post-conditions-start
/-- The outcome of reducing the hyperbolic cotangent of a sum, given the
remaining part `x` and the nonzero multiple part `m`.

The reduction completes with a value (`Except.ok …`); which value is decided by
the hyperbolic cotangent of `m`:

  * if `cothFn m` is the point at infinity, the result is `cothFn x`;
  * otherwise the result is `tanhFn x`.

The result is fully pinned to the inputs through the two evaluators; nothing is
left free, and the error outcome never occurs. -/
def problem_spec_cothReduce (x m : Expr) (result : Except Unit Expr) : Prop :=
  result = Except.ok (if cothFn m = complexInfinity then cothFn x else tanhFn x)
-- post-conditions-end

-- impl-start
def implementation_cothReduce (x m : Expr) : Except Unit Expr := Id.run do
  let cothm := cothFn m
  if cothm = complexInfinity then
    return Except.ok (cothFn x)
  else
    return Except.ok (tanhFn x)
-- impl-end

-- proof-start
theorem correct_cothReduce :
    ∀ (x m : Expr),
      problem_spec_cothReduce x m (implementation_cothReduce x m) := by
  intro x m
  unfold problem_spec_cothReduce implementation_cothReduce
  by_cases h : cothFn m = complexInfinity
  · simp only [Id.run, h, if_true]; rfl
  · simp only [Id.run, h, if_false]; rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: total functional pin. problem_spec_cothReduce x m result := result = Except.ok (if cothFn m = complexInfinity then cothFn x else tanhFn x), quantified over ALL x m with cothFn/tanhFn/complexInfinity OPAQUE. Any verifying impl is therefore forced extensionally equal to gold; there is no behavioral slack.

SAME_SPEC: all 8 attacks + pos_control byte-identical spec view except impl/proof (same_spec=True; confirmed with swebench_unified.markers.same_spec, backend=lean). Only the impl region (and the carried gold proof body) differ; axioms/pure/pre/post byte-identical.

### ATTACK BATTERY (all run via `bash scripts/lean_verify.sh <f>`):
- atk_1 (branches swapped: true->tanhFn x, false->cothFn x): EXIT=1, rfl failed at both legs.
- atk_2 (always Except.ok (cothFn x), ignore dispatch): EXIT=1, rfl failed (goal pure(cothFn x)=Except.ok(if ...)).
- atk_3 (always Except.ok (tanhFn x)): EXIT=1, rfl failed.
- atk_4 (return Except.error () — prepatch non-completion bug re-encoded): EXIT=1, goal `pure (Except.error ()) = Except.ok (cothFn x)`.
- atk_5 (partial-domain / wrong dispatch var: tests cothFn x = complexInfinity): EXIT=1, rfl failed both legs.
- atk_6 (wrong return argument: returns cothFn m / tanhFn m): EXIT=1, rfl failed both legs.
- atk_7 (control-flow-effect: negated dispatch `cothm ≠ complexInfinity`): EXIT=1, rfl failed both legs.
- atk_8 (ungrounded-oracle echo / boundary: dispatch on tanhFn m = complexInfinity): EXIT=1, rfl failed both legs.
All 8 failures are genuine proof failures (`Tactic rfl failed`, LHS not defeq RHS), NOT syntax/timeout. Verified concurrently in batches of 4 background Bash jobs.

POSITIVE CONTROL (gold copy): `bash scripts/lean_verify.sh pos_control.lean` -> EXIT=0 (verifies, no sorry/error). `#print axioms correct_cothReduce` -> `[propext]` only (no sorryAx, no Classical.choice) — CLEAN axioms.

PREPATCH: Solution_prepatch.lean (impl = Except.error (), carried gold proof) -> EXIT=1: goal `pure (Except.error ()) = Except.ok (if cothFn m = complexInfinity then cothFn x else tanhFn x)` cannot close. Prepatch bug faithfully reproduced.

NO MANDATORY RESOLVE RUN: the protocol requires materializing a faithful refined patch and running run_resolve ONLY for a wrong impl whose proof CLOSES with clean axioms. Zero wrong impls close (the total functional pin admits only gold-equivalent impls). Hence no verify⇏correct witness exists and no resolve run was required; patches={}.

REFINEMENT.MD AUDIT: legs are `let cothm := cothFn m` (A-reference->coth), `if cothm = complexInfinity` (I, the corrected dispatch line), `return Except.ok (cothFn x)` (A-reference->coth), `return Except.ok (tanhFn x)` (A-reference->tanh). No R-only, no consumed `_prop` axiom (kind-3 absent) — proof discharges by definitional case-analysis on one decidable test, consuming no callee property (confirmed by axioms=[propext]). G-AX skip stub legitimate. A-reference correspondence verified against real post-patch sympy/functions/elementary/hyperbolic.py: `cothm = coth(m)` @606, `if cothm is S.ComplexInfinity` @607, `return coth(x)` @608, `else return tanh(x)` @610; coth class @554, tanh class @399, ComplexInfinity singleton @sympy/core/numbers.py:3312. Structure matches faithfully (line numbers differ from mapping.md's base_commit because the on-disk checkout is a nearby merge commit; branch semantics identical).

VERDICT: SOUND. 8 distinct same-spec wrong impls attacked, none closes; the spec's total functional pin over opaque callees rejects every behaviorally-wrong impl. Positive control verifies clean; prepatch reproduced; refinement A-legs faithful.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Reducing the hyperbolic cotangent of a sum one of whose summands is a nonzero
multiple of the imaginary half-period.

When the argument of the hyperbolic cotangent is an additive expression, it is
split into a remaining part `x` and a part `m` that is a multiple of the
imaginary half-period. In the case that this multiple part is nonzero, the value
of the whole is determined by the hyperbolic cotangent of `m`:

  * if the hyperbolic cotangent of `m` is the distinguished point at (complex)
    infinity, the result is the hyperbolic cotangent of `x`;
  * otherwise the result is the hyperbolic tangent of `x`.

The reduction always produces a value for this case (it never fails to
complete). We model the outcome as `Except Unit Expr`: `Except.ok v` is a
completed reduction yielding the value `v`; `Except.error ()` denotes a
computation that does not complete and yields no value. A correct reduction of
this case is always `Except.ok …`.

The splitting of the argument and the test that the multiple part is nonzero are
unchanged surrounding context; the behavior specified here is the reduction
reached once `x` and the nonzero multiple `m` are in hand. The two hyperbolic
evaluators and the point at infinity are unchanged outside operations, left
abstract — the specification constrains none of their internals, only how the
reduction selects among their results.
-/

-- axioms-start
/-- A symbolic expression, identified by its canonical representation. The
behavior under specification observes expressions only through equality and as
the arguments threaded to the two hyperbolic evaluators below, so a
representation-tagged carrier is a faithful model. -/
structure Expr where
  repr : String
deriving DecidableEq, Inhabited, Repr

/-- The distinguished point at (complex) infinity — the sentinel expression the
reduction tests its dispatch value against. An unchanged outside value, left
abstract; observed only through equality. -/
opaque complexInfinity : Expr

/-- The (unchanged) hyperbolic cotangent evaluator applied to a subterm. Its
internal algorithm lies outside the behavior under specification and is left
abstract: the specification constrains none of its inner workings, only how its
result is used. -/
opaque cothFn : Expr → Expr

/-- The (unchanged) hyperbolic tangent evaluator applied to a subterm. Left
abstract for the same reason as `cothFn`. -/
opaque tanhFn : Expr → Expr
-- axioms-end

-- pure-start
-- No additional functional helpers are needed: the behavior is the control flow
-- selecting between the two unchanged evaluators above.
-- pure-end

-- post-conditions-start
/-- The outcome of reducing the hyperbolic cotangent of a sum, given the
remaining part `x` and the nonzero multiple part `m`.

The reduction completes with a value (`Except.ok …`); which value is decided by
the hyperbolic cotangent of `m`:

  * if `cothFn m` is the point at infinity, the result is `cothFn x`;
  * otherwise the result is `tanhFn x`.

The result is fully pinned to the inputs through the two evaluators; nothing is
left free, and the error outcome never occurs. -/
def problem_spec_cothReduce (x m : Expr) (result : Except Unit Expr) : Prop :=
  result = Except.ok (if cothFn m = complexInfinity then cothFn x else tanhFn x)
-- post-conditions-end

-- impl-start
def implementation_cothReduce (x m : Expr) : Except Unit Expr := Id.run do
  let cothm := cothFn m
  if cothm = complexInfinity then
    return Except.ok (cothFn x)
  else
    return Except.ok (tanhFn x)
-- impl-end

-- proof-start
theorem correct_cothReduce :
    ∀ (x m : Expr),
      problem_spec_cothReduce x m (implementation_cothReduce x m) := by
  intro x m
  unfold problem_spec_cothReduce implementation_cothReduce
  by_cases h : cothFn m = complexInfinity
  · simp only [Id.run, h, if_true]; rfl
  · simp only [Id.run, h, if_false]; rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: total functional pin. problem_spec_cothReduce x m result := result = Except.ok (if cothFn m = complexInfinity then cothFn x else tanhFn x), quantified over ALL x m with cothFn/tanhFn/complexInfinity OPAQUE. Any verifying impl is therefore forced extensionally equal to gold; there is no behavioral slack.

SAME_SPEC: all 8 attacks + pos_control byte-identical spec view except impl/proof (same_spec=True; confirmed with swebench_unified.markers.same_spec, backend=lean). Only the impl region (and the carried gold proof body) differ; axioms/pure/pre/post byte-identical.

### ATTACK BATTERY (all run via `bash scripts/lean_verify.sh <f>`):
- atk_1 (branches swapped: true->tanhFn x, false->cothFn x): EXIT=1, rfl failed at both legs.
- atk_2 (always Except.ok (cothFn x), ignore dispatch): EXIT=1, rfl failed (goal pure(cothFn x)=Except.ok(if ...)).
- atk_3 (always Except.ok (tanhFn x)): EXIT=1, rfl failed.
- atk_4 (return Except.error () — prepatch non-completion bug re-encoded): EXIT=1, goal `pure (Except.error ()) = Except.ok (cothFn x)`.
- atk_5 (partial-domain / wrong dispatch var: tests cothFn x = complexInfinity): EXIT=1, rfl failed both legs.
- atk_6 (wrong return argument: returns cothFn m / tanhFn m): EXIT=1, rfl failed both legs.
- atk_7 (control-flow-effect: negated dispatch `cothm ≠ complexInfinity`): EXIT=1, rfl failed both legs.
- atk_8 (ungrounded-oracle echo / boundary: dispatch on tanhFn m = complexInfinity): EXIT=1, rfl failed both legs.
All 8 failures are genuine proof failures (`Tactic rfl failed`, LHS not defeq RHS), NOT syntax/timeout. Verified concurrently in batches of 4 background Bash jobs.

POSITIVE CONTROL (gold copy): `bash scripts/lean_verify.sh pos_control.lean` -> EXIT=0 (verifies, no sorry/error). `#print axioms correct_cothReduce` -> `[propext]` only (no sorryAx, no Classical.choice) — CLEAN axioms.

PREPATCH: Solution_prepatch.lean (impl = Except.error (), carried gold proof) -> EXIT=1: goal `pure (Except.error ()) = Except.ok (if cothFn m = complexInfinity then cothFn x else tanhFn x)` cannot close. Prepatch bug faithfully reproduced.

NO MANDATORY RESOLVE RUN: the protocol requires materializing a faithful refined patch and running run_resolve ONLY for a wrong impl whose proof CLOSES with clean axioms. Zero wrong impls close (the total functional pin admits only gold-equivalent impls). Hence no verify⇏correct witness exists and no resolve run was required; patches={}.

REFINEMENT.MD AUDIT: legs are `let cothm := cothFn m` (A-reference->coth), `if cothm = complexInfinity` (I, the corrected dispatch line), `return Except.ok (cothFn x)` (A-reference->coth), `return Except.ok (tanhFn x)` (A-reference->tanh). No R-only, no consumed `_prop` axiom (kind-3 absent) — proof discharges by definitional case-analysis on one decidable test, consuming no callee property (confirmed by axioms=[propext]). G-AX skip stub legitimate. A-reference correspondence verified against real post-patch sympy/functions/elementary/hyperbolic.py: `cothm = coth(m)` @606, `if cothm is S.ComplexInfinity` @607, `return coth(x)` @608, `else return tanh(x)` @610; coth class @554, tanh class @399, ComplexInfinity singleton @sympy/core/numbers.py:3312. Structure matches faithfully (line numbers differ from mapping.md's base_commit because the on-disk checkout is a nearby merge commit; branch semantics identical).

VERDICT: SOUND. 8 distinct same-spec wrong impls attacked, none closes; the spec's total functional pin over opaque callees rejects every behaviorally-wrong impl. Positive control verifies clean; prepatch reproduced; refinement A-legs faithful.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) attack: no divergence found. Evidence:

1. Compiles + genuine proof: scripts/lean_verify.sh exits 0; `#print axioms correct_cothReduce` => [propext] only (no sorryAx, no Classical.choice beyond std). Proof is by definitional case-analysis on the single decidable test cothFn m = complexInfinity — real, not a stub.

2. Spec region byte-identical: swebench_unified markers same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend.language) == True. Only impl/proof regions differ; the modeled spec `problem_spec_cothReduce` is frozen.

3. Real repo at base_commit f57fe3f4b3f2cab225749e1b3b38ae1bf80b62f0, post-patch coth.eval additive branch:
     if arg.is_Add:
         x, m = _peeloff_ipi(arg)
         if m:
             cothm = coth(m)
             if cothm is S.ComplexInfinity:   # (post-patch corrected line)
                 return coth(x)
             else: # cothm == 0
                 return tanh(x)
   Spec: result = Except.ok (if cothFn m = complexInfinity then cothFn x else tanhFn x). This is a structural mirror of the real dispatch.

4. No over-constraint / no drift:
   - The real `else` arm is unconditional over ALL non-zoo values (the `# cothm == 0` is a comment, not a guard). The model's else -> tanhFn x matches the CODE, not the comment, so it does not falsely narrow behavior. Faithful.
   - 'Always completes' (Except.ok, never Except.error) is correct: inside `if m:` every path returns via one of the two arms — no fall-through, no exception, no None. The spec's guarantee that error never occurs matches the real code exactly (the error/NameError case is prepatch only, correctly modeled in Solution_prepatch as Except.error ()).
   - Callees cothFn/tanhFn/complexInfinity are opaque (A-reference); the spec constrains none of their internals, only how results are selected — so the spec cannot be 'too strong' about them. Their fidelity to real coth/tanh/S.ComplexInfinity is validated differentially by G-CONF.
   - Modeling scope (x, m already split with m != 0) is honestly documented; the unmodeled surrounding pre-branches (is_Number, imaginary-coeff, negative-coeff, _peeloff_ipi split) only SELECT which (x,m) reach the dispatch, they do not alter the dispatch's behavior. No in-scope input diverges.

For every scoped input (x, m) with m nonzero, the modeled function agrees with the real coth.eval dispatch. No diverging input exists. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view = Solution.lean (the file G-LEAK screens via bundle.solution_src()). It is fully abstract: opaque `cothFn`/`tanhFn`/`complexInfinity` and a spec `problem_spec_cothReduce x m result := result = Except.ok (if cothFn m = complexInfinity then cothFn x else tanhFn x)`. It contains NONE of the gold-edit tokens (`cotm`/`cothm`, `S.ComplexInfinity`, `NameError`, `hyperbolic.py:590`, `_peeloff_ipi`). The lexical screen (swebench_unified.leakage.screen with backend lean) returns passed=True, hard_failures=[]. same_spec(Solution.lean, Solution_prepatch.lean) = True — spec region byte-identical across variants, so the spec does not encode the fix by differing between pre/post. Critically, the public problem_statement ALREADY discloses the bug maximally: it prints the traceback `if cotm is S.ComplexInfinity:` at hyperbolic.py:590 and `NameError: name 'cotm' is not defined`; the gold fix is the one-token `cotm`->`cothm` correction, essentially readable straight from the public statement plus the unchanged surrounding repo code. The spec's true/false legs (`cothFn x` / `tanhFn x`) mirror UNCHANGED repo context (`return coth(x)` / `return tanh(x)`), not the gold edit. Specifying the corrected intended outcome is inherent to any faithful spec and reveals nothing about the gold implementation beyond what problem_statement already exposes. refinement.md/mapping.md do quote patch specifics (cotm/cothm, line numbers), but those are auditor derivation artifacts, not the solver-facing spec view that G-LEAK/G-PANEL-3 screen. No leakage beyond public problem_statement (excluding hints_text).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
