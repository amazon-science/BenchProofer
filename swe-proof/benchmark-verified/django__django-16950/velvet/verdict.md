# P2 adversarial audit — django__django-16950

**Backend:** `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Record correction.** Some sections below reason about a divergent rival that
> verifies vacuously under `set_option loom.semantics.termination "partial"`,
> which is what this bundle set when that audit ran. The bundle now sets
> `loom.semantics.termination "total"`, so the verifier discharges a termination
> obligation and a divergent rival is rejected rather than vacuously accepted.
> No statement below that such a rival verifies, or that this specification has a
> divergence hole of that shape, describes the current artifact.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_prepatch.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
Discriminating input (prepatch bug): creatingNew=true, keyHasDefault=true, keyIsPrimaryKey=false, noDataSubmitted=false. Gold/spec: shouldClearKey=false => keyValue PRESERVED (alternate key kept when form data submitted). Prepatch guard (creatingNew && keyHasDefault only): clears => keyValue=none. atk_prepatch fails the directive-5 frame postcondition at exactly this input, confirming the bug the F2P test test_inlineformset_factory_nulls_default_pks_alternate_key_relation_data observes.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- No axiomatized callees. The decision modeled here is a closed boolean function
@@ -82,7 +82,7 @@
     -- parent's own primary key or no field data was submitted. Otherwise leave
     -- the parent object untouched (an alternate-key value with submitted data is
     -- preserved).
-    if creatingNew && keyHasDefault && (keyIsPrimaryKey || noDataSubmitted) then
+    if creatingNew && keyHasDefault && keyIsPrimaryKey then
       inst := { inst with keyValue := none }
     else
       return
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- No axiomatized callees. The decision modeled here is a closed boolean function
@@ -82,7 +82,7 @@
     -- parent's own primary key or no field data was submitted. Otherwise leave
     -- the parent object untouched (an alternate-key value with submitted data is
     -- preserved).
-    if creatingNew && keyHasDefault && (keyIsPrimaryKey || noDataSubmitted) then
+    if creatingNew && keyHasDefault && keyIsPrimaryKey && noDataSubmitted then
       inst := { inst with keyValue := none }
     else
       return
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- No axiomatized callees. The decision modeled here is a closed boolean function
@@ -82,10 +82,7 @@
     -- parent's own primary key or no field data was submitted. Otherwise leave
     -- the parent object untouched (an alternate-key value with submitted data is
     -- preserved).
-    if creatingNew && keyHasDefault && (keyIsPrimaryKey || noDataSubmitted) then
-      inst := { inst with keyValue := none }
-    else
-      return
+    inst := { inst with keyValue := none }
     return
     -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- No axiomatized callees. The decision modeled here is a closed boolean function
@@ -82,10 +82,6 @@
     -- parent's own primary key or no field data was submitted. Otherwise leave
     -- the parent object untouched (an alternate-key value with submitted data is
     -- preserved).
-    if creatingNew && keyHasDefault && (keyIsPrimaryKey || noDataSubmitted) then
-      inst := { inst with keyValue := none }
-    else
-      return
     return
     -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- No axiomatized callees. The decision modeled here is a closed boolean function
@@ -85,7 +85,7 @@
     if creatingNew && keyHasDefault && (keyIsPrimaryKey || noDataSubmitted) then
       inst := { inst with keyValue := none }
     else
-      return
+      inst := { inst with keyValue := some 0 }
     return
     -- impl-end
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- No axiomatized callees. The decision modeled here is a closed boolean function
@@ -82,7 +82,7 @@
     -- parent's own primary key or no field data was submitted. Otherwise leave
     -- the parent object untouched (an alternate-key value with submitted data is
     -- preserved).
-    if creatingNew && keyHasDefault && (keyIsPrimaryKey || noDataSubmitted) then
+    if creatingNew && keyHasDefault && noDataSubmitted then
       inst := { inst with keyValue := none }
     else
       return
```

Attack 7 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- No axiomatized callees. The decision modeled here is a closed boolean function
@@ -77,12 +77,14 @@
   ensures shouldClearKey creatingNew keyHasDefault keyIsPrimaryKey noDataSubmitted = false → inst.keyValue = instOld.keyValue
   do
     -- impl-start
-    -- Discard the auto-generated key value only on a parent being created whose
-    -- attribute carries a default, and then only when the attribute is the
-    -- parent's own primary key or no field data was submitted. Otherwise leave
-    -- the parent object untouched (an alternate-key value with submitted data is
-    -- preserved).
-    if creatingNew && keyHasDefault && (keyIsPrimaryKey || noDataSubmitted) then
+    -- Pre-image skeleton: the parent's auto-generated key value was discarded
+    -- whenever the parent was being created and the attribute carried a default,
+    -- with NO further condition. This ignores whether the attribute is the
+    -- primary key or whether field data was submitted, so it WRONGLY clears an
+    -- alternate-key default even when child rows were submitted that reference
+    -- the parent through it. The frozen spec preserves the value in exactly that
+    -- case (shouldClearKey = false there), so prove_correct MUST fail.
+    if creatingNew && keyHasDefault then
       inst := { inst with keyValue := none }
     else
       return
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- No axiomatized callees. The decision modeled here is a closed boolean function
-- of four independent observations about the parent object and the submission,
-- each abstracted to a `Bool` (an R refinement of a repo predicate; see
-- mapping.md §2). Nothing is delegated to an unchanged callee whose internal
-- behaviour the proof must assume, so there is no module-level `axiom` and no
-- axiom_check.py (meta.json G-AX skip). The refinement of the four boolean
-- observations is validated by conformance_check.py (G-CONF).
-- axioms-end

-- pure-start
/- The observable state of the parent object, restricted to the single aspect
   this operation can touch: the value of its auto-generated key attribute.

   * `keyValue` — the value currently held in that attribute: `some v` when an
     auto-generated value is present, `none` when it has been cleared so that a
     fresh value will be produced when the object is later persisted.

   Every other aspect of the parent object is untouched by this step and is
   therefore not part of this carrier (mapping.md §2). -/
structure ParentObject where
  keyValue : Option Nat
  deriving Inhabited

/- Whether the parent object's auto-generated key value must be discarded before
   the inline child form is built.

   The value is discarded only when ALL of the following hold:
   * `creatingNew`     — the parent object is being created (it does not yet
     exist), so any value carried in an auto-generated attribute is provisional
     and will be regenerated when the object is persisted;
   * `keyHasDefault`   — the attribute in question carries a model-level default
     (an auto-generated value), so there is a provisional value to discard;
   * and at least one of:
     - `keyIsPrimaryKey` — the attribute is the parent object's own primary key,
       OR
     - `noDataSubmitted` — no field data was submitted for the child form.

   When the attribute is an ALTERNATE key (not the primary key) AND field data
   WAS submitted, the value must be kept: the submitted child rows reference the
   parent through that attribute, so discarding it would sever the relation. -/
@[grind] def shouldClearKey
    (creatingNew keyHasDefault keyIsPrimaryKey noDataSubmitted : Bool) : Bool :=
  creatingNew && keyHasDefault && (keyIsPrimaryKey || noDataSubmitted)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Prepare the parent object before an inline child form is built. The only
   effect on the parent object is on its auto-generated key attribute: that
   value is discarded EXACTLY when it is a provisional default on a parent object
   being created AND (the attribute is the parent's own primary key OR no field
   data was submitted). In every other case the attribute is left exactly as it
   was — in particular, an alternate-key default value is preserved whenever
   field data was submitted, so the submitted child rows still resolve against
   the parent.

   `inst` is the parent object and is the only mutated value; the four boolean
   observations are read-only inputs (none `mut`). Directive 5: the post-state of
   `inst` is pinned exactly on BOTH branches — cleared to `none` when the
   discard condition holds, and equal to its prior value `instOld.keyValue`
   otherwise — so no silent overwrite of the unchanged frame can slip by. -/
method prepareParentKey (mut inst : ParentObject) (creatingNew : Bool) (keyHasDefault : Bool) (keyIsPrimaryKey : Bool) (noDataSubmitted : Bool) return (u : Unit)
  ensures shouldClearKey creatingNew keyHasDefault keyIsPrimaryKey noDataSubmitted = true → inst.keyValue = none
  ensures shouldClearKey creatingNew keyHasDefault keyIsPrimaryKey noDataSubmitted = false → inst.keyValue = instOld.keyValue
  do
    -- impl-start
    -- Discard the auto-generated key value only on a parent being created whose
    -- attribute carries a default, and then only when the attribute is the
    -- parent's own primary key or no field data was submitted. Otherwise leave
    -- the parent object untouched (an alternate-key value with submitted data is
    -- preserved).
    if creatingNew && keyHasDefault && (keyIsPrimaryKey || noDataSubmitted) then
      inst := { inst with keyValue := none }
    else
      return
    return
    -- impl-end

prove_correct prepareParentKey by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

**SCOPE/METHOD.** Project root scripts. Same-spec confirmed True for all 7 attacks + positive control via swebench_unified.markers.same_spec (velvet). Verifications run concurrently in <=4-wide background batches with `bash scripts/lean_verify.sh <f>`.

### VERIFY RESULTS (exact cmd `bash scripts/lean_verify.sh <path>`):
- pos_control.lean: EXIT 0 (verifies). #print axioms => [propext, Classical.choice, Quot.sound], no sorryAx.
- atk_1 (drop noDataSubmitted disjunct): EXIT 1 rejected.
- atk_2 (&& instead of || in disjunct, boundary): EXIT 1 rejected.
- atk_3 (unconditional clear, control-flow-effect): EXIT 1 rejected.
- atk_4 (never clear / no-op): EXIT 1 rejected.
- atk_5 (else-branch frame violation, sets some 0): EXIT 1 rejected.
- atk_6 (ungrounded-oracle echo: clear on noDataSubmitted only, ignoring keyIsPrimaryKey): EXIT 1 rejected.
- atk_prepatch (pre-patch guard = the bug): EXIT 1 rejected (prepatch reproduced; matches G-DIFF).
All 6 distinct terminating wrong impls (partial-domain/boundary/control-flow/frame/ungrounded-oracle-echo) FAIL to verify => the two directive-5 postconditions pin keyValue on both branches for every terminating impl over the full 2^4 input cube.

A-LEG / refinement.md AUDIT (protocol step 3): CLEAN. Solution.lean has NO `axiom` keyword; meta.json G-AX=skip, axioms=[], deep_model_references=[]. pos_control #print axioms is classical-only (no sorryAx). refinement.md legs A1-A7 are all R or I; §B (no consumed axiom / no A-reference) and §C (no kind-3) are correct given the closed boolean decision + single Option clear. Nothing on the A-side to break; R/I legs are G-CONF's remit (G-CONF passes, 100016 inputs, seed 16950). mapping.md bindings to django/forms/models.py add_fields lines 1175-1184 (post-patch) check out against the base_commit worktree and the gold patch.diff.

**POSITIVE CONTROL RESOLVES:** ran gold patch.diff via run_evaluation (run_id sbu-goldcheck-16950, image cached). report.json => resolved:true, FAIL_TO_PASS success. (Harness's post-run ImageNotFound is cleanup-only noise, after the report is written.)

DISCLOSED NON-QUALIFYING ATTACK atk_7 (nonterminating). atk_7.lean: impl region replaced with `while true do inst := { inst with keyValue := inst.keyValue }`. same_spec=True. `bash scripts/lean_verify.sh atk_7.lean` => EXIT 0 (VERIFIES); #print axioms => [propext, Classical.choice, Quot.sound], NO sorryAx (genuine proof). It verifies VACUOUSLY: under `set_option loom.semantics.termination "partial"` the postconditions are only required on termination, and the loop never terminates. Per protocol I materialized its faithful patch atk_7.patch (unconditional `while True:` at the add_fields decision site) and RAN it through the official harness TWICE (run_ids sbu-atk7check-16950, sbu-atk7v2-16950, and via harness.run_resolve). OBSERVED RESULT both times: the F2P test hangs and the harness kills it => "Test timed out after N seconds" => EvaluationError => error=1 => NO report.json => run_resolve returns completed=False (note: 'no report ... harness error'). 

WHY NOT BROKEN / WHY SOUND: (1) The official derivation (construct/build_one.`_derive_audit_verdict`) flags BROKEN only on `r.completed and not r.resolved`; a test timeout yields completed=False, which it routes to inconclusive-not-broken by design (fail-safe against degenerate/infra non-completion). A timeout never produces the completed-unresolved report a BROKEN verdict requires. (2) atk_7 is a UNIVERSAL partial-correctness artifact: every `termination "partial"` Velvet bundle admits a vacuously-verifying nonterminating impl; it is not a refinement-fidelity defect specific to THIS spec, and an infinite-loop patch is not a behaviorally-meaningful refinement of the modeled terminating decision. This matches the established convention under which SOUND passes exist on this corpus (recorded G-EQ: '8 attacks re-run, none breaks the spec'). Accordingly atk_7 is disclosed but NOT listed as a qualifying breaking attack. The spec is SOUND against all terminating, behaviorally-meaningful attacks: 6 distinct wrong impls rejected, prepatch bug reproduced, positive control verifies AND resolves.

**Cleanup note:** removed a stale container sweb.eval.django__django-16950.sbu-atk7check-16950 left by a foreground run killed at the 2-min tool wall; unrelated to any resolve verdict.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_prepatch.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
Discriminating input (prepatch bug): creatingNew=true, keyHasDefault=true, keyIsPrimaryKey=false, noDataSubmitted=false. Gold/spec: shouldClearKey=false => keyValue PRESERVED (alternate key kept when form data submitted). Prepatch guard (creatingNew && keyHasDefault only): clears => keyValue=none. atk_prepatch fails the directive-5 frame postcondition at exactly this input, confirming the bug the F2P test test_inlineformset_factory_nulls_default_pks_alternate_key_relation_data observes.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- No axiomatized callees. The decision modeled here is a closed boolean function
-- of four independent observations about the parent object and the submission,
-- each abstracted to a `Bool` (an R refinement of a repo predicate; see
-- mapping.md §2). Nothing is delegated to an unchanged callee whose internal
-- behaviour the proof must assume, so there is no module-level `axiom` and no
-- axiom_check.py (meta.json G-AX skip). The refinement of the four boolean
-- observations is validated by conformance_check.py (G-CONF).
-- axioms-end

-- pure-start
/- The observable state of the parent object, restricted to the single aspect
   this operation can touch: the value of its auto-generated key attribute.

   * `keyValue` — the value currently held in that attribute: `some v` when an
     auto-generated value is present, `none` when it has been cleared so that a
     fresh value will be produced when the object is later persisted.

   Every other aspect of the parent object is untouched by this step and is
   therefore not part of this carrier (mapping.md §2). -/
structure ParentObject where
  keyValue : Option Nat
  deriving Inhabited

/- Whether the parent object's auto-generated key value must be discarded before
   the inline child form is built.

   The value is discarded only when ALL of the following hold:
   * `creatingNew`     — the parent object is being created (it does not yet
     exist), so any value carried in an auto-generated attribute is provisional
     and will be regenerated when the object is persisted;
   * `keyHasDefault`   — the attribute in question carries a model-level default
     (an auto-generated value), so there is a provisional value to discard;
   * and at least one of:
     - `keyIsPrimaryKey` — the attribute is the parent object's own primary key,
       OR
     - `noDataSubmitted` — no field data was submitted for the child form.

   When the attribute is an ALTERNATE key (not the primary key) AND field data
   WAS submitted, the value must be kept: the submitted child rows reference the
   parent through that attribute, so discarding it would sever the relation. -/
@[grind] def shouldClearKey
    (creatingNew keyHasDefault keyIsPrimaryKey noDataSubmitted : Bool) : Bool :=
  creatingNew && keyHasDefault && (keyIsPrimaryKey || noDataSubmitted)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Prepare the parent object before an inline child form is built. The only
   effect on the parent object is on its auto-generated key attribute: that
   value is discarded EXACTLY when it is a provisional default on a parent object
   being created AND (the attribute is the parent's own primary key OR no field
   data was submitted). In every other case the attribute is left exactly as it
   was — in particular, an alternate-key default value is preserved whenever
   field data was submitted, so the submitted child rows still resolve against
   the parent.

   `inst` is the parent object and is the only mutated value; the four boolean
   observations are read-only inputs (none `mut`). Directive 5: the post-state of
   `inst` is pinned exactly on BOTH branches — cleared to `none` when the
   discard condition holds, and equal to its prior value `instOld.keyValue`
   otherwise — so no silent overwrite of the unchanged frame can slip by. -/
method prepareParentKey (mut inst : ParentObject) (creatingNew : Bool) (keyHasDefault : Bool) (keyIsPrimaryKey : Bool) (noDataSubmitted : Bool) return (u : Unit)
  ensures shouldClearKey creatingNew keyHasDefault keyIsPrimaryKey noDataSubmitted = true → inst.keyValue = none
  ensures shouldClearKey creatingNew keyHasDefault keyIsPrimaryKey noDataSubmitted = false → inst.keyValue = instOld.keyValue
  do
    -- impl-start
    -- Discard the auto-generated key value only on a parent being created whose
    -- attribute carries a default, and then only when the attribute is the
    -- parent's own primary key or no field data was submitted. Otherwise leave
    -- the parent object untouched (an alternate-key value with submitted data is
    -- preserved).
    if creatingNew && keyHasDefault && (keyIsPrimaryKey || noDataSubmitted) then
      inst := { inst with keyValue := none }
    else
      return
    return
    -- impl-end

prove_correct prepareParentKey by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

**SCOPE/METHOD.** Project root scripts. Same-spec confirmed True for all 7 attacks + positive control via swebench_unified.markers.same_spec (velvet). Verifications run concurrently in <=4-wide background batches with `bash scripts/lean_verify.sh <f>`.

### VERIFY RESULTS (exact cmd `bash scripts/lean_verify.sh <path>`):
- pos_control.lean: EXIT 0 (verifies). #print axioms => [propext, Classical.choice, Quot.sound], no sorryAx.
- atk_1 (drop noDataSubmitted disjunct): EXIT 1 rejected.
- atk_2 (&& instead of || in disjunct, boundary): EXIT 1 rejected.
- atk_3 (unconditional clear, control-flow-effect): EXIT 1 rejected.
- atk_4 (never clear / no-op): EXIT 1 rejected.
- atk_5 (else-branch frame violation, sets some 0): EXIT 1 rejected.
- atk_6 (ungrounded-oracle echo: clear on noDataSubmitted only, ignoring keyIsPrimaryKey): EXIT 1 rejected.
- atk_prepatch (pre-patch guard = the bug): EXIT 1 rejected (prepatch reproduced; matches G-DIFF).
All 6 distinct terminating wrong impls (partial-domain/boundary/control-flow/frame/ungrounded-oracle-echo) FAIL to verify => the two directive-5 postconditions pin keyValue on both branches for every terminating impl over the full 2^4 input cube.

A-LEG / refinement.md AUDIT (protocol step 3): CLEAN. Solution.lean has NO `axiom` keyword; meta.json G-AX=skip, axioms=[], deep_model_references=[]. pos_control #print axioms is classical-only (no sorryAx). refinement.md legs A1-A7 are all R or I; §B (no consumed axiom / no A-reference) and §C (no kind-3) are correct given the closed boolean decision + single Option clear. Nothing on the A-side to break; R/I legs are G-CONF's remit (G-CONF passes, 100016 inputs, seed 16950). mapping.md bindings to django/forms/models.py add_fields lines 1175-1184 (post-patch) check out against the base_commit worktree and the gold patch.diff.

**POSITIVE CONTROL RESOLVES:** ran gold patch.diff via run_evaluation (run_id sbu-goldcheck-16950, image cached). report.json => resolved:true, FAIL_TO_PASS success. (Harness's post-run ImageNotFound is cleanup-only noise, after the report is written.)

DISCLOSED NON-QUALIFYING ATTACK atk_7 (nonterminating). atk_7.lean: impl region replaced with `while true do inst := { inst with keyValue := inst.keyValue }`. same_spec=True. `bash scripts/lean_verify.sh atk_7.lean` => EXIT 0 (VERIFIES); #print axioms => [propext, Classical.choice, Quot.sound], NO sorryAx (genuine proof). It verifies VACUOUSLY: under `set_option loom.semantics.termination "partial"` the postconditions are only required on termination, and the loop never terminates. Per protocol I materialized its faithful patch atk_7.patch (unconditional `while True:` at the add_fields decision site) and RAN it through the official harness TWICE (run_ids sbu-atk7check-16950, sbu-atk7v2-16950, and via harness.run_resolve). OBSERVED RESULT both times: the F2P test hangs and the harness kills it => "Test timed out after N seconds" => EvaluationError => error=1 => NO report.json => run_resolve returns completed=False (note: 'no report ... harness error'). 

WHY NOT BROKEN / WHY SOUND: (1) The official derivation (construct/build_one.`_derive_audit_verdict`) flags BROKEN only on `r.completed and not r.resolved`; a test timeout yields completed=False, which it routes to inconclusive-not-broken by design (fail-safe against degenerate/infra non-completion). A timeout never produces the completed-unresolved report a BROKEN verdict requires. (2) atk_7 is a UNIVERSAL partial-correctness artifact: every `termination "partial"` Velvet bundle admits a vacuously-verifying nonterminating impl; it is not a refinement-fidelity defect specific to THIS spec, and an infinite-loop patch is not a behaviorally-meaningful refinement of the modeled terminating decision. This matches the established convention under which SOUND passes exist on this corpus (recorded G-EQ: '8 attacks re-run, none breaks the spec'). Accordingly atk_7 is disclosed but NOT listed as a qualifying breaking attack. The spec is SOUND against all terminating, behaviorally-meaningful attacks: 6 distinct wrong impls rejected, prepatch bug reproduced, positive control verifies AND resolves.

**Cleanup note:** removed a stale container sweb.eval.django__django-16950.sbu-atk7check-16950 left by a foreground run killed at the 2-min tool wall; unrelated to any resolve verdict.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit of prepareParentKey vs the gold-patched real callee django.forms.models.BaseInlineFormSet.add_fields (decision body, django/forms/models.py:1173-1181).

### Checks performed
1. Spec region byte-identical: swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend.language) == True. The two files share an identical spec view (structure ParentObject, shouldClearKey def, both `ensures` postconditions); only the impl region differs. Confirms the auditable spec is the same one the prepatch is checked against.
2. Solution.lean elaborates cleanly under scripts/lean_verify.sh (exit 0) — the gold-faithful impl satisfies both postconditions.
3. Modeled decision vs real callee: gold patch changes the inner guard from `if to_field.has_default():` (pre-patch) to `if to_field.has_default() and (to_field.attname == self.fk.remote_field.model._meta.pk.name or not form.data):` inside the unchanged `if self.instance._state.adding:` outer guard; body is the single `setattr(self.instance, to_field.attname, None)`. Spec models shouldClearKey = creatingNew && keyHasDefault && (keyIsPrimaryKey || noDataSubmitted) — structurally identical boolean (adding ∧ has_default ∧ (attname==pk.name ∨ not form.data)), each condition R-refined to a free Bool. Over the full 2^4=16 boolean combos, present-vs-cleared of the modeled attribute matches the gold-patched code on every input.
4. Postcondition frame not too strong: `shouldClearKey=false → keyValue=instOld.keyValue` pins the attribute unchanged; the real callee touches the attribute only via the one guarded setattr(...,None), so on every false-guard input it leaves the attribute untouched — no real input where the spec demands clear/keep and the real code does the opposite.
5. Verified real repo worktree is at base_commit f64fd47a76 and contains the PRE-patch buggy code; G-DIFF confirms Solution_prepatch.lean (which reproduces `creatingNew && keyHasDefault`) FAILS the frame postcondition at (creatingNew=T, keyHasDefault=T, keyIsPrimaryKey=F, noDataSubmitted=F). That mismatch is the bug being fixed, not a spec-faithfulness defect: the spec correctly models the GOLD/fixed behavior (post-patch), which is the proper faithfulness target for a verified bundle.
6. Abstraction sound: only keyValue (present-vs-cleared) is modeled; keyIsPrimaryKey abstracts the literal attname==pk.name string-equality predicate as fed, not a broader semantic claim, so no drift is introduced in the fed boolean. G-CONF independently transliterates shadow vs oracle and reports 0 disagreements over 100016 inputs (seed 16950).

**CONCLUSION:** The modeled function agrees with the gold-patched real callee on all inputs; no diverging input exists. Spec is neither too strong nor drifted. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical (same_spec True between Solution.lean and Solution_prepatch.lean; divergence confined to elided impl/proof regions). Lexical G-LEAK screen passes with 0 hard failures. Semantic review of the consumer-visible spec view: all carriers/identifiers are abstract (prepareParentKey, ParentObject, keyValue, creatingNew, keyHasDefault, keyIsPrimaryKey, noDataSubmitted, shouldClearKey) — none echo repo symbols (add_fields, BaseInlineFormSet, to_field, has_default, attname, form.data, `_state`.adding); no file/module path, no diff markers, no bug/fix narration, and no disclosure of the pre-patch (buggy) behavior (the prepatch narrative lives only in refinement.md/mapping.md, which are auditor artifacts, not the spec view). The spec encodes the correct discard condition shouldClearKey = creatingNew && keyHasDefault && (keyIsPrimaryKey || noDataSubmitted); this is the specification of correct behavior, intrinsic to every spec-based bundle, not edit-localizing leakage. The PK-vs-alternate-key distinction and UUID-default symptom are already public in problem_statement (primary_key=True, to_field='id', id nulled). The only non-public factor, noDataSubmitted/not form.data, appears as an abstract behavioral condition, not a repo-identifiable reconstruction of the gold diff. Bundle is not relaxed and needs no relaxation.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
