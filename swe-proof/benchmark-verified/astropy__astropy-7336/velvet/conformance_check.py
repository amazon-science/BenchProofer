#!/usr/bin/env python3
"""G-CONF differential conformance check for astropy__astropy-7336 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the real repo types, via the mapping.md bijection
              (annotation ↔ Annot, return value ↔ RetVal). The changed op is the
              guard `annotation not in (empty, None)`. The A-tagged callee `.to`
              (`coerceUnit`, an A-reference) is left as the REAL callee here —
              G-CONF isolates the R/I (guard) leg; the A leg stays with G-AX.
  * ORACLE  — `patch.diff`'s behaviour: the patched `quantity_input` decorator
              applied at base_commit (the real correctness oracle, G-RESOLVE),
              exercising the genuine return post-processing tail.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image) with the gold patch
applied; stdlib + astropy only. The fuzz seed is pinned (mapping.md §4).
"""
import inspect
import random
import sys

import astropy.units as u
from astropy.units import Quantity

SEED = 7336
N_FUZZ = 100_000

_EMPTY = inspect.Signature.empty
# Genuine unit annotations to use as `.target` and the units of return values.
_UNITS = [u.m, u.km, u.arcsec, u.deg, u.eV, u.J, u.s, u.kg, u.V, u.Hz]


def observe(thunk):
    """Run thunk; project its outcome onto what the F2P/P2P tests observe:
    a returned unit, a returned None, or a raised exception type."""
    try:
        r = thunk()
    except Exception as e:                       # noqa: BLE001 — type is the observable
        return ("err", type(e).__name__)
    if r is None:
        return ("none",)
    if isinstance(r, Quantity):
        return ("ok", r.unit)
    return ("other", repr(r))


def make_wrapper(return_annotation, retval):
    """ORACLE: a function decorated by the real (patched) quantity_input, whose
    body returns `retval`, declared with the given return annotation. The arg is
    unannotated, so no argument validation interferes — only the return tail
    runs."""
    def f(x):
        return retval
    if return_annotation is not _EMPTY:
        f.__annotations__['return'] = return_annotation
    return u.quantity_input(f)


def oracle(return_annotation, retval):
    wrapper = make_wrapper(return_annotation, retval)
    return observe(lambda: wrapper(retval))


def shadow(return_annotation, retval):
    """SHADOW: the impl's guard, transliterated. annotation in (empty, None) ->
    pass the value through; else -> value.to(annotation) (real A-tagged callee)."""
    if return_annotation not in (_EMPTY, None):
        return observe(lambda: retval.to(return_annotation))
    return observe(lambda: retval)


def fuzz_inputs(n, rng):
    # annotation shapes: absent (empty), null sentinel (None), genuine units
    annot_choices = [_EMPTY, None] + _UNITS
    # return values: None (null), or a Quantity of some unit
    def mk_retval(kind, unit, mag):
        return None if kind == "null" else Quantity(mag, unit)

    # boundary cases first (every annotation shape × {None, a quantity})
    for a in annot_choices:
        yield (a, None)
        yield (a, Quantity(1.0, u.m))
        yield (a, Quantity(0.0, u.arcsec))
    # the reported crash configuration explicitly: unit annotation + None value
    yield (u.deg, None)
    yield (u.m, None)

    for _ in range(n):
        a = rng.choice(annot_choices)
        kind = rng.choice(["null", "quantity"])
        unit = rng.choice(_UNITS)
        mag = rng.uniform(-1e6, 1e6)
        yield (a, mk_retval(kind, unit, mag))


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for annot, retval in fuzz_inputs(N_FUZZ, rng):
        count += 1
        s = shadow(annot, retval)
        o = oracle(annot, retval)
        if s != o:
            disagreements.append((annot, retval, s, o))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for a, rv, s, o in disagreements:
            print("  annot=%r retval=%r shadow=%r oracle=%r" % (a, rv, s, o))
        return 1
    print("G-CONF OK: R/I shadow of processReturn agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
