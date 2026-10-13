#!/usr/bin/env python3
"""G-AX executable soundness check for astropy__astropy-7336.

The bundle consumes NO `@ContractOnly` axiom inside a postcondition (the axioms
region of model.py is empty). Instead the changed behaviour is modelled DEEPLY
as the verified decision in `finalize_return` together with the pure
`convert_unit` operation. G-AX validates that deep model against the REAL
astropy callees, in-container:

  (A-reference 1) `convert_unit(q_unit, target)` deep model == the real
      `astropy.units.Quantity.to(target)` unit semantics: converting a quantity
      into a genuine `target` unit yields a quantity whose `.unit` equals that
      target unit. (Unchanged operation the wrapper invokes.)

  (A-reference 2) `finalize_return(ret, target)` decision == the real
      `astropy.units.quantity_input` wrapper return-finalisation (post-fix, the
      face of the spec):
        * a declared genuine unit return target -> the return value is converted
          into that unit (result `.unit` == target);
        * a `-> None` return target (the model's "no value" target) -> the
          return value passes through UNCHANGED (no `.to` is attempted), so a
          constructor-style function declared `-> None` returns its value as-is;
        * no declared return target -> the return value passes through unchanged.

This is exactly the discriminating behaviour: the `-> None` target is treated
like the unspecified sentinel (pass through), NOT like a genuine unit target.

Imports only `astropy.units` (the very package the gold patch edits) and the
standard library. The G-AX driver applies the gold patch before running this
script, so the wrapper under test is the fixed one. Exit 0 iff every obligation
holds.
"""
import sys

import astropy.units as u
from astropy.units.decorators import quantity_input


# --- (A-reference 1) convert_unit deep model == real Quantity.to -------------

def check_convert_unit():
    """`convert_unit(q_unit, target) == target` (model.py) mirrors the real
    `Quantity.to(target)`: the converted quantity's unit IS the target unit."""
    pairs = [
        (1.0 * u.arcsec, u.deg),
        (3.0 * u.deg, u.arcsec),
        (5.0 * u.m, u.km),
        (2.0 * u.km, u.m),
        (10.0 * u.eV, u.J),
        (1.0 * u.kg, u.g),
        (90.0 * u.deg, u.arcmin),
        (1.5 * u.s, u.ms),
    ]
    for q, target in pairs:
        converted = q.to(target)                 # real callee
        assert converted.unit == target, (
            "convert_unit deep model unsound: %r.to(%r).unit == %r, "
            "model requires it to equal the target unit"
            % (q, target, converted.unit))


# --- (A-reference 2) finalize_return decision == real wrapper ----------------

def check_genuine_target_converts():
    """A genuine unit return target -> the wrapper converts (result unit ==
    target)."""
    @quantity_input
    def f(x: u.arcsec) -> u.deg:
        return x

    out = f(1 * u.arcsec)
    assert out.unit == u.deg, (
        "finalize_return decision unsound on a genuine unit target: expected "
        "the result converted to u.deg, got unit %r" % (out.unit,))


def check_none_target_passes_through():
    """A `-> None` return target -> the wrapper passes the return value through
    UNCHANGED; it must NOT attempt a conversion. THE discriminating clause."""
    @quantity_input
    def ctor(x: u.V) -> None:
        return None

    out = ctor(1.0 * u.V)
    assert out is None, (
        "finalize_return decision unsound on the no-value (-> None) target: "
        "expected pass-through (None), got %r" % (out,))

    # A non-None return under a `-> None` annotation must ALSO pass through
    # untouched (no conversion), since None is not a genuine unit target.
    @quantity_input
    def g(x: u.arcsec) -> None:
        return x

    out2 = g(2 * u.arcsec)
    assert out2 is not None and out2.unit == u.arcsec, (
        "finalize_return decision unsound: a value returned under a -> None "
        "target must pass through unchanged (unit u.arcsec), got %r" % (out2,))


def check_unspecified_target_passes_through():
    """No declared return target -> the wrapper passes the return value through
    unchanged (the unspecified sentinel branch)."""
    @quantity_input
    def h(x: u.arcsec):
        return x

    out = h(7 * u.arcsec)
    assert out.unit == u.arcsec, (
        "finalize_return decision unsound on the unspecified target: expected "
        "pass-through (unit u.arcsec), got %r" % (out.unit,))


def main():
    check_convert_unit()
    check_genuine_target_converts()
    # The discriminating clause: under the buggy (pre-fix) wrapper a `-> None`
    # target attempts `None.to(None)` and raises AttributeError here, which
    # fails this script with a non-zero exit — so this check alone witnesses
    # that the wrapper under test is the fixed callee the deep model models.
    check_none_target_passes_through()
    check_unspecified_target_passes_through()
    print("G-AX OK: convert_unit deep model == real Quantity.to; "
          "finalize_return decision == real quantity_input wrapper "
          "(genuine unit converts; -> None and unspecified pass through).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
