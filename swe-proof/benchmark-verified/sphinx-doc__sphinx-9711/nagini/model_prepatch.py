"""Twin-artifact model for sphinx-doc__sphinx-9711.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A configuration check guards that every required companion component is
  present at no less than a minimum version. A required minimum and the loaded
  component's reported version are both *dotted release numbers* — an ordered
  sequence of non-negative integer release segments (e.g. the number written
  "3.10" is the two-segment sequence [3, 10], whose second segment is the
  integer ten, NOT the two characters '1','0').

  The guard must accept the loaded component exactly when it is *at least* the
  required minimum under the ORDERING OF RELEASE NUMBERS, and reject it (and
  abort the build out of band) otherwise. The release-number ordering compares
  the segments left to right as INTEGERS, a missing trailing segment counting
  as zero; so the number "3.10" is greater than "3.9" because its second
  segment, ten, exceeds nine — even though, read as bare text, "3.9" would sort
  after "3.10". A loaded component whose version is not reported at all is
  always treated as failing the requirement.

  Concretely: the requirement is fulfilled iff the loaded version is known AND
  the required minimum is not strictly greater than the loaded version under
  release-number ordering. When it is not fulfilled the guard does not return
  normally; it signals the failure out of band.

Release numbers are modelled as `List[int]` of segments (Nagini bans `str`
indexing, and the tested behaviour is precisely that the segments compare as
integers, not as text). The pure sequence theory `PSeq[int]` carries the
ordering. The release-number ordering is modelled DEEPLY as a verified
segment-wise comparison (`version_gt`); its equality to the real version
comparator is checked out-of-band by axiom_check.py (G-AX), not consumed as an
axiom. The out-of-band failure signal is a user-defined exception (a builtin
exception in an ``Exsures`` crashes the Nagini translator).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class RequirementUnfulfilled(Exception):
    """Out-of-band signal that a required component is absent or too old, so
    the build cannot proceed. User-defined stand-in for the abort the guard
    raises (a builtin exception in an ``Exsures`` crashes the Nagini
    translator; mapping.md §2)."""
    pass


# axioms-start
# (No opaque library callee is CONSUMED as an axiom. The release-number
#  ordering — the operation whose semantics changed — is modelled DEEPLY by the
#  @Pure comparator `version_gt` below and validated == the real version
#  comparator out-of-band by axiom_check.py / G-AX, as an A-reference.)
# axioms-end


# pure-start
@Pure
def seg(s: PSeq[int], i: int) -> int:
    """Release segment ``i`` of ``s``, a missing trailing segment counting as
    the integer zero (the padding rule of release-number ordering)."""
    Requires(0 <= i)
    if i < len(s):
        return s[i]
    return 0


@Pure
def version_gt_from(a: PSeq[int], b: PSeq[int], i: int) -> bool:
    """Whether release number ``a`` is strictly greater than ``b`` when both
    are compared segment-by-segment as INTEGERS from index ``i`` onward, a
    missing trailing segment counting as zero. Front-recursive so a single
    unfold is available per comparison step."""
    Requires(0 <= i)
    if i >= len(a) and i >= len(b):
        return False
    if seg(a, i) > seg(b, i):
        return True
    if seg(a, i) < seg(b, i):
        return False
    return version_gt_from(a, b, i + 1)


@Pure
def version_gt(a: PSeq[int], b: PSeq[int]) -> bool:
    """Release-number ordering: True iff ``a`` is a strictly greater release
    number than ``b`` (segments compared as integers, missing trailing segment
    = zero). The deep model of the real version comparator (A-reference,
    validated by axiom_check.py / G-AX)."""
    return version_gt_from(a, b, 0)
# pure-end


def verify_requirement(reqversion: List[int], extversion: List[int],
                       ext_known: bool) -> bool:
    # pre-conditions-start
    # Both release numbers are read-only inputs (fractional permission; they
    # are not mutated and the same fraction is returned).
    Requires(Acc(list_pred(reqversion), 1 / 2))
    Requires(Acc(list_pred(extversion), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(reqversion), 1 / 2))
    Ensures(Acc(list_pred(extversion), 1 / 2))
    # The guard returns normally EXACTLY when the requirement is fulfilled:
    # the loaded version is known AND the required minimum is not strictly
    # greater than the loaded version under release-number ordering. A normal
    # return reports TRUE.
    Ensures(Result() is True)
    Ensures(ext_known is True)
    Ensures(version_gt(ToSeq(reqversion), ToSeq(extversion)) is False)
    # The guard signals the failure out of band EXACTLY when the requirement is
    # not fulfilled: the loaded version is unknown, OR the required minimum is
    # strictly greater than the loaded version under release-number ordering.
    Exsures(RequirementUnfulfilled,
            Acc(list_pred(reqversion), 1 / 2) and
            Acc(list_pred(extversion), 1 / 2) and
            (ext_known is False or
             version_gt(ToSeq(reqversion), ToSeq(extversion)) is True))
    # post-conditions-end
    # impl-start
    # PRE-PATCH (buggy) skeleton: the minimum/loaded comparison is the bare
    # TEXTUAL ordering of the two numbers, not the release-number ordering. The
    # segments are compared as their written characters position by position
    # (first differing position decides; a prefix is the smaller), so e.g. the
    # number "3.9" is judged greater than "3.10" because the character '9'
    # follows '1'. This is the behaviour the spec rejects.
    fulfilled = True
    if not ext_known:
        fulfilled = False
    else:
        # textual ">" of reqversion over extversion, code point by code point
        n = len(reqversion)
        m = len(extversion)
        bound = n
        if m < n:
            bound = m
        req_gt_text = False
        decided = False
        i = 0
        while i < bound:
            # invariants-start
            Invariant(Acc(list_pred(reqversion), 1 / 2))
            Invariant(Acc(list_pred(extversion), 1 / 2))
            Invariant(0 <= i and i <= bound)
            Invariant(bound <= len(reqversion) and bound <= len(extversion))
            Invariant(MustTerminate(bound - i + 1))
            # invariants-end
            rc = reqversion[i]
            ec = extversion[i]
            if not decided:
                if rc > ec:
                    req_gt_text = True
                    decided = True
                elif rc < ec:
                    req_gt_text = False
                    decided = True
            i = i + 1
        if not decided:
            if n > m:
                req_gt_text = True
        if req_gt_text:
            fulfilled = False
    if not fulfilled:
        raise RequirementUnfulfilled()
    return True
    # impl-end
