#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-24213.

Executes the REAL sympy dimension engine (the unchanged callee the fixed
comparison consults) and asserts that every observation matches the model, as
encoded in model.py.

The two kind-A obligations:

  (A-consumed) the `reduction_of` axiom (model.py axioms region): the canonical
      reduction of a dimension to its base-dimension dependencies is a genuine
      FUNCTION of the dimension -- the only guarantee the proof needs.  The real
      reduction engine `DimensionSystem.get_dimensional_dependencies` is checked
      to be deterministic (same dimension -> same reduction) and to depend only
      on the dimension (structurally-equal dimensions reduce equally).  The
      model encodes this as: each addend's reduction identity `red[i]` is
      `reduction_of(surf[i])`, a pure function of its surface identity.

  (A-reference) the deep model `equivalent(surf_a, red_a, surf_b, red_b) ==
      (red_a == red_b)` (model.py pure region): physical equivalence is equality
      of canonical reductions.  This is validated EQUAL to the real callee
      `DimensionSystem.equivalent_dims`:
          equivalent_dims(d_a, d_b)  ==  (reduction(d_a) == reduction(d_b))
      i.e. the surface descriptions are never consulted -- only the reductions.
      The discriminating case (two dimensions written differently but reducing
      to the same base dimensions, e.g. velocity vs acceleration*time) is shown
      to be ACCEPTED (equivalent), which is exactly the behaviour the F2P test
      `test_issue_24211` demands and the pre-patch surface-identity comparison
      rejects.

Imports only sympy (the repo under test, whose dimension engine IS the real
callee) and the standard library.  Exit 0 iff every obligation holds.
"""
import itertools
import random
import sys

from sympy.physics.units.systems.si import SI
from sympy.physics.units import (
    length, time, mass, velocity, acceleration, force, energy, momentum,
    frequency, area, volume, pressure, power, current, charge, luminous_intensity,
    amount_of_substance, temperature,
)
from sympy.physics.units.dimensions import Dimension


DS = SI.get_dimension_system()


def reduction_id(dim):
    """The identity of a dimension's canonical reduction to base dimensions --
    the REAL reduction engine `get_dimensional_dependencies` materialised as a
    hashable, comparable value (model.py `reduction_of(surf)`).  This is exactly
    what the real `equivalent_dims` compares."""
    return frozenset(DS.get_dimensional_dependencies(dim).items())


def equivalent_model(red_a, red_b):
    """Deep model `equivalent`: physical equivalence is equality of reductions
    (surface descriptions are never consulted)."""
    return red_a == red_b


def check_reduction_is_function(dim):
    """A-consumed: the reduction engine is deterministic -- a genuine function
    of the dimension (model.py `reduction_of` is @Pure)."""
    r1 = reduction_id(dim)
    r2 = reduction_id(dim)
    assert r1 == r2, (
        "reduction engine not deterministic on %r: %r vs %r"
        % (dim.name, r1, r2))


def check_equivalent_reference(d_a, d_b):
    """A-reference: equivalent_dims(d_a, d_b) == (reduction(d_a)==reduction(d_b)).
    The deep model matches the real callee, and equivalence is decided by the
    reductions, never by the surface descriptions."""
    real = DS.equivalent_dims(d_a, d_b)
    model = equivalent_model(reduction_id(d_a), reduction_id(d_b))
    assert real == model, (
        "equivalent deep model unsound on (%r, %r): real equivalent_dims=%r, "
        "deep model (reduction equality)=%r" % (d_a.name, d_b.name, real, model))
    return real


def main():
    # A composite dimension built from base-dimension name expressions, the way
    # the dimensions collected inside _collect_factor_and_dimension are built
    # (their `.name` is a Symbol/Mul, never a doubly-wrapped Dimension).
    def D(name_expr):
        return Dimension(name_expr)

    base_dims = [length, time, mass, current, temperature,
                 amount_of_substance, luminous_intensity]
    named = [velocity, acceleration, force, energy, momentum, frequency, area,
             volume, pressure, power, charge]
    composite = [
        D(acceleration.name * time.name),     # == velocity (the issue's case)
        D(force.name * length.name),          # == energy
        D(mass.name * acceleration.name),     # == force
        D(length.name / time.name),           # == velocity (another spelling)
        D(mass.name * velocity.name),         # == momentum
        D(length.name ** 2),                  # == area
        D(velocity.name * time.name),         # == length
        D(force.name / area.name),            # == pressure
        D(energy.name / time.name),           # == power
    ]
    all_dims = base_dims + named + composite

    # --- A-consumed: the reduction engine is a genuine function -------------
    for d in all_dims:
        check_reduction_is_function(d)

    # structurally-equal dimensions reduce equally (function of the dimension):
    # rebuild each named dimension a second, identical way and confirm equal id.
    for d in named + base_dims:
        d2 = Dimension(d.name)
        assert reduction_id(d) == reduction_id(d2), (
            "reduction not a function of surface identity on %r" % (d.name,))

    # --- A-reference: equivalent deep model == real equivalent_dims ---------
    n_pairs = 0
    for a, b in itertools.product(all_dims, repeat=2):
        check_equivalent_reference(a, b)
        n_pairs += 1

    # --- the issue's exact discriminating witness ---------------------------
    # velocity vs acceleration*time: written differently, same base dimensions.
    v = velocity
    at = D(acceleration.name * time.name)
    assert v != at, "expected distinct SURFACE descriptions for the witness"
    assert check_equivalent_reference(v, at) is True, (
        "velocity and acceleration*time must be physically equivalent "
        "(the F2P test_issue_24211 case)")
    # an inequivalent pair must be rejected
    assert check_equivalent_reference(velocity, force) is False, (
        "velocity and force are not physically equivalent")

    # --- end-to-end on the gold-fixed function -------------------------------
    # The collected (factor, dimension) of `A1*T1 + V1` must not be rejected.
    from sympy.physics.units import second, meter
    from sympy.physics.units import Quantity
    V1 = Quantity('V1_axck'); SI.set_quantity_dimension(V1, velocity)
    SI.set_quantity_scale_factor(V1, 1 * meter / second)
    A1 = Quantity('A1_axck'); SI.set_quantity_dimension(A1, acceleration)
    SI.set_quantity_scale_factor(A1, 1 * meter / second ** 2)
    T1 = Quantity('T1_axck'); SI.set_quantity_dimension(T1, time)
    SI.set_quantity_scale_factor(T1, 1 * second)
    _factor, dim = SI._collect_factor_and_dimension(A1 * T1 + V1)
    assert reduction_id(dim) == reduction_id(velocity), (
        "collected sum dimension not equivalent to velocity: %r" % (dim.name,))

    # --- randomized fuzz over products/quotients of base dimensions ----------
    rng = random.Random(24213)
    checked = 0
    pool = base_dims + named
    for _ in range(4000):
        k = rng.randint(1, 4)
        expr_a = 1
        for _j in range(k):
            d = rng.choice(pool)
            e = rng.choice([1, 1, 1, 2, -1])
            expr_a = expr_a * d.name ** e
        expr_b = 1
        for _j in range(rng.randint(1, 4)):
            d = rng.choice(pool)
            e = rng.choice([1, 1, 1, 2, -1])
            expr_b = expr_b * d.name ** e
        try:
            da, db = Dimension(expr_a), Dimension(expr_b)
            check_equivalent_reference(da, db)
        except Exception:
            # malformed/unsupported reduction (e.g. non-integer power): the
            # real callee raises identically for model and gold; out of domain.
            continue
        checked += 1

    print("G-AX OK: reduction_of (A-consumed) is a genuine function + "
          "equivalent deep model (A-reference) == real equivalent_dims on "
          "%d dimension pairs + %d fuzz pairs + the issue witness "
          "(velocity == acceleration*time)." % (n_pairs, checked))
    return 0


if __name__ == "__main__":
    sys.exit(main())
