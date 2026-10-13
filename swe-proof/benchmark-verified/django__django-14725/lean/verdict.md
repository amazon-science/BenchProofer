# P2 adversarial audit — django__django-14725

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -36,8 +36,6 @@
 -- impl-start
 def implementation_saveFormset {α : Type}
     (editOnly : Bool) (existing new : List α) : List α := Id.run do
-  if editOnly then
-    return existing
   return existing ++ new
 -- impl-end
 
@@ -48,5 +46,5 @@
         (implementation_saveFormset editOnly existing new) := by
   intro editOnly existing new
   unfold problem_spec_saveFormset implementation_saveFormset
-  cases editOnly <;> rfl
+  cases editOnly <;> simp
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,7 @@
     (editOnly : Bool) (existing new : List α) : List α := Id.run do
   if editOnly then
     return existing
-  return existing ++ new
+  return new ++ existing
 -- impl-end
 
 -- proof-start
@@ -48,5 +48,5 @@
         (implementation_saveFormset editOnly existing new) := by
   intro editOnly existing new
   unfold problem_spec_saveFormset implementation_saveFormset
-  cases editOnly <;> rfl
+  cases editOnly <;> simp
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -37,7 +37,7 @@
 def implementation_saveFormset {α : Type}
     (editOnly : Bool) (existing new : List α) : List α := Id.run do
   if editOnly then
-    return existing
+    return new
   return existing ++ new
 -- impl-end
 
@@ -48,5 +48,5 @@
         (implementation_saveFormset editOnly existing new) := by
   intro editOnly existing new
   unfold problem_spec_saveFormset implementation_saveFormset
-  cases editOnly <;> rfl
+  cases editOnly <;> simp
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -36,9 +36,7 @@
 -- impl-start
 def implementation_saveFormset {α : Type}
     (editOnly : Bool) (existing new : List α) : List α := Id.run do
-  if editOnly then
-    return existing
-  return existing ++ new
+  return existing
 -- impl-end
 
 -- proof-start
@@ -48,5 +46,5 @@
         (implementation_saveFormset editOnly existing new) := by
   intro editOnly existing new
   unfold problem_spec_saveFormset implementation_saveFormset
-  cases editOnly <;> rfl
+  cases editOnly <;> simp
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -37,7 +37,9 @@
 def implementation_saveFormset {α : Type}
     (editOnly : Bool) (existing new : List α) : List α := Id.run do
   if editOnly then
-    return existing
+    match existing with
+    | [] => return new
+    | _  => return existing
   return existing ++ new
 -- impl-end
 
@@ -48,5 +50,5 @@
         (implementation_saveFormset editOnly existing new) := by
   intro editOnly existing new
   unfold problem_spec_saveFormset implementation_saveFormset
-  cases editOnly <;> rfl
+  cases editOnly <;> (try cases existing) <;> simp
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,7 @@
     (editOnly : Bool) (existing new : List α) : List α := Id.run do
   if editOnly then
     return existing
-  return existing ++ new
+  return existing ++ new ++ new
 -- impl-end
 
 -- proof-start
@@ -48,5 +48,5 @@
         (implementation_saveFormset editOnly existing new) := by
   intro editOnly existing new
   unfold problem_spec_saveFormset implementation_saveFormset
-  cases editOnly <;> rfl
+  cases editOnly <;> simp
 -- proof-end
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -36,9 +36,9 @@
 -- impl-start
 def implementation_saveFormset {α : Type}
     (editOnly : Bool) (existing new : List α) : List α := Id.run do
-  if editOnly then
-    return existing
-  return existing ++ new
+  match editOnly with
+  | true  => return existing
+  | false => return existing ++ new
 -- impl-end
 
 -- proof-start
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -38,7 +38,7 @@
     (editOnly : Bool) (existing new : List α) : List α := Id.run do
   if editOnly then
     return existing
-  return existing ++ new
+  return (existing ++ new).reverse
 -- impl-end
 
 -- proof-start
@@ -48,5 +48,5 @@
         (implementation_saveFormset editOnly existing new) := by
   intro editOnly existing new
   unfold problem_spec_saveFormset implementation_saveFormset
-  cases editOnly <;> rfl
+  cases editOnly <;> simp
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The function under spec
-- composes the result lists of two collaborators: the list of persisted
-- already-existing objects, and the list of persisted freshly-created objects.
-- Those two lists are the genuine input carriers of this function (modeled as
-- the `existing` / `new` arguments — an R refinement, mapping.md), so they are
-- not axiomatized and not opaque. The proof agent may add `_prop` axioms only
-- if stuck (none are expected).
-- axioms-end

-- pure-start
-- No auxiliary pure helpers are required: the behavior is a single selection
-- between two ways of combining the two input lists.
-- pure-end

-- post-conditions-start
/-- The returned collection of persisted objects.

When the formset is restricted to editing the objects it already manages, the
result is exactly the list of persisted already-present objects, in order, and
nothing else — no freshly-created objects are added. Otherwise the result is the
list of persisted already-present objects followed by the list of persisted
freshly-created objects, in order.

Both components are pinned to the inputs in every case: in the restricted mode
the freshly-created list contributes nothing, and in the unrestricted mode it is
appended after the existing list with order preserved. -/
def problem_spec_saveFormset {α : Type}
    (editOnly : Bool) (existing new : List α) (result : List α) : Prop :=
  result = if editOnly then existing else existing ++ new
-- post-conditions-end

-- impl-start
def implementation_saveFormset {α : Type}
    (editOnly : Bool) (existing new : List α) : List α := Id.run do
  if editOnly then
    return existing
  return existing ++ new
-- impl-end

-- proof-start
theorem correct_saveFormset {α : Type} :
    ∀ (editOnly : Bool) (existing new : List α),
      problem_spec_saveFormset editOnly existing new
        (implementation_saveFormset editOnly existing new) := by
  intro editOnly existing new
  unfold problem_spec_saveFormset implementation_saveFormset
  cases editOnly <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC: exact pointwise equality, polymorphic in alpha: problem_spec_saveFormset editOnly existing new result := result = if editOnly then existing else existing ++ new. Quantified over ALL (editOnly, existing, new). This admits NO extensionally-distinct implementation, so any impl whose correct_saveFormset closes must equal the gold behavior.

SAME_SPEC: all 8 attacks + pos verified True via swebench_unified.markers.same_spec (spec/axioms/pre/post regions byte-identical; only impl+proof edited).

POSITIVE CONTROL pos.lean (gold impl): `bash scripts/lean_verify.sh .../pos.lean` -> exit 0; `#print axioms correct_saveFormset` -> 'does not depend on any axioms' (clean).

PREPATCH prepatch.lean (Solution_prepatch.lean, always `existing ++ new`): lean_verify exit 1, unsolved goal (bug reproduced: extra forms still create new objects in edit-only mode).

ATTACKS (all `bash scripts/lean_verify.sh .../atk_N.lean`), run concurrently in batches of 4:
- atk_1 prepatch bug (ignore flag, always existing++new): exit 1, unsolved `new = []`.
- atk_2 else-branch order swap (new++existing): exit 1, unsolved `new++existing = existing++new`.
- atk_3 wrong then-branch (return new): exit 1, unsolved `new = existing`.
- atk_4 control-flow effect (always return existing, drop new): exit 1, unsolved `new = []`.
- atk_5 partial-domain/boundary (editOnly & existing=[] => return new): exit 1, unsolved `new = []`.
- atk_6 duplicate append (existing++new++new): exit 1, unsolved `new = []`.
- atk_7 ungrounded-oracle ECHO (match editOnly: true=>existing, false=>existing++new) — semantically IDENTICAL to gold: exit 0, clean axioms ('does not depend on any axioms'). This is a gold-equivalent echo, not a divergent impl; per echo-attack policy its faithful refined patch IS the gold patch. Materialized (== gold patch, patch_equals_gold=True) and RAN through official harness (run_resolve / run_evaluation, Docker): RESOLVED=TRUE. report.json (sbu-audit-atk7-eq-...-p3518781): resolved:true, FAIL_TO_PASS all 3 test_edit_only* success, PASS_TO_PASS 63/63 success, 0 failures. So verify => correct holds for the one closing impl.
- atk_8 reversed else result ((existing++new).reverse): exit 1, unsolved `new.reverse++existing.reverse = existing++new`.

Only atk_7 closes; it resolves. No closing-but-non-resolving impl found. verify=>correct NOT falsified.

REFINEMENT.MD AUDIT: 3 legs, ALL R-tagged (no kind-3): (1) editOnly:Bool read <-> `if self.edit_only:` (R, bool<->Bool); (2) return existing <-> save_existing_objects(commit) returned list (R, callee UNCHANGED, only its return list consumed as input); (3) existing++new <-> save_existing_objects(commit)+save_new_objects(commit) (R, list `+`<->`++`, order-preserving). NO A-consumed / A-reference legs (axioms region empty; consistent with axiom-clean proofs) and NO changed-inexpressible legs. Model<->patch correspondence matches gold patch verbatim (save() edit_only branch + factory flag plumbing which is behavior-free). A-leg concern is moot here: there are no A legs. G-AX correctly SKIPs. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The function under spec
-- composes the result lists of two collaborators: the list of persisted
-- already-existing objects, and the list of persisted freshly-created objects.
-- Those two lists are the genuine input carriers of this function (modeled as
-- the `existing` / `new` arguments — an R refinement, mapping.md), so they are
-- not axiomatized and not opaque. The proof agent may add `_prop` axioms only
-- if stuck (none are expected).
-- axioms-end

-- pure-start
-- No auxiliary pure helpers are required: the behavior is a single selection
-- between two ways of combining the two input lists.
-- pure-end

-- post-conditions-start
/-- The returned collection of persisted objects.

When the formset is restricted to editing the objects it already manages, the
result is exactly the list of persisted already-present objects, in order, and
nothing else — no freshly-created objects are added. Otherwise the result is the
list of persisted already-present objects followed by the list of persisted
freshly-created objects, in order.

Both components are pinned to the inputs in every case: in the restricted mode
the freshly-created list contributes nothing, and in the unrestricted mode it is
appended after the existing list with order preserved. -/
def problem_spec_saveFormset {α : Type}
    (editOnly : Bool) (existing new : List α) (result : List α) : Prop :=
  result = if editOnly then existing else existing ++ new
-- post-conditions-end

-- impl-start
def implementation_saveFormset {α : Type}
    (editOnly : Bool) (existing new : List α) : List α := Id.run do
  if editOnly then
    return existing
  return existing ++ new
-- impl-end

-- proof-start
theorem correct_saveFormset {α : Type} :
    ∀ (editOnly : Bool) (existing new : List α),
      problem_spec_saveFormset editOnly existing new
        (implementation_saveFormset editOnly existing new) := by
  intro editOnly existing new
  unfold problem_spec_saveFormset implementation_saveFormset
  cases editOnly <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC: exact pointwise equality, polymorphic in alpha: problem_spec_saveFormset editOnly existing new result := result = if editOnly then existing else existing ++ new. Quantified over ALL (editOnly, existing, new). This admits NO extensionally-distinct implementation, so any impl whose correct_saveFormset closes must equal the gold behavior.

SAME_SPEC: all 8 attacks + pos verified True via swebench_unified.markers.same_spec (spec/axioms/pre/post regions byte-identical; only impl+proof edited).

POSITIVE CONTROL pos.lean (gold impl): `bash scripts/lean_verify.sh .../pos.lean` -> exit 0; `#print axioms correct_saveFormset` -> 'does not depend on any axioms' (clean).

PREPATCH prepatch.lean (Solution_prepatch.lean, always `existing ++ new`): lean_verify exit 1, unsolved goal (bug reproduced: extra forms still create new objects in edit-only mode).

ATTACKS (all `bash scripts/lean_verify.sh .../atk_N.lean`), run concurrently in batches of 4:
- atk_1 prepatch bug (ignore flag, always existing++new): exit 1, unsolved `new = []`.
- atk_2 else-branch order swap (new++existing): exit 1, unsolved `new++existing = existing++new`.
- atk_3 wrong then-branch (return new): exit 1, unsolved `new = existing`.
- atk_4 control-flow effect (always return existing, drop new): exit 1, unsolved `new = []`.
- atk_5 partial-domain/boundary (editOnly & existing=[] => return new): exit 1, unsolved `new = []`.
- atk_6 duplicate append (existing++new++new): exit 1, unsolved `new = []`.
- atk_7 ungrounded-oracle ECHO (match editOnly: true=>existing, false=>existing++new) — semantically IDENTICAL to gold: exit 0, clean axioms ('does not depend on any axioms'). This is a gold-equivalent echo, not a divergent impl; per echo-attack policy its faithful refined patch IS the gold patch. Materialized (== gold patch, patch_equals_gold=True) and RAN through official harness (run_resolve / run_evaluation, Docker): RESOLVED=TRUE. report.json (sbu-audit-atk7-eq-...-p3518781): resolved:true, FAIL_TO_PASS all 3 test_edit_only* success, PASS_TO_PASS 63/63 success, 0 failures. So verify => correct holds for the one closing impl.
- atk_8 reversed else result ((existing++new).reverse): exit 1, unsolved `new.reverse++existing.reverse = existing++new`.

Only atk_7 closes; it resolves. No closing-but-non-resolving impl found. verify=>correct NOT falsified.

REFINEMENT.MD AUDIT: 3 legs, ALL R-tagged (no kind-3): (1) editOnly:Bool read <-> `if self.edit_only:` (R, bool<->Bool); (2) return existing <-> save_existing_objects(commit) returned list (R, callee UNCHANGED, only its return list consumed as input); (3) existing++new <-> save_existing_objects(commit)+save_new_objects(commit) (R, list `+`<->`++`, order-preserving). NO A-consumed / A-reference legs (axioms region empty; consistent with axiom-clean proofs) and NO changed-inexpressible legs. Model<->patch correspondence matches gold patch verbatim (save() edit_only branch + factory flag plumbing which is behavior-free). A-leg concern is moot here: there are no A legs. G-AX correctly SKIPs. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for django__django-14725, modeled function BaseModelFormSet.save(self, commit=True). Gold patch body: `if self.edit_only: return self.save_existing_objects(commit) else: return self.save_existing_objects(commit) + self.save_new_objects(commit)` (verified against @ base_commit 0af9a5fc and the SWE-bench gold patch). Spec: `result = if editOnly then existing else existing ++ new`. The two UNCHANGED callees (save_existing_objects, save_new_objects) are modeled as R-refinement input lists `existing`/`new`; Python list `+` maps to order-preserving Lean `++`; `self.edit_only:bool` maps to `editOnly:Bool`. This is an exact functional characterization of the real return value across every input class (both editOnly values, empty/non-empty existing/new). The spec is not too strong: it forbids no behavior the real function exhibits, and pins the result to exactly what the real callee composition returns. `commit` is correctly subsumed into the callee-return abstraction (it only affects what the opaque callees return, which are the modeled inputs). No diverging input exists. Solution.lean compiles (exit 0), `#print axioms correct_saveFormset` reports no axiom dependence (no sorryAx — proof is genuine), and same_spec(Solution, Solution_prepatch)=True with the spec region unchanged between variants (G-DIFF signal is impl-only, as intended).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (impl/proof elided) for django__django-14725. Verified: (1) same_spec(Solution, Solution_prepatch)=True — spec region byte-identical; (2) lexical G-LEAK screen passes with zero hard failures. Semantic review against the public problem_statement (NOT hints_text): the problem_statement explicitly requests 'a way for model formsets to disallow new object creation' / an 'edit only view of objects' — i.e. edit-only mode must not create new objects. The only substantive spec content is the post-condition `result = if editOnly then existing else existing ++ new` plus an abstract docstring, which faithfully formalizes exactly that public requirement. No leak of the gold edit beyond the problem statement: no diff markers, no patched file path (django/forms/models.py) or module dotted path, none of the patched repo symbols (save, save_existing_objects, save_new_objects, edit_only, modelformset_factory, inlineformset_factory) appear in the spec view — modeling identifiers are abstract (editOnly/existing/new/saveFormset), and `editOnly` merely echoes the public phrase 'edit only'. No bug/fix narration in comments. mapping.md/refinement.md name the patched symbols but are auxiliary docs, not part of the solver-visible spec view. A correct spec must pin the required behavior; doing so here reveals nothing about the edit's location or mechanism beyond what the task already discloses. No relaxation flag present and none needed.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
