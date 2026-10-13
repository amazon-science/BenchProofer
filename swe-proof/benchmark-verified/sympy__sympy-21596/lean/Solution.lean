import Mathlib
-- imports-end

/-!
Selecting the real members of a parametrized family of complex values.

A family of complex values is indexed by a *parameter* drawn from a base set of
parameters (for example, the integers). Each value is built from the parameter by
a single rule; the value is *real* exactly when its imaginary part vanishes, and it
is *defined* only when none of the rule's denominators vanish.

The imaginary part of the value, as a function of the parameter, factors into a
list of simpler factors; the imaginary part vanishes precisely when at least one
factor vanishes. Likewise the value is undefined precisely when at least one
denominator factor vanishes.

The set of parameters that yield a real, defined value is therefore obtained from
the base set of parameters by *keeping* those parameters at which some
imaginary-part factor vanishes (an intersection with the union of the factors'
zero sets), and then *removing* those parameters at which some denominator factor
vanishes (a difference against the union of the denominators' zero sets).

This pins the exact set of surviving parameters as a function of the base set and
the two factor lists; nothing in the result is left free. The family-building rule
itself is the unchanged, monotone outer wrapper applied to this parameter set and
is modeled away (refinement.md).
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The quantity modeled — the
-- set of surviving parameters — is built directly from the base parameter set and
-- the two lists of factor functions by ordinary set operations (union over a
-- factor list, then one intersection and one difference). The per-factor
-- zero-set construction is modeled deeply by `zeroUnion` below (refinement.md
-- tags it R, an A-reference modeled in-spec), so no `opaque`/`axiom` callee
-- contract is required. The family-building rule applied to the parameter set is
-- an unchanged, monotone outer wrapper that is modeled away, so it needs no
-- contract either.
-- axioms-end

-- pure-start
/-- The union of the zero sets of a list of factor functions: the set of points
at which *at least one* factor vanishes. Front-recursive so a `for`-accumulator
loop matches it by Route-B induction. -/
def zeroUnion : List (ℚ → ℚ) → Set ℚ
  | []      => ∅
  | f :: fs => {x | f x = 0} ∪ zeroUnion fs
-- pure-end

-- post-conditions-start
/-- The result is exactly the set of parameters drawn from `base` that survive:
keep those at which some `vanish` factor is zero (intersection with the union of
their zero sets), then drop those at which some `poles` factor is zero (difference
against the union of their zero sets). The single output set is fully pinned to
the three inputs. -/
def problem_spec_realParams
    (base : Set ℚ) (vanish poles : List (ℚ → ℚ)) (result : Set ℚ) : Prop :=
  result = (base ∩ zeroUnion vanish) \ zeroUnion poles
-- post-conditions-end

-- impl-start
def implementation_realParams
    (base : Set ℚ) (vanish poles : List (ℚ → ℚ)) : Set ℚ := Id.run do
  -- union of the imaginary-part factors' zero sets
  let mut sols1 : Set ℚ := ∅
  for f in vanish do
    sols1 := sols1 ∪ {x | f x = 0}
  -- keep the base parameters that make the value real
  let mut base_set := base ∩ sols1
  -- union of the denominator factors' zero sets
  let mut sols2 : Set ℚ := ∅
  for d in poles do
    sols2 := sols2 ∪ {x | d x = 0}
  -- drop the parameters that make the value undefined
  base_set := base_set \ sols2
  return base_set
-- impl-end

-- proof-start
/-- The `for`-accumulator loop builds, from `init`, the union of `init` with the
front-recursive `zeroUnion` of the factor list. Generalized over the accumulator
so the Route-B induction goes through. -/
theorem fold_zeroUnion (xs : List (ℚ → ℚ)) (init : Set ℚ) :
    (forIn (m := Id) xs init (fun f r =>
        pure (ForInStep.yield (r ∪ {x | f x = 0})))) = init ∪ zeroUnion xs := by
  induction xs generalizing init with
  | nil => simp only [List.forIn_nil, zeroUnion, Set.union_empty]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [bind, pure] at ih ⊢
    rw [ih]
    simp only [zeroUnion, Set.union_assoc]

theorem correct_realParams :
    ∀ (base : Set ℚ) (vanish poles : List (ℚ → ℚ)),
      problem_spec_realParams base vanish poles
        (implementation_realParams base vanish poles) := by
  intro base vanish poles
  unfold problem_spec_realParams implementation_realParams
  simp only [Id.run, bind]
  rw [fold_zeroUnion, fold_zeroUnion]
  simp only [Set.empty_union]
  rfl
-- proof-end
