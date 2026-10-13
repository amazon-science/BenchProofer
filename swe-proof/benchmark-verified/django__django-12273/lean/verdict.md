# P2 adversarial audit — django__django-12273

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_5.lean`, `atk_9.lean`, `atk_10.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. The spec post-condition is a total functional equality (result = setAttr (applyLinks store ancestorLinks value) primaryKeyName value): result is pinned to a single closed function of the inputs. Any implementation for which correct_setPrimaryKey closes is provably extensionally equal to the gold function on every input, hence behaviorally identical to the gold patch, hence resolving. All 6 genuinely-wrong-behavior impls fail to close (exit 1); the only closer is the trivial echo of the spec RHS, whose faithful patch equals the gold patch and RESOLVES=True.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -83,9 +83,6 @@
     (ancestorLinks : List AncestorLink) (value : Option Int) :
     String → Option Int := Id.run do
   let mut s := store
-  for link in ancestorLinks do
-    if link.linked && !link.sameAsPrimaryKey then
-      s := setAttr s link.keyName value
   s := setAttr s primaryKeyName value
   return s
 -- impl-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -84,7 +84,7 @@
     String → Option Int := Id.run do
   let mut s := store
   for link in ancestorLinks do
-    if link.linked && !link.sameAsPrimaryKey then
+    if link.linked then
       s := setAttr s link.keyName value
   s := setAttr s primaryKeyName value
   return s
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -84,7 +84,7 @@
     String → Option Int := Id.run do
   let mut s := store
   for link in ancestorLinks do
-    if link.linked && !link.sameAsPrimaryKey then
+    if !link.sameAsPrimaryKey then
       s := setAttr s link.keyName value
   s := setAttr s primaryKeyName value
   return s
```

Attack 4 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -86,7 +86,6 @@
   for link in ancestorLinks do
     if link.linked && !link.sameAsPrimaryKey then
       s := setAttr s link.keyName value
-  s := setAttr s primaryKeyName value
   return s
 -- impl-end
 
```

Attack 5 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -81,46 +81,15 @@
 def implementation_setPrimaryKey
     (store : String → Option Int) (primaryKeyName : String)
     (ancestorLinks : List AncestorLink) (value : Option Int) :
-    String → Option Int := Id.run do
-  let mut s := store
-  for link in ancestorLinks do
-    if link.linked && !link.sameAsPrimaryKey then
-      s := setAttr s link.keyName value
-  s := setAttr s primaryKeyName value
-  return s
+    String → Option Int := setAttr (applyLinks store ancestorLinks value) primaryKeyName value
 -- impl-end
 
 -- proof-start
-/-- Helper (Route B): the cleaned `forIn` accumulation over the ancestor links,
-generalized over the accumulator, equals the front-recursive `applyLinks` fold. -/
-theorem forIn_helper (links : List AncestorLink) (init : String → Option Int)
-    (value : Option Int) :
-    Id.run (forIn links init (fun link r =>
-      if (link.linked && !link.sameAsPrimaryKey) = true then
-        pure (ForInStep.yield (setAttr r link.keyName value))
-      else
-        pure (ForInStep.yield r))) = applyLinks init links value := by
-  induction links generalizing init with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, applyLinks] at ih ⊢
-    by_cases h : (a.linked && !a.sameAsPrimaryKey) = true
-    · simp only [h, if_true, ih]
-    · simp only [h, ih]
-      simp only [Bool.not_eq_true] at h
-      simp only [Bool.false_eq_true, if_false]
-
 theorem correct_setPrimaryKey :
     ∀ (store : String → Option Int) (primaryKeyName : String)
       (ancestorLinks : List AncestorLink) (value : Option Int),
       problem_spec_setPrimaryKey store primaryKeyName ancestorLinks value
         (implementation_setPrimaryKey store primaryKeyName ancestorLinks value) := by
   intro store primaryKeyName ancestorLinks value
-  unfold problem_spec_setPrimaryKey implementation_setPrimaryKey
-  simp only [Id.run, bind]
-  have := forIn_helper ancestorLinks store value
-  simp only [Id.run] at this
-  rw [this]
   rfl
 -- proof-end
```

Attack 6 — `atk_9.lean` → rejected (same spec, does not verify — good)

```diff
@@ -83,9 +83,11 @@
     (ancestorLinks : List AncestorLink) (value : Option Int) :
     String → Option Int := Id.run do
   let mut s := store
+  let mut done := false
   for link in ancestorLinks do
-    if link.linked && !link.sameAsPrimaryKey then
+    if link.linked && !link.sameAsPrimaryKey && !done then
       s := setAttr s link.keyName value
+      done := true
   s := setAttr s primaryKeyName value
   return s
 -- impl-end
```

Attack 7 — `atk_10.lean` → rejected (same spec, does not verify — good)

```diff
@@ -85,7 +85,7 @@
   let mut s := store
   for link in ancestorLinks do
     if link.linked && !link.sameAsPrimaryKey then
-      s := setAttr s link.keyName value
+      s := setAttr s link.keyName none
   s := setAttr s primaryKeyName value
   return s
 -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Assigning a primary-key value to an object that participates in a chain of
inheritance.

An object built by inheritance keeps, alongside its own primary-key attribute, a
distinct key attribute for each ancestor it descends from; those ancestor-key
attributes are what tie the object to its inherited parts. When a single
primary-key value is assigned to such an object, the assignment must reach ALL of
those keys at once — both the object's own primary-key attribute and every
ancestor-key attribute that links it to an inherited part — so that the object is
consistently re-keyed (in particular, clearing the primary key clears the whole
key chain). An ancestor link is excluded only when it is absent, or when it
already coincides with the object's own primary-key attribute (so it is covered
by that assignment). Every attribute that is not part of this key chain keeps its
previous value.

The object's attributes are modeled as a total map from attribute name to its
value (absent ⇒ `none`). `store` is the object before the assignment,
`primaryKeyName` its own primary-key attribute name, `ancestorLinks` the list of
ancestor links (each carrying whether it is present, whether it coincides with
the own primary key, and the ancestor-key attribute name it writes to), and
`value` the assigned value. The result is the object after the assignment.
-/

-- axioms-start
-- No UNCHANGED callee is consumed as an opaque axiom and none is deep-modeled as
-- an A-reference: the assignment is a concrete sequence of attribute-store
-- updates over metadata that is supplied as INPUT (the ancestor-link list, the
-- own primary-key attribute name, each link's target attribute name). The
-- attribute reads/writes are modeled directly as the `store` map. Hence no
-- `opaque`/`axiom` declaration is required.
-- axioms-end

-- pure-start
/-- One ancestor link of an inherited object.
  * `linked` — the link is present (a real link field, not absent);
  * `sameAsPrimaryKey` — the link coincides with the object's own primary-key
    attribute (and so is already handled by the own-key assignment);
  * `keyName` — the ancestor-key attribute name this link writes to. -/
structure AncestorLink where
  linked : Bool
  sameAsPrimaryKey : Bool
  keyName : String
deriving DecidableEq, Repr

/-- Update one attribute of the store to `v`, leaving all others unchanged. -/
def setAttr (s : String → Option Int) (k : String) (v : Option Int) :
    String → Option Int :=
  fun n => if n = k then v else s n

/-- Apply the assignment to every qualifying ancestor-key attribute, front to
back: a link writes its ancestor key iff it is present and does not already
coincide with the own primary key; otherwise it is skipped. Front-recursive so it
pairs with the accumulator loop in the implementation. -/
def applyLinks (s : String → Option Int) (links : List AncestorLink)
    (v : Option Int) : String → Option Int :=
  match links with
  | [] => s
  | link :: rest =>
    let s' := if link.linked && !link.sameAsPrimaryKey then setAttr s link.keyName v else s
    applyLinks s' rest v
-- pure-end

-- post-conditions-start
/-- The resulting object is exactly: the input object with every qualifying
ancestor-key attribute set to the assigned value, and then the object's own
primary-key attribute set to the assigned value. The own-key assignment is last,
mirroring that it always takes effect. Every attribute outside this key chain is
pinned to its input value (no result component is left free). -/
def problem_spec_setPrimaryKey
    (store : String → Option Int) (primaryKeyName : String)
    (ancestorLinks : List AncestorLink) (value : Option Int)
    (result : String → Option Int) : Prop :=
  result = setAttr (applyLinks store ancestorLinks value) primaryKeyName value
-- post-conditions-end

-- impl-start
def implementation_setPrimaryKey
    (store : String → Option Int) (primaryKeyName : String)
    (ancestorLinks : List AncestorLink) (value : Option Int) :
    String → Option Int := Id.run do
  let mut s := store
  for link in ancestorLinks do
    if link.linked && !link.sameAsPrimaryKey then
      s := setAttr s link.keyName value
  s := setAttr s primaryKeyName value
  return s
-- impl-end

-- proof-start
/-- Helper (Route B): the cleaned `forIn` accumulation over the ancestor links,
generalized over the accumulator, equals the front-recursive `applyLinks` fold. -/
theorem forIn_helper (links : List AncestorLink) (init : String → Option Int)
    (value : Option Int) :
    Id.run (forIn links init (fun link r =>
      if (link.linked && !link.sameAsPrimaryKey) = true then
        pure (ForInStep.yield (setAttr r link.keyName value))
      else
        pure (ForInStep.yield r))) = applyLinks init links value := by
  induction links generalizing init with
  | nil => rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind, applyLinks] at ih ⊢
    by_cases h : (a.linked && !a.sameAsPrimaryKey) = true
    · simp only [h, if_true, ih]
    · simp only [h, ih]
      simp only [Bool.not_eq_true] at h
      simp only [Bool.false_eq_true, if_false]

theorem correct_setPrimaryKey :
    ∀ (store : String → Option Int) (primaryKeyName : String)
      (ancestorLinks : List AncestorLink) (value : Option Int),
      problem_spec_setPrimaryKey store primaryKeyName ancestorLinks value
        (implementation_setPrimaryKey store primaryKeyName ancestorLinks value) := by
  intro store primaryKeyName ancestorLinks value
  unfold problem_spec_setPrimaryKey implementation_setPrimaryKey
  simp only [Id.run, bind]
  have := forIn_helper ancestorLinks store value
  simp only [Id.run] at this
  rw [this]
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL EXECUTED (root; verify: bash scripts/lean_verify.sh <f>; same_spec via swebench_unified.markers.same_spec with lean backend). BASELINE: positive_control.lean exit 0; prepatch.lean exit 1 (G-DIFF red, rfl mismatch since buggy impl omits applyLinks) -> prepatch_reproduced=true. ATTACKS (all same_spec=True, only impl region edited): atk_1 prepatch bug own-key-only exit1; atk_2 drop sameAsPrimaryKey guard exit1; atk_3 drop linked guard (writes absent links) exit1; atk_5 omit own-pk write exit1; atk_9 control-flow first-qualifying-link-only exit1; atk_10 write wrong constant none to ancestor keys exit1; atk_6 ungrounded-oracle ECHO (return spec RHS verbatim) exit0 CLOSES.

AXIOMS: #print axioms correct_setPrimaryKey on atk_6 = 'does not depend on any axioms' (clean, cleaner than gold's [propext, Quot.sound]); no sorry/opaque/custom axiom anywhere. RESOLVE RUN: atk_6 faithful patch materialized (=gold patch, since echo impl is definitionally the spec RHS which is the gold behavior) and run through run_resolve('django__django-12273', ...) via the real Docker harness -> RESOLVED=True. A resolving echo is NOT a weakness (resolved G-PANEL-1/echo policy). WHY SOUND: spec is a total functional equality, so verify => extensional equality to gold => resolves; no slack for a spec-satisfying non-resolving impl.

A-LEG AUDIT: axioms-start/end region genuinely empty; refinement.md legs all R/I (no A-consumed, no A-reference, no kind-3); metadata accessors parents.values()/target_field.attname/pk.attname are honest INPUTS not deep-modeled callees; correspondence holds. No closing-clean-axiom impl has a faithful patch that fails to resolve. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_5.lean`, `atk_9.lean`, `atk_10.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. The spec post-condition is a total functional equality (result = setAttr (applyLinks store ancestorLinks value) primaryKeyName value): result is pinned to a single closed function of the inputs. Any implementation for which correct_setPrimaryKey closes is provably extensionally equal to the gold function on every input, hence behaviorally identical to the gold patch, hence resolving. All 6 genuinely-wrong-behavior impls fail to close (exit 1); the only closer is the trivial echo of the spec RHS, whose faithful patch equals the gold patch and RESOLVES=True.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_9.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_10.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Assigning a primary-key value to an object that participates in a chain of
inheritance.

An object built by inheritance keeps, alongside its own primary-key attribute, a
distinct key attribute for each ancestor it descends from; those ancestor-key
attributes are what tie the object to its inherited parts. When a single
primary-key value is assigned to such an object, the assignment must reach ALL of
those keys at once — both the object's own primary-key attribute and every
ancestor-key attribute that links it to an inherited part — so that the object is
consistently re-keyed (in particular, clearing the primary key clears the whole
key chain). An ancestor link is excluded only when it is absent, or when it
already coincides with the object's own primary-key attribute (so it is covered
by that assignment). Every attribute that is not part of this key chain keeps its
previous value.

The object's attributes are modeled as a total map from attribute name to its
value (absent ⇒ `none`). `store` is the object before the assignment,
`primaryKeyName` its own primary-key attribute name, `ancestorLinks` the list of
ancestor links (each carrying whether it is present, whether it coincides with
the own primary key, and the ancestor-key attribute name it writes to), and
`value` the assigned value. The result is the object after the assignment.
-/

-- axioms-start
-- No UNCHANGED callee is consumed as an opaque axiom and none is deep-modeled as
-- an A-reference: the assignment is a concrete sequence of attribute-store
-- updates over metadata that is supplied as INPUT (the ancestor-link list, the
-- own primary-key attribute name, each link's target attribute name). The
-- attribute reads/writes are modeled directly as the `store` map. Hence no
-- `opaque`/`axiom` declaration is required.
-- axioms-end

-- pure-start
/-- One ancestor link of an inherited object.
  * `linked` — the link is present (a real link field, not absent);
  * `sameAsPrimaryKey` — the link coincides with the object's own primary-key
    attribute (and so is already handled by the own-key assignment);
  * `keyName` — the ancestor-key attribute name this link writes to. -/
structure AncestorLink where
  linked : Bool
  sameAsPrimaryKey : Bool
  keyName : String
deriving DecidableEq, Repr

/-- Update one attribute of the store to `v`, leaving all others unchanged. -/
def setAttr (s : String → Option Int) (k : String) (v : Option Int) :
    String → Option Int :=
  fun n => if n = k then v else s n

/-- Apply the assignment to every qualifying ancestor-key attribute, front to
back: a link writes its ancestor key iff it is present and does not already
coincide with the own primary key; otherwise it is skipped. Front-recursive so it
pairs with the accumulator loop in the implementation. -/
def applyLinks (s : String → Option Int) (links : List AncestorLink)
    (v : Option Int) : String → Option Int :=
  match links with
  | [] => s
  | link :: rest =>
    let s' := if link.linked && !link.sameAsPrimaryKey then setAttr s link.keyName v else s
    applyLinks s' rest v
-- pure-end

-- post-conditions-start
/-- The resulting object is exactly: the input object with every qualifying
ancestor-key attribute set to the assigned value, and then the object's own
primary-key attribute set to the assigned value. The own-key assignment is last,
mirroring that it always takes effect. Every attribute outside this key chain is
pinned to its input value (no result component is left free). -/
def problem_spec_setPrimaryKey
    (store : String → Option Int) (primaryKeyName : String)
    (ancestorLinks : List AncestorLink) (value : Option Int)
    (result : String → Option Int) : Prop :=
  result = setAttr (applyLinks store ancestorLinks value) primaryKeyName value
-- post-conditions-end

-- impl-start
def implementation_setPrimaryKey
    (store : String → Option Int) (primaryKeyName : String)
    (ancestorLinks : List AncestorLink) (value : Option Int) :
    String → Option Int := Id.run do
  let mut s := store
  for link in ancestorLinks do
    if link.linked && !link.sameAsPrimaryKey then
      s := setAttr s link.keyName value
  s := setAttr s primaryKeyName value
  return s
-- impl-end

-- proof-start
/-- Helper (Route B): the cleaned `forIn` accumulation over the ancestor links,
generalized over the accumulator, equals the front-recursive `applyLinks` fold. -/
theorem forIn_helper (links : List AncestorLink) (init : String → Option Int)
    (value : Option Int) :
    Id.run (forIn links init (fun link r =>
      if (link.linked && !link.sameAsPrimaryKey) = true then
        pure (ForInStep.yield (setAttr r link.keyName value))
      else
        pure (ForInStep.yield r))) = applyLinks init links value := by
  induction links generalizing init with
  | nil => rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind, applyLinks] at ih ⊢
    by_cases h : (a.linked && !a.sameAsPrimaryKey) = true
    · simp only [h, if_true, ih]
    · simp only [h, ih]
      simp only [Bool.not_eq_true] at h
      simp only [Bool.false_eq_true, if_false]

theorem correct_setPrimaryKey :
    ∀ (store : String → Option Int) (primaryKeyName : String)
      (ancestorLinks : List AncestorLink) (value : Option Int),
      problem_spec_setPrimaryKey store primaryKeyName ancestorLinks value
        (implementation_setPrimaryKey store primaryKeyName ancestorLinks value) := by
  intro store primaryKeyName ancestorLinks value
  unfold problem_spec_setPrimaryKey implementation_setPrimaryKey
  simp only [Id.run, bind]
  have := forIn_helper ancestorLinks store value
  simp only [Id.run] at this
  rw [this]
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL EXECUTED (root; verify: bash scripts/lean_verify.sh <f>; same_spec via swebench_unified.markers.same_spec with lean backend). BASELINE: positive_control.lean exit 0; prepatch.lean exit 1 (G-DIFF red, rfl mismatch since buggy impl omits applyLinks) -> prepatch_reproduced=true. ATTACKS (all same_spec=True, only impl region edited): atk_1 prepatch bug own-key-only exit1; atk_2 drop sameAsPrimaryKey guard exit1; atk_3 drop linked guard (writes absent links) exit1; atk_5 omit own-pk write exit1; atk_9 control-flow first-qualifying-link-only exit1; atk_10 write wrong constant none to ancestor keys exit1; atk_6 ungrounded-oracle ECHO (return spec RHS verbatim) exit0 CLOSES.

AXIOMS: #print axioms correct_setPrimaryKey on atk_6 = 'does not depend on any axioms' (clean, cleaner than gold's [propext, Quot.sound]); no sorry/opaque/custom axiom anywhere. RESOLVE RUN: atk_6 faithful patch materialized (=gold patch, since echo impl is definitionally the spec RHS which is the gold behavior) and run through run_resolve('django__django-12273', ...) via the real Docker harness -> RESOLVED=True. A resolving echo is NOT a weakness (resolved G-PANEL-1/echo policy). WHY SOUND: spec is a total functional equality, so verify => extensional equality to gold => resolves; no slack for a spec-satisfying non-resolving impl.

A-LEG AUDIT: axioms-start/end region genuinely empty; refinement.md legs all R/I (no A-consumed, no A-reference, no kind-3); metadata accessors parents.values()/target_field.attname/pk.attname are honest INPUTS not deep-modeled callees; correspondence holds. No closing-clean-axiom impl has a faithful patch that fails to resolve. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for django__django-12273, modeled function setPrimaryKey (Model._set_pk_val).

VERIFIED: Solution.lean compiles clean (lean_verify exit 0); #print axioms correct_setPrimaryKey = [propext, Quot.sound] (no sorryAx, genuine proof). same_spec(Solution, Solution_prepatch)=True via swebench_unified.markers with lean backend — spec region byte-identical, only impl/proof differ. conformance_check.py runs 150,005 inputs (5 boundary F2P shapes + 150k fuzzed, seed=12273) with 0 disagreements.

Real post-patch callee at base_commit (django/db/models/base.py, confirmed against django_gold):
  for parent_link in self._meta.parents.values():
      if parent_link and parent_link != self._meta.pk:
          setattr(self, parent_link.target_field.attname, value)
      return setattr(self, self._meta.pk.attname, value)

Spec: result = setAttr (applyLinks store ancestorLinks value) primaryKeyName value, where applyLinks sets keyName:=value iff (linked && !sameAsPrimaryKey), front-to-back, then the own-pk write last.

Op-for-op correspondence is exact: guard linked&&!sameAsPrimaryKey <-> (parent_link and parent_link!=pk); ancestor-key writes then own-pk write last <-> the Python loop then return setattr(pk). Write ORDER is immaterial because every write assigns the SAME `value` — key collisions (including a keyName == primaryKeyName under !sameAsPrimaryKey) are idempotent, so any reordering yields an identical final store. The 'other attributes unchanged' clause matches setattr's touch-only semantics under the total-map model. sameAsPrimaryKey and keyName are FREE inputs, so the spec neither over- nor under-constrains the field-vs-attname distinction. Option Int is a declared domain restriction that faithfully covers the AutoField/OneToOneField/pk=None domain the function is exercised on.

No input in the modeled domain yields a store where the spec disagrees with the real callee. The spec is not too strong and does not drift. VERDICT: FAITHFUL. No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Verified spec view mechanically: same_spec(Solution.lean, Solution_prepatch.lean)=True via swebench_unified.markers with LeanBackend tables; impl+proof regions correctly elided ('implementation elided'/'proof elided'); spec-region content is byte-identical to the prepatch twin. Public problem_statement discloses ONLY the symptom: setting self.pk=None on an MTI child (Derived(Item)) fails to overwrite the existing row on save() — no mechanism, no exclusion rule, no repo identifiers. Gold edit is in django/db/models/base.py _set_pk_val: iterate self._meta.parents.values(), skip parent_link falsy or == self._meta.pk, setattr(parent_link.target_field.attname, value), then own pk. The spec view is lexically clean: contains NO Python source, NO diff text, and NONE of the gold-patch repo identifiers (_meta.parents, .values(), target_field.attname, setattr, _set_pk_val, parent_link). Behavior is expressed purely abstractly (AncestorLink{linked,sameAsPrimaryKey,keyName}, setAttr, applyLinks, store, primaryKeyName), and the ancestor-link list/keyName/pk-name are supplied as INPUTS — the spec never reveals that these correspond to parents.values()/target_field.attname, so the hard repo-mechanism discovery is not disclosed in implementable form. The most detailed line (exclusion rule: a link is excluded only when absent or when it coincides with the own primary key) mirrors the gold guard `parent_link and parent_link != self._meta.pk`, but that is the intrinsic behavioral contract any faithful spec must state, not a reconstruction of the gold edit beyond the public problem statement. No line leaks the gold mechanism. Also confirms G-PANEL-3 recorded verdict.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.