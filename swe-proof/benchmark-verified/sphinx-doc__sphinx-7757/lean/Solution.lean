import Mathlib
-- imports-end

/-!
Attaching default values to the positional parameters of a parsed function
signature.

A function's positional parameters come in two consecutive groups: first the
positional-only parameters (there are `nPosonly` of them), then the
positional-or-keyword parameters (there are `nArgs` of them). Separately, the
signature supplies a list of default-value expressions. By the usual rule for
positional parameters, the supplied defaults fill the parameters from the right:
the LAST `defaults.length` positional parameters carry the given defaults, in
order, and every earlier positional parameter has no default.

This holds across the WHOLE positional run — the positional-only group and the
positional-or-keyword group are treated as one sequence for the purpose of lining
defaults up with parameters. So when a positional-only parameter is among the
rightmost ones, it keeps its default just like a positional-or-keyword parameter
would.

The result reports, for each positional parameter in order (positional-only
parameters first, then positional-or-keyword parameters), the default it carries:
`some d` when it has default expression `d`, or `none` when it has no default.
-/

-- axioms-start
-- No UNCHANGED callee needs an `opaque` signature here. The modeled behavior is
-- the pure alignment of supplied default-value expressions to positional
-- parameters; the parser that produces the parameter groups and default
-- expressions, and the routine that renders a default expression back to text,
-- are modeled by the abstract inputs directly (a count of each parameter group
-- and the list of default expressions as text). No `axiom <callee>_prop` is
-- consumed by the proof.
-- axioms-end

-- pure-start
-- (no shared pure helpers needed)
-- pure-end

-- post-conditions-start
/-- Specification of the default carried by each positional parameter.

`nPosonly` is the number of positional-only parameters, `nArgs` the number of
positional-or-keyword parameters, and `defaults` the supplied default-value
expressions (as text), which fill the rightmost positional parameters.

`result` lists, for each of the `nPosonly + nArgs` positional parameters in order
(positional-only first, then positional-or-keyword), `some d` if it carries
default expression `d`, otherwise `none`. The supplied defaults occupy the last
`defaults.length` positions in order, and every earlier position has no default —
hence the result is `defaults.length` fewer-than-`nPosonly+nArgs` `none`s followed
by the defaults wrapped in `some`. -/
def problem_spec_positionalDefaults
    (nPosonly nArgs : Nat) (defaults : List String)
    (result : List (Option String)) : Prop :=
  result = List.replicate (nPosonly + nArgs - defaults.length) none
            ++ defaults.map some
-- post-conditions-end

-- impl-start
def implementation_positionalDefaults
    (nPosonly nArgs : Nat) (defaults : List String) : List (Option String) := Id.run do
  let positionals := nPosonly + nArgs
  -- Start from the supplied defaults and left-pad with "no default" until there
  -- is one entry per positional parameter; the defaults thus land on the
  -- rightmost positions across the whole positional run.
  let mut padded : List (Option String) := defaults.map some
  for _ in [padded.length:positionals] do
    padded := none :: padded
  return padded
-- impl-end

-- proof-start
theorem correct_positionalDefaults :
    ∀ (nPosonly nArgs : Nat) (defaults : List String),
      defaults.length ≤ nPosonly + nArgs →
      problem_spec_positionalDefaults nPosonly nArgs defaults
        (implementation_positionalDefaults nPosonly nArgs defaults) := by
  intro nPosonly nArgs defaults _h
  unfold problem_spec_positionalDefaults implementation_positionalDefaults
  simp only [List.length_map, bind_pure_comp, map_pure, Std.Range.forIn_eq_forIn_range',
    Std.Range.size, add_tsub_cancel_right, Nat.div_one, List.forIn_pure_yield_eq_foldl,
    List.foldl_flip_cons_eq_append, List.map_const', List.length_range', List.reverse_replicate,
    bind_pure, Id.run_pure]
-- proof-end
