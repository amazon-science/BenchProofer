#!/usr/bin/env python3
"""G-AX executable soundness check for pydata__xarray-7393.

Runs the REAL repo objects the modeled dispatch consults — the per-level
`PandasMultiIndexingAdapter` produced when a coordinate is stacked into a
composite (multi-) index — in-container, on boundary and fuzzed dtypes, and
asserts the facts the model relies on. All modeled callees are UNCHANGED by the
patch; they are modeled `opaque` with NO asserted `ensures`, so there is NO
consumed axiom to validate point-wise (directive 7). What G-AX establishes are
the **A-reference** facts that make the modeled control flow faithful and the
retag non-vacuous (mapping.md §3, refinement.md §B):

  1. RECORDED DTYPE FAITHFUL: the level view's recorded `self.dtype`
     (`recordedDtype`) equals the dtype the coordinate was created with.
  2. RETAG LOAD-BEARING: the stored level values
     `self.array.get_level_values(self.level).values` (`componentValues`) carry
     the storage's NATIVE (promoted) dtype, which DIFFERS from the recorded
     dtype for the sub-64-bit cases (int32/float32/int16/uint8/float16) — so the
     `np.asarray(..., dtype=self.dtype)` retag the patch adds genuinely changes
     the observable dtype. (This is the bug: without the retag the dtype escapes
     as the promoted int64/float64.)
  3. toDtype FAITHFUL: `np.asarray(values, dtype=self.dtype)` (`toDtype`) yields
     an array whose `.dtype == self.dtype` AND whose element content is
     preserved (for the integer/float values at play).
  4. BASE PATH ALREADY CORRECT: the inherited `super().__array__` path
     (`baseMaterialize`) already returns the recorded dtype (so the change is
     confined to the level branch; the else leg is unchanged & sound).

stdlib + the numpy / pandas / xarray under test only (no gold patch needed — the
modeled objects are the UNCHANGED base-commit objects). Exit 0 iff every
obligation holds.
"""
import random
import sys

import numpy as np
import pandas as pd
import xarray as xr
from xarray.core.indexing import (
    PandasIndexingAdapter,
    PandasMultiIndexingAdapter,
)


def level_adapter(dtype):
    """Build the issue's scenario and reach the per-level multi-index adapter.

    Mirrors the MVCE: a 1-D coordinate of the given dtype, stacked into a
    composite index; the resulting view for the original coordinate is a
    `PandasMultiIndexingAdapter` whose `.level` is that coordinate name.
    """
    foo = xr.Dataset(coords={"bar": ("bar", np.array([0, 1, 2, 3], dtype=dtype))})
    foo = foo.stack(baz=("bar",))
    var = foo["bar"].variable
    data = var._data
    # unwrap any lazy/explicitly-indexed wrappers down to the adapter
    seen = 0
    while not isinstance(data, PandasMultiIndexingAdapter) and seen < 8:
        inner = getattr(data, "array", None)
        if inner is None or inner is data:
            break
        data = inner
        seen += 1
    assert isinstance(data, PandasMultiIndexingAdapter), (
        "expected a PandasMultiIndexingAdapter level view for dtype %r, got %r"
        % (dtype, type(data).__name__))
    assert data.level is not None, "the level view must expose a single level"
    return data


def native_level_values(adapter):
    """componentValues: the stored level values with their NATIVE dtype (the
    pre-patch level branch returned exactly this)."""
    return adapter.array.get_level_values(adapter.level).values


def check_one(dtype, expect_promoted):
    adapter = level_adapter(dtype)

    # fact 1: recorded dtype faithful (recordedDtype == requested dtype)
    assert str(adapter.dtype) == dtype, (
        "recorded dtype %r != requested %r" % (str(adapter.dtype), dtype))

    # fact 2: retag load-bearing (native dtype vs recorded dtype)
    native = native_level_values(adapter)
    native_dtype = str(native.dtype)
    if expect_promoted:
        assert native_dtype != dtype, (
            "expected the stored level values to be PROMOTED away from %r "
            "(making the retag load-bearing), but they were already %r"
            % (dtype, native_dtype))
    # the pre-patch level branch would have escaped with `native_dtype`

    # fact 3: toDtype faithful (np.asarray(..., dtype=recorded) has recorded
    #         dtype and preserves content)
    retagged = np.asarray(native, dtype=adapter.dtype)
    assert str(retagged.dtype) == dtype, (
        "toDtype gave dtype %r, expected %r" % (str(retagged.dtype), dtype))
    assert np.array_equal(retagged.astype("int64"), native.astype("int64")), (
        "toDtype changed the integer content for dtype %r" % dtype)

    # fact 4: the inherited (non-level) base path already returns the view's
    # RECORDED dtype (so the change is confined to the level branch; the else
    # leg is unchanged & sound). Reach a NON-level adapter (a plain pandas index
    # coordinate) and confirm super().__array__ (dtype=None) materializes at the
    # adapter's *recorded* dtype `self.dtype` -- NOT necessarily the dtype the
    # numpy array was constructed with: `pd.Index` itself promotes sub-64-bit
    # integer/float dtypes (int32->int64, uint8->uint64, float16->float64) at
    # construction, so for a plain pandas index the recorded dtype is the
    # promoted one. The A-reference fact is `base.dtype == recorded`, the
    # identity that makes the base path's default-resolution faithful; comparing
    # to the pre-promotion construction dtype would be testing pandas' index
    # promotion, not the materialization path the model relies on.
    plain = PandasIndexingAdapter(pd.Index(np.array([0, 1, 2], dtype=dtype)))
    base = plain.__array__()  # super().__array__ with dtype=None
    assert str(base.dtype) == str(plain.dtype), (
        "base (non-level) materialization gave dtype %r, expected the recorded "
        "dtype %r" % (str(base.dtype), str(plain.dtype)))

    return native_dtype


def main():
    # boundary dtypes: the issue's int32/float32 plus other sub-64-bit dtypes
    # that pandas promotes (retag load-bearing), and the 64-bit controls where
    # native == recorded (retag is a no-op but still correct).
    promoted = ["int32", "float32", "int16", "uint8", "float16", "int8", "uint16"]
    controls = ["int64", "float64"]

    observed = {}
    for dt in promoted:
        observed[dt] = check_one(dt, expect_promoted=True)
    for dt in controls:
        observed[dt] = check_one(dt, expect_promoted=False)

    # the issue's exact assertion: the F2P test compares str(values.dtype) == dtype
    for dt in ["int32", "float32"]:
        foo = xr.Dataset(coords={"bar": ("bar", np.array([0, 1], dtype=dt))})
        foo = foo.stack(baz=("bar",))
        # the patched __array__ is what .values triggers; G-AX only needs the
        # A-reference facts, but we assert the load-bearing native divergence:
        adapter = level_adapter(dt)
        assert str(native_level_values(adapter).dtype) != dt, (
            "the F2P dtype %r must be promoted natively for the bug to bite" % dt)

    # randomized fuzz: vary length and value range across the promoted dtypes
    rng = random.Random(7393)
    n_checks = 0
    for _ in range(400):
        dt = rng.choice(promoted + controls)
        n = rng.randint(1, 6)
        info = np.iinfo(dt) if np.issubdtype(np.dtype(dt), np.integer) else None
        if info is not None:
            vals = [rng.randint(int(info.min), int(info.max)) for _ in range(n)]
        else:
            vals = [rng.uniform(-10, 10) for _ in range(n)]
        foo = xr.Dataset(coords={"bar": ("bar", np.array(vals, dtype=dt))})
        foo = foo.stack(baz=("bar",))
        var = foo["bar"].variable
        data = var._data
        seen = 0
        while not isinstance(data, PandasMultiIndexingAdapter) and seen < 8:
            inner = getattr(data, "array", None)
            if inner is None or inner is data:
                break
            data = inner
            seen += 1
        assert isinstance(data, PandasMultiIndexingAdapter)
        assert str(data.dtype) == dt
        retagged = np.asarray(
            data.array.get_level_values(data.level).values, dtype=data.dtype)
        assert str(retagged.dtype) == dt
        n_checks += 1

    print("G-AX OK: per-level multi-index adapter recorded dtype faithful; "
          "stored level values natively PROMOTED away from the recorded dtype "
          "on %d sub-64-bit dtypes (retag load-bearing: %s); np.asarray retag "
          "yields the recorded dtype with content preserved; inherited base "
          "path already returns the recorded dtype; %d fuzz checks. A-reference "
          "facts sound; no consumed axiom."
          % (len(promoted), {k: observed[k] for k in promoted}, n_checks))
    return 0


if __name__ == "__main__":
    sys.exit(main())
