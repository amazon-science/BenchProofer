# P2 adversarial audit — django__django-15127

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -64,14 +64,13 @@
       result = prevTagMap)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_resolveTagMap
     (tagsSettingChanged : Bool)
     (defaultTags overrideTags prevTagMap : List (Int × String)) :
     List (Int × String) := Id.run do
   let mut tagMap := prevTagMap
-  if tagsSettingChanged then
-    tagMap := mergeTags defaultTags overrideTags
   return tagMap
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -64,6 +64,7 @@
       result = prevTagMap)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_resolveTagMap
     (tagsSettingChanged : Bool)
@@ -71,7 +72,7 @@
     List (Int × String) := Id.run do
   let mut tagMap := prevTagMap
   if tagsSettingChanged then
-    tagMap := mergeTags defaultTags overrideTags
+    tagMap := defaultTags ++ overrideTags
   return tagMap
 -- impl-end
 
@@ -83,5 +84,5 @@
         (implementation_resolveTagMap tagsSettingChanged defaultTags overrideTags prevTagMap) := by
   intro tagsSettingChanged defaultTags overrideTags prevTagMap
   refine ⟨fun h => ?_, fun h => ?_⟩ <;>
-    subst h <;> rfl
+    subst h <;> simp [mergeTags]
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -64,14 +64,15 @@
       result = prevTagMap)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_resolveTagMap
     (tagsSettingChanged : Bool)
     (defaultTags overrideTags prevTagMap : List (Int × String)) :
     List (Int × String) := Id.run do
-  let mut tagMap := prevTagMap
+  let mut tagMap := mergeTags defaultTags overrideTags
   if tagsSettingChanged then
-    tagMap := mergeTags defaultTags overrideTags
+    tagMap := prevTagMap
   return tagMap
 -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -64,14 +64,13 @@
       result = prevTagMap)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_resolveTagMap
     (tagsSettingChanged : Bool)
     (defaultTags overrideTags prevTagMap : List (Int × String)) :
     List (Int × String) := Id.run do
-  let mut tagMap := prevTagMap
-  if tagsSettingChanged then
-    tagMap := mergeTags defaultTags overrideTags
+  let mut tagMap := mergeTags defaultTags overrideTags
   return tagMap
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -64,6 +64,7 @@
       result = prevTagMap)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_resolveTagMap
     (tagsSettingChanged : Bool)
@@ -71,7 +72,7 @@
     List (Int × String) := Id.run do
   let mut tagMap := prevTagMap
   if tagsSettingChanged then
-    tagMap := mergeTags defaultTags overrideTags
+    tagMap := defaultTags
   return tagMap
 -- impl-end
 
@@ -83,5 +84,5 @@
         (implementation_resolveTagMap tagsSettingChanged defaultTags overrideTags prevTagMap) := by
   intro tagsSettingChanged defaultTags overrideTags prevTagMap
   refine ⟨fun h => ?_, fun h => ?_⟩ <;>
-    subst h <;> rfl
+    subst h <;> simp [mergeTags]
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -64,6 +64,7 @@
       result = prevTagMap)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_resolveTagMap
     (tagsSettingChanged : Bool)
@@ -71,7 +72,7 @@
     List (Int × String) := Id.run do
   let mut tagMap := prevTagMap
   if tagsSettingChanged then
-    tagMap := mergeTags defaultTags overrideTags
+    tagMap := overrideTags ++ defaultTags ++ defaultTags
   return tagMap
 -- impl-end
 
@@ -83,5 +84,5 @@
         (implementation_resolveTagMap tagsSettingChanged defaultTags overrideTags prevTagMap) := by
   intro tagsSettingChanged defaultTags overrideTags prevTagMap
   refine ⟨fun h => ?_, fun h => ?_⟩ <;>
-    subst h <;> rfl
+    subst h <;> simp [mergeTags]
 -- proof-end
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -64,15 +64,13 @@
       result = prevTagMap)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_resolveTagMap
     (tagsSettingChanged : Bool)
     (defaultTags overrideTags prevTagMap : List (Int × String)) :
-    List (Int × String) := Id.run do
-  let mut tagMap := prevTagMap
-  if tagsSettingChanged then
-    tagMap := mergeTags defaultTags overrideTags
-  return tagMap
+    List (Int × String) :=
+  if tagsSettingChanged then overrideTags ++ defaultTags else prevTagMap
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
The effective mapping from a message's level to its display tag is derived from
two configuration sources: a built-in set of default tags and a
user-supplied override mapping keyed by the same levels, with the override value
taking precedence whenever a level appears in both. This effective mapping is
held in a cache that downstream code consults to label individual messages.

Whenever a configuration value changes, the cached mapping must stay consistent
with the current configuration:

  * if the configuration value that changed is the message-tag override, the
    effective mapping is recomputed from the current defaults and the current
    overrides;
  * for any other configuration change, the cached mapping is left exactly as it
    was.

Inputs:
  * `tagsSettingChanged` — whether the configuration value that changed is the
    message-tag override;
  * `defaultTags` — the built-in default level→tag pairs;
  * `overrideTags` — the user-supplied override level→tag pairs;
  * `prevTagMap` — the cached mapping in effect prior to the change.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The defaults,
-- the overrides, and the previously-cached mapping all enter as plain data, and
-- the change indicator enters as a Bool. The only operation is the combination
-- of the two configuration sources into the effective mapping (overrides taking
-- precedence per level), modeled directly below. Hence no `opaque`/`axiom`
-- callee contract is required.
-- axioms-end

-- pure-start
/-- The effective level→tag mapping built from a set of default pairs and a set
of override pairs: the overrides take precedence over the defaults whenever a
level is present in both. Modeled as the overrides followed by the defaults, so
that a first-match lookup over the result returns the override value when one
exists for a level and the default value otherwise (the key set being the union
of both sources). -/
def mergeTags (defaultTags overrideTags : List (Int × String)) : List (Int × String) :=
  overrideTags ++ defaultTags
-- pure-end

-- post-conditions-start
/-- The cached mapping is fully pinned to the inputs:

  * when the configuration value that changed is the message-tag override, the
    result is exactly the effective mapping recomputed from the current defaults
    and overrides;
  * otherwise the result is exactly the previously-cached mapping, unchanged.

The two cases are exhaustive in `tagsSettingChanged`, so the result is
determined for every input — no output component is left free. -/
def problem_spec_resolveTagMap
    (tagsSettingChanged : Bool)
    (defaultTags overrideTags prevTagMap result : List (Int × String)) : Prop :=
  (tagsSettingChanged = true →
      result = mergeTags defaultTags overrideTags) ∧
  (tagsSettingChanged = false →
      result = prevTagMap)
-- post-conditions-end

-- impl-start
def implementation_resolveTagMap
    (tagsSettingChanged : Bool)
    (defaultTags overrideTags prevTagMap : List (Int × String)) :
    List (Int × String) := Id.run do
  let mut tagMap := prevTagMap
  if tagsSettingChanged then
    tagMap := mergeTags defaultTags overrideTags
  return tagMap
-- impl-end

-- proof-start
theorem correct_resolveTagMap :
    ∀ (tagsSettingChanged : Bool)
      (defaultTags overrideTags prevTagMap : List (Int × String)),
      problem_spec_resolveTagMap tagsSettingChanged defaultTags overrideTags prevTagMap
        (implementation_resolveTagMap tagsSettingChanged defaultTags overrideTags prevTagMap) := by
  intro tagsSettingChanged defaultTags overrideTags prevTagMap
  refine ⟨fun h => ?_, fun h => ?_⟩ <;>
    subst h <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec is TOTAL and FULLY PINNED: problem_spec_resolveTagMap constrains result to an EXACT list in both boolean cases (tagsSettingChanged=true -> result = mergeTags d o = o++d; false -> result = prevTagMap). Any proof-closing impl is forced to return the gold value.

Attacks (all same_spec=True, verified via swebench_unified.markers.same_spec on lean backend; verifier = scripts/lean_verify.sh <f>):
- atk_1 prepatch bug (unconditional `return prevTagMap`): exit=1, FAILS to close (true-arm goal `impl = mergeTags d o` unprovable). Reproduces the real prepatch bug (stale cache never recomputed).
- atk_2 swapped merge order (defaultTags ++ overrideTags): exit=1, simp made no progress (d++o != o++d for free vars).
- atk_3 inverted branches: exit=1 (false-arm goal `impl false = prevTagMap` unprovable).
- atk_4 always-merge (ignore flag): exit=1 (false-arm fails).
- atk_5 drop overrides (return defaultTags on change): exit=1, simp no progress.
- atk_6 duplicate append o++d++d (dict-equal but list-unequal, ungrounded-oracle echo of the dict view): exit=1, simp no progress.
All 6 genuinely-wrong impls FAIL to close with real spec-violation goals (not tactic weakness).
- atk_7 ECHO gold-equivalent (`if tc then o++d else prevTagMap`): exit=0 VERIFIES; `#print axioms correct_resolveTagMap` => 'does not depend on any axioms' (clean).
pos_control (gold Solution.lean): exit=0 VERIFIES; #print axioms clean.

Per the fixed G-EQ/G-PANEL-1 derivation, the sole closing clean-axiom impl (atk_7 echo) was materialized to a faithful patch and RUN through the official harness (run_evaluation, princeton-nlp/SWE-bench_Verified, namespace swebench). First materialization had a wrong hunk count (@@-1,7+1,18@@; I split gold's single get_level_tags import into constants+settings = 2 lines) -> IndentationError at apps.py:18 -> unresolved; diagnosed as a patch-materialization defect NOT a spec break (BOTH a FAIL_TO_PASS and an unrelated PASS_TO_PASS test_eq failed = module-import/collection failure signature). Corrected to @@-1,7+1,19@@ (git apply --check clean, ast.parse OK). RE-RUN: run_id atk7fixW resolved=True, FAIL_TO_PASS success=[test_override_settings_level_tags]. GOLD positive-control run_id goldctrlW resolved=True, identical F2P. => the verifying echo RESOLVES, so it is NOT a weakness.

refinement.md audit: every leg is R or I; NO A-leg (no consumed callee axiom, no A-reference) — axiom_check.py is a correct skip stub, meta.json axioms=[] / deep_model_references=[]. No kind-3 leg. R-leg correspondence holds: get_level_tags dict-spread {**DEFAULT_TAGS,**MESSAGE_TAGS} (override-wins) <-> overrideTags ++ defaultTags under first-match lookup (override-wins); validated by G-CONF (120k fuzz, seed 15127). No deep-model callee to break.

Conclusion: no same-spec impl verifies-but-is-wrong. The only verifying non-gold impl is a gold-equivalent echo whose faithful patch resolves. verify => correct holds. SOUND.

Note the recorded meta.json G-EQ=fail(INCONCLUSIVE) is a prior wall/contention artifact of the automated re-audit; this manual pass completed all attacks + the required resolve runs and finds the spec SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
The effective mapping from a message's level to its display tag is derived from
two configuration sources: a built-in set of default tags and a
user-supplied override mapping keyed by the same levels, with the override value
taking precedence whenever a level appears in both. This effective mapping is
held in a cache that downstream code consults to label individual messages.

Whenever a configuration value changes, the cached mapping must stay consistent
with the current configuration:

  * if the configuration value that changed is the message-tag override, the
    effective mapping is recomputed from the current defaults and the current
    overrides;
  * for any other configuration change, the cached mapping is left exactly as it
    was.

Inputs:
  * `tagsSettingChanged` — whether the configuration value that changed is the
    message-tag override;
  * `defaultTags` — the built-in default level→tag pairs;
  * `overrideTags` — the user-supplied override level→tag pairs;
  * `prevTagMap` — the cached mapping in effect prior to the change.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The defaults,
-- the overrides, and the previously-cached mapping all enter as plain data, and
-- the change indicator enters as a Bool. The only operation is the combination
-- of the two configuration sources into the effective mapping (overrides taking
-- precedence per level), modeled directly below. Hence no `opaque`/`axiom`
-- callee contract is required.
-- axioms-end

-- pure-start
/-- The effective level→tag mapping built from a set of default pairs and a set
of override pairs: the overrides take precedence over the defaults whenever a
level is present in both. Modeled as the overrides followed by the defaults, so
that a first-match lookup over the result returns the override value when one
exists for a level and the default value otherwise (the key set being the union
of both sources). -/
def mergeTags (defaultTags overrideTags : List (Int × String)) : List (Int × String) :=
  overrideTags ++ defaultTags
-- pure-end

-- post-conditions-start
/-- The cached mapping is fully pinned to the inputs:

  * when the configuration value that changed is the message-tag override, the
    result is exactly the effective mapping recomputed from the current defaults
    and overrides;
  * otherwise the result is exactly the previously-cached mapping, unchanged.

The two cases are exhaustive in `tagsSettingChanged`, so the result is
determined for every input — no output component is left free. -/
def problem_spec_resolveTagMap
    (tagsSettingChanged : Bool)
    (defaultTags overrideTags prevTagMap result : List (Int × String)) : Prop :=
  (tagsSettingChanged = true →
      result = mergeTags defaultTags overrideTags) ∧
  (tagsSettingChanged = false →
      result = prevTagMap)
-- post-conditions-end

-- impl-start
def implementation_resolveTagMap
    (tagsSettingChanged : Bool)
    (defaultTags overrideTags prevTagMap : List (Int × String)) :
    List (Int × String) := Id.run do
  let mut tagMap := prevTagMap
  if tagsSettingChanged then
    tagMap := mergeTags defaultTags overrideTags
  return tagMap
-- impl-end

-- proof-start
theorem correct_resolveTagMap :
    ∀ (tagsSettingChanged : Bool)
      (defaultTags overrideTags prevTagMap : List (Int × String)),
      problem_spec_resolveTagMap tagsSettingChanged defaultTags overrideTags prevTagMap
        (implementation_resolveTagMap tagsSettingChanged defaultTags overrideTags prevTagMap) := by
  intro tagsSettingChanged defaultTags overrideTags prevTagMap
  refine ⟨fun h => ?_, fun h => ?_⟩ <;>
    subst h <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec is TOTAL and FULLY PINNED: problem_spec_resolveTagMap constrains result to an EXACT list in both boolean cases (tagsSettingChanged=true -> result = mergeTags d o = o++d; false -> result = prevTagMap). Any proof-closing impl is forced to return the gold value.

Attacks (all same_spec=True, verified via swebench_unified.markers.same_spec on lean backend; verifier = scripts/lean_verify.sh <f>):
- atk_1 prepatch bug (unconditional `return prevTagMap`): exit=1, FAILS to close (true-arm goal `impl = mergeTags d o` unprovable). Reproduces the real prepatch bug (stale cache never recomputed).
- atk_2 swapped merge order (defaultTags ++ overrideTags): exit=1, simp made no progress (d++o != o++d for free vars).
- atk_3 inverted branches: exit=1 (false-arm goal `impl false = prevTagMap` unprovable).
- atk_4 always-merge (ignore flag): exit=1 (false-arm fails).
- atk_5 drop overrides (return defaultTags on change): exit=1, simp no progress.
- atk_6 duplicate append o++d++d (dict-equal but list-unequal, ungrounded-oracle echo of the dict view): exit=1, simp no progress.
All 6 genuinely-wrong impls FAIL to close with real spec-violation goals (not tactic weakness).
- atk_7 ECHO gold-equivalent (`if tc then o++d else prevTagMap`): exit=0 VERIFIES; `#print axioms correct_resolveTagMap` => 'does not depend on any axioms' (clean).
pos_control (gold Solution.lean): exit=0 VERIFIES; #print axioms clean.

Per the fixed G-EQ/G-PANEL-1 derivation, the sole closing clean-axiom impl (atk_7 echo) was materialized to a faithful patch and RUN through the official harness (run_evaluation, princeton-nlp/SWE-bench_Verified, namespace swebench). First materialization had a wrong hunk count (@@-1,7+1,18@@; I split gold's single get_level_tags import into constants+settings = 2 lines) -> IndentationError at apps.py:18 -> unresolved; diagnosed as a patch-materialization defect NOT a spec break (BOTH a FAIL_TO_PASS and an unrelated PASS_TO_PASS test_eq failed = module-import/collection failure signature). Corrected to @@-1,7+1,19@@ (git apply --check clean, ast.parse OK). RE-RUN: run_id atk7fixW resolved=True, FAIL_TO_PASS success=[test_override_settings_level_tags]. GOLD positive-control run_id goldctrlW resolved=True, identical F2P. => the verifying echo RESOLVES, so it is NOT a weakness.

refinement.md audit: every leg is R or I; NO A-leg (no consumed callee axiom, no A-reference) — axiom_check.py is a correct skip stub, meta.json axioms=[] / deep_model_references=[]. No kind-3 leg. R-leg correspondence holds: get_level_tags dict-spread {**DEFAULT_TAGS,**MESSAGE_TAGS} (override-wins) <-> overrideTags ++ defaultTags under first-match lookup (override-wins); validated by G-CONF (120k fuzz, seed 15127). No deep-model callee to break.

Conclusion: no same-spec impl verifies-but-is-wrong. The only verifying non-gold impl is a gold-equivalent echo whose faithful patch resolves. verify => correct holds. SOUND.

Note the recorded meta.json G-EQ=fail(INCONCLUSIVE) is a prior wall/contention artifact of the automated re-audit; this manual pass completed all attacks + the required resolve runs and finds the spec SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness attack (spec-too-strong / drift) FAILED — spec is faithful to the real callee.

### Verification
- Lean: lean_verify.sh exit 0; `#print axioms correct_resolveTagMap` => 'does not depend on any axioms' (no sorryAx, genuine proof).
- Spec region byte-identical between Solution.lean and Solution_prepatch.lean (imports→pre-impl: docstring, mergeTags, problem_spec_resolveTagMap all identical); only impl differs. Prepatch impl (no recompute branch) genuinely fails the spec => good discriminating power.
- Real callee at base 9a6e2df3a8: get_level_tags() = {**constants.DEFAULT_TAGS, **getattr(settings,'MESSAGE_TAGS',{})}; gold receiver recomputes LEVEL_TAGS iff setting=='MESSAGE_TAGS', else leaves it untouched. Downstream consumer is LEVEL_TAGS.get(level,'') — a pure dict lookup, so ordering is unobservable and the dict abstraction is the correct faithfulness target.

### SPEC vs REAL:
- tagsSettingChanged=true branch: model result = mergeTags defaultTags overrideTags = overrideTags ++ defaultTags. Under first-match assoc lookup this denotes exactly {**DEFAULT_TAGS, **MESSAGE_TAGS} (override-wins) because the real Python sources are dicts with unique keys within each source; cross-source overlap resolves override-wins in both. Confirmed on the real domain (unique keys per source) — full agreement.
- tagsSettingChanged=false branch: result = prevTagMap = 'LEVEL_TAGS unchanged'. Matches exactly.

BREAK ATTEMPT: The only constructible divergence is intra-source DUPLICATE keys, e.g. overrideTags=[(20,'first'),(20,'second')] with tc=true => oracle dict {20:'second'} (last-wins in **spread) vs model first-match {20:'first'}. But this input is UNREACHABLE: constants.DEFAULT_TAGS and settings.MESSAGE_TAGS are genuine Python dicts, so keys are unique within each source by construction. No valid input in the modeled domain produces a divergence. The conformance harness correctly samples unique keys per source (rng.sample) and passes 120,014 inputs with 0 disagreements.

The spec is neither too strong nor drifting — it pins result to a list that denotes exactly the real callee's dict on every reachable input. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view screened mechanically (leakage.screen, lean backend): passed=True, no hard failures. same_spec(Solution, Solution_prepatch)=True (spec region byte-identical; impl/proof elided in the view). Semantic review: the public problem_statement already discloses the bug and desired behavior (LEVEL_TAGS not updated under @override_settings, Message.level_tag returns empty string, new message tags not reflected). The spec view exposes NONE of the gold-edit specifics: identifiers are neutral (resolveTagMap, tagsSettingChanged, defaultTags, overrideTags, prevTagMap, mergeTags) and embed no patched symbol (update_level_tags, ready, get_level_tags, setting_changed, LEVEL_TAGS, MessagesConfig); no diff markers; patched file/module path (apps.py / django.contrib.messages.apps) absent; no gold-patch line reproduced; no bug/fix narration in comments; the receiver-registration MECHANISM (setting_changed.connect in MessagesConfig.ready) is not narrated — only the behavioral requirement (recompute the effective mapping from current defaults+overrides when the message-tag override changes; otherwise leave the cache unchanged), which is directly implied by the public problem statement and which any faithful spec must state. Gold changed symbols detected: ready, update_level_tags — neither appears in the spec view. No leakage beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
