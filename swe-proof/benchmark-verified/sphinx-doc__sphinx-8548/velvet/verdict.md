# P2 adversarial audit — sphinx-doc__sphinx-8548

**Backend:** `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 11 admissible attacks re-run of 11 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 11 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (11):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -136,26 +136,29 @@
   ensures out = collected existing (candidates hierarchy)
   do
     -- impl-start
+    -- ATTACK 1 (prepatch bug re-encode): annotations walked hierarchy-wide, documented
+    -- attributes taken ONLY from the most-derived class's own namespace and attributed to
+    -- it -- pre-patch `namespace = '.'.join(objpath)` + `ClassAttribute(subject, ...)`.
     let mut result : List Member := []
     let mut i := 0
-    while i < (candidates hierarchy).length
-      invariant i ≤ (candidates hierarchy).length
-      invariant result = ((candidates hierarchy).take i).foldl (collectStep existing) []
-      done_with i = (candidates hierarchy).length
-      decreasing (candidates hierarchy).length - i
+    while i < (((hierarchy.map (fun c => (c.annots.filter (fun n => n != "")).map (fun n => (⟨n, c.owner, none⟩ : Member)))).flatten) ++ ((hierarchy.headD default).attrs.map (fun a => (⟨a.name, (hierarchy.headD default).owner, some a.doc⟩ : Member)))).length
+      invariant i ≤ (((hierarchy.map (fun c => (c.annots.filter (fun n => n != "")).map (fun n => (⟨n, c.owner, none⟩ : Member)))).flatten) ++ ((hierarchy.headD default).attrs.map (fun a => (⟨a.name, (hierarchy.headD default).owner, some a.doc⟩ : Member)))).length
+      invariant result = ((((hierarchy.map (fun c => (c.annots.filter (fun n => n != "")).map (fun n => (⟨n, c.owner, none⟩ : Member)))).flatten) ++ ((hierarchy.headD default).attrs.map (fun a => (⟨a.name, (hierarchy.headD default).owner, some a.doc⟩ : Member)))).take i).foldl (collectStep existing) []
+      done_with i = (((hierarchy.map (fun c => (c.annots.filter (fun n => n != "")).map (fun n => (⟨n, c.owner, none⟩ : Member)))).flatten) ++ ((hierarchy.headD default).attrs.map (fun a => (⟨a.name, (hierarchy.headD default).owner, some a.doc⟩ : Member)))).length
+      decreasing (((hierarchy.map (fun c => (c.annots.filter (fun n => n != "")).map (fun n => (⟨n, c.owner, none⟩ : Member)))).flatten) ++ ((hierarchy.headD default).attrs.map (fun a => (⟨a.name, (hierarchy.headD default).owner, some a.doc⟩ : Member)))).length - i
     do
-      let a := (candidates hierarchy)[i]!
-      result := collectStep existing result a
+      let a := (((hierarchy.map (fun c => (c.annots.filter (fun n => n != "")).map (fun n => (⟨n, c.owner, none⟩ : Member)))).flatten) ++ ((hierarchy.headD default).attrs.map (fun a => (⟨a.name, (hierarchy.headD default).owner, some a.doc⟩ : Member))))[i]!
+      result := (collectStep existing) result a
       i := i + 1
     return result
     -- impl-end
 
 prove_correct collectInstanceAttrDocs by
   loom_solve
-  case «invariant_2: result = ((candidates hierarchy).take i).foldl (collectStep existing) []» =>
-    have hi : i < (candidates hierarchy).length := by omega
-    rw [invariant_2, foldl_take_step (collectStep existing) (candidates hierarchy) [] i hi]
-  case «ensures_1: out = collected existing (candidates hierarchy)» =>
-    injection i_2 with _ hr
-    subst hr
-    rw [collected, invariant_2, done_1, List.take_length]
+  all_goals
+    first
+      | (injection i_2 with _ hr
+         subst hr
+         rw [collected, invariant_2, done_1, List.take_length])
+      | (have hi : i < (((hierarchy.map (fun c => (c.annots.filter (fun n => n != "")).map (fun n => (⟨n, c.owner, none⟩ : Member)))).flatten) ++ ((hierarchy.headD default).attrs.map (fun a => (⟨a.name, (hierarchy.headD default).owner, some a.doc⟩ : Member)))).length := by omega
+         rw [invariant_2, foldl_take_step (collectStep existing) (((hierarchy.map (fun c => (c.annots.filter (fun n => n != "")).map (fun n => (⟨n, c.owner, none⟩ : Member)))).flatten) ++ ((hierarchy.headD default).attrs.map (fun a => (⟨a.name, (hierarchy.headD default).owner, some a.doc⟩ : Member)))) [] i hi])
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -136,26 +136,29 @@
   ensures out = collected existing (candidates hierarchy)
   do
     -- impl-start
+    -- ATTACK 2 (partial domain): right on a SINGLETON hierarchy, wrong the moment the
+    -- subject has a base -- only the most-derived class is walked (importer.py without the
+    -- `for cls in getmro(subject)` loop).
     let mut result : List Member := []
     let mut i := 0
-    while i < (candidates hierarchy).length
-      invariant i ≤ (candidates hierarchy).length
-      invariant result = ((candidates hierarchy).take i).foldl (collectStep existing) []
-      done_with i = (candidates hierarchy).length
-      decreasing (candidates hierarchy).length - i
+    while i < (levelCandidates (hierarchy.headD default)).length
+      invariant i ≤ (levelCandidates (hierarchy.headD default)).length
+      invariant result = ((levelCandidates (hierarchy.headD default)).take i).foldl (collectStep existing) []
+      done_with i = (levelCandidates (hierarchy.headD default)).length
+      decreasing (levelCandidates (hierarchy.headD default)).length - i
     do
-      let a := (candidates hierarchy)[i]!
-      result := collectStep existing result a
+      let a := (levelCandidates (hierarchy.headD default))[i]!
+      result := (collectStep existing) result a
       i := i + 1
     return result
     -- impl-end
 
 prove_correct collectInstanceAttrDocs by
   loom_solve
-  case «invariant_2: result = ((candidates hierarchy).take i).foldl (collectStep existing) []» =>
-    have hi : i < (candidates hierarchy).length := by omega
-    rw [invariant_2, foldl_take_step (collectStep existing) (candidates hierarchy) [] i hi]
-  case «ensures_1: out = collected existing (candidates hierarchy)» =>
-    injection i_2 with _ hr
-    subst hr
-    rw [collected, invariant_2, done_1, List.take_length]
+  all_goals
+    first
+      | (injection i_2 with _ hr
+         subst hr
+         rw [collected, invariant_2, done_1, List.take_length])
+      | (have hi : i < (levelCandidates (hierarchy.headD default)).length := by omega
+         rw [invariant_2, foldl_take_step (collectStep existing) (levelCandidates (hierarchy.headD default)) [] i hi])
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -136,26 +136,28 @@
   ensures out = collected existing (candidates hierarchy)
   do
     -- impl-start
+    -- ATTACK 3 (boundary / off-by-one): the candidate stream is correct but its LAST
+    -- element is never considered -- the final class's last declaration is silently lost.
     let mut result : List Member := []
     let mut i := 0
-    while i < (candidates hierarchy).length
-      invariant i ≤ (candidates hierarchy).length
-      invariant result = ((candidates hierarchy).take i).foldl (collectStep existing) []
-      done_with i = (candidates hierarchy).length
-      decreasing (candidates hierarchy).length - i
+    while i < ((candidates hierarchy).dropLast).length
+      invariant i ≤ ((candidates hierarchy).dropLast).length
+      invariant result = (((candidates hierarchy).dropLast).take i).foldl (collectStep existing) []
+      done_with i = ((candidates hierarchy).dropLast).length
+      decreasing ((candidates hierarchy).dropLast).length - i
     do
-      let a := (candidates hierarchy)[i]!
-      result := collectStep existing result a
+      let a := ((candidates hierarchy).dropLast)[i]!
+      result := (collectStep existing) result a
       i := i + 1
     return result
     -- impl-end
 
 prove_correct collectInstanceAttrDocs by
   loom_solve
-  case «invariant_2: result = ((candidates hierarchy).take i).foldl (collectStep existing) []» =>
-    have hi : i < (candidates hierarchy).length := by omega
-    rw [invariant_2, foldl_take_step (collectStep existing) (candidates hierarchy) [] i hi]
-  case «ensures_1: out = collected existing (candidates hierarchy)» =>
-    injection i_2 with _ hr
-    subst hr
-    rw [collected, invariant_2, done_1, List.take_length]
+  all_goals
+    first
+      | (injection i_2 with _ hr
+         subst hr
+         rw [collected, invariant_2, done_1, List.take_length])
+      | (have hi : i < ((candidates hierarchy).dropLast).length := by omega
+         rw [invariant_2, foldl_take_step (collectStep existing) ((candidates hierarchy).dropLast) [] i hi])
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -136,26 +136,29 @@
   ensures out = collected existing (candidates hierarchy)
   do
     -- impl-start
+    -- ATTACK 4 (control-flow effect): the stream and first-wins among candidates are right,
+    -- but `name not in members` is not consulted against the members the untouched prefix
+    -- already surfaced -- the `existing` guard is dropped.
     let mut result : List Member := []
     let mut i := 0
     while i < (candidates hierarchy).length
       invariant i ≤ (candidates hierarchy).length
-      invariant result = ((candidates hierarchy).take i).foldl (collectStep existing) []
+      invariant result = ((candidates hierarchy).take i).foldl (collectStep []) []
       done_with i = (candidates hierarchy).length
       decreasing (candidates hierarchy).length - i
     do
       let a := (candidates hierarchy)[i]!
-      result := collectStep existing result a
+      result := (collectStep []) result a
       i := i + 1
     return result
     -- impl-end
 
 prove_correct collectInstanceAttrDocs by
   loom_solve
-  case «invariant_2: result = ((candidates hierarchy).take i).foldl (collectStep existing) []» =>
-    have hi : i < (candidates hierarchy).length := by omega
-    rw [invariant_2, foldl_take_step (collectStep existing) (candidates hierarchy) [] i hi]
-  case «ensures_1: out = collected existing (candidates hierarchy)» =>
-    injection i_2 with _ hr
-    subst hr
-    rw [collected, invariant_2, done_1, List.take_length]
+  all_goals
+    first
+      | (injection i_2 with _ hr
+         subst hr
+         rw [collected, invariant_2, done_1, List.take_length])
+      | (have hi : i < (candidates hierarchy).length := by omega
+         rw [invariant_2, foldl_take_step (collectStep []) (candidates hierarchy) [] i hi])
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -136,26 +136,11 @@
   ensures out = collected existing (candidates hierarchy)
   do
     -- impl-start
-    let mut result : List Member := []
-    let mut i := 0
-    while i < (candidates hierarchy).length
-      invariant i ≤ (candidates hierarchy).length
-      invariant result = ((candidates hierarchy).take i).foldl (collectStep existing) []
-      done_with i = (candidates hierarchy).length
-      decreasing (candidates hierarchy).length - i
-    do
-      let a := (candidates hierarchy)[i]!
-      result := collectStep existing result a
-      i := i + 1
-    return result
+    -- ATTACK 5 (ungrounded-oracle echo): the postcondition is returned verbatim as the
+    -- computation. Nothing is proved about HOW the collection is built; if the frozen
+    -- model itself is not the gold behaviour, this is the impl that exposes it.
+    return collected existing (candidates hierarchy)
     -- impl-end
 
 prove_correct collectInstanceAttrDocs by
   loom_solve
-  case «invariant_2: result = ((candidates hierarchy).take i).foldl (collectStep existing) []» =>
-    have hi : i < (candidates hierarchy).length := by omega
-    rw [invariant_2, foldl_take_step (collectStep existing) (candidates hierarchy) [] i hi]
-  case «ensures_1: out = collected existing (candidates hierarchy)» =>
-    injection i_2 with _ hr
-    subst hr
-    rw [collected, invariant_2, done_1, List.take_length]
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -136,26 +136,30 @@
   ensures out = collected existing (candidates hierarchy)
   do
     -- impl-start
+    -- ATTACK 6 (wrong attribution): every name and docstring of the whole hierarchy is
+    -- gathered correctly, but attributed to the class being documented --
+    -- `ClassAttribute(subject, ...)` where the patch writes `ClassAttribute(cls, ...)`.
+    -- This is the impl `__init__.py:1606`'s `m.class_ == self.object` filter exposes.
     let mut result : List Member := []
     let mut i := 0
-    while i < (candidates hierarchy).length
-      invariant i ≤ (candidates hierarchy).length
-      invariant result = ((candidates hierarchy).take i).foldl (collectStep existing) []
-      done_with i = (candidates hierarchy).length
-      decreasing (candidates hierarchy).length - i
+    while i < ((hierarchy.map (fun c => (c.annots.filter (fun n => n != "")).map (fun n => (⟨n, c.owner, none⟩ : Member)) ++ c.attrs.map (fun a => (⟨a.name, (hierarchy.headD default).owner, some a.doc⟩ : Member)))).flatten).length
+      invariant i ≤ ((hierarchy.map (fun c => (c.annots.filter (fun n => n != "")).map (fun n => (⟨n, c.owner, none⟩ : Member)) ++ c.attrs.map (fun a => (⟨a.name, (hierarchy.headD default).owner, some a.doc⟩ : Member)))).flatten).length
+      invariant result = (((hierarchy.map (fun c => (c.annots.filter (fun n => n != "")).map (fun n => (⟨n, c.owner, none⟩ : Member)) ++ c.attrs.map (fun a => (⟨a.name, (hierarchy.headD default).owner, some a.doc⟩ : Member)))).flatten).take i).foldl (collectStep existing) []
+      done_with i = ((hierarchy.map (fun c => (c.annots.filter (fun n => n != "")).map (fun n => (⟨n, c.owner, none⟩ : Member)) ++ c.attrs.map (fun a => (⟨a.name, (hierarchy.headD default).owner, some a.doc⟩ : Member)))).flatten).length
+      decreasing ((hierarchy.map (fun c => (c.annots.filter (fun n => n != "")).map (fun n => (⟨n, c.owner, none⟩ : Member)) ++ c.attrs.map (fun a => (⟨a.name, (hierarchy.headD default).owner, some a.doc⟩ : Member)))).flatten).length - i
     do
-      let a := (candidates hierarchy)[i]!
-      result := collectStep existing result a
+      let a := ((hierarchy.map (fun c => (c.annots.filter (fun n => n != "")).map (fun n => (⟨n, c.owner, none⟩ : Member)) ++ c.attrs.map (fun a => (⟨a.name, (hierarchy.headD default).owner, some a.doc⟩ : Member)))).flatten)[i]!
+      result := (collectStep existing) result a
       i := i + 1
     return result
     -- impl-end
 
 prove_correct collectInstanceAttrDocs by
   loom_solve
-  case «invariant_2: result = ((candidates hierarchy).take i).foldl (collectStep existing) []» =>
-    have hi : i < (candidates hierarchy).length := by omega
-    rw [invariant_2, foldl_take_step (collectStep existing) (candidates hierarchy) [] i hi]
-  case «ensures_1: out = collected existing (candidates hierarchy)» =>
-    injection i_2 with _ hr
-    subst hr
-    rw [collected, invariant_2, done_1, List.take_length]
+  all_goals
+    first
+      | (injection i_2 with _ hr
+         subst hr
+         rw [collected, invariant_2, done_1, List.take_length])
+      | (have hi : i < ((hierarchy.map (fun c => (c.annots.filter (fun n => n != "")).map (fun n => (⟨n, c.owner, none⟩ : Member)) ++ c.attrs.map (fun a => (⟨a.name, (hierarchy.headD default).owner, some a.doc⟩ : Member)))).flatten).length := by omega
+         rw [invariant_2, foldl_take_step (collectStep existing) ((hierarchy.map (fun c => (c.annots.filter (fun n => n != "")).map (fun n => (⟨n, c.owner, none⟩ : Member)) ++ c.attrs.map (fun a => (⟨a.name, (hierarchy.headD default).owner, some a.doc⟩ : Member)))).flatten) [] i hi])
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -136,26 +136,29 @@
   ensures out = collected existing (candidates hierarchy)
   do
     -- impl-start
+    -- ATTACK 7 (interleaving): the two declaration kinds resolved as two hierarchy-wide
+    -- passes instead of per class, so a base class's annotation beats a subclass's
+    -- docstring for the same identifier.
     let mut result : List Member := []
     let mut i := 0
-    while i < (candidates hierarchy).length
-      invariant i ≤ (candidates hierarchy).length
-      invariant result = ((candidates hierarchy).take i).foldl (collectStep existing) []
-      done_with i = (candidates hierarchy).length
-      decreasing (candidates hierarchy).length - i
+    while i < (((hierarchy.map (fun c => (c.annots.filter (fun n => n != "")).map (fun n => (⟨n, c.owner, none⟩ : Member)))).flatten) ++ ((hierarchy.map (fun c => c.attrs.map (fun a => (⟨a.name, c.owner, some a.doc⟩ : Member)))).flatten)).length
+      invariant i ≤ (((hierarchy.map (fun c => (c.annots.filter (fun n => n != "")).map (fun n => (⟨n, c.owner, none⟩ : Member)))).flatten) ++ ((hierarchy.map (fun c => c.attrs.map (fun a => (⟨a.name, c.owner, some a.doc⟩ : Member)))).flatten)).length
+      invariant result = ((((hierarchy.map (fun c => (c.annots.filter (fun n => n != "")).map (fun n => (⟨n, c.owner, none⟩ : Member)))).flatten) ++ ((hierarchy.map (fun c => c.attrs.map (fun a => (⟨a.name, c.owner, some a.doc⟩ : Member)))).flatten)).take i).foldl (collectStep existing) []
+      done_with i = (((hierarchy.map (fun c => (c.annots.filter (fun n => n != "")).map (fun n => (⟨n, c.owner, none⟩ : Member)))).flatten) ++ ((hierarchy.map (fun c => c.attrs.map (fun a => (⟨a.name, c.owner, some a.doc⟩ : Member)))).flatten)).length
+      decreasing (((hierarchy.map (fun c => (c.annots.filter (fun n => n != "")).map (fun n => (⟨n, c.owner, none⟩ : Member)))).flatten) ++ ((hierarchy.map (fun c => c.attrs.map (fun a => (⟨a.name, c.owner, some a.doc⟩ : Member)))).flatten)).length - i
     do
-      let a := (candidates hierarchy)[i]!
-      result := collectStep existing result a
+      let a := (((hierarchy.map (fun c => (c.annots.filter (fun n => n != "")).map (fun n => (⟨n, c.owner, none⟩ : Member)))).flatten) ++ ((hierarchy.map (fun c => c.attrs.map (fun a => (⟨a.name, c.owner, some a.doc⟩ : Member)))).flatten))[i]!
+      result := (collectStep existing) result a
       i := i + 1
     return result
     -- impl-end
 
 prove_correct collectInstanceAttrDocs by
   loom_solve
-  case «invariant_2: result = ((candidates hierarchy).take i).foldl (collectStep existing) []» =>
-    have hi : i < (candidates hierarchy).length := by omega
-    rw [invariant_2, foldl_take_step (collectStep existing) (candidates hierarchy) [] i hi]
-  case «ensures_1: out = collected existing (candidates hierarchy)» =>
-    injection i_2 with _ hr
-    subst hr
-    rw [collected, invariant_2, done_1, List.take_length]
+  all_goals
+    first
+      | (injection i_2 with _ hr
+         subst hr
+         rw [collected, invariant_2, done_1, List.take_length])
+      | (have hi : i < (((hierarchy.map (fun c => (c.annots.filter (fun n => n != "")).map (fun n => (⟨n, c.owner, none⟩ : Member)))).flatten) ++ ((hierarchy.map (fun c => c.attrs.map (fun a => (⟨a.name, c.owner, some a.doc⟩ : Member)))).flatten)).length := by omega
+         rw [invariant_2, foldl_take_step (collectStep existing) (((hierarchy.map (fun c => (c.annots.filter (fun n => n != "")).map (fun n => (⟨n, c.owner, none⟩ : Member)))).flatten) ++ ((hierarchy.map (fun c => c.attrs.map (fun a => (⟨a.name, c.owner, some a.doc⟩ : Member)))).flatten)) [] i hi])
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -136,26 +136,29 @@
   ensures out = collected existing (candidates hierarchy)
   do
     -- impl-start
+    -- ATTACK 8 (observable collapsed): an annotation-only member is given an EMPTY
+    -- docstring instead of NO docstring -- 4-argument `ClassAttribute(cls, name,
+    -- INSTANCEATTR, '')` where the patch uses the 3-argument form (docstring is None).
     let mut result : List Member := []
     let mut i := 0
-    while i < (candidates hierarchy).length
-      invariant i ≤ (candidates hierarchy).length
-      invariant result = ((candidates hierarchy).take i).foldl (collectStep existing) []
-      done_with i = (candidates hierarchy).length
-      decreasing (candidates hierarchy).length - i
+    while i < ((hierarchy.map (fun c => (c.annots.filter (fun n => n != "")).map (fun n => (⟨n, c.owner, some ""⟩ : Member)) ++ c.attrs.map (fun a => (⟨a.name, c.owner, some a.doc⟩ : Member)))).flatten).length
+      invariant i ≤ ((hierarchy.map (fun c => (c.annots.filter (fun n => n != "")).map (fun n => (⟨n, c.owner, some ""⟩ : Member)) ++ c.attrs.map (fun a => (⟨a.name, c.owner, some a.doc⟩ : Member)))).flatten).length
+      invariant result = (((hierarchy.map (fun c => (c.annots.filter (fun n => n != "")).map (fun n => (⟨n, c.owner, some ""⟩ : Member)) ++ c.attrs.map (fun a => (⟨a.name, c.owner, some a.doc⟩ : Member)))).flatten).take i).foldl (collectStep existing) []
+      done_with i = ((hierarchy.map (fun c => (c.annots.filter (fun n => n != "")).map (fun n => (⟨n, c.owner, some ""⟩ : Member)) ++ c.attrs.map (fun a => (⟨a.name, c.owner, some a.doc⟩ : Member)))).flatten).length
+      decreasing ((hierarchy.map (fun c => (c.annots.filter (fun n => n != "")).map (fun n => (⟨n, c.owner, some ""⟩ : Member)) ++ c.attrs.map (fun a => (⟨a.name, c.owner, some a.doc⟩ : Member)))).flatten).length - i
     do
-      let a := (candidates hierarchy)[i]!
-      result := collectStep existing result a
+      let a := ((hierarchy.map (fun c => (c.annots.filter (fun n => n != "")).map (fun n => (⟨n, c.owner, some ""⟩ : Member)) ++ c.attrs.map (fun a => (⟨a.name, c.owner, some a.doc⟩ : Member)))).flatten)[i]!
+      result := (collectStep existing) result a
       i := i + 1
     return result
     -- impl-end
 
 prove_correct collectInstanceAttrDocs by
   loom_solve
-  case «invariant_2: result = ((candidates hierarchy).take i).foldl (collectStep existing) []» =>
-    have hi : i < (candidates hierarchy).length := by omega
-    rw [invariant_2, foldl_take_step (collectStep existing) (candidates hierarchy) [] i hi]
-  case «ensures_1: out = collected existing (candidates hierarchy)» =>
-    injection i_2 with _ hr
-    subst hr
-    rw [collected, invariant_2, done_1, List.take_length]
+  all_goals
+    first
+      | (injection i_2 with _ hr
+         subst hr
+         rw [collected, invariant_2, done_1, List.take_length])
+      | (have hi : i < ((hierarchy.map (fun c => (c.annots.filter (fun n => n != "")).map (fun n => (⟨n, c.owner, some ""⟩ : Member)) ++ c.attrs.map (fun a => (⟨a.name, c.owner, some a.doc⟩ : Member)))).flatten).length := by omega
+         rw [invariant_2, foldl_take_step (collectStep existing) ((hierarchy.map (fun c => (c.annots.filter (fun n => n != "")).map (fun n => (⟨n, c.owner, some ""⟩ : Member)) ++ c.attrs.map (fun a => (⟨a.name, c.owner, some a.doc⟩ : Member)))).flatten) [] i hi])
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

```diff
@@ -136,26 +136,29 @@
   ensures out = collected existing (candidates hierarchy)
   do
     -- impl-start
+    -- ATTACK 9 (within-class phase order): per class the documented attributes are resolved
+    -- BEFORE that class's annotations, so an identifier a class both annotates and documents
+    -- keeps its docstring instead of losing it to the annotation.
     let mut result : List Member := []
     let mut i := 0
-    while i < (candidates hierarchy).length
-      invariant i ≤ (candidates hierarchy).length
-      invariant result = ((candidates hierarchy).take i).foldl (collectStep existing) []
-      done_with i = (candidates hierarchy).length
-      decreasing (candidates hierarchy).length - i
+    while i < ((hierarchy.map (fun c => c.attrs.map (fun a => (⟨a.name, c.owner, some a.doc⟩ : Member)) ++ (c.annots.filter (fun n => n != "")).map (fun n => (⟨n, c.owner, none⟩ : Member)))).flatten).length
+      invariant i ≤ ((hierarchy.map (fun c => c.attrs.map (fun a => (⟨a.name, c.owner, some a.doc⟩ : Member)) ++ (c.annots.filter (fun n => n != "")).map (fun n => (⟨n, c.owner, none⟩ : Member)))).flatten).length
+      invariant result = (((hierarchy.map (fun c => c.attrs.map (fun a => (⟨a.name, c.owner, some a.doc⟩ : Member)) ++ (c.annots.filter (fun n => n != "")).map (fun n => (⟨n, c.owner, none⟩ : Member)))).flatten).take i).foldl (collectStep existing) []
+      done_with i = ((hierarchy.map (fun c => c.attrs.map (fun a => (⟨a.name, c.owner, some a.doc⟩ : Member)) ++ (c.annots.filter (fun n => n != "")).map (fun n => (⟨n, c.owner, none⟩ : Member)))).flatten).length
+      decreasing ((hierarchy.map (fun c => c.attrs.map (fun a => (⟨a.name, c.owner, some a.doc⟩ : Member)) ++ (c.annots.filter (fun n => n != "")).map (fun n => (⟨n, c.owner, none⟩ : Member)))).flatten).length - i
     do
-      let a := (candidates hierarchy)[i]!
-      result := collectStep existing result a
+      let a := ((hierarchy.map (fun c => c.attrs.map (fun a => (⟨a.name, c.owner, some a.doc⟩ : Member)) ++ (c.annots.filter (fun n => n != "")).map (fun n => (⟨n, c.owner, none⟩ : Member)))).flatten)[i]!
+      result := (collectStep existing) result a
       i := i + 1
     return result
     -- impl-end
 
 prove_correct collectInstanceAttrDocs by
   loom_solve
-  case «invariant_2: result = ((candidates hierarchy).take i).foldl (collectStep existing) []» =>
-    have hi : i < (candidates hierarchy).length := by omega
-    rw [invariant_2, foldl_take_step (collectStep existing) (candidates hierarchy) [] i hi]
-  case «ensures_1: out = collected existing (candidates hierarchy)» =>
-    injection i_2 with _ hr
-    subst hr
-    rw [collected, invariant_2, done_1, List.take_length]
+  all_goals
+    first
+      | (injection i_2 with _ hr
+         subst hr
+         rw [collected, invariant_2, done_1, List.take_length])
+      | (have hi : i < ((hierarchy.map (fun c => c.attrs.map (fun a => (⟨a.name, c.owner, some a.doc⟩ : Member)) ++ (c.annots.filter (fun n => n != "")).map (fun n => (⟨n, c.owner, none⟩ : Member)))).flatten).length := by omega
+         rw [invariant_2, foldl_take_step (collectStep existing) ((hierarchy.map (fun c => c.attrs.map (fun a => (⟨a.name, c.owner, some a.doc⟩ : Member)) ++ (c.annots.filter (fun n => n != "")).map (fun n => (⟨n, c.owner, none⟩ : Member)))).flatten) [] i hi])
```

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

```diff
@@ -136,26 +136,29 @@
   ensures out = collected existing (candidates hierarchy)
   do
     -- impl-start
+    -- ATTACK 10 (precedence inverted): a later namesake OVERWRITES an earlier one, so a base
+    -- class's declaration displaces the more-derived class's -- `members[name] = ...` with
+    -- the `name not in members` guard removed from the assignment.
     let mut result : List Member := []
     let mut i := 0
     while i < (candidates hierarchy).length
       invariant i ≤ (candidates hierarchy).length
-      invariant result = ((candidates hierarchy).take i).foldl (collectStep existing) []
+      invariant result = ((candidates hierarchy).take i).foldl (fun (acc : List Member) (m : Member) => if existing.contains m.name then acc else (acc.filter (fun x => x.name != m.name)) ++ [m]) []
       done_with i = (candidates hierarchy).length
       decreasing (candidates hierarchy).length - i
     do
       let a := (candidates hierarchy)[i]!
-      result := collectStep existing result a
+      result := (fun (acc : List Member) (m : Member) => if existing.contains m.name then acc else (acc.filter (fun x => x.name != m.name)) ++ [m]) result a
       i := i + 1
     return result
     -- impl-end
 
 prove_correct collectInstanceAttrDocs by
   loom_solve
-  case «invariant_2: result = ((candidates hierarchy).take i).foldl (collectStep existing) []» =>
-    have hi : i < (candidates hierarchy).length := by omega
-    rw [invariant_2, foldl_take_step (collectStep existing) (candidates hierarchy) [] i hi]
-  case «ensures_1: out = collected existing (candidates hierarchy)» =>
-    injection i_2 with _ hr
-    subst hr
-    rw [collected, invariant_2, done_1, List.take_length]
+  all_goals
+    first
+      | (injection i_2 with _ hr
+         subst hr
+         rw [collected, invariant_2, done_1, List.take_length])
+      | (have hi : i < (candidates hierarchy).length := by omega
+         rw [invariant_2, foldl_take_step (fun (acc : List Member) (m : Member) => if existing.contains m.name then acc else (acc.filter (fun x => x.name != m.name)) ++ [m]) (candidates hierarchy) [] i hi])
```

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good)

```diff
@@ -136,26 +136,29 @@
   ensures out = collected existing (candidates hierarchy)
   do
     -- impl-start
+    -- ATTACK 11 (sentinel boundary): the leading `if name` at importer.py:306 is dropped, so
+    -- a private identifier annotated by ANOTHER class of the MRO (`unmangle` -> None,
+    -- modeled as "") is surfaced as a member instead of being passed over.
     let mut result : List Member := []
     let mut i := 0
-    while i < (candidates hierarchy).length
-      invariant i ≤ (candidates hierarchy).length
-      invariant result = ((candidates hierarchy).take i).foldl (collectStep existing) []
-      done_with i = (candidates hierarchy).length
-      decreasing (candidates hierarchy).length - i
+    while i < ((hierarchy.map (fun c => c.annots.map (fun n => (⟨n, c.owner, none⟩ : Member)) ++ c.attrs.map (fun a => (⟨a.name, c.owner, some a.doc⟩ : Member)))).flatten).length
+      invariant i ≤ ((hierarchy.map (fun c => c.annots.map (fun n => (⟨n, c.owner, none⟩ : Member)) ++ c.attrs.map (fun a => (⟨a.name, c.owner, some a.doc⟩ : Member)))).flatten).length
+      invariant result = (((hierarchy.map (fun c => c.annots.map (fun n => (⟨n, c.owner, none⟩ : Member)) ++ c.attrs.map (fun a => (⟨a.name, c.owner, some a.doc⟩ : Member)))).flatten).take i).foldl (collectStep existing) []
+      done_with i = ((hierarchy.map (fun c => c.annots.map (fun n => (⟨n, c.owner, none⟩ : Member)) ++ c.attrs.map (fun a => (⟨a.name, c.owner, some a.doc⟩ : Member)))).flatten).length
+      decreasing ((hierarchy.map (fun c => c.annots.map (fun n => (⟨n, c.owner, none⟩ : Member)) ++ c.attrs.map (fun a => (⟨a.name, c.owner, some a.doc⟩ : Member)))).flatten).length - i
     do
-      let a := (candidates hierarchy)[i]!
-      result := collectStep existing result a
+      let a := ((hierarchy.map (fun c => c.annots.map (fun n => (⟨n, c.owner, none⟩ : Member)) ++ c.attrs.map (fun a => (⟨a.name, c.owner, some a.doc⟩ : Member)))).flatten)[i]!
+      result := (collectStep existing) result a
       i := i + 1
     return result
     -- impl-end
 
 prove_correct collectInstanceAttrDocs by
   loom_solve
-  case «invariant_2: result = ((candidates hierarchy).take i).foldl (collectStep existing) []» =>
-    have hi : i < (candidates hierarchy).length := by omega
-    rw [invariant_2, foldl_take_step (collectStep existing) (candidates hierarchy) [] i hi]
-  case «ensures_1: out = collected existing (candidates hierarchy)» =>
-    injection i_2 with _ hr
-    subst hr
-    rw [collected, invariant_2, done_1, List.take_length]
+  all_goals
+    first
+      | (injection i_2 with _ hr
+         subst hr
+         rw [collected, invariant_2, done_1, List.take_length])
+      | (have hi : i < ((hierarchy.map (fun c => c.annots.map (fun n => (⟨n, c.owner, none⟩ : Member)) ++ c.attrs.map (fun a => (⟨a.name, c.owner, some a.doc⟩ : Member)))).flatten).length := by omega
+         rw [invariant_2, foldl_take_step (collectStep existing) ((hierarchy.map (fun c => c.annots.map (fun n => (⟨n, c.owner, none⟩ : Member)) ++ c.attrs.map (fun a => (⟨a.name, c.owner, some a.doc⟩ : Member)))).flatten) [] i hi])
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no deep-model reference to a foreign callee. The
   behaviour under specification — which documented instance attributes a class
   surfaces, with which docstring, and which class each surfaced member is
   attributed to — is modeled DIRECTLY in the `pure` region
   (`levelCandidates`/`candidates`/`collectStep`/`collected`): the collection is
   concrete data-flow over the inputs, not hidden behind a module-level `axiom`.
   The structural descriptors that feed the collection (a class's inheritance
   hierarchy, the member names each class declares by annotation alone, and the
   documented instance attributes assigned within each class's own namespace) are
   produced by unchanged read-only helpers; their faithful abstraction into the
   inputs `existing` / `hierarchy` is recorded in mapping.md and validated
   against the real helpers by axiom_check.py (G-AX). -/
-- axioms-end

-- pure-start
/- One documented instance attribute as the source analyzer records it: the
   identifier assigned on the instance and the docstring attached to that
   assignment. mapping.md §2 gives the bijection to the repository's attribute
   record. -/
structure AttrDoc where
  name : String
  doc  : String
  deriving Inhabited, DecidableEq, Repr

/- One class of the subject's inheritance hierarchy. `owner` is that class's
   identity; `annots` are the member names it declares by annotation alone — no
   value, hence no docstring — in declaration order, where the empty string
   stands for an annotated identifier that is not reachable under this class's
   name; `attrs` are the documented instance attributes assigned inside this
   class's own namespace, in analyzer order. mapping.md §2. -/
structure ClassLevel where
  owner  : String
  annots : List String
  attrs  : List AttrDoc
  deriving Inhabited, DecidableEq, Repr

/- One surfaced member: its identifier, the identity of the class it is
   attributed to, and its docstring — `none` for a member that exists only as an
   annotation, `some d` for a documented instance attribute. A consumer renders
   `doc` and selects the members to list by comparing `owner` against the class
   being documented, so both components are observable and neither may be left
   unconstrained. mapping.md §2. -/
structure Member where
  name  : String
  owner : String
  doc   : Option String
  deriving Inhabited, DecidableEq, Repr

/- The candidate members one class contributes, in the order the collection meets
   them: first that class's annotation-only names (an annotated identifier not
   reachable under this class's name is passed over), then its own-namespace
   documented instance attributes. Every candidate a class contributes is
   attributed to THAT class — not to the class being documented. -/
def levelCandidates (c : ClassLevel) : List Member :=
  (c.annots.filter (fun n => n != "")).map (fun n => ⟨n, c.owner, none⟩)
    ++ c.attrs.map (fun a => ⟨a.name, c.owner, some a.doc⟩)

/- The whole candidate stream: each class of the hierarchy in turn contributes
   its own two groups. The interleaving is per class — a class's annotations and
   that same class's documented attributes are resolved before the next class is
   considered — so when two classes declare the same identifier in different
   ways, which declaration survives is decided by the position of the
   contributing class in the hierarchy, not by the kind of declaration. -/
def candidates (hierarchy : List ClassLevel) : List Member :=
  (hierarchy.map levelCandidates).flatten

/- Fold one candidate into the running collection. A candidate is accepted
   (appended, preserving discovery order) only when its identifier has not
   already been claimed — either it is already an `existing` member, or an
   earlier candidate of the same name was kept. This is first-occurrence
   precedence: the earliest contributor of an identifier is kept, together with
   its attribution and its docstring, and later namesakes are passed over. -/
def collectStep (existing : List String) (acc : List Member) (m : Member) : List Member :=
  if existing.contains m.name || acc.any (fun x => x.name == m.name) then acc
  else acc ++ [m]

/- The members a class surfaces: fold the candidate stream left-to-right with
   first-occurrence precedence. Because the hierarchy is ordered
   most-derived-first, a member declared on a base class is surfaced precisely
   when no more-derived class (and no `existing` member) already claims its
   identifier — and it is then attributed to the base class that declared it. -/
def collected (existing : List String) (xs : List Member) : List Member :=
  xs.foldl (collectStep existing) []

/- Forward-fold step: extending the consumed prefix by one candidate folds that
   candidate into the collection built from the shorter prefix. The single goal
   `loom_solve` leaves for the loop body (the forward-fold pattern, plan §5.4). -/
lemma foldl_take_step {α β : Type _} [Inhabited α] (f : β → α → β) (xs : List α) (init : β)
    (i : Nat) (hi : i < xs.length) :
    (xs.take (i + 1)).foldl f init = f ((xs.take i).foldl f init) xs[i]! := by
  have hcons : xs.take (i + 1) = xs.take i ++ [xs[i]!] := by
    rw [List.take_succ, List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
    simp
  rw [hcons, List.foldl_append, List.foldl_cons, List.foldl_nil]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Collect the members a class surfaces from the declarations spread across its
   whole inheritance hierarchy.

   `existing` (the identifiers of members already surfaced from other sources)
   and `hierarchy` (each class's own annotation-only names and own-namespace
   documented instance attributes, ordered most-derived-first) are read-only
   inputs — neither is `mut`: the collection consumes them and never alters them
   (directive 5). The result is exactly the first-occurrence collection over the
   per-class candidate stream, `out = collected existing (candidates hierarchy)`.
   Three consequences a verifying implementation cannot escape:

   * an attribute declared on a base class is surfaced whenever no more-derived
     class and no existing member already claims its identifier — so the
     collection cannot be restricted to the most-derived class alone;
   * every surfaced member carries the `owner` of the class whose declaration it
     came from — so an inherited declaration cannot be attributed to the class
     being documented, which is what decides whether a consumer that lists only
     a class's own members lists it;
   * a class's annotation-only names are resolved together with that same class's
     documented attributes rather than ahead of the entire hierarchy's — so
     whether an annotation of the same identifier suppresses a docstring is
     decided by hierarchy position. -/
method collectInstanceAttrDocs (existing : List String) (hierarchy : List ClassLevel)
    return (out : List Member)
  ensures out = collected existing (candidates hierarchy)
  do
    -- impl-start
    let mut result : List Member := []
    let mut i := 0
    while i < (candidates hierarchy).length
      invariant i ≤ (candidates hierarchy).length
      invariant result = ((candidates hierarchy).take i).foldl (collectStep existing) []
      done_with i = (candidates hierarchy).length
      decreasing (candidates hierarchy).length - i
    do
      let a := (candidates hierarchy)[i]!
      result := collectStep existing result a
      i := i + 1
    return result
    -- impl-end

prove_correct collectInstanceAttrDocs by
  loom_solve
  case «invariant_2: result = ((candidates hierarchy).take i).foldl (collectStep existing) []» =>
    have hi : i < (candidates hierarchy).length := by omega
    rw [invariant_2, foldl_take_step (collectStep existing) (candidates hierarchy) [] i hi]
  case «ensures_1: out = collected existing (candidates hierarchy)» =>
    injection i_2 with _ hr
    subst hr
    rw [collected, invariant_2, done_1, List.take_length]
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial pass. 11 same-spec attacks (markers.same_spec=True for every one; axioms/pure/pre/post regions verified byte-identical to Solution.lean programmatically). Positive control pos_control.lean verifies (exit 0).

METHODOLOGY NOTE (self-caught false negative): my first encoding used `let cs := ...` in the impl and named `cs` in the prove_correct tactic block. All four attacks were 'rejected' -- but the logs showed `error(lean.unknownIdentifier): Unknown identifier cs`, i.e. a SCOPE error in my own proof, not a proof failure. Those rejections were worthless. I re-encoded all attacks with the candidate-stream expression INLINED at every occurrence and a case-name-free proof (`all_goals first | <ensures tac> | <invariant tac>`, no sorry/skip), then added ctl_shape.lean -- the CORRECT stream under that exact generator/proof shape -- which verifies (exit 0). Only after that control passed do the rejections mean anything. Every reported rejection was then confirmed to carry 0 unknownIdentifier/syntax errors and exactly `error: unsolved goals`.

### ATTACKS (cmd: `bash scripts/lean_verify.sh <path>`, run 4-way concurrent):
- atk_1 PREPATCH BUG (documented attrs from the subject namespace only; pre-patch `namespace='.'.join(objpath)` + ClassAttribute(subject,...)): exit 1, unsolved goals @156. Prepatch reproduced and rejected.
- atk_2 partial domain (only head class walked; correct on singleton hierarchies): exit 1, unsolved goals.
- atk_3 boundary/off-by-one (stream `.dropLast`, last declaration lost): exit 1, unsolved goals.
- atk_4 control-flow effect (`existing` guard dropped: collectStep [] instead of collectStep existing): exit 1, unsolved goals.
- atk_5 UNGROUNDED-ORACLE ECHO (`return collected existing (candidates hierarchy)`): exit 0 -- VERIFIES. Patch materialized + resolved, see below.
- atk_6 wrong attribution (inherited attrs credited to the documented class; the impl `__init__`.py:1606's `m.class_ == self.object` filter exposes): exit 1, unsolved goals.
- atk_7 interleaving (two hierarchy-wide passes instead of per-class): exit 1, unsolved goals.
- atk_8 observable collapsed (annotation-only member gets `some ""` instead of `none`): exit 1, unsolved goals.
- atk_9 within-class phase order swapped (attrs before annots): exit 1, unsolved goals.
- atk_10 precedence inverted (last-wins overwrite instead of first-wins): exit 1, unsolved goals.
- atk_11 sentinel boundary (the leading `if name` at importer.py:306 dropped, so unmangle->None surfaces): exit 1, unsolved goals.

WHY ONLY THE ECHO VERIFIES -- and why that is not a weakness here. The postcondition `out = collected existing (candidates hierarchy)` is a TOTAL functional equation over a pure model, with an empty precondition. So the verifying class is a single extensional behaviour: every verifying impl computes exactly the model on every input. Impl-side freedom is nil, and G-EQ therefore reduces entirely to MODEL fidelity -- which is precisely what the echo probes. atk_5 is the extensional representative of the whole verifying class, so resolving its faithful patch tests the spec's fidelity completely rather than partially.

MANDATORY RESOLVE (executed, not speculated) -- atk_5's faithful refined patch, a literal transliteration of levelCandidates/candidates/collectStep/collected (patch text submitted above; file atk_5.patch):
  cmd: `python resolve.py atk_5 .../atk_5.patch` -> swebench_unified.harness.run_resolve('sphinx-doc__sphinx-8548', patch, timeout=1800, retries=1)
  RESULT: resolved=true, completed=true, note='resolved', flaky=false. F2P test_inherited_instance_variable PASS; all 5 P2P PASS; PASS_TO_FAIL empty.
  Harness control (validates my invocation): gold patch.diff -> resolved=true, identical test table. So the harness was live and discriminating, and the verifying impl's patch RESOLVES => no verify-but-wrong witness. Not BROKEN.

INDEPENDENT DIFFERENTIAL (extra evidence for model fidelity, diffcheck.py): extracted the base commit twice, applied gold to wt_gold and the atk_5 transliteration to wt, and compared the full observable {name: (owner identity, docstring)} over INSTANCEATTR entries on 6 subjects -- the F2P Bar(Foo) fixture plus annotation-vs-docstring collision, mangled private annotation, `__slots__`, and a diamond MRO. Output is BYTE-IDENTICAL (`diff` clean), including the discriminating cases: Bar.attr1 -> owner Foo (not Bar), AnnotVsDoc.ann -> annotation wins with docstring None, Mangled.`__priv` present, diamond dl/dr attributed to DiamondL/DiamondR.

REFINEMENT.MD AUDIT (A-legs, my assigned focus). Solution.lean contains NO `axiom` declaration and no sorry/admit (grepped), consistent with meta.json axioms=[] and deep_model_references=[]; so there is no A-consumed leg and no kind-3 step -- every leg of the A-table is R or I, matching §C's claim. The changed collection is modeled directly in the pure region, not hidden behind an axiom about the function under change, which is the honest shape for this patch.

I verified every A-leg's line-number correspondence against the PATCHED worktree by exact string match: 301 `for cls in getmro(subject)`, 304 `for name in getannotations(cls)`, 305 `name = unmangle`, 306 `if name and name not in members`, 307 3-arg `ClassAttribute(cls, name, INSTANCEATTR)` (docstring defaults None => A4's `none`), 313 `modname = safe_getattr`, 315 `ModuleAnalyzer.for_module`, 318 `if ns == qualname and name not in members`, 319 `ClassAttribute(cls, name, INSTANCEATTR,` (=> A5's `some`), 326 `return members` -- all 10 OK.

Caller §3.4 confirmed: `__init__`.py:1587 drops the analyzer arg, and 1602-1606 are the two projections (`inherited_members` lists all; the else branch filters `m.class_ == self.object`), which is the real justification that Member.owner must be pinned (§2.1) -- atk_6 is exactly that rival and it is rejected. A1's read-only claim holds (`existing`/`hierarchy` are not `mut`). The three §B twins were independently confirmed same_spec=True.

**VERDICT SOUND:** 11 attacks run under a validated control, 10 honestly rejected on `unsolved goals`, the one verifying impl's materialized faithful patch executed through the official harness and RESOLVED, and the refinement map's A-legs check out against the real callees.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 11 admissible attacks re-run of 11 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 11 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (11):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 11 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no deep-model reference to a foreign callee. The
   behaviour under specification — which documented instance attributes a class
   surfaces, with which docstring, and which class each surfaced member is
   attributed to — is modeled DIRECTLY in the `pure` region
   (`levelCandidates`/`candidates`/`collectStep`/`collected`): the collection is
   concrete data-flow over the inputs, not hidden behind a module-level `axiom`.
   The structural descriptors that feed the collection (a class's inheritance
   hierarchy, the member names each class declares by annotation alone, and the
   documented instance attributes assigned within each class's own namespace) are
   produced by unchanged read-only helpers; their faithful abstraction into the
   inputs `existing` / `hierarchy` is recorded in mapping.md and validated
   against the real helpers by axiom_check.py (G-AX). -/
-- axioms-end

-- pure-start
/- One documented instance attribute as the source analyzer records it: the
   identifier assigned on the instance and the docstring attached to that
   assignment. mapping.md §2 gives the bijection to the repository's attribute
   record. -/
structure AttrDoc where
  name : String
  doc  : String
  deriving Inhabited, DecidableEq, Repr

/- One class of the subject's inheritance hierarchy. `owner` is that class's
   identity; `annots` are the member names it declares by annotation alone — no
   value, hence no docstring — in declaration order, where the empty string
   stands for an annotated identifier that is not reachable under this class's
   name; `attrs` are the documented instance attributes assigned inside this
   class's own namespace, in analyzer order. mapping.md §2. -/
structure ClassLevel where
  owner  : String
  annots : List String
  attrs  : List AttrDoc
  deriving Inhabited, DecidableEq, Repr

/- One surfaced member: its identifier, the identity of the class it is
   attributed to, and its docstring — `none` for a member that exists only as an
   annotation, `some d` for a documented instance attribute. A consumer renders
   `doc` and selects the members to list by comparing `owner` against the class
   being documented, so both components are observable and neither may be left
   unconstrained. mapping.md §2. -/
structure Member where
  name  : String
  owner : String
  doc   : Option String
  deriving Inhabited, DecidableEq, Repr

/- The candidate members one class contributes, in the order the collection meets
   them: first that class's annotation-only names (an annotated identifier not
   reachable under this class's name is passed over), then its own-namespace
   documented instance attributes. Every candidate a class contributes is
   attributed to THAT class — not to the class being documented. -/
def levelCandidates (c : ClassLevel) : List Member :=
  (c.annots.filter (fun n => n != "")).map (fun n => ⟨n, c.owner, none⟩)
    ++ c.attrs.map (fun a => ⟨a.name, c.owner, some a.doc⟩)

/- The whole candidate stream: each class of the hierarchy in turn contributes
   its own two groups. The interleaving is per class — a class's annotations and
   that same class's documented attributes are resolved before the next class is
   considered — so when two classes declare the same identifier in different
   ways, which declaration survives is decided by the position of the
   contributing class in the hierarchy, not by the kind of declaration. -/
def candidates (hierarchy : List ClassLevel) : List Member :=
  (hierarchy.map levelCandidates).flatten

/- Fold one candidate into the running collection. A candidate is accepted
   (appended, preserving discovery order) only when its identifier has not
   already been claimed — either it is already an `existing` member, or an
   earlier candidate of the same name was kept. This is first-occurrence
   precedence: the earliest contributor of an identifier is kept, together with
   its attribution and its docstring, and later namesakes are passed over. -/
def collectStep (existing : List String) (acc : List Member) (m : Member) : List Member :=
  if existing.contains m.name || acc.any (fun x => x.name == m.name) then acc
  else acc ++ [m]

/- The members a class surfaces: fold the candidate stream left-to-right with
   first-occurrence precedence. Because the hierarchy is ordered
   most-derived-first, a member declared on a base class is surfaced precisely
   when no more-derived class (and no `existing` member) already claims its
   identifier — and it is then attributed to the base class that declared it. -/
def collected (existing : List String) (xs : List Member) : List Member :=
  xs.foldl (collectStep existing) []

/- Forward-fold step: extending the consumed prefix by one candidate folds that
   candidate into the collection built from the shorter prefix. The single goal
   `loom_solve` leaves for the loop body (the forward-fold pattern, plan §5.4). -/
lemma foldl_take_step {α β : Type _} [Inhabited α] (f : β → α → β) (xs : List α) (init : β)
    (i : Nat) (hi : i < xs.length) :
    (xs.take (i + 1)).foldl f init = f ((xs.take i).foldl f init) xs[i]! := by
  have hcons : xs.take (i + 1) = xs.take i ++ [xs[i]!] := by
    rw [List.take_succ, List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
    simp
  rw [hcons, List.foldl_append, List.foldl_cons, List.foldl_nil]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Collect the members a class surfaces from the declarations spread across its
   whole inheritance hierarchy.

   `existing` (the identifiers of members already surfaced from other sources)
   and `hierarchy` (each class's own annotation-only names and own-namespace
   documented instance attributes, ordered most-derived-first) are read-only
   inputs — neither is `mut`: the collection consumes them and never alters them
   (directive 5). The result is exactly the first-occurrence collection over the
   per-class candidate stream, `out = collected existing (candidates hierarchy)`.
   Three consequences a verifying implementation cannot escape:

   * an attribute declared on a base class is surfaced whenever no more-derived
     class and no existing member already claims its identifier — so the
     collection cannot be restricted to the most-derived class alone;
   * every surfaced member carries the `owner` of the class whose declaration it
     came from — so an inherited declaration cannot be attributed to the class
     being documented, which is what decides whether a consumer that lists only
     a class's own members lists it;
   * a class's annotation-only names are resolved together with that same class's
     documented attributes rather than ahead of the entire hierarchy's — so
     whether an annotation of the same identifier suppresses a docstring is
     decided by hierarchy position. -/
method collectInstanceAttrDocs (existing : List String) (hierarchy : List ClassLevel)
    return (out : List Member)
  ensures out = collected existing (candidates hierarchy)
  do
    -- impl-start
    let mut result : List Member := []
    let mut i := 0
    while i < (candidates hierarchy).length
      invariant i ≤ (candidates hierarchy).length
      invariant result = ((candidates hierarchy).take i).foldl (collectStep existing) []
      done_with i = (candidates hierarchy).length
      decreasing (candidates hierarchy).length - i
    do
      let a := (candidates hierarchy)[i]!
      result := collectStep existing result a
      i := i + 1
    return result
    -- impl-end

prove_correct collectInstanceAttrDocs by
  loom_solve
  case «invariant_2: result = ((candidates hierarchy).take i).foldl (collectStep existing) []» =>
    have hi : i < (candidates hierarchy).length := by omega
    rw [invariant_2, foldl_take_step (collectStep existing) (candidates hierarchy) [] i hi]
  case «ensures_1: out = collected existing (candidates hierarchy)» =>
    injection i_2 with _ hr
    subst hr
    rw [collected, invariant_2, done_1, List.take_length]
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial pass. 11 same-spec attacks (markers.same_spec=True for every one; axioms/pure/pre/post regions verified byte-identical to Solution.lean programmatically). Positive control pos_control.lean verifies (exit 0).

METHODOLOGY NOTE (self-caught false negative): my first encoding used `let cs := ...` in the impl and named `cs` in the prove_correct tactic block. All four attacks were 'rejected' -- but the logs showed `error(lean.unknownIdentifier): Unknown identifier cs`, i.e. a SCOPE error in my own proof, not a proof failure. Those rejections were worthless. I re-encoded all attacks with the candidate-stream expression INLINED at every occurrence and a case-name-free proof (`all_goals first | <ensures tac> | <invariant tac>`, no sorry/skip), then added ctl_shape.lean -- the CORRECT stream under that exact generator/proof shape -- which verifies (exit 0). Only after that control passed do the rejections mean anything. Every reported rejection was then confirmed to carry 0 unknownIdentifier/syntax errors and exactly `error: unsolved goals`.

### ATTACKS (cmd: `bash scripts/lean_verify.sh <path>`, run 4-way concurrent):
- atk_1 PREPATCH BUG (documented attrs from the subject namespace only; pre-patch `namespace='.'.join(objpath)` + ClassAttribute(subject,...)): exit 1, unsolved goals @156. Prepatch reproduced and rejected.
- atk_2 partial domain (only head class walked; correct on singleton hierarchies): exit 1, unsolved goals.
- atk_3 boundary/off-by-one (stream `.dropLast`, last declaration lost): exit 1, unsolved goals.
- atk_4 control-flow effect (`existing` guard dropped: collectStep [] instead of collectStep existing): exit 1, unsolved goals.
- atk_5 UNGROUNDED-ORACLE ECHO (`return collected existing (candidates hierarchy)`): exit 0 -- VERIFIES. Patch materialized + resolved, see below.
- atk_6 wrong attribution (inherited attrs credited to the documented class; the impl `__init__`.py:1606's `m.class_ == self.object` filter exposes): exit 1, unsolved goals.
- atk_7 interleaving (two hierarchy-wide passes instead of per-class): exit 1, unsolved goals.
- atk_8 observable collapsed (annotation-only member gets `some ""` instead of `none`): exit 1, unsolved goals.
- atk_9 within-class phase order swapped (attrs before annots): exit 1, unsolved goals.
- atk_10 precedence inverted (last-wins overwrite instead of first-wins): exit 1, unsolved goals.
- atk_11 sentinel boundary (the leading `if name` at importer.py:306 dropped, so unmangle->None surfaces): exit 1, unsolved goals.

WHY ONLY THE ECHO VERIFIES -- and why that is not a weakness here. The postcondition `out = collected existing (candidates hierarchy)` is a TOTAL functional equation over a pure model, with an empty precondition. So the verifying class is a single extensional behaviour: every verifying impl computes exactly the model on every input. Impl-side freedom is nil, and G-EQ therefore reduces entirely to MODEL fidelity -- which is precisely what the echo probes. atk_5 is the extensional representative of the whole verifying class, so resolving its faithful patch tests the spec's fidelity completely rather than partially.

MANDATORY RESOLVE (executed, not speculated) -- atk_5's faithful refined patch, a literal transliteration of levelCandidates/candidates/collectStep/collected (patch text submitted above; file atk_5.patch):
  cmd: `python resolve.py atk_5 .../atk_5.patch` -> swebench_unified.harness.run_resolve('sphinx-doc__sphinx-8548', patch, timeout=1800, retries=1)
  RESULT: resolved=true, completed=true, note='resolved', flaky=false. F2P test_inherited_instance_variable PASS; all 5 P2P PASS; PASS_TO_FAIL empty.
  Harness control (validates my invocation): gold patch.diff -> resolved=true, identical test table. So the harness was live and discriminating, and the verifying impl's patch RESOLVES => no verify-but-wrong witness. Not BROKEN.

INDEPENDENT DIFFERENTIAL (extra evidence for model fidelity, diffcheck.py): extracted the base commit twice, applied gold to wt_gold and the atk_5 transliteration to wt, and compared the full observable {name: (owner identity, docstring)} over INSTANCEATTR entries on 6 subjects -- the F2P Bar(Foo) fixture plus annotation-vs-docstring collision, mangled private annotation, `__slots__`, and a diamond MRO. Output is BYTE-IDENTICAL (`diff` clean), including the discriminating cases: Bar.attr1 -> owner Foo (not Bar), AnnotVsDoc.ann -> annotation wins with docstring None, Mangled.`__priv` present, diamond dl/dr attributed to DiamondL/DiamondR.

REFINEMENT.MD AUDIT (A-legs, my assigned focus). Solution.lean contains NO `axiom` declaration and no sorry/admit (grepped), consistent with meta.json axioms=[] and deep_model_references=[]; so there is no A-consumed leg and no kind-3 step -- every leg of the A-table is R or I, matching §C's claim. The changed collection is modeled directly in the pure region, not hidden behind an axiom about the function under change, which is the honest shape for this patch.

I verified every A-leg's line-number correspondence against the PATCHED worktree by exact string match: 301 `for cls in getmro(subject)`, 304 `for name in getannotations(cls)`, 305 `name = unmangle`, 306 `if name and name not in members`, 307 3-arg `ClassAttribute(cls, name, INSTANCEATTR)` (docstring defaults None => A4's `none`), 313 `modname = safe_getattr`, 315 `ModuleAnalyzer.for_module`, 318 `if ns == qualname and name not in members`, 319 `ClassAttribute(cls, name, INSTANCEATTR,` (=> A5's `some`), 326 `return members` -- all 10 OK.

Caller §3.4 confirmed: `__init__`.py:1587 drops the analyzer arg, and 1602-1606 are the two projections (`inherited_members` lists all; the else branch filters `m.class_ == self.object`), which is the real justification that Member.owner must be pinned (§2.1) -- atk_6 is exactly that rival and it is rejected. A1's read-only claim holds (`existing`/`hierarchy` are not `mut`). The three §B twins were independently confirmed same_spec=True.

**VERDICT SOUND:** 11 attacks run under a validated control, 10 honestly rejected on `unsolved goals`, the one verifying impl's materialized faithful patch executed through the official harness and RESOLVED, and the refinement map's A-legs check out against the real callees.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** G-PANEL(2) faithfulness-break attack on sphinx-doc__sphinx-8548/velvet. NO divergence found between the modeled function and the real repo behavior. Reference used correctly: worktree at base_commit dd1615c59 with patch.diff APPLIED (verified: git diff in  matches patch.diff byte-for-byte on both hunks); base commit used only for the untouched callees (getmro/getannotations/unmangle/ModuleAnalyzer.attr_docs and the importer.py:259-298 prefix that feeds `existing`).

### What I checked

1. Spec-region freeze. swebench_unified.markers.same_spec(Solution.lean, twin, velvet backend) = True for all three twins (Solution_prepatch, Solution_prepatch_attribution, Solution_prepatch_annotation_prepass). Spec view confirms the ensures clause `out = collected existing (candidates hierarchy)` plus the pure region is the whole contract; impl+proof elided.

2. Verifier. scripts/lean_verify.sh Solution.lean -> exit 0 (no sorry/error). Each of the three prepatch twins fails with exactly one `error:` on ensures_1, so the spec is non-vacuous and discriminates all three independently-observable behaviours the patch fixes (base-namespace widening, per-class attribution, per-class interleaving).

3. INDEPENDENT differential harness (mine.py/hostile.py/fuzz.py/exotic.py/mangle.py/final.py), written from Solution.lean directly, NOT reusing the bundle's conformance_check.py. Ran inside the instance image swebench/sweb.eval.x86_64.sphinx-doc_1776_sphinx-8548 with patch.diff applied. Oracle = REAL patched get_class_members observed as the caller observes it (name -> (owner identity, docstring)); model = transcription of levelCandidates/candidates/collectStep/collected over hierarchy abstracted from the REAL unchanged callees. I compared the full observable AND the insertion ORDER (stricter than mapping.md, which only claims map-equality) -- the spec's ordered List Member reading also holds.

Results, all agreeing with zero disagreements:
  - 20/20 hostile hand-built shapes (F2P Bar(Foo) fixture; base-annotation vs subclass-docstring both directions; same class annotating+documenting one name; nested-class subjects; cross-module bases; mangled private annotations; `__slots__` tuple and dict forms; class attributes with #: docs; enum subject; diamond MRO with a name shared across all four classes; multiline/empty docstrings; attribute documented in a non-`__init__` method; spoofed non-importable `__module__`; qualname collisions on one MRO; property raising NotImplementedError; inherited `__annotations__`).
  - 8/8 mangling/suppression probes using `existing` computed by an INDEPENDENT transliteration of the untouched prefix importer.py:259-298 (not read off the oracle) -- the independent `existing` equalled the oracle complement on every input, so the bridge is measured, not tuned.
  - 17/17 exotic/semantic-edge probes (dynamic type() classes with no source -> PycodeError branch; dynamic subclass over a real documented base; builtins dict/Exception/SimpleNamespace; abc.ABC; dataclass; typing.NamedTuple; attr documented in a nested function inside `__init__`; empty own `__annotations__` shadowing an inherited one; three-deep nested classes and a subclass of the innermost; same qualname in two modules across one MRO).
  - 5 independent fuzz seeds (777, 4242, 1, 99, 31337, 20260815) over generated real modules/classes, testing every class of each hierarchy as subject: 7957, 4705, 3781, 3833, 3814, 18755 cases -> 42,845 total, 0 disagreements.

4. Two apparent MAP-DIFFs I chased to ground and REFUTED as artifacts of my own harness, not spec defects: injecting the INSTANCEATTR sentinel as a class attribute (E1) or on a base (E2) made my `value is INSTANCEATTR` proxy misclassify a PREFIX-created entry as walk-created. I re-ran both with an oracle that instruments the real function (wrapping ClassAttribute construction and marking the getmro call site) to identify walk-created entries by construction provenance instead of by sentinel value: 2/2 agreed. So this is a limitation of the observable projection under a pathological injected sentinel, reachable only by mutating a class to hold sphinx's private sentinel, not a disagreement between the spec and the patched function.

5. Too-strong checks. No preconditions are stated and none are needed: `existing`/`hierarchy` are general inputs (weak-ignore-existing pins the dependence on `existing`). Member.owner and Member.doc (Option String) are genuinely observable via `__init__`.py:1602-1606 (`m.class_ == self.object` filter and `m.docstring` rendering), so pinning them is not over-specification -- a spec omitting owner would admit an impl that breaks the P2P test_instance_variable. objpath is correctly ABSENT from the spec: I confirmed by static scan that post-patch objpath occurs only in get_class_members' signature and nowhere in its body, so it is dead and modeling it would have been the over-specification. The annots abstraction correctly does NOT claim only-own annotations (getannotations goes through getattr, so a class inherits its ancestor's `__annotations__`) -- probes F5/F6 exercise exactly that quirk and agreed.

**CONCLUSION:** no input on which the modeled function disagrees with the real patched callee was found across ~42.8k independent differential cases plus 45 targeted adversarial shapes, checked on the full observable including order. The spec is neither too strong nor drifted. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** ROLE: attacker 3 - leakage / gold-reconstruction. Judged against the SOLVER-VISIBLE problem_statement ONLY; hints_text deliberately excluded from the screen (the hints do contain the smoking gun - tk0miya's example and 'parses only one module. It should also parse modules of all parent classes' - but the solver never sees them, so I did not credit them).

**NO RELAXATION CLAIM IN THIS BUNDLE.** Checked explicitly: there is no RELAXED_LEAKAGE.md anywhere in the instance dir, and meta.json has no `relaxed_leakage` key (`'relaxed_leakage' in meta` -> False). So this is judged as an ordinary unrelaxed leakage review; no inherited disposition to re-derive.

WHAT SHIPS (re-derived, not inherited). eval/dataset.py: MODES_WITH_SPEC={1,2} pass only adapter.spec_view(model); WITHHELD_FIELDS=('patch','test_patch','FAIL_TO_PASS','PASS_TO_PASS'). mapping.md and refinement.md are NOT shipped - which matters, because both are saturated with edit vocabulary (get_class_members, getmro, ModuleAnalyzer.for_module, attr_docs, `__qualname__`, PycodeError, safe_getattr, objpath, ClassAttribute, and even the F2P fixture names Bar(Foo)/attr1/test_inherited_instance_variable, plus refinement.md quoting the gold hunk verbatim with +/- markers). None of that reaches the consumer. I judged the projected spec view only, computed myself via markers.spec_view(src, get_backend('velvet')).

SPEC-REGION IDENTITY (measured). markers.same_spec(Solution.lean, twin) = True for ALL THREE twins: Solution_prepatch.lean, Solution_prepatch_attribution.lean, Solution_prepatch_annotation_prepass.lean. Recomputed markers.region_hashes: axioms=4834d6e93e4144c2, pure=4894235dfac1c10d, impl=e3f4638c3407f4d7, spec_view=e4525d02a24e242c - all four byte-match meta.json G-HYGIENE's recorded region_hashes. patch.diff == instance.json['patch'] verbatim.

MECHANICAL SCREEN (re-run, not trusted from meta). leakage.screen(Solution.lean, velvet, gold_patch=..., problem_statement=..., test_patch=...) -> 0 hard failures, 0 warnings. Re-derived each rule independently rather than trusting the aggregate: (L1) no Lean diff marker present; no normalized gold added/removed line of len>=8 occurs in the spec view (reproduced-gold-line list empty). (L2) neither 'sphinx/ext/autodoc/importer.py' nor 'sphinx/ext/autodoc/`__init__`.py' appears; `_patch_changed_symbols` = {get_class_members, add_directive_header}, `_patch_new_symbols` = empty, and I ran the underscore-stripped len>=4 embedding test of every changed/new symbol against all 88 spec-view code identifiers - zero echoes.

(L3) `_NARRATION_RE` over the Lean comment text: zero hits (no fix/bug/patch/previously/wrong/broken/regression). Targeted verbatim sweep for 20 sensitive repo tokens (getmro, qualname, `__module__`, ModuleAnalyzer, for_module, attr_docs, PycodeError, safe_getattr, getannotations, unmangle, ClassAttribute, objpath, autodoc, sphinx, importer, INSTANCEATTR, try, except, ...): the only three regex hits are benign English/naming collisions - 'the source analyzer records it' and 'in analyzer order' (generic prose; and note `analyzer` is the parameter the gold DELETES, so naming it points away from the edit, not at it), "the subject's inheritance hierarchy" (generic prose), and 'InstanceAttr' as a substring of the descriptive method name collectInstanceAttrDocs - the constant INSTANCEATTR is never named and is unchanged pre-existing code that localizes nothing.

RECONSTRUCTION TEST (the substantive judgement). The spec view's whole discriminating content is `out = collected existing (candidates hierarchy)` over per-class ClassLevel records, i.e. three facets: (a) collect over the WHOLE hierarchy not just the most-derived class; (b) each surfaced member carries the `owner` of the contributing class; (c) a class's annotations and that same class's documented attributes are resolved together (per-class interleaving) rather than as two hierarchy-wide passes.

Facet (a) is a restatement of the PUBLIC problem_statement, which spells out the root cause verbatim: 'autodoc searches for a cached docstring using (namespace, attrname) as search-key, but doesn't check for baseclass-namespace', titled "inherited-members won't work for inherited attributes (data members)". Read as an instruction that IS 'check the baseclass namespaces too'. Facets (b) and (c) I checked against the PRE-patch source at base_commit dd1615c59 in a fresh worktree (, importer.py:254-317): both are visible there already. The pre-patch annotation loop ALREADY walks `for cls in getmro(subject)` and ALREADY passes `ClassAttribute(cls, name, INSTANCEATTR)` - so per-class attribution and the MRO walk are pre-existing, solver-readable code, not edit disclosure.

The first-wins dedup (`name not in members`) is likewise on the gold's REMOVED lines, i.e. unchanged behaviour. And the consumer filter that makes `owner` observable is at base_commit `__init__`.py:1606 (`for m in members.values() if m.class_ == self.object`) - I read it in the worktree; it is untouched by the patch. So every facet the spec pins is derivable from problem_statement + base repo.

What the spec view WITHHOLDS is exactly the edit mechanics: nothing about switching the namespace key from '.'.join(objpath) to cls.`__qualname__`, nothing about constructing a per-class ModuleAnalyzer.for_module(safe_getattr(cls,'`__module__`')) + .analyze(), nothing about the try/except (AttributeError, PycodeError) restructure, nothing about the new PycodeError import, nothing about dropping the `analyzer` parameter from get_class_members or the caller edit at `__init__`.py:1587. Inputs are abstract (existing : List String, hierarchy : List ClassLevel) with no hint that hierarchy is getmro or that the grouping key is `__qualname__`. A solver handed this spec still has to find the file, the function, and every one of those mechanics.

LOAD-BEARING / GRATUITOUS-PROSE TEST (strip-and-reverify, my own measurement). To rule out that the contrastive narration in the method doc ('the collection cannot be restricted to the most-derived class alone', 'an inherited declaration cannot be attributed to the class being documented', 'decided by hierarchy position') is doing work no formal clause does, I built *_stripped.lean: all 10 /- -/ block comments and every non-marker -- line comment deleted from Solution.lean and all three twins, formal regions untouched. scripts/lean_verify.sh results: Solution_stripped -> EXIT 0 (verifies clean, no sorry); Solution_prepatch_stripped -> EXIT 1; Solution_prepatch_attribution_stripped -> EXIT 1; Solution_prepatch_annotation_prepass_stripped -> EXIT 1 (each with `error: unsolved goals` on the ensures_1 case).

Also verified the unstripped originals: Solution EXIT 0 with 0 errors, all three twins EXIT 1. So the prose is inert to the verifier - G-DIFF discrimination survives its total removal - which means the narration is GRATUITOUS rather than load-bearing. I weighed submitting that as a finding and did NOT, because gratuitousness is only a leak if the removed prose discloses something beyond problem_statement, and per the reconstruction test above each clause restates either the public issue text ('doesn't check for baseclass-namespace') or pre-patch code the solver reads directly. It is redundant, not disclosing. Recording it here so the next reviewer has the measurement rather than my conclusion alone.

**REVIEWER-DIRECTED CONTENT:** none. leakage.reviewer_directed() run over every file in the bundle (Solution.lean, all three twins, mapping.md, refinement.md, meta.json, patch.diff, instance.json, properties.py, axiom_check.py, conformance_check.py, verdict.md) -> clean on all. No file instructs me how to record or which verdict is honest.

STALE-RECORD OBSERVATION (flagging, does not change my verdict). The recorded G-PANEL-3 pass in meta.json was measured against a DIFFERENT artifact: its sources hash is Solution.lean=10e338314cc8, whereas the current file is aa51a50042d3. The stale verdict.md text confirms the drift - it describes the signature as 'hierarchy : List (List AttrDoc)' and spec_view=a5d6187be48e69db, but the current spec has 'hierarchy : List ClassLevel' (owner/annots/attrs) and spec_view=e4525d02a24e242c. The ClassLevel/owner/interleaving structure - i.e. facets (b) and (c) - did not exist in the audited version and was never leak-reviewed. My verdict above is measured on the CURRENT aa51a50042d3 artifact and covers those new facets explicitly. Separately: G-EQ, G-PANEL, G-PANEL-1 and G-PANEL-2 are all recorded FAIL on that same stale hash (G-PANEL-2 alleging a faithfulness divergence on interleaved annotations, G-PANEL-1 a verifying-but-not-resolving rival), so the cell is not green for reasons outside this gate's scope; leakage is orthogonal and I judge it on its own terms.

**CONCLUSION:** the spec view is an abstract behavioural contract whose every discriminating clause is derivable from the public problem_statement plus the pre-patch source at base_commit; it reproduces no gold line, names no patched file or symbol, and withholds all edit mechanics. NO-LEAKAGE.

**ROLE:** attacker 3 - leakage / gold-reconstruction. Judged against the SOLVER-VISIBLE problem_statement ONLY; hints_text deliberately excluded from the screen (the hints do contain the smoking gun - tk0miya's example and 'parses only one module. It should also parse modules of all parent classes' - but the solver never sees them, so I did not credit them).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
