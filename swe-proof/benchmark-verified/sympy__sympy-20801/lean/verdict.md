# P2 adversarial audit — sympy__sympy-20801

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. All 7 same-spec wrong impls fail to close correct_floatEq (exit 1, genuine rfl proof failures). No verifying attack exists, so no faithful patch could be materialized for a resolve run.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -92,6 +92,9 @@
 
 -- impl-start
 def implementation_floatEq (inp : EqInput) : Bool := Id.run do
+  -- prepatch bug: zero clause consulted FIRST
+  if inp.selfIsZero then
+    return inp.otherIsFalsy
   if inp.otherIsBoolean then
     return false
   if inp.otherIsNumberSymbol then
@@ -104,8 +107,6 @@
     return inp.rationalEq
   if inp.otherIsNumber then
     return inp.numberMpfEq
-  if inp.selfIsZero then
-    return inp.otherIsFalsy
   return false
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -92,20 +92,7 @@
 
 -- impl-start
 def implementation_floatEq (inp : EqInput) : Bool := Id.run do
-  if inp.otherIsBoolean then
-    return false
-  if inp.otherIsNumberSymbol then
-    if inp.otherIsIrrational then
-      return false
-    return inp.numberSymbolEq
-  if inp.otherIsFloat then
-    return inp.mpfEq
-  if inp.otherIsRational then
-    return inp.rationalEq
-  if inp.otherIsNumber then
-    return inp.numberMpfEq
-  if inp.selfIsZero then
-    return inp.otherIsFalsy
+  -- ungrounded: always false, ignores all dispatch
   return false
 -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -95,8 +95,7 @@
   if inp.otherIsBoolean then
     return false
   if inp.otherIsNumberSymbol then
-    if inp.otherIsIrrational then
-      return false
+    -- boundary: irrational sub-branch dropped
     return inp.numberSymbolEq
   if inp.otherIsFloat then
     return inp.mpfEq
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -98,10 +98,11 @@
     if inp.otherIsIrrational then
       return false
     return inp.numberSymbolEq
+  -- control-flow: Rational checked before Float
+  if inp.otherIsRational then
+    return inp.rationalEq
   if inp.otherIsFloat then
     return inp.mpfEq
-  if inp.otherIsRational then
-    return inp.rationalEq
   if inp.otherIsNumber then
     return inp.numberMpfEq
   if inp.selfIsZero then
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -106,7 +106,8 @@
     return inp.numberMpfEq
   if inp.selfIsZero then
     return inp.otherIsFalsy
-  return false
+  -- boundary: terminal fallthrough returns true instead of false
+  return true
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -93,7 +93,8 @@
 -- impl-start
 def implementation_floatEq (inp : EqInput) : Bool := Id.run do
   if inp.otherIsBoolean then
-    return false
+    -- ungrounded-oracle echo: Boolean defers to falsy fallback
+    return inp.otherIsFalsy
   if inp.otherIsNumberSymbol then
     if inp.otherIsIrrational then
       return false
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -103,7 +103,8 @@
   if inp.otherIsRational then
     return inp.rationalEq
   if inp.otherIsNumber then
-    return inp.numberMpfEq
+    -- wrong carried observation: uses mpfEq instead of numberMpfEq
+    return inp.mpfEq
   if inp.selfIsZero then
     return inp.otherIsFalsy
   return false
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Equality of a floating-point value against another (already-normalised) symbolic
operand.

A float decides equality by dispatching on the *kind* of the operand. The
operand has already been brought into the symbolic domain (operands that cannot
be brought in at all are outside the scope of this routine). The decision is:

* a logic boolean operand is never equal to a float;
* a named numeric-constant operand: an irrational one is never equal; a rational
  one defers to that constant's own equality with the float;
* a float operand: equal exactly when the two share the same exact value;
* a rational operand: defers to the rational's own equality with the float;
* any other numeric operand: equal when the two agree once compared at a shared
  precision;
* for every remaining (non-numeric) operand, a *zero* float is equal precisely
  to those operands that are themselves empty/zero-like, and a non-zero float is
  never equal.

The intended guarantee is that the kind-based decision above is consulted in
full for every numeric and boolean operand, and the zero-float "empty-like"
fallback applies ONLY to the operands that fall through every numeric and
boolean case. In particular a zero float and a logic boolean are decided by the
boolean rule (never equal), giving a symmetric result.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The dispatch is
-- modeled structurally over the observable kind-flags of the operand together
-- with the boolean outcomes of the unchanged delegated comparisons (a named
-- constant's own equality, a rational's own equality, the shared-precision
-- numeric comparison) and whether the float / operand are zero-like; these enter
-- as plain data, so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- The observations of the float `self` and the (already-normalised) operand
that the equality decision reads.

* `selfIsZero` — the float value is zero;
* `otherIsBoolean` — the operand is a logic boolean;
* `otherIsNumberSymbol` — the operand is a named numeric constant;
* `otherIsIrrational` — that constant is irrational;
* `numberSymbolEq` — the result of the rational-constant's own equality with the
  float;
* `otherIsFloat` — the operand is itself a float;
* `mpfEq` — the two floats hold the same exact value;
* `otherIsRational` — the operand is a rational;
* `rationalEq` — the result of the rational's own equality with the float;
* `otherIsNumber` — the operand is some other numeric value;
* `numberMpfEq` — the two agree once compared at a shared precision;
* `otherIsFalsy` — the operand is itself empty/zero-like. -/
structure EqInput where
  selfIsZero : Bool
  otherIsBoolean : Bool
  otherIsNumberSymbol : Bool
  otherIsIrrational : Bool
  numberSymbolEq : Bool
  otherIsFloat : Bool
  mpfEq : Bool
  otherIsRational : Bool
  rationalEq : Bool
  otherIsNumber : Bool
  numberMpfEq : Bool
  otherIsFalsy : Bool

/-- The boolean a float returns for equality with the operand, by the rule
described above: the kind dispatch is consulted in full, and the zero-float
empty-like fallback applies only to operands that match none of the boolean or
numeric kinds. -/
def floatEqResult (inp : EqInput) : Bool :=
  if inp.otherIsBoolean then false
  else if inp.otherIsNumberSymbol then
    (if inp.otherIsIrrational then false else inp.numberSymbolEq)
  else if inp.otherIsFloat then inp.mpfEq
  else if inp.otherIsRational then inp.rationalEq
  else if inp.otherIsNumber then inp.numberMpfEq
  else if inp.selfIsZero then inp.otherIsFalsy
  else false
-- pure-end

-- post-conditions-start
/-- The returned boolean is exactly the value assigned by the kind dispatch. A
zero float compared to a logic boolean is decided by the boolean rule (never
equal), not by the empty-like fallback. -/
def problem_spec_floatEq (inp : EqInput) (result : Bool) : Prop :=
  result = floatEqResult inp
-- post-conditions-end

-- impl-start
def implementation_floatEq (inp : EqInput) : Bool := Id.run do
  if inp.otherIsBoolean then
    return false
  if inp.otherIsNumberSymbol then
    if inp.otherIsIrrational then
      return false
    return inp.numberSymbolEq
  if inp.otherIsFloat then
    return inp.mpfEq
  if inp.otherIsRational then
    return inp.rationalEq
  if inp.otherIsNumber then
    return inp.numberMpfEq
  if inp.selfIsZero then
    return inp.otherIsFalsy
  return false
-- impl-end

-- proof-start
theorem correct_floatEq :
    ∀ (inp : EqInput),
      problem_spec_floatEq inp (implementation_floatEq inp) := by
  intro inp
  unfold problem_spec_floatEq implementation_floatEq floatEqResult
  simp only [Id.run]
  by_cases h1 : inp.otherIsBoolean = true <;>
    by_cases h2 : inp.otherIsNumberSymbol = true <;>
    by_cases h3 : inp.otherIsIrrational = true <;>
    by_cases h4 : inp.otherIsFloat = true <;>
    by_cases h5 : inp.otherIsRational = true <;>
    by_cases h6 : inp.otherIsNumber = true <;>
    by_cases h7 : inp.selfIsZero = true <;>
    simp_all <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Bundle sympy__sympy-20801 (lean). Spec is a TIGHT total functional equality: problem_spec_floatEq inp result := result = floatEqResult inp, where floatEqResult is a total EqInput->Bool function pinning all 12 observable fields (selfIsZero, otherIsBoolean, otherIsNumberSymbol, otherIsIrrational, numberSymbolEq, otherIsFloat, mpfEq, otherIsRational, rationalEq, otherIsNumber, numberMpfEq, otherIsFalsy). No existential, no free output component, no partiality -> any impl closing correct_floatEq is pointwise-equal to floatEqResult, hence resolving. 

SAME_SPEC: all 8 files (7 attacks + pos) confirmed same_spec=True via swebench_unified.markers.same_spec (spec regions byte-identical; only impl+proof edited).

### ATTACKS (project root; cmd: bash scripts/lean_verify.sh <file>):
- atk_1 PREPATCH BUG (zero clause consulted first): exit 1, rfl fails at line 127 on selfIsZero branches. Confirms spec distinguishes pre/post patch (mutation value preserved).
- atk_2 ungrounded (always return false): exit 1, rfl fails line 113.
- atk_3 boundary (drop irrational sub-branch, NumberSymbol always -> numberSymbolEq): exit 1.
- atk_4 control-flow (Rational checked before Float): exit 1, rfl fails line 127.
- atk_5 boundary (terminal fallthrough returns true not false): exit 1.
- atk_6 ungrounded-oracle echo (Boolean returns otherIsFalsy not false): exit 1.
- atk_7 wrong carried-observation (Number branch uses mpfEq not numberMpfEq): exit 1.
All 7 are behaviorally distinct wrong impls; ALL fail to verify with genuine rfl proof failures on their divergent branches. NONE closes with clean axioms, so NO resolve run is required by the protocol (step 2 triggers only for a wrong impl whose proof closes).

POSITIVE CONTROL pos.lean (= gold impl): exit 0. #print axioms correct_floatEq -> [propext, Quot.sound] (clean, no sorryAx).

REFINEMENT.md AUDIT: 7 R legs + 1 I leg (the relocation, op '—'). Axioms region is EMPTY (byte-identical across all files). No A-consumed / A-reference legs exist -> A-leg correspondence audit vacuously holds; no kind-3 legs. The carried sub-results (numberSymbolEq/rationalEq/numberMpfEq/mpfEq/otherIsFalsy) are outcomes of UNCHANGED upstream delegations entering as plain data (carried-observation R refinement), orthogonal to the ordering fix. This matches mapping.md's field<->Python-expression bijection.

CONCLUSION: verify => correct holds. The tight functional spec admits no divergent closing impl, so verify does not imply anything weaker than correct. SOUND after 7 distinct attacks, all machine-checked; no resolve run needed since none verified.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. All 7 same-spec wrong impls fail to close correct_floatEq (exit 1, genuine rfl proof failures). No verifying attack exists, so no faithful patch could be materialized for a resolve run.
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

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Equality of a floating-point value against another (already-normalised) symbolic
operand.

A float decides equality by dispatching on the *kind* of the operand. The
operand has already been brought into the symbolic domain (operands that cannot
be brought in at all are outside the scope of this routine). The decision is:

* a logic boolean operand is never equal to a float;
* a named numeric-constant operand: an irrational one is never equal; a rational
  one defers to that constant's own equality with the float;
* a float operand: equal exactly when the two share the same exact value;
* a rational operand: defers to the rational's own equality with the float;
* any other numeric operand: equal when the two agree once compared at a shared
  precision;
* for every remaining (non-numeric) operand, a *zero* float is equal precisely
  to those operands that are themselves empty/zero-like, and a non-zero float is
  never equal.

The intended guarantee is that the kind-based decision above is consulted in
full for every numeric and boolean operand, and the zero-float "empty-like"
fallback applies ONLY to the operands that fall through every numeric and
boolean case. In particular a zero float and a logic boolean are decided by the
boolean rule (never equal), giving a symmetric result.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The dispatch is
-- modeled structurally over the observable kind-flags of the operand together
-- with the boolean outcomes of the unchanged delegated comparisons (a named
-- constant's own equality, a rational's own equality, the shared-precision
-- numeric comparison) and whether the float / operand are zero-like; these enter
-- as plain data, so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- The observations of the float `self` and the (already-normalised) operand
that the equality decision reads.

* `selfIsZero` — the float value is zero;
* `otherIsBoolean` — the operand is a logic boolean;
* `otherIsNumberSymbol` — the operand is a named numeric constant;
* `otherIsIrrational` — that constant is irrational;
* `numberSymbolEq` — the result of the rational-constant's own equality with the
  float;
* `otherIsFloat` — the operand is itself a float;
* `mpfEq` — the two floats hold the same exact value;
* `otherIsRational` — the operand is a rational;
* `rationalEq` — the result of the rational's own equality with the float;
* `otherIsNumber` — the operand is some other numeric value;
* `numberMpfEq` — the two agree once compared at a shared precision;
* `otherIsFalsy` — the operand is itself empty/zero-like. -/
structure EqInput where
  selfIsZero : Bool
  otherIsBoolean : Bool
  otherIsNumberSymbol : Bool
  otherIsIrrational : Bool
  numberSymbolEq : Bool
  otherIsFloat : Bool
  mpfEq : Bool
  otherIsRational : Bool
  rationalEq : Bool
  otherIsNumber : Bool
  numberMpfEq : Bool
  otherIsFalsy : Bool

/-- The boolean a float returns for equality with the operand, by the rule
described above: the kind dispatch is consulted in full, and the zero-float
empty-like fallback applies only to operands that match none of the boolean or
numeric kinds. -/
def floatEqResult (inp : EqInput) : Bool :=
  if inp.otherIsBoolean then false
  else if inp.otherIsNumberSymbol then
    (if inp.otherIsIrrational then false else inp.numberSymbolEq)
  else if inp.otherIsFloat then inp.mpfEq
  else if inp.otherIsRational then inp.rationalEq
  else if inp.otherIsNumber then inp.numberMpfEq
  else if inp.selfIsZero then inp.otherIsFalsy
  else false
-- pure-end

-- post-conditions-start
/-- The returned boolean is exactly the value assigned by the kind dispatch. A
zero float compared to a logic boolean is decided by the boolean rule (never
equal), not by the empty-like fallback. -/
def problem_spec_floatEq (inp : EqInput) (result : Bool) : Prop :=
  result = floatEqResult inp
-- post-conditions-end

-- impl-start
def implementation_floatEq (inp : EqInput) : Bool := Id.run do
  if inp.otherIsBoolean then
    return false
  if inp.otherIsNumberSymbol then
    if inp.otherIsIrrational then
      return false
    return inp.numberSymbolEq
  if inp.otherIsFloat then
    return inp.mpfEq
  if inp.otherIsRational then
    return inp.rationalEq
  if inp.otherIsNumber then
    return inp.numberMpfEq
  if inp.selfIsZero then
    return inp.otherIsFalsy
  return false
-- impl-end

-- proof-start
theorem correct_floatEq :
    ∀ (inp : EqInput),
      problem_spec_floatEq inp (implementation_floatEq inp) := by
  intro inp
  unfold problem_spec_floatEq implementation_floatEq floatEqResult
  simp only [Id.run]
  by_cases h1 : inp.otherIsBoolean = true <;>
    by_cases h2 : inp.otherIsNumberSymbol = true <;>
    by_cases h3 : inp.otherIsIrrational = true <;>
    by_cases h4 : inp.otherIsFloat = true <;>
    by_cases h5 : inp.otherIsRational = true <;>
    by_cases h6 : inp.otherIsNumber = true <;>
    by_cases h7 : inp.selfIsZero = true <;>
    simp_all <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Bundle sympy__sympy-20801 (lean). Spec is a TIGHT total functional equality: problem_spec_floatEq inp result := result = floatEqResult inp, where floatEqResult is a total EqInput->Bool function pinning all 12 observable fields (selfIsZero, otherIsBoolean, otherIsNumberSymbol, otherIsIrrational, numberSymbolEq, otherIsFloat, mpfEq, otherIsRational, rationalEq, otherIsNumber, numberMpfEq, otherIsFalsy). No existential, no free output component, no partiality -> any impl closing correct_floatEq is pointwise-equal to floatEqResult, hence resolving. 

SAME_SPEC: all 8 files (7 attacks + pos) confirmed same_spec=True via swebench_unified.markers.same_spec (spec regions byte-identical; only impl+proof edited).

### ATTACKS (project root; cmd: bash scripts/lean_verify.sh <file>):
- atk_1 PREPATCH BUG (zero clause consulted first): exit 1, rfl fails at line 127 on selfIsZero branches. Confirms spec distinguishes pre/post patch (mutation value preserved).
- atk_2 ungrounded (always return false): exit 1, rfl fails line 113.
- atk_3 boundary (drop irrational sub-branch, NumberSymbol always -> numberSymbolEq): exit 1.
- atk_4 control-flow (Rational checked before Float): exit 1, rfl fails line 127.
- atk_5 boundary (terminal fallthrough returns true not false): exit 1.
- atk_6 ungrounded-oracle echo (Boolean returns otherIsFalsy not false): exit 1.
- atk_7 wrong carried-observation (Number branch uses mpfEq not numberMpfEq): exit 1.
All 7 are behaviorally distinct wrong impls; ALL fail to verify with genuine rfl proof failures on their divergent branches. NONE closes with clean axioms, so NO resolve run is required by the protocol (step 2 triggers only for a wrong impl whose proof closes).

POSITIVE CONTROL pos.lean (= gold impl): exit 0. #print axioms correct_floatEq -> [propext, Quot.sound] (clean, no sorryAx).

REFINEMENT.md AUDIT: 7 R legs + 1 I leg (the relocation, op '—'). Axioms region is EMPTY (byte-identical across all files). No A-consumed / A-reference legs exist -> A-leg correspondence audit vacuously holds; no kind-3 legs. The carried sub-results (numberSymbolEq/rationalEq/numberMpfEq/mpfEq/otherIsFalsy) are outcomes of UNCHANGED upstream delegations entering as plain data (carried-observation R refinement), orthogonal to the ordering fix. This matches mapping.md's field<->Python-expression bijection.

CONCLUSION: verify => correct holds. The tight functional spec admits no divergent closing impl, so verify does not imply anything weaker than correct. SOUND after 7 distinct attacks, all machine-checked; no resolve run needed since none verified.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-drift) check for sympy__sympy-20801 Lean bundle. Modeled routine: the boolean dispatch inside Float.__eq__ (sympy/core/numbers.py:1385-1411) AFTER the operand is successfully sympified. The bundle models POST-PATCH behavior (zero-operand clause relocated to the END of the kind dispatch); refinement.md/mapping.md confirm this and the worktree is in the patched state (verified: `if not self: return not other` sits just before terminal `return False`).

Checks performed:
1. same_spec(Solution.lean, Solution_prepatch.lean) = True with lean LanguageTables — spec region byte-identical; the patch only reorders the impl clause. spec_view confirms floatEqResult's branch order matches the post-patch Python (Boolean -> NumberSymbol(irrational?/delegate) -> Float(mpfEq) -> Rational(delegate) -> Number(mpf_eq) -> selfIsZero(falsy) -> False).
2. Differential test against the REAL repo (not just the self-consistent G-CONF shadow, which only diffs an in-process replica): derived all 12 observables from live sympy objects and compared floatEqResult to real Float.__eq__ across ~20 operand kinds (S.true/S.false, pi, E, GoldenRatio, Catalan, EulerGamma, Rationals, Integers, Floats at differing prec, oo, zoo, nan, I, sqrt(2), Symbol) x 5 float selves (incl. Float(0.0)). 0 mismatches. In particular the F2P case Float(0.0)==S.false yields False in both.
3. Fuzzy-predicate fidelity: Catalan.is_irrational and EulerGamma.is_irrational are None; the real code treats None as falsy (falls through to the delegated __eq__), and the model's bool(None)=False plus captured numberSymbolEq reproduces the real False. No divergence.
4. Totality of modeled branches: delegated __eq__ (Rational + NumberSymbol branches) and _as_mpf_val+mpf_eq always return a bool (never NotImplemented / never raised) across fuzzing, so modeling result : Bool as total within the domain is faithful. The only non-bool return (NotImplemented on SympifyError) is explicitly and legitimately scoped out as a documented precondition — not drift.
5. Lean: scripts/lean_verify.sh exit 0; #print axioms correct_floatEq -> [propext, Quot.sound] only (standard axioms, no sorryAx) — genuine proof.

Conclusion: the spec is neither too strong nor drifting; floatEqResult agrees with the real callee on every tested input. No diverging input found. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Independently verified. Mechanical screen leakage.screen(lean) over the actual spec_view() projection passes with zero hard_failures (no diff markers, no reproduced gold-patch line, no patched file/module path numbers.py, no spec-view identifier or comment naming a patched repo symbol, no bug/fix narration). Bundle is NOT relaxed (relaxed_leakage=None, no RELAXED_LEAKAGE.md), so this is a genuine clean pass, not a panel_3 deferral.

Gold edit: relocate the leading `if not self: return not other` clause to AFTER the full type dispatch, so a zero float vs a logic Boolean is decided by the Boolean->False rule (fixes asymmetric S(0.0)==S.false). The public problem_statement already exhibits the entire target: the S(0.0)==S.false=True vs S.false==S(0.0)=False asymmetry and the S(0)==S.false=False reference behavior. The spec view only encodes the CORRECT dispatch semantics abstractly (Boolean first -> false; zero-float empty-like fallback consulted last, only for operands falling through every numeric/boolean case) — the necessary correctness contract any faithful spec must encode, derivable from the public statement, not a disclosure of which lines moved.

Decisive: same_spec(Solution, Solution_prepatch)=True — the consumer spec view is byte-identical for the gold and buggy variants, so the spec view by itself cannot distinguish which impl is gold. spec_view here = imports + abstract domain docstring + empty axioms + pure (EqInput/floatEqResult) + post-conditions; impl and proof elided. The relocation/delete/reorder narrative lives ONLY in refinement.md and mapping.md, which are not part of the spec view. No mention of numbers.py, __eq__ edit, issue number, test_zero_not_false, or 'not self'/'not other' as diff mechanics. hints_text is empty, so no hint-echo concern. NO-LEAKAGE beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
