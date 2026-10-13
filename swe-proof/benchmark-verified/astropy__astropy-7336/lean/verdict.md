# P2 adversarial audit — astropy__astropy-7336

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
None — no same-spec wrong implementation produced a closing clean-axiom proof, so there is nothing to break the spec.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -91,12 +91,10 @@
 -- impl-start
 def implementation_applyReturnAnnotation
     (annot : RetAnnotation) (ret : RetVal) : Except FinalizeError RetVal := Id.run do
-  -- If the annotation designates a concrete unit, convert the produced value to
-  -- it; otherwise (absent annotation or an explicit no-unit annotation) return
-  -- the produced value unchanged, without attempting any conversion.
   match annot with
   | .unit u => return .ok (convertTo ret u)
-  | _       => return .ok ret
+  | .empty  => return .ok ret
+  | .noUnit => return .error {}
 -- impl-end
 
 -- proof-start
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -91,12 +91,7 @@
 -- impl-start
 def implementation_applyReturnAnnotation
     (annot : RetAnnotation) (ret : RetVal) : Except FinalizeError RetVal := Id.run do
-  -- If the annotation designates a concrete unit, convert the produced value to
-  -- it; otherwise (absent annotation or an explicit no-unit annotation) return
-  -- the produced value unchanged, without attempting any conversion.
-  match annot with
-  | .unit u => return .ok (convertTo ret u)
-  | _       => return .ok ret
+  return .ok ret
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -91,11 +91,8 @@
 -- impl-start
 def implementation_applyReturnAnnotation
     (annot : RetAnnotation) (ret : RetVal) : Except FinalizeError RetVal := Id.run do
-  -- If the annotation designates a concrete unit, convert the produced value to
-  -- it; otherwise (absent annotation or an explicit no-unit annotation) return
-  -- the produced value unchanged, without attempting any conversion.
   match annot with
-  | .unit u => return .ok (convertTo ret u)
+  | .unit _ => return .ok ret
   | _       => return .ok ret
 -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -91,12 +91,10 @@
 -- impl-start
 def implementation_applyReturnAnnotation
     (annot : RetAnnotation) (ret : RetVal) : Except FinalizeError RetVal := Id.run do
-  -- If the annotation designates a concrete unit, convert the produced value to
-  -- it; otherwise (absent annotation or an explicit no-unit annotation) return
-  -- the produced value unchanged, without attempting any conversion.
   match annot with
   | .unit u => return .ok (convertTo ret u)
-  | _       => return .ok ret
+  | .empty  => return .error {}
+  | .noUnit => return .ok ret
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -91,12 +91,9 @@
 -- impl-start
 def implementation_applyReturnAnnotation
     (annot : RetAnnotation) (ret : RetVal) : Except FinalizeError RetVal := Id.run do
-  -- If the annotation designates a concrete unit, convert the produced value to
-  -- it; otherwise (absent annotation or an explicit no-unit annotation) return
-  -- the produced value unchanged, without attempting any conversion.
   match annot with
-  | .unit u => return .ok (convertTo ret u)
-  | _       => return .ok ret
+  | .empty => return .ok ret
+  | _      => return .error {}
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -91,11 +91,8 @@
 -- impl-start
 def implementation_applyReturnAnnotation
     (annot : RetAnnotation) (ret : RetVal) : Except FinalizeError RetVal := Id.run do
-  -- If the annotation designates a concrete unit, convert the produced value to
-  -- it; otherwise (absent annotation or an explicit no-unit annotation) return
-  -- the produced value unchanged, without attempting any conversion.
   match annot with
-  | .unit u => return .ok (convertTo ret u)
+  | .unit _ => return .error {}
   | _       => return .ok ret
 -- impl-end
 
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -91,11 +91,8 @@
 -- impl-start
 def implementation_applyReturnAnnotation
     (annot : RetAnnotation) (ret : RetVal) : Except FinalizeError RetVal := Id.run do
-  -- If the annotation designates a concrete unit, convert the produced value to
-  -- it; otherwise (absent annotation or an explicit no-unit annotation) return
-  -- the produced value unchanged, without attempting any conversion.
   match annot with
-  | .unit u => return .ok (convertTo ret u)
+  | .unit u => return .ok (convertTo (convertTo ret u) u)
   | _       => return .ok ret
 -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Finalizing the result of a unit-validating function wrapper.

A function may declare, via its return annotation, the physical unit its result
should carry. After the wrapped function has produced a value, the wrapper turns
that raw value into the function's final result according to the annotation:

* if the annotation designates a concrete unit, the produced value is converted
  to that unit and the converted value is returned successfully;
* if the annotation is absent, or it explicitly designates *no unit at all*,
  the produced value is returned unchanged, successfully — no conversion is
  attempted.

The "no unit at all" annotation and the "absent" annotation are treated
identically here: both mean "leave the produced value exactly as it is". In
particular, finalizing succeeds for every annotation shape — designating *no
unit* never triggers a conversion (which on a value carrying no convertible
target would be a failure).

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- Dependency model used while finalizing the result, declared as opaque
-- signatures (the proof needs no property axiom about them — the contract is
-- stated directly over them and discharged by case analysis):
--
-- * `UnitObj`        : an opaque concrete physical unit that an annotation may name.
-- * `RetVal`         : the value the wrapped function produced.
-- * `convertTo r u`  : the value `r` re-expressed under the concrete unit `u`
--                      (the unchanged value conversion the wrapper performs on
--                      the concrete-unit branch only).

/-- An opaque concrete physical unit (e.g. metres, degrees). -/
opaque UnitObj : Type

/-- The value produced by the wrapped function. Its internal structure is opaque
to the contract; modeled as a one-field carrier so it is inhabited/computable. -/
structure RetVal where
  payload : Nat
deriving Inhabited, DecidableEq

/-- A function's declared return annotation. It is one of three shapes:

* `empty`   — no annotation was given;
* `noUnit`  — an annotation was given that explicitly designates *no unit*;
* `unit u`  — an annotation designating the concrete unit `u`. -/
inductive RetAnnotation where
  | empty
  | noUnit
  | unit (u : UnitObj)

/-- A finalization failure: attempting to convert a value to a unit when the
annotation does not actually name one (the value has no convertible target). -/
structure FinalizeError where
deriving Repr, DecidableEq, Inhabited

/-- The unchanged value conversion: re-express the produced value under a
*concrete* unit. Takes a `UnitObj` (never an absent/no-unit annotation), so the
primitive has no impossible states. Modeled as an opaque callee (an A-reference);
its behavior is validated against the real conversion by G-AX. -/
opaque convertTo : RetVal → UnitObj → RetVal
-- axioms-end

-- pure-start
-- (no additional pure helpers required)
-- pure-end

-- post-conditions-start
/-- Finalizing contract. The result is an `Except` because conversion can fail
when attempted against a non-unit target; a correct finalizer must succeed on
every annotation shape:

* a concrete-unit annotation `unit u` yields success with the produced value
  converted to `u`;
* an absent annotation (`empty`) yields success with the produced value
  unchanged;
* a *no-unit* annotation (`noUnit`) ALSO yields success with the produced value
  unchanged — it must NOT attempt a conversion (which would fail). -/
def problem_spec_applyReturnAnnotation
    (annot : RetAnnotation) (ret : RetVal) (result : Except FinalizeError RetVal) : Prop :=
  (∀ u, annot = .unit u → result = .ok (convertTo ret u)) ∧
  (annot = .empty  → result = .ok ret) ∧
  (annot = .noUnit → result = .ok ret)
-- post-conditions-end

-- impl-start
def implementation_applyReturnAnnotation
    (annot : RetAnnotation) (ret : RetVal) : Except FinalizeError RetVal := Id.run do
  -- If the annotation designates a concrete unit, convert the produced value to
  -- it; otherwise (absent annotation or an explicit no-unit annotation) return
  -- the produced value unchanged, without attempting any conversion.
  match annot with
  | .unit u => return .ok (convertTo ret u)
  | _       => return .ok ret
-- impl-end

-- proof-start
theorem correct_applyReturnAnnotation :
    ∀ (annot : RetAnnotation) (ret : RetVal),
      problem_spec_applyReturnAnnotation annot ret
        (implementation_applyReturnAnnotation annot ret) := by
  intro annot ret
  cases annot with
  | empty =>
    refine ⟨?_, ?_, ?_⟩ <;> intro <;>
      simp_all [implementation_applyReturnAnnotation, Id.run, pure]
  | noUnit =>
    refine ⟨?_, ?_, ?_⟩ <;> intro <;>
      simp_all [implementation_applyReturnAnnotation, Id.run, pure]
  | unit u =>
    refine ⟨?_, ?_, ?_⟩ <;> intro <;>
      simp_all [implementation_applyReturnAnnotation, Id.run, pure]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec is a complete deterministic input->output relation over the 3-constructor inductive RetAnnotation: problem_spec pins .unit u -> .ok (convertTo ret u), .empty -> .ok ret, .noUnit -> .ok ret, exhausting the whole domain. Any verifying impl is provably pointwise-equal to gold, so verify<=>correct.

Attempted 7 DISTINCT same-spec (all same_spec=True) wrong impls; all fail lean_verify with genuine unsolved-goal errors, none closes: atk_1 prepatch bug noUnit->.error (exit 1; case noUnit.refine_3 leaves |- False); atk_2 always-passthrough never convert (exit 1, unit clause); atk_3 unit-branch forgets conversion (exit 1); atk_4 empty->.error boundary (exit 1, empty clause); atk_5 all-error-except-empty ungrounded (exit 1); atk_6 unit-branch->.error control-flow-effect (exit 1); atk_7 double-convert ungrounded-oracle echo convertTo (convertTo ret u) u (exit 1; needs opaque convertTo idempotence, unprovable). Positive control = exact gold: lean_verify exit 0; #print axioms correct_applyReturnAnnotation -> [propext] only (clean, no sorryAx).

Since NO wrong impl closed with clean axioms, step-2 resolve runs are vacuous (no faithful patch to materialize); patches={}. Commands: same_spec via swebench_unified.markers.same_spec with backend 'lean' -> True for all; per file 'bash scripts/lean_verify.sh <path>' -> pos_control exit=0, atk_1..7 exit=1; axiom check appended '#print axioms correct_applyReturnAnnotation' to pos_ax.lean -> exit 0, depends on axioms: [propext]. Ran verifications concurrently in two batches of <=4 background jobs.

Refinement audit (refinement.md): op1 guard/selector = R (three-way RetAnnotation refining Python 'not in (empty, None)'), op2 convertTo = A-reference (opaque, models unchanged Quantity.to on concrete-unit branch = line 224 return_.to(annot), no consumed property axiom; validated by G-AX + G-CONF against real patched decorator), op3 passthrough = I. No A-consumed and no kind-3 legs; A-reference correspondence to real Quantity.to holds and is called only on the concrete-unit arm as in the source. verify=>correct upheld.

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
None — no same-spec wrong implementation produced a closing clean-axiom proof, so there is nothing to break the spec.
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
Finalizing the result of a unit-validating function wrapper.

A function may declare, via its return annotation, the physical unit its result
should carry. After the wrapped function has produced a value, the wrapper turns
that raw value into the function's final result according to the annotation:

* if the annotation designates a concrete unit, the produced value is converted
  to that unit and the converted value is returned successfully;
* if the annotation is absent, or it explicitly designates *no unit at all*,
  the produced value is returned unchanged, successfully — no conversion is
  attempted.

The "no unit at all" annotation and the "absent" annotation are treated
identically here: both mean "leave the produced value exactly as it is". In
particular, finalizing succeeds for every annotation shape — designating *no
unit* never triggers a conversion (which on a value carrying no convertible
target would be a failure).

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- Dependency model used while finalizing the result, declared as opaque
-- signatures (the proof needs no property axiom about them — the contract is
-- stated directly over them and discharged by case analysis):
--
-- * `UnitObj`        : an opaque concrete physical unit that an annotation may name.
-- * `RetVal`         : the value the wrapped function produced.
-- * `convertTo r u`  : the value `r` re-expressed under the concrete unit `u`
--                      (the unchanged value conversion the wrapper performs on
--                      the concrete-unit branch only).

/-- An opaque concrete physical unit (e.g. metres, degrees). -/
opaque UnitObj : Type

/-- The value produced by the wrapped function. Its internal structure is opaque
to the contract; modeled as a one-field carrier so it is inhabited/computable. -/
structure RetVal where
  payload : Nat
deriving Inhabited, DecidableEq

/-- A function's declared return annotation. It is one of three shapes:

* `empty`   — no annotation was given;
* `noUnit`  — an annotation was given that explicitly designates *no unit*;
* `unit u`  — an annotation designating the concrete unit `u`. -/
inductive RetAnnotation where
  | empty
  | noUnit
  | unit (u : UnitObj)

/-- A finalization failure: attempting to convert a value to a unit when the
annotation does not actually name one (the value has no convertible target). -/
structure FinalizeError where
deriving Repr, DecidableEq, Inhabited

/-- The unchanged value conversion: re-express the produced value under a
*concrete* unit. Takes a `UnitObj` (never an absent/no-unit annotation), so the
primitive has no impossible states. Modeled as an opaque callee (an A-reference);
its behavior is validated against the real conversion by G-AX. -/
opaque convertTo : RetVal → UnitObj → RetVal
-- axioms-end

-- pure-start
-- (no additional pure helpers required)
-- pure-end

-- post-conditions-start
/-- Finalizing contract. The result is an `Except` because conversion can fail
when attempted against a non-unit target; a correct finalizer must succeed on
every annotation shape:

* a concrete-unit annotation `unit u` yields success with the produced value
  converted to `u`;
* an absent annotation (`empty`) yields success with the produced value
  unchanged;
* a *no-unit* annotation (`noUnit`) ALSO yields success with the produced value
  unchanged — it must NOT attempt a conversion (which would fail). -/
def problem_spec_applyReturnAnnotation
    (annot : RetAnnotation) (ret : RetVal) (result : Except FinalizeError RetVal) : Prop :=
  (∀ u, annot = .unit u → result = .ok (convertTo ret u)) ∧
  (annot = .empty  → result = .ok ret) ∧
  (annot = .noUnit → result = .ok ret)
-- post-conditions-end

-- impl-start
def implementation_applyReturnAnnotation
    (annot : RetAnnotation) (ret : RetVal) : Except FinalizeError RetVal := Id.run do
  -- If the annotation designates a concrete unit, convert the produced value to
  -- it; otherwise (absent annotation or an explicit no-unit annotation) return
  -- the produced value unchanged, without attempting any conversion.
  match annot with
  | .unit u => return .ok (convertTo ret u)
  | _       => return .ok ret
-- impl-end

-- proof-start
theorem correct_applyReturnAnnotation :
    ∀ (annot : RetAnnotation) (ret : RetVal),
      problem_spec_applyReturnAnnotation annot ret
        (implementation_applyReturnAnnotation annot ret) := by
  intro annot ret
  cases annot with
  | empty =>
    refine ⟨?_, ?_, ?_⟩ <;> intro <;>
      simp_all [implementation_applyReturnAnnotation, Id.run, pure]
  | noUnit =>
    refine ⟨?_, ?_, ?_⟩ <;> intro <;>
      simp_all [implementation_applyReturnAnnotation, Id.run, pure]
  | unit u =>
    refine ⟨?_, ?_, ?_⟩ <;> intro <;>
      simp_all [implementation_applyReturnAnnotation, Id.run, pure]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec is a complete deterministic input->output relation over the 3-constructor inductive RetAnnotation: problem_spec pins .unit u -> .ok (convertTo ret u), .empty -> .ok ret, .noUnit -> .ok ret, exhausting the whole domain. Any verifying impl is provably pointwise-equal to gold, so verify<=>correct.

Attempted 7 DISTINCT same-spec (all same_spec=True) wrong impls; all fail lean_verify with genuine unsolved-goal errors, none closes: atk_1 prepatch bug noUnit->.error (exit 1; case noUnit.refine_3 leaves |- False); atk_2 always-passthrough never convert (exit 1, unit clause); atk_3 unit-branch forgets conversion (exit 1); atk_4 empty->.error boundary (exit 1, empty clause); atk_5 all-error-except-empty ungrounded (exit 1); atk_6 unit-branch->.error control-flow-effect (exit 1); atk_7 double-convert ungrounded-oracle echo convertTo (convertTo ret u) u (exit 1; needs opaque convertTo idempotence, unprovable). Positive control = exact gold: lean_verify exit 0; #print axioms correct_applyReturnAnnotation -> [propext] only (clean, no sorryAx).

Since NO wrong impl closed with clean axioms, step-2 resolve runs are vacuous (no faithful patch to materialize); patches={}. Commands: same_spec via swebench_unified.markers.same_spec with backend 'lean' -> True for all; per file 'bash scripts/lean_verify.sh <path>' -> pos_control exit=0, atk_1..7 exit=1; axiom check appended '#print axioms correct_applyReturnAnnotation' to pos_ax.lean -> exit 0, depends on axioms: [propext]. Ran verifications concurrently in two batches of <=4 background jobs.

Refinement audit (refinement.md): op1 guard/selector = R (three-way RetAnnotation refining Python 'not in (empty, None)'), op2 convertTo = A-reference (opaque, models unchanged Quantity.to on concrete-unit branch = line 224 return_.to(annot), no consumed property axiom; validated by G-AX + G-CONF against real patched decorator), op3 passthrough = I. No A-consumed and no kind-3 legs; A-reference correspondence to real Quantity.to holds and is called only on the concrete-unit arm as in the source. verify=>correct upheld.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-drift / too-strong) check for astropy__astropy-7336 lean bundle.

### Setup verified
- same_spec(Solution.lean, Solution_prepatch.lean, lean-backend) = True: the frozen spec region (docstring + axioms + RetAnnotation/RetVal/FinalizeError/convertTo decls + problem_spec_applyReturnAnnotation) is byte-identical between patched and prepatch; only impl+proof differ, as required.
- Solution.lean compiles clean via scripts/lean_verify.sh (exit 0). #print axioms correct_applyReturnAnnotation => [propext] only; no sorryAx, proof is genuine.
- Worktree is at base_commit 732d89c2 with patch applied; real epilogue (decorators.py:223-226): `if return_annotation not in (Signature.empty, None): return return_.to(annot) else: return return_`.

MODELED FUNCTION = the return-finalizing epilogue of QuantityInput.__call__.<locals>.wrapper. Spec is the three-way relation over RetAnnotation:
  (∀u, annot=.unit u → result=.ok (convertTo ret u)) ∧ (annot=.empty → result=.ok ret) ∧ (annot=.noUnit → result=.ok ret).

### Domain-by-domain agreement with real patched callee
- empty  → real `else` branch → passthrough. Spec demands .ok ret. AGREES.
- None (noUnit) → real `else` branch (None now excluded by the `not in (...,None)` fix) → passthrough. Spec demands .ok ret. AGREES. This is exactly the F2P test_return_annotation_none (`-> None` returns value unchanged, asserts `solarx is None`).
- concrete unit → real `return_.to(u)`. Spec demands .ok (convertTo ret u). convertTo is an opaque A-reference explicitly delegated to G-AX to validate against real Quantity.to. AGREES within the abstracted total-callee domain.

STRONGEST DRIFT CANDIDATE considered and rejected: real `return_.to(u)` can raise (unit mismatch / non-Quantity return), whereas the model wraps it as .ok (convertTo ret u), never surfacing a failure on the concrete-unit arm. However convertTo is modeled opaquely and offloaded to G-AX by design; the raising behavior is not part of the frozen spec domain here. The .error outcome is exclusively a prepatch artifact modeling the None.to(...) AttributeError that the patch fixes — the patched code never errors on any of the three shapes for valid inputs, so the spec is NOT too strong: it does not force success where the real patched code fails, nor forbid a behavior the real code exhibits. No diverging input exists within the modeled domain.

The three-way RetAnnotation partition is a faithful type refinement of Python's `not in (empty, None)` guard (empty↔.empty, None↔.noUnit, concrete↔.unit u). Spec is neither too strong nor drifted from real repo behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical between Solution.lean and Solution_prepatch.lean (same_spec=True), so the spec view carries no impl-specific content. Mechanical leakage screen passes with no hard failures; recorded G-LEAK=pass; no relaxation flag/RELAXED_LEAKAGE.md. Spec view is a purely abstract Lean model (RetAnnotation empty/noUnit/unit, opaque convertTo, Except FinalizeError) and contains none of the gold-patch specifics: no `inspect.Signature.empty`, no `None`, no `.to`, no guard code, no patch/problem-statement wording. The decisive spec clause (noUnit -> result = .ok ret: an explicit no-unit annotation passes the value through and never attempts conversion) encodes exactly the correct behavior that the PUBLIC problem_statement already discloses — the statement describes the `-> None` AttributeError and even proposes 'check whether None is returned and then omit the unit check', and the empty (workaround: drop the hint) vs noUnit (`-> None`) distinction is also in the public text. The spec reveals nothing about the gold edit beyond the public problem_statement (hints_text not relied upon). NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.