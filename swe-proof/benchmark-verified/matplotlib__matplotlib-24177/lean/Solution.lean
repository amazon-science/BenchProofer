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
