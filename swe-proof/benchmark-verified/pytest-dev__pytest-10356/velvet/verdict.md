# P2 adversarial audit — pytest-dev__pytest-10356

**Backend:** `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 23 admissible attacks re-run of 23 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 23 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 21 | `atk_breadth.lean`, `atk_skipgate.lean`, `atk_order.lean`, `atk_flagignored.lean`, `atk_selectlate.lean`, `atk_lastoffender.lean`, `atk_fixedname.lean`, `atk_nounwrap.lean`, `atk_partial.lean`, `atk_dedupe.lean`, `atk_boundary.lean`, `atk_emptyrefuse.lean`, `atk_persource.lean`, `atk_selfcall.lean`, +7 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_echo.lean`, `atk_forward.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE FOUND — no verifying wrong impl exists. The prior pass's named counterexample (atk_12: normalize_mark_list folded as IDENTITY, so an unchecked `return list(mark_list)` verified and broke testing/test_mark.py::TestFunctional::test_mark_with_wrong_marker) is REPAIRED in this spec revision and no longer reproducible. The current spec widens the element domain to the RAW `Item` (canonical | wrapped | foreign), makes the refusal an observable `Outcome.refused n`, and models `canonicalize` deeply, so the type-checking gate at post:401-402 is visible in the frozen spec view. I re-encoded that exact attack as atk_skipgate.lean (offenders silently skipped instead of refusing) — it now FAILS to verify with a real unsolved goal `Outcome.collected (List.filterMap markOf i_1) = canonicalize (flattenSeq ...)`. I also re-encoded the refusal-IDENTITY variants the old identity fold could not see (atk_lastoffender: names the LAST offender; atk_fixedname: names a constant token; atk_nounwrap: refuses `wrapped` elements instead of taking the annotation out) — all three are rejected with real unsolved goals. Both verifying impls I found (atk_echo, atk_forward) are extensionally EQUAL to the spec function, and both of their materialized faithful patches RESOLVE (F2P 1/1, P2P 79/79, zero failures), including test_mark_with_wrong_marker.
```

**Attacks re-run (23):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -151,25 +151,8 @@
     canonicalize (flattenSeq (if wholeLineage then lineage else [lineage.headD []]))
   do
     -- impl-start
-    -- Select which sources contribute: the whole lineage, or only the class's
-    -- own list; then concatenate the selected sources in order. The fold runs
-    -- from the back, prepending each source's elements before those already
-    -- gathered, yielding their in-order concatenation. The assembled elements
-    -- are canonicalized before they leave.
-    let selected : List (List Item) :=
-      if wholeLineage then lineage else [lineage.headD []]
-    let mut gathered : List Item := []
-    let mut i := selected.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ selected.length
-      invariant gathered = flattenSeq (selected.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let g := selected[i - 1]!
-      gathered := g ++ gathered
-      i := i - 1
-    return canonicalize gathered
+    -- ORACLE ECHO: recompute the postcondition's right-hand side verbatim.
+    return canonicalize (flattenSeq (if wholeLineage then lineage else [lineage.headD []]))
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -188,11 +171,6 @@
 
 prove_correct collectMarks by
   loom_solve
-  rw [flattenSeq_drop_step
-        (if wholeLineage = true then lineage else [lineage.headD []]) i
-        (by omega) (by omega)]
-  simp_all
-
 /- Record a freshly-applied annotation on a class: the class's new own list is
    the canonicalization of its existing own list, extended with the new
    annotation at the end. The existing own elements are obtained by collecting
```

Attack 2 — `atk_forward.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -151,24 +151,21 @@
     canonicalize (flattenSeq (if wholeLineage then lineage else [lineage.headD []]))
   do
     -- impl-start
-    -- Select which sources contribute: the whole lineage, or only the class's
-    -- own list; then concatenate the selected sources in order. The fold runs
-    -- from the back, prepending each source's elements before those already
-    -- gathered, yielding their in-order concatenation. The assembled elements
-    -- are canonicalized before they leave.
+    -- Forward assembly: walk the selected sources front to back, appending each
+    -- source's elements after those already gathered. Same in-order
+    -- concatenation as the backward fold, reached the other way round.
     let selected : List (List Item) :=
       if wholeLineage then lineage else [lineage.headD []]
     let mut gathered : List Item := []
-    let mut i := selected.length
-    while i > 0
+    let mut i := 0
+    while i < selected.length
       invariant 0 ≤ i ∧ i ≤ selected.length
-      invariant gathered = flattenSeq (selected.drop i)
-      done_with i = 0
-      decreasing i
+      invariant gathered = flattenSeq (selected.take i)
+      done_with i = selected.length
+      decreasing selected.length - i
     do
-      let g := selected[i - 1]!
-      gathered := g ++ gathered
-      i := i - 1
+      gathered := gathered ++ (selected.drop i).headD []
+      i := i + 1
     return canonicalize gathered
     -- impl-end
 
@@ -188,11 +185,22 @@
 
 prove_correct collectMarks by
   loom_solve
-  rw [flattenSeq_drop_step
-        (if wholeLineage = true then lineage else [lineage.headD []]) i
-        (by omega) (by omega)]
-  simp_all
-
+  all_goals
+    (have key : ∀ (xs : List (List Item)) (k : Nat), k < xs.length →
+        flattenSeq (xs.take (k + 1)) = flattenSeq (xs.take k) ++ (xs.drop k).headD [] := by
+      intro xs k hk
+      induction k generalizing xs with
+      | zero =>
+          cases xs with
+          | nil => simp at hk
+          | cons hd tl => simp [flattenSeq]
+      | succ n ih =>
+          cases xs with
+          | nil => simp at hk
+          | cons hd tl =>
+              have hn : n < tl.length := by simpa using hk
+              simp [flattenSeq, ih tl hn, List.append_assoc]
+     simp_all)
 /- Record a freshly-applied annotation on a class: the class's new own list is
    the canonicalization of its existing own list, extended with the new
    annotation at the end. The existing own elements are obtained by collecting
```

Attack 3 — `atk_breadth.lean` → rejected (same spec, does not verify — good)

```diff
@@ -151,13 +151,8 @@
     canonicalize (flattenSeq (if wholeLineage then lineage else [lineage.headD []]))
   do
     -- impl-start
-    -- Select which sources contribute: the whole lineage, or only the class's
-    -- own list; then concatenate the selected sources in order. The fold runs
-    -- from the back, prepending each source's elements before those already
-    -- gathered, yielding their in-order concatenation. The assembled elements
-    -- are canonicalized before they leave.
-    let selected : List (List Item) :=
-      if wholeLineage then lineage else [lineage.headD []]
+    -- WRONG (prepatch): only the class's own list ever contributes.
+    let selected : List (List Item) := [lineage.headD []]
     let mut gathered : List Item := []
     let mut i := selected.length
     while i > 0
@@ -188,11 +183,8 @@
 
 prove_correct collectMarks by
   loom_solve
-  rw [flattenSeq_drop_step
-        (if wholeLineage = true then lineage else [lineage.headD []]) i
-        (by omega) (by omega)]
+  rw [flattenSeq_drop_step [lineage.headD []] i (by omega) (by omega)]
   simp_all
-
 /- Record a freshly-applied annotation on a class: the class's new own list is
    the canonicalization of its existing own list, extended with the new
    annotation at the end. The existing own elements are obtained by collecting
```

Attack 4 — `atk_skipgate.lean` → rejected (same spec, does not verify — good)

```diff
@@ -151,11 +151,8 @@
     canonicalize (flattenSeq (if wholeLineage then lineage else [lineage.headD []]))
   do
     -- impl-start
-    -- Select which sources contribute: the whole lineage, or only the class's
-    -- own list; then concatenate the selected sources in order. The fold runs
-    -- from the back, prepending each source's elements before those already
-    -- gathered, yielding their in-order concatenation. The assembled elements
-    -- are canonicalized before they leave.
+    -- WRONG (A4 leg): no refusal. Elements that make no annotation available
+    -- are silently skipped instead of refusing the whole collection.
     let selected : List (List Item) :=
       if wholeLineage then lineage else [lineage.headD []]
     let mut gathered : List Item := []
@@ -169,7 +166,7 @@
       let g := selected[i - 1]!
       gathered := g ++ gathered
       i := i - 1
-    return canonicalize gathered
+    return Outcome.collected (gathered.filterMap markOf)
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -192,7 +189,6 @@
         (if wholeLineage = true then lineage else [lineage.headD []]) i
         (by omega) (by omega)]
   simp_all
-
 /- Record a freshly-applied annotation on a class: the class's new own list is
    the canonicalization of its existing own list, extended with the new
    annotation at the end. The existing own elements are obtained by collecting
```

Attack 5 — `atk_order.lean` → rejected (same spec, does not verify — good)

```diff
@@ -151,24 +151,21 @@
     canonicalize (flattenSeq (if wholeLineage then lineage else [lineage.headD []]))
   do
     -- impl-start
-    -- Select which sources contribute: the whole lineage, or only the class's
-    -- own list; then concatenate the selected sources in order. The fold runs
-    -- from the back, prepending each source's elements before those already
-    -- gathered, yielding their in-order concatenation. The assembled elements
-    -- are canonicalized before they leave.
+    -- WRONG (order): the loop runs forward and still prepends, so the sources
+    -- are assembled in reverse resolution order.
     let selected : List (List Item) :=
       if wholeLineage then lineage else [lineage.headD []]
     let mut gathered : List Item := []
-    let mut i := selected.length
-    while i > 0
+    let mut i := 0
+    while i < selected.length
       invariant 0 ≤ i ∧ i ≤ selected.length
-      invariant gathered = flattenSeq (selected.drop i)
-      done_with i = 0
-      decreasing i
+      invariant gathered = flattenSeq ((selected.take i).reverse)
+      done_with i = selected.length
+      decreasing selected.length - i
     do
-      let g := selected[i - 1]!
+      let g := selected[i]!
       gathered := g ++ gathered
-      i := i - 1
+      i := i + 1
     return canonicalize gathered
     -- impl-end
 
@@ -188,11 +185,7 @@
 
 prove_correct collectMarks by
   loom_solve
-  rw [flattenSeq_drop_step
-        (if wholeLineage = true then lineage else [lineage.headD []]) i
-        (by omega) (by omega)]
-  simp_all
-
+  all_goals simp_all [flattenSeq]
 /- Record a freshly-applied annotation on a class: the class's new own list is
    the canonicalization of its existing own list, extended with the new
    annotation at the end. The existing own elements are obtained by collecting
```

Attack 6 — `atk_flagignored.lean` → rejected (same spec, does not verify — good)

```diff
@@ -151,13 +151,9 @@
     canonicalize (flattenSeq (if wholeLineage then lineage else [lineage.headD []]))
   do
     -- impl-start
-    -- Select which sources contribute: the whole lineage, or only the class's
-    -- own list; then concatenate the selected sources in order. The fold runs
-    -- from the back, prepending each source's elements before those already
-    -- gathered, yielding their in-order concatenation. The assembled elements
-    -- are canonicalized before they leave.
-    let selected : List (List Item) :=
-      if wholeLineage then lineage else [lineage.headD []]
+    -- WRONG (control-flow): the selection branch is gone; the whole lineage
+    -- always contributes, even when only the class's own list should.
+    let selected : List (List Item) := lineage
     let mut gathered : List Item := []
     let mut i := selected.length
     while i > 0
@@ -188,11 +184,8 @@
 
 prove_correct collectMarks by
   loom_solve
-  rw [flattenSeq_drop_step
-        (if wholeLineage = true then lineage else [lineage.headD []]) i
-        (by omega) (by omega)]
+  rw [flattenSeq_drop_step lineage i (by omega) (by omega)]
   simp_all
-
 /- Record a freshly-applied annotation on a class: the class's new own list is
    the canonicalization of its existing own list, extended with the new
    annotation at the end. The existing own elements are obtained by collecting
```

Attack 7 — `atk_selectlate.lean` → rejected (same spec, does not verify — good)

```diff
@@ -151,25 +151,14 @@
     canonicalize (flattenSeq (if wholeLineage then lineage else [lineage.headD []]))
   do
     -- impl-start
-    -- Select which sources contribute: the whole lineage, or only the class's
-    -- own list; then concatenate the selected sources in order. The fold runs
-    -- from the back, prepending each source's elements before those already
-    -- gathered, yielding their in-order concatenation. The assembled elements
-    -- are canonicalized before they leave.
+    -- WRONG: the canonicalizing gate is applied to the WHOLE lineage before the
+    -- selection, so an element of a NON-contributing source can refuse a
+    -- collection it takes no part in.
     let selected : List (List Item) :=
       if wholeLineage then lineage else [lineage.headD []]
-    let mut gathered : List Item := []
-    let mut i := selected.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ selected.length
-      invariant gathered = flattenSeq (selected.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let g := selected[i - 1]!
-      gathered := g ++ gathered
-      i := i - 1
-    return canonicalize gathered
+    return (match canonicalize (flattenSeq lineage) with
+            | Outcome.refused n   => Outcome.refused n
+            | Outcome.collected _ => canonicalize (flattenSeq selected))
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -188,11 +177,7 @@
 
 prove_correct collectMarks by
   loom_solve
-  rw [flattenSeq_drop_step
-        (if wholeLineage = true then lineage else [lineage.headD []]) i
-        (by omega) (by omega)]
-  simp_all
-
+  all_goals simp_all [flattenSeq, canonicalize]
 /- Record a freshly-applied annotation on a class: the class's new own list is
    the canonicalization of its existing own list, extended with the new
    annotation at the end. The existing own elements are obtained by collecting
```

Attack 8 — `atk_lastoffender.lean` → rejected (same spec, does not verify — good)

```diff
@@ -151,11 +151,6 @@
     canonicalize (flattenSeq (if wholeLineage then lineage else [lineage.headD []]))
   do
     -- impl-start
-    -- Select which sources contribute: the whole lineage, or only the class's
-    -- own list; then concatenate the selected sources in order. The fold runs
-    -- from the back, prepending each source's elements before those already
-    -- gathered, yielding their in-order concatenation. The assembled elements
-    -- are canonicalized before they leave.
     let selected : List (List Item) :=
       if wholeLineage then lineage else [lineage.headD []]
     let mut gathered : List Item := []
@@ -169,7 +164,12 @@
       let g := selected[i - 1]!
       gathered := g ++ gathered
       i := i - 1
-    return canonicalize gathered
+    -- WRONG (A4 refusal identity): refuse when some element makes no
+    -- annotation available, but name the LAST such element, not the first.
+    let offenders := gathered.filter (fun it => markOf it = none)
+    return (match offenders.reverse with
+            | []      => Outcome.collected (gathered.filterMap markOf)
+            | it :: _ => Outcome.refused (nameOf it))
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -192,7 +192,6 @@
         (if wholeLineage = true then lineage else [lineage.headD []]) i
         (by omega) (by omega)]
   simp_all
-
 /- Record a freshly-applied annotation on a class: the class's new own list is
    the canonicalization of its existing own list, extended with the new
    annotation at the end. The existing own elements are obtained by collecting
```

Attack 9 — `atk_fixedname.lean` → rejected (same spec, does not verify — good)

```diff
@@ -151,11 +151,6 @@
     canonicalize (flattenSeq (if wholeLineage then lineage else [lineage.headD []]))
   do
     -- impl-start
-    -- Select which sources contribute: the whole lineage, or only the class's
-    -- own list; then concatenate the selected sources in order. The fold runs
-    -- from the back, prepending each source's elements before those already
-    -- gathered, yielding their in-order concatenation. The assembled elements
-    -- are canonicalized before they leave.
     let selected : List (List Item) :=
       if wholeLineage then lineage else [lineage.headD []]
     let mut gathered : List Item := []
@@ -169,7 +164,11 @@
       let g := selected[i - 1]!
       gathered := g ++ gathered
       i := i - 1
-    return canonicalize gathered
+    -- WRONG (A4 refusal identity): the refusal carries a constant token, so
+    -- WHICH element offended is lost.
+    return (if gathered.any (fun it => markOf it = none)
+            then Outcome.refused 0
+            else Outcome.collected (gathered.filterMap markOf))
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -192,7 +191,6 @@
         (if wholeLineage = true then lineage else [lineage.headD []]) i
         (by omega) (by omega)]
   simp_all
-
 /- Record a freshly-applied annotation on a class: the class's new own list is
    the canonicalization of its existing own list, extended with the new
    annotation at the end. The existing own elements are obtained by collecting
```

Attack 10 — `atk_nounwrap.lean` → rejected (same spec, does not verify — good)

```diff
@@ -151,11 +151,6 @@
     canonicalize (flattenSeq (if wholeLineage then lineage else [lineage.headD []]))
   do
     -- impl-start
-    -- Select which sources contribute: the whole lineage, or only the class's
-    -- own list; then concatenate the selected sources in order. The fold runs
-    -- from the back, prepending each source's elements before those already
-    -- gathered, yielding their in-order concatenation. The assembled elements
-    -- are canonicalized before they leave.
     let selected : List (List Item) :=
       if wholeLineage then lineage else [lineage.headD []]
     let mut gathered : List Item := []
@@ -169,7 +164,15 @@
       let g := selected[i - 1]!
       gathered := g ++ gathered
       i := i - 1
-    return canonicalize gathered
+    -- WRONG (A4 unwrap leg): only already-canonical elements are accepted; an
+    -- applicator object carrying an annotation is treated as an offender
+    -- instead of having its annotation taken out of it.
+    let step : Item → Outcome → Outcome := fun it acc =>
+      match it with
+      | Item.canonical m => consMark m acc
+      | Item.wrapped _   => Outcome.refused (nameOf it)
+      | Item.foreign n   => Outcome.refused n
+    return gathered.foldr step (Outcome.collected [])
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -192,7 +195,6 @@
         (if wholeLineage = true then lineage else [lineage.headD []]) i
         (by omega) (by omega)]
   simp_all
-
 /- Record a freshly-applied annotation on a class: the class's new own list is
    the canonicalization of its existing own list, extended with the new
    annotation at the end. The existing own elements are obtained by collecting
```

Attack 11 — `atk_partial.lean` → rejected (same spec, does not verify — good)

```diff
@@ -151,11 +151,6 @@
     canonicalize (flattenSeq (if wholeLineage then lineage else [lineage.headD []]))
   do
     -- impl-start
-    -- Select which sources contribute: the whole lineage, or only the class's
-    -- own list; then concatenate the selected sources in order. The fold runs
-    -- from the back, prepending each source's elements before those already
-    -- gathered, yielding their in-order concatenation. The assembled elements
-    -- are canonicalized before they leave.
     let selected : List (List Item) :=
       if wholeLineage then lineage else [lineage.headD []]
     let mut gathered : List Item := []
@@ -169,7 +164,14 @@
       let g := selected[i - 1]!
       gathered := g ++ gathered
       i := i - 1
-    return canonicalize gathered
+    -- WRONG (partial domain): the refusal obligation is discharged only for
+    -- the FIRST assembled element; later offenders are silently skipped.
+    return (match gathered with
+            | []       => Outcome.collected []
+            | it :: rest =>
+                match markOf it with
+                | none   => Outcome.refused (nameOf it)
+                | some m => Outcome.collected (m :: rest.filterMap markOf))
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -192,7 +194,6 @@
         (if wholeLineage = true then lineage else [lineage.headD []]) i
         (by omega) (by omega)]
   simp_all
-
 /- Record a freshly-applied annotation on a class: the class's new own list is
    the canonicalization of its existing own list, extended with the new
    annotation at the end. The existing own elements are obtained by collecting
```

Attack 12 — `atk_dedupe.lean` → rejected (same spec, does not verify — good)

```diff
@@ -151,11 +151,6 @@
     canonicalize (flattenSeq (if wholeLineage then lineage else [lineage.headD []]))
   do
     -- impl-start
-    -- Select which sources contribute: the whole lineage, or only the class's
-    -- own list; then concatenate the selected sources in order. The fold runs
-    -- from the back, prepending each source's elements before those already
-    -- gathered, yielding their in-order concatenation. The assembled elements
-    -- are canonicalized before they leave.
     let selected : List (List Item) :=
       if wholeLineage then lineage else [lineage.headD []]
     let mut gathered : List Item := []
@@ -169,7 +164,8 @@
       let g := selected[i - 1]!
       gathered := g ++ gathered
       i := i - 1
-    return canonicalize gathered
+    -- WRONG: collapse duplicate raw elements before canonicalizing.
+    return canonicalize gathered.eraseDups
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -192,7 +188,6 @@
         (if wholeLineage = true then lineage else [lineage.headD []]) i
         (by omega) (by omega)]
   simp_all
-
 /- Record a freshly-applied annotation on a class: the class's new own list is
    the canonicalization of its existing own list, extended with the new
    annotation at the end. The existing own elements are obtained by collecting
```

Attack 13 — `atk_boundary.lean` → rejected (same spec, does not verify — good)

```diff
@@ -151,11 +151,6 @@
     canonicalize (flattenSeq (if wholeLineage then lineage else [lineage.headD []]))
   do
     -- impl-start
-    -- Select which sources contribute: the whole lineage, or only the class's
-    -- own list; then concatenate the selected sources in order. The fold runs
-    -- from the back, prepending each source's elements before those already
-    -- gathered, yielding their in-order concatenation. The assembled elements
-    -- are canonicalized before they leave.
     let selected : List (List Item) :=
       if wholeLineage then lineage else [lineage.headD []]
     let mut gathered : List Item := []
@@ -169,7 +164,8 @@
       let g := selected[i - 1]!
       gathered := g ++ gathered
       i := i - 1
-    return canonicalize gathered
+    -- WRONG (boundary): drop the first assembled element.
+    return canonicalize gathered.tail
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -192,7 +188,6 @@
         (if wholeLineage = true then lineage else [lineage.headD []]) i
         (by omega) (by omega)]
   simp_all
-
 /- Record a freshly-applied annotation on a class: the class's new own list is
    the canonicalization of its existing own list, extended with the new
    annotation at the end. The existing own elements are obtained by collecting
```

Attack 14 — `atk_emptyrefuse.lean` → rejected (same spec, does not verify — good)

```diff
@@ -151,25 +151,11 @@
     canonicalize (flattenSeq (if wholeLineage then lineage else [lineage.headD []]))
   do
     -- impl-start
-    -- Select which sources contribute: the whole lineage, or only the class's
-    -- own list; then concatenate the selected sources in order. The fold runs
-    -- from the back, prepending each source's elements before those already
-    -- gathered, yielding their in-order concatenation. The assembled elements
-    -- are canonicalized before they leave.
-    let selected : List (List Item) :=
-      if wholeLineage then lineage else [lineage.headD []]
-    let mut gathered : List Item := []
-    let mut i := selected.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ selected.length
-      invariant gathered = flattenSeq (selected.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let g := selected[i - 1]!
-      gathered := g ++ gathered
-      i := i - 1
-    return canonicalize gathered
+    -- WRONG (boundary): an empty lineage refuses instead of collecting nothing.
+    if lineage.isEmpty then
+      return Outcome.refused 0
+    else
+      return canonicalize (flattenSeq (if wholeLineage then lineage else [lineage.headD []]))
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -188,11 +174,7 @@
 
 prove_correct collectMarks by
   loom_solve
-  rw [flattenSeq_drop_step
-        (if wholeLineage = true then lineage else [lineage.headD []]) i
-        (by omega) (by omega)]
-  simp_all
-
+  all_goals simp_all [flattenSeq, canonicalize]
 /- Record a freshly-applied annotation on a class: the class's new own list is
    the canonicalization of its existing own list, extended with the new
    annotation at the end. The existing own elements are obtained by collecting
```

Attack 15 — `atk_persource.lean` → rejected (same spec, does not verify — good)

```diff
@@ -151,11 +151,6 @@
     canonicalize (flattenSeq (if wholeLineage then lineage else [lineage.headD []]))
   do
     -- impl-start
-    -- Select which sources contribute: the whole lineage, or only the class's
-    -- own list; then concatenate the selected sources in order. The fold runs
-    -- from the back, prepending each source's elements before those already
-    -- gathered, yielding their in-order concatenation. The assembled elements
-    -- are canonicalized before they leave.
     let selected : List (List Item) :=
       if wholeLineage then lineage else [lineage.headD []]
     let mut gathered : List Item := []
@@ -169,7 +164,22 @@
       let g := selected[i - 1]!
       gathered := g ++ gathered
       i := i - 1
-    return canonicalize gathered
+    -- Restructured: canonicalize by a backward fold over the assembly. Same
+    -- function as `canonicalize`, a different route to it.
+    let mut acc : Outcome := Outcome.collected []
+    let mut j := gathered.length
+    while j > 0
+      invariant 0 ≤ j ∧ j ≤ gathered.length
+      invariant acc = canonicalize (gathered.drop j)
+      done_with j = 0
+      decreasing j
+    do
+      let it := (gathered.drop (j - 1)).headD (Item.canonical 0)
+      acc := (match markOf it with
+              | none   => Outcome.refused (nameOf it)
+              | some m => consMark m acc)
+      j := j - 1
+    return acc
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -192,7 +202,6 @@
         (if wholeLineage = true then lineage else [lineage.headD []]) i
         (by omega) (by omega)]
   simp_all
-
 /- Record a freshly-applied annotation on a class: the class's new own list is
    the canonicalization of its existing own list, extended with the new
    annotation at the end. The existing own elements are obtained by collecting
```

Attack 16 — `atk_selfcall.lean` → rejected (same spec, does not verify — good)

```diff
@@ -151,25 +151,9 @@
     canonicalize (flattenSeq (if wholeLineage then lineage else [lineage.headD []]))
   do
     -- impl-start
-    -- Select which sources contribute: the whole lineage, or only the class's
-    -- own list; then concatenate the selected sources in order. The fold runs
-    -- from the back, prepending each source's elements before those already
-    -- gathered, yielding their in-order concatenation. The assembled elements
-    -- are canonicalized before they leave.
-    let selected : List (List Item) :=
-      if wholeLineage then lineage else [lineage.headD []]
-    let mut gathered : List Item := []
-    let mut i := selected.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ selected.length
-      invariant gathered = flattenSeq (selected.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let g := selected[i - 1]!
-      gathered := g ++ gathered
-      i := i - 1
-    return canonicalize gathered
+    -- VACUITY PROBE: assume this method's own contract via a self-call.
+    let r ← collectMarks lineage wholeLineage
+    return r
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -188,11 +172,6 @@
 
 prove_correct collectMarks by
   loom_solve
-  rw [flattenSeq_drop_step
-        (if wholeLineage = true then lineage else [lineage.headD []]) i
-        (by omega) (by omega)]
-  simp_all
-
 /- Record a freshly-applied annotation on a class: the class's new own list is
    the canonicalization of its existing own list, extended with the new
    annotation at the end. The existing own elements are obtained by collecting
```

Attack 17 — `atk_diverge.lean` → rejected (same spec, does not verify — good)

```diff
@@ -151,25 +151,15 @@
     canonicalize (flattenSeq (if wholeLineage then lineage else [lineage.headD []]))
   do
     -- impl-start
-    -- Select which sources contribute: the whole lineage, or only the class's
-    -- own list; then concatenate the selected sources in order. The fold runs
-    -- from the back, prepending each source's elements before those already
-    -- gathered, yielding their in-order concatenation. The assembled elements
-    -- are canonicalized before they leave.
-    let selected : List (List Item) :=
-      if wholeLineage then lineage else [lineage.headD []]
-    let mut gathered : List Item := []
-    let mut i := selected.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ selected.length
-      invariant gathered = flattenSeq (selected.drop i)
-      done_with i = 0
-      decreasing i
+    -- TERMINATION PROBE: the measure is not decreased.
+    let mut k : Nat := 1
+    while k > 0
+      invariant 0 ≤ k
+      done_with k = 0
+      decreasing k
     do
-      let g := selected[i - 1]!
-      gathered := g ++ gathered
-      i := i - 1
-    return canonicalize gathered
+      k := k + 1
+    return canonicalize (flattenSeq (if wholeLineage then lineage else [lineage.headD []]))
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -188,11 +178,7 @@
 
 prove_correct collectMarks by
   loom_solve
-  rw [flattenSeq_drop_step
-        (if wholeLineage = true then lineage else [lineage.headD []]) i
-        (by omega) (by omega)]
-  simp_all
-
+  all_goals simp_all
 /- Record a freshly-applied annotation on a class: the class's new own list is
    the canonicalization of its existing own list, extended with the new
    annotation at the end. The existing own elements are obtained by collecting
```

Attack 18 — `atk_falseinv.lean` → rejected (same spec, does not verify — good)

```diff
@@ -151,11 +151,8 @@
     canonicalize (flattenSeq (if wholeLineage then lineage else [lineage.headD []]))
   do
     -- impl-start
-    -- Select which sources contribute: the whole lineage, or only the class's
-    -- own list; then concatenate the selected sources in order. The fold runs
-    -- from the back, prepending each source's elements before those already
-    -- gathered, yielding their in-order concatenation. The assembled elements
-    -- are canonicalized before they leave.
+    -- VACUITY PROBE: a false invariant. `Assert(False)`-style control: if this
+    -- verifies, any impl can be smuggled through under a bogus invariant.
     let selected : List (List Item) :=
       if wholeLineage then lineage else [lineage.headD []]
     let mut gathered : List Item := []
@@ -163,13 +160,14 @@
     while i > 0
       invariant 0 ≤ i ∧ i ≤ selected.length
       invariant gathered = flattenSeq (selected.drop i)
+      invariant False
       done_with i = 0
       decreasing i
     do
       let g := selected[i - 1]!
       gathered := g ++ gathered
       i := i - 1
-    return canonicalize gathered
+    return Outcome.refused 42
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -192,7 +190,7 @@
         (if wholeLineage = true then lineage else [lineage.headD []]) i
         (by omega) (by omega)]
   simp_all
-
+  all_goals simp_all
 /- Record a freshly-applied annotation on a class: the class's new own list is
    the canonicalization of its existing own list, extended with the new
    annotation at the end. The existing own elements are obtained by collecting
```

Attack 19 — `atk_vacuity_const.lean` → rejected (same spec, does not verify — good)

```diff
@@ -151,25 +151,8 @@
     canonicalize (flattenSeq (if wholeLineage then lineage else [lineage.headD []]))
   do
     -- impl-start
-    -- Select which sources contribute: the whole lineage, or only the class's
-    -- own list; then concatenate the selected sources in order. The fold runs
-    -- from the back, prepending each source's elements before those already
-    -- gathered, yielding their in-order concatenation. The assembled elements
-    -- are canonicalized before they leave.
-    let selected : List (List Item) :=
-      if wholeLineage then lineage else [lineage.headD []]
-    let mut gathered : List Item := []
-    let mut i := selected.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ selected.length
-      invariant gathered = flattenSeq (selected.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let g := selected[i - 1]!
-      gathered := g ++ gathered
-      i := i - 1
-    return canonicalize gathered
+    -- VACUITY CONTROL: ignore the inputs entirely.
+    return Outcome.collected []
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -188,11 +171,7 @@
 
 prove_correct collectMarks by
   loom_solve
-  rw [flattenSeq_drop_step
-        (if wholeLineage = true then lineage else [lineage.headD []]) i
-        (by omega) (by omega)]
-  simp_all
-
+  all_goals simp_all [flattenSeq, canonicalize]
 /- Record a freshly-applied annotation on a class: the class's new own list is
    the canonicalization of its existing own list, extended with the new
    annotation at the end. The existing own elements are obtained by collecting
```

Attack 20 — `atk_attach_mro.lean` → rejected (same spec, does not verify — good)

```diff
@@ -206,9 +206,12 @@
   ensures out = withMark (canonicalize (lineage.headD [])) mark
   do
     -- impl-start
-    let own ← collectMarks lineage false
+    -- WRONG (B1): collect with the WHOLE lineage before extending, absorbing
+    -- ancestors' annotations into this class's own list.
+    let own ← collectMarks lineage true
     return withMark own mark
     -- impl-end
 
 prove_correct attachMark by
   loom_solve
+  all_goals simp_all [flattenSeq]
```

Attack 21 — `atk_attach_prepend.lean` → rejected (same spec, does not verify — good)

```diff
@@ -206,9 +206,11 @@
   ensures out = withMark (canonicalize (lineage.headD [])) mark
   do
     -- impl-start
+    -- WRONG (B2): put the new annotation in FRONT of the existing ones.
     let own ← collectMarks lineage false
-    return withMark own mark
+    return consMark mark own
     -- impl-end
 
 prove_correct attachMark by
   loom_solve
+  all_goals simp_all [consMark, withMark, flattenSeq]
```

Attack 22 — `atk_attach_swallow.lean` → rejected (same spec, does not verify — good)

```diff
@@ -206,9 +206,14 @@
   ensures out = withMark (canonicalize (lineage.headD [])) mark
   do
     -- impl-start
+    -- WRONG (B2): if the existing own list refuses, ignore the refusal and
+    -- record the new annotation on its own anyway.
     let own ← collectMarks lineage false
-    return withMark own mark
+    return (match own with
+            | Outcome.refused _  => Outcome.collected [mark]
+            | Outcome.collected ms => Outcome.collected (ms ++ [mark]))
     -- impl-end
 
 prove_correct attachMark by
   loom_solve
+  all_goals simp_all [withMark, flattenSeq]
```

Attack 23 — `atk_attach_filter.lean` → rejected (same spec, does not verify — good)

```diff
@@ -206,9 +206,12 @@
   ensures out = withMark (canonicalize (lineage.headD [])) mark
   do
     -- impl-start
-    let own ← collectMarks lineage false
-    return withMark own mark
+    -- WRONG (B2 partial domain): silently drop own elements that make no
+    -- annotation available, then record the new one.
+    let own := (lineage.headD []).filterMap markOf
+    return Outcome.collected (own ++ [mark])
     -- impl-end
 
 prove_correct attachMark by
   loom_solve
+  all_goals simp_all [withMark, canonicalize]
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No foreign callee is consumed as an axiom, and none is folded away as a
   convenience. The canonicalizing step the collection finishes with — taking the
   annotation out of each assembled raw element, and REFUSING the whole
   collection when an element makes none available — is modeled DEEPLY below
   (`markOf` / `canonicalize`), as is the assembly it is applied to
   (`flattenSeq`). Both deep models are validated against the real
   sub-computations out of band (mapping.md §3, axiom_check.py / G-AX). -/
-- axioms-end

-- pure-start
/- A canonical annotation (an opaque identity token; equality is all that is
   observed). -/
abbrev Mark := Int

/- One RAW element of a source's attached-annotation list, as it is actually
   found there. The three shapes are distinguished because the collection treats
   them differently:

     * `canonical m` — already a canonical annotation; taken as it stands;
     * `wrapped m`   — an applicator object that carries the annotation `m`
       inside it; the annotation is taken OUT of it (this is the ordinary shape
       when a source's list is written by hand);
     * `foreign n`   — an element from which NO annotation can be obtained: it is
       no annotation itself and carries none. `n` is its own identity token, the
       one a refusal names.

   `canonical` and `wrapped` both make an annotation available; only `foreign`
   does not. -/
inductive Item where
  | canonical (m : Mark)
  | wrapped (m : Mark)
  | foreign (n : Int)
  deriving DecidableEq

/- What a collection yields. Either it produced a canonical annotation sequence,
   or it REFUSED, naming the offending element: an element it was asked to
   canonicalize makes no annotation available, and then the collection produces
   no sequence at all — the refusal is the observable result, not a
   silently-skipped element, not a substituted annotation, and not an empty
   sequence. -/
inductive Outcome where
  | refused (offending : Int)
  | collected (ms : List Mark)
  deriving DecidableEq

/- The annotation a raw element makes available, if any. -/
def markOf : Item → Option Mark
  | Item.canonical m => some m
  | Item.wrapped m   => some m
  | Item.foreign _   => none

/- The identity token a raw element is known by — for an element that makes no
   annotation available, this is what a refusal names. -/
def nameOf : Item → Int
  | Item.canonical m => m
  | Item.wrapped m   => m
  | Item.foreign n   => n

@[grind] lemma markOf_canonical (m : Mark) : markOf (Item.canonical m) = some m := rfl
@[grind] lemma markOf_wrapped (m : Mark) : markOf (Item.wrapped m) = some m := rfl
@[grind] lemma markOf_foreign (n : Int) : markOf (Item.foreign n) = none := rfl

/- The in-order concatenation of a sequence of per-source raw element lists: the
   elements contributed by the first source, then those of each subsequent
   source, and nothing else. A source that contributes none appears as an empty
   element and is simply skipped without ending the assembly. Front-recursive
   (one unfold per source) so a backward impl loop that prepends one source's
   elements each step can discharge the value equality (the fold pattern,
   plan §5.4). -/
def flattenSeq : List (List Item) → List Item
  | []      => []
  | g :: gs => g ++ flattenSeq gs

@[grind] lemma flattenSeq_nil : flattenSeq [] = [] := rfl
@[grind] lemma flattenSeq_cons (g : List Item) (gs : List (List Item)) :
    flattenSeq (g :: gs) = g ++ flattenSeq gs := rfl

/- A single-source assembly is just that source's own elements. -/
@[grind] lemma flattenSeq_singleton (g : List Item) : flattenSeq [g] = g := by
  simp [flattenSeq]

/- Put one annotation in front of a collection's outcome. A refusal stays that
   same refusal: once the collection has been refused, no annotation is carried
   out of it. -/
def consMark (m : Mark) (o : Outcome) : Outcome :=
  match o with
  | Outcome.collected ms => Outcome.collected (m :: ms)
  | Outcome.refused n    => Outcome.refused n

/- Canonicalize an assembled element sequence, IN ORDER: every element must make
   an annotation available, and that annotation — not the element it came out of
   — is what the resulting sequence carries, at the same position. If an element
   makes none available, the whole collection is REFUSED and yields no sequence,
   naming the FIRST such element: the obligation is discharged element by element
   from the front, never assumed away and never postponed. Front-recursive, one
   element per unfold. -/
def canonicalize : List Item → Outcome
  | [] => Outcome.collected []
  | it :: rest =>
      match markOf it with
      | none   => Outcome.refused (nameOf it)
      | some m => consMark m (canonicalize rest)

@[grind] lemma canonicalize_nil : canonicalize [] = Outcome.collected [] := rfl

/- Extend a collection's outcome with one further annotation at the end. A
   refusal stays that same refusal — nothing is recorded on top of a collection
   that was refused. -/
def withMark (o : Outcome) (mark : Mark) : Outcome :=
  match o with
  | Outcome.collected ms => Outcome.collected (ms ++ [mark])
  | Outcome.refused n    => Outcome.refused n

@[grind] lemma withMark_collected (ms : List Mark) (mark : Mark) :
    withMark (Outcome.collected ms) mark = Outcome.collected (ms ++ [mark]) := rfl
@[grind] lemma withMark_refused (n : Int) (mark : Mark) :
    withMark (Outcome.refused n) mark = Outcome.refused n := rfl
-- pure-end

-- pre-conditions-start
-- (preconditions are inline on each `method`; none are module-level)
-- pre-conditions-end

-- post-conditions-start
-- (postconditions are the inline `ensures` clauses on each `method` below)
-- post-conditions-end

/- Collect the annotations of a class. `lineage` is the ordered sequence of the
   per-source raw element lists that may contribute, the class's own list first.
   When `wholeLineage` is true every source in the lineage contributes (so
   annotations applied to any ancestor are kept, not just those of the nearest
   one); when false only the class's own list (the first element) does. The
   contributing sources are assembled in order, and the assembled elements are
   then canonicalized: each yields the annotation it makes available, and the
   collection is REFUSED as a whole — naming the first offender — if some
   assembled element makes none. Elements of sources that do NOT contribute are
   never canonicalized, so they cannot refuse a collection they take no part in.
   `lineage` is read-only. -/
method collectMarks (lineage : List (List Item)) (wholeLineage : Bool)
    return (out : Outcome)
  ensures out =
    canonicalize (flattenSeq (if wholeLineage then lineage else [lineage.headD []]))
  do
    -- impl-start
    -- Select which sources contribute: the whole lineage, or only the class's
    -- own list; then concatenate the selected sources in order. The fold runs
    -- from the back, prepending each source's elements before those already
    -- gathered, yielding their in-order concatenation. The assembled elements
    -- are canonicalized before they leave.
    let selected : List (List Item) :=
      if wholeLineage then lineage else [lineage.headD []]
    let mut gathered : List Item := []
    let mut i := selected.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ selected.length
      invariant gathered = flattenSeq (selected.drop i)
      done_with i = 0
      decreasing i
    do
      let g := selected[i - 1]!
      gathered := g ++ gathered
      i := i - 1
    return canonicalize gathered
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `flattenSeq` peels one source's elements off the
   front of its output. This is the single goal `loom_solve` leaves. -/
lemma flattenSeq_drop_step (xs : List (List Item)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ xs.length) :
    flattenSeq (xs.drop (i - 1)) = xs[i - 1]! ++ flattenSeq (xs.drop i) := by
  have hlt : i - 1 < xs.length := by omega
  have hcons : xs.drop (i - 1) = xs[i - 1]! :: xs.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, flattenSeq_cons]

prove_correct collectMarks by
  loom_solve
  rw [flattenSeq_drop_step
        (if wholeLineage = true then lineage else [lineage.headD []]) i
        (by omega) (by omega)]
  simp_all

/- Record a freshly-applied annotation on a class: the class's new own list is
   the canonicalization of its existing own list, extended with the new
   annotation at the end. The existing own elements are obtained by collecting
   WITHOUT the lineage (only the class's own), so applying an annotation never
   absorbs ancestors' annotations into the class's own list; and if that own list
   holds an element making no annotation available, the whole recording is
   REFUSED — the new annotation is not recorded on top of a refusal, and the
   offending element is not dropped. `lineage` and `mark` are read-only. -/
method attachMark (lineage : List (List Item)) (mark : Mark)
    return (out : Outcome)
  ensures out = withMark (canonicalize (lineage.headD [])) mark
  do
    -- impl-start
    let own ← collectMarks lineage false
    return withMark own mark
    -- impl-end

prove_correct attachMark by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL:** 23 same-spec attacks (all same_spec=True via swebench_unified.markers.same_spec) + positive control, all; verified with `bash scripts/lean_verify.sh <f>.lean` run 4-at-a-time as concurrent background jobs. Repo worktree at base_commit: wt (restored clean; `git status --porcelain` empty).

WHY SOUND — the structural argument. The `ensures` clauses are TOTAL FUNCTIONAL EQUALITIES (`out = canonicalize (flattenSeq (if wholeLineage then lineage else [lineage.headD []]))` and `out = withMark (canonicalize (lineage.headD [])) mark`), with NO precondition and NO existential/relational slack. So any impl that verifies is extensionally equal to that function on EVERY input; there is no room for a divergent-but-verifying impl. Soundness therefore reduces to two checks, which I ran directly rather than assuming:

(1) Does the spec FUNCTION equal GOLD? model_vs_gold.py transliterates the frozen pure region (markOf/nameOf/flattenSeq/canonicalize) and diffs it against the GOLD-PATCHED get_unpacked_marks over 1500 randomly generated real class hierarchies (varying MRO depth/branching incl. diamonds, per-class own lists mixing all three element shapes, present/absent pytestmark) plus 400 non-class objects (list / non-list / absent attr), both flag values, comparing SUCCESS VALUES and REFUSAL IDENTITY => 0 failures. attach_vs_gold.py does the same for attachMark vs GOLD store_mark over 1200 cases, additionally asserting a refusal leaves obj.pytestmark UNMUTATED => 0 failures. edge_vs_gold.py covers the edges the bulk fuzz under-samples (class with a bare-Mark / str non-list attr; a wrapper whose.mark is a NON-Mark, confirming the refusal names the UNWRAPPED value as mapping.md §2 claims; tuple attr; empty-everything deep MRO; first-offender ACROSS source boundaries; and a poisoned ANCESTOR with consider_mro=False, confirming a non-contributing source cannot refuse) => 0 failures.

(2) Is the obligation non-vacuous? Controls atk_vacuity_const (`return Outcome.collected []`, ignores inputs) and atk_falseinv (`invariant False`) are both REJECTED (atk_falseinv leaves the literal goal `⊢ False`), and atk_selfcall (assume-own-contract via self-call) fails termination. So prove_correct is a real obligation.

A-LEG AUDIT (the assigned focus). meta.json axioms = [] and Solution.lean declares no `axiom`, so there are no A-consumed legs; the single A-reference leg is A4 (canonicalize/markOf/nameOf <-> normalize_mark_list). I independently validated it with a4_check.py, which loads the REAL `_pytest`.mark.structures.normalize_mark_list from the base_commit worktree (host `py` shim stubbed to only supply py.path.local, so the genuine callee module loads unmodified) and diffs it against the Lean model on: all-canonical lists, all-wrapped lists, an offender-POSITION sweep, ALL two-offender pairs (must name the FIRST), and 4000 randomized mixed-shape fuzz cases — asserting both success values and the exact TypeError message identity => 0 failures. I also confirmed the A4 premise mechanically: normalize_mark_list is BYTE-IDENTICAL between base and post (`git show HEAD:...` vs patched), base returned the lazy generator while post wraps it in `list(...)`, which is what makes the refusal observable. So the A-reference correspondence to the real callee holds.

refinement.md leg audit: every leg is tagged R (A1, A5, B3, B4), I (A2, A3, B1, B2) or A-reference (A4); NO kind-3 (inexpressible-changed-op) legs and no A-consumed legs — §C's claim checks out. The two genuinely-changed operations (the MRO-aware flatten and consider_mro=False storage) are modeled deeply as verified methods, not axiomatized, satisfying directive 7.

RESOLVE RUNS (the mandatory step — executed, not speculated). Exactly 2 of 23 attacks verify, and BOTH are behaviorally correct impls rather than wrong ones, so I materialized and RAN both faithful patches through the official harness (swebench_unified.harness.run_resolve, timeout=1800, retries=1):
- atk_echo.lean (exit 0; ungrounded-ORACLE-ECHO: impl literally recomputes the postcondition RHS) -> patch_echo.diff -> RESOLVED=True, note='resolved', FAIL_TO_PASS 1/1, PASS_TO_PASS 79/79, 0 failures. Note test_mark_with_wrong_marker is among the PASSING P2P tests — the prior audit's break is gone.
- atk_forward.lean (exit 0; structurally DIFFERENT verifying impl: forward `while i < selected.length` assembly with invariant `gathered = flattenSeq (selected.take i)`, helper lemma proved inline so spec regions stay byte-identical) -> patch_forward.diff -> RESOLVED=True, FAIL_TO_PASS 1/1, PASS_TO_PASS 79/79, 0 failures.
So no verifying impl's faithful patch fails to resolve => NOT BROKEN.

**PREPATCH REPRODUCED:** yes, both twins. I re-encoded the prepatch breadth bug myself as atk_breadth.lean (only the nearest own list contributes) => exit 1, real rewrite/goal failure; and re-ran the shipped Solution_prepatch_1.lean (exit 1) and Solution_prepatch_2.lean (exit 1, unsolved goals). atk_attach_mro.lean independently re-encodes the prepatch_2 bug (collectMarks lineage true inside attachMark) => exit 1.

REJECTED ATTACKS (all exit 1 with GENUINE unsolved goals, not tactic/syntax artifacts — I audited every log and REPAIRED my own elaboration bugs in atk_dedupe/atk_boundary/atk_partial (stray grind), atk_diverge (Option-Nat numeral), atk_persource (missing Inhabited Item), atk_emptyrefuse and atk_selectlate (bad tactic/match shape) before counting them): breadth, skipgate, order (reverse assembly), flagignored (selection branch removed), selectlate (gate applied before selection so a non-contributing source refuses), lastoffender, fixedname, nounwrap, partial (only the first element's refusal obligation discharged), dedupe (diamond duplicates collapsed), boundary (first element dropped), emptyrefuse (empty lineage refused), persource (restructured backward canonicalize fold — rejected only because loom left a goal my inline script did not close; not a spec weakness), selfcall, diverge, falseinv, vacuity_const, attach_mro, attach_prepend (new mark at the front), attach_swallow (refusal swallowed), attach_filter (offenders silently filtered from the own list).

CAVEAT / non-blocking: atk_persource is a semantically-EQUIVALENT impl that I failed to prove within the heartbeat budget, so its exit-1 reflects my tactic script rather than a spec rejection; it is submitted for completeness but is not evidence of tightness. This does not affect the verdict, which rests on the functional-equality argument plus the two executed resolve runs.

**VERDICT:** SOUND. 23 attacks run (>=5 required), 2 verified, both verifying impls' faithful patches EXECUTED through run_resolve and both RESOLVED; positive control verifies (exit 0); both prepatch twins reproduce as failures; the A4 deep model is validated against the real unchanged callee including refusal identity; no kind-3 legs. verify => correct holds for this bundle.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 23 admissible attacks re-run of 23 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 23 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 21 | `atk_breadth.lean`, `atk_skipgate.lean`, `atk_order.lean`, `atk_flagignored.lean`, `atk_selectlate.lean`, `atk_lastoffender.lean`, `atk_fixedname.lean`, `atk_nounwrap.lean`, `atk_partial.lean`, `atk_dedupe.lean`, `atk_boundary.lean`, `atk_emptyrefuse.lean`, `atk_persource.lean`, `atk_selfcall.lean`, +7 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_echo.lean`, `atk_forward.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE FOUND — no verifying wrong impl exists. The prior pass's named counterexample (atk_12: normalize_mark_list folded as IDENTITY, so an unchecked `return list(mark_list)` verified and broke testing/test_mark.py::TestFunctional::test_mark_with_wrong_marker) is REPAIRED in this spec revision and no longer reproducible. The current spec widens the element domain to the RAW `Item` (canonical | wrapped | foreign), makes the refusal an observable `Outcome.refused n`, and models `canonicalize` deeply, so the type-checking gate at post:401-402 is visible in the frozen spec view. I re-encoded that exact attack as atk_skipgate.lean (offenders silently skipped instead of refusing) — it now FAILS to verify with a real unsolved goal `Outcome.collected (List.filterMap markOf i_1) = canonicalize (flattenSeq ...)`. I also re-encoded the refusal-IDENTITY variants the old identity fold could not see (atk_lastoffender: names the LAST offender; atk_fixedname: names a constant token; atk_nounwrap: refuses `wrapped` elements instead of taking the annotation out) — all three are rejected with real unsolved goals. Both verifying impls I found (atk_echo, atk_forward) are extensionally EQUAL to the spec function, and both of their materialized faithful patches RESOLVE (F2P 1/1, P2P 79/79, zero failures), including test_mark_with_wrong_marker.
```

**Attacks re-run (23):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 23 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 2 — `atk_forward.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_breadth.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_skipgate.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_order.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_flagignored.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_selectlate.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_lastoffender.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_fixedname.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_nounwrap.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_partial.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_dedupe.lean` → rejected (same spec, does not verify — good)

Attack 13 — `atk_boundary.lean` → rejected (same spec, does not verify — good)

Attack 14 — `atk_emptyrefuse.lean` → rejected (same spec, does not verify — good)

Attack 15 — `atk_persource.lean` → rejected (same spec, does not verify — good)

Attack 16 — `atk_selfcall.lean` → rejected (same spec, does not verify — good)

Attack 17 — `atk_diverge.lean` → rejected (same spec, does not verify — good)

Attack 18 — `atk_falseinv.lean` → rejected (same spec, does not verify — good)

Attack 19 — `atk_vacuity_const.lean` → rejected (same spec, does not verify — good)

Attack 20 — `atk_attach_mro.lean` → rejected (same spec, does not verify — good)

Attack 21 — `atk_attach_prepend.lean` → rejected (same spec, does not verify — good)

Attack 22 — `atk_attach_swallow.lean` → rejected (same spec, does not verify — good)

Attack 23 — `atk_attach_filter.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No foreign callee is consumed as an axiom, and none is folded away as a
   convenience. The canonicalizing step the collection finishes with — taking the
   annotation out of each assembled raw element, and REFUSING the whole
   collection when an element makes none available — is modeled DEEPLY below
   (`markOf` / `canonicalize`), as is the assembly it is applied to
   (`flattenSeq`). Both deep models are validated against the real
   sub-computations out of band (mapping.md §3, axiom_check.py / G-AX). -/
-- axioms-end

-- pure-start
/- A canonical annotation (an opaque identity token; equality is all that is
   observed). -/
abbrev Mark := Int

/- One RAW element of a source's attached-annotation list, as it is actually
   found there. The three shapes are distinguished because the collection treats
   them differently:

     * `canonical m` — already a canonical annotation; taken as it stands;
     * `wrapped m`   — an applicator object that carries the annotation `m`
       inside it; the annotation is taken OUT of it (this is the ordinary shape
       when a source's list is written by hand);
     * `foreign n`   — an element from which NO annotation can be obtained: it is
       no annotation itself and carries none. `n` is its own identity token, the
       one a refusal names.

   `canonical` and `wrapped` both make an annotation available; only `foreign`
   does not. -/
inductive Item where
  | canonical (m : Mark)
  | wrapped (m : Mark)
  | foreign (n : Int)
  deriving DecidableEq

/- What a collection yields. Either it produced a canonical annotation sequence,
   or it REFUSED, naming the offending element: an element it was asked to
   canonicalize makes no annotation available, and then the collection produces
   no sequence at all — the refusal is the observable result, not a
   silently-skipped element, not a substituted annotation, and not an empty
   sequence. -/
inductive Outcome where
  | refused (offending : Int)
  | collected (ms : List Mark)
  deriving DecidableEq

/- The annotation a raw element makes available, if any. -/
def markOf : Item → Option Mark
  | Item.canonical m => some m
  | Item.wrapped m   => some m
  | Item.foreign _   => none

/- The identity token a raw element is known by — for an element that makes no
   annotation available, this is what a refusal names. -/
def nameOf : Item → Int
  | Item.canonical m => m
  | Item.wrapped m   => m
  | Item.foreign n   => n

@[grind] lemma markOf_canonical (m : Mark) : markOf (Item.canonical m) = some m := rfl
@[grind] lemma markOf_wrapped (m : Mark) : markOf (Item.wrapped m) = some m := rfl
@[grind] lemma markOf_foreign (n : Int) : markOf (Item.foreign n) = none := rfl

/- The in-order concatenation of a sequence of per-source raw element lists: the
   elements contributed by the first source, then those of each subsequent
   source, and nothing else. A source that contributes none appears as an empty
   element and is simply skipped without ending the assembly. Front-recursive
   (one unfold per source) so a backward impl loop that prepends one source's
   elements each step can discharge the value equality (the fold pattern,
   plan §5.4). -/
def flattenSeq : List (List Item) → List Item
  | []      => []
  | g :: gs => g ++ flattenSeq gs

@[grind] lemma flattenSeq_nil : flattenSeq [] = [] := rfl
@[grind] lemma flattenSeq_cons (g : List Item) (gs : List (List Item)) :
    flattenSeq (g :: gs) = g ++ flattenSeq gs := rfl

/- A single-source assembly is just that source's own elements. -/
@[grind] lemma flattenSeq_singleton (g : List Item) : flattenSeq [g] = g := by
  simp [flattenSeq]

/- Put one annotation in front of a collection's outcome. A refusal stays that
   same refusal: once the collection has been refused, no annotation is carried
   out of it. -/
def consMark (m : Mark) (o : Outcome) : Outcome :=
  match o with
  | Outcome.collected ms => Outcome.collected (m :: ms)
  | Outcome.refused n    => Outcome.refused n

/- Canonicalize an assembled element sequence, IN ORDER: every element must make
   an annotation available, and that annotation — not the element it came out of
   — is what the resulting sequence carries, at the same position. If an element
   makes none available, the whole collection is REFUSED and yields no sequence,
   naming the FIRST such element: the obligation is discharged element by element
   from the front, never assumed away and never postponed. Front-recursive, one
   element per unfold. -/
def canonicalize : List Item → Outcome
  | [] => Outcome.collected []
  | it :: rest =>
      match markOf it with
      | none   => Outcome.refused (nameOf it)
      | some m => consMark m (canonicalize rest)

@[grind] lemma canonicalize_nil : canonicalize [] = Outcome.collected [] := rfl

/- Extend a collection's outcome with one further annotation at the end. A
   refusal stays that same refusal — nothing is recorded on top of a collection
   that was refused. -/
def withMark (o : Outcome) (mark : Mark) : Outcome :=
  match o with
  | Outcome.collected ms => Outcome.collected (ms ++ [mark])
  | Outcome.refused n    => Outcome.refused n

@[grind] lemma withMark_collected (ms : List Mark) (mark : Mark) :
    withMark (Outcome.collected ms) mark = Outcome.collected (ms ++ [mark]) := rfl
@[grind] lemma withMark_refused (n : Int) (mark : Mark) :
    withMark (Outcome.refused n) mark = Outcome.refused n := rfl
-- pure-end

-- pre-conditions-start
-- (preconditions are inline on each `method`; none are module-level)
-- pre-conditions-end

-- post-conditions-start
-- (postconditions are the inline `ensures` clauses on each `method` below)
-- post-conditions-end

/- Collect the annotations of a class. `lineage` is the ordered sequence of the
   per-source raw element lists that may contribute, the class's own list first.
   When `wholeLineage` is true every source in the lineage contributes (so
   annotations applied to any ancestor are kept, not just those of the nearest
   one); when false only the class's own list (the first element) does. The
   contributing sources are assembled in order, and the assembled elements are
   then canonicalized: each yields the annotation it makes available, and the
   collection is REFUSED as a whole — naming the first offender — if some
   assembled element makes none. Elements of sources that do NOT contribute are
   never canonicalized, so they cannot refuse a collection they take no part in.
   `lineage` is read-only. -/
method collectMarks (lineage : List (List Item)) (wholeLineage : Bool)
    return (out : Outcome)
  ensures out =
    canonicalize (flattenSeq (if wholeLineage then lineage else [lineage.headD []]))
  do
    -- impl-start
    -- Select which sources contribute: the whole lineage, or only the class's
    -- own list; then concatenate the selected sources in order. The fold runs
    -- from the back, prepending each source's elements before those already
    -- gathered, yielding their in-order concatenation. The assembled elements
    -- are canonicalized before they leave.
    let selected : List (List Item) :=
      if wholeLineage then lineage else [lineage.headD []]
    let mut gathered : List Item := []
    let mut i := selected.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ selected.length
      invariant gathered = flattenSeq (selected.drop i)
      done_with i = 0
      decreasing i
    do
      let g := selected[i - 1]!
      gathered := g ++ gathered
      i := i - 1
    return canonicalize gathered
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `flattenSeq` peels one source's elements off the
   front of its output. This is the single goal `loom_solve` leaves. -/
lemma flattenSeq_drop_step (xs : List (List Item)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ xs.length) :
    flattenSeq (xs.drop (i - 1)) = xs[i - 1]! ++ flattenSeq (xs.drop i) := by
  have hlt : i - 1 < xs.length := by omega
  have hcons : xs.drop (i - 1) = xs[i - 1]! :: xs.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, flattenSeq_cons]

prove_correct collectMarks by
  loom_solve
  rw [flattenSeq_drop_step
        (if wholeLineage = true then lineage else [lineage.headD []]) i
        (by omega) (by omega)]
  simp_all

/- Record a freshly-applied annotation on a class: the class's new own list is
   the canonicalization of its existing own list, extended with the new
   annotation at the end. The existing own elements are obtained by collecting
   WITHOUT the lineage (only the class's own), so applying an annotation never
   absorbs ancestors' annotations into the class's own list; and if that own list
   holds an element making no annotation available, the whole recording is
   REFUSED — the new annotation is not recorded on top of a refusal, and the
   offending element is not dropped. `lineage` and `mark` are read-only. -/
method attachMark (lineage : List (List Item)) (mark : Mark)
    return (out : Outcome)
  ensures out = withMark (canonicalize (lineage.headD [])) mark
  do
    -- impl-start
    let own ← collectMarks lineage false
    return withMark own mark
    -- impl-end

prove_correct attachMark by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL:** 23 same-spec attacks (all same_spec=True via swebench_unified.markers.same_spec) + positive control, all; verified with `bash scripts/lean_verify.sh <f>.lean` run 4-at-a-time as concurrent background jobs. Repo worktree at base_commit: wt (restored clean; `git status --porcelain` empty).

WHY SOUND — the structural argument. The `ensures` clauses are TOTAL FUNCTIONAL EQUALITIES (`out = canonicalize (flattenSeq (if wholeLineage then lineage else [lineage.headD []]))` and `out = withMark (canonicalize (lineage.headD [])) mark`), with NO precondition and NO existential/relational slack. So any impl that verifies is extensionally equal to that function on EVERY input; there is no room for a divergent-but-verifying impl. Soundness therefore reduces to two checks, which I ran directly rather than assuming:

(1) Does the spec FUNCTION equal GOLD? model_vs_gold.py transliterates the frozen pure region (markOf/nameOf/flattenSeq/canonicalize) and diffs it against the GOLD-PATCHED get_unpacked_marks over 1500 randomly generated real class hierarchies (varying MRO depth/branching incl. diamonds, per-class own lists mixing all three element shapes, present/absent pytestmark) plus 400 non-class objects (list / non-list / absent attr), both flag values, comparing SUCCESS VALUES and REFUSAL IDENTITY => 0 failures. attach_vs_gold.py does the same for attachMark vs GOLD store_mark over 1200 cases, additionally asserting a refusal leaves obj.pytestmark UNMUTATED => 0 failures. edge_vs_gold.py covers the edges the bulk fuzz under-samples (class with a bare-Mark / str non-list attr; a wrapper whose.mark is a NON-Mark, confirming the refusal names the UNWRAPPED value as mapping.md §2 claims; tuple attr; empty-everything deep MRO; first-offender ACROSS source boundaries; and a poisoned ANCESTOR with consider_mro=False, confirming a non-contributing source cannot refuse) => 0 failures.

(2) Is the obligation non-vacuous? Controls atk_vacuity_const (`return Outcome.collected []`, ignores inputs) and atk_falseinv (`invariant False`) are both REJECTED (atk_falseinv leaves the literal goal `⊢ False`), and atk_selfcall (assume-own-contract via self-call) fails termination. So prove_correct is a real obligation.

A-LEG AUDIT (the assigned focus). meta.json axioms = [] and Solution.lean declares no `axiom`, so there are no A-consumed legs; the single A-reference leg is A4 (canonicalize/markOf/nameOf <-> normalize_mark_list). I independently validated it with a4_check.py, which loads the REAL `_pytest`.mark.structures.normalize_mark_list from the base_commit worktree (host `py` shim stubbed to only supply py.path.local, so the genuine callee module loads unmodified) and diffs it against the Lean model on: all-canonical lists, all-wrapped lists, an offender-POSITION sweep, ALL two-offender pairs (must name the FIRST), and 4000 randomized mixed-shape fuzz cases — asserting both success values and the exact TypeError message identity => 0 failures. I also confirmed the A4 premise mechanically: normalize_mark_list is BYTE-IDENTICAL between base and post (`git show HEAD:...` vs patched), base returned the lazy generator while post wraps it in `list(...)`, which is what makes the refusal observable. So the A-reference correspondence to the real callee holds.

refinement.md leg audit: every leg is tagged R (A1, A5, B3, B4), I (A2, A3, B1, B2) or A-reference (A4); NO kind-3 (inexpressible-changed-op) legs and no A-consumed legs — §C's claim checks out. The two genuinely-changed operations (the MRO-aware flatten and consider_mro=False storage) are modeled deeply as verified methods, not axiomatized, satisfying directive 7.

RESOLVE RUNS (the mandatory step — executed, not speculated). Exactly 2 of 23 attacks verify, and BOTH are behaviorally correct impls rather than wrong ones, so I materialized and RAN both faithful patches through the official harness (swebench_unified.harness.run_resolve, timeout=1800, retries=1):
- atk_echo.lean (exit 0; ungrounded-ORACLE-ECHO: impl literally recomputes the postcondition RHS) -> patch_echo.diff -> RESOLVED=True, note='resolved', FAIL_TO_PASS 1/1, PASS_TO_PASS 79/79, 0 failures. Note test_mark_with_wrong_marker is among the PASSING P2P tests — the prior audit's break is gone.
- atk_forward.lean (exit 0; structurally DIFFERENT verifying impl: forward `while i < selected.length` assembly with invariant `gathered = flattenSeq (selected.take i)`, helper lemma proved inline so spec regions stay byte-identical) -> patch_forward.diff -> RESOLVED=True, FAIL_TO_PASS 1/1, PASS_TO_PASS 79/79, 0 failures.
So no verifying impl's faithful patch fails to resolve => NOT BROKEN.

**PREPATCH REPRODUCED:** yes, both twins. I re-encoded the prepatch breadth bug myself as atk_breadth.lean (only the nearest own list contributes) => exit 1, real rewrite/goal failure; and re-ran the shipped Solution_prepatch_1.lean (exit 1) and Solution_prepatch_2.lean (exit 1, unsolved goals). atk_attach_mro.lean independently re-encodes the prepatch_2 bug (collectMarks lineage true inside attachMark) => exit 1.

REJECTED ATTACKS (all exit 1 with GENUINE unsolved goals, not tactic/syntax artifacts — I audited every log and REPAIRED my own elaboration bugs in atk_dedupe/atk_boundary/atk_partial (stray grind), atk_diverge (Option-Nat numeral), atk_persource (missing Inhabited Item), atk_emptyrefuse and atk_selectlate (bad tactic/match shape) before counting them): breadth, skipgate, order (reverse assembly), flagignored (selection branch removed), selectlate (gate applied before selection so a non-contributing source refuses), lastoffender, fixedname, nounwrap, partial (only the first element's refusal obligation discharged), dedupe (diamond duplicates collapsed), boundary (first element dropped), emptyrefuse (empty lineage refused), persource (restructured backward canonicalize fold — rejected only because loom left a goal my inline script did not close; not a spec weakness), selfcall, diverge, falseinv, vacuity_const, attach_mro, attach_prepend (new mark at the front), attach_swallow (refusal swallowed), attach_filter (offenders silently filtered from the own list).

CAVEAT / non-blocking: atk_persource is a semantically-EQUIVALENT impl that I failed to prove within the heartbeat budget, so its exit-1 reflects my tactic script rather than a spec rejection; it is submitted for completeness but is not evidence of tightness. This does not affect the verdict, which rests on the functional-equality argument plus the two executed resolve runs.

**VERDICT:** SOUND. 23 attacks run (>=5 required), 2 verified, both verifying impls' faithful patches EXECUTED through run_resolve and both RESOLVED; positive control verifies (exit 0); both prepatch twins reproduce as failures; the A4 deep model is validated against the real unchanged callee including refusal identity; no kind-3 legs. verify => correct holds for this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** FAITHFULNESS-BREAK ATTACK: no divergence found between the modeled functions and the real patched repo. Reference used correctly = base_commit 3c1534944cbd34e8a41bc9e76818018fadefc9a1 worktree with patch.diff APPLIED (fresh worktree *, `git apply` clean, 30+/7- as expected); base commit used only to confirm the unchanged callee.

**SPEC REGION INTEGRITY:** swebench_unified.markers.same_spec(Solution.lean, rival, velvet) == True for BOTH Solution_prepatch_1.lean and Solution_prepatch_2.lean. spec_view sha256 = 833899fe1f72767bddd93f16a6340202087f9ee1f391e16079ee91e65e376f7f, byte-identical to meta.json gates.G-HYGIENE.data.region_hashes.spec_view. parse_regions ok, regions = axioms/pure/pre-conditions/post-conditions/impl. meta.json axioms == [] (no consumed axioms to attack).

**LEAN:** scripts/lean_verify.sh on Solution.lean => EXIT 0 (both collectMarks and attachMark discharge; no sorry/admit path relied on).

INDEPENDENT DIFFERENTIAL (my own harness, NOT the bundle's conformance_check.py): transliterated ONLY the two ensures clauses -- out = canonicalize (flattenSeq (if wholeLineage then lineage else [lineage.headD []])) and out = withMark (canonicalize (lineage.headD [])) mark -- and diffed against the REAL patched get_unpacked_marks / store_mark. Compared on BOTH observables: success value AND refusal identity (that TypeError is raised and which object its message reprs).
  * 12,274 inputs: diamond hierarchies C(A,B) x 14 per-class own-list shapes^3 x consider_mro in {True,False}, plus store_mark on each; randomized linear MROs to depth 5 (4,000 iters); non-class module objects. => 0 disagreements.
  * 208 inputs: non-class INSTANCES (where getattr walks to the class, a shape the bundle's own checker does not drive) and plain functions, cls-own x inst-own x flag, incl. store_mark. => 0 disagreements.
  * exotic element/attribute shapes: list subclass, dict, generator, str, bytes, int, False, None, nested list, bare Mark as non-list own, tuple, set, class-object-as-element, type-as-own; each on the owning class AND an inheriting subclass, both flags. => 0 disagreements.

HARNESS SENSITIVITY (a clean run is worthless unless the harness can fail): mutation-tested the spec side, all four mutants caught with large counterexample counts -- MRO order reversed => 2,029; breadth collapsed to own-list-only (the prepatch_1 defect) => 2,137; canonicalizing gate removed / offenders silently skipped => 6,387; last-offender instead of first-offender => 3,105. So order, breadth, the refusal gate, and the first-offender rule are all genuinely pinned and observable by this harness.

**CALLEE/AXIOM CLAIM VERIFIED:** normalize_mark_list is byte-identical between base and patched structures.py, confirming mapping.md §3.1's A-reference premise (it is an unchanged callee, deeply modeled rather than axiomatized). canonicalize/markOf/nameOf reproduce it exactly, refusal identity included.

**TARGET TEST:** reconstructed test_mark_mro on the patched repo -- get_unpacked_marks(C) == [xfail('c').mark, xfail('a').mark, xfail('b').mark] passes, and the spec's ensures clause predicts exactly that same triple in MRO order.

NOT-A-DEFECT considered and rejected: an element whose `.mark` is a raising property (non-AttributeError, e.g. ValueError) escapes as ValueError from the real callee and is not representable in the 3-shape Item domain. This is unmodeled-exotic-input (no precondition claims to cover it, and it is unreachable from any pytest usage), i.e. a domain-width observation, NOT the spec being too strong or disagreeing with the repo on a modeled input. It yields no diverging input, so it does not support UNFAITHFUL.

**Also checked the classic drift trap:** I did NOT compare against the base version, so the MRO-breadth delta and consider_mro=False storage delta are correctly attributed to the patch rather than reported as divergence. Item/Outcome is a documented WIDENING (previously-modeled inputs = the all-canonical sub-domain), adding no precondition, so nothing was narrowed.

**FAITHFULNESS-BREAK ATTACK:** no divergence found between the modeled functions and the real patched repo. Reference used correctly = base_commit 3c1534944cbd34e8a41bc9e76818018fadefc9a1 worktree with patch.diff APPLIED (fresh worktree *, `git apply` clean, 30+/7- as expected); base commit used only to confirm the unchanged callee.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** SCOPE. No relaxation in this bundle: no RELAXED_LEAKAGE.md anywhere under benchmark-verified/pytest-dev__pytest-10356/ (find -iname '*RELAX*' empty) and no relaxed_leakage key in meta.json (recursive key walk for /relax|leak/ returned only gates.G-LEAK, which is mode='strict', status='pass'). So this is judged as an ordinary strict review, not an inherited disposition. I also ran leakage.reviewer_directed() over every.md/.lean/.json/.py in the bundle: zero hits -- no file in the bundle addresses me, prescribes a verdict, or states a recording convention.

### WHAT I RAN (my own measurements, not meta.json's assertions).
1. Spec region identity: markers.same_spec(Solution.lean, Solution_prepatch_1.lean) = True and same_spec(Solution.lean, Solution_prepatch_2.lean) = True; all three spec_signature sha256 = 4e56a846b79bc2dd... byte-identical. The prepatch rivals differ only inside impl regions.
2. Re-ran the mechanical screen myself: leakage.screen(Solution.lean, velvet, instance.patch, instance.problem_statement) -> passed=True, hard_failures=[], warnings=[]. Confirms meta.json G-LEAK rather than trusting it.
3. Independent narration-strip + verify (the load-bearing test). I stripped EVERY comment (line + nested block) from all three files with leakage.`_lean_strip_comments_collect`, leaving only code/contracts, and ran scripts/lean_verify.sh on each: gold nc_Solution.lean EXIT=0 (verifies with zero prose); nc_Solution_prepatch_1.lean EXIT=1, one real unsolved goal ('canonicalize i_1 = canonicalize (flattenSeq (if wholeLineage = true then lineage else [lineage.headD []]))'); nc_Solution_prepatch_2.lean EXIT=1, one real unsolved goal ('withMark x mark = withMark (canonicalize (lineage.headD [])) mark' with hypothesis 'x = canonicalize (flattenSeq (if True then lineage else...))'). So all discriminating power lives in the two formal `ensures` clauses, NOT in the prose -- the comments are removable narration and the spec still rejects both rivals. That is the opposite of a spec whose prose is load-bearing.

LEAK SURFACE SWEEP OF THE ACTUAL SPEC VIEW (markers.spec_view, velvet tables -- impl regions and both prove_correct bodies elided; that is exactly what eval/prompts.py `_spec_block` ships).
- Patched symbols get_unpacked_marks and store_mark: 0 occurrences in identifiers and 0 in comments (get_unpacked=0, store_mark=0).
- Patched path src/`_pytest`/mark/structures.py and dotted module: absent. Repo vocabulary all zero: mro=0, `__mro__`=0, pytestmark=0, consider/consider_mro=0, normalize_mark_list=0, `__dict__`=0, getattr=0, isinstance=0, TypeError=0, MarkDecorator=0, metaclass=0, pytest=0, python=0.
- Gold-line reproduction below the gate's 8-char floor: I brute-forced the LONGEST normalized substring of any added/removed gold line present in the view. Answer: 10 chars, 'sappliedto', landing inside the English phrase 'as is the assembly it is applied to (`flattenSeq`)' -- a coincidental prose collision with the docstring 'marks applied to', carrying no code. Nothing longer exists; no gold code fragment survives.
- Spec-view identifiers are all domain-neutral inventions (Item/canonical/wrapped/foreign, Mark, Outcome/collected/refused, markOf/nameOf, flattenSeq, canonicalize, consMark, withMark, collectMarks, attachMark, lineage, wholeLineage). None echoes a patched repo symbol.

**FACET RE-CONFIRMED AS PUBLIC.** The one discriminator the spec view does state in prose -- 'when `wholeLineage` is true every source in the lineage contributes (so annotations applied to any ancestor are kept, not just those of the nearest one)' -- is fully public in the problem_statement, which I re-read end to end: its title is 'Consider MRO when obtaining marks for classes'; it says inheriting from two marked baseclasses 'will lose the markers of one of those classes'; 'foo and bar markers override each other'; 'markers are resolved using MRO (so foo wins)'; "I'd expect `foo` and `bar` to be markers for `test_dings`"; and the repro literally walks `self.__mro__` with itertools.chain.from_iterable.

Regex-confirmed present in problem_statement: `__mro__`, MRO, `_pytestmark`, setter, 'lose the markers', 'override each other', 'foo wins', chain.from_iterable. The spec view states this abstractly (lineage/ancestor/nearest) and never in the patch's vocabulary, so it says strictly less than the public issue. attachMark's clause (the class's own list plus the new annotation, never absorbing ancestors') is the direct behavioral consequence of the publicly requested merge -- state a merge on read and you must not write the merged list back -- and it names neither store_mark nor consider_mro. The canonicalize/refusal facet models normalize_mark_list, which is TEXTUALLY UNCHANGED across the patch (base:366-380 == post:389-403), so it is pre-existing behavior and cannot localize the edit.

**CORE GATES THIS VERDICT LEANS ON:** G-LEAK (re-measured, pass), G-DIFF (re-measured independently on comment-stripped rivals, both fail with real goals), G-GOLD/G-VERIFY (gold verifies, EXIT=0 measured). No gate I depend on is unsound.

TWO NON-LEAKING BLEMISHES, recorded for the file, deliberately NOT my verdict: (a) the spec view leaks bundle-PROCESS references, not the edit -- line 16 'validated against the real sub-computations out of band (mapping.md §3, axiom_check.py / G-AX)' and line 78 '(the fold pattern, plan §5.4)'. These expose that an audit harness exists and should be de-narrated for tidiness, but they name no patched file, symbol, or diff line and localize no edit, so they are outside this gate's rules. (b) meta.json modeled_functions.carrier_type does contain repo vocabulary (`__mro__`, consider_mro, post:380-385, post:411) and repo_symbol names both patched functions -- but eval/prompts.py `_spec_block` renders ONLY 'model_symbol (↔ repo_symbol)' pairs, and repo-symbol localization is the deliberate, documented mode-1/2 aid, not spec-view content; carrier_type never reaches the agent. Neither is leakage.

UNRELATED PRE-EXISTING FAILS, not converted: meta.json shows G-EQ and G-PANEL-1 as fail with detail 'INCONCLUSIVE -- patch unusable: the auditor's patch does not apply, so the oracle graded nothing'. That is a harness/environment inconclusive, not a measured spec weakness, and it is not a gate this leakage verdict rests on; I did not re-label it as a spec defect.

**SCOPE.** No relaxation in this bundle: no RELAXED_LEAKAGE.md anywhere under benchmark-verified/pytest-dev__pytest-10356/ (find -iname '*RELAX*' empty) and no relaxed_leakage key in meta.json (recursive key walk for /relax|leak/ returned only gates.G-LEAK, which is mode='strict', status='pass'). So this is judged as an ordinary strict review, not an inherited disposition. I also ran leakage.reviewer_directed() over every.md/.lean/.json/.py in the bundle: zero hits -- no file in the bundle addresses me, prescribes a verdict, or states a recording convention.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
