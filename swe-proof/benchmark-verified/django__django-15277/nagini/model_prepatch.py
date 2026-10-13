"""Twin-artifact model for django__django-15277.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A text field is constructed with an optional maximum-length attribute. During
  construction the field assembles the list of length-validators that will run
  whenever a candidate value is later cleaned. A length-validator carries a
  numeric limit and, when it runs, compares the candidate's length against that
  limit; the comparison is only meaningful when the limit is a concrete number.

  The behaviour pinned here:

    (1) When no maximum length is supplied, the field assembles NO length
        validator: the assembled list is empty. (A length validator with an
        absent limit could not perform its numeric comparison.)
    (2) When a maximum length IS supplied, the field assembles exactly one
        length validator whose limit equals the supplied maximum, so that
        length checking is still performed for fields that declare a maximum.
    (3) Consequently, cleaning an arbitrary candidate value against a freshly
        constructed field of this kind always completes normally — running the
        assembled validators never fails on an absent limit — regardless of
        whether a maximum length was supplied.

A length validator is characterised, for the behaviour observed here, entirely
by its numeric limit; the assembled validator list is therefore modelled as a
``List[Optional[int]]`` of limits (an element is the limit of one assembled
length validator; an absent limit is ``None``). The maximum-length attribute is
``Optional[int]``. The failure of a length comparison against an absent limit is
a user-defined exception (a builtin exception in an ``Exsures`` crashes the
Nagini translator; mapping.md §2).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class LimitComparisonError(Exception):
    """Signals that a length validator was asked to compare a candidate's
    length against an absent (``None``) limit — the comparison is undefined.
    Stands in for the ``TypeError`` such a comparison raises in reality (a
    builtin exception in an ``Exsures`` crashes the Nagini translator;
    mapping.md §2)."""
    pass


# axioms-start
# (no axiomatized callees: the validator-assembly decision and the length
# comparison the cleaning step performs are both modelled deeply below. Every
# other operation the real constructor / cleaning path delegates to is
# unchanged, independent of the limit-present/absent decision, and unobserved
# by this specification.)
# axioms-end


# pure-start
# (no module-level pure helpers required: the assembled-list properties are
# stated directly in the contracts via quantification over the result.)
# pure-end


def compare_length(value_length: int, limit: Optional[int]) -> bool:
    # pre-conditions-start
    # `value_length` is the candidate's length; `limit` is one validator's
    # numeric limit. Both are immutable scalars (no heap permission needed).
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The comparison completes normally ONLY when the limit is a concrete
    # number; when it is, the result is the ordinary "exceeds the limit" test.
    Ensures(limit is not None)
    Ensures(Result() == (value_length > limit))
    # A length comparison against an absent limit is undefined and is signalled
    # to the caller rather than producing a value.
    Exsures(LimitComparisonError, limit is None)
    # post-conditions-end
    # impl-start
    if limit is None:
        raise LimitComparisonError()
    return value_length > limit
    # impl-end


def build_char_validators(max_length: Optional[int]) -> List[Optional[int]]:
    # pre-conditions-start
    # `max_length` is the optional maximum-length attribute (immutable scalar).
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # No assembled length validator has an absent limit: every assembled
    # validator can perform its numeric comparison.
    Ensures(Forall(int, lambda k: (
        Implies(0 <= k and k < len(Result()), Result()[k] is not None))))
    # When no maximum length is supplied, no length validator is assembled.
    Ensures(Implies(max_length is None, len(Result()) == 0))
    # When a maximum length IS supplied, exactly one length validator is
    # assembled and its limit equals the supplied maximum (length checking is
    # preserved for fields that declare a maximum).
    Ensures(Implies(max_length is not None,
                    len(Result()) == 1 and Result()[0] == max_length))
    # post-conditions-end
    # impl-start
    validators = []  # type: List[Optional[int]]
    validators.append(max_length)
    return validators
    # impl-end


def clean_charfield(max_length: Optional[int], value_length: int) -> bool:
    # pre-conditions-start
    # `max_length` is the field's optional maximum-length attribute;
    # `value_length` is the length of the candidate value being cleaned. Both
    # are immutable scalars (no heap permission needed).
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    # Cleaning a candidate against a freshly constructed field always completes
    # normally: there is no Exsures clause, so running the assembled validators
    # must be PROVABLY non-raising for every `max_length` (including absent).
    # The result reports whether the assembled length validator flagged the
    # candidate as exceeding its limit: when no maximum is supplied no validator
    # runs, so nothing is ever flagged; when a maximum IS supplied the single
    # assembled validator runs and flags iff the candidate's length exceeds the
    # maximum.
    Ensures(Implies(max_length is None, Result() is False))
    Ensures(Implies(max_length is not None,
                    Result() == (value_length > max_length)))
    # post-conditions-end
    # impl-start
    validators = build_char_validators(max_length)
    flagged = False
    if len(validators) > 0:
        limit = validators[0]
        flagged = compare_length(value_length, limit)
    return flagged
    # impl-end
