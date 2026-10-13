"""Twin-artifact model for astropy__astropy-7671.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A routine reports whether an installed component's version satisfies a
  requested minimum version. A version is an ordered list of release segments
  (the dotted numeric components of the public version label). A requested
  version label may carry a trailing NON-numeric qualifier (a pre/dev/release
  suffix such as the textual tail of "0.12dev" or "1.2rc1"); only the leading
  run of numeric release segments is meaningful for the ordering, and the
  qualifier tail must be discarded before any comparison. The installed
  version is a plain numeric version with no qualifier tail.

  The comparison itself is the standard component-wise version order: compare
  segments left to right; the first differing segment decides; when one is a
  proper prefix of the other the longer (more specific) version is the greater.
  The routine returns, inclusively, whether the installed version is at least
  the (qualifier-stripped) requested version, or, non-inclusively, whether it
  is strictly greater.

  Crucially the comparison operates on the qualifier-STRIPPED requested
  version: comparing against a label that still carries its non-numeric tail is
  not well defined and must never be performed.

Versions are modelled as `List[int]` of parsed release segments: a segment
>= 0 is a numeric release component; the sentinel value -1 marks the start of
the non-numeric qualifier tail (so "0.12dev" ~ [0, 12, -1], "1.2rc1" ~
[1, 2, -1], "0.12.0.dev" ~ [0, 12, 0, -1]). The pure sequence theory
`PSeq[int]` carries the specification. No external callee is axiomatized: the
qualifier stripping and the component-wise order are modelled deeply, and are
validated against the real version machinery out-of-band by axiom_check.py
(G-AX), not consumed as axioms.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# axioms-end


# pure-start
@Pure
def is_numeric(s: PSeq[int]) -> bool:
    """True iff every segment is a numeric release component (>= 0), i.e. the
    sequence carries no non-numeric qualifier tail. Front-recursive so a single
    unfold is available per fold/loop step."""
    if len(s) == 0:
        return True
    return s[0] >= 0 and is_numeric(s.drop(1))


@Pure
def normalize(s: PSeq[int]) -> PSeq[int]:
    """The meaningful leading run of numeric release segments: the prefix of
    `s` up to (not including) the first qualifier marker (the first negative
    segment). Front-recursive, one unfold per leading segment. The result is
    always qualifier-free, so the component-wise order is always defined on it.
    """
    if len(s) == 0:
        return PSeq(0).take(0)
    if s[0] < 0:
        return PSeq(0).take(0)
    return PSeq(s[0]) + normalize(s.drop(1))


@Pure
def loose_ge(a: PSeq[int], b: PSeq[int]) -> bool:
    """Component-wise version order, inclusive (`a` is at least `b`). Compare
    release segments left to right; the first differing segment decides; on a
    proper prefix the longer (more specific) version is the greater.

    The order is well defined only between two qualifier-free versions. If a
    position pairs a numeric segment of one version with the qualifier marker
    of the other, the comparison has no defined result (the real version
    machinery raises a type error there); the modelled value at such a position
    is the non-satisfied outcome `False`, so a comparison that ever reaches the
    qualifier tail can never report 'satisfied'. The specification only ever
    compares against the qualifier-STRIPPED requested version, on which this
    case never arises. Front-recursive."""
    if len(a) == 0 and len(b) == 0:
        return True
    if len(a) == 0:
        return False
    if len(b) == 0:
        return True
    if (a[0] < 0) != (b[0] < 0):
        return False        # numeric vs qualifier marker: comparison undefined
    if a[0] != b[0]:
        return a[0] > b[0]
    return loose_ge(a.drop(1), b.drop(1))


@Pure
def loose_gt(a: PSeq[int], b: PSeq[int]) -> bool:
    """Strict component-wise version order (`a` is greater than `b`), with the
    same qualifier-marker handling as `loose_ge`: a position pairing a numeric
    segment with a qualifier marker has no defined result and is modelled as the
    non-satisfied outcome `False`. Front-recursive."""
    if len(a) == 0 and len(b) == 0:
        return False
    if len(a) == 0:
        return False
    if len(b) == 0:
        return True
    if (a[0] < 0) != (b[0] < 0):
        return False        # numeric vs qualifier marker: comparison undefined
    if a[0] != b[0]:
        return a[0] > b[0]
    return loose_gt(a.drop(1), b.drop(1))
# pure-end


def version_meets_minimum(have: List[int], want: List[int], inclusive: bool) -> bool:
    # pre-conditions-start
    # Both version lists are read-only (the routine reports a boolean and
    # mutates nothing): required AND ensured at fractional permission
    # (directive 5).
    Requires(Acc(list_pred(have), 1 / 2))
    Requires(Acc(list_pred(want), 1 / 2))
    # The installed version is a plain numeric version with no qualifier tail.
    Requires(is_numeric(ToSeq(have)))
    # The requested version begins with a numeric release segment, so its
    # qualifier-stripped form has a non-empty leading numeric run. A requested
    # label whose first segment is NOT a numeric release component (a pure or
    # leading qualifier such as "dev" / "" / ".1") has no well-defined release
    # ordering at all -- the comparison is not meaningful and is outside the
    # behaviour this contract specifies. Restricting the domain here keeps the
    # contract a sound over-approximation: it promises a defined boolean ONLY
    # where the real comparison is itself defined.
    Requires(len(ToSeq(want)) > 0 and ToSeq(want)[0] >= 0)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(have), 1 / 2))
    Ensures(Acc(list_pred(want), 1 / 2))
    Ensures(is_numeric(ToSeq(have)))
    # The result is the component-wise order against the qualifier-STRIPPED
    # requested version: inclusively at-least, or strictly-greater. Comparing
    # against the un-stripped `want` (which may carry a qualifier tail) is
    # never performed; the comparison's domain is the normalized, numeric-only
    # version. This pins the discriminating behaviour the issue demands.
    Ensures(Implies(inclusive,
                    Result() == loose_ge(ToSeq(have), normalize(ToSeq(want)))))
    Ensures(Implies(not inclusive,
                    Result() == loose_gt(ToSeq(have), normalize(ToSeq(want)))))
    # post-conditions-end
    # impl-start
    # Pre-patch skeleton: the requested version is compared as-is, WITHOUT
    # first stripping its trailing non-numeric qualifier, mirroring the direct
    # LooseVersion(have_version) >= LooseVersion(version) of the pre-patch code.
    if inclusive:
        return loose_ge(ToSeq(have), ToSeq(want))
    else:
        return loose_gt(ToSeq(have), ToSeq(want))
    # impl-end
