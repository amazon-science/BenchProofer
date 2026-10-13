"""Twin-artifact model for sympy__sympy-20428.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A coefficient drawn from the symbolic ground domain carries two independent
  facets:
    * its STRUCTURAL form -- the concrete syntactic shape of the stored
      expression (in particular, whether that shape IS the bare literal whose
      value is zero); and
    * its MATHEMATICAL VALUE -- whether the expression denotes zero once its
      meaning is taken into account.
  These can disagree: a coefficient may have a non-trivial structural shape and
  yet denote zero (a non-obvious but genuine zero).

  (1) The truthiness of such a coefficient must track its MATHEMATICAL VALUE: a
      coefficient counts as "false" exactly when it denotes zero, regardless of
      how elaborate its structural shape is. It is NOT enough for the shape to
      differ syntactically from the bare zero literal.

  (2) A constant univariate polynomial is stored as a leading-coefficient list.
      Stripping its leading zero coefficient must remove a coefficient that
      denotes zero, leaving the canonical empty list that represents the zero
      polynomial. Consequently the stored list is empty -- and the polynomial
      registers as the zero polynomial -- EXACTLY when the single coefficient
      denotes zero, so that a polynomial built from a constant that denotes zero
      is canonically identical to the one built from the bare zero literal.

  (3) Both operations are bounded, straight-line computations: they MUST
      terminate and return their answer (a total-correctness obligation,
      carried as MustTerminate in the preconditions). An implementation that
      diverges before returning would satisfy the value postconditions only
      vacuously and would never deliver the truthiness verdict (or the stripped
      representation) to its consumer.

The symbolic coefficient is modelled as a minimal class carrying only the two
touched facets: a flag for whether its structural shape is the bare zero
literal, and a flag for whether it denotes zero mathematically. A bare-literal
shape always denotes zero (the constructor enforces this), but a coefficient
that denotes zero need not have the bare-literal shape -- which is the whole
point of the distinction. The stored polynomial representation is modelled by
its length (0 = the canonical zero polynomial, 1 = a retained constant).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class Coeff:
    """A ground-domain coefficient, reduced to the two facets that matter:

      lit0  -- 1 iff its structural shape IS the bare literal whose value is 0;
      mzero -- 1 iff it denotes zero mathematically.

    The constructor enforces that a bare-literal-zero shape always denotes zero
    (lit0 == 1 ==> mzero == 1); the converse is deliberately NOT enforced, so a
    structurally non-trivial coefficient that nonetheless denotes zero
    (lit0 == 0, mzero == 1) is representable -- that is the discriminating case.
    """

    def __init__(self, lit0: int, mzero: int) -> None:
        Requires(MustTerminate(1))
        Requires(lit0 == 0 or lit0 == 1)
        Requires(mzero == 0 or mzero == 1)
        Requires(Implies(lit0 == 1, mzero == 1))
        Ensures(Acc(self.lit0) and self.lit0 == lit0)    # type: ignore
        Ensures(Acc(self.mzero) and self.mzero == mzero)  # type: ignore
        self.lit0 = lit0
        self.mzero = mzero


# axioms-start
# (No @ContractOnly axioms are needed: the mathematical-zero facet is modelled
# directly by the `mzero` field of the coefficient; the leading-zero stripping
# is spelled out in the impl, not axiomatized.)
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


def coeff_truthy(c: Coeff) -> bool:
    # pre-conditions-start
    # Total-correctness obligation: the truthiness test is a bounded,
    # straight-line computation and MUST terminate; a diverging implementation
    # would satisfy the value postcondition only vacuously.
    Requires(MustTerminate(2))
    Requires(Acc(c.lit0, 1 / 2) and Acc(c.mzero, 1 / 2))
    Requires(c.lit0 == 0 or c.lit0 == 1)
    Requires(c.mzero == 0 or c.mzero == 1)
    Requires(Implies(c.lit0 == 1, c.mzero == 1))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(c.lit0, 1 / 2) and Acc(c.mzero, 1 / 2))
    # The coefficient is truthy EXACTLY when it does not denote zero -- the
    # truthiness tracks the mathematical value, not the structural shape.
    Ensures(Result() == (c.mzero == 0))
    # post-conditions-end
    # impl-start
    return c.lit0 == 0
    # impl-end


def strip_constant_len(c: Coeff) -> int:
    # pre-conditions-start
    # Total-correctness obligation: the strip is a bounded computation over a
    # length-<=1 list and MUST terminate and return the resulting length; a
    # diverging implementation would satisfy the value postconditions only
    # vacuously. Measure 3 leaves room to call coeff_truthy (measure 2).
    Requires(MustTerminate(3))
    Requires(Acc(c.lit0, 1 / 2) and Acc(c.mzero, 1 / 2))
    Requires(c.lit0 == 0 or c.lit0 == 1)
    Requires(c.mzero == 0 or c.mzero == 1)
    Requires(Implies(c.lit0 == 1, c.mzero == 1))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(c.lit0, 1 / 2) and Acc(c.mzero, 1 / 2))
    Ensures(Result() == 0 or Result() == 1)
    # The stored constant-polynomial list is empty -- the canonical zero
    # polynomial -- EXACTLY when the single coefficient denotes zero. A
    # coefficient whose structural shape is non-trivial but which denotes zero
    # is stripped just the same as the bare zero literal.
    Ensures(Implies(c.mzero == 1, Result() == 0))
    Ensures(Implies(c.mzero == 0, Result() == 1))
    # post-conditions-end
    # impl-start
    if coeff_truthy(c):
        return 1
    else:
        return 0
    # impl-end
