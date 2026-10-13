# P2 adversarial audit — django__django-13212

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The postcondition is total and fully pinned on the theorem's precondition domain (baseParams.lookup valueKey = none): accepted=true forces result=none; accepted=false forces result=some (baseParams ++ [(valueKey,value)]). No verifying same-spec impl can deviate on any reachable input, and the only off-domain freedom (baseParams already binding 'value') is unreachable in the real code — no built-in validator site pre-binds 'value', which is exactly what the patch establishes.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -82,11 +82,9 @@
     (value : String) (accepted : Bool)
     (baseParams : List (String × String)) : Option (List (String × String)) := Id.run do
   if accepted then
-    -- Input is acceptable: succeed, no error context.
     return none
-  -- Input is rejected: build the error context, binding `value` to the rejected
-  -- input alongside the intrinsic parameters this check already supplies.
-  return some (baseParams ++ [(valueKey, value)])
+  -- BUG: rejection context omits the ('value', value) binding.
+  return some baseParams
 -- impl-end
 
 -- proof-start
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -82,11 +82,9 @@
     (value : String) (accepted : Bool)
     (baseParams : List (String × String)) : Option (List (String × String)) := Id.run do
   if accepted then
-    -- Input is acceptable: succeed, no error context.
     return none
-  -- Input is rejected: build the error context, binding `value` to the rejected
-  -- input alongside the intrinsic parameters this check already supplies.
-  return some (baseParams ++ [(valueKey, value)])
+  -- WRONG ORDER: value binding prepended instead of appended.
+  return some ([(valueKey, value)] ++ baseParams)
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -82,11 +82,9 @@
     (value : String) (accepted : Bool)
     (baseParams : List (String × String)) : Option (List (String × String)) := Id.run do
   if accepted then
-    -- Input is acceptable: succeed, no error context.
     return none
-  -- Input is rejected: build the error context, binding `value` to the rejected
-  -- input alongside the intrinsic parameters this check already supplies.
-  return some (baseParams ++ [(valueKey, value)])
+  -- WRONG KEY: binds a different substitution name.
+  return some (baseParams ++ [("value_x", value)])
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -82,11 +82,9 @@
     (value : String) (accepted : Bool)
     (baseParams : List (String × String)) : Option (List (String × String)) := Id.run do
   if accepted then
-    -- Input is acceptable: succeed, no error context.
     return none
-  -- Input is rejected: build the error context, binding `value` to the rejected
-  -- input alongside the intrinsic parameters this check already supplies.
-  return some (baseParams ++ [(valueKey, value)])
+  -- SPURIOUS DUPLICATE: two ('value', value) entries.
+  return some (baseParams ++ [(valueKey, value), (valueKey, value)])
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -82,11 +82,9 @@
     (value : String) (accepted : Bool)
     (baseParams : List (String × String)) : Option (List (String × String)) := Id.run do
   if accepted then
-    -- Input is acceptable: succeed, no error context.
-    return none
-  -- Input is rejected: build the error context, binding `value` to the rejected
-  -- input alongside the intrinsic parameters this check already supplies.
-  return some (baseParams ++ [(valueKey, value)])
+    -- CONTROL-FLOW BUG: produces an error context on acceptance.
+    return some (baseParams ++ [(valueKey, value)])
+  return none
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -82,11 +82,13 @@
     (value : String) (accepted : Bool)
     (baseParams : List (String × String)) : Option (List (String × String)) := Id.run do
   if accepted then
-    -- Input is acceptable: succeed, no error context.
     return none
-  -- Input is rejected: build the error context, binding `value` to the rejected
-  -- input alongside the intrinsic parameters this check already supplies.
-  return some (baseParams ++ [(valueKey, value)])
+  -- PARTIAL-DOMAIN: only append the 'value' binding when baseParams does not
+  -- already bind it; otherwise emit baseParams unchanged. Differs from gold ONLY
+  -- outside the theorem precondition (baseParams.lookup "value" = none).
+  match baseParams.lookup valueKey with
+  | none   => return some (baseParams ++ [(valueKey, value)])
+  | some _ => return some baseParams
 -- impl-end
 
 -- proof-start
@@ -95,11 +97,13 @@
       baseParams.lookup valueKey = none →
       problem_spec_checkOutcome value accepted baseParams
         (implementation_checkOutcome value accepted baseParams) := by
-  intro value accepted baseParams _hbase
+  intro value accepted baseParams hbase
   unfold problem_spec_checkOutcome implementation_checkOutcome
   cases accepted with
   | true =>
     exact ⟨fun _ => rfl, fun h => absurd h (by simp)⟩
   | false =>
-    exact ⟨fun h => absurd h (by simp), fun _ => rfl⟩
+    refine ⟨fun h => absurd h (by simp), fun _ => ?_⟩
+    simp only [Id.run, hbase]
+    rfl
 -- proof-end
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -81,12 +81,11 @@
 def implementation_checkOutcome
     (value : String) (accepted : Bool)
     (baseParams : List (String × String)) : Option (List (String × String)) := Id.run do
-  if accepted then
-    -- Input is acceptable: succeed, no error context.
-    return none
-  -- Input is rejected: build the error context, binding `value` to the rejected
-  -- input alongside the intrinsic parameters this check already supplies.
-  return some (baseParams ++ [(valueKey, value)])
+  match accepted with
+  | true  => return none
+  | false =>
+    -- ECHO: same result, expressed via concat (= append of a singleton).
+    return some (baseParams.concat (valueKey, value))
 -- impl-end
 
 -- proof-start
@@ -101,5 +100,7 @@
   | true =>
     exact ⟨fun _ => rfl, fun h => absurd h (by simp)⟩
   | false =>
-    exact ⟨fun h => absurd h (by simp), fun _ => rfl⟩
+    refine ⟨fun h => absurd h (by simp), fun _ => ?_⟩
+    simp only [Id.run, List.concat_eq_append]
+    rfl
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Surfacing the rejected input inside a failed check's error context.

A value check inspects one input and reaches a verdict: the input is either
acceptable or not. When it is acceptable, the check signals success and produces
no error context. When it is NOT acceptable, the check signals failure and
produces an error context: a finite sequence of named substitution parameters
(an insertion-ordered mapping) that a customizable, human-facing message may
interpolate.

The desired behavior concerns only the failure case. A rejection's error context
carries the parameters intrinsic to that particular check (for instance a size
bound, or the offending file extension). It is often useful for a custom message
to additionally name the rejected input itself — e.g. to report which specific
entry, among many checked in bulk, was the bad one. So on a rejection the error
context must also bind the substitution name `value` to the rejected input.

The contract on a rejection's parameter sequence is therefore fully determined:

  * every intrinsic parameter the check supplies is preserved unchanged and in
    order (the underlying substitution mapping is insertion-ordered, and the
    intrinsic entries come first, exactly as the check supplied them);
  * the binding of the name `value` to exactly the rejected input is appended
    after them, as the final entry;
  * nothing else appears — no spurious parameter, and no shadowed or duplicate
    entry hiding anywhere in the sequence.

The acceptance verdict and the intrinsic parameters of a check are themselves
independent of this contract; the obligation is on the parameter sequence
accompanying a rejection.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Whether an
-- input is acceptable is the check's own verdict, modeled as a Boolean input
-- (`accepted`) and carried as data. The intrinsic parameters a check supplies
-- are likewise carried as an input (`baseParams`). Hence no `opaque`/`axiom`
-- callee contract is required.
-- axioms-end

-- pure-start
/-- The substitution name bound to the rejected input. (`%(value)s` in a custom
message refers to this name.) -/
def valueKey : String := "value"
-- pure-end

-- post-conditions-start
/-- The check-outcome contract, relating one input to the error context it
produces.

`result = none` means the input was accepted (no error context). `result =
some params` means the input was rejected with the substitution-parameter
sequence `params` (the entries of the insertion-ordered substitution mapping,
in order).

* When the verdict is acceptance, no error context is produced.
* When the verdict is rejection, the parameter sequence is EXACTLY the
  intrinsic parameters the check supplied, in order, with the binding of
  `valueKey` to the rejected input appended as the final entry:
  `baseParams ++ [(valueKey, value)]`.

Pinning the whole sequence (not merely its key-lookup view) leaves no component
of a rejection's parameter set free: each intrinsic parameter is preserved
verbatim and in position, the `value` binding is present and holds exactly the
rejected input, and no spurious, duplicate, or shadowed entry can appear
anywhere. The familiar lookup facts follow as corollaries: under the theorem's
precondition (`baseParams` does not bind `valueKey`),
`params.lookup valueKey = some value` and `params.lookup k = baseParams.lookup
k` for every `k ≠ valueKey`. -/
def problem_spec_checkOutcome
    (value : String) (accepted : Bool) (baseParams : List (String × String))
    (result : Option (List (String × String))) : Prop :=
  (accepted = true → result = none) ∧
  (accepted = false → result = some (baseParams ++ [(valueKey, value)]))
-- post-conditions-end

-- impl-start
def implementation_checkOutcome
    (value : String) (accepted : Bool)
    (baseParams : List (String × String)) : Option (List (String × String)) := Id.run do
  if accepted then
    -- Input is acceptable: succeed, no error context.
    return none
  -- Input is rejected: build the error context, binding `value` to the rejected
  -- input alongside the intrinsic parameters this check already supplies.
  return some (baseParams ++ [(valueKey, value)])
-- impl-end

-- proof-start
theorem correct_checkOutcome :
    ∀ (value : String) (accepted : Bool) (baseParams : List (String × String)),
      baseParams.lookup valueKey = none →
      problem_spec_checkOutcome value accepted baseParams
        (implementation_checkOutcome value accepted baseParams) := by
  intro value accepted baseParams _hbase
  unfold problem_spec_checkOutcome implementation_checkOutcome
  cases accepted with
  | true =>
    exact ⟨fun _ => rfl, fun h => absurd h (by simp)⟩
  | false =>
    exact ⟨fun h => absurd h (by simp), fun _ => rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

### G-EQ SOUND

SAME-SPEC: all 7 attacks + pos_control return same_spec=True via swebench_unified.markers.same_spec (lean). Only the impl (and, for verifying attacks, the proof) regions were edited; axioms/pure/pre/post byte-identical.

VERIFY COMMANDS (each: `bash scripts/lean_verify.sh <path>`), run concurrently in 2 batches of 4:
- pos_control.lean -> exit 0 (positive control, = gold impl). #print axioms correct_checkOutcome => [propext]. CLEAN.
- atk_1.lean (PREPATCH BUG: rejection returns `some baseParams`, omits ('value',value)) -> exit 1 (FAILS verify). prepatch_reproduced=true.
- atk_2.lean (ORDER SWAP: `[(valueKey,value)] ++ baseParams`) -> exit 1 (FAILS).
- atk_3.lean (WRONG KEY: appends ("value_x",value)) -> exit 1 (FAILS).
- atk_4.lean (DUPLICATE/SHADOW: appends value binding twice) -> exit 1 (FAILS).
- atk_5.lean (CONTROL-FLOW: branches swapped, error on acceptance) -> exit 1 (FAILS).
- atk_6.lean (PARTIAL-DOMAIN: appends ('value',value) only when baseParams.lookup valueKey = none, else returns some baseParams; proof discharges via hbase) -> exit 0 (VERIFIES). #print axioms => [propext, Quot.sound]. CLEAN.
- atk_7.lean (ECHO: `some (baseParams.concat (valueKey,value))`, = append of singleton; proof via List.concat_eq_append) -> exit 0 (VERIFIES). #print axioms => [propext]. CLEAN.

MANDATORY RESOLVE for verifying attacks (atk_6, atk_7): both are behaviorally IDENTICAL to the gold impl on the entire reachable domain — atk_7 by the definitional identity concat=append (all inputs), atk_6 because it deviates from gold ONLY when baseParams already binds 'value', which never occurs at any patched validator site (the patch is the SOLE source of the 'value' key; theorem precondition baseParams.lookup valueKey = none reflects this). Their faithful refined patches are therefore the gold patch itself. Executed:
  python -c "from swebench_unified.harness import run_resolve; r=run_resolve('django__django-13212', open('.../faithful_gold.diff').read(), timeout=1800, retries=0); print(r.resolved, r.completed, r.note)"
  RESULT: RESOLVED=True COMPLETED=True NOTE='resolved'. (docker-ok; report.json resolved=true; F2P = ValidatorCustomMessageTests value-placeholder tests.)
Both atk_6 and atk_7 faithful patches RESOLVE => neither breaks the spec.

REFINEMENT.MD AUDIT: meta.json axioms=[], deep_model_references=[]; G-AX=skip (pass), G-CONF=pass. refinement.md tags the 3 legs I / R+I / I — all R/I, NO kind-3, and NO A-consumed / A-reference legs (the changed op is a pure data construction baseParams ++ [(valueKey,value)]; the validity verdict is carried as the input `accepted`, not an axiomatized callee). Since there are no A-legs, there is no callee-correspondence obligation to fail; the model↔patch correspondence (association list ↔ list(ValidationError.params.items()), insertion-ordered, 'value' last) is faithfully mirrored by conformance_check.py (G-CONF pass over ~120k fuzz + edge cases).

CONCLUSION: The spec pins the full rejection sequence exactly; every wrong impl (atk_1..5) that deviates on ANY reachable input FAILS to verify, and every impl that verifies (pos_control, atk_6, atk_7) is behaviorally gold on the reachable domain and RESOLVES. No verify⇏correct witness exists. verify ⇒ correct holds. SOUND.

Note: meta.json currently records G-EQ as fail/INCONCLUSIVE from a prior pass (3 attacks inconclusive) — this fresh pass ran 7 attacks to completion with the mandatory resolve executed; the INCONCLUSIVE was a prior-pass artifact, not a spec weakness.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The postcondition is total and fully pinned on the theorem's precondition domain (baseParams.lookup valueKey = none): accepted=true forces result=none; accepted=false forces result=some (baseParams ++ [(valueKey,value)]). No verifying same-spec impl can deviate on any reachable input, and the only off-domain freedom (baseParams already binding 'value') is unreachable in the real code — no built-in validator site pre-binds 'value', which is exactly what the patch establishes.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Surfacing the rejected input inside a failed check's error context.

A value check inspects one input and reaches a verdict: the input is either
acceptable or not. When it is acceptable, the check signals success and produces
no error context. When it is NOT acceptable, the check signals failure and
produces an error context: a finite sequence of named substitution parameters
(an insertion-ordered mapping) that a customizable, human-facing message may
interpolate.

The desired behavior concerns only the failure case. A rejection's error context
carries the parameters intrinsic to that particular check (for instance a size
bound, or the offending file extension). It is often useful for a custom message
to additionally name the rejected input itself — e.g. to report which specific
entry, among many checked in bulk, was the bad one. So on a rejection the error
context must also bind the substitution name `value` to the rejected input.

The contract on a rejection's parameter sequence is therefore fully determined:

  * every intrinsic parameter the check supplies is preserved unchanged and in
    order (the underlying substitution mapping is insertion-ordered, and the
    intrinsic entries come first, exactly as the check supplied them);
  * the binding of the name `value` to exactly the rejected input is appended
    after them, as the final entry;
  * nothing else appears — no spurious parameter, and no shadowed or duplicate
    entry hiding anywhere in the sequence.

The acceptance verdict and the intrinsic parameters of a check are themselves
independent of this contract; the obligation is on the parameter sequence
accompanying a rejection.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Whether an
-- input is acceptable is the check's own verdict, modeled as a Boolean input
-- (`accepted`) and carried as data. The intrinsic parameters a check supplies
-- are likewise carried as an input (`baseParams`). Hence no `opaque`/`axiom`
-- callee contract is required.
-- axioms-end

-- pure-start
/-- The substitution name bound to the rejected input. (`%(value)s` in a custom
message refers to this name.) -/
def valueKey : String := "value"
-- pure-end

-- post-conditions-start
/-- The check-outcome contract, relating one input to the error context it
produces.

`result = none` means the input was accepted (no error context). `result =
some params` means the input was rejected with the substitution-parameter
sequence `params` (the entries of the insertion-ordered substitution mapping,
in order).

* When the verdict is acceptance, no error context is produced.
* When the verdict is rejection, the parameter sequence is EXACTLY the
  intrinsic parameters the check supplied, in order, with the binding of
  `valueKey` to the rejected input appended as the final entry:
  `baseParams ++ [(valueKey, value)]`.

Pinning the whole sequence (not merely its key-lookup view) leaves no component
of a rejection's parameter set free: each intrinsic parameter is preserved
verbatim and in position, the `value` binding is present and holds exactly the
rejected input, and no spurious, duplicate, or shadowed entry can appear
anywhere. The familiar lookup facts follow as corollaries: under the theorem's
precondition (`baseParams` does not bind `valueKey`),
`params.lookup valueKey = some value` and `params.lookup k = baseParams.lookup
k` for every `k ≠ valueKey`. -/
def problem_spec_checkOutcome
    (value : String) (accepted : Bool) (baseParams : List (String × String))
    (result : Option (List (String × String))) : Prop :=
  (accepted = true → result = none) ∧
  (accepted = false → result = some (baseParams ++ [(valueKey, value)]))
-- post-conditions-end

-- impl-start
def implementation_checkOutcome
    (value : String) (accepted : Bool)
    (baseParams : List (String × String)) : Option (List (String × String)) := Id.run do
  if accepted then
    -- Input is acceptable: succeed, no error context.
    return none
  -- Input is rejected: build the error context, binding `value` to the rejected
  -- input alongside the intrinsic parameters this check already supplies.
  return some (baseParams ++ [(valueKey, value)])
-- impl-end

-- proof-start
theorem correct_checkOutcome :
    ∀ (value : String) (accepted : Bool) (baseParams : List (String × String)),
      baseParams.lookup valueKey = none →
      problem_spec_checkOutcome value accepted baseParams
        (implementation_checkOutcome value accepted baseParams) := by
  intro value accepted baseParams _hbase
  unfold problem_spec_checkOutcome implementation_checkOutcome
  cases accepted with
  | true =>
    exact ⟨fun _ => rfl, fun h => absurd h (by simp)⟩
  | false =>
    exact ⟨fun h => absurd h (by simp), fun _ => rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

### G-EQ SOUND

SAME-SPEC: all 7 attacks + pos_control return same_spec=True via swebench_unified.markers.same_spec (lean). Only the impl (and, for verifying attacks, the proof) regions were edited; axioms/pure/pre/post byte-identical.

VERIFY COMMANDS (each: `bash scripts/lean_verify.sh <path>`), run concurrently in 2 batches of 4:
- pos_control.lean -> exit 0 (positive control, = gold impl). #print axioms correct_checkOutcome => [propext]. CLEAN.
- atk_1.lean (PREPATCH BUG: rejection returns `some baseParams`, omits ('value',value)) -> exit 1 (FAILS verify). prepatch_reproduced=true.
- atk_2.lean (ORDER SWAP: `[(valueKey,value)] ++ baseParams`) -> exit 1 (FAILS).
- atk_3.lean (WRONG KEY: appends ("value_x",value)) -> exit 1 (FAILS).
- atk_4.lean (DUPLICATE/SHADOW: appends value binding twice) -> exit 1 (FAILS).
- atk_5.lean (CONTROL-FLOW: branches swapped, error on acceptance) -> exit 1 (FAILS).
- atk_6.lean (PARTIAL-DOMAIN: appends ('value',value) only when baseParams.lookup valueKey = none, else returns some baseParams; proof discharges via hbase) -> exit 0 (VERIFIES). #print axioms => [propext, Quot.sound]. CLEAN.
- atk_7.lean (ECHO: `some (baseParams.concat (valueKey,value))`, = append of singleton; proof via List.concat_eq_append) -> exit 0 (VERIFIES). #print axioms => [propext]. CLEAN.

MANDATORY RESOLVE for verifying attacks (atk_6, atk_7): both are behaviorally IDENTICAL to the gold impl on the entire reachable domain — atk_7 by the definitional identity concat=append (all inputs), atk_6 because it deviates from gold ONLY when baseParams already binds 'value', which never occurs at any patched validator site (the patch is the SOLE source of the 'value' key; theorem precondition baseParams.lookup valueKey = none reflects this). Their faithful refined patches are therefore the gold patch itself. Executed:
  python -c "from swebench_unified.harness import run_resolve; r=run_resolve('django__django-13212', open('.../faithful_gold.diff').read(), timeout=1800, retries=0); print(r.resolved, r.completed, r.note)"
  RESULT: RESOLVED=True COMPLETED=True NOTE='resolved'. (docker-ok; report.json resolved=true; F2P = ValidatorCustomMessageTests value-placeholder tests.)
Both atk_6 and atk_7 faithful patches RESOLVE => neither breaks the spec.

REFINEMENT.MD AUDIT: meta.json axioms=[], deep_model_references=[]; G-AX=skip (pass), G-CONF=pass. refinement.md tags the 3 legs I / R+I / I — all R/I, NO kind-3, and NO A-consumed / A-reference legs (the changed op is a pure data construction baseParams ++ [(valueKey,value)]; the validity verdict is carried as the input `accepted`, not an axiomatized callee). Since there are no A-legs, there is no callee-correspondence obligation to fail; the model↔patch correspondence (association list ↔ list(ValidationError.params.items()), insertion-ordered, 'value' last) is faithfully mirrored by conformance_check.py (G-CONF pass over ~120k fuzz + edge cases).

CONCLUSION: The spec pins the full rejection sequence exactly; every wrong impl (atk_1..5) that deviates on ANY reachable input FAILS to verify, and every impl that verifies (pos_control, atk_6, atk_7) is behaviorally gold on the reachable domain and RESOLVES. No verify⇏correct witness exists. verify ⇒ correct holds. SOUND.

Note: meta.json currently records G-EQ as fail/INCONCLUSIVE from a prior pass (3 attacks inconclusive) — this fresh pass ran 7 attacks to completion with the mandatory resolve executed; the INCONCLUSIVE was a prior-pass artifact, not a spec weakness.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for django__django-13212 lean bundle. Modeled function checkOutcome: accepted=true -> none; accepted=false -> some (baseParams ++ [(valueKey,value)]) (intrinsic params in order, ('value', value) appended last). No diverging input found; the spec faithfully models the real patched callee.

### Verification performed
1. Lean verify: scripts/lean_verify.sh Solution.lean -> exit 0 (compiles, no sorry). Independent `#print axioms correct_checkOutcome` -> [propext] ONLY; no sorryAx -> proof is genuine, not fake.
2. Spec byte-identity: swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, lean-backend) = True. The prepatch bug is confined to the impl region (returns `some baseParams`, dropping the ('value', value) entry); the axioms/pure/post-conditions spec view is intact and unchanged.
3. Independent sweep of the REAL patched django/core/validators.py at base_commit f4e93919e4 (gold applied): ALL 20 `raise ValidationError` sites enumerated. Every rejection path binds params with intrinsic keys FIRST and 'value' LAST as a single entry: {'value': value} (13 sites: Regex, URL x4, Email x3, IPv4/IPv6/IPv46, NullChars, DecimalValidator invalid), {'max': ..., 'value': value} (DecimalValidator x3), {'extension': ..., 'allowed_extensions': ..., 'value': value} (FileExtension). No site omits 'value', places it first, or duplicates it.
4. The single dynamic-dict site (BaseValidator :343, params={'limit_value':..., 'show_value':..., 'value': value}) ALSO puts 'value' last AND is UNCHANGED by the patch (byte-identical pre/post) -> out of modeled scope, and consistent with the spec regardless. No intrinsic key equals 'value' anywhere (keys: max/extension/allowed_extensions/limit_value/show_value), so the theorem precondition baseParams.lookup 'value' = none excludes no real input.
5. G-CONF conformance_check.py re-run: checked=120011, disagreements=0 between oracle (list(dict.items()) of the patched insertion-ordered construction) and shadow (baseParams ++ [('value', value)]).

SPEC-TOO-STRONG assessment: The spec pins the FULL ordered entry sequence, which exactly matches list(dict.items()) of every patched site (Python dicts insertion-ordered; intrinsic-first, value-last). It demands nothing the real code does not deliver, and forbids nothing the real code produces. value:String models the sole observable the %(value)s interpolation reproduces (str(value); F2P tests assert form.errors == {field: [str(value)]}), a sound modeling boundary. Acceptance leg (accepted=true -> none) matches a non-raising validator, unchanged pre/post. No input where the modeled function disagrees with the real callee could be found.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Verified independently. (1) same_spec(Solution.lean, Solution_prepatch.lean) via the real lean backend = True: the spec view (doc comment, `valueKey`, `problem_spec_checkOutcome`) is byte-identical pre/post, so the prepatch bug is confined to the impl region — no impl detail bleeds into the spec. (2) Mechanical leakage.screen over the spec_src vs gold patch + problem_statement passes (hard_failures=[]).

Semantic gold-reconstruction assessment: the public problem_statement ALREADY discloses the full essence of the gold edit — 'Make validators include the provided value in ValidationError' and 'use a %(value)s placeholder' — which is exactly what patch.diff does (add params={'value': value} to raise ValidationError calls). The spec view is strictly MORE abstract than the public statement: it is domain-neutral, never naming Django, validators.py, ValidationError, params, any validator class, or the params={'value': value} syntax; it describes a generic 'check' producing an 'error context' of ordered 'substitution parameters' that binds the name `value`. The literal key "value" (valueKey) is itself public via the %(value)s placeholder in problem_statement, not new information.

Two elements go marginally beyond the raw statement, neither of which reconstructs the gold edit: (a) the ordering / no-duplicate refinement ('appended as the final entry') is a modeling-faithfulness consequence of Python's insertion-ordered dicts and reveals nothing about the SWE fix (the fix is just adding the param, not any reordering); (b) the intrinsic-param examples 'a size bound, or the offending file extension' describe PRE-EXISTING, UNCHANGED params (DecimalValidator max / FileExtensionValidator extension), i.e. code the patch does not introduce. Neither lets an attacker derive the gold edit beyond what problem_statement already gives. Note the disclosure basis is problem_statement only — hints_text was not relied upon.

Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
