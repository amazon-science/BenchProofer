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
    -- Pre-patch skeleton: the reordering branch regenerates the canonical
    -- solution set in the DEFAULT (base-only) mode rather than under the
    -- caller's `permute` mode, so the mode is not propagated.
    let mut acc : List (List Int) := []
    for t in solveCanonical eq false do
      acc := acc ++ [reindexTuple var syms t]
    return acc
  return solveCanonical eq permute
-- impl-end

-- proof-start
theorem correct_diophantine :
    ∀ (eq : Equation) (var syms : List Nat) (permute : Bool),
      problem_spec_diophantine eq var syms permute
        (implementation_diophantine eq var syms permute) := by
  sorry   -- carries the gold proof body; UNCLOSABLE against the buggy impl (G-DIFF)
-- proof-end
