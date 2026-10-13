# P2 adversarial audit — django__django-13023

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -104,7 +104,8 @@
     return Outcome.returned
   match v.conv with
   | none => return Outcome.returned
-  | some _ => return Outcome.validationError
+  | some ConvError.notANumber => return Outcome.validationError
+  | some _ => return Outcome.propagated
 -- impl-end
 
 -- proof-start
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -101,7 +101,7 @@
   if v.isNone then
     return Outcome.returned
   if v.isFloat then
-    return Outcome.returned
+    return Outcome.validationError
   match v.conv with
   | none => return Outcome.returned
   | some _ => return Outcome.validationError
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -98,8 +98,6 @@
 
 -- impl-start
 def implementation_toPython (v : Value) : Outcome := Id.run do
-  if v.isNone then
-    return Outcome.returned
   if v.isFloat then
     return Outcome.returned
   match v.conv with
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -98,13 +98,7 @@
 
 -- impl-start
 def implementation_toPython (v : Value) : Outcome := Id.run do
-  if v.isNone then
-    return Outcome.returned
-  if v.isFloat then
-    return Outcome.returned
-  match v.conv with
-  | none => return Outcome.returned
-  | some _ => return Outcome.validationError
+  return Outcome.returned
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -103,7 +103,7 @@
   if v.isFloat then
     return Outcome.returned
   match v.conv with
-  | none => return Outcome.returned
+  | none => return Outcome.validationError
   | some _ => return Outcome.validationError
 -- impl-end
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -98,13 +98,7 @@
 
 -- impl-start
 def implementation_toPython (v : Value) : Outcome := Id.run do
-  if v.isNone then
-    return Outcome.returned
-  if v.isFloat then
-    return Outcome.returned
-  match v.conv with
-  | none => return Outcome.returned
-  | some _ => return Outcome.validationError
+  return Outcome.validationError
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Interpreting an arbitrary input value as a decimal number.

A model field that stores decimal numbers must turn whatever value it is handed
into a decimal. The conversion follows a definite precedence:

  * a missing value (the absence of any value) passes straight through unchanged;
  * a value that is already a floating-point number is converted directly to a
    decimal;
  * any other value is interpreted as a decimal number.

That last interpretation can fail in several different low-level ways, depending
on the nature of the offending value (a value that looks numeric but is not a
well-formed decimal literal, a value whose very type cannot stand for a number at
all, or a structurally malformed value). However it fails, the failure means the
same thing to a caller: the supplied value is not a usable decimal number.

The contract is therefore that EVERY low-level failure of that interpretation is
reported uniformly, as one and the same validation error — so a caller never has
to discriminate among, or be surprised by, the assorted low-level failure modes.
A value that does interpret cleanly (and the missing / floating-point cases)
returns normally. The four cases are exhaustive and mutually exclusive, so the
outcome is fully determined for every input.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The conversion
-- of a value to a decimal number is modeled DEEPLY as a classification of the
-- input (whether the conversion succeeds, and if not, which kind of low-level
-- failure it produces); the floating-point branch is modeled as a normal
-- return. There is no `opaque`/`axiom` callee contract the proof consumes.
-- axioms-end

-- pure-start
/-- The way an attempt to interpret a non-missing, non-floating-point value as a
decimal number can fail at the low level. The three kinds reflect the distinct
natures of an unusable value; the contract treats them identically. -/
inductive ConvError where
  /-- a value that looks number-like but is not a well-formed decimal literal -/
  | notANumber
  /-- a value whose type cannot represent a number at all -/
  | unsupportedType
  /-- a structurally malformed value -/
  | malformedValue
deriving DecidableEq, Repr

/-- An input value, observed through the only features the conversion inspects:
whether it is the missing value, whether it is a floating-point number, and — for
any other value — whether interpreting it as a decimal succeeds (`none`) or fails
with a low-level error of some kind (`some e`). The three features are read in
that precedence order. -/
structure Value where
  /-- the value is missing (the absence of any value) -/
  isNone : Bool
  /-- the value is a floating-point number (consulted only when not missing) -/
  isFloat : Bool
  /-- how interpreting the value as a decimal behaves (consulted only when the
  value is neither missing nor floating-point): `none` = succeeds, `some e` =
  fails with a low-level error of kind `e` -/
  conv : Option ConvError
deriving Repr

/-- The observable outcome of the conversion. -/
inductive Outcome where
  /-- a value is returned normally (a decimal, or the missing value unchanged) -/
  | returned
  /-- a uniform validation error is reported -/
  | validationError
  /-- a low-level failure escapes the conversion uncaught -/
  | propagated
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- The outcome of interpreting `v` as a decimal number:

  * a missing value returns normally;
  * a non-missing floating-point value returns normally;
  * a non-missing, non-floating-point value that interprets cleanly returns
    normally;
  * a non-missing, non-floating-point value whose interpretation fails in ANY
    low-level way is reported as a validation error.

The four cases are exhaustive and mutually exclusive (directive 5 frame: the
outcome is pinned in every case; directive 8: each outcome is grounded in the
classification of the actual input `v`, with no low-level failure left to escape
uncaught). -/
def problem_spec_toPython (v : Value) (result : Outcome) : Prop :=
  (v.isNone = true → result = Outcome.returned) ∧
  (v.isNone = false → v.isFloat = true → result = Outcome.returned) ∧
  (v.isNone = false → v.isFloat = false → v.conv = none → result = Outcome.returned) ∧
  (v.isNone = false → v.isFloat = false → v.conv.isSome = true →
      result = Outcome.validationError)
-- post-conditions-end

-- impl-start
def implementation_toPython (v : Value) : Outcome := Id.run do
  if v.isNone then
    return Outcome.returned
  if v.isFloat then
    return Outcome.returned
  match v.conv with
  | none => return Outcome.returned
  | some _ => return Outcome.validationError
-- impl-end

-- proof-start
theorem correct_toPython :
    ∀ (v : Value), problem_spec_toPython v (implementation_toPython v) := by
  intro v
  unfold problem_spec_toPython implementation_toPython
  refine ⟨?_, ?_, ?_, ?_⟩ <;> intro h1
  · simp only [Id.run, h1, if_true]; rfl
  · intro h2; simp only [Id.run, h1, h2, Bool.false_eq_true, if_false]; rfl
  · intro h2 h3
    simp only [Id.run, h1, h2, Bool.false_eq_true, if_false, h3]; rfl
  · intro h2 h3
    cases hcv : v.conv with
    | none => rw [hcv] at h3; simp at h3
    | some e => simp only [Id.run, h1, h2, Bool.false_eq_true, if_false]; rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC IS FULLY DETERMINISTIC: problem_spec_toPython's four conjuncts partition the entire Value input space (isNone bool x isFloat bool x conv Option) and pin `result` uniquely in each case: isNone=true -> returned; isNone=false,isFloat=true -> returned; isNone=false,isFloat=false,conv=none -> returned; isNone=false,isFloat=false,conv.isSome -> validationError. No deviating implementation can satisfy it under ANY proof.

All files pass same_spec (True) against Solution.lean — impl region edited only, axioms/pure/pre/post byte-identical.

### VERIFICATION (scripts/lean_verify.sh <file>, run concurrently <=4 at a time):
- pos.lean (gold impl, positive control): EXIT=0 (verifies, no sorry). #print axioms correct_toPython => [propext, Quot.sound] — CLEAN (no sorry, no custom axiom). Ran via pos_axioms.lean.
- atk_1.lean (prepatch bug: validationError only for notANumber, else propagated): EXIT=1. Error: goal `pure Outcome.propagated = Outcome.validationError` unprovable in the conv.isSome branch. This reproduces the pre-patch bug (matches Solution_prepatch.lean).
- atk_2.lean (boundary: float branch -> validationError): EXIT=1.
- atk_3.lean (control-flow-effect: isNone guard dropped): EXIT=1.
- atk_4.lean (ungrounded-oracle echo: always returned): EXIT=1. Error: `pure Outcome.returned = Outcome.validationError` in conv.isSome branch.
- atk_5.lean (partial-domain flip: conv=none -> validationError): EXIT=1.
- atk_6.lean (constant validationError): EXIT=1. Error: `pure Outcome.validationError = Outcome.returned` — distinct constructors, genuinely unprovable.

All 6 same-spec wrong impls FAIL to verify (exit 1); errors are genuine spec-violation unsolved goals (distinct Outcome constructors), NOT proof-syntax artifacts. Because NO wrong impl closes with clean axioms, there is NO patch to materialize/resolve (patches={}). verify=>correct holds for every attacked deviation.

REFINEMENT.MD AUDIT: leg #1 = I (identical: isNone guard); legs #2,#3,#4 = R (type refinement / deep model of decimal.Decimal + create_decimal_from_float abstracted to observable Outcome). No A-consumed / A-reference legs (axioms=[], deep_model_references=[]), consistent with G-AX skip stub. No kind-3 (unsupported-construct) legs. The changed op #4 deeply models the post-patch `except (InvalidOperation, TypeError, ValueError)` widening as a uniform conv=some e -> validationError for all three ConvError kinds (notANumber/unsupportedType/malformedValue), faithfully matching the gold patch; mapping.md bijection to the three real decimal.Decimal exception types holds. Model<->patch correspondence is sound.

prepatch_reproduced=true: atk_1 is the byte-equivalent prepatch impl and fails to verify against this spec, so the spec detects the real bug (fourth conjunct).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Interpreting an arbitrary input value as a decimal number.

A model field that stores decimal numbers must turn whatever value it is handed
into a decimal. The conversion follows a definite precedence:

  * a missing value (the absence of any value) passes straight through unchanged;
  * a value that is already a floating-point number is converted directly to a
    decimal;
  * any other value is interpreted as a decimal number.

That last interpretation can fail in several different low-level ways, depending
on the nature of the offending value (a value that looks numeric but is not a
well-formed decimal literal, a value whose very type cannot stand for a number at
all, or a structurally malformed value). However it fails, the failure means the
same thing to a caller: the supplied value is not a usable decimal number.

The contract is therefore that EVERY low-level failure of that interpretation is
reported uniformly, as one and the same validation error — so a caller never has
to discriminate among, or be surprised by, the assorted low-level failure modes.
A value that does interpret cleanly (and the missing / floating-point cases)
returns normally. The four cases are exhaustive and mutually exclusive, so the
outcome is fully determined for every input.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The conversion
-- of a value to a decimal number is modeled DEEPLY as a classification of the
-- input (whether the conversion succeeds, and if not, which kind of low-level
-- failure it produces); the floating-point branch is modeled as a normal
-- return. There is no `opaque`/`axiom` callee contract the proof consumes.
-- axioms-end

-- pure-start
/-- The way an attempt to interpret a non-missing, non-floating-point value as a
decimal number can fail at the low level. The three kinds reflect the distinct
natures of an unusable value; the contract treats them identically. -/
inductive ConvError where
  /-- a value that looks number-like but is not a well-formed decimal literal -/
  | notANumber
  /-- a value whose type cannot represent a number at all -/
  | unsupportedType
  /-- a structurally malformed value -/
  | malformedValue
deriving DecidableEq, Repr

/-- An input value, observed through the only features the conversion inspects:
whether it is the missing value, whether it is a floating-point number, and — for
any other value — whether interpreting it as a decimal succeeds (`none`) or fails
with a low-level error of some kind (`some e`). The three features are read in
that precedence order. -/
structure Value where
  /-- the value is missing (the absence of any value) -/
  isNone : Bool
  /-- the value is a floating-point number (consulted only when not missing) -/
  isFloat : Bool
  /-- how interpreting the value as a decimal behaves (consulted only when the
  value is neither missing nor floating-point): `none` = succeeds, `some e` =
  fails with a low-level error of kind `e` -/
  conv : Option ConvError
deriving Repr

/-- The observable outcome of the conversion. -/
inductive Outcome where
  /-- a value is returned normally (a decimal, or the missing value unchanged) -/
  | returned
  /-- a uniform validation error is reported -/
  | validationError
  /-- a low-level failure escapes the conversion uncaught -/
  | propagated
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- The outcome of interpreting `v` as a decimal number:

  * a missing value returns normally;
  * a non-missing floating-point value returns normally;
  * a non-missing, non-floating-point value that interprets cleanly returns
    normally;
  * a non-missing, non-floating-point value whose interpretation fails in ANY
    low-level way is reported as a validation error.

The four cases are exhaustive and mutually exclusive (directive 5 frame: the
outcome is pinned in every case; directive 8: each outcome is grounded in the
classification of the actual input `v`, with no low-level failure left to escape
uncaught). -/
def problem_spec_toPython (v : Value) (result : Outcome) : Prop :=
  (v.isNone = true → result = Outcome.returned) ∧
  (v.isNone = false → v.isFloat = true → result = Outcome.returned) ∧
  (v.isNone = false → v.isFloat = false → v.conv = none → result = Outcome.returned) ∧
  (v.isNone = false → v.isFloat = false → v.conv.isSome = true →
      result = Outcome.validationError)
-- post-conditions-end

-- impl-start
def implementation_toPython (v : Value) : Outcome := Id.run do
  if v.isNone then
    return Outcome.returned
  if v.isFloat then
    return Outcome.returned
  match v.conv with
  | none => return Outcome.returned
  | some _ => return Outcome.validationError
-- impl-end

-- proof-start
theorem correct_toPython :
    ∀ (v : Value), problem_spec_toPython v (implementation_toPython v) := by
  intro v
  unfold problem_spec_toPython implementation_toPython
  refine ⟨?_, ?_, ?_, ?_⟩ <;> intro h1
  · simp only [Id.run, h1, if_true]; rfl
  · intro h2; simp only [Id.run, h1, h2, Bool.false_eq_true, if_false]; rfl
  · intro h2 h3
    simp only [Id.run, h1, h2, Bool.false_eq_true, if_false, h3]; rfl
  · intro h2 h3
    cases hcv : v.conv with
    | none => rw [hcv] at h3; simp at h3
    | some e => simp only [Id.run, h1, h2, Bool.false_eq_true, if_false]; rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC IS FULLY DETERMINISTIC: problem_spec_toPython's four conjuncts partition the entire Value input space (isNone bool x isFloat bool x conv Option) and pin `result` uniquely in each case: isNone=true -> returned; isNone=false,isFloat=true -> returned; isNone=false,isFloat=false,conv=none -> returned; isNone=false,isFloat=false,conv.isSome -> validationError. No deviating implementation can satisfy it under ANY proof.

All files pass same_spec (True) against Solution.lean — impl region edited only, axioms/pure/pre/post byte-identical.

### VERIFICATION (scripts/lean_verify.sh <file>, run concurrently <=4 at a time):
- pos.lean (gold impl, positive control): EXIT=0 (verifies, no sorry). #print axioms correct_toPython => [propext, Quot.sound] — CLEAN (no sorry, no custom axiom). Ran via pos_axioms.lean.
- atk_1.lean (prepatch bug: validationError only for notANumber, else propagated): EXIT=1. Error: goal `pure Outcome.propagated = Outcome.validationError` unprovable in the conv.isSome branch. This reproduces the pre-patch bug (matches Solution_prepatch.lean).
- atk_2.lean (boundary: float branch -> validationError): EXIT=1.
- atk_3.lean (control-flow-effect: isNone guard dropped): EXIT=1.
- atk_4.lean (ungrounded-oracle echo: always returned): EXIT=1. Error: `pure Outcome.returned = Outcome.validationError` in conv.isSome branch.
- atk_5.lean (partial-domain flip: conv=none -> validationError): EXIT=1.
- atk_6.lean (constant validationError): EXIT=1. Error: `pure Outcome.validationError = Outcome.returned` — distinct constructors, genuinely unprovable.

All 6 same-spec wrong impls FAIL to verify (exit 1); errors are genuine spec-violation unsolved goals (distinct Outcome constructors), NOT proof-syntax artifacts. Because NO wrong impl closes with clean axioms, there is NO patch to materialize/resolve (patches={}). verify=>correct holds for every attacked deviation.

REFINEMENT.MD AUDIT: leg #1 = I (identical: isNone guard); legs #2,#3,#4 = R (type refinement / deep model of decimal.Decimal + create_decimal_from_float abstracted to observable Outcome). No A-consumed / A-reference legs (axioms=[], deep_model_references=[]), consistent with G-AX skip stub. No kind-3 (unsupported-construct) legs. The changed op #4 deeply models the post-patch `except (InvalidOperation, TypeError, ValueError)` widening as a uniform conv=some e -> validationError for all three ConvError kinds (notANumber/unsupportedType/malformedValue), faithfully matching the gold patch; mapping.md bijection to the three real decimal.Decimal exception types holds. Model<->patch correspondence is sound.

prepatch_reproduced=true: atk_1 is the byte-equivalent prepatch impl and fails to verify against this spec, so the spec detects the real bug (fourth conjunct).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on django__django-13023 (DecimalField.to_python). Modeled function: DecimalField.to_python, base_commit f83b44075d. Gold widens `except decimal.InvalidOperation` -> `except (decimal.InvalidOperation, TypeError, ValueError)`; base float branch has NO math.isnan guard (that is a LATER commit), so base+gold float branch always returns normally. Spec `problem_spec_toPython`: None->returned, float->returned, conv=none->returned, conv=some e->validationError (uniform for all 3 kinds). 

Checks performed:
1. Spec region byte-identical between Solution.lean and Solution_prepatch.lean via swebench_unified.markers.same_spec (True).
2. Lean compiles clean via scripts/lean_verify.sh (exit 0). #print axioms correct_toPython => [propext, Quot.sound] only — no sorryAx, proof is real.
3. conformance_check.py runs pass: 120057 inputs, 0 disagreements.
4. Independent adversarial probe for an ESCAPING exception from decimal.Decimal(value) on non-None/non-float inputs (the spec's exhaustiveness claim): 300k+ fuzzed inputs incl. exotic tuples, complex, bytes, containers, fullwidth/arabic digits, huge exponents — zero escaping exceptions beyond {InvalidOperation, TypeError, ValueError}.
5. Independent probe of create_decimal_from_float over inf/nan/±1e308/subnormals/200k random 64-bit floats under prec=4/default/full contexts — never raised, so float->returned is faithful.
6. Full differential test of the spec model vs a faithful base+gold reconstruction (float branch without isnan guard) over 300k mixed fuzzed inputs: 0 mismatches.

Attempted to break on the two highest-risk fronts (a 'propagated' escaping decimal exception the spec forbids; a raising float) and found NO diverging input. Spec is neither too strong nor drifted; it exactly matches the post-patch/base observable behavior. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gold edit: widen `except decimal.InvalidOperation` -> `except (decimal.InvalidOperation, TypeError, ValueError)` in DecimalField.to_python, i.e. turn every low-level decimal-conversion failure into a single ValidationError. Public problem_statement already discloses the fix's nature (to_python raises TypeError on dict values instead of ValidationError; links the PR).

Spec view (Solution.lean minus impl-start..impl-end and proof-start..proof-end) states only the abstract contract: None passes through, float returns, otherwise interpret as decimal, and ANY low-level interpretation failure (v.conv.isSome) is reported as one uniform validationError. Checks performed:
- Spec view is byte-identical between Solution.lean and Solution_prepatch.lean (only the impl/proof regions differ), so the leak surface is exactly this shared abstract contract.
- Token scan of the spec view: no gold-diff specifics present — no `InvalidOperation`, `TypeError`, `ValueError`, `except`, exception tuple, `decimal.Decimal`, `create_decimal_from_float`, `__init__.py`, diff markers/hunk headers, or the PR link. (grep hits for 'diff'/'PR' were substring false-positives inside 'different'/'precedence'.)
- ConvError constructor names (notANumber/unsupportedType/malformedValue) describe only the abstract NATURE of a conversion failure; the concrete exception-type bijection lives in mapping.md (not solver-visible). The spec treats all three kinds identically, so it never reveals WHICH failure modes the patch added — that delta is visible only in the elided impl/proof region (prepatch impl handles notANumber alone, escaping the other two as propagated).

The spec encodes correct post-patch behavior at an altitude no more revealing than the public problem_statement and does not reconstruct the gold edit. NO-LEAKAGE beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
