import Mathlib
-- imports-end

/-!
Computing a quantile reduction of a labelled numeric array, with optional
preservation of the array's metadata attributes.

A source array carries:
  * a set of metadata attributes (`selfAttrs`) — key/value string pairs;
  * the value data and the dimension labels that survive the reduction.

The quantile reduction itself (the remaining dimension labels `newDims` and the
computed quantile value array `qs`) is supplied as input — it is independent of
the metadata question.  The behavior modeled here is the metadata contract:

  * an `attrs`-keeping request is either explicit (`some true` / `some false`) or
    unspecified (`none`);
  * when unspecified, it falls back to a caller-supplied default flag;
  * the result keeps the source attributes exactly when the resolved request is
    true, and otherwise carries no attributes;
  * the result's dimension labels and value data are exactly the supplied
    reduction (unchanged by the metadata choice).

A collection-level reduction applies the same reduction to each member array,
forwarding the SAME keep request to every member, so each member's attributes
are kept or dropped according to that one shared request.

Stated as input→output relations; the implementations and their correctness
proofs are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee needs a logical contract. The quantile
-- reduction (the remaining dimension labels and the computed value array) and
-- the resolved global default flag are taken as modeled inputs (`newDims`, `qs`,
-- `globalDefault`); they are unchanged by this behavior and exercised end-to-end
-- by the differential check. There is therefore no `axiom <callee>_prop` for the
-- proofs to consume.

/-- A metadata attribute mapping, abstracted to the only property observed here:
identity (equality). Modeled as its list of key/value string pairs. -/
abbrev Attrs := List (String × String)

/-- The result of a quantile reduction:
* `dims`  — the dimension labels that remain after the reduction;
* `data`  — the computed quantile value array (modeled as integer values);
* `attrs` — the kept metadata attributes, or none when not kept. -/
structure QResult where
  dims : List String
  data : List Int
  attrs : Option Attrs
deriving DecidableEq, Repr

/-- A source array as seen by a collection-level reduction: its surviving
dimension labels, its computed quantile value array, and its metadata. -/
structure SrcArray where
  dims : List String
  qs : List Int
  attrs : Attrs
deriving DecidableEq, Repr
-- axioms-end

-- pure-start
/-- Resolve an attribute-keeping request: an explicit choice when given,
otherwise the supplied default flag. -/
def resolveKeepAttrs (keepAttrs : Option Bool) (globalDefault : Bool) : Bool :=
  keepAttrs.getD globalDefault
-- pure-end

-- post-conditions-start
/-- The single-array quantile result as a function of the inputs:

* `dims` and `data` are exactly the supplied reduction (`newDims`, `qs`) — the
  metadata choice does not touch them;
* `attrs` is the source attributes when the resolved keep request is true, and
  none otherwise. -/
def problem_spec_arrayQuantile
    (newDims : List String) (qs : List Int) (selfAttrs : Attrs)
    (keepAttrs : Option Bool) (globalDefault : Bool)
    (result : QResult) : Prop :=
  result.dims = newDims ∧
  result.data = qs ∧
  result.attrs =
    (if resolveKeepAttrs keepAttrs globalDefault then some selfAttrs else none)
-- post-conditions-end

-- impl-start
def implementation_arrayQuantile
    (newDims : List String) (qs : List Int) (selfAttrs : Attrs)
    (keepAttrs : Option Bool) (globalDefault : Bool) : QResult := Id.run do
  -- default the keep request from the supplied default flag when unspecified
  let mut keep := keepAttrs
  if keep.isNone then
    keep := some globalDefault
  let attrs := if keep.getD globalDefault then some selfAttrs else none
  return { dims := newDims, data := qs, attrs := attrs }
-- impl-end

-- proof-start
/-- Closed form of the single-array implementation: the loop just resolves the
keep request, so the result is the supplied reduction with attributes kept iff
the resolved request is true.  Proved by case split on `keepAttrs`; each branch
is definitionally the spec's `if`. -/
theorem arrayQuantile_eq
    (newDims : List String) (qs : List Int) (selfAttrs : Attrs)
    (keepAttrs : Option Bool) (globalDefault : Bool) :
    implementation_arrayQuantile newDims qs selfAttrs keepAttrs globalDefault =
      { dims := newDims, data := qs,
        attrs := if resolveKeepAttrs keepAttrs globalDefault then some selfAttrs else none } := by
  cases keepAttrs <;> rfl

theorem correct_arrayQuantile :
    ∀ (newDims : List String) (qs : List Int) (selfAttrs : Attrs)
      (keepAttrs : Option Bool) (globalDefault : Bool),
      problem_spec_arrayQuantile newDims qs selfAttrs keepAttrs globalDefault
        (implementation_arrayQuantile newDims qs selfAttrs keepAttrs globalDefault) := by
  intro newDims qs selfAttrs keepAttrs globalDefault
  unfold problem_spec_arrayQuantile
  rw [arrayQuantile_eq]
  exact ⟨rfl, rfl, rfl⟩
-- proof-end

-- post-conditions-start
/-- The collection-level quantile result: each member array is reduced with the
SAME keep request forwarded to every member.  So each member result has the
member's own surviving dims and value data, and keeps the member's attributes
exactly when the one shared resolved request is true. -/
def problem_spec_collectionQuantile
    (arrays : List SrcArray) (keepAttrs : Option Bool) (globalDefault : Bool)
    (result : List QResult) : Prop :=
  result = arrays.map (fun a =>
    { dims := a.dims, data := a.qs,
      attrs := if resolveKeepAttrs keepAttrs globalDefault then some a.attrs else none })
-- post-conditions-end

-- impl-start
def implementation_collectionQuantile
    (arrays : List SrcArray) (keepAttrs : Option Bool)
    (globalDefault : Bool) : List QResult := Id.run do
  let mut out : Array QResult := #[]
  for a in arrays do
    -- forward the SAME keep request to each member array's reduction
    let r := implementation_arrayQuantile a.dims a.qs a.attrs keepAttrs globalDefault
    out := out.push r
  return out.toList
-- impl-end

-- proof-start
/-- The accumulator loop (in its desugared `forIn` form, generalized over the
running accumulator) appends each member's single-array reduction.  Route B
induction on the list. -/
theorem collectionQuantile_forIn
    (arrays : List SrcArray) (keepAttrs : Option Bool) (globalDefault : Bool)
    (init : Array QResult) :
    (forIn arrays init (fun a r => do
        pure PUnit.unit
        pure (ForInStep.yield
          (r.push (implementation_arrayQuantile a.dims a.qs a.attrs keepAttrs globalDefault))))
        : Id (Array QResult)).run.toList
    = init.toList ++ arrays.map (fun a =>
        { dims := a.dims, data := a.qs,
          attrs := if resolveKeepAttrs keepAttrs globalDefault then some a.attrs else none }) := by
  induction arrays generalizing init with
  | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    rw [ih, arrayQuantile_eq, Array.toList_push]
    simp

theorem correct_collectionQuantile :
    ∀ (arrays : List SrcArray) (keepAttrs : Option Bool) (globalDefault : Bool),
      problem_spec_collectionQuantile arrays keepAttrs globalDefault
        (implementation_collectionQuantile arrays keepAttrs globalDefault) := by
  intro arrays keepAttrs globalDefault
  unfold problem_spec_collectionQuantile implementation_collectionQuantile
  have h := collectionQuantile_forIn arrays keepAttrs globalDefault #[]
  simpa [Id.run] using h
-- proof-end
