"""Twin-artifact model for django__django-13821.

Behaviour under specification (stated as desired behaviour, not as an edit):

  At start-up the database backend checks the runtime version of the embedded
  SQLite library against the minimum version the project is willing to support,
  and refuses to proceed when the runtime is too old. The minimum supported
  version is 3.9.0: a runtime whose version is BELOW 3.9.0 is rejected with a
  configuration error, and a runtime AT OR ABOVE 3.9.0 is accepted.

  A version is an ordered sequence of release components (major, then minor,
  then successively finer levels); two versions are ordered the standard way,
  component by component, the first differing component deciding the order and a
  shorter version that is a prefix of a longer one counting as the smaller. The
  accept/reject decision is exactly this ordering applied to the runtime version
  and the minimum 3.9.0: reject iff the runtime is strictly below 3.9.0.

  The discriminating cases the contract pins:
    * any 3.8-series runtime (3.8.x for every finer level, including finer
      levels whose numeric value is large) is BELOW 3.9.0 and must be rejected;
    * the exact minimum 3.9.0, and anything above it, is accepted.

Version tuples are modelled as `List[int]` of release components (Nagini bans
the relevant rich-tuple operations); the component-wise ordering is carried by
the pure sequence theory `PSeq[int]`. The ordering is modelled DEEPLY as a
verified front-recursive fold (`lt_lex`); its agreement with Python's tuple
ordering is checked out-of-band by axiom_check.py (G-AX), not consumed as an
axiom. The rejection is a user-defined exception class (a builtin exception in
an `Exsures` crashes the Nagini translator; mapping.md).

The guard is a bounded, straight-line start-up check: it MUST terminate, by
either returning normally or raising the configuration error (a
total-correctness obligation, carried as MustTerminate in the precondition).
An implementation that diverges — e.g. hangs instead of raising on an
unsupported runtime — would satisfy the value postconditions only vacuously
and would hang Django start-up (and the F2P test) forever.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class UnsupportedConfiguration(Exception):
    """Signals that the runtime is below the minimum supported version. Stands
    in for the configuration error the desired behaviour raises (a builtin
    exception in an `Exsures` crashes the Nagini translator; mapping.md)."""
    pass


# axioms-start
# (no axiomatized callees: the runtime-vs-minimum version ordering is modelled
# deeply by the front-recursive fold `lt_lex` below and validated against
# Python's component-wise tuple comparison by axiom_check.py — an A-reference,
# not a consumed axiom.)
# axioms-end


# pure-start
@Pure
def min_version() -> PSeq[int]:
    """The minimum supported version, 3.9.0, as a component sequence."""
    return PSeq(3, 9, 0)


@Pure
def lt_lex(a: PSeq[int], b: PSeq[int]) -> bool:
    """Standard component-wise (lexicographic) ordering on version component
    sequences: True iff `a` is strictly below `b`. The first differing
    component decides; a shorter sequence that is a prefix of a longer one is
    the smaller. Front-recursive so a single unfold is available per proof
    step. This is exactly Python's tuple `<`."""
    if len(a) == 0 and len(b) == 0:
        return False
    if len(a) == 0:
        return True
    if len(b) == 0:
        return False
    if a[0] < b[0]:
        return True
    if a[0] > b[0]:
        return False
    return lt_lex(a.drop(1), b.drop(1))
# pure-end


def check_supported_version(version: List[int]) -> None:
    # pre-conditions-start
    # `version` is the runtime version components, read-only (fractional
    # permission: the check never mutates it).
    Requires(Acc(list_pred(version), 1 / 2))
    # The guard is a bounded start-up check: it MUST terminate (return or
    # raise) — total correctness. A diverging impl (e.g. hanging instead of
    # raising on an unsupported runtime) would satisfy the value
    # postconditions only vacuously and hang start-up (and the F2P test).
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The runtime version is preserved (read-only).
    Ensures(Acc(list_pred(version), 1 / 2))
    # Normal return is reachable ONLY when the runtime is AT OR ABOVE the
    # minimum 3.9.0 (i.e. NOT strictly below it).
    Ensures(not lt_lex(ToSeq(version), min_version()))
    # The configuration error is raised on EXACTLY the unsupported case: a
    # runtime strictly below the minimum 3.9.0.
    Exsures(UnsupportedConfiguration, Acc(list_pred(version), 1 / 2)
            and lt_lex(ToSeq(version), min_version()))
    # post-conditions-end
    # impl-start
    # Pre-patch skeleton: the runtime is compared against the OLD threshold
    # 3.8.3 instead of the supported minimum 3.9.0. Everything else (the
    # component-wise comparison, the raise on "below") is unchanged.
    mn = [3, 8, 3]  # type: List[int]
    below = False
    i = 0
    n = len(version)
    m = len(mn)
    while i < n and i < m:
        # invariants-start
        Invariant(Acc(list_pred(version), 1 / 2))
        Invariant(Acc(list_pred(mn)))
        Invariant(0 <= i and i <= n and i <= m)
        Invariant(n == len(version) and m == len(mn))
        Invariant(ToSeq(mn) == PSeq(3, 8, 3))
        Invariant(not below)
        # What the pre-patch loop actually computes: the ordering against 3.8.3.
        Invariant(lt_lex(ToSeq(version), PSeq(3, 8, 3))
                  == lt_lex(ToSeq(version).drop(i), PSeq(3, 8, 3).drop(i)))
        # The comparison loop consumes the caller's termination obligation
        # with a strictly decreasing measure (m - i), discharging
        # MustTerminate(2) from the precondition.
        Invariant(MustTerminate(m - i + 1))
        # invariants-end
        a = version[i]
        b = mn[i]
        Assert(ToSeq(version).drop(i)[0] == a)
        Assert(PSeq(3, 8, 3).drop(i)[0] == b)
        Assert(ToSeq(version).drop(i).drop(1) == ToSeq(version).drop(i + 1))
        Assert(PSeq(3, 8, 3).drop(i).drop(1) == PSeq(3, 8, 3).drop(i + 1))
        if a < b:
            below = True
            break
        if a > b:
            below = False
            break
        i = i + 1
    else:
        # The loop ran to exhaustion (no break): one sequence ran out. The
        # runtime is below the threshold iff it is the strict prefix, i.e. it
        # ran out of components first.
        Assert(i == n or i == m)
        if i < n:
            # threshold exhausted first => runtime is longer => not below.
            Assert(len(PSeq(3, 8, 3).drop(i)) == 0)
            below = False
        elif i < m:
            # runtime exhausted first => runtime is a strict prefix => below.
            Assert(len(ToSeq(version).drop(i)) == 0)
            below = True
        else:
            # both exhausted simultaneously => equal => not below.
            Assert(len(ToSeq(version).drop(i)) == 0)
            Assert(len(PSeq(3, 8, 3).drop(i)) == 0)
            below = False
    if below:
        raise UnsupportedConfiguration()
    return
    # impl-end
