# P2 adversarial audit — pallets__flask-5014

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -52,8 +52,6 @@
 def implementation_construct (name : String) : Except BPError BPState := Id.run do
   if name = "" then
     return Except.error BPError.emptyName
-  if name.contains '.' then
-    return Except.error BPError.dottedName
   let st : BPState := { name := name }
   return Except.ok st
 -- impl-end
@@ -64,9 +62,10 @@
       problem_spec_construct name (implementation_construct name) := by
   intro name
   unfold problem_spec_construct implementation_construct
-  by_cases he : name = ""
-  · simp only [Id.run, he, if_true]; rfl
-  · by_cases hd : name.contains '.'
-    · simp only [Id.run, he, hd, if_false, if_true]; rfl
-    · simp only [Id.run, he, hd, if_false]; rfl
+  simp only [Id.run, Id.pure_eq, Id.bind_eq]
+  by_cases h1 : name = ""
+  · simp [h1]
+  · by_cases h2 : name.contains '.' = true
+    · simp [h1, h2]
+    · simp [h1, h2]
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -50,8 +50,6 @@
 
 -- impl-start
 def implementation_construct (name : String) : Except BPError BPState := Id.run do
-  if name = "" then
-    return Except.error BPError.emptyName
   if name.contains '.' then
     return Except.error BPError.dottedName
   let st : BPState := { name := name }
@@ -64,9 +62,10 @@
       problem_spec_construct name (implementation_construct name) := by
   intro name
   unfold problem_spec_construct implementation_construct
-  by_cases he : name = ""
-  · simp only [Id.run, he, if_true]; rfl
-  · by_cases hd : name.contains '.'
-    · simp only [Id.run, he, hd, if_false, if_true]; rfl
-    · simp only [Id.run, he, hd, if_false]; rfl
+  simp only [Id.run, Id.pure_eq, Id.bind_eq]
+  by_cases h1 : name = ""
+  · simp [h1]
+  · by_cases h2 : name.contains '.' = true
+    · simp [h1, h2]
+    · simp [h1, h2]
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -51,9 +51,9 @@
 -- impl-start
 def implementation_construct (name : String) : Except BPError BPState := Id.run do
   if name = "" then
+    return Except.error BPError.dottedName
+  if name.contains '.' then
     return Except.error BPError.emptyName
-  if name.contains '.' then
-    return Except.error BPError.dottedName
   let st : BPState := { name := name }
   return Except.ok st
 -- impl-end
@@ -64,9 +64,10 @@
       problem_spec_construct name (implementation_construct name) := by
   intro name
   unfold problem_spec_construct implementation_construct
-  by_cases he : name = ""
-  · simp only [Id.run, he, if_true]; rfl
-  · by_cases hd : name.contains '.'
-    · simp only [Id.run, he, hd, if_false, if_true]; rfl
-    · simp only [Id.run, he, hd, if_false]; rfl
+  simp only [Id.run, Id.pure_eq, Id.bind_eq]
+  by_cases h1 : name = ""
+  · simp [h1]
+  · by_cases h2 : name.contains '.' = true
+    · simp [h1, h2]
+    · simp [h1, h2]
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -54,6 +54,8 @@
     return Except.error BPError.emptyName
   if name.contains '.' then
     return Except.error BPError.dottedName
+  if name = "a" then
+    return Except.error BPError.dottedName
   let st : BPState := { name := name }
   return Except.ok st
 -- impl-end
@@ -64,9 +66,10 @@
       problem_spec_construct name (implementation_construct name) := by
   intro name
   unfold problem_spec_construct implementation_construct
-  by_cases he : name = ""
-  · simp only [Id.run, he, if_true]; rfl
-  · by_cases hd : name.contains '.'
-    · simp only [Id.run, he, hd, if_false, if_true]; rfl
-    · simp only [Id.run, he, hd, if_false]; rfl
+  simp only [Id.run, Id.pure_eq, Id.bind_eq]
+  by_cases h1 : name = ""
+  · simp [h1]
+  · by_cases h2 : name.contains '.' = true
+    · simp [h1, h2]
+    · simp [h1, h2]
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -54,7 +54,7 @@
     return Except.error BPError.emptyName
   if name.contains '.' then
     return Except.error BPError.dottedName
-  let st : BPState := { name := name }
+  let st : BPState := { name := "" }
   return Except.ok st
 -- impl-end
 
@@ -64,9 +64,10 @@
       problem_spec_construct name (implementation_construct name) := by
   intro name
   unfold problem_spec_construct implementation_construct
-  by_cases he : name = ""
-  · simp only [Id.run, he, if_true]; rfl
-  · by_cases hd : name.contains '.'
-    · simp only [Id.run, he, hd, if_false, if_true]; rfl
-    · simp only [Id.run, he, hd, if_false]; rfl
+  simp only [Id.run, Id.pure_eq, Id.bind_eq]
+  by_cases h1 : name = ""
+  · simp [h1]
+  · by_cases h2 : name.contains '.' = true
+    · simp [h1, h2]
+    · simp [h1, h2]
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -50,10 +50,6 @@
 
 -- impl-start
 def implementation_construct (name : String) : Except BPError BPState := Id.run do
-  if name = "" then
-    return Except.error BPError.emptyName
-  if name.contains '.' then
-    return Except.error BPError.dottedName
   let st : BPState := { name := name }
   return Except.ok st
 -- impl-end
@@ -64,9 +60,10 @@
       problem_spec_construct name (implementation_construct name) := by
   intro name
   unfold problem_spec_construct implementation_construct
-  by_cases he : name = ""
-  · simp only [Id.run, he, if_true]; rfl
-  · by_cases hd : name.contains '.'
-    · simp only [Id.run, he, hd, if_false, if_true]; rfl
-    · simp only [Id.run, he, hd, if_false]; rfl
+  simp only [Id.run, Id.pure_eq, Id.bind_eq]
+  by_cases h1 : name = ""
+  · simp [h1]
+  · by_cases h2 : name.contains '.' = true
+    · simp [h1, h2]
+    · simp [h1, h2]
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -50,12 +50,7 @@
 
 -- impl-start
 def implementation_construct (name : String) : Except BPError BPState := Id.run do
-  if name = "" then
-    return Except.error BPError.emptyName
-  if name.contains '.' then
-    return Except.error BPError.dottedName
-  let st : BPState := { name := name }
-  return Except.ok st
+  return Except.error BPError.emptyName
 -- impl-end
 
 -- proof-start
@@ -64,9 +59,10 @@
       problem_spec_construct name (implementation_construct name) := by
   intro name
   unfold problem_spec_construct implementation_construct
-  by_cases he : name = ""
-  · simp only [Id.run, he, if_true]; rfl
-  · by_cases hd : name.contains '.'
-    · simp only [Id.run, he, hd, if_false, if_true]; rfl
-    · simp only [Id.run, he, hd, if_false]; rfl
+  simp only [Id.run, Id.pure_eq, Id.bind_eq]
+  by_cases h1 : name = ""
+  · simp [h1]
+  · by_cases h2 : name.contains '.' = true
+    · simp [h1, h2]
+    · simp [h1, h2]
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Constructing a named registrable component from a caller-supplied name.

A name is subject to two validity requirements: it must be present (a non-empty
string), and it must not contain a dot `.` character (the dot is reserved as a
hierarchy separator). Construction is an input→output relation: given a name, it
either fails — exactly when the name is empty, or when it contains a dot — or
succeeds, yielding a component that records the supplied name unchanged.

This is stated abstractly as an input→output relation; the implementation and
correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the validation is modeled
-- deeply with concrete operations (an emptiness test, a dot-membership test, and
-- a field assignment). The orthogonal base-class initialization that stores the
-- other, untouched attributes is abstracted out of the modeled state.
-- axioms-end

-- pure-start
/-- The two distinct validity failures observable here. -/
inductive BPError where
  | emptyName
  | dottedName
deriving DecidableEq, Repr

/-- A constructed component, carrying only the field this validation touches:
the supplied name. -/
structure BPState where
  name : String
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- Construction fails with the emptiness failure exactly when the name is
empty; otherwise it fails with the dot failure exactly when the name contains a
dot character; otherwise it succeeds, recording the supplied name unchanged. -/
def problem_spec_construct (name : String) (result : Except BPError BPState) : Prop :=
  if name = "" then
    result = Except.error BPError.emptyName
  else if name.contains '.' then
    result = Except.error BPError.dottedName
  else
    result = Except.ok { name := name }
-- post-conditions-end

-- impl-start
def implementation_construct (name : String) : Except BPError BPState := Id.run do
  if name = "" then
    return Except.error BPError.emptyName
  if name.contains '.' then
    return Except.error BPError.dottedName
  let st : BPState := { name := name }
  return Except.ok st
-- impl-end

-- proof-start
theorem correct_construct :
    ∀ (name : String),
      problem_spec_construct name (implementation_construct name) := by
  intro name
  unfold problem_spec_construct implementation_construct
  by_cases he : name = ""
  · simp only [Id.run, he, if_true]; rfl
  · by_cases hd : name.contains '.'
    · simp only [Id.run, he, hd, if_false, if_true]; rfl
    · simp only [Id.run, he, hd, if_false]; rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Pure R/I bundle: meta.json has axioms=[], deep_model_references=[], opaque_callees=[]. No A-legs exist to attack; refinement.md correctly tags every leg R or I (G-AX is a skip stub; R/I legs covered by G-CONF). Soundness therefore reduces to spec tightness. problem_spec_construct is TOTAL and FULLY DETERMINISTIC over all String inputs: `if name="" then result=Except.error emptyName else if name.contains '.' then result=Except.error dottedName else result=Except.ok {name:=name}` — every branch pins result to exactly one value, leaving no slack for a behaviorally-wrong impl.

same_spec: all 7 attacks + positive control = True (swebench_unified.markers.same_spec, lean backend). Only impl+proof edited; both collapse to placeholders in lean spec_view, so spec regions are byte-identical.

Commands & results:
- Positive control: `bash scripts/lean_verify.sh pos_control.lean` -> EXIT=0 (verifies, no sorry). Axiom check (pos_axcheck.lean, appended `#print axioms correct_construct`): EXIT=0 -> "'correct_construct' depends on axioms: [propext, Quot.sound]" — clean, no sorryAx/native_decide.
- Prepatch (bundle Solution_prepatch.lean = dot-guard only, no empty-guard): EXIT=1, unsolved goals `(if "".contains '.' = true then Except.error dottedName else Except.ok {name:=""}) = Except.error emptyName` — exact FAIL_TO_PASS (test_empty_name_not_allowed). prepatch_reproduced=true.

All 7 same-spec wrong impls FAILED verification with genuine 'unsolved goals' proof-obligation errors (verified via `bash scripts/lean_verify.sh atk_N.lean`, EXIT=1 each). First-generation files had a missing-theorem-header syntax bug; regenerated with header and re-verified so failures are behavioral, not syntactic. The gold tactic closes the positive control, confirming failures are behavioral refutations:
  atk_1 (drop dot-guard; dotted names wrongly succeed): EXIT=1 unsolved goals @ dotted branch.
  atk_2 (prepatch bug, drop empty-guard): EXIT=1, goal `...=Except.error emptyName` unprovable for "".
  atk_3 (swap error constructors emptyName<->dottedName): EXIT=1 unsolved goals both branches.
  atk_4 (boundary: extra-reject name="a" as dottedName): EXIT=1 unsolved goals (spec requires ok for "a").
  atk_5 (wrong stored field: success records name:=""): EXIT=1 unsolved goals (spec requires name:=name).
  atk_6 (ungrounded oracle: always Except.ok {name:=name}): EXIT=1 unsolved goals on both error branches.
  atk_7 (constant: always Except.error emptyName): EXIT=1 unsolved goals on dotted/ok branches.

No wrong impl closed with clean axioms => zero patches to materialize/resolve (patches={} correctly). Attacks span partial-domain (atk_1,atk_2), control-flow-effect (atk_3), boundary (atk_4), wrong-carrier (atk_5), and ungrounded-oracle/echo (atk_6,atk_7) — 7 distinct classes, all refuted. verify => correct holds for this spec. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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
Constructing a named registrable component from a caller-supplied name.

A name is subject to two validity requirements: it must be present (a non-empty
string), and it must not contain a dot `.` character (the dot is reserved as a
hierarchy separator). Construction is an input→output relation: given a name, it
either fails — exactly when the name is empty, or when it contains a dot — or
succeeds, yielding a component that records the supplied name unchanged.

This is stated abstractly as an input→output relation; the implementation and
correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the validation is modeled
-- deeply with concrete operations (an emptiness test, a dot-membership test, and
-- a field assignment). The orthogonal base-class initialization that stores the
-- other, untouched attributes is abstracted out of the modeled state.
-- axioms-end

-- pure-start
/-- The two distinct validity failures observable here. -/
inductive BPError where
  | emptyName
  | dottedName
deriving DecidableEq, Repr

/-- A constructed component, carrying only the field this validation touches:
the supplied name. -/
structure BPState where
  name : String
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- Construction fails with the emptiness failure exactly when the name is
empty; otherwise it fails with the dot failure exactly when the name contains a
dot character; otherwise it succeeds, recording the supplied name unchanged. -/
def problem_spec_construct (name : String) (result : Except BPError BPState) : Prop :=
  if name = "" then
    result = Except.error BPError.emptyName
  else if name.contains '.' then
    result = Except.error BPError.dottedName
  else
    result = Except.ok { name := name }
-- post-conditions-end

-- impl-start
def implementation_construct (name : String) : Except BPError BPState := Id.run do
  if name = "" then
    return Except.error BPError.emptyName
  if name.contains '.' then
    return Except.error BPError.dottedName
  let st : BPState := { name := name }
  return Except.ok st
-- impl-end

-- proof-start
theorem correct_construct :
    ∀ (name : String),
      problem_spec_construct name (implementation_construct name) := by
  intro name
  unfold problem_spec_construct implementation_construct
  by_cases he : name = ""
  · simp only [Id.run, he, if_true]; rfl
  · by_cases hd : name.contains '.'
    · simp only [Id.run, he, hd, if_false, if_true]; rfl
    · simp only [Id.run, he, hd, if_false]; rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Pure R/I bundle: meta.json has axioms=[], deep_model_references=[], opaque_callees=[]. No A-legs exist to attack; refinement.md correctly tags every leg R or I (G-AX is a skip stub; R/I legs covered by G-CONF). Soundness therefore reduces to spec tightness. problem_spec_construct is TOTAL and FULLY DETERMINISTIC over all String inputs: `if name="" then result=Except.error emptyName else if name.contains '.' then result=Except.error dottedName else result=Except.ok {name:=name}` — every branch pins result to exactly one value, leaving no slack for a behaviorally-wrong impl.

same_spec: all 7 attacks + positive control = True (swebench_unified.markers.same_spec, lean backend). Only impl+proof edited; both collapse to placeholders in lean spec_view, so spec regions are byte-identical.

Commands & results:
- Positive control: `bash scripts/lean_verify.sh pos_control.lean` -> EXIT=0 (verifies, no sorry). Axiom check (pos_axcheck.lean, appended `#print axioms correct_construct`): EXIT=0 -> "'correct_construct' depends on axioms: [propext, Quot.sound]" — clean, no sorryAx/native_decide.
- Prepatch (bundle Solution_prepatch.lean = dot-guard only, no empty-guard): EXIT=1, unsolved goals `(if "".contains '.' = true then Except.error dottedName else Except.ok {name:=""}) = Except.error emptyName` — exact FAIL_TO_PASS (test_empty_name_not_allowed). prepatch_reproduced=true.

All 7 same-spec wrong impls FAILED verification with genuine 'unsolved goals' proof-obligation errors (verified via `bash scripts/lean_verify.sh atk_N.lean`, EXIT=1 each). First-generation files had a missing-theorem-header syntax bug; regenerated with header and re-verified so failures are behavioral, not syntactic. The gold tactic closes the positive control, confirming failures are behavioral refutations:
  atk_1 (drop dot-guard; dotted names wrongly succeed): EXIT=1 unsolved goals @ dotted branch.
  atk_2 (prepatch bug, drop empty-guard): EXIT=1, goal `...=Except.error emptyName` unprovable for "".
  atk_3 (swap error constructors emptyName<->dottedName): EXIT=1 unsolved goals both branches.
  atk_4 (boundary: extra-reject name="a" as dottedName): EXIT=1 unsolved goals (spec requires ok for "a").
  atk_5 (wrong stored field: success records name:=""): EXIT=1 unsolved goals (spec requires name:=name).
  atk_6 (ungrounded oracle: always Except.ok {name:=name}): EXIT=1 unsolved goals on both error branches.
  atk_7 (constant: always Except.error emptyName): EXIT=1 unsolved goals on dotted/ok branches.

No wrong impl closed with clean axioms => zero patches to materialize/resolve (patches={} correctly). Attacks span partial-domain (atk_1,atk_2), control-flow-effect (atk_3), boundary (atk_4), wrong-carrier (atk_5), and ungrounded-oracle/echo (atk_6,atk_7) — 7 distinct classes, all refuted. verify => correct holds for this spec. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness attack (spec-too-strong / drift): no divergence found between the modeled function and the real callee. VERIFIED: (1) same_spec(Solution, Solution_prepatch)=True — spec view byte-identical, prepatch differential is honest. (2) Solution.lean compiles clean (lean_verify exit 0); #print axioms correct_construct = [propext, Quot.sound] — NO sorryAx, genuine proof. (3) Real callee at base_commit 7ee9ceb (fetched from GitHub): Blueprint.__init__ has only the dot guard `if "." in name: raise ValueError`; gold patch (patch_equals_gold=True) inserts `if not name: raise ValueError("'name' may not be empty.")` BEFORE the dot guard. Patched behavior = spec: name=="" -> emptyName; else '.' in name -> dottedName; else ok{name}. (4) Bijection holds on every input class: Python `not name` (str) is true iff name=="" == Lean `name = ""`; Python `"." in name` (single-char substring) == Lean `String.contains name '.'`; precedence empty-before-dot consistent and the only overlap (empty AND dotted) is impossible since "" has no dot. Whitespace-only names construct in both; U+002E char membership identical. super().__init__ and untouched attrs are name-independent and correctly abstracted out of the modeled state. (5) G-CONF ran 120,020 differential checks against the REAL patched flask.Blueprint in-container with 0 disagreements. I could construct no input on which the spec disagrees with the real repo behavior. Spec is neither too strong nor drifted.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region is byte-identical between Solution.lean and Solution_prepatch.lean (swebench_unified.markers.same_spec = True with the lean backend). The spec view elides impl+proof, exposing only: (1) the empty-name -> ValueError requirement, which is stated VERBATIM by the public problem_statement ('Require a non-empty name for Blueprints ... It would be helpful if a ValueError was raised'), so formalizing it cannot leak beyond problem_statement; and (2) the dot-character guard (name.contains '.') which is PRE-EXISTING base_commit behavior (src/flask/blueprints.py:193-194), NOT the gold edit — it is carried only to frame the full validation and is discoverable from repo source, not from the patch. The gold edit (insert `if not name: raise ValueError(...)` before the dot guard) is not disclosed by any spec-view line beyond what problem_statement already states. No gold-specific artifacts appear in the spec view: no error-message strings, no file/line references, no 'insert-before-dot' instruction. The empty-before-dot precedence is behaviorally forced (an empty string contains no dot) rather than a hidden solution detail. Comments in the axioms/pure/post-conditions regions describe abstract modeling choices, not the patch. Judged against the public problem_statement only (hints_text excluded, which was empty anyway).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
