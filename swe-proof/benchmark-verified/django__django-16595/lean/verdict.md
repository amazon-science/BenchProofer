# P2 adversarial audit — django__django-16595

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -126,16 +126,12 @@
 
 -- impl-start
 def implementation_reduceAlter (self op : Op) : List Op := Id.run do
-  if (op.kind == OpKind.alterField || op.kind == OpKind.removeField) && sameField self op then
+  if op.kind == OpKind.removeField && sameField self op then
     return [op]
   if op.kind == OpKind.renameField && sameField self op && self.field.dbColumn.isNone then
     return [op,
-      { kind := OpKind.alterField,
-        modelName := self.modelName,
-        name := op.newName,
-        newName := "",
-        elidable := false,
-        field := self.field }]
+      { kind := OpKind.alterField, modelName := self.modelName, name := op.newName,
+        newName := "", elidable := false, field := self.field }]
   if self.elidable then
     return [op]
   if op.elidable then
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -130,17 +130,13 @@
     return [op]
   if op.kind == OpKind.renameField && sameField self op && self.field.dbColumn.isNone then
     return [op,
-      { kind := OpKind.alterField,
-        modelName := self.modelName,
-        name := op.newName,
-        newName := "",
-        elidable := false,
-        field := self.field }]
+      { kind := OpKind.alterField, modelName := self.modelName, name := op.newName,
+        newName := "", elidable := false, field := self.field }]
   if self.elidable then
     return [op]
   if op.elidable then
     return [self]
-  return []
+  return [op]
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -128,14 +128,10 @@
 def implementation_reduceAlter (self op : Op) : List Op := Id.run do
   if (op.kind == OpKind.alterField || op.kind == OpKind.removeField) && sameField self op then
     return [op]
-  if op.kind == OpKind.renameField && sameField self op && self.field.dbColumn.isNone then
+  if op.kind == OpKind.renameField && sameField self op then
     return [op,
-      { kind := OpKind.alterField,
-        modelName := self.modelName,
-        name := op.newName,
-        newName := "",
-        elidable := false,
-        field := self.field }]
+      { kind := OpKind.alterField, modelName := self.modelName, name := op.newName,
+        newName := "", elidable := false, field := self.field }]
   if self.elidable then
     return [op]
   if op.elidable then
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -126,20 +126,16 @@
 
 -- impl-start
 def implementation_reduceAlter (self op : Op) : List Op := Id.run do
+  if self.elidable then
+    return [op]
+  if op.elidable then
+    return [self]
   if (op.kind == OpKind.alterField || op.kind == OpKind.removeField) && sameField self op then
     return [op]
   if op.kind == OpKind.renameField && sameField self op && self.field.dbColumn.isNone then
     return [op,
-      { kind := OpKind.alterField,
-        modelName := self.modelName,
-        name := op.newName,
-        newName := "",
-        elidable := false,
-        field := self.field }]
-  if self.elidable then
-    return [op]
-  if op.elidable then
-    return [self]
+      { kind := OpKind.alterField, modelName := self.modelName, name := op.newName,
+        newName := "", elidable := false, field := self.field }]
   return []
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -126,21 +126,7 @@
 
 -- impl-start
 def implementation_reduceAlter (self op : Op) : List Op := Id.run do
-  if (op.kind == OpKind.alterField || op.kind == OpKind.removeField) && sameField self op then
-    return [op]
-  if op.kind == OpKind.renameField && sameField self op && self.field.dbColumn.isNone then
-    return [op,
-      { kind := OpKind.alterField,
-        modelName := self.modelName,
-        name := op.newName,
-        newName := "",
-        elidable := false,
-        field := self.field }]
-  if self.elidable then
-    return [op]
-  if op.elidable then
-    return [self]
-  return []
+  return [op]
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -130,12 +130,8 @@
     return [op]
   if op.kind == OpKind.renameField && sameField self op && self.field.dbColumn.isNone then
     return [op,
-      { kind := OpKind.alterField,
-        modelName := self.modelName,
-        name := op.newName,
-        newName := "",
-        elidable := false,
-        field := self.field }]
+      { kind := OpKind.alterField, modelName := self.modelName, name := op.newName,
+        newName := "", elidable := true, field := self.field }]
   if self.elidable then
     return [op]
   if op.elidable then
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -130,16 +130,12 @@
     return [op]
   if op.kind == OpKind.renameField && sameField self op && self.field.dbColumn.isNone then
     return [op,
-      { kind := OpKind.alterField,
-        modelName := self.modelName,
-        name := op.newName,
-        newName := "",
-        elidable := false,
-        field := self.field }]
+      { kind := OpKind.alterField, modelName := self.modelName, name := op.newName,
+        newName := "", elidable := false, field := self.field }]
   if self.elidable then
+    return [self]
+  if op.elidable then
     return [op]
-  if op.elidable then
-    return [self]
   return []
 -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Reducing an alter-field migration step against the step that immediately
follows it during migration optimization.

A migration is optimized by repeatedly looking at one step together with the
step that immediately follows it and, where possible, fusing the pair into a
shorter sequence. The step considered here alters one field of one model — it
is identified by a model name, a field name, and the new field definition it
carries.

Two field steps act on the *same field* when they name the same model and the
same field, compared case-insensitively. When the following step acts on the
same field, the alter step can be reconciled with it:

  * If the following step either alters that same field again, or removes it,
    then the alter step is subsumed: the pair collapses to just the following
    step (a later alter or a removal makes the earlier alter redundant).
  * If the following step renames that same field — and the altered field
    pins no explicit database column name — then the rename is floated to the
    front and the alter step is re-expressed against the field's new name: the
    pair becomes the rename followed by an alter step that carries the original
    field definition under the new name.
  * In every other case this reconciliation itself produces no fusion, and the
    outcome falls to the generic pairing rule for *elidable* steps (a step may
    be marked elidable, meaning it can be dropped entirely when the sequence is
    squashed): if the alter step is marked elidable it is dropped and the pair
    collapses to just the following step; otherwise, if the following step is
    marked elidable it is dropped and the pair collapses to just the alter
    step; and when neither is marked elidable no replacement sequence is
    produced.

These cases are exhaustive and mutually exclusive, so the result is fully
determined for every pairing.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The reduction
-- performs only a runtime kind test of the following step, a
-- case-insensitive model+field name comparison, an "explicit column name absent"
-- test, a read of each step's elidable flag, and the construction of
-- replacement steps that copy carried-over components. All are modeled directly
-- (`String.toLower`, an `Option` check, `Bool` fields, and record literals), so
-- no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- The runtime kind of a field step, as far as the reduction distinguishes:
an alter-field step, a remove-field step, a rename-field step, or any other
step. -/
inductive OpKind where
  | alterField
  | removeField
  | renameField
  | otherOp
deriving DecidableEq, Repr

/-- The field definition an alter/add step carries, observed through the only
component the reduction inspects (whether an explicit database column name is
pinned) plus an opaque token standing for the rest, which is only ever copied. -/
structure FieldInfo where
  /-- the explicit database column name, if one is pinned (`none` when absent) -/
  dbColumn : Option String
  /-- opaque stand-in for the remainder of the field definition (copied verbatim) -/
  repr : String
deriving DecidableEq, Repr

/-- A field step, observed through the components the reduction reads or
rewrites: its kind, the model and field it names, the new name it introduces
(meaningful only for a rename), whether it is marked elidable (droppable when
the sequence is squashed), and the field definition it carries. -/
structure Op where
  kind : OpKind
  modelName : String
  name : String
  newName : String
  elidable : Bool
  field : FieldInfo
deriving DecidableEq, Repr

/-- Two field steps act on the same field when they name the same model and
the same field, compared case-insensitively. -/
def sameField (a b : Op) : Bool :=
  a.modelName.toLower == b.modelName.toLower && a.name.toLower == b.name.toLower
-- pure-end

-- post-conditions-start
/-- The outcome of pairing an alter-field step `self` with the step `op` that
immediately follows it:

  * when `op` alters or removes the same field, the pair collapses into exactly
    the following step (`[op]`);
  * when `op` renames the same field and `self` pins no explicit database column
    name, the rename is floated to the front and the alter step is re-expressed
    against the new name, carrying `self`'s original field definition unchanged
    (directive 5 frame: model name and field carried over verbatim); the
    re-expressed alter step is a freshly constructed step, not marked elidable;
  * otherwise the outcome falls to the generic elidable pairing rule: if `self`
    is marked elidable the pair collapses to just the following step (`[op]`);
    failing that, if `op` is marked elidable the pair collapses to just the
    alter step (`[self]`); and when neither is marked elidable no fused
    replacement sequence is produced (the empty result).

The cases are exhaustive and mutually exclusive, so the result is fully
determined for every input. -/
def problem_spec_reduceAlter (self op : Op) (result : List Op) : Prop :=
  ((op.kind = OpKind.alterField ∨ op.kind = OpKind.removeField) ∧ sameField self op = true →
      result = [op]) ∧
  ((op.kind = OpKind.renameField ∧ sameField self op = true ∧ self.field.dbColumn = none) →
      result =
        [op,
         { kind := OpKind.alterField,
           modelName := self.modelName,
           name := op.newName,
           newName := "",
           elidable := false,
           field := self.field }]) ∧
  (¬((op.kind = OpKind.alterField ∨ op.kind = OpKind.removeField) ∧ sameField self op = true) ∧
   ¬(op.kind = OpKind.renameField ∧ sameField self op = true ∧ self.field.dbColumn = none) →
      (self.elidable = true → result = [op]) ∧
      (self.elidable = false ∧ op.elidable = true → result = [self]) ∧
      (self.elidable = false ∧ op.elidable = false → result = []))
-- post-conditions-end

-- impl-start
def implementation_reduceAlter (self op : Op) : List Op := Id.run do
  if (op.kind == OpKind.alterField || op.kind == OpKind.removeField) && sameField self op then
    return [op]
  if op.kind == OpKind.renameField && sameField self op && self.field.dbColumn.isNone then
    return [op,
      { kind := OpKind.alterField,
        modelName := self.modelName,
        name := op.newName,
        newName := "",
        elidable := false,
        field := self.field }]
  if self.elidable then
    return [op]
  if op.elidable then
    return [self]
  return []
-- impl-end

-- proof-start
theorem correct_reduceAlter :
    ∀ (self op : Op),
      problem_spec_reduceAlter self op (implementation_reduceAlter self op) := by
  intro self op
  unfold problem_spec_reduceAlter implementation_reduceAlter
  simp only [Id.run]
  refine ⟨?_, ?_, ?_⟩
  · rintro ⟨hk, hs⟩
    have hb : (op.kind == OpKind.alterField || op.kind == OpKind.removeField) = true := by
      rcases hk with h | h <;> simp [h]
    simp [hb, hs]
    rfl
  · rintro ⟨hk, hs, hc⟩
    have h1 : (op.kind == OpKind.alterField || op.kind == OpKind.removeField) = false := by
      simp [hk]
    have h2 : (op.kind == OpKind.renameField) = true := by simp [hk]
    have h3 : self.field.dbColumn.isNone = true := by simp [hc]
    simp [h1, h2, h3, hs]
    rfl
  · rintro ⟨h1, h2⟩
    have hne1 : ((op.kind == OpKind.alterField || op.kind == OpKind.removeField)
        && sameField self op) = false := by
      by_contra hc
      simp only [Bool.not_eq_false, Bool.and_eq_true, Bool.or_eq_true, beq_iff_eq] at hc
      exact h1 ⟨hc.1, hc.2⟩
    have hne2 : (op.kind == OpKind.renameField && sameField self op
        && self.field.dbColumn.isNone) = false := by
      by_contra hc
      simp only [Bool.not_eq_false, Bool.and_eq_true, beq_iff_eq,
        Option.isNone_iff_eq_none] at hc
      exact h2 ⟨hc.1.1, hc.1.2, hc.2⟩
    refine ⟨?_, ?_, ?_⟩
    · intro hse
      simp [hne1, hne2, hse]
      rfl
    · rintro ⟨hse, hoe⟩
      simp [hne1, hne2, hse, hoe]
      rfl
    · rintro ⟨hse, hoe⟩
      simp [hne1, hne2, hse, hoe]
      rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit for django__django-16595 (lean).

SPEC ANALYSIS: problem_spec_reduceAlter is a conjunction of three implications whose guards PARTITION the entire (self,op) input space: C1 = (op alter OR remove) AND sameField -> result=[op]; C2 = (op rename AND sameField AND dbColumn=none) -> result=[op, freshly-built AlterField]; C3 = (NOT C1-guard AND NOT C2-guard) -> full Bool x Bool elidable sub-rules ([op] when self.elidable; [self] when only op.elidable; [] when neither). C1 disjoint from C2 by op.kind; C3 is the exact complement of C1-guard OR C2-guard; each region pins result to one concrete value. Therefore the spec is functionally TOTAL and DETERMINISTIC: any behaviorally-divergent impl leaves some conjunct's goal as an unprovable equality between distinct concrete values, so NO wrong impl can close correct_reduceAlter. => No same-spec wrong impl verifies => there is no faithful patch to resolve => verify=>correct holds. No BROKEN case possible.

SAME-SPEC: all 7 attacks + positive control return same_spec==True (swebench_unified.markers.same_spec, lean). Only the impl region was edited; axioms/pure/pre/post byte-identical.

POSITIVE CONTROL (pos.lean = exact gold impl): bash scripts/lean_verify.sh <pos.lean> -> exit 0. #print axioms correct_reduceAlter -> 'depends on axioms: [propext, Quot.sound]' (clean; no sorryAx / Classical.choice).

### ATTACKS (cmd: bash scripts/lean_verify.sh <atk_N.lean>; all run concurrently as background jobs, <=4 at a time):
- atk_1 (PREPATCH BUG: first guard tests only op.kind==removeField, dropping the widened alterField collapse; impl region byte-identical to Solution_prepatch.lean) -> exit 1. Genuine goal error: rfl failed on the C1 alterField branch ([op] vs fall-through []). PREPATCH REPRODUCED.
- atk_2 (PARTIAL-DOMAIN: correct except otherOp/neither-elidable returns [op] instead of []) -> exit 1. rfl failed on C3 neither-elidable goal ([op]=[]).
- atk_3 (BOUNDARY: rename arm drops the self.field.dbColumn.isNone guard, fires even when a column is pinned) -> exit 1. rfl failed on C3 fall-through goals.
- atk_4 (CONTROL-FLOW-EFFECT: elidable checks reordered before the collapse/rename arms) -> exit 1. rfl failed on C1/C2 goals.
- atk_5 (UNGROUNDED-ORACLE ECHO: always return [op]) -> exit 1. simp made no progress on C2/C3 goals ([op] != pair / []).
- atk_6 (SUBTLE BOUNDARY: rename arm builds the re-expressed AlterField with elidable:=true instead of false) -> exit 1. rfl failed on C2 pair-equality goal.
- atk_7 (SUBTLE: swap elidable fall-through outputs -> [self] when self.elidable, [op] when op.elidable) -> exit 1. rfl failed on C3 goals.
Every failure is a genuine goal-level equality error (rfl/simp on the exact spec conjunct), not a syntax/import artifact.

Because 0 of 7 wrong impls closed with clean axioms, NO faithful refined patch needed to be materialized or run through run_resolve (protocol step 2 triggers only for a verifying wrong impl). patches={} accordingly.

A-LEG / AXIOM AUDIT: Solution.lean declares NO axiom/opaque (axioms-start..axioms-end region is comment-only; grep for ^\s*(axiom|opaque) => no matches). axiom_check.py is a legitimate SKIP STUB (prints status=skip, exit 0) — nothing to validate because the modeled callee AlterField.reduce is modeled DEEPLY (OpKind tag, String.toLower equality, Option check, Bool fields, record literals). refinement.md: all 8 legs are R or I (rows 2,3,4,5,6 = I deeply-modeled; rows 1,7,8 = R type refinement); NO A-consumed / A-reference / kind-3 legs exist. mapping.md confirms axioms=[], deep_model_references=[]. The A-leg attack surface is therefore empty/vacuous by construction; the R/I legs correspond faithfully to the post-patch reduce arms (verified against patch.diff + instance.json: patch widens isinstance(operation, RemoveField) to (AlterField, RemoveField), exactly matching the Lean guard's added op.kind==alterField disjunct).

VERDICT: SOUND. Spec is total+deterministic; >=7 distinct same-spec wrong impls (prepatch bug + partial-domain + 2 boundary + control-flow-effect + ungrounded-oracle echo + fall-through swap) all fail to close with genuine goal errors; positive control closes with clean axioms; no A-legs to break. verify=>correct upheld.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Reducing an alter-field migration step against the step that immediately
follows it during migration optimization.

A migration is optimized by repeatedly looking at one step together with the
step that immediately follows it and, where possible, fusing the pair into a
shorter sequence. The step considered here alters one field of one model — it
is identified by a model name, a field name, and the new field definition it
carries.

Two field steps act on the *same field* when they name the same model and the
same field, compared case-insensitively. When the following step acts on the
same field, the alter step can be reconciled with it:

  * If the following step either alters that same field again, or removes it,
    then the alter step is subsumed: the pair collapses to just the following
    step (a later alter or a removal makes the earlier alter redundant).
  * If the following step renames that same field — and the altered field
    pins no explicit database column name — then the rename is floated to the
    front and the alter step is re-expressed against the field's new name: the
    pair becomes the rename followed by an alter step that carries the original
    field definition under the new name.
  * In every other case this reconciliation itself produces no fusion, and the
    outcome falls to the generic pairing rule for *elidable* steps (a step may
    be marked elidable, meaning it can be dropped entirely when the sequence is
    squashed): if the alter step is marked elidable it is dropped and the pair
    collapses to just the following step; otherwise, if the following step is
    marked elidable it is dropped and the pair collapses to just the alter
    step; and when neither is marked elidable no replacement sequence is
    produced.

These cases are exhaustive and mutually exclusive, so the result is fully
determined for every pairing.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The reduction
-- performs only a runtime kind test of the following step, a
-- case-insensitive model+field name comparison, an "explicit column name absent"
-- test, a read of each step's elidable flag, and the construction of
-- replacement steps that copy carried-over components. All are modeled directly
-- (`String.toLower`, an `Option` check, `Bool` fields, and record literals), so
-- no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- The runtime kind of a field step, as far as the reduction distinguishes:
an alter-field step, a remove-field step, a rename-field step, or any other
step. -/
inductive OpKind where
  | alterField
  | removeField
  | renameField
  | otherOp
deriving DecidableEq, Repr

/-- The field definition an alter/add step carries, observed through the only
component the reduction inspects (whether an explicit database column name is
pinned) plus an opaque token standing for the rest, which is only ever copied. -/
structure FieldInfo where
  /-- the explicit database column name, if one is pinned (`none` when absent) -/
  dbColumn : Option String
  /-- opaque stand-in for the remainder of the field definition (copied verbatim) -/
  repr : String
deriving DecidableEq, Repr

/-- A field step, observed through the components the reduction reads or
rewrites: its kind, the model and field it names, the new name it introduces
(meaningful only for a rename), whether it is marked elidable (droppable when
the sequence is squashed), and the field definition it carries. -/
structure Op where
  kind : OpKind
  modelName : String
  name : String
  newName : String
  elidable : Bool
  field : FieldInfo
deriving DecidableEq, Repr

/-- Two field steps act on the same field when they name the same model and
the same field, compared case-insensitively. -/
def sameField (a b : Op) : Bool :=
  a.modelName.toLower == b.modelName.toLower && a.name.toLower == b.name.toLower
-- pure-end

-- post-conditions-start
/-- The outcome of pairing an alter-field step `self` with the step `op` that
immediately follows it:

  * when `op` alters or removes the same field, the pair collapses into exactly
    the following step (`[op]`);
  * when `op` renames the same field and `self` pins no explicit database column
    name, the rename is floated to the front and the alter step is re-expressed
    against the new name, carrying `self`'s original field definition unchanged
    (directive 5 frame: model name and field carried over verbatim); the
    re-expressed alter step is a freshly constructed step, not marked elidable;
  * otherwise the outcome falls to the generic elidable pairing rule: if `self`
    is marked elidable the pair collapses to just the following step (`[op]`);
    failing that, if `op` is marked elidable the pair collapses to just the
    alter step (`[self]`); and when neither is marked elidable no fused
    replacement sequence is produced (the empty result).

The cases are exhaustive and mutually exclusive, so the result is fully
determined for every input. -/
def problem_spec_reduceAlter (self op : Op) (result : List Op) : Prop :=
  ((op.kind = OpKind.alterField ∨ op.kind = OpKind.removeField) ∧ sameField self op = true →
      result = [op]) ∧
  ((op.kind = OpKind.renameField ∧ sameField self op = true ∧ self.field.dbColumn = none) →
      result =
        [op,
         { kind := OpKind.alterField,
           modelName := self.modelName,
           name := op.newName,
           newName := "",
           elidable := false,
           field := self.field }]) ∧
  (¬((op.kind = OpKind.alterField ∨ op.kind = OpKind.removeField) ∧ sameField self op = true) ∧
   ¬(op.kind = OpKind.renameField ∧ sameField self op = true ∧ self.field.dbColumn = none) →
      (self.elidable = true → result = [op]) ∧
      (self.elidable = false ∧ op.elidable = true → result = [self]) ∧
      (self.elidable = false ∧ op.elidable = false → result = []))
-- post-conditions-end

-- impl-start
def implementation_reduceAlter (self op : Op) : List Op := Id.run do
  if (op.kind == OpKind.alterField || op.kind == OpKind.removeField) && sameField self op then
    return [op]
  if op.kind == OpKind.renameField && sameField self op && self.field.dbColumn.isNone then
    return [op,
      { kind := OpKind.alterField,
        modelName := self.modelName,
        name := op.newName,
        newName := "",
        elidable := false,
        field := self.field }]
  if self.elidable then
    return [op]
  if op.elidable then
    return [self]
  return []
-- impl-end

-- proof-start
theorem correct_reduceAlter :
    ∀ (self op : Op),
      problem_spec_reduceAlter self op (implementation_reduceAlter self op) := by
  intro self op
  unfold problem_spec_reduceAlter implementation_reduceAlter
  simp only [Id.run]
  refine ⟨?_, ?_, ?_⟩
  · rintro ⟨hk, hs⟩
    have hb : (op.kind == OpKind.alterField || op.kind == OpKind.removeField) = true := by
      rcases hk with h | h <;> simp [h]
    simp [hb, hs]
    rfl
  · rintro ⟨hk, hs, hc⟩
    have h1 : (op.kind == OpKind.alterField || op.kind == OpKind.removeField) = false := by
      simp [hk]
    have h2 : (op.kind == OpKind.renameField) = true := by simp [hk]
    have h3 : self.field.dbColumn.isNone = true := by simp [hc]
    simp [h1, h2, h3, hs]
    rfl
  · rintro ⟨h1, h2⟩
    have hne1 : ((op.kind == OpKind.alterField || op.kind == OpKind.removeField)
        && sameField self op) = false := by
      by_contra hc
      simp only [Bool.not_eq_false, Bool.and_eq_true, Bool.or_eq_true, beq_iff_eq] at hc
      exact h1 ⟨hc.1, hc.2⟩
    have hne2 : (op.kind == OpKind.renameField && sameField self op
        && self.field.dbColumn.isNone) = false := by
      by_contra hc
      simp only [Bool.not_eq_false, Bool.and_eq_true, beq_iff_eq,
        Option.isNone_iff_eq_none] at hc
      exact h2 ⟨hc.1.1, hc.1.2, hc.2⟩
    refine ⟨?_, ?_, ?_⟩
    · intro hse
      simp [hne1, hne2, hse]
      rfl
    · rintro ⟨hse, hoe⟩
      simp [hne1, hne2, hse, hoe]
      rfl
    · rintro ⟨hse, hoe⟩
      simp [hne1, hne2, hse, hoe]
      rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit for django__django-16595 (lean).

SPEC ANALYSIS: problem_spec_reduceAlter is a conjunction of three implications whose guards PARTITION the entire (self,op) input space: C1 = (op alter OR remove) AND sameField -> result=[op]; C2 = (op rename AND sameField AND dbColumn=none) -> result=[op, freshly-built AlterField]; C3 = (NOT C1-guard AND NOT C2-guard) -> full Bool x Bool elidable sub-rules ([op] when self.elidable; [self] when only op.elidable; [] when neither). C1 disjoint from C2 by op.kind; C3 is the exact complement of C1-guard OR C2-guard; each region pins result to one concrete value. Therefore the spec is functionally TOTAL and DETERMINISTIC: any behaviorally-divergent impl leaves some conjunct's goal as an unprovable equality between distinct concrete values, so NO wrong impl can close correct_reduceAlter. => No same-spec wrong impl verifies => there is no faithful patch to resolve => verify=>correct holds. No BROKEN case possible.

SAME-SPEC: all 7 attacks + positive control return same_spec==True (swebench_unified.markers.same_spec, lean). Only the impl region was edited; axioms/pure/pre/post byte-identical.

POSITIVE CONTROL (pos.lean = exact gold impl): bash scripts/lean_verify.sh <pos.lean> -> exit 0. #print axioms correct_reduceAlter -> 'depends on axioms: [propext, Quot.sound]' (clean; no sorryAx / Classical.choice).

### ATTACKS (cmd: bash scripts/lean_verify.sh <atk_N.lean>; all run concurrently as background jobs, <=4 at a time):
- atk_1 (PREPATCH BUG: first guard tests only op.kind==removeField, dropping the widened alterField collapse; impl region byte-identical to Solution_prepatch.lean) -> exit 1. Genuine goal error: rfl failed on the C1 alterField branch ([op] vs fall-through []). PREPATCH REPRODUCED.
- atk_2 (PARTIAL-DOMAIN: correct except otherOp/neither-elidable returns [op] instead of []) -> exit 1. rfl failed on C3 neither-elidable goal ([op]=[]).
- atk_3 (BOUNDARY: rename arm drops the self.field.dbColumn.isNone guard, fires even when a column is pinned) -> exit 1. rfl failed on C3 fall-through goals.
- atk_4 (CONTROL-FLOW-EFFECT: elidable checks reordered before the collapse/rename arms) -> exit 1. rfl failed on C1/C2 goals.
- atk_5 (UNGROUNDED-ORACLE ECHO: always return [op]) -> exit 1. simp made no progress on C2/C3 goals ([op] != pair / []).
- atk_6 (SUBTLE BOUNDARY: rename arm builds the re-expressed AlterField with elidable:=true instead of false) -> exit 1. rfl failed on C2 pair-equality goal.
- atk_7 (SUBTLE: swap elidable fall-through outputs -> [self] when self.elidable, [op] when op.elidable) -> exit 1. rfl failed on C3 goals.
Every failure is a genuine goal-level equality error (rfl/simp on the exact spec conjunct), not a syntax/import artifact.

Because 0 of 7 wrong impls closed with clean axioms, NO faithful refined patch needed to be materialized or run through run_resolve (protocol step 2 triggers only for a verifying wrong impl). patches={} accordingly.

A-LEG / AXIOM AUDIT: Solution.lean declares NO axiom/opaque (axioms-start..axioms-end region is comment-only; grep for ^\s*(axiom|opaque) => no matches). axiom_check.py is a legitimate SKIP STUB (prints status=skip, exit 0) — nothing to validate because the modeled callee AlterField.reduce is modeled DEEPLY (OpKind tag, String.toLower equality, Option check, Bool fields, record literals). refinement.md: all 8 legs are R or I (rows 2,3,4,5,6 = I deeply-modeled; rows 1,7,8 = R type refinement); NO A-consumed / A-reference / kind-3 legs exist. mapping.md confirms axioms=[], deep_model_references=[]. The A-leg attack surface is therefore empty/vacuous by construction; the R/I legs correspond faithfully to the post-patch reduce arms (verified against patch.diff + instance.json: patch widens isinstance(operation, RemoveField) to (AlterField, RemoveField), exactly matching the Lean guard's added op.kind==alterField disjunct).

VERDICT: SOUND. Spec is total+deterministic; >=7 distinct same-spec wrong impls (prepatch bug + partial-domain + 2 boundary + control-flow-effect + ungrounded-oracle echo + fall-through swap) all fail to close with genuine goal errors; positive control closes with clean axioms; no A-legs to break. verify=>correct upheld.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-vs-real-callee) audit of AlterField.reduce model. Real repo cloned at base_commit f9fe062de5 with gold patch applied (isinstance widened RemoveField -> (AlterField, RemoveField)); matches patch.diff/refinement.md. Lean compiles (lean_verify.sh exit 0); #print axioms correct_reduceAlter = [propext, Quot.sound] (no sorryAx, real proof). same_spec(Solution, prepatch, lean_tables)=True (spec region byte-identical). Differential test of the modeled abstraction (implementation_reduceAlter) against the in-process real reduce over 288 pairings: op.kind in {alterField, removeField, renameField, AddField/RunPython as other}, case-varying ASCII model/field names, db_column in {None,'col'}, self.elidable x op.elidable = both flags -> 0 mismatches. Key cases verified against real code: (1) same-field alter-or-remove -> [op]; (2) same-field rename with self.field.db_column is None -> [op, AlterField(model_name=self.model_name, name=op.new_name, field=self.field)] with fresh op elidable=class-default False; (3) fall-through Operation.reduce: self.elidable -> [operation]=[op], op.elidable (self not) -> [self] (identity-checked res[0] is self_op) which is exactly the historical G-PANEL-2 diverging input now modeled correctly, neither elidable -> real returns bool False, modeled as [] per the documented result-type note (only 'replacement list produced vs not' is in the modeled outcome; the bool value is out of scope of the abstraction). No input found where the modeled function disagrees with the real callee within the declared abstraction. Spec is not too strong and does not drift.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `refinement.md`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical patched vs prepatch (markers.same_spec(...,lean)=True); impl+proof elided from the spec view, so the leak surface is the docstring + problem_spec_reduceAlter + type defs only. The public problem_statement already fully discloses the gold edit: it names AlterField.reduce, states the defect ('does not consider the case where operation is also an AlterField'), and literally proposes the fix code (isinstance(operation, AlterField) ... return [operation]). The spec-view docstring only restates that abstract collapse behavior ('If the following step either alters that same field again, or removes it ... the pair collapses to just the following step'), and the first postcondition conjunct mirrors it. No gold-diff line reproduced, no diff marker, no patched file path (fields.py), no hunk-header token (migration_name_fragment appears nowhere), no hints_text narrative, no bug->fix mechanism beyond the public statement. Rename/elidable arms are unchanged-by-patch scaffolding, not leakage. Nothing in the spec view exceeds the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
