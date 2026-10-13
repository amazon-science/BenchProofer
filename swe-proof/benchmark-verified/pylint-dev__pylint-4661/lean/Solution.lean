import Mathlib
-- imports-end

-- axioms-start
/-- The platform-specific per-application *cache* directory for an application of
the given name. This is an UNCHANGED standard-library facility the computation
delegates to; its concrete value depends on the operating system and the user's
environment, so it is left abstract here (a signature only). No property of it is
consumed by the proof — the result is returned verbatim. -/
opaque platformCacheDir : String → String
-- axioms-end

-- pure-start
-- No additional functional helpers are needed: the decision is a direct,
-- three-way selection on the two inputs.
-- pure-end

-- post-conditions-start
/-- The persistent-data home directory is selected from two inputs: an optional
explicit override (an environment-provided path) and the resolved user home
directory (which is the literal `"~"` when it cannot be resolved).

* If an explicit override is provided, it is used verbatim.
* Otherwise, if the user home cannot be resolved, a bare relative directory
  name (`".pylint.d"`) in the current working directory is used.
* Otherwise the application's platform-specific per-application cache directory
  is used.

Every component of the result is pinned to the inputs, so no other value can
satisfy the predicate. -/
def problem_spec_pylintHome
    (envHome : Option String) (userHome : String) (result : String) : Prop :=
  result =
    (match envHome with
     | some h => h
     | none => if userHome = "~" then ".pylint.d" else platformCacheDir "pylint")
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
