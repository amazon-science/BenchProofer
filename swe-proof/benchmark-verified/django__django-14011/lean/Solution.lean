import Mathlib
-- imports-end

-- axioms-start
/- No unchanged callee needs an opaque signature here: every operation the modeled
behaviors invoke (a keyed registry insert/replace, and releasing a resource) is a
pure value-level transformation, modeled directly in the `pure` region and used
identically on both sides of each refinement. The proof agent therefore consumes
no `_prop` axiom. -/
-- axioms-end

-- pure-start
/-- A managed resource held in a registry. `name` is the key under which the
registry tracks it; `isOpen` records whether the resource is currently live
(`true`) or has been released (`false`). -/
structure Resource where
  name : String
  isOpen : Bool
deriving DecidableEq, Repr

/-- Look the resource up by its key, returning the first entry with that name. -/
def lookupRes (reg : List Resource) (key : String) : Option Resource :=
  reg.find? (fun r => r.name == key)

/-- Insert `r` into the registry under its key: if an entry with the same key
already exists, replace it in place (keeping position); otherwise append it. -/
def setRes (reg : List Resource) (r : Resource) : List Resource :=
  if reg.any (fun d => d.name == r.name) then
    reg.map (fun d => if d.name == r.name then r else d)
  else
    reg ++ [r]

/-- Release a single resource: mark it closed, leaving its key unchanged. -/
def releaseRes (r : Resource) : Resource := { r with isOpen := false }
-- pure-end

-- post-conditions-start
/-- Binding a provided collection into the registry. The result is a registry with
no duplicate keys whose lookup is fully determined: every key the provided
collection mentions resolves to the provided value for that key, and every other
key keeps whatever the registry held before. -/
def problem_spec_bindResources
    (reg provided : List Resource) (result : List Resource) : Prop :=
  result.Pairwise (fun a b => a.name ≠ b.name) ∧
  (∀ key, lookupRes result key =
    match lookupRes provided key with
    | some r => some r
    | none   => lookupRes reg key)
-- post-conditions-end

-- impl-start
def implementation_bindResources
    (reg provided : List Resource) : List Resource := Id.run do
  let mut r := reg
  for c in provided do
    r := setRes r c
  return r
-- impl-end

-- proof-start
theorem correct_bindResources :
    ∀ (reg provided : List Resource),
      reg.Pairwise (fun a b => a.name ≠ b.name) →
      provided.Pairwise (fun a b => a.name ≠ b.name) →
      problem_spec_bindResources reg provided
        (implementation_bindResources reg provided) := by
  have hlookup : ∀ (reg : List Resource) (r : Resource) (key : String),
      lookupRes (setRes reg r) key = if r.name = key then some r else lookupRes reg key := by
    intro reg r key
    unfold setRes lookupRes
    by_cases hany : reg.any (fun d => d.name == r.name) = true
    · rw [if_pos hany, List.find?_map]
      by_cases hk : r.name = key
      · subst hk
        rw [if_pos rfl]
        have hcomp : ((fun r' => r'.name == r.name) ∘ (fun d => if d.name == r.name then r else d))
            = (fun d => d.name == r.name) := by
          funext d; by_cases hd : d.name = r.name <;> simp [Function.comp_apply, hd]
        rw [hcomp]
        rcases hfind : reg.find? (fun d => d.name == r.name) with _ | d0
        · exfalso
          rw [List.find?_eq_none] at hfind
          rw [List.any_eq_true] at hany
          obtain ⟨x, hx, hxp⟩ := hany
          exact hfind x hx hxp
        · have hd0 := List.find?_some hfind
          simp only [beq_iff_eq] at hd0
          rw [hfind]; simp [hd0]
      · rw [if_neg hk]
        have hcomp : ((fun r' => r'.name == key) ∘ (fun d => if d.name == r.name then r else d))
            = (fun d => d.name == key) := by
          funext d; by_cases hd : d.name = r.name <;> simp [Function.comp_apply, hd]
        rw [hcomp]
        rcases hfind : reg.find? (fun d => d.name == key) with _ | d0
        · rw [hfind]; simp
        · have hd0 := List.find?_some hfind
          simp only [beq_iff_eq] at hd0
          have hne : d0.name ≠ r.name := by rw [hd0]; exact fun h => hk h.symm
          rw [hfind]; simp [hne]
    · rw [if_neg hany, List.find?_append]
      simp only [List.any_eq_true, not_exists, Bool.not_eq_true, not_and] at hany
      by_cases hk : r.name = key
      · rw [if_pos hk]
        have hnone : reg.find? (fun r' => r'.name == key) = none := by
          rw [List.find?_eq_none]
          intro x hx hxp
          have h2 := hany x hx
          simp only [beq_iff_eq] at hxp
          simp [hxp, ← hk] at h2
        rw [hnone]; simp [hk]
      · rw [if_neg hk]; simp [hk]
  have hpair : ∀ (reg : List Resource) (r : Resource),
      reg.Pairwise (fun a b => a.name ≠ b.name) →
      (setRes reg r).Pairwise (fun a b => a.name ≠ b.name) := by
    intro reg r h
    unfold setRes
    by_cases hany : reg.any (fun d => d.name == r.name) = true
    · rw [if_pos hany]
      have hname : ∀ d ∈ reg, ((if d.name == r.name then r else d).name) = d.name := by
        intro d hd; by_cases hdd : d.name = r.name <;> simp [hdd]
      rw [List.pairwise_map]
      apply h.imp_of_mem
      intro a b ha hb hab
      rw [hname a ha, hname b hb]; exact hab
    · rw [if_neg hany]
      rw [List.pairwise_append]
      refine ⟨h, List.pairwise_singleton _ _, ?_⟩
      intro a ha b hb
      simp only [List.mem_singleton] at hb
      subst hb
      simp only [List.any_eq_true, not_exists, Bool.not_eq_true, not_and] at hany
      have := hany a ha
      simp only [beq_eq_false_iff_ne] at this
      exact this
  have key_lemma : ∀ (provided reg : List Resource),
      reg.Pairwise (fun a b => a.name ≠ b.name) →
      provided.Pairwise (fun a b => a.name ≠ b.name) →
      problem_spec_bindResources reg provided (provided.foldl setRes reg) := by
    intro provided
    induction provided with
    | nil =>
      intro reg hreg _
      refine ⟨hreg, ?_⟩
      intro key; simp [lookupRes]
    | cons c cs ih =>
      intro reg hreg hprov
      rw [List.foldl_cons]
      have hprovcs : cs.Pairwise (fun a b => a.name ≠ b.name) := hprov.tail
      have hregc : (setRes reg c).Pairwise (fun a b => a.name ≠ b.name) := hpair reg c hreg
      obtain ⟨hp1, hp2⟩ := ih (setRes reg c) hregc hprovcs
      refine ⟨hp1, ?_⟩
      intro key
      rw [hp2 key, hlookup reg c key]
      have hcons : lookupRes (c :: cs) key
          = if c.name = key then some c else lookupRes cs key := by
        simp only [lookupRes, List.find?_cons]
        by_cases hck : c.name = key
        · simp [hck]
        · rw [if_neg hck]
          have : (c.name == key) = false := by simpa using hck
          simp [this]
      rw [hcons]
      by_cases hck : c.name = key
      · have hcsnone : lookupRes cs key = none := by
          rw [lookupRes, List.find?_eq_none]
          intro x hx hxp
          simp only [beq_iff_eq] at hxp
          have hne : c.name ≠ x.name := (List.pairwise_cons.mp hprov).1 x hx
          exact hne (by rw [hck, hxp])
        rw [hcsnone]; simp [hck]
      · simp [hck]
  intro reg provided hreg hprov
  have himpl : implementation_bindResources reg provided = provided.foldl setRes reg := by
    simp [implementation_bindResources, Id.run]
    rfl
  rw [himpl]
  exact key_lemma provided reg hreg hprov

-- proof-end

-- post-conditions-start
/-- Releasing the whole registry. The set of keys is preserved exactly (same keys,
same order, none added or dropped), and every resulting resource is closed. -/
def problem_spec_releaseResources
    (reg : List Resource) (result : List Resource) : Prop :=
  result.map (·.name) = reg.map (·.name) ∧
  (∀ r ∈ result, r.isOpen = false)
-- post-conditions-end

-- impl-start
def implementation_releaseResources (reg : List Resource) : List Resource := Id.run do
  let mut out := []
  for c in reg do
    out := out ++ [releaseRes c]
  return out
-- impl-end

-- proof-start
theorem correct_releaseResources :
    ∀ (reg : List Resource),
      problem_spec_releaseResources reg (implementation_releaseResources reg) := by
  intro reg
  have h : implementation_releaseResources reg = reg.map releaseRes := by
    simp only [implementation_releaseResources, Id.run]
    suffices hg : ∀ (init : List Resource),
        (forIn reg init fun c r => (pure (ForInStep.yield (r ++ [releaseRes c])) : Id _))
          = init ++ reg.map releaseRes by
      have := hg []
      simpa using this
    intro init
    induction reg generalizing init with
    | nil => simp; rfl
    | cons a as ih =>
        rw [List.forIn_cons]
        show forIn as (init ++ [releaseRes a]) _ = _
        rw [ih]
        simp
  rw [h]
  constructor
  · simp [releaseRes]
  · intro r hr
    simp [releaseRes] at hr
    obtain ⟨a, _, ha⟩ := hr
    rw [← ha]

-- proof-end
