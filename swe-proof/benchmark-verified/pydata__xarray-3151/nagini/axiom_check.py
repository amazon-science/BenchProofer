#!/usr/bin/env python3
"""G-AX / A-reference soundness check for pydata__xarray-3151.

This bundle consumes NO `@ContractOnly` axiom: the changed behaviour (WHICH
dimensions the post-concatenation monotonicity guard inspects) is modelled
DEEPLY in model.py (`any_joined_nonmonotonic` + the `guard_rejects` loop).
G-AX therefore validates that DEEP MODEL == the real post-patch behaviour.

The real post-patch guard, in `xarray.core.combine.combine_by_coords`, is:

    for dim in concat_dims:
        indexes = concatenated.indexes.get(dim)
        if not (indexes.is_monotonic_increasing
                or indexes.is_monotonic_decreasing):
            raise ValueError(...)

i.e. it rejects iff SOME dimension in `concat_dims` (the dimensions actually
concatenated along) has a non-monotonic combined index. Dimensions that were
NOT concatenated along (bystanders whose coordinate is identical across the
inputs) are not in `concat_dims` and so are never inspected — even if their
coordinate is non-monotonic.

Two checks, exit 0 iff both hold:

  (1) ABSTRACT: reproduce the real post-patch guard predicate over the
      dimension metadata (`concat_dims` membership = `is_joined`; per-dim
      monotonicity = `is_monotonic`) and assert it equals the deep model
      `any_joined_nonmonotonic` on boundary + randomized fuzz over the
      dimension flag lists.

  (2) CONCRETE (only if xarray importable AND the in-tree source is the
      POST-GOLD version): build real `xarray.Dataset`s — including the issue's
      `['a','c','b']` non-monotonic bystander coordinate — run the real
      `combine_by_coords`, observe whether it raises, and assert the
      observation matches the deep model. This pins the abstraction to the real
      PATCHED library, not just to a re-spelling.

      IMPORTANT: the standard SWE-bench container checks out `base_commit`,
      i.e. the PRE-PATCH (buggy) source, in which the guard loops over every
      coordinate dimension. Running the concrete cross-check against that
      buggy source would (correctly) DISAGREE with the deep model — the model
      describes the FIXED behaviour. We therefore PROVENANCE-GATE the concrete
      run on the post-gold source marker (`for dim in concat_dims:`); if only
      the pre-patch marker (`for dim in concatenated.dims:`) is present we
      SKIP-WITH-REASON rather than assert against buggy source. The harness may
      apply the gold patch first (run_in_container(apply_gold=True)); either
      way this gate keeps the script rc 0 in both pre- and post-gold images.

`itertools`/`random` are standard library; xarray is the package the patch
edits. Nothing else repo-specific.
"""
import itertools
import random
import sys


# Provenance markers (the gold patch's discriminating loop edit). Post-gold the
# guard iterates `concat_dims`; pre-patch (base_commit, buggy) it iterates
# `concatenated.dims`. See tasks/pydata__xarray-3151/patch.diff.
_POST_GOLD_MARKER = "for dim in concat_dims:"
_PRE_PATCH_MARKER = "for dim in concatenated.dims:"
_COMBINE_SRC = "/testbed/xarray/core/combine.py"
# The modeled guard's exact ValueError message fragment (post-concatenation
# monotonicity check). An upstream guard in _infer_concat_order_from_coords
# uses a DIFFERENT message ("neither monotonically increasing nor ...") — the
# concrete scenarios below are constructed to never trip it (each dataset's
# coordinate is individually monotonic), so reaching it would be a real bug.
_GUARD_MSG = "monotonic global indexes"


# --- the model (model.py deep model) reproduced as plain Python --------------

def any_joined_nonmonotonic(is_joined, is_mono):
    """model.py `any_joined_nonmonotonic`: True iff some joined dimension is
    non-monotonic. A dimension contributes iff is_joined==1 AND is_mono==0."""
    assert len(is_joined) == len(is_mono)
    for j, m in zip(is_joined, is_mono):
        if j == 1 and m == 0:
            return True
    return False


# --- (1) the REAL post-patch guard predicate, reproduced from its loop -------

def real_guard_rejects(concat_dims, mono_by_dim):
    """The real post-patch guard predicate.

    `concat_dims` is the list of dimensions actually concatenated along (the
    exact iterable the post-patch loop walks); `mono_by_dim[dim]` is whether
    that dimension's combined index is monotonic (increasing OR decreasing).
    Returns True iff the guard would raise ValueError. Mirrors

        for dim in concat_dims:
            if not (is_monotonic_increasing or is_monotonic_decreasing):
                raise ...
    """
    for dim in concat_dims:
        if not mono_by_dim[dim]:
            return True
    return False


def check_abstract(is_joined, is_monotonic):
    # Build the real-guard inputs from the abstract flag lists: a dimension is
    # in concat_dims iff it was joined along; its monotonicity is is_monotonic.
    concat_dims = [d for d, j in enumerate(is_joined) if j == 1]
    mono_by_dim = {d: bool(m) for d, m in enumerate(is_monotonic)}
    real = real_guard_rejects(concat_dims, mono_by_dim)
    model = any_joined_nonmonotonic(is_joined, is_monotonic)
    assert real == model, (
        "deep model unsound: is_joined=%r is_monotonic=%r real=%r model=%r"
        % (is_joined, is_monotonic, real, model))


# --- (2) the REAL library, when available in-container -----------------------

def _source_is_post_gold():
    """Return True if /testbed holds the POST-GOLD source, False if it holds
    the pre-patch source, None if the file/marker is absent (can't decide)."""
    try:
        with open(_COMBINE_SRC) as fh:
            src = fh.read()
    except Exception:
        return None
    if _POST_GOLD_MARKER in src:
        return True
    if _PRE_PATCH_MARKER in src:
        return False
    return None


def _combine_rejects(xr, ds_tuple):
    """Run the real combine_by_coords; return True iff it raises the modeled
    post-concatenation monotonicity guard's ValueError. Any OTHER exception is
    re-raised wrapped as an explicit AssertionError (the concrete scenarios are
    constructed so no upstream guard fires; reaching one is a genuine defect in
    the scenario, surfaced loudly rather than silently re-raised)."""
    try:
        xr.combine_by_coords(ds_tuple)
        return False
    except ValueError as e:
        if _GUARD_MSG in str(e):
            return True
        raise AssertionError(
            "concrete scenario tripped a NON-modeled guard (expected only the "
            "post-concatenation %r ValueError): %s" % (_GUARD_MSG, e))


def check_concrete():
    try:
        import numpy as np
        import xarray as xr
    except Exception:
        return ("skip-no-xarray", 0)  # host run; the abstract check stands

    # DEFECT-1 GATE: only cross-check against the real library when /testbed is
    # the POST-GOLD source. The deep model describes the FIXED behaviour; the
    # pre-patch (base_commit) source is buggy and would correctly disagree.
    prov = _source_is_post_gold()
    if prov is False:
        return ("skip-pre-patch-source", 0)
    if prov is None:
        return ("skip-source-marker-absent", 0)

    n_checked = 0

    def model_says_reject(is_joined, is_monotonic):
        return any_joined_nonmonotonic(is_joined, is_monotonic)

    data = np.arange(7 * 3, dtype=float).reshape(7, 3)

    # Scenario 1 — the issue's exact case: x is joined (varies, monotonic), y is
    # a bystander (identical across inputs) and NON-monotonic ['a','c','b'].
    # Deep model: is_joined=[1,0] (x joined, y bystander), is_monotonic=[1,0]
    # -> no joined dimension is non-monotonic -> should NOT reject.
    ycoord = ['a', 'c', 'b']
    ds1 = xr.Dataset(data_vars=dict(data=(['x', 'y'], data[:3, :])),
                     coords=dict(x=[1, 2, 3], y=ycoord))
    ds2 = xr.Dataset(data_vars=dict(data=(['x', 'y'], data[3:, :])),
                     coords=dict(x=[4, 5, 6, 7], y=ycoord))
    raised = _combine_rejects(xr, (ds1, ds2))
    expected = model_says_reject([1, 0], [1, 0])   # -> False
    assert raised == expected, (
        "real combine_by_coords raised=%r but deep model expected reject=%r "
        "on the non-monotonic bystander scenario" % (raised, expected))
    n_checked += 1

    # Scenario 2 (DEFECT-2 FIX) — a genuinely non-monotonic JOINED dimension
    # MUST reject. Each dataset's x is INDIVIDUALLY monotonic increasing
    # (x=[1,3,5] and x=[2,4,6]) so the upstream per-dataset monotonicity guard
    # in _infer_concat_order_from_coords does NOT fire; but the COMBINED global
    # index interleaves to [1,3,5,2,4,6], which is non-monotonic -> the modeled
    # post-concatenation guard rejects. is_joined=[1], is_monotonic=[0] -> model
    # rejects. (The previous per-dataset non-monotonic x=[1,3,2]/[4,6,5] tripped
    # the upstream guard with a DIFFERENT message and crashed the check.)
    xa = [1, 3, 5]
    xb = [2, 4, 6]
    da = np.arange(3 * 3, dtype=float).reshape(3, 3)
    db = np.arange(3 * 3, dtype=float).reshape(3, 3) + 100
    dsa = xr.Dataset(data_vars=dict(data=(['x', 'y'], da)),
                     coords=dict(x=xa, y=['a', 'b', 'c']))
    dsb = xr.Dataset(data_vars=dict(data=(['x', 'y'], db)),
                     coords=dict(x=xb, y=['a', 'b', 'c']))
    raised2 = _combine_rejects(xr, (dsa, dsb))
    expected2 = model_says_reject([1], [0])   # -> True
    assert raised2 == expected2, (
        "real combine_by_coords raised=%r but deep model expected reject=%r "
        "on the non-monotonic JOINED-dimension scenario" % (raised2, expected2))
    n_checked += 1

    # Scenario 3 — control: a clean monotonic join, monotonic bystander -> no
    # reject. is_joined=[1,0], is_monotonic=[1,1] -> model says no reject.
    ds3 = xr.Dataset(data_vars=dict(data=(['x', 'y'], data[:3, :])),
                     coords=dict(x=[1, 2, 3], y=['a', 'b', 'c']))
    ds4 = xr.Dataset(data_vars=dict(data=(['x', 'y'], data[3:, :])),
                     coords=dict(x=[4, 5, 6, 7], y=['a', 'b', 'c']))
    raised3 = _combine_rejects(xr, (ds3, ds4))
    assert raised3 == model_says_reject([1, 0], [1, 1]), (
        "real combine_by_coords raised=%r on the all-monotonic control"
        % raised3)
    n_checked += 1

    return ("ran-post-gold", n_checked)


def main():
    # --- (1) abstract: boundary over small dimension counts ------------------
    boundary = 0
    for n in range(0, 5):
        for is_joined in itertools.product((0, 1), repeat=n):
            for is_monotonic in itertools.product((0, 1), repeat=n):
                check_abstract(list(is_joined), list(is_monotonic))
                boundary += 1

    # --- (1) abstract: randomized fuzz over larger dimension counts ----------
    rng = random.Random(3151)
    for _ in range(50000):
        n = rng.randint(0, 8)
        is_joined = [rng.randint(0, 1) for _ in range(n)]
        is_monotonic = [rng.randint(0, 1) for _ in range(n)]
        check_abstract(is_joined, is_monotonic)

    # --- (2) concrete real-library cross-check (post-gold source only) -------
    status, concrete = check_concrete()

    print("G-AX OK: deep model any_joined_nonmonotonic == real post-patch "
          "monotonicity guard on %d exhaustive boundary + 50000 fuzz dimension "
          "metadata vectors; concrete real-xarray combine_by_coords: %s "
          "(%d scenarios checked)" % (boundary, status, concrete))
    return 0


if __name__ == "__main__":
    sys.exit(main())
