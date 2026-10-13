# P2 adversarial audit — django__django-13964

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No same-spec wrong impl closes. The spec is a TOTAL functional equation: problem_spec pins result = (if fkValueIsEmpty fkValue then some objPk else fkValue), so correct_ = ∀ fkValue objPk, result = <deterministic RHS>. Any impl not extensionally equal to gold makes correct_ a FALSE proposition, and no proof can close it. The prepatch bug (atk_1) fails at exactly the discriminating goal: with hs : s.isEmpty = true it leaves ⊢ s = objPk (the empty-string / CharField-PK case exercised by test_save_fk_after_parent_with_non_numeric_pk_set_on_child). Since no wrong impl closes with clean axioms, there is no candidate patch to materialize/resolve, and none can exist that verifies-but-fails-resolve.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,10 +61,8 @@
 -- impl-start
 def implementation_foreignKeyValueOnSave
     (fkValue : Option String) (objPk : String) : Option String := Id.run do
-  -- start from the foreign-key field's currently stored key value
   let mut result := fkValue
-  -- when that stored value is still empty, adopt the related object's primary key
-  if fkValueIsEmpty result then
+  if result.isNone then
     result := some objPk
   return result
 -- impl-end
@@ -76,7 +74,8 @@
         (implementation_foreignKeyValueOnSave fkValue objPk) := by
   intro fkValue objPk
   unfold problem_spec_foreignKeyValueOnSave implementation_foreignKeyValueOnSave
-  by_cases h : fkValueIsEmpty fkValue
-  · simp only [Id.run, h, if_true]; rfl
-  · simp only [Id.run, h]; rfl
+  simp only [Id.run, bind, pure]
+  cases fkValue with
+  | none => simp [fkValueIsEmpty]
+  | some s => by_cases hs : s.isEmpty <;> simp [fkValueIsEmpty, hs]
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,12 +61,7 @@
 -- impl-start
 def implementation_foreignKeyValueOnSave
     (fkValue : Option String) (objPk : String) : Option String := Id.run do
-  -- start from the foreign-key field's currently stored key value
-  let mut result := fkValue
-  -- when that stored value is still empty, adopt the related object's primary key
-  if fkValueIsEmpty result then
-    result := some objPk
-  return result
+  return some objPk
 -- impl-end
 
 -- proof-start
@@ -76,7 +71,8 @@
         (implementation_foreignKeyValueOnSave fkValue objPk) := by
   intro fkValue objPk
   unfold problem_spec_foreignKeyValueOnSave implementation_foreignKeyValueOnSave
-  by_cases h : fkValueIsEmpty fkValue
-  · simp only [Id.run, h, if_true]; rfl
-  · simp only [Id.run, h]; rfl
+  simp only [Id.run, bind, pure]
+  cases fkValue with
+  | none => simp [fkValueIsEmpty]
+  | some s => by_cases hs : s.isEmpty <;> simp [fkValueIsEmpty, hs]
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,12 +61,7 @@
 -- impl-start
 def implementation_foreignKeyValueOnSave
     (fkValue : Option String) (objPk : String) : Option String := Id.run do
-  -- start from the foreign-key field's currently stored key value
-  let mut result := fkValue
-  -- when that stored value is still empty, adopt the related object's primary key
-  if fkValueIsEmpty result then
-    result := some objPk
-  return result
+  return fkValue
 -- impl-end
 
 -- proof-start
@@ -76,7 +71,8 @@
         (implementation_foreignKeyValueOnSave fkValue objPk) := by
   intro fkValue objPk
   unfold problem_spec_foreignKeyValueOnSave implementation_foreignKeyValueOnSave
-  by_cases h : fkValueIsEmpty fkValue
-  · simp only [Id.run, h, if_true]; rfl
-  · simp only [Id.run, h]; rfl
+  simp only [Id.run, bind, pure]
+  cases fkValue with
+  | none => simp [fkValueIsEmpty]
+  | some s => by_cases hs : s.isEmpty <;> simp [fkValueIsEmpty, hs]
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,11 +61,10 @@
 -- impl-start
 def implementation_foreignKeyValueOnSave
     (fkValue : Option String) (objPk : String) : Option String := Id.run do
-  -- start from the foreign-key field's currently stored key value
   let mut result := fkValue
-  -- when that stored value is still empty, adopt the related object's primary key
-  if fkValueIsEmpty result then
-    result := some objPk
+  match result with
+  | none => result := some objPk
+  | some s => if s.isEmpty || s = " " then result := some objPk
   return result
 -- impl-end
 
@@ -76,7 +75,8 @@
         (implementation_foreignKeyValueOnSave fkValue objPk) := by
   intro fkValue objPk
   unfold problem_spec_foreignKeyValueOnSave implementation_foreignKeyValueOnSave
-  by_cases h : fkValueIsEmpty fkValue
-  · simp only [Id.run, h, if_true]; rfl
-  · simp only [Id.run, h]; rfl
+  simp only [Id.run, bind, pure]
+  cases fkValue with
+  | none => simp [fkValueIsEmpty]
+  | some s => by_cases hs : s.isEmpty <;> simp [fkValueIsEmpty, hs]
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,10 +61,8 @@
 -- impl-start
 def implementation_foreignKeyValueOnSave
     (fkValue : Option String) (objPk : String) : Option String := Id.run do
-  -- start from the foreign-key field's currently stored key value
   let mut result := fkValue
-  -- when that stored value is still empty, adopt the related object's primary key
-  if fkValueIsEmpty result then
+  if objPk.isEmpty then
     result := some objPk
   return result
 -- impl-end
@@ -76,7 +74,8 @@
         (implementation_foreignKeyValueOnSave fkValue objPk) := by
   intro fkValue objPk
   unfold problem_spec_foreignKeyValueOnSave implementation_foreignKeyValueOnSave
-  by_cases h : fkValueIsEmpty fkValue
-  · simp only [Id.run, h, if_true]; rfl
-  · simp only [Id.run, h]; rfl
+  simp only [Id.run, bind, pure]
+  cases fkValue with
+  | none => simp [fkValueIsEmpty]
+  | some s => by_cases hs : s.isEmpty <;> simp [fkValueIsEmpty, hs]
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,10 +61,8 @@
 -- impl-start
 def implementation_foreignKeyValueOnSave
     (fkValue : Option String) (objPk : String) : Option String := Id.run do
-  -- start from the foreign-key field's currently stored key value
   let mut result := fkValue
-  -- when that stored value is still empty, adopt the related object's primary key
-  if fkValueIsEmpty result then
+  if ! fkValueIsEmpty result then
     result := some objPk
   return result
 -- impl-end
@@ -76,7 +74,8 @@
         (implementation_foreignKeyValueOnSave fkValue objPk) := by
   intro fkValue objPk
   unfold problem_spec_foreignKeyValueOnSave implementation_foreignKeyValueOnSave
-  by_cases h : fkValueIsEmpty fkValue
-  · simp only [Id.run, h, if_true]; rfl
-  · simp only [Id.run, h]; rfl
+  simp only [Id.run, bind, pure]
+  cases fkValue with
+  | none => simp [fkValueIsEmpty]
+  | some s => by_cases hs : s.isEmpty <;> simp [fkValueIsEmpty, hs]
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,11 +61,9 @@
 -- impl-start
 def implementation_foreignKeyValueOnSave
     (fkValue : Option String) (objPk : String) : Option String := Id.run do
-  -- start from the foreign-key field's currently stored key value
   let mut result := fkValue
-  -- when that stored value is still empty, adopt the related object's primary key
   if fkValueIsEmpty result then
-    result := some objPk
+    result := some ""
   return result
 -- impl-end
 
@@ -76,7 +74,8 @@
         (implementation_foreignKeyValueOnSave fkValue objPk) := by
   intro fkValue objPk
   unfold problem_spec_foreignKeyValueOnSave implementation_foreignKeyValueOnSave
-  by_cases h : fkValueIsEmpty fkValue
-  · simp only [Id.run, h, if_true]; rfl
-  · simp only [Id.run, h]; rfl
+  simp only [Id.run, bind, pure]
+  cases fkValue with
+  | none => simp [fkValueIsEmpty]
+  | some s => by_cases hs : s.isEmpty <;> simp [fkValueIsEmpty, hs]
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Adopting a related object's primary key into a foreign-key field when a model is
saved.

A model instance can hold a foreign-key relation to another, not-yet-persisted
object. The foreign-key field stores a *key value* (the scalar that mirrors the
related object's primary key); separately, the related object carries its own
primary key.

When the owning model is saved and the related object already has a primary key,
the owning model must end up referencing that primary key. The subtlety is the
condition under which the stored key value is (re)adopted from the related
object: it must be adopted whenever the stored key value is still *empty* — both
the absent value and an empty scalar (such as the empty string) count as empty.
A non-empty stored key value is left untouched. This guarantees that a foreign
key to an object whose primary key is a non-numeric (e.g. string) value is
populated with that primary key rather than left holding an empty placeholder.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The emptiness
-- test on a stored foreign-key value and the adoption of the related object's
-- primary key are both modeled directly (an `Option String` carrier with an
-- explicit emptiness predicate), so no `opaque`/`axiom` callee contract is
-- required.
-- axioms-end

-- pure-start
/-- A stored foreign-key value counts as *empty* when it is absent (`none`) or
is an empty scalar (the empty string). A present, non-empty value is not empty.
This mirrors the membership of a scalar key value in the set of empty values
recognised for a field (the absent value and the empty string being the cases a
foreign-key scalar can take). -/
def fkValueIsEmpty (v : Option String) : Bool :=
  match v with
  | none   => true
  | some s => s.isEmpty
-- pure-end

-- post-conditions-start
/-- After preparing a cached foreign-key relation for save, the stored key value
is the related object's primary key `objPk` when the stored value `fkValue` is
empty, and is `fkValue` itself otherwise.

Directive 5 (frame): the result is pinned entirely to the two inputs — the
stored value `fkValue` and the related object's primary key `objPk`; nothing is
left unconstrained.

The binder precondition (in `correct_*`) is that the related object already has
a primary key, modeled by `objPk : String` always being a present value (the
prepare step only reaches this adoption decision once the related object's
primary key is known to be present). -/
def problem_spec_foreignKeyValueOnSave
    (fkValue : Option String) (objPk : String) (result : Option String) : Prop :=
  result = (if fkValueIsEmpty fkValue then some objPk else fkValue)
-- post-conditions-end

-- impl-start
def implementation_foreignKeyValueOnSave
    (fkValue : Option String) (objPk : String) : Option String :=
  if fkValueIsEmpty fkValue then some objPk else fkValue
-- impl-end

-- proof-start
theorem correct_foreignKeyValueOnSave :
    ∀ (fkValue : Option String) (objPk : String),
      problem_spec_foreignKeyValueOnSave fkValue objPk
        (implementation_foreignKeyValueOnSave fkValue objPk) := by
  intro fkValue objPk
  unfold problem_spec_foreignKeyValueOnSave implementation_foreignKeyValueOnSave
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SAME-SPEC: all 7 attacks + positive control confirmed same_spec=True via swebench_unified.markers.same_spec (lean backend). Each file edits ONLY impl+proof regions (both elided from spec_view); axioms/pure/pre/post kept byte-identical (generated from head -n 61 Solution.lean).

### COMMANDS (run concurrently, ≤4 background jobs per batch):
  bash scripts/lean_verify.sh <D>/atk_N.lean
### RESULTS (exit codes; 0=verifies/no-sorry, 1=error/unsolved):
  atk_1 (prepatch bug, adopt only on isNone) exit=1 — unsolved goal 's.isEmpty=true ⊢ s = objPk'
  atk_2 (always adopt objPk)                 exit=1
  atk_3 (identity, never adopt)              exit=1
  atk_4 (boundary: treat " " as empty)       exit=1
  atk_5 (branch on objPk.isEmpty)            exit=1
  atk_6 (inverted guard: adopt when non-empty) exit=1
  atk_7 (ungrounded echo: empty -> some "")  exit=1
  pos_control (correct if-expr impl)         exit=0
  pos_ax.lean (pos_control + #print axioms)  exit=0 -> "'correct_foreignKeyValueOnSave' does not depend on any axioms" (CLEAN axioms)

STEP 2 (resolve): NO wrong impl closed with clean axioms, so there is nothing to materialize/resolve. run_resolve not invoked (correctly — nothing to run). Not INCONCLUSIVE: the absence of a resolve run is because zero attacks passed verification, not because a needed run couldn't complete.

STEP 3 (refinement.md A-leg audit): axiom_check.py is a SKIP stub; refinement.md declares axioms=[], deep_model_references=[]. All 6 legs tagged R/I (no kind-3, no A-consumed/A-reference). The ONLY deep-model correspondence to audit is fkValueIsEmpty <-> (getattr(self, field.attname) in field.empty_values). This is SOUND: field.empty_values = [None, '', [], (), {}]; for a scalar string FK key value the reachable members are exactly None and '' (lists/tuples/dicts unreachable for a scalar), so the membership test == (v is None or v == '') == fkValueIsEmpty (none=>true, some s=>s.isEmpty). Guard change is None -> in empty_values maps faithfully to isNone -> fkValueIsEmpty. G-CONF (conformance_check.py) independently differential-tests the R/I shadow vs a post-patch replica over the full stored-value x pk grid + 120k fuzz (0 disagreements, seed 13964).

WHY SOUND / no falsification possible: because the spec fully determines result as a function of both inputs, verify => extensional equality with gold => resolve. There is no room for a verifying-but-incorrect impl. prepatch_reproduced=true: the prepatch impl (atk_1) is genuinely rejected by the post-patch spec at the empty-string case.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No same-spec wrong impl closes. The spec is a TOTAL functional equation: problem_spec pins result = (if fkValueIsEmpty fkValue then some objPk else fkValue), so correct_ = ∀ fkValue objPk, result = <deterministic RHS>. Any impl not extensionally equal to gold makes correct_ a FALSE proposition, and no proof can close it. The prepatch bug (atk_1) fails at exactly the discriminating goal: with hs : s.isEmpty = true it leaves ⊢ s = objPk (the empty-string / CharField-PK case exercised by test_save_fk_after_parent_with_non_numeric_pk_set_on_child). Since no wrong impl closes with clean axioms, there is no candidate patch to materialize/resolve, and none can exist that verifies-but-fails-resolve.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Adopting a related object's primary key into a foreign-key field when a model is
saved.

A model instance can hold a foreign-key relation to another, not-yet-persisted
object. The foreign-key field stores a *key value* (the scalar that mirrors the
related object's primary key); separately, the related object carries its own
primary key.

When the owning model is saved and the related object already has a primary key,
the owning model must end up referencing that primary key. The subtlety is the
condition under which the stored key value is (re)adopted from the related
object: it must be adopted whenever the stored key value is still *empty* — both
the absent value and an empty scalar (such as the empty string) count as empty.
A non-empty stored key value is left untouched. This guarantees that a foreign
key to an object whose primary key is a non-numeric (e.g. string) value is
populated with that primary key rather than left holding an empty placeholder.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The emptiness
-- test on a stored foreign-key value and the adoption of the related object's
-- primary key are both modeled directly (an `Option String` carrier with an
-- explicit emptiness predicate), so no `opaque`/`axiom` callee contract is
-- required.
-- axioms-end

-- pure-start
/-- A stored foreign-key value counts as *empty* when it is absent (`none`) or
is an empty scalar (the empty string). A present, non-empty value is not empty.
This mirrors the membership of a scalar key value in the set of empty values
recognised for a field (the absent value and the empty string being the cases a
foreign-key scalar can take). -/
def fkValueIsEmpty (v : Option String) : Bool :=
  match v with
  | none   => true
  | some s => s.isEmpty
-- pure-end

-- post-conditions-start
/-- After preparing a cached foreign-key relation for save, the stored key value
is the related object's primary key `objPk` when the stored value `fkValue` is
empty, and is `fkValue` itself otherwise.

Directive 5 (frame): the result is pinned entirely to the two inputs — the
stored value `fkValue` and the related object's primary key `objPk`; nothing is
left unconstrained.

The binder precondition (in `correct_*`) is that the related object already has
a primary key, modeled by `objPk : String` always being a present value (the
prepare step only reaches this adoption decision once the related object's
primary key is known to be present). -/
def problem_spec_foreignKeyValueOnSave
    (fkValue : Option String) (objPk : String) (result : Option String) : Prop :=
  result = (if fkValueIsEmpty fkValue then some objPk else fkValue)
-- post-conditions-end

-- impl-start
def implementation_foreignKeyValueOnSave
    (fkValue : Option String) (objPk : String) : Option String :=
  if fkValueIsEmpty fkValue then some objPk else fkValue
-- impl-end

-- proof-start
theorem correct_foreignKeyValueOnSave :
    ∀ (fkValue : Option String) (objPk : String),
      problem_spec_foreignKeyValueOnSave fkValue objPk
        (implementation_foreignKeyValueOnSave fkValue objPk) := by
  intro fkValue objPk
  unfold problem_spec_foreignKeyValueOnSave implementation_foreignKeyValueOnSave
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SAME-SPEC: all 7 attacks + positive control confirmed same_spec=True via swebench_unified.markers.same_spec (lean backend). Each file edits ONLY impl+proof regions (both elided from spec_view); axioms/pure/pre/post kept byte-identical (generated from head -n 61 Solution.lean).

### COMMANDS (run concurrently, ≤4 background jobs per batch):
  bash scripts/lean_verify.sh <D>/atk_N.lean
### RESULTS (exit codes; 0=verifies/no-sorry, 1=error/unsolved):
  atk_1 (prepatch bug, adopt only on isNone) exit=1 — unsolved goal 's.isEmpty=true ⊢ s = objPk'
  atk_2 (always adopt objPk)                 exit=1
  atk_3 (identity, never adopt)              exit=1
  atk_4 (boundary: treat " " as empty)       exit=1
  atk_5 (branch on objPk.isEmpty)            exit=1
  atk_6 (inverted guard: adopt when non-empty) exit=1
  atk_7 (ungrounded echo: empty -> some "")  exit=1
  pos_control (correct if-expr impl)         exit=0
  pos_ax.lean (pos_control + #print axioms)  exit=0 -> "'correct_foreignKeyValueOnSave' does not depend on any axioms" (CLEAN axioms)

STEP 2 (resolve): NO wrong impl closed with clean axioms, so there is nothing to materialize/resolve. run_resolve not invoked (correctly — nothing to run). Not INCONCLUSIVE: the absence of a resolve run is because zero attacks passed verification, not because a needed run couldn't complete.

STEP 3 (refinement.md A-leg audit): axiom_check.py is a SKIP stub; refinement.md declares axioms=[], deep_model_references=[]. All 6 legs tagged R/I (no kind-3, no A-consumed/A-reference). The ONLY deep-model correspondence to audit is fkValueIsEmpty <-> (getattr(self, field.attname) in field.empty_values). This is SOUND: field.empty_values = [None, '', [], (), {}]; for a scalar string FK key value the reachable members are exactly None and '' (lists/tuples/dicts unreachable for a scalar), so the membership test == (v is None or v == '') == fkValueIsEmpty (none=>true, some s=>s.isEmpty). Guard change is None -> in empty_values maps faithfully to isNone -> fkValueIsEmpty. G-CONF (conformance_check.py) independently differential-tests the R/I shadow vs a post-patch replica over the full stored-value x pk grid + 120k fuzz (0 disagreements, seed 13964).

WHY SOUND / no falsification possible: because the spec fully determines result as a function of both inputs, verify => extensional equality with gold => resolve. There is no room for a verifying-but-incorrect impl. prepatch_reproduced=true: the prepatch impl (atk_1) is genuinely rejected by the post-patch spec at the empty-string case.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found NO diverging input. Modeled callee = the FK key-value adoption decision in Model._prepare_related_fields_for_save (post-patch, django/db/models/base.py:936): `elif getattr(self, field.attname) in field.empty_values: setattr(self, field.attname, obj.pk)`, else the stored scalar is unchanged. Confirmed against at base_commit f39634ff22: EMPTY_VALUES=(None,'',[],(),{}) (core/validators.py:16), field.empty_values=list(validators.EMPTY_VALUES) (fields/__init__.py:91). Branch reached only when obj truthy and obj.pk is not None, so objPk is a present string.

Spec: result = if fkValueIsEmpty fkValue then some objPk else fkValue; fkValueIsEmpty(none)=true, fkValueIsEmpty(some s)=s.isEmpty. Modeled domain: fkValue:Option String (scalar FK column, None or string), objPk present.

Exhaustive point-by-point agreement over the modeled domain:
- fkValue=none(None): real adopts (None in empty_values) -> some objPk; spec -> some objPk. AGREE.
- fkValue=some ""(''): real adopts ('' in empty_values) -> some objPk; spec -> some objPk. AGREE (fixed data-loss case; F2P test_save_fk_after_parent_with_non_numeric_pk_set_on_child).
- fkValue=some s, s!="": real leaves unchanged (s not in empty_values, since for a string s, s in empty_values <=> s==''); spec -> fkValue. AGREE.

Break vectors attempted and rejected: (a) list/tuple/dict members of empty_values are unreachable for a scalar FK key value -> outside modeled domain, not drift; (b) numeric-PK FK (product_id int or None) -> None case still agrees, ints are never == None/'' so never empty, consistent; (c) not too-strong (never demands adoption on a nonempty value), not too-weak (demands adoption on every empty incl. some ""). The fkValueIsEmpty model exactly equals the real `x in field.empty_values` membership restricted to the scalar's reachable values.

Mechanical checks: swebench_unified.markers.same_spec(Solution, prepatch)=True and spec_view hash = 3fff35766e199d13378d669858c302c8b3471771b161a9bf28930b37c5512ac7 matching meta.json region_hashes. Solution.lean compiles via scripts/lean_verify.sh (exit 0). #print axioms correct_foreignKeyValueOnSave = [propext] only (no sorryAx; proof is genuine). Solution_prepatch.lean (guard = result.isNone, the pre-patch `is None` behavior) fails G-DIFF as expected on fkValue=some "". Spec is a tight biconditional pinned to both inputs; faithful to the real post-patch callee on the entire modeled domain.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** same_spec(Solution.lean, Solution_prepatch.lean, lean) = True, so the spec-region view I judged is authoritative. Gold edit: guard `getattr(self, field.attname) is None` -> `... in field.empty_values`, i.e. the stored FK key value must adopt the related object's pk whenever it is empty (None OR empty string), not just None.

The public problem_statement already discloses the operative facts: a ForeignKey to a model with a non-auto CharField primary key; an empty related instance whose pk is set later; `product_id` ending up as the empty string "" "but shouldn't", when it should be "populated with product.sku" (the related pk). Thus the *correct behavior* — that an empty-string FK value must adopt the related pk — is directly derivable from public text, independent of the spec.

The spec view (docstring + `pure` fkValueIsEmpty + `post-conditions`) states only abstract behavior: adopt objPk when the stored key value is empty where 'both the absent value and an empty scalar (such as the empty string) count as empty', leave non-empty untouched, populate with the primary key 'rather than left holding an empty placeholder', 'non-numeric (e.g. string) value'. Each of these maps to something already public (empty string vs sku; non-numeric CharField PK). A spec must state the intended correct behavior; restating it abstractly is not leakage.

Crucially the spec view does NOT expose anything beyond the public statement that would reconstruct the gold: no patched file (django/db/models/base.py), no function (_prepare_related_fields_for_save), no changed symbols (field.empty_values, field.attname, getattr/setattr), no gold-diff line/marker, and no narration of the `is None` -> `in empty_values` guard-edit mechanism. The G-LEAK lexical screen (meta.json: 'spec view clean', failures=[]) is consistent. Nothing in the spec view leaks the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
