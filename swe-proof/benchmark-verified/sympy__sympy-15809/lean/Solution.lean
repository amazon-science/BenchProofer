import Mathlib
-- imports-end

/-!
Reduction of a finite collection of comparable extended-real values to its
greatest-lower-bound (`min`) and least-upper-bound (`max`).

Values are modeled as `WithTop (WithBot ℚ)`: a finite rational, the top element
`⊤` (positive infinity), or the bottom element `⊥` (negative infinity). The
collection is processed in call order with mutable accumulation, starting from
the neutral element of the reduction (`⊤` for the minimum, `⊥` for the maximum);
an empty collection therefore reduces to that neutral element. The reduction is
always defined (returns a value, never the failure branch `Except.error`).
-/

-- axioms-start
-- No unchanged callee is consumed as an axiom: the reduction over comparable
-- extended reals is modeled deeply as a fold (see the impl regions). A result
-- is `Except.ok v` for a produced value `v`, or `Except.error ()` for failure.
abbrev EVal := WithTop (WithBot ℚ)
-- axioms-end

-- pure-start
-- (no shared pure helpers needed)
-- pure-end

/-! ## Minimum reduction -/

-- post-conditions-start
/-- The reduction always succeeds with some value `v` which is a lower bound of
every input, equals the neutral element `⊤` exactly when there is no input, and
is otherwise itself one of the inputs (the attained greatest lower bound). -/
def problem_spec_min (args : List EVal) (result : Except Unit EVal) : Prop :=
  ∃ v : EVal, result = Except.ok v ∧
    (args = [] → v = ⊤) ∧
    (∀ x ∈ args, v ≤ x) ∧
    (args ≠ [] → v ∈ args)
-- post-conditions-end

-- impl-start
def implementation_min (args : List EVal) : Except Unit EVal := Id.run do
  let mut acc : EVal := ⊤
  for x in args do
    acc := min acc x
  return Except.ok acc
-- impl-end

-- proof-start
theorem min_fold_eq (args : List EVal) (init : EVal) :
    (Id.run (forIn args init (fun (x r : EVal) => (pure (ForInStep.yield (min r x)) : Id _))))
      = List.foldl min init args := by
  induction args generalizing init with
  | nil => rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    rw [List.foldl_cons]
    exact ih (min init a)

theorem foldl_min_le (init x : EVal) (as : List EVal) :
    List.foldl min (min init x) as ≤ min init x := by
  induction as generalizing init x with
  | nil => simp
  | cons b bs ih =>
    rw [List.foldl_cons]
    exact le_trans (ih (min init x) b) (min_le_left _ _)

theorem foldl_min_props (args : List EVal) (init : EVal) :
    (∀ x ∈ args, List.foldl min init args ≤ x) ∧
    (List.foldl min init args = init ∨ List.foldl min init args ∈ args) := by
  induction args generalizing init with
  | nil => simp
  | cons a as ih =>
    rw [List.foldl_cons]
    obtain ⟨hmem, hcase⟩ := ih (min init a)
    refine ⟨?_, ?_⟩
    · intro x hx
      rcases List.mem_cons.mp hx with rfl | hx
      · exact le_trans (foldl_min_le init x as) (min_le_right _ _)
      · exact hmem x hx
    · rcases hcase with h | h
      · rw [h]
        rcases min_choice init a with hh | hh
        · exact Or.inl hh
        · exact Or.inr (by rw [hh]; exact List.mem_cons_self)
      · exact Or.inr (List.mem_cons_of_mem _ h)

theorem impl_min_eq (args : List EVal) :
    implementation_min args = Except.ok (List.foldl min ⊤ args) := by
  unfold implementation_min
  simp only [Id.run, bind]
  rw [← min_fold_eq args ⊤]
  rfl

theorem correct_min : ∀ args : List EVal,
    problem_spec_min args (implementation_min args) := by
  intro args
  refine ⟨List.foldl min ⊤ args, impl_min_eq args, ?_, (foldl_min_props args ⊤).1, ?_⟩
  · intro h; subst h; rfl
  · intro hne
    cases args with
    | nil => exact absurd rfl hne
    | cons a as =>
      rw [List.foldl_cons, min_top_left]
      rcases (foldl_min_props as a).2 with h | h
      · rw [h]; exact List.mem_cons_self
      · exact List.mem_cons_of_mem _ h
-- proof-end

/-! ## Maximum reduction -/

-- post-conditions-start
/-- The reduction always succeeds with some value `v` which is an upper bound of
every input, equals the neutral element `⊥` exactly when there is no input, and
is otherwise itself one of the inputs (the attained least upper bound). -/
def problem_spec_max (args : List EVal) (result : Except Unit EVal) : Prop :=
  ∃ v : EVal, result = Except.ok v ∧
    (args = [] → v = ⊥) ∧
    (∀ x ∈ args, x ≤ v) ∧
    (args ≠ [] → v ∈ args)
-- post-conditions-end

-- impl-start
def implementation_max (args : List EVal) : Except Unit EVal := Id.run do
  let mut acc : EVal := ⊥
  for x in args do
    acc := max acc x
  return Except.ok acc
-- impl-end

-- proof-start
theorem max_fold_eq (args : List EVal) (init : EVal) :
    (Id.run (forIn args init (fun (x r : EVal) => (pure (ForInStep.yield (max r x)) : Id _))))
      = List.foldl max init args := by
  induction args generalizing init with
  | nil => rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    rw [List.foldl_cons]
    exact ih (max init a)

theorem le_foldl_max (init x : EVal) (as : List EVal) :
    max init x ≤ List.foldl max (max init x) as := by
  induction as generalizing init x with
  | nil => simp
  | cons b bs ih =>
    rw [List.foldl_cons]
    exact le_trans (le_max_left _ _) (ih (max init x) b)

theorem foldl_max_props (args : List EVal) (init : EVal) :
    (∀ x ∈ args, x ≤ List.foldl max init args) ∧
    (List.foldl max init args = init ∨ List.foldl max init args ∈ args) := by
  induction args generalizing init with
  | nil => simp
  | cons a as ih =>
    rw [List.foldl_cons]
    obtain ⟨hmem, hcase⟩ := ih (max init a)
    refine ⟨?_, ?_⟩
    · intro x hx
      rcases List.mem_cons.mp hx with rfl | hx
      · exact le_trans (le_max_right _ _) (le_foldl_max init x as)
      · exact hmem x hx
    · rcases hcase with h | h
      · rw [h]
        rcases max_choice init a with hh | hh
        · exact Or.inl hh
        · exact Or.inr (by rw [hh]; exact List.mem_cons_self)
      · exact Or.inr (List.mem_cons_of_mem _ h)

theorem impl_max_eq (args : List EVal) :
    implementation_max args = Except.ok (List.foldl max ⊥ args) := by
  unfold implementation_max
  simp only [Id.run, bind]
  rw [← max_fold_eq args ⊥]
  rfl

theorem correct_max : ∀ args : List EVal,
    problem_spec_max args (implementation_max args) := by
  intro args
  refine ⟨List.foldl max ⊥ args, impl_max_eq args, ?_, (foldl_max_props args ⊥).1, ?_⟩
  · intro h; subst h; rfl
  · intro hne
    cases args with
    | nil => exact absurd rfl hne
    | cons a as =>
      rw [List.foldl_cons, max_bot_left]
      rcases (foldl_max_props as a).2 with h | h
      · rw [h]; exact List.mem_cons_self
      · exact List.mem_cons_of_mem _ h
-- proof-end
