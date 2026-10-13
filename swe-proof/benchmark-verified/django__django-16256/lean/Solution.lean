import Mathlib
-- imports-end

/-!
Abstract behavior of an async collection operation on a scoped collection.

A scoped collection carries a set of *scope bindings* (key → value) that every
element created or matched through it must satisfy. When an operation is invoked
with a set of caller-supplied keyword arguments, the operation must first merge
the collection's scope bindings into those arguments (a binding overrides any
caller value for the same key) before performing the underlying data operation.

We model the observable result as the *effective argument map*: the caller
kwargs with every scope binding forced in. The specification pins that map:
every scope key resolves to its scope value, and every non-scope key is left
exactly as the caller supplied it (frame). This is the behavior an operation
routed through the scoped collection must exhibit; an operation that ignores the
scope bindings (leaving scope keys unset or at a caller-chosen value) fails it.

Keys are modeled as `String`, values as `Int` (an opaque value identifier); the
argument map is an association list, `List.lookup` giving first-occurrence
semantics as for a Python dict.
-/

-- axioms-start
-- (No unchanged callee needs an opaque signature: the merge is modeled deeply
-- as a pure association-list update. The proof agent may add `_prop` axioms
-- only if a callee contract is genuinely required.)
-- axioms-end

-- pure-start
/-- Force a single binding `key ↦ val` into an association list: replace the
first occurrence of `key` if present, otherwise append. Mirrors `d[key] = val`
on an insertion-ordered map. -/
def kwUpsert : List (String × Int) → String → Int → List (String × Int)
  | [],             key, val => [(key, val)]
  | (k, v) :: rest, key, val =>
      if k = key then (key, val) :: rest
      else (k, v) :: kwUpsert rest key val

theorem kwUpsert_lookup_self (kvs key val) :
    (kwUpsert kvs key val).lookup key = some val := by
  induction kvs with
  | nil => simp [kwUpsert]
  | cons a as ih =>
    obtain ⟨k, v⟩ := a
    unfold kwUpsert
    by_cases h : k = key
    · subst h; simp [List.lookup_cons]
    · have hne : key ≠ k := fun e => h e.symm
      simp only [h, if_false, List.lookup_cons, beq_eq_false_iff_ne.mpr hne, ih]

theorem kwUpsert_lookup_other (kvs key val k) (h : k ≠ key) :
    (kwUpsert kvs key val).lookup k = kvs.lookup k := by
  induction kvs with
  | nil =>
    have : (k == key) = false := beq_eq_false_iff_ne.mpr h
    simp [kwUpsert, List.lookup_cons, this]
  | cons a as ih =>
    obtain ⟨k0, v0⟩ := a
    unfold kwUpsert
    by_cases hh : k0 = key
    · subst hh
      have hne : (k == k0) = false := beq_eq_false_iff_ne.mpr h
      simp [List.lookup_cons, hne]
    · simp only [hh, if_false, List.lookup_cons]
      by_cases hk0 : k == k0
      · simp [hk0]
      · simp [hk0, ih]

/-- Folding bindings whose keys all differ from `k` preserves `lookup k`. -/
theorem foldl_lookup_other : ∀ (bindings kwargs : List (String × Int)) (k : String),
    (∀ b ∈ bindings, b.1 ≠ k) →
    (bindings.foldl (fun acc b => kwUpsert acc b.1 b.2) kwargs).lookup k = kwargs.lookup k := by
  intro bindings
  induction bindings with
  | nil => intro kwargs k _; rfl
  | cons a as ih =>
    intro kwargs k h
    rw [List.foldl_cons]
    have hnk : a.1 ≠ k := h a (List.mem_cons_self)
    rw [ih (kwUpsert kwargs a.1 a.2) k (fun b hb => h b (List.mem_cons_of_mem _ hb))]
    exact kwUpsert_lookup_other kwargs a.1 a.2 k (fun e => hnk e.symm)

/-- Every bound key resolves to its bound value after the full fold (keys nodup). -/
theorem foldl_lookup_bound : ∀ (bindings : List (String × Int)),
    (bindings.map Prod.fst).Nodup → ∀ kwargs, ∀ b ∈ bindings,
      (bindings.foldl (fun acc b => kwUpsert acc b.1 b.2) kwargs).lookup b.1 = some b.2 := by
  intro bindings
  induction bindings with
  | nil => intro _ kwargs b hb; simp at hb
  | cons a as ih =>
    intro hnd kwargs b hb
    simp only [List.map_cons, List.nodup_cons] at hnd
    obtain ⟨hnotin, hnd'⟩ := hnd
    rw [List.foldl_cons]
    rcases List.mem_cons.mp hb with rfl | hmem
    · rw [foldl_lookup_other as (kwUpsert kwargs b.1 b.2) b.1
            (fun c hc e => hnotin (e ▸ List.mem_map_of_mem hc))]
      exact kwUpsert_lookup_self kwargs b.1 b.2
    · exact ih hnd' (kwUpsert kwargs a.1 a.2) b hmem
-- pure-end

-- post-conditions-start
/-- The effective argument map produced by a scoped async operation: every scope
binding is forced (scope key ↦ scope value), and every key not in the scope is
left exactly as the caller supplied it. -/
def problem_spec_scopedOp
    (bindings kwargs result : List (String × Int)) : Prop :=
  (∀ b ∈ bindings, result.lookup b.1 = some b.2) ∧
  (∀ k, (∀ b ∈ bindings, b.1 ≠ k) → result.lookup k = kwargs.lookup k)
-- post-conditions-end

-- impl-start
/-- Merge the collection's scope bindings into the caller kwargs, one binding at
a time (each forced in), then hand the effective map to the data operation. -/
def implementation_scopedOp
    (bindings kwargs : List (String × Int)) : List (String × Int) := Id.run do
  let mut out := kwargs
  for b in bindings do
    out := kwUpsert out b.1 b.2
  return out
-- impl-end

-- proof-start
theorem impl_eq_foldl (bindings kwargs) :
    implementation_scopedOp bindings kwargs
      = bindings.foldl (fun acc b => kwUpsert acc b.1 b.2) kwargs := by
  induction bindings generalizing kwargs with
  | nil => rfl
  | cons a as ih =>
    unfold implementation_scopedOp
    simp only [List.forIn_cons, List.foldl_cons, Id.run, bind, pure]
    have := ih (kwUpsert kwargs a.1 a.2)
    unfold implementation_scopedOp at this
    simp only [Id.run, bind, pure] at this
    exact this

theorem correct_scopedOp : ∀ (bindings kwargs : List (String × Int)),
    (bindings.map Prod.fst).Nodup →
    problem_spec_scopedOp bindings kwargs (implementation_scopedOp bindings kwargs) := by
  intro bindings kwargs hnd
  rw [impl_eq_foldl]
  refine ⟨?_, ?_⟩
  · intro b hb
    exact foldl_lookup_bound bindings hnd kwargs b hb
  · intro k hk
    exact foldl_lookup_other bindings kwargs k hk
-- proof-end
