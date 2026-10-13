"""Twin-artifact model for pydata__xarray-6721.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A collection of array-bearing entries is inspected to report, per labelled
  axis, the block lengths of the entries that are stored in block form. Each
  entry wraps an underlying store which may or may not advertise a block
  structure. Two views of an entry's payload exist:

    * the UNDERLYING store, which can be inspected for a block structure
      cheaply and without ever pulling the payload into memory; and
    * the MATERIALISED payload, obtaining which forces a lazily-backed entry to
      pull its whole payload into memory (an observable, possibly very
      expensive or even impossible, side effect).

  The desired behaviour: deciding whether an entry is block-structured, and
  reading its block lengths, MUST consult the underlying store only, so that
  inspecting the collection NEVER materialises any lazily-backed entry. The
  reported mapping sends each axis carried by a block-structured entry to that
  entry's block length on the axis; entries whose underlying store advertises
  no block structure contribute nothing.

Entries are modelled as a minimal object carrying only the touched fields:
whether the underlying store advertises a block structure, whether obtaining
the materialised payload would force a load (i.e. the store is lazily backed),
the single axis label it carries, and its block length on that axis. Axis
labels and lengths are abstracted to ints (mapping.md gives the bijection).

The no-materialisation requirement is pinned by an UNFORGEABLE, CONSUMABLE
capability token `payload_intact`: every entry starts intact (its payload has
not been pulled into memory), and the result is required to leave every entry
intact. Inspecting an entry's UNDERLYING store reads it IN PLACE and preserves
the token; obtaining the MATERIALISED payload pulls the payload into memory and
CONSUMES the token without restoring it. The token is abstract (no body), so
nothing can fabricate or re-fold it once consumed. Hence a verifying
implementation can never have obtained the materialised payload of any entry:
the only way to keep every entry intact through to the result is to read every
block status in place. An implementation that materialises an entry (forcing a
load) -- even one that also reads the underlying store and reports a load count
of zero -- permanently loses that entry's token and cannot re-establish the
postcondition. A running "loads forced" tally, threaded through and required to
stay zero, additionally records that no materialisation happened.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Tuple
from nagini_contracts.contracts import *


class Entry:
    # One array-bearing entry of the inspected collection.
    #   block_backed : the UNDERLYING store advertises a block structure
    #   forces_load  : obtaining the MATERIALISED payload would force a load
    #                  (the store is lazily backed, not already in memory)
    #   axis         : the single axis label this entry carries
    #   length       : the entry's block length along that axis
    def __init__(self, block_backed: bool, forces_load: bool,
                 axis: int, length: int) -> None:
        self.block_backed = block_backed  # type: bool
        self.forces_load = forces_load    # type: bool
        self.axis = axis                  # type: int
        self.length = length              # type: int
        Ensures(Acc(self.block_backed) and Acc(self.forces_load))
        Ensures(Acc(self.axis) and Acc(self.length))
        Ensures(self.block_backed == block_backed)
        Ensures(self.forces_load == forces_load)
        Ensures(self.axis == axis and self.length == length)


# pure-start
@Pure
def block_load_cost(e: Entry) -> int:
    # Loads forced by inspecting an entry's block status via its MATERIALISED
    # payload: one when the store is lazily backed, none otherwise.
    Requires(Acc(e.forces_load, 1 / 8))
    return 1 if e.forces_load else 0
# pure-end


# axioms-start
# Abstract, CONSUMABLE capability token: held for an entry exactly while its
# payload has NOT been pulled into memory (the entry is "intact"). The token is
# abstract (no body), so nothing can `Fold` or otherwise fabricate it -- once
# consumed it is gone for good. `inspect_underlying` reads the entry in place
# and threads the token through unchanged (the entry stays intact);
# `inspect_materialised` REQUIRES the token but does not return it (obtaining
# the materialised payload pulls it into memory, consuming intactness). The
# whole inspection both requires and re-establishes the token for every entry
# (see `block_lengths_by_axis`), so a verifying implementation can never have
# materialised any entry: materialising one would permanently lose its token
# and leave the result-side obligation undischargeable -- regardless of what is
# written into the trailing load-count slot, and even if the underlying store
# is also read.
@ContractOnly
@Predicate
def payload_intact(e: Entry) -> bool:
    pass


# The two payload-view operations are unchanged library reads modelled as
# contract-only callees (mapping.md cites their provenance; axiom_check.py /
# G-AX validates each contract against the real xarray Variable semantics).
@ContractOnly
def inspect_underlying(e: Entry) -> Tuple[bool, int]:
    """Inspect the UNDERLYING store for a block structure. Returns the block
    status and the loads this forces -- always zero, because the underlying
    store is inspected in place without pulling the payload into memory. Reads
    in place, so the entry stays intact: the `payload_intact` token is required
    and returned unchanged."""
    Requires(Acc(e.block_backed, 1 / 8))
    Requires(payload_intact(e))
    Ensures(Acc(e.block_backed, 1 / 8))
    Ensures(payload_intact(e))
    Ensures(Result()[0] == e.block_backed)
    Ensures(Result()[1] == 0)


@ContractOnly
def inspect_materialised(e: Entry) -> Tuple[bool, int]:
    """Inspect the entry's block status via its MATERIALISED payload. Obtaining
    that payload forces a load on a lazily-backed entry (and a materialised
    payload, once in memory, never advertises a block structure of its own).
    Pulls the payload into memory, CONSUMING the `payload_intact` token: it is
    required but NOT returned, so the entry is no longer intact afterwards."""
    Requires(Acc(e.block_backed, 1 / 8) and Acc(e.forces_load, 1 / 8))
    Requires(payload_intact(e))
    Ensures(Acc(e.block_backed, 1 / 8) and Acc(e.forces_load, 1 / 8))
    # for an in-memory entry the materialised view agrees with the underlying
    # one; for a lazily-backed entry the materialised payload is a plain in-
    # memory array and advertises no block structure
    Ensures(Result()[0] == (e.block_backed and not e.forces_load))
    Ensures(Result()[1] == block_load_cost(e))
# axioms-end


def block_lengths_by_axis(entries: List[Entry]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(entries), 1 / 2))
    # every entry is a valid object exposing the touched fields (read-only)
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(entries),
        Acc(entries[k].block_backed, 1 / 8) and Acc(entries[k].forces_load, 1 / 8)
        and Acc(entries[k].axis, 1 / 8) and Acc(entries[k].length, 1 / 8)),
        [[entries[k]]])))
    # every entry enters the inspection intact: its payload has not been pulled
    # into memory
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(entries),
        payload_intact(entries[k])), [[entries[k]]])))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(entries), 1 / 2))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(entries),
        Acc(entries[k].block_backed, 1 / 8) and Acc(entries[k].forces_load, 1 / 8)
        and Acc(entries[k].axis, 1 / 8) and Acc(entries[k].length, 1 / 8)),
        [[entries[k]]])))
    Ensures(Acc(list_pred(Result())))
    # The result is a flat (axis, length) pair list, one slot pair per entry:
    # (Result()[2*i], Result()[2*i+1]) is the contribution of entry i. The
    # final slot, Result()[2*len(entries)], is the total loads forced by the
    # whole inspection and MUST be zero -- no lazily-backed entry is ever
    # materialised.
    Ensures(len(Result()) == 2 * len(entries) + 1)
    Ensures(Result()[2 * len(entries)] == 0)
    # UNFORGEABLE no-materialisation obligation: every entry is still intact --
    # its payload was never pulled into memory by the inspection. The
    # `payload_intact` token is consumable and cannot be fabricated; an
    # implementation that obtained the materialised payload of any entry
    # (forcing a load) consumes that entry's token and cannot re-establish this
    # clause -- regardless of what it writes into the trailing load-count slot,
    # and even if it also reads the underlying store. This pins the
    # no-materialisation behaviour the desired contract demands; the trailing
    # `== 0` slot alone would be an echoable constant.
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(entries),
        payload_intact(entries[k])), [[entries[k]]])))
    # block status and lengths come from the underlying store: an entry whose
    # underlying store is NOT block-structured contributes the empty marker
    # (-1, -1); a block-structured entry contributes its (axis, block length).
    Ensures(Forall(int, lambda k: (
        Implies(0 <= k and k < len(entries),
            Implies(not entries[k].block_backed,
                    Result()[2 * k] == -1 and Result()[2 * k + 1] == -1)
            and Implies(entries[k].block_backed,
                    Result()[2 * k] == entries[k].axis
                    and Result()[2 * k + 1] == entries[k].length)),
        [[entries[k]]])))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    loads = 0
    i = 0
    while i < len(entries):
        # invariants-start
        Invariant(Acc(list_pred(entries), 1 / 2))
        Invariant(0 <= i and i <= len(entries))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(entries),
            Acc(entries[k].block_backed, 1 / 8) and Acc(entries[k].forces_load, 1 / 8)
            and Acc(entries[k].axis, 1 / 8) and Acc(entries[k].length, 1 / 8)),
            [[entries[k]]])))
        Invariant(Acc(list_pred(result)))
        Invariant(len(result) == 2 * i)
        # only the not-yet-inspected entries remain intact: the pre-patch skeleton
        # has already materialised (consuming the token of) entries [0, i).
        Invariant(Forall(int, lambda k: (Implies(i <= k and k < len(entries),
            payload_intact(entries[k])), [[entries[k]]])))
        Invariant(Forall(int, lambda k: (
            Implies(0 <= k and k < i,
                Implies(not entries[k].block_backed,
                        result[2 * k] == -1 and result[2 * k + 1] == -1)
                and Implies(entries[k].block_backed,
                        result[2 * k] == entries[k].axis
                        and result[2 * k + 1] == entries[k].length)),
            [[entries[k]]])))
        # invariants-end
        e = entries[i]
        # Pre-patch skeleton: the block status is inspected via the MATERIALISED
        # payload, which forces a load on every lazily-backed entry and CONSUMES
        # its `payload_intact` token -- so neither the loads-tally clause nor the
        # `payload_intact` postcondition can be re-established (G-DIFF).
        probe = inspect_materialised(e)
        loads = loads + probe[1]
        if probe[0]:
            result = result + [e.axis, e.length]
        else:
            result = result + [-1, -1]
        i = i + 1
    result = result + [loads]
    return result
    # impl-end
