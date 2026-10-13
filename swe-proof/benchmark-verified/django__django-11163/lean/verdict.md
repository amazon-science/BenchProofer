# P2 adversarial audit — django__django-11163

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk1.lean`, `atk2.lean`, `atk3.lean`, `atk4.lean`, `atk5.lean`, `atk6.lean`, `atk7.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong impl closes correct_modelToDict, so no faithful patch was materializable and no resolve run was required. The post-condition is a fully-pinned equality (result = (fs.filter (keep fields exclude)).map (fun f => (f.name, f.val))), pinning order/membership/names/values; every genuinely-wrong impl produces an unsatisfiable equality goal.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,14 +77,12 @@
     (fs : List (FieldRec α)) : List (String × α) := Id.run do
   let mut data : List (String × α) := []
   for f in fs do
-    -- skip non-editable fields
     if !f.editable then
       continue
-    -- a present inclusion selection (even if empty) must name the field
     if let some sel := fields then
-      if !(sel.contains f.name) then
-        continue
-    -- a present exclusion list bars the field if it names it
+      if !sel.isEmpty then
+        if !(sel.contains f.name) then
+          continue
     if let some ex := exclude then
       if ex.contains f.name then
         continue
```

Attack 2 — `atk2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,16 +77,10 @@
     (fs : List (FieldRec α)) : List (String × α) := Id.run do
   let mut data : List (String × α) := []
   for f in fs do
-    -- skip non-editable fields
     if !f.editable then
       continue
-    -- a present inclusion selection (even if empty) must name the field
     if let some sel := fields then
       if !(sel.contains f.name) then
-        continue
-    -- a present exclusion list bars the field if it names it
-    if let some ex := exclude then
-      if ex.contains f.name then
         continue
     data := data ++ [(f.name, f.val)]
   return data
```

Attack 3 — `atk3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,14 +77,9 @@
     (fs : List (FieldRec α)) : List (String × α) := Id.run do
   let mut data : List (String × α) := []
   for f in fs do
-    -- skip non-editable fields
-    if !f.editable then
-      continue
-    -- a present inclusion selection (even if empty) must name the field
     if let some sel := fields then
       if !(sel.contains f.name) then
         continue
-    -- a present exclusion list bars the field if it names it
     if let some ex := exclude then
       if ex.contains f.name then
         continue
```

Attack 4 — `atk4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,18 +77,15 @@
     (fs : List (FieldRec α)) : List (String × α) := Id.run do
   let mut data : List (String × α) := []
   for f in fs do
-    -- skip non-editable fields
     if !f.editable then
       continue
-    -- a present inclusion selection (even if empty) must name the field
     if let some sel := fields then
       if !(sel.contains f.name) then
         continue
-    -- a present exclusion list bars the field if it names it
     if let some ex := exclude then
       if ex.contains f.name then
         continue
-    data := data ++ [(f.name, f.val)]
+    data := (f.name, f.val) :: data
   return data
 -- impl-end
 
```

Attack 5 — `atk5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -74,22 +74,7 @@
 
 -- impl-start
 def implementation_modelToDict {α : Type} (fields exclude : Option (List String))
-    (fs : List (FieldRec α)) : List (String × α) := Id.run do
-  let mut data : List (String × α) := []
-  for f in fs do
-    -- skip non-editable fields
-    if !f.editable then
-      continue
-    -- a present inclusion selection (even if empty) must name the field
-    if let some sel := fields then
-      if !(sel.contains f.name) then
-        continue
-    -- a present exclusion list bars the field if it names it
-    if let some ex := exclude then
-      if ex.contains f.name then
-        continue
-    data := data ++ [(f.name, f.val)]
-  return data
+    (fs : List (FieldRec α)) : List (String × α) := []
 -- impl-end
 
 
```

Attack 6 — `atk6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,19 +77,16 @@
     (fs : List (FieldRec α)) : List (String × α) := Id.run do
   let mut data : List (String × α) := []
   for f in fs do
-    -- skip non-editable fields
     if !f.editable then
       continue
-    -- a present inclusion selection (even if empty) must name the field
     if let some sel := fields then
       if !(sel.contains f.name) then
         continue
-    -- a present exclusion list bars the field if it names it
     if let some ex := exclude then
       if ex.contains f.name then
         continue
     data := data ++ [(f.name, f.val)]
-  return data
+  return data.reverse
 -- impl-end
 
 
```

Attack 7 — `atk7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,16 +77,13 @@
     (fs : List (FieldRec α)) : List (String × α) := Id.run do
   let mut data : List (String × α) := []
   for f in fs do
-    -- skip non-editable fields
     if !f.editable then
       continue
-    -- a present inclusion selection (even if empty) must name the field
     if let some sel := fields then
       if !(sel.contains f.name) then
         continue
-    -- a present exclusion list bars the field if it names it
     if let some ex := exclude then
-      if ex.contains f.name then
+      if !(ex.contains f.name) then
         continue
     data := data ++ [(f.name, f.val)]
   return data
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Projecting a record's editable fields into an ordered association list.

We are given a sequence of field records, each carrying a name, an "editable"
flag, and an extracted value. We build an association list of `(name, value)`
pairs by walking the sequence in order and keeping a field exactly when all of
the following hold:

  * the field is editable;
  * an OPTIONAL inclusion selection includes it — the selection is either absent
    or an explicit list of names. When the selection is ABSENT, every field is
    included. When the selection is PRESENT, only fields whose name occurs in it
    are included; in particular an empty selection includes NOTHING;
  * an OPTIONAL exclusion list does not bar it — the exclusion is either absent
    or an explicit list of names. A field is barred exactly when its name occurs
    in that list; an absent or empty exclusion bars nothing.

The two options are independent of each other and of the field order: the result
keeps the surviving fields in their original sequence order, pairing each with
its own name and its own extracted value.

The salient point is the meaning of the inclusion selection: being ABSENT
(no selection supplied) and being PRESENT-BUT-EMPTY are different requests. An
absent selection imposes no inclusion constraint, whereas an empty selection is
a genuine request that includes no field at all.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The only per-field datum
-- the projection reads beyond a field's name and editability is its extracted
-- value; that value is unchanged by the modeled behavior, so it is carried as a
-- given attribute `Field.val` (a type refinement) rather than axiomatized. Hence
-- the spec needs no `opaque`/`axiom` callee contract.
-- axioms-end

-- pure-start
/-- A field record, restricted to the three attributes the projection reads:
its name, whether it is editable, and its extracted value. -/
structure FieldRec (α : Type) where
  name : String
  editable : Bool
  val : α

/-- Whether a field survives the projection, given the optional inclusion
selection and the optional exclusion list. A field survives iff it is editable,
the inclusion selection includes it (absent ⇒ include all; present ⇒ name must occur,
so an empty selection includes none), and the exclusion list does not contain its
name (absent ⇒ bar none). -/
def keep {α : Type} (fields exclude : Option (List String)) (f : FieldRec α) : Bool :=
  f.editable
  && (match fields with
      | none => true
      | some sel => sel.contains f.name)
  && (match exclude with
      | none => true
      | some ex => !ex.contains f.name)
-- pure-end

-- post-conditions-start
/-- The result is fully pinned to the inputs: it is exactly the surviving fields
(in their original order) paired with their own name and extracted value. Order,
membership, names, and values are all determined — no output component is free.

In particular, when the inclusion selection is present and empty no field
survives (the result is empty), and when it is absent every editable, non-barred
field survives. -/
def problem_spec_modelToDict {α : Type} (fields exclude : Option (List String))
    (fs : List (FieldRec α)) (result : List (String × α)) : Prop :=
  result = (fs.filter (keep fields exclude)).map (fun f => (f.name, f.val))
-- post-conditions-end

-- impl-start
def implementation_modelToDict {α : Type} (fields exclude : Option (List String))
    (fs : List (FieldRec α)) : List (String × α) := Id.run do
  let mut data : List (String × α) := []
  for f in fs do
    -- skip non-editable fields
    if !f.editable then
      continue
    -- a present inclusion selection (even if empty) must name the field
    if let some sel := fields then
      if !(sel.contains f.name) then
        continue
    -- a present exclusion list bars the field if it names it
    if let some ex := exclude then
      if ex.contains f.name then
        continue
    data := data ++ [(f.name, f.val)]
  return data
-- impl-end


-- proof-start
theorem correct_modelToDict :
    ∀ {α : Type} (fields exclude : Option (List String)) (fs : List (FieldRec α)),
      problem_spec_modelToDict fields exclude fs
        (implementation_modelToDict fields exclude fs) := by
  intro α fields exclude fs
  unfold problem_spec_modelToDict implementation_modelToDict
  suffices h : ∀ (init : List (String × α)),
      (forIn fs init fun f r =>
        (if (!f.editable) = true then pure (ForInStep.yield r)
        else do
          match fields with
          | some sel =>
            if (!sel.contains f.name) = true then pure (ForInStep.yield r)
            else do
              match exclude with
              | some ex =>
                if ex.contains f.name = true then pure (ForInStep.yield r)
                else pure (ForInStep.yield (r ++ [(f.name, f.val)]))
              | x => pure (ForInStep.yield (r ++ [(f.name, f.val)]))
          | x =>
            match exclude with
            | some ex =>
              if ex.contains f.name = true then pure (ForInStep.yield r)
              else pure (ForInStep.yield (r ++ [(f.name, f.val)]))
            | x => pure (ForInStep.yield (r ++ [(f.name, f.val)]))) : Id _)
        = init ++ (fs.filter (keep fields exclude)).map (fun f => (f.name, f.val)) by
    have := h []
    simpa using this
  intro init
  induction fs generalizing init with
  | nil => simp only [List.forIn_nil, List.filter_nil, List.map_nil, List.append_nil]; rfl
  | cons f fs ih =>
    rw [List.forIn_cons]
    simp only [keep, List.filter_cons]
    rcases fields with _ | sel <;> rcases exclude with _ | ex <;> split_ifs <;>
      simp_all [List.append_assoc]

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

 Each attack copies gold Solution.lean and edits ONLY the impl region (axioms/pure/pre/post byte-identical). same_spec check (swebench_unified.markers.same_spec, lean backend) = True for all 7 attacks.

VERIFY COMMAND (per file): bash scripts/lean_verify.sh <file>. Run concurrently in two batches of 4.

### Results
- atk_pos.lean (= gold Solution.lean, positive control): exit 0 (VERIFIES). #print axioms correct_modelToDict = [propext, Quot.sound] — clean, no sorry/sorryAx.
- atk1.lean PREPATCH BUG (empty inclusion selection imposes no constraint via `if !sel.isEmpty then`; returns all on fields=[]): same_spec True, exit 1 — prepatch reproduced, proof fails with unsolved equality goal.
- atk2.lean PARTIAL-DOMAIN (drops exclusion check entirely): same_spec True, exit 1.
- atk3.lean CONTROL-FLOW/BOUNDARY (ignores editable flag, keeps all): same_spec True, exit 1.
- atk4.lean CONTROL-FLOW-EFFECT (prepend `(f.name,f.val)::data` -> reversed order): same_spec True, exit 1.
- atk5.lean UNGROUNDED-ORACLE ECHO (always returns []): same_spec True, exit 1 (goal reduces to `∀ a ∈ fs, keep fields exclude a = false`, false in general).
- atk6.lean BOUNDARY (return data.reverse): same_spec True, exit 1.
- atk7.lean PARTIAL-DOMAIN (exclusion inverted: bar when name NOT in exclude): same_spec True, exit 1.

All 7 failures are genuine unsolved-equality proof goals (log tails show the residual `... = List.map (fun f => (f.name, f.val)) (List.filter (keep fields exclude) fs)` goal), NOT import/syntax errors. NO wrong impl closes with clean axioms => step-2 obligation (materialize faithful patch + run_resolve) is vacuous: there is no verifying-but-wrong candidate to resolve.

REFINEMENT AUDIT: refinement.md legs are all R (rows 1-5) / I (row 6), no A-consumed / A-reference / kind-3. meta.json confirms axioms=[], deep_model_references=[], conf_skip=false; axiom_check.py is a skip stub. No A-legs to audit for callee correspondence; the sole callee f.value_from_object(instance) is carried as the FieldRec.val type-refinement attribute (R), consistent across Solution.lean/refinement.md/mapping.md/meta.json. R/I legs mechanically covered by G-CONF (100000 inputs, 0 disagreements per meta.json).

CONCLUSION: The post-condition is a total, fully-pinned functional equality; verify (correct_* closes with clean axioms) coincides with correct (output matches the gold spec) for this bundle. verify => correct holds across all attempted falsifications. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk1.lean`, `atk2.lean`, `atk3.lean`, `atk4.lean`, `atk5.lean`, `atk6.lean`, `atk7.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong impl closes correct_modelToDict, so no faithful patch was materializable and no resolve run was required. The post-condition is a fully-pinned equality (result = (fs.filter (keep fields exclude)).map (fun f => (f.name, f.val))), pinning order/membership/names/values; every genuinely-wrong impl produces an unsatisfiable equality goal.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Projecting a record's editable fields into an ordered association list.

We are given a sequence of field records, each carrying a name, an "editable"
flag, and an extracted value. We build an association list of `(name, value)`
pairs by walking the sequence in order and keeping a field exactly when all of
the following hold:

  * the field is editable;
  * an OPTIONAL inclusion selection includes it — the selection is either absent
    or an explicit list of names. When the selection is ABSENT, every field is
    included. When the selection is PRESENT, only fields whose name occurs in it
    are included; in particular an empty selection includes NOTHING;
  * an OPTIONAL exclusion list does not bar it — the exclusion is either absent
    or an explicit list of names. A field is barred exactly when its name occurs
    in that list; an absent or empty exclusion bars nothing.

The two options are independent of each other and of the field order: the result
keeps the surviving fields in their original sequence order, pairing each with
its own name and its own extracted value.

The salient point is the meaning of the inclusion selection: being ABSENT
(no selection supplied) and being PRESENT-BUT-EMPTY are different requests. An
absent selection imposes no inclusion constraint, whereas an empty selection is
a genuine request that includes no field at all.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The only per-field datum
-- the projection reads beyond a field's name and editability is its extracted
-- value; that value is unchanged by the modeled behavior, so it is carried as a
-- given attribute `Field.val` (a type refinement) rather than axiomatized. Hence
-- the spec needs no `opaque`/`axiom` callee contract.
-- axioms-end

-- pure-start
/-- A field record, restricted to the three attributes the projection reads:
its name, whether it is editable, and its extracted value. -/
structure FieldRec (α : Type) where
  name : String
  editable : Bool
  val : α

/-- Whether a field survives the projection, given the optional inclusion
selection and the optional exclusion list. A field survives iff it is editable,
the inclusion selection includes it (absent ⇒ include all; present ⇒ name must occur,
so an empty selection includes none), and the exclusion list does not contain its
name (absent ⇒ bar none). -/
def keep {α : Type} (fields exclude : Option (List String)) (f : FieldRec α) : Bool :=
  f.editable
  && (match fields with
      | none => true
      | some sel => sel.contains f.name)
  && (match exclude with
      | none => true
      | some ex => !ex.contains f.name)
-- pure-end

-- post-conditions-start
/-- The result is fully pinned to the inputs: it is exactly the surviving fields
(in their original order) paired with their own name and extracted value. Order,
membership, names, and values are all determined — no output component is free.

In particular, when the inclusion selection is present and empty no field
survives (the result is empty), and when it is absent every editable, non-barred
field survives. -/
def problem_spec_modelToDict {α : Type} (fields exclude : Option (List String))
    (fs : List (FieldRec α)) (result : List (String × α)) : Prop :=
  result = (fs.filter (keep fields exclude)).map (fun f => (f.name, f.val))
-- post-conditions-end

-- impl-start
def implementation_modelToDict {α : Type} (fields exclude : Option (List String))
    (fs : List (FieldRec α)) : List (String × α) := Id.run do
  let mut data : List (String × α) := []
  for f in fs do
    -- skip non-editable fields
    if !f.editable then
      continue
    -- a present inclusion selection (even if empty) must name the field
    if let some sel := fields then
      if !(sel.contains f.name) then
        continue
    -- a present exclusion list bars the field if it names it
    if let some ex := exclude then
      if ex.contains f.name then
        continue
    data := data ++ [(f.name, f.val)]
  return data
-- impl-end


-- proof-start
theorem correct_modelToDict :
    ∀ {α : Type} (fields exclude : Option (List String)) (fs : List (FieldRec α)),
      problem_spec_modelToDict fields exclude fs
        (implementation_modelToDict fields exclude fs) := by
  intro α fields exclude fs
  unfold problem_spec_modelToDict implementation_modelToDict
  suffices h : ∀ (init : List (String × α)),
      (forIn fs init fun f r =>
        (if (!f.editable) = true then pure (ForInStep.yield r)
        else do
          match fields with
          | some sel =>
            if (!sel.contains f.name) = true then pure (ForInStep.yield r)
            else do
              match exclude with
              | some ex =>
                if ex.contains f.name = true then pure (ForInStep.yield r)
                else pure (ForInStep.yield (r ++ [(f.name, f.val)]))
              | x => pure (ForInStep.yield (r ++ [(f.name, f.val)]))
          | x =>
            match exclude with
            | some ex =>
              if ex.contains f.name = true then pure (ForInStep.yield r)
              else pure (ForInStep.yield (r ++ [(f.name, f.val)]))
            | x => pure (ForInStep.yield (r ++ [(f.name, f.val)]))) : Id _)
        = init ++ (fs.filter (keep fields exclude)).map (fun f => (f.name, f.val)) by
    have := h []
    simpa using this
  intro init
  induction fs generalizing init with
  | nil => simp only [List.forIn_nil, List.filter_nil, List.map_nil, List.append_nil]; rfl
  | cons f fs ih =>
    rw [List.forIn_cons]
    simp only [keep, List.filter_cons]
    rcases fields with _ | sel <;> rcases exclude with _ | ex <;> split_ifs <;>
      simp_all [List.append_assoc]

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

 Each attack copies gold Solution.lean and edits ONLY the impl region (axioms/pure/pre/post byte-identical). same_spec check (swebench_unified.markers.same_spec, lean backend) = True for all 7 attacks.

VERIFY COMMAND (per file): bash scripts/lean_verify.sh <file>. Run concurrently in two batches of 4.

### Results
- atk_pos.lean (= gold Solution.lean, positive control): exit 0 (VERIFIES). #print axioms correct_modelToDict = [propext, Quot.sound] — clean, no sorry/sorryAx.
- atk1.lean PREPATCH BUG (empty inclusion selection imposes no constraint via `if !sel.isEmpty then`; returns all on fields=[]): same_spec True, exit 1 — prepatch reproduced, proof fails with unsolved equality goal.
- atk2.lean PARTIAL-DOMAIN (drops exclusion check entirely): same_spec True, exit 1.
- atk3.lean CONTROL-FLOW/BOUNDARY (ignores editable flag, keeps all): same_spec True, exit 1.
- atk4.lean CONTROL-FLOW-EFFECT (prepend `(f.name,f.val)::data` -> reversed order): same_spec True, exit 1.
- atk5.lean UNGROUNDED-ORACLE ECHO (always returns []): same_spec True, exit 1 (goal reduces to `∀ a ∈ fs, keep fields exclude a = false`, false in general).
- atk6.lean BOUNDARY (return data.reverse): same_spec True, exit 1.
- atk7.lean PARTIAL-DOMAIN (exclusion inverted: bar when name NOT in exclude): same_spec True, exit 1.

All 7 failures are genuine unsolved-equality proof goals (log tails show the residual `... = List.map (fun f => (f.name, f.val)) (List.filter (keep fields exclude) fs)` goal), NOT import/syntax errors. NO wrong impl closes with clean axioms => step-2 obligation (materialize faithful patch + run_resolve) is vacuous: there is no verifying-but-wrong candidate to resolve.

REFINEMENT AUDIT: refinement.md legs are all R (rows 1-5) / I (row 6), no A-consumed / A-reference / kind-3. meta.json confirms axioms=[], deep_model_references=[], conf_skip=false; axiom_check.py is a skip stub. No A-legs to audit for callee correspondence; the sole callee f.value_from_object(instance) is carried as the FieldRec.val type-refinement attribute (R), consistent across Solution.lean/refinement.md/mapping.md/meta.json. R/I legs mechanically covered by G-CONF (100000 inputs, 0 disagreements per meta.json).

CONCLUSION: The post-condition is a total, fully-pinned functional equality; verify (correct_* closes with clean axioms) coincides with correct (output matches the gold spec) for this bundle. verify => correct holds across all attempted falsifications. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) review for django__django-11163 (lean). The modeled function is the post-condition problem_spec_modelToDict, an exact equality: result = (fs.filter (keep fields exclude)).map (fun f => (f.name, f.val)), with keep f = f.editable && (fields: none⇒true | some sel⇒sel.contains f.name) && (exclude: none⇒true | some ex⇒!ex.contains f.name). Real callee (post-patch model_to_dict, django/forms/models.py) confirmed byte-identical: guard sequence is `not editable ⇒ skip`, `fields is not None and f.name not in fields ⇒ skip`, `exclude and f.name in exclude ⇒ skip`, else data[f.name]=f.value_from_object(instance).

Leg-by-leg agreement: (1) editable ↔ getattr(f,'editable',False) skip — match. (2) THE FIXED OP: some sel/none ↔ `fields is not None`; empty `some []` keeps nothing (contains always false) exactly mirrors `[] is not None` skipping all, and none/`None` keeps all — the discriminating absent-vs-present-empty behavior is modeled correctly. (3) exclusion: spec's `!ex.contains` under `some` vs none is behavior-equivalent to the repo's truthy guard `if exclude and f.name in exclude`, because `f.name in exclude` is already false for None/[] and any non-containing list — so None, [], and name-absent all keep the field in both; only present-and-containing skips. Match. (4) order/result: filter-then-map preserves walk order = dict insertion order via list(d.items()) — match.

Only theoretical divergence is duplicate field names (list model keeps both pairs; a dict collapses them), but this is OUT OF THE MODELED DOMAIN — Django model field names are unique across chain(concrete_fields, private_fields, many_to_many), so the walk never yields duplicates. mapping.md/refinement.md document this invariant and G-CONF enforces it (rng.sample ⇒ unique names) over 1e5 inputs with 0 disagreements. The spec imposes no constraint the real repo violates on any in-domain input, and is not weaker either.

Verification performed: same_spec(Solution, Solution_prepatch, LeanBackend.language) = True (spec region byte-identical). Solution.lean compiles via lean_verify.sh (exit 0); #print axioms correct_modelToDict = [propext, Quot.sound] only — no sorryAx, proof is genuine. G-DIFF: prepatch (empty-selection quirk via `if !sel.isEmpty`) fails verification against this spec, confirming the spec discriminates the bug. No drift / no spec-too-strong found.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage/gold-reconstruction judgment for django__django-11163 (lean). Public problem_statement is maximally explicit: it contains the verbatim gold diff ('if fields and f.name not in fields:' -> 'if fields is not None and f.name not in fields:') AND the exact behavioral consequence ('model_to_dict(instance, fields=[]) should return empty dict, because no fields were requested. But it returns all fields'), plus a link to the fixing PR. The lean spec view discloses precisely and only this same distinction: doc-comment 'when the selection is ABSENT, every field is included ... an empty selection includes NOTHING' and post-condition note 'when the inclusion selection is present and empty no field survives ... when it is absent every editable, non-barred field survives'. That is a faithful restatement of already-public information, not disclosure beyond it. Verification performed: (1) markers.same_spec(Solution.lean, Solution_prepatch.lean, lean tables) = True — the spec region (doc-comment + FieldRec + keep + problem_spec_modelToDict) is byte-identical between gold and prepatch, so nothing in the spec view discriminates the gold from the buggy variant beyond the public statement; (2) impl-start region = 'implementation elided — supplied by the consumer' and proof-start region = 'proof elided — supplied by the consumer' — the algorithm (Id.run for-loop with per-guard continue) and proof strategy (induction + split_ifs) are NOT in the spec view; (3) the exclude/editable/ordering modeling and the Option none/some bijection are generic spec structure needed to state any faithful post-condition, and the exclude leg is unchanged by the patch, so it is not the gold discriminator. No spec-view line reconstructs the gold edit beyond what problem_statement already fully publishes. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
