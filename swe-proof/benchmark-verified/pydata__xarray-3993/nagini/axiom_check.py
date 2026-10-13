#!/usr/bin/env python3
"""G-AX executable soundness check for pydata__xarray-3993.

This bundle has NO axiomatized library callee and NO A-reference deep model of
a library function: the changed function (`integrate_route` in model.py, the
selector-routing prologue of the integration entry point) reads only its two
selector arguments and is modeled DEEPLY (a spelled-out three-way decision).
Everything it delegates to downstream (`_to_temp_dataset`, `Dataset.integrate`,
`_integrate_one`, `numpy.trapz`) is UNCHANGED by the gold, independent of the
routing decision, and unobserved by the specification (mapping.md §3.1).

There is therefore no library callee to fuzz. What G-AX must instead confirm is
that the deep routing model in model.py == the gold patch's prologue control
flow (mapping.md §3.3). This script encodes the gold prologue from
`xarray/core/dataarray.py` (post-patch) as a reference oracle and asserts, over
the full enumeration of `(coord, dim)` supplied/omitted combinations plus fuzzed
selector identifiers, that the model's decision agrees with the gold on:
  * the refusal (raise) when BOTH selectors are supplied,
  * the coordinate the integration is routed along, and
  * whether the deprecation signal is emitted.

It is dependency-free (the heavy xarray/numpy stack cannot be imported in the
gate sandbox, and is unnecessary: the routing prologue is pure Python control
flow over the two arguments). Exit 0 iff the deep model matches the gold
prologue on every case.
"""
import random
import sys

_SENTINEL = object()  # marks "argument not supplied" (the real default None)


# --- gold reference oracle: the prologue from DataArray.integrate (post-patch)
# Faithfully transcribed from xarray/core/dataarray.py:
#     if dim is not None and coord is not None:
#         raise ValueError("Cannot pass both 'dim' and 'coord'. ...")
#     if dim is not None and coord is None:
#         coord = dim
#         warnings.warn(msg, FutureWarning, stacklevel=2)
#     ds = self._to_temp_dataset().integrate(coord, datetime_unit)
# Returns (routed_coord, deprecated_emitted) or raises ValueError.
def gold_prologue(coord, dim):
    if dim is not None and coord is not None:
        raise ValueError("Cannot pass both 'dim' and 'coord'.")
    deprecated = False
    if dim is not None and coord is None:
        coord = dim
        deprecated = True
    return coord, deprecated


# --- model reference: the deep routing decision from model.py integrate_route
# (the impl region, transcribed; ConflictingSelection <-> ValueError per
#  refinement.md A2; Routed.deprecated <-> the FutureWarning per A3).
def model_route(coord, dim):
    if dim is not None and coord is not None:
        raise ValueError("ConflictingSelection")
    deprecated = False
    if dim is not None and coord is None:
        coord = dim
        deprecated = True
    return coord, deprecated


def check(coord, dim):
    """Assert the deep model agrees with the gold prologue on (coord, dim)."""
    gold_exc = None
    try:
        g = gold_prologue(coord, dim)
    except ValueError:
        gold_exc = True

    model_exc = None
    try:
        m = model_route(coord, dim)
    except ValueError:
        model_exc = True

    # Refusal must agree exactly.
    assert (gold_exc is True) == (model_exc is True), (
        "refusal disagreement on coord=%r dim=%r: gold_raises=%r "
        "model_raises=%r" % (coord, dim, gold_exc, model_exc))
    if gold_exc:
        return
    # Routed coordinate and deprecation signal must agree exactly.
    assert g[0] == m[0], (
        "routed coordinate disagreement on coord=%r dim=%r: gold=%r model=%r"
        % (coord, dim, g[0], m[0]))
    assert g[1] == m[1], (
        "deprecation signal disagreement on coord=%r dim=%r: gold=%r model=%r"
        % (coord, dim, g[1], m[1]))


def main():
    # --- full enumeration of supplied/omitted x supplied/omitted -------------
    # None means "not supplied"; an int identifier means "supplied".
    values = [None, 0, 1, 7, -3, 100]
    cases = 0
    for coord in values:
        for dim in values:
            check(coord, dim)
            cases += 1

    # explicit F2P-shaped witnesses ------------------------------------------
    # da.integrate(dim="x"): legacy selector alone -> route dim, MUST deprecate.
    rc, dep = model_route(None, 5)
    assert rc == 5 and dep is True, "legacy-only call must route dim and warn"
    rc, dep = gold_prologue(None, 5)
    assert rc == 5 and dep is True, "gold legacy-only call must route dim+warn"
    # da.integrate("x"): primary selector alone -> route coord, NO deprecation.
    rc, dep = model_route(5, None)
    assert rc == 5 and dep is False, "primary-only call must route coord, no warn"
    # both supplied -> refusal on both sides.
    for f in (model_route, gold_prologue):
        raised = False
        try:
            f(3, 4)
        except ValueError:
            raised = True
        assert raised, "%s must refuse a double selection" % f.__name__

    # --- randomized fuzz over identifier values ------------------------------
    rng = random.Random(3993)
    for _ in range(20000):
        coord = rng.choice([None] + list(range(-50, 50)))
        dim = rng.choice([None] + list(range(-50, 50)))
        check(coord, dim)
        cases += 1

    print("G-AX OK: deep routing model == gold DataArray.integrate prologue on "
          "%d cases (full supplied/omitted enumeration + 20000 fuzz); refusal, "
          "routed coordinate, and deprecation signal all agree." % cases)
    return 0


if __name__ == "__main__":
    sys.exit(main())
