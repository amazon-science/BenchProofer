#!/usr/bin/env python
"""G-AX: validate the A-reference callee behavior for astropy__astropy-7336.

Runs INSIDE the instance image at base_commit (PYTHONPATH=/testbed). The gold
patch is NOT applied for G-AX, so this harness may only assert properties of the
UNCHANGED callee the fix relies on — never behavior introduced by the patch
(that is G-CONF's job, run against the patched oracle).

The bundle declares no consumed property axiom (`correct_applyReturnAnnotation`
closes by case analysis on the annotation shape). The one A-reference in the
impl is `convertTo`: on the concrete-unit branch the produced value is converted
with the real repo primitive `Quantity.to(unit)`, which the patch does NOT
touch. The soundness-critical property of that model is:

  * `convertTo` corresponds to `Quantity.to`: it re-expresses the produced value
    under the named unit, and the result's unit IS the requested annotation unit
    (so `result.unit == annotation`). This is what the concrete-unit branch of
    the contract buys, and what the decorator's `return return_.to(annot)`
    actually does — identically before and after the patch.

We also confirm the ABSENT-annotation passthrough (the pre-existing `else`
branch, unchanged by the patch): with no return annotation the wrapper returns
the produced value unchanged, attempting no conversion. The `None`-annotation
passthrough is the patched behavior and is intentionally NOT tested here — it is
covered by G-CONF against the gold-patched oracle.

stdlib-only (+ astropy under test). Exit 0 iff sound.
"""
import random
import sys
import traceback

SEED = 7336
N_FUZZ = 2000


def build():
    import astropy.units as u
    return u


def main():
    u = build()
    import inspect
    empty = inspect.Signature.empty

    rng = random.Random(SEED)
    units = [u.m, u.km, u.cm, u.mm, u.deg, u.arcsec, u.arcmin, u.rad]
    failures = []

    def decorate(annot):
        produced_holder = {}

        def f(x: u.m):
            return produced_holder["v"]
        if annot is not empty:
            f.__annotations__["return"] = annot
        return u.quantity_input(f), produced_holder

    # --- Boundary 1: absent annotation passes value through -------------------
    f_empty, holder = decorate(empty)
    holder["v"] = 5.0 * u.deg
    try:
        r = f_empty(1.0 * u.m)
        if not (isinstance(r, u.Quantity) and r.unit == u.deg and r.value == 5.0):
            failures.append(f"absent annotation did not pass through: got {r!r}")
    except Exception as e:
        failures.append(f"absent annotation raised {type(e).__name__}: {e}")

    # --- Boundary 2: concrete unit converts, result unit == annotation --------
    f_unit, holder = decorate(u.km)
    holder["v"] = 2000.0 * u.m
    try:
        r = f_unit(1.0 * u.m)
        ref = (2000.0 * u.m).to(u.km)
        if not (isinstance(r, u.Quantity) and r.unit == u.km and r.unit == ref.unit
                and abs(float(r.value) - float(ref.value)) < 1e-9):
            failures.append(f"concrete-unit branch mismatch: got {r!r}, ref {ref!r}")
    except Exception as e:
        failures.append(f"concrete-unit branch raised {type(e).__name__}: {e}")

    # --- Fuzz: convertTo == Quantity.to on the concrete-unit branch -----------
    for _ in range(N_FUZZ):
        src = rng.choice(units)
        conv = [un for un in units if un.is_equivalent(src)]
        tgt = rng.choice(conv)
        val = rng.uniform(-1e6, 1e6) * (10 ** rng.randint(-6, 6))
        produced = val * src
        f_u, holder = decorate(tgt)
        holder["v"] = produced
        try:
            r = f_u(1.0 * u.m)
            ref = produced.to(tgt)              # the real A-reference primitive
            if not (isinstance(r, u.Quantity) and r.unit == ref.unit
                    and abs(float(r.value) - float(ref.value))
                        <= 1e-6 * (1 + abs(float(ref.value)))):
                failures.append(
                    f"convertTo != Quantity.to: src={src} tgt={tgt} "
                    f"got {r!r} ref {ref!r}")
        except Exception as e:
            failures.append(f"convert fuzz raised {type(e).__name__}: {e}")
        if len(failures) > 20:
            break

    if failures:
        print("status=fail")
        for f in failures[:20]:
            print("  -", f)
        print(f"({len(failures)} total)")
        return 1

    print(f"status=pass A-reference convertTo consistent with real Quantity.to; "
          f"absent annotation passes value through (no conversion attempted); "
          f"boundary + {N_FUZZ} fuzz scenarios")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        traceback.print_exc()
        print("status=error")
        sys.exit(2)
