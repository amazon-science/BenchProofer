# P2 adversarial audit — django__django-16560

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
none — no same-spec wrong impl verifies, so no candidate exists to materialize a patch for
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -78,11 +78,7 @@
 -- impl-start
 def implementation_validateError
     (violated : Bool) (code : Option String) : Option (Option String) := Id.run do
-  -- A detected violation is signalled by raising an error that carries the
-  -- configured code; no violation raises nothing.
-  if violated then
-    return some code
-  return none
+  return some code
 -- impl-end
 
 -- impl-start
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -78,10 +78,10 @@
 -- impl-start
 def implementation_validateError
     (violated : Bool) (code : Option String) : Option (Option String) := Id.run do
-  -- A detected violation is signalled by raising an error that carries the
-  -- configured code; no violation raises nothing.
   if violated then
-    return some code
+    match code with
+    | some c => return some (some c)
+    | none   => return none
   return none
 -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -78,10 +78,8 @@
 -- impl-start
 def implementation_validateError
     (violated : Bool) (code : Option String) : Option (Option String) := Id.run do
-  -- A detected violation is signalled by raising an error that carries the
-  -- configured code; no violation raises nothing.
   if violated then
-    return some code
+    return some none
   return none
 -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -87,7 +87,7 @@
 
 -- impl-start
 def implementation_constraintEq (a b : Constr) : Bool := Id.run do
-  return (a.rest == b.rest) && (a.code == b.code)
+  return (a.rest == b.rest) || (a.code == b.code)
 -- impl-end
 
 -- impl-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -87,7 +87,7 @@
 
 -- impl-start
 def implementation_constraintEq (a b : Constr) : Bool := Id.run do
-  return (a.rest == b.rest) && (a.code == b.code)
+  return (a.rest == b.rest)
 -- impl-end
 
 -- impl-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -92,10 +92,9 @@
 
 -- impl-start
 def implementation_serializedCode (code : Option String) : Option String := Id.run do
-  -- Include the code in the reconstruction data only when one is configured.
   match code with
   | some c => return some c
-  | none   => return none
+  | none   => return some ""
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -92,10 +92,7 @@
 
 -- impl-start
 def implementation_serializedCode (code : Option String) : Option String := Id.run do
-  -- Include the code in the reconstruction data only when one is configured.
-  match code with
-  | some c => return some c
-  | none   => return none
+  return none
 -- impl-end
 
 -- proof-start
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -87,7 +87,7 @@
 
 -- impl-start
 def implementation_constraintEq (a b : Constr) : Bool := Id.run do
-  return (a.rest == b.rest) && (a.code == b.code)
+  return true
 -- impl-end
 
 -- impl-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Customising the machine-readable error code carried by a data-integrity
constraint, alongside the human-readable message it can already carry.

A constraint may now be configured with an OPTIONAL error code (a short string).
Some constraints carry a concrete code; others carry none. This optional code is
threaded into three observable behaviors of a constraint, each pinned below:

  * VALIDATION ERROR — when a constraint checks a candidate value and detects a
    violation, it signals that violation by raising a validation error; the error
    carries the constraint's configured code (or no code when none is configured).
    When no violation is detected, nothing is raised.

  * EQUALITY — two constraints are considered equal exactly when their
    pre-existing comparison payload (everything compared before) matches AND their
    optional codes match. Two otherwise-identical constraints carrying different
    codes are therefore not equal; carrying the same code (including both having
    none) keeps them equal.

  * RECONSTRUCTION DATA — the keyword data used to rebuild a constraint surfaces
    the code exactly when one is configured, and omits it entirely when none is
    configured (mirroring how the existing message is handled).

Each behavior is a TOTAL function of its inputs and is fully pinned: no output
component is left free.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom and none is referenced as a
-- deep model. Each modeled behavior is a total computation over the constraint's
-- own data: the optional code, the pre-existing comparison payload (collapsed to a
-- single comparison key, unchanged by this work), and a boolean recording whether
-- the constraint's own (unchanged) detection found a violation. Hence no
-- `opaque`/`axiom` declaration is required.
-- axioms-end

-- pure-start
/-- The comparison-relevant payload of a constraint: its pre-existing comparison
key (name plus the constraint's defining data and message, collapsed to one key
that is compared unchanged) together with the optional error code. -/
structure Constr where
  rest : String
  code : Option String
deriving DecidableEq
-- pure-end

-- post-conditions-start
/-- The validation-error behavior is TOTAL and fully pinned.

  * When the constraint detects a violation (`violated = true`), it raises an
    error (`some _`) whose carried code is exactly the configured code.
  * When no violation is detected (`violated = false`), nothing is raised
    (`none`).

The carried code is pinned to the configured `code`, not left free. -/
def problem_spec_validateError
    (violated : Bool) (code : Option String) (result : Option (Option String)) : Prop :=
  result = (if violated then some code else none)
-- post-conditions-end

-- post-conditions-start
/-- Equality is pinned to BOTH the pre-existing comparison payload AND the optional
code: no output freedom remains. Equal exactly when both agree. -/
def problem_spec_constraintEq (a b : Constr) (result : Bool) : Prop :=
  result = ((a.rest == b.rest) && (a.code == b.code))
-- post-conditions-end

-- post-conditions-start
/-- The reconstruction data surfaces the code exactly when one is configured: the
result is `some c` when a code `c` is configured and `none` when none is. -/
def problem_spec_serializedCode (code : Option String) (result : Option String) : Prop :=
  result = code
-- post-conditions-end

-- impl-start
def implementation_validateError
    (violated : Bool) (code : Option String) : Option (Option String) := Id.run do
  -- A detected violation is signalled by raising an error that carries the
  -- configured code; no violation raises nothing.
  if violated then
    return some code
  return none
-- impl-end

-- impl-start
def implementation_constraintEq (a b : Constr) : Bool := Id.run do
  return (a.rest == b.rest) && (a.code == b.code)
-- impl-end

-- impl-start
def implementation_serializedCode (code : Option String) : Option String := Id.run do
  -- Include the code in the reconstruction data only when one is configured.
  match code with
  | some c => return some c
  | none   => return none
-- impl-end

-- proof-start
theorem correct_validateError :
    ∀ (violated : Bool) (code : Option String),
      problem_spec_validateError violated code
        (implementation_validateError violated code) := by
  intro violated code
  unfold problem_spec_validateError implementation_validateError
  cases violated <;> rfl
-- proof-end

-- proof-start
theorem correct_constraintEq :
    ∀ (a b : Constr),
      problem_spec_constraintEq a b (implementation_constraintEq a b) := by
  intro a b
  rfl
-- proof-end

-- proof-start
theorem correct_serializedCode :
    ∀ (code : Option String),
      problem_spec_serializedCode code (implementation_serializedCode code) := by
  intro code
  unfold problem_spec_serializedCode implementation_serializedCode
  cases code <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

django__django-16560 (Lean), 3 modeled behaviors. All three problem_spec_* are FULLY-PINNED total functional equalities with zero output freedom: validateError result = (if violated then some code else none); constraintEq result = ((a.rest==b.rest) && (a.code==b.code)); serializedCode result = code. axioms=[], deep_model_references=[]; G-AX/axiom_check.py is a genuine skip stub (no consumed callee axiom, no axiomatized A-reference) => NO axiom escape hatch. Closing correct_<name> for any wrong impl would require proving wrong_impl = pinned_spec_expr, which is false; Lean soundness forbids it regardless of proof-region edits (same_spec leaves proof free). Therefore no same-spec wrong impl can verify, and protocol step 2 (materialize+resolve a verifying wrong impl's patch) has NO triggering candidate — correctly, none exists to break the spec.

### PROTOCOL EXECUTED (all same_spec=True vs Solution.lean, verified via swebench_unified.markers.same_spec with LeanBackend):
Command template: `bash scripts/lean_verify.sh <atk>.lean` (run concurrently, 4 at a time).
- atk_1 (validateError, ungrounded-oracle echo: `return some code` ignoring violated): EXIT=1, rfl failed at correct_validateError (line 104). Wrong at violated=false (spec none, impl some code).
- atk_2 (validateError, None-code boundary drop: raise only when code=some c, drop at code=none): EXIT=1, rfl failed (line 108). Wrong at violated=true & code=none (spec some none, impl none).
- atk_3 (validateError, PREPATCH bug: `if violated then return some none`): EXIT=1, rfl failed (line 106). Reproduces the base_commit bug (raises with no code).
- atk_4 (constraintEq, control-flow-effect: `||` instead of `&&`): EXIT=1, rfl failed at correct_constraintEq (line 116).
- atk_5 (constraintEq, PREPATCH bug: `a.rest == b.rest` only, ignores code): EXIT=1, rfl failed (line 116). Reproduces base_commit bug.
- atk_6 (serializedCode, boundary: map none -> some ""): EXIT=1, rfl failed at correct_serializedCode (line 124).
- atk_7 (serializedCode, PREPATCH bug: always `return none`, drops code): EXIT=1, rfl failed (line 122). Reproduces base_commit bug.
- atk_8 (constraintEq, ungrounded-oracle echo: `return true`): EXIT=1, rfl failed (line 116).
Positive control (pos_control.lean = byte copy of Solution.lean): `bash scripts/lean_verify.sh pos_control.lean` -> EXIT=0 (compiles, no sorry; correct_* proofs close with clean axioms per G-VERIFY/meta.json #print axioms 'does not depend on any axioms').

Since ZERO wrong impls close their proof (all exit 1), there is no clean-axiom-closing wrong impl for which a faithful refined patch could be materialized and resolve-run; the verify=>correct implication holds by Lean soundness over the pinned equalities. All three prepatch bugs (atk_3/5/7, matching Solution_prepatch.lean's real base_commit behavior) fail to verify => prepatch_reproduced=true; spec is discriminating.

REFINEMENT AUDIT: refinement.md legs are all R (carrier/type refinement: code:Option String<->str|None, Constr.rest<->pre-existing comparison key, violated:Bool<->unchanged detection) or trivially I (no violation => nothing raised). No A-consumed, no A-reference, no kind-3 legs. Consistent with meta.json axioms=[]/deep_model_references=[] and the skip-stub axiom_check.py. No A-legs exist whose callee correspondence could fail; the abstracted callees (Q.check/queryset.exists detection, get_violation_error_message) are inputs/orthogonal, not axioms. Audit clean.

>=8 distinct attacks run (partial-domain, boundary/None-code, control-flow-effect, ungrounded-oracle echo, all three prepatch bugs); none breaks the spec. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
none — no same-spec wrong impl verifies, so no candidate exists to materialize a patch for
```

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
Customising the machine-readable error code carried by a data-integrity
constraint, alongside the human-readable message it can already carry.

A constraint may now be configured with an OPTIONAL error code (a short string).
Some constraints carry a concrete code; others carry none. This optional code is
threaded into three observable behaviors of a constraint, each pinned below:

  * VALIDATION ERROR — when a constraint checks a candidate value and detects a
    violation, it signals that violation by raising a validation error; the error
    carries the constraint's configured code (or no code when none is configured).
    When no violation is detected, nothing is raised.

  * EQUALITY — two constraints are considered equal exactly when their
    pre-existing comparison payload (everything compared before) matches AND their
    optional codes match. Two otherwise-identical constraints carrying different
    codes are therefore not equal; carrying the same code (including both having
    none) keeps them equal.

  * RECONSTRUCTION DATA — the keyword data used to rebuild a constraint surfaces
    the code exactly when one is configured, and omits it entirely when none is
    configured (mirroring how the existing message is handled).

Each behavior is a TOTAL function of its inputs and is fully pinned: no output
component is left free.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom and none is referenced as a
-- deep model. Each modeled behavior is a total computation over the constraint's
-- own data: the optional code, the pre-existing comparison payload (collapsed to a
-- single comparison key, unchanged by this work), and a boolean recording whether
-- the constraint's own (unchanged) detection found a violation. Hence no
-- `opaque`/`axiom` declaration is required.
-- axioms-end

-- pure-start
/-- The comparison-relevant payload of a constraint: its pre-existing comparison
key (name plus the constraint's defining data and message, collapsed to one key
that is compared unchanged) together with the optional error code. -/
structure Constr where
  rest : String
  code : Option String
deriving DecidableEq
-- pure-end

-- post-conditions-start
/-- The validation-error behavior is TOTAL and fully pinned.

  * When the constraint detects a violation (`violated = true`), it raises an
    error (`some _`) whose carried code is exactly the configured code.
  * When no violation is detected (`violated = false`), nothing is raised
    (`none`).

The carried code is pinned to the configured `code`, not left free. -/
def problem_spec_validateError
    (violated : Bool) (code : Option String) (result : Option (Option String)) : Prop :=
  result = (if violated then some code else none)
-- post-conditions-end

-- post-conditions-start
/-- Equality is pinned to BOTH the pre-existing comparison payload AND the optional
code: no output freedom remains. Equal exactly when both agree. -/
def problem_spec_constraintEq (a b : Constr) (result : Bool) : Prop :=
  result = ((a.rest == b.rest) && (a.code == b.code))
-- post-conditions-end

-- post-conditions-start
/-- The reconstruction data surfaces the code exactly when one is configured: the
result is `some c` when a code `c` is configured and `none` when none is. -/
def problem_spec_serializedCode (code : Option String) (result : Option String) : Prop :=
  result = code
-- post-conditions-end

-- impl-start
def implementation_validateError
    (violated : Bool) (code : Option String) : Option (Option String) := Id.run do
  -- A detected violation is signalled by raising an error that carries the
  -- configured code; no violation raises nothing.
  if violated then
    return some code
  return none
-- impl-end

-- impl-start
def implementation_constraintEq (a b : Constr) : Bool := Id.run do
  return (a.rest == b.rest) && (a.code == b.code)
-- impl-end

-- impl-start
def implementation_serializedCode (code : Option String) : Option String := Id.run do
  -- Include the code in the reconstruction data only when one is configured.
  match code with
  | some c => return some c
  | none   => return none
-- impl-end

-- proof-start
theorem correct_validateError :
    ∀ (violated : Bool) (code : Option String),
      problem_spec_validateError violated code
        (implementation_validateError violated code) := by
  intro violated code
  unfold problem_spec_validateError implementation_validateError
  cases violated <;> rfl
-- proof-end

-- proof-start
theorem correct_constraintEq :
    ∀ (a b : Constr),
      problem_spec_constraintEq a b (implementation_constraintEq a b) := by
  intro a b
  rfl
-- proof-end

-- proof-start
theorem correct_serializedCode :
    ∀ (code : Option String),
      problem_spec_serializedCode code (implementation_serializedCode code) := by
  intro code
  unfold problem_spec_serializedCode implementation_serializedCode
  cases code <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

django__django-16560 (Lean), 3 modeled behaviors. All three problem_spec_* are FULLY-PINNED total functional equalities with zero output freedom: validateError result = (if violated then some code else none); constraintEq result = ((a.rest==b.rest) && (a.code==b.code)); serializedCode result = code. axioms=[], deep_model_references=[]; G-AX/axiom_check.py is a genuine skip stub (no consumed callee axiom, no axiomatized A-reference) => NO axiom escape hatch. Closing correct_<name> for any wrong impl would require proving wrong_impl = pinned_spec_expr, which is false; Lean soundness forbids it regardless of proof-region edits (same_spec leaves proof free). Therefore no same-spec wrong impl can verify, and protocol step 2 (materialize+resolve a verifying wrong impl's patch) has NO triggering candidate — correctly, none exists to break the spec.

### PROTOCOL EXECUTED (all same_spec=True vs Solution.lean, verified via swebench_unified.markers.same_spec with LeanBackend):
Command template: `bash scripts/lean_verify.sh <atk>.lean` (run concurrently, 4 at a time).
- atk_1 (validateError, ungrounded-oracle echo: `return some code` ignoring violated): EXIT=1, rfl failed at correct_validateError (line 104). Wrong at violated=false (spec none, impl some code).
- atk_2 (validateError, None-code boundary drop: raise only when code=some c, drop at code=none): EXIT=1, rfl failed (line 108). Wrong at violated=true & code=none (spec some none, impl none).
- atk_3 (validateError, PREPATCH bug: `if violated then return some none`): EXIT=1, rfl failed (line 106). Reproduces the base_commit bug (raises with no code).
- atk_4 (constraintEq, control-flow-effect: `||` instead of `&&`): EXIT=1, rfl failed at correct_constraintEq (line 116).
- atk_5 (constraintEq, PREPATCH bug: `a.rest == b.rest` only, ignores code): EXIT=1, rfl failed (line 116). Reproduces base_commit bug.
- atk_6 (serializedCode, boundary: map none -> some ""): EXIT=1, rfl failed at correct_serializedCode (line 124).
- atk_7 (serializedCode, PREPATCH bug: always `return none`, drops code): EXIT=1, rfl failed (line 122). Reproduces base_commit bug.
- atk_8 (constraintEq, ungrounded-oracle echo: `return true`): EXIT=1, rfl failed (line 116).
Positive control (pos_control.lean = byte copy of Solution.lean): `bash scripts/lean_verify.sh pos_control.lean` -> EXIT=0 (compiles, no sorry; correct_* proofs close with clean axioms per G-VERIFY/meta.json #print axioms 'does not depend on any axioms').

Since ZERO wrong impls close their proof (all exit 1), there is no clean-axiom-closing wrong impl for which a faithful refined patch could be materialized and resolve-run; the verify=>correct implication holds by Lean soundness over the pinned equalities. All three prepatch bugs (atk_3/5/7, matching Solution_prepatch.lean's real base_commit behavior) fail to verify => prepatch_reproduced=true; spec is discriminating.

REFINEMENT AUDIT: refinement.md legs are all R (carrier/type refinement: code:Option String<->str|None, Constr.rest<->pre-existing comparison key, violated:Bool<->unchanged detection) or trivially I (no violation => nothing raised). No A-consumed, no A-reference, no kind-3 legs. Consistent with meta.json axioms=[]/deep_model_references=[] and the skip-stub axiom_check.py. No A-legs exist whose callee correspondence could fail; the abstracted callees (Q.check/queryset.exists detection, get_violation_error_message) are inputs/orthogonal, not axioms. Audit clean.

>=8 distinct attacks run (partial-domain, boundary/None-code, control-flow-effect, ungrounded-oracle echo, all three prepatch bugs); none breaks the spec. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-drift / too-strong) audit of django__django-16560 lean bundle.

### Structural checks
- same_spec(Solution.lean, Solution_prepatch.lean, lean tables) == True: spec region (imports/axioms/pure/post-conditions) byte-identical; prepatch differs only in impl bodies + sorry proofs.
- lean_verify.sh exit 0 (compiles, no sorry/error).
- #print axioms on all three theorems: 'does not depend on any axioms' — no sorryAx, proofs genuine.

### FAITHFULNESS vs REAL CALLEE (gold patch applied to base_commit 51c9bb7cd1 in fresh worktree):
- Ran bundle conformance_check.py against real patched CheckConstraint.validate/__eq__/deconstruct: 120,000 inputs, 0 disagreements.
- Direct boundary probes of the real callee confirm each modeled leg:
  * validateError: violated=>ValidationError raised with .code == configured code for None/''/'x'/'0' (spec: `if violated then some code else none`); not-violated => nothing raised. Match.
  * constraintEq: None vs '' codes => real __eq__ False (spec `some ''` != `none`); equal codes => True. `rest` abstraction of unchanged name+check+message payload is sound (patch only ADDS the code conjunct). Match.
  * serializedCode: deconstruct kwargs includes key iff code is not None, value == code (spec `some c` <-> present, `none` <-> absent). Match.

The abstractions violated:Bool (unchanged detection incl. FieldError-swallow path -> no raise) and Constr.rest (single unchanged comparison key) are conservative and do not over-constrain the modeled change. No input distinguishes the modeled functions from the real post-patch behavior. Spec is neither too strong nor drifted.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region verified byte-identical between Solution.lean and Solution_prepatch.lean via swebench_unified.markers.same_spec (lean backend) => True. Mechanical G-LEAK screen (leakage.screen) passes with zero hard_failures: no diff markers, no reproduced gold-patch line, no patched file/module path, no spec-view identifier embedding a patched symbol (e.g. 'violation_error_code', 'CheckConstraint', 'deconstruct'), no bug/fix narration. No RELAXED_LEAKAGE flag on this bundle (screen genuinely clean).

Semantic assessment vs PUBLIC problem_statement (hints_text excluded): the statement discloses the whole feature -- 'Allow to customize the code attribute of ValidationError raised by BaseConstraint.validate', framed explicitly as parallel to the already-existing violation_error_message customization ('I'd like to add a new ... parameter to BaseConstraint'). The spec view (docstring + Constr structure + three problem_spec signatures) models exactly the three observable behaviors that 'customize the code, like the message' decomposes into: (1) VALIDATION ERROR carries the configured code -- verbatim the public request; (2) EQUALITY compares the code -- implied because the message already participates in __eq__ and the code is asked to behave like the message; (3) RECONSTRUCTION DATA surfaces the code iff set, phrased 'mirroring how the existing message is handled' -- again the publicly-implied completion of 'behave like the message', not a disclosure of the gold's `is not None` token.

Crucially, the spec view discloses NOTHING beyond the public statement's localization surface: no class names (BaseConstraint/CheckConstraint/UniqueConstraint/ExclusionConstraint), no method names (validate/__eq__/deconstruct/__repr__), no field identifier, no file paths (constraints.py), no line numbers, no `is not None` conditional structure, no diff text. The equality and reconstruction legs are the natural, publicly-implied contract of threading a new optional field 'like the existing message', which the problem statement explicitly invites. No spec-view line hands the solver gold-edit detail past the public problem_statement. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
