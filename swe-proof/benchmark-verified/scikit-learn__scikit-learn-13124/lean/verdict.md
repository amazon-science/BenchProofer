# P2 adversarial audit — scikit-learn__scikit-learn-13124

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -79,15 +79,10 @@
     List (List Nat) := Id.run do
   if !shuffle then
     return counts.map (fun c => List.range (max c nFolds))
-  -- Obtain ONE generator from the seed and keep it as we go.
-  let mut st : RngState := seedState seed
   let mut orders : List (List Nat) := []
   for c in counts do
-    -- Shuffle this class's index range with the current generator, then carry
-    -- the advanced generator forward to the next class.
-    let res := shuffleN st (max c nFolds)
+    let res := shuffleN (seedState seed) (max c nFolds)
     orders := orders ++ [res.1]
-    st := res.2
   return orders
 -- impl-end
 
@@ -99,47 +94,5 @@
         (implementation_classOrders seed shuffle nFolds counts) := by
   intro seed shuffle nFolds counts
   unfold problem_spec_classOrders implementation_classOrders
-  cases shuffle
-  · simp only [Id.run]; rfl
-  · simp only [Id.run, Bool.not_true, Bool.false_eq_true, reduceIte]
-    -- goal: the forIn loop equals perClassShuffleOrders
-    -- generalize the accumulator and state
-    suffices h : ∀ (cs : List Nat) (st : RngState) (acc : List (List Nat)),
-        (forIn (m := Id) cs (⟨acc, st⟩ : MProd (List (List Nat)) RngState)
-          (fun c r =>
-            (do
-              pure PUnit.unit
-              pure (ForInStep.yield (⟨r.fst ++ [(shuffleN r.snd (max c nFolds)).1],
-                (shuffleN r.snd (max c nFolds)).2⟩ : MProd (List (List Nat)) RngState))))).fst
-          = acc ++ perClassShuffleOrders nFolds cs st by
-      have := h counts (seedState seed) []
-      simpa using this
-    intro cs
-    induction cs with
-    | nil => intro st acc; simp only [List.forIn_nil, perClassShuffleOrders, List.append_nil]; rfl
-    | cons c cs ih =>
-      intro st acc
-      simp only [List.forIn_cons, perClassShuffleOrders]
-      simp only [bind_pure_comp, map_pure, pure_bind] at *
-      rw [ih]
-      simp [List.append_assoc]
-
-/-- The spec is DETERMINISTIC: `problem_spec_classOrders` pins `result` by an
-EXACT equality to a total function of the inputs, so ANY result satisfying it
-equals `implementation_classOrders`. Consequently no observably wrong same-spec
-implementation can verify — a same-spec implementation whose `correct_` closes
-is extensionally the gold (threaded-generator) behavior. In particular a
-gold-equivalent restatement of the implementation (e.g. one returning the
-spec's right-hand side directly) is a POSITIVE CONTROL, not a spec-too-weak
-counterexample: its faithful refined patch is the gold patch and resolves. -/
-theorem spec_classOrders_deterministic :
-    ∀ (seed : Nat) (shuffle : Bool) (nFolds : Nat) (counts : List Nat)
-      (r : List (List Nat)),
-      problem_spec_classOrders seed shuffle nFolds counts r →
-        r = implementation_classOrders seed shuffle nFolds counts := by
-  intro seed shuffle nFolds counts r h
-  have h2 := correct_classOrders seed shuffle nFolds counts
-  unfold problem_spec_classOrders at h h2
-  rw [h, h2]
-
+  cases shuffle <;> simp_all [Id.run] <;> rfl
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -78,14 +78,11 @@
     (seed : Nat) (shuffle : Bool) (nFolds : Nat) (counts : List Nat) :
     List (List Nat) := Id.run do
   if !shuffle then
-    return counts.map (fun c => List.range (max c nFolds))
-  -- Obtain ONE generator from the seed and keep it as we go.
+    return counts.map (fun c => List.range c)
   let mut st : RngState := seedState seed
   let mut orders : List (List Nat) := []
   for c in counts do
-    -- Shuffle this class's index range with the current generator, then carry
-    -- the advanced generator forward to the next class.
-    let res := shuffleN st (max c nFolds)
+    let res := shuffleN st c
     orders := orders ++ [res.1]
     st := res.2
   return orders
@@ -99,47 +96,5 @@
         (implementation_classOrders seed shuffle nFolds counts) := by
   intro seed shuffle nFolds counts
   unfold problem_spec_classOrders implementation_classOrders
-  cases shuffle
-  · simp only [Id.run]; rfl
-  · simp only [Id.run, Bool.not_true, Bool.false_eq_true, reduceIte]
-    -- goal: the forIn loop equals perClassShuffleOrders
-    -- generalize the accumulator and state
-    suffices h : ∀ (cs : List Nat) (st : RngState) (acc : List (List Nat)),
-        (forIn (m := Id) cs (⟨acc, st⟩ : MProd (List (List Nat)) RngState)
-          (fun c r =>
-            (do
-              pure PUnit.unit
-              pure (ForInStep.yield (⟨r.fst ++ [(shuffleN r.snd (max c nFolds)).1],
-                (shuffleN r.snd (max c nFolds)).2⟩ : MProd (List (List Nat)) RngState))))).fst
-          = acc ++ perClassShuffleOrders nFolds cs st by
-      have := h counts (seedState seed) []
-      simpa using this
-    intro cs
-    induction cs with
-    | nil => intro st acc; simp only [List.forIn_nil, perClassShuffleOrders, List.append_nil]; rfl
-    | cons c cs ih =>
-      intro st acc
-      simp only [List.forIn_cons, perClassShuffleOrders]
-      simp only [bind_pure_comp, map_pure, pure_bind] at *
-      rw [ih]
-      simp [List.append_assoc]
-
-/-- The spec is DETERMINISTIC: `problem_spec_classOrders` pins `result` by an
-EXACT equality to a total function of the inputs, so ANY result satisfying it
-equals `implementation_classOrders`. Consequently no observably wrong same-spec
-implementation can verify — a same-spec implementation whose `correct_` closes
-is extensionally the gold (threaded-generator) behavior. In particular a
-gold-equivalent restatement of the implementation (e.g. one returning the
-spec's right-hand side directly) is a POSITIVE CONTROL, not a spec-too-weak
-counterexample: its faithful refined patch is the gold patch and resolves. -/
-theorem spec_classOrders_deterministic :
-    ∀ (seed : Nat) (shuffle : Bool) (nFolds : Nat) (counts : List Nat)
-      (r : List (List Nat)),
-      problem_spec_classOrders seed shuffle nFolds counts r →
-        r = implementation_classOrders seed shuffle nFolds counts := by
-  intro seed shuffle nFolds counts r h
-  have h2 := correct_classOrders seed shuffle nFolds counts
-  unfold problem_spec_classOrders at h h2
-  rw [h, h2]
-
+  cases shuffle <;> simp_all [Id.run] <;> rfl
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -79,14 +79,11 @@
     List (List Nat) := Id.run do
   if !shuffle then
     return counts.map (fun c => List.range (max c nFolds))
-  -- Obtain ONE generator from the seed and keep it as we go.
   let mut st : RngState := seedState seed
   let mut orders : List (List Nat) := []
   for c in counts do
-    -- Shuffle this class's index range with the current generator, then carry
-    -- the advanced generator forward to the next class.
     let res := shuffleN st (max c nFolds)
-    orders := orders ++ [res.1]
+    orders := [res.1] ++ orders
     st := res.2
   return orders
 -- impl-end
@@ -99,47 +96,5 @@
         (implementation_classOrders seed shuffle nFolds counts) := by
   intro seed shuffle nFolds counts
   unfold problem_spec_classOrders implementation_classOrders
-  cases shuffle
-  · simp only [Id.run]; rfl
-  · simp only [Id.run, Bool.not_true, Bool.false_eq_true, reduceIte]
-    -- goal: the forIn loop equals perClassShuffleOrders
-    -- generalize the accumulator and state
-    suffices h : ∀ (cs : List Nat) (st : RngState) (acc : List (List Nat)),
-        (forIn (m := Id) cs (⟨acc, st⟩ : MProd (List (List Nat)) RngState)
-          (fun c r =>
-            (do
-              pure PUnit.unit
-              pure (ForInStep.yield (⟨r.fst ++ [(shuffleN r.snd (max c nFolds)).1],
-                (shuffleN r.snd (max c nFolds)).2⟩ : MProd (List (List Nat)) RngState))))).fst
-          = acc ++ perClassShuffleOrders nFolds cs st by
-      have := h counts (seedState seed) []
-      simpa using this
-    intro cs
-    induction cs with
-    | nil => intro st acc; simp only [List.forIn_nil, perClassShuffleOrders, List.append_nil]; rfl
-    | cons c cs ih =>
-      intro st acc
-      simp only [List.forIn_cons, perClassShuffleOrders]
-      simp only [bind_pure_comp, map_pure, pure_bind] at *
-      rw [ih]
-      simp [List.append_assoc]
-
-/-- The spec is DETERMINISTIC: `problem_spec_classOrders` pins `result` by an
-EXACT equality to a total function of the inputs, so ANY result satisfying it
-equals `implementation_classOrders`. Consequently no observably wrong same-spec
-implementation can verify — a same-spec implementation whose `correct_` closes
-is extensionally the gold (threaded-generator) behavior. In particular a
-gold-equivalent restatement of the implementation (e.g. one returning the
-spec's right-hand side directly) is a POSITIVE CONTROL, not a spec-too-weak
-counterexample: its faithful refined patch is the gold patch and resolves. -/
-theorem spec_classOrders_deterministic :
-    ∀ (seed : Nat) (shuffle : Bool) (nFolds : Nat) (counts : List Nat)
-      (r : List (List Nat)),
-      problem_spec_classOrders seed shuffle nFolds counts r →
-        r = implementation_classOrders seed shuffle nFolds counts := by
-  intro seed shuffle nFolds counts r h
-  have h2 := correct_classOrders seed shuffle nFolds counts
-  unfold problem_spec_classOrders at h h2
-  rw [h, h2]
-
+  cases shuffle <;> simp_all [Id.run] <;> rfl
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -79,12 +79,9 @@
     List (List Nat) := Id.run do
   if !shuffle then
     return counts.map (fun c => List.range (max c nFolds))
-  -- Obtain ONE generator from the seed and keep it as we go.
   let mut st : RngState := seedState seed
   let mut orders : List (List Nat) := []
-  for c in counts do
-    -- Shuffle this class's index range with the current generator, then carry
-    -- the advanced generator forward to the next class.
+  for c in counts.tail do
     let res := shuffleN st (max c nFolds)
     orders := orders ++ [res.1]
     st := res.2
@@ -99,47 +96,5 @@
         (implementation_classOrders seed shuffle nFolds counts) := by
   intro seed shuffle nFolds counts
   unfold problem_spec_classOrders implementation_classOrders
-  cases shuffle
-  · simp only [Id.run]; rfl
-  · simp only [Id.run, Bool.not_true, Bool.false_eq_true, reduceIte]
-    -- goal: the forIn loop equals perClassShuffleOrders
-    -- generalize the accumulator and state
-    suffices h : ∀ (cs : List Nat) (st : RngState) (acc : List (List Nat)),
-        (forIn (m := Id) cs (⟨acc, st⟩ : MProd (List (List Nat)) RngState)
-          (fun c r =>
-            (do
-              pure PUnit.unit
-              pure (ForInStep.yield (⟨r.fst ++ [(shuffleN r.snd (max c nFolds)).1],
-                (shuffleN r.snd (max c nFolds)).2⟩ : MProd (List (List Nat)) RngState))))).fst
-          = acc ++ perClassShuffleOrders nFolds cs st by
-      have := h counts (seedState seed) []
-      simpa using this
-    intro cs
-    induction cs with
-    | nil => intro st acc; simp only [List.forIn_nil, perClassShuffleOrders, List.append_nil]; rfl
-    | cons c cs ih =>
-      intro st acc
-      simp only [List.forIn_cons, perClassShuffleOrders]
-      simp only [bind_pure_comp, map_pure, pure_bind] at *
-      rw [ih]
-      simp [List.append_assoc]
-
-/-- The spec is DETERMINISTIC: `problem_spec_classOrders` pins `result` by an
-EXACT equality to a total function of the inputs, so ANY result satisfying it
-equals `implementation_classOrders`. Consequently no observably wrong same-spec
-implementation can verify — a same-spec implementation whose `correct_` closes
-is extensionally the gold (threaded-generator) behavior. In particular a
-gold-equivalent restatement of the implementation (e.g. one returning the
-spec's right-hand side directly) is a POSITIVE CONTROL, not a spec-too-weak
-counterexample: its faithful refined patch is the gold patch and resolves. -/
-theorem spec_classOrders_deterministic :
-    ∀ (seed : Nat) (shuffle : Bool) (nFolds : Nat) (counts : List Nat)
-      (r : List (List Nat)),
-      problem_spec_classOrders seed shuffle nFolds counts r →
-        r = implementation_classOrders seed shuffle nFolds counts := by
-  intro seed shuffle nFolds counts r h
-  have h2 := correct_classOrders seed shuffle nFolds counts
-  unfold problem_spec_classOrders at h h2
-  rw [h, h2]
-
+  cases shuffle <;> simp_all [Id.run] <;> rfl
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -76,19 +76,8 @@
 -- impl-start
 def implementation_classOrders
     (seed : Nat) (shuffle : Bool) (nFolds : Nat) (counts : List Nat) :
-    List (List Nat) := Id.run do
-  if !shuffle then
-    return counts.map (fun c => List.range (max c nFolds))
-  -- Obtain ONE generator from the seed and keep it as we go.
-  let mut st : RngState := seedState seed
-  let mut orders : List (List Nat) := []
-  for c in counts do
-    -- Shuffle this class's index range with the current generator, then carry
-    -- the advanced generator forward to the next class.
-    let res := shuffleN st (max c nFolds)
-    orders := orders ++ [res.1]
-    st := res.2
-  return orders
+    List (List Nat) :=
+  counts.map (fun c => List.range (max c nFolds))
 -- impl-end
 
 
@@ -99,47 +88,5 @@
         (implementation_classOrders seed shuffle nFolds counts) := by
   intro seed shuffle nFolds counts
   unfold problem_spec_classOrders implementation_classOrders
-  cases shuffle
-  · simp only [Id.run]; rfl
-  · simp only [Id.run, Bool.not_true, Bool.false_eq_true, reduceIte]
-    -- goal: the forIn loop equals perClassShuffleOrders
-    -- generalize the accumulator and state
-    suffices h : ∀ (cs : List Nat) (st : RngState) (acc : List (List Nat)),
-        (forIn (m := Id) cs (⟨acc, st⟩ : MProd (List (List Nat)) RngState)
-          (fun c r =>
-            (do
-              pure PUnit.unit
-              pure (ForInStep.yield (⟨r.fst ++ [(shuffleN r.snd (max c nFolds)).1],
-                (shuffleN r.snd (max c nFolds)).2⟩ : MProd (List (List Nat)) RngState))))).fst
-          = acc ++ perClassShuffleOrders nFolds cs st by
-      have := h counts (seedState seed) []
-      simpa using this
-    intro cs
-    induction cs with
-    | nil => intro st acc; simp only [List.forIn_nil, perClassShuffleOrders, List.append_nil]; rfl
-    | cons c cs ih =>
-      intro st acc
-      simp only [List.forIn_cons, perClassShuffleOrders]
-      simp only [bind_pure_comp, map_pure, pure_bind] at *
-      rw [ih]
-      simp [List.append_assoc]
-
-/-- The spec is DETERMINISTIC: `problem_spec_classOrders` pins `result` by an
-EXACT equality to a total function of the inputs, so ANY result satisfying it
-equals `implementation_classOrders`. Consequently no observably wrong same-spec
-implementation can verify — a same-spec implementation whose `correct_` closes
-is extensionally the gold (threaded-generator) behavior. In particular a
-gold-equivalent restatement of the implementation (e.g. one returning the
-spec's right-hand side directly) is a POSITIVE CONTROL, not a spec-too-weak
-counterexample: its faithful refined patch is the gold patch and resolves. -/
-theorem spec_classOrders_deterministic :
-    ∀ (seed : Nat) (shuffle : Bool) (nFolds : Nat) (counts : List Nat)
-      (r : List (List Nat)),
-      problem_spec_classOrders seed shuffle nFolds counts r →
-        r = implementation_classOrders seed shuffle nFolds counts := by
-  intro seed shuffle nFolds counts r h
-  have h2 := correct_classOrders seed shuffle nFolds counts
-  unfold problem_spec_classOrders at h h2
-  rw [h, h2]
-
+  cases shuffle <;> simp_all [Id.run] <;> rfl
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -79,13 +79,10 @@
     List (List Nat) := Id.run do
   if !shuffle then
     return counts.map (fun c => List.range (max c nFolds))
-  -- Obtain ONE generator from the seed and keep it as we go.
   let mut st : RngState := seedState seed
   let mut orders : List (List Nat) := []
-  for c in counts do
-    -- Shuffle this class's index range with the current generator, then carry
-    -- the advanced generator forward to the next class.
-    let res := shuffleN st (max c nFolds)
+  for _c in counts do
+    let res := shuffleN st nFolds
     orders := orders ++ [res.1]
     st := res.2
   return orders
@@ -99,47 +96,5 @@
         (implementation_classOrders seed shuffle nFolds counts) := by
   intro seed shuffle nFolds counts
   unfold problem_spec_classOrders implementation_classOrders
-  cases shuffle
-  · simp only [Id.run]; rfl
-  · simp only [Id.run, Bool.not_true, Bool.false_eq_true, reduceIte]
-    -- goal: the forIn loop equals perClassShuffleOrders
-    -- generalize the accumulator and state
-    suffices h : ∀ (cs : List Nat) (st : RngState) (acc : List (List Nat)),
-        (forIn (m := Id) cs (⟨acc, st⟩ : MProd (List (List Nat)) RngState)
-          (fun c r =>
-            (do
-              pure PUnit.unit
-              pure (ForInStep.yield (⟨r.fst ++ [(shuffleN r.snd (max c nFolds)).1],
-                (shuffleN r.snd (max c nFolds)).2⟩ : MProd (List (List Nat)) RngState))))).fst
-          = acc ++ perClassShuffleOrders nFolds cs st by
-      have := h counts (seedState seed) []
-      simpa using this
-    intro cs
-    induction cs with
-    | nil => intro st acc; simp only [List.forIn_nil, perClassShuffleOrders, List.append_nil]; rfl
-    | cons c cs ih =>
-      intro st acc
-      simp only [List.forIn_cons, perClassShuffleOrders]
-      simp only [bind_pure_comp, map_pure, pure_bind] at *
-      rw [ih]
-      simp [List.append_assoc]
-
-/-- The spec is DETERMINISTIC: `problem_spec_classOrders` pins `result` by an
-EXACT equality to a total function of the inputs, so ANY result satisfying it
-equals `implementation_classOrders`. Consequently no observably wrong same-spec
-implementation can verify — a same-spec implementation whose `correct_` closes
-is extensionally the gold (threaded-generator) behavior. In particular a
-gold-equivalent restatement of the implementation (e.g. one returning the
-spec's right-hand side directly) is a POSITIVE CONTROL, not a spec-too-weak
-counterexample: its faithful refined patch is the gold patch and resolves. -/
-theorem spec_classOrders_deterministic :
-    ∀ (seed : Nat) (shuffle : Bool) (nFolds : Nat) (counts : List Nat)
-      (r : List (List Nat)),
-      problem_spec_classOrders seed shuffle nFolds counts r →
-        r = implementation_classOrders seed shuffle nFolds counts := by
-  intro seed shuffle nFolds counts r h
-  have h2 := correct_classOrders seed shuffle nFolds counts
-  unfold problem_spec_classOrders at h h2
-  rw [h, h2]
-
+  cases shuffle <;> simp_all [Id.run] <;> rfl
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -79,15 +79,11 @@
     List (List Nat) := Id.run do
   if !shuffle then
     return counts.map (fun c => List.range (max c nFolds))
-  -- Obtain ONE generator from the seed and keep it as we go.
-  let mut st : RngState := seedState seed
+  let st : RngState := seedState seed
   let mut orders : List (List Nat) := []
   for c in counts do
-    -- Shuffle this class's index range with the current generator, then carry
-    -- the advanced generator forward to the next class.
     let res := shuffleN st (max c nFolds)
     orders := orders ++ [res.1]
-    st := res.2
   return orders
 -- impl-end
 
@@ -99,47 +95,5 @@
         (implementation_classOrders seed shuffle nFolds counts) := by
   intro seed shuffle nFolds counts
   unfold problem_spec_classOrders implementation_classOrders
-  cases shuffle
-  · simp only [Id.run]; rfl
-  · simp only [Id.run, Bool.not_true, Bool.false_eq_true, reduceIte]
-    -- goal: the forIn loop equals perClassShuffleOrders
-    -- generalize the accumulator and state
-    suffices h : ∀ (cs : List Nat) (st : RngState) (acc : List (List Nat)),
-        (forIn (m := Id) cs (⟨acc, st⟩ : MProd (List (List Nat)) RngState)
-          (fun c r =>
-            (do
-              pure PUnit.unit
-              pure (ForInStep.yield (⟨r.fst ++ [(shuffleN r.snd (max c nFolds)).1],
-                (shuffleN r.snd (max c nFolds)).2⟩ : MProd (List (List Nat)) RngState))))).fst
-          = acc ++ perClassShuffleOrders nFolds cs st by
-      have := h counts (seedState seed) []
-      simpa using this
-    intro cs
-    induction cs with
-    | nil => intro st acc; simp only [List.forIn_nil, perClassShuffleOrders, List.append_nil]; rfl
-    | cons c cs ih =>
-      intro st acc
-      simp only [List.forIn_cons, perClassShuffleOrders]
-      simp only [bind_pure_comp, map_pure, pure_bind] at *
-      rw [ih]
-      simp [List.append_assoc]
-
-/-- The spec is DETERMINISTIC: `problem_spec_classOrders` pins `result` by an
-EXACT equality to a total function of the inputs, so ANY result satisfying it
-equals `implementation_classOrders`. Consequently no observably wrong same-spec
-implementation can verify — a same-spec implementation whose `correct_` closes
-is extensionally the gold (threaded-generator) behavior. In particular a
-gold-equivalent restatement of the implementation (e.g. one returning the
-spec's right-hand side directly) is a POSITIVE CONTROL, not a spec-too-weak
-counterexample: its faithful refined patch is the gold patch and resolves. -/
-theorem spec_classOrders_deterministic :
-    ∀ (seed : Nat) (shuffle : Bool) (nFolds : Nat) (counts : List Nat)
-      (r : List (List Nat)),
-      problem_spec_classOrders seed shuffle nFolds counts r →
-        r = implementation_classOrders seed shuffle nFolds counts := by
-  intro seed shuffle nFolds counts r h
-  have h2 := correct_classOrders seed shuffle nFolds counts
-  unfold problem_spec_classOrders at h h2
-  rw [h, h2]
-
+  cases shuffle <;> simp_all [Id.run] <;> rfl
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Producing, for a stratified k-fold split, the ORDER in which each class's own
samples are arranged before they are handed out to the folds.

A stratified split treats each class independently: every class has a number of
samples, and that class's local index range is laid out in some order; a per-class
fold splitter then deals those positions out to the folds, preserving the class
balance. This file models how those per-class orders are produced from
  (a seed, whether shuffling is on, the number of folds, the per-class counts)
      ↦ the list of orders, one per class.

* When shuffling is OFF, every class keeps its natural ascending order.
* When shuffling is ON, each class's index range is shuffled. The orders are
  drawn from a SINGLE source of randomness, consumed once per class in class
  order, so that source carries forward from each class to the next. The
  intended, observable consequence is that distinct classes generally receive
  distinct orders, and two distinct seeds generally yield distinct overall
  collections of orders — rather than every class being arranged identically and
  the seed having no real effect.

Each class's index range spans `max(count, n_folds)` positions, matching the
range the per-class fold splitter operates over. The implementation and the
correctness proof are supplied separately.
-/

-- axioms-start
-- The source of randomness is an UNCHANGED routine: a seeded random generator
-- whose internal numeric behavior is irrelevant to what this file pins. We take
-- it OPAQUELY through two signatures — initialising the generator from a seed,
-- and consuming it once to obtain an order of `n` positions together with the
-- generator advanced past that draw. No property of these is asserted (no
-- `_prop` axiom is consumed); the whole point pinned here is the structural way
-- the single generator is THREADED across the classes, which holds for any such
-- generator. Behavioural agreement with the real generator is checked by G-CONF.
abbrev RngState := Nat

/-- Initialise the random generator from an integer seed. -/
opaque seedState : Nat → RngState

/-- Consume the generator once: arrange `n` positions into an order and return
that order together with the generator advanced past this draw. -/
opaque shuffleN : RngState → Nat → (List Nat × RngState)
-- axioms-end

-- pure-start
/-- The orders produced when shuffling is ON, stated front-recursively: the
single generator state `st` is threaded through the classes in order. The first
class consumes `st` (obtaining its order and the advanced state), and every later
class consumes the state left by its predecessor. -/
def perClassShuffleOrders (nFolds : Nat) : List Nat → RngState → List (List Nat)
  | [], _ => []
  | c :: cs, st =>
    let res := shuffleN st (max c nFolds)
    res.1 :: perClassShuffleOrders nFolds cs res.2
-- pure-end

-- post-conditions-start
/-- The result is exactly the per-class orders dictated by the rule:
* shuffling OFF — each class keeps its natural ascending order over
  `max(count, n_folds)` positions;
* shuffling ON — the orders threaded from a single generator seeded by `seed`,
  consumed once per class in class order (`perClassShuffleOrders`). -/
def problem_spec_classOrders
    (seed : Nat) (shuffle : Bool) (nFolds : Nat) (counts : List Nat)
    (result : List (List Nat)) : Prop :=
  result =
    (if shuffle then
      perClassShuffleOrders nFolds counts (seedState seed)
     else
      counts.map (fun c => List.range (max c nFolds)))
-- post-conditions-end

-- impl-start
def implementation_classOrders
    (seed : Nat) (shuffle : Bool) (nFolds : Nat) (counts : List Nat) :
    List (List Nat) :=
  if shuffle then
    perClassShuffleOrders nFolds counts (seedState seed)
  else
    counts.map (fun c => List.range (max c nFolds))
-- impl-end


-- proof-start
theorem correct_classOrders :
    ∀ (seed : Nat) (shuffle : Bool) (nFolds : Nat) (counts : List Nat),
      problem_spec_classOrders seed shuffle nFolds counts
        (implementation_classOrders seed shuffle nFolds counts) := by
  intro seed shuffle nFolds counts
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec `problem_spec_classOrders` pins `result` by EXACT equality to a total function of the inputs (if shuffle then perClassShuffleOrders nFolds counts (seedState seed) else counts.map (fun c => List.range (max c nFolds))). It is deterministic: `spec_classOrders_deterministic` (in Solution.lean, axioms [propext, Quot.sound]) proves any r satisfying the spec equals implementation_classOrders. Therefore NO observably-wrong same-spec impl can close correct_classOrders, and step-2 resolve-materialization has no candidates (no wrong impl verifies) => patches={}.

Same_spec=True verified for all 8 files (pos + 7 attacks) via swebench_unified.markers.same_spec on LeanBackend — spec/axioms/pure/pre/post regions byte-identical, only impl+proof edited.

 Verify command: `bash scripts/lean_verify.sh <file>`.

### RESULTS (each attack verified; concurrent batches of <=4):
- pos.lean (POSITIVE CONTROL, gold-equivalent restatement returning spec RHS directly, proof `intro; rfl`): exit=0 VERIFIES. `#print axioms correct_classOrders` => 'does not depend on any axioms' (clean, no sorryAx, no _prop). This is the determinism-lemma-sanctioned oracle-echo positive control, NOT a counterexample; its faithful refined patch is the gold patch (RESOLVED per prior round).
- atk_1.lean (prepatch bug: re-seed `shuffleN (seedState seed) (max c nFolds)` per class, no threading): exit=1, `rfl` failed — output != spec RHS. This reproduces the actual bug (equal-length classes get identical orders); its faithful patch is the prepatch (buggy), which does NOT resolve — correctly does NOT verify, so cannot break the spec.
- atk_2.lean (boundary: uses `c`/`shuffleN st c` instead of `max c nFolds`, drops fold-floor): exit=1, rfl failed.
- atk_3.lean (control-flow-effect: prepend `[res.1] ++ orders` => reversed order list): exit=1, rfl failed.
- atk_4.lean (partial-domain: iterates `counts.tail`, drops first class): exit=1, rfl failed.
- atk_5.lean (ungrounded-oracle echo: returns `counts.map (fun c => List.range (max c nFolds))` unconditionally, ignoring shuffle=True): exit=1, rfl failed.
- atk_6.lean (wrong draw width: `shuffleN st nFolds` ignores per-class count): exit=1, rfl failed.
- atk_7.lean (no-advance non-threading: threads a `let st` but never carries res.2 forward): exit=1, rfl failed.

All 7 wrong impls FAIL to close correct_classOrders (rfl mismatch: their output is not the spec's exact RHS). None closes with clean axioms => zero candidates require the resolve step => no verify⇏correct gap. prepatch_reproduced=true (atk_1 = Solution_prepatch behavior, fails as expected).

Refinement.md A-leg audit: legs tagged R (1,4,6,8), I (3), A-reference (2,5,7). seedState = real sklearn check_random_state on int seed; shuffleN = real np.arange + numpy.random.RandomState.shuffle returning order + advanced generator. Both taken OPAQUELY (opaque decls), spec asserts NO numeric property (no `_prop` axiom consumed) => G-AX legitimately skips; there is NO kind-3 dead axiom. correct_classOrders and spec_classOrders_deterministic both #print axioms = [propext, Quot.sound] (genuine, no sorryAx). A-reference correspondence to real callees (check_random_state / RandomState.shuffle threading) validated by G-CONF (120009 configs, fix_disagreements=0; prepatch negative control distinguished on 55617). Model↔patch correspondence holds: the modeled threading (st carried forward) exactly mirrors the gold one-line fix `rng = self.random_state` -> `rng = check_random_state(self.random_state)`.

Verdict SOUND: >=5 distinct same-spec wrong impls attempted; none closes; positive control verifies with clean axioms.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Producing, for a stratified k-fold split, the ORDER in which each class's own
samples are arranged before they are handed out to the folds.

A stratified split treats each class independently: every class has a number of
samples, and that class's local index range is laid out in some order; a per-class
fold splitter then deals those positions out to the folds, preserving the class
balance. This file models how those per-class orders are produced from
  (a seed, whether shuffling is on, the number of folds, the per-class counts)
      ↦ the list of orders, one per class.

* When shuffling is OFF, every class keeps its natural ascending order.
* When shuffling is ON, each class's index range is shuffled. The orders are
  drawn from a SINGLE source of randomness, consumed once per class in class
  order, so that source carries forward from each class to the next. The
  intended, observable consequence is that distinct classes generally receive
  distinct orders, and two distinct seeds generally yield distinct overall
  collections of orders — rather than every class being arranged identically and
  the seed having no real effect.

Each class's index range spans `max(count, n_folds)` positions, matching the
range the per-class fold splitter operates over. The implementation and the
correctness proof are supplied separately.
-/

-- axioms-start
-- The source of randomness is an UNCHANGED routine: a seeded random generator
-- whose internal numeric behavior is irrelevant to what this file pins. We take
-- it OPAQUELY through two signatures — initialising the generator from a seed,
-- and consuming it once to obtain an order of `n` positions together with the
-- generator advanced past that draw. No property of these is asserted (no
-- `_prop` axiom is consumed); the whole point pinned here is the structural way
-- the single generator is THREADED across the classes, which holds for any such
-- generator. Behavioural agreement with the real generator is checked by G-CONF.
abbrev RngState := Nat

/-- Initialise the random generator from an integer seed. -/
opaque seedState : Nat → RngState

/-- Consume the generator once: arrange `n` positions into an order and return
that order together with the generator advanced past this draw. -/
opaque shuffleN : RngState → Nat → (List Nat × RngState)
-- axioms-end

-- pure-start
/-- The orders produced when shuffling is ON, stated front-recursively: the
single generator state `st` is threaded through the classes in order. The first
class consumes `st` (obtaining its order and the advanced state), and every later
class consumes the state left by its predecessor. -/
def perClassShuffleOrders (nFolds : Nat) : List Nat → RngState → List (List Nat)
  | [], _ => []
  | c :: cs, st =>
    let res := shuffleN st (max c nFolds)
    res.1 :: perClassShuffleOrders nFolds cs res.2
-- pure-end

-- post-conditions-start
/-- The result is exactly the per-class orders dictated by the rule:
* shuffling OFF — each class keeps its natural ascending order over
  `max(count, n_folds)` positions;
* shuffling ON — the orders threaded from a single generator seeded by `seed`,
  consumed once per class in class order (`perClassShuffleOrders`). -/
def problem_spec_classOrders
    (seed : Nat) (shuffle : Bool) (nFolds : Nat) (counts : List Nat)
    (result : List (List Nat)) : Prop :=
  result =
    (if shuffle then
      perClassShuffleOrders nFolds counts (seedState seed)
     else
      counts.map (fun c => List.range (max c nFolds)))
-- post-conditions-end

-- impl-start
def implementation_classOrders
    (seed : Nat) (shuffle : Bool) (nFolds : Nat) (counts : List Nat) :
    List (List Nat) :=
  if shuffle then
    perClassShuffleOrders nFolds counts (seedState seed)
  else
    counts.map (fun c => List.range (max c nFolds))
-- impl-end


-- proof-start
theorem correct_classOrders :
    ∀ (seed : Nat) (shuffle : Bool) (nFolds : Nat) (counts : List Nat),
      problem_spec_classOrders seed shuffle nFolds counts
        (implementation_classOrders seed shuffle nFolds counts) := by
  intro seed shuffle nFolds counts
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec `problem_spec_classOrders` pins `result` by EXACT equality to a total function of the inputs (if shuffle then perClassShuffleOrders nFolds counts (seedState seed) else counts.map (fun c => List.range (max c nFolds))). It is deterministic: `spec_classOrders_deterministic` (in Solution.lean, axioms [propext, Quot.sound]) proves any r satisfying the spec equals implementation_classOrders. Therefore NO observably-wrong same-spec impl can close correct_classOrders, and step-2 resolve-materialization has no candidates (no wrong impl verifies) => patches={}.

Same_spec=True verified for all 8 files (pos + 7 attacks) via swebench_unified.markers.same_spec on LeanBackend — spec/axioms/pure/pre/post regions byte-identical, only impl+proof edited.

 Verify command: `bash scripts/lean_verify.sh <file>`.

### RESULTS (each attack verified; concurrent batches of <=4):
- pos.lean (POSITIVE CONTROL, gold-equivalent restatement returning spec RHS directly, proof `intro; rfl`): exit=0 VERIFIES. `#print axioms correct_classOrders` => 'does not depend on any axioms' (clean, no sorryAx, no _prop). This is the determinism-lemma-sanctioned oracle-echo positive control, NOT a counterexample; its faithful refined patch is the gold patch (RESOLVED per prior round).
- atk_1.lean (prepatch bug: re-seed `shuffleN (seedState seed) (max c nFolds)` per class, no threading): exit=1, `rfl` failed — output != spec RHS. This reproduces the actual bug (equal-length classes get identical orders); its faithful patch is the prepatch (buggy), which does NOT resolve — correctly does NOT verify, so cannot break the spec.
- atk_2.lean (boundary: uses `c`/`shuffleN st c` instead of `max c nFolds`, drops fold-floor): exit=1, rfl failed.
- atk_3.lean (control-flow-effect: prepend `[res.1] ++ orders` => reversed order list): exit=1, rfl failed.
- atk_4.lean (partial-domain: iterates `counts.tail`, drops first class): exit=1, rfl failed.
- atk_5.lean (ungrounded-oracle echo: returns `counts.map (fun c => List.range (max c nFolds))` unconditionally, ignoring shuffle=True): exit=1, rfl failed.
- atk_6.lean (wrong draw width: `shuffleN st nFolds` ignores per-class count): exit=1, rfl failed.
- atk_7.lean (no-advance non-threading: threads a `let st` but never carries res.2 forward): exit=1, rfl failed.

All 7 wrong impls FAIL to close correct_classOrders (rfl mismatch: their output is not the spec's exact RHS). None closes with clean axioms => zero candidates require the resolve step => no verify⇏correct gap. prepatch_reproduced=true (atk_1 = Solution_prepatch behavior, fails as expected).

Refinement.md A-leg audit: legs tagged R (1,4,6,8), I (3), A-reference (2,5,7). seedState = real sklearn check_random_state on int seed; shuffleN = real np.arange + numpy.random.RandomState.shuffle returning order + advanced generator. Both taken OPAQUELY (opaque decls), spec asserts NO numeric property (no `_prop` axiom consumed) => G-AX legitimately skips; there is NO kind-3 dead axiom. correct_classOrders and spec_classOrders_deterministic both #print axioms = [propext, Quot.sound] (genuine, no sorryAx). A-reference correspondence to real callees (check_random_state / RandomState.shuffle threading) validated by G-CONF (120009 configs, fix_disagreements=0; prepatch negative control distinguished on 55617). Model↔patch correspondence holds: the modeled threading (st carried forward) exactly mirrors the gold one-line fix `rng = self.random_state` -> `rng = check_random_state(self.random_state)`.

Verdict SOUND: >=5 distinct same-spec wrong impls attempted; none closes; positive control verifies with clean axioms.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for scikit-learn__scikit-learn-13124 (lean). Verdict: FAITHFUL — no diverging input found.

What the model pins: problem_spec_classOrders equates result to (if shuffle then perClassShuffleOrders nFolds counts (seedState seed) else counts.map (fun c => List.range (max c nFolds))). The RNG is taken OPAQUELY (opaque seedState : Nat→RngState, opaque shuffleN : RngState→Nat→(List Nat × RngState)); NO numeric property of the generator is asserted (axioms clean: [propext, Quot.sound], no _prop). perClassShuffleOrders threads a single seeded generator through the classes in class order, consuming it once per class over max(count,nFolds) positions.

Real callee @ base_commit 9f0b959 (verified via git show ...:sklearn/model_selection/_split.py):
- POST-patch _make_test_folds: rng = check_random_state(self.random_state) → one RandomState instance; per_cls_cvs builds KFold(shuffle=self.shuffle, random_state=rng).split(np.zeros(max(count,n_splits))) per class, consumed lazily by zip(*per_cls_cvs) in class order; each KFold._iter_test_indices does indices=np.arange(max(count,n_splits)); check_random_state(rng).shuffle(indices), which returns the SAME instance and advances it → single generator threaded in class order.
- OFF: arange(max(count,n_splits)) unshuffled = List.range (max c nFolds). Matches.

Verification performed:
1. lean_verify.sh Solution.lean → exit 0 (compiles, no sorry).
2. #print axioms correct_classOrders / spec_classOrders_deterministic = [propext, Quot.sound] — clean, no sorryAx.
3. same_spec(Solution.lean, Solution_prepatch.lean, lean backend) = True (spec region byte-identical; prepatch differs only in impl/proof: re-seed loop with sorry).
4. conformance_check.py ran: checked=120009, fix_disagreements=0, bug_disagreements=55617 — model shadow == genuine post-patch threading on all configs; prepatch (re-seed) negative control distinguished on 55617.
5. INDEPENDENT end-to-end faithfulness test I wrote: drove the ACTUAL patched _make_test_folds code path (real KFold(...).split generators consumed lazily by zip, real scatter-back to test_folds) against the model's threaded per-class-order abstraction over 4000 realistic (n_splits, seed, multi-class y) configs → 0 mismatches. This ties the model's abstract orders to the real observable output through the real code path, not just a reimplementation.

Because the generator is opaque and no numeric property is asserted, the spec cannot be 'too strong' about RNG behavior; the only thing pinned (threading discipline over max(c,nFolds) ranges in class order) matches the real post-patch callee exactly, on every input tested. No input where the modeled function disagrees with the real callee was found.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage judged over the consumer spec_view (signatures + axioms + pure helper + post-condition + docstrings; impl and proof regions elided), against the public problem_statement ONLY (not hints_text, not refinement.md/mapping.md which are auditor-only docs and not part of the screened view).

Gold edit: sklearn/model_selection/_split.py L623 `rng = self.random_state` -> `rng = check_random_state(self.random_state)` — behaviorally: build ONE RandomState instance and thread/advance it across classes instead of re-seeding a fresh generator per class, so distinct classes/seeds generally yield distinct per-class orders.

What the problem_statement ALREADY makes public: it states that with shuffle=True the batches are identical regardless of random_state, and the Expected Results section explicitly asks for 'batches to be different when Shuffle is turned on for different random_state seeds.' So the corrected observable (seed-dependent, distinct per-class orders) is already solver-visible.

Mechanical screen: leakage.screen PASSES (no failures). No diff markers; patched file path 'sklearn/model_selection/_split.py' and dotted module path absent from the view; no gold-patch changed line reproduced ('check_random_state' never appears in the view); the only distinctive changed symbol is 'StratifiedKFold', which appears nowhere among spec-view identifiers or comments; no _NARRATION terms (bug/fix/prepatch/wrong/...) in any spec-view comment.

Semantic gold-reconstruction judgment: The docstring's 'single source of randomness, consumed once per class... carries forward from each class to the next' with observable consequence 'distinct seeds generally yield distinct overall collections' is a faithful SPECIFICATION of correct behavior, not narration of the edit. It (a) does not name the callee check_random_state or the RandomState instance vs int-seed mechanism, (b) does not describe or contrast the buggy path (the re-seed contrast lives only in refinement.md/mapping.md, outside the screened view), and (c) restates only the corrected behavior the problem_statement already demands publicly. A faithful deterministic spec of this fix is necessarily forced to pin that the generator genuinely advances/threads; that is legitimate specification content, not disclosure of the one-line gold edit. A solver reading only the spec view learns WHAT correct behavior is (already public) but not the specific source-file one-liner that achieves it.

Recorded meta G-LEAK status: pass; relaxed_leakage flag: none. same_spec(post, prepatch)=True (spec region byte-stable across the fix, as required). No LEAKAGE finding.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
