#!/usr/bin/env python3
"""G-AX executable soundness check for astropy__astropy-7336.

Validates the ONE deep-model reference of this bundle (there are no consumed
axioms) against the REAL unchanged callee it models:

  (A-reference) `coerceUnit` (Solution.lean pure region) == `astropy.units`
      `Quantity.to` / `None.to`, the unit re-expression operation the patched
      return post-processing guards.

The model is PARTIAL on dimensional compatibility:

    coerceUnit (.quantity s) t = if compatible s t
                                   then .ok (.quantity t)
                                   else .error .notCompatible
    coerceUnit .null _         = .error .noConvertOp

where `compatible s t := unitKind s == unitKind t`. The model's two
obligations against the real callee are therefore:

  (Q-ok)   compatible s t  ⇒  q.to(target).unit == target
                              (re-express a quantity into a same-kind unit)
  (Q-err)  ¬ compatible s t ⇒  q.to(target) raises UnitConversionError
                              (a cross-kind target is rejected, NOT total-success)
  (N-err)  None.to(target)  raises AttributeError ('NoneType' has no 'to')

`unitKind` is pinned to the real physical dimension: units in the SAME group
below are mutually convertible (same kind ⇒ `.to` succeeds), units in DIFFERENT
groups are not (different kind ⇒ `.to` raises). This closes the over-approximation
gap of the previous check, which only ever sampled same-kind pairs and so could
never witness the cross-kind `UnitConversionError` the real callee raises.

The (N-err) observation is the crash the issue reports and the reason the fix
routes a null-sentinel annotation to the pass-through branch instead of `.to`.

Imports `astropy.units` — the same package the gold patch lives in (the repo
under test); plus stdlib. Exit 0 iff every obligation holds.
"""
import random
import sys

import astropy.units as u
from astropy.units import Quantity, UnitConversionError


# Real units grouped by physical dimension (kind). Units within a group are
# mutually convertible; units across groups are not. This grouping IS the
# concrete witness for the opaque `unitKind` tag: `compatible s t` holds iff s
# and t fall in the same group, which must coincide with real `.to` succeeding.
_GROUPS = [
    [u.m, u.km, u.cm, u.mm],        # length
    [u.s, u.minute, u.hour, u.day], # time
    [u.kg, u.g],                    # mass
    [u.deg, u.arcsec, u.arcmin, u.rad],  # angle
    [u.eV, u.J],                    # energy
    [u.V, u.mV],                    # electric potential
    [u.Hz, u.kHz],                  # frequency
]

# (source, target) within-group pairs: real `.to` MUST succeed, unit == target.
_SAME_KIND = [(s, t) for g in _GROUPS for s in g for t in g]
# (source, target) cross-group pairs: real `.to` MUST raise UnitConversionError.
_CROSS_KIND = [
    (s, t)
    for i, gi in enumerate(_GROUPS)
    for j, gj in enumerate(_GROUPS) if i != j
    for s in gi for t in gj
]


def check_quantity_ok(value, source_unit, target_unit):
    """(Q-ok): compatible s t ⇒ q.to(target).unit == target."""
    q = Quantity(value, source_unit)
    converted = q.to(target_unit)                     # real callee, must succeed
    assert converted.unit == target_unit, (
        "coerceUnit deep model unsound (same-kind success case): "
        "%r.to(%r).unit == %r, model requires the target unit %r"
        % (q, target_unit, converted.unit, target_unit))


def check_quantity_err(value, source_unit, target_unit):
    """(Q-err): NOT compatible s t ⇒ q.to(target) raises UnitConversionError.
    This is the obligation the previous (gappy) check never exercised."""
    q = Quantity(value, source_unit)
    raised = False
    try:
        q.to(target_unit)                             # real callee, must raise
    except UnitConversionError:
        raised = True
    assert raised, (
        "coerceUnit deep model unsound (cross-kind rejection case): "
        "%r.to(%r) did NOT raise UnitConversionError; model requires "
        ".error .notCompatible (source %r and target %r are different kinds)"
        % (q, target_unit, source_unit, target_unit))


def check_null_reference(target_unit):
    """(N-err): None.to(target) raises AttributeError (the reported crash) ⇔
    coerceUnit .null _ = .error .noConvertOp."""
    raised = False
    try:
        None.to(target_unit)                          # real behavior: AttributeError
    except AttributeError:
        raised = True
    assert raised, (
        "coerceUnit deep model unsound (null case): None.to(%r) did not raise "
        "AttributeError; model requires .error .noConvertOp" % (target_unit,))


def main():
    # --- (Q-ok) same-kind success: boundary + fuzz ------------------------
    for src, tgt in _SAME_KIND:
        for v in (0.0, 1.0, -1.0, 3.5, 1e3, 1e-3):
            check_quantity_ok(v, src, tgt)

    # --- (Q-err) cross-kind rejection: boundary + fuzz (the gap fix) ------
    for src, tgt in _CROSS_KIND:
        for v in (0.0, 1.0, -1.0, 3.5, 1e3, 1e-3):
            check_quantity_err(v, src, tgt)

    rng = random.Random(7336)
    for _ in range(20000):
        src, tgt = rng.choice(_SAME_KIND)
        v = rng.uniform(-1e6, 1e6)
        check_quantity_ok(v, src, tgt)
    for _ in range(20000):
        src, tgt = rng.choice(_CROSS_KIND)
        v = rng.uniform(-1e6, 1e6)
        check_quantity_err(v, src, tgt)

    # --- (N-err) null case: the reported crash ----------------------------
    targets = sorted({t for g in _GROUPS for t in g}, key=str)
    for tgt in targets:
        check_null_reference(tgt)

    print("G-AX OK: coerceUnit deep model (== Quantity.to / None.to) sound on "
          "%d same-kind successes + %d cross-kind rejections (boundary) + "
          "40000 fuzz conversions and %d null-target crash checks"
          % (len(_SAME_KIND) * 6, len(_CROSS_KIND) * 6, len(targets)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
