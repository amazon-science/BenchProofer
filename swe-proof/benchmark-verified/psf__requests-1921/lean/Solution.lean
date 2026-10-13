import Mathlib
-- imports-end

/-!
Combining a per-request mapping of options with a session-level mapping of
defaults into the single effective mapping used for a request.

The two mappings are ordered key/value collections (insertion order, unique
keys). A value may be a real value or the explicit *null* sentinel. The
effective mapping is obtained by taking the session defaults, letting the
per-request entries override them by key (a request entry replaces the value
for an existing key in place, or is appended for a new key), and then honoring
the null sentinel: any key the caller maps to null is suppressed from the
result. The exported guarantee is that the effective mapping never carries a
null-valued entry — null means "leave this out", regardless of whether the null
came from the per-request mapping or from the session defaults.
-/

-- axioms-start
-- (No unchanged opaque callee is consumed: the mapping operations are modeled
--  structurally as list operations, so there is no `_prop` axiom to declare.)
-- axioms-end

-- pure-start
/-- A key/value entry. The value is `some v` for a real value, or `none` for the
explicit null sentinel meaning "do not carry this key". -/
abbrev Entry := String × Option String

/-- Set `k` to `v` in an ordered mapping: if `k` is already present, replace its
value in place (preserving position); otherwise append the new entry at the end.
Mirrors updating an insertion-ordered mapping. -/
def dictSet (d : List Entry) (k : String) (v : Option String) : List Entry :=
  if d.any (fun p => p.1 == k) then
    d.map (fun p => if p.1 == k then (k, v) else p)
  else
    d ++ [(k, v)]

/-- Overlay one ordered mapping on top of another: start from `base` and apply
each entry of `overlay` in order, so `overlay` wins on shared keys. -/
def overlay (base overlay : List Entry) : List Entry :=
  overlay.foldl (fun acc p => dictSet acc p.1 p.2) base

/-- Drop, from `d`, every key that `keys` maps to the null sentinel. -/
def dropNulledKeys (keys d : List Entry) : List Entry :=
  keys.foldl (fun acc p => if p.2.isNone then acc.filter (fun q => q.1 != p.1) else acc) d

/-- The effective mapping: session defaults overlaid by the per-request entries,
with request-nulled keys removed, then with every remaining null-valued entry
removed. -/
def effective (req ses : List Entry) : List Entry :=
  (dropNulledKeys req (overlay ses req)).filter (fun q => q.2.isSome)
-- pure-end

-- post-conditions-start
/-- The result is exactly the effective mapping of the two inputs: the session
defaults overlaid by the per-request entries, with the null sentinel honored so
that no null-valued entry survives. Everything else (key set, surviving values,
relative order) is pinned to the inputs by `effective`. -/
def problem_spec_effectiveSetting
    (req ses : List Entry) (result : List Entry) : Prop :=
  result = effective req ses
-- post-conditions-end

-- impl-start
def implementation_effectiveSetting
    (req ses : List Entry) : List Entry := Id.run do
  -- Start from the session defaults, then let the per-request entries override.
  let mut merged : List Entry := ses
  for p in req do
    merged := dictSet merged p.1 p.2
  -- Honor keys the request maps to the null sentinel.
  for p in req do
    if p.2.isNone then
      merged := merged.filter (fun q => q.1 != p.1)
  -- Keep only entries that carry a real value.
  merged := merged.filter (fun q => q.2.isSome)
  return merged
-- impl-end

-- proof-start
theorem correct_effectiveSetting : ∀ (req ses : List Entry),
    problem_spec_effectiveSetting req ses
      (implementation_effectiveSetting req ses) := by
  intro req ses
  unfold problem_spec_effectiveSetting implementation_effectiveSetting effective
  -- helper for loop 1 (overlay)
  have loop1 : ∀ (xs : List Entry) (init : List Entry),
      (Id.run (forIn xs init (fun (p : Entry) (r : List Entry) =>
          (do
            pure PUnit.unit
            pure (ForInStep.yield (dictSet r p.1 p.2)) : Id (ForInStep (List Entry))))))
      = xs.foldl (fun acc p => dictSet acc p.1 p.2) init := by
    intro xs
    induction xs with
    | nil => intro init; rfl
    | cons a as ih =>
      intro init
      rw [List.forIn_cons, List.foldl_cons]
      simp only [Id.run, bind] at ih ⊢
      rw [ih]
  -- helper for loop 2 (dropNulledKeys)
  have loop2 : ∀ (xs : List Entry) (init : List Entry),
      (Id.run (forIn xs init (fun (p : Entry) (r : List Entry) =>
          (if p.2.isNone = true then
            (do
              pure PUnit.unit
              pure (ForInStep.yield (List.filter (fun q => q.1 != p.1) r)))
          else
            (do
              pure PUnit.unit
              pure (ForInStep.yield r)) : Id (ForInStep (List Entry))))))
      = xs.foldl (fun acc p => if p.2.isNone then acc.filter (fun q => q.1 != p.1) else acc) init := by
    intro xs
    induction xs with
    | nil => intro init; rfl
    | cons a as ih =>
      intro init
      rw [List.forIn_cons, List.foldl_cons]
      simp only [Id.run, bind] at ih ⊢
      by_cases h : a.2.isNone = true
      · simp only [h, if_true, ih]
      · simp only [h, ih, Bool.false_eq_true, if_false]
  simp only [Id.run, bind] at loop1 loop2 ⊢
  rw [loop1, loop2]
  rfl
-- proof-end
