"""Twin-artifact model for pytest-dev__pytest-5631.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A collection-time helper counts how many of a callable's recorded
  replacement directives stand in for an argument that the test runner will
  supply itself (rather than binding a named attribute). A directive counts
  exactly when it binds no attribute name AND its replacement value is one of
  the framework's well-known replacement-placeholder singletons.

  The membership decision must be made by OBJECT IDENTITY against those
  placeholder singletons — i.e. "is this value that very singleton object" —
  never by value-equality. The reason is robustness: a replacement value may be
  an arbitrary user object whose equality test does not yield a usable boolean
  (for instance an object that, when compared for equality, produces a
  non-scalar or otherwise non-truth-evaluable answer). An identity decision is
  TOTAL: it yields a definite yes/no for every replacement value and can never
  fail on such an object, whereas a value-equality decision can.

  Consequences pinned here:
    * the count is the number of directives that bind no attribute name and
      whose replacement value IS (by identity) a placeholder singleton;
    * a directive that binds an attribute name never counts;
    * a directive whose replacement value is a non-placeholder is excluded;
    * the helper returns a count for EVERY well-formed input and never fails —
      in particular it never fails on a directive whose replacement value has a
      non-truth-evaluable equality.

The directive sequence is modelled as a `List[int]` of per-directive kind tags
(Nagini bans attribute reflection over heterogeneous objects); the kind records
exactly the three observables the helper reads: whether the directive binds an
attribute name, whether its replacement value is a placeholder singleton (by
identity), and whether its replacement value's equality is non-truth-evaluable.
The specification is phrased over `PSeq[int]` via `ToSeq`. The total identity
decision is modelled deeply (a per-tag classifier with no failure path); a
non-truth-evaluable equality is a user-defined exception class (a builtin
exception in an `Exsures` crashes the Nagini translator), and the spec forbids
the helper from ever surfacing it.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


class NonTruthEvaluableEquality(Exception):
    """Raised when a replacement value is compared for VALUE-EQUALITY and the
    comparison does not yield a usable boolean (e.g. it produces a non-scalar
    answer). User-defined stand-in for that failure (a builtin exception in an
    `Exsures` crashes the Nagini translator; mapping.md §2). The desired
    behaviour FORBIDS the helper from ever surfacing this: the membership
    decision is by identity, which is total. The contract below carries no
    `Exsures`, so any implementation whose decision can raise this on an
    admissible input fails to verify."""
    pass


# axioms-start
# (no axiomatized callee: the helper reads only the per-directive observables —
#  attribute-binding, identity-to-a-placeholder, and equality-truth-evaluability
#  — all modelled abstractly as integer kind tags. The membership decision is
#  the changed operation and is modelled DEEPLY (the total identity classifier
#  `counts_as_mock` below), not behind an axiom.)
# axioms-end


# pure-start
# Per-directive kind tags (the only observables the helper reads):
#   0 — binds an attribute name: never counts (and never inspects the value).
#   1 — binds no attribute name; replacement value IS a placeholder singleton
#       (identity match): counts.
#   2 — binds no attribute name; replacement value is a non-placeholder whose
#       equality is a usable boolean: does not count.
#   3 — binds no attribute name; replacement value is a non-placeholder whose
#       equality is NOT truth-evaluable (e.g. a non-scalar comparison result):
#       does not count. An identity decision handles it; a value-equality
#       decision would fail on it.

@Pure
def counts_as_mock(kind: int) -> bool:
    """Whether a single directive of the given kind contributes to the count.
    This is the TOTAL identity decision: it returns a definite boolean for
    EVERY kind, including kind 3 (the non-truth-evaluable-equality value), and
    has no failure path. A directive counts exactly when it binds no attribute
    name (kind != 0) and its replacement value is a placeholder singleton by
    identity (kind == 1)."""
    return kind == 1


@Pure
def count_sentinel_directives(s: PSeq[int]) -> int:
    """The number of directives in the sequence that count, by identity.
    Front-recursive so a single unfold is available to the loop per step."""
    if len(s) == 0:
        return 0
    return (1 if counts_as_mock(s[0]) else 0) + count_sentinel_directives(s.drop(1))
# pure-end


def count_mock_patch_args(kinds: List[int]) -> int:
    # pre-conditions-start
    # `kinds` is the directive sequence, each element a per-directive kind tag
    # in {0,1,2,3} (read-only: the helper does not mutate it).
    Requires(Acc(list_pred(kinds), 1 / 2))
    Requires(Forall(int, lambda i: (Implies(0 <= i and i < len(kinds),
                                            0 <= kinds[i] and kinds[i] <= 3),
                                     [[kinds[i]]])))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(kinds), 1 / 2))
    # Totality: the helper returns a count for EVERY well-formed input and never
    # surfaces a failure — in particular not on a kind-3 directive (a value with
    # non-truth-evaluable equality). The absence of any `Exsures` on this
    # contract pins that: no exceptional post-state is admissible.
    #
    # The count equals the number of directives that bind no attribute name and
    # whose replacement value is a placeholder singleton by identity (kind 1).
    Ensures(Result() == count_sentinel_directives(ToSeq(kinds)))
    # Soundness of the count as a count: it is non-negative and never exceeds the
    # number of directives (each directive contributes at most one).
    Ensures(0 <= Result() and Result() <= len(kinds))
    # post-conditions-end
    # impl-start
    # PRE-PATCH (buggy) skeleton: the membership decision is made by
    # VALUE-EQUALITY rather than by identity. For a directive whose replacement
    # value has a non-truth-evaluable equality (kind 3) the equality test does
    # not yield a usable boolean and surfaces a failure — exactly the behaviour
    # the spec forbids. Because the contract carries no matching `Exsures`, this
    # skeleton fails to verify on the kind-3 input (the totality clause).
    count = 0
    i = len(kinds)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(kinds), 1 / 2))
        Invariant(0 <= i and i <= len(kinds))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(kinds),
                                                 0 <= kinds[k] and kinds[k] <= 3),
                                          [[kinds[k]]])))
        Invariant(count == count_sentinel_directives(ToSeq(kinds).drop(i)))
        Invariant(0 <= count and count <= len(kinds) - i)
        # invariants-end
        c = kinds[i - 1]
        Assert(ToSeq(kinds).drop(i - 1)[0] == c)
        Assert(ToSeq(kinds).drop(i - 1).drop(1) == ToSeq(kinds).drop(i))
        # Value-equality membership decision. A non-attribute directive (kind in
        # {1,2,3}) compares its replacement value for equality against the
        # placeholder singletons. Kind 1 equals a placeholder (counts); kind 2 is
        # unequal (does not count); kind 3's equality is non-truth-evaluable and
        # raises — the bug.
        if c != 0:
            if c == 3:
                raise NonTruthEvaluableEquality()
            if c == 1:
                count = count + 1
        i = i - 1
    return count
    # impl-end
