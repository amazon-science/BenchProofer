#!/usr/bin/env python3
"""G-AX executable soundness check for pydata__xarray-4356.

The bundle has NO consumed @ContractOnly axiom. The one changed quantity --
the number of input elements reduced over at an output position, which the fix
computes as the PRODUCT of the input's sizes along ALL reduced axes (the real
expression `np.take(mask.shape, axis).prod()`) rather than the size of a single
axis -- is modelled DEEPLY in model.py (the front-recursive `prod` fold applied
to the selected reduced-axes sizes). G-AX validates that deep model against the
real select-then-product callee (an A-reference):

    deep model:  prod(select(shape, axis))   == real:  np.take(shape, axis).prod()

where `select(shape, axis)` is the per-reduced-axis-list selection of the shape
tuple (exactly numpy's `np.take`), and `prod` is the product fold (numpy's
`.prod()` over that selection).

It also validates the downstream decision the model specifies -- the position
is flagged "too few present" iff `total - missing - min_count < 0`, i.e. the
present element count `total - missing` is below `min_count` -- matches the real
`null_mask = (np.take(mask.shape, axis).prod() - mask.sum(axis) - min_count) < 0`
computed by numpy directly on real arrays (the gold expression).

Imports only `numpy` -- the same library the gold patch calls. Exit 0 iff every
obligation holds.
"""
import itertools
import random
import sys

import numpy as np


# --- model.py deep-model reference encodings (kept in lock-step) -------------

def prod_model(xs):
    """Reference of model.py's `prod` fold (empty product is 1)."""
    out = 1
    for v in xs:
        out *= v
    return out


def select_model(shape, axis):
    """Reference of `np.take(shape, axis)` as a plain list: the sizes of the
    shape along the reduced axes, in order."""
    return [shape[ax] for ax in axis]


def total_model(shape, axis):
    """model.py's `total` = prod(select(shape, axis))."""
    return prod_model(select_model(shape, axis))


def flag_model(shape, axis, missing, min_count):
    """model.py's `flag_too_few` postcondition."""
    return (total_model(shape, axis) - missing - min_count) < 0


# --- the checks --------------------------------------------------------------

def check_total_reference(shape, axis):
    """Assert deep model prod(select(shape, axis)) == real np.take(..).prod()."""
    real = int(np.take(np.array(shape), axis).prod())   # the real fixed callee
    model = total_model(shape, axis)                     # the deep model
    assert real == model, (
        "deep model unsound: shape=%r axis=%r np.take.prod=%r prod(select)=%r"
        % (shape, axis, real, model))
    return real


def check_null_mask_decision(shape, axis, min_count, rng):
    """Build a real mask of the given shape, reduce over `axis`, and assert the
    real numpy null_mask expression agrees with the model's flag at EVERY output
    position."""
    arr_shape = tuple(shape)
    # random boolean mask (True == missing element), as xarray's `mask = isnull(a)`
    mask = rng.random(arr_shape) < 0.5
    axis_t = tuple(axis)
    # the gold expression, verbatim
    total = np.take(np.array(mask.shape), axis_t).prod()
    null_mask = (total - mask.sum(axis_t) - min_count) < 0
    null_mask = np.atleast_1d(null_mask)
    # model: at each output position, flag iff total - missing - min_count < 0
    missing = np.atleast_1d(mask.sum(axis_t))
    flat_null = null_mask.reshape(-1)
    flat_missing = missing.reshape(-1)
    for i in range(flat_null.size):
        m = int(flat_missing[i])
        expected = flag_model(list(shape), list(axis), m, min_count)
        assert bool(flat_null[i]) == expected, (
            "null_mask decision mismatch: shape=%r axis=%r min_count=%r "
            "missing=%r real=%r model=%r"
            % (shape, axis, min_count, m, bool(flat_null[i]), expected))


def main():
    rng = random.Random(4356)
    nprng = np.random.RandomState(4356)

    # --- A-reference: prod(select(shape, axis)) == np.take(shape, axis).prod()
    # boundary: single-axis (must coincide with old shape[axis]), multi-axis,
    # all-axes, size-1 axes, and larger products.
    boundary = [
        ((5,), [0]),
        ((2, 3), [0]),
        ((2, 3), [1]),
        ((2, 3), [0, 1]),
        ((2, 3, 4), [0, 1]),
        ((2, 3, 4), [0, 2]),
        ((2, 3, 4), [1, 2]),
        ((2, 3, 4), [0, 1, 2]),
        ((1, 1, 1), [0, 1, 2]),
        ((1, 7), [0, 1]),
        ((7, 1), [0, 1]),
        ((3, 3, 3, 3), [0, 1, 2, 3]),
        ((10, 1, 1), [0]),
    ]
    for shape, axis in boundary:
        check_total_reference(shape, axis)

    # fuzz: random shapes (sizes 1..5), random non-empty distinct axis subsets
    fuzz = 0
    for _ in range(4000):
        ndim = rng.randint(1, 4)
        shape = tuple(rng.randint(1, 5) for _ in range(ndim))
        k = rng.randint(1, ndim)
        axis = tuple(sorted(rng.sample(range(ndim), k)))
        check_total_reference(shape, list(axis))
        fuzz += 1

    # --- the downstream null_mask decision matches the gold numpy expression --
    # use real reductions over real boolean masks (with a result of ndim>=1, the
    # branch the fix lives in) for a range of multi-axis configurations.
    decision_cases = [
        ((2, 3, 4), (0,), 3),
        ((2, 3, 4), (0, 1), 3),
        ((2, 3, 4), (1, 2), 1),
        ((2, 3, 4), (0, 2), 5),
        ((3, 3, 3), (0, 1), 4),
        ((4, 5, 2), (1,), 2),
        ((2, 2, 2, 2), (0, 1), 2),
    ]
    for shape, axis, min_count in decision_cases:
        # leave at least one un-reduced axis so the result keeps ndim>=1
        if len(axis) < len(shape):
            check_null_mask_decision(shape, axis, min_count, nprng)

    print("G-AX OK: prod(select) deep model == np.take(shape, axis).prod() on "
          "%d boundary + %d fuzz cases; null_mask decision matches gold numpy "
          "expression on %d real-array configurations"
          % (len(boundary), fuzz, len(decision_cases)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
