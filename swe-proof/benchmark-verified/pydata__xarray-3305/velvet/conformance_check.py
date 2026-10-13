#!/usr/bin/env python3
"""G-CONF differential conformance check for pydata__xarray-3305 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl regions transliterated
              to Python over the *real* repo types, via the mapping.md bijection
              (`attrs` OrderedDict/None <-> association list / {}; `keep_attrs`
              bool/None <-> Option Bool; OPTIONS["keep_attrs"] <-> GlobalPref).
              The A-reference callee `resolveGlobal` is NOT substituted by its
              model here; G-CONF isolates the R/I legs, so the `none` fallback is
              delegated to the REAL `_get_keep_attrs` (the A leg stays with G-AX).
  * ORACLE  — `patch.diff`'s behaviour: the patched `DataArray.quantile`
              (-> Dataset.quantile -> Variable.quantile) applied at base_commit,
              the real correctness oracle (the F2P path, G-RESOLVE). We observe
              the attribute mapping carried onto the result.

This exercises BOTH patched sites end to end (the DataArray wrapper delegates to
Dataset.quantile which forwards keep_attrs to Variable.quantile). They must agree
on every input. Exit 0 iff zero disagreements; any disagreement is a mechanical
R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image). The fuzz seed is
pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

SEED = 3305
N_FUZZ = 100_000


def shadow_attrs(src_attrs, choice, glob, get_keep_attrs, set_options):
    """keptAttrs(srcAttrs, choice, glob) transliterated. The `none` branch
    delegates to the REAL _get_keep_attrs (A-reference, mapping.md §3.1), with
    the element op's own fallback = False (the variable.py hunk's default)."""
    if choice is not None:
        effective = bool(choice)
    else:
        with set_options(keep_attrs=glob):
            effective = bool(get_keep_attrs(default=False))
    return dict(src_attrs) if effective else {}


def oracle_attrs(src_attrs, choice, glob, np, DataArray, set_options):
    """patch.diff's behaviour: the patched DataArray.quantile end to end. Build a
    labeled array carrying `src_attrs`, reduce it, observe the result's attrs."""
    data = np.arange(6.0).reshape(6)
    da = DataArray(data, dims="x", attrs=dict(src_attrs))
    with set_options(keep_attrs=glob):
        out = da.quantile(0.5, dim="x", keep_attrs=choice)
    return dict(out.attrs)


def fuzz_inputs(n, rng):
    keys = ["units", "long_name", "attr1", "attr2", "source", "_FillValue"]
    vals = ["K", "m/s", "value1", "2929", "temperature", "x", "", "0"]
    choices = [True, False, None]
    globs = ["default", True, False]
    # boundary cases first
    base_attr_sets = [
        {},
        {"units": "K"},
        {"attr1": "value1", "attr2": "2929"},
        {"units": "K", "long_name": "temperature", "source": "x"},
    ]
    for sa in base_attr_sets:
        for c in choices:
            for g in globs:
                yield (sa, c, g)
    for _ in range(n):
        k = rng.randint(0, 4)
        sa = {}
        for _ in range(k):
            sa[rng.choice(keys)] = rng.choice(vals)
        yield (sa, rng.choice(choices), rng.choice(globs))


def main():
    import numpy as np
    from xarray import DataArray, set_options
    from xarray.core.options import _get_keep_attrs

    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for src_attrs, choice, glob in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_attrs(src_attrs, choice, glob, _get_keep_attrs, set_options)
        oracle = oracle_attrs(src_attrs, choice, glob, np, DataArray, set_options)
        if shadow != oracle:
            disagreements.append((src_attrs, choice, glob, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for sa, c, g, sh, orc in disagreements:
            print("  attrs=%r choice=%r glob=%r shadow=%r oracle=%r"
                  % (sa, c, g, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of reduce*Attrs agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
