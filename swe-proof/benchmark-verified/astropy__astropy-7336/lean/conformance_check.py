#!/usr/bin/env python
"""G-CONF for astropy__astropy-7336.

Differential test of the R/I legs of `implementation_applyReturnAnnotation`
against the PATCHED unit-validating function wrapper (the gate git-applies the
gold patch before running this, so `astropy.units.quantity_input` here is the
fixed code).

Modeled behavior (the return-finalizing epilogue):

  * R leg (op 1, the guard): the produced value is converted to the return
    annotation exactly when that annotation designates a CONCRETE UNIT — i.e.
    when it is neither the "no annotation" sentinel nor `None`.
  * A-reference leg (op 2): on the concrete-unit branch, the value is converted
    with the REAL repo primitive `Quantity.to(unit)`.
  * I leg (op 3): otherwise the produced value is returned unchanged.

Shadow (this file): decide convert-vs-passthrough by the modeled three-way
annotation classification, performing the conversion with the real
`Quantity.to`. Oracle: the value the real patched `@u.quantity_input`-decorated
function actually returns for the same (produced-value, annotation) pair.

stdlib + astropy only. Exit 0 iff zero disagreements over >=1e5 fuzzed inputs.
"""
import random
import sys
import traceback

SEED = 7336
N = 100_000


def build():
    import astropy.units as u
    return u


def classify(annot, u, empty):
    """Three-way classification of the return annotation (the modeled
    `RetAnnotation`): 'empty' (absent), 'noUnit' (explicit None), or
    'unit' (a concrete unit)."""
    if annot is empty:
        return "empty"
    if annot is None:
        return "noUnit"
    return "unit"


def shadow(produced, annot, u, empty):
    """Modeled result: convert iff the annotation designates a concrete unit
    (R leg); the conversion itself uses the real `Quantity.to` (A-reference);
    otherwise pass the produced value through unchanged (I leg)."""
    kind = classify(annot, u, empty)
    if kind == "unit":
        return produced.to(annot)          # A-reference: real Quantity.to
    return produced                         # passthrough (empty or noUnit)


def oracle(produced, annot, u, empty):
    """Result the real patched decorator returns for a function that produces
    `produced` and declares return annotation `annot`."""
    if annot is empty:
        @u.quantity_input
        def f(x: u.m):
            return produced
    else:
        # Build a function whose return annotation is exactly `annot`.
        def f(x: u.m):
            return produced
        f.__annotations__["return"] = annot
        f = u.quantity_input(f)
    return f(1.0 * u.m)


def same(a, b, u):
    """Compare two finalized results: identical None, or equal Quantity (value
    and unit)."""
    if a is None or b is None:
        return a is None and b is None
    if isinstance(a, u.Quantity) and isinstance(b, u.Quantity):
        return a.unit == b.unit and bool((a.value == b.value).all() if hasattr(a.value, "all")
                                         else a.value == b.value)
    return a == b


def main():
    u = build()
    import inspect
    empty = inspect.Signature.empty

    rng = random.Random(SEED)
    units = [u.m, u.km, u.cm, u.mm, u.deg, u.arcsec, u.arcmin, u.rad]
    # annotation choices: absent (empty), explicit None, or a concrete unit.
    annot_choices = ["empty", "none"] + ["unit"] * 6

    failures = []
    for i in range(N):
        val = rng.uniform(-1e6, 1e6) * (10 ** rng.randint(-6, 6))
        src_unit = rng.choice(units)
        produced = val * src_unit

        choice = rng.choice(annot_choices)
        if choice == "empty":
            annot = empty
        elif choice == "none":
            annot = None
        else:
            # concrete unit convertible to the produced value's unit
            conv = [un for un in units if un.is_equivalent(src_unit)]
            annot = rng.choice(conv)

        try:
            o = oracle(produced, annot, u, empty)
        except Exception as e:
            failures.append(f"case {i}: oracle raised {type(e).__name__}: {e}")
            if len(failures) > 20:
                break
            continue
        try:
            s = shadow(produced, annot, u, empty)
        except Exception as e:
            failures.append(f"case {i}: shadow raised {type(e).__name__}: {e}")
            if len(failures) > 20:
                break
            continue

        if not same(o, s, u):
            failures.append(f"case {i}: annot={annot!r} produced={produced!r} "
                            f"oracle={o!r} shadow={s!r}")
            if len(failures) > 20:
                break

    if failures:
        print("status=fail")
        for f in failures[:20]:
            print("  -", f)
        print(f"({len(failures)} disagreements)")
        return 1

    print(f"status=pass R/I legs agree with patched wrapper over {N} fuzzed "
          f"inputs (guard classifies empty/None/unit; concrete-unit branch "
          f"converts via real Quantity.to, else passthrough)")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        traceback.print_exc()
        print("status=error")
        sys.exit(2)
