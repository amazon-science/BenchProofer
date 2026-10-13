import Mathlib
-- imports-end

/-!
Combining the attribute mappings of several source objects under the
"override" policy: the combined attributes are taken from the FIRST source.

Each source object carries an *identity* (which object it is) and *contents*
(its key→value attribute mapping). Two distinct objects have distinct
identities; the contents are an association of keys to values.

Under the "override" policy the desired behavior is:

  * with no sources, there is nothing to combine (no result);
  * with at least one source, the combined attributes have the SAME contents
    as the first source, but live in a result object that is INDEPENDENT of
    every source — its identity differs from each source's identity, so the
    sources are never shared into the result. Changing the result later can
    therefore not be reflected back into any source.
-/

-- axioms-start
-- No unchanged outside callee is consumed. Producing a fresh independent copy of
-- the first source's attributes — a new object whose contents equal the first
-- source's and whose identity differs from every source's — is reproduced
-- structurally (a fresh identity + a verbatim content copy), so no
-- `opaque`/`axiom` callee contract is needed. The proof agent may add `_prop`
-- axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- The contents of an attribute object: an association of keys to values.
String keys/values are abstracted to `Int` by an injective encoding; only
equality of contents is observed. -/
abbrev AttrDict := List (Int × Int)

/-- A source object: its identity paired with its contents. Distinct objects
have distinct identities; only equality/distinctness of identities is observed. -/
abbrev AttrObj := Nat × AttrDict
-- pure-end

-- post-conditions-start
/-- The "override" combination, pinned at every component:

* with no sources the result is absent;
* with at least one source `first`, the result is present, its contents are
  exactly `first`'s contents (the data is carried over unchanged), and its
  identity is fresh — distinct from the identity of every source — so the
  result aliases none of the sources. -/
def problem_spec_mergeAttrsOverride
    (attrs : List AttrObj) (result : Option AttrObj) : Prop :=
  match attrs with
  | [] => result = none
  | first :: _ =>
    ∃ id, result = some (id, first.2) ∧ id ∉ attrs.map Prod.fst
-- post-conditions-end

-- impl-start
def implementation_mergeAttrsOverride
    (attrs : List AttrObj) : Option AttrObj := Id.run do
  -- With no sources there is nothing to combine.
  if attrs.isEmpty then
    return none
  -- Override: produce a fresh independent copy of the first source's
  -- attributes. Its identity is chosen distinct from every source's identity
  -- (strictly greater than all of them), and its contents are the first
  -- source's contents copied verbatim.
  let mut maxId := 0
  for p in attrs do
    if p.1 > maxId then
      maxId := p.1
  let freshId := maxId + 1
  let first := attrs.head!
  return some (freshId, first.2)
-- impl-end

-- proof-start
/-- Closed-form spec of the loop: the running maximum of all `p.1`. -/
private def loopMax (attrs : List AttrObj) (init : Nat) : Nat :=
  List.foldl (fun r p => if p.1 > r then p.1 else r) init attrs

private theorem loopMax_cons (a : AttrObj) (as : List AttrObj) (init : Nat) :
    loopMax (a :: as) init = loopMax as (if a.1 > init then a.1 else init) := by
  simp only [loopMax, List.foldl_cons]

/-- The desugared `forIn` loop computes `loopMax` (Route B helper, generalized
over the accumulator). -/
private theorem loop_eq (attrs : List AttrObj) (init : Nat) :
    Id.run (forIn (m := Id) attrs init (fun (p : AttrObj) r =>
      (if p.1 > r then ForInStep.yield p.1 else ForInStep.yield r)))
      = loopMax attrs init := by
  induction attrs generalizing init with
  | nil => rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    by_cases h : a.1 > init <;> simp only [h, if_true, if_false, ih, loopMax_cons]

private theorem loopMax_ge_init (attrs : List AttrObj) (init : Nat) :
    init ≤ loopMax attrs init := by
  induction attrs generalizing init with
  | nil => simp [loopMax]
  | cons a as ih =>
    rw [loopMax_cons]
    by_cases h : a.1 > init
    · exact le_trans (le_of_lt h) (by simpa [h] using ih a.1)
    · simpa [h] using ih init

private theorem loopMax_ge_mem (attrs : List AttrObj) (init : Nat) :
    ∀ p ∈ attrs, p.1 ≤ loopMax attrs init := by
  induction attrs generalizing init with
  | nil => simp
  | cons a as ih =>
    intro p hp
    rw [loopMax_cons]
    rcases List.mem_cons.1 hp with rfl | hmem
    · by_cases h : p.1 > init
      · simpa [h] using loopMax_ge_init as p.1
      · exact le_trans (le_of_not_gt h) (by simpa [h] using loopMax_ge_init as init)
    · exact ih _ p hmem

/-- Evaluate the implementation on a non-empty input: identity is `loopMax + 1`,
contents are the first source's contents copied verbatim. -/
private theorem impl_cons (a : AttrObj) (as : List AttrObj) :
    implementation_mergeAttrsOverride (a :: as) = some (loopMax (a :: as) 0 + 1, a.2) := by
  unfold implementation_mergeAttrsOverride
  simp only [Id.run, List.isEmpty_cons, Bool.false_eq_true, if_false]
  show some ((Id.run (forIn (m := Id) (a :: as) 0 (fun (p : AttrObj) r =>
      (if p.1 > r then ForInStep.yield p.1 else ForInStep.yield r)))) + 1, (a :: as).head!.2) = _
  rw [loop_eq (a :: as) 0]
  rfl

theorem correct_mergeAttrsOverride :
    ∀ (attrs : List AttrObj),
    problem_spec_mergeAttrsOverride attrs
      (implementation_mergeAttrsOverride attrs) := by
  intro attrs
  cases attrs with
  | nil => simp [problem_spec_mergeAttrsOverride, implementation_mergeAttrsOverride]
  | cons a as =>
    simp only [problem_spec_mergeAttrsOverride]
    refine ⟨loopMax (a :: as) 0 + 1, impl_cons a as, ?_⟩
    intro hmem
    rw [List.mem_map] at hmem
    obtain ⟨p, hp, hpeq⟩ := hmem
    have := loopMax_ge_mem (a :: as) 0 p hp
    rw [hpeq] at this
    omega
-- proof-end
