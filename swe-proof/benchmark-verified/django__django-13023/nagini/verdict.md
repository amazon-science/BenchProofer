# P2 adversarial audit — django__django-13023

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 13 admissible attacks re-run of 13 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 13 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1_prepatch.py`, `atk_2_kind8_to_validation.py`, `atk_3_float_class_swap.py`, `atk_4_kind8_normal_return.py`, `atk_5_float_token_literal.py`, `atk_8_kind6_as_conversion_range.py`, `atk_9_literal_tag.py`, `atk_10_reverse_token_crossing.py`, `atk_12_vacuity_kind8.py`, `atk_13_diverge_kind8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_6_float_echo.py`, `atk_7_double_call.py`, `atk_11_full_echo.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (13):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -325,8 +325,4 @@
         return construct_numeric(kind)
     except ConstructorMalformedError:
         raise ValidationFailure()
-    except ConstructorOperandError:
-        raise ValidationFailure()
-    except ConstructorDomainError:
-        raise ValidationFailure()
     # impl-end
```

Attack 2 — `atk_2_kind8_to_validation.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -319,8 +319,13 @@
     # impl-start
     if kind == 0:
         return None
-    if kind == 1 or kind == 7 or kind == 8:
+    if kind == 1 or kind == 7:
         return convert_floating(kind)
+    if kind == 8:
+        try:
+            return convert_floating(kind)
+        except ConversionRangeError:
+            raise ValidationFailure()
     try:
         return construct_numeric(kind)
     except ConstructorMalformedError:
```

Attack 3 — `atk_3_float_class_swap.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -319,8 +319,18 @@
     # impl-start
     if kind == 0:
         return None
-    if kind == 1 or kind == 7 or kind == 8:
+    if kind == 1:
         return convert_floating(kind)
+    if kind == 7:
+        try:
+            return convert_floating(kind)
+        except ConstructorOperandError:
+            raise ConversionRangeError()
+    if kind == 8:
+        try:
+            return convert_floating(kind)
+        except ConversionRangeError:
+            raise ConstructorOperandError()
     try:
         return construct_numeric(kind)
     except ConstructorMalformedError:
```

Attack 4 — `atk_4_kind8_normal_return.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -319,7 +319,9 @@
     # impl-start
     if kind == 0:
         return None
-    if kind == 1 or kind == 7 or kind == 8:
+    if kind == 8:
+        return None
+    if kind == 1 or kind == 7:
         return convert_floating(kind)
     try:
         return construct_numeric(kind)
```

Attack 5 — `atk_5_float_token_literal.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -319,7 +319,9 @@
     # impl-start
     if kind == 0:
         return None
-    if kind == 1 or kind == 7 or kind == 8:
+    if kind == 1:
+        return 0
+    if kind == 7 or kind == 8:
         return convert_floating(kind)
     try:
         return construct_numeric(kind)
```

Attack 6 — `atk_6_float_echo.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -319,8 +319,12 @@
     # impl-start
     if kind == 0:
         return None
-    if kind == 1 or kind == 7 or kind == 8:
-        return convert_floating(kind)
+    if kind == 1:
+        return from_floating()
+    if kind == 7:
+        raise ConstructorOperandError()
+    if kind == 8:
+        raise ConversionRangeError()
     try:
         return construct_numeric(kind)
     except ConstructorMalformedError:
```

Attack 7 — `atk_7_double_call.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -320,8 +320,10 @@
     if kind == 0:
         return None
     if kind == 1 or kind == 7 or kind == 8:
+        first = convert_floating(kind)
         return convert_floating(kind)
     try:
+        probe = construct_numeric(kind)
         return construct_numeric(kind)
     except ConstructorMalformedError:
         raise ValidationFailure()
```

Attack 8 — `atk_8_kind6_as_conversion_range.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -329,4 +329,6 @@
         raise ValidationFailure()
     except ConstructorDomainError:
         raise ValidationFailure()
+    except ConstructorRangeError:
+        raise ConversionRangeError()
     # impl-end
```

Attack 9 — `atk_9_literal_tag.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -320,9 +320,9 @@
     if kind == 0:
         return None
     if kind == 1 or kind == 7 or kind == 8:
-        return convert_floating(kind)
+        return convert_floating(1)
     try:
-        return construct_numeric(kind)
+        return construct_numeric(2)
     except ConstructorMalformedError:
         raise ValidationFailure()
     except ConstructorOperandError:
```

Attack 10 — `atk_10_reverse_token_crossing.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -319,7 +319,9 @@
     # impl-start
     if kind == 0:
         return None
-    if kind == 1 or kind == 7 or kind == 8:
+    if kind == 1:
+        return accepted_value(2)
+    if kind == 7 or kind == 8:
         return convert_floating(kind)
     try:
         return construct_numeric(kind)
```

Attack 11 — `atk_11_full_echo.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -319,14 +319,15 @@
     # impl-start
     if kind == 0:
         return None
-    if kind == 1 or kind == 7 or kind == 8:
-        return convert_floating(kind)
-    try:
-        return construct_numeric(kind)
-    except ConstructorMalformedError:
+    if kind == 1:
+        return from_floating()
+    if kind == 2:
+        return accepted_value(2)
+    if kind == 3 or kind == 4 or kind == 5:
         raise ValidationFailure()
-    except ConstructorOperandError:
-        raise ValidationFailure()
-    except ConstructorDomainError:
-        raise ValidationFailure()
+    if kind == 6:
+        raise ConstructorRangeError()
+    if kind == 7:
+        raise ConstructorOperandError()
+    raise ConversionRangeError()
     # impl-end
```

Attack 12 — `atk_12_vacuity_kind8.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -317,6 +317,8 @@
     Exsures(ConversionRangeError, kind == 8)
     # post-conditions-end
     # impl-start
+    if kind == 8:
+        Assert(False)
     if kind == 0:
         return None
     if kind == 1 or kind == 7 or kind == 8:
```

Attack 13 — `atk_13_diverge_kind8.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -319,7 +319,13 @@
     # impl-start
     if kind == 0:
         return None
-    if kind == 1 or kind == 7 or kind == 8:
+    if kind == 8:
+        i = 0
+        while i >= 0:
+            Invariant(i >= 0)
+            i = i + 1
+        return None
+    if kind == 1 or kind == 7:
         return convert_floating(kind)
     try:
         return construct_numeric(kind)
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit, django__django-13023/nagini. 13 attacks, ALL same-spec rc=0 (adversary same-spec). Verification run as concurrent background batches of 3 (each Nagini check = 1 JVM+Z3); schedule only, every attack fully verified.

**POSITIVE CONTROL:** positive_control.py (verbatim model.py) -> `python -m swebench_unified.adversary weakness nagini django__django-13023 <path>` rc=0, CANDIDATE (shares spec AND verifies, 17.1s). So the frozen spec is satisfiable and the battery is live.

**PREPATCH REPRODUCED:** atk_1_prepatch.py (only ConstructorMalformedError converted; kinds 4/5 escape raw) -> weakness rc=2, 'attack does not verify'. G-DIFF holds.

### PER-ATTACK (command in every case: `python -m swebench_unified.adversary weakness nagini django__django-13023 <path>` from repo root):
1 atk_1_prepatch.py -- PREPATCH BUG. rc=2 REJECTED. 2 atk_2_kind8_to_validation.py -- CONVERTS TOO MUCH on the NEWEST leg: the float callee's ConversionRangeError (kind 8) swallowed into ValidationFailure. rc=2 REJECTED. 3 atk_3_float_class_swap.py -- BOUNDARY SWAP on the SAME callee: kinds 7 and 8 trade escape classes. rc=2 REJECTED. 4 atk_4_kind8_normal_return.py -- PARTIAL DOMAIN: kind 8 returns the null token (silent accept). rc=2 REJECTED. 5 atk_5_float_token_literal.py -- UNGROUNDED TOKEN on the FLOAT arm: kind 1 returns literal 0 instead of from_floating(). rc=2 REJECTED => the float-arm value pin is load-bearing.

6 atk_6_float_echo.py -- A-LEG ECHO on the float arm: convert_floating NEVER invoked as a propagating call; from_floating() read directly, kinds 7/8 raise their pinned classes from thin air. rc=0 CANDIDATE -> resolve RAN. 7 atk_7_double_call.py -- CONTROL-FLOW EFFECT: both callees invoked TWICE, first result discarded (the model cannot see the real float callee's Context-flag mutation). rc=0 CANDIDATE -> resolve RAN. 8 atk_8_kind6_as_conversion_range.py -- CLASS CROSSING across callees: the constructor's kind-6 range rejection escapes wearing the FLOAT callee's ConversionRangeError. rc=2 REJECTED.

9 atk_9_literal_tag.py -- LITERAL-TAG A-LEG attack (refinement.md A1b / mapping.md 3.4): convert_floating(1) / construct_numeric(2) at literal tags. rc=2 REJECTED => `Requires(kind == value_kind())` really removes calls that denote nothing the coercion performs. This is the central A1b claim, machine-confirmed. 10 atk_10_reverse_token_crossing.py -- REVERSE TOKEN CROSSING (direction the prior pass's atk_13 did not test): kind 1 returns accepted_value(2). Note accepted_value has only Requires(kind==2) and NO value_kind tie, so the literal call is legal and only the kind-1 postcondition can reject it -- it does. rc=2 REJECTED.

11 atk_11_full_echo.py -- MAXIMAL ORACLE ECHO: NEITHER accept-or-refuse callee invoked; both pure accessors read directly and all five rejection kinds raised from thin air. rc=0 CANDIDATE -> resolve RAN. 12 atk_12_vacuity_kind8.py -- VACUITY CONTROL on the newest leg: Assert(False) under kind==8 (prior passes controlled 4, 7 and 3/5/6 but never 8). rc=2 REJECTED => kind 8 is a FEASIBLE input, the kind-8 Exsures leg is a real obligation, not a free pass. 13 atk_13_diverge_kind8.py -- DIVERGENCE confined to kind 8 (correct elsewhere, non-terminating on 8). rc=2 REJECTED => MustTerminate(8) reaches the newest branch, so a hanging (test-timing-out) impl cannot verify there.

RESOLVE RUNS FOR ALL THREE CANDIDATEs (mandatory step; `run_resolve('django__django-13023', patch)` via swebench_unified.harness, script resolve.py, raw JSON in resolve_<attack>.json). Each faithful refined patch was materialized in a base_commit git worktree (the upstream repository @ f83b44075dafa429d59e8755aa47e15577cc49f9) and `git apply --check` PASSED for all three before submission:
 * atk_6_float_echo -> patch_atk_6_float_echo.diff. Faithful refinement: the float arm classifies the value's floating-branch shape against the real create_decimal_from_float (accept / TypeError / decimal.Overflow) and then EMITS that shape's outcome; constructor arm is the gold three-class handler. resolved=True, completed=True, patch_successfully_applied=True; F2P 2/2 failure 0, P2P 9/9 failure 0, PASS_TO_FAIL and FAIL_TO_FAIL empty.
 * atk_7_double_call -> patch_atk_7_double_call.diff. Faithful refinement: create_decimal_from_float and decimal.Decimal each called twice with the first result discarded. resolved=True, completed=True, applied=True; F2P 2/2, P2P 9/9, PASS_TO_FAIL/FAIL_TO_FAIL empty. The repeated-invocation effect the kind abstraction cannot see is genuinely unobserved by the oracle (both callees are pure w.r.t. every tested observation; the Context flag mutation is not asserted).
 * atk_11_full_echo -> patch_atk_11_full_echo.diff. Faithful refinement: BOTH arms classify into a kind variable and emit that kind's outcome; `except OverflowError: kind=6` re-raises OverflowError so kind 6 stays unconverted. resolved=True, completed=True, applied=True; F2P 2/2, P2P 9/9, PASS_TO_FAIL/FAIL_TO_FAIL empty.
All three are alternative shapes behaviourally equal to the gold patch on the tested inputs -- NOT counterexamples. No verifying wrong impl's patch failed to resolve, so verify=>resolve survives.

A-LEG CORRESPONDENCE AUDIT (executed on a base_commit worktree AND on the gold-patched tree, aleg.py; the R/I legs are G-CONF's). Every deep-model claim refinement.md makes about the real callees holds:
 * A3 kind-7: SimpleLazyObject(lambda: 1.5) -> isinstance(v,float)=True (branch IS taken) and to_python raises raw builtins.TypeError('argument must be int or float'), IDENTICALLY on base and gold-patched trees => not a patch delta, and the propagating leg is faithfulness not weakening.
 * A3 kind-8: class IntSpoofFloat(int) with `__class__`=float. `10**999999` -> normal return (kind 1); `10**1000000` -> raw decimal.Overflow; decimal.Decimal(W) SUCCEEDS on both, so it is genuinely NOT the kind-6 constructor arm. Emax=999999 boundary confirmed by direct measurement on both trees.
 * kind-6: to_python((0,(1,),`2**63`)) -> raw builtins.OverflowError('Python int too large to convert to C ssize_t') on BOTH trees, while the boundary (0,(1,),`2**63`-1) is ValidationError (kind 3). Confirms the unclassified-shape leg and the stated boundary.
 * Class disjointness (the load-bearing premise for five distinct stand-ins): decimal.Overflow MRO = Overflow->Inexact->Rounded->DecimalException->ArithmeticError->Exception; issubclass(Overflow, X) is False for X in {InvalidOperation, TypeError, ValueError, OverflowError}; OverflowError is a subclass of none of ValueError/TypeError/InvalidOperation. So kinds 6 and 8 are genuinely different classes from different callees and no handler catches either.
 * kind 3/4/5 binding vs the 8 exact F2P test_invalid_value inputs: () and [] -> ValueError (kind 5); {} , set(), object(), complex(), b'non-numeric byte-string' -> TypeError (kind 4); 'non-numeric string' -> InvalidOperation (kind 3). On the base tree these escape RAW; on the gold-patched tree all 8 become ValidationError. Exactly the mapping.md sec 1 binding, and kind 5 is oracle-FORCED (() and [] are in F2P), not narration.
 * kind-2 token pin: to_python(3)==Decimal('3'), to_python('3.14')==Decimal('3.14'), to_python(Decimal('2.5'))==Decimal('2.5') -- the P2P test_to_python observation, and atk_5/atk_10 confirm both value pins are load-bearing in both directions.

**REFINEMENT.MD LEG-KIND AUDIT:** the table's six legs are tagged R / R / R+I / R+A-consumed / A-consumed / R+I -- every leg is R, A-consumed or I. Section B explicitly declares no kind-3 (unexpressible-changed-op) step and no A-reference deep model, which is correct here: the change is an exception-classification widening modeled DIRECTLY by the three except clauses (A5) driven by construct_numeric's three Exsures (A4), not a value computation. The five axioms are all A-consumed and all correspond to real unchanged callees at lines 1501/1503 (verified above). No kind-3 leg present.

ONE DOCUMENTATION DEFECT (cosmetic, non-blocking, does NOT affect soundness or any machine check): refinement.md lines 157 and 177 still say the domain 'was WIDENED (`0 <= kind <= 7`)' and mapping.md line 293 still quotes value_kind's postcondition as `Ensures(0 <= Result() and Result() <= 7)` / 'verified at every kind in 0..7'. The frozen model.py actually has `Requires(0 <= kind and kind <= 8)` (line 270) and `Ensures(0 <= Result() and Result() <= 8)` (line 141) -- stale text from before the kind-8 leg was added. Everything substantive about kind 8 is correct and present elsewhere (refinement.md sec C enumerates all four Exsures legs including kind 8, and its 'three UNCLASSIFIED rejection kinds' count is right); these are three stale numerals in prose. I did NOT edit the bundle. Note the numerals are load-bearing for a reader auditing totality, so a repair pass should fix them; they misstate the domain bound by one, in the SAFE direction (understating coverage), and the actual spec is the wider one.

**VERDICT:** SOUND. 13 same-spec attacks executed (>=5 required), all reaching a verdict -- no timeouts, no crashes, no inconclusive results. 10 REJECTED by the spec (rc=2). 3 CANDIDATEs, and for EVERY one the faithful refined patch was materialized, `git apply --check`ed at base_commit, and RUN through the official harness: all three resolved=True with F2P 2/2 and P2P 9/9. No verifying wrong impl exists whose faithful patch fails to resolve, so verify=>correct holds for this bundle.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 13 admissible attacks re-run of 13 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 13 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1_prepatch.py`, `atk_2_kind8_to_validation.py`, `atk_3_float_class_swap.py`, `atk_4_kind8_normal_return.py`, `atk_5_float_token_literal.py`, `atk_8_kind6_as_conversion_range.py`, `atk_9_literal_tag.py`, `atk_10_reverse_token_crossing.py`, `atk_12_vacuity_kind8.py`, `atk_13_diverge_kind8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_6_float_echo.py`, `atk_7_double_call.py`, `atk_11_full_echo.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (13):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 13 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1_prepatch.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_kind8_to_validation.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_float_class_swap.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_kind8_normal_return.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_float_token_literal.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_float_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7_double_call.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8_kind6_as_conversion_range.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9_literal_tag.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10_reverse_token_crossing.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11_full_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 12 — `atk_12_vacuity_kind8.py` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13_diverge_kind8.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit, django__django-13023/nagini. 13 attacks, ALL same-spec rc=0 (adversary same-spec). Verification run as concurrent background batches of 3 (each Nagini check = 1 JVM+Z3); schedule only, every attack fully verified.

**POSITIVE CONTROL:** positive_control.py (verbatim model.py) -> `python -m swebench_unified.adversary weakness nagini django__django-13023 <path>` rc=0, CANDIDATE (shares spec AND verifies, 17.1s). So the frozen spec is satisfiable and the battery is live.

**PREPATCH REPRODUCED:** atk_1_prepatch.py (only ConstructorMalformedError converted; kinds 4/5 escape raw) -> weakness rc=2, 'attack does not verify'. G-DIFF holds.

### PER-ATTACK (command in every case: `python -m swebench_unified.adversary weakness nagini django__django-13023 <path>` from repo root):
1 atk_1_prepatch.py -- PREPATCH BUG. rc=2 REJECTED. 2 atk_2_kind8_to_validation.py -- CONVERTS TOO MUCH on the NEWEST leg: the float callee's ConversionRangeError (kind 8) swallowed into ValidationFailure. rc=2 REJECTED. 3 atk_3_float_class_swap.py -- BOUNDARY SWAP on the SAME callee: kinds 7 and 8 trade escape classes. rc=2 REJECTED. 4 atk_4_kind8_normal_return.py -- PARTIAL DOMAIN: kind 8 returns the null token (silent accept). rc=2 REJECTED. 5 atk_5_float_token_literal.py -- UNGROUNDED TOKEN on the FLOAT arm: kind 1 returns literal 0 instead of from_floating(). rc=2 REJECTED => the float-arm value pin is load-bearing.

6 atk_6_float_echo.py -- A-LEG ECHO on the float arm: convert_floating NEVER invoked as a propagating call; from_floating() read directly, kinds 7/8 raise their pinned classes from thin air. rc=0 CANDIDATE -> resolve RAN. 7 atk_7_double_call.py -- CONTROL-FLOW EFFECT: both callees invoked TWICE, first result discarded (the model cannot see the real float callee's Context-flag mutation). rc=0 CANDIDATE -> resolve RAN. 8 atk_8_kind6_as_conversion_range.py -- CLASS CROSSING across callees: the constructor's kind-6 range rejection escapes wearing the FLOAT callee's ConversionRangeError. rc=2 REJECTED.

9 atk_9_literal_tag.py -- LITERAL-TAG A-LEG attack (refinement.md A1b / mapping.md 3.4): convert_floating(1) / construct_numeric(2) at literal tags. rc=2 REJECTED => `Requires(kind == value_kind())` really removes calls that denote nothing the coercion performs. This is the central A1b claim, machine-confirmed. 10 atk_10_reverse_token_crossing.py -- REVERSE TOKEN CROSSING (direction the prior pass's atk_13 did not test): kind 1 returns accepted_value(2). Note accepted_value has only Requires(kind==2) and NO value_kind tie, so the literal call is legal and only the kind-1 postcondition can reject it -- it does. rc=2 REJECTED.

11 atk_11_full_echo.py -- MAXIMAL ORACLE ECHO: NEITHER accept-or-refuse callee invoked; both pure accessors read directly and all five rejection kinds raised from thin air. rc=0 CANDIDATE -> resolve RAN. 12 atk_12_vacuity_kind8.py -- VACUITY CONTROL on the newest leg: Assert(False) under kind==8 (prior passes controlled 4, 7 and 3/5/6 but never 8). rc=2 REJECTED => kind 8 is a FEASIBLE input, the kind-8 Exsures leg is a real obligation, not a free pass. 13 atk_13_diverge_kind8.py -- DIVERGENCE confined to kind 8 (correct elsewhere, non-terminating on 8). rc=2 REJECTED => MustTerminate(8) reaches the newest branch, so a hanging (test-timing-out) impl cannot verify there.

RESOLVE RUNS FOR ALL THREE CANDIDATEs (mandatory step; `run_resolve('django__django-13023', patch)` via swebench_unified.harness, script resolve.py, raw JSON in resolve_<attack>.json). Each faithful refined patch was materialized in a base_commit git worktree (the upstream repository @ f83b44075dafa429d59e8755aa47e15577cc49f9) and `git apply --check` PASSED for all three before submission:
 * atk_6_float_echo -> patch_atk_6_float_echo.diff. Faithful refinement: the float arm classifies the value's floating-branch shape against the real create_decimal_from_float (accept / TypeError / decimal.Overflow) and then EMITS that shape's outcome; constructor arm is the gold three-class handler. resolved=True, completed=True, patch_successfully_applied=True; F2P 2/2 failure 0, P2P 9/9 failure 0, PASS_TO_FAIL and FAIL_TO_FAIL empty.
 * atk_7_double_call -> patch_atk_7_double_call.diff. Faithful refinement: create_decimal_from_float and decimal.Decimal each called twice with the first result discarded. resolved=True, completed=True, applied=True; F2P 2/2, P2P 9/9, PASS_TO_FAIL/FAIL_TO_FAIL empty. The repeated-invocation effect the kind abstraction cannot see is genuinely unobserved by the oracle (both callees are pure w.r.t. every tested observation; the Context flag mutation is not asserted).
 * atk_11_full_echo -> patch_atk_11_full_echo.diff. Faithful refinement: BOTH arms classify into a kind variable and emit that kind's outcome; `except OverflowError: kind=6` re-raises OverflowError so kind 6 stays unconverted. resolved=True, completed=True, applied=True; F2P 2/2, P2P 9/9, PASS_TO_FAIL/FAIL_TO_FAIL empty.
All three are alternative shapes behaviourally equal to the gold patch on the tested inputs -- NOT counterexamples. No verifying wrong impl's patch failed to resolve, so verify=>resolve survives.

A-LEG CORRESPONDENCE AUDIT (executed on a base_commit worktree AND on the gold-patched tree, aleg.py; the R/I legs are G-CONF's). Every deep-model claim refinement.md makes about the real callees holds:
 * A3 kind-7: SimpleLazyObject(lambda: 1.5) -> isinstance(v,float)=True (branch IS taken) and to_python raises raw builtins.TypeError('argument must be int or float'), IDENTICALLY on base and gold-patched trees => not a patch delta, and the propagating leg is faithfulness not weakening.
 * A3 kind-8: class IntSpoofFloat(int) with `__class__`=float. `10**999999` -> normal return (kind 1); `10**1000000` -> raw decimal.Overflow; decimal.Decimal(W) SUCCEEDS on both, so it is genuinely NOT the kind-6 constructor arm. Emax=999999 boundary confirmed by direct measurement on both trees.
 * kind-6: to_python((0,(1,),`2**63`)) -> raw builtins.OverflowError('Python int too large to convert to C ssize_t') on BOTH trees, while the boundary (0,(1,),`2**63`-1) is ValidationError (kind 3). Confirms the unclassified-shape leg and the stated boundary.
 * Class disjointness (the load-bearing premise for five distinct stand-ins): decimal.Overflow MRO = Overflow->Inexact->Rounded->DecimalException->ArithmeticError->Exception; issubclass(Overflow, X) is False for X in {InvalidOperation, TypeError, ValueError, OverflowError}; OverflowError is a subclass of none of ValueError/TypeError/InvalidOperation. So kinds 6 and 8 are genuinely different classes from different callees and no handler catches either.
 * kind 3/4/5 binding vs the 8 exact F2P test_invalid_value inputs: () and [] -> ValueError (kind 5); {} , set(), object(), complex(), b'non-numeric byte-string' -> TypeError (kind 4); 'non-numeric string' -> InvalidOperation (kind 3). On the base tree these escape RAW; on the gold-patched tree all 8 become ValidationError. Exactly the mapping.md sec 1 binding, and kind 5 is oracle-FORCED (() and [] are in F2P), not narration.
 * kind-2 token pin: to_python(3)==Decimal('3'), to_python('3.14')==Decimal('3.14'), to_python(Decimal('2.5'))==Decimal('2.5') -- the P2P test_to_python observation, and atk_5/atk_10 confirm both value pins are load-bearing in both directions.

**REFINEMENT.MD LEG-KIND AUDIT:** the table's six legs are tagged R / R / R+I / R+A-consumed / A-consumed / R+I -- every leg is R, A-consumed or I. Section B explicitly declares no kind-3 (unexpressible-changed-op) step and no A-reference deep model, which is correct here: the change is an exception-classification widening modeled DIRECTLY by the three except clauses (A5) driven by construct_numeric's three Exsures (A4), not a value computation. The five axioms are all A-consumed and all correspond to real unchanged callees at lines 1501/1503 (verified above). No kind-3 leg present.

ONE DOCUMENTATION DEFECT (cosmetic, non-blocking, does NOT affect soundness or any machine check): refinement.md lines 157 and 177 still say the domain 'was WIDENED (`0 <= kind <= 7`)' and mapping.md line 293 still quotes value_kind's postcondition as `Ensures(0 <= Result() and Result() <= 7)` / 'verified at every kind in 0..7'. The frozen model.py actually has `Requires(0 <= kind and kind <= 8)` (line 270) and `Ensures(0 <= Result() and Result() <= 8)` (line 141) -- stale text from before the kind-8 leg was added. Everything substantive about kind 8 is correct and present elsewhere (refinement.md sec C enumerates all four Exsures legs including kind 8, and its 'three UNCLASSIFIED rejection kinds' count is right); these are three stale numerals in prose. I did NOT edit the bundle. Note the numerals are load-bearing for a reader auditing totality, so a repair pass should fix them; they misstate the domain bound by one, in the SAFE direction (understating coverage), and the actual spec is the wider one.

**VERDICT:** SOUND. 13 same-spec attacks executed (>=5 required), all reaching a verdict -- no timeouts, no crashes, no inconclusive results. 10 REJECTED by the spec (rc=2). 3 CANDIDATEs, and for EVERY one the faithful refined patch was materialized, `git apply --check`ed at base_commit, and RUN through the official harness: all three resolved=True with F2P 2/2 and P2P 9/9. No verifying wrong impl exists whose faithful patch fails to resolve, so verify=>correct holds for this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

FAITHFULNESS-BREAK attack on django__django-13023/nagini. Reference = base_commit f83b4407 worktree () with patch.diff APPLIED (), per the brief; base used only for callees the patch does not touch.

**SPEC INTEGRITY:** `adversary same-spec` on an unmodified copy of model.py => exit 0 (byte-identical spec region). `nagini_verify.sh` on it => Verification successful (14.2s).

WHAT THE SPEC CLAIMS (coerce_to_numeric, kinds 0..8): normal return only on 0/1/2 with the result value-pinned (0->None, 1->from_floating(), 2->accepted_value(kind)); ValidationFailure on exactly {3,4,5}; and three RAW-PROPAGATION legs, ConstructorRangeError on 6, ConstructorOperandError on 7, ConversionRangeError on 8. The propagation legs are where a too-strong spec would hide, so I attacked totality of the value->kind map and each leg's real class.

### EVIDENCE THE SPEC IS NOT TOO STRONG (real repo == modeled function):
1. Per-config differential sweep (defin.py): 12 DecimalField configs (max_digits in {None,1,2,4,5,10,28,50,1000,999999,True}) x 862 values = 10344 comparisons; each value lowered to a kind by the REAL callees, spec prediction vs real to_python. Result: 0 DIVERGENCES, 0 NO-KIND. Kind histogram {0:12,1:156,2:336,3:4704,4:120,5:4632,6:312,7:72}.
2. Value fuzz (fuzz.py): 24018 probes (random strings over printable+unicode-digit+inf/nan alphabets, random coordinate tuples/lists straddling the C ssize_t/long boundaries, random ints/floats/Decimals, float subclasses, +-0.0, +-inf, nan, float_info.max/min, 5e-324) => 0 divergences, 0 NO-KIND.
3. Broad type sweep (final.py): 36 exotic types (memoryview, deque, array, Fraction, PurePath, datetime, uuid, generators, slice, property, bare classes, ...) => 0 divergences. Values with exception-raising `__repr__`/`__str__`/`__hash__` still yield ValidationError (kind 4/5), so ValidationError construction does not leak a foreign class.
4. Each propagation leg confirmed on the REAL patched tree, and confirmed NOT a patch delta (base==patched):
   - kind 6: to_python((0,(1,),`2**63`)) and ((0,(`10**100`,),0)) raise raw OverflowError on BOTH base and patched. Boundary respected: (0,(1,),`2**63`-1)/(0,(1,),-`2**63`) are kind 3 (-> ValidationError).
   - kind 7: isinstance(v,float) True while create_decimal_from_float refuses with TypeError. 13 independent witnesses all give raw TypeError on BOTH trees: SimpleLazyObject(lambda:1.5), `__class__`-attribute spoofer, `__class__`-property spoofer, MagicMock/Mock/NonCallableMock(spec=float), str/Decimal/bytes/tuple/complex subclasses with `__class__`=float. Correctly NOT confused with kind 4: SimpleLazyObject(lambda:3) and (lambda:'a') are isinstance-False and give ValidationError.
   - kind 8: IntSpoofFloat(int) with `__class__`=float. `10**1000000` -> raw decimal.Overflow at line 1501 (isinstance(...,TypeError/ValueError/OverflowError/InvalidOperation) all False); decimal.Decimal(W) succeeds, so genuinely NOT the kind-6 constructor arm. Accepting side of the Emax boundary holds: `10**999999` converts normally (kind 1). Precision-independent (Emax stays 999999 for every max_digits).
5. No 5th rejection class found for either callee. Constructor under MAXIMAL thread-context traps (Overflow/Inexact/Rounded/Subnormal/Underflow/Clamped/FloatOperation all on, prec=1, Emax=1): every rejection still lands in {InvalidOperation,TypeError,ValueError,OverflowError} - no undeclared class. create_decimal_from_float over prec in {1,4,28,50} on genuine floats incl. subnormals/subclasses/inf/nan: 0 raises; on guard-satisfiers only TypeError or decimal.Overflow.
6. Thread-local decimal context axis (ctxaxis.py): default, all-traps-OFF (where 'abc'/''/1e(`9*400`) legitimately become kind 2 and to_python returns Decimal('NaN')), and prec=1/Emax=2/InvalidOperation-trapped. The spec tracks the real function in ALL three because the kind is derived from the real callee under the same context - 0 divergences. So the spec is not silently pinned to one context.

PATCH DELTA CORRECTLY LOCATED (basepatch.py, base vs patched): {} , () , b'1', set(), complex(1), [1,2] flip from raw TypeError/ValueError to ValidationError (= kinds 4/5, the classified legs). The three propagation legs (kind 6 OverflowError, kind 7 TypeError) are IDENTICAL on both trees, so declaring them is faithful widening, not spec drift onto the patch delta.

NON-VACUITY / TIGHTNESS CONTROLS (all keep the spec byte-identical via same-spec, all correctly FAIL to verify - so the propagation legs are not escape hatches):
  ctlA Assert(False) -> 'Assertion False might not hold' (spec is not vacuous)
  ctlB returns normally on kind 7 -> fails Ensures(kind==0 or 1 or 2)
  ctlC prepatch shape (kinds 4/5 escape) -> fails Exsures(...,kind==7): declaring kind 7 does NOT open a door for kind 4, despite both being TypeError
  ctlD blanket handler also swallowing kind 6 -> fails Exsures(ValidationFailure, kind in {3,4,5})
  ctlE drops the kind-2 value pin (return 1) -> fails Result()==accepted_value(kind)

**BUNDLE GATES REPRODUCED:** axiom_check.py exit 0 (no 5th constructor class in a 40000-input cross-arm census; both float-callee refusals confirmed with the accepting side of the Emax boundary). conformance_check.py against my patched tree => 'G-CONF OK ... 100136 inputs (136 boundary + 100000 fuzz), 0 disagreements, out_of_domain 0'.

HOST ARTIFACT RULED OUT (recorded so it is not re-litigated as a finding): my first bare `python3 conformance_check.py` reported a DISAGREEMENT on {} (shadow=validation-failure vs real=raw TypeError). That was NOT a spec defect - `django` resolved to an unrelated, UNPATCHED copy of Django, so the oracle side of the comparison was the pre-patch function. The gate itself runs this in docker against a patched /testbed. Pinned to the patched tree instead, and with `PATCHED` confirmed by inspecting the imported to_python source, the check passes clean. Judging that echo as UNFAITHFUL would have invented spec drift out of an environment defect.

ONE HONEST SCOPE NOTE (not a defect): outside the field's documented domain the modeled function can be out-run by the real one - max_digits values that make decimal.Context(prec=...) itself raise (0, -1, 4.5, '4', >MAX_PREC) make to_python(1.5) raise raw ValueError/TypeError/OverflowError from the `self.context` property at line 1501, before any modeled callee. Those values lower to NO kind. But this is a field-CONFIGURATION axis, not the coercion's `value` argument, which is what the spec's domain (0<=kind<=8, kind==value_kind()) quantifies over; max_digits<=0 is rejected by Django's own system check fields.E133, and non-int max_digits is outside the field's contract. mapping.md declares the modeled binding as the F2P shape DecimalField(max_digits=4, decimal_places=2) and the callee is applied to the value in scope. For every well-configured field I tested (11 configs, incl. max_digits=None/1/True/999999) the value->kind map is TOTAL and the spec agrees exactly.

**CONCLUSION:** I could not find any input on which the modeled coercion disagrees with the real patched DecimalField.to_python. The spec is total over the rejection space (four mutually exclusive Exsures legs plus three value-pinned normal returns), each propagation leg is a measured property of the real function on BOTH trees rather than a weakening, and the tightness controls confirm the legs do not admit the prepatch or a blanket handler. Verdict FAITHFUL; no diverging input.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

STRICT-MODE JUDGEMENT — NO RELAXATION IN PLAY. I checked for the documented-relaxation shape first and it does NOT apply to this bundle: (a) no RELAXED_LEAKAGE.md in the nagini bundle (`find` over the nagini dir -> nothing; the ONLY RELAXED_LEAKAGE.md under this instance is in the sibling **velvet** bundle, a different bundle whose disposition does not travel here); (b) `meta.json` has NO `relaxed_leakage` key (top-level keys enumerated: additional_change_sites, axioms, base_commit, changed_files, deep_model_references, float_encoding, gates, instance_id, modeled_functions, patch_diff, prepatch_models, refinement_history, region_hashes, repo, schema_version, string_modeling, version); (c) live gate run `gates.leak.run(Bundle('django__django-13023', get_backend('nagini')))` -> status=pass, detail='spec view clean', failures=[] — i.e. status is 'pass', not 'relaxed'. So there is no relaxation argument to re-derive; this is an ordinary strict leakage judgement, and I made it from my own measurements.

**BUNDLE-DIRECTED-AT-ME CHECK:** ran `leakage.reviewer_directed()` over all 11 bundle files (model.py, model_prepatch.py, mapping.md, refinement.md, verdict.md, meta.json, axiom_check.py, conformance_check.py, properties.py, pbt_result.json, plus one transient build artifact) -> [] for every one. No file addresses me, instructs me how to record, or names an 'honest' verdict. meta.json DOES carry a prior G-PANEL-3 note stamped NO-LEAKAGE; I treated that as a ledger entry only and re-derived every measurement below independently. Bundle never modified (all work in /tmp; `git status --porcelain` on the instance dir shows only pre-existing modifications to conformance_check.py/meta.json, none from me).

PROCESS NOTE (measurement hygiene): my first spec-view dump went to a fixed path specview.txt and came back with docstring line 1 reading `django__django-13410` — a concurrent agent had clobbered the file. I discarded that scan entirely and redid it against a `mktemp` path (sv3_wAz4bP.txt, line 1 = `django__django-13023`). Every token count below is from the re-run.

**WHAT THE GOLD EDIT IS.** Single hunk, django/db/models/fields/`__init__`.py:1504: `except decimal.InvalidOperation:` -> `except (decimal.InvalidOperation, TypeError, ValueError):`. Public problem_statement names only: DecimalField.to_python, dict values, TypeError, ValidationError. Token scan of the PS: `ValueError` 0 hits, `InvalidOperation` 0 hits. hints_text is EMPTY (len 0), so nothing here is excused by the hints exclusion.

1. SPEC VIEW DERIVED MECHANICALLY (not by eye): `markers.spec_view(model.py, nagini)` -> 321 lines / 17729 chars, impl region correctly collapsed to `...  # implementation elided`. Spec-region integrity: `adversary same-spec nagini django__django-13023` on a verbatim copy -> exit 0 ('SAME'). `scripts/nagini_verify.sh` on the verbatim model -> 'Verification successful', 13.34s, exit 0 (positive control holds).

2. **MECHANICAL SCREEN:** `leakage.screen(model.py, nagini, gold_patch, problem_statement, test_patch)` -> passed=True, hard_failures=[], warnings=[]. Independent regex probe of the rendered view: ZERO hits for InvalidOperation | TypeError | ValueError | OverflowError | ValidationError | decimal | Decimal | to_python | DecimalField | create_decimal_from_float | fields/`__init__` | db.models | 'except decimal' | 'sequence of length' | max_digits | Emax | isinstance | float( | tuple | list | dict, and zero for every diff marker (@@, 'diff --git', '+++ ', '--- ', '\nindex '), zero for line numbers 1501/1503/1504/1509. `leakage._NARRATION_RE` -> 0 matching lines. 'django' appears exactly once, in the instance label `django__django-13023` on docstring line 1 (already agent-visible). Symbol collision: the patch's only distinctive changed symbol is `to_python`; the spec view's 24 identifiers (coerce_to_numeric, construct_numeric, convert_floating, value_kind, accepted_value, from_floating, ConstructorMalformedError/OperandError/DomainError/RangeError, ConversionRangeError, ValidationFailure, ...) embed none of it.

3. THE ONE NON-PS FACET, AND WHY IT IS NOT A LEAK. The spec pins THREE converted rejection shapes: kind 3 'malformed-literal', kind 4 'wrong-typed-operand', kind 5 'out-of-domain argument'. Kind 4 is the PS's own TypeError-on-dict facet; kind 3 is pre-patch repo behavior the solver reads straight off base_commit (`except decimal.InvalidOperation:` is the UNCHANGED line, and pre-existing P2P test_to_python already pinned 'abc' -> ValidationError). Kind 5 is the only shape with no PS token. I confirmed it is load-bearing spec weight rather than smuggled narration by the strip test: atk_no_kind5.py deletes ONLY `except ConstructorDomainError: raise ValidationFailure()` from the IMPL region (same-spec -> exit 0, spec byte-identical) and nagini_verify -> 'Verification failed ... Assertion "method only raises exceptions of types ValidationFailure, ConstructorRangeError, ConstructorOperandError, ConversionRangeError" might not hold.' Stripping it breaks the proof, so the clause carries real weight. It is also oracle-forced, not gratuitous: I executed the real constructor — decimal.Decimal(()) and decimal.Decimal([]) raise **ValueError** ('argument must be a sequence of length 3'), while {} / set() / object() / complex() / b'non-numeric' all raise TypeError and 'abc' raises InvalidOperation. F2P test_invalid_value (read from test_patch) asserts ValidationError for all eight of (), [], {}, set(), object(), complex(), 'non-numeric string', b'non-numeric byte-string' — so a spec omitting kind 5 could not imply G-RESOLVE. Control: stripping the PS-PUBLIC kind-4 handler also fails verification, confirming the strip test discriminates rather than always failing.

4. **WHY THE FACET DOES NOT RECONSTRUCT THE EDIT.** Kind 5 is named only as an abstract acceptance shape — 'the constructor rejects the value as an out-of-domain argument' — over an integer tag, with a user-defined stand-in class `ConstructorDomainError`. Nothing maps it onto `ValueError`, onto the tuple/list-of-wrong-length input family, onto `except`, onto a tuple-broadening edit, or onto to_python's source. A consumer reading the spec view learns 'three classified rejection shapes must all surface as one uniform validation failure' — the abstract desired behavior the issue demands — not 'add TypeError and ValueError to the except clause on line 1504'. Crucially the spec view is stated purely as DESIRED behavior with no prepatch contrast: I scanned for comparative/mechanism phrasing (no longer, used to, previously, instead of, formerly, now also, was only, single-member, three-member, broaden, widen, added, omitted, missing, failed to, only one, narrow) -> ZERO hits. There is no bug->fix narration to invert. The spec view also pins three UNCLASSIFIED escape shapes (kinds 6/7/8) that are NOT part of the gold edit at all, which further dilutes rather than localizes any edit signal.

5. CORE GATES I CONFIRMED MYSELF (so the record is my measurement): G-LEAK live re-run -> pass/clean/[]. G-VERIFY positive control -> 'Verification successful' 13.34s. G-DIFF -> model_prepatch.py shares the spec (same-spec exit 0) and FAILS for the right reason ('Postcondition ... Assertion (kind == 7) might not hold'), so the spec does see the delta. G-RESOLVE recorded resolved (attempts 1, flaky false).

**CONCLUSION:** the spec view reveals no gold-diff line, no patched file/function/line, no identifier echoing a patched symbol, and no bug->fix mechanism. The single non-PS facet (a third converted rejection shape) is F2P-forced, load-bearing under a machine strip test, and stated at an abstraction level that does not reconstruct the edit. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
