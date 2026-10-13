# P2 adversarial audit — matplotlib__matplotlib-24627

**Backend:** `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -52,54 +52,22 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_clearAxes (artists : List Artist)
-    : List Artist × List Artist := Id.run do
-  -- mirror `old_children, self._children = self._children, []`
-  let oldChildren := artists
-  let mut newChildren : List Artist := []
-  -- mirror `for chld in old_children: chld.axes = chld.figure = None`
-  let mut formerChildren : List Artist := []
-  for chld in oldChildren do
-    let chld := { chld with axes := none, figure := none }
-    formerChildren := formerChildren ++ [chld]
-  return (newChildren, formerChildren)
+    : List Artist × List Artist :=
+  ([], artists)
 -- impl-end
 
 -- proof-start
-/-- The loop accumulates a `++ [deparented child]` per element; generalized over
-the accumulator it equals `init ++ (map deparent xs)`. -/
-theorem loop_helper_clearAxes (xs : List Artist) (init : List Artist) :
-    Id.run (forIn xs init (fun chld r =>
-      (pure (ForInStep.yield (r ++ [{ chld with axes := none, figure := none }])) : Id _)))
-      = init ++ xs.map (fun c => { c with axes := none, figure := none }) := by
-  induction xs generalizing init with
-  | nil => simp
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [ih]
-    simp [List.map_cons]
-
-/-- Closed form of the implementation. -/
-theorem impl_eq_clearAxes (artists : List Artist) :
-    implementation_clearAxes artists
-      = ([], artists.map (fun c => { c with axes := none, figure := none })) := by
-  unfold implementation_clearAxes
-  simp only [Id.run, bind]
-  have := loop_helper_clearAxes artists []
-  simp only [Id.run] at this
-  rw [this]
-  rfl
-
 theorem correct_clearAxes : ∀ artists,
     problem_spec_clearAxes artists (implementation_clearAxes artists) := by
   intro artists
-  rw [impl_eq_clearAxes]
-  refine ⟨rfl, ?_, ?_⟩
-  · simp
-  · intro i hi
-    refine ⟨{ artists[i] with axes := none, figure := none }, artists[i], ?_, ?_, rfl, rfl, rfl⟩
-    · rw [List.getElem?_eq_getElem (by simpa using hi)]
-      simp [List.getElem_map]
-    · rw [List.getElem?_eq_getElem hi]
+  unfold implementation_clearAxes problem_spec_clearAxes
+  refine ⟨rfl, by simp, ?_⟩
+  intro i hi
+  refine ⟨artists[i], artists[i], ?_, ?_, ?_, ?_, rfl⟩
+  · rw [List.getElem?_eq_getElem hi]
+  · rw [List.getElem?_eq_getElem hi]
+  · sorry
+  · sorry
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -52,54 +52,23 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_clearAxes (artists : List Artist)
-    : List Artist × List Artist := Id.run do
-  -- mirror `old_children, self._children = self._children, []`
-  let oldChildren := artists
-  let mut newChildren : List Artist := []
-  -- mirror `for chld in old_children: chld.axes = chld.figure = None`
-  let mut formerChildren : List Artist := []
-  for chld in oldChildren do
-    let chld := { chld with axes := none, figure := none }
-    formerChildren := formerChildren ++ [chld]
-  return (newChildren, formerChildren)
+    : List Artist × List Artist :=
+  ([], (artists.map (fun c => { c with axes := none, figure := none })).reverse)
 -- impl-end
 
 -- proof-start
-/-- The loop accumulates a `++ [deparented child]` per element; generalized over
-the accumulator it equals `init ++ (map deparent xs)`. -/
-theorem loop_helper_clearAxes (xs : List Artist) (init : List Artist) :
-    Id.run (forIn xs init (fun chld r =>
-      (pure (ForInStep.yield (r ++ [{ chld with axes := none, figure := none }])) : Id _)))
-      = init ++ xs.map (fun c => { c with axes := none, figure := none }) := by
-  induction xs generalizing init with
-  | nil => simp
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [ih]
-    simp [List.map_cons]
-
-/-- Closed form of the implementation. -/
-theorem impl_eq_clearAxes (artists : List Artist) :
-    implementation_clearAxes artists
-      = ([], artists.map (fun c => { c with axes := none, figure := none })) := by
-  unfold implementation_clearAxes
-  simp only [Id.run, bind]
-  have := loop_helper_clearAxes artists []
-  simp only [Id.run] at this
-  rw [this]
-  rfl
-
 theorem correct_clearAxes : ∀ artists,
     problem_spec_clearAxes artists (implementation_clearAxes artists) := by
   intro artists
-  rw [impl_eq_clearAxes]
-  refine ⟨rfl, ?_, ?_⟩
-  · simp
-  · intro i hi
-    refine ⟨{ artists[i] with axes := none, figure := none }, artists[i], ?_, ?_, rfl, rfl, rfl⟩
-    · rw [List.getElem?_eq_getElem (by simpa using hi)]
-      simp [List.getElem_map]
-    · rw [List.getElem?_eq_getElem hi]
+  unfold implementation_clearAxes problem_spec_clearAxes
+  refine ⟨rfl, by simp, ?_⟩
+  intro i hi
+  refine ⟨_, artists[i], ?_, ?_, ?_, ?_, ?_⟩
+  · sorry
+  · rw [List.getElem?_eq_getElem hi]
+  · sorry
+  · sorry
+  · sorry
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -52,54 +52,18 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_clearAxes (artists : List Artist)
-    : List Artist × List Artist := Id.run do
-  -- mirror `old_children, self._children = self._children, []`
-  let oldChildren := artists
-  let mut newChildren : List Artist := []
-  -- mirror `for chld in old_children: chld.axes = chld.figure = None`
-  let mut formerChildren : List Artist := []
-  for chld in oldChildren do
-    let chld := { chld with axes := none, figure := none }
-    formerChildren := formerChildren ++ [chld]
-  return (newChildren, formerChildren)
+    : List Artist × List Artist :=
+  ([], (artists.map (fun c => { c with axes := none, figure := none })).dropLast)
 -- impl-end
 
 -- proof-start
-/-- The loop accumulates a `++ [deparented child]` per element; generalized over
-the accumulator it equals `init ++ (map deparent xs)`. -/
-theorem loop_helper_clearAxes (xs : List Artist) (init : List Artist) :
-    Id.run (forIn xs init (fun chld r =>
-      (pure (ForInStep.yield (r ++ [{ chld with axes := none, figure := none }])) : Id _)))
-      = init ++ xs.map (fun c => { c with axes := none, figure := none }) := by
-  induction xs generalizing init with
-  | nil => simp
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [ih]
-    simp [List.map_cons]
-
-/-- Closed form of the implementation. -/
-theorem impl_eq_clearAxes (artists : List Artist) :
-    implementation_clearAxes artists
-      = ([], artists.map (fun c => { c with axes := none, figure := none })) := by
-  unfold implementation_clearAxes
-  simp only [Id.run, bind]
-  have := loop_helper_clearAxes artists []
-  simp only [Id.run] at this
-  rw [this]
-  rfl
-
 theorem correct_clearAxes : ∀ artists,
     problem_spec_clearAxes artists (implementation_clearAxes artists) := by
   intro artists
-  rw [impl_eq_clearAxes]
+  unfold implementation_clearAxes problem_spec_clearAxes
   refine ⟨rfl, ?_, ?_⟩
   · simp
-  · intro i hi
-    refine ⟨{ artists[i] with axes := none, figure := none }, artists[i], ?_, ?_, rfl, rfl, rfl⟩
-    · rw [List.getElem?_eq_getElem (by simpa using hi)]
-      simp [List.getElem_map]
-    · rw [List.getElem?_eq_getElem hi]
+  · sorry
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -52,54 +52,21 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_clearAxes (artists : List Artist)
-    : List Artist × List Artist := Id.run do
-  -- mirror `old_children, self._children = self._children, []`
-  let oldChildren := artists
-  let mut newChildren : List Artist := []
-  -- mirror `for chld in old_children: chld.axes = chld.figure = None`
-  let mut formerChildren : List Artist := []
-  for chld in oldChildren do
-    let chld := { chld with axes := none, figure := none }
-    formerChildren := formerChildren ++ [chld]
-  return (newChildren, formerChildren)
+    : List Artist × List Artist :=
+  ([], artists.map (fun c => { c with axes := none }))
 -- impl-end
 
 -- proof-start
-/-- The loop accumulates a `++ [deparented child]` per element; generalized over
-the accumulator it equals `init ++ (map deparent xs)`. -/
-theorem loop_helper_clearAxes (xs : List Artist) (init : List Artist) :
-    Id.run (forIn xs init (fun chld r =>
-      (pure (ForInStep.yield (r ++ [{ chld with axes := none, figure := none }])) : Id _)))
-      = init ++ xs.map (fun c => { c with axes := none, figure := none }) := by
-  induction xs generalizing init with
-  | nil => simp
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [ih]
-    simp [List.map_cons]
-
-/-- Closed form of the implementation. -/
-theorem impl_eq_clearAxes (artists : List Artist) :
-    implementation_clearAxes artists
-      = ([], artists.map (fun c => { c with axes := none, figure := none })) := by
-  unfold implementation_clearAxes
-  simp only [Id.run, bind]
-  have := loop_helper_clearAxes artists []
-  simp only [Id.run] at this
-  rw [this]
-  rfl
-
 theorem correct_clearAxes : ∀ artists,
     problem_spec_clearAxes artists (implementation_clearAxes artists) := by
   intro artists
-  rw [impl_eq_clearAxes]
-  refine ⟨rfl, ?_, ?_⟩
-  · simp
-  · intro i hi
-    refine ⟨{ artists[i] with axes := none, figure := none }, artists[i], ?_, ?_, rfl, rfl, rfl⟩
-    · rw [List.getElem?_eq_getElem (by simpa using hi)]
-      simp [List.getElem_map]
-    · rw [List.getElem?_eq_getElem hi]
+  unfold implementation_clearAxes problem_spec_clearAxes
+  refine ⟨rfl, by simp, ?_⟩
+  intro i hi
+  refine ⟨{ artists[i] with axes := none }, artists[i], ?_, ?_, rfl, ?_, rfl⟩
+  · rw [List.getElem?_eq_getElem (by simpa using hi)]; simp [List.getElem_map]
+  · rw [List.getElem?_eq_getElem hi]
+  · sorry
 -- proof-end
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -52,54 +52,20 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_clearAxes (artists : List Artist)
-    : List Artist × List Artist := Id.run do
-  -- mirror `old_children, self._children = self._children, []`
-  let oldChildren := artists
-  let mut newChildren : List Artist := []
-  -- mirror `for chld in old_children: chld.axes = chld.figure = None`
-  let mut formerChildren : List Artist := []
-  for chld in oldChildren do
-    let chld := { chld with axes := none, figure := none }
-    formerChildren := formerChildren ++ [chld]
-  return (newChildren, formerChildren)
+    : List Artist × List Artist :=
+  ([], artists.map (fun c => { c with figure := none, axes := none }))
 -- impl-end
 
 -- proof-start
-/-- The loop accumulates a `++ [deparented child]` per element; generalized over
-the accumulator it equals `init ++ (map deparent xs)`. -/
-theorem loop_helper_clearAxes (xs : List Artist) (init : List Artist) :
-    Id.run (forIn xs init (fun chld r =>
-      (pure (ForInStep.yield (r ++ [{ chld with axes := none, figure := none }])) : Id _)))
-      = init ++ xs.map (fun c => { c with axes := none, figure := none }) := by
-  induction xs generalizing init with
-  | nil => simp
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [ih]
-    simp [List.map_cons]
-
-/-- Closed form of the implementation. -/
-theorem impl_eq_clearAxes (artists : List Artist) :
-    implementation_clearAxes artists
-      = ([], artists.map (fun c => { c with axes := none, figure := none })) := by
-  unfold implementation_clearAxes
-  simp only [Id.run, bind]
-  have := loop_helper_clearAxes artists []
-  simp only [Id.run] at this
-  rw [this]
-  rfl
-
 theorem correct_clearAxes : ∀ artists,
     problem_spec_clearAxes artists (implementation_clearAxes artists) := by
   intro artists
-  rw [impl_eq_clearAxes]
-  refine ⟨rfl, ?_, ?_⟩
-  · simp
-  · intro i hi
-    refine ⟨{ artists[i] with axes := none, figure := none }, artists[i], ?_, ?_, rfl, rfl, rfl⟩
-    · rw [List.getElem?_eq_getElem (by simpa using hi)]
-      simp [List.getElem_map]
-    · rw [List.getElem?_eq_getElem hi]
+  unfold implementation_clearAxes problem_spec_clearAxes
+  refine ⟨rfl, by simp, ?_⟩
+  intro i hi
+  refine ⟨{ artists[i] with figure := none, axes := none }, artists[i], ?_, ?_, rfl, rfl, rfl⟩
+  · rw [List.getElem?_eq_getElem (by simpa using hi)]; simp [List.getElem_map]
+  · rw [List.getElem?_eq_getElem hi]
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -52,54 +52,21 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_clearAxes (artists : List Artist)
-    : List Artist × List Artist := Id.run do
-  -- mirror `old_children, self._children = self._children, []`
-  let oldChildren := artists
-  let mut newChildren : List Artist := []
-  -- mirror `for chld in old_children: chld.axes = chld.figure = None`
-  let mut formerChildren : List Artist := []
-  for chld in oldChildren do
-    let chld := { chld with axes := none, figure := none }
-    formerChildren := formerChildren ++ [chld]
-  return (newChildren, formerChildren)
+    : List Artist × List Artist :=
+  ([], artists.map (fun _ => { data := 0, axes := none, figure := none }))
 -- impl-end
 
 -- proof-start
-/-- The loop accumulates a `++ [deparented child]` per element; generalized over
-the accumulator it equals `init ++ (map deparent xs)`. -/
-theorem loop_helper_clearAxes (xs : List Artist) (init : List Artist) :
-    Id.run (forIn xs init (fun chld r =>
-      (pure (ForInStep.yield (r ++ [{ chld with axes := none, figure := none }])) : Id _)))
-      = init ++ xs.map (fun c => { c with axes := none, figure := none }) := by
-  induction xs generalizing init with
-  | nil => simp
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [ih]
-    simp [List.map_cons]
-
-/-- Closed form of the implementation. -/
-theorem impl_eq_clearAxes (artists : List Artist) :
-    implementation_clearAxes artists
-      = ([], artists.map (fun c => { c with axes := none, figure := none })) := by
-  unfold implementation_clearAxes
-  simp only [Id.run, bind]
-  have := loop_helper_clearAxes artists []
-  simp only [Id.run] at this
-  rw [this]
-  rfl
-
 theorem correct_clearAxes : ∀ artists,
     problem_spec_clearAxes artists (implementation_clearAxes artists) := by
   intro artists
-  rw [impl_eq_clearAxes]
-  refine ⟨rfl, ?_, ?_⟩
-  · simp
-  · intro i hi
-    refine ⟨{ artists[i] with axes := none, figure := none }, artists[i], ?_, ?_, rfl, rfl, rfl⟩
-    · rw [List.getElem?_eq_getElem (by simpa using hi)]
-      simp [List.getElem_map]
-    · rw [List.getElem?_eq_getElem hi]
+  unfold implementation_clearAxes problem_spec_clearAxes
+  refine ⟨rfl, by simp, ?_⟩
+  intro i hi
+  refine ⟨{ data := 0, axes := none, figure := none }, artists[i], ?_, ?_, rfl, rfl, ?_⟩
+  · rw [List.getElem?_eq_getElem (by simpa using hi)]; simp [List.getElem_map]
+  · rw [List.getElem?_eq_getElem hi]
+  · sorry
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -52,54 +52,19 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_clearAxes (artists : List Artist)
-    : List Artist × List Artist := Id.run do
-  -- mirror `old_children, self._children = self._children, []`
-  let oldChildren := artists
-  let mut newChildren : List Artist := []
-  -- mirror `for chld in old_children: chld.axes = chld.figure = None`
-  let mut formerChildren : List Artist := []
-  for chld in oldChildren do
-    let chld := { chld with axes := none, figure := none }
-    formerChildren := formerChildren ++ [chld]
-  return (newChildren, formerChildren)
+    : List Artist × List Artist :=
+  ([], { data := 0, axes := none, figure := none } ::
+        artists.map (fun c => { c with axes := none, figure := none }))
 -- impl-end
 
 -- proof-start
-/-- The loop accumulates a `++ [deparented child]` per element; generalized over
-the accumulator it equals `init ++ (map deparent xs)`. -/
-theorem loop_helper_clearAxes (xs : List Artist) (init : List Artist) :
-    Id.run (forIn xs init (fun chld r =>
-      (pure (ForInStep.yield (r ++ [{ chld with axes := none, figure := none }])) : Id _)))
-      = init ++ xs.map (fun c => { c with axes := none, figure := none }) := by
-  induction xs generalizing init with
-  | nil => simp
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [Id.run, bind] at ih ⊢
-    rw [ih]
-    simp [List.map_cons]
-
-/-- Closed form of the implementation. -/
-theorem impl_eq_clearAxes (artists : List Artist) :
-    implementation_clearAxes artists
-      = ([], artists.map (fun c => { c with axes := none, figure := none })) := by
-  unfold implementation_clearAxes
-  simp only [Id.run, bind]
-  have := loop_helper_clearAxes artists []
-  simp only [Id.run] at this
-  rw [this]
-  rfl
-
 theorem correct_clearAxes : ∀ artists,
     problem_spec_clearAxes artists (implementation_clearAxes artists) := by
   intro artists
-  rw [impl_eq_clearAxes]
+  unfold implementation_clearAxes problem_spec_clearAxes
   refine ⟨rfl, ?_, ?_⟩
   · simp
-  · intro i hi
-    refine ⟨{ artists[i] with axes := none, figure := none }, artists[i], ?_, ?_, rfl, rfl, rfl⟩
-    · rw [List.getElem?_eq_getElem (by simpa using hi)]
-      simp [List.getElem_map]
-    · rw [List.getElem?_eq_getElem hi]
+  · sorry
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Model of the behavior of clearing a plotting axes.

Public behavior (from the issue): when an axes is cleared, its list of child
artists is emptied, AND every former child artist is *deparented* — its owning
`axes` and owning `figure` references are unset (set to "none"). Removing an
artist individually already deparents it; clearing must do the same for every
child it drops. Any other state carried by an artist is left untouched.

We model an artist as a record carrying opaque payload `data` (all state the
clear operation must NOT touch), plus its owning-`axes` and owning-`figure`
references as `Option` identities (`none` ⇒ deparented).
-/

-- axioms-start
-- No unchanged outside callee is consumed: the modeled behavior is a pure
-- list/record transformation, so there is no `opaque` callee and no `_prop`
-- axiom. (G-AX is a skip stub for this instance.)
-- axioms-end

-- pure-start
/-- An artist owned by an axes/figure. `data` stands for every other field the
clear operation must preserve; `axes`/`figure` are the owning references that
clearing unsets (`none` ⇒ deparented). -/
structure Artist where
  data : Nat
  axes : Option Nat
  figure : Option Nat
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- Clearing returns the pair `(newChildren, formerChildren)`:
* `newChildren` (`result.1`) is the axes' fresh child list — empty;
* `formerChildren` (`result.2`) are the artists that were children, each now
  deparented.

The contract pins, in order: the new child list is empty; the former-children
list has the same length (and positional correspondence) as the input; and for
each position the former child has its owning `axes` and `figure` unset to
`none` while every other field (`data`) is preserved (frame discipline). -/
def problem_spec_clearAxes (artists : List Artist)
    (result : List Artist × List Artist) : Prop :=
  result.1 = [] ∧
  result.2.length = artists.length ∧
  ∀ i, i < artists.length →
    ∃ a c, result.2[i]? = some a ∧ artists[i]? = some c ∧
      a.axes = none ∧ a.figure = none ∧ a.data = c.data
-- post-conditions-end

-- impl-start
def implementation_clearAxes (artists : List Artist)
    : List Artist × List Artist := Id.run do
  -- mirror `old_children, self._children = self._children, []`
  let oldChildren := artists
  let mut newChildren : List Artist := []
  -- mirror `for chld in old_children: chld.axes = chld.figure = None`
  let mut formerChildren : List Artist := []
  for chld in oldChildren do
    let chld := { chld with axes := none, figure := none }
    formerChildren := formerChildren ++ [chld]
  return (newChildren, formerChildren)
-- impl-end

-- proof-start
/-- The loop accumulates a `++ [deparented child]` per element; generalized over
the accumulator it equals `init ++ (map deparent xs)`. -/
theorem loop_helper_clearAxes (xs : List Artist) (init : List Artist) :
    Id.run (forIn xs init (fun chld r =>
      (pure (ForInStep.yield (r ++ [{ chld with axes := none, figure := none }])) : Id _)))
      = init ++ xs.map (fun c => { c with axes := none, figure := none }) := by
  induction xs generalizing init with
  | nil => simp
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    rw [ih]
    simp [List.map_cons]

/-- Closed form of the implementation. -/
theorem impl_eq_clearAxes (artists : List Artist) :
    implementation_clearAxes artists
      = ([], artists.map (fun c => { c with axes := none, figure := none })) := by
  unfold implementation_clearAxes
  simp only [Id.run, bind]
  have := loop_helper_clearAxes artists []
  simp only [Id.run] at this
  rw [this]
  rfl

theorem correct_clearAxes : ∀ artists,
    problem_spec_clearAxes artists (implementation_clearAxes artists) := by
  intro artists
  rw [impl_eq_clearAxes]
  refine ⟨rfl, ?_, ?_⟩
  · simp
  · intro i hi
    refine ⟨{ artists[i] with axes := none, figure := none }, artists[i], ?_, ?_, rfl, rfl, rfl⟩
    · rw [List.getElem?_eq_getElem (by simpa using hi)]
      simp [List.getElem_map]
    · rw [List.getElem?_eq_getElem hi]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

**VERDICT:** SOUND. The frozen spec problem_spec_clearAxes is a TOTAL functional specification that pins the entire observable post-state positionally: result.1 = [] (child list emptied), result.2.length = artists.length (same length), and for every i, the former child is forced to axes=none AND figure=none AND data=c.data (all three of Artist's fields fixed). This uniquely determines result = ([], artists.map deparent) with no behavioral wiggle room. Any spec-closing impl is therefore observationally identical to the gold behavior, which is exactly what the resolve test (test_cla_clears_children_axes_and_fig: art.axes is None and art.figure is None after ax.clear()) checks.

ATTACKS (all files same_spec=True vs Solution.lean, verified via swebench_unified.markers.same_spec; command per file: `bash scripts/lean_verify.sh <path>`; run concurrently in 2 batches of 4 as background jobs):
- atk_1 (PREPATCH BUG, no deparenting, ([], artists)): exit=3 (proof needs a.axes=none which is false; sorry remains). PREPATCH REPRODUCED — the pre-patch behavior canNOT close correct_clearAxes.
- atk_2 (reversed former children, ([], (map deparent).reverse)): exit=1 (positional obligation artists[i].data can't be met on non-palindromic data; unsolved goals).
- atk_3 (partial-domain / boundary, dropLast): exit=1 (length obligation artists.length-1 = artists.length false).
- atk_4 (control-flow-effect, only .axes unset, figure preserved): exit=3 (a.figure=none false; sorry).
- atk_5 (UNGROUNDED-ORACLE ECHO, gold-equivalent, ([], map (fun c => {c with figure:=none, axes:=none}))): exit=0 CLOSES. `#print axioms correct_clearAxes` => [propext] (clean, no sorryAx). Per protocol, materialized its faithful refined patch (atk_5.patch — snapshot + per-child `chld.figure = chld.axes = None` deparent loop) and RAN it through the official harness: `run_resolve('matplotlib__matplotlib-24627', patch)` => RESOLVED=True (completed). So this verifying impl's faithful patch DOES resolve — no verify⇏correct break. This is a resolving echo of the gold, which per 2026-08-06 policy is NOT a weakness.
- atk_6 (payload clobber, data:=0): exit=3 (a.data=c.data false; sorry).
- atk_7 (boundary, extra spurious deparented element prepended): exit=1 (length obligation reduces to False).

**POSITIVE CONTROL:** pos.lean = bundle Solution.lean verbatim => exit=0, `#print axioms` = [propext, Quot.sound] (allowed only).

**RESULT:** Of 7 same-spec attacks, ONLY the gold-equivalent echo (atk_5) closes with clean axioms; its materialized faithful patch RESOLVED=True. All 6 genuinely-wrong impls (partial-domain, boundary, control-flow-effect, payload-clobber, reversal, un-deparented prepatch) FAIL to close — their spec obligations are provably false, not lazily sorried. No spec-closing-but-non-resolving impl exists.

REFINEMENT.MD / A-LEG AUDIT: meta.json confirms axioms=[], opaque_callees=[], deep_model_references=[], conf_skip=false. There are NO A-legs (no opaque callee, no `_prop` axiom, no deep-model reference) — the A-leg / correspondence audit is vacuous by construction. refinement.md rows 1-6 are all tagged R/I and correspond op-for-op to the gold edit (`old_children, self._children = self._children, []; for chld in old_children: chld.axes = chld.figure = None`): list snapshot->R, new []->R, iteration->I, two-field reset (axes+figure to none, other fields preserved)->R, accumulation->R, pair return->R. No kind-3 (inexpressible) leg. Chained attribute assignment sets exactly .axes/.figure to None and touches nothing else, matching the frame-discipline data=c.data conjunct. Correspondence holds.

**SCHEDULE NOTE:** attack lean_verify runs were launched concurrently as background Bash jobs, <=4 at a time (batch1: pos,atk_1,atk_2,atk_3; batch2: atk_4,atk_5,atk_6,atk_7; then axiom checks for pos+atk_5 concurrently). The single needed resolve (atk_5) completed with RESOLVED=True.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Model of the behavior of clearing a plotting axes.

Public behavior (from the issue): when an axes is cleared, its list of child
artists is emptied, AND every former child artist is *deparented* — its owning
`axes` and owning `figure` references are unset (set to "none"). Removing an
artist individually already deparents it; clearing must do the same for every
child it drops. Any other state carried by an artist is left untouched.

We model an artist as a record carrying opaque payload `data` (all state the
clear operation must NOT touch), plus its owning-`axes` and owning-`figure`
references as `Option` identities (`none` ⇒ deparented).
-/

-- axioms-start
-- No unchanged outside callee is consumed: the modeled behavior is a pure
-- list/record transformation, so there is no `opaque` callee and no `_prop`
-- axiom. (G-AX is a skip stub for this instance.)
-- axioms-end

-- pure-start
/-- An artist owned by an axes/figure. `data` stands for every other field the
clear operation must preserve; `axes`/`figure` are the owning references that
clearing unsets (`none` ⇒ deparented). -/
structure Artist where
  data : Nat
  axes : Option Nat
  figure : Option Nat
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- Clearing returns the pair `(newChildren, formerChildren)`:
* `newChildren` (`result.1`) is the axes' fresh child list — empty;
* `formerChildren` (`result.2`) are the artists that were children, each now
  deparented.

The contract pins, in order: the new child list is empty; the former-children
list has the same length (and positional correspondence) as the input; and for
each position the former child has its owning `axes` and `figure` unset to
`none` while every other field (`data`) is preserved (frame discipline). -/
def problem_spec_clearAxes (artists : List Artist)
    (result : List Artist × List Artist) : Prop :=
  result.1 = [] ∧
  result.2.length = artists.length ∧
  ∀ i, i < artists.length →
    ∃ a c, result.2[i]? = some a ∧ artists[i]? = some c ∧
      a.axes = none ∧ a.figure = none ∧ a.data = c.data
-- post-conditions-end

-- impl-start
def implementation_clearAxes (artists : List Artist)
    : List Artist × List Artist := Id.run do
  -- mirror `old_children, self._children = self._children, []`
  let oldChildren := artists
  let mut newChildren : List Artist := []
  -- mirror `for chld in old_children: chld.axes = chld.figure = None`
  let mut formerChildren : List Artist := []
  for chld in oldChildren do
    let chld := { chld with axes := none, figure := none }
    formerChildren := formerChildren ++ [chld]
  return (newChildren, formerChildren)
-- impl-end

-- proof-start
/-- The loop accumulates a `++ [deparented child]` per element; generalized over
the accumulator it equals `init ++ (map deparent xs)`. -/
theorem loop_helper_clearAxes (xs : List Artist) (init : List Artist) :
    Id.run (forIn xs init (fun chld r =>
      (pure (ForInStep.yield (r ++ [{ chld with axes := none, figure := none }])) : Id _)))
      = init ++ xs.map (fun c => { c with axes := none, figure := none }) := by
  induction xs generalizing init with
  | nil => simp
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    rw [ih]
    simp [List.map_cons]

/-- Closed form of the implementation. -/
theorem impl_eq_clearAxes (artists : List Artist) :
    implementation_clearAxes artists
      = ([], artists.map (fun c => { c with axes := none, figure := none })) := by
  unfold implementation_clearAxes
  simp only [Id.run, bind]
  have := loop_helper_clearAxes artists []
  simp only [Id.run] at this
  rw [this]
  rfl

theorem correct_clearAxes : ∀ artists,
    problem_spec_clearAxes artists (implementation_clearAxes artists) := by
  intro artists
  rw [impl_eq_clearAxes]
  refine ⟨rfl, ?_, ?_⟩
  · simp
  · intro i hi
    refine ⟨{ artists[i] with axes := none, figure := none }, artists[i], ?_, ?_, rfl, rfl, rfl⟩
    · rw [List.getElem?_eq_getElem (by simpa using hi)]
      simp [List.getElem_map]
    · rw [List.getElem?_eq_getElem hi]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

**VERDICT:** SOUND. The frozen spec problem_spec_clearAxes is a TOTAL functional specification that pins the entire observable post-state positionally: result.1 = [] (child list emptied), result.2.length = artists.length (same length), and for every i, the former child is forced to axes=none AND figure=none AND data=c.data (all three of Artist's fields fixed). This uniquely determines result = ([], artists.map deparent) with no behavioral wiggle room. Any spec-closing impl is therefore observationally identical to the gold behavior, which is exactly what the resolve test (test_cla_clears_children_axes_and_fig: art.axes is None and art.figure is None after ax.clear()) checks.

ATTACKS (all files same_spec=True vs Solution.lean, verified via swebench_unified.markers.same_spec; command per file: `bash scripts/lean_verify.sh <path>`; run concurrently in 2 batches of 4 as background jobs):
- atk_1 (PREPATCH BUG, no deparenting, ([], artists)): exit=3 (proof needs a.axes=none which is false; sorry remains). PREPATCH REPRODUCED — the pre-patch behavior canNOT close correct_clearAxes.
- atk_2 (reversed former children, ([], (map deparent).reverse)): exit=1 (positional obligation artists[i].data can't be met on non-palindromic data; unsolved goals).
- atk_3 (partial-domain / boundary, dropLast): exit=1 (length obligation artists.length-1 = artists.length false).
- atk_4 (control-flow-effect, only .axes unset, figure preserved): exit=3 (a.figure=none false; sorry).
- atk_5 (UNGROUNDED-ORACLE ECHO, gold-equivalent, ([], map (fun c => {c with figure:=none, axes:=none}))): exit=0 CLOSES. `#print axioms correct_clearAxes` => [propext] (clean, no sorryAx). Per protocol, materialized its faithful refined patch (atk_5.patch — snapshot + per-child `chld.figure = chld.axes = None` deparent loop) and RAN it through the official harness: `run_resolve('matplotlib__matplotlib-24627', patch)` => RESOLVED=True (completed). So this verifying impl's faithful patch DOES resolve — no verify⇏correct break. This is a resolving echo of the gold, which per 2026-08-06 policy is NOT a weakness.
- atk_6 (payload clobber, data:=0): exit=3 (a.data=c.data false; sorry).
- atk_7 (boundary, extra spurious deparented element prepended): exit=1 (length obligation reduces to False).

**POSITIVE CONTROL:** pos.lean = bundle Solution.lean verbatim => exit=0, `#print axioms` = [propext, Quot.sound] (allowed only).

**RESULT:** Of 7 same-spec attacks, ONLY the gold-equivalent echo (atk_5) closes with clean axioms; its materialized faithful patch RESOLVED=True. All 6 genuinely-wrong impls (partial-domain, boundary, control-flow-effect, payload-clobber, reversal, un-deparented prepatch) FAIL to close — their spec obligations are provably false, not lazily sorried. No spec-closing-but-non-resolving impl exists.

REFINEMENT.MD / A-LEG AUDIT: meta.json confirms axioms=[], opaque_callees=[], deep_model_references=[], conf_skip=false. There are NO A-legs (no opaque callee, no `_prop` axiom, no deep-model reference) — the A-leg / correspondence audit is vacuous by construction. refinement.md rows 1-6 are all tagged R/I and correspond op-for-op to the gold edit (`old_children, self._children = self._children, []; for chld in old_children: chld.axes = chld.figure = None`): list snapshot->R, new []->R, iteration->I, two-field reset (axes+figure to none, other fields preserved)->R, accumulation->R, pair return->R. No kind-3 (inexpressible) leg. Chained attribute assignment sets exactly .axes/.figure to None and touches nothing else, matching the frame-discipline data=c.data conjunct. Correspondence holds.

**SCHEDULE NOTE:** attack lean_verify runs were launched concurrently as background Bash jobs, <=4 at a time (batch1: pos,atk_1,atk_2,atk_3; batch2: atk_4,atk_5,atk_6,atk_7; then axiom checks for pos+atk_5 concurrently). The single needed resolve (atk_5) completed with RESOLVED=True.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Preliminaries all pass. Solution.lean compiles clean (lean_verify exit 0). `#print axioms correct_clearAxes` => [propext, Quot.sound] — no sorryAx, proof is real. same_spec(Solution, Solution_prepatch, LeanBackend) = True (spec region byte-identical). Base commit 9d22ab09; gold patch confirmed from dataset: replaces `self._children = []` with `old_children, self._children = self._children, []; for chld in old_children: chld.axes = chld.figure = None`.

Modeled function = ([], artists.map deparent). Spec pins: result.1 = [] ∧ result.2.length = artists.length ∧ ∀ i<len, ∃ a c, result.2[i]?=some a ∧ artists[i]?=some c ∧ a.axes=none ∧ a.figure=none ∧ a.data=c.data.

Faithfulness check vs real callee, every observable dimension:
- new child list empty: real sets self.`_children`=[]. MATCH.
- former-children count/order: real iterates old_children in original order; count preserved. MATCH.
- axes/figure -> None: chained assignment sets exactly .axes and .figure to None on each former child. In mpl 3.6 these are properties but the setter only rejects re-parenting to a *different non-None* axes; assigning None is always permitted for every artist type. Resolve test test_cla_clears_children_axes_and_fig confirms art.axes is None and art.figure is None for Line2D + AxesImage after ax.clear(). MATCH.
- data (frame discipline): the a.data=c.data conjunct is NOT an over-strengthening — the gold loop touches ONLY .axes and .figure, leaving every other field untouched, so the real callee genuinely preserves all other state. MATCH.
- empty input: no iteration, `_children`=[]; spec length 0, result.1=[]. MATCH.

The spec is exactly the observable post-state of the real callee — neither too strong nor drifting. No diverging input exists within the modeled abstraction (identities abstracted to Nat, data as opaque Nat; abstraction is sound: real code never inspects or mutates identities/other-fields during deparenting). Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Solver-visible spec view (Solution.lean spec_view) discloses nothing beyond the public problem_statement. The problem_statement already states verbatim the gold behavior: 'cla(), clf() should unset the .axes and .figure attributes of deparented artists'. The spec-view docstring ('every former child artist is deparented — its owning axes and figure references are unset (set to none)') is a faithful restatement of that public task, not the edit. The gold discriminator is the per-child deparenting (chld.axes = chld.figure = None); the child-list reset self.`_children`=[] is pre-existing base-commit clear() behavior, not the fix. Checks performed: (1) mechanical leakage.screen() PASSES — no diff markers, no gold-patch line reproduced (>=8-char normalized), no patched file/module path, no narration words, no spec-view identifier or comment naming a distinctive patched symbol; the only changed symbol 'clear' is a substring of 'clearing' in problem_statement and thus already public. (2) same_spec(Solution.lean, Solution_prepatch.lean)=True — spec region byte-identical, so no gold information smuggled via the contract. (3) impl and proof regions are elided in the spec view. NOTE: refinement.md and mapping.md quote the gold patch verbatim, but those are auditor-side artifacts, not the consumer spec view screened by G-LEAK/panel-3. No leakage of the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
