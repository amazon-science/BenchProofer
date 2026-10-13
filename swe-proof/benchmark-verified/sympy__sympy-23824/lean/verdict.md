# P2 adversarial audit — sympy__sympy-23824

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -54,43 +54,21 @@
   let lead := labels.take leadCount
   let mut out : List (List Int) := []
   for t in terms do
-    out := out ++ [lead ++ t]
+    let mut acc := t
+    for x in lead do
+      acc := x :: acc
+    out := out ++ [acc]
   return out
 -- impl-end
 
 -- proof-start
-theorem helper_prependLeading (lead : List Int) (terms : List (List Int)) :
-    ∀ (init : List (List Int)),
-      Id.run (forIn terms init (fun t r =>
-        (pure (ForInStep.yield (r ++ [lead ++ t]))))) = init ++ terms.map (fun t => lead ++ t) := by
-  induction terms with
-  | nil =>
-    intro init
-    show Id.run (pure init) = _
-    rw [Id.run_pure]; simp
-  | cons a as ih =>
-    intro init
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    rw [ih]
-    simp [List.append_assoc]
-
 theorem correct_prependLeading :
     ∀ (leadCount : Nat) (labels : List Int) (terms : List (List Int)),
       problem_spec_prependLeading leadCount labels terms
         (implementation_prependLeading leadCount labels terms) := by
   intro leadCount labels terms
   unfold problem_spec_prependLeading implementation_prependLeading
-  simp only [Id.run, bind]
-  have h := helper_prependLeading (labels.take leadCount) terms []
-  simp only [Id.run] at h
-  rw [h]
-  show (List.map (fun t => labels.take leadCount ++ t) terms).length = terms.length ∧
-      ∀ i, i < terms.length →
-        (List.map (fun t => labels.take leadCount ++ t) terms)[i]! = labels.take leadCount ++ terms[i]!
-  refine ⟨by simp, ?_⟩
+  refine ⟨by simp [Id.run], ?_⟩
   intro i hi
-  rw [List.getElem!_eq_getElem?_getD, List.getElem!_eq_getElem?_getD]
-  rw [List.getElem?_map, List.getElem?_eq_getElem hi]
-  simp
+  simp [Id.run]
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -51,7 +51,7 @@
 def implementation_prependLeading
     (leadCount : Nat) (labels : List Int) (terms : List (List Int)) :
     List (List Int) := Id.run do
-  let lead := labels.take leadCount
+  let lead := labels.drop leadCount
   let mut out : List (List Int) := []
   for t in terms do
     out := out ++ [lead ++ t]
@@ -59,38 +59,13 @@
 -- impl-end
 
 -- proof-start
-theorem helper_prependLeading (lead : List Int) (terms : List (List Int)) :
-    ∀ (init : List (List Int)),
-      Id.run (forIn terms init (fun t r =>
-        (pure (ForInStep.yield (r ++ [lead ++ t]))))) = init ++ terms.map (fun t => lead ++ t) := by
-  induction terms with
-  | nil =>
-    intro init
-    show Id.run (pure init) = _
-    rw [Id.run_pure]; simp
-  | cons a as ih =>
-    intro init
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    rw [ih]
-    simp [List.append_assoc]
-
 theorem correct_prependLeading :
     ∀ (leadCount : Nat) (labels : List Int) (terms : List (List Int)),
       problem_spec_prependLeading leadCount labels terms
         (implementation_prependLeading leadCount labels terms) := by
   intro leadCount labels terms
   unfold problem_spec_prependLeading implementation_prependLeading
-  simp only [Id.run, bind]
-  have h := helper_prependLeading (labels.take leadCount) terms []
-  simp only [Id.run] at h
-  rw [h]
-  show (List.map (fun t => labels.take leadCount ++ t) terms).length = terms.length ∧
-      ∀ i, i < terms.length →
-        (List.map (fun t => labels.take leadCount ++ t) terms)[i]! = labels.take leadCount ++ terms[i]!
-  refine ⟨by simp, ?_⟩
+  refine ⟨by simp [Id.run], ?_⟩
   intro i hi
-  rw [List.getElem!_eq_getElem?_getD, List.getElem!_eq_getElem?_getD]
-  rw [List.getElem?_map, List.getElem?_eq_getElem hi]
-  simp
+  simp [Id.run]
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -54,43 +54,18 @@
   let lead := labels.take leadCount
   let mut out : List (List Int) := []
   for t in terms do
-    out := out ++ [lead ++ t]
+    out := out ++ [t ++ lead]
   return out
 -- impl-end
 
 -- proof-start
-theorem helper_prependLeading (lead : List Int) (terms : List (List Int)) :
-    ∀ (init : List (List Int)),
-      Id.run (forIn terms init (fun t r =>
-        (pure (ForInStep.yield (r ++ [lead ++ t]))))) = init ++ terms.map (fun t => lead ++ t) := by
-  induction terms with
-  | nil =>
-    intro init
-    show Id.run (pure init) = _
-    rw [Id.run_pure]; simp
-  | cons a as ih =>
-    intro init
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    rw [ih]
-    simp [List.append_assoc]
-
 theorem correct_prependLeading :
     ∀ (leadCount : Nat) (labels : List Int) (terms : List (List Int)),
       problem_spec_prependLeading leadCount labels terms
         (implementation_prependLeading leadCount labels terms) := by
   intro leadCount labels terms
   unfold problem_spec_prependLeading implementation_prependLeading
-  simp only [Id.run, bind]
-  have h := helper_prependLeading (labels.take leadCount) terms []
-  simp only [Id.run] at h
-  rw [h]
-  show (List.map (fun t => labels.take leadCount ++ t) terms).length = terms.length ∧
-      ∀ i, i < terms.length →
-        (List.map (fun t => labels.take leadCount ++ t) terms)[i]! = labels.take leadCount ++ terms[i]!
-  refine ⟨by simp, ?_⟩
+  refine ⟨by simp [Id.run], ?_⟩
   intro i hi
-  rw [List.getElem!_eq_getElem?_getD, List.getElem!_eq_getElem?_getD]
-  rw [List.getElem?_map, List.getElem?_eq_getElem hi]
-  simp
+  simp [Id.run]
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -54,43 +54,21 @@
   let lead := labels.take leadCount
   let mut out : List (List Int) := []
   for t in terms do
-    out := out ++ [lead ++ t]
+    if t.isEmpty then
+      out := out ++ [t]
+    else
+      out := out ++ [lead ++ t]
   return out
 -- impl-end
 
 -- proof-start
-theorem helper_prependLeading (lead : List Int) (terms : List (List Int)) :
-    ∀ (init : List (List Int)),
-      Id.run (forIn terms init (fun t r =>
-        (pure (ForInStep.yield (r ++ [lead ++ t]))))) = init ++ terms.map (fun t => lead ++ t) := by
-  induction terms with
-  | nil =>
-    intro init
-    show Id.run (pure init) = _
-    rw [Id.run_pure]; simp
-  | cons a as ih =>
-    intro init
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    rw [ih]
-    simp [List.append_assoc]
-
 theorem correct_prependLeading :
     ∀ (leadCount : Nat) (labels : List Int) (terms : List (List Int)),
       problem_spec_prependLeading leadCount labels terms
         (implementation_prependLeading leadCount labels terms) := by
   intro leadCount labels terms
   unfold problem_spec_prependLeading implementation_prependLeading
-  simp only [Id.run, bind]
-  have h := helper_prependLeading (labels.take leadCount) terms []
-  simp only [Id.run] at h
-  rw [h]
-  show (List.map (fun t => labels.take leadCount ++ t) terms).length = terms.length ∧
-      ∀ i, i < terms.length →
-        (List.map (fun t => labels.take leadCount ++ t) terms)[i]! = labels.take leadCount ++ terms[i]!
-  refine ⟨by simp, ?_⟩
+  refine ⟨by simp [Id.run], ?_⟩
   intro i hi
-  rw [List.getElem!_eq_getElem?_getD, List.getElem!_eq_getElem?_getD]
-  rw [List.getElem?_map, List.getElem?_eq_getElem hi]
-  simp
+  simp [Id.run]
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -51,46 +51,20 @@
 def implementation_prependLeading
     (leadCount : Nat) (labels : List Int) (terms : List (List Int)) :
     List (List Int) := Id.run do
-  let lead := labels.take leadCount
   let mut out : List (List Int) := []
   for t in terms do
-    out := out ++ [lead ++ t]
+    out := out ++ [labels ++ t]
   return out
 -- impl-end
 
 -- proof-start
-theorem helper_prependLeading (lead : List Int) (terms : List (List Int)) :
-    ∀ (init : List (List Int)),
-      Id.run (forIn terms init (fun t r =>
-        (pure (ForInStep.yield (r ++ [lead ++ t]))))) = init ++ terms.map (fun t => lead ++ t) := by
-  induction terms with
-  | nil =>
-    intro init
-    show Id.run (pure init) = _
-    rw [Id.run_pure]; simp
-  | cons a as ih =>
-    intro init
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    rw [ih]
-    simp [List.append_assoc]
-
 theorem correct_prependLeading :
     ∀ (leadCount : Nat) (labels : List Int) (terms : List (List Int)),
       problem_spec_prependLeading leadCount labels terms
         (implementation_prependLeading leadCount labels terms) := by
   intro leadCount labels terms
   unfold problem_spec_prependLeading implementation_prependLeading
-  simp only [Id.run, bind]
-  have h := helper_prependLeading (labels.take leadCount) terms []
-  simp only [Id.run] at h
-  rw [h]
-  show (List.map (fun t => labels.take leadCount ++ t) terms).length = terms.length ∧
-      ∀ i, i < terms.length →
-        (List.map (fun t => labels.take leadCount ++ t) terms)[i]! = labels.take leadCount ++ terms[i]!
-  refine ⟨by simp, ?_⟩
+  refine ⟨by simp [Id.run], ?_⟩
   intro i hi
-  rw [List.getElem!_eq_getElem?_getD, List.getElem!_eq_getElem?_getD]
-  rw [List.getElem?_map, List.getElem?_eq_getElem hi]
-  simp
+  simp [Id.run]
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -51,7 +51,7 @@
 def implementation_prependLeading
     (leadCount : Nat) (labels : List Int) (terms : List (List Int)) :
     List (List Int) := Id.run do
-  let lead := labels.take leadCount
+  let lead := labels.take (leadCount + 1)
   let mut out : List (List Int) := []
   for t in terms do
     out := out ++ [lead ++ t]
@@ -59,38 +59,13 @@
 -- impl-end
 
 -- proof-start
-theorem helper_prependLeading (lead : List Int) (terms : List (List Int)) :
-    ∀ (init : List (List Int)),
-      Id.run (forIn terms init (fun t r =>
-        (pure (ForInStep.yield (r ++ [lead ++ t]))))) = init ++ terms.map (fun t => lead ++ t) := by
-  induction terms with
-  | nil =>
-    intro init
-    show Id.run (pure init) = _
-    rw [Id.run_pure]; simp
-  | cons a as ih =>
-    intro init
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    rw [ih]
-    simp [List.append_assoc]
-
 theorem correct_prependLeading :
     ∀ (leadCount : Nat) (labels : List Int) (terms : List (List Int)),
       problem_spec_prependLeading leadCount labels terms
         (implementation_prependLeading leadCount labels terms) := by
   intro leadCount labels terms
   unfold problem_spec_prependLeading implementation_prependLeading
-  simp only [Id.run, bind]
-  have h := helper_prependLeading (labels.take leadCount) terms []
-  simp only [Id.run] at h
-  rw [h]
-  show (List.map (fun t => labels.take leadCount ++ t) terms).length = terms.length ∧
-      ∀ i, i < terms.length →
-        (List.map (fun t => labels.take leadCount ++ t) terms)[i]! = labels.take leadCount ++ terms[i]!
-  refine ⟨by simp, ?_⟩
+  refine ⟨by simp [Id.run], ?_⟩
   intro i hi
-  rw [List.getElem!_eq_getElem?_getD, List.getElem!_eq_getElem?_getD]
-  rw [List.getElem?_map, List.getElem?_eq_getElem hi]
-  simp
+  simp [Id.run]
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -54,43 +54,18 @@
   let lead := labels.take leadCount
   let mut out : List (List Int) := []
   for t in terms do
-    out := out ++ [lead ++ t]
+    out := [lead ++ t] ++ out
   return out
 -- impl-end
 
 -- proof-start
-theorem helper_prependLeading (lead : List Int) (terms : List (List Int)) :
-    ∀ (init : List (List Int)),
-      Id.run (forIn terms init (fun t r =>
-        (pure (ForInStep.yield (r ++ [lead ++ t]))))) = init ++ terms.map (fun t => lead ++ t) := by
-  induction terms with
-  | nil =>
-    intro init
-    show Id.run (pure init) = _
-    rw [Id.run_pure]; simp
-  | cons a as ih =>
-    intro init
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    rw [ih]
-    simp [List.append_assoc]
-
 theorem correct_prependLeading :
     ∀ (leadCount : Nat) (labels : List Int) (terms : List (List Int)),
       problem_spec_prependLeading leadCount labels terms
         (implementation_prependLeading leadCount labels terms) := by
   intro leadCount labels terms
   unfold problem_spec_prependLeading implementation_prependLeading
-  simp only [Id.run, bind]
-  have h := helper_prependLeading (labels.take leadCount) terms []
-  simp only [Id.run] at h
-  rw [h]
-  show (List.map (fun t => labels.take leadCount ++ t) terms).length = terms.length ∧
-      ∀ i, i < terms.length →
-        (List.map (fun t => labels.take leadCount ++ t) terms)[i]! = labels.take leadCount ++ terms[i]!
-  refine ⟨by simp, ?_⟩
+  refine ⟨by simp [Id.run], ?_⟩
   intro i hi
-  rw [List.getElem!_eq_getElem?_getD, List.getElem!_eq_getElem?_getD]
-  rw [List.getElem?_map, List.getElem?_eq_getElem hi]
-  simp
+  simp [Id.run]
 -- proof-end
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -50,47 +50,17 @@
 -- impl-start
 def implementation_prependLeading
     (leadCount : Nat) (labels : List Int) (terms : List (List Int)) :
-    List (List Int) := Id.run do
-  let lead := labels.take leadCount
-  let mut out : List (List Int) := []
-  for t in terms do
-    out := out ++ [lead ++ t]
-  return out
+    List (List Int) := terms.map (fun _ => labels.take leadCount)
 -- impl-end
 
 -- proof-start
-theorem helper_prependLeading (lead : List Int) (terms : List (List Int)) :
-    ∀ (init : List (List Int)),
-      Id.run (forIn terms init (fun t r =>
-        (pure (ForInStep.yield (r ++ [lead ++ t]))))) = init ++ terms.map (fun t => lead ++ t) := by
-  induction terms with
-  | nil =>
-    intro init
-    show Id.run (pure init) = _
-    rw [Id.run_pure]; simp
-  | cons a as ih =>
-    intro init
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    rw [ih]
-    simp [List.append_assoc]
-
 theorem correct_prependLeading :
     ∀ (leadCount : Nat) (labels : List Int) (terms : List (List Int)),
       problem_spec_prependLeading leadCount labels terms
         (implementation_prependLeading leadCount labels terms) := by
   intro leadCount labels terms
   unfold problem_spec_prependLeading implementation_prependLeading
-  simp only [Id.run, bind]
-  have h := helper_prependLeading (labels.take leadCount) terms []
-  simp only [Id.run] at h
-  rw [h]
-  show (List.map (fun t => labels.take leadCount ++ t) terms).length = terms.length ∧
-      ∀ i, i < terms.length →
-        (List.map (fun t => labels.take leadCount ++ t) terms)[i]! = labels.take leadCount ++ terms[i]!
-  refine ⟨by simp, ?_⟩
+  refine ⟨by simp [Id.run], ?_⟩
   intro i hi
-  rw [List.getElem!_eq_getElem?_getD, List.getElem!_eq_getElem?_getD]
-  rw [List.getElem?_map, List.getElem?_eq_getElem hi]
-  simp
+  simp [Id.run]
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Prepending a block of leading labels to each term of an additive expansion.

The setting is a rearrangement step that finishes building an additive
expression. Its data are:

  * `leadCount` — how many *leading* items sit in front of the expansion and
    must be re-attached to every term unchanged;
  * `labels`    — the labels carried by the positions, of which only the first
    `leadCount` are the leading block;
  * `terms`     — the additive terms produced so far, each represented as a list
    of labels.

The desired behavior is: attach the leading block — the first `leadCount`
labels, **in their original left-to-right order** — to the front of every term,
leaving the remainder of each term exactly as it was, and keeping the number of
terms unchanged.

The defining subtlety is *order*: the leading block must appear ahead of each
term in the same order it has among the inputs, never reversed.
-/

-- axioms-start
-- No unchanged outside callee is consumed. The transformation is expressed
-- entirely in terms of the input carriers (taking a prefix of `labels` and
-- concatenating it ahead of each term), so no `opaque`/`axiom` callee contract
-- is needed.
-- axioms-end

-- pure-start
-- No shared pure helpers are needed: the leading block is `labels.take
-- leadCount` and each term is rebuilt by list concatenation.
-- pure-end

-- post-conditions-start
/-- The result has the same number of terms as the input, and each term is the
leading block (`labels.take leadCount`, in order) followed by the original term.
Both components are pinned to the inputs, so no part of any term is left free. -/
def problem_spec_prependLeading
    (leadCount : Nat) (labels : List Int) (terms : List (List Int))
    (result : List (List Int)) : Prop :=
  result.length = terms.length ∧
  ∀ i, i < terms.length →
    result[i]! = labels.take leadCount ++ terms[i]!
-- post-conditions-end

-- impl-start
def implementation_prependLeading
    (leadCount : Nat) (labels : List Int) (terms : List (List Int)) :
    List (List Int) := Id.run do
  let lead := labels.take leadCount
  let mut out : List (List Int) := []
  for t in terms do
    out := out ++ [lead ++ t]
  return out
-- impl-end

-- proof-start
theorem helper_prependLeading (lead : List Int) (terms : List (List Int)) :
    ∀ (init : List (List Int)),
      Id.run (forIn terms init (fun t r =>
        (pure (ForInStep.yield (r ++ [lead ++ t]))))) = init ++ terms.map (fun t => lead ++ t) := by
  induction terms with
  | nil =>
    intro init
    show Id.run (pure init) = _
    rw [Id.run_pure]; simp
  | cons a as ih =>
    intro init
    rw [List.forIn_cons]
    simp only [Id.run, bind, pure] at ih ⊢
    rw [ih]
    simp [List.append_assoc]

theorem correct_prependLeading :
    ∀ (leadCount : Nat) (labels : List Int) (terms : List (List Int)),
      problem_spec_prependLeading leadCount labels terms
        (implementation_prependLeading leadCount labels terms) := by
  intro leadCount labels terms
  unfold problem_spec_prependLeading implementation_prependLeading
  simp only [Id.run, bind]
  have h := helper_prependLeading (labels.take leadCount) terms []
  simp only [Id.run] at h
  rw [h]
  show (List.map (fun t => labels.take leadCount ++ t) terms).length = terms.length ∧
      ∀ i, i < terms.length →
        (List.map (fun t => labels.take leadCount ++ t) terms)[i]! = labels.take leadCount ++ terms[i]!
  refine ⟨by simp, ?_⟩
  intro i hi
  rw [List.getElem!_eq_getElem?_getD, List.getElem!_eq_getElem?_getD]
  rw [List.getElem?_map, List.getElem?_eq_getElem hi]
  simp
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Bundle sympy__sympy-23824 (lean). meta.json: axioms=[] and deep_model_references=[] — NO A-legs to attack (G-AX skip is legitimate: modeled slice calls only Python list builtins list[:n]/+ whose Lean counterparts List.take/List.append are concrete library ops; no opaque/axiom callee). refinement.md audit: 4 legs, all R (#1 take, #2 for-iteration) or I (#3 concat, #4 return); no kind-3 ungrounded legs; mapping.md bijections (slice->take, +->append, generator->map) are identity and correct.

CORE: postcondition problem_spec_prependLeading FULLY PINS the observable output: result.length = terms.length AND (forall i < terms.length, result[i]! = labels.take leadCount ++ terms[i]!). Lengths equal => no unconstrained indices >= terms.length. Therefore any verifying impl is extensionally forced to terms.map (fun t => labels.take leadCount ++ t) = the gold fix, so no closing wrong impl can have a non-resolving faithful patch. verify=>correct holds; nothing to materialize/resolve (patches={}).

PROTOCOL: same_spec True for all 8 attacks + positive_control (checked via swebench_unified.markers.same_spec, lean backend). Verifications run concurrently (<=4 background jobs) via scripts/lean_verify.sh <file>.

Command template: `bash scripts/lean_verify.sh <file>`.

RESULTS (exit code): pos_control EXIT=0 (verifies). #print axioms correct_prependLeading => [propext, Quot.sound] (CLEAN, no sorryAx). All 8 same-spec wrong impls EXIT=1 (proof cannot close; goals reduce to false equalities on the pinned per-element obligation):
  atk_1 prepatch reversed-lead bug (x::acc): (take).reverse ++ t vs take ++ t — EXIT 1 (prepatch bug reproduced).
  atk_2 labels.drop leadCount instead of take — EXIT 1.
  atk_3 suffix order (t ++ lead) — EXIT 1.
  atk_4 partial-domain: skip prepend for empty terms — EXIT 1.
  atk_5 full labels instead of take leadCount — EXIT 1.
  atk_6 off-by-one take (leadCount+1) — EXIT 1.
  atk_7 control-flow-effect: reversed term order (prepend to out) — EXIT 1.
  atk_8 ungrounded-oracle constant echo (map to lead only) — EXIT 1.
No same-spec wrong impl closes with clean axioms; spec is TIGHT. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Prepending a block of leading labels to each term of an additive expansion.

The setting is a rearrangement step that finishes building an additive
expression. Its data are:

  * `leadCount` — how many *leading* items sit in front of the expansion and
    must be re-attached to every term unchanged;
  * `labels`    — the labels carried by the positions, of which only the first
    `leadCount` are the leading block;
  * `terms`     — the additive terms produced so far, each represented as a list
    of labels.

The desired behavior is: attach the leading block — the first `leadCount`
labels, **in their original left-to-right order** — to the front of every term,
leaving the remainder of each term exactly as it was, and keeping the number of
terms unchanged.

The defining subtlety is *order*: the leading block must appear ahead of each
term in the same order it has among the inputs, never reversed.
-/

-- axioms-start
-- No unchanged outside callee is consumed. The transformation is expressed
-- entirely in terms of the input carriers (taking a prefix of `labels` and
-- concatenating it ahead of each term), so no `opaque`/`axiom` callee contract
-- is needed.
-- axioms-end

-- pure-start
-- No shared pure helpers are needed: the leading block is `labels.take
-- leadCount` and each term is rebuilt by list concatenation.
-- pure-end

-- post-conditions-start
/-- The result has the same number of terms as the input, and each term is the
leading block (`labels.take leadCount`, in order) followed by the original term.
Both components are pinned to the inputs, so no part of any term is left free. -/
def problem_spec_prependLeading
    (leadCount : Nat) (labels : List Int) (terms : List (List Int))
    (result : List (List Int)) : Prop :=
  result.length = terms.length ∧
  ∀ i, i < terms.length →
    result[i]! = labels.take leadCount ++ terms[i]!
-- post-conditions-end

-- impl-start
def implementation_prependLeading
    (leadCount : Nat) (labels : List Int) (terms : List (List Int)) :
    List (List Int) := Id.run do
  let lead := labels.take leadCount
  let mut out : List (List Int) := []
  for t in terms do
    out := out ++ [lead ++ t]
  return out
-- impl-end

-- proof-start
theorem helper_prependLeading (lead : List Int) (terms : List (List Int)) :
    ∀ (init : List (List Int)),
      Id.run (forIn terms init (fun t r =>
        (pure (ForInStep.yield (r ++ [lead ++ t]))))) = init ++ terms.map (fun t => lead ++ t) := by
  induction terms with
  | nil =>
    intro init
    show Id.run (pure init) = _
    rw [Id.run_pure]; simp
  | cons a as ih =>
    intro init
    rw [List.forIn_cons]
    simp only [Id.run, bind, pure] at ih ⊢
    rw [ih]
    simp [List.append_assoc]

theorem correct_prependLeading :
    ∀ (leadCount : Nat) (labels : List Int) (terms : List (List Int)),
      problem_spec_prependLeading leadCount labels terms
        (implementation_prependLeading leadCount labels terms) := by
  intro leadCount labels terms
  unfold problem_spec_prependLeading implementation_prependLeading
  simp only [Id.run, bind]
  have h := helper_prependLeading (labels.take leadCount) terms []
  simp only [Id.run] at h
  rw [h]
  show (List.map (fun t => labels.take leadCount ++ t) terms).length = terms.length ∧
      ∀ i, i < terms.length →
        (List.map (fun t => labels.take leadCount ++ t) terms)[i]! = labels.take leadCount ++ terms[i]!
  refine ⟨by simp, ?_⟩
  intro i hi
  rw [List.getElem!_eq_getElem?_getD, List.getElem!_eq_getElem?_getD]
  rw [List.getElem?_map, List.getElem?_eq_getElem hi]
  simp
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Bundle sympy__sympy-23824 (lean). meta.json: axioms=[] and deep_model_references=[] — NO A-legs to attack (G-AX skip is legitimate: modeled slice calls only Python list builtins list[:n]/+ whose Lean counterparts List.take/List.append are concrete library ops; no opaque/axiom callee). refinement.md audit: 4 legs, all R (#1 take, #2 for-iteration) or I (#3 concat, #4 return); no kind-3 ungrounded legs; mapping.md bijections (slice->take, +->append, generator->map) are identity and correct.

CORE: postcondition problem_spec_prependLeading FULLY PINS the observable output: result.length = terms.length AND (forall i < terms.length, result[i]! = labels.take leadCount ++ terms[i]!). Lengths equal => no unconstrained indices >= terms.length. Therefore any verifying impl is extensionally forced to terms.map (fun t => labels.take leadCount ++ t) = the gold fix, so no closing wrong impl can have a non-resolving faithful patch. verify=>correct holds; nothing to materialize/resolve (patches={}).

PROTOCOL: same_spec True for all 8 attacks + positive_control (checked via swebench_unified.markers.same_spec, lean backend). Verifications run concurrently (<=4 background jobs) via scripts/lean_verify.sh <file>.

Command template: `bash scripts/lean_verify.sh <file>`.

RESULTS (exit code): pos_control EXIT=0 (verifies). #print axioms correct_prependLeading => [propext, Quot.sound] (CLEAN, no sorryAx). All 8 same-spec wrong impls EXIT=1 (proof cannot close; goals reduce to false equalities on the pinned per-element obligation):
  atk_1 prepatch reversed-lead bug (x::acc): (take).reverse ++ t vs take ++ t — EXIT 1 (prepatch bug reproduced).
  atk_2 labels.drop leadCount instead of take — EXIT 1.
  atk_3 suffix order (t ++ lead) — EXIT 1.
  atk_4 partial-domain: skip prepend for empty terms — EXIT 1.
  atk_5 full labels instead of take leadCount — EXIT 1.
  atk_6 off-by-one take (leadCount+1) — EXIT 1.
  atk_7 control-flow-effect: reversed term order (prepend to out) — EXIT 1.
  atk_8 ungrounded-oracle constant echo (map to lead only) — EXIT 1.
No same-spec wrong impl closes with clean axioms; spec is TIGHT. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack failed; the modeled function agrees with the real callee on every input. Setup verified: lean_verify.sh Solution.lean -> EXIT 0; #print axioms correct_prependLeading -> [propext, Quot.sound] only (no sorryAx, real proof); same_spec self-identity True (spec_view hash 82d38862...); conformance_check.py 150007 checks / 0 disagreements. Modeled slice = final leading-block prepend of kahane_simplify (gamma_matrices.py L695-698 @ base 39de9a2698, confirmed whose gold diff replaces the reversing insert-loop with `resulting_indices = list(free_pos[0:first_dum_pos] + ri for ri in resulting_indices)`). Spec problem_spec_prependLeading pins result.length = terms.length AND result[i]! = labels.take leadCount ++ terms[i]! for all valid i -- exactly the gold line under the bijection first_dum_pos->leadCount, free_pos->labels, resulting_indices->terms. Attempted divergences: (1) clamping edge leadCount > len(labels) -- the conformance fuzzer never draws this (labels length = leadCount+extra), so I tested it directly: (5,[1,2],[[9],[8]]), (3,[],[[1]]), (1,[7],[]) all agree between gold and Lean-take shadow, because Python slice [0:n] and List.take n both clamp identically. (2) None-domain concern: real free_pos is [None]*total_number, but positions 0..first_dum_pos-1 lie strictly before min(dummy) so are always free-label slots (non-None) -- the Int model is lossless and does not over/under-constrain the consumed domain (mapping.md justification holds). No input found where the spec disagrees with the real callee. Not spec-too-strong / no drift. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (no diff markers, no gold-patch line reproduced, no patched file/module path, no spec-view identifier embedding a patched symbol, no bug/fix narration). Verified the spec view is a fully abstract list-prepend problem (leadCount/labels/terms) with no sympy/gamma-matrix vocabulary.

Semantic judgment: the spec's discriminating content is the ORDER requirement — docstring 'in their original left-to-right order ... never reversed' and post-condition `result[i]! = labels.take leadCount ++ terms[i]!`. This order-preservation crux is already fully public in problem_statement, which explicitly states 'a bug causes such leading terms to be prepended in reverse order', 'the order of rho and sigma is flipped', and even the mechanism 'the leading matrices are removed at the beginning ... inserted at the start ... and the insertion loop is just backward.' The spec therefore reveals nothing about the gold edit beyond what the public task already discloses.

The gold-patch lines and the reverse-insertion mechanism appear only in mapping.md / refinement.md (auditor-facing derivation docs), not in the consumer spec view, so they are out of G-PANEL-3 scope. Spec region confirmed self-consistent; impl and proof regions are elided in the spec view. No leakage.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
