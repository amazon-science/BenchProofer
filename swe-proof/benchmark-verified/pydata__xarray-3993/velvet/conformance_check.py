#!/usr/bin/env python3
"""G-CONF differential conformance check for pydata__xarray-3993 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outcomes:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region (`resolve`)
              transliterated to Python over the real repo types, via the
              mapping.md bijection (a selector argument ↔ `None` / a coordinate
              name). The whole impl region is R/I: there is NO A-tagged callee in
              it (the downstream integrator is reached only THROUGH the forwarded
              selector and is observed via that selector — see refinement.md §C),
              so `conf_skip=false` and the entire dispatch is transliterated.
              The shadow then forwards its chosen selector to the SAME real
              integrator the oracle uses, so the two sides differ ONLY in the
              dispatch decision under test (which selector is forwarded, whether
              the advisory fires, whether a both-supplied call is rejected).
  * ORACLE  — `patch.diff`'s behaviour: the patched `DataArray.integrate`
              applied at base_commit (the real correctness oracle, G-RESOLVE),
              projected onto exactly what the F2P test observes.

The observable projection is (kind, forwarded_signature, advisory_raised):
  * kind='err'  — a ValueError was raised (a both-supplied call is rejected
                  before forwarding; a no-selector call forwards None and the
                  unchanged integrator rejects it). advisory/signature = None.
  * kind='ok'   — the integration ran; `forwarded_signature` is the rounded
                  result values (which DISTINGUISH the forwarded coordinate, as
                  different coordinates give different trapezoidal results) and
                  `advisory_raised` is whether a FutureWarning was emitted.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image) with the gold patch
applied; stdlib + numpy + xarray only. The fuzz seed is pinned (mapping.md §4).
"""
import random
import sys
import warnings

import numpy as np
import xarray as xr


SEED = 3993
N_FUZZ = 100_000
# A small pool of real one-dimensional coordinate names present on the probe
# DataArray. The dispatch never inspects a name's internals, so a handful of
# distinct, integration-valid coordinates fully exercises the forwarding leg.
_COORDS = ["x", "x2", "x3"]
_MISSING = object()


def _make_da():
    """A DataArray with three distinct 1-D coordinates along dim `x`, each valid
    for trapezoidal integration. Built once; the dispatch under test is
    independent of the data, so a fixed probe array suffices. The two non-index
    coordinates (`x2`, `x3`) are declared along `x` via the `(dim, values)` form
    so they are 1-D coordinates of `x` (not new dimensions); each spans a
    different range, so integrating along each yields a DIFFERENT result and the
    forwarded-coordinate choice is observable in the signature."""
    n = 6
    rs = np.random.RandomState(0)
    return xr.DataArray(
        rs.randn(n),
        dims=["x"],
        coords={
            "x": np.linspace(0.0, 1.0, n),
            "x2": ("x", np.linspace(0.0, 2.0, n)),
            "x3": ("x", np.linspace(0.0, 3.0, n)),
        },
    )


def _signature(res):
    return tuple(np.round(np.atleast_1d(res.values).ravel(), 9).tolist())


def _observe_real(da, coord_arg, dim_arg):
    """ORACLE: call the patched DataArray.integrate and project the outcome."""
    kwargs = {}
    if coord_arg is not _MISSING:
        kwargs["coord"] = coord_arg
    if dim_arg is not _MISSING:
        kwargs["dim"] = dim_arg
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            res = da.integrate(**kwargs)
        except ValueError:
            return ("err", None, None)
        advisory = any(issubclass(w.category, FutureWarning) for w in caught)
    return ("ok", _signature(res), advisory)


def _shadow(da, coord_arg, dim_arg):
    """SHADOW: `resolve` transliterated, then forward to the real integrator.
    Reject a both-supplied call; otherwise forward whichever selector carries a
    value, raising the advisory iff the value came from the legacy (`dim`)
    selector; forward None when neither is supplied (the integrator then rejects
    it). The forwarded value is handed to the SAME real integrator the oracle
    uses, so the shadow asserts only the DISPATCH decision."""
    has_primary = coord_arg is not _MISSING and coord_arg is not None
    has_legacy = dim_arg is not _MISSING and dim_arg is not None
    if has_primary and has_legacy:
        return ("err", None, None)
    if has_primary:
        forwarded, advisory = coord_arg, False
    elif has_legacy:
        forwarded, advisory = dim_arg, True
    else:
        forwarded, advisory = None, False
    try:
        res = da.integrate(forwarded)  # forward to the (unchanged) integrator
    except ValueError:
        return ("err", None, None)
    return ("ok", _signature(res), advisory)


def fuzz_inputs(n, rng):
    # boundary cases first: the F2P scenario + the explicit selector forms.
    yield (_MISSING, "x")          # legacy-only: da.integrate(dim="x") -> advisory
    yield ("x", _MISSING)          # primary-only: no advisory
    yield ("x2", _MISSING)
    yield ("x", "x")               # both supplied -> ValueError
    yield ("x", "x2")              # both supplied (different) -> ValueError
    yield (None, "x3")             # primary explicitly None, legacy supplied
    yield ("x3", None)             # legacy explicitly None, primary supplied
    yield (_MISSING, _MISSING)     # neither supplied -> integrator rejects None

    def pick():
        r = rng.random()
        if r < 0.34:
            return _MISSING
        if r < 0.5:
            return None
        return rng.choice(_COORDS)

    for _ in range(n):
        yield (pick(), pick())


def main():
    rng = random.Random(SEED)
    da = _make_da()
    disagreements = []
    count = 0
    for coord_arg, dim_arg in fuzz_inputs(N_FUZZ, rng):
        count += 1
        s = _shadow(da, coord_arg, dim_arg)
        o = _observe_real(da, coord_arg, dim_arg)
        if s != o:
            disagreements.append((coord_arg, dim_arg, s, o))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for ca, dh, s, o in disagreements:
            print("  coord=%r dim=%r shadow=%r oracle=%r" % (ca, dh, s, o))
        return 1
    print("G-CONF OK: R/I shadow of integrateDispatch agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
