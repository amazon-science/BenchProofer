import Mathlib
-- imports-end

/-!
Releasing a dimension index from a labelled multi-dimensional container.

A container tracks three name collections over the same underlying axes:

  * `varNames`   — the stored data/coordinate variables, by name;
  * `coordNames` — the subset of those names that are coordinates;
  * `indexNames` — the names that currently carry a fast lookup index.

A core invariant ties them together: every coordinate name must also be a stored
variable name (`coordNames ⊆ varNames`). When a dimension index is released, the
container must preserve that invariant.

This models releasing one or more *plain dimension indexes* — each a lookup index
whose only associated coordinate is the dimension's own name. Releasing such a
name always removes its lookup index. A boolean `drop` then decides the fate of
the underlying coordinate:

  * when `drop` is true, the coordinate is discarded — its name leaves BOTH the
    stored variables and the coordinate set together, so the invariant is kept;
  * when `drop` is false, the coordinate is retained as an ordinary stored
    variable — its name stays in both collections unchanged.

The desired behaviour is stated abstractly as an input→output relation over the
three name collections; the implementation and correctness proof are supplied
separately.
-/

-- axioms-start
-- The set of coordinate names sharing one dimension index is, for a plain
-- dimension index, exactly the singleton of that index's own name; this is
-- modeled DEEPLY as the literal singleton (a deep-model reference, not a
-- consumed callee contract). Converting a retained coordinate to an ordinary
-- stored variable changes only its internal kind, never its name, so it is the
-- identity on the name-collection abstraction. No separate property of an
-- unchanged callee is consumed by the proof, so there is no `opaque`/`axiom`
-- callee declaration here.
-- axioms-end

-- pure-start
/-- A labelled container observed through the only features that determine the
result of releasing a dimension index: the names of its stored variables, the
names that are coordinates, and the names that carry a lookup index. -/
structure ContainerNames where
  /-- names of all stored variables -/
  varNames : List String
  /-- names that are coordinates (must be a sub-collection of `varNames`) -/
  coordNames : List String
  /-- names that currently carry a lookup index -/
  indexNames : List String
deriving Repr, DecidableEq

/-- Drop from `xs` every name occurring in `ys`, preserving the order of the
names that remain. -/
def removeAll (xs ys : List String) : List String :=
  xs.filter (fun k => ¬ ys.contains k)
-- pure-end

-- post-conditions-start
/-- Releasing the plain dimension indexes named in `resetNames` (with flag
`drop`). The names whose coordinates are discarded are exactly `resetNames` when
`drop` is true and none otherwise. The result is pinned in full (directive 5
frame; directive 8 grounded in the input collections):

  * every released name loses its lookup index;
  * a discarded coordinate's name leaves the stored variables AND the coordinate
    set together — so the invariant `coordNames ⊆ varNames` is preserved;
  * when nothing is discarded, the stored variables and coordinate set are
    unchanged. -/
def problem_spec_resetIndexCoords
    (c : ContainerNames) (resetNames : List String) (drop : Bool)
    (result : ContainerNames) : Prop :=
  let dropVariables := if drop then resetNames else ([] : List String)
  result.indexNames = removeAll c.indexNames resetNames ∧
  result.varNames   = removeAll c.varNames dropVariables ∧
  result.coordNames = removeAll c.coordNames dropVariables
-- post-conditions-end

-- impl-start
def implementation_resetIndexCoords
    (c : ContainerNames) (resetNames : List String) (drop : Bool) :
    ContainerNames := Id.run do
  let mut dropIndexes : List String := []
  let mut dropVariables : List String := []
  for name in resetNames do
    -- the coordinate names sharing this plain dimension index: just `name`
    dropIndexes := dropIndexes ++ [name]
    -- discard-or-convert the underlying coordinate
    if drop then
      dropVariables := dropVariables ++ [name]
  let indexNames := removeAll c.indexNames dropIndexes
  let varNames := removeAll c.varNames dropVariables
  let coordNames := removeAll c.coordNames dropVariables
  return { varNames := varNames, coordNames := coordNames, indexNames := indexNames }
-- impl-end

-- proof-start
-- @decl:loopState-start
/-- The pair state threaded through the `for` loop, in the program's declaration
order: `dropIndexes` first, `dropVariables` second. -/
def loopState : Type := List String × List String
-- @decl:loopState-end

-- @decl:loopBody-start
/-- The per-iteration transition of the loop body: append the current `name` to
`dropIndexes`, and (only when `drop`) also to `dropVariables`. -/
def loopBody (drop : Bool) (name : String) (s : List String × List String) :
    ForInStep (List String × List String) :=
  ForInStep.yield (s.1 ++ [name], if drop then s.2 ++ [name] else s.2)
-- @decl:loopBody-end

-- @ns:loop_closed_form-start
-- @decl:loop_closed_form-start
/-- Closed form of the loop's tuple accumulator: folding `loopBody` over
`resetNames` from `(di, dv)` yields `(di ++ resetNames, dv ++ (if drop then
resetNames else []))`. Stated over the FULL tuple (declaration order) so it
unifies with the desugared `forIn`. -/
theorem loop_closed_form (drop : Bool) (resetNames di dv : List String) :
    (forIn resetNames (di, dv) (fun name s => loopBody drop name s) :
        Id (List String × List String))
      = (di ++ resetNames, dv ++ (if drop then resetNames else ([] : List String))) := by
  induction resetNames generalizing di dv with
  | nil => rw [List.forIn_nil]; simp [pure]
  | cons name rest ih =>
    rw [List.forIn_cons]
    show (forIn rest (di ++ [name], if drop then dv ++ [name] else dv)
            (fun name s => loopBody drop name s) : Id _) = _
    rw [ih]
    cases drop with
    | true => simp [List.append_assoc]
    | false => simp [List.append_assoc]
-- @decl:loop_closed_form-end
-- @ns:loop_closed_form-end

-- @ns:reduce_impl-start
-- @decl:reduce_impl-start
/-- Evaluate the implementation to the explicit record built from the closed-form
accumulators. -/
theorem reduce_impl (c : ContainerNames) (resetNames : List String) (drop : Bool) :
    implementation_resetIndexCoords c resetNames drop
      = { varNames := removeAll c.varNames (if drop then resetNames else ([] : List String)),
          coordNames := removeAll c.coordNames (if drop then resetNames else ([] : List String)),
          indexNames := removeAll c.indexNames resetNames } := by
  unfold implementation_resetIndexCoords
  simp only [Id.run, bind, pure]
  have key : ∀ (l di dv : List String),
      (forIn l (⟨di, dv⟩ : MProd (List String) (List String))
        (fun name r => if drop = true then ForInStep.yield ⟨r.1 ++ [name], r.2 ++ [name]⟩
          else ForInStep.yield ⟨r.1 ++ [name], r.2⟩) : Id (MProd (List String) (List String)))
      = ⟨di ++ l, dv ++ (if drop then l else ([] : List String))⟩ := by
    intro l
    induction l with
    | nil => intro di dv; cases drop <;>
        simp only [List.forIn_nil, List.append_nil, if_true, if_false, Bool.false_eq_true] <;> rfl
    | cons a t ih =>
        intro di dv
        rw [List.forIn_cons]
        cases drop <;>
          · show forIn t _ _ = _
            rw [ih]
            simp [List.append_assoc]
  rw [key]
  simp
-- @decl:reduce_impl-end
-- @ns:reduce_impl-end

-- @ns:match_spec-start
-- @decl:match_spec-start
/-- The concrete record produced by `reduce_impl` satisfies the specification:
all three postcondition conjuncts hold. -/
theorem match_spec (c : ContainerNames) (resetNames : List String) (drop : Bool) :
    problem_spec_resetIndexCoords c resetNames drop
      { varNames := removeAll c.varNames (if drop then resetNames else ([] : List String)),
        coordNames := removeAll c.coordNames (if drop then resetNames else ([] : List String)),
        indexNames := removeAll c.indexNames resetNames } := by
  refine ⟨rfl, rfl, rfl⟩
-- @decl:match_spec-end
-- @ns:match_spec-end


theorem correct_resetIndexCoords :
    ∀ (c : ContainerNames) (resetNames : List String) (drop : Bool),
    problem_spec_resetIndexCoords c resetNames drop
      (implementation_resetIndexCoords c resetNames drop) := by
  intro c resetNames drop
  rw [reduce_impl]
  exact match_spec c resetNames drop
-- proof-end
