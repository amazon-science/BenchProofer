"""Twin-artifact model for django__django-14765.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A state container is constructed from an optional collection of auxiliary
  app labels. The collection is supplied through an internal construction API,
  so the container imposes a TYPE DISCIPLINE on it rather than silently
  accommodating any shape:

    * when the collection is ABSENT, the container holds an empty collection;
    * when the collection is PRESENT and is already the expected unordered
      collection kind (a set), the container holds exactly that collection,
      with its membership preserved unchanged — no copy or coercion alters it;
    * when the collection is PRESENT but is NOT the expected kind (for example
      an ordered list), construction must FAIL — the container does not quietly
      convert an off-kind collection into the expected kind. The failure is
      reported to the caller as an internal-contract violation.

  The behaviour pinned here is exactly that discipline: normal construction is
  reachable only for an absent collection or one that is already the expected
  kind, and the stored collection then equals (absent ⇒ empty; present-and-
  expected ⇒ the supplied membership). A present collection that is not the
  expected kind produces the failure and never a coerced result.

The auxiliary-app-label collection is modelled as a `List[int]` of label code
points together with a boolean `present` (absent ⟺ ``not present``, in which
case the list contents are irrelevant); Nagini bans `str` indexing, and the
discriminating observable is purely WHICH outcome construction produces and
WHAT membership it stores, not the labels' characters. A second boolean models
whether a present collection is already the expected kind (the runtime kind
test). The off-kind construction failure is a user-defined exception class (a
builtin exception in an `Exsures` crashes the Nagini translator; mapping.md).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class OffKindCollection(Exception):
    """Signals that a present auxiliary-app-label collection is NOT the expected
    unordered kind, so construction must fail rather than coerce it. User-defined
    stand-in for the internal-contract violation the desired behaviour raises; a
    builtin exception in an `Exsures` crashes the Nagini translator (mapping.md
    §2)."""


# axioms-start
# (no callee is axiomatized: the construction's decision and store are spelled
# out directly over the modelled collection; there is no unchanged library
# callee inside the changed operation.)
# axioms-end


# pure-start
# (no module-level pure helpers required: the stored membership is stated
# inline as the supplied sequence on the present-and-expected path and the
# empty sequence on the absent path.)
# pure-end


def build_state(real_apps: List[int], present: bool, is_expected_kind: bool) -> List[int]:
    # pre-conditions-start
    # The supplied collection is read-only here (construction stores it by
    # reference when it is the expected kind; it is never mutated). Fractional
    # permission, required and ensured, so no caller can satisfy a postcondition
    # vacuously by overwriting the input.
    Requires(Acc(list_pred(real_apps), 1 / 2))
    # Construction always COMPLETES: it reaches one of its two outcomes (a
    # normally-returned stored collection, or the internal-contract violation)
    # in finitely many steps, within a budget bounded by the size of the
    # supplied collection. It never diverges — neither outcome may be evaded by
    # running forever, on ANY admissible input (absent, present-and-expected, or
    # present-and-off-kind). Without this, a non-terminating construction would
    # discharge every clause below vacuously by never reaching an outcome.
    Requires(MustTerminate(len(real_apps) + 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(real_apps), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # Normal construction is reachable ONLY for an absent collection or one that
    # is already the expected kind. A present off-kind collection must NOT
    # return normally (it raises below) — never a coerced result.
    Ensures((not present) or is_expected_kind)
    # Stored membership: absent ⇒ empty; present-and-expected ⇒ exactly the
    # supplied membership, preserved unchanged (no copy or coercion alters it).
    Ensures(Implies(not present, len(Result()) == 0))
    Ensures(Implies(present and is_expected_kind,
                    ToSeq(Result()) == ToSeq(real_apps)))
    # The pinned failure: a present collection that is not the expected kind
    # raises the internal-contract violation and ONLY that, for EVERY such
    # collection (whether empty or non-empty), never a coerced result.
    Exsures(OffKindCollection,
            Acc(list_pred(real_apps), 1 / 2) and present and not is_expected_kind)
    # post-conditions-end
    # impl-start
    if not present:
        empty = []  # type: List[int]
        return empty
    if not is_expected_kind:
        raise OffKindCollection()
    # Present-and-expected: the stored collection preserves the supplied
    # membership unchanged. Materialised here as a same-membership sequence so
    # the result carries full permission while the input stays read-only
    # (refinement.md: the real store is by reference, contents preserved — an
    # R-refinement of object identity to membership equality).
    result = []  # type: List[int]
    i = 0
    while i < len(real_apps):
        # invariants-start
        Invariant(Acc(list_pred(real_apps), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(real_apps))
        Invariant(ToSeq(result) == ToSeq(real_apps).take(i))
        Invariant(MustTerminate(len(real_apps) - i + 1))
        # invariants-end
        Assert(ToSeq(real_apps).take(i + 1).drop(i)[0] == real_apps[i])
        result.append(real_apps[i])
        i = i + 1
    return result
    # impl-end
