"""Twin-artifact model for sympy__sympy-14976.

Behaviour under specification (an abstract behavioural contract, not an edit):

  A high-precision arbitrary-precision renderer turns a ratio of two integers
  (a numerator carrier and a denominator carrier, each already rendered as its
  decimal digit string) into source text that performs the division WITHIN the
  arbitrary-precision arithmetic domain. Concretely, the rendered text is the
  numerator wrapped in a high-precision constructor call, divided by the
  denominator wrapped in the SAME high-precision constructor call:

      CTOR ( <numerator digits> ) / CTOR ( <denominator digits> )

  where ``CTOR`` is the constant fully-qualified constructor token the renderer
  uses for high-precision numbers. The discriminating property is that BOTH
  operands of the division are wrapped in that constructor call — so the
  quotient is computed at arbitrary precision — rather than the two digit
  strings being divided as a bare ``num / den`` (which would be an ordinary
  truncating/limited-precision division and lose precision).

The two digit-string carriers and the constructor token are modelled as
``List[int]`` of code points (Nagini bans ``str`` indexing); the specification
is carried over ``PSeq[int]`` via ``ToSeq``. The literal tokens are the ASCII
code points ``(`` = 40, ``)`` = 41, ``/`` = 47, and the constructor token
``mpmath.mpf`` = ``[109,112,109,97,116,104,46,109,112,102]``.

The constructor token is produced by an unchanged helper (the fully-qualified
module-formatter) that, under the renderer's default configuration, returns
that constant token; it is modelled as the pure constant ``ctor`` and validated
against the real helper out-of-band by axiom_check.py (G-AX), not consumed as
an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No consumed @ContractOnly axioms. The renderer's changed string construction
# is modelled DEEPLY below as the pure fold-free concatenation `rendered`. The
# only callee the construction invokes — the fully-qualified module-formatter
# that yields the constructor token — is an UNCHANGED helper that, under the
# renderer's default configuration, returns the constant token modelled by the
# pure constant `ctor`; its equality to the real helper is validated
# out-of-band by axiom_check.py (G-AX), an A-reference, NOT a consumed axiom.)
# axioms-end


# pure-start
@Pure
def ctor() -> PSeq[int]:
    """The constant fully-qualified high-precision constructor token, as code
    points: ``mpmath.mpf``. This is what the unchanged module-formatter returns
    under the renderer's default (fully-qualified) configuration."""
    return PSeq(109, 112, 109, 97, 116, 104, 46, 109, 112, 102)


@Pure
def rendered(p: PSeq[int], q: PSeq[int]) -> PSeq[int]:
    """The rendered text for the ratio of the numerator digit string ``p`` and
    the denominator digit string ``q``: each wrapped in a constructor call and
    divided.

        ctor '(' p ')' '/' ctor '(' q ')'
    """
    return (ctor() + PSeq(40) + p + PSeq(41) + PSeq(47)
            + ctor() + PSeq(40) + q + PSeq(41))
# pure-end


def render_mpf_ratio(p_digits: List[int], q_digits: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(p_digits), 1 / 2))
    Requires(Acc(list_pred(q_digits), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(p_digits), 1 / 2))
    Ensures(Acc(list_pred(q_digits), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The rendered text wraps BOTH the numerator digits and the denominator
    # digits in the high-precision constructor call, dividing the two calls.
    Ensures(ToSeq(Result()) == rendered(ToSeq(p_digits), ToSeq(q_digits)))
    # post-conditions-end
    # impl-start
    # Pre-patch skeleton: the ratio is rendered as a bare "num/den" — the two
    # digit strings divided directly, with NEITHER operand wrapped in the
    # high-precision constructor call. (This is the inherited generic
    # number-printer behaviour the renderer falls back to.)
    out = []  # type: List[int]
    # numerator digits
    out = out + p_digits
    # '/'
    out = out + [47]
    # denominator digits
    out = out + q_digits
    return out
    # impl-end
