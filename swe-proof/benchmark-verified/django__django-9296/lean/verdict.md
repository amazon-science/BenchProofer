# P2 adversarial audit — django__django-9296

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The postcondition problem_spec_paginatorPages pins the result EXACTLY (result = (pageNumbers objectList.length perPage orphans allowEmpty).map (fun n => pageSlice objectList perPage orphans n)) under the theorem hypothesis 1 ≤ perPage. Every wrong impl that diverges anywhere on the perPage≥1 domain fails to close (atk_1..5 all EXIT=1). The only impls that verify either equal gold everywhere (atk_6 echo) or diverge ONLY at perPage=0 (atk_7), which is outside both the theorem hypothesis AND the Python domain (per_page=0 raises ZeroDivisionError in num_pages; the F2P/P2P tests use per_page≥1). Both verifying impls' faithful patches RESOLVE under the official harness.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -67,42 +67,21 @@
       (fun n => pageSlice objectList perPage orphans n)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_paginatorPages {α : Type}
     (objectList : List α) (perPage orphans : Nat) (allowEmpty : Bool) :
     List (List α) := Id.run do
   let mut pages : List (List α) := []
-  for n in pageNumbers objectList.length perPage orphans allowEmpty do
-    pages := pages ++ [pageSlice objectList perPage orphans n]
   return pages
 -- impl-end
 
 -- proof-start
-/-- The `for` loop, generalized over the accumulator, appends each page's slice
-in order: walking `xs` from `init` yields `init ++ xs.map pageSlice`. -/
-theorem paginatorPages_forIn {α : Type} (objectList : List α) (perPage orphans : Nat)
-    (xs : List Nat) (init : List (List α)) :
-    Id.run (forIn xs init (fun n r =>
-      (do pure PUnit.unit;
-          pure (ForInStep.yield (r ++ [pageSlice objectList perPage orphans n]))))) =
-      init ++ xs.map (fun n => pageSlice objectList perPage orphans n) := by
-  induction xs generalizing init with
-  | nil => simp [Id.run, pure, List.forIn_nil]
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [ih]
-    simp
-
 theorem correct_paginatorPages {α : Type}
     (objectList : List α) (perPage orphans : Nat) (allowEmpty : Bool)
     (hperPage : 1 ≤ perPage) :
     problem_spec_paginatorPages objectList perPage orphans allowEmpty
       (implementation_paginatorPages objectList perPage orphans allowEmpty) := by
   unfold problem_spec_paginatorPages implementation_paginatorPages
-  have h := paginatorPages_forIn objectList perPage orphans
-    (pageNumbers objectList.length perPage orphans allowEmpty) []
-  simp only [Id.run, bind, pure] at h ⊢
-  rw [h]
-  simp
+  simp [Id.run]
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -67,42 +67,21 @@
       (fun n => pageSlice objectList perPage orphans n)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_paginatorPages {α : Type}
     (objectList : List α) (perPage orphans : Nat) (allowEmpty : Bool) :
-    List (List α) := Id.run do
-  let mut pages : List (List α) := []
-  for n in pageNumbers objectList.length perPage orphans allowEmpty do
-    pages := pages ++ [pageSlice objectList perPage orphans n]
-  return pages
+    List (List α) :=
+  ((pageNumbers objectList.length perPage orphans allowEmpty).map
+    (fun n => pageSlice objectList perPage orphans n)).reverse
 -- impl-end
 
 -- proof-start
-/-- The `for` loop, generalized over the accumulator, appends each page's slice
-in order: walking `xs` from `init` yields `init ++ xs.map pageSlice`. -/
-theorem paginatorPages_forIn {α : Type} (objectList : List α) (perPage orphans : Nat)
-    (xs : List Nat) (init : List (List α)) :
-    Id.run (forIn xs init (fun n r =>
-      (do pure PUnit.unit;
-          pure (ForInStep.yield (r ++ [pageSlice objectList perPage orphans n]))))) =
-      init ++ xs.map (fun n => pageSlice objectList perPage orphans n) := by
-  induction xs generalizing init with
-  | nil => simp [Id.run, pure, List.forIn_nil]
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [ih]
-    simp
-
 theorem correct_paginatorPages {α : Type}
     (objectList : List α) (perPage orphans : Nat) (allowEmpty : Bool)
     (hperPage : 1 ≤ perPage) :
     problem_spec_paginatorPages objectList perPage orphans allowEmpty
       (implementation_paginatorPages objectList perPage orphans allowEmpty) := by
   unfold problem_spec_paginatorPages implementation_paginatorPages
-  have h := paginatorPages_forIn objectList perPage orphans
-    (pageNumbers objectList.length perPage orphans allowEmpty) []
-  simp only [Id.run, bind, pure] at h ⊢
-  rw [h]
   simp
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -67,42 +67,21 @@
       (fun n => pageSlice objectList perPage orphans n)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_paginatorPages {α : Type}
     (objectList : List α) (perPage orphans : Nat) (allowEmpty : Bool) :
-    List (List α) := Id.run do
-  let mut pages : List (List α) := []
-  for n in pageNumbers objectList.length perPage orphans allowEmpty do
-    pages := pages ++ [pageSlice objectList perPage orphans n]
-  return pages
+    List (List α) :=
+  (List.range' 0 (pageCount objectList.length perPage orphans allowEmpty)).map
+    (fun n => pageSlice objectList perPage orphans n)
 -- impl-end
 
 -- proof-start
-/-- The `for` loop, generalized over the accumulator, appends each page's slice
-in order: walking `xs` from `init` yields `init ++ xs.map pageSlice`. -/
-theorem paginatorPages_forIn {α : Type} (objectList : List α) (perPage orphans : Nat)
-    (xs : List Nat) (init : List (List α)) :
-    Id.run (forIn xs init (fun n r =>
-      (do pure PUnit.unit;
-          pure (ForInStep.yield (r ++ [pageSlice objectList perPage orphans n]))))) =
-      init ++ xs.map (fun n => pageSlice objectList perPage orphans n) := by
-  induction xs generalizing init with
-  | nil => simp [Id.run, pure, List.forIn_nil]
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [ih]
-    simp
-
 theorem correct_paginatorPages {α : Type}
     (objectList : List α) (perPage orphans : Nat) (allowEmpty : Bool)
     (hperPage : 1 ≤ perPage) :
     problem_spec_paginatorPages objectList perPage orphans allowEmpty
       (implementation_paginatorPages objectList perPage orphans allowEmpty) := by
-  unfold problem_spec_paginatorPages implementation_paginatorPages
-  have h := paginatorPages_forIn objectList perPage orphans
-    (pageNumbers objectList.length perPage orphans allowEmpty) []
-  simp only [Id.run, bind, pure] at h ⊢
-  rw [h]
+  unfold problem_spec_paginatorPages implementation_paginatorPages pageNumbers
   simp
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -67,42 +67,21 @@
       (fun n => pageSlice objectList perPage orphans n)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_paginatorPages {α : Type}
     (objectList : List α) (perPage orphans : Nat) (allowEmpty : Bool) :
-    List (List α) := Id.run do
-  let mut pages : List (List α) := []
-  for n in pageNumbers objectList.length perPage orphans allowEmpty do
-    pages := pages ++ [pageSlice objectList perPage orphans n]
-  return pages
+    List (List α) :=
+  (pageNumbers objectList.length perPage orphans allowEmpty).map
+    (fun n => (objectList.drop ((n - 1) * perPage)).take perPage)
 -- impl-end
 
 -- proof-start
-/-- The `for` loop, generalized over the accumulator, appends each page's slice
-in order: walking `xs` from `init` yields `init ++ xs.map pageSlice`. -/
-theorem paginatorPages_forIn {α : Type} (objectList : List α) (perPage orphans : Nat)
-    (xs : List Nat) (init : List (List α)) :
-    Id.run (forIn xs init (fun n r =>
-      (do pure PUnit.unit;
-          pure (ForInStep.yield (r ++ [pageSlice objectList perPage orphans n]))))) =
-      init ++ xs.map (fun n => pageSlice objectList perPage orphans n) := by
-  induction xs generalizing init with
-  | nil => simp [Id.run, pure, List.forIn_nil]
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [ih]
-    simp
-
 theorem correct_paginatorPages {α : Type}
     (objectList : List α) (perPage orphans : Nat) (allowEmpty : Bool)
     (hperPage : 1 ≤ perPage) :
     problem_spec_paginatorPages objectList perPage orphans allowEmpty
       (implementation_paginatorPages objectList perPage orphans allowEmpty) := by
-  unfold problem_spec_paginatorPages implementation_paginatorPages
-  have h := paginatorPages_forIn objectList perPage orphans
-    (pageNumbers objectList.length perPage orphans allowEmpty) []
-  simp only [Id.run, bind, pure] at h ⊢
-  rw [h]
+  unfold problem_spec_paginatorPages implementation_paginatorPages pageSlice
   simp
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -67,42 +67,21 @@
       (fun n => pageSlice objectList perPage orphans n)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_paginatorPages {α : Type}
     (objectList : List α) (perPage orphans : Nat) (allowEmpty : Bool) :
-    List (List α) := Id.run do
-  let mut pages : List (List α) := []
-  for n in pageNumbers objectList.length perPage orphans allowEmpty do
-    pages := pages ++ [pageSlice objectList perPage orphans n]
-  return pages
+    List (List α) :=
+  ((pageNumbers objectList.length perPage orphans allowEmpty).map
+    (fun n => pageSlice objectList perPage orphans n)).dropLast
 -- impl-end
 
 -- proof-start
-/-- The `for` loop, generalized over the accumulator, appends each page's slice
-in order: walking `xs` from `init` yields `init ++ xs.map pageSlice`. -/
-theorem paginatorPages_forIn {α : Type} (objectList : List α) (perPage orphans : Nat)
-    (xs : List Nat) (init : List (List α)) :
-    Id.run (forIn xs init (fun n r =>
-      (do pure PUnit.unit;
-          pure (ForInStep.yield (r ++ [pageSlice objectList perPage orphans n]))))) =
-      init ++ xs.map (fun n => pageSlice objectList perPage orphans n) := by
-  induction xs generalizing init with
-  | nil => simp [Id.run, pure, List.forIn_nil]
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [ih]
-    simp
-
 theorem correct_paginatorPages {α : Type}
     (objectList : List α) (perPage orphans : Nat) (allowEmpty : Bool)
     (hperPage : 1 ≤ perPage) :
     problem_spec_paginatorPages objectList perPage orphans allowEmpty
       (implementation_paginatorPages objectList perPage orphans allowEmpty) := by
   unfold problem_spec_paginatorPages implementation_paginatorPages
-  have h := paginatorPages_forIn objectList perPage orphans
-    (pageNumbers objectList.length perPage orphans allowEmpty) []
-  simp only [Id.run, bind, pure] at h ⊢
-  rw [h]
   simp
 -- proof-end
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -67,42 +67,21 @@
       (fun n => pageSlice objectList perPage orphans n)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_paginatorPages {α : Type}
     (objectList : List α) (perPage orphans : Nat) (allowEmpty : Bool) :
-    List (List α) := Id.run do
-  let mut pages : List (List α) := []
-  for n in pageNumbers objectList.length perPage orphans allowEmpty do
-    pages := pages ++ [pageSlice objectList perPage orphans n]
-  return pages
+    List (List α) :=
+  (pageNumbers objectList.length perPage orphans allowEmpty).map
+    (fun n => pageSlice objectList perPage orphans n)
 -- impl-end
 
 -- proof-start
-/-- The `for` loop, generalized over the accumulator, appends each page's slice
-in order: walking `xs` from `init` yields `init ++ xs.map pageSlice`. -/
-theorem paginatorPages_forIn {α : Type} (objectList : List α) (perPage orphans : Nat)
-    (xs : List Nat) (init : List (List α)) :
-    Id.run (forIn xs init (fun n r =>
-      (do pure PUnit.unit;
-          pure (ForInStep.yield (r ++ [pageSlice objectList perPage orphans n]))))) =
-      init ++ xs.map (fun n => pageSlice objectList perPage orphans n) := by
-  induction xs generalizing init with
-  | nil => simp [Id.run, pure, List.forIn_nil]
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [ih]
-    simp
-
 theorem correct_paginatorPages {α : Type}
     (objectList : List α) (perPage orphans : Nat) (allowEmpty : Bool)
     (hperPage : 1 ≤ perPage) :
     problem_spec_paginatorPages objectList perPage orphans allowEmpty
       (implementation_paginatorPages objectList perPage orphans allowEmpty) := by
   unfold problem_spec_paginatorPages implementation_paginatorPages
-  have h := paginatorPages_forIn objectList perPage orphans
-    (pageNumbers objectList.length perPage orphans allowEmpty) []
-  simp only [Id.run, bind, pure] at h ⊢
-  rw [h]
-  simp
+  rfl
 -- proof-end
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -67,42 +67,23 @@
       (fun n => pageSlice objectList perPage orphans n)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_paginatorPages {α : Type}
     (objectList : List α) (perPage orphans : Nat) (allowEmpty : Bool) :
-    List (List α) := Id.run do
-  let mut pages : List (List α) := []
-  for n in pageNumbers objectList.length perPage orphans allowEmpty do
-    pages := pages ++ [pageSlice objectList perPage orphans n]
-  return pages
+    List (List α) :=
+  if perPage = 0 then []
+  else (pageNumbers objectList.length perPage orphans allowEmpty).map
+    (fun n => pageSlice objectList perPage orphans n)
 -- impl-end
 
 -- proof-start
-/-- The `for` loop, generalized over the accumulator, appends each page's slice
-in order: walking `xs` from `init` yields `init ++ xs.map pageSlice`. -/
-theorem paginatorPages_forIn {α : Type} (objectList : List α) (perPage orphans : Nat)
-    (xs : List Nat) (init : List (List α)) :
-    Id.run (forIn xs init (fun n r =>
-      (do pure PUnit.unit;
-          pure (ForInStep.yield (r ++ [pageSlice objectList perPage orphans n]))))) =
-      init ++ xs.map (fun n => pageSlice objectList perPage orphans n) := by
-  induction xs generalizing init with
-  | nil => simp [Id.run, pure, List.forIn_nil]
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [ih]
-    simp
-
 theorem correct_paginatorPages {α : Type}
     (objectList : List α) (perPage orphans : Nat) (allowEmpty : Bool)
     (hperPage : 1 ≤ perPage) :
     problem_spec_paginatorPages objectList perPage orphans allowEmpty
       (implementation_paginatorPages objectList perPage orphans allowEmpty) := by
   unfold problem_spec_paginatorPages implementation_paginatorPages
-  have h := paginatorPages_forIn objectList perPage orphans
-    (pageNumbers objectList.length perPage orphans allowEmpty) []
-  simp only [Id.run, bind, pure] at h ⊢
-  rw [h]
-  simp
+  have : perPage ≠ 0 := by omega
+  simp [this]
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Mathlib
-- imports-end

/-!
Walking every page of a paginated collection, in order.

A paginated collection is described by four data:

  * the underlying list of items being paged over;
  * how many items make up a full page;
  * how many trailing items may be absorbed into the final page instead of
    spilling onto a page of their own (the orphan allowance);
  * whether an empty collection still presents a single (empty) page.

From these the collection exposes a 1-based numbering of its pages and, for each
page number, the contiguous slice of items shown on that page. Walking the
collection produces, in increasing page-number order, the slice of items
belonging to each page — i.e. exactly the same sequence of page contents one
would obtain by asking for each page number in turn.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The page count, the
-- 1-based page numbering, and the per-page slice are each total, pure functions
-- of the four input data (a length/arithmetic computation and a list slice), so
-- they are modeled directly below rather than abstracted behind an `opaque`
-- contract. Hence no `opaque`/`axiom` callee declaration is required.
-- axioms-end

-- pure-start
/-- The number of pages for a collection of `count` items shown `perPage` at a
time, allowing `orphans` trailing items to be folded into the final page.
`allowEmpty = false` collapses an empty collection to zero pages; otherwise an
empty collection still has one (empty) page. For `perPage ≥ 1` this is the
ceiling of `max 1 (count - orphans)` divided by `perPage`. -/
def pageCount (count perPage orphans : Nat) (allowEmpty : Bool) : Nat :=
  if count = 0 ∧ allowEmpty = false then 0
  else (max 1 (count - orphans) + perPage - 1) / perPage

/-- The 1-based list of page numbers, `[1, 2, …, pageCount]`. -/
def pageNumbers (count perPage orphans : Nat) (allowEmpty : Bool) : List Nat :=
  List.range' 1 (pageCount count perPage orphans allowEmpty)

/-- The contiguous slice of items shown on page `n` (1-based). The window starts
at `(n-1)*perPage` and spans `perPage` items, except that a window whose end is
within `orphans` of the collection's end is extended to absorb those trailing
items. -/
def pageSlice {α : Type} (objectList : List α) (perPage orphans n : Nat) : List α :=
  let count := objectList.length
  let bottom := (n - 1) * perPage
  let top := bottom + perPage
  let top := if top + orphans ≥ count then count else top
  (objectList.drop bottom).take (top - bottom)
-- pure-end

-- post-conditions-start
/-- Walking the collection yields, in increasing page-number order, the slice of
items on each page: the result is exactly the list obtained by mapping the
per-page slice over every page number `[1, …, pageCount]`. This pins the result
fully — its length is the page count and its `k`-th entry is the slice for page
`k+1` — so no output component is left free. -/
def problem_spec_paginatorPages {α : Type}
    (objectList : List α) (perPage orphans : Nat) (allowEmpty : Bool)
    (result : List (List α)) : Prop :=
  result =
    (pageNumbers objectList.length perPage orphans allowEmpty).map
      (fun n => pageSlice objectList perPage orphans n)
-- post-conditions-end

-- impl-start
def implementation_paginatorPages {α : Type}
    (objectList : List α) (perPage orphans : Nat) (allowEmpty : Bool) :
    List (List α) := Id.run do
  let mut pages : List (List α) := []
  for n in pageNumbers objectList.length perPage orphans allowEmpty do
    pages := pages ++ [pageSlice objectList perPage orphans n]
  return pages
-- impl-end

-- proof-start
/-- The `for` loop, generalized over the accumulator, appends each page's slice
in order: walking `xs` from `init` yields `init ++ xs.map pageSlice`. -/
theorem paginatorPages_forIn {α : Type} (objectList : List α) (perPage orphans : Nat)
    (xs : List Nat) (init : List (List α)) :
    Id.run (forIn xs init (fun n r =>
      (do pure PUnit.unit;
          pure (ForInStep.yield (r ++ [pageSlice objectList perPage orphans n]))))) =
      init ++ xs.map (fun n => pageSlice objectList perPage orphans n) := by
  induction xs generalizing init with
  | nil => simp [Id.run, pure, List.forIn_nil]
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    rw [ih]
    simp

theorem correct_paginatorPages {α : Type}
    (objectList : List α) (perPage orphans : Nat) (allowEmpty : Bool)
    (hperPage : 1 ≤ perPage) :
    problem_spec_paginatorPages objectList perPage orphans allowEmpty
      (implementation_paginatorPages objectList perPage orphans allowEmpty) := by
  unfold problem_spec_paginatorPages implementation_paginatorPages
  have h := paginatorPages_forIn objectList perPage orphans
    (pageNumbers objectList.length perPage orphans allowEmpty) []
  simp only [Id.run, bind, pure] at h ⊢
  rw [h]
  simp
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL: same_spec=True confirmed for all 7 attacks (spec_view elides the entire impl+proof regions incl. theorem header; axioms/pure/pre/post byte-identical). Verified concurrently in batches of ≤4 via scripts/lean_verify.sh.

### ATTACKS (path, command, exit, axioms, resolve):
- atk_1 (prepatch bug: return []): `bash scripts/lean_verify.sh atk_1.lean` EXIT=1 (does NOT close) — prepatch reproduced.
- atk_2 (reversed page order via .reverse): EXIT=1 (does NOT close).
- atk_3 (off-by-one: List.range' 0 ... 0-based numbering, wrong slices): EXIT=1 (does NOT close).
- atk_4 (boundary: orphan-absorption dropped, inline (drop).take perPage): EXIT=1 (does NOT close).
- atk_5 (control-flow effect: .dropLast drops last page): EXIT=1 (does NOT close).
- atk_6 (ungrounded-oracle echo of spec RHS): `bash scripts/lean_verify.sh atk_6.lean` EXIT=0; `#print axioms correct_paginatorPages` => 'does not depend on any axioms' (clean, no sorryAx). Faithful patch = gold __iter__. RESOLVE: run_resolve('django__django-9296', atk_6_patch.diff) => completed=True resolved=True attempts=1 flaky=False note=resolved. Per G-PANEL-1/G-EQ policy a resolving echo is NOT a weakness.
- atk_7 (partial-domain: diverges from gold only at perPage=0, returns [] there; equals gold for perPage≥1): EXIT=0; `#print axioms` => [propext, Quot.sound] (⊆ STANDARD_AXIOMS, clean, no sorryAx). Faithful patch adds `if self.per_page == 0: return` guard to gold __iter__. RESOLVE: run_resolve => completed=True resolved=True attempts=1 flaky=False note=resolved. Diverges only OUTSIDE the theorem hypothesis (1 ≤ perPage) and outside the Python test domain (per_page=0 -> ZeroDivisionError), so does not break verify⇒correct.
- positive control pc.lean (gold for-loop impl): EXIT=0 (verifies).

REFINEMENT.MD AUDIT: 4 legs, all tagged R (deep model of unchanged callees page_range/num_pages/page). No kind-3 legs. axioms region is empty (axiom_check.py is a skip stub — no opaque/axiom declared); the three A-reference deep models (pageCount↔num_pages, pageNumbers↔page_range, pageSlice↔page(n).object_list) are validated by G-CONF differential test, correspondence prose matches the base_commit source. No A-consumed legs. Correspondence holds.

SOUNDNESS BASIS: postcondition fully pins result (frame directive 5) — length = page count AND every element = per-page slice; no free output component; no ungrounded oracle (dischargeable only by computing page numbers + slices from inputs). ≥5 distinct wrong impls attempted (partial-domain, boundary, control-flow-effect, off-by-one, ungrounded-oracle echo, prepatch); none with a closing clean-axiom proof has a materialized faithful patch that fails to resolve. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The postcondition problem_spec_paginatorPages pins the result EXACTLY (result = (pageNumbers objectList.length perPage orphans allowEmpty).map (fun n => pageSlice objectList perPage orphans n)) under the theorem hypothesis 1 ≤ perPage. Every wrong impl that diverges anywhere on the perPage≥1 domain fails to close (atk_1..5 all EXIT=1). The only impls that verify either equal gold everywhere (atk_6 echo) or diverge ONLY at perPage=0 (atk_7), which is outside both the theorem hypothesis AND the Python domain (per_page=0 raises ZeroDivisionError in num_pages; the F2P/P2P tests use per_page≥1). Both verifying impls' faithful patches RESOLVE under the official harness.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Mathlib
-- imports-end

/-!
Walking every page of a paginated collection, in order.

A paginated collection is described by four data:

  * the underlying list of items being paged over;
  * how many items make up a full page;
  * how many trailing items may be absorbed into the final page instead of
    spilling onto a page of their own (the orphan allowance);
  * whether an empty collection still presents a single (empty) page.

From these the collection exposes a 1-based numbering of its pages and, for each
page number, the contiguous slice of items shown on that page. Walking the
collection produces, in increasing page-number order, the slice of items
belonging to each page — i.e. exactly the same sequence of page contents one
would obtain by asking for each page number in turn.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The page count, the
-- 1-based page numbering, and the per-page slice are each total, pure functions
-- of the four input data (a length/arithmetic computation and a list slice), so
-- they are modeled directly below rather than abstracted behind an `opaque`
-- contract. Hence no `opaque`/`axiom` callee declaration is required.
-- axioms-end

-- pure-start
/-- The number of pages for a collection of `count` items shown `perPage` at a
time, allowing `orphans` trailing items to be folded into the final page.
`allowEmpty = false` collapses an empty collection to zero pages; otherwise an
empty collection still has one (empty) page. For `perPage ≥ 1` this is the
ceiling of `max 1 (count - orphans)` divided by `perPage`. -/
def pageCount (count perPage orphans : Nat) (allowEmpty : Bool) : Nat :=
  if count = 0 ∧ allowEmpty = false then 0
  else (max 1 (count - orphans) + perPage - 1) / perPage

/-- The 1-based list of page numbers, `[1, 2, …, pageCount]`. -/
def pageNumbers (count perPage orphans : Nat) (allowEmpty : Bool) : List Nat :=
  List.range' 1 (pageCount count perPage orphans allowEmpty)

/-- The contiguous slice of items shown on page `n` (1-based). The window starts
at `(n-1)*perPage` and spans `perPage` items, except that a window whose end is
within `orphans` of the collection's end is extended to absorb those trailing
items. -/
def pageSlice {α : Type} (objectList : List α) (perPage orphans n : Nat) : List α :=
  let count := objectList.length
  let bottom := (n - 1) * perPage
  let top := bottom + perPage
  let top := if top + orphans ≥ count then count else top
  (objectList.drop bottom).take (top - bottom)
-- pure-end

-- post-conditions-start
/-- Walking the collection yields, in increasing page-number order, the slice of
items on each page: the result is exactly the list obtained by mapping the
per-page slice over every page number `[1, …, pageCount]`. This pins the result
fully — its length is the page count and its `k`-th entry is the slice for page
`k+1` — so no output component is left free. -/
def problem_spec_paginatorPages {α : Type}
    (objectList : List α) (perPage orphans : Nat) (allowEmpty : Bool)
    (result : List (List α)) : Prop :=
  result =
    (pageNumbers objectList.length perPage orphans allowEmpty).map
      (fun n => pageSlice objectList perPage orphans n)
-- post-conditions-end

-- impl-start
def implementation_paginatorPages {α : Type}
    (objectList : List α) (perPage orphans : Nat) (allowEmpty : Bool) :
    List (List α) := Id.run do
  let mut pages : List (List α) := []
  for n in pageNumbers objectList.length perPage orphans allowEmpty do
    pages := pages ++ [pageSlice objectList perPage orphans n]
  return pages
-- impl-end

-- proof-start
/-- The `for` loop, generalized over the accumulator, appends each page's slice
in order: walking `xs` from `init` yields `init ++ xs.map pageSlice`. -/
theorem paginatorPages_forIn {α : Type} (objectList : List α) (perPage orphans : Nat)
    (xs : List Nat) (init : List (List α)) :
    Id.run (forIn xs init (fun n r =>
      (do pure PUnit.unit;
          pure (ForInStep.yield (r ++ [pageSlice objectList perPage orphans n]))))) =
      init ++ xs.map (fun n => pageSlice objectList perPage orphans n) := by
  induction xs generalizing init with
  | nil => simp [Id.run, pure, List.forIn_nil]
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    rw [ih]
    simp

theorem correct_paginatorPages {α : Type}
    (objectList : List α) (perPage orphans : Nat) (allowEmpty : Bool)
    (hperPage : 1 ≤ perPage) :
    problem_spec_paginatorPages objectList perPage orphans allowEmpty
      (implementation_paginatorPages objectList perPage orphans allowEmpty) := by
  unfold problem_spec_paginatorPages implementation_paginatorPages
  have h := paginatorPages_forIn objectList perPage orphans
    (pageNumbers objectList.length perPage orphans allowEmpty) []
  simp only [Id.run, bind, pure] at h ⊢
  rw [h]
  simp
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL: same_spec=True confirmed for all 7 attacks (spec_view elides the entire impl+proof regions incl. theorem header; axioms/pure/pre/post byte-identical). Verified concurrently in batches of ≤4 via scripts/lean_verify.sh.

### ATTACKS (path, command, exit, axioms, resolve):
- atk_1 (prepatch bug: return []): `bash scripts/lean_verify.sh atk_1.lean` EXIT=1 (does NOT close) — prepatch reproduced.
- atk_2 (reversed page order via .reverse): EXIT=1 (does NOT close).
- atk_3 (off-by-one: List.range' 0 ... 0-based numbering, wrong slices): EXIT=1 (does NOT close).
- atk_4 (boundary: orphan-absorption dropped, inline (drop).take perPage): EXIT=1 (does NOT close).
- atk_5 (control-flow effect: .dropLast drops last page): EXIT=1 (does NOT close).
- atk_6 (ungrounded-oracle echo of spec RHS): `bash scripts/lean_verify.sh atk_6.lean` EXIT=0; `#print axioms correct_paginatorPages` => 'does not depend on any axioms' (clean, no sorryAx). Faithful patch = gold __iter__. RESOLVE: run_resolve('django__django-9296', atk_6_patch.diff) => completed=True resolved=True attempts=1 flaky=False note=resolved. Per G-PANEL-1/G-EQ policy a resolving echo is NOT a weakness.
- atk_7 (partial-domain: diverges from gold only at perPage=0, returns [] there; equals gold for perPage≥1): EXIT=0; `#print axioms` => [propext, Quot.sound] (⊆ STANDARD_AXIOMS, clean, no sorryAx). Faithful patch adds `if self.per_page == 0: return` guard to gold __iter__. RESOLVE: run_resolve => completed=True resolved=True attempts=1 flaky=False note=resolved. Diverges only OUTSIDE the theorem hypothesis (1 ≤ perPage) and outside the Python test domain (per_page=0 -> ZeroDivisionError), so does not break verify⇒correct.
- positive control pc.lean (gold for-loop impl): EXIT=0 (verifies).

REFINEMENT.MD AUDIT: 4 legs, all tagged R (deep model of unchanged callees page_range/num_pages/page). No kind-3 legs. axioms region is empty (axiom_check.py is a skip stub — no opaque/axiom declared); the three A-reference deep models (pageCount↔num_pages, pageNumbers↔page_range, pageSlice↔page(n).object_list) are validated by G-CONF differential test, correspondence prose matches the base_commit source. No A-consumed legs. Correspondence holds.

SOUNDNESS BASIS: postcondition fully pins result (frame directive 5) — length = page count AND every element = per-page slice; no free output component; no ungrounded oracle (dischargeable only by computing page numbers + slices from inputs). ≥5 distinct wrong impls attempted (partial-domain, boundary, control-flow-effect, off-by-one, ungrounded-oracle echo, prepatch); none with a closing clean-axiom proof has a materialized faithful patch that fails to resolve. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-vs-real-repo drift) check for django__django-9296 lean bundle. Modeled function implementation_paginatorPages = Paginator.__iter__ (gold-added), which drives unchanged callees page_range/num_pages/page(n), modeled deeply as pageNumbers/pageCount/pageSlice.

### Checks
- lean_verify.sh Solution.lean -> exit 0 (only unused-var lint). #print axioms correct_paginatorPages -> [propext, Quot.sound]; NO sorryAx, proof genuine.
- same_spec(Solution, Solution_prepatch, LeanBackend) = True (spec region byte-identical).
- Independent oracle transcribed verbatim from real django/core/paginator.py (num_pages/page_range/page) diff-tested vs Lean-model transliteration (Nat truncated sub, (h+p-1)//p ceiling, drop/take slice):
  * exhaustive small domain (len 0-59, per_page 1-14, orphans 0-59, allow_empty both) -> 0 divergences
  * 2,000,000 random fuzz inputs -> 0 divergences
  * F2P [1,2,3] per_page=2 -> [[1,2],[3]] correct.

SEAM PROBED: real num_pages uses float ceil(hits/per_page); model uses integer (h+p-1)//p. These diverge ONLY for hits > 2^53 (~9e15), which requires an object_list of that length. mapping.md scopes the domain to plain Python lists (QuerySet.count() branch unmodeled), so such a count is unrealizable. Nat truncated subtraction correctly mirrors Python max(1, count-orphans) clamp and slice clamping. No realizable diverging input.

The spec is not too strong: it pins result exactly (result = (pageNumbers ...).map (pageSlice ...)), grounded entirely in the 4 inputs, agreeing with the real callees over the entire realizable domain. Spec is faithful — no defect.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage / gold-reconstruction check for django__django-9296 (lean). Gold edit is the newly-added Paginator.__iter__:
    def __iter__(self):
        for page_number in self.page_range:
            yield self.page(page_number)
This edit is quoted VERBATIM in the public problem_statement (the reporter proposed the exact implementation). Therefore the gold change is fully public independently of the spec view, and nothing in the spec view can leak it 'beyond' the public problem_statement.

Spec view content (Solution.lean minus impl-start..impl-end and proof-start..proof-end): the docstring, the empty-axioms note, the pure helpers pageCount/pageNumbers/pageSlice, and the postcondition problem_spec_paginatorPages.
- pageCount/pageNumbers/pageSlice deeply model num_pages/page_range/page(n) — these are UNCHANGED callees that pre-exist at base_commit (public repo source), NOT the gold edit. Their presence describes the surrounding paginator machinery, not the patch.
- problem_spec_paginatorPages states: result = (pageNumbers ...).map (pageSlice ...) — i.e. iterating yields, in page-number order, each page's slice. This is exactly the iteration structure the problem_statement already spells out ('for page_num in self.page_range: yield self.page(page_num)'). It is the specification of the observable behavior, standard for a spec view, and reveals nothing about the fix that the problem_statement doesn't already state.
- No comment or identifier reconstructs a hidden edit; the modeled diff (adding __iter__) is public. impl/proof regions (which carry the actual implementation) are excluded from the spec view.

Recorded G-LEAK lexical screen is 'pass' (spec view clean). No spec-view line leaks the gold edit beyond the public problem_statement.

Note: could not run same_spec byte-identity of the spec region (harness helper requires a 'tables' arg not available here); this is orthogonal to the leakage judgment, which concerns whether the spec view discloses the gold edit — it does not.

    def __iter__(self):
        for page_number in self.page_range:
            yield self.page(page_number)
This edit is quoted VERBATIM in the public problem_statement (the reporter proposed the exact implementation). Therefore the gold change is fully public independently of the spec view, and nothing in the spec view can leak it 'beyond' the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
