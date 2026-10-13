import Mathlib
-- imports-end

-- axioms-start
/-- An opaque carrier for the equation being solved. Only its identity matters
to the modeled behavior; nothing is assumed about its internals. -/
opaque Equation : Type

/-- The canonical solver: it returns the complete list of integer solution
tuples for an equation, with each tuple ordered according to the canonical
ordering of the equation's variables. Its boolean argument selects the
solution-generation mode: when `false`, only the base family of solutions is
produced; when `true`, the additionally admissible solutions are produced as
well. This is an UNCHANGED subroutine the modeled behavior delegates to; the
proof consumes no property of it, so it carries only a signature (no `_prop`
axiom). -/
opaque solveCanonical : Equation → Bool → List (List Int)
-- axioms-end

-- pure-start
/-- Rearrange a single solution tuple from canonical variable order into the
requested symbol order. `var` lists the equation's variables in canonical
order; `syms` lists the requested output order of those same variables. For
each canonical position `i`, the value is read from the tuple at the position
that `i` occupies within `syms`. -/
def reindexTuple (var syms : List Nat) (t : List Int) : List Int :=
  var.map (fun i => t.getD (syms.idxOf i) 0)

/-- Front-recursive specification fold: rearrange every solution tuple of a
solution list, preserving order. -/
def reindexAll (var syms : List Nat) : List (List Int) → List (List Int)
  | [] => []
  | t :: ts => reindexTuple var syms t :: reindexAll var syms ts
-- pure-end

-- post-conditions-start
/-- Desired behavior of solving for the requested symbol order.

`var` is the equation's variables in canonical order; `syms` is the requested
output order; `permute` is the solution-generation mode.

When the requested order differs from the canonical order, the result is the
complete canonical solution set — generated under the SAME `permute` mode —
with every tuple rearranged into the requested order. When the requested order
already matches the canonical order, the result is the canonical solution set
itself (under the same `permute` mode). In particular the solution-generation
mode applies identically whether or not a reordering is requested. -/
def problem_spec_diophantine
    (eq : Equation) (var syms : List Nat) (permute : Bool)
    (result : List (List Int)) : Prop :=
  result =
    (if syms ≠ var then reindexAll var syms (solveCanonical eq permute)
     else solveCanonical eq permute)
-- post-conditions-end

-- impl-start
def implementation_diophantine
    (eq : Equation) (var syms : List Nat) (permute : Bool) :
    List (List Int) := Id.run do
  if syms ≠ var then
    let mut acc : List (List Int) := []
    for t in solveCanonical eq permute do
      acc := acc ++ [reindexTuple var syms t]
    return acc
  return solveCanonical eq permute
-- impl-end

-- proof-start
/-- `reindexAll` is exactly `List.map (reindexTuple var syms)`. -/
private theorem reindexAll_eq_map (var syms : List Nat) (xs : List (List Int)) :
    reindexAll var syms xs = xs.map (reindexTuple var syms) := by
  induction xs with
  | nil => rfl
  | cons a as ih => simp [reindexAll, ih]

/-- The imperative loop, generalized over the accumulator, appends the mapped
tuples onto the initial accumulator. -/
private theorem loop_helper (var syms : List Nat) (xs init : List (List Int)) :
    Id.run (forIn xs init
        (fun t r => ForInStep.yield (r ++ [reindexTuple var syms t])))
      = init ++ xs.map (reindexTuple var syms) := by
  induction xs generalizing init with
  | nil => simp
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    rw [ih]
    simp

theorem correct_diophantine :
    ∀ (eq : Equation) (var syms : List Nat) (permute : Bool),
      problem_spec_diophantine eq var syms permute
        (implementation_diophantine eq var syms permute) := by
  intro eq var syms permute
  unfold problem_spec_diophantine implementation_diophantine
  by_cases h : syms ≠ var
  · rw [if_pos h, if_pos h]
    -- bridge the desugared `do` loop body to the clean `forIn` form of `loop_helper`
    have hbridge :
        Id.run (do
          let r ← forIn (solveCanonical eq permute) ([] : List (List Int))
            (fun t r => do
              pure PUnit.unit
              pure (ForInStep.yield (r ++ [reindexTuple var syms t])))
          pure r)
        = Id.run (forIn (solveCanonical eq permute) ([] : List (List Int))
            (fun t r => ForInStep.yield (r ++ [reindexTuple var syms t]))) := rfl
    rw [hbridge, loop_helper, reindexAll_eq_map]
    simp
  · rw [if_neg h, if_neg h]
    rfl
-- proof-end
