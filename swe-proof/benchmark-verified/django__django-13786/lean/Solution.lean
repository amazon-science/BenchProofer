import Mathlib
-- imports-end

/-!
Collapsing two consecutive option-configuration steps into a single combined
option set.

The first step establishes an initial set of named option settings (a mapping
from option keys to their values). A second, overriding step supplies its own
set of settings that should take effect in place of the first. The combined
result is obtained by overlaying the overriding step's settings on top of the
initial ones (the overriding value wins for any key both mention, and keys only
the overriding step mentions are added).

There is, however, a designated family of *managed* keys: keys whose value is
considered to be owned entirely by the overriding step. For a managed key, the
overriding step is authoritative — if it does NOT mention that key, the key must
be cleared from the combined result, even when the initial step had set it.
Keys outside the managed family are left untouched when the overriding step is
silent about them.

The behavior is stated abstractly as an input→output relation on the combined
option set; the implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the combination is
-- spelled out concretely (an overlay of two key→value mappings followed by the
-- clearing of any managed key the overriding mapping is silent about).
-- axioms-end

-- pure-start
/-- Is key `k` present in the key→value mapping `d`? -/
def keyPresent {V : Type} (d : List (String × V)) (k : String) : Bool :=
  d.any (fun p => p.1 == k)

/-- Look up key `k` in `d`, returning the value of the first entry with that key
(`none` if absent). A mapping is read as a dictionary: first match wins. -/
def optLookup {V : Type} (d : List (String × V)) (k : String) : Option V :=
  (d.find? (fun p => p.1 == k)).map (·.2)

/-- Overlay `override` on top of `base`: keep every overriding entry, and keep
each base entry whose key the overriding mapping does not mention. -/
def mergeOpts {V : Type} (base override : List (String × V)) : List (String × V) :=
  override ++ base.filter (fun p => ! keyPresent override p.1)

/-- Remove every entry whose key equals `k`. -/
def dropKey {V : Type} (d : List (String × V)) (k : String) : List (String × V) :=
  d.filter (fun p => p.1 != k)

/-- The value the combined mapping should hold at key `k`:
* if the overriding mapping mentions `k`, its value wins;
* otherwise, if `k` is a managed key, it is cleared (`none`);
* otherwise the base value (if any) survives. -/
def expectedLookup {V : Type} (base override : List (String × V))
    (managedKeys : List String) (k : String) : Option V :=
  match optLookup override k with
  | some v => some v
  | none   => if managedKeys.contains k then none else optLookup base k
-- pure-end

-- post-conditions-start
/-- The combined mapping is a genuine dictionary (its keys are distinct) and
agrees, at every key, with the desired overlay-then-clear-managed behavior. The
key-distinctness conjunct rules out a result that merely shares the right
first-match lookups while hiding shadowed duplicate keys (a Python `dict` has no
duplicate keys); together the two clauses pin the resulting dictionary exactly. -/
def problem_spec_combineOptions {V : Type}
    (base override : List (String × V)) (managedKeys : List String)
    (result : List (String × V)) : Prop :=
  (result.map Prod.fst).Nodup ∧
  (∀ k : String, optLookup result k = expectedLookup base override managedKeys k)
-- post-conditions-end

-- impl-start
def implementation_combineOptions {V : Type}
    (base override : List (String × V)) (managedKeys : List String) :
    List (String × V) := Id.run do
  let mut options := mergeOpts base override
  for key in managedKeys do
    if ! keyPresent override key then
      options := dropKey options key
  return options
-- impl-end


-- proof-start
/-- The loop's initial accumulator: the overlay of `override` on `base`. -/
def options0 {V : Type} (base override : List (String × V)) : List (String × V) :=
  mergeOpts base override

/-- The pure loop-step: drop `key` from the accumulator iff `override` is silent
about it. -/
def stepFn {V : Type} (override : List (String × V))
    (acc : List (String × V)) (key : String) : List (String × V) :=
  if ! keyPresent override key then dropKey acc key else acc

/-- Fold-level invariant: the accumulator has distinct keys, and its lookup at
every key agrees with the initial overlay except that keys already processed and
not mentioned by `override` read as `none`. -/
def CombineInv {V : Type} (base override : List (String × V))
    (processed : List String) (acc : List (String × V)) : Prop :=
  (acc.map Prod.fst).Nodup ∧
  (∀ k : String,
    optLookup acc k =
      (if processed.contains k && ! keyPresent override k then none
       else optLookup (mergeOpts base override) k))

theorem keyPresent_iff_lookup {V : Type} (d : List (String × V)) (k : String) :
    keyPresent d k = true ↔ ∃ v, optLookup d k = some v := by
  simp only [keyPresent, optLookup, ← Option.isSome_iff_exists, Option.isSome_map,
    List.find?_isSome, List.any_eq_true]

theorem optLookup_dropKey_eq {V : Type} (d : List (String × V)) (k q : String) :
    optLookup (dropKey d k) q = if q = k then none else optLookup d q := by
  simp only [optLookup, dropKey]
  induction d with
  | nil => simp
  | cons p ds ih =>
    rw [List.filter_cons]
    by_cases hpk : (p.1 != k) = true
    · rw [if_pos hpk, List.find?_cons, List.find?_cons]
      by_cases hpq : (p.1 == q) = true
      · rw [hpq]
        simp only [beq_iff_eq] at hpq
        subst hpq
        simp only [bne_iff_ne, ne_eq] at hpk
        rw [if_neg hpk]
      · rw [Bool.not_eq_true] at hpq
        rw [hpq, ih]
    · rw [if_neg hpk, List.find?_cons]
      simp only [bne_iff_ne, ne_eq, Decidable.not_not] at hpk
      by_cases hpq : (p.1 == q) = true
      · simp only [beq_iff_eq] at hpq
        subst hpk
        rw [if_pos hpq.symm, ih, if_pos hpq.symm]
      · rw [Bool.not_eq_true] at hpq
        rw [hpq, ih]

theorem map_fst_dropKey_Nodup {V : Type} (d : List (String × V)) (k : String) :
    (d.map Prod.fst).Nodup → ((dropKey d k).map Prod.fst).Nodup := by
  intro h
  unfold dropKey
  exact List.Nodup.sublist (List.filter_sublist.map Prod.fst) h

theorem optLookup_mergeOpts {V : Type} (base override : List (String × V)) (k : String) :
    optLookup (mergeOpts base override) k =
      (match optLookup override k with
       | some v => some v
       | none   => optLookup base k) := by
  unfold optLookup mergeOpts
  rw [List.find?_append]
  cases h : (override.find? (fun p => p.1 == k)) with
  | some pair => simp
  | none =>
    have hp : keyPresent override k = false := by
      have hiff := keyPresent_iff_lookup override k
      simp only [optLookup, h, Option.map_none] at hiff
      by_contra hc
      simp only [Bool.not_eq_false] at hc
      obtain ⟨v, hv⟩ := hiff.mp hc
      exact Option.noConfusion hv
    simp only [Option.none_or, Option.map_none]
    rw [List.find?_filter]
    have hpred : (fun a : String × V => decide ((!keyPresent override a.1) = true ∧ (a.1 == k) = true))
        = (fun p : String × V => p.1 == k) := by
      funext a
      by_cases hak : (a.1 == k) = true
      · have he : a.1 = k := by simpa using hak
        subst he
        simp [hp]
      · simp only [Bool.not_eq_true] at hak
        simp [hak]
    rw [hpred]

theorem options0_Nodup {V : Type} (base override : List (String × V)) :
    (base.map Prod.fst).Nodup → (override.map Prod.fst).Nodup →
    ((mergeOpts base override).map Prod.fst).Nodup := by
  intro hbase hoverride
  unfold mergeOpts
  rw [List.map_append, List.nodup_append]
  refine ⟨hoverride, (List.filter_sublist.map Prod.fst).nodup hbase, ?_⟩
  intro a ha b hb hab
  subst hab
  obtain ⟨q, hq_mem, hq_eq⟩ := List.mem_map.mp ha
  obtain ⟨p, hp_filter, hp_eq⟩ := List.mem_map.mp hb
  rw [List.mem_filter] at hp_filter
  obtain ⟨_, hpP⟩ := hp_filter
  have hpres : keyPresent override a = true := by
    unfold keyPresent
    rw [List.any_eq_true]
    exact ⟨q, hq_mem, by simp [hq_eq]⟩
  rw [hp_eq, hpres] at hpP
  simp at hpP

theorem loop_is_foldl {V : Type} (base override : List (String × V))
    (managedKeys : List String) :
    implementation_combineOptions base override managedKeys =
      List.foldl (stepFn override) (mergeOpts base override) managedKeys := by
  simp only [implementation_combineOptions, Id.run]
  generalize mergeOpts base override = init
  induction managedKeys generalizing init with
  | nil => rfl
  | cons k ks ih =>
    simp only [List.forIn_cons, List.foldl_cons, stepFn]
    split <;> exact ih _

theorem Inv_step {V : Type} (base override : List (String × V))
    (processed : List String) (acc : List (String × V)) (key : String) :
    CombineInv base override processed acc →
    CombineInv base override (processed ++ [key]) (stepFn override acc key) := by
  intro h
  obtain ⟨hnodup, hlook⟩ := h
  unfold stepFn
  by_cases hk : keyPresent override key = true
  · -- override mentions key: stepFn = acc
    simp only [hk, Bool.not_true, Bool.false_eq_true, if_false]
    refine ⟨hnodup, fun k => ?_⟩
    rw [hlook k]
    by_cases hkk : k = key
    · subst hkk
      simp [hk]
    · rw [List.contains_append, List.contains_cons]
      simp [hkk]
  · -- override silent about key: stepFn = dropKey acc key
    have hkf : keyPresent override key = false := by
      simpa using hk
    simp only [hkf, Bool.not_false, if_true]
    refine ⟨map_fst_dropKey_Nodup acc key hnodup, fun k => ?_⟩
    rw [optLookup_dropKey_eq acc key k, hlook k]
    by_cases hkk : k = key
    · subst hkk
      rw [List.contains_append, List.contains_cons]
      simp [hkf]
    · rw [List.contains_append, List.contains_cons]
      simp [hkk]

theorem foldl_preserves_Inv {V : Type} (base override : List (String × V))
    (processed_init : List String) (acc : List (String × V)) :
    CombineInv base override processed_init acc →
    ∀ (ks : List String),
      CombineInv base override (processed_init ++ ks)
        (List.foldl (stepFn override) acc ks) := by
  intro h ks
  induction ks generalizing processed_init acc with
  | nil => simpa using h
  | cons k rest ih =>
    have hstep := Inv_step base override processed_init acc k h
    have hrec := ih (processed_init ++ [k]) (stepFn override acc k) hstep
    simpa [List.append_assoc] using hrec

theorem result_Nodup {V : Type} (base override : List (String × V))
    (managedKeys : List String) :
    (base.map Prod.fst).Nodup → (override.map Prod.fst).Nodup →
    ((implementation_combineOptions base override managedKeys).map Prod.fst).Nodup := by
  intro h1 h2
  rw [loop_is_foldl]
  have hinit : CombineInv base override [] (mergeOpts base override) := by
    refine ⟨options0_Nodup base override h1 h2, ?_⟩
    intro k
    simp
  have h := foldl_preserves_Inv base override [] (mergeOpts base override) hinit managedKeys
  exact h.1

theorem lookup_eq_expected {V : Type} (base override : List (String × V))
    (managedKeys : List String) :
    (base.map Prod.fst).Nodup → (override.map Prod.fst).Nodup →
    ∀ k : String,
      optLookup (implementation_combineOptions base override managedKeys) k
        = expectedLookup base override managedKeys k := by
  intro hbase hover k
  rw [loop_is_foldl]
  have hinit : CombineInv base override [] (mergeOpts base override) := by
    refine ⟨options0_Nodup base override hbase hover, ?_⟩
    intro q
    simp
  have hfold := foldl_preserves_Inv base override [] (mergeOpts base override) hinit managedKeys
  obtain ⟨_, hlook⟩ := hfold
  have hk := hlook k
  simp only [List.nil_append] at hk
  rw [hk, optLookup_mergeOpts]
  unfold expectedLookup
  cases hov : optLookup override k with
  | some v =>
    have hpres : keyPresent override k = true := by
      rw [keyPresent_iff_lookup]; exact ⟨v, hov⟩
    simp [hpres]
  | none =>
    have hpres : keyPresent override k = false := by
      cases hh : keyPresent override k with
      | false => rfl
      | true =>
        exfalso
        rw [keyPresent_iff_lookup] at hh
        obtain ⟨v, hv⟩ := hh
        rw [hov] at hv
        exact Option.noConfusion hv
    simp [hpres]

theorem correct_combineOptions :
    ∀ {V : Type} (base override : List (String × V)) (managedKeys : List String),
      (base.map Prod.fst).Nodup →
      (override.map Prod.fst).Nodup →
      problem_spec_combineOptions base override managedKeys
        (implementation_combineOptions base override managedKeys) := by
  intro V base override managedKeys hbase hoverride
  refine ⟨result_Nodup base override managedKeys hbase hoverride, ?_⟩
  exact lookup_eq_expected base override managedKeys hbase hoverride

-- proof-end
