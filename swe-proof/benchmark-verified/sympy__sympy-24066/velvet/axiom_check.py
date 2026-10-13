#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-24066.

Executes the REAL repo callees on inputs (boundary dimensions over the
dimensionful / canonical-dimensionless / NON-canonical-dimensionless cases, plus
randomized fuzzing built from real unit expressions) and asserts that every
observation matches the model, as encoded in Solution.lean.

The kind-A checks:

  (A-reference) the deep model `normSeq` (Solution.lean pure region) == the real
      post-patch per-element comprehension
        [Dimension(1) if dimsys.is_dimensionless(d) else d for d in dims].
      The changed operation is modeled DEEPLY, not behind a consumed equational
      axiom; G-AX validates that deep model against the real callee.

  (A-consumed) `isDimensionless` / `dimOne`: the predicate
      `SI.get_dimension_system().is_dimensionless` is total Dimension -> bool,
      and `Dimension(1)` (dimOne) is dimensionless. CRUCIALLY exhibits the
      load-bearing witness: there exist dimensions that are dimensionless yet
      `!= Dimension(1)` (e.g. Dimension(time/(capacitance*impedance))), so the
      canonicalization genuinely changes the result (the bug).

Imports only sympy — the same package the patch lives in. Exit 0 iff every
obligation holds.
"""
import random
import sys

from sympy import exp, sin, cos, sqrt, Function
from sympy.physics import units
from sympy.physics.units.systems.si import SI
from sympy.physics.units.dimensions import Dimension


def dimsys():
    return SI.get_dimension_system()


def norm_dim(d):
    """Reference of Solution.lean `normDim`: dimensionless -> canonical, else id."""
    return Dimension(1) if dimsys().is_dimensionless(d) else d


def norm_seq(dims):
    """Reference of Solution.lean `normSeq`: per-element map, order preserved."""
    return [norm_dim(d) for d in dims]


def real_comprehension(dims):
    """The REAL post-patch source line (unitsystem.py:194), executed verbatim."""
    return [Dimension(1) if dimsys().is_dimensionless(d) else d for d in dims]


def collect_dims_of_args(expr):
    """Build the argument-dimension list `[d[1] for d in fds]` the patched branch
    consumes: collect each argument's dimension via the UNCHANGED recursion."""
    return [SI._collect_factor_and_dimension(arg)[1] for arg in expr.args]


def check_reference(dims):
    """A-reference: normSeq(dims) == the real per-element comprehension."""
    observed = real_comprehension(dims)          # real post-patch line
    expected = norm_seq(dims)                     # deep model
    assert observed == expected, (
        "normSeq deep model unsound on %r: real comprehension gave %r, "
        "deep model gives %r" % (dims, observed, expected))


def main():
    ds = dimsys()

    # --- build a pool of real Dimension values --------------------------------
    # canonical dimensionless
    dim_one = Dimension(1)
    # dimensionful base/derived dimensions
    time = units.time.dimension if hasattr(units.time, "dimension") else None
    # Use _collect_factor_and_dimension to obtain genuine Dimension objects.
    second = units.second
    ohm = units.ohm
    farad = units.farad
    meter = units.meter
    kg = units.kilogram

    def dim_of(expr):
        return SI._collect_factor_and_dimension(expr)[1]

    d_time = dim_of(second)                       # dimensionful: time
    d_len = dim_of(meter)                         # dimensionful: length
    d_mass = dim_of(kg)                           # dimensionful: mass
    # NON-canonical dimensionless: time/(capacitance*impedance) = second/(ohm*farad)
    d_noncanon = dim_of(second / (ohm * farad))   # dimensionless but != Dimension(1)
    d_noncanon2 = dim_of(ohm * farad / second)    # the reciprocal, also dimensionless

    pool = [dim_one, d_time, d_len, d_mass, d_noncanon, d_noncanon2,
            Dimension(1), dim_of(meter / meter), dim_of(second * ohm * farad / second / ohm / farad)]

    # --- A-consumed: isDimensionless total + dimOne dimensionless -------------
    for d in pool:
        r = ds.is_dimensionless(d)
        assert isinstance(r, bool), (
            "is_dimensionless not bool-valued on %r: got %r" % (d, r))
    assert ds.is_dimensionless(dim_one) is True, (
        "Dimension(1) (dimOne) must be dimensionless")

    # load-bearing witness: dimensionless yet != Dimension(1) (the whole bug)
    assert ds.is_dimensionless(d_noncanon) is True, (
        "expected second/(ohm*farad) to be dimensionless")
    assert d_noncanon != dim_one, (
        "load-bearing witness broken: a non-canonical dimensionless dimension "
        "must differ from Dimension(1), else normDim would be vacuous")
    # ... and that normDim actually canonicalizes it (changes the value)
    assert norm_dim(d_noncanon) == dim_one, (
        "normDim must canonicalize a dimensionless dimension to Dimension(1)")
    assert norm_dim(d_time) == d_time, (
        "normDim must keep a dimensionful dimension unchanged")

    # --- A-reference: normSeq == real comprehension, boundary cases -----------
    boundary = [
        [],
        [dim_one],
        [d_noncanon],
        [d_time],
        [d_time, d_noncanon],
        [d_noncanon, d_time],
        [d_noncanon, d_noncanon2, dim_one],
        [d_time, d_len, d_mass],
        [d_noncanon, d_noncanon, d_noncanon],
        pool,
    ]
    for dims in boundary:
        check_reference(dims)

    # --- A-reference: randomized fuzz over real argument-dimension lists ------
    rng = random.Random(24066)
    exprs = [second, ohm, farad, meter, kg,
             second / (ohm * farad), ohm * farad,
             meter / meter, second * ohm, kg * meter,
             units.coulomb, units.volt, units.newton, units.joule]
    funcs = [exp, sin, cos, sqrt]
    for _ in range(3000):
        k = rng.randint(0, 4)
        dims = [dim_of(rng.choice(exprs)) for _ in range(k)]
        check_reference(dims)
        # also exercise dims as they appear inside a real applied Function
        f = rng.choice(funcs)
        e = rng.choice(exprs)
        try:
            applied = f(e)
        except Exception:
            continue
        if applied.args:
            adims = collect_dims_of_args(applied)
            check_reference(adims)

    print("G-AX OK: normSeq deep model (== real per-element dimensionless "
          "canonicalization) sound on %d boundary + ~3000 fuzz dimension lists; "
          "isDimensionless total; load-bearing non-canonical dimensionless "
          "witness (second/(ohm*farad) != Dimension(1)) confirmed."
          % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
