"""Twin-artifact model for django__django-16255.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A section that exposes a per-entry modification stamp reports the most recent
  stamp across its entries. The stamps are obtained by applying the section's
  per-entry stamp function to each entry the section enumerates, forming a
  collection of comparable values. The section then reports:

    (1) when the section enumerates NO entries, the collection of stamps is
        empty and the reported value is the absent marker (None) — computing a
        latest stamp over an empty section must NOT fail; and

    (2) when the section enumerates one or more entries, the reported value is
        the greatest stamp in the collection: it is one of the collected stamps
        and is greater than or equal to every collected stamp.

The collection of per-entry stamps is modelled as ``List[int]`` of comparable
stamp values (the per-entry stamp function applied across the enumerated
entries). The reported value is ``Optional[int]``: the absent marker for an
empty section, otherwise the maximum stamp.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no @ContractOnly callees: the reported value is the greatest of the
# collected stamps, modelled deeply over List[int]; there is no unchanged
# library callee the proof must axiomatize.)
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour.)
# pure-end


def latest_stamp(stamps: List[int]) -> Optional[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(stamps), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(stamps), 1 / 2))
    # (1) an empty section reports the absent marker (no failure on empty).
    Ensures(Implies(len(stamps) == 0, Result() is None))
    # (2) a non-empty section reports the greatest collected stamp: it is one of
    # the collected stamps and dominates every collected stamp.
    Ensures(Implies(len(stamps) > 0, Result() is not None))
    Ensures(Implies(
        len(stamps) > 0,
        Exists(int, lambda k: 0 <= k and k < len(stamps) and Result() == stamps[k])))
    Ensures(Forall(int, lambda k: Implies(
        0 <= k and k < len(stamps),
        (Result() is not None) and stamps[k] <= Result())))
    # post-conditions-end
    # impl-start
    result = None  # type: Optional[int]
    i = 0
    while i < len(stamps):
        # invariants-start
        Invariant(Acc(list_pred(stamps), 1 / 2))
        Invariant(0 <= i and i <= len(stamps))
        Invariant((i == 0) == (result is None))
        Invariant(Implies(
            result is not None,
            Exists(int, lambda k: 0 <= k and k < i and result == stamps[k])))
        Invariant(Forall(int, lambda k: Implies(
            0 <= k and k < i,
            (result is not None) and stamps[k] <= result)))
        Invariant(MustTerminate(len(stamps) - i + 1))
        # invariants-end
        v = stamps[i]
        if result is None or v > result:
            result = v
        i = i + 1
    return result
    # impl-end
