# P2 adversarial audit — sympy__sympy-20428

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -50,7 +50,7 @@
 
 -- impl-start
 def implementation_nonzero (e : ExprVal) : Bool := Id.run do
-  return !e.isMathZero
+  return !e.isLiteralZero
 -- impl-end
 
 -- proof-start
@@ -58,5 +58,6 @@
     ∀ (e : ExprVal),
       problem_spec_nonzero e (implementation_nonzero e) := by
   intro e
-  rfl
+  obtain ⟨l, m⟩ := e
+  cases l <;> cases m <;> first | rfl | decide | simp_all [implementation_nonzero, problem_spec_nonzero]
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -49,8 +49,7 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_nonzero (e : ExprVal) : Bool := Id.run do
-  return !e.isMathZero
+def implementation_nonzero (e : ExprVal) : Bool := true
 -- impl-end
 
 -- proof-start
@@ -58,5 +57,6 @@
     ∀ (e : ExprVal),
       problem_spec_nonzero e (implementation_nonzero e) := by
   intro e
-  rfl
+  obtain ⟨l, m⟩ := e
+  cases l <;> cases m <;> first | rfl | decide | simp_all [implementation_nonzero, problem_spec_nonzero]
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -49,8 +49,7 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_nonzero (e : ExprVal) : Bool := Id.run do
-  return !e.isMathZero
+def implementation_nonzero (e : ExprVal) : Bool := !e.isMathZero || e.isLiteralZero
 -- impl-end
 
 -- proof-start
@@ -58,5 +57,6 @@
     ∀ (e : ExprVal),
       problem_spec_nonzero e (implementation_nonzero e) := by
   intro e
-  rfl
+  obtain ⟨l, m⟩ := e
+  cases l <;> cases m <;> first | rfl | decide | simp_all [implementation_nonzero, problem_spec_nonzero]
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -49,8 +49,7 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_nonzero (e : ExprVal) : Bool := Id.run do
-  return !e.isMathZero
+def implementation_nonzero (e : ExprVal) : Bool := !e.isMathZero && !e.isLiteralZero
 -- impl-end
 
 -- proof-start
@@ -58,5 +57,6 @@
     ∀ (e : ExprVal),
       problem_spec_nonzero e (implementation_nonzero e) := by
   intro e
-  rfl
+  obtain ⟨l, m⟩ := e
+  cases l <;> cases m <;> first | rfl | decide | simp_all [implementation_nonzero, problem_spec_nonzero]
 -- proof-end
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -50,7 +50,12 @@
 
 -- impl-start
 def implementation_nonzero (e : ExprVal) : Bool := Id.run do
-  return !e.isMathZero
+  let mut r := true
+  if e.isMathZero then
+    r := false
+  else
+    r := true
+  return r
 -- impl-end
 
 -- proof-start
@@ -58,5 +63,6 @@
     ∀ (e : ExprVal),
       problem_spec_nonzero e (implementation_nonzero e) := by
   intro e
-  rfl
+  obtain ⟨l, m⟩ := e
+  cases l <;> cases m <;> first | rfl | decide | simp_all [implementation_nonzero, problem_spec_nonzero]
 -- proof-end
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -49,8 +49,9 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_nonzero (e : ExprVal) : Bool := Id.run do
-  return !e.isMathZero
+def implementation_nonzero (e : ExprVal) : Bool :=
+  let _ignore := e.isLiteralZero
+  if e.isMathZero then false else true
 -- impl-end
 
 -- proof-start
@@ -58,5 +59,6 @@
     ∀ (e : ExprVal),
       problem_spec_nonzero e (implementation_nonzero e) := by
   intro e
-  rfl
+  obtain ⟨l, m⟩ := e
+  cases l <;> cases m <;> first | rfl | decide | simp_all [implementation_nonzero, problem_spec_nonzero]
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -50,7 +50,7 @@
 
 -- impl-start
 def implementation_nonzero (e : ExprVal) : Bool := Id.run do
-  return !e.isMathZero
+  return !(e.isMathZero && !e.isLiteralZero)
 -- impl-end
 
 -- proof-start
@@ -58,5 +58,6 @@
     ∀ (e : ExprVal),
       problem_spec_nonzero e (implementation_nonzero e) := by
   intro e
-  rfl
+  obtain ⟨l, m⟩ := e
+  cases l <;> cases m <;> first | rfl | decide | simp_all [implementation_nonzero, problem_spec_nonzero]
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
The truthiness (nonzero) test of an element of a symbolic-expression coefficient
domain.

Such an element wraps a symbolic value. Deciding whether the element is "zero"
(falsy) or "nonzero" (truthy) must reflect the *mathematical* value of that
expression, not merely its written form: an expression that evaluates to the
additive identity counts as zero even when it is written as a large, non-trivial
combination of terms that does not literally reduce to the constant `0` on the
surface. Only when the value is definitely mathematically zero is the element
falsy; in every other case (definitely nonzero, or value not determined to be
zero) the element is truthy.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the desired behavior is a
-- direct function of the two zero-observations carried by the input element
-- (its syntactic form and its determined mathematical value), both modeled
-- explicitly below.
-- axioms-end

-- pure-start
/-- The relevant observable state of a symbolic-expression coefficient, for the
purpose of the nonzero test.

`isLiteralZero` records whether the element's value is *syntactically* the
additive identity (its representation is literally the constant `0`).
`isMathZero` records whether the element's value is *determined to be
mathematically* the additive identity (it evaluates to zero, regardless of how
it is written). A value that is written non-trivially yet evaluates to zero has
`isLiteralZero = false` and `isMathZero = true`; a value whose vanishing is not
determined has `isMathZero = false`. -/
structure ExprVal where
  isLiteralZero : Bool
  isMathZero : Bool
-- pure-end

-- post-conditions-start
/-- The element is nonzero (truthy) exactly when its value is **not** determined
to be mathematically zero. The syntactic form is irrelevant to the result. -/
def problem_spec_nonzero (e : ExprVal) (result : Bool) : Prop :=
  result = !e.isMathZero
-- post-conditions-end

-- impl-start
def implementation_nonzero (e : ExprVal) : Bool := Id.run do
  return !e.isMathZero
-- impl-end

-- proof-start
theorem correct_nonzero :
    ∀ (e : ExprVal),
      problem_spec_nonzero e (implementation_nonzero e) := by
  intro e
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_nonzero e result := (result = !e.isMathZero) is a TOTAL FUNCTIONAL postcondition — it pins the output uniquely for every input e, and correct_nonzero quantifies over ALL e:ExprVal with NO precondition. Therefore any impl that closes the proof MUST equal !e.isMathZero pointwise on all 4 flag combinations. This is what makes the spec robust against verify⇏correct.

ATTACKS (all same_spec=True vs Solution.lean, verified via markers.same_spec; positive control pos_control.lean = gold impl verbatim VERIFIES exit 0):
- atk_1 (prepatch bug / partial-domain: return !e.isLiteralZero): lean_verify EXIT 1 (goal False at case true.false / different combos). Does NOT verify. Reproduces the documented prepatch bug.
- atk_2 (ungrounded-oracle constant: return true): EXIT 1 (False at true.true). Does NOT verify.
- atk_3 (boundary: !isMathZero || isLiteralZero): EXIT 1 (False at true.true). Does NOT verify.
- atk_4 (boundary: !isMathZero && !isLiteralZero): EXIT 1 (False at true.false). Does NOT verify.
- atk_5 (control-flow-effect echo: Id.run mutable var + if/else, computes !isMathZero): VERIFIES EXIT 0, #print axioms = 'does not depend on any axioms' (clean).
- atk_6 (ungrounded-oracle echo: reads isLiteralZero then discards, if isMathZero then false else true): VERIFIES EXIT 0, clean axioms.
- atk_7 (partial-domain: !(isMathZero && !isLiteralZero)): EXIT 1 (False at true.true). Does NOT verify.

MANDATORY RESOLVE OF VERIFYING ATTACKS (protocol step 2): atk_5 and atk_6 are the only two same-spec impls whose correct_nonzero closes with clean axioms. Both are gold-EQUIVALENT echoes (each computes not(f.ex.is_zero is True) = not f.ex.is_zero on every input, just via extra control flow / a discarded read). Materialized faithful refined patches and ran the OFFICIAL harness run_resolve:
  cmd: python -c 'from swebench_unified.harness import run_resolve; run_resolve("sympy__sympy-20428", <patch>, timeout=1800)'
  - GOLD control: resolved=True, completed=True (harness environment validated).
  - atk_5 patch (patch_atk5.diff): resolved=True, completed=True. FAIL_TO_PASS test_issue_20427 success; all PASS_TO_PASS success; 0 failures.
  - atk_6 patch (patch_atk6.diff): resolved=True, completed=True. FAIL_TO_PASS test_issue_20427 success; all PASS_TO_PASS success; 0 failures.
Both verifying attacks RESOLVE => verify⇒correct holds for every verifying candidate found. No break.

REFINEMENT AUDIT (refinement.md): 2 legs, no kind-3.
- Row1 `return !e.isMathZero` ↔ `return not f.ex.is_zero`: A-reference. Three-valued correspondence verified: isMathZero=true iff is_zero is True. Python not(True/False/None) = False/True/True; Lean !isMathZero with isMathZero=false covering both False and None -> true. Faithful across all 3 cases. Validated by G-CONF (conformance_check.py fuzzes True/False/None, >=1.2e5 draws, pinned SEED=20240626, catalogue includes the issue's nested-radical zero coefficient).
- Row2 Boolean result: R (bool↔Bool).
- G-AX is a legitimate skip stub: no consumed callee axiom; the zero-test is the operation the patch changes, modeled deeply per SPEC_GUIDE §0.7, not axiomatized. No A-consumed legs to break. A-reference correspondence to real callee `not f.ex.is_zero` holds.

CONCLUSION: The functional postcondition admits exactly one behavior; every same-spec impl that verifies is pointwise-equal to the gold and its faithful patch resolves (confirmed by execution for both verifying attacks). 7 attacks encoded (>=5 required), 4 wrong-impl families (partial-domain, boundary, control-flow-effect, ungrounded-oracle) covered; 5 non-verifying attacks fail-closed and 2 verifying echoes RESOLVE. verify⇒correct. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
The truthiness (nonzero) test of an element of a symbolic-expression coefficient
domain.

Such an element wraps a symbolic value. Deciding whether the element is "zero"
(falsy) or "nonzero" (truthy) must reflect the *mathematical* value of that
expression, not merely its written form: an expression that evaluates to the
additive identity counts as zero even when it is written as a large, non-trivial
combination of terms that does not literally reduce to the constant `0` on the
surface. Only when the value is definitely mathematically zero is the element
falsy; in every other case (definitely nonzero, or value not determined to be
zero) the element is truthy.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the desired behavior is a
-- direct function of the two zero-observations carried by the input element
-- (its syntactic form and its determined mathematical value), both modeled
-- explicitly below.
-- axioms-end

-- pure-start
/-- The relevant observable state of a symbolic-expression coefficient, for the
purpose of the nonzero test.

`isLiteralZero` records whether the element's value is *syntactically* the
additive identity (its representation is literally the constant `0`).
`isMathZero` records whether the element's value is *determined to be
mathematically* the additive identity (it evaluates to zero, regardless of how
it is written). A value that is written non-trivially yet evaluates to zero has
`isLiteralZero = false` and `isMathZero = true`; a value whose vanishing is not
determined has `isMathZero = false`. -/
structure ExprVal where
  isLiteralZero : Bool
  isMathZero : Bool
-- pure-end

-- post-conditions-start
/-- The element is nonzero (truthy) exactly when its value is **not** determined
to be mathematically zero. The syntactic form is irrelevant to the result. -/
def problem_spec_nonzero (e : ExprVal) (result : Bool) : Prop :=
  result = !e.isMathZero
-- post-conditions-end

-- impl-start
def implementation_nonzero (e : ExprVal) : Bool := Id.run do
  return !e.isMathZero
-- impl-end

-- proof-start
theorem correct_nonzero :
    ∀ (e : ExprVal),
      problem_spec_nonzero e (implementation_nonzero e) := by
  intro e
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_nonzero e result := (result = !e.isMathZero) is a TOTAL FUNCTIONAL postcondition — it pins the output uniquely for every input e, and correct_nonzero quantifies over ALL e:ExprVal with NO precondition. Therefore any impl that closes the proof MUST equal !e.isMathZero pointwise on all 4 flag combinations. This is what makes the spec robust against verify⇏correct.

ATTACKS (all same_spec=True vs Solution.lean, verified via markers.same_spec; positive control pos_control.lean = gold impl verbatim VERIFIES exit 0):
- atk_1 (prepatch bug / partial-domain: return !e.isLiteralZero): lean_verify EXIT 1 (goal False at case true.false / different combos). Does NOT verify. Reproduces the documented prepatch bug.
- atk_2 (ungrounded-oracle constant: return true): EXIT 1 (False at true.true). Does NOT verify.
- atk_3 (boundary: !isMathZero || isLiteralZero): EXIT 1 (False at true.true). Does NOT verify.
- atk_4 (boundary: !isMathZero && !isLiteralZero): EXIT 1 (False at true.false). Does NOT verify.
- atk_5 (control-flow-effect echo: Id.run mutable var + if/else, computes !isMathZero): VERIFIES EXIT 0, #print axioms = 'does not depend on any axioms' (clean).
- atk_6 (ungrounded-oracle echo: reads isLiteralZero then discards, if isMathZero then false else true): VERIFIES EXIT 0, clean axioms.
- atk_7 (partial-domain: !(isMathZero && !isLiteralZero)): EXIT 1 (False at true.true). Does NOT verify.

MANDATORY RESOLVE OF VERIFYING ATTACKS (protocol step 2): atk_5 and atk_6 are the only two same-spec impls whose correct_nonzero closes with clean axioms. Both are gold-EQUIVALENT echoes (each computes not(f.ex.is_zero is True) = not f.ex.is_zero on every input, just via extra control flow / a discarded read). Materialized faithful refined patches and ran the OFFICIAL harness run_resolve:
  cmd: python -c 'from swebench_unified.harness import run_resolve; run_resolve("sympy__sympy-20428", <patch>, timeout=1800)'
  - GOLD control: resolved=True, completed=True (harness environment validated).
  - atk_5 patch (patch_atk5.diff): resolved=True, completed=True. FAIL_TO_PASS test_issue_20427 success; all PASS_TO_PASS success; 0 failures.
  - atk_6 patch (patch_atk6.diff): resolved=True, completed=True. FAIL_TO_PASS test_issue_20427 success; all PASS_TO_PASS success; 0 failures.
Both verifying attacks RESOLVE => verify⇒correct holds for every verifying candidate found. No break.

REFINEMENT AUDIT (refinement.md): 2 legs, no kind-3.
- Row1 `return !e.isMathZero` ↔ `return not f.ex.is_zero`: A-reference. Three-valued correspondence verified: isMathZero=true iff is_zero is True. Python not(True/False/None) = False/True/True; Lean !isMathZero with isMathZero=false covering both False and None -> true. Faithful across all 3 cases. Validated by G-CONF (conformance_check.py fuzzes True/False/None, >=1.2e5 draws, pinned SEED=20240626, catalogue includes the issue's nested-radical zero coefficient).
- Row2 Boolean result: R (bool↔Bool).
- G-AX is a legitimate skip stub: no consumed callee axiom; the zero-test is the operation the patch changes, modeled deeply per SPEC_GUIDE §0.7, not axiomatized. No A-consumed legs to break. A-reference correspondence to real callee `not f.ex.is_zero` holds.

CONCLUSION: The functional postcondition admits exactly one behavior; every same-spec impl that verifies is pointwise-equal to the gold and its faithful patch resolves (confirmed by execution for both verifying attacks). 7 attacks encoded (>=5 required), 4 wrong-impl families (partial-domain, boundary, control-flow-effect, ungrounded-oracle) covered; 5 non-verifying attacks fail-closed and 2 verifying echoes RESOLVE. verify⇒correct. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attempt on the modeled function implementation_nonzero (models ExpressionDomain.Expression.__bool__ at expressiondomain.py:122-123). Independent audit findings:

1. MECHANICS: spec region byte-identical between Solution.lean and Solution_prepatch.lean via swebench_unified.markers.same_spec + LeanBackend.language => True. Solution.lean compiles under scripts/lean_verify.sh (exit 0) and `#print axioms correct_nonzero` reports 'does not depend on any axioms' (no sorryAx; proof is real, a definitional rfl).

2. BRIDGE: the model abstracts the real EX element by two flags: isMathZero = (expr.is_zero is True), isLiteralZero = bool(expr == 0). The post-patch spec/impl is `result = !isMathZero`, mirroring gold `return not f.ex.is_zero`. Verified against real base-commit source: I built a worktree at c0e8516040 (real pre-patch is `return f.ex != 0`, matching patch.diff), applied the gold edit `not f.ex.is_zero`, and ran the REAL patched callee bool(EX(expr)).

3. DIFFERENTIAL: Basic.is_zero is strictly three-valued (confirmed only {True, False, None} observed across all draws; no odd values). Python `not None == not False == True`, so both None and False map to real=True, matched by the model's None/False -> isMathZero=false -> !isMathZero=true. Tri-value table: is_zero True->False(F), is_zero False->True(T), is_zero None->True(T) — model matches all three.

4. EMPIRICAL: curated catalogue of ~50 adversarial inputs (0, literals, radicals, symbols, math-zero-non-literal, nan, +/-oo, zoo, I, pi, E, Float(0), Float(1e-300), Piecewise, assumption symbols zero=True/nonzero=True/positive/integer, exp(I*pi)+1, x/x-1, log/log-1) => 0 mismatches. Independent random fuzz of 30000 draws (sums/products/differences/quotients of a rich atom set, seed 999, distinct from the pinned G-CONF seed 20240626) => 0 mismatches, 0 odd is_zero values.

No diverging input found between the modeled function and the real repo callee. The tri-valued collapse (None->false) is faithful because __bool__ only observes `not is_zero`, which cannot distinguish None from False. The claimed FAITHFUL verdict in verdict.md is corroborated by independent testing. The spec is a total functional equality (no extensional slack), so it is neither too strong nor drifting from real behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region verified byte-identical pre/post via swebench_unified.markers.same_spec (lean tables) = True; spec_view correctly elides impl and proof.

Gold edit: expressiondomain.py __bool__ `return f.ex != 0` -> `return not f.ex.is_zero` (syntactic nonzero test -> semantic determined-zero test).

Leakage screen (spec view = docstring + ExprVal + problem_spec_nonzero + signatures + axioms block; NO impl, NO proof):
- The public problem_statement ALREADY exhibits the full bug mechanism: bad_poly.is_zero -> False vs bad_poly.as_expr().is_zero -> True (the syntactic-form vs mathematical-value contrast), the unstripped DMP([EX(0)], EX, None) vs correct DMP([], EX, None), and it explicitly names issue #20428 attributing the cause to this. The written-form-vs-determined-value distinction is therefore public, NOT hints_text-only.
- Spec docstring restates only that abstract contrast; it does NOT name the file expressiondomain.py, the method __bool__, or the call site f.ex.is_zero. Those concrete bindings live only in mapping.md / refinement.md, which are outside the spec view.
- postcondition `result = !e.isMathZero` is the correct-behavior spec itself (nonzero iff not mathematically-determined-zero) — this is the required contract, not a leak of the edit's code/path/symbol.
- Field names isLiteralZero / isMathZero are abstractions of the True/False/zero distinction already public in the statement; isMathZero collapses the three-valued is_zero, but that domain fact is also public. The presence of an unused isLiteralZero field hints only that 'a syntactic test exists', itself derivable from the public form-vs-value contrast.

No gold-edit code, file path, or symbol (expressiondomain.py, __bool__, f.ex.is_zero, `!= 0`) appears in the spec view. Lexical leakage screen passes. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
