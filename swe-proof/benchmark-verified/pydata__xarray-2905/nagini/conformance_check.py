#!/usr/bin/env python3
"""G-CONF differential conformance check for pydata__xarray-2905 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures) stripped. The `Incoming` carrier becomes a plain
Python class (same fields, no contracts). There are no @ContractOnly callees
and no @Pure helpers in this bundle, and no PSeq is used, so no sequence shim
is needed.

ORACLE: the REAL repo function the model models per mapping.md —
`xarray.core.variable.as_compatible_data` (the normalization step that decides
whether an incoming value is replaced by the contents of its ``values``
attribute lives inside it). The gate applies the gold diff to /testbed before
this script runs; PYTHONPATH=/testbed makes the patched module importable.
This script never applies any diff itself.

Type bridge (mapping.md sections 1-2): the model works over identity tags —
  is_recognized_container <-> isinstance(obj, (pd.Series, pd.Index, pd.DataFrame))
  exposes_values          <-> hasattr(obj, "values")
  identity                <-> id(obj)
  values_identity         <-> id(obj.values)
and the model's return value is the tag of the object that survives the
normalization step. The step itself is inline in the real function, so the
surviving object is observed through the function's public outcome:
  - if the wrapped result is a 0-d object array whose single item IS the
    original object, the object itself survived (tag = id(obj));
  - else if the wrapped result's content equals the array form of
    obj.values, the ``values`` contents survived (tag = id(obj.values)).
Generated inputs are constructed so the two outcomes are distinguishable and
so they reach the modeled step unchanged (opaque user objects and the three
recognized pandas container kinds; no tuples/Timestamps/ndarrays that earlier
branches of the real function would transform first). Content is kept to
plain int/float/str/bool values so the downstream dtype round-trips preserve
equality. The model's Requires (a recognized container exposes ``values``)
holds by construction for bits derived from real objects and is asserted.

>= 1e5 Requires-satisfying inputs: structured boundary cases (the issue's
scalar-.values object, array-.values objects, bare objects, all three pandas
container kinds, self-referential .values) plus 100000 fuzz inputs.
Pinned fuzz seed: 290520.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outcomes and exits 1. stdlib + numpy + pandas + xarray (the libraries the
patched code itself uses).
"""
import random
import sys

import numpy as np
import pandas as pd


SEED = 290520
N_FUZZ = 100_000


# --- the Incoming carrier from model.py, contracts stripped -------------------

class Incoming:
    def __init__(self, is_recognized_container, exposes_values,
                 identity, values_identity):
        assert (not is_recognized_container) or exposes_values
        self.is_recognized_container = is_recognized_container
        self.exposes_values = exposes_values
        self.identity = identity
        self.values_identity = values_identity


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def normalize_self_describing(data):
    if data.is_recognized_container:
        result = data.values_identity
    else:
        result = data.identity
    return result


# --- discriminating user objects ----------------------------------------------

class WithValues:
    """An opaque user object exposing a .values attribute; NOT a pandas type."""
    def __init__(self, values):
        self.values = values


class Bare:
    """An opaque user object with no .values attribute."""
    def __init__(self, tag):
        self._tag = tag


RECOGNIZED = (pd.Series, pd.Index, pd.DataFrame)
_NO_VALUES = object()


# --- bridge: real object <-> model input facts ---------------------------------

def classification_bits(obj):
    is_recognized = isinstance(obj, RECOGNIZED)
    exposes = hasattr(obj, "values")
    values_obj = obj.values if exposes else _NO_VALUES
    values_tag = id(values_obj) if exposes else 0
    return (Incoming(is_recognized, exposes, id(obj), values_tag), values_obj)


def real_surviving_tag(as_compatible_data, obj, values_obj):
    """Run the REAL function and map its observable outcome back to the tag of
    the object that survived the normalization step (see module docstring).
    Returns None when the outcome matches neither signature."""
    r = as_compatible_data(obj)
    arr = np.asarray(r)
    if arr.dtype == object and arr.shape == () and arr.item() is obj:
        return id(obj)
    if values_obj is not _NO_VALUES:
        vals = np.asarray(values_obj)
        if arr.shape == vals.shape and np.array_equal(arr, vals):
            return id(values_obj)
    return None


def check_one(as_compatible_data, obj):
    bits, values_obj = classification_bits(obj)
    shadow = normalize_self_describing(bits)
    real = real_surviving_tag(as_compatible_data, obj, values_obj)
    if real != shadow:
        def describe(tag):
            if tag == id(obj):
                return "the object itself (tag %d)" % tag
            if values_obj is not _NO_VALUES and tag == id(values_obj):
                return "the .values contents (tag %d)" % tag
            return "unrecognizable outcome (%r)" % (tag,)
        return ("DISAGREEMENT\n"
                "  input: %r (type %s)\n"
                "  bits: is_recognized_container=%r exposes_values=%r "
                "identity=%d values_identity=%d\n"
                "  shadow survivor: %s\n"
                "  real survivor:   %s"
                % (obj, type(obj).__name__,
                   bits.is_recognized_container, bits.exposes_values,
                   bits.identity, bits.values_identity,
                   describe(shadow), describe(real)))
    return None


# --- input generation -----------------------------------------------------------

def boundary_cases():
    class ScalarValues:
        """The issue's shape: a plain object whose .values is a scalar."""
        values = 5
    cases = [
        # non-recognized, exposes .values: must pass through unchanged
        ScalarValues(),
        WithValues(np.arange(3)),
        WithValues(np.array([1.5, 2.5])),
        WithValues([1, 2, 3]),
        WithValues("some string"),
        WithValues(0),
        WithValues(None),
        WithValues(np.array([], dtype=int)),
        WithValues(np.array(7)),
        WithValues(np.array([[1, 2], [3, 4]])),
        # non-recognized, no .values
        Bare(0),
        Bare(-1),
        # recognized containers: must be replaced by their .values contents
        pd.Series([1, 2, 3]),
        pd.Series([1.0]),
        pd.Series([True, False]),
        pd.Series([], dtype=float),
        pd.Index([10, 20, 30]),
        pd.Index([0.5, 1.5]),
        pd.DataFrame({"a": [1, 2], "b": [3, 4]}),
        pd.DataFrame({"x": [1.0]}),
    ]
    # self-referential .values: both possible survivors carry the same tag
    loop = WithValues(None)
    loop.values = loop
    cases.append(loop)
    return cases


def fuzz_object(rng):
    kind = rng.random()
    if kind < 0.45:
        # non-recognized object exposing .values of assorted shapes/content
        choice = rng.randrange(6)
        if choice == 0:
            v = rng.randint(-10**6, 10**6)
        elif choice == 1:
            v = rng.uniform(-1e6, 1e6)
        elif choice == 2:
            v = np.array([rng.randint(-100, 100)
                          for _ in range(rng.randint(0, 6))])
        elif choice == 3:
            v = np.array(rng.uniform(-100, 100))
        elif choice == 4:
            v = "s%d" % rng.randint(0, 999)
        else:
            v = [rng.random() for _ in range(rng.randint(0, 4))]
        return WithValues(v)
    if kind < 0.65:
        # non-recognized object with no .values
        return Bare(rng.randint(0, 10**9))
    # recognized pandas containers with simple numeric/bool content
    n = rng.randint(0, 5)
    which = rng.randrange(3)
    if which == 0:
        data = [rng.randint(-1000, 1000) for _ in range(n)]
        return pd.Series(data, dtype=float if rng.random() < 0.3 else int)
    if which == 1:
        return pd.Index([rng.randint(-1000, 1000) for _ in range(max(n, 0))],
                        dtype=int)
    return pd.DataFrame({"c%d" % j: [rng.randint(-50, 50)
                                     for _ in range(max(n, 1))]
                         for j in range(rng.randint(1, 3))})


def main():
    # REAL repo symbol (the function the model models, per mapping.md):
    from xarray.core.variable import as_compatible_data

    checked = 0
    n_boundary = 0
    for obj in boundary_cases():
        err = check_one(as_compatible_data, obj)
        if err:
            print(err)
            return 1
        checked += 1
        n_boundary += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        obj = fuzz_object(rng)
        err = check_one(as_compatible_data, obj)
        if err:
            print(err)
            return 1
        checked += 1

    import json
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    print("G-CONF OK: shadow impl == real normalization outcome on %d inputs "
          "(%d boundary + %d fuzz, seed %d)."
          % (checked, n_boundary, N_FUZZ, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
