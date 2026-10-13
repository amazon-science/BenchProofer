#!/usr/bin/env python3
"""G-AX executable soundness check for pydata__xarray-4695.

This bundle has NO consumed @ContractOnly axioms: the routing behaviour of the
selection facade is modelled DEEPLY (model.py's `forward_axis_names` /
`bound_reserved_option`, and the pure `option_after_namekeyed`). What must be
validated out-of-band is that the deep model faithfully captures the REAL
Python argument-binding semantics that the gold patch depends on -- i.e. the
difference between forwarding an axis mapping POSITIONALLY versus splatting it
into KEYWORDS, when the underlying selector reserves option names
(`method`, `tolerance`, `drop`).

It reproduces, with the real Python interpreter, a `sel`-shaped callee with the
exact signature of `DataArray.sel`

    sel(indexers=None, method=None, tolerance=None, drop=False, **indexers_kwargs)

and the exact dispatch helper `either_dict_or_kwargs` from xarray.core.utils,
then asserts on boundary + fuzz mappings that:

  (model: positional forwarding -- the gold `self.data_array.sel(key)`)
    * every entry of the mapping is forwarded as an axis indexer
      (effective_indexers == the whole mapping), and
    * the reserved option `method` stays at its default (None) for every
      mapping, including one whose axis name is "method".
    => matches model.py `forward_axis_names` (Result == names in full) and
       `bound_reserved_option` (Result == DEFAULT_OPTION).

  (pre-fix: keyword splatting -- `self.data_array.sel(**key)`)
    * an entry whose name collides with a reserved option name is diverted out
      of the axis indexers into that reserved slot, so the colliding axis is
      DROPPED from the effective indexers and the reserved option is polluted.
    => matches the pre-patch skeletons (forward drops RESERVED_NAME entries;
       option == option_after_namekeyed, the last colliding value).

Imports nothing repo-specific beyond a faithful local copy of the stdlib-only
helper. Exit 0 iff every observation matches the model.
"""
import random
import sys
from typing import Any, Hashable, Mapping, Optional


# --- faithful copy of xarray.core.utils.either_dict_or_kwargs (base_commit) --
def either_dict_or_kwargs(pos_kwargs, kw_kwargs, func_name):
    if pos_kwargs is not None:
        if not (hasattr(pos_kwargs, "keys") and hasattr(pos_kwargs, "__getitem__")):
            raise ValueError(
                "the first argument to .%s must be a dictionary" % func_name
            )
        if kw_kwargs:
            raise ValueError(
                "cannot specify both keyword and positional "
                "arguments to .%s" % func_name
            )
        return pos_kwargs
    else:
        return kw_kwargs


# --- a `sel`-shaped callee with DataArray.sel's exact reserved-option names --
def sel(indexers=None, method=None, tolerance=None, drop=False, **indexers_kwargs):
    """Returns (effective_indexers, method, tolerance, drop) -- exactly the
    dispatch DataArray.sel performs before delegating, so we observe how the
    incoming mapping is routed."""
    effective = either_dict_or_kwargs(indexers, indexers_kwargs, "sel")
    return dict(effective), method, tolerance, drop


# Reserved option names of the underlying selector (DataArray.sel parameters
# that are NOT the axis mapping). "method" is the one the issue collides with.
RESERVED = ("method", "tolerance", "drop")


def check_positional(mapping):
    """The gold path: sel(key). All entries forwarded; options at default."""
    eff, method, tolerance, drop = sel(mapping)
    assert eff == mapping, (
        "positional forwarding lost/changed entries: %r -> %r" % (mapping, eff))
    assert method is None, "positional call polluted method: %r" % (method,)
    assert tolerance is None, "positional call polluted tolerance: %r" % (tolerance,)
    assert drop is False, "positional call polluted drop: %r" % (drop,)


def check_keyword_splat(mapping):
    """The pre-fix path: sel(**key). A colliding axis name is diverted into the
    reserved option slot and dropped from the effective indexers."""
    eff, method, tolerance, drop = sel(**mapping)
    expected_eff = {k: v for k, v in mapping.items() if k not in RESERVED}
    assert eff == expected_eff, (
        "keyword splat routing mismatch: %r -> indexers %r, expected %r"
        % (mapping, eff, expected_eff))
    # reserved options take the colliding entries' values (else default)
    assert method == mapping.get("method", None), (
        "method option not bound from colliding axis: %r" % (mapping,))
    assert tolerance == mapping.get("tolerance", None)
    assert drop == mapping.get("drop", False)
    # The discriminating consequence: when an axis is named like a reserved
    # option, the splat path corrupts the selection.
    if "method" in mapping:
        assert "method" not in eff, (
            "splat path must drop the 'method' axis from indexers: %r" % (eff,))
        assert method == mapping["method"], (
            "splat path must bind 'method' axis value to the option slot")


def main():
    # --- boundary mappings ---------------------------------------------------
    boundary = [
        {},
        {"dim1": "x"},
        {"dim1": "x", "dim2": "a"},
        {"dim1": "x", "method": "a"},            # the issue's exact case
        {"method": "a"},                         # axis named like the option
        {"method": "a", "tolerance": "b", "drop": "c"},  # all three collide
        {"dim1": "x", "method": "a", "dim2": "b"},
        {"method": "a", "method2": "b"},
        {"x": 1, "y": 2, "z": 3},
        {"drop": 0},
        {"tolerance": 5},
    ]
    for m in boundary:
        check_positional(m)
        check_keyword_splat(m)

    # --- randomized fuzz -----------------------------------------------------
    rng = random.Random(4695)
    names_pool = ["dim1", "dim2", "method", "tolerance", "drop", "x", "y",
                  "alpha", "beta", "method_", "k0", "k1"]
    for _ in range(20000):
        n = rng.randint(0, 6)
        keys = rng.sample(names_pool, min(n, len(names_pool)))
        m = {k: rng.randint(0, 9) for k in keys}
        check_positional(m)
        check_keyword_splat(m)

    print("G-AX OK: positional forwarding (gold) keeps every axis and leaves "
          "reserved options at default; keyword-splat (pre-fix) diverts a "
          "reserved-name axis into the option slot -- validated on %d boundary "
          "+ 20000 fuzz mappings. Deep model is faithful." % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
