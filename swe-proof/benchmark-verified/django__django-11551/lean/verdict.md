# P2 adversarial audit — django__django-11551

**Backend:** `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -85,19 +85,12 @@
     return []
   if adminHasAttr then
     return []
-  -- Resolve a field for the entry: prefer the metadata lookup, then fall back to
-  -- model attribute access. If neither route yields a field, the entry is
-  -- unresolvable.
-  let mut fieldIsM2M : Bool := false
-  match modelField with
-  | some m => fieldIsM2M := m
-  | none =>
-    match modelAttr with
-    | some m => fieldIsM2M := m
-    | none => return ["E108"]
-  if fieldIsM2M then
-    return ["E109"]
-  return []
+  match modelAttr with
+  | some _ =>
+    match modelField with
+    | none => return []
+    | some m => if m then return ["E109"] else return []
+  | none => return ["E108"]
 -- impl-end
 
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,24 +80,7 @@
 -- impl-start
 def implementation_validateDisplayItem
     (itemCallable adminHasAttr : Bool) (modelField modelAttr : Option Bool)
-    : List String := Id.run do
-  if itemCallable then
-    return []
-  if adminHasAttr then
-    return []
-  -- Resolve a field for the entry: prefer the metadata lookup, then fall back to
-  -- model attribute access. If neither route yields a field, the entry is
-  -- unresolvable.
-  let mut fieldIsM2M : Bool := false
-  match modelField with
-  | some m => fieldIsM2M := m
-  | none =>
-    match modelAttr with
-    | some m => fieldIsM2M := m
-    | none => return ["E108"]
-  if fieldIsM2M then
-    return ["E109"]
-  return []
+    : List String := []
 -- impl-end
 
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -85,18 +85,15 @@
     return []
   if adminHasAttr then
     return []
-  -- Resolve a field for the entry: prefer the metadata lookup, then fall back to
-  -- model attribute access. If neither route yields a field, the entry is
-  -- unresolvable.
   let mut fieldIsM2M : Bool := false
   match modelField with
   | some m => fieldIsM2M := m
   | none =>
     match modelAttr with
     | some m => fieldIsM2M := m
-    | none => return ["E108"]
+    | none => return ["E109"]
   if fieldIsM2M then
-    return ["E109"]
+    return ["E108"]
   return []
 -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -85,14 +85,11 @@
     return []
   if adminHasAttr then
     return []
-  -- Resolve a field for the entry: prefer the metadata lookup, then fall back to
-  -- model attribute access. If neither route yields a field, the entry is
-  -- unresolvable.
   let mut fieldIsM2M : Bool := false
-  match modelField with
+  match modelAttr with
   | some m => fieldIsM2M := m
   | none =>
-    match modelAttr with
+    match modelField with
     | some m => fieldIsM2M := m
     | none => return ["E108"]
   if fieldIsM2M then
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -80,24 +80,14 @@
 -- impl-start
 def implementation_validateDisplayItem
     (itemCallable adminHasAttr : Bool) (modelField modelAttr : Option Bool)
-    : List String := Id.run do
-  if itemCallable then
-    return []
-  if adminHasAttr then
-    return []
-  -- Resolve a field for the entry: prefer the metadata lookup, then fall back to
-  -- model attribute access. If neither route yields a field, the entry is
-  -- unresolvable.
-  let mut fieldIsM2M : Bool := false
-  match modelField with
-  | some m => fieldIsM2M := m
-  | none =>
-    match modelAttr with
-    | some m => fieldIsM2M := m
-    | none => return ["E108"]
-  if fieldIsM2M then
-    return ["E109"]
-  return []
+    : List String :=
+  if itemCallable then []
+  else if adminHasAttr then []
+  else match modelField with
+    | some m => if m then ["E109"] else []
+    | none => match modelAttr with
+      | some m => if m then ["E109"] else []
+      | none => ["E108"]
 -- impl-end
 
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -82,12 +82,9 @@
     (itemCallable adminHasAttr : Bool) (modelField modelAttr : Option Bool)
     : List String := Id.run do
   if itemCallable then
-    return []
+    return ["E108"]
   if adminHasAttr then
     return []
-  -- Resolve a field for the entry: prefer the metadata lookup, then fall back to
-  -- model attribute access. If neither route yields a field, the entry is
-  -- unresolvable.
   let mut fieldIsM2M : Bool := false
   match modelField with
   | some m => fieldIsM2M := m
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -85,19 +85,12 @@
     return []
   if adminHasAttr then
     return []
-  -- Resolve a field for the entry: prefer the metadata lookup, then fall back to
-  -- model attribute access. If neither route yields a field, the entry is
-  -- unresolvable.
-  let mut fieldIsM2M : Bool := false
   match modelField with
-  | some m => fieldIsM2M := m
+  | some _ => return []
   | none =>
     match modelAttr with
-    | some m => fieldIsM2M := m
+    | some _ => return []
     | none => return ["E108"]
-  if fieldIsM2M then
-    return ["E109"]
-  return []
 -- impl-end
 
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Validating one entry of an admin screen's column configuration.

When an admin registration lists the columns to display for a model, each listed
entry must resolve to something usable: a callable, an attribute of the admin
object itself, a concrete model field, or an attribute/method reachable on the
model. This routine decides, for a SINGLE listed entry, whether the entry is
acceptable and — if not — which diagnostic to emit.

The decision rests on four independent observations made about the entry:

* whether the entry is itself callable;
* whether the admin object exposes the entry as one of its own attributes;
* whether the model's metadata can produce a concrete field for the entry (it
  either yields a field or reports that no such field exists);
* whether the entry is reachable as an attribute on the model class (this access
  either yields a value or fails).

A field obtained either way additionally carries one relevant property: whether
it is a many-to-many relation.

The acceptance rule, abstractly:

* a callable entry is always acceptable;
* otherwise, an entry that is an attribute of the admin object is acceptable;
* otherwise the routine resolves a field for the entry — preferring the model
  metadata, and falling back to model attribute access. If a field is resolved
  by EITHER route, the entry is acceptable unless that field is a many-to-many
  relation, in which case the "must not be a many-to-many" diagnostic
  (`admin.E109`) is emitted;
* only when NEITHER route yields a field is the entry rejected as unresolvable,
  with the "not a callable / attribute / field" diagnostic (`admin.E108`).

The result is the (possibly empty) list of diagnostic identifiers produced for
the entry. The behavior is stated as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract. The four observations the
-- routine makes about the entry — callability, admin-attribute presence, the
-- metadata field lookup, and model attribute access — together with whether a
-- resolved field is a many-to-many relation, are supplied as the inputs below;
-- the acceptance/diagnostic logic is spelled out concretely.
-- axioms-end

-- pure-start
-- No additional pure helpers are needed; the decision is expressed directly.
-- pure-end

-- post-conditions-start
/-- Input→output relation for validating one display-configuration entry.

Inputs (the observations available at the decision point):
* `itemCallable` — the entry is callable;
* `adminHasAttr` — the entry is an attribute of the admin object;
* `modelField`   — the model-metadata field lookup: `none` = no such field,
                    `some b` = a field whose many-to-many flag is `b`;
* `modelAttr`    — model attribute access: `none` = no such attribute,
                    `some b` = a value whose many-to-many flag is `b`.

`result` is the list of diagnostic identifiers (empty = acceptable). The relation
pins the result in every case. -/
def problem_spec_validateDisplayItem
    (itemCallable adminHasAttr : Bool) (modelField modelAttr : Option Bool)
    (result : List String) : Prop :=
  (itemCallable = true → result = []) ∧
  (itemCallable = false → adminHasAttr = true → result = []) ∧
  (itemCallable = false → adminHasAttr = false → ∀ m, modelField = some m →
      result = (if m then ["E109"] else [])) ∧
  (itemCallable = false → adminHasAttr = false → modelField = none →
      ∀ m, modelAttr = some m → result = (if m then ["E109"] else [])) ∧
  (itemCallable = false → adminHasAttr = false → modelField = none → modelAttr = none →
      result = ["E108"])
-- post-conditions-end

-- impl-start
def implementation_validateDisplayItem
    (itemCallable adminHasAttr : Bool) (modelField modelAttr : Option Bool)
    : List String := Id.run do
  if itemCallable then
    return []
  if adminHasAttr then
    return []
  let mut fieldIsM2M : Bool := false
  match modelField with
  | some m => fieldIsM2M := m
  | none =>
    match modelAttr with
    | some m => fieldIsM2M := m
    | none => return ["E108"]
  if fieldIsM2M then
    return ["E109"]
  return []
-- impl-end


-- proof-start
theorem correct_validateDisplayItem :
    ∀ (itemCallable adminHasAttr : Bool) (modelField modelAttr : Option Bool),
      problem_spec_validateDisplayItem itemCallable adminHasAttr modelField modelAttr
        (implementation_validateDisplayItem itemCallable adminHasAttr modelField modelAttr) := by
  intro itemCallable adminHasAttr modelField modelAttr
  cases itemCallable <;> cases adminHasAttr <;>
    cases modelField <;> cases modelAttr <;>
    simp_all [problem_spec_validateDisplayItem, implementation_validateDisplayItem, Id.run, bind, pure]

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

**SPEC STRUCTURE:** problem_spec_validateDisplayItem is a TOTAL input->output relation pinning `result` uniquely at every one of the `2*2*3*3` = 36 observable points (itemCallable, adminHasAttr : Bool; modelField, modelAttr : Option Bool). No gaps, no contradictions => any verifying impl is behaviorally equal to the oracle. This predicts SOUND; I attempted genuine falsification with 7 distinct same-spec impls.

**SAME-SPEC:** all 7 attacks + positive control confirmed same_spec=True via swebench_unified.markers.same_spec (only impl region edited; axioms/pure/pre/post byte-identical).

### ATTACKS (cmd: `bash scripts/lean_verify.sh <f>`; project root):
- atk_1 (PREPATCH BUG, gate on modelAttr; field resolved only when modelAttr=some): exit=1, error 'unsolved goals' at proof. Reproduces the F2P bug (modelField=some, modelAttr=none wrongly rejected E108). prepatch_reproduced=true.
- atk_2 (partial-domain, always return []): exit=1, unsolved goals.
- atk_3 (boundary, swap E108<->E109): exit=1, unsolved goals.
- atk_4 (control-flow-effect, prefer modelAttr's M2M flag over modelField when both some): exit=1, unsolved goals.
- atk_5 (ungrounded-oracle echo, nested-if transliteration behaviorally identical to gold): exit=0, VERIFIES clean (only unusedSimpArgs linter warnings; no sorry/admit; correct_ theorem closed).
- atk_6 (reject callable, return E108 when itemCallable): exit=1, unsolved goals.
- atk_7 (flag-off, never emit E109): exit=1, unsolved goals.
pos_control (gold impl): exit=0, verifies.

RESOLVE (protocol step 2, for the one closing impl atk_5): atk_5 is op-for-op behaviorally identical to the gold patched control flow, so its faithful refined patch IS the gold patch. Materialized at atk_5.patch and EXECUTED run_resolve('django__django-11551', ...) => RESOLVED=True, COMPLETED=True, note='resolved'. Since the only clean-axiom verifying attack's faithful patch RESOLVES, verify does NOT diverge from correct. Per resolved echo-attack policy a resolving echo of gold is not a weakness.

**AXIOMS:** Solution.lean axioms-start/axioms-end block is empty (no axiom declarations); correct_validateDisplayItem proved by cases+simp_all with no axiom appeals. atk_5 verifies with the same clean proof discharge (no sorry, no extra axioms). #print-axioms concern moot: no user axioms in the bundle.

**REFINEMENT AUDIT:** all 7 rows are R (inputs type-refinement of the four UNCHANGED callee outcomes callable/hasattr/get_field/getattr), I (callable accept, admin-attr accept, trailing non-M2M accept), or A-reference (get_field-preferred field-resolution flow + M2M rejection + both-fail E108), validated by G-CONF conformance_check.py. NO kind-3 legs, NO consumed axioms. A-reference correspondence holds: modelField consulted before modelAttr matching patch (get_field tried first, getattr only on FieldDoesNotExist); conformance oracle is a faithful in-process replica exhaustive over all 36 points + 120000-point fuzz (SEED=20240709). axiom_check.py is a skip stub (justified: no axioms).

**VERDICT:** SOUND. 7 attacks run (>=5), 6 genuinely-distinct wrong impls all FAIL to verify (genuine 'unsolved goals' spec violations), 1 verifying impl is a behavioral echo whose faithful patch resolves. Spec is total and correctly discriminating; verify => correct holds.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Validating one entry of an admin screen's column configuration.

When an admin registration lists the columns to display for a model, each listed
entry must resolve to something usable: a callable, an attribute of the admin
object itself, a concrete model field, or an attribute/method reachable on the
model. This routine decides, for a SINGLE listed entry, whether the entry is
acceptable and — if not — which diagnostic to emit.

The decision rests on four independent observations made about the entry:

* whether the entry is itself callable;
* whether the admin object exposes the entry as one of its own attributes;
* whether the model's metadata can produce a concrete field for the entry (it
  either yields a field or reports that no such field exists);
* whether the entry is reachable as an attribute on the model class (this access
  either yields a value or fails).

A field obtained either way additionally carries one relevant property: whether
it is a many-to-many relation.

The acceptance rule, abstractly:

* a callable entry is always acceptable;
* otherwise, an entry that is an attribute of the admin object is acceptable;
* otherwise the routine resolves a field for the entry — preferring the model
  metadata, and falling back to model attribute access. If a field is resolved
  by EITHER route, the entry is acceptable unless that field is a many-to-many
  relation, in which case the "must not be a many-to-many" diagnostic
  (`admin.E109`) is emitted;
* only when NEITHER route yields a field is the entry rejected as unresolvable,
  with the "not a callable / attribute / field" diagnostic (`admin.E108`).

The result is the (possibly empty) list of diagnostic identifiers produced for
the entry. The behavior is stated as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract. The four observations the
-- routine makes about the entry — callability, admin-attribute presence, the
-- metadata field lookup, and model attribute access — together with whether a
-- resolved field is a many-to-many relation, are supplied as the inputs below;
-- the acceptance/diagnostic logic is spelled out concretely.
-- axioms-end

-- pure-start
-- No additional pure helpers are needed; the decision is expressed directly.
-- pure-end

-- post-conditions-start
/-- Input→output relation for validating one display-configuration entry.

Inputs (the observations available at the decision point):
* `itemCallable` — the entry is callable;
* `adminHasAttr` — the entry is an attribute of the admin object;
* `modelField`   — the model-metadata field lookup: `none` = no such field,
                    `some b` = a field whose many-to-many flag is `b`;
* `modelAttr`    — model attribute access: `none` = no such attribute,
                    `some b` = a value whose many-to-many flag is `b`.

`result` is the list of diagnostic identifiers (empty = acceptable). The relation
pins the result in every case. -/
def problem_spec_validateDisplayItem
    (itemCallable adminHasAttr : Bool) (modelField modelAttr : Option Bool)
    (result : List String) : Prop :=
  (itemCallable = true → result = []) ∧
  (itemCallable = false → adminHasAttr = true → result = []) ∧
  (itemCallable = false → adminHasAttr = false → ∀ m, modelField = some m →
      result = (if m then ["E109"] else [])) ∧
  (itemCallable = false → adminHasAttr = false → modelField = none →
      ∀ m, modelAttr = some m → result = (if m then ["E109"] else [])) ∧
  (itemCallable = false → adminHasAttr = false → modelField = none → modelAttr = none →
      result = ["E108"])
-- post-conditions-end

-- impl-start
def implementation_validateDisplayItem
    (itemCallable adminHasAttr : Bool) (modelField modelAttr : Option Bool)
    : List String := Id.run do
  if itemCallable then
    return []
  if adminHasAttr then
    return []
  let mut fieldIsM2M : Bool := false
  match modelField with
  | some m => fieldIsM2M := m
  | none =>
    match modelAttr with
    | some m => fieldIsM2M := m
    | none => return ["E108"]
  if fieldIsM2M then
    return ["E109"]
  return []
-- impl-end


-- proof-start
theorem correct_validateDisplayItem :
    ∀ (itemCallable adminHasAttr : Bool) (modelField modelAttr : Option Bool),
      problem_spec_validateDisplayItem itemCallable adminHasAttr modelField modelAttr
        (implementation_validateDisplayItem itemCallable adminHasAttr modelField modelAttr) := by
  intro itemCallable adminHasAttr modelField modelAttr
  cases itemCallable <;> cases adminHasAttr <;>
    cases modelField <;> cases modelAttr <;>
    simp_all [problem_spec_validateDisplayItem, implementation_validateDisplayItem, Id.run, bind, pure]

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

**SPEC STRUCTURE:** problem_spec_validateDisplayItem is a TOTAL input->output relation pinning `result` uniquely at every one of the `2*2*3*3` = 36 observable points (itemCallable, adminHasAttr : Bool; modelField, modelAttr : Option Bool). No gaps, no contradictions => any verifying impl is behaviorally equal to the oracle. This predicts SOUND; I attempted genuine falsification with 7 distinct same-spec impls.

**SAME-SPEC:** all 7 attacks + positive control confirmed same_spec=True via swebench_unified.markers.same_spec (only impl region edited; axioms/pure/pre/post byte-identical).

### ATTACKS (cmd: `bash scripts/lean_verify.sh <f>`; project root):
- atk_1 (PREPATCH BUG, gate on modelAttr; field resolved only when modelAttr=some): exit=1, error 'unsolved goals' at proof. Reproduces the F2P bug (modelField=some, modelAttr=none wrongly rejected E108). prepatch_reproduced=true.
- atk_2 (partial-domain, always return []): exit=1, unsolved goals.
- atk_3 (boundary, swap E108<->E109): exit=1, unsolved goals.
- atk_4 (control-flow-effect, prefer modelAttr's M2M flag over modelField when both some): exit=1, unsolved goals.
- atk_5 (ungrounded-oracle echo, nested-if transliteration behaviorally identical to gold): exit=0, VERIFIES clean (only unusedSimpArgs linter warnings; no sorry/admit; correct_ theorem closed).
- atk_6 (reject callable, return E108 when itemCallable): exit=1, unsolved goals.
- atk_7 (flag-off, never emit E109): exit=1, unsolved goals.
pos_control (gold impl): exit=0, verifies.

RESOLVE (protocol step 2, for the one closing impl atk_5): atk_5 is op-for-op behaviorally identical to the gold patched control flow, so its faithful refined patch IS the gold patch. Materialized at atk_5.patch and EXECUTED run_resolve('django__django-11551', ...) => RESOLVED=True, COMPLETED=True, note='resolved'. Since the only clean-axiom verifying attack's faithful patch RESOLVES, verify does NOT diverge from correct. Per resolved echo-attack policy a resolving echo of gold is not a weakness.

**AXIOMS:** Solution.lean axioms-start/axioms-end block is empty (no axiom declarations); correct_validateDisplayItem proved by cases+simp_all with no axiom appeals. atk_5 verifies with the same clean proof discharge (no sorry, no extra axioms). #print-axioms concern moot: no user axioms in the bundle.

**REFINEMENT AUDIT:** all 7 rows are R (inputs type-refinement of the four UNCHANGED callee outcomes callable/hasattr/get_field/getattr), I (callable accept, admin-attr accept, trailing non-M2M accept), or A-reference (get_field-preferred field-resolution flow + M2M rejection + both-fail E108), validated by G-CONF conformance_check.py. NO kind-3 legs, NO consumed axioms. A-reference correspondence holds: modelField consulted before modelAttr matching patch (get_field tried first, getattr only on FieldDoesNotExist); conformance oracle is a faithful in-process replica exhaustive over all 36 points + 120000-point fuzz (SEED=20240709). axiom_check.py is a skip stub (justified: no axioms).

**VERDICT:** SOUND. 7 attacks run (>=5), 6 genuinely-distinct wrong impls all FAIL to verify (genuine 'unsolved goals' spec violations), 1 verifying impl is a behavioral echo whose faithful patch resolves. Spec is total and correctly discriminating; verify => correct holds.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) attack on django__django-11551 lean bundle. FINDING: no divergence — spec is a complete, exact characterization of the patched `_check_list_display_item`, not too strong.

### Evidence
1. Spec region byte-identical: swebench_unified.markers.same_spec(Solution, Solution_prepatch, LeanBackend.language) = True. Spec view stable.
2. Compiles clean: scripts/lean_verify.sh Solution.lean -> exit 0.
3. Genuine proof: `#print axioms correct_validateDisplayItem` = [propext, Quot.sound] — NO sorryAx, no fake proof.
4. Real repo cross-check at base_commit 859a87d873 (django/contrib/admin/checks.py:894-928). Patched flow: callable->[]; hasattr(obj)->[]; try get_field (success -> M2M?E109:[]; getattr never reached); except FieldDoesNotExist: try getattr (success -> M2M?E109:[]); except AttributeError -> E108.
5. Traced all 5 problem_spec clauses vs the real function over the entire finite observable space (itemCallable,adminHasAttr in Bool; modelField,modelAttr in {none,true,false} = 36 points):
   - Clause3 (modelField=some m): real short-circuits on successful get_field so result is independent of modelAttr = E109/[]; spec's clause 3 also omits modelAttr — MATCH.
   - Clause4 (modelField=none): matches except-FieldDoesNotExist->getattr path.
   - Clause5 (both none): matches except-AttributeError->E108.
   No input where spec disagrees with real callee.
6. conformance_check.py (oracle=faithful patched-flow replica vs shadow=impl transliteration): exhaustive 36 + 120k fuzz, seed 20240709 -> checked=120036 disagreements=0, status=pass.

**ATTACK RESULT:** could not construct a diverging input. The only unmodeled behavior is propagation of NON-standard exceptions from get_field/getattr (anything other than FieldDoesNotExist/AttributeError), which is outside the callees' return-value contract and is the accepted standard modeling boundary — not a faithfulness defect. Spec is neither too strong nor drifted. Prepatch correctly fails clause 3 (the real bug: gated field resolution on modelAttr), confirming the spec discriminates the fix. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend.language) = True; the two files' spec views are byte-identical (impl + proof regions elided), so the spec view carries no impl/proof-side leakage.

Leakage judgement is against the PUBLIC problem_statement (not hints). The problem_statement for django__django-11551 is exceptionally disclosive: it prints the ENTIRE corrected `_check_list_display_item` source verbatim (try get_field first, fall back to getattr, return E108 only when both fail, then E109 if ManyToManyField), a full 12-row truth table with an explicit 'Correct behaviour' column pinning every output, and prose stating 'there is no longer a check for hasattr(model, item)... only return an E108 in the case both of them fail. If either... successful then we need to check if it's a ManyToMany.'

Everything the spec view exposes is already fully public:
- The four observables (callable(item), hasattr(obj,item), get_field, getattr(model,item)) are named explicitly in the problem_statement.
- The get_field-preferred ordering / fallback-to-getattr control flow is printed as source in the problem_statement.
- The E108/E109 diagnostics and their exact triggering conditions are in the truth table.
- problem_spec_validateDisplayItem's five clauses are precisely the problem_statement's 'Correct behaviour' column (E108 only when both routes fail; E109 iff resolved field is M2M; else []). The docstring acceptance rule is a paraphrase of the already-published corrected function.

The spec view adds no information about the gold edit beyond the problem_statement; if anything it is strictly less explicit (abstract prose vs. the published diff-equivalent source). No line leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
