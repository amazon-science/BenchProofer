# P2 adversarial audit — django__django-12308

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 admissible attacks re-run of 8 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -93,16 +93,9 @@
 
 -- impl-start
 def implementation_displayForField (value : PyVal) (empty : String) : String := Id.run do
-  -- An absent value shows the placeholder.
+  -- PREPATCH: a present value never gets the JSON rendering.
   if isNull value then
     return empty
-  -- A present, non-empty value is rendered as JSON; if it cannot be represented
-  -- as JSON, fall back to the generic rendering.
-  if truthy value then
-    match jsonSerialize value with
-    | .ok s => return s
-    | .error _ => return genericDisplay value empty
-  -- A present but empty value uses the generic rendering.
   return genericDisplay value empty
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -93,17 +93,13 @@
 
 -- impl-start
 def implementation_displayForField (value : PyVal) (empty : String) : String := Id.run do
-  -- An absent value shows the placeholder.
+  -- WRONG: the present-and-non-empty guard is dropped, so a present-but-empty
+  -- value (e.g. `{}`) is JSON-serialized instead of generically rendered.
   if isNull value then
     return empty
-  -- A present, non-empty value is rendered as JSON; if it cannot be represented
-  -- as JSON, fall back to the generic rendering.
-  if truthy value then
-    match jsonSerialize value with
-    | .ok s => return s
-    | .error _ => return genericDisplay value empty
-  -- A present but empty value uses the generic rendering.
-  return genericDisplay value empty
+  match jsonSerialize value with
+  | .ok s => return s
+  | .error _ => return genericDisplay value empty
 -- impl-end
 
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -93,16 +93,14 @@
 
 -- impl-start
 def implementation_displayForField (value : PyVal) (empty : String) : String := Id.run do
-  -- An absent value shows the placeholder.
+  -- WRONG: on a serialization failure the placeholder text is shown instead of
+  -- the generic rendering.
   if isNull value then
     return empty
-  -- A present, non-empty value is rendered as JSON; if it cannot be represented
-  -- as JSON, fall back to the generic rendering.
   if truthy value then
     match jsonSerialize value with
     | .ok s => return s
-    | .error _ => return genericDisplay value empty
-  -- A present but empty value uses the generic rendering.
+    | .error _ => return empty
   return genericDisplay value empty
 -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -93,16 +93,17 @@
 
 -- impl-start
 def implementation_displayForField (value : PyVal) (empty : String) : String := Id.run do
-  -- An absent value shows the placeholder.
+  -- WRONG (partial domain): only object/array values get the JSON rendering;
+  -- a present, non-empty scalar (e.g. the string "a") falls back to generic.
   if isNull value then
     return empty
-  -- A present, non-empty value is rendered as JSON; if it cannot be represented
-  -- as JSON, fall back to the generic rendering.
   if truthy value then
-    match jsonSerialize value with
-    | .ok s => return s
-    | .error _ => return genericDisplay value empty
-  -- A present but empty value uses the generic rendering.
+    match value with
+    | .dict _ | .list _ =>
+      match jsonSerialize value with
+      | .ok s => return s
+      | .error _ => return genericDisplay value empty
+    | _ => return genericDisplay value empty
   return genericDisplay value empty
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -93,17 +93,21 @@
 
 -- impl-start
 def implementation_displayForField (value : PyVal) (empty : String) : String := Id.run do
-  -- An absent value shows the placeholder.
+  -- WRONG (boundary): for containers the presence test is only non-nullness, so
+  -- an EMPTY object/array is JSON-serialized instead of generically rendered.
   if isNull value then
     return empty
-  -- A present, non-empty value is rendered as JSON; if it cannot be represented
-  -- as JSON, fall back to the generic rendering.
-  if truthy value then
+  match value with
+  | .dict _ | .list _ =>
     match jsonSerialize value with
     | .ok s => return s
     | .error _ => return genericDisplay value empty
-  -- A present but empty value uses the generic rendering.
-  return genericDisplay value empty
+  | _ =>
+    if truthy value then
+      match jsonSerialize value with
+      | .ok s => return s
+      | .error _ => return genericDisplay value empty
+    return genericDisplay value empty
 -- impl-end
 
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -93,16 +93,14 @@
 
 -- impl-start
 def implementation_displayForField (value : PyVal) (empty : String) : String := Id.run do
-  -- An absent value shows the placeholder.
+  -- WRONG (control-flow effect): the absent value is routed to the generic
+  -- renderer rather than returned as the placeholder text.
   if isNull value then
-    return empty
-  -- A present, non-empty value is rendered as JSON; if it cannot be represented
-  -- as JSON, fall back to the generic rendering.
+    return genericDisplay value empty
   if truthy value then
     match jsonSerialize value with
     | .ok s => return s
     | .error _ => return genericDisplay value empty
-  -- A present but empty value uses the generic rendering.
   return genericDisplay value empty
 -- impl-end
 
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -93,16 +93,14 @@
 
 -- impl-start
 def implementation_displayForField (value : PyVal) (empty : String) : String := Id.run do
-  -- An absent value shows the placeholder.
+  -- WRONG (ungrounded oracle echo): the truthy arm consults the serializer but
+  -- throws its text away, echoing the generic rendering for both outcomes.
   if isNull value then
     return empty
-  -- A present, non-empty value is rendered as JSON; if it cannot be represented
-  -- as JSON, fall back to the generic rendering.
   if truthy value then
     match jsonSerialize value with
-    | .ok s => return s
+    | .ok _ => return genericDisplay value empty
     | .error _ => return genericDisplay value empty
-  -- A present but empty value uses the generic rendering.
   return genericDisplay value empty
 -- impl-end
 
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -93,17 +93,15 @@
 
 -- impl-start
 def implementation_displayForField (value : PyVal) (empty : String) : String := Id.run do
-  -- An absent value shows the placeholder.
+  -- WRONG (boundary/placeholder confusion): a present-but-empty value shows the
+  -- absent-value placeholder text instead of the generic rendering.
   if isNull value then
     return empty
-  -- A present, non-empty value is rendered as JSON; if it cannot be represented
-  -- as JSON, fall back to the generic rendering.
   if truthy value then
     match jsonSerialize value with
     | .ok s => return s
     | .error _ => return genericDisplay value empty
-  -- A present but empty value uses the generic rendering.
-  return genericDisplay value empty
+  return empty
 -- impl-end
 
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**VERDICT:** SOUND. 8 same-spec attacks (same_spec=True, unsound_evasions=[] for all 8 + pos_control, via swebench_unified.markers.same_spec / variant_scope.unsound_evasions, lean backend). Only the impl+proof regions were edited. Verifications run concurrently in 3 background batches of <=4 via 'bash scripts/lean_verify.sh <f>'.

**LEAN VERIFY:** pos_control EXIT=0 (verifies). atk_1..atk_8 ALL EXIT=1 (rejected). Every rejection is a genuine unprovable postcondition goal ('Tactic rfl failed ... is not definitionally equal', with the refine_1/2/3 case and the opaque-term disequality shown in atk_N.log) — NOT a syntax/elaboration error, so each attack actually reached the specification and the spec performed the rejection.

AXIOMS (axcheck.lean, EXIT=0): correct_displayForField depends on axioms: [propext, Quot.sound]; implementation_displayForField/jsonSerialize/genericDisplay: [propext]. Clean — no sorryAx, no bundle-declared axiom.

DECISIVE MACHINE-CHECKED RESULT — the spec is FUNCTIONAL. tightness.lean (cmd: bash scripts/lean_verify.sh tightness.lean) EXIT=0, closing two auditor-written theorems on top of the frozen spec: (a) spec_is_functional: problem_spec_displayForField value empty r1 -> problem_spec_displayForField value empty r2 -> r1 = r2; (b) spec_pins_gold: problem_spec_displayForField value empty r <-> r = implementation_displayForField value empty. The three postcondition clauses partition on isNull/truthy and each PINS the result, so the spec admits EXACTLY ONE output per input. Hence no same-spec wrong impl can ever verify: verify=>correct (w.r.t. the model) is a proved theorem here, not an inference from N failed attacks. This is stronger evidence than the attack battery alone.

ATTACKS (all 8 REJECTED; each faithful patch materialized, 'git apply --check' OK in a clean base_commit tree at .../base extracted from git archive 2e0f04507b17362239ba49830d26fec504d46978, and RUN through the official run_resolve anyway to prove the attacks were not vacuous): atk_1 prepatch bug re-encoded (no JSON branch; present value -> genericDisplay) resolve=NOT RESOLVED (3 attempts, consistent); atk_2 dropped 'and value' truthiness guard, resolve=RESOLVED; atk_3 serialization-failure arm returns the placeholder instead of genericDisplay, resolve=NOT RESOLVED (consistent); atk_4 partial domain (JSON only for dict/list, so a non-empty scalar 'a' falls to generic), resolve=NOT RESOLVED (consistent); atk_5 boundary (containers bypass the emptiness test, so {} is serialized), resolve=RESOLVED; atk_6 control-flow effect (absent value routed to genericDisplay instead of the placeholder; patch moves the JSONField handling above the 'value is None' test), resolve=RESOLVED; atk_7 ungrounded oracle echo (serializer consulted, its .ok text discarded, generic rendering echoed on both outcomes), resolve=NOT RESOLVED (consistent); atk_8 present-but-empty shows the absent-value placeholder, resolve=RESOLVED.

**ORACLE LIVENESS CONTROL:** patches/gold.diff run through the same run_resolve => RESOLVED (attempt 2/3). G-RESOLVE=pass is also recorded in meta.json, so `_oracle_cannot_refute_here` is empty and resolve outcomes here are informative. 4 of my 8 wrong patches are refuted by the oracle, so it demonstrably discriminates on this instance.

**NO BREAK:** BROKEN requires an impl whose proof CLOSES with clean axioms and whose faithful patch does NOT resolve. Zero attacks closed — every one was rejected at exit 1 — so no such pair exists. The four non-resolving patches (atk_1/3/4/7) are the reverse of a break: the spec rejected exactly the impls the oracle also rejects, i.e. the spec is at least as strong as the suite on those behaviors.

SCOPE NOTE (not a weakness): atk_2/5/6/8 were rejected by the spec yet their patches RESOLVE — the suite cannot distinguish them because display_for_value coincidentally agrees with json.dumps on the uncovered boundary inputs ({}, 0, None). The Lean spec is STRICTER than the test suite there (genericDisplay is opaque, so the spec cannot exploit those coincidences). Strictness in that direction is soundness; it produces no verify=>/=>correct pair and is G-PANEL-2's (spec-too-strong) axis, not G-EQ's. Recorded here for the reader rather than as a finding.

A-LEG AUDIT (the assigned focus; R/I legs are G-CONF's). aleg_diff.py stood up the REAL Django at base_commit + gold patch (tree at .../goldtree, deps vendored to ./pylibs) and differentially compared the real display_for_field(value, models.JSONField(), empty) against an op-for-op transliteration of implementation_displayForField that calls the REAL callees field.get_prep_value and display_for_value: 135 values, 0 mismatches. Corpus covers every PyVal constructor, all emptiness boundaries ({}, [], (), '', 0, 0.0, False), nested containers, and TypeError drivers (tuple-keyed and frozenset-keyed dicts, nested and mixed). The shadow also reproduces all four FAIL_TO_PASS expectations and the None+JSONField PASS_TO_PASS case exactly. So both A-reference rows in refinement.md (the 'and value' guard ↦ truthy; the try/except dispatch ↦ match jsonSerialize) correspond to real callee behavior.

**REFINEMENT.MD LEG AUDIT:** 5 rows, tagged R (inputs/PyVal bijection), I (the earlier 'value is None' cascade test), A-reference (the 'and value' guard), A-reference (the edited try/except dispatch), I (the final else for present-but-empty). Every leg is R / A-reference / I — NO kind-3 leg, and no A-consumed row is claimed. That claim is verified, not taken on trust: the proof body is 'cases jsonSerialize value <;> rfl', and both opaques occur IDENTICALLY in problem_spec_displayForField and implementation_displayForField, so no contract of either is consumed; #print axioms confirms nothing beyond propext/Quot.sound. axiom_check.py's skip stub is therefore correct. The claimed patch text in refinement.md and mapping.md matches django/contrib/admin/utils.py:399-403 post-patch byte-for-byte, and the prepatch story (fall-through to the final else, {'foo': 'bar'} vs {"foo": "bar"}) matches the base_commit source and the problem statement.

Modeling remark (no action): PyVal.num is Rat, so float NaN/Infinity — which json.dumps renders as non-JSON 'NaN'/'Infinity' rather than raising — are outside the model's value domain. That is a declared modeling scope choice consistent with mapping.md's bijection table, not a hole the spec hides.

**ARTIFACTS:** {atk_1..atk_8}.lean + .log, pos_control.lean, axcheck.lean(+.log), tightness.lean(+.log), aleg_diff.py, patches/{atk_1..atk_8,gold}.diff, resolve_*.json, results.txt, NOTES.md.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 admissible attacks re-run of 8 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**VERDICT:** SOUND. 8 same-spec attacks (same_spec=True, unsound_evasions=[] for all 8 + pos_control, via swebench_unified.markers.same_spec / variant_scope.unsound_evasions, lean backend). Only the impl+proof regions were edited. Verifications run concurrently in 3 background batches of <=4 via 'bash scripts/lean_verify.sh <f>'.

**LEAN VERIFY:** pos_control EXIT=0 (verifies). atk_1..atk_8 ALL EXIT=1 (rejected). Every rejection is a genuine unprovable postcondition goal ('Tactic rfl failed ... is not definitionally equal', with the refine_1/2/3 case and the opaque-term disequality shown in atk_N.log) — NOT a syntax/elaboration error, so each attack actually reached the specification and the spec performed the rejection.

AXIOMS (axcheck.lean, EXIT=0): correct_displayForField depends on axioms: [propext, Quot.sound]; implementation_displayForField/jsonSerialize/genericDisplay: [propext]. Clean — no sorryAx, no bundle-declared axiom.

DECISIVE MACHINE-CHECKED RESULT — the spec is FUNCTIONAL. tightness.lean (cmd: bash scripts/lean_verify.sh tightness.lean) EXIT=0, closing two auditor-written theorems on top of the frozen spec: (a) spec_is_functional: problem_spec_displayForField value empty r1 -> problem_spec_displayForField value empty r2 -> r1 = r2; (b) spec_pins_gold: problem_spec_displayForField value empty r <-> r = implementation_displayForField value empty. The three postcondition clauses partition on isNull/truthy and each PINS the result, so the spec admits EXACTLY ONE output per input. Hence no same-spec wrong impl can ever verify: verify=>correct (w.r.t. the model) is a proved theorem here, not an inference from N failed attacks. This is stronger evidence than the attack battery alone.

ATTACKS (all 8 REJECTED; each faithful patch materialized, 'git apply --check' OK in a clean base_commit tree at .../base extracted from git archive 2e0f04507b17362239ba49830d26fec504d46978, and RUN through the official run_resolve anyway to prove the attacks were not vacuous): atk_1 prepatch bug re-encoded (no JSON branch; present value -> genericDisplay) resolve=NOT RESOLVED (3 attempts, consistent); atk_2 dropped 'and value' truthiness guard, resolve=RESOLVED; atk_3 serialization-failure arm returns the placeholder instead of genericDisplay, resolve=NOT RESOLVED (consistent); atk_4 partial domain (JSON only for dict/list, so a non-empty scalar 'a' falls to generic), resolve=NOT RESOLVED (consistent); atk_5 boundary (containers bypass the emptiness test, so {} is serialized), resolve=RESOLVED; atk_6 control-flow effect (absent value routed to genericDisplay instead of the placeholder; patch moves the JSONField handling above the 'value is None' test), resolve=RESOLVED; atk_7 ungrounded oracle echo (serializer consulted, its .ok text discarded, generic rendering echoed on both outcomes), resolve=NOT RESOLVED (consistent); atk_8 present-but-empty shows the absent-value placeholder, resolve=RESOLVED.

**ORACLE LIVENESS CONTROL:** patches/gold.diff run through the same run_resolve => RESOLVED (attempt 2/3). G-RESOLVE=pass is also recorded in meta.json, so `_oracle_cannot_refute_here` is empty and resolve outcomes here are informative. 4 of my 8 wrong patches are refuted by the oracle, so it demonstrably discriminates on this instance.

**NO BREAK:** BROKEN requires an impl whose proof CLOSES with clean axioms and whose faithful patch does NOT resolve. Zero attacks closed — every one was rejected at exit 1 — so no such pair exists. The four non-resolving patches (atk_1/3/4/7) are the reverse of a break: the spec rejected exactly the impls the oracle also rejects, i.e. the spec is at least as strong as the suite on those behaviors.

SCOPE NOTE (not a weakness): atk_2/5/6/8 were rejected by the spec yet their patches RESOLVE — the suite cannot distinguish them because display_for_value coincidentally agrees with json.dumps on the uncovered boundary inputs ({}, 0, None). The Lean spec is STRICTER than the test suite there (genericDisplay is opaque, so the spec cannot exploit those coincidences). Strictness in that direction is soundness; it produces no verify=>/=>correct pair and is G-PANEL-2's (spec-too-strong) axis, not G-EQ's. Recorded here for the reader rather than as a finding.

A-LEG AUDIT (the assigned focus; R/I legs are G-CONF's). aleg_diff.py stood up the REAL Django at base_commit + gold patch (tree at .../goldtree, deps vendored to ./pylibs) and differentially compared the real display_for_field(value, models.JSONField(), empty) against an op-for-op transliteration of implementation_displayForField that calls the REAL callees field.get_prep_value and display_for_value: 135 values, 0 mismatches. Corpus covers every PyVal constructor, all emptiness boundaries ({}, [], (), '', 0, 0.0, False), nested containers, and TypeError drivers (tuple-keyed and frozenset-keyed dicts, nested and mixed). The shadow also reproduces all four FAIL_TO_PASS expectations and the None+JSONField PASS_TO_PASS case exactly. So both A-reference rows in refinement.md (the 'and value' guard ↦ truthy; the try/except dispatch ↦ match jsonSerialize) correspond to real callee behavior.

**REFINEMENT.MD LEG AUDIT:** 5 rows, tagged R (inputs/PyVal bijection), I (the earlier 'value is None' cascade test), A-reference (the 'and value' guard), A-reference (the edited try/except dispatch), I (the final else for present-but-empty). Every leg is R / A-reference / I — NO kind-3 leg, and no A-consumed row is claimed. That claim is verified, not taken on trust: the proof body is 'cases jsonSerialize value <;> rfl', and both opaques occur IDENTICALLY in problem_spec_displayForField and implementation_displayForField, so no contract of either is consumed; #print axioms confirms nothing beyond propext/Quot.sound. axiom_check.py's skip stub is therefore correct. The claimed patch text in refinement.md and mapping.md matches django/contrib/admin/utils.py:399-403 post-patch byte-for-byte, and the prepatch story (fall-through to the final else, {'foo': 'bar'} vs {"foo": "bar"}) matches the base_commit source and the problem statement.

Modeling remark (no action): PyVal.num is Rat, so float NaN/Infinity — which json.dumps renders as non-JSON 'NaN'/'Infinity' rather than raising — are outside the model's value domain. That is a declared modeling scope choice consistent with mapping.md's bijection table, not a hole the spec hides.

**ARTIFACTS:** {atk_1..atk_8}.lean + .log, pos_control.lean, axcheck.lean(+.log), tightness.lean(+.log), aleg_diff.py, patches/{atk_1..atk_8,gold}.diff, resolve_*.json, results.txt, NOTES.md.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

Faithfulness (spec-too-strong / drift) audit of django__django-12308. Reference = worktree at base 2e0f04507b with patch.diff APPLIED (confirmed: git diff --stat shows only the 5-line JSONField branch in django/contrib/admin/utils.py + 17 test lines; display_for_field body read directly and contains the branch).

### Mechanical checks
1. Lean gold verifies: scripts/lean_verify.sh ATK2P2_12308_gold.lean exit=0. Axioms clean: `#print axioms correct_displayForField` -> [propext, Quot.sound]; problem_spec/implementation -> [propext]. NO sorryAx, so the proof is real, not fake.
2. Spec region byte-identical: markers.same_spec(Solution.lean, Solution_prepatch.lean, get_backend('lean')) = True (spec_view = 101 lines). Prepatch differs only in the impl+proof regions.
3. Bundle checks: conformance_check.py status=ok 0/120015 disagreements (seed 20240627). axiom_check.py status=skip (no consumed callee axioms — correct: jsonSerialize/genericDisplay appear IDENTICALLY in problem_spec and impl, so the proof is pure case analysis and consumes no contract for either; I confirmed this by reading the proof term).
4. properties.py imports OK (release-gate check).
5. FAIL_TO_PASS reference tests pass in the patched worktree: admin_utils.tests.UtilsTests.test_json_display_for_field and test_null_display_for_field -> OK (2 tests).

### PRIMARY FAITHFULNESS DIFFERENTIAL (the real callee, not a replica)
I did NOT trust the bundle's stdlib replica. I stood up real Django from the patched worktree (django.`__file__` = `__init__`.py, verified display_for_field source contains the JSONField branch) and drove the REAL django.contrib.admin.utils.display_for_field with a REAL models.JSONField(), then checked the result against the LEAN SPEC's three clauses with the opaque callees instantiated by the REAL repo callees (field.get_prep_value, display_for_value). 80,212 cases (52 hand-picked discrete edge cases x 4 placeholder strings + 80,000 fuzzed nested values): 0 spec violations. Coverage included all three clauses: null -> placeholder; present-and-non-empty with .ok (dicts, lists, strings, ints, floats, True, nested); present-and-non-empty with .error (dicts keyed by tuple/list -> TypeError -> generic renderer, e.g. {('a','b'):'c'} -> "{('a', 'b'): 'c'}"); present-but-empty ({}, [], (), '', 0, 0.0, False) -> generic renderer. The empty-value clause is genuinely exercised, confirming the `and value` guard routes those to the final else.

### SPEC-STRENGTH PROBES (attempts to find the spec too strong — all failed to break it)
- truthy: matches Python bool() on every value class a JSONField can hold; -0.0/Rat 0 collapse correctly; bool handled before int so True/False render as JSON true/false.
- .error arm models ONLY TypeError. I probed the non-TypeError failure: a self-referential list makes get_prep_value raise ValueError('Circular reference detected'), which propagates out of the real display_for_field. This is NOT a divergence: PyVal is a finite inductive type and literally cannot encode a circular structure, so such values are outside the modeled domain — matching the docstring's explicit 'any other failure propagates and is out of scope'. Likewise nan/inf are excluded by `num (q : Rat)`, and bytes/set are unrepresentable in PyVal (and agree anyway when tested).
- isinstance disjointness: JSONField() is not an instance of Boolean/Integer/Float/Decimal/Date/Time/DateTime/FileField, so no earlier cascade branch can steal a JSONField value. Verified all 8.

### SCOPE-BOUNDARY NOTE (documentation nit, NOT a faithfulness defect, so not reported as the diverging input)
The cascade's first gate `if getattr(field, 'flatchoices', None)` precedes the JSON branch. For the default models.JSONField(), flatchoices == [] (falsy), so the gate never fires — this is why all 80k cases agree. For a pathological models.JSONField(choices=[...]), the real code takes the flatchoices branch: value 'a' -> 'Alpha' while the spec demands '"a"'. I deliberately do NOT cite this as UNFAITHFUL: (a) mapping.md declares the precondition as isinstance(field, models.JSONField) selecting the model with field fixed, not a runtime input; (b) that configuration is broken in Django itself, not merely unmodeled — dict(field.flatchoices).get(value) raises TypeError: unhashable type 'dict'/'list' for exactly the dict/list values that characterize a JSON field (I reproduced this crash for {'foo':'bar'}, ['a','b'], {}); (c) the gold patch's own branch is equally unreachable there, so the upstream fix does not contemplate it either. Condemning the spec for a config where the real function crashes on its characteristic inputs would be condemning a correct spec.

**CONCLUSION:** the spec is not too strong and does not drift. It pins the result in all three cases, the cases partition the input domain, and on the modeled domain (a JSON-valued field's value, PyVal-representable) it agrees with the patched real repo on every one of 80,212 real-callee cases. No diverging input exists. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

MEASURED, not inherited. No relaxation in this bundle: meta.json has no `relaxed_leakage` key (keys: axioms, conf_skip, deep_model_references, gates, modeled_functions, opaque_callees, patch_equals_gold, pbt_audit, prepatch_variants, region_hashes, schema_version, spec_provenance, verifier_pins) and no RELAXED_LEAKAGE.md exists (find -iname '*relax*' empty). So this is a straight leakage judgement, no unavoidability argument to re-derive.

Nothing in the bundle addresses the reviewer or prescribes a verdict. verdict.md line 3 explicitly subordinates agent prose to machine re-runs, and its Role-4 line is a record of a prior run, not an instruction. Clean on that axis.

### Preliminaries I ran
- Spec region byte-identity: markers.same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend()) = True; diff of pure-start..post-conditions-end is empty. The prepatch variant differs only in impl+proof.
- scripts/lean_verify.sh Solution.lean -> exit 0 (compiles, no sorry).
- Mechanical screen: leakage.screen(Solution.lean, LeanBackend(), gold_patch, problem_statement, test_patch) -> passed=True, hard_failures=[], warnings=[].
- Hand-checked the spec view for the tells the screen keys on: narration regex hits = [] ; no diff markers ; no patched path ('admin/utils', 'utils.py', 'contrib' all absent) ; and every patched-symbol/API token absent: get_prep_value, display_for_value, JSONField, isinstance, models., encoder, InvalidJSONInput, json.dumps, prepare_value, TypeError, readonly, admin. The spec view is written entirely in domain vocabulary (jsonSerialize / genericDisplay / PyVal / truthy).

### LOAD-BEARING TEST (the substantive check — which part of the spec view actually carries the discriminator):
Built two files in a mktemp -d: stripped the ENTIRE /-! ... -/ narration docstring and reduced problem_spec to the present-and-non-empty clause alone, then adapted the proof.
- A = gold impl vs that stripped 1-clause spec -> lean_verify exit 0.
- B = prepatch impl (isNull -> empty; else genericDisplay) vs the same stripped spec -> exit 1.
So the discriminator is carried by the FORMAL clause, and the narration prose is NOT load-bearing — it is removable without losing the pre/post separation. That is the healthy direction: the spec does not lean on prose that names a fix.

B's failure message pins the case precisely: 'case ok', i.e. the sole discriminating input class is present + non-empty + JSON-representable. That is verbatim the public problem_statement's complaint ('{"foo": "bar"} would be displayed as {'foo': 'bar'}, which is not valid JSON'). The other three arms are pre-patch-INVARIANT and therefore disclose nothing about the edit: the null arm is the pre-existing `value is None` branch (present in the base_commit cascade I read  django/contrib/admin/utils.py:381-408); the .error arm demands genericDisplay, which is exactly what prepatch already returns for such a value (refinement.md concedes this is not independently observable from prepatch, and B confirms it — only `ok` failed); the present-but-empty arm likewise matches the cascade's final else on both sides.

CALIBRATION AGAINST problem_statement: the public statement is unusually disclosive — it names the file (django.contrib.admin.utils), the function (display_for_field), the field type (JSONField), the fix mechanism (call prepare_value), and even the recovery concern (InvalidJSONInput / do not call json.dumps directly). The spec view names NONE of those. It is strictly less edit-localizing than the text the solver already has.

CLOSEST CALL, recorded rather than buried: the `pure` docstring's 'e.g. a mapping keyed by a tuple' echoes the F2P fixture {('a','b'): 'c'}, and the PyVal.tuple constructor exists to carry it. I judged this not a finding — it discloses a non-serializable INPUT CLASS that the problem_statement already gestures at via 'to take care of the InvalidJSONInput case', and it is not the edit (the .error arm it motivates is prepatch-invariant per B). It is test-fixture flavour, not gold-edit localization, and the gate's mandate is the edit vs problem_statement.

**VERDICT:** no line of the spec view reveals where or how to edit beyond the public problem_statement. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
