# P2 adversarial audit — django__django-16877

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

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
@@ -62,33 +62,17 @@
 def implementation_escapeEach (value : List Elem) : List String := Id.run do
   let mut acc := []
   for obj in value do
-    acc := acc ++ [condEscape obj]
+    acc := acc ++ [obj.text]
   return acc
 -- impl-end
 
 -- proof-start
-theorem helper_escapeEach :
-    ∀ (xs : List Elem) (init : List String),
-      (Id.run (forIn xs init (fun obj r => do
-          pure PUnit.unit; pure (ForInStep.yield (r ++ [condEscape obj])))))
-        = init ++ xs.map condEscape := by
-  intro xs
-  induction xs with
-  | nil => intro init; simp [Id.run, pure]
-  | cons a as ih =>
-    intro init
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    rw [ih]
-    simp [List.map_cons]
-
 theorem correct_escapeEach :
     ∀ (value : List Elem),
       problem_spec_escapeEach value (implementation_escapeEach value) := by
   intro value
   unfold problem_spec_escapeEach implementation_escapeEach
-  show (Id.run (forIn value [] (fun obj r => do
-          pure PUnit.unit; pure (ForInStep.yield (r ++ [condEscape obj]))))) = _
-  rw [helper_escapeEach value []]
-  simp
+  induction value with
+  | nil => rfl
+  | cons a as ih => simp [List.forIn_cons, ih]
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,35 +60,26 @@
 
 -- impl-start
 def implementation_escapeEach (value : List Elem) : List String := Id.run do
-  let mut acc := []
-  for obj in value do
-    acc := acc ++ [condEscape obj]
-  return acc
+  match value with
+  | [] => return [""]
+  | _ =>
+    let mut acc := []
+    for obj in value do
+      acc := acc ++ [condEscape obj]
+    return acc
 -- impl-end
 
 -- proof-start
-theorem helper_escapeEach :
-    ∀ (xs : List Elem) (init : List String),
-      (Id.run (forIn xs init (fun obj r => do
-          pure PUnit.unit; pure (ForInStep.yield (r ++ [condEscape obj])))))
-        = init ++ xs.map condEscape := by
-  intro xs
-  induction xs with
-  | nil => intro init; simp [Id.run, pure]
-  | cons a as ih =>
-    intro init
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    rw [ih]
-    simp [List.map_cons]
-
 theorem correct_escapeEach :
     ∀ (value : List Elem),
       problem_spec_escapeEach value (implementation_escapeEach value) := by
   intro value
   unfold problem_spec_escapeEach implementation_escapeEach
-  show (Id.run (forIn value [] (fun obj r => do
-          pure PUnit.unit; pure (ForInStep.yield (r ++ [condEscape obj]))))) = _
-  rw [helper_escapeEach value []]
-  simp
+  cases value with
+  | nil => simp
+  | cons a as =>
+    simp only []
+    induction (a :: as) with
+    | nil => rfl
+    | cons b bs ih => simp [List.forIn_cons, ih]
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -59,36 +59,17 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_escapeEach (value : List Elem) : List String := Id.run do
-  let mut acc := []
-  for obj in value do
-    acc := acc ++ [condEscape obj]
-  return acc
+def implementation_escapeEach (value : List Elem) : List String :=
+  value.dropLast.map condEscape
 -- impl-end
 
 -- proof-start
-theorem helper_escapeEach :
-    ∀ (xs : List Elem) (init : List String),
-      (Id.run (forIn xs init (fun obj r => do
-          pure PUnit.unit; pure (ForInStep.yield (r ++ [condEscape obj])))))
-        = init ++ xs.map condEscape := by
-  intro xs
-  induction xs with
-  | nil => intro init; simp [Id.run, pure]
-  | cons a as ih =>
-    intro init
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    rw [ih]
-    simp [List.map_cons]
-
 theorem correct_escapeEach :
     ∀ (value : List Elem),
       problem_spec_escapeEach value (implementation_escapeEach value) := by
   intro value
   unfold problem_spec_escapeEach implementation_escapeEach
-  show (Id.run (forIn value [] (fun obj r => do
-          pure PUnit.unit; pure (ForInStep.yield (r ++ [condEscape obj]))))) = _
-  rw [helper_escapeEach value []]
-  simp
+  cases value with
+  | nil => rfl
+  | cons a as => simp [List.map]
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,33 +62,17 @@
 def implementation_escapeEach (value : List Elem) : List String := Id.run do
   let mut acc := []
   for obj in value do
-    acc := acc ++ [condEscape obj]
+    acc := [condEscape obj] ++ acc
   return acc
 -- impl-end
 
 -- proof-start
-theorem helper_escapeEach :
-    ∀ (xs : List Elem) (init : List String),
-      (Id.run (forIn xs init (fun obj r => do
-          pure PUnit.unit; pure (ForInStep.yield (r ++ [condEscape obj])))))
-        = init ++ xs.map condEscape := by
-  intro xs
-  induction xs with
-  | nil => intro init; simp [Id.run, pure]
-  | cons a as ih =>
-    intro init
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    rw [ih]
-    simp [List.map_cons]
-
 theorem correct_escapeEach :
     ∀ (value : List Elem),
       problem_spec_escapeEach value (implementation_escapeEach value) := by
   intro value
   unfold problem_spec_escapeEach implementation_escapeEach
-  show (Id.run (forIn value [] (fun obj r => do
-          pure PUnit.unit; pure (ForInStep.yield (r ++ [condEscape obj]))))) = _
-  rw [helper_escapeEach value []]
-  simp
+  induction value with
+  | nil => rfl
+  | cons a as ih => simp [List.forIn_cons, ih]
 -- proof-end
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -59,36 +59,14 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_escapeEach (value : List Elem) : List String := Id.run do
-  let mut acc := []
-  for obj in value do
-    acc := acc ++ [condEscape obj]
-  return acc
+def implementation_escapeEach (value : List Elem) : List String :=
+  value.map condEscape
 -- impl-end
 
 -- proof-start
-theorem helper_escapeEach :
-    ∀ (xs : List Elem) (init : List String),
-      (Id.run (forIn xs init (fun obj r => do
-          pure PUnit.unit; pure (ForInStep.yield (r ++ [condEscape obj])))))
-        = init ++ xs.map condEscape := by
-  intro xs
-  induction xs with
-  | nil => intro init; simp [Id.run, pure]
-  | cons a as ih =>
-    intro init
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    rw [ih]
-    simp [List.map_cons]
-
 theorem correct_escapeEach :
     ∀ (value : List Elem),
       problem_spec_escapeEach value (implementation_escapeEach value) := by
   intro value
-  unfold problem_spec_escapeEach implementation_escapeEach
-  show (Id.run (forIn value [] (fun obj r => do
-          pure PUnit.unit; pure (ForInStep.yield (r ++ [condEscape obj]))))) = _
-  rw [helper_escapeEach value []]
-  simp
+  rfl
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -59,36 +59,19 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_escapeEach (value : List Elem) : List String := Id.run do
-  let mut acc := []
-  for obj in value do
-    acc := acc ++ [condEscape obj]
-  return acc
+def implementation_escapeEach (value : List Elem) : List String :=
+  match value with
+  | [] => []
+  | x :: _ => condEscape x :: value.map condEscape
 -- impl-end
 
 -- proof-start
-theorem helper_escapeEach :
-    ∀ (xs : List Elem) (init : List String),
-      (Id.run (forIn xs init (fun obj r => do
-          pure PUnit.unit; pure (ForInStep.yield (r ++ [condEscape obj])))))
-        = init ++ xs.map condEscape := by
-  intro xs
-  induction xs with
-  | nil => intro init; simp [Id.run, pure]
-  | cons a as ih =>
-    intro init
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    rw [ih]
-    simp [List.map_cons]
-
 theorem correct_escapeEach :
     ∀ (value : List Elem),
       problem_spec_escapeEach value (implementation_escapeEach value) := by
   intro value
   unfold problem_spec_escapeEach implementation_escapeEach
-  show (Id.run (forIn value [] (fun obj r => do
-          pure PUnit.unit; pure (ForInStep.yield (r ++ [condEscape obj]))))) = _
-  rw [helper_escapeEach value []]
-  simp
+  cases value with
+  | nil => rfl
+  | cons a as => simp [List.map_cons]
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,34 +61,18 @@
 -- impl-start
 def implementation_escapeEach (value : List Elem) : List String := Id.run do
   let mut acc := []
-  for obj in value do
-    acc := acc ++ [condEscape obj]
+  for _ in value do
+    acc := acc ++ [""]
   return acc
 -- impl-end
 
 -- proof-start
-theorem helper_escapeEach :
-    ∀ (xs : List Elem) (init : List String),
-      (Id.run (forIn xs init (fun obj r => do
-          pure PUnit.unit; pure (ForInStep.yield (r ++ [condEscape obj])))))
-        = init ++ xs.map condEscape := by
-  intro xs
-  induction xs with
-  | nil => intro init; simp [Id.run, pure]
-  | cons a as ih =>
-    intro init
-    rw [List.forIn_cons]
-    simp only [Id.run, bind, pure] at ih ⊢
-    rw [ih]
-    simp [List.map_cons]
-
 theorem correct_escapeEach :
     ∀ (value : List Elem),
       problem_spec_escapeEach value (implementation_escapeEach value) := by
   intro value
   unfold problem_spec_escapeEach implementation_escapeEach
-  show (Id.run (forIn value [] (fun obj r => do
-          pure PUnit.unit; pure (ForInStep.yield (r ++ [condEscape obj]))))) = _
-  rw [helper_escapeEach value []]
-  simp
+  induction value with
+  | nil => rfl
+  | cons a as ih => simp [List.forIn_cons, ih]
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
A template filter that escapes every element of a sequence individually.

Some template filters mark text as safe-for-HTML by escaping the characters that
the HTML engine would otherwise interpret. There is an established filter that
performs this escaping decision on a single value; this bundle models the
companion filter that applies the SAME per-element escaping decision to each
member of a sequence, returning the resulting list.

The desired behavior is:

  * the result is a list with exactly one entry per element of the input
    sequence, in the same order; and

  * each entry is the per-element escaping decision applied to the corresponding
    input element.

The per-element escaping decision is the unchanged, shared HTML-escaping
behavior (a conditional HTML escaper that escapes ordinary text but leaves
content already marked safe untouched). It is referenced opaquely here: the
specification does not pin its concrete output, only that each result entry is
exactly the value that escaper yields for the corresponding input element.
-/

-- axioms-start
/-- An element of the input sequence, modeled by the attributes the per-element
escaper observes about it: whether the element is already marked safe (in which
case the escaper leaves it untouched) and its underlying text. -/
structure Elem where
  /-- Whether this element is already marked safe-for-HTML. -/
  isSafe : Bool
  /-- The underlying text of this element. -/
  text : String
deriving DecidableEq, Repr

/-- The unchanged, shared per-element HTML-escaping decision applied to a single
element. It escapes ordinary text but returns content already marked safe
untouched. It is referenced opaquely: the specification pins each result entry to
its value, but consumes no property of it. -/
opaque condEscape : Elem → String
-- axioms-end

-- pure-start
-- No additional pure helpers are required: the modeled behavior is the
-- element-wise application of the per-element escaper over the input sequence.
-- pure-end

-- post-conditions-start
/-- Escaping each element of a sequence individually. The result is fully
determined: it is the list obtained by applying the per-element escaper
`condEscape` to every element of `value`, in order. This pins the length (one
entry per input element), the order, and each entry's value; no component of the
result is left unconstrained. -/
def problem_spec_escapeEach (value : List Elem) (result : List String) : Prop :=
  result = value.map condEscape
-- post-conditions-end

-- impl-start
def implementation_escapeEach (value : List Elem) : List String := Id.run do
  let mut acc := []
  for obj in value do
    acc := acc ++ [condEscape obj]
  return acc
-- impl-end

-- proof-start
theorem helper_escapeEach :
    ∀ (xs : List Elem) (init : List String),
      (Id.run (forIn xs init (fun obj r => do
          pure PUnit.unit; pure (ForInStep.yield (r ++ [condEscape obj])))))
        = init ++ xs.map condEscape := by
  intro xs
  induction xs with
  | nil => intro init; simp [Id.run, pure]
  | cons a as ih =>
    intro init
    rw [List.forIn_cons]
    simp only [Id.run, bind, pure] at ih ⊢
    rw [ih]
    simp [List.map_cons]

theorem correct_escapeEach :
    ∀ (value : List Elem),
      problem_spec_escapeEach value (implementation_escapeEach value) := by
  intro value
  unfold problem_spec_escapeEach implementation_escapeEach
  show (Id.run (forIn value [] (fun obj r => do
          pure PUnit.unit; pure (ForInStep.yield (r ++ [condEscape obj]))))) = _
  rw [helper_escapeEach value []]
  simp
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec is a COMPLETE fully-determined functional spec: problem_spec_escapeEach value result := result = value.map condEscape, with `opaque condEscape : Elem -> String` carrying NO consumable property. Any impl whose correct_escapeEach closes must be provably `= value.map condEscape` for ALL inputs against a SYMBOLIC condEscape, i.e. extensionally identical to gold -> its faithful patch computes [conditional_escape(obj) for obj in value] -> resolves. So verify==correct here; no verified-but-wrong witness can exist.

 Verifier: `bash scripts/lean_verify.sh <file>`. same_spec: swebench_unified.markers.same_spec(Solution.lean, atk, lean) — True for ALL 7 attacks + pos_control.

### ATTACKS (all same_spec=True; spec/axioms/pure/pre/post byte-identical, only impl+proof region edited):
- atk_1 PREPATCH BUG (acc ++ [obj.text], no escaping): lean_verify exit 1 — unsolved goal `a.text = condEscape a` (opaque condEscape unprovable). prepatch_reproduced=true.
- atk_2 PARTIAL-DOMAIN (empty input -> [""], else correct): exit 1 — unsolved goals (empty-case `[""] = []` and cons-branch).
- atk_3 BOUNDARY (value.dropLast.map condEscape, drops last elem): exit 1 — goal `(condEscape a :: map).dropLast = condEscape a :: map`.
- atk_4 CONTROL-FLOW-EFFECT (prepend => reversed order): exit 1 — unsolved goals (reversed != forward map).
- atk_5 UNGROUNDED-ORACLE ECHO / behaviorally-CORRECT (value.map condEscape): lean_verify exit 0; `#print axioms correct_escapeEach` => 'does not depend on any axioms' (clean, no sorryAx). MATERIALIZED faithful patch (the escapeseq filter = [conditional_escape(obj) for obj in value]) and RAN run_resolve(django__django-16877, ...) => RESOLVED=True, completed=True, note='resolved'. Per RESOLVED G-PANEL-1/echo policy a same-spec verifying impl whose refined patch RESOLVES is NOT a weakness — this is the verify=>resolve correspondence control, confirms spec is not broken.
- atk_6 OFF-BY-ONE (condEscape head :: value.map condEscape, dup first): exit 1 — unsolved goals.
- atk_7 UNGROUNDED-ORACLE (constant "" per elem): exit 1 — unsolved goals ("" != condEscape a).

Every wrong impl (atk_1,2,3,4,6,7) fails with GENUINE 'unsolved goals' proof-obligation errors (verified in .out files), NOT syntax/timeout artifacts. Each residual goal is precisely the behavioral divergence the opaque condEscape makes unprovable. pos_control (gold Solution.lean) lean_verify exit 0.

The ONLY impl that closes (atk_5) is behaviorally identical to gold and RESOLVES. No impl with a closing clean-axiom proof has a materialized faithful patch that does NOT resolve => NOT BROKEN.

REFINEMENT AUDIT: all legs R / I / A-reference, NO kind-3. Ops 1(R),2(I),3(R+A-reference),4(R),type(R). The sole A-leg is condEscape (A-reference, no consumed axiom — meta.json axioms=[], deep_model_references=[condEscape]). Correspondence holds: condEscape <-> real conditional_escape (django/utils/html.py:92, confirmed present & UNCHANGED by patch), branches only on __html__/str content = exactly Elem{isSafe,text}; G-AX validated total+string-valued (50039 checks). Proof consumes no property of condEscape (loop-fold induction), so reference (not axiomatized) is correct.

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
A template filter that escapes every element of a sequence individually.

Some template filters mark text as safe-for-HTML by escaping the characters that
the HTML engine would otherwise interpret. There is an established filter that
performs this escaping decision on a single value; this bundle models the
companion filter that applies the SAME per-element escaping decision to each
member of a sequence, returning the resulting list.

The desired behavior is:

  * the result is a list with exactly one entry per element of the input
    sequence, in the same order; and

  * each entry is the per-element escaping decision applied to the corresponding
    input element.

The per-element escaping decision is the unchanged, shared HTML-escaping
behavior (a conditional HTML escaper that escapes ordinary text but leaves
content already marked safe untouched). It is referenced opaquely here: the
specification does not pin its concrete output, only that each result entry is
exactly the value that escaper yields for the corresponding input element.
-/

-- axioms-start
/-- An element of the input sequence, modeled by the attributes the per-element
escaper observes about it: whether the element is already marked safe (in which
case the escaper leaves it untouched) and its underlying text. -/
structure Elem where
  /-- Whether this element is already marked safe-for-HTML. -/
  isSafe : Bool
  /-- The underlying text of this element. -/
  text : String
deriving DecidableEq, Repr

/-- The unchanged, shared per-element HTML-escaping decision applied to a single
element. It escapes ordinary text but returns content already marked safe
untouched. It is referenced opaquely: the specification pins each result entry to
its value, but consumes no property of it. -/
opaque condEscape : Elem → String
-- axioms-end

-- pure-start
-- No additional pure helpers are required: the modeled behavior is the
-- element-wise application of the per-element escaper over the input sequence.
-- pure-end

-- post-conditions-start
/-- Escaping each element of a sequence individually. The result is fully
determined: it is the list obtained by applying the per-element escaper
`condEscape` to every element of `value`, in order. This pins the length (one
entry per input element), the order, and each entry's value; no component of the
result is left unconstrained. -/
def problem_spec_escapeEach (value : List Elem) (result : List String) : Prop :=
  result = value.map condEscape
-- post-conditions-end

-- impl-start
def implementation_escapeEach (value : List Elem) : List String := Id.run do
  let mut acc := []
  for obj in value do
    acc := acc ++ [condEscape obj]
  return acc
-- impl-end

-- proof-start
theorem helper_escapeEach :
    ∀ (xs : List Elem) (init : List String),
      (Id.run (forIn xs init (fun obj r => do
          pure PUnit.unit; pure (ForInStep.yield (r ++ [condEscape obj])))))
        = init ++ xs.map condEscape := by
  intro xs
  induction xs with
  | nil => intro init; simp [Id.run, pure]
  | cons a as ih =>
    intro init
    rw [List.forIn_cons]
    simp only [Id.run, bind, pure] at ih ⊢
    rw [ih]
    simp [List.map_cons]

theorem correct_escapeEach :
    ∀ (value : List Elem),
      problem_spec_escapeEach value (implementation_escapeEach value) := by
  intro value
  unfold problem_spec_escapeEach implementation_escapeEach
  show (Id.run (forIn value [] (fun obj r => do
          pure PUnit.unit; pure (ForInStep.yield (r ++ [condEscape obj]))))) = _
  rw [helper_escapeEach value []]
  simp
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec is a COMPLETE fully-determined functional spec: problem_spec_escapeEach value result := result = value.map condEscape, with `opaque condEscape : Elem -> String` carrying NO consumable property. Any impl whose correct_escapeEach closes must be provably `= value.map condEscape` for ALL inputs against a SYMBOLIC condEscape, i.e. extensionally identical to gold -> its faithful patch computes [conditional_escape(obj) for obj in value] -> resolves. So verify==correct here; no verified-but-wrong witness can exist.

 Verifier: `bash scripts/lean_verify.sh <file>`. same_spec: swebench_unified.markers.same_spec(Solution.lean, atk, lean) — True for ALL 7 attacks + pos_control.

### ATTACKS (all same_spec=True; spec/axioms/pure/pre/post byte-identical, only impl+proof region edited):
- atk_1 PREPATCH BUG (acc ++ [obj.text], no escaping): lean_verify exit 1 — unsolved goal `a.text = condEscape a` (opaque condEscape unprovable). prepatch_reproduced=true.
- atk_2 PARTIAL-DOMAIN (empty input -> [""], else correct): exit 1 — unsolved goals (empty-case `[""] = []` and cons-branch).
- atk_3 BOUNDARY (value.dropLast.map condEscape, drops last elem): exit 1 — goal `(condEscape a :: map).dropLast = condEscape a :: map`.
- atk_4 CONTROL-FLOW-EFFECT (prepend => reversed order): exit 1 — unsolved goals (reversed != forward map).
- atk_5 UNGROUNDED-ORACLE ECHO / behaviorally-CORRECT (value.map condEscape): lean_verify exit 0; `#print axioms correct_escapeEach` => 'does not depend on any axioms' (clean, no sorryAx). MATERIALIZED faithful patch (the escapeseq filter = [conditional_escape(obj) for obj in value]) and RAN run_resolve(django__django-16877, ...) => RESOLVED=True, completed=True, note='resolved'. Per RESOLVED G-PANEL-1/echo policy a same-spec verifying impl whose refined patch RESOLVES is NOT a weakness — this is the verify=>resolve correspondence control, confirms spec is not broken.
- atk_6 OFF-BY-ONE (condEscape head :: value.map condEscape, dup first): exit 1 — unsolved goals.
- atk_7 UNGROUNDED-ORACLE (constant "" per elem): exit 1 — unsolved goals ("" != condEscape a).

Every wrong impl (atk_1,2,3,4,6,7) fails with GENUINE 'unsolved goals' proof-obligation errors (verified in .out files), NOT syntax/timeout artifacts. Each residual goal is precisely the behavioral divergence the opaque condEscape makes unprovable. pos_control (gold Solution.lean) lean_verify exit 0.

The ONLY impl that closes (atk_5) is behaviorally identical to gold and RESOLVES. No impl with a closing clean-axiom proof has a materialized faithful patch that does NOT resolve => NOT BROKEN.

REFINEMENT AUDIT: all legs R / I / A-reference, NO kind-3. Ops 1(R),2(I),3(R+A-reference),4(R),type(R). The sole A-leg is condEscape (A-reference, no consumed axiom — meta.json axioms=[], deep_model_references=[condEscape]). Correspondence holds: condEscape <-> real conditional_escape (django/utils/html.py:92, confirmed present & UNCHANGED by patch), branches only on __html__/str content = exactly Elem{isSafe,text}; G-AX validated total+string-valued (50039 checks). Proof consumes no property of condEscape (loop-fold induction), so reference (not axiomatized) is correct.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on django__django-16877/lean. Real callee (gold patch, django/template/defaultfilters.py): escapeseq(value) = [conditional_escape(obj) for obj in value]; conditional_escape (html.py:82-94) UNCHANGED by patch. Spec: problem_spec_escapeEach value result := result = value.map condEscape, where condEscape is an OPAQUE A-reference bound to the real conditional_escape.

TOO-STRONG probe: the spec pins the result completely to value.map condEscape (length = |value|, same order, each entry = condEscape obj). Because condEscape is opaque and IS the real callee, the spec demands exactly what the real function yields on every element — it cannot over-constrain. No input in the modeled domain (List Elem) produces a real escapeseq result the spec would reject.

DRIFT probe: value.map condEscape is a term-for-term match of the Python list comprehension [conditional_escape(obj) for obj in value] — identical order, identical length, identical per-element mapping. The List Elem <-> iterable and List String <-> list[str] correspondences are domain abstractions, not strengthenings. Elem carries exactly the two observables conditional_escape branches on (hasattr __html__ / str content).

MECHANICAL confirmation: (1) same_spec(Solution.lean, Solution_prepatch.lean, lean backend) = True — spec region byte-identical; spec_view clean (impl/proof elided). (2) lean_verify.sh Solution.lean exit 0; appended #print axioms correct_escapeEach = [propext, Quot.sound] — NO sorryAx, proof is genuine, not fake. (3) G-CONF conformance_check.py transliteration (shadow = accumulator append of REAL conditional_escape) vs oracle (real patched escapeseq): checked 120007 fuzzed+edge inputs (empty, metachar, mark_safe, mixed), disagreements=0. (4) Prepatch buggy impl (raw obj.text) fails to typecheck (leaves goal a.text = condEscape a) — valid G-DIFF: the spec sees the bug.

No diverging input found. Spec is neither too strong nor drifting. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (leakage.screen -> passed=True, hard_failures=[]) and adversarial semantic review agrees. Public problem_statement already discloses the entire behavioral intent: 'New template filter escapeseq ... to escape what safeseq is to safe ... where each item of some_list is escaped before applying the join operation ... autoescape is off.' The gold edit is exactly the addition of that per-element-escape filter (`[conditional_escape(obj) for obj in value]`). The spec view stays within that public envelope: (1) it describes the desired behavior — one output entry per input element, same order, each entry the per-element escape decision — which the task itself already states; (2) patched repo symbols are NOT echoed: Lean uses `escapeEach`/`condEscape` instead of `escapeseq`/`conditional_escape` (changed_symbols {escapeseq, escape_filter} do not appear as identifiers or in comments); (3) no patched file path (defaultfilters.py), no module path, no diff markers, and no gold-patch line is reproduced; (4) no bug/fix/patch narration in comments. The 'conditional escaper that escapes ordinary text but leaves already-safe content untouched' phrasing is inherent to 'escape what safeseq is to safe' (standard Django escape/safe semantics) and is referenced opaquely (condEscape is `opaque`; spec pins no concrete output), so it discloses nothing about the edit's location or form beyond the public statement. The impl/proof regions are elided from the spec view entirely. No line leaks the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
