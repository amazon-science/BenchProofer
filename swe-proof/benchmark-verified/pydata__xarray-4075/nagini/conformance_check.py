#!/usr/bin/env python3
"""G-CONF differential conformance check for pydata__xarray-4075 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls stripped. The impl's single callee ``dot_reduce`` is @ContractOnly (an
A-consumed axiom for the unchanged community dot-product reduction), so the
shadow delegates it to the REAL repo callee the model maps it to
(``xarray.core.computation.dot`` via the public ``xr.dot``, per mapping.md
section 3.1): the presence mask is handed as a boolean array (it always is in
the repo) and ``boolean_dot`` selects the element type of the weights operand
— numeric when False (the impl's choice), boolean when True. The @Pure deep
models ``int_dot`` / ``bool_dot`` copy over on a small PSeq shim and serve as
an internal cross-check of the shadow's output.

ORACLE: the REAL patched repo function per mapping.md section 1 —
``xarray.core.weighted.Weighted._sum_of_weights``. The gate applies patch.diff
to /testbed and sets PYTHONPATH=/testbed before this script runs, so the
import resolves to the patched module.

Type bridge (mapping.md section 2): ``mask: List[int]`` of 0/1 lifts to a
data array with a present value where 1 and a missing value (NaN) where 0, so
the repo's own presence mask (``da.notnull()``) reproduces it exactly;
``weights: List[int]`` lifts to a weights array of dtype bool when
``weights_are_bool`` (values then 0/1 by the precondition) else a numeric
integer dtype; the modeled single reduced axis is the whole 1-D sequence.
The modeled function returns the value of the reduction statement itself; the
repo function additionally applies its unchanged downstream masking of
zero-total results (mapping.md section 1: identity on non-zero results, and a
zero reduction is the only way our finite inputs produce a masked slot), so
the bridge back is: a masked (NaN) oracle result denotes the reduction value
0, any other result is the reduction value itself.

Input domain (the preconditions): equal-length lists, mask values in {0,1},
weights non-negative ints, and all-{0,1} weights whenever weights_are_bool.

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz pairs.
Pinned fuzz seed: 4075 (the instance number).

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + the repo's own numpy/xarray only.
"""
import json
import random
import sys

SEED = 4075
N_FUZZ = 100000


# --- PSeq shim: immutable sequence, the operations the pure region uses ------

class PSeq(object):
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]


def ToSeq(lst):
    return PSeq._wrap(lst)


# --- pure region of model.py, contracts stripped (internal cross-check) -----

def int_dot(mask, weights):
    """Numeric dot-product reduction: the arithmetic sum of the present
    samples' weights, sum_i mask[i] * weights[i]. (Iterative here to sidestep
    recursion limits on long fuzz inputs; extensionally the same fold as
    model.py's front recursion.)"""
    total = 0
    i = 0
    while i < len(mask):
        total = total + mask[i] * weights[i]
        i = i + 1
    return total


def bool_dot(mask, weights):
    """Boolean (saturating) dot-product reduction: 1 iff some position has
    both flags set, else 0. Iterative form of model.py's front recursion."""
    acc = 0
    i = 0
    while i < len(mask):
        head = 1 if (mask[i] >= 1 and weights[i] >= 1) else 0
        acc = head if head >= acc else acc
        i = i + 1
    return acc


# --- @ContractOnly callee: the REAL repo dot (mapping.md section 3.1) --------

def dot_reduce(mask, weights, boolean_dot):
    """The axiomatized array dot-product reduction, delegated to the REAL
    unchanged repo callee ``xarray.core.computation.dot`` (public ``xr.dot``),
    contracting the single modeled axis fully. Per the type bridge, the
    presence mask is always a boolean array; ``boolean_dot`` says whether the
    weights operand is ALSO boolean (both-boolean is the only way the
    contraction runs in boolean arithmetic)."""
    import numpy as np
    import xarray as xr

    m = xr.DataArray(np.asarray([v == 1 for v in mask._t], dtype=bool),
                     dims=["x"])
    wdtype = bool if boolean_dot else np.int64
    w = xr.DataArray(np.asarray(list(weights._t), dtype=wdtype), dims=["x"])
    return int(np.asarray(xr.dot(m, w, dims="x").values).item())


# --- the impl region of model.py, verbatim, contract calls stripped ----------

def sum_of_weights_value(mask, weights, weights_are_bool):
    # Hand the dot a numeric operand (a boolean weight array is cast to int
    # first), so the reduction always runs in numeric arithmetic and counts.
    boolean_dot = False
    result = dot_reduce(ToSeq(mask), ToSeq(weights), boolean_dot)
    return result


# --- oracle: the real patched repo function ----------------------------------

def make_oracle():
    import numpy as np
    import xarray as xr

    def oracle(mask, weights, weights_are_bool):
        # bridge in: mask -> data array with a missing value where mask==0,
        # so the repo's own presence mask reproduces the model's mask exactly;
        # weights -> array of the declared element type.
        vals = np.asarray([1.0 if m == 1 else np.nan for m in mask],
                          dtype=float)
        da = xr.DataArray(vals, dims=["x"])
        wdtype = bool if weights_are_bool else np.int64
        w = xr.DataArray(np.asarray(weights, dtype=wdtype), dims=["x"])
        out = da.weighted(w)._sum_of_weights(da, dim="x")
        v = np.asarray(out.values).item()
        # bridge out: the repo function masks zero totals to a missing value
        # downstream of the modeled statement (identity on non-zero results);
        # with finite inputs a missing result denotes the reduction value 0.
        if isinstance(v, float) and np.isnan(v):
            return 0
        return int(v)

    return oracle


# --- differential driver ------------------------------------------------------

def check(oracle, mask, weights, weights_are_bool):
    """Run shadow and oracle on one input; return an error string on
    disagreement, else None."""
    shadow = sum_of_weights_value(mask, weights, weights_are_bool)
    real = oracle(mask, weights, weights_are_bool)
    if shadow != real:
        return ("DISAGREEMENT on mask=%r weights=%r weights_are_bool=%r:\n"
                "  shadow (impl region)                    = %r\n"
                "  real (patched repo _sum_of_weights)     = %r"
                % (mask, weights, weights_are_bool, shadow, real))
    # internal cross-check: the shadow agrees with the pure numeric fold
    expected = int_dot(mask, weights)
    if shadow != expected:
        return ("INTERNAL: impl region (%r) and pure fold int_dot (%r) "
                "disagree on mask=%r weights=%r"
                % (shadow, expected, mask, weights))
    return None


def boundary_cases():
    """(mask, weights, weights_are_bool) triples at the domain's edges."""
    cases = [
        # empty sequences
        ([], [], False),
        ([], [], True),
        # singletons, every mask/weight flag combination (boolean weights)
        ([0], [0], True), ([0], [1], True),
        ([1], [0], True), ([1], [1], True),
        # singletons, numeric weights incl. zero and large
        ([0], [0], False), ([1], [0], False),
        ([1], [1], False), ([1], [7], False), ([0], [9], False),
        # the decisive shape: several present unit weights must accumulate
        ([1, 1], [1, 1], True),
        ([1, 1], [1, 1], False),
        ([1, 1, 1], [1, 1, 1], True),
        ([1, 1, 1, 1, 1], [1, 1, 1, 1, 1], True),
        # exactly one overlapping position (saturating and counting agree)
        ([1, 0], [1, 1], True),
        ([0, 1], [1, 0], True),
        # no overlap / all-absent / all-zero weights (zero total, the
        # masked-downstream case)
        ([0, 0], [1, 1], True),
        ([1, 1], [0, 0], True),
        ([1, 0, 1], [0, 1, 0], True),
        ([0, 0, 0], [4, 5, 6], False),
        ([1, 1, 1], [0, 0, 0], False),
        # mixed numeric weights
        ([1, 0, 1], [3, 5, 7], False),
        ([1, 1, 1, 1], [0, 1, 0, 1], False),
        ([1, 1], [1, 2], False),
        ([0, 1, 1, 0, 1], [9, 8, 7, 6, 5], False),
        # longer runs
        ([1] * 40, [1] * 40, True),
        ([1] * 40, [1] * 40, False),
        ([i % 2 for i in range(30)], [i % 3 for i in range(30)], False),
        ([1] * 25, [0, 1] * 12 + [1], True),
    ]
    return cases


def main():
    smoke = "--smoke" in sys.argv[1:]
    n_fuzz = 500 if smoke else N_FUZZ
    oracle = make_oracle()

    checked = 0
    boundary = boundary_cases()
    for mask, weights, wab in boundary:
        err = check(oracle, mask, weights, wab)
        if err:
            print(err)
            return 1
        checked += 1

    # randomized fuzz over the precondition's domain (pinned seed):
    # length 0..12 (occasionally up to 48), mask flags 0/1, and both weight
    # element types — boolean weights drawn from {0,1}, numeric weights from
    # 0..9 with occasional larger values. Present/weighted densities vary so
    # zero-total, saturating-equal (count<=1) and count>=2 shapes all recur.
    rng = random.Random(SEED)
    for k in range(n_fuzz):
        n = rng.randint(0, 48) if k % 20 == 0 else rng.randint(0, 12)
        p_mask = rng.choice((0.1, 0.3, 0.5, 0.7, 0.9))
        mask = [1 if rng.random() < p_mask else 0 for _ in range(n)]
        wab = rng.random() < 0.5
        if wab:
            p_w = rng.choice((0.1, 0.5, 0.9))
            weights = [1 if rng.random() < p_w else 0 for _ in range(n)]
        else:
            weights = [rng.randint(0, 9) if rng.random() < 0.9
                       else rng.randint(10, 1000) for _ in range(n)]
        err = check(oracle, mask, weights, wab)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched _sum_of_weights on %d "
          "inputs (%d boundary + %d fuzz, seed %d); 0 disagreements."
          % (checked, len(boundary), n_fuzz, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region; "
                                "dot_reduce delegated to the real xr.dot)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
