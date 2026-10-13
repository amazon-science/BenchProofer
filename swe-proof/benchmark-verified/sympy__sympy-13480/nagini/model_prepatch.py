"""Twin-artifact model for sympy__sympy-13480.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An automatic simplifier for a hyperbolic-cotangent-like function handles the
  case where its argument decomposes into a remainder part and a multiple of a
  distinguished imaginary period. When that periodic part is present, the
  simplifier evaluates the SAME function on the periodic part and inspects the
  resulting expression:

    * if evaluating the function on the periodic part yields the
      "directed-infinity" sentinel, the simplified result is the function
      applied to the remainder part;
    * otherwise (the evaluation yields the finite/zero alternative), the
      simplified result is the reciprocal-family sibling function applied to
      the remainder part.

  The behaviour pinned here: the branch that chooses between these two results
  is governed by the value obtained by evaluating the function on the PERIODIC
  PART — i.e. the quantity that was just computed from the periodic part — and
  by no other quantity. The result is the remainder-part evaluation of the same
  function exactly when that computed value is the directed-infinity sentinel,
  and the reciprocal-family sibling on the remainder part otherwise.

Symbolic expressions are modelled as opaque integer handles. The two unchanged
elementary functions consulted here are deterministic pure callees over those
handles (axioms region); the directed-infinity sentinel is a distinguished
handle. The simplifier never raises on this branch: the value it inspects is
always the one it just computed.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def primary(arg: int) -> int:
    """The function being simplified, as an opaque deterministic map over
    expression handles (an UNCHANGED elementary callee — it is consulted, not
    redefined). Determinism is all the proof relies on: the value computed from
    the periodic part is the same value later inspected. Provenance + executable
    soundness check: mapping.md / axiom_check.py."""


@Pure
@ContractOnly
def sibling(arg: int) -> int:
    """The reciprocal-family sibling function, likewise an opaque deterministic
    UNCHANGED callee over expression handles. Provenance: mapping.md."""


@Pure
@ContractOnly
def directed_infinity() -> int:
    """The distinguished "directed-infinity" sentinel expression handle (an
    UNCHANGED module constant). Provenance: mapping.md."""
# axioms-end


def periodic_part_simplification(x: int, m: int) -> int:
    # pre-conditions-start
    # x is the remainder part, m the (present, non-trivial) periodic part.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The result is governed by evaluating the primary function on the periodic
    # part `m`: the primary function on `x` exactly when that value is the
    # directed-infinity sentinel, the sibling function on `x` otherwise. The
    # branch is decided by `primary(m)`, the quantity just computed, and by no
    # other quantity. The two implications are exhaustive and mutually
    # exclusive, so together they pin the result on every input — stated
    # directly over the input handles (no answer-key oracle to echo).
    Ensures(Implies(primary(m) == directed_infinity(), Result() == primary(x)))
    Ensures(Implies(primary(m) != directed_infinity(), Result() == sibling(x)))
    # post-conditions-end
    # impl-start
    primary_m = primary(m)
    if primary(x) == directed_infinity():
        return primary(x)
    else:
        return sibling(x)
    # impl-end
