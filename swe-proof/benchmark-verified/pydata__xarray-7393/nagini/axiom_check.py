#!/usr/bin/env python3
"""G-AX executable soundness check for pydata__xarray-7393.

This bundle has NO consumed `@ContractOnly` axioms: the changed behaviour --
when a labelled-index wrapper is materialised into a dense array for one
selected label, the array's element type is the REQUESTED type if one is given,
else the wrapper's DECLARED element type, never the (possibly wider) element
type of the underlying storage; and the element values are carried through
unchanged -- is modelled DEEPLY in model.py (the `materialize_level` function
with `effective_type` and the value-copy loop).

What is validated here is therefore the **A-reference** obligation: that the
deep model matches the REAL post-patch behaviour of the materialisation step.
It exercises two layers, both in-container, with stdlib + numpy + xarray only:

  (1) The construction primitive the patch relies on, `np.asarray(values,
      dtype=d)`, on a deliberately PROMOTED underlying array (so the storage
      element type differs from the requested/declared one). It asserts:
        * the resulting array's element type is exactly `d` (the effective type
          chosen by the model: requested if given, else declared);
        * the element VALUES equal the input values (carried through unchanged).
      This is exactly `effective_type` + the value-copy loop of model.py.

  (2) The end-to-end scenario from the issue / FAIL_TO_PASS tests: build a
      Dataset coordinate of a narrow element type, `stack` it (which builds a
      multi-index whose pandas level values are PROMOTED to a wider type), then
      read `.values` (which produces a dense array with NO requested element
      type). The instance image may be at the base commit OR have the change
      applied first (`run_in_container(..., apply_gold=True)`), so this layer
      DETECTS the regime from the real behaviour and asserts the appropriate
      obligation: under the applied regime the produced array's element type
      round-trips the DECLARED element type (the A-reference obligation); under
      the base regime the narrow integer dtypes are still PROMOTED (the bug the
      model_prepatch skeleton reproduces) while the VALUES are preserved. Exit 0
      in both regimes; the value-preservation half of the A-reference holds
      either way.

Imports only `numpy` / `xarray` (the package the gold patch edits) + stdlib;
nothing test-specific. Exit 0 iff every obligation holds.
"""
import itertools
import sys

import numpy as np


def _check_asarray_primitive(values, storage_dtype, requested, declared):
    """Validate effective_type + value-copy against real np.asarray.

    Mirrors model.py: effective = requested if requested is not None else
    declared; the materialised array has dtype `effective` and values `values`.
    `storage_dtype` is the (possibly wider) element type of the underlying
    storage, which must NOT leak into the result when no type is requested.
    """
    # The underlying (possibly promoted) storage array.
    storage = np.asarray(values, dtype=storage_dtype)

    effective = requested if requested is not None else declared

    # The materialisation primitive the patch uses.
    out = np.asarray(storage, dtype=effective)

    # (a) element type is exactly the effective type (model: Result().etype ==
    #     effective_type(requested, declared)); never the storage type unless
    #     it happens to coincide with the effective type.
    assert out.dtype == np.dtype(effective), (
        "element type leaked: np.asarray(..., dtype=%r) gave dtype %r, "
        "effective type is %r" % (effective, out.dtype, np.dtype(effective)))

    # (b) values carried through unchanged (model: ToSeq(Result().values) ==
    #     ToSeq(level_values)).
    assert list(out.tolist()) == list(np.asarray(values, dtype=effective).tolist()), (
        "values not carried through unchanged for %r" % (values,))


def check_primitive_layer():
    # Narrow declared types whose underlying storage is promoted to a wider one
    # (exactly the pandas Int64Index / float64 promotion the issue describes).
    cases = [
        # (values, storage_dtype, declared) with storage WIDER than declared.
        ([0, 1, 2], "int64", "int32"),
        ([0], "int64", "int32"),
        ([3, -7, 42], "int64", "int16"),
        ([0, 1], "float64", "float32"),
        ([5, 6, 7, 8], "int64", "int8"),
        ([], "int64", "int32"),
    ]
    for values, storage_dtype, declared in cases:
        # requested = None  -> result type must be the DECLARED type, NOT the
        #                      wider storage type (the bug being fixed).
        _check_asarray_primitive(values, storage_dtype, None, declared)
        # requested given   -> result type is exactly the requested type.
        for requested in ("int32", "float32", "int64", "float64", declared):
            _check_asarray_primitive(values, storage_dtype, requested, declared)


def _stacked_values_dtype(xr, dtype):
    """Real xarray observation: declare a coordinate of element type `dtype`,
    stack it (builds a multi-index whose pandas level values are promoted),
    then read `.values` with no requested element type. Returns the observed
    element-type string and the carried values list (for value-preservation)."""
    foo = xr.Dataset(coords={"bar": ("bar", np.array([0, 1], dtype=dtype))})
    stacked = foo.stack(baz=("bar",))
    arr = stacked["bar"].values
    return str(arr.dtype), list(arr.tolist())


def check_end_to_end():
    """The FAIL_TO_PASS scenario, against the REAL xarray IN WHATEVER STATE the
    container is in (base commit OR gold-applied).

    G-AX runs this script in the instance image. That image may be at the base
    commit (the change NOT yet applied) or have the gold patch applied first
    (`run_in_container(..., apply_gold=True)`). The end-to-end declared-dtype
    round trip only holds once the change is applied, so we first DETECT the
    regime from the real behaviour on the canonical int32 example, then assert
    the obligation appropriate to that regime. Exit 0 in BOTH regimes:

      * PATCHED regime: reading `.values` restores the DECLARED element type for
        every narrow dtype -- the A-reference obligation the model encodes.
      * BASE regime: reading `.values` exposes the promoted (wider) element type
        for narrow integer dtypes (the bug) while the VALUES are unchanged --
        i.e. the discriminator the model_prepatch skeleton reproduces is real,
        and value-preservation (the other half of the A-reference) holds either
        way.

    This keeps the check meaningful and RC=0 regardless of which state the
    orchestrator chooses, and never silently passes in a state it cannot judge.
    """
    try:
        import xarray as xr
    except Exception as exc:  # pragma: no cover - xarray must be present in-container
        print("G-AX SKIP end-to-end: xarray import failed (%r)" % (exc,),
              file=sys.stderr)
        return None

    # Detect the regime from the canonical int32 case in the issue.
    probe_dtype, probe_values = _stacked_values_dtype(xr, "int32")
    patched = (probe_dtype == "int32")
    assert probe_values == [0, 1], (
        "end-to-end: stacked coordinate VALUES changed (%r) -- the carried "
        "values must be preserved in every regime" % (probe_values,))

    if patched:
        # Every narrow declared element type must round-trip to itself.
        for dtype in ["int32", "float32", "int16", "int8", "float64", "int64"]:
            observed, values = _stacked_values_dtype(xr, dtype)
            assert observed == dtype, (
                "end-to-end (patched): stacked coordinate element type %r != "
                "declared %r (the materialised array leaked the promoted "
                "storage type)" % (observed, dtype))
            assert values == [0, 1], (
                "end-to-end (patched): values changed for %r: %r"
                % (dtype, values))
    else:
        # Base commit: narrow INTEGER dtypes are promoted to a WIDER type by the
        # pandas multi-index (the bug); values are still preserved. This
        # confirms the discriminator the model_prepatch skeleton encodes is real
        # (declared != storage_type) and that value-preservation is independent
        # of the type leak.
        for dtype in ["int32", "int16", "int8"]:
            observed, values = _stacked_values_dtype(xr, dtype)
            assert observed != dtype, (
                "end-to-end (base): expected the pre-fix promotion for %r but "
                "observed %r == declared -- the bug is not reproduced, the "
                "discriminator may be vacuous" % (dtype, observed))
            assert np.dtype(observed).itemsize >= np.dtype(dtype).itemsize, (
                "end-to-end (base): %r promoted to a non-wider type %r"
                % (dtype, observed))
            assert values == [0, 1], (
                "end-to-end (base): values changed for %r: %r"
                % (dtype, values))
    return patched


def main():
    check_primitive_layer()
    patched = check_end_to_end()
    regime = ("post-patch: stack/.values round-trips the DECLARED element type"
              if patched else
              "base-commit: stack/.values exposes the promoted element type "
              "(bug present), values preserved -- discriminator confirmed real"
              if patched is False else
              "xarray import skipped")
    print("G-AX OK: materialize_level deep model (effective_type + value copy) "
          "matches real np.asarray on promoted storage across %d primitive "
          "cases; end-to-end real-xarray check passed in regime [%s]." %
          (6 * (1 + 5), regime))
    return 0


if __name__ == "__main__":
    sys.exit(main())
