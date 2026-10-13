#!/usr/bin/env python
"""G-CONF: differential conformance for pydata__xarray-3305.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). Builds the Python R shadow of the Lean impl skeletons and
diffs it against the REAL patched `Variable.quantile` and `Dataset.quantile`
over a discrete matrix plus >=1e5 randomized draws on real numpy/xarray objects.

  shadow of implementation_arrayQuantile        vs   Variable.quantile
  shadow of implementation_collectionQuantile   vs   Dataset.quantile
  observable: (sorted dims, attrs-as-sorted-items)

The differential test targets the CHANGED behavior: whether the reduced result
keeps the source's attributes.  Post-patch this is governed by the resolved
keep request (explicit `keep_attrs`, else the global option); a kept result
carries the source attrs, a dropped result carries empty attrs.  The reduction
itself (remaining dims + the nanpercentile value array) is unchanged by the
patch and taken as modeled input.

Exit 0 iff zero disagreements. stdlib-only fuzzing (pinned seed).
"""
import random
import sys

SEED = 3305
N_RANDOM = 110_000  # >= 1e5


def resolve_keep_attrs(keep_attrs, global_default):
    """resolveKeepAttrs: explicit choice if given, else the default flag."""
    return global_default if keep_attrs is None else keep_attrs


def shadow_array(self_attrs, keep_attrs, global_default):
    """R shadow of implementation_arrayQuantile, attrs component only.
    Returns the observable attrs as a sorted item tuple ((),) when dropped."""
    keep = resolve_keep_attrs(keep_attrs, global_default)
    return tuple(sorted(self_attrs.items())) if keep else tuple()


def main():
    import numpy as np
    import xarray as xr
    from xarray.core.variable import Variable

    rng = random.Random(SEED)

    # attribute mappings whose presence vs absence is the observable.
    ATTR_CHOICES = [
        {},
        {"units": "K"},
        {"units": "K", "long_name": "temperature"},
        {"a": "1", "b": "2", "c": "3"},
    ]
    # global option -> resolved global_default bool (default => False here).
    GLOBAL_CHOICES = ["default", True, False]

    def global_default_of(opt):
        return False if opt == "default" else opt

    def observe_attrs(obj):
        return tuple(sorted(dict(obj.attrs).items()))

    def real_observe_array(self_attrs, keep_attrs, global_opt, n, q):
        data = np.arange(float(n)) + 0.5
        var = Variable(("x",), data, attrs=dict(self_attrs))
        with xr.set_options(keep_attrs=global_opt):
            res = var.quantile(q, dim="x", keep_attrs=keep_attrs)
        return observe_attrs(res)

    def real_observe_collection(members, keep_attrs, global_opt, n, q):
        # members: list of attr dicts; build a Dataset whose data_vars each
        # reduce over the shared dim "x".
        data_vars = {}
        for i, attrs in enumerate(members):
            data = np.arange(float(n)) + 0.5 + i
            data_vars[f"v{i}"] = xr.DataArray(
                data, dims=("x",), attrs=dict(attrs), name=f"v{i}"
            )
        ds = xr.Dataset(data_vars)
        with xr.set_options(keep_attrs=global_opt):
            res = ds.quantile(q, dim="x", keep_attrs=keep_attrs)
        return tuple(observe_attrs(res[f"v{i}"]) for i in range(len(members)))

    disagreements = 0
    checked = 0

    def check_array(self_attrs, keep_attrs, global_opt, n, q):
        nonlocal disagreements, checked
        gd = global_default_of(global_opt)
        exp = shadow_array(self_attrs, keep_attrs, gd)
        got = real_observe_array(self_attrs, keep_attrs, global_opt, n, q)
        checked += 1
        if exp != got:
            disagreements += 1
            if disagreements <= 5:
                print(f"ARRAY MISMATCH attrs={self_attrs} keep={keep_attrs} "
                      f"opt={global_opt} q={q}: real={got!r} shadow={exp!r}")

    def check_collection(members, keep_attrs, global_opt, n, q):
        nonlocal disagreements, checked
        gd = global_default_of(global_opt)
        exp = tuple(shadow_array(m, keep_attrs, gd) for m in members)
        got = real_observe_collection(members, keep_attrs, global_opt, n, q)
        checked += 1
        if exp != got:
            disagreements += 1
            if disagreements <= 5:
                print(f"COLL MISMATCH members={members} keep={keep_attrs} "
                      f"opt={global_opt} q={q}: real={got!r} shadow={exp!r}")

    # ---- discrete edge matrix (incl. the F2P scenario: keep_attrs=True) -------
    for attrs in ATTR_CHOICES:
        for keep in [None, True, False]:
            for opt in GLOBAL_CHOICES:
                for q in [0.5, [0.25, 0.75]]:
                    check_array(attrs, keep, opt, 4, q)
    # F2P-faithful: non-empty attrs, keep_attrs=True, global default -> keep.
    check_array({"units": "K"}, True, "default", 2, 0.9)

    # collection edge matrix
    for keep in [None, True, False]:
        for opt in GLOBAL_CHOICES:
            check_collection([{"units": "K"}, {}, {"a": "1"}], keep, opt, 4, 0.5)

    # ---- randomized fuzz ----
    for _ in range(N_RANDOM):
        attrs = rng.choice(ATTR_CHOICES)
        keep = rng.choice([None, True, False])
        opt = rng.choice(GLOBAL_CHOICES)
        n = rng.randint(2, 6)
        q = rng.choice([0.1, 0.5, 0.9, [0.25, 0.5], [0.0, 0.5, 1.0]])
        check_array(attrs, keep, opt, n, q)
        if _ % 50 == 0:
            members = [rng.choice(ATTR_CHOICES) for _ in range(rng.randint(1, 3))]
            check_collection(members, keep, opt, n, q)

    print(f"checked={checked} disagreements={disagreements}")
    if disagreements == 0:
        print(f"status=pass conformance OK ({checked} checks, 0 disagreements)")
        return 0
    print(f"status=fail {disagreements} disagreement(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
