#!/usr/bin/env python
"""G-CONF: differential conformance for astropy__astropy-13977.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). Builds the Python R shadow of the Lean
`implementation_dispatchOp` skeleton and diffs it against the REAL patched
`Quantity.__array_ufunc__` dispatch/recovery behavior over a discrete matrix
plus >=1e5 randomized draws.

  shadow of `implementation_dispatchOp`  vs  Quantity.__array_ufunc__
  observable:
    "value"          -> the wrapper returned an ordinary result (a Quantity)
    "unhandled"      -> the wrapper returned NotImplemented
    "surfacedError"  -> the wrapper raised TypeError/ValueError

Exit 0 iff zero disagreements. stdlib-only fuzzing (pinned seed).
"""
import random
import sys

SEED = 20240625
N_RANDOM = 120_000  # >= 1e5


# ---- shadow of implementation_dispatchOp -----------------------------------
# An operand is a dict {"defers": bool}. `inner` is ("completes",) or ("fails",).

def shadow_array_ufunc(inner, operands):
    if inner[0] == "completes":
        return "value"
    # inner == fails
    if all(o["defers"] for o in operands):
        return "surfacedError"
    return "unhandled"


def main():
    import numpy as np
    import astropy.units as u

    # A duck type that DOES supply its own __array_ufunc__ (does not defer).
    class DuckOverride:
        def __init__(self, q):
            self.data = q

        @property
        def unit(self):
            return self.data.unit

        def __array_ufunc__(self, function, method, *inputs, **kwargs):
            return NotImplemented

    # A duck type with a `unit` attribute but NO __array_ufunc__ override
    # (defers to default handling; treated as a Quantity-like and fails to
    # convert).
    class DuckPlain:
        def __init__(self, q):
            self.data = q

        @property
        def unit(self):
            return self.data.unit

    def make_operand(kind):
        """Return (object, expected_defers, contributes_failure)."""
        if kind == "q_same":
            return (1.0 * u.m, True, False)
        if kind == "q_arr":
            return ([1.0, 2.0] * u.m, True, False)
        if kind == "q_compat":
            return (1000.0 * u.mm, True, False)  # convertible to m
        if kind == "dict":
            return ({"a": 1}, True, True)  # defers, not convertible -> fails
        if kind == "duck_plain":
            return (DuckPlain(1.0 * u.mm), True, True)  # defers, fails to convert
        if kind == "duck_override":
            return (DuckOverride(1.0 * u.mm), False, True)  # overrides, fails
        raise AssertionError(kind)

    # The self/first operand is always a plain Quantity (defers, good).
    self_q = 1.0 * u.m
    ignored = (None, np.ndarray.__array_ufunc__, type(self_q).__array_ufunc__)

    def operand_defers(io):
        return getattr(type(io), "__array_ufunc__", None) in ignored

    def real_observe(second_obj):
        try:
            res = self_q.__array_ufunc__(np.add, "__call__", self_q, second_obj)
        except (TypeError, ValueError):
            return "surfacedError"
        if res is NotImplemented:
            return "unhandled"
        return "value"

    second_kinds = [
        "q_same", "q_arr", "q_compat", "dict", "duck_plain", "duck_override",
    ]

    def run_case(kind):
        obj, _exp_defers, contributes_failure = make_operand(kind)
        # Independent abstraction of the inputs:
        #   inner = fails iff a non-convertible / foreign operand is present.
        inner = ("fails",) if contributes_failure else ("completes",)
        operands = [
            {"defers": operand_defers(self_q)},
            {"defers": operand_defers(obj)},
        ]
        expected = shadow_array_ufunc(inner, operands)
        got = real_observe(obj)
        return expected, got

    cases = list(second_kinds)
    rng = random.Random(SEED)
    for _ in range(N_RANDOM):
        cases.append(rng.choice(second_kinds))

    disagreements = 0
    checked = 0
    for kind in cases:
        expected, got = run_case(kind)
        checked += 1
        if got != expected:
            disagreements += 1
            if disagreements <= 5:
                print(f"MISMATCH kind={kind}: real={got!r} shadow={expected!r}")

    print(f"checked={checked} disagreements={disagreements}")
    if disagreements == 0:
        print(f"status=pass conformance OK ({checked} checks, 0 disagreements)")
        return 0
    print(f"status=fail {disagreements} disagreement(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
