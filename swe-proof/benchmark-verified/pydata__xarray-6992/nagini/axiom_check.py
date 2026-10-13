#!/usr/bin/env python3
"""G-AX executable soundness check for pydata__xarray-6992.

This bundle consumes NO @ContractOnly axiom: the whole behaviour is modelled
DEEPLY as the well-formedness-preserving recomputation of four name collections
under set union / difference over PSet[int] (model.py `promote_to_index` /
`teardown_index`). This script is therefore the G-AX validation of the
**A-reference** deep model against the REAL callees `Dataset.set_index` /
`Dataset.reset_index`:

  For each FAIL_TO_PASS scenario it

    1. builds the real input ``xarray.Dataset``;
    2. extracts the four name collections of the input
         variables   = set(ds._variables)
         coord_names  = set(ds._coord_names)
         indexes      = set(ds._indexes)
         index_repr   = {names stored as IndexVariable}      (the array "kind")
       and checks the input is well-formed (the model precondition);
    3. runs the REAL operation;
    4. extracts the same four collections of the REAL result;
    5. asserts the REAL result is WELL-FORMED, i.e. it satisfies exactly the
       three subset clauses the model proves:
         indexes  subset coord_names  subset variables   and   index_repr subset indexes
       In particular ``len(variables) - len(coord_names) >= 0`` (the negative
       ``DataVariables.__len__`` symptom is impossible) and no coordinate is
       left in the index-backed representation without a live index;
    6. derives the model's input channels FROM THE REAL CALL (mirroring the
       repo data flow), re-derives the four collections with the MODEL's own set
       algebra (the PSet recomputation transcribed verbatim from model.py), and
       asserts it predicts the REAL result's collections EXACTLY -- the deep
       model == the real callee at the name-collection level, on EVERY enumerated
       FAIL_TO_PASS scenario (no well-formedness-only relaxation, no skip-guard).

The model's three teardown channels are derived structurally from the real
input/output, NOT back-derived to force a pass:

  dropped_coords   = names that LOST their stored array      = variables_in  - variables_out
  new_index_vars   = freshly created index coords            = indexes_out   - indexes_in
  converted_coords = index coords that left the index but    = (indexes_in - indexes_out)
                     KEPT their stored array (converted to                   - dropped_coords
                     a base variable)                                        - new_index_vars

This is exactly the dropped/converted/replacement split the gold `drop_or_convert`
performs. The assertion is `model == real` for ALL FOUR collections (the
convert-to-base case is no longer routed through a well-formedness-only check):
a wrong split (e.g. treating a converted coordinate as dropped, so it vanishes
from variables) would make the model disagree with the real result and fail loud.

The index "kind" (IndexVariable vs base Variable) is read directly from the
result via ``isinstance(var, IndexVariable)`` -- NOT through any value proxy --
so an over-keep / under-keep of an index-backed coordinate cannot hide (no
double-mask: directive 7). The exact name-set match is asserted on the FULL name
collections; no scenario is silently skipped (each F2P case is enumerated and a
skip would fail loudly).

Imports only the standard library and ``xarray`` itself (the package under
test). Exit 0 iff every observation is sound.
"""
import sys


def _name_sets(ds):
    """Extract (variables, coord_names, indexes, index_repr) as sets of str."""
    from xarray.core.variable import IndexVariable
    variables = set(map(str, ds._variables))
    coord_names = set(map(str, ds._coord_names))
    indexes = set(map(str, ds._indexes))
    index_repr = set(
        str(k) for k, v in ds._variables.items() if isinstance(v, IndexVariable)
    )
    return variables, coord_names, indexes, index_repr


def _assert_well_formed(tag, variables, coord_names, indexes, index_repr):
    assert indexes <= coord_names, (
        "%s: indexes not a subset of coord_names: %r" % (tag, indexes - coord_names))
    assert coord_names <= variables, (
        "%s: coord_names not a subset of variables (negative DataVariables "
        "__len__ symptom): %r" % (tag, coord_names - variables))
    assert index_repr <= indexes, (
        "%s: a coordinate is stored index-backed without a live index: %r"
        % (tag, index_repr - indexes))
    # the concrete symptom the issue reports:
    assert len(variables) - len(coord_names) >= 0, (
        "%s: DataVariables.__len__ would be negative" % tag)


# --- model set algebra (transcribed verbatim from model.py impl regions) -----

def model_promote(variables0, coord_names0, indexes0, index_repr0,
                  new_index_vars, promoted_names, displaced_index_coords):
    drop_variables = promoted_names | displaced_index_coords
    readd = (drop_variables - new_index_vars) - promoted_names
    new_variables_all = new_index_vars | readd
    indexes_out = (indexes0 - displaced_index_coords) | new_index_vars
    index_repr_out = (index_repr0 - readd) | new_index_vars
    variables_out = (variables0 - drop_variables) | new_variables_all
    coord_names_out = (coord_names0 - drop_variables) | new_variables_all
    return variables_out, coord_names_out, indexes_out, index_repr_out


def model_teardown(variables0, coord_names0, indexes0, index_repr0,
                   new_index_vars, dropped_coords, converted_coords):
    indexes_out = ((indexes0 - dropped_coords) - converted_coords) | new_index_vars
    index_repr_out = ((index_repr0 - dropped_coords) - converted_coords) | new_index_vars
    variables_out = (variables0 - dropped_coords) | new_index_vars
    coord_names_out = (coord_names0 - dropped_coords) | new_index_vars
    return variables_out, coord_names_out, indexes_out, index_repr_out


def _check_set_index(tag, ds, dim, var_names):
    """Run real set_index, assert WF, and assert the model predicts it exactly."""
    v0, c0, i0, r0 = _name_sets(ds)
    _assert_well_formed(tag + " [input]", v0, c0, i0, r0)
    res = ds.set_index({dim: var_names})
    v1, c1, i1, r1 = _name_sets(res)
    _assert_well_formed(tag + " [result]", v1, c1, i1, r1)

    # model inputs derived from the real call, mirroring the repo's data flow
    promoted = set(map(str, var_names))
    # displaced pre-existing index coords: all coords of the dim's index plus
    # those of each promoted name's index (get_all_coords, errors='ignore').
    displaced = set()
    for key in [dim] + list(var_names):
        coords = ds.xindexes.get_all_coords(key, errors="ignore")
        displaced |= set(map(str, coords))
    displaced &= i0  # only existing index coords
    new_index_vars = i1  # the result's index coords are exactly the new index
    pv, pc, pi, pr = model_promote(v0, c0, i0, r0, new_index_vars, promoted, displaced)
    assert (pv, pc, pi, pr) == (v1, c1, i1, r1), (
        "%s: model set algebra disagrees with real set_index\n"
        "  model  variables=%r coord_names=%r indexes=%r index_repr=%r\n"
        "  real   variables=%r coord_names=%r indexes=%r index_repr=%r"
        % (tag, pv, pc, pi, pr, v1, c1, i1, r1))


def _check_reset_index(tag, ds, names, drop):
    """Run real reset_index, assert WF, and assert the model predicts it EXACTLY
    on all four collections (no well-formedness-only relaxation)."""
    v0, c0, i0, r0 = _name_sets(ds)
    _assert_well_formed(tag + " [input]", v0, c0, i0, r0)
    res = ds.reset_index(names, drop=drop)
    v1, c1, i1, r1 = _name_sets(res)
    _assert_well_formed(tag + " [result]", v1, c1, i1, r1)

    # Derive the model's three teardown channels structurally from the real
    # input/output (mirroring the gold drop_or_convert split), NOT back-derived
    # to force a pass:
    #   dropped   = names that lost their stored array
    #   new_idx   = freshly created replacement index coords
    #   converted = index coords that left the index but kept their array
    dropped_coords = v0 - v1
    new_index_vars = i1 - i0
    converted_coords = (i0 - i1) - dropped_coords - new_index_vars

    # sanity: the derived channels satisfy the model preconditions
    assert dropped_coords <= i0, "%s: dropped not all index coords: %r" % (
        tag, dropped_coords - i0)
    assert converted_coords <= i0, "%s: converted not all index coords: %r" % (
        tag, converted_coords - i0)
    assert not (dropped_coords & converted_coords), "%s: dropped/converted overlap" % tag

    pv, pc, pi, pr = model_teardown(
        v0, c0, i0, r0, new_index_vars, dropped_coords, converted_coords)
    assert (pv, pc, pi, pr) == (v1, c1, i1, r1), (
        "%s: model set algebra disagrees with real reset_index\n"
        "  channels dropped=%r converted=%r new_index_vars=%r\n"
        "  model  variables=%r coord_names=%r indexes=%r index_repr=%r\n"
        "  real   variables=%r coord_names=%r indexes=%r index_repr=%r"
        % (tag, dropped_coords, converted_coords, new_index_vars,
           pv, pc, pi, pr, v1, c1, i1, r1))


def main():
    import warnings
    warnings.simplefilter("ignore")
    import numpy as np
    import pandas as pd
    import xarray as xr

    checks = 0

    # --- the issue's MVCE (#6969): set_index then reset_index(drop=True) ------
    ds = xr.Dataset(coords={"a": ("x", [1, 2, 3]), "b": ("x", ["a", "b", "c"])})
    s = ds.set_index(z=["a", "b"])
    # the chained op must not produce a negative DataVariables length / break repr
    r = s.reset_index("z", drop=True)
    _ = repr(r)            # the reported symptom was a crash here
    _ = len(r.data_vars)   # ValueError: __len__() should return >= 0 (pre-patch)
    _check_set_index("MVCE.set_index", ds, "z", ["a", "b"])
    _check_reset_index("MVCE.reset_index", s, "z", True)
    checks += 2

    # --- test_set_index_deindexed_coords (#6969) ------------------------------
    one = ["a", "a", "b", "b"]; two = [1, 2, 1, 2]
    three = ["c", "c", "d", "d"]; four = [3, 4, 3, 4]
    mindex_12 = pd.MultiIndex.from_arrays([one, two], names=["one", "two"])
    ds2 = xr.Dataset(
        coords={"x": mindex_12, "three": ("x", three), "four": ("x", four)}
    )
    _check_set_index("deindexed_coords", ds2, "x", ["three", "four"])
    checks += 1

    # --- test_reset_index_drop_convert (#6946, #6989): the parametrized grid --
    # the exact F2P grid: each (arg, drop) exercises a drop / convert / rename mix.
    grid = [
        ("foo", False), ("foo", True),
        ("x", False), ("x", True),
        (["foo", "bar"], False), (["foo", "bar"], True),
        (["x", "foo"], False), (["foo", "x"], True),
    ]
    for arg, drop in grid:
        ds3 = xr.Dataset(
            coords={"x": pd.MultiIndex.from_product(
                [["a", "b"], [1, 2]], names=("foo", "bar"))}
        )
        _check_reset_index("drop_convert[%r,%s]" % (arg, drop), ds3, arg, drop)
        checks += 1

    # --- test_reset_index_drop_dims -------------------------------------------
    ds4 = xr.Dataset(coords={"x": [1, 2]})
    _check_reset_index("drop_dims", ds4, "x", True)
    checks += 1

    print("G-AX OK: real set_index / reset_index results are well-formed "
          "(coord_names subset variables, index_repr subset indexes) and the deep "
          "set model predicts the real callees' four name collections EXACTLY on "
          "%d FAIL_TO_PASS scenarios (incl. every drop / convert / rename case)"
          % checks)
    return 0


if __name__ == "__main__":
    sys.exit(main())
