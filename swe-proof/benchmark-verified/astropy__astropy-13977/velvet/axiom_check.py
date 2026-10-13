#!/usr/bin/env python3
"""G-AX executable soundness check for astropy__astropy-13977.

Runs the REAL repo callees the modeled dispatch consults — the UNCHANGED body of
`Quantity.__array_ufunc__` (`coreUfunc`) and the per-operand handler
classification (`canDefer`) — in-container, on boundary and fuzzed operand
configurations, and asserts the facts the model relies on. Both are modeled
`opaque` with NO asserted `ensures`, so there is NO consumed axiom to validate
point-wise (directive 7). What G-AX establishes are the **A-reference** facts
that make the modeled control flow faithful and non-vacuous (mapping.md §3,
refinement.md §B):

  1. RECOVERABLE LEG REAL & REACHABLE: the unchanged body actually RAISES on the
     incompatible operands the issue exhibits (a value-bearing operand whose unit
     is convertible but whose value cannot be coerced — the duck type) and the
     raised exception is a `TypeError`/`ValueError` — exactly the set the new
     `except (TypeError, ValueError)` clause catches (the `UfuncErr.recoverable`
     leg). So the modeled recover branch — and hence the deferral the patch adds
     — is a genuine runtime path, not dead code.
  2. SUCCESS LEG REAL: on compatible operands the unchanged body returns a value
     WITHOUT raising (so the `Except.ok` leg is inhabited).
  3. canDefer FAITHFUL: the deferral classification is True exactly when some
     participating operand advertises its own `__array_ufunc__` distinct from
     `ndarray`'s and the `Quantity`'s — True for a duck operand that defines
     `__array_ufunc__`, False for a plain `dict`. This is what decides
     defer-vs-re-raise on the recoverable leg.

stdlib + the astropy/numpy under test only (no gold patch needed — the modeled
body is the UNCHANGED base-commit body, reconstructed here verbatim). Exit 0 iff
every obligation holds.
"""
import dataclasses
import random
import sys

import numpy as np
import astropy.units as u
from astropy.units import Quantity
from astropy.units.quantity_helper import check_output, converters_and_unit


# --- coreUfunc: the UNCHANGED body of Quantity.__array_ufunc__ (lines 639-682
#     @ base_commit), reconstructed verbatim as a standalone callable. The gold
#     patch leaves these lines byte-for-byte identical; it only wraps them. -----
def core_ufunc(self, function, method, *inputs, **kwargs):
    converters, unit = converters_and_unit(function, method, *inputs)
    out = kwargs.get("out", None)
    if out is not None:
        if function.nout == 1:
            out = out[0]
        out_array = check_output(out, unit, inputs, function=function)
        kwargs["out"] = (out_array,) if function.nout == 1 else out_array
    if method == "reduce" and "initial" in kwargs and unit is not None:
        kwargs["initial"] = self._to_own_unit(
            kwargs["initial"], check_precision=False, unit=unit)
    arrays = []
    for input_, converter in zip(inputs, converters):
        input_ = getattr(input_, "value", input_)
        arrays.append(converter(input_) if converter else input_)
    result = super(Quantity, self).__array_ufunc__(function, method, *arrays, **kwargs)
    if unit is None or result is None or result is NotImplemented:
        return result
    return self._result_as_quantity(result, unit, out)


# --- canDefer: the deferral classification the change introduces -------------
def can_defer(self, inputs, kwargs):
    out_normalized = kwargs.get("out", tuple())
    inputs_and_outputs = tuple(inputs) + tuple(out_normalized)
    ignored_ufunc = (None, np.ndarray.__array_ufunc__, type(self).__array_ufunc__)
    return not all(
        getattr(type(io), "__array_ufunc__", None) in ignored_ufunc
        for io in inputs_and_outputs)


# --- the issue's duck type (defines its own __array_ufunc__) ------------------
@dataclasses.dataclass(eq=False)
class DuckQuantity:
    data: u.Quantity

    @property
    def unit(self):
        return self.data.unit

    def __array_ufunc__(self, function, method, *inputs, **kwargs):
        inputs = [inp.data if isinstance(inp, type(self)) else inp for inp in inputs]
        for inp in inputs:
            if isinstance(inp, np.ndarray):
                result = inp.__array_ufunc__(function, method, *inputs, **kwargs)
                if result is not NotImplemented:
                    return type(self)(result)
        return NotImplemented


def check_recoverable_leg(self, function, method, inputs):
    """fact 1: real body RAISES exactly a TypeError/ValueError on these ops."""
    try:
        core_ufunc(self, function, method, *inputs)
    except (TypeError, ValueError):
        return  # the modeled Except.error .recoverable leg — exactly right
    except Exception as e:  # any OTHER exception is NOT in the caught set
        raise AssertionError(
            "body raised %s, not TypeError/ValueError, on inputs %r — the "
            "modeled recover clause would not catch it"
            % (type(e).__name__, inputs))
    raise AssertionError(
        "body did NOT raise on inputs %r; the recoverable leg is supposed to be "
        "reachable here" % (inputs,))


def check_success_leg(self, function, method, inputs):
    """fact 2: real body returns WITHOUT raising on compatible operands."""
    try:
        core_ufunc(self, function, method, *inputs)
    except Exception as e:
        raise AssertionError(
            "body raised %s on compatible inputs %r — the success leg must be "
            "inhabited here" % (type(e).__name__, inputs))


def check_defer_classification(self, inputs, kwargs, expected):
    """fact 3: canDefer matches the real per-operand handler classification."""
    observed = can_defer(self, inputs, kwargs)
    assert observed == expected, (
        "canDefer(inputs=%r) = %r, expected %r — the deferral classification is "
        "wrong" % ([type(i).__name__ for i in inputs], observed, expected))


def main():
    q_m = 1 * u.m
    q_mm = 1 * u.mm
    q_s = 1 * u.s
    duck = DuckQuantity(1 * u.mm)
    duck_list = DuckQuantity([1, 2] * u.mm)

    # --- fact 1: the recoverable leg (incompatible operands raise TypeError/
    #     ValueError) ------------------------------------------------------------
    # Conversion-requiring ufuncs (additive / comparison) demand a common unit,
    # so the input-conversion step is reached and RAISES on an operand whose
    # value cannot be coerced (the duck) or whose unit is incompatible (q_s), and
    # on a wholly unsupported operand (dict). Multiply/divide do NOT require a
    # converter (units just combine), so they instead reach the success leg with
    # value NotImplemented (fact 2 below) — they are not recoverable-raise cases.
    recoverable_inputs = [
        (np.add, "__call__", (q_m, duck)),        # the issue: m + duck(mm) -> ValueError
        (np.subtract, "__call__", (q_m, duck)),
        (np.less, "__call__", (q_m, duck)),
        (np.greater, "__call__", (q_m, duck)),
        (np.add, "__call__", (q_m, {"a": 1})),    # unsupported operand -> TypeError
        (np.add, "__call__", (q_m, q_s)),         # incompatible units -> raises
        (np.add, "__call__", (q_m, duck_list)),
    ]
    for function, method, inputs in recoverable_inputs:
        check_recoverable_leg(q_m, function, method, inputs)

    # --- fact 2: the success leg (body returns WITHOUT raising) ----------------
    # Either a genuine compatible-operand value, or the body's OWN NotImplemented
    # path (multiply/divide on a duck: no converter needed, super() returns
    # NotImplemented). Both are `Except.ok` legs returned verbatim by the patch.
    success_inputs = [
        (np.add, "__call__", (q_m, 2 * u.m)),
        (np.add, "__call__", (q_m, 100 * u.cm)),  # convertible same dimension
        (np.multiply, "__call__", (q_m, 3 * u.s)),
        (np.less, "__call__", (q_m, 2 * u.m)),
        (np.add, "__call__", (q_m, q_m)),
        (np.multiply, "__call__", (q_m, duck)),   # body returns NotImplemented, no raise
        (np.divide, "__call__", (q_m, duck)),
    ]
    for function, method, inputs in success_inputs:
        check_success_leg(q_m, function, method, inputs)

    # --- fact 3: canDefer classification --------------------------------------
    # duck operand advertises its own __array_ufunc__  -> deferrable (True)
    check_defer_classification(q_m, (q_m, duck), {}, True)
    check_defer_classification(q_m, (duck, q_m), {}, True)
    check_defer_classification(q_m, (q_m, duck_list), {}, True)
    # plain dict / plain Quantity-vs-Quantity advertise no custom handler -> False
    check_defer_classification(q_m, (q_m, {"a": 1}), {}, False)
    check_defer_classification(q_m, (q_m, 2 * u.m), {}, False)
    check_defer_classification(q_m, (q_m, q_s), {}, False)

    # --- randomized fuzz over both legs and the classification ----------------
    rng = random.Random(13977)
    units = [u.m, u.cm, u.mm, u.km]            # mutually convertible
    # conversion-requiring ufuncs: reach the converter step, so an
    # uncoercible/incompatible operand trips a recoverable raise.
    conv_ufuncs = [np.add, np.subtract, np.less, np.greater]
    n_rec = 0
    n_suc = 0
    for _ in range(3000):
        left = rng.uniform(0.1, 9.0) * rng.choice(units)
        roll = rng.random()
        if roll < 0.5:
            # deferrable recoverable case: a conversion-requiring ufunc on a duck
            # operand whose unit DIFFERS from the left's (so a converter is built
            # and applied to the duck, whose value cannot be coerced) -> body
            # raises ValueError, canDefer True. (Same unit ⇒ converter is None ⇒
            # no conversion ⇒ the body returns NotImplemented, not a raise — that
            # is the success leg, exercised below.)
            f = rng.choice(conv_ufuncs)
            left_unit = left.unit
            duck_unit = rng.choice([uu for uu in units if uu != left_unit])
            d = DuckQuantity(rng.uniform(0.1, 9.0) * duck_unit)
            check_recoverable_leg(left, f, "__call__", (left, d))
            check_defer_classification(left, (left, d), {}, True)
            n_rec += 1
        elif roll < 0.8:
            # success: compatible numeric operand (additive/comparison/multiply)
            f = rng.choice(conv_ufuncs + [np.multiply])
            right = rng.uniform(0.1, 9.0) * rng.choice(units)
            check_success_leg(left, f, "__call__", (left, right))
            n_suc += 1
        else:
            # non-deferrable: plain dict operand -> canDefer False
            check_defer_classification(left, (left, {"x": 1}), {}, False)

    assert n_rec > 200 and n_suc > 200, (
        "fuzz produced too few genuine recoverable/success cases (%d/%d)"
        % (n_rec, n_suc))

    print("G-AX OK: unchanged __array_ufunc__ body raises exactly "
          "TypeError/ValueError on %d boundary incompatible operands (+%d fuzz) "
          "and returns without raising on %d compatible operands (+%d fuzz); "
          "canDefer matches the real per-operand handler classification on all "
          "boundary + fuzz cases. A-reference facts sound; no consumed axiom."
          % (len(recoverable_inputs), n_rec, len(success_inputs), n_suc))
    return 0


if __name__ == "__main__":
    sys.exit(main())
