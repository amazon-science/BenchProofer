#!/usr/bin/env python3
"""G-CONF differential conformance for pydata__xarray-6461.

Refutes the R/I refinement leg (A4: `return xAttrs` ↔
`keep_attrs = lambda attrs, context: getattr(x, "attrs", {})`).

SHADOW = the transliterated impl over the real types: the preserved attribute
mapping is the SECOND positional argument's OWN mapping (`getattr(x, "attrs",
{})`), regardless of where (or whether) it sits in the present-mappings list.
ORACLE = the patched `xr.where(cond, x, y, keep_attrs=True).attrs` applied to the
same configuration. They must agree on every input. Exit 0 iff zero
disagreements. Runs in-container with the gold patch applied; imports xarray.

The fuzzed configurations range the second positional argument `x` over both a
DataArray-with-attrs (it appears in the present list, at a position that varies
with how many leading arguments are DataArrays) and a bare scalar (it is absent
from the list, the reported bug). The shadow models the kept mapping as `x`'s
own attrs; the oracle is what `where` actually keeps.
"""
import random
import sys

SEED = 6461
N_FUZZ = 100_000


def shadow_keep(x_attrs):
    """attrsToKeep transliterated: the preserved mapping is the second
    argument's OWN attribute mapping (the empty mapping {} for a scalar)."""
    return x_attrs


def main():
    import numpy as np
    import xarray as xr

    rng = random.Random(SEED)
    disagreements = []
    count = 0

    # Boundary configs + fuzz. Each config picks attrs for cond/x/y and whether
    # x (and y) are scalars or DataArrays. `cond` is always a DataArray.
    configs = []
    # the two F2P-shaped boundary configs:
    configs.append(("all_da", {"attr": "cond"}, {"attr": "x"}, {"attr": "y"}, False, False))
    configs.append(("scalar_x", {"attr": "cond"}, None, None, True, True))
    # fuzz
    keys = ["a", "b", "c", "x", "y", "cond", "z"]
    for _ in range(N_FUZZ):
        cond_attrs = {rng.choice(keys): rng.choice(keys)} if rng.random() < 0.8 else {}
        x_is_scalar = rng.random() < 0.5
        y_is_scalar = rng.random() < 0.5
        x_attrs = None if x_is_scalar else (
            {rng.choice(keys): rng.choice(keys)} if rng.random() < 0.8 else {})
        y_attrs = None if y_is_scalar else (
            {rng.choice(keys): rng.choice(keys)} if rng.random() < 0.8 else {})
        configs.append(("fuzz", cond_attrs, x_attrs, y_attrs, x_is_scalar, y_is_scalar))

    n = 3
    for tag, cond_attrs, x_attrs, y_attrs, x_scalar, y_scalar in configs:
        count += 1
        cond = xr.DataArray(np.array([True, False, True]), dims="d", attrs=cond_attrs)
        if x_scalar:
            x = 1
            x_own = {}                      # getattr(1, "attrs", {})
        else:
            x = xr.DataArray(np.ones(n), dims="d", attrs=x_attrs)
            x_own = dict(x_attrs)           # x's own mapping
        if y_scalar:
            y = 0
        else:
            y = xr.DataArray(np.zeros(n), dims="d", attrs=y_attrs)

        try:
            actual = xr.where(cond, x, y, keep_attrs=True)
            oracle = dict(actual.attrs)     # the mapping `where` actually kept
        except Exception as e:              # noqa: BLE001
            disagreements.append((tag, "oracle-raised", repr(e)))
            if len(disagreements) >= 5:
                break
            continue

        shadow = shadow_keep(x_own)         # attrsToKeep R/I shadow: x's own attrs
        if oracle != shadow:
            disagreements.append((tag, shadow, oracle))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s): %r" % (len(disagreements), disagreements))
        return 1
    print("G-CONF OK: R/I shadow of attrsToKeep (keep x's own attrs) agrees with "
          "patched xr.where(...).attrs on %d configs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
