#!/usr/bin/env python3
"""G-CONF differential conformance check for astropy__astropy-13977 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outcomes:

  * SHADOW  — the R/I-tagged ops of Solution.lean's `dispatchUfunc` impl region,
              transliterated to Python over the *real* repo types (a real
              `Quantity.__array_ufunc__` call). The A-tagged callees
              `coreUfunc` (the unchanged dispatch body) and `canDefer` (the
              per-operand handler classification) are NOT substituted by a model
              here — they are reconstructed from the REAL repo code (the unchanged
              base-commit body, verbatim) and the REAL attribute machinery (the
              bundle's A content is `opaque`, validated by G-AX, so it is out of
              G-CONF's R/I scope). What G-CONF exercises is the CONTROL FLOW the
              change adds: branch on the body's success/recoverable-raise/fatal-
              raise outcome; defer (NotImplemented) on a recoverable raise iff an
              alternate handler is available, else re-raise; propagate a fatal
              raise; return a success value verbatim.
  * ORACLE  — `patch.diff`'s behaviour: the gold-patched
              `Quantity.__array_ufunc__` itself, called on the same operands (the
              real correctness oracle, G-RESOLVE — the harness applies patch.diff
              before this runs).

They must agree on the observable OUTCOME for every operand configuration. Exit
0 iff zero disagreements; any disagreement is a mechanical R/I-fidelity
counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + the
astropy/numpy under test only. The fuzz seed is pinned (mapping.md §4) for a
deterministic verdict.
"""
import dataclasses
import random
import sys

import numpy as np
import astropy.units as u
from astropy.units import Quantity
from astropy.units.quantity_helper import check_output, converters_and_unit

SEED = 13977
N_FUZZ = 100_000


# --- coreUfunc: the UNCHANGED body of Quantity.__array_ufunc__ (lines 639-682
#     @ base_commit), reconstructed verbatim. The patch leaves these byte-for-
#     byte identical and only wraps them; G-CONF replays them as the A-reference
#     callee (real repo code, not a model). ------------------------------------
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


# --- canDefer: the deferral classification (A-reference per-operand lookups + I
#     aggregation), transliterated verbatim from the patch. ---------------------
def can_defer(self, inputs, kwargs):
    out_normalized = kwargs.get("out", tuple())
    inputs_and_outputs = tuple(inputs) + tuple(out_normalized)
    ignored_ufunc = (None, np.ndarray.__array_ufunc__, type(self).__array_ufunc__)
    return not all(
        getattr(type(io), "__array_ufunc__", None) in ignored_ufunc
        for io in inputs_and_outputs)


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


# --- observable-outcome normalizer (the Except UfuncErr Outcome domain) -------
def normalize_value(v):
    """A stable, comparable encoding of a normally-returned value. The change
    returns the body's value VERBATIM, so equal computations encode equally."""
    if v is None:
        return ("none",)
    if isinstance(v, Quantity):
        return ("quantity", str(v.unit), np.asarray(v.value).tolist())
    if isinstance(v, np.ndarray):
        return ("ndarray", np.asarray(v).tolist())
    return ("other", repr(v))


def outcome_shadow(self, function, method, inputs, kwargs):
    """The R/I transliteration of `dispatchUfunc`: dispatch on the OUTCOME of the
    real (A-reference) body, deferring on a recoverable raise iff `canDefer`."""
    try:
        v = core_ufunc(self, function, method, *inputs, **dict(kwargs))
    except (TypeError, ValueError):
        if can_defer(self, inputs, kwargs):
            return ("defer",)                  # Except.ok Outcome.deferred
        return ("raise", "recoverable")        # Except.error recoverable (re-raise)
    except Exception:
        return ("raise", "fatal")              # Except.error fatal
    if v is NotImplemented:
        return ("defer",)                      # body's own NotImplemented (success leg)
    return ("value", normalize_value(v))       # Except.ok (Outcome.result v)


def outcome_oracle(self, function, method, inputs, kwargs):
    """patch.diff's behaviour: the gold-patched Quantity.__array_ufunc__ itself,
    classified into the same observable-outcome domain."""
    try:
        v = self.__array_ufunc__(function, method, *inputs, **dict(kwargs))
    except (TypeError, ValueError):
        return ("raise", "recoverable")
    except Exception:
        return ("raise", "fatal")
    if v is NotImplemented:
        return ("defer",)
    return ("value", normalize_value(v))


def fuzz_inputs(n, rng):
    q_m = 1 * u.m
    q_s = 1 * u.s
    duck = DuckQuantity(1 * u.mm)
    duck_list = DuckQuantity([1, 2] * u.mm)

    # --- boundary cases first (plan §4.1 step 4) -----------------------------
    # recoverable raise, deferrable -> the issue's scenario (defer)
    yield (q_m, np.add, "__call__", (q_m, duck), {})
    yield (q_m, np.subtract, "__call__", (q_m, duck), {})
    yield (q_m, np.less, "__call__", (q_m, duck), {})
    yield (q_m, np.greater, "__call__", (q_m, duck), {})
    yield (q_m, np.add, "__call__", (q_m, duck_list), {})
    # recoverable raise, NOT deferrable -> re-raise (PASS_TO_PASS still raises)
    yield (q_m, np.add, "__call__", (q_m, {"a": 1}), {})
    yield (q_m, np.add, "__call__", (q_m, q_s), {})
    # success value
    yield (q_m, np.add, "__call__", (q_m, 2 * u.m), {})
    yield (q_m, np.add, "__call__", (q_m, 100 * u.cm), {})
    yield (q_m, np.less, "__call__", (q_m, 2 * u.m), {})
    yield (q_m, np.multiply, "__call__", (q_m, 3 * u.s), {})
    # body's own NotImplemented (multiply/divide on a duck: no converter needed)
    yield (q_m, np.multiply, "__call__", (q_m, duck), {})
    yield (q_m, np.divide, "__call__", (q_m, duck), {})

    # --- randomized fuzz -----------------------------------------------------
    units = [u.m, u.cm, u.mm, u.km]
    incompat = [u.s, u.kg, u.K]
    conv_ufuncs = [np.add, np.subtract, np.less, np.greater]
    all_ufuncs = conv_ufuncs + [np.multiply, np.divide]
    for _ in range(n):
        left = rng.uniform(0.1, 9.0) * rng.choice(units)
        roll = rng.random()
        if roll < 0.4:
            # deferrable: a duck operand with a DIFFERENT unit (conv ufunc) ->
            # recoverable raise -> defer; or multiply/divide -> body NotImplemented
            f = rng.choice(all_ufuncs)
            duck_unit = rng.choice([uu for uu in units if uu != left.unit])
            d = DuckQuantity(rng.uniform(0.1, 9.0) * duck_unit)
            yield (left, f, "__call__", (left, d), {})
        elif roll < 0.6:
            # non-deferrable bad operand -> re-raise
            f = rng.choice(conv_ufuncs)
            bad = rng.choice([{"a": 1}, "str", rng.uniform(1, 9) * rng.choice(incompat)])
            yield (left, f, "__call__", (left, bad), {})
        else:
            # success: compatible operand
            f = rng.choice(all_ufuncs)
            right = rng.uniform(0.1, 9.0) * rng.choice(units)
            yield (left, f, "__call__", (left, right), {})


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for self_, function, method, inputs, kwargs in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = outcome_shadow(self_, function, method, inputs, kwargs)
        oracle = outcome_oracle(self_, function, method, inputs, kwargs)
        if shadow != oracle:
            disagreements.append(
                (function.__name__, [type(i).__name__ for i in inputs],
                 shadow, oracle))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for fn, types, sh, orc in disagreements:
            print("  ufunc=%s inputs=%s shadow=%r oracle=%r" % (fn, types, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of dispatchUfunc agrees with patch.diff "
          "behaviour on %d ufunc calls (seed=%d), 0 disagreements."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
