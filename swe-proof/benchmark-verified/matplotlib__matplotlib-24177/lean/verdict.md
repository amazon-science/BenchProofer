# P2 adversarial audit — matplotlib__matplotlib-24177

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1_alwaysnone.lean`, `atk_2_swapminmax.lean`, `atk_3_loosexmin.lean`, `atk_4_firstonly.lean`, `atk_5_singlenone.lean`, `atk_6_prepatch.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec wrong implementation closes correct_dataLimits with clean axioms, so there is no closing-clean-axiom impl whose faithful patch could fail to resolve. verify => correct holds for this spec.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_alwaysnone.lean` → rejected (same spec, does not verify — good)

```diff
@@ -50,26 +50,7 @@
 
 -- impl-start
 def implementation_dataLimits (verts : List (Rat × Rat)) :
-    Option (Rat × Rat × Rat × Rat) := Id.run do
-  -- Collect the points taken along the path, retaining every point (keep-all).
-  let mut vertices : List (Rat × Rat) := []
-  for v in sampledVertices verts false do
-    vertices := vertices ++ [v]
-  -- With no collected points there is nothing to update.
-  match vertices with
-  | [] => return none
-  | p0 :: rest =>
-    -- Bounding box of the collected points, seeded from the first point.
-    let mut xmin := p0.1
-    let mut xmax := p0.1
-    let mut ymin := p0.2
-    let mut ymax := p0.2
-    for v in rest do
-      if v.1 < xmin then xmin := v.1
-      if v.1 > xmax then xmax := v.1
-      if v.2 < ymin then ymin := v.2
-      if v.2 > ymax then ymax := v.2
-    return some (xmin, xmax, ymin, ymax)
+    Option (Rat × Rat × Rat × Rat) := none
 -- impl-end
 
 
```

Attack 2 — `atk_2_swapminmax.lean` → rejected (same spec, does not verify — good)

```diff
@@ -51,15 +51,12 @@
 -- impl-start
 def implementation_dataLimits (verts : List (Rat × Rat)) :
     Option (Rat × Rat × Rat × Rat) := Id.run do
-  -- Collect the points taken along the path, retaining every point (keep-all).
   let mut vertices : List (Rat × Rat) := []
   for v in sampledVertices verts false do
     vertices := vertices ++ [v]
-  -- With no collected points there is nothing to update.
   match vertices with
   | [] => return none
   | p0 :: rest =>
-    -- Bounding box of the collected points, seeded from the first point.
     let mut xmin := p0.1
     let mut xmax := p0.1
     let mut ymin := p0.2
@@ -69,7 +66,7 @@
       if v.1 > xmax then xmax := v.1
       if v.2 < ymin then ymin := v.2
       if v.2 > ymax then ymax := v.2
-    return some (xmin, xmax, ymin, ymax)
+    return some (xmax, xmin, ymax, ymin)
 -- impl-end
 
 
```

Attack 3 — `atk_3_loosexmin.lean` → rejected (same spec, does not verify — good)

```diff
@@ -51,15 +51,12 @@
 -- impl-start
 def implementation_dataLimits (verts : List (Rat × Rat)) :
     Option (Rat × Rat × Rat × Rat) := Id.run do
-  -- Collect the points taken along the path, retaining every point (keep-all).
   let mut vertices : List (Rat × Rat) := []
   for v in sampledVertices verts false do
     vertices := vertices ++ [v]
-  -- With no collected points there is nothing to update.
   match vertices with
   | [] => return none
   | p0 :: rest =>
-    -- Bounding box of the collected points, seeded from the first point.
     let mut xmin := p0.1
     let mut xmax := p0.1
     let mut ymin := p0.2
@@ -69,7 +66,7 @@
       if v.1 > xmax then xmax := v.1
       if v.2 < ymin then ymin := v.2
       if v.2 > ymax then ymax := v.2
-    return some (xmin, xmax, ymin, ymax)
+    return some (xmin - 1, xmax, ymin, ymax)
 -- impl-end
 
 
```

Attack 4 — `atk_4_firstonly.lean` → rejected (same spec, does not verify — good)

```diff
@@ -51,25 +51,13 @@
 -- impl-start
 def implementation_dataLimits (verts : List (Rat × Rat)) :
     Option (Rat × Rat × Rat × Rat) := Id.run do
-  -- Collect the points taken along the path, retaining every point (keep-all).
   let mut vertices : List (Rat × Rat) := []
   for v in sampledVertices verts false do
     vertices := vertices ++ [v]
-  -- With no collected points there is nothing to update.
   match vertices with
   | [] => return none
-  | p0 :: rest =>
-    -- Bounding box of the collected points, seeded from the first point.
-    let mut xmin := p0.1
-    let mut xmax := p0.1
-    let mut ymin := p0.2
-    let mut ymax := p0.2
-    for v in rest do
-      if v.1 < xmin then xmin := v.1
-      if v.1 > xmax then xmax := v.1
-      if v.2 < ymin then ymin := v.2
-      if v.2 > ymax then ymax := v.2
-    return some (xmin, xmax, ymin, ymax)
+  | p0 :: _ =>
+    return some (p0.1, p0.1, p0.2, p0.2)
 -- impl-end
 
 
```

Attack 5 — `atk_5_singlenone.lean` → rejected (same spec, does not verify — good)

```diff
@@ -51,15 +51,13 @@
 -- impl-start
 def implementation_dataLimits (verts : List (Rat × Rat)) :
     Option (Rat × Rat × Rat × Rat) := Id.run do
-  -- Collect the points taken along the path, retaining every point (keep-all).
   let mut vertices : List (Rat × Rat) := []
   for v in sampledVertices verts false do
     vertices := vertices ++ [v]
-  -- With no collected points there is nothing to update.
   match vertices with
   | [] => return none
+  | [_] => return none
   | p0 :: rest =>
-    -- Bounding box of the collected points, seeded from the first point.
     let mut xmin := p0.1
     let mut xmax := p0.1
     let mut ymin := p0.2
```

Attack 6 — `atk_6_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -51,15 +51,12 @@
 -- impl-start
 def implementation_dataLimits (verts : List (Rat × Rat)) :
     Option (Rat × Rat × Rat × Rat) := Id.run do
-  -- Collect the points taken along the path, retaining every point (keep-all).
   let mut vertices : List (Rat × Rat) := []
-  for v in sampledVertices verts false do
+  for v in sampledVertices verts true do
     vertices := vertices ++ [v]
-  -- With no collected points there is nothing to update.
   match vertices with
   | [] => return none
   | p0 :: rest =>
-    -- Bounding box of the collected points, seeded from the first point.
     let mut xmin := p0.1
     let mut xmax := p0.1
     let mut ymin := p0.2
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
/-- The sequence of representative points taken along a geometric path, given the
path's defining points.

The boolean selects how the sequence is produced: when `false`, every point of
the path is retained; when `true`, the returned sequence may be a reduced one in
which points that do not change the rendered shape are omitted. This is an
UNCHANGED callee here, so only its signature is declared. The proof agent may add
a `_prop` axiom capturing the property a proof step requires (e.g. that the
keep-all sequence ranges over exactly the path's defining points). -/
opaque sampledVertices : List (Rat × Rat) → Bool → List (Rat × Rat)

/-- Keep-all sampling (`false`) retains exactly the path's defining points, in
order. This is the characterizing property of the opaque `sampledVertices`
callee for the keep-all mode, anticipated by the comment above. -/
axiom sampledVertices_keepall_prop : ∀ (verts : List (Rat × Rat)),
    sampledVertices verts false = verts
-- axioms-end

-- pure-start
/-- Minimum of `x0 :: xs` (a nonempty rational sequence), folded from `x0`. -/
def listMin (x0 : Rat) (xs : List Rat) : Rat := xs.foldl min x0

/-- Maximum of `x0 :: xs` (a nonempty rational sequence), folded from `x0`. -/
def listMax (x0 : Rat) (xs : List Rat) : Rat := xs.foldl max x0
-- pure-end

-- post-conditions-start
/-- The data limits induced by a path with defining points `verts`, on freshly
initialized axes with an identity data transform.

* If the path has no points, no limits are produced (`none`).
* Otherwise the result is the tight axis-aligned bounding box `(xmin, xmax, ymin,
  ymax)` of the WHOLE path: it covers every defining point, and each of its four
  bounds is attained by some defining point (so the box is exactly the
  componentwise min/max over `verts`, leaving no slack and no overshoot). -/
def problem_spec_dataLimits (verts : List (Rat × Rat))
    (result : Option (Rat × Rat × Rat × Rat)) : Prop :=
  match result with
  | none => verts = []
  | some (xmin, xmax, ymin, ymax) =>
      verts ≠ [] ∧
      (∀ v ∈ verts, xmin ≤ v.1 ∧ v.1 ≤ xmax ∧ ymin ≤ v.2 ∧ v.2 ≤ ymax) ∧
      (∃ a ∈ verts, a.1 = xmin) ∧ (∃ b ∈ verts, b.1 = xmax) ∧
      (∃ c ∈ verts, c.2 = ymin) ∧ (∃ d ∈ verts, d.2 = ymax)
-- post-conditions-end

-- impl-start
def implementation_dataLimits (verts : List (Rat × Rat)) :
    Option (Rat × Rat × Rat × Rat) := Id.run do
  -- Collect the points taken along the path, retaining every point (keep-all).
  let mut vertices : List (Rat × Rat) := []
  for v in sampledVertices verts false do
    vertices := vertices ++ [v]
  -- With no collected points there is nothing to update.
  match vertices with
  | [] => return none
  | p0 :: rest =>
    -- Bounding box of the collected points, seeded from the first point.
    let mut xmin := p0.1
    let mut xmax := p0.1
    let mut ymin := p0.2
    let mut ymax := p0.2
    for v in rest do
      if v.1 < xmin then xmin := v.1
      if v.1 > xmax then xmax := v.1
      if v.2 < ymin then ymin := v.2
      if v.2 > ymax then ymax := v.2
    return some (xmin, xmax, ymin, ymax)
-- impl-end


-- proof-start
theorem sampledVertices_keepall_mem (verts : List (Rat × Rat)) (v : Rat × Rat) :
    v ∈ sampledVertices verts false ↔ v ∈ verts := by
  rw [sampledVertices_keepall_prop]

theorem sampledVertices_keepall_nil (verts : List (Rat × Rat)) :
    sampledVertices verts false = [] ↔ verts = [] := by
  simp only [List.eq_nil_iff_forall_not_mem, sampledVertices_keepall_mem]

theorem append_loop_id (s : List (Rat × Rat)) :
    List.foldl (fun acc v => acc ++ [v]) [] s = s := by
  suffices h : ∀ (acc : List (Rat × Rat)),
      List.foldl (fun acc v => acc ++ [v]) acc s = acc ++ s by
    simpa using h []
  induction s with
  | nil => intro acc; simp
  | cons x xs ih =>
    intro acc
    simp only [List.foldl_cons, ih, List.append_assoc, List.cons_append, List.nil_append]

theorem none_branch (verts : List (Rat × Rat))
    (h : sampledVertices verts false = []) :
    implementation_dataLimits verts = none := by
  simp only [implementation_dataLimits, h]
  rfl

theorem verts_ne_nil (verts : List (Rat × Rat)) (p0 : Rat × Rat)
    (rest : List (Rat × Rat))
    (h : sampledVertices verts false = p0 :: rest) : verts ≠ [] := by
  intro hv
  have hnil : sampledVertices verts false = [] := (sampledVertices_keepall_nil verts).mpr hv
  rw [hnil] at h
  exact absurd h (by simp)

theorem loop_min_char (x0 : Rat) (xs : List Rat) :
    xs.foldl (fun a v => if v < a then v else a) x0 = listMin x0 xs := by
  unfold listMin
  have hfun : (fun a v => if v < a then v else a) = (min : Rat → Rat → Rat) := by
    funext a v
    rw [min_def]
    by_cases h : v < a <;> by_cases h2 : a ≤ v <;> simp_all <;> linarith
  rw [hfun]

theorem loop_max_char (x0 : Rat) (xs : List Rat) :
    xs.foldl (fun a v => if v > a then v else a) x0 = listMax x0 xs := by
  unfold listMax
  congr 1
  funext a v
  by_cases h : a < v
  · rw [if_pos h, max_eq_right h.le]
  · rw [if_neg h, max_eq_left (not_lt.mp h)]
/-- The exact 4-tuple accumulator update that the interleaved bounding-box `for`
loop in `implementation_dataLimits` elaborates into.  The accumulator slots are
`(xmax, xmin, ymax, ymin)` and the four guarded updates are elaborated as a
single nested `if`. -/
@[reducible] def bboxStep (s : MProd Rat (MProd Rat (MProd Rat Rat))) (v : Rat × Rat) :
    MProd Rat (MProd Rat (MProd Rat Rat)) :=
  if v.1 < s.2.1 then
    if v.1 > s.1 then
      if v.2 < s.2.2.2 then
        if v.2 > s.2.2.1 then ⟨v.1, v.1, v.2, v.2⟩ else ⟨v.1, v.1, s.2.2.1, v.2⟩
      else
        if v.2 > s.2.2.1 then ⟨v.1, v.1, v.2, s.2.2.2⟩ else ⟨v.1, v.1, s.2.2.1, s.2.2.2⟩
    else
      if v.2 < s.2.2.2 then
        if v.2 > s.2.2.1 then ⟨s.1, v.1, v.2, v.2⟩ else ⟨s.1, v.1, s.2.2.1, v.2⟩
      else
        if v.2 > s.2.2.1 then ⟨s.1, v.1, v.2, s.2.2.2⟩ else ⟨s.1, v.1, s.2.2.1, s.2.2.2⟩
  else
    if v.1 > s.1 then
      if v.2 < s.2.2.2 then
        if v.2 > s.2.2.1 then ⟨v.1, s.2.1, v.2, v.2⟩ else ⟨v.1, s.2.1, s.2.2.1, v.2⟩
      else
        if v.2 > s.2.2.1 then ⟨v.1, s.2.1, v.2, s.2.2.2⟩ else ⟨v.1, s.2.1, s.2.2.1, s.2.2.2⟩
    else
      if v.2 < s.2.2.2 then
        if v.2 > s.2.2.1 then ⟨s.1, s.2.1, v.2, v.2⟩ else ⟨s.1, s.2.1, s.2.2.1, v.2⟩
      else
        if v.2 > s.2.2.1 then ⟨s.1, s.2.1, v.2, s.2.2.2⟩ else ⟨s.1, s.2.1, s.2.2.1, s.2.2.2⟩

theorem vertices_eq (verts : List (Rat × Rat)) (p0 : Rat × Rat)
    (rest : List (Rat × Rat))
    (h : sampledVertices verts false = p0 :: rest) :
    List.foldl (fun acc v => acc ++ [v]) [] (sampledVertices verts false) = p0 :: rest := by
  rw [h]; exact append_loop_id (p0 :: rest)

theorem decompose_bbox_fold (rest : List (Rat × Rat)) (a b c d : Rat) :
    rest.foldl bboxStep ⟨a, b, c, d⟩ =
      ⟨rest.foldl (fun x v => if v.1 > x then v.1 else x) a,
       rest.foldl (fun x v => if v.1 < x then v.1 else x) b,
       rest.foldl (fun x v => if v.2 > x then v.2 else x) c,
       rest.foldl (fun x v => if v.2 < x then v.2 else x) d⟩ := by
  induction rest generalizing a b c d with
  | nil => rfl
  | cons x xs ih =>
    have hstep : bboxStep ⟨a, b, c, d⟩ x =
        ⟨(if x.1 > a then x.1 else a), (if x.1 < b then x.1 else b),
         (if x.2 > c then x.2 else c), (if x.2 < d then x.2 else d)⟩ := by
      unfold bboxStep
      split_ifs <;> rfl
    simp only [List.foldl_cons, hstep, ih]

theorem fold_min_x_eq (p0 : Rat × Rat) (rest : List (Rat × Rat)) :
    rest.foldl (fun a v => if v.1 < a then v.1 else a) p0.1
      = listMin p0.1 (rest.map (·.1)) := by
  rw [← loop_min_char p0.1 (rest.map (·.1)), List.foldl_map]

theorem fold_max_x_eq (p0 : Rat × Rat) (rest : List (Rat × Rat)) :
    rest.foldl (fun a v => if v.1 > a then v.1 else a) p0.1
      = listMax p0.1 (rest.map (·.1)) := by
  rw [← loop_max_char p0.1 (rest.map (·.1)), List.foldl_map]

theorem fold_min_y_eq (p0 : Rat × Rat) (rest : List (Rat × Rat)) :
    rest.foldl (fun a v => if v.2 < a then v.2 else a) p0.2
      = listMin p0.2 (rest.map (·.2)) := by
  rw [← loop_min_char p0.2 (rest.map (·.2)), List.foldl_map]

theorem fold_max_y_eq (p0 : Rat × Rat) (rest : List (Rat × Rat)) :
    rest.foldl (fun a v => if v.2 > a then v.2 else a) p0.2
      = listMax p0.2 (rest.map (·.2)) := by
  rw [← loop_max_char, List.foldl_map]

theorem returned_tuple_eq (p0 : Rat × Rat) (rest : List (Rat × Rat)) :
    rest.foldl bboxStep ⟨p0.1, p0.1, p0.2, p0.2⟩ =
      ⟨listMax p0.1 (rest.map (·.1)), listMin p0.1 (rest.map (·.1)),
       listMax p0.2 (rest.map (·.2)), listMin p0.2 (rest.map (·.2))⟩ := by
  rw [decompose_bbox_fold, fold_max_x_eq, fold_min_x_eq, fold_max_y_eq, fold_min_y_eq]

theorem impl_some_char (verts : List (Rat × Rat)) (p0 : Rat × Rat)
    (rest : List (Rat × Rat))
    (h : sampledVertices verts false = p0 :: rest) :
    implementation_dataLimits verts =
      some (listMin p0.1 (rest.map (·.1)), listMax p0.1 (rest.map (·.1)),
            listMin p0.2 (rest.map (·.2)), listMax p0.2 (rest.map (·.2))) := by
  unfold implementation_dataLimits
  simp only [Id.run, bind, pure, List.forIn_yield_eq_foldl]
  rw [vertices_eq verts p0 rest h]
  dsimp only
  simp only [← apply_ite ForInStep.yield, List.forIn_yield_eq_foldl]
  exact congrArg
    (fun t : MProd Rat (MProd Rat (MProd Rat Rat)) => some (t.2.1, t.1, t.2.2.2, t.2.2.1))
    (returned_tuple_eq p0 rest)

theorem listMin_le_mem (x0 : Rat) (xs : List Rat) (y : Rat)
    (hy : y ∈ x0 :: xs) : listMin x0 xs ≤ y := by
  unfold listMin
  have hA : ∀ (l : List Rat) (z : Rat), l.foldl min z ≤ z := by
    intro l
    induction l with
    | nil => intro z; simp
    | cons a as ih =>
      intro z
      simp only [List.foldl_cons]
      exact le_trans (ih (min z a)) (min_le_left z a)
  have hB : ∀ (l : List Rat) (z : Rat) (w : Rat), w ∈ l → l.foldl min z ≤ w := by
    intro l
    induction l with
    | nil => intro z w hw; simp at hw
    | cons a as ih =>
      intro z w hw
      simp only [List.foldl_cons]
      rcases List.mem_cons.mp hw with h | h
      · subst h
        exact le_trans (hA as (min z w)) (min_le_right z w)
      · exact ih (min z a) w h
  rcases List.mem_cons.mp hy with h | h
  · subst h; exact hA xs y
  · exact hB xs x0 y h

theorem listMax_ge_mem (x0 : Rat) (xs : List Rat) (y : Rat)
    (hy : y ∈ x0 :: xs) : y ≤ listMax x0 xs := by
  unfold listMax
  have seed : ∀ (l : List Rat) (a : Rat), a ≤ l.foldl max a := by
    intro l
    induction l with
    | nil => intro a; simp
    | cons b t ih =>
      intro a
      simp only [List.foldl_cons]
      exact le_trans (le_max_left a b) (ih (max a b))
  have mem : ∀ (l : List Rat) (a : Rat) (z : Rat), z ∈ l → z ≤ l.foldl max a := by
    intro l
    induction l with
    | nil => intro a z hz; simp at hz
    | cons b t ih =>
      intro a z hz
      simp only [List.foldl_cons]
      rcases List.mem_cons.mp hz with h | h
      · subst h
        exact le_trans (le_max_right a z) (seed t (max a z))
      · exact ih (max a b) z h
  rcases List.mem_cons.mp hy with h | h
  · subst h; exact seed xs y
  · exact mem xs x0 y h

theorem bounds_all (verts : List (Rat × Rat)) (p0 : Rat × Rat)
    (rest : List (Rat × Rat))
    (h : sampledVertices verts false = p0 :: rest) :
    ∀ v ∈ verts,
      listMin p0.1 (rest.map (·.1)) ≤ v.1 ∧ v.1 ≤ listMax p0.1 (rest.map (·.1)) ∧
      listMin p0.2 (rest.map (·.2)) ≤ v.2 ∧ v.2 ≤ listMax p0.2 (rest.map (·.2)) := by
  intro v hv
  have hmem : v ∈ sampledVertices verts false := (sampledVertices_keepall_mem verts v).mpr hv
  rw [h] at hmem
  have hx : v.1 ∈ p0.1 :: rest.map (·.1) := by
    rcases List.mem_cons.mp hmem with h' | h'
    · exact List.mem_cons.mpr (Or.inl (by rw [h']))
    · exact List.mem_cons.mpr (Or.inr (List.mem_map.mpr ⟨v, h', rfl⟩))
  have hy : v.2 ∈ p0.2 :: rest.map (·.2) := by
    rcases List.mem_cons.mp hmem with h' | h'
    · exact List.mem_cons.mpr (Or.inl (by rw [h']))
    · exact List.mem_cons.mpr (Or.inr (List.mem_map.mpr ⟨v, h', rfl⟩))
  exact ⟨listMin_le_mem p0.1 _ v.1 hx, listMax_ge_mem p0.1 _ v.1 hx,
         listMin_le_mem p0.2 _ v.2 hy, listMax_ge_mem p0.2 _ v.2 hy⟩

theorem listMin_attained (x0 : Rat) (xs : List Rat) :
    ∃ y ∈ x0 :: xs, y = listMin x0 xs := by
  induction xs generalizing x0 with
  | nil => exact ⟨x0, by simp [listMin]⟩
  | cons a rest ih =>
    obtain ⟨y, hy, hval⟩ := ih (min x0 a)
    refine ⟨y, ?_, ?_⟩
    · simp only [List.mem_cons] at hy ⊢
      rcases hy with h | h
      · rcases min_choice x0 a with h2 | h2 <;> simp [h, h2]
      · right; right; exact h
    · rw [hval]; rfl

theorem listMax_attained (x0 : Rat) (xs : List Rat) :
    ∃ y ∈ x0 :: xs, y = listMax x0 xs := by
  unfold listMax
  induction xs generalizing x0 with
  | nil => exact ⟨x0, by simp⟩
  | cons a as ih =>
    obtain ⟨y, hy_mem, hy_eq⟩ := ih (max x0 a)
    refine ⟨y, ?_, hy_eq⟩
    simp only [List.mem_cons] at hy_mem ⊢
    rcases hy_mem with h | h
    · rcases max_choice x0 a with hm | hm
      · left; rw [h, hm]
      · right; left; rw [h, hm]
    · right; right; exact h

theorem coord_attain_lift (verts : List (Rat × Rat)) (p0 : Rat × Rat)
    (rest : List (Rat × Rat))
    (h : sampledVertices verts false = p0 :: rest) :
    (∃ a ∈ verts, a.1 = listMin p0.1 (rest.map (·.1))) ∧
    (∃ b ∈ verts, b.1 = listMax p0.1 (rest.map (·.1))) ∧
    (∃ c ∈ verts, c.2 = listMin p0.2 (rest.map (·.2))) ∧
    (∃ d ∈ verts, d.2 = listMax p0.2 (rest.map (·.2))) := by
  have hmem : ∀ a, a ∈ p0 :: rest → a ∈ verts := by
    intro a ha
    rw [← h] at ha
    exact (sampledVertices_keepall_mem verts a).mp ha
  have key : ∀ (f : (Rat × Rat) → Rat) (v : Rat),
      v ∈ f p0 :: rest.map f → ∃ a ∈ verts, f a = v := by
    intro f v hv
    rw [List.mem_cons] at hv
    rcases hv with h1 | h2
    · exact ⟨p0, hmem p0 (List.mem_cons_self ..), h1.symm⟩
    · rw [List.mem_map] at h2
      obtain ⟨a, ha, hfa⟩ := h2
      exact ⟨a, hmem a (List.mem_cons_of_mem _ ha), hfa⟩
  refine ⟨?_, ?_, ?_, ?_⟩
  · obtain ⟨y, hy, hyeq⟩ := listMin_attained p0.1 (rest.map (·.1))
    rw [hyeq] at hy
    exact key (·.1) _ hy
  · obtain ⟨y, hy, hyeq⟩ := listMax_attained p0.1 (rest.map (·.1))
    rw [hyeq] at hy
    exact key (·.1) _ hy
  · obtain ⟨y, hy, hyeq⟩ := listMin_attained p0.2 (rest.map (·.2))
    rw [hyeq] at hy
    exact key (·.2) _ hy
  · obtain ⟨y, hy, hyeq⟩ := listMax_attained p0.2 (rest.map (·.2))
    rw [hyeq] at hy
    exact key (·.2) _ hy

theorem correct_dataLimits : ∀ (verts : List (Rat × Rat)),
    problem_spec_dataLimits verts (implementation_dataLimits verts) := by
  intro verts
  cases hs : sampledVertices verts false with
  | nil =>
    rw [none_branch verts hs]
    simp only [problem_spec_dataLimits]
    exact (sampledVertices_keepall_nil verts).mp hs
  | cons p0 rest =>
    rw [impl_some_char verts p0 rest hs]
    simp only [problem_spec_dataLimits]
    exact ⟨verts_ne_nil verts p0 rest hs, bounds_all verts p0 rest hs,
      (coord_attain_lift verts p0 rest hs).1,
      (coord_attain_lift verts p0 rest hs).2.1,
      (coord_attain_lift verts p0 rest hs).2.2.1,
      (coord_attain_lift verts p0 rest hs).2.2.2⟩

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

 All 6 attacks confirmed same_spec=True via swebench_unified.markers.same_spec (lean backend) against bundle Solution.lean; only the impl region was edited, axioms/pure/pre/post byte-identical.

### VERIFICATION RESULTS (scripts/lean_verify.sh <file>, run concurrently in 2 batches of <=4)
- pos_control (= bundle Solution.lean): exit 0 (verifies, no sorry). #print axioms correct_dataLimits => [propext, sampledVertices_keepall_prop, Classical.choice, Quot.sound]. Clean: only non-standard axiom is the frozen A-reference sampledVertices_keepall_prop; NO sorryAx.
- atk_1_alwaysnone (implementation := none): exit 1. Genuine error 'No goals to be solved' at none_branch and 'simp made no progress' -- forces proving verts=[] for all verts, false. [partial-domain/degenerate]
- atk_2_swapminmax (return some(xmax,xmin,ymax,ymin)): exit 1. Type mismatch at impl_some_char -- returned tuple no longer matches the min/max characterization. [control-flow-effect]
- atk_3_loosexmin (return some(xmin-1,xmax,ymin,ymax)): exit 1. Type mismatch -- overshoot box, attainment clause (exists a in verts, a.1=xmin) unprovable. [boundary/ungrounded overshoot]
- atk_4_firstonly (return some(p0.1,p0.1,p0.2,p0.2), ignoring rest): exit 1. 'simp made no progress' -- box collapses to first point, coverage clause fails for other verts. [partial-domain]
- atk_5_singlenone (return none for single-element vertices): exit 1. 'dsimp made no progress' at impl_some_char -- none-on-nonempty violates verts<>[] characterization. [boundary]
- atk_6_prepatch (sampledVertices verts TRUE = may-drop, the real prepatch bug): exit 1. 'rfl failed' at none_branch and 'rewrite failed' at impl_some_char -- carried keep-all(false) lemmas do not apply to the true argument; there is NO sound true-coverage axiom (mapping.md/axiom_check.py witness may-drop omits vertices). Prepatch bug reproduced.

### Protocol step 2
No same-spec wrong impl closed with clean axioms (all 6 exit 1 with genuine proof errors), so NO faithful refined patch needed materialization/resolve. patches={} accordingly. Nothing to run through run_resolve because there is no verifying-but-wrong candidate.

### WHY SOUND (spec tightness)
problem_spec_dataLimits is TOTAL and pairs COVERAGE (forall v in verts: xmin<=v.1<=xmax & ymin<=v.2<=ymax) with ATTAINMENT (exists a in verts: a.1=xmin, and 3 analogues) plus none<=>verts=[]. Coverage forces xmin<=min x; attainment forces xmin to equal some vertex's x; together xmin=min x exactly. So the some-tuple is uniquely pinned to the tight componentwise min/max bbox of the WHOLE defining-point set, and none iff verts=[]. Any impl whose correct_ closes is thus extensionally equal to the tight-bbox function on all inputs, so its refined patch computes identical limits and resolves. The only opaque freedom (sampledVertices) is fixed to the keep-all branch by the frozen axiom (false only); a true-branch impl (atk_6) has no sound coverage axiom and cannot close.

### refinement.md A-LEG AUDIT
Sampling op (sampledVertices verts false ↦ iter_bezier(simplify=False)) tagged A-reference: validated by axiom_check.py (G-AX) which runs the REAL callee on boundary+2000 fuzzed polylines and asserts keep-all sampled set == defining points (subset both ways), and witnesses may-drop (simplify=True) can omit defining vertices -> non-vacuous. Correspondence holds. match []=>none is I; bbox loop + some(...) is R (differential-tested by conformance_check.py G-CONF, seed 20240630, >=1.2e5 polylines). Every leg is R / A-reference / I -- NO kind-3 ungrounded oracle. The sole non-standard axiom sampledVertices_keepall_prop is the A-reference and appears in the clean #print axioms. Legs consistent with mapping.md symbol binding (_update_patch_limits, _base.py:2420-2458, edited line 2437).

VERDICT: SOUND. 6 distinct same-spec wrong impls (incl. prepatch bug) all fail to close; positive control verifies clean; spec's coverage+attainment leaves no divergent-but-closing implementation.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1_alwaysnone.lean`, `atk_2_swapminmax.lean`, `atk_3_loosexmin.lean`, `atk_4_firstonly.lean`, `atk_5_singlenone.lean`, `atk_6_prepatch.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec wrong implementation closes correct_dataLimits with clean axioms, so there is no closing-clean-axiom impl whose faithful patch could fail to resolve. verify => correct holds for this spec.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_alwaysnone.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_swapminmax.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_loosexmin.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_firstonly.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_singlenone.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_prepatch.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
/-- The sequence of representative points taken along a geometric path, given the
path's defining points.

The boolean selects how the sequence is produced: when `false`, every point of
the path is retained; when `true`, the returned sequence may be a reduced one in
which points that do not change the rendered shape are omitted. This is an
UNCHANGED callee here, so only its signature is declared. The proof agent may add
a `_prop` axiom capturing the property a proof step requires (e.g. that the
keep-all sequence ranges over exactly the path's defining points). -/
opaque sampledVertices : List (Rat × Rat) → Bool → List (Rat × Rat)

/-- Keep-all sampling (`false`) retains exactly the path's defining points, in
order. This is the characterizing property of the opaque `sampledVertices`
callee for the keep-all mode, anticipated by the comment above. -/
axiom sampledVertices_keepall_prop : ∀ (verts : List (Rat × Rat)),
    sampledVertices verts false = verts
-- axioms-end

-- pure-start
/-- Minimum of `x0 :: xs` (a nonempty rational sequence), folded from `x0`. -/
def listMin (x0 : Rat) (xs : List Rat) : Rat := xs.foldl min x0

/-- Maximum of `x0 :: xs` (a nonempty rational sequence), folded from `x0`. -/
def listMax (x0 : Rat) (xs : List Rat) : Rat := xs.foldl max x0
-- pure-end

-- post-conditions-start
/-- The data limits induced by a path with defining points `verts`, on freshly
initialized axes with an identity data transform.

* If the path has no points, no limits are produced (`none`).
* Otherwise the result is the tight axis-aligned bounding box `(xmin, xmax, ymin,
  ymax)` of the WHOLE path: it covers every defining point, and each of its four
  bounds is attained by some defining point (so the box is exactly the
  componentwise min/max over `verts`, leaving no slack and no overshoot). -/
def problem_spec_dataLimits (verts : List (Rat × Rat))
    (result : Option (Rat × Rat × Rat × Rat)) : Prop :=
  match result with
  | none => verts = []
  | some (xmin, xmax, ymin, ymax) =>
      verts ≠ [] ∧
      (∀ v ∈ verts, xmin ≤ v.1 ∧ v.1 ≤ xmax ∧ ymin ≤ v.2 ∧ v.2 ≤ ymax) ∧
      (∃ a ∈ verts, a.1 = xmin) ∧ (∃ b ∈ verts, b.1 = xmax) ∧
      (∃ c ∈ verts, c.2 = ymin) ∧ (∃ d ∈ verts, d.2 = ymax)
-- post-conditions-end

-- impl-start
def implementation_dataLimits (verts : List (Rat × Rat)) :
    Option (Rat × Rat × Rat × Rat) := Id.run do
  -- Collect the points taken along the path, retaining every point (keep-all).
  let mut vertices : List (Rat × Rat) := []
  for v in sampledVertices verts false do
    vertices := vertices ++ [v]
  -- With no collected points there is nothing to update.
  match vertices with
  | [] => return none
  | p0 :: rest =>
    -- Bounding box of the collected points, seeded from the first point.
    let mut xmin := p0.1
    let mut xmax := p0.1
    let mut ymin := p0.2
    let mut ymax := p0.2
    for v in rest do
      if v.1 < xmin then xmin := v.1
      if v.1 > xmax then xmax := v.1
      if v.2 < ymin then ymin := v.2
      if v.2 > ymax then ymax := v.2
    return some (xmin, xmax, ymin, ymax)
-- impl-end


-- proof-start
theorem sampledVertices_keepall_mem (verts : List (Rat × Rat)) (v : Rat × Rat) :
    v ∈ sampledVertices verts false ↔ v ∈ verts := by
  rw [sampledVertices_keepall_prop]

theorem sampledVertices_keepall_nil (verts : List (Rat × Rat)) :
    sampledVertices verts false = [] ↔ verts = [] := by
  simp only [List.eq_nil_iff_forall_not_mem, sampledVertices_keepall_mem]

theorem append_loop_id (s : List (Rat × Rat)) :
    List.foldl (fun acc v => acc ++ [v]) [] s = s := by
  suffices h : ∀ (acc : List (Rat × Rat)),
      List.foldl (fun acc v => acc ++ [v]) acc s = acc ++ s by
    simpa using h []
  induction s with
  | nil => intro acc; simp
  | cons x xs ih =>
    intro acc
    simp only [List.foldl_cons, ih, List.append_assoc, List.cons_append, List.nil_append]

theorem none_branch (verts : List (Rat × Rat))
    (h : sampledVertices verts false = []) :
    implementation_dataLimits verts = none := by
  simp only [implementation_dataLimits, h]
  rfl

theorem verts_ne_nil (verts : List (Rat × Rat)) (p0 : Rat × Rat)
    (rest : List (Rat × Rat))
    (h : sampledVertices verts false = p0 :: rest) : verts ≠ [] := by
  intro hv
  have hnil : sampledVertices verts false = [] := (sampledVertices_keepall_nil verts).mpr hv
  rw [hnil] at h
  exact absurd h (by simp)

theorem loop_min_char (x0 : Rat) (xs : List Rat) :
    xs.foldl (fun a v => if v < a then v else a) x0 = listMin x0 xs := by
  unfold listMin
  have hfun : (fun a v => if v < a then v else a) = (min : Rat → Rat → Rat) := by
    funext a v
    rw [min_def]
    by_cases h : v < a <;> by_cases h2 : a ≤ v <;> simp_all <;> linarith
  rw [hfun]

theorem loop_max_char (x0 : Rat) (xs : List Rat) :
    xs.foldl (fun a v => if v > a then v else a) x0 = listMax x0 xs := by
  unfold listMax
  congr 1
  funext a v
  by_cases h : a < v
  · rw [if_pos h, max_eq_right h.le]
  · rw [if_neg h, max_eq_left (not_lt.mp h)]
/-- The exact 4-tuple accumulator update that the interleaved bounding-box `for`
loop in `implementation_dataLimits` elaborates into.  The accumulator slots are
`(xmax, xmin, ymax, ymin)` and the four guarded updates are elaborated as a
single nested `if`. -/
@[reducible] def bboxStep (s : MProd Rat (MProd Rat (MProd Rat Rat))) (v : Rat × Rat) :
    MProd Rat (MProd Rat (MProd Rat Rat)) :=
  if v.1 < s.2.1 then
    if v.1 > s.1 then
      if v.2 < s.2.2.2 then
        if v.2 > s.2.2.1 then ⟨v.1, v.1, v.2, v.2⟩ else ⟨v.1, v.1, s.2.2.1, v.2⟩
      else
        if v.2 > s.2.2.1 then ⟨v.1, v.1, v.2, s.2.2.2⟩ else ⟨v.1, v.1, s.2.2.1, s.2.2.2⟩
    else
      if v.2 < s.2.2.2 then
        if v.2 > s.2.2.1 then ⟨s.1, v.1, v.2, v.2⟩ else ⟨s.1, v.1, s.2.2.1, v.2⟩
      else
        if v.2 > s.2.2.1 then ⟨s.1, v.1, v.2, s.2.2.2⟩ else ⟨s.1, v.1, s.2.2.1, s.2.2.2⟩
  else
    if v.1 > s.1 then
      if v.2 < s.2.2.2 then
        if v.2 > s.2.2.1 then ⟨v.1, s.2.1, v.2, v.2⟩ else ⟨v.1, s.2.1, s.2.2.1, v.2⟩
      else
        if v.2 > s.2.2.1 then ⟨v.1, s.2.1, v.2, s.2.2.2⟩ else ⟨v.1, s.2.1, s.2.2.1, s.2.2.2⟩
    else
      if v.2 < s.2.2.2 then
        if v.2 > s.2.2.1 then ⟨s.1, s.2.1, v.2, v.2⟩ else ⟨s.1, s.2.1, s.2.2.1, v.2⟩
      else
        if v.2 > s.2.2.1 then ⟨s.1, s.2.1, v.2, s.2.2.2⟩ else ⟨s.1, s.2.1, s.2.2.1, s.2.2.2⟩

theorem vertices_eq (verts : List (Rat × Rat)) (p0 : Rat × Rat)
    (rest : List (Rat × Rat))
    (h : sampledVertices verts false = p0 :: rest) :
    List.foldl (fun acc v => acc ++ [v]) [] (sampledVertices verts false) = p0 :: rest := by
  rw [h]; exact append_loop_id (p0 :: rest)

theorem decompose_bbox_fold (rest : List (Rat × Rat)) (a b c d : Rat) :
    rest.foldl bboxStep ⟨a, b, c, d⟩ =
      ⟨rest.foldl (fun x v => if v.1 > x then v.1 else x) a,
       rest.foldl (fun x v => if v.1 < x then v.1 else x) b,
       rest.foldl (fun x v => if v.2 > x then v.2 else x) c,
       rest.foldl (fun x v => if v.2 < x then v.2 else x) d⟩ := by
  induction rest generalizing a b c d with
  | nil => rfl
  | cons x xs ih =>
    have hstep : bboxStep ⟨a, b, c, d⟩ x =
        ⟨(if x.1 > a then x.1 else a), (if x.1 < b then x.1 else b),
         (if x.2 > c then x.2 else c), (if x.2 < d then x.2 else d)⟩ := by
      unfold bboxStep
      split_ifs <;> rfl
    simp only [List.foldl_cons, hstep, ih]

theorem fold_min_x_eq (p0 : Rat × Rat) (rest : List (Rat × Rat)) :
    rest.foldl (fun a v => if v.1 < a then v.1 else a) p0.1
      = listMin p0.1 (rest.map (·.1)) := by
  rw [← loop_min_char p0.1 (rest.map (·.1)), List.foldl_map]

theorem fold_max_x_eq (p0 : Rat × Rat) (rest : List (Rat × Rat)) :
    rest.foldl (fun a v => if v.1 > a then v.1 else a) p0.1
      = listMax p0.1 (rest.map (·.1)) := by
  rw [← loop_max_char p0.1 (rest.map (·.1)), List.foldl_map]

theorem fold_min_y_eq (p0 : Rat × Rat) (rest : List (Rat × Rat)) :
    rest.foldl (fun a v => if v.2 < a then v.2 else a) p0.2
      = listMin p0.2 (rest.map (·.2)) := by
  rw [← loop_min_char p0.2 (rest.map (·.2)), List.foldl_map]

theorem fold_max_y_eq (p0 : Rat × Rat) (rest : List (Rat × Rat)) :
    rest.foldl (fun a v => if v.2 > a then v.2 else a) p0.2
      = listMax p0.2 (rest.map (·.2)) := by
  rw [← loop_max_char, List.foldl_map]

theorem returned_tuple_eq (p0 : Rat × Rat) (rest : List (Rat × Rat)) :
    rest.foldl bboxStep ⟨p0.1, p0.1, p0.2, p0.2⟩ =
      ⟨listMax p0.1 (rest.map (·.1)), listMin p0.1 (rest.map (·.1)),
       listMax p0.2 (rest.map (·.2)), listMin p0.2 (rest.map (·.2))⟩ := by
  rw [decompose_bbox_fold, fold_max_x_eq, fold_min_x_eq, fold_max_y_eq, fold_min_y_eq]

theorem impl_some_char (verts : List (Rat × Rat)) (p0 : Rat × Rat)
    (rest : List (Rat × Rat))
    (h : sampledVertices verts false = p0 :: rest) :
    implementation_dataLimits verts =
      some (listMin p0.1 (rest.map (·.1)), listMax p0.1 (rest.map (·.1)),
            listMin p0.2 (rest.map (·.2)), listMax p0.2 (rest.map (·.2))) := by
  unfold implementation_dataLimits
  simp only [Id.run, bind, pure, List.forIn_yield_eq_foldl]
  rw [vertices_eq verts p0 rest h]
  dsimp only
  simp only [← apply_ite ForInStep.yield, List.forIn_yield_eq_foldl]
  exact congrArg
    (fun t : MProd Rat (MProd Rat (MProd Rat Rat)) => some (t.2.1, t.1, t.2.2.2, t.2.2.1))
    (returned_tuple_eq p0 rest)

theorem listMin_le_mem (x0 : Rat) (xs : List Rat) (y : Rat)
    (hy : y ∈ x0 :: xs) : listMin x0 xs ≤ y := by
  unfold listMin
  have hA : ∀ (l : List Rat) (z : Rat), l.foldl min z ≤ z := by
    intro l
    induction l with
    | nil => intro z; simp
    | cons a as ih =>
      intro z
      simp only [List.foldl_cons]
      exact le_trans (ih (min z a)) (min_le_left z a)
  have hB : ∀ (l : List Rat) (z : Rat) (w : Rat), w ∈ l → l.foldl min z ≤ w := by
    intro l
    induction l with
    | nil => intro z w hw; simp at hw
    | cons a as ih =>
      intro z w hw
      simp only [List.foldl_cons]
      rcases List.mem_cons.mp hw with h | h
      · subst h
        exact le_trans (hA as (min z w)) (min_le_right z w)
      · exact ih (min z a) w h
  rcases List.mem_cons.mp hy with h | h
  · subst h; exact hA xs y
  · exact hB xs x0 y h

theorem listMax_ge_mem (x0 : Rat) (xs : List Rat) (y : Rat)
    (hy : y ∈ x0 :: xs) : y ≤ listMax x0 xs := by
  unfold listMax
  have seed : ∀ (l : List Rat) (a : Rat), a ≤ l.foldl max a := by
    intro l
    induction l with
    | nil => intro a; simp
    | cons b t ih =>
      intro a
      simp only [List.foldl_cons]
      exact le_trans (le_max_left a b) (ih (max a b))
  have mem : ∀ (l : List Rat) (a : Rat) (z : Rat), z ∈ l → z ≤ l.foldl max a := by
    intro l
    induction l with
    | nil => intro a z hz; simp at hz
    | cons b t ih =>
      intro a z hz
      simp only [List.foldl_cons]
      rcases List.mem_cons.mp hz with h | h
      · subst h
        exact le_trans (le_max_right a z) (seed t (max a z))
      · exact ih (max a b) z h
  rcases List.mem_cons.mp hy with h | h
  · subst h; exact seed xs y
  · exact mem xs x0 y h

theorem bounds_all (verts : List (Rat × Rat)) (p0 : Rat × Rat)
    (rest : List (Rat × Rat))
    (h : sampledVertices verts false = p0 :: rest) :
    ∀ v ∈ verts,
      listMin p0.1 (rest.map (·.1)) ≤ v.1 ∧ v.1 ≤ listMax p0.1 (rest.map (·.1)) ∧
      listMin p0.2 (rest.map (·.2)) ≤ v.2 ∧ v.2 ≤ listMax p0.2 (rest.map (·.2)) := by
  intro v hv
  have hmem : v ∈ sampledVertices verts false := (sampledVertices_keepall_mem verts v).mpr hv
  rw [h] at hmem
  have hx : v.1 ∈ p0.1 :: rest.map (·.1) := by
    rcases List.mem_cons.mp hmem with h' | h'
    · exact List.mem_cons.mpr (Or.inl (by rw [h']))
    · exact List.mem_cons.mpr (Or.inr (List.mem_map.mpr ⟨v, h', rfl⟩))
  have hy : v.2 ∈ p0.2 :: rest.map (·.2) := by
    rcases List.mem_cons.mp hmem with h' | h'
    · exact List.mem_cons.mpr (Or.inl (by rw [h']))
    · exact List.mem_cons.mpr (Or.inr (List.mem_map.mpr ⟨v, h', rfl⟩))
  exact ⟨listMin_le_mem p0.1 _ v.1 hx, listMax_ge_mem p0.1 _ v.1 hx,
         listMin_le_mem p0.2 _ v.2 hy, listMax_ge_mem p0.2 _ v.2 hy⟩

theorem listMin_attained (x0 : Rat) (xs : List Rat) :
    ∃ y ∈ x0 :: xs, y = listMin x0 xs := by
  induction xs generalizing x0 with
  | nil => exact ⟨x0, by simp [listMin]⟩
  | cons a rest ih =>
    obtain ⟨y, hy, hval⟩ := ih (min x0 a)
    refine ⟨y, ?_, ?_⟩
    · simp only [List.mem_cons] at hy ⊢
      rcases hy with h | h
      · rcases min_choice x0 a with h2 | h2 <;> simp [h, h2]
      · right; right; exact h
    · rw [hval]; rfl

theorem listMax_attained (x0 : Rat) (xs : List Rat) :
    ∃ y ∈ x0 :: xs, y = listMax x0 xs := by
  unfold listMax
  induction xs generalizing x0 with
  | nil => exact ⟨x0, by simp⟩
  | cons a as ih =>
    obtain ⟨y, hy_mem, hy_eq⟩ := ih (max x0 a)
    refine ⟨y, ?_, hy_eq⟩
    simp only [List.mem_cons] at hy_mem ⊢
    rcases hy_mem with h | h
    · rcases max_choice x0 a with hm | hm
      · left; rw [h, hm]
      · right; left; rw [h, hm]
    · right; right; exact h

theorem coord_attain_lift (verts : List (Rat × Rat)) (p0 : Rat × Rat)
    (rest : List (Rat × Rat))
    (h : sampledVertices verts false = p0 :: rest) :
    (∃ a ∈ verts, a.1 = listMin p0.1 (rest.map (·.1))) ∧
    (∃ b ∈ verts, b.1 = listMax p0.1 (rest.map (·.1))) ∧
    (∃ c ∈ verts, c.2 = listMin p0.2 (rest.map (·.2))) ∧
    (∃ d ∈ verts, d.2 = listMax p0.2 (rest.map (·.2))) := by
  have hmem : ∀ a, a ∈ p0 :: rest → a ∈ verts := by
    intro a ha
    rw [← h] at ha
    exact (sampledVertices_keepall_mem verts a).mp ha
  have key : ∀ (f : (Rat × Rat) → Rat) (v : Rat),
      v ∈ f p0 :: rest.map f → ∃ a ∈ verts, f a = v := by
    intro f v hv
    rw [List.mem_cons] at hv
    rcases hv with h1 | h2
    · exact ⟨p0, hmem p0 (List.mem_cons_self ..), h1.symm⟩
    · rw [List.mem_map] at h2
      obtain ⟨a, ha, hfa⟩ := h2
      exact ⟨a, hmem a (List.mem_cons_of_mem _ ha), hfa⟩
  refine ⟨?_, ?_, ?_, ?_⟩
  · obtain ⟨y, hy, hyeq⟩ := listMin_attained p0.1 (rest.map (·.1))
    rw [hyeq] at hy
    exact key (·.1) _ hy
  · obtain ⟨y, hy, hyeq⟩ := listMax_attained p0.1 (rest.map (·.1))
    rw [hyeq] at hy
    exact key (·.1) _ hy
  · obtain ⟨y, hy, hyeq⟩ := listMin_attained p0.2 (rest.map (·.2))
    rw [hyeq] at hy
    exact key (·.2) _ hy
  · obtain ⟨y, hy, hyeq⟩ := listMax_attained p0.2 (rest.map (·.2))
    rw [hyeq] at hy
    exact key (·.2) _ hy

theorem correct_dataLimits : ∀ (verts : List (Rat × Rat)),
    problem_spec_dataLimits verts (implementation_dataLimits verts) := by
  intro verts
  cases hs : sampledVertices verts false with
  | nil =>
    rw [none_branch verts hs]
    simp only [problem_spec_dataLimits]
    exact (sampledVertices_keepall_nil verts).mp hs
  | cons p0 rest =>
    rw [impl_some_char verts p0 rest hs]
    simp only [problem_spec_dataLimits]
    exact ⟨verts_ne_nil verts p0 rest hs, bounds_all verts p0 rest hs,
      (coord_attain_lift verts p0 rest hs).1,
      (coord_attain_lift verts p0 rest hs).2.1,
      (coord_attain_lift verts p0 rest hs).2.2.1,
      (coord_attain_lift verts p0 rest hs).2.2.2⟩

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

 All 6 attacks confirmed same_spec=True via swebench_unified.markers.same_spec (lean backend) against bundle Solution.lean; only the impl region was edited, axioms/pure/pre/post byte-identical.

### VERIFICATION RESULTS (scripts/lean_verify.sh <file>, run concurrently in 2 batches of <=4)
- pos_control (= bundle Solution.lean): exit 0 (verifies, no sorry). #print axioms correct_dataLimits => [propext, sampledVertices_keepall_prop, Classical.choice, Quot.sound]. Clean: only non-standard axiom is the frozen A-reference sampledVertices_keepall_prop; NO sorryAx.
- atk_1_alwaysnone (implementation := none): exit 1. Genuine error 'No goals to be solved' at none_branch and 'simp made no progress' -- forces proving verts=[] for all verts, false. [partial-domain/degenerate]
- atk_2_swapminmax (return some(xmax,xmin,ymax,ymin)): exit 1. Type mismatch at impl_some_char -- returned tuple no longer matches the min/max characterization. [control-flow-effect]
- atk_3_loosexmin (return some(xmin-1,xmax,ymin,ymax)): exit 1. Type mismatch -- overshoot box, attainment clause (exists a in verts, a.1=xmin) unprovable. [boundary/ungrounded overshoot]
- atk_4_firstonly (return some(p0.1,p0.1,p0.2,p0.2), ignoring rest): exit 1. 'simp made no progress' -- box collapses to first point, coverage clause fails for other verts. [partial-domain]
- atk_5_singlenone (return none for single-element vertices): exit 1. 'dsimp made no progress' at impl_some_char -- none-on-nonempty violates verts<>[] characterization. [boundary]
- atk_6_prepatch (sampledVertices verts TRUE = may-drop, the real prepatch bug): exit 1. 'rfl failed' at none_branch and 'rewrite failed' at impl_some_char -- carried keep-all(false) lemmas do not apply to the true argument; there is NO sound true-coverage axiom (mapping.md/axiom_check.py witness may-drop omits vertices). Prepatch bug reproduced.

### Protocol step 2
No same-spec wrong impl closed with clean axioms (all 6 exit 1 with genuine proof errors), so NO faithful refined patch needed materialization/resolve. patches={} accordingly. Nothing to run through run_resolve because there is no verifying-but-wrong candidate.

### WHY SOUND (spec tightness)
problem_spec_dataLimits is TOTAL and pairs COVERAGE (forall v in verts: xmin<=v.1<=xmax & ymin<=v.2<=ymax) with ATTAINMENT (exists a in verts: a.1=xmin, and 3 analogues) plus none<=>verts=[]. Coverage forces xmin<=min x; attainment forces xmin to equal some vertex's x; together xmin=min x exactly. So the some-tuple is uniquely pinned to the tight componentwise min/max bbox of the WHOLE defining-point set, and none iff verts=[]. Any impl whose correct_ closes is thus extensionally equal to the tight-bbox function on all inputs, so its refined patch computes identical limits and resolves. The only opaque freedom (sampledVertices) is fixed to the keep-all branch by the frozen axiom (false only); a true-branch impl (atk_6) has no sound coverage axiom and cannot close.

### refinement.md A-LEG AUDIT
Sampling op (sampledVertices verts false ↦ iter_bezier(simplify=False)) tagged A-reference: validated by axiom_check.py (G-AX) which runs the REAL callee on boundary+2000 fuzzed polylines and asserts keep-all sampled set == defining points (subset both ways), and witnesses may-drop (simplify=True) can omit defining vertices -> non-vacuous. Correspondence holds. match []=>none is I; bbox loop + some(...) is R (differential-tested by conformance_check.py G-CONF, seed 20240630, >=1.2e5 polylines). Every leg is R / A-reference / I -- NO kind-3 ungrounded oracle. The sole non-standard axiom sampledVertices_keepall_prop is the A-reference and appears in the clean #print axioms. Legs consistent with mapping.md symbol binding (_update_patch_limits, _base.py:2420-2458, edited line 2437).

VERDICT: SOUND. 6 distinct same-spec wrong impls (incl. prepatch bug) all fail to close; positive control verifies clean; spec's coverage+attainment leaves no divergent-but-closing implementation.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical between Solution.lean and Solution_prepatch.lean (markers.same_spec = True). Solution.lean compiles (lean_verify exit 0, no sorry); #print axioms correct_dataLimits = [propext, sampledVertices_keepall_prop, Classical.choice, Quot.sound] — only the declared A-reference _prop, no sorryAx. Modeled function is _update_patch_limits @ _base.py:2420-2458 (gold flips iter_bezier() -> iter_bezier(simplify=False)). Empirically compared the REAL patched Axes._update_patch_limits pipeline (matplotlib 3.6.3, and against a base_commit 493d608e39 worktree) to the spec problem_spec_dataLimits (tight componentwise min/max bbox over all verts; none iff verts=[]): 5000+ random polylines n<=12, 1000+ large-N (50-500) polylines, plus collinear/tall-spike/degenerate/single-point/duplicate/empty cases — 0 disagreements under 1e-6..1e-9 tol. Empty path -> dataLim inf/-inf -> None, matching 'none <-> verts=[]'. The real keep-all callee returns duplicated endpoints (e.g. [(0,0),(0,0),(0,0),(1,1)]) but with identical membership, so min/max and both the universal coverage and existential attainment clauses hold exactly. The exact-list axiom sampledVertices verts false = verts is stronger than the duplicate-bearing real callee, but that is a callee-modeling/G-AX concern and does NOT cause problem_spec_dataLimits to disagree with the real function on any input. Modeling boundary (fresh axes, identity data transform) is declared in the spec docstring and enforced by conformance_check.py. No diverging input found; spec is not too strong.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view rendered via markers.spec_view (LeanBackend tables) hashes to e878c4af5b92227ca037fdbcf14301c72555921ff468877f31339c8287b4dda8, matching recorded region_hashes.spec_view — intact, no tampering.

Decisive: same_spec(Solution.lean, Solution_prepatch.lean) = True. The four spec regions (axioms, pure, pre-, post-conditions) are byte-identical between the gold (post-patch) and buggy (prepatch) variants. The distinguishing edit — sampledVertices verts false (keep-all, fix) vs ...true (may-drop, bug) — lives entirely in the impl region, which the spec view ELIDES ('implementation elided — supplied by the consumer'). A spec view identical for both fixed and buggy variants cannot by construction leak which edit distinguishes them.

Lexical screen: the spec view contains NONE of the gold-patch / problem-statement tokens — no iter_bezier, simplify, should_simplify, _update_patch_limits, iter_segments, histtype, density, _base.py, row_stack, or update_datalim. It is pure abstract Lean: no Python symbol, file path, line number, or kwarg named. Code location (_base.py:2437) appears only in mapping.md (not part of spec view).

The post-condition (tight bbox covers every defining point, each bound attained) is the legitimate correct-behavior contract, no stronger than the public problem_statement's requirement that the autoscaled density axis cover the whole histogram. The axioms region models the unchanged callee abstractly (keep-all/may-drop selector) — intrinsic callee modeling, expressed without quoting the gold mechanism, and identical across pre/post variants. Nothing in the spec view discloses the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
