# P2 adversarial audit — django__django-11880

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_5.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_4.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -84,18 +84,10 @@
 -- post-conditions-end
 
 -- impl-start
--- Build the duplicate. Start from a shallow copy of the original (every
--- component initially the SAME object), then replace each mutable container with
--- a freshly allocated object that carries the same contents: the widget gets
--- fresh identity fw; the error-message mapping gets fresh identity fe with the
--- original's contents; the validator list gets fresh identity fv with the
--- original's contents. The immutable scalar is left as carried by the shallow
--- copy.
 def implementation_duplicateField
     (self : FormField) (fw fe fv : ObjId) : FormField := Id.run do
   let mut result := self
   result := { result with widgetId := fw }
-  result := { result with errMsgId := fe, errMsg := self.errMsg }
   result := { result with validId := fv, validators := self.validators }
   return result
 -- impl-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -84,20 +84,9 @@
 -- post-conditions-end
 
 -- impl-start
--- Build the duplicate. Start from a shallow copy of the original (every
--- component initially the SAME object), then replace each mutable container with
--- a freshly allocated object that carries the same contents: the widget gets
--- fresh identity fw; the error-message mapping gets fresh identity fe with the
--- original's contents; the validator list gets fresh identity fv with the
--- original's contents. The immutable scalar is left as carried by the shallow
--- copy.
 def implementation_duplicateField
-    (self : FormField) (fw fe fv : ObjId) : FormField := Id.run do
-  let mut result := self
-  result := { result with widgetId := fw }
-  result := { result with errMsgId := fe, errMsg := self.errMsg }
-  result := { result with validId := fv, validators := self.validators }
-  return result
+    (self : FormField) (fw fe fv : ObjId) : FormField :=
+  { self with errMsgId := fe, errMsg := self.errMsg, validId := fv, validators := self.validators }
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -84,20 +84,9 @@
 -- post-conditions-end
 
 -- impl-start
--- Build the duplicate. Start from a shallow copy of the original (every
--- component initially the SAME object), then replace each mutable container with
--- a freshly allocated object that carries the same contents: the widget gets
--- fresh identity fw; the error-message mapping gets fresh identity fe with the
--- original's contents; the validator list gets fresh identity fv with the
--- original's contents. The immutable scalar is left as carried by the shallow
--- copy.
 def implementation_duplicateField
-    (self : FormField) (fw fe fv : ObjId) : FormField := Id.run do
-  let mut result := self
-  result := { result with widgetId := fw }
-  result := { result with errMsgId := fe, errMsg := self.errMsg }
-  result := { result with validId := fv, validators := self.validators }
-  return result
+    (self : FormField) (fw fe fv : ObjId) : FormField :=
+  { self with widgetId := fw, errMsgId := fe, errMsg := [], validId := fv, validators := self.validators }
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -84,20 +84,10 @@
 -- post-conditions-end
 
 -- impl-start
--- Build the duplicate. Start from a shallow copy of the original (every
--- component initially the SAME object), then replace each mutable container with
--- a freshly allocated object that carries the same contents: the widget gets
--- fresh identity fw; the error-message mapping gets fresh identity fe with the
--- original's contents; the validator list gets fresh identity fv with the
--- original's contents. The immutable scalar is left as carried by the shallow
--- copy.
 def implementation_duplicateField
-    (self : FormField) (fw fe fv : ObjId) : FormField := Id.run do
-  let mut result := self
-  result := { result with widgetId := fw }
-  result := { result with errMsgId := fe, errMsg := self.errMsg }
-  result := { result with validId := fv, validators := self.validators }
-  return result
+    (self : FormField) (fw fe fv : ObjId) : FormField :=
+  { self with widgetId := fw, errMsgId := fe, errMsg := self.errMsg.reverse.reverse,
+              validId := fv, validators := self.validators }
 -- impl-end
 
 -- proof-start
@@ -108,5 +98,5 @@
         (implementation_duplicateField self fw fe fv) := by
   intro self fw fe fv _ _ _
   unfold problem_spec_duplicateField implementation_duplicateField
-  refine ⟨rfl, rfl, rfl, rfl, rfl, rfl⟩
+  simp [List.reverse_reverse]
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -84,20 +84,11 @@
 -- post-conditions-end
 
 -- impl-start
--- Build the duplicate. Start from a shallow copy of the original (every
--- component initially the SAME object), then replace each mutable container with
--- a freshly allocated object that carries the same contents: the widget gets
--- fresh identity fw; the error-message mapping gets fresh identity fe with the
--- original's contents; the validator list gets fresh identity fv with the
--- original's contents. The immutable scalar is left as carried by the shallow
--- copy.
 def implementation_duplicateField
-    (self : FormField) (fw fe fv : ObjId) : FormField := Id.run do
-  let mut result := self
-  result := { result with widgetId := fw }
-  result := { result with errMsgId := fe, errMsg := self.errMsg }
-  result := { result with validId := fv, validators := self.validators }
-  return result
+    (self : FormField) (fw fe fv : ObjId) : FormField :=
+  let e := if fe = self.errMsgId then self.errMsgId else fe
+  { self with widgetId := fw, errMsgId := e, errMsg := self.errMsg,
+              validId := fv, validators := self.validators }
 -- impl-end
 
 -- proof-start
@@ -106,7 +97,8 @@
       fw ≠ self.widgetId → fe ≠ self.errMsgId → fv ≠ self.validId →
       problem_spec_duplicateField self fw fe fv
         (implementation_duplicateField self fw fe fv) := by
-  intro self fw fe fv _ _ _
+  intro self fw fe fv _ hfe _
   unfold problem_spec_duplicateField implementation_duplicateField
+  simp only [if_neg hfe]
   refine ⟨rfl, rfl, rfl, rfl, rfl, rfl⟩
 -- proof-end
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -84,20 +84,11 @@
 -- post-conditions-end
 
 -- impl-start
--- Build the duplicate. Start from a shallow copy of the original (every
--- component initially the SAME object), then replace each mutable container with
--- a freshly allocated object that carries the same contents: the widget gets
--- fresh identity fw; the error-message mapping gets fresh identity fe with the
--- original's contents; the validator list gets fresh identity fv with the
--- original's contents. The immutable scalar is left as carried by the shallow
--- copy.
 def implementation_duplicateField
-    (self : FormField) (fw fe fv : ObjId) : FormField := Id.run do
-  let mut result := self
-  result := { result with widgetId := fw }
-  result := { result with errMsgId := fe, errMsg := self.errMsg }
-  result := { result with validId := fv, validators := self.validators }
-  return result
+    (self : FormField) (fw fe fv : ObjId) : FormField :=
+  let r0 : FormField := { self with validId := fv, validators := self.validators }
+  let r1 : FormField := { r0 with errMsgId := fe, errMsg := self.errMsg }
+  { r1 with widgetId := fw }
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -84,20 +84,10 @@
 -- post-conditions-end
 
 -- impl-start
--- Build the duplicate. Start from a shallow copy of the original (every
--- component initially the SAME object), then replace each mutable container with
--- a freshly allocated object that carries the same contents: the widget gets
--- fresh identity fw; the error-message mapping gets fresh identity fe with the
--- original's contents; the validator list gets fresh identity fv with the
--- original's contents. The immutable scalar is left as carried by the shallow
--- copy.
 def implementation_duplicateField
-    (self : FormField) (fw fe fv : ObjId) : FormField := Id.run do
-  let mut result := self
-  result := { result with widgetId := fw }
-  result := { result with errMsgId := fe, errMsg := self.errMsg }
-  result := { result with validId := fv, validators := self.validators }
-  return result
+    (self : FormField) (fw fe fv : ObjId) : FormField :=
+  { self with widgetId := fw, errMsgId := fe, errMsg := self.errMsg,
+              validators := self.validators }
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Duplicating a form field into an independent copy.

A form field bundles several components. Some are immutable scalars (modeled
here by `required`). Others are mutable containers — a widget object, a mapping
of error codes to messages, and a list of validators — each of which is a
distinct runtime object with its own identity (`ObjId`) in addition to its
contents.

Producing a duplicate of a field must yield a copy that is fully independent of
the original: each of its mutable containers is its OWN object, distinct in
identity from the original's, while carrying the SAME contents. Concretely, the
duplicate's widget, error-message mapping, and validator list must each be a
fresh object (a new identity), the error-message mapping and validator list must
have contents equal to the original's, and the immutable scalar components must
be preserved unchanged.

This independence is what lets two duplicates of one field be mutated in
isolation: changing one duplicate's error-message mapping must never be visible
through the other.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The duplication
-- of each mutable container (allocating a fresh object that carries the same
-- contents) and the preservation of the immutable scalar are modeled
-- structurally over the field's components, so no `opaque`/`axiom` callee
-- contract is needed.
-- axioms-end

-- pure-start
/-- A runtime object's identity. Modeled as a `Nat` (an injective encoding of
the distinct object identities; only equality is observed). Two values are the
SAME object iff their `ObjId`s are equal. -/
abbrev ObjId := Nat

/-- An error-code → message mapping, restricted to its observable contents.
Codes and messages are distinct strings, modeled by injective `Nat` encodings;
only equality of contents is observed. -/
abbrev MsgDict := List (Nat × Nat)

/-- A form field, restricted to the touched components:
* `widgetId`  — the identity of the field's widget object;
* `errMsgId`  — the identity of the error-message mapping object;
* `errMsg`    — the contents of that mapping;
* `validId`   — the identity of the validator-list object;
* `validators`— the contents of that list;
* `required`  — a representative immutable scalar component. -/
structure FormField where
  widgetId : ObjId
  errMsgId : ObjId
  errMsg : MsgDict
  validId : ObjId
  validators : List Nat
  required : Bool
deriving DecidableEq
-- pure-end

-- post-conditions-start
/-- The duplicate is independent of the original. Given the fresh object
identities `fw`, `fe`, `fv` produced when allocating the duplicate's widget,
error-message mapping, and validator list:

* each mutable container of the result carries its OWN (fresh) identity
  (`fw`, `fe`, `fv` respectively), so it is a distinct object from the
  original's container;
* the error-message mapping and the validator list have contents EQUAL to the
  original's (the copy preserves contents);
* the immutable scalar component is preserved unchanged.

The freshness of `fw`/`fe`/`fv` (distinctness from the original's identities) is
a precondition of `correct_duplicateField`. -/
def problem_spec_duplicateField
    (self : FormField) (fw fe fv : ObjId) (result : FormField) : Prop :=
  result.widgetId = fw ∧
  result.errMsgId = fe ∧
  result.errMsg = self.errMsg ∧
  result.validId = fv ∧
  result.validators = self.validators ∧
  result.required = self.required
-- post-conditions-end

-- impl-start
-- Build the duplicate. Start from a shallow copy of the original (every
-- component initially the SAME object), then replace each mutable container with
-- a freshly allocated object that carries the same contents: the widget gets
-- fresh identity fw; the error-message mapping gets fresh identity fe with the
-- original's contents; the validator list gets fresh identity fv with the
-- original's contents. The immutable scalar is left as carried by the shallow
-- copy.
def implementation_duplicateField
    (self : FormField) (fw fe fv : ObjId) : FormField := Id.run do
  let mut result := self
  result := { result with widgetId := fw }
  result := { result with errMsgId := fe, errMsg := self.errMsg }
  result := { result with validId := fv, validators := self.validators }
  return result
-- impl-end

-- proof-start
theorem correct_duplicateField :
    ∀ (self : FormField) (fw fe fv : ObjId),
      fw ≠ self.widgetId → fe ≠ self.errMsgId → fv ≠ self.validId →
      problem_spec_duplicateField self fw fe fv
        (implementation_duplicateField self fw fe fv) := by
  intro self fw fe fv _ _ _
  unfold problem_spec_duplicateField implementation_duplicateField
  refine ⟨rfl, rfl, rfl, rfl, rfl, rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC IS A TOTAL FUNCTIONAL SPEC. problem_spec_duplicateField pins ALL 6 result fields to exact values on the entire precondition domain (fw!=widgetId, fe!=errMsgId, fv!=validId): result.widgetId=fw, errMsgId=fe, errMsg=self.errMsg, validId=fv, validators=self.validators, required=self.required. Hence any impl whose correct_ proof closes is behaviorally IDENTICAL to gold on the whole domain; its faithful refined patch IS the gold patch, which resolves. No closing clean-axiom impl exists whose faithful patch fails to resolve.

### ATTACK BATTERY (cmd: `bash scripts/lean_verify.sh <file>`; all same_spec=True via swebench_unified.markers.same_spec, verified):
- atk_1 PREPATCH BUG (omit fresh error-message id; errMsgId stays shared) -> exit 1, proof CANNOT close (fe=self.errMsgId unprovable). Prepatch bug reproduced & correctly rejected by the spec.
- atk_2 shared WIDGET identity (widgetId:=self.widgetId) -> exit 1 (rejected; fw clause fails).
- atk_3 WRONG error-message CONTENTS (errMsg:=[]) -> exit 1 (rejected; errMsg clause fails).
- atk_4 BOUNDARY / gold-equivalent (errMsg:=self.errMsg.reverse.reverse, proved equal via List.reverse_reverse) -> exit 0; `#print axioms correct_duplicateField` => depends on [propext] (clean, standard). CLOSES.
- atk_5 PARTIAL-DOMAIN / control-flow-effect (reproduce prepatch alias ONLY off-domain when fe=errMsgId) -> exit 1 (my chosen closing tactic did not discharge; impl is gold-equivalent on-domain anyway since precondition fe!=errMsgId forces the fresh branch, so no falsification available).
- atk_6 UNGROUNDED-ORACLE ECHO / reordered record build (validators->errMsg->widget) -> exit 0; `#print axioms` => does not depend on any axioms (clean). CLOSES.
- atk_7 shared VALIDATORS identity (validId:=self.validId) -> exit 1 (rejected; fv clause fails).
- pos POSITIVE CONTROL (canonical gold impl) -> exit 0, no axioms. VERIFIES.

RESOLVE RUNS (cmd: run_resolve('django__django-11880', patch) via swebench_unified.harness; docker oracle, benchmark swe_bench_verified):
- GOLD patch (faithful refined patch of every closing impl atk_4/atk_6/pos, since they are gold-equivalent) -> resolved=True, note='resolved'. POSITIVE control confirms harness discriminates & correctness oracle works.
- NOOP non-fixing patch (comment only, error_messages.copy() line ABSENT, bug remains) -> resolved=False, note='patch did not resolve in 3 attempts (consistent - not flaky)'. NEGATIVE control confirms the F2P test (assertIsNot(field_copy.error_messages, field.error_messages)) actually gates resolution.
- (empty patch -> 'no report'/harness-reject, not a usable signal; superseded by the noop negative control above.)

REFINEMENT.md AUDIT: all 7 legs tagged R (1-6) or I (7); ZERO A-legs. Solution.lean has NO opaque/axiom declarations (grep -E '^\s*(opaque|axiom)' => none), so there is no A-consumed/A-reference correspondence to validate. axiom_check.py is a legitimate G-AX skip stub (deeply-modeled changed decision, not axiomatized). No kind-3 (ungrounded) legs: every clause of problem_spec is grounded in self's components or the freshly-supplied identities fw/fe/fv. mapping.md Lean<->Python bijection is faithful (id()/is <-> ObjId equality; dict.copy()/list-slice/deepcopy modeled as fresh identity + preserved contents).

CONCLUSION: verify => correct holds. The discriminating clause result.errMsgId=fe under precondition fe!=self.errMsgId exactly captures the F2P assertIsNot; the prepatch alias makes correct_ unprovable (confirmed by atk_1). All 7 attacks fully verified; both needed resolve runs (positive gold + negative noop) executed and reported. Nothing broke the spec => SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_5.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_4.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Duplicating a form field into an independent copy.

A form field bundles several components. Some are immutable scalars (modeled
here by `required`). Others are mutable containers — a widget object, a mapping
of error codes to messages, and a list of validators — each of which is a
distinct runtime object with its own identity (`ObjId`) in addition to its
contents.

Producing a duplicate of a field must yield a copy that is fully independent of
the original: each of its mutable containers is its OWN object, distinct in
identity from the original's, while carrying the SAME contents. Concretely, the
duplicate's widget, error-message mapping, and validator list must each be a
fresh object (a new identity), the error-message mapping and validator list must
have contents equal to the original's, and the immutable scalar components must
be preserved unchanged.

This independence is what lets two duplicates of one field be mutated in
isolation: changing one duplicate's error-message mapping must never be visible
through the other.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The duplication
-- of each mutable container (allocating a fresh object that carries the same
-- contents) and the preservation of the immutable scalar are modeled
-- structurally over the field's components, so no `opaque`/`axiom` callee
-- contract is needed.
-- axioms-end

-- pure-start
/-- A runtime object's identity. Modeled as a `Nat` (an injective encoding of
the distinct object identities; only equality is observed). Two values are the
SAME object iff their `ObjId`s are equal. -/
abbrev ObjId := Nat

/-- An error-code → message mapping, restricted to its observable contents.
Codes and messages are distinct strings, modeled by injective `Nat` encodings;
only equality of contents is observed. -/
abbrev MsgDict := List (Nat × Nat)

/-- A form field, restricted to the touched components:
* `widgetId`  — the identity of the field's widget object;
* `errMsgId`  — the identity of the error-message mapping object;
* `errMsg`    — the contents of that mapping;
* `validId`   — the identity of the validator-list object;
* `validators`— the contents of that list;
* `required`  — a representative immutable scalar component. -/
structure FormField where
  widgetId : ObjId
  errMsgId : ObjId
  errMsg : MsgDict
  validId : ObjId
  validators : List Nat
  required : Bool
deriving DecidableEq
-- pure-end

-- post-conditions-start
/-- The duplicate is independent of the original. Given the fresh object
identities `fw`, `fe`, `fv` produced when allocating the duplicate's widget,
error-message mapping, and validator list:

* each mutable container of the result carries its OWN (fresh) identity
  (`fw`, `fe`, `fv` respectively), so it is a distinct object from the
  original's container;
* the error-message mapping and the validator list have contents EQUAL to the
  original's (the copy preserves contents);
* the immutable scalar component is preserved unchanged.

The freshness of `fw`/`fe`/`fv` (distinctness from the original's identities) is
a precondition of `correct_duplicateField`. -/
def problem_spec_duplicateField
    (self : FormField) (fw fe fv : ObjId) (result : FormField) : Prop :=
  result.widgetId = fw ∧
  result.errMsgId = fe ∧
  result.errMsg = self.errMsg ∧
  result.validId = fv ∧
  result.validators = self.validators ∧
  result.required = self.required
-- post-conditions-end

-- impl-start
-- Build the duplicate. Start from a shallow copy of the original (every
-- component initially the SAME object), then replace each mutable container with
-- a freshly allocated object that carries the same contents: the widget gets
-- fresh identity fw; the error-message mapping gets fresh identity fe with the
-- original's contents; the validator list gets fresh identity fv with the
-- original's contents. The immutable scalar is left as carried by the shallow
-- copy.
def implementation_duplicateField
    (self : FormField) (fw fe fv : ObjId) : FormField := Id.run do
  let mut result := self
  result := { result with widgetId := fw }
  result := { result with errMsgId := fe, errMsg := self.errMsg }
  result := { result with validId := fv, validators := self.validators }
  return result
-- impl-end

-- proof-start
theorem correct_duplicateField :
    ∀ (self : FormField) (fw fe fv : ObjId),
      fw ≠ self.widgetId → fe ≠ self.errMsgId → fv ≠ self.validId →
      problem_spec_duplicateField self fw fe fv
        (implementation_duplicateField self fw fe fv) := by
  intro self fw fe fv _ _ _
  unfold problem_spec_duplicateField implementation_duplicateField
  refine ⟨rfl, rfl, rfl, rfl, rfl, rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC IS A TOTAL FUNCTIONAL SPEC. problem_spec_duplicateField pins ALL 6 result fields to exact values on the entire precondition domain (fw!=widgetId, fe!=errMsgId, fv!=validId): result.widgetId=fw, errMsgId=fe, errMsg=self.errMsg, validId=fv, validators=self.validators, required=self.required. Hence any impl whose correct_ proof closes is behaviorally IDENTICAL to gold on the whole domain; its faithful refined patch IS the gold patch, which resolves. No closing clean-axiom impl exists whose faithful patch fails to resolve.

### ATTACK BATTERY (cmd: `bash scripts/lean_verify.sh <file>`; all same_spec=True via swebench_unified.markers.same_spec, verified):
- atk_1 PREPATCH BUG (omit fresh error-message id; errMsgId stays shared) -> exit 1, proof CANNOT close (fe=self.errMsgId unprovable). Prepatch bug reproduced & correctly rejected by the spec.
- atk_2 shared WIDGET identity (widgetId:=self.widgetId) -> exit 1 (rejected; fw clause fails).
- atk_3 WRONG error-message CONTENTS (errMsg:=[]) -> exit 1 (rejected; errMsg clause fails).
- atk_4 BOUNDARY / gold-equivalent (errMsg:=self.errMsg.reverse.reverse, proved equal via List.reverse_reverse) -> exit 0; `#print axioms correct_duplicateField` => depends on [propext] (clean, standard). CLOSES.
- atk_5 PARTIAL-DOMAIN / control-flow-effect (reproduce prepatch alias ONLY off-domain when fe=errMsgId) -> exit 1 (my chosen closing tactic did not discharge; impl is gold-equivalent on-domain anyway since precondition fe!=errMsgId forces the fresh branch, so no falsification available).
- atk_6 UNGROUNDED-ORACLE ECHO / reordered record build (validators->errMsg->widget) -> exit 0; `#print axioms` => does not depend on any axioms (clean). CLOSES.
- atk_7 shared VALIDATORS identity (validId:=self.validId) -> exit 1 (rejected; fv clause fails).
- pos POSITIVE CONTROL (canonical gold impl) -> exit 0, no axioms. VERIFIES.

RESOLVE RUNS (cmd: run_resolve('django__django-11880', patch) via swebench_unified.harness; docker oracle, benchmark swe_bench_verified):
- GOLD patch (faithful refined patch of every closing impl atk_4/atk_6/pos, since they are gold-equivalent) -> resolved=True, note='resolved'. POSITIVE control confirms harness discriminates & correctness oracle works.
- NOOP non-fixing patch (comment only, error_messages.copy() line ABSENT, bug remains) -> resolved=False, note='patch did not resolve in 3 attempts (consistent - not flaky)'. NEGATIVE control confirms the F2P test (assertIsNot(field_copy.error_messages, field.error_messages)) actually gates resolution.
- (empty patch -> 'no report'/harness-reject, not a usable signal; superseded by the noop negative control above.)

REFINEMENT.md AUDIT: all 7 legs tagged R (1-6) or I (7); ZERO A-legs. Solution.lean has NO opaque/axiom declarations (grep -E '^\s*(opaque|axiom)' => none), so there is no A-consumed/A-reference correspondence to validate. axiom_check.py is a legitimate G-AX skip stub (deeply-modeled changed decision, not axiomatized). No kind-3 (ungrounded) legs: every clause of problem_spec is grounded in self's components or the freshly-supplied identities fw/fe/fv. mapping.md Lean<->Python bijection is faithful (id()/is <-> ObjId equality; dict.copy()/list-slice/deepcopy modeled as fresh identity + preserved contents).

CONCLUSION: verify => correct holds. The discriminating clause result.errMsgId=fe under precondition fe!=self.errMsgId exactly captures the F2P assertIsNot; the prepatch alias makes correct_ unprovable (confirmed by atk_1). All 7 attacks fully verified; both needed resolve runs (positive gold + negative noop) executed and reported. Nothing broke the spec => SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on django__django-11880 (Field.__deepcopy__, post-patch adds result.error_messages = self.error_messages.copy()). Mechanical checks all pass: (1) same_spec(Solution, Solution_prepatch)=True via swebench_unified.markers with the lean backend — spec region (imports/docstring/axioms-comment/ObjId/MsgDict/FormField/problem_spec_duplicateField) is byte-identical/frozen, only impl+proof differ. (2) lean_verify.sh exit 0 and `#print axioms correct_duplicateField` -> 'does not depend on any axioms' (real proof, no sorryAx). (3) conformance_check.py passes 120,005 cases with 0 disagreements against an in-process replica of the POST-PATCH __deepcopy__ run on real Python objects (id()/is exercised).

Faithfulness of the model vs real callee: the spec pins, for the actual allocated identities fw/fe/fv, fresh widget/errMsg/validator identities + equal errMsg & validator contents + preserved scalar. Verified against real CPython semantics that dict.copy() and list[:] ALWAYS allocate a new object (even for empty {}/[]), and deepcopy of the widget always yields a fresh object — so the theorem's freshness preconditions (fe!=errMsgId, fv!=validId, fw!=widgetId) never assert more than the real code delivers. Contents-equality matches shallow-copy semantics; scalar preserved by copy.copy. Widget is modeled by identity only (deliberately weaker on contents, matching that F2P inspects only error_messages identity), so no over-strong claim. No real input makes the post-patch callee violate the spec; the discriminating clause result.errMsgId=fe under fe!=self.errMsgId is exactly the F2P assertIsNot(field_copy.error_messages, field.error_messages), and the prepatch (alias) correctly cannot satisfy it. Spec is neither too strong nor drifting. No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (no diff markers, no patched path django/forms/fields.py, no reproduced gold line 'result.error_messages = self.error_messages.copy()', no narration, no spec-view identifier/comment echoing patched symbol 'deepcopy' beyond public text; spec names the fn 'duplicateField'). same_spec(Solution, Solution_prepatch)=True, so the discriminator lives only in the elided impl/proof. Semantically the post-condition pins fresh identities symmetrically for all three mutable containers (widget fw / error-msg fe / validator fv) and does NOT single out error_messages as 'the fix'. The one gold-discriminating clause — fresh error-message identity fe distinct from the original — is exactly the independence property the PUBLIC problem_statement already states ('all copies of the same field share the same dictionary', copies must be independent). Spec view leaks nothing beyond problem_statement (hints_text not consulted).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
