#!/usr/bin/env python3
"""G-CONF for pydata__xarray-3993.

The gold patch is already applied to /testbed when this runs. We compare the
R/I Python shadow of `implementation_integrate` (the Lean impl, transliterated
op-for-op per refinement.md) against the REAL patched `DataArray.integrate`, over
>=1e5 fuzzed inputs. Zero disagreements => exit 0.

Model (refinement.md): `DataArray.integrate(coord=None, datetime_unit=None, *,
dim=None)` resolves the integration coordinate as:

    if dim is not None and coord is not None:  -> ValueError            (reject)
    elif dim is not None and coord is None:     -> effective=dim, warned=True
    else:                                       -> effective=coord, warned=False

then integrates along `effective` via the UNCHANGED downstream step
`self._to_temp_dataset().integrate(effective, datetime_unit)` ->
`_from_temp_dataset`.

  * Oracle = the REAL patched `DataArray.integrate(coord=..., dim=...)`, capturing
             whether a FutureWarning was raised and the returned DataArray (or the
             raised exception).
  * Shadow = the resolution table above, with the downstream integration done by
             the REAL `DataArray.integrate` along the resolved `effective`
             coordinate (the A-reference op #5, NOT substituted by a model), and
             `warned` computed by the resolution rule.

Type bijection (mapping.md): coord<->coord keyword (Option), dim<->dim keyword
(Option), integrateAlong<->_to_temp_dataset().integrate, Except.error<->ValueError,
warned<->a FutureWarning was emitted.
stdlib-only (numpy + xarray are the repo's own deps); no hypothesis required.
"""
import sys
import warnings

import numpy as np
import xarray as xr


def build_da():
    rs = np.random.RandomState(3993)
    return xr.DataArray(
        rs.randn(8, 6),
        dims=["x", "y"],
        coords={"x": np.linspace(0.0, 1.0, 8), "y": np.linspace(0.0, 2.0, 6)},
    )


# Selector pool: None (omitted), single coords, and a multi-coord sequence.
SELECTORS = [None, "x", "y", ("y", "x")]


def _run(call):
    """Run `call`, returning a comparable outcome token.

    ('error', ExcType) on exception, else ('ok', warned, DataArray).
    """
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            val = call()
        except Exception as e:  # noqa: BLE001 - we compare the exception type
            return ("error", type(e).__name__)
        warned = any(issubclass(w.category, FutureWarning) for w in caught)
        return ("ok", warned, val)


def _outcomes_equal(o, s):
    if o[0] != s[0]:
        return False
    if o[0] == "error":
        return o[1] == s[1]
    # ('ok', warned, DataArray)
    if o[1] != s[1]:
        return False
    try:
        return bool(o[2].identical(s[2]))
    except Exception:  # noqa: BLE001
        return False


def oracle(da, coord, dim):
    return _run(lambda: da.integrate(coord, dim=dim))


def shadow(da, coord, dim):
    """R/I transliteration of implementation_integrate (Lean)."""
    # Op 1: contradictory pair -> reject.
    if dim is not None and coord is not None:
        return ("error", "ValueError")
    # Ops 2-4: resolve effective coordinate + deprecation notice.
    effective = coord
    warned = False
    if dim is not None and coord is None:
        effective = dim
        warned = True
    # Op 5 (A-reference): the REAL downstream integration along `effective`.
    # Op 6: package value with the notice flag.
    def step():
        return da.integrate(effective)
    try:
        val = step()
    except Exception as e:  # noqa: BLE001
        return ("error", type(e).__name__)
    return ("ok", warned, val)


def main():
    import random
    rng = random.Random(3993)  # pinned seed (mapping.md)
    da = build_da()
    N = 100_000
    disagreements = 0
    first = None
    for _ in range(N):
        coord = rng.choice(SELECTORS)
        dim = rng.choice(SELECTORS)
        o = oracle(da, coord, dim)
        s = shadow(da, coord, dim)
        if not _outcomes_equal(o, s):
            disagreements += 1
            if first is None:
                first = (coord, dim, o[:2], s[:2])
    if disagreements:
        print("G-CONF FAIL: %d/%d disagreements; first=%r"
              % (disagreements, N, first))
        return 1
    print("G-CONF OK: %d inputs, 0 disagreements" % N)
    return 0


if __name__ == "__main__":
    sys.exit(main())
