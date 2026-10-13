#!/usr/bin/env python3
"""G-CONF differential conformance check for pydata__xarray-4356 (nagini).

SHADOW: the impl region of model.py's `flag_too_few`, copied verbatim below
with the contract calls (Requires/Ensures/Invariant/Assert) and the proof-only
lemma call stripped. The @Pure helper `prod` copies over as a plain function on
a tuple-backed PSeq shim (used only to sanity-check that generated inputs
satisfy the Requires bounds). There are no @ContractOnly callees in this
bundle.

ORACLE: the REAL patched repo function the model models per mapping.md —
`xarray.core.nanops._maybe_null_out`, reducing a boolean missing-element mask
over a group of axes. The gate applies patch.diff to /testbed before this
script runs; PYTHONPATH=/testbed makes the patched module importable. The
per-position flag is observed behaviourally: the callee is handed a result
array of finite sentinel floats, and a position is flagged exactly when the
callee fills it with the promoted missing-value marker (NaN for floats), so
`isnan(output)` IS the per-position boolean under specification.

Type bridge (mapping.md section 2): `sizes` is the selection of the mask's
shape along the reduced axes, `missing` is the mask's per-position sum over
those axes, `required_minimum` is the callee's `min_count` keyword, and the
shadow's bool compares against the observed per-position fill flag. All
quantities are exact integers / booleans — no precision concern.

Input domain: Requires demands len(sizes) >= 1 (at least one reduced axis) and
0 <= missing <= prod(sizes); both hold by construction for any boolean mask
summed over a non-empty axis group. The callee's array branch additionally
needs at least one un-reduced axis (so its result keeps ndim >= 1), so
generation reduces over proper non-empty axis subsets. Both spellings of a
single reduced axis (bare int and 1-tuple) are exercised. `min_count` spans
negative, zero, interior, and beyond-block values.

>= 1e5 Requires-satisfying inputs: every output position of every reduction is
one input triple (sizes, missing, required_minimum) to the modeled function.
Deterministic boundary configurations (all-missing / none-missing masks,
size-1 axes, extreme minimums) plus fuzz until >= 100000 positions checked.
Pinned fuzz seed: 4356.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + numpy only.
"""
import json
import random
import sys

import numpy as np

SEED = 4356
TARGET = 100_000


# --- PSeq shim: immutable sequence, the operations the pure region uses -------

class PSeq:
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def take(self, n):
        return PSeq._wrap(self._t[:n])

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]


# --- pure helper from model.py, contracts stripped ----------------------------

def prod(xs):
    """Product fold over a sequence (empty product is 1). Front-recursive so a
    single unfold is available per loop step."""
    if len(xs) == 0:
        return 1
    return xs[0] * prod(xs.drop(1))


# --- the impl region of model.py, verbatim, contract/lemma calls stripped -----

def flag_too_few(sizes, missing, required_minimum):
    # total = product over the reduced axes of their sizes  (select then product)
    total = 1
    k = 0
    while k < len(sizes):
        total = total * sizes[k]
        k = k + 1
    return (total - missing - required_minimum) < 0


# --- driver -------------------------------------------------------------------

SENTINEL = 7.0  # finite value the callee only replaces at flagged positions


def check_config(maybe_null_out, mask, axis_arg, min_count):
    """Reduce `mask` over `axis_arg` with the real callee and compare its
    per-position flag against the shadow at EVERY output position. Returns
    (positions_checked, error_string_or_None)."""
    axis_list = [axis_arg] if isinstance(axis_arg, int) else list(axis_arg)
    sizes = [int(mask.shape[ax]) for ax in axis_list]

    # Requires of the modeled function (sanity via the copied pure helper)
    assert len(sizes) >= 1
    block = prod(PSeq(*sizes))

    axis_t = axis_arg if isinstance(axis_arg, int) else tuple(axis_arg)
    missing = np.asarray(mask.sum(axis_t))
    assert missing.ndim >= 1  # the array branch under specification

    result = np.full(missing.shape, SENTINEL, dtype=np.float64)
    out = np.asarray(maybe_null_out(result, axis_t, mask, min_count))
    real_flags = np.isnan(out).reshape(-1)
    flat_missing = missing.reshape(-1)

    for i in range(flat_missing.size):
        m = int(flat_missing[i])
        assert 0 <= m <= block  # Requires holds by construction
        shadow = flag_too_few(list(sizes), m, min_count)
        real = bool(real_flags[i])
        if shadow != real:
            return i, ("DISAGREEMENT\n  mask_shape=%r axis=%r min_count=%r\n"
                       "  sizes=%r missing=%r\n  shadow=%r real=%r"
                       % (mask.shape, axis_t, min_count, sizes, m, shadow, real))
    return flat_missing.size, None


def boundary_configs():
    """(shape, axis, min_count, mask_kind) with deterministic masks: size-1
    axes, single vs several reduced axes (int and tuple spellings), and
    minimums below / at / just above / far above the block size."""
    cfgs = []
    for shape, axis in [
        ((1, 1), (0,)),
        ((1, 5), (1,)),
        ((5, 1), (0,)),
        ((3, 4), 0),            # bare-int single axis
        ((3, 4), (0,)),         # same axis, tuple spelling
        ((2, 3, 4), (0, 1)),
        ((2, 3, 4), (1, 2)),
        ((2, 3, 4), (0, 2)),
        ((1, 1, 6), (0, 1)),
        ((4, 4, 4), (0, 1)),
        ((2, 2, 2, 3), (0, 1, 2)),
    ]:
        axis_list = [axis] if isinstance(axis, int) else list(axis)
        block = 1
        for ax in axis_list:
            block *= shape[ax]
        for mc in (-1, 0, 1, block - 1, block, block + 1, block + 5):
            for kind in ("none", "all", "checker"):
                cfgs.append((shape, axis, mc, kind))
    return cfgs


def make_mask(shape, kind, rng):
    n = 1
    for s in shape:
        n *= s
    if kind == "none":
        return np.zeros(shape, dtype=bool)
    if kind == "all":
        return np.ones(shape, dtype=bool)
    if kind == "checker":
        return (np.arange(n) % 2 == 0).reshape(shape)
    # random with a random density (drives missing across [0, block])
    p = rng.random()
    return np.array([rng.random() < p for _ in range(n)]).reshape(shape)


def main():
    from xarray.core.nanops import _maybe_null_out  # REAL patched callee

    checked = 0
    n_boundary = 0
    for shape, axis, mc, kind in boundary_configs():
        mask = make_mask(shape, kind, None)
        n, err = check_config(_maybe_null_out, mask, axis, mc)
        if err:
            print(err)
            return 1
        checked += n
        n_boundary += n

    rng = random.Random(SEED)
    n_fuzz_cfg = 0
    while checked < TARGET:
        ndim = rng.randint(2, 4)
        shape = tuple(rng.randint(1, 6) for _ in range(ndim))
        k = rng.randint(1, ndim - 1)     # leave >=1 un-reduced axis
        axis_list = sorted(rng.sample(range(ndim), k))
        if k == 1 and rng.random() < 0.5:
            axis = axis_list[0]          # exercise the bare-int spelling too
        else:
            axis = tuple(axis_list)
        block = 1
        for ax in axis_list:
            block *= shape[ax]
        mc = rng.choice([rng.randint(-2, block + 3), 0, 1, block])
        mask = make_mask(shape, "random", rng)
        n, err = check_config(_maybe_null_out, mask, axis, mc)
        if err:
            print(err)
            return 1
        checked += n
        n_fuzz_cfg += 1

    print("G-CONF OK: shadow impl == real per-position flag on %d positions "
          "(%d boundary, %d fuzz configurations, seed %d)."
          % (checked, n_boundary, n_fuzz_cfg, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
