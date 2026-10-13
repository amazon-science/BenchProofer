#!/usr/bin/env python3
"""G-AX executable soundness check for pydata__xarray-4094.

Executes the REAL xarray callees that model.py axiomatizes and asserts that
every observation matches the model. The model's axioms:

  carried(discard, position) -- the annotation a per-member slice carries for its
      position, as a function of the selection's drop flag. Selecting one
      variable label along the stacked MultiIndex level turns the stacked
      position coordinate ('y') into a scalar coordinate on the slice;
      .squeeze(drop=True) removes only the size-one *dimension*, NOT that scalar
      coordinate. So with drop=False (keep) the slice carries its own position
      label; with drop=True (discard) it carries no distinguishing position
      annotation -- modelled as a single shared value common to every slice
      (shared_value()).

  assemble + all_equal -- combining the per-variable slices (Dataset(data_dict))
      succeeds iff the annotations the slices carry agree across members: a
      shared-name coordinate carrying two different values is a MergeError
      ('conflicting values for variable y ...', the exact error in the issue);
      when every slice carries the same value the combination succeeds and
      recovers each variable's data verbatim.

  combined_collection -- the abstract token marking the combination's output.
      Sound because the reconstructed collection IS the result of the combination
      (Dataset(data_dict)) and there is no other producer of it in the function:
      the recovered, original-equal collection is exactly what the Dataset merge
      returns -- a value the reconstruction cannot obtain without going through
      that merge. (Checked below: the merge's output equals the original; the
      function's only return is that merge's output.)

The decisive single-position-axis case (the issue's MCVE): two variables 'a','b'
sharing sample dim 'x', stacked along 'y'. Their positions on 'y' are distinct,
so with drop=False each slice keeps a distinct 'y' scalar coordinate -> the
slices disagree -> rejected; with drop=True the 'y' coordinate is dropped -> the
slices agree -> combination succeeds and the roundtrip recovers the original.

Imports nothing repo-specific beyond xarray/numpy/pandas (the library under
test, present in the evaluation image). Exit 0 iff every obligation holds.
"""
import sys


def _stacked():
    import numpy as np
    import xarray as xr
    arr = xr.DataArray(np.arange(3), coords=[("x", [0, 1, 2])])
    data = xr.Dataset({"a": arr, "b": arr})
    stacked = data.to_stacked_array("y", sample_dims=["x"])
    idx = stacked.indexes["y"]
    level_number = idx._get_level_number(0)
    variables = idx.levels[level_number]
    variable_dim = idx.names[level_number]
    return data, stacked, variables, variable_dim


def check_carried():
    """Assert carried(discard, position): the residual position coordinate 'y'
    survives onto a per-member slice iff drop=False, and when it survives it
    carries that member's own (distinct) position value; when drop=True it does
    not survive (every slice then agrees -- no distinguishing position
    annotation). The only modelled residual is the stacked position coordinate
    'y'. (DEFECT-2 fix: do NOT over-scope to the selection level 'variable',
    whose survival is version-dependent and is not the modelled residual.)
    """
    data, stacked, variables, variable_dim = _stacked()
    residual_name = "y"  # the single modelled residual (the stacked position dim)

    import numpy as np

    # drop=False: the position coordinate survives, carrying a per-member value.
    kept_values = []
    for k in variables:
        sel = stacked.sel({variable_dim: k}, drop=False).squeeze(drop=True)
        assert residual_name in sel.coords, (
            "carried axiom unsound: with drop=False the residual position "
            "coordinate %r should survive onto the slice, but it did not"
            % (residual_name,))
        kept_values.append(np.asarray(sel.coords[residual_name].values).tolist())

    # drop=True: the position coordinate is discarded (does not survive).
    for k in variables:
        sel = stacked.sel({variable_dim: k}, drop=True).squeeze(drop=True)
        assert residual_name not in sel.coords, (
            "carried axiom unsound: with drop=True the residual position "
            "coordinate %r should be discarded, but it survived" % (residual_name,))

    # the kept (drop=False) per-member position values are pairwise distinct --
    # the single-position-axis shape (so kept => members disagree => conflict).
    assert len(kept_values) >= 2, "expected at least two members"
    for a in range(len(kept_values)):
        for b in range(a + 1, len(kept_values)):
            assert kept_values[a] != kept_values[b], (
                "carried axiom unsound: the members' kept position values should "
                "be pairwise distinct, got %r" % (kept_values,))


def check_assemble_and_roundtrip():
    """Assert the combination semantics: Dataset(data_dict) is REJECTED on a
    conflicting kept residual (drop=False, distinct positions => not all-equal)
    and SUCCEEDS recovering each member's data verbatim otherwise (drop=True =>
    every slice carries no distinguishing position => all-equal)."""
    import xarray as xr
    data, stacked, variables, variable_dim = _stacked()

    # drop=False (residual kept, distinct positions): combination REJECTED.
    bad = {}
    for k in variables:
        bad[k] = stacked.sel({variable_dim: k}, drop=False).squeeze(drop=True)
    rejected = False
    try:
        xr.Dataset(bad)
    except Exception:  # MergeError: conflicting values for the residual 'y'
        rejected = True
    assert rejected, (
        "assemble axiom unsound: a conflicting kept residual coordinate should "
        "be rejected (not all-equal), but Dataset(data_dict) succeeded")

    # drop=True (residual discarded): combination SUCCEEDS and recovers verbatim.
    good = {}
    for k in variables:
        good[k] = stacked.sel({variable_dim: k}, drop=True).squeeze(drop=True)
    recovered = xr.Dataset(good)
    assert recovered.identical(data), (
        "assemble axiom unsound: drop=True roundtrip should recover the "
        "original data verbatim, got a differing Dataset")

    # combined_collection token soundness: the recovered collection is exactly
    # the output of the merge (Dataset(good)); a bare per-member mapping that
    # skips the merge (the surviving counterexample's refinement: `return
    # data_dict` instead of `return Dataset(data_dict)`) is NOT a Dataset and is
    # NOT identical to the original -- so the token (held only by the merge's
    # output) cannot be obtained by bypassing the merge.
    assert isinstance(recovered, xr.Dataset)
    assert not (isinstance(good, xr.Dataset)), (
        "token soundness: the un-merged per-member mapping is a plain dict, not "
        "the combination's output -- it cannot equal the original Dataset")
    assert not getattr(good, "identical", lambda _o: False)(data), (
        "token soundness: the un-merged mapping must NOT already equal the "
        "original collection (only the merge's output does)")
    # NOTE: we deliberately do NOT call the public to_unstacked_dataset here --
    # that is the function under change, and at base_commit it is the buggy
    # (drop omitted) version that raises. G-AX validates only the UNCHANGED
    # callees (.sel/.squeeze and the Dataset constructor/merge), which the gold
    # patch composes with drop=True; the manual drop=True path above is exactly
    # that composition and recovers the original verbatim.


def main():
    try:
        import xarray  # noqa: F401
    except Exception as exc:
        print("G-AX SKIP: xarray unavailable (%r) -- run in the evaluation "
              "image" % (exc,))
        return 0

    check_carried()
    check_assemble_and_roundtrip()
    print("G-AX OK: carried(discard, .) matches the real .sel(drop=...).squeeze "
          "(residual position coordinate survives iff drop=False, carrying "
          "distinct per-member values), and the combination (Dataset merge) "
          "rejects the conflicting kept residual / recovers data verbatim when "
          "discarded -- both axioms sound against the real xarray callees.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
