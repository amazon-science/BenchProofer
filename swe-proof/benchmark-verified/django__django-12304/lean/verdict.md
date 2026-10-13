# P2 adversarial audit — django__django-12304

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1_prepatch.lean`, `atk_2_partial.lean`, `atk_3_reverse.lean`, `atk_4_cfeffect.lean`, `atk_5_emptymap.lean`, `atk_7_tail.lean`, `atk_8_parity.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
none — spec is fully deterministic; no verifying wrong-impl exists whose faithful patch fails to resolve
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -71,10 +71,8 @@
 def implementation_buildChoicesClass
     (memberValues : List (Int × String)) : ChoicesClass := Id.run do
   let mut cls : ChoicesClass := { value2label := memberValues, doNotCallInTemplates := false }
-  -- The value→label association is built from the class's members.
   cls := { cls with value2label := memberValues }
-  -- Flag the class so a template engine leaves it intact instead of invoking it.
-  cls := { cls with doNotCallInTemplates := true }
+  -- BUG: never set the flag (prepatch behavior)
   return cls
 -- impl-end
 
```

Attack 2 — `atk_2_partial.lean` → rejected (same spec, does not verify — good)

```diff
@@ -69,13 +69,8 @@
 
 -- impl-start
 def implementation_buildChoicesClass
-    (memberValues : List (Int × String)) : ChoicesClass := Id.run do
-  let mut cls : ChoicesClass := { value2label := memberValues, doNotCallInTemplates := false }
-  -- The value→label association is built from the class's members.
-  cls := { cls with value2label := memberValues }
-  -- Flag the class so a template engine leaves it intact instead of invoking it.
-  cls := { cls with doNotCallInTemplates := true }
-  return cls
+    (memberValues : List (Int × String)) : ChoicesClass :=
+  { value2label := memberValues, doNotCallInTemplates := memberValues.isEmpty }
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3_reverse.lean` → rejected (same spec, does not verify — good)

```diff
@@ -69,13 +69,8 @@
 
 -- impl-start
 def implementation_buildChoicesClass
-    (memberValues : List (Int × String)) : ChoicesClass := Id.run do
-  let mut cls : ChoicesClass := { value2label := memberValues, doNotCallInTemplates := false }
-  -- The value→label association is built from the class's members.
-  cls := { cls with value2label := memberValues }
-  -- Flag the class so a template engine leaves it intact instead of invoking it.
-  cls := { cls with doNotCallInTemplates := true }
-  return cls
+    (memberValues : List (Int × String)) : ChoicesClass :=
+  { value2label := memberValues.reverse, doNotCallInTemplates := true }
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4_cfeffect.lean` → rejected (same spec, does not verify — good)

```diff
@@ -71,10 +71,9 @@
 def implementation_buildChoicesClass
     (memberValues : List (Int × String)) : ChoicesClass := Id.run do
   let mut cls : ChoicesClass := { value2label := memberValues, doNotCallInTemplates := false }
-  -- The value→label association is built from the class's members.
-  cls := { cls with value2label := memberValues }
-  -- Flag the class so a template engine leaves it intact instead of invoking it.
   cls := { cls with doNotCallInTemplates := true }
+  -- effect clobbered afterwards
+  cls := { cls with doNotCallInTemplates := false }
   return cls
 -- impl-end
 
```

Attack 5 — `atk_5_emptymap.lean` → rejected (same spec, does not verify — good)

```diff
@@ -69,13 +69,8 @@
 
 -- impl-start
 def implementation_buildChoicesClass
-    (memberValues : List (Int × String)) : ChoicesClass := Id.run do
-  let mut cls : ChoicesClass := { value2label := memberValues, doNotCallInTemplates := false }
-  -- The value→label association is built from the class's members.
-  cls := { cls with value2label := memberValues }
-  -- Flag the class so a template engine leaves it intact instead of invoking it.
-  cls := { cls with doNotCallInTemplates := true }
-  return cls
+    (memberValues : List (Int × String)) : ChoicesClass :=
+  { value2label := [], doNotCallInTemplates := true }
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -69,13 +69,8 @@
 
 -- impl-start
 def implementation_buildChoicesClass
-    (memberValues : List (Int × String)) : ChoicesClass := Id.run do
-  let mut cls : ChoicesClass := { value2label := memberValues, doNotCallInTemplates := false }
-  -- The value→label association is built from the class's members.
-  cls := { cls with value2label := memberValues }
-  -- Flag the class so a template engine leaves it intact instead of invoking it.
-  cls := { cls with doNotCallInTemplates := true }
-  return cls
+    (memberValues : List (Int × String)) : ChoicesClass :=
+  { value2label := memberValues, doNotCallInTemplates := true }
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7_tail.lean` → rejected (same spec, does not verify — good)

```diff
@@ -69,13 +69,8 @@
 
 -- impl-start
 def implementation_buildChoicesClass
-    (memberValues : List (Int × String)) : ChoicesClass := Id.run do
-  let mut cls : ChoicesClass := { value2label := memberValues, doNotCallInTemplates := false }
-  -- The value→label association is built from the class's members.
-  cls := { cls with value2label := memberValues }
-  -- Flag the class so a template engine leaves it intact instead of invoking it.
-  cls := { cls with doNotCallInTemplates := true }
-  return cls
+    (memberValues : List (Int × String)) : ChoicesClass :=
+  { value2label := memberValues.tail, doNotCallInTemplates := true }
 -- impl-end
 
 -- proof-start
```

Attack 8 — `atk_8_parity.lean` → rejected (same spec, does not verify — good)

```diff
@@ -69,13 +69,8 @@
 
 -- impl-start
 def implementation_buildChoicesClass
-    (memberValues : List (Int × String)) : ChoicesClass := Id.run do
-  let mut cls : ChoicesClass := { value2label := memberValues, doNotCallInTemplates := false }
-  -- The value→label association is built from the class's members.
-  cls := { cls with value2label := memberValues }
-  -- Flag the class so a template engine leaves it intact instead of invoking it.
-  cls := { cls with doNotCallInTemplates := true }
-  return cls
+    (memberValues : List (Int × String)) : ChoicesClass :=
+  { value2label := memberValues, doNotCallInTemplates := (memberValues.length % 2 == 0) }
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Making an enumerated-choices class usable as a value inside a template.

An enumerated-choices class bundles a set of members; each member carries a
stored value together with a human-readable label, and the class exposes the
value→label association built from its members.

A template engine, when it resolves a name to a value and finds that value is
callable, will by default INVOKE it with no arguments and substitute the result.
An enumerated-choices class is itself callable — invoking it performs a value
lookup and therefore demands an argument — so invoking it with no arguments
fails, and the member/attribute the template actually wanted (e.g. a member and
then its label or value) can never be reached.

A value may carry a flag that tells the engine NOT to invoke it. The desired
behavior is that the constructed class carries this flag, so that when the engine
encounters the class as a resolved value it leaves the class untouched instead of
calling it — letting the subsequent member and attribute lookups proceed. The
value→label association the class exposes is unchanged by this.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The members'
-- (value, label) entries enter as plain data, the value→label association is
-- that same data carried through unchanged, the "do not invoke" flag is a
-- literal, and the engine's invoke decision is modeled directly as a boolean over
-- the three observables it reads (is the value callable, does it carry the
-- "do not invoke" flag, does it alter data). Hence no `opaque`/`axiom` callee
-- contract is required.
-- axioms-end

-- pure-start
/-- The constructed enumerated-choices class, restricted to the touched
observables:
* `value2label` — the value→label association built from the class's members;
* `doNotCallInTemplates` — whether the class is flagged so a template engine must
  NOT invoke it when it is encountered as a resolved value. -/
structure ChoicesClass where
  value2label : List (Int × String)
  doNotCallInTemplates : Bool

/-- A template engine's decision, when a resolved value is encountered, of whether
to INVOKE it with no arguments: it invokes exactly the values that are callable,
not flagged against invocation, and that do not alter data. Mirrors the engine's
resolution arm. -/
def templateWouldCall (isCallable doNotCall altersData : Bool) : Bool :=
  isCallable && !doNotCall && !altersData
-- pure-end

-- post-conditions-start
/-- The constructed class is pinned at every observable:

  * its value→label association is exactly the one built from the supplied
    members (unchanged — directive 5 frame: this component equals its input);
  * it is flagged so that a template engine encountering the class as a resolved
    value would NOT invoke it. Because such a class is callable and does not alter
    data, "would not be invoked" forces the flag to be set, which is precisely
    what lets the engine leave the class intact and resolve a member and its
    attribute against it. -/
def problem_spec_buildChoicesClass
    (memberValues : List (Int × String)) (result : ChoicesClass) : Prop :=
  result.value2label = memberValues ∧
  templateWouldCall (isCallable := true) result.doNotCallInTemplates
      (altersData := false) = false
-- post-conditions-end

-- impl-start
def implementation_buildChoicesClass
    (memberValues : List (Int × String)) : ChoicesClass := Id.run do
  let mut cls : ChoicesClass := { value2label := memberValues, doNotCallInTemplates := false }
  -- The value→label association is built from the class's members.
  cls := { cls with value2label := memberValues }
  -- Flag the class so a template engine leaves it intact instead of invoking it.
  cls := { cls with doNotCallInTemplates := true }
  return cls
-- impl-end

-- proof-start
theorem correct_buildChoicesClass :
    ∀ (memberValues : List (Int × String)),
      problem_spec_buildChoicesClass memberValues
        (implementation_buildChoicesClass memberValues) := by
  intro memberValues
  refine ⟨rfl, rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec post-condition pins BOTH observables for ALL inputs: result.value2label = memberValues (exact list equality, order-sensitive) AND templateWouldCall true d false = false which reduces to d = true. Fully deterministic spec.

Same-spec check: all 8 attacks + pos_control return same_spec=True (spec_view collapses impl AND proof regions; I edited only the impl region byte-for-byte otherwise).

Verification (scripts/lean_verify.sh, 300s, run concurrently in batches of <=4):
- pos_control.lean: EXIT 0 (verifies, no sorry). #print axioms correct_buildChoicesClass -> 'does not depend on any axioms'.
- atk_1_prepatch (flag stays false): EXIT 1 (proof fails to close) — prepatch bug correctly rejected; the discriminating clause templateWouldCall true false false = true != false is unprovable.
- atk_2_partial (doNotCall := memberValues.isEmpty): EXIT 1.
- atk_3_reverse (value2label := memberValues.reverse): EXIT 1.
- atk_4_cfeffect (set flag true then clobber to false): EXIT 1.
- atk_5_emptymap (value2label := []): EXIT 1.
- atk_6_echo (value2label := memberValues, doNotCall := true): EXIT 0 (verifies), #print axioms -> 'does not depend on any axioms'. Gold-equivalent same-spec impl.
- atk_7_tail (value2label := memberValues.tail): EXIT 1.
- atk_8_parity (doNotCall := length%2==0): EXIT 1.

Protocol step 2: the ONLY wrong-impl whose proof closes with clean axioms is atk_6_echo, which is observationally identical to gold (value2label = memberValues, doNotCallInTemplates = true for every input). Its faithful refined patch is the gold patch (single added line cls.do_not_call_in_templates = True). Executed run_resolve('django__django-12304', patch, retries=1): ResolveResult(resolved=True, completed=True, attempts=1, flaky=False); FAIL_TO_PASS test_templates PASS, all 17 PASS_TO_PASS PASS. The echo RESOLVES => not a weakness (per G-PANEL-1/G-EQ resolve policy). No verify-but-not-resolve gap.

Refinement.md audit: meta.json axioms=[], deep_model_references=[], conf_skip=false. All 4 legs tagged I or R/I; no A-consumed, no A-reference, no kind-3. axiom_check.py is a legitimate skip stub (no consumed callee axiom, no A-reference). The lone deep-model reference (templateWouldCall) matches base.py:851-856 exactly: isCallable && !doNotCall && !altersData == callable(current) and not do_not_call_in_templates and not alters_data, with isCallable=true/altersData=false fixed for the always-callable, never-alters-data enum class (justified in mapping.md). Correspondence holds.

Conclusion: tight deterministic spec; every wrong impl fails to close; the sole verifying same-spec impl is gold-equivalent and its faithful patch resolves. verify => correct holds. SOUND. Commands used: `bash scripts/lean_verify.sh <atk>.lean` for each; same_spec via swebench_unified.markers.same_spec + get_backend('lean'); run_resolve via swebench_unified.harness.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1_prepatch.lean`, `atk_2_partial.lean`, `atk_3_reverse.lean`, `atk_4_cfeffect.lean`, `atk_5_emptymap.lean`, `atk_7_tail.lean`, `atk_8_parity.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
none — spec is fully deterministic; no verifying wrong-impl exists whose faithful patch fails to resolve
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_partial.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_reverse.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_cfeffect.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_emptymap.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7_tail.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8_parity.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Making an enumerated-choices class usable as a value inside a template.

An enumerated-choices class bundles a set of members; each member carries a
stored value together with a human-readable label, and the class exposes the
value→label association built from its members.

A template engine, when it resolves a name to a value and finds that value is
callable, will by default INVOKE it with no arguments and substitute the result.
An enumerated-choices class is itself callable — invoking it performs a value
lookup and therefore demands an argument — so invoking it with no arguments
fails, and the member/attribute the template actually wanted (e.g. a member and
then its label or value) can never be reached.

A value may carry a flag that tells the engine NOT to invoke it. The desired
behavior is that the constructed class carries this flag, so that when the engine
encounters the class as a resolved value it leaves the class untouched instead of
calling it — letting the subsequent member and attribute lookups proceed. The
value→label association the class exposes is unchanged by this.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The members'
-- (value, label) entries enter as plain data, the value→label association is
-- that same data carried through unchanged, the "do not invoke" flag is a
-- literal, and the engine's invoke decision is modeled directly as a boolean over
-- the three observables it reads (is the value callable, does it carry the
-- "do not invoke" flag, does it alter data). Hence no `opaque`/`axiom` callee
-- contract is required.
-- axioms-end

-- pure-start
/-- The constructed enumerated-choices class, restricted to the touched
observables:
* `value2label` — the value→label association built from the class's members;
* `doNotCallInTemplates` — whether the class is flagged so a template engine must
  NOT invoke it when it is encountered as a resolved value. -/
structure ChoicesClass where
  value2label : List (Int × String)
  doNotCallInTemplates : Bool

/-- A template engine's decision, when a resolved value is encountered, of whether
to INVOKE it with no arguments: it invokes exactly the values that are callable,
not flagged against invocation, and that do not alter data. Mirrors the engine's
resolution arm. -/
def templateWouldCall (isCallable doNotCall altersData : Bool) : Bool :=
  isCallable && !doNotCall && !altersData
-- pure-end

-- post-conditions-start
/-- The constructed class is pinned at every observable:

  * its value→label association is exactly the one built from the supplied
    members (unchanged — directive 5 frame: this component equals its input);
  * it is flagged so that a template engine encountering the class as a resolved
    value would NOT invoke it. Because such a class is callable and does not alter
    data, "would not be invoked" forces the flag to be set, which is precisely
    what lets the engine leave the class intact and resolve a member and its
    attribute against it. -/
def problem_spec_buildChoicesClass
    (memberValues : List (Int × String)) (result : ChoicesClass) : Prop :=
  result.value2label = memberValues ∧
  templateWouldCall (isCallable := true) result.doNotCallInTemplates
      (altersData := false) = false
-- post-conditions-end

-- impl-start
def implementation_buildChoicesClass
    (memberValues : List (Int × String)) : ChoicesClass := Id.run do
  let mut cls : ChoicesClass := { value2label := memberValues, doNotCallInTemplates := false }
  -- The value→label association is built from the class's members.
  cls := { cls with value2label := memberValues }
  -- Flag the class so a template engine leaves it intact instead of invoking it.
  cls := { cls with doNotCallInTemplates := true }
  return cls
-- impl-end

-- proof-start
theorem correct_buildChoicesClass :
    ∀ (memberValues : List (Int × String)),
      problem_spec_buildChoicesClass memberValues
        (implementation_buildChoicesClass memberValues) := by
  intro memberValues
  refine ⟨rfl, rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec post-condition pins BOTH observables for ALL inputs: result.value2label = memberValues (exact list equality, order-sensitive) AND templateWouldCall true d false = false which reduces to d = true. Fully deterministic spec.

Same-spec check: all 8 attacks + pos_control return same_spec=True (spec_view collapses impl AND proof regions; I edited only the impl region byte-for-byte otherwise).

Verification (scripts/lean_verify.sh, 300s, run concurrently in batches of <=4):
- pos_control.lean: EXIT 0 (verifies, no sorry). #print axioms correct_buildChoicesClass -> 'does not depend on any axioms'.
- atk_1_prepatch (flag stays false): EXIT 1 (proof fails to close) — prepatch bug correctly rejected; the discriminating clause templateWouldCall true false false = true != false is unprovable.
- atk_2_partial (doNotCall := memberValues.isEmpty): EXIT 1.
- atk_3_reverse (value2label := memberValues.reverse): EXIT 1.
- atk_4_cfeffect (set flag true then clobber to false): EXIT 1.
- atk_5_emptymap (value2label := []): EXIT 1.
- atk_6_echo (value2label := memberValues, doNotCall := true): EXIT 0 (verifies), #print axioms -> 'does not depend on any axioms'. Gold-equivalent same-spec impl.
- atk_7_tail (value2label := memberValues.tail): EXIT 1.
- atk_8_parity (doNotCall := length%2==0): EXIT 1.

Protocol step 2: the ONLY wrong-impl whose proof closes with clean axioms is atk_6_echo, which is observationally identical to gold (value2label = memberValues, doNotCallInTemplates = true for every input). Its faithful refined patch is the gold patch (single added line cls.do_not_call_in_templates = True). Executed run_resolve('django__django-12304', patch, retries=1): ResolveResult(resolved=True, completed=True, attempts=1, flaky=False); FAIL_TO_PASS test_templates PASS, all 17 PASS_TO_PASS PASS. The echo RESOLVES => not a weakness (per G-PANEL-1/G-EQ resolve policy). No verify-but-not-resolve gap.

Refinement.md audit: meta.json axioms=[], deep_model_references=[], conf_skip=false. All 4 legs tagged I or R/I; no A-consumed, no A-reference, no kind-3. axiom_check.py is a legitimate skip stub (no consumed callee axiom, no A-reference). The lone deep-model reference (templateWouldCall) matches base.py:851-856 exactly: isCallable && !doNotCall && !altersData == callable(current) and not do_not_call_in_templates and not alters_data, with isCallable=true/altersData=false fixed for the always-callable, never-alters-data enum class (justified in mapping.md). Correspondence holds.

Conclusion: tight deterministic spec; every wrong impl fails to close; the sole verifying same-spec impl is gold-equivalent and its faithful patch resolves. verify => correct holds. SOUND. Commands used: `bash scripts/lean_verify.sh <atk>.lean` for each; same_spec via swebench_unified.markers.same_spec + get_backend('lean'); run_resolve via swebench_unified.harness.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Verified against real repo at base_commit 4c1b401e82 (django_gold worktree). Solution.lean compiles (exit 0); `#print axioms correct_buildChoicesClass` → 'does not depend on any axioms' (clean, no sorryAx). same_spec(Solution, Solution_prepatch, LeanBackend.language) = True — spec region byte-identical, only impl differs (prepatch leaves flag false, patched sets it true).

Modeled function `buildChoicesClass` = ChoicesMeta.__new__ (django/db/models/enums.py). Two observables:
(1) value2label = memberValues — real `cls._value2label_map_ = dict(zip(...))` is built earlier in __new__ and is UNCHANGED by the gold patch; mapping.md binds memberValues to exactly those recorded (value,label) entries, so the frame-pin `= memberValues` is a faithful identity carrier, not a strengthening.
(2) doNotCallInTemplates forced to true by clause 2 (templateWouldCall true d false = false ⟺ d=true). Gold patch adds `cls.do_not_call_in_templates = True` UNCONDITIONALLY for every Choices class, so the modeled function returns true on every input — matches real callee.

templateWouldCall c d a := c && !d && !a faithfully mirrors base.py:851-856 resolver arm `callable(current) and not getattr(current,'do_not_call_in_templates',False) and not getattr(current,'alters_data',False)`. Fixings isCallable:=true (class objects are callable) and altersData:=false (Choices classes never set alters_data; getattr default False) both agree with real behavior.

No input exists on which the modeled function disagrees with the real callee on the modeled observables. The spec is not too strong: value2label is genuinely frame-invariant under this patch, and the flag is set unconditionally. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region confirmed byte-identical patched vs prepatch (same_spec=True; impl/proof elided in the spec view). Gold edit is a single added statement `cls.do_not_call_in_templates = True` in ChoicesMeta.__new__ (enums.py). The public problem_statement ALREADY hands over the fix verbatim: 'Django Templates always call callables with no arguments...' and 'The easy solution would be to declare do_not_call_in_templates = True on the various Choices classes.' The spec view's discriminating content — a flag telling the engine NOT to invoke a callable value, the identifier doNotCallInTemplates (camelCase of the public token), and the postcondition templateWouldCall true doNotCallInTemplates false = false forcing the flag set — is entirely within what problem_statement discloses. The modeled function is named neutrally (buildChoicesClass), not the patched symbol ChoicesMeta/__new__/enums.py; no file path, patched def/class name, or line-level code specificity appears. The value2label = memberValues clause is a frame (unchanged-behavior) condition, not a gold disclosure. Nothing in the spec view leaks beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
