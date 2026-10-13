# P2 adversarial audit — django__django-13406

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
@@ -80,10 +80,7 @@
 def implementation_installQuery
     (rs : ResultSet) (value : StoredQuery) : ResultSet := Id.run do
   let mut rs := rs
-  -- A field-projecting query switches the row builder to field-value mappings;
-  -- a query that projects no specific fields leaves the row builder as-is.
-  if value.selectedFields ≠ [] then
-    rs := { rs with rowMode := RowMode.fieldValuesDict }
+  -- WRONG (prepatch): only store the query; never touch the row builder.
   rs := { rs with storedQuery := value }
   return rs
 -- impl-end
@@ -94,13 +91,8 @@
       problem_spec_installQuery rs value (implementation_installQuery rs value) := by
   intro rs value
   unfold problem_spec_installQuery implementation_installQuery
-  by_cases h : value.selectedFields = []
-  · simp only [Id.run, h, ne_eq, not_true_eq_false, if_false]
-    refine ⟨rfl, ?_, ?_⟩
-    · intro hne; exact hne.elim
-    · intro _; rfl
-  · simp only [Id.run, if_pos h]
-    refine ⟨rfl, ?_, ?_⟩
-    · intro _; rfl
-    · intro hempty; exact absurd hempty h
+  simp only [Id.run, bind, pure]
+  refine ⟨rfl, ?_, ?_⟩
+  · intro _; rfl
+  · intro _; rfl
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,10 +80,8 @@
 def implementation_installQuery
     (rs : ResultSet) (value : StoredQuery) : ResultSet := Id.run do
   let mut rs := rs
-  -- A field-projecting query switches the row builder to field-value mappings;
-  -- a query that projects no specific fields leaves the row builder as-is.
-  if value.selectedFields ≠ [] then
-    rs := { rs with rowMode := RowMode.fieldValuesDict }
+  -- WRONG (boundary): unconditionally switch the row builder to fieldValuesDict.
+  rs := { rs with rowMode := RowMode.fieldValuesDict }
   rs := { rs with storedQuery := value }
   return rs
 -- impl-end
@@ -94,13 +92,8 @@
       problem_spec_installQuery rs value (implementation_installQuery rs value) := by
   intro rs value
   unfold problem_spec_installQuery implementation_installQuery
-  by_cases h : value.selectedFields = []
-  · simp only [Id.run, h, ne_eq, not_true_eq_false, if_false]
-    refine ⟨rfl, ?_, ?_⟩
-    · intro hne; exact hne.elim
-    · intro _; rfl
-  · simp only [Id.run, if_pos h]
-    refine ⟨rfl, ?_, ?_⟩
-    · intro _; rfl
-    · intro hempty; exact absurd hempty h
+  simp only [Id.run, bind, pure]
+  refine ⟨rfl, ?_, ?_⟩
+  · intro _; rfl
+  · intro _; rfl
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,10 +80,9 @@
 def implementation_installQuery
     (rs : ResultSet) (value : StoredQuery) : ResultSet := Id.run do
   let mut rs := rs
-  -- A field-projecting query switches the row builder to field-value mappings;
-  -- a query that projects no specific fields leaves the row builder as-is.
+  -- WRONG (wrong constructor): switch to fieldValuesTuple, not fieldValuesDict.
   if value.selectedFields ≠ [] then
-    rs := { rs with rowMode := RowMode.fieldValuesDict }
+    rs := { rs with rowMode := RowMode.fieldValuesTuple }
   rs := { rs with storedQuery := value }
   return rs
 -- impl-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,9 +80,8 @@
 def implementation_installQuery
     (rs : ResultSet) (value : StoredQuery) : ResultSet := Id.run do
   let mut rs := rs
-  -- A field-projecting query switches the row builder to field-value mappings;
-  -- a query that projects no specific fields leaves the row builder as-is.
-  if value.selectedFields ≠ [] then
+  -- WRONG (inverted control-flow): switch when the query projects NO fields.
+  if value.selectedFields = [] then
     rs := { rs with rowMode := RowMode.fieldValuesDict }
   rs := { rs with storedQuery := value }
   return rs
@@ -95,11 +94,11 @@
   intro rs value
   unfold problem_spec_installQuery implementation_installQuery
   by_cases h : value.selectedFields = []
-  · simp only [Id.run, h, ne_eq, not_true_eq_false, if_false]
+  · simp only [Id.run, h, if_pos]
     refine ⟨rfl, ?_, ?_⟩
-    · intro hne; exact hne.elim
+    · intro hne; exact absurd h hne
     · intro _; rfl
-  · simp only [Id.run, if_pos h]
+  · simp only [Id.run, h, if_neg, not_false_iff]
     refine ⟨rfl, ?_, ?_⟩
     · intro _; rfl
     · intro hempty; exact absurd hempty h
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,11 +80,9 @@
 def implementation_installQuery
     (rs : ResultSet) (value : StoredQuery) : ResultSet := Id.run do
   let mut rs := rs
-  -- A field-projecting query switches the row builder to field-value mappings;
-  -- a query that projects no specific fields leaves the row builder as-is.
+  -- WRONG (dropped store): update rowMode but never store the installed query.
   if value.selectedFields ≠ [] then
     rs := { rs with rowMode := RowMode.fieldValuesDict }
-  rs := { rs with storedQuery := value }
   return rs
 -- impl-end
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -78,14 +78,13 @@
 
 -- impl-start
 def implementation_installQuery
-    (rs : ResultSet) (value : StoredQuery) : ResultSet := Id.run do
-  let mut rs := rs
-  -- A field-projecting query switches the row builder to field-value mappings;
-  -- a query that projects no specific fields leaves the row builder as-is.
-  if value.selectedFields ≠ [] then
-    rs := { rs with rowMode := RowMode.fieldValuesDict }
-  rs := { rs with storedQuery := value }
-  return rs
+    (rs : ResultSet) (value : StoredQuery) : ResultSet :=
+  -- ungrounded oracle echo: branch on decide (selectedFields = []) but return
+  -- modelInstances in the non-empty branch (wrong), dict in empty (wrong).
+  if value.selectedFields = [] then
+    { rowMode := rs.rowMode, storedQuery := value }
+  else
+    { rowMode := RowMode.modelInstances, storedQuery := value }
 -- impl-end
 
 -- proof-start
@@ -95,11 +94,11 @@
   intro rs value
   unfold problem_spec_installQuery implementation_installQuery
   by_cases h : value.selectedFields = []
-  · simp only [Id.run, h, ne_eq, not_true_eq_false, if_false]
+  · simp only [h, if_pos]
     refine ⟨rfl, ?_, ?_⟩
-    · intro hne; exact hne.elim
+    · intro hne; exact absurd h hne
     · intro _; rfl
-  · simp only [Id.run, if_pos h]
+  · simp only [h, if_neg, not_false_iff]
     refine ⟨rfl, ?_, ?_⟩
     · intro _; rfl
     · intro hempty; exact absurd hempty h
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -78,14 +78,12 @@
 
 -- impl-start
 def implementation_installQuery
-    (rs : ResultSet) (value : StoredQuery) : ResultSet := Id.run do
-  let mut rs := rs
-  -- A field-projecting query switches the row builder to field-value mappings;
-  -- a query that projects no specific fields leaves the row builder as-is.
-  if value.selectedFields ≠ [] then
-    rs := { rs with rowMode := RowMode.fieldValuesDict }
-  rs := { rs with storedQuery := value }
-  return rs
+    (rs : ResultSet) (value : StoredQuery) : ResultSet :=
+  -- gold-equivalent: same behavior, expressed as a direct branch.
+  if value.selectedFields = [] then
+    { rowMode := rs.rowMode, storedQuery := value }
+  else
+    { rowMode := RowMode.fieldValuesDict, storedQuery := value }
 -- impl-end
 
 -- proof-start
@@ -95,11 +93,11 @@
   intro rs value
   unfold problem_spec_installQuery implementation_installQuery
   by_cases h : value.selectedFields = []
-  · simp only [Id.run, h, ne_eq, not_true_eq_false, if_false]
+  · rw [if_pos h]
     refine ⟨rfl, ?_, ?_⟩
-    · intro hne; exact hne.elim
+    · intro hne; exact absurd h hne
     · intro _; rfl
-  · simp only [Id.run, if_pos h]
+  · rw [if_neg h]
     refine ⟨rfl, ?_, ?_⟩
     · intro _; rfl
     · intro hempty; exact absurd hempty h
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Installing a prepared query into a result set, and keeping the row-building
strategy consistent with what the query projects.

A result set carries two pieces of state: the prepared query it will run, and the
strategy used to turn each raw database row into a Python-level result value. Some
queries project a specific set of named fields (so each row is naturally a mapping
from field name to value); others project no specific fields (so each row is a
full model instance).

When a prepared query is installed into a result set, the stored query is replaced
by exactly that query. In addition, if the installed query projects a specific set
of fields, the row-building strategy is set to the one that yields field-value
mappings — so that a result set fed a field-projecting query produces field-value
mappings rather than model instances. If the installed query projects no specific
fields, the existing row-building strategy is left untouched.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom and none is deep-modeled.
-- Installing a query reads one thing off the query — the set of fields it
-- projects — and performs two state updates (store the query; possibly switch the
-- row-building strategy). The available row-building strategies are modeled
-- directly as the constructors of `RowMode` (sentinel choices that are selected,
-- never invoked), so the bundle needs no `opaque`/`axiom` callee contract.
-- axioms-end

-- pure-start
/-- The row-building strategy a result set uses to turn each raw row into a
result value. The distinguished value here is `fieldValuesDict` (each row becomes
a mapping from projected field name to value); `modelInstances` builds a full
model instance per row; the remaining three are alternative field-projecting
strategies (tuple / single-value / named-tuple per row). -/
inductive RowMode where
  | modelInstances
  | fieldValuesDict
  | fieldValuesTuple
  | fieldValuesFlat
  | fieldValuesNamed
deriving DecidableEq, Repr

/-- A prepared query, observed only by the list of field names it projects
(empty ⇔ it projects no specific fields). -/
structure StoredQuery where
  selectedFields : List String
deriving DecidableEq, Repr

/-- A result set: the row-building strategy plus the prepared query it will run. -/
structure ResultSet where
  rowMode : RowMode
  storedQuery : StoredQuery
deriving Repr
-- pure-end

-- post-conditions-start
/-- Installing `value` into `rs` is fully pinned to the inputs:

  * the stored query of the result is exactly the installed `value`
    (directive-5 frame: the query component always equals its input);
  * if `value` projects a specific set of fields (`selectedFields ≠ []`) the
    row-building strategy of the result is the field-value-mapping strategy
    (`fieldValuesDict`), regardless of the prior strategy;
  * if `value` projects no specific fields (`selectedFields = []`) the
    row-building strategy is left equal to its prior value `rs.rowMode`
    (directive-5 frame: the unchanged branch pins the component to its input).

Both output components are pinned in every case, so no incorrect installer can
fill a free hole. -/
def problem_spec_installQuery
    (rs : ResultSet) (value : StoredQuery) (result : ResultSet) : Prop :=
  result.storedQuery = value ∧
  (value.selectedFields ≠ [] → result.rowMode = RowMode.fieldValuesDict) ∧
  (value.selectedFields = [] → result.rowMode = rs.rowMode)
-- post-conditions-end

-- impl-start
def implementation_installQuery
    (rs : ResultSet) (value : StoredQuery) : ResultSet := Id.run do
  let mut rs := rs
  -- A field-projecting query switches the row builder to field-value mappings;
  -- a query that projects no specific fields leaves the row builder as-is.
  if value.selectedFields ≠ [] then
    rs := { rs with rowMode := RowMode.fieldValuesDict }
  rs := { rs with storedQuery := value }
  return rs
-- impl-end

-- proof-start
theorem correct_installQuery :
    ∀ (rs : ResultSet) (value : StoredQuery),
      problem_spec_installQuery rs value (implementation_installQuery rs value) := by
  intro rs value
  unfold problem_spec_installQuery implementation_installQuery
  by_cases h : value.selectedFields = []
  · simp only [Id.run, h, ne_eq, not_true_eq_false, if_false]
    refine ⟨rfl, ?_, ?_⟩
    · intro hne; exact hne.elim
    · intro _; rfl
  · simp only [Id.run, if_pos h]
    refine ⟨rfl, ?_, ?_⟩
    · intro _; rfl
    · intro hempty; exact absurd hempty h
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec fully pins BOTH output components as total functions of inputs: (1) result.storedQuery = value (unconditional); (2) selectedFields != [] -> rowMode = fieldValuesDict; (3) selectedFields = [] -> rowMode = rs.rowMode (frame clause). No A-legs exist: meta.json axioms=[] deep_model_references=[]; refinement.md legs all R/I (leg1 I, leg2 R, leg3 R/I, leg4 I; no kind-3). The real patched QuerySet.query setter calls nothing (reads value.values_select, does two assignments); the 5 iterable classes are assigned-never-invoked sentinels correctly modeled as RowMode constructors -> no axiom slack. axiom_check.py is a legitimate skip stub.

### ATTACKS (all same_spec=True, verified via swebench_unified.markers.same_spec):
- atk_1 PREPATCH bug (store query only, never touch rowMode): lean_verify EXIT=1. Fails for CORRECT reason: residual goal `rs.rowMode = RowMode.fieldValuesDict` for arbitrary rs is unprovable. Prepatch bug reproduced & discriminated.
- atk_2 boundary (unconditionally set fieldValuesDict): EXIT=1. Residual goal `fieldValuesDict = rs.rowMode` unprovable (empty-branch frame clause).
- atk_3 wrong constructor (fieldValuesTuple instead of Dict): EXIT=1. Residual goal `fieldValuesTuple = fieldValuesDict` unprovable.
- atk_4 inverted control-flow (switch when selectedFields = []): EXIT=1. Proof cannot close.
- atk_5 dropped store (update rowMode but never store value): EXIT=1. Proof cannot close.
- atk_6 ungrounded oracle echo (modelInstances on non-empty branch): EXIT=1. Residual goal `modelInstances = fieldValuesDict` unprovable.
- atk_7 GOLD-EQUIVALENT echo (direct branch, same behavior): lean_verify EXIT=0, `#print axioms correct_installQuery` => 'does not depend on any axioms' (CLEAN). Its faithful transliterated patch was materialized and RUN through run_resolve('django__django-13406'): resolved=True, completed=True, note='resolved'. So the only closing-clean-axiom impl RESOLVES -> not a weakness (G-EQ/G-PANEL-1 resolve policy).

POSITIVE CONTROL pos_control.lean (gold verbatim): lean_verify EXIT=0, #print axioms => [propext] (clean). Gold patch run through run_resolve: resolved=True, completed=True. Harness confirmed live and correct.

Every behavior-divergent wrong impl (atk_1..6) fails to close because the spec Prop is literally false for it on some input (residual false equations shown in each .out). No impl with a closing clean-axiom proof has a non-resolving faithful patch. Per protocol step 2, there were ZERO mandatory resolve runs on wrong impls (none closed); the two resolve runs executed (gold + atk_7 echo) both resolved, confirming verify does NOT diverge from correct. Commands: `bash scripts/lean_verify.sh <file>` for each; `run_resolve(instance_id, patch, timeout=1800, retries=1)` for gold (run_id sbu-audit-v4nz-gold2) and atk_7 (run_id sbu-audit-v4nz-atk7b). Docker via `docker` confirmed working.

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
Installing a prepared query into a result set, and keeping the row-building
strategy consistent with what the query projects.

A result set carries two pieces of state: the prepared query it will run, and the
strategy used to turn each raw database row into a Python-level result value. Some
queries project a specific set of named fields (so each row is naturally a mapping
from field name to value); others project no specific fields (so each row is a
full model instance).

When a prepared query is installed into a result set, the stored query is replaced
by exactly that query. In addition, if the installed query projects a specific set
of fields, the row-building strategy is set to the one that yields field-value
mappings — so that a result set fed a field-projecting query produces field-value
mappings rather than model instances. If the installed query projects no specific
fields, the existing row-building strategy is left untouched.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom and none is deep-modeled.
-- Installing a query reads one thing off the query — the set of fields it
-- projects — and performs two state updates (store the query; possibly switch the
-- row-building strategy). The available row-building strategies are modeled
-- directly as the constructors of `RowMode` (sentinel choices that are selected,
-- never invoked), so the bundle needs no `opaque`/`axiom` callee contract.
-- axioms-end

-- pure-start
/-- The row-building strategy a result set uses to turn each raw row into a
result value. The distinguished value here is `fieldValuesDict` (each row becomes
a mapping from projected field name to value); `modelInstances` builds a full
model instance per row; the remaining three are alternative field-projecting
strategies (tuple / single-value / named-tuple per row). -/
inductive RowMode where
  | modelInstances
  | fieldValuesDict
  | fieldValuesTuple
  | fieldValuesFlat
  | fieldValuesNamed
deriving DecidableEq, Repr

/-- A prepared query, observed only by the list of field names it projects
(empty ⇔ it projects no specific fields). -/
structure StoredQuery where
  selectedFields : List String
deriving DecidableEq, Repr

/-- A result set: the row-building strategy plus the prepared query it will run. -/
structure ResultSet where
  rowMode : RowMode
  storedQuery : StoredQuery
deriving Repr
-- pure-end

-- post-conditions-start
/-- Installing `value` into `rs` is fully pinned to the inputs:

  * the stored query of the result is exactly the installed `value`
    (directive-5 frame: the query component always equals its input);
  * if `value` projects a specific set of fields (`selectedFields ≠ []`) the
    row-building strategy of the result is the field-value-mapping strategy
    (`fieldValuesDict`), regardless of the prior strategy;
  * if `value` projects no specific fields (`selectedFields = []`) the
    row-building strategy is left equal to its prior value `rs.rowMode`
    (directive-5 frame: the unchanged branch pins the component to its input).

Both output components are pinned in every case, so no incorrect installer can
fill a free hole. -/
def problem_spec_installQuery
    (rs : ResultSet) (value : StoredQuery) (result : ResultSet) : Prop :=
  result.storedQuery = value ∧
  (value.selectedFields ≠ [] → result.rowMode = RowMode.fieldValuesDict) ∧
  (value.selectedFields = [] → result.rowMode = rs.rowMode)
-- post-conditions-end

-- impl-start
def implementation_installQuery
    (rs : ResultSet) (value : StoredQuery) : ResultSet := Id.run do
  let mut rs := rs
  -- A field-projecting query switches the row builder to field-value mappings;
  -- a query that projects no specific fields leaves the row builder as-is.
  if value.selectedFields ≠ [] then
    rs := { rs with rowMode := RowMode.fieldValuesDict }
  rs := { rs with storedQuery := value }
  return rs
-- impl-end

-- proof-start
theorem correct_installQuery :
    ∀ (rs : ResultSet) (value : StoredQuery),
      problem_spec_installQuery rs value (implementation_installQuery rs value) := by
  intro rs value
  unfold problem_spec_installQuery implementation_installQuery
  by_cases h : value.selectedFields = []
  · simp only [Id.run, h, ne_eq, not_true_eq_false, if_false]
    refine ⟨rfl, ?_, ?_⟩
    · intro hne; exact hne.elim
    · intro _; rfl
  · simp only [Id.run, if_pos h]
    refine ⟨rfl, ?_, ?_⟩
    · intro _; rfl
    · intro hempty; exact absurd hempty h
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec fully pins BOTH output components as total functions of inputs: (1) result.storedQuery = value (unconditional); (2) selectedFields != [] -> rowMode = fieldValuesDict; (3) selectedFields = [] -> rowMode = rs.rowMode (frame clause). No A-legs exist: meta.json axioms=[] deep_model_references=[]; refinement.md legs all R/I (leg1 I, leg2 R, leg3 R/I, leg4 I; no kind-3). The real patched QuerySet.query setter calls nothing (reads value.values_select, does two assignments); the 5 iterable classes are assigned-never-invoked sentinels correctly modeled as RowMode constructors -> no axiom slack. axiom_check.py is a legitimate skip stub.

### ATTACKS (all same_spec=True, verified via swebench_unified.markers.same_spec):
- atk_1 PREPATCH bug (store query only, never touch rowMode): lean_verify EXIT=1. Fails for CORRECT reason: residual goal `rs.rowMode = RowMode.fieldValuesDict` for arbitrary rs is unprovable. Prepatch bug reproduced & discriminated.
- atk_2 boundary (unconditionally set fieldValuesDict): EXIT=1. Residual goal `fieldValuesDict = rs.rowMode` unprovable (empty-branch frame clause).
- atk_3 wrong constructor (fieldValuesTuple instead of Dict): EXIT=1. Residual goal `fieldValuesTuple = fieldValuesDict` unprovable.
- atk_4 inverted control-flow (switch when selectedFields = []): EXIT=1. Proof cannot close.
- atk_5 dropped store (update rowMode but never store value): EXIT=1. Proof cannot close.
- atk_6 ungrounded oracle echo (modelInstances on non-empty branch): EXIT=1. Residual goal `modelInstances = fieldValuesDict` unprovable.
- atk_7 GOLD-EQUIVALENT echo (direct branch, same behavior): lean_verify EXIT=0, `#print axioms correct_installQuery` => 'does not depend on any axioms' (CLEAN). Its faithful transliterated patch was materialized and RUN through run_resolve('django__django-13406'): resolved=True, completed=True, note='resolved'. So the only closing-clean-axiom impl RESOLVES -> not a weakness (G-EQ/G-PANEL-1 resolve policy).

POSITIVE CONTROL pos_control.lean (gold verbatim): lean_verify EXIT=0, #print axioms => [propext] (clean). Gold patch run through run_resolve: resolved=True, completed=True. Harness confirmed live and correct.

Every behavior-divergent wrong impl (atk_1..6) fails to close because the spec Prop is literally false for it on some input (residual false equations shown in each .out). No impl with a closing clean-axiom proof has a non-resolving faithful patch. Per protocol step 2, there were ZERO mandatory resolve runs on wrong impls (none closed); the two resolve runs executed (gold + atk_7 echo) both resolved, confirming verify does NOT diverge from correct. Commands: `bash scripts/lean_verify.sh <file>` for each; `run_resolve(instance_id, patch, timeout=1800, retries=1)` for gold (run_id sbu-audit-v4nz-gold2) and atk_7 (run_id sbu-audit-v4nz-atk7b). Docker via `docker` confirmed working.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical to prepatch (same_spec=True with lean tables). Solution.lean compiles (exit 0, no sorry); #print axioms correct_installQuery = [propext] only, no sorryAx — proof is real. Modeled implementation_installQuery faithfully reproduces the real QuerySet.query setter's observable state (_iterable_class, _query) ↔ (rowMode, storedQuery). Gold patch (verbatim): `if value.values_select: self._iterable_class = ValuesIterable; self._query = value`. Case analysis over the full input space (selectedFields empty/non-empty × 5 initial rowModes): (1) storedQuery=value always matches self._query=value; (2) non-empty selectedFields → rowMode=fieldValuesDict matches unconditional _iterable_class=ValuesIterable overwrite (confirmed by test_annotation_values_list collapsing tuple/flat/named→values regardless of prior class); (3) empty selectedFields → rowMode=rs.rowMode matches leaving _iterable_class untouched. The abstraction selectedFields≠[] ↔ values_select tuple truthiness is exact (values_select is a tuple; only its emptiness is read). No diverging input exists. Spec is not too strong (gold impl satisfies it and resolves) and does not drift from repo behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical leakage.screen passes clean (no diff markers, no patched path/module, no patched-symbol echo, no narration). same_spec(Solution, Solution_prepatch)=True — spec region byte-identical and unchanged by the fix. Spec view uses only invented abstractions (RowMode/ResultSet/StoredQuery/installQuery/fieldValuesDict/selectedFields); none echo the patched setter `query` or `_iterable_class`/`ValuesIterable`/`values_select`. The post-condition (field-projecting query => field-value-mapping row builder; empty => frame/unchanged) is derivable from the PUBLIC problem_statement, which already states values()/values_list() queries must yield dicts rather than model instances. The mechanistic detail (which attribute, which class, which setter) appears only in hints_text, which is out of scope and is NOT reflected in the spec view. No reconstruction of the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
