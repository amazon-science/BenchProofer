#!/usr/bin/env python3
"""G-AX executable soundness / faithfulness check for pydata__xarray-2905.

This bundle has NO consumed @ContractOnly axiom: the changed decision (whether
to replace an incoming value by the contents of its ``values`` attribute) is
modelled DEEPLY by the boolean ``is_recognized_container`` in model.py and the
verified branch of ``normalize_self_describing``. What must be checked is that
this deep model is FAITHFUL to the real normalization step in xarray, namely:

    surviving value = data.values    iff   data is a recognized self-describing
                                           container (pandas Series / Index /
                                           DataFrame)
                    = data           otherwise   (INCLUDING a plain user object
                                           that merely exposes a .values attr)

and that the model's input invariant
    is_recognized_container  ==>  exposes_values
is sound for the real pandas container types (not an artificially convenient
assumption).

We exercise the REAL ``xarray.core.variable.as_compatible_data`` (the function
the gold patch edits) and the public ``Variable`` constructor on the
discriminating inputs and assert the observed wrapped data matches the deep
model. Imports numpy / pandas / xarray (the exact libraries the patched code
uses), available in the evaluation container. Exit 0 iff every obligation
holds.
"""
import sys

import numpy as np
import pandas as pd

from xarray.core.variable import as_compatible_data, Variable


# --- deep-model reference (kept in lock-step with model.py) ------------------

def deep_model(is_recognized_container, exposes_values, identity,
               values_identity):
    """model.py's normalize_self_describing as a pure Python function over the
    identity tags: unwrap to .values iff the value is a recognized container,
    otherwise keep the value itself."""
    assert (not is_recognized_container) or exposes_values, (
        "model input invariant violated: a recognized container must expose "
        ".values")
    if is_recognized_container:
        return values_identity
    return identity


# --- discriminating user objects --------------------------------------------

class HasValuesScalar:
    """The issue's `HasValues`: exposes a scalar .values attribute but is not a
    pandas type.  exposes_values=True, is_recognized_container=False."""
    values = 5


class HasValuesArray:
    """A plain user object whose .values is array-like (still not pandas)."""
    def __init__(self, array):
        self.values = array


def assert_passes_through(obj):
    """The real step must keep the object itself (a 0-d object array whose item
    IS the original object), NOT coerce it to its .values contents.  Asserted
    via both the direct callee and the public Variable constructor (the F2P
    oracle uses `Variable(dims=(), data=obj)._data.item() is obj`)."""
    r = as_compatible_data(obj)
    arr = np.asarray(r)
    assert arr.dtype == object and arr.shape == (), (
        "non-container should wrap as a 0-d object array, got dtype=%r shape=%r"
        % (arr.dtype, arr.shape))
    assert arr.item() is obj, (
        "non-container value was coerced away from itself (the bug)")
    v = Variable(dims=(), data=obj)
    assert v._data.item() is obj, (
        "Variable coerced a plain .values-bearing object (the bug)")


def assert_unwrapped(container):
    """A recognized pandas container must be unwrapped to its .values content."""
    assert hasattr(container, "values"), (
        "model invariant unsound: %r lacks .values"
        % type(container).__name__)
    r = as_compatible_data(container)
    assert np.array_equal(np.asarray(r), np.asarray(container.values)), (
        "%s was not unwrapped to its .values content"
        % type(container).__name__)


def main():
    # === A-reference faithfulness: NON-recognized values pass through ========
    obj1 = HasValuesScalar()
    assert_passes_through(obj1)
    assert deep_model(False, True, id(obj1), id(obj1.values)) == id(obj1)

    obj2 = HasValuesArray(np.arange(3))
    assert_passes_through(obj2)
    assert deep_model(False, True, id(obj2), id(obj2.values)) == id(obj2)

    class Bare:
        pass
    bare = Bare()
    assert_passes_through(bare)
    assert deep_model(False, False, id(bare), 0) == id(bare)

    # === recognized containers ARE unwrapped to .values =====================
    assert_unwrapped(pd.Series([1, 2, 3]))
    assert deep_model(True, True, 111, 222) == 222
    assert_unwrapped(pd.Index([10, 20, 30]))
    assert deep_model(True, True, 333, 444) == 444
    assert_unwrapped(pd.DataFrame({"a": [1, 2], "b": [3, 4]}))
    assert deep_model(True, True, 555, 666) == 666

    # === the input invariant is sound for the real pandas types =============
    for container in (pd.Series([1.0]), pd.Index([1]),
                      pd.DataFrame({"x": [1]})):
        assert hasattr(container, "values"), (
            "model invariant unsound: recognized container %r lacks .values"
            % type(container).__name__)

    print("G-AX OK: deep model is_recognized_container is faithful to the real "
          "as_compatible_data on 3 non-container pass-through cases (incl. the "
          "issue's scalar-.values object and the F2P Variable(dims=()) oracle) "
          "+ 3 pandas container unwrap cases; input invariant (recognized => "
          "exposes values) holds on the real pandas types.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
