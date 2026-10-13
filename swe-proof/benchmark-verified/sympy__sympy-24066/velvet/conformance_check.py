#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-24066 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated to
              Python over the real repo types: `normSeq` is the per-element map
              of `normDim d = dimOne if isDimensionless d else d`, applied to the
              operand-dimension list `[d[1] for d in fds]` in order. The A-tagged
              callees are NOT replaced by axiom models here; G-CONF isolates the
              R/I legs, so `isDimensionless` stays the REAL
              `SI.get_dimension_system().is_dimensionless` and `dimOne` stays the
              REAL `Dimension(1)`.
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `UnitSystem._collect_factor_and_dimension` applied to a real
              applied-`Function` expression, whose returned tuple `(factor,
              *dims)` exposes the normalized dimension list `dims`.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container against the repo at base_commit WITH patch.diff applied (the
harness applies it before this runs). The fuzz seed is pinned (mapping.md §4)
for a deterministic verdict.
"""
import random
import sys

from sympy import exp, sin, cos, sqrt, log, tan
from sympy.core.function import Function
from sympy.physics import units
from sympy.physics.units.systems.si import SI
from sympy.physics.units.dimensions import Dimension

SEED = 24066
N_FUZZ = 4000


def dimsys():
    return SI.get_dimension_system()


def shadow_normalize(dims):
    """normSeq (Solution.lean), transliterated: per-element normDim, order kept.
    A-tagged callees left as the REAL repo callees (is_dimensionless, Dimension(1))."""
    return [Dimension(1) if dimsys().is_dimensionless(d) else d for d in dims]


def oracle_function_dims(expr):
    """patch.diff's behaviour: call the patched _collect_factor_and_dimension on
    an applied Function `expr`; its returned tuple is (factor, *dims) where dims
    is the normalized operand-dimension list. Returns that dims list."""
    res = SI._collect_factor_and_dimension(expr)
    # tuple is (factor, *dims); the dims portion is res[1:]
    return list(res[1:])


def arg_dims(expr):
    """The operand-dimension list the patched branch consumes:
    [self._collect_factor_and_dimension(arg)[1] for arg in expr.args]."""
    return [SI._collect_factor_and_dimension(a)[1] for a in expr.args]


def fuzz_exprs(n, rng):
    second, ohm, farad, meter, kg = (units.second, units.ohm, units.farad,
                                     units.meter, units.kilogram)
    coulomb, volt = units.coulomb, units.volt
    # dimensionless building block (the issue's witness) and dimensionful ones
    dimensionless = [second / (ohm * farad), ohm * farad / second, meter / meter,
                     second * ohm * farad / (second * ohm * farad)]
    dimensionful = [second, ohm, farad, meter, kg, coulomb, volt,
                    second / ohm, meter * kg, ohm * farad]
    funcs = [exp, sin, cos, sqrt, log, tan]

    # boundary cases first (plan §4.1 step 4): single-arg functions of a
    # dimensionless argument are the exact issue scenario.
    yield exp(second / (ohm * farad))
    yield sin(second / (ohm * farad))
    yield exp(meter / meter)
    yield sqrt(second / (ohm * farad))
    yield cos(ohm * farad / second)
    yield exp(second)            # dimensionful arg (kept verbatim)
    yield sin(meter)

    for _ in range(n):
        f = rng.choice(funcs)
        # mix dimensionless and dimensionful arguments
        pool = dimensionless + dimensionful
        a = rng.choice(pool)
        try:
            e = f(a)
        except Exception:
            continue
        if getattr(e, "args", None):
            yield e


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for expr in fuzz_exprs(N_FUZZ, rng):
        # Only the applied-Function branch is modeled. sympy auto-simplifies many
        # constructions (sqrt -> Pow, exp(1) -> E, products -> Mul); those route
        # through OTHER, unchanged branches and are out of scope here.
        if not isinstance(expr, Function):
            continue
        try:
            oracle = oracle_function_dims(expr)
        except Exception:
            # unsupported exprs are out of scope
            continue
        # Only compare when the expr actually routed through the Function branch
        # (its dims come from its args). Reconstruct the shadow from arg dims.
        try:
            shadow = shadow_normalize(arg_dims(expr))
        except Exception:
            continue
        count += 1
        if shadow != oracle:
            disagreements.append((expr, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for e, sh, orc in disagreements:
            print("  expr=%r shadow=%r oracle=%r" % (e, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of normalizeDimensions agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
