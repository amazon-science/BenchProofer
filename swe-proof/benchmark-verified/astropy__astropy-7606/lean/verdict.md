# P2 adversarial audit — astropy__astropy-7606

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
None found. No same-spec wrong implementation admits a closing proof, so there is no candidate to materialize/resolve.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -89,7 +89,7 @@
     (selfName : String) (po : ParseOutcome) : Except UnitError EqResult := Id.run do
   match po with
   | .raised =>
-      return .ok .notApplicable
+      return .error .parseError
   | .parsed isUnrecognized otherName =>
       return .ok (if isUnrecognized && selfName == otherName then .isTrue else .isFalse)
 -- impl-end
@@ -101,5 +101,9 @@
         (implementation_unrecognizedUnitEq selfName po) := by
   intro selfName po
   unfold problem_spec_unrecognizedUnitEq implementation_unrecognizedUnitEq eqResult
-  cases po <;> rfl
+  cases po <;> first
+    | rfl
+    | (simp_all) <;> rfl
+    | simp_all
+    | (split <;> simp_all)
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -89,7 +89,7 @@
     (selfName : String) (po : ParseOutcome) : Except UnitError EqResult := Id.run do
   match po with
   | .raised =>
-      return .ok .notApplicable
+      return .ok .isFalse
   | .parsed isUnrecognized otherName =>
       return .ok (if isUnrecognized && selfName == otherName then .isTrue else .isFalse)
 -- impl-end
@@ -101,5 +101,9 @@
         (implementation_unrecognizedUnitEq selfName po) := by
   intro selfName po
   unfold problem_spec_unrecognizedUnitEq implementation_unrecognizedUnitEq eqResult
-  cases po <;> rfl
+  cases po <;> first
+    | rfl
+    | (simp_all) <;> rfl
+    | simp_all
+    | (split <;> simp_all)
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -91,7 +91,7 @@
   | .raised =>
       return .ok .notApplicable
   | .parsed isUnrecognized otherName =>
-      return .ok (if isUnrecognized && selfName == otherName then .isTrue else .isFalse)
+      return .ok (if isUnrecognized && selfName == otherName then .isFalse else .isTrue)
 -- impl-end
 
 -- proof-start
@@ -101,5 +101,9 @@
         (implementation_unrecognizedUnitEq selfName po) := by
   intro selfName po
   unfold problem_spec_unrecognizedUnitEq implementation_unrecognizedUnitEq eqResult
-  cases po <;> rfl
+  cases po <;> first
+    | rfl
+    | (simp_all) <;> rfl
+    | simp_all
+    | (split <;> simp_all)
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -90,8 +90,8 @@
   match po with
   | .raised =>
       return .ok .notApplicable
-  | .parsed isUnrecognized otherName =>
-      return .ok (if isUnrecognized && selfName == otherName then .isTrue else .isFalse)
+  | .parsed isUnrecognized _otherName =>
+      return .ok (if isUnrecognized then .isTrue else .isFalse)
 -- impl-end
 
 -- proof-start
@@ -101,5 +101,9 @@
         (implementation_unrecognizedUnitEq selfName po) := by
   intro selfName po
   unfold problem_spec_unrecognizedUnitEq implementation_unrecognizedUnitEq eqResult
-  cases po <;> rfl
+  cases po <;> first
+    | rfl
+    | (simp_all) <;> rfl
+    | simp_all
+    | (split <;> simp_all)
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -91,7 +91,7 @@
   | .raised =>
       return .ok .notApplicable
   | .parsed isUnrecognized otherName =>
-      return .ok (if isUnrecognized && selfName == otherName then .isTrue else .isFalse)
+      return .ok (if isUnrecognized || selfName == otherName then .isTrue else .isFalse)
 -- impl-end
 
 -- proof-start
@@ -101,5 +101,9 @@
         (implementation_unrecognizedUnitEq selfName po) := by
   intro selfName po
   unfold problem_spec_unrecognizedUnitEq implementation_unrecognizedUnitEq eqResult
-  cases po <;> rfl
+  cases po <;> first
+    | rfl
+    | (simp_all) <;> rfl
+    | simp_all
+    | (split <;> simp_all)
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -90,8 +90,8 @@
   match po with
   | .raised =>
       return .ok .notApplicable
-  | .parsed isUnrecognized otherName =>
-      return .ok (if isUnrecognized && selfName == otherName then .isTrue else .isFalse)
+  | .parsed _isUnrecognized _otherName =>
+      return .ok .notApplicable
 -- impl-end
 
 -- proof-start
@@ -101,5 +101,9 @@
         (implementation_unrecognizedUnitEq selfName po) := by
   intro selfName po
   unfold problem_spec_unrecognizedUnitEq implementation_unrecognizedUnitEq eqResult
-  cases po <;> rfl
+  cases po <;> first
+    | rfl
+    | (simp_all) <;> rfl
+    | simp_all
+    | (split <;> simp_all)
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -90,8 +90,8 @@
   match po with
   | .raised =>
       return .ok .notApplicable
-  | .parsed isUnrecognized otherName =>
-      return .ok (if isUnrecognized && selfName == otherName then .isTrue else .isFalse)
+  | .parsed _isUnrecognized otherName =>
+      return .ok (if selfName == otherName then .isTrue else .isFalse)
 -- impl-end
 
 -- proof-start
@@ -101,5 +101,9 @@
         (implementation_unrecognizedUnitEq selfName po) := by
   intro selfName po
   unfold problem_spec_unrecognizedUnitEq implementation_unrecognizedUnitEq eqResult
-  cases po <;> rfl
+  cases po <;> first
+    | rfl
+    | (simp_all) <;> rfl
+    | simp_all
+    | (split <;> simp_all)
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Equality of an unrecognised unit against an arbitrary operand.

An unrecognised unit carries a name string. Comparing it for equality with some
other operand proceeds by first trying to interpret that operand as a unit, in a
lenient mode:

* some operands cannot be interpreted as a unit at all (for example the null
  object, or a value of an unrelated type) — the interpretation step fails for
  these;
* otherwise the operand yields a unit value, which either is itself an
  unrecognised unit (carrying its own name string) or is some recognised unit.

The desired result of the comparison is three-valued:

  * if the operand cannot be interpreted as a unit, the comparison yields the
    "comparison not applicable" sentinel — it never propagates the interpretation
    failure to the caller;
  * if the operand yields an unrecognised unit whose name equals this unit's name,
    the comparison is true;
  * in every other case (a recognised unit, or an unrecognised unit with a
    different name), the comparison is false.

In particular, an operand that cannot be interpreted as a unit must produce the
sentinel result, not an escaping error.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The lenient
-- interpretation step is an unchanged upstream operation; its observable result
-- (interpretation failed, or a unit value tagged by whether it is unrecognised
-- and by its name) enters the decision as plain data (`ParseOutcome`). The
-- comparison rule itself is modeled structurally, so no `opaque`/`axiom` callee
-- contract is needed.
-- axioms-end

-- pure-start
/-- An error that can escape the comparison. `parseError` stands for the
interpretation step failing and that failure reaching the caller. -/
inductive UnitError where
  | parseError
deriving DecidableEq, Repr

/-- The three-valued result of the comparison: true, false, or the
"comparison not applicable" sentinel. -/
inductive EqResult where
  | isTrue
  | isFalse
  | notApplicable
deriving DecidableEq, Repr

/-- The observable result of interpreting the other operand as a unit (lenient
mode):

* `raised` — the operand could not be interpreted as a unit;
* `parsed isUnrecognized otherName` — the operand yielded a unit value;
  `isUnrecognized` records whether that value is itself an unrecognised unit, and
  `otherName` is its name string. -/
inductive ParseOutcome where
  | raised
  | parsed (isUnrecognized : Bool) (otherName : String)
deriving DecidableEq, Repr

/-- The desired comparison result for an unrecognised unit named `selfName`
against an operand whose interpretation outcome is `po`. -/
def eqResult (selfName : String) (po : ParseOutcome) : Except UnitError EqResult :=
  match po with
  | .raised => .ok .notApplicable
  | .parsed isUnrecognized otherName =>
      .ok (if isUnrecognized && selfName == otherName then .isTrue else .isFalse)
-- pure-end

-- post-conditions-start
/-- The comparison result is exactly the value assigned by the rule: an
uninterpretable operand yields the not-applicable sentinel (never an escaping
error); a parsed operand yields true iff it is an unrecognised unit with a
matching name, else false. -/
def problem_spec_unrecognizedUnitEq
    (selfName : String) (po : ParseOutcome)
    (result : Except UnitError EqResult) : Prop :=
  result = eqResult selfName po
-- post-conditions-end

-- impl-start
def implementation_unrecognizedUnitEq
    (selfName : String) (po : ParseOutcome) : Except UnitError EqResult := Id.run do
  match po with
  | .raised => return .ok .notApplicable
  | .parsed isUnrecognized otherName =>
      match isUnrecognized, selfName == otherName with
      | true, true => return .ok .isTrue
      | _, _ => return .ok .isFalse
-- impl-end

-- proof-start
theorem correct_unrecognizedUnitEq :
    ∀ (selfName : String) (po : ParseOutcome),
      problem_spec_unrecognizedUnitEq selfName po
        (implementation_unrecognizedUnitEq selfName po) := by
  intro selfName po
  unfold problem_spec_unrecognizedUnitEq implementation_unrecognizedUnitEq eqResult
  cases po with
  | raised => rfl
  | parsed isUnrecognized otherName =>
      cases isUnrecognized <;>
        cases h : (selfName == otherName) <;>
        simp_all [Id.run, pure, Except.pure]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: postcondition problem_spec_unrecognizedUnitEq is a TOTAL EQUALITY `result = eqResult selfName po` that fully pins `result` for every (selfName, po); nothing is left free. Axioms region is EMPTY -> NO A-legs (R/I legs are G-CONF's domain per instructions, but here all 3 refinement legs are R and validated in-container). Consequently any implementation whose correct_* closes must be extensionally equal to eqResult, i.e. the gold three-valued decision.

PROTOCOL: same_spec confirmed True for ALL 8 files (atk_1..7 + pos_control) — spec/axioms/pure/pre/post regions byte-identical to Solution.lean; only the impl region (and proof) edited. Each wrong impl was given an ADVERSARIALLY STRONG proof attempt: `cases po <;> first | rfl | (simp_all)<;>rfl | simp_all | (split<;>simp_all)`.

CMD: `cd && bash scripts/lean_verify.sh <path>` (run concurrently, <=4 at a time).

### ATTACKS (all distinct wrong impls, all FAIL with genuine `unsolved goals` at proof line 101, exit=1):
- atk_1 control-flow-effect / PREPATCH BUG: `.raised => .error .parseError` (escaping error instead of sentinel). exit=1, unsolved goal `case raised |- False`. This reproduces the reported defect (prepatch_reproduced=true; matches Solution_prepatch.lean which ships this body with a `sorry`).
- atk_2 wrong-sentinel/boundary: `.raised => .ok .isFalse`. exit=1 unsolved goals.
- atk_3 boundary: swapped truth values on parsed branch (isFalse<->isTrue). exit=1 unsolved goals.
- atk_4 partial-domain: parsed branch drops the name check (`if isUnrecognized`). exit=1 unsolved goals.
- atk_5 control-flow-effect: `||` instead of `&&`. exit=1 unsolved goals.
- atk_6 ungrounded/collapse: parsed branch always `.notApplicable`. exit=1 unsolved goals.
- atk_7 partial-domain: parsed branch drops isUnrecognized, only name-match. exit=1 unsolved goals.

No wrong impl's proof closed => step-2 (materialize faithful refined patch + run_resolve) has ZERO candidates; patches={} accordingly (no speculation — there was nothing to resolve).

POSITIVE CONTROL: pos_control.lean is a STRUCTURALLY DIFFERENT but pointwise-equal correct impl (nested `match isUnrecognized, selfName==otherName` instead of the gold `if ... && ...`). It VERIFIES: exit=0. `#print axioms correct_unrecognizedUnitEq` => `[propext, Classical.choice, Quot.sound]` (clean Mathlib axioms, NO sorryAx/no user axioms). This confirms the total-equality postcondition admits exactly the gold behavior and closing proofs are clean.

REFINEMENT.MD AUDIT: 3 legs, all tagged R (no A-consumed, no A-reference, no I-needing-deep-model, NO kind-3). The changed decision (.raised uninterpretable-operand -> notApplicable sentinel vs escaping error) is modeled DEEPLY/STRUCTURALLY over ParseOutcome, not axiomatized — compliant with SPEC_GUIDE §3 (no axiomatizing a deeply-modeled changed decision). The unchanged callee `Unit(other, parse_strict='silent')` is carried as grounded observation `po` and validated against reality by conformance_check.py, which drives the REAL factory + REAL post-patch UnrecognizedUnit.__eq__ in-container (SEED 7606, 120k inputs + hand-picked F2P edges). mapping.md `type(self) is UnrecognizedUnit` (no subclasses in tree) -> isUnrecognized folding is exact. Correspondence holds.

CONCLUSION: verify=>correct is upheld. >=7 distinct same-spec wrong impls (>= the 5-6 required, spanning prepatch-bug/partial-domain/boundary/control-flow-effect/ungrounded-collapse) all fail to close; positive control closes clean. SOUND.

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
None found. No same-spec wrong implementation admits a closing proof, so there is no candidate to materialize/resolve.
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
Equality of an unrecognised unit against an arbitrary operand.

An unrecognised unit carries a name string. Comparing it for equality with some
other operand proceeds by first trying to interpret that operand as a unit, in a
lenient mode:

* some operands cannot be interpreted as a unit at all (for example the null
  object, or a value of an unrelated type) — the interpretation step fails for
  these;
* otherwise the operand yields a unit value, which either is itself an
  unrecognised unit (carrying its own name string) or is some recognised unit.

The desired result of the comparison is three-valued:

  * if the operand cannot be interpreted as a unit, the comparison yields the
    "comparison not applicable" sentinel — it never propagates the interpretation
    failure to the caller;
  * if the operand yields an unrecognised unit whose name equals this unit's name,
    the comparison is true;
  * in every other case (a recognised unit, or an unrecognised unit with a
    different name), the comparison is false.

In particular, an operand that cannot be interpreted as a unit must produce the
sentinel result, not an escaping error.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The lenient
-- interpretation step is an unchanged upstream operation; its observable result
-- (interpretation failed, or a unit value tagged by whether it is unrecognised
-- and by its name) enters the decision as plain data (`ParseOutcome`). The
-- comparison rule itself is modeled structurally, so no `opaque`/`axiom` callee
-- contract is needed.
-- axioms-end

-- pure-start
/-- An error that can escape the comparison. `parseError` stands for the
interpretation step failing and that failure reaching the caller. -/
inductive UnitError where
  | parseError
deriving DecidableEq, Repr

/-- The three-valued result of the comparison: true, false, or the
"comparison not applicable" sentinel. -/
inductive EqResult where
  | isTrue
  | isFalse
  | notApplicable
deriving DecidableEq, Repr

/-- The observable result of interpreting the other operand as a unit (lenient
mode):

* `raised` — the operand could not be interpreted as a unit;
* `parsed isUnrecognized otherName` — the operand yielded a unit value;
  `isUnrecognized` records whether that value is itself an unrecognised unit, and
  `otherName` is its name string. -/
inductive ParseOutcome where
  | raised
  | parsed (isUnrecognized : Bool) (otherName : String)
deriving DecidableEq, Repr

/-- The desired comparison result for an unrecognised unit named `selfName`
against an operand whose interpretation outcome is `po`. -/
def eqResult (selfName : String) (po : ParseOutcome) : Except UnitError EqResult :=
  match po with
  | .raised => .ok .notApplicable
  | .parsed isUnrecognized otherName =>
      .ok (if isUnrecognized && selfName == otherName then .isTrue else .isFalse)
-- pure-end

-- post-conditions-start
/-- The comparison result is exactly the value assigned by the rule: an
uninterpretable operand yields the not-applicable sentinel (never an escaping
error); a parsed operand yields true iff it is an unrecognised unit with a
matching name, else false. -/
def problem_spec_unrecognizedUnitEq
    (selfName : String) (po : ParseOutcome)
    (result : Except UnitError EqResult) : Prop :=
  result = eqResult selfName po
-- post-conditions-end

-- impl-start
def implementation_unrecognizedUnitEq
    (selfName : String) (po : ParseOutcome) : Except UnitError EqResult := Id.run do
  match po with
  | .raised => return .ok .notApplicable
  | .parsed isUnrecognized otherName =>
      match isUnrecognized, selfName == otherName with
      | true, true => return .ok .isTrue
      | _, _ => return .ok .isFalse
-- impl-end

-- proof-start
theorem correct_unrecognizedUnitEq :
    ∀ (selfName : String) (po : ParseOutcome),
      problem_spec_unrecognizedUnitEq selfName po
        (implementation_unrecognizedUnitEq selfName po) := by
  intro selfName po
  unfold problem_spec_unrecognizedUnitEq implementation_unrecognizedUnitEq eqResult
  cases po with
  | raised => rfl
  | parsed isUnrecognized otherName =>
      cases isUnrecognized <;>
        cases h : (selfName == otherName) <;>
        simp_all [Id.run, pure, Except.pure]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: postcondition problem_spec_unrecognizedUnitEq is a TOTAL EQUALITY `result = eqResult selfName po` that fully pins `result` for every (selfName, po); nothing is left free. Axioms region is EMPTY -> NO A-legs (R/I legs are G-CONF's domain per instructions, but here all 3 refinement legs are R and validated in-container). Consequently any implementation whose correct_* closes must be extensionally equal to eqResult, i.e. the gold three-valued decision.

PROTOCOL: same_spec confirmed True for ALL 8 files (atk_1..7 + pos_control) — spec/axioms/pure/pre/post regions byte-identical to Solution.lean; only the impl region (and proof) edited. Each wrong impl was given an ADVERSARIALLY STRONG proof attempt: `cases po <;> first | rfl | (simp_all)<;>rfl | simp_all | (split<;>simp_all)`.

CMD: `cd && bash scripts/lean_verify.sh <path>` (run concurrently, <=4 at a time).

### ATTACKS (all distinct wrong impls, all FAIL with genuine `unsolved goals` at proof line 101, exit=1):
- atk_1 control-flow-effect / PREPATCH BUG: `.raised => .error .parseError` (escaping error instead of sentinel). exit=1, unsolved goal `case raised |- False`. This reproduces the reported defect (prepatch_reproduced=true; matches Solution_prepatch.lean which ships this body with a `sorry`).
- atk_2 wrong-sentinel/boundary: `.raised => .ok .isFalse`. exit=1 unsolved goals.
- atk_3 boundary: swapped truth values on parsed branch (isFalse<->isTrue). exit=1 unsolved goals.
- atk_4 partial-domain: parsed branch drops the name check (`if isUnrecognized`). exit=1 unsolved goals.
- atk_5 control-flow-effect: `||` instead of `&&`. exit=1 unsolved goals.
- atk_6 ungrounded/collapse: parsed branch always `.notApplicable`. exit=1 unsolved goals.
- atk_7 partial-domain: parsed branch drops isUnrecognized, only name-match. exit=1 unsolved goals.

No wrong impl's proof closed => step-2 (materialize faithful refined patch + run_resolve) has ZERO candidates; patches={} accordingly (no speculation — there was nothing to resolve).

POSITIVE CONTROL: pos_control.lean is a STRUCTURALLY DIFFERENT but pointwise-equal correct impl (nested `match isUnrecognized, selfName==otherName` instead of the gold `if ... && ...`). It VERIFIES: exit=0. `#print axioms correct_unrecognizedUnitEq` => `[propext, Classical.choice, Quot.sound]` (clean Mathlib axioms, NO sorryAx/no user axioms). This confirms the total-equality postcondition admits exactly the gold behavior and closing proofs are clean.

REFINEMENT.MD AUDIT: 3 legs, all tagged R (no A-consumed, no A-reference, no I-needing-deep-model, NO kind-3). The changed decision (.raised uninterpretable-operand -> notApplicable sentinel vs escaping error) is modeled DEEPLY/STRUCTURALLY over ParseOutcome, not axiomatized — compliant with SPEC_GUIDE §3 (no axiomatizing a deeply-modeled changed decision). The unchanged callee `Unit(other, parse_strict='silent')` is carried as grounded observation `po` and validated against reality by conformance_check.py, which drives the REAL factory + REAL post-patch UnrecognizedUnit.__eq__ in-container (SEED 7606, 120k inputs + hand-picked F2P edges). mapping.md `type(self) is UnrecognizedUnit` (no subclasses in tree) -> isUnrecognized folding is exact. Correspondence holds.

CONCLUSION: verify=>correct is upheld. >=7 distinct same-spec wrong impls (>= the 5-6 required, spanning prepatch-bug/partial-domain/boundary/control-flow-effect/ungrounded-collapse) all fail to close; positive control closes clean. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for astropy__astropy-7606 lean bundle, modeling UnrecognizedUnit.__eq__ (astropy/units/core.py). RESULT: FAITHFUL — no diverging input found; the modeled eqResult agrees with the real repo callee on every in-domain input.

Evidence:
1. same_spec(Solution.lean, Solution_prepatch.lean, lean_tables) = True — spec region byte-identical; only impl (.raised => .ok .notApplicable vs prepatch .error .parseError) and proof differ. Spec view confirmed.
2. Solution.lean compiles under scripts/lean_verify.sh (exit 0, no sorry); `#print axioms correct_unrecognizedUnitEq` => 'does not depend on any axioms' — genuine proof, no sorryAx.
3. Differential conformance against REAL post-patch astropy (installed 8.0.1, __eq__ source byte-identical to gold patch): ran conformance_check.py (SEED 7606) = checked=120013 disagreements=0 status=pass. Independent 8000-sample rerun: 0 disagreements.
4. Adversarial exotic-operand sweep (None, ints/floats, bytes/bytearray, lists/dicts/sets/frozensets/range, numpy scalars & arrays, complex, NaN/inf, functions, classes, memoryview, real Unit objects, UnrecognizedUnit instances): oracle (real __eq__) matches shadow (impl transliteration fed by real Unit(...,'silent') factory) in every case.
5. Model fold `isinstance(other, type(self))` ↔ `isUnrecognized` is sound: UnrecognizedUnit.__subclasses__() == [] so type(self) IS UnrecognizedUnit.
6. Domain boundary is symmetric: the only escaping-exception operand constructible (a custom object raising RecursionError, i.e. an exception outside) escapes on BOTH the real callee and the harness parse_outcome — both catch only the same three exception types. So it lies outside the modeled ParseOutcome domain on both sides; no drift. The docstring phrase 'never propagates the interpretation failure' is faithfully scoped to interpret-as-unit failures (the caught exceptions), matching reality.

The spec is not too strong: every input it constrains matches the real UnrecognizedUnit.__eq__. G-CONF-style differential check passes decisively. No FAITHFUL-defect diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region verified byte-identical Solution.lean <-> Solution_prepatch.lean (markers.same_spec = True with LeanBackend tables), so the spec view is well-defined and shared. Solution.lean compiles with a clean proof (verdict.md records lean_verify exit 0 and #print axioms clean). Compared the spec view (doc-comment + inductives UnitError/EqResult/ParseOutcome + eqResult/problem_spec signatures + empty axioms region; impl and proof regions elided) against the PUBLIC problem_statement only (NOT hints_text).

The public problem_statement already discloses: the exact buggy body (`other = Unit(other, parse_strict='silent')` / `return isinstance(other, UnrecognizedUnit) and self.name == other.name`), the failing call `x == None  # Should be False`, the factory raising `TypeError("None is not a valid Unit")` when `s is None`, and the requirement that `==` not fail / should be False.

The spec view restates the DESIRED post-patch semantics abstractly (a lenient interpretation step that can fail for some operands; three-valued result; uninterpretable operand -> 'comparison not applicable' sentinel, never an escaping error; matching unrecognised name -> true, else false). This is precisely the spec's job. It contains NONE of the gold edit's form: no `try`/`except`, no `NotImplemented` literal, no `parse_strict='silent'`, no `Unit(...)` factory call, and no `isinstance(other, type(self))` rename. The 'must not propagate the interpretation failure' clause is a direct restatement of the public bug (the TypeError shown escaping `x == None` marked 'Should be False'); the abstract 'not applicable' sentinel is a legitimate modeling of __eq__'s raw return, not the NotImplemented mechanics. No hints_text content (which discusses `x is None`) appears anywhere in the spec view. The spec view reveals nothing about the gold edit's FORM beyond what the public statement already discloses.

Verdict: NO-LEAKAGE. Concur with recorded verdict.md Role 4.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
