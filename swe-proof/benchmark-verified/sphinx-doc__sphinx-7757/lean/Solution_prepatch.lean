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
  -- Pre-patch (buggy) behavior: positional-only parameters never receive a
  -- default, and the positional-or-keyword parameters line their defaults up
  -- only among THEMSELVES — ignoring the positional-only group. A default that
  -- belongs to a positional-only parameter is therefore lost.
  let mut params : List (Option String) := []
  for _ in [0:nPosonly] do
    params := params ++ [none]
  for i in [0:nArgs] do
    if nArgs - i ≤ defaults.length then
      params := params ++ [some (defaults[defaults.length - (nArgs - i)]!)]
    else
      params := params ++ [none]
  return params
-- impl-end

-- proof-start
-- Gold proof body carried over from Solution.lean (SPEC_GUIDE §1.1). Against this
-- pre-patch impl it cannot close: the spec demands the supplied defaults occupy
-- the rightmost positions across the WHOLE positional run, so a positional-only
-- parameter among the rightmost ones must carry its default. This impl gives
-- every positional-only parameter `none` and aligns defaults only within the
-- positional-or-keyword group, so for e.g. nPosonly=2, nArgs=1, defaults=["0","1"]
-- it yields [none, none, some "1"] while the spec demands [none, some "0", some "1"].
-- (Construction phase: body left as `sorry`; the proof agent carries the closed
-- gold body here, where it fails to typecheck against the buggy impl — G-DIFF.)
theorem correct_positionalDefaults :
    ∀ (nPosonly nArgs : Nat) (defaults : List String),
      defaults.length ≤ nPosonly + nArgs →
      problem_spec_positionalDefaults nPosonly nArgs defaults
        (implementation_positionalDefaults nPosonly nArgs defaults) := by
  sorry
-- proof-end
