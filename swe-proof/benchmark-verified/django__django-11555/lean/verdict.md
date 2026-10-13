# P2 adversarial audit — django__django-11555

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec wrong implementation produced a closing correct_expandOrdering proof, so there is no closing-clean-axiom impl whose faithful patch could be resolve-tested. verify does NOT diverge from correct here.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -73,59 +73,20 @@
 
 -- impl-start
 def implementation_expandOrdering
-    (items : List OrderingItem) : List (OrderExpr × Bool) := Id.run do
-  let mut results : List (OrderExpr × Bool) := []
-  for item in items do
-    match item with
-    | .expression e =>
-        -- Already a directive: emit it directly (flagged `false`) and move on,
-        -- skipping name resolution.
-        results := results ++ [(e, false)]
-    | .fieldRef _ =>
-        results := results ++ resolveFieldRef item
-  return results
+    (items : List OrderingItem) : List (OrderExpr × Bool) :=
+  items.flatMap resolveFieldRef
 -- impl-end
 
 -- proof-start
-theorem helper_expandOrdering (items : List OrderingItem)
-    (init : List (OrderExpr × Bool)) :
-    Id.run (forIn items init (fun item r =>
-        (match item with
-          | OrderingItem.expression e => ForInStep.yield (r ++ [(e, false)])
-          | OrderingItem.fieldRef _ => ForInStep.yield (r ++ resolveFieldRef item)
-          : Id (ForInStep (List (OrderExpr × Bool))))))
-      = init ++ items.flatMap expandOrderingItem := by
-  induction items generalizing init with
-  | nil => simp only [List.forIn_nil, Id.run, pure, List.flatMap_nil, List.append_nil]
-  | cons a as ih =>
-      rw [List.forIn_cons]
-      simp only [Id.run, bind] at ih ⊢
-      cases a with
-      | expression e =>
-          simp only [expandOrderingItem, List.flatMap_cons, ih, List.append_assoc]
-      | fieldRef name =>
-          simp only [expandOrderingItem, List.flatMap_cons, ih, List.append_assoc]
-
 theorem correct_expandOrdering :
     ∀ (items : List OrderingItem),
       problem_spec_expandOrdering items (implementation_expandOrdering items) := by
   intro items
   unfold problem_spec_expandOrdering implementation_expandOrdering
-  have h2 : (Id.run do
-        let r ← forIn items [] fun item r =>
-            match item with
-            | OrderingItem.expression e => do
-              pure PUnit.unit
-              pure (ForInStep.yield (r ++ [(e, false)]))
-            | OrderingItem.fieldRef _ => do
-              pure PUnit.unit
-              pure (ForInStep.yield (r ++ resolveFieldRef item))
-        pure r)
-      = Id.run (forIn items [] (fun item r =>
-        (match item with
-          | OrderingItem.expression e => ForInStep.yield (r ++ [(e, false)])
-          | OrderingItem.fieldRef _ => ForInStep.yield (r ++ resolveFieldRef item)
-          : Id (ForInStep (List (OrderExpr × Bool)))))) := rfl
-  rw [h2, helper_expandOrdering]
-  simp
+  induction items with
+  | nil => simp
+  | cons a as ih =>
+      cases a with
+      | expression e => simp [expandOrderingItem, ih]
+      | fieldRef name => simp [expandOrderingItem, ih]
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -73,59 +73,23 @@
 
 -- impl-start
 def implementation_expandOrdering
-    (items : List OrderingItem) : List (OrderExpr × Bool) := Id.run do
-  let mut results : List (OrderExpr × Bool) := []
-  for item in items do
+    (items : List OrderingItem) : List (OrderExpr × Bool) :=
+  items.flatMap (fun item =>
     match item with
-    | .expression e =>
-        -- Already a directive: emit it directly (flagged `false`) and move on,
-        -- skipping name resolution.
-        results := results ++ [(e, false)]
-    | .fieldRef _ =>
-        results := results ++ resolveFieldRef item
-  return results
+    | .expression e => [(e, true)]
+    | .fieldRef _   => resolveFieldRef item)
 -- impl-end
 
 -- proof-start
-theorem helper_expandOrdering (items : List OrderingItem)
-    (init : List (OrderExpr × Bool)) :
-    Id.run (forIn items init (fun item r =>
-        (match item with
-          | OrderingItem.expression e => ForInStep.yield (r ++ [(e, false)])
-          | OrderingItem.fieldRef _ => ForInStep.yield (r ++ resolveFieldRef item)
-          : Id (ForInStep (List (OrderExpr × Bool))))))
-      = init ++ items.flatMap expandOrderingItem := by
-  induction items generalizing init with
-  | nil => simp only [List.forIn_nil, Id.run, pure, List.flatMap_nil, List.append_nil]
-  | cons a as ih =>
-      rw [List.forIn_cons]
-      simp only [Id.run, bind] at ih ⊢
-      cases a with
-      | expression e =>
-          simp only [expandOrderingItem, List.flatMap_cons, ih, List.append_assoc]
-      | fieldRef name =>
-          simp only [expandOrderingItem, List.flatMap_cons, ih, List.append_assoc]
-
 theorem correct_expandOrdering :
     ∀ (items : List OrderingItem),
       problem_spec_expandOrdering items (implementation_expandOrdering items) := by
   intro items
   unfold problem_spec_expandOrdering implementation_expandOrdering
-  have h2 : (Id.run do
-        let r ← forIn items [] fun item r =>
-            match item with
-            | OrderingItem.expression e => do
-              pure PUnit.unit
-              pure (ForInStep.yield (r ++ [(e, false)]))
-            | OrderingItem.fieldRef _ => do
-              pure PUnit.unit
-              pure (ForInStep.yield (r ++ resolveFieldRef item))
-        pure r)
-      = Id.run (forIn items [] (fun item r =>
-        (match item with
-          | OrderingItem.expression e => ForInStep.yield (r ++ [(e, false)])
-          | OrderingItem.fieldRef _ => ForInStep.yield (r ++ resolveFieldRef item)
-          : Id (ForInStep (List (OrderExpr × Bool)))))) := rfl
-  rw [h2, helper_expandOrdering]
-  simp
+  induction items with
+  | nil => simp
+  | cons a as ih =>
+      cases a with
+      | expression e => simp [expandOrderingItem, ih]
+      | fieldRef name => simp [expandOrderingItem, ih]
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -73,59 +73,17 @@
 
 -- impl-start
 def implementation_expandOrdering
-    (items : List OrderingItem) : List (OrderExpr × Bool) := Id.run do
-  let mut results : List (OrderExpr × Bool) := []
-  for item in items do
-    match item with
-    | .expression e =>
-        -- Already a directive: emit it directly (flagged `false`) and move on,
-        -- skipping name resolution.
-        results := results ++ [(e, false)]
-    | .fieldRef _ =>
-        results := results ++ resolveFieldRef item
-  return results
+    (items : List OrderingItem) : List (OrderExpr × Bool) :=
+  []
 -- impl-end
 
 -- proof-start
-theorem helper_expandOrdering (items : List OrderingItem)
-    (init : List (OrderExpr × Bool)) :
-    Id.run (forIn items init (fun item r =>
-        (match item with
-          | OrderingItem.expression e => ForInStep.yield (r ++ [(e, false)])
-          | OrderingItem.fieldRef _ => ForInStep.yield (r ++ resolveFieldRef item)
-          : Id (ForInStep (List (OrderExpr × Bool))))))
-      = init ++ items.flatMap expandOrderingItem := by
-  induction items generalizing init with
-  | nil => simp only [List.forIn_nil, Id.run, pure, List.flatMap_nil, List.append_nil]
-  | cons a as ih =>
-      rw [List.forIn_cons]
-      simp only [Id.run, bind] at ih ⊢
-      cases a with
-      | expression e =>
-          simp only [expandOrderingItem, List.flatMap_cons, ih, List.append_assoc]
-      | fieldRef name =>
-          simp only [expandOrderingItem, List.flatMap_cons, ih, List.append_assoc]
-
 theorem correct_expandOrdering :
     ∀ (items : List OrderingItem),
       problem_spec_expandOrdering items (implementation_expandOrdering items) := by
   intro items
   unfold problem_spec_expandOrdering implementation_expandOrdering
-  have h2 : (Id.run do
-        let r ← forIn items [] fun item r =>
-            match item with
-            | OrderingItem.expression e => do
-              pure PUnit.unit
-              pure (ForInStep.yield (r ++ [(e, false)]))
-            | OrderingItem.fieldRef _ => do
-              pure PUnit.unit
-              pure (ForInStep.yield (r ++ resolveFieldRef item))
-        pure r)
-      = Id.run (forIn items [] (fun item r =>
-        (match item with
-          | OrderingItem.expression e => ForInStep.yield (r ++ [(e, false)])
-          | OrderingItem.fieldRef _ => ForInStep.yield (r ++ resolveFieldRef item)
-          : Id (ForInStep (List (OrderExpr × Bool)))))) := rfl
-  rw [h2, helper_expandOrdering]
-  simp
+  induction items with
+  | nil => simp
+  | cons a as ih => simp_all [expandOrderingItem]
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -73,59 +73,15 @@
 
 -- impl-start
 def implementation_expandOrdering
-    (items : List OrderingItem) : List (OrderExpr × Bool) := Id.run do
-  let mut results : List (OrderExpr × Bool) := []
-  for item in items do
-    match item with
-    | .expression e =>
-        -- Already a directive: emit it directly (flagged `false`) and move on,
-        -- skipping name resolution.
-        results := results ++ [(e, false)]
-    | .fieldRef _ =>
-        results := results ++ resolveFieldRef item
-  return results
+    (items : List OrderingItem) : List (OrderExpr × Bool) :=
+  (items.flatMap expandOrderingItem).reverse
 -- impl-end
 
 -- proof-start
-theorem helper_expandOrdering (items : List OrderingItem)
-    (init : List (OrderExpr × Bool)) :
-    Id.run (forIn items init (fun item r =>
-        (match item with
-          | OrderingItem.expression e => ForInStep.yield (r ++ [(e, false)])
-          | OrderingItem.fieldRef _ => ForInStep.yield (r ++ resolveFieldRef item)
-          : Id (ForInStep (List (OrderExpr × Bool))))))
-      = init ++ items.flatMap expandOrderingItem := by
-  induction items generalizing init with
-  | nil => simp only [List.forIn_nil, Id.run, pure, List.flatMap_nil, List.append_nil]
-  | cons a as ih =>
-      rw [List.forIn_cons]
-      simp only [Id.run, bind] at ih ⊢
-      cases a with
-      | expression e =>
-          simp only [expandOrderingItem, List.flatMap_cons, ih, List.append_assoc]
-      | fieldRef name =>
-          simp only [expandOrderingItem, List.flatMap_cons, ih, List.append_assoc]
-
 theorem correct_expandOrdering :
     ∀ (items : List OrderingItem),
       problem_spec_expandOrdering items (implementation_expandOrdering items) := by
   intro items
   unfold problem_spec_expandOrdering implementation_expandOrdering
-  have h2 : (Id.run do
-        let r ← forIn items [] fun item r =>
-            match item with
-            | OrderingItem.expression e => do
-              pure PUnit.unit
-              pure (ForInStep.yield (r ++ [(e, false)]))
-            | OrderingItem.fieldRef _ => do
-              pure PUnit.unit
-              pure (ForInStep.yield (r ++ resolveFieldRef item))
-        pure r)
-      = Id.run (forIn items [] (fun item r =>
-        (match item with
-          | OrderingItem.expression e => ForInStep.yield (r ++ [(e, false)])
-          | OrderingItem.fieldRef _ => ForInStep.yield (r ++ resolveFieldRef item)
-          : Id (ForInStep (List (OrderExpr × Bool)))))) := rfl
-  rw [h2, helper_expandOrdering]
   simp
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -73,59 +73,23 @@
 
 -- impl-start
 def implementation_expandOrdering
-    (items : List OrderingItem) : List (OrderExpr × Bool) := Id.run do
-  let mut results : List (OrderExpr × Bool) := []
-  for item in items do
+    (items : List OrderingItem) : List (OrderExpr × Bool) :=
+  items.flatMap (fun item =>
     match item with
-    | .expression e =>
-        -- Already a directive: emit it directly (flagged `false`) and move on,
-        -- skipping name resolution.
-        results := results ++ [(e, false)]
-    | .fieldRef _ =>
-        results := results ++ resolveFieldRef item
-  return results
+    | .expression e => [(e, false), (e, false)]
+    | .fieldRef _   => resolveFieldRef item)
 -- impl-end
 
 -- proof-start
-theorem helper_expandOrdering (items : List OrderingItem)
-    (init : List (OrderExpr × Bool)) :
-    Id.run (forIn items init (fun item r =>
-        (match item with
-          | OrderingItem.expression e => ForInStep.yield (r ++ [(e, false)])
-          | OrderingItem.fieldRef _ => ForInStep.yield (r ++ resolveFieldRef item)
-          : Id (ForInStep (List (OrderExpr × Bool))))))
-      = init ++ items.flatMap expandOrderingItem := by
-  induction items generalizing init with
-  | nil => simp only [List.forIn_nil, Id.run, pure, List.flatMap_nil, List.append_nil]
-  | cons a as ih =>
-      rw [List.forIn_cons]
-      simp only [Id.run, bind] at ih ⊢
-      cases a with
-      | expression e =>
-          simp only [expandOrderingItem, List.flatMap_cons, ih, List.append_assoc]
-      | fieldRef name =>
-          simp only [expandOrderingItem, List.flatMap_cons, ih, List.append_assoc]
-
 theorem correct_expandOrdering :
     ∀ (items : List OrderingItem),
       problem_spec_expandOrdering items (implementation_expandOrdering items) := by
   intro items
   unfold problem_spec_expandOrdering implementation_expandOrdering
-  have h2 : (Id.run do
-        let r ← forIn items [] fun item r =>
-            match item with
-            | OrderingItem.expression e => do
-              pure PUnit.unit
-              pure (ForInStep.yield (r ++ [(e, false)]))
-            | OrderingItem.fieldRef _ => do
-              pure PUnit.unit
-              pure (ForInStep.yield (r ++ resolveFieldRef item))
-        pure r)
-      = Id.run (forIn items [] (fun item r =>
-        (match item with
-          | OrderingItem.expression e => ForInStep.yield (r ++ [(e, false)])
-          | OrderingItem.fieldRef _ => ForInStep.yield (r ++ resolveFieldRef item)
-          : Id (ForInStep (List (OrderExpr × Bool)))))) := rfl
-  rw [h2, helper_expandOrdering]
-  simp
+  induction items with
+  | nil => simp
+  | cons a as ih =>
+      cases a with
+      | expression e => simp [expandOrderingItem, ih]
+      | fieldRef name => simp [expandOrderingItem, ih]
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -73,59 +73,23 @@
 
 -- impl-start
 def implementation_expandOrdering
-    (items : List OrderingItem) : List (OrderExpr × Bool) := Id.run do
-  let mut results : List (OrderExpr × Bool) := []
-  for item in items do
+    (items : List OrderingItem) : List (OrderExpr × Bool) :=
+  items.flatMap (fun item =>
     match item with
-    | .expression e =>
-        -- Already a directive: emit it directly (flagged `false`) and move on,
-        -- skipping name resolution.
-        results := results ++ [(e, false)]
-    | .fieldRef _ =>
-        results := results ++ resolveFieldRef item
-  return results
+    | .expression _ => resolveFieldRef item
+    | .fieldRef _   => [])
 -- impl-end
 
 -- proof-start
-theorem helper_expandOrdering (items : List OrderingItem)
-    (init : List (OrderExpr × Bool)) :
-    Id.run (forIn items init (fun item r =>
-        (match item with
-          | OrderingItem.expression e => ForInStep.yield (r ++ [(e, false)])
-          | OrderingItem.fieldRef _ => ForInStep.yield (r ++ resolveFieldRef item)
-          : Id (ForInStep (List (OrderExpr × Bool))))))
-      = init ++ items.flatMap expandOrderingItem := by
-  induction items generalizing init with
-  | nil => simp only [List.forIn_nil, Id.run, pure, List.flatMap_nil, List.append_nil]
-  | cons a as ih =>
-      rw [List.forIn_cons]
-      simp only [Id.run, bind] at ih ⊢
-      cases a with
-      | expression e =>
-          simp only [expandOrderingItem, List.flatMap_cons, ih, List.append_assoc]
-      | fieldRef name =>
-          simp only [expandOrderingItem, List.flatMap_cons, ih, List.append_assoc]
-
 theorem correct_expandOrdering :
     ∀ (items : List OrderingItem),
       problem_spec_expandOrdering items (implementation_expandOrdering items) := by
   intro items
   unfold problem_spec_expandOrdering implementation_expandOrdering
-  have h2 : (Id.run do
-        let r ← forIn items [] fun item r =>
-            match item with
-            | OrderingItem.expression e => do
-              pure PUnit.unit
-              pure (ForInStep.yield (r ++ [(e, false)]))
-            | OrderingItem.fieldRef _ => do
-              pure PUnit.unit
-              pure (ForInStep.yield (r ++ resolveFieldRef item))
-        pure r)
-      = Id.run (forIn items [] (fun item r =>
-        (match item with
-          | OrderingItem.expression e => ForInStep.yield (r ++ [(e, false)])
-          | OrderingItem.fieldRef _ => ForInStep.yield (r ++ resolveFieldRef item)
-          : Id (ForInStep (List (OrderExpr × Bool)))))) := rfl
-  rw [h2, helper_expandOrdering]
-  simp
+  induction items with
+  | nil => simp
+  | cons a as ih =>
+      cases a with
+      | expression e => simp [expandOrderingItem, ih]
+      | fieldRef name => simp [expandOrderingItem, ih]
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -73,59 +73,17 @@
 
 -- impl-start
 def implementation_expandOrdering
-    (items : List OrderingItem) : List (OrderExpr × Bool) := Id.run do
-  let mut results : List (OrderExpr × Bool) := []
-  for item in items do
-    match item with
-    | .expression e =>
-        -- Already a directive: emit it directly (flagged `false`) and move on,
-        -- skipping name resolution.
-        results := results ++ [(e, false)]
-    | .fieldRef _ =>
-        results := results ++ resolveFieldRef item
-  return results
+    (items : List OrderingItem) : List (OrderExpr × Bool) :=
+  (items.dropLast).flatMap expandOrderingItem
 -- impl-end
 
 -- proof-start
-theorem helper_expandOrdering (items : List OrderingItem)
-    (init : List (OrderExpr × Bool)) :
-    Id.run (forIn items init (fun item r =>
-        (match item with
-          | OrderingItem.expression e => ForInStep.yield (r ++ [(e, false)])
-          | OrderingItem.fieldRef _ => ForInStep.yield (r ++ resolveFieldRef item)
-          : Id (ForInStep (List (OrderExpr × Bool))))))
-      = init ++ items.flatMap expandOrderingItem := by
-  induction items generalizing init with
-  | nil => simp only [List.forIn_nil, Id.run, pure, List.flatMap_nil, List.append_nil]
-  | cons a as ih =>
-      rw [List.forIn_cons]
-      simp only [Id.run, bind] at ih ⊢
-      cases a with
-      | expression e =>
-          simp only [expandOrderingItem, List.flatMap_cons, ih, List.append_assoc]
-      | fieldRef name =>
-          simp only [expandOrderingItem, List.flatMap_cons, ih, List.append_assoc]
-
 theorem correct_expandOrdering :
     ∀ (items : List OrderingItem),
       problem_spec_expandOrdering items (implementation_expandOrdering items) := by
   intro items
   unfold problem_spec_expandOrdering implementation_expandOrdering
-  have h2 : (Id.run do
-        let r ← forIn items [] fun item r =>
-            match item with
-            | OrderingItem.expression e => do
-              pure PUnit.unit
-              pure (ForInStep.yield (r ++ [(e, false)]))
-            | OrderingItem.fieldRef _ => do
-              pure PUnit.unit
-              pure (ForInStep.yield (r ++ resolveFieldRef item))
-        pure r)
-      = Id.run (forIn items [] (fun item r =>
-        (match item with
-          | OrderingItem.expression e => ForInStep.yield (r ++ [(e, false)])
-          | OrderingItem.fieldRef _ => ForInStep.yield (r ++ resolveFieldRef item)
-          : Id (ForInStep (List (OrderExpr × Bool)))))) := rfl
-  rw [h2, helper_expandOrdering]
-  simp
+  induction items with
+  | nil => simp
+  | cons a as ih => simp_all [expandOrderingItem]
 -- proof-end
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -73,59 +73,23 @@
 
 -- impl-start
 def implementation_expandOrdering
-    (items : List OrderingItem) : List (OrderExpr × Bool) := Id.run do
-  let mut results : List (OrderExpr × Bool) := []
-  for item in items do
+    (items : List OrderingItem) : List (OrderExpr × Bool) :=
+  items.flatMap (fun item =>
     match item with
-    | .expression e =>
-        -- Already a directive: emit it directly (flagged `false`) and move on,
-        -- skipping name resolution.
-        results := results ++ [(e, false)]
-    | .fieldRef _ =>
-        results := results ++ resolveFieldRef item
-  return results
+    | .expression e => [(e, false)]
+    | .fieldRef _   => [])
 -- impl-end
 
 -- proof-start
-theorem helper_expandOrdering (items : List OrderingItem)
-    (init : List (OrderExpr × Bool)) :
-    Id.run (forIn items init (fun item r =>
-        (match item with
-          | OrderingItem.expression e => ForInStep.yield (r ++ [(e, false)])
-          | OrderingItem.fieldRef _ => ForInStep.yield (r ++ resolveFieldRef item)
-          : Id (ForInStep (List (OrderExpr × Bool))))))
-      = init ++ items.flatMap expandOrderingItem := by
-  induction items generalizing init with
-  | nil => simp only [List.forIn_nil, Id.run, pure, List.flatMap_nil, List.append_nil]
-  | cons a as ih =>
-      rw [List.forIn_cons]
-      simp only [Id.run, bind] at ih ⊢
-      cases a with
-      | expression e =>
-          simp only [expandOrderingItem, List.flatMap_cons, ih, List.append_assoc]
-      | fieldRef name =>
-          simp only [expandOrderingItem, List.flatMap_cons, ih, List.append_assoc]
-
 theorem correct_expandOrdering :
     ∀ (items : List OrderingItem),
       problem_spec_expandOrdering items (implementation_expandOrdering items) := by
   intro items
   unfold problem_spec_expandOrdering implementation_expandOrdering
-  have h2 : (Id.run do
-        let r ← forIn items [] fun item r =>
-            match item with
-            | OrderingItem.expression e => do
-              pure PUnit.unit
-              pure (ForInStep.yield (r ++ [(e, false)]))
-            | OrderingItem.fieldRef _ => do
-              pure PUnit.unit
-              pure (ForInStep.yield (r ++ resolveFieldRef item))
-        pure r)
-      = Id.run (forIn items [] (fun item r =>
-        (match item with
-          | OrderingItem.expression e => ForInStep.yield (r ++ [(e, false)])
-          | OrderingItem.fieldRef _ => ForInStep.yield (r ++ resolveFieldRef item)
-          : Id (ForInStep (List (OrderExpr × Bool)))))) := rfl
-  rw [h2, helper_expandOrdering]
-  simp
+  induction items with
+  | nil => simp
+  | cons a as ih =>
+      cases a with
+      | expression e => simp [expandOrderingItem, ih]
+      | fieldRef name => simp [expandOrderingItem, ih]
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Expanding a model's *default ordering specification* into a flat list of concrete
column ordering directives.

A default ordering specification is an ordered list of items. Two kinds of item
occur:

  * a plain **field reference** — a textual name (possibly a multi-part lookup)
    that still has to be resolved against the model into one or more concrete
    column ordering directives; and
  * an already-formed **ordering expression** — a directive that has *already*
    been built and therefore needs no further resolution.

The desired behavior is: walk the specification in order and expand each item.
A field reference is expanded by the (unchanged) name-resolution routine, which
turns it into its concrete directives. An ordering expression is *not* a name and
must NOT be sent through name resolution; it is already a directive, so it is
emitted directly — paired with the flag `false`, meaning the surrounding sort
direction is not re-applied to it — and the result list is the in-order
concatenation of all per-item expansions.

The point pinned by the specification is the per-item dispatch: every ordering
expression in the specification contributes exactly itself (with flag `false`),
and only field references are routed through name resolution.
-/

-- axioms-start
/-- An already-formed ordering directive (an "ordering expression"). Opaque: only
its identity is observed by the modeled behavior — it is carried through
unchanged. The mapping file gives the bijection with the repository object. -/
opaque OrderExpr : Type

/-- A single item of a default ordering specification: either a textual field
reference that still needs resolving, or an already-formed ordering expression. -/
inductive OrderingItem where
  | fieldRef  (name : String)
  | expression (e : OrderExpr)

/-- The (UNCHANGED) name-resolution routine: it expands a single specification
item into its concrete column ordering directives, each paired with its
descending flag. It is referenced identically in the specification and in the
implementation — the modeled behavior does not change *how* a field reference is
resolved, only *which* items are sent to it. Declared `opaque` so it can appear
in the executable implementation. -/
opaque resolveFieldRef : OrderingItem → List (OrderExpr × Bool)
-- axioms-end

-- pure-start
/-- The expansion of a single specification item:

  * an ordering expression is already a directive, so it contributes exactly
    itself paired with `false` (the surrounding direction is not re-applied);
  * a field reference is contributed via the unchanged name-resolution routine. -/
def expandOrderingItem (item : OrderingItem) : List (OrderExpr × Bool) :=
  match item with
  | .expression e => [(e, false)]
  | .fieldRef _   => resolveFieldRef item
-- pure-end

-- post-conditions-start
/-- The expanded ordering is the in-order concatenation of the per-item
expansions: every ordering expression contributes exactly itself (flagged
`false`), and every field reference contributes its name-resolved directives.
Nothing is dropped, reordered, or invented; the whole result is pinned to the
input specification. -/
def problem_spec_expandOrdering
    (items : List OrderingItem) (result : List (OrderExpr × Bool)) : Prop :=
  result = items.flatMap expandOrderingItem
-- post-conditions-end

-- impl-start
def implementation_expandOrdering
    (items : List OrderingItem) : List (OrderExpr × Bool) :=
  items.flatMap (fun item =>
    match item with
    | .expression e => [(e, false)]
    | .fieldRef _   => resolveFieldRef item)
-- impl-end

-- proof-start
theorem correct_expandOrdering :
    ∀ (items : List OrderingItem),
      problem_spec_expandOrdering items (implementation_expandOrdering items) := by
  intro items
  unfold problem_spec_expandOrdering implementation_expandOrdering
  induction items with
  | nil => simp
  | cons a as ih =>
      cases a with
      | expression e => simp [expandOrderingItem, ih]
      | fieldRef name => simp [expandOrderingItem, ih]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC STRUCTURE: The Lean spec view (swebench_unified.markers._lean_spec_view) elides BOTH the impl and proof regions to placeholders, so same_spec pins only the axioms/pure/post-condition regions. The post-condition is an EXACT extensional equality: `problem_spec_expandOrdering items result := result = items.flatMap expandOrderingItem`. This uniquely determines the output list for every (resolveFieldRef, items). Therefore ANY implementation whose correct_* closes must be extensionally equal to `items.flatMap expandOrderingItem`, which is exactly the gold-patch behavior (.expression e -> [(e,false)]; .fieldRef _ -> resolveFieldRef item). resolveFieldRef is `opaque` (no defining equations), so no degenerate/vacuous closure can identify a buggy result with the spec value.

SAME_SPEC: all 8 attacks + positive control return same_spec=True vs shipped Solution.lean (swebench_unified.markers.same_spec, lean backend).

### ATTACKS (cmd: `bash scripts/lean_verify.sh <file>`; run concurrently in 2 batches of 4):
- atk_1 (PREPATCH BUG, route every item through resolveFieldRef = `items.flatMap resolveFieldRef`): EXIT=1. Residual goal `resolveFieldRef (.expression e) ++ ... = (e,false) :: ...` — opaque callee cannot be identified with [(e,false)]. Cannot close. (This is prepatch_reproduced.)
- atk_2 (WRONG FLAG, .expression e -> [(e,true)]): EXIT=1. Residual `⊢ False` (true ≠ false, provably false). Cannot close.
- atk_3 (PARTIAL-DOMAIN, always []): EXIT=1. Residual `... = []`. Cannot close.
- atk_4 (CONTROL-FLOW EFFECT, reverse the correct expansion): EXIT=1. `simp made no progress`; reverse ≠ identity. Cannot close.
- atk_5 (DUPLICATE, .expression e -> [(e,false),(e,false)]): EXIT=1. Residual `⊢ False`. Cannot close.
- atk_6 (SWAPPED BRANCHES, .expression -> resolveFieldRef, .fieldRef -> []): EXIT=1. Residual `resolveFieldRef (.fieldRef name) = []` — opaque, unprovable. Cannot close.
- atk_7 (BOUNDARY, drop last item via dropLast): EXIT=1. Residual mismatch on the extra cons. Cannot close.
- atk_8 (UNGROUNDED-ORACLE ECHO / drop fieldRefs, .fieldRef _ -> []): EXIT=1. Residual `resolveFieldRef (.fieldRef name) = []` — opaque, unprovable. Cannot close.

POSITIVE CONTROL: pos_control.lean (operationally-distinct correct impl: `items.flatMap` with match instead of shipped forIn accumulator). `lean_verify.sh` EXIT=0; `#print axioms correct_expandOrdering` = [propext] (clean; no sorryAx/Classical.choice). Its faithful patch reproduces the same isinstance(item,OrderBy) short-circuit as gold, so it RESOLVES — not a counterexample. Shipped Solution.lean also verified here: EXIT=0, axioms [propext, Quot.sound] (clean).

PATCH/RESOLVE STEP: Vacuous. Protocol step 2 requires materializing + running a faithful patch ONLY for wrong impls whose proof closes with clean axioms. ZERO wrong impls closed, so there is no closing-clean-axiom-but-non-resolving impl to exhibit. Every attack ran to completion (no timeouts/contention), so this is SOUND, not INCONCLUSIVE.

REFINEMENT.MD AUDIT: 7 legs. #1 accumulator init (I), #2 loop over items (R: opts.ordering ↔ List OrderingItem), #3 dispatch (R: OrderingItem.expression ↔ isinstance(item,OrderBy)), #4 append (e,false) (R), #5 else/string path (R), #6 resolveFieldRef (A-REFERENCE), #7 return (I). No kind-3 (changed-inexpressible) leg. meta.json axioms=[] (no A-consumed). The ONLY A-leg: resolveFieldRef ↔ self.find_ordering_name(item, opts, alias, order, already_seen) recursive call on a string item.

Validated against gold patch context lines (data/swe_bench_verified test.jsonl, base_commit 8dd5877f58f84f2b11126afbd0813e24545919ed): the base loop `for item in opts.ordering: results.extend(self.find_ordering_name(item, ...))` forwards every non-OrderBy item to that identical recursive call, UNCHANGED on the string path (the patch only inserts the `if isinstance(item, OrderBy): results.append((item, False)); continue` guard above it). patch_equals_gold=True. The 5→1-arg abstraction is sound: order/already_seen are loop-invariant and not observed by the per-item dispatch, which keys ONLY on isinstance(item, OrderBy). resolveFieldRef appears identically in the spec helper expandOrderingItem and in the impl, so it cancels in the obligation (no dead/consumed axiom shipped). A-reference correspondence holds.

CONCLUSION: The post-condition is a single exact equality admitting exactly one output value; the discriminating .expression clause is pinned structurally to [(e,false)] independent of the opaque resolveFieldRef, leaving no closing-but-non-resolving loophole. verify ⇒ correct. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec wrong implementation produced a closing correct_expandOrdering proof, so there is no closing-clean-axiom impl whose faithful patch could be resolve-tested. verify does NOT diverge from correct here.
```

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
Expanding a model's *default ordering specification* into a flat list of concrete
column ordering directives.

A default ordering specification is an ordered list of items. Two kinds of item
occur:

  * a plain **field reference** — a textual name (possibly a multi-part lookup)
    that still has to be resolved against the model into one or more concrete
    column ordering directives; and
  * an already-formed **ordering expression** — a directive that has *already*
    been built and therefore needs no further resolution.

The desired behavior is: walk the specification in order and expand each item.
A field reference is expanded by the (unchanged) name-resolution routine, which
turns it into its concrete directives. An ordering expression is *not* a name and
must NOT be sent through name resolution; it is already a directive, so it is
emitted directly — paired with the flag `false`, meaning the surrounding sort
direction is not re-applied to it — and the result list is the in-order
concatenation of all per-item expansions.

The point pinned by the specification is the per-item dispatch: every ordering
expression in the specification contributes exactly itself (with flag `false`),
and only field references are routed through name resolution.
-/

-- axioms-start
/-- An already-formed ordering directive (an "ordering expression"). Opaque: only
its identity is observed by the modeled behavior — it is carried through
unchanged. The mapping file gives the bijection with the repository object. -/
opaque OrderExpr : Type

/-- A single item of a default ordering specification: either a textual field
reference that still needs resolving, or an already-formed ordering expression. -/
inductive OrderingItem where
  | fieldRef  (name : String)
  | expression (e : OrderExpr)

/-- The (UNCHANGED) name-resolution routine: it expands a single specification
item into its concrete column ordering directives, each paired with its
descending flag. It is referenced identically in the specification and in the
implementation — the modeled behavior does not change *how* a field reference is
resolved, only *which* items are sent to it. Declared `opaque` so it can appear
in the executable implementation. -/
opaque resolveFieldRef : OrderingItem → List (OrderExpr × Bool)
-- axioms-end

-- pure-start
/-- The expansion of a single specification item:

  * an ordering expression is already a directive, so it contributes exactly
    itself paired with `false` (the surrounding direction is not re-applied);
  * a field reference is contributed via the unchanged name-resolution routine. -/
def expandOrderingItem (item : OrderingItem) : List (OrderExpr × Bool) :=
  match item with
  | .expression e => [(e, false)]
  | .fieldRef _   => resolveFieldRef item
-- pure-end

-- post-conditions-start
/-- The expanded ordering is the in-order concatenation of the per-item
expansions: every ordering expression contributes exactly itself (flagged
`false`), and every field reference contributes its name-resolved directives.
Nothing is dropped, reordered, or invented; the whole result is pinned to the
input specification. -/
def problem_spec_expandOrdering
    (items : List OrderingItem) (result : List (OrderExpr × Bool)) : Prop :=
  result = items.flatMap expandOrderingItem
-- post-conditions-end

-- impl-start
def implementation_expandOrdering
    (items : List OrderingItem) : List (OrderExpr × Bool) :=
  items.flatMap (fun item =>
    match item with
    | .expression e => [(e, false)]
    | .fieldRef _   => resolveFieldRef item)
-- impl-end

-- proof-start
theorem correct_expandOrdering :
    ∀ (items : List OrderingItem),
      problem_spec_expandOrdering items (implementation_expandOrdering items) := by
  intro items
  unfold problem_spec_expandOrdering implementation_expandOrdering
  induction items with
  | nil => simp
  | cons a as ih =>
      cases a with
      | expression e => simp [expandOrderingItem, ih]
      | fieldRef name => simp [expandOrderingItem, ih]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC STRUCTURE: The Lean spec view (swebench_unified.markers._lean_spec_view) elides BOTH the impl and proof regions to placeholders, so same_spec pins only the axioms/pure/post-condition regions. The post-condition is an EXACT extensional equality: `problem_spec_expandOrdering items result := result = items.flatMap expandOrderingItem`. This uniquely determines the output list for every (resolveFieldRef, items). Therefore ANY implementation whose correct_* closes must be extensionally equal to `items.flatMap expandOrderingItem`, which is exactly the gold-patch behavior (.expression e -> [(e,false)]; .fieldRef _ -> resolveFieldRef item). resolveFieldRef is `opaque` (no defining equations), so no degenerate/vacuous closure can identify a buggy result with the spec value.

SAME_SPEC: all 8 attacks + positive control return same_spec=True vs shipped Solution.lean (swebench_unified.markers.same_spec, lean backend).

### ATTACKS (cmd: `bash scripts/lean_verify.sh <file>`; run concurrently in 2 batches of 4):
- atk_1 (PREPATCH BUG, route every item through resolveFieldRef = `items.flatMap resolveFieldRef`): EXIT=1. Residual goal `resolveFieldRef (.expression e) ++ ... = (e,false) :: ...` — opaque callee cannot be identified with [(e,false)]. Cannot close. (This is prepatch_reproduced.)
- atk_2 (WRONG FLAG, .expression e -> [(e,true)]): EXIT=1. Residual `⊢ False` (true ≠ false, provably false). Cannot close.
- atk_3 (PARTIAL-DOMAIN, always []): EXIT=1. Residual `... = []`. Cannot close.
- atk_4 (CONTROL-FLOW EFFECT, reverse the correct expansion): EXIT=1. `simp made no progress`; reverse ≠ identity. Cannot close.
- atk_5 (DUPLICATE, .expression e -> [(e,false),(e,false)]): EXIT=1. Residual `⊢ False`. Cannot close.
- atk_6 (SWAPPED BRANCHES, .expression -> resolveFieldRef, .fieldRef -> []): EXIT=1. Residual `resolveFieldRef (.fieldRef name) = []` — opaque, unprovable. Cannot close.
- atk_7 (BOUNDARY, drop last item via dropLast): EXIT=1. Residual mismatch on the extra cons. Cannot close.
- atk_8 (UNGROUNDED-ORACLE ECHO / drop fieldRefs, .fieldRef _ -> []): EXIT=1. Residual `resolveFieldRef (.fieldRef name) = []` — opaque, unprovable. Cannot close.

POSITIVE CONTROL: pos_control.lean (operationally-distinct correct impl: `items.flatMap` with match instead of shipped forIn accumulator). `lean_verify.sh` EXIT=0; `#print axioms correct_expandOrdering` = [propext] (clean; no sorryAx/Classical.choice). Its faithful patch reproduces the same isinstance(item,OrderBy) short-circuit as gold, so it RESOLVES — not a counterexample. Shipped Solution.lean also verified here: EXIT=0, axioms [propext, Quot.sound] (clean).

PATCH/RESOLVE STEP: Vacuous. Protocol step 2 requires materializing + running a faithful patch ONLY for wrong impls whose proof closes with clean axioms. ZERO wrong impls closed, so there is no closing-clean-axiom-but-non-resolving impl to exhibit. Every attack ran to completion (no timeouts/contention), so this is SOUND, not INCONCLUSIVE.

REFINEMENT.MD AUDIT: 7 legs. #1 accumulator init (I), #2 loop over items (R: opts.ordering ↔ List OrderingItem), #3 dispatch (R: OrderingItem.expression ↔ isinstance(item,OrderBy)), #4 append (e,false) (R), #5 else/string path (R), #6 resolveFieldRef (A-REFERENCE), #7 return (I). No kind-3 (changed-inexpressible) leg. meta.json axioms=[] (no A-consumed). The ONLY A-leg: resolveFieldRef ↔ self.find_ordering_name(item, opts, alias, order, already_seen) recursive call on a string item.

Validated against gold patch context lines (data/swe_bench_verified test.jsonl, base_commit 8dd5877f58f84f2b11126afbd0813e24545919ed): the base loop `for item in opts.ordering: results.extend(self.find_ordering_name(item, ...))` forwards every non-OrderBy item to that identical recursive call, UNCHANGED on the string path (the patch only inserts the `if isinstance(item, OrderBy): results.append((item, False)); continue` guard above it). patch_equals_gold=True. The 5→1-arg abstraction is sound: order/already_seen are loop-invariant and not observed by the per-item dispatch, which keys ONLY on isinstance(item, OrderBy). resolveFieldRef appears identically in the spec helper expandOrderingItem and in the impl, so it cancels in the obligation (no dead/consumed axiom shipped). A-reference correspondence holds.

CONCLUSION: The post-condition is a single exact equality admitting exactly one output value; the discriminating .expression clause is pinned structurally to [(e,false)] independent of the opaque resolveFieldRef, leaving no closing-but-non-resolving loophole. verify ⇒ correct. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec `result = items.flatMap expandOrderingItem` (expression e -> [(e,false)], fieldRef -> resolveFieldRef item) is a faithful model of the gold-patched `SQLCompiler.find_ordering_name` default-ordering loop at base_commit 8dd5877f. Gold patch (dataset + patch_equals_gold=True) adds `if isinstance(item, OrderBy): results.append((item, False)); continue` before the recursive `find_ordering_name` extend. The opaque `resolveFieldRef` stands for the UNCHANGED recursive string-item resolver and appears IDENTICALLY on spec and impl sides, so it cancels in the correctness statement; faithfulness reduces to the per-item dispatch + in-order concatenation, which match exactly: (a) OrderBy item -> (item, False) in both; (b) non-OrderBy item -> routed to resolver in both (two-constructor partition mirrors the binary isinstance dispatch, faithful regardless of the non-OrderBy item's concrete type); (c) flatMap == list extend/++ preserves order; empty list -> empty in both; the modeled `false` is the patch's literal False flag. No input diverges. Not over-constrained (spec == impl exactly) nor drifting. Mechanical: lean_verify.sh Solution.lean exit 0; #print axioms correct_expandOrdering = [propext, Quot.sound] (clean, no sorryAx, real proof); same_spec(Solution, Solution_prepatch, lean)=True (spec region byte-identical; prepatch removes the dispatch and its correct_* is a genuine sorry => G-DIFF holds). No patch.diff file in bundle; verified against real repo git history (base 8dd5877f) instead.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (docstring + axioms/pure/post-conditions, lines 1-72) is expressed entirely in abstracted Lean vocabulary: OrderExpr, OrderingItem(.fieldRef/.expression), resolveFieldRef, flatMap. Lexical screen finds NONE of the gold-patch tokens in the spec view: OrderBy, isinstance, append, continue, find_ordering_name, get_order_dir, opts.ordering, Meta.ordering, results.extend, base_commit hash. The public problem_statement already discloses the bug ('the field is an OrderBy object, not a string, during get_order_dir' when 'Meta.ordering contains expressions'), i.e. that ordering-expression items must be dispatched differently from string field names is already public. The spec merely states correct behavior (expression items contribute themselves flagged false; field refs go through the resolver) at a higher abstraction level than the problem_statement, quoting no patch specifics and using the generic Lean literal `false` rather than the Python `False`. patch_equals_gold=True; spec region hashed (spec_view 232cf39f). No spec-view line leaks the gold edit beyond problem_statement (which is the permitted baseline, hints_text excluded).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).