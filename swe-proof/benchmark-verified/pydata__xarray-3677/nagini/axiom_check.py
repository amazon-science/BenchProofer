#!/usr/bin/env python3
"""G-AX executable soundness check for pydata__xarray-3677.

Validates the single kind-A obligation of this bundle:

  (A-reference) the deep model `as_mapping` (model.py) == the REAL conversion
      callee the fix invokes, `xarray.DataArray.to_dataset()`, on BOTH of its
      outcomes: the one-entry Dataset it produces for a named array, and the
      undefinedness it reports for an array whose name is also one of its own
      coordinate names (dataarray.py:472-476). The conversion of
      an array-shaped operand into a mapping-shaped one is modeled DEEPLY (an
      ordinary verified function), not behind a consumed axiom; G-AX validates
      that deep model against the real callee on boundary + randomized inputs.

`as_mapping`'s relied-on Ensures (model.py):
    Result().is_mapping                        # the product is mapping-shaped
    Result().name == o.name                    # same single entry name
    Result().value == o.value                  # same single entry value

Concretely, for a NAMED DataArray `da` carrying a single scalar/array value:
    ds = da.to_dataset()
  must satisfy
    * ds is an xarray.Dataset (mapping-shaped: exposes the `.items()` named-entry
      interface that `coerce_pandas_values` requires of every operand);
    * list(ds.items()) == [(da.name, <variable carrying da's data>)]
      i.e. exactly one entry, keyed by the array's name, holding its value.

There is NO consumed @ContractOnly axiom in this bundle; this is the only G-AX
obligation. Runs in-container where `xarray` is installed (the same package the
gold patch calls). Exit 0 iff every obligation holds.
"""
import random
import sys

import numpy as np
import xarray as xr


def check_to_dataset_undefined(name, data):
    """Assert as_mapping's Exsures holds on the REAL DataArray.to_dataset(): for
    an array whose name is also one of its OWN coordinate names there is no
    one-entry Dataset form, and the real callee says so instead of producing one
    (dataarray.py:472-476). This class is INSIDE the model's domain (a NAMED
    array), so the model must predict this outcome, not exclude the input."""
    if isinstance(data, list):
        # a 1-D array whose single axis is named after the entry itself, so the
        # axis-label name collides with the entry name
        da = xr.DataArray(data=data, name=name, dims=[name],
                          coords={name: list(range(len(data)))})
    else:
        da = xr.DataArray(data=data, name=name, coords={name: data})
    assert da.name in da.coords, (
        "constructed probe is not the undefined class: name=%r coords=%r"
        % (da.name, list(da.coords)))
    try:
        ds = da.to_dataset()
    except ValueError:
        return
    except Exception as exc:
        raise AssertionError(
            "to_dataset(name=%r) on a name-is-own-coordinate array failed with "
            "%s, but the model represents this outcome as the conversion being "
            "undefined: %r" % (name, type(exc).__name__, exc))
    raise AssertionError(
        "to_dataset(name=%r) on a name-is-own-coordinate array PRODUCED %r; the "
        "model's Exsures claims no one-entry form exists for this class"
        % (name, ds))


def check_to_dataset_reference(name, data):
    """Assert as_mapping's Ensures hold on the REAL DataArray.to_dataset()."""
    da = xr.DataArray(data=data, name=name)
    assert da.name not in da.coords, (
        "probe is the UNDEFINED class, not the returning one: name=%r" % (name,))
    ds = da.to_dataset()                                  # the real callee

    # (1) mapping-shaped: the product is a Dataset and exposes `.items()`
    assert isinstance(ds, xr.Dataset), (
        "to_dataset(%r, name=%r) did not produce a Dataset: %r"
        % (data, name, type(ds)))
    assert hasattr(ds, "items"), (
        "produced Dataset lacks the .items() named-entry interface")

    # (2) carries exactly the same single named variable (name + value preserved)
    items = list(ds.items())
    assert len(items) == 1, (
        "to_dataset(name=%r) produced %d data variables, expected 1: %r"
        % (name, len(items), [k for k, _ in items]))
    (got_name, got_var), = items
    assert got_name == name, (
        "to_dataset preserved wrong name: got %r expected %r"
        % (got_name, name))
    assert np.array_equal(np.asarray(got_var.values), np.asarray(data)), (
        "to_dataset preserved wrong value for name %r: got %r expected %r"
        % (name, got_var.values, data))


def main():
    # --- boundary cases ---------------------------------------------------
    boundary = [
        ("b", 1),                       # the F2P test's named array (da, data=1)
        ("a", 0),                       # the F2P receiver's lone variable shape
        ("b", -1),
        ("x", 2.0),
        ("name_with_underscore", 42),
        ("0", 0),                       # numeric-looking name
        ("longname" * 4, 7),
        ("v", [1, 2, 3]),               # 1-D array value
        ("w", [[1, 2], [3, 4]]),        # 2-D array value
        ("z", 2 ** 31),                 # large scalar
    ]
    for name, data in boundary:
        check_to_dataset_reference(name, data)

    # --- the OTHER outcome: the undefined-normalisation class ---------------
    # as_mapping's Exsures: an array whose name is one of its own coordinate
    # names has NO one-entry Dataset form. Same names/values as above, so the
    # only difference from the returning class is the collision itself.
    for name, data in [("b", 1), ("a", 0), ("x", 2.0), ("z", 7),
                       ("v", [1, 2, 3]), ("q", -5)]:
        check_to_dataset_undefined(name, data)

    # --- randomized fuzz over names and scalar/array values ---------------
    rng = random.Random(3677)
    letters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_"
    for _ in range(2000):
        n = rng.randint(1, 12)
        name = "".join(rng.choice(letters) for _ in range(n))
        kind = rng.randint(0, 2)
        if kind == 0:
            data = rng.randint(-(10 ** 6), 10 ** 6)
        elif kind == 1:
            data = rng.uniform(-1e6, 1e6)
        else:
            data = [rng.randint(-100, 100) for _ in range(rng.randint(1, 6))]
        check_to_dataset_reference(name, data)
        # the same input in the undefined class: scalar/1-D values only (a
        # coordinate must be 0-D or match the axis length)
        if not isinstance(data, list):
            check_to_dataset_undefined(name, data)

    print("G-AX OK: as_mapping deep model (== DataArray.to_dataset()) sound on "
          "%d boundary + 2000 fuzz inputs; every product is a mapping-shaped "
          "Dataset carrying the same single {name: value} variable, and on the "
          "class whose name is one of its own coordinate names the real callee "
          "reports no such form exists (the model's Exsures)"
          % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
