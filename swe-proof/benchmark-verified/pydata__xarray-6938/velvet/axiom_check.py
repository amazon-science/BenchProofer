#!/usr/bin/env python3
"""G-AX executable soundness check for pydata__xarray-6938.

Executes the REAL repo callee (`xarray.IndexVariable.to_index_variable`, whose
post-patch body is `self.copy()`) on boundary + fuzzed inputs and asserts that
every observation meets the deep model's `ensures` (Solution.lean's
`reifyIndependent`). The changed operation is modeled DEEPLY (a fresh
allocation + slot copy over an explicit heap), not behind a consumed axiom, so
this is an **A-reference** validation: the deep model == the real callee.

A-REFERENCE TARGET = `IndexVariable.copy` (xarray/core/variable.py:2831), the
UNCHANGED callee the post-patch `to_index_variable` delegates to (`self.copy()`).
We deliberately validate against `copy()`, NOT `to_index_variable()`:
  * directive 7 forbids validating against the function under change;
  * `to_index_variable` is the buggy function at base_commit (returns `self`),
    so it would spuriously fail clause (1) depending on which source is in-image.
`copy()` is byte-identical in both images, so this check is image-independent and
captures exactly the sub-operation the deep model mirrors.

The modeled `ensures`, restated over the real object:
  (1) res ≠ self              -> `to_index_variable()` returns a DISTINCT object
                                  (`a is not b`); res = nextFreshOld (fresh).
  (2) store res = storeOld self -> the copy's `dims` equals the source's `dims`
                                  at call time.
  (3) store self = storeOld self and the frame
                              -> mutating the copy's `dims` does NOT change the
                                 source's `dims` (independence), and the call
                                 itself does not mutate the source.

It also asserts the discriminator's reality: the PRE-PATCH behaviour
(`return self`) would VIOLATE (1) — the source and result would be one object,
so mutating the result would change the source. (We do not have the buggy code
in-image; we demonstrate the violation directly via an alias to make the
discriminating clause executable.)

Imports only the repo's own `xarray` (the same module the gold patch edits) and
stdlib. Exit 0 iff every obligation holds.
"""
import random
import sys

import numpy as np
import xarray as xr
from xarray.core.variable import IndexVariable


def _mk(dimname, values):
    """Construct a 1-D IndexVariable (the object `to_index_variable` returns)."""
    return IndexVariable(dimname, list(values))


def check_copy_reference(iv):
    """Assert the REAL IndexVariable.copy() meets the deep model's ensures."""
    src_dims_before = iv.dims
    src_data_before = list(np.asarray(iv.values).tolist())

    out = iv.copy()                              # UNCHANGED callee (the A-ref)

    # (1) res ≠ self : distinct object identity (the `a is not b` assertion).
    assert out is not iv, (
        "A-reference unsound: copy() returned the SAME object "
        "(res = self); the model requires res ≠ self (a fresh handle). dims=%r"
        % (src_dims_before,))

    # (2) store res = storeOld self : copied content (dims equal at call time).
    assert out.dims == src_dims_before, (
        "A-reference unsound: copy's dims %r != source's dims %r at call time"
        % (out.dims, src_dims_before))

    # (3a) independence: mutating the copy's dims must NOT change the source.
    new_dims = tuple(str(d) + "_y" for d in out.dims)
    out.dims = new_dims
    assert iv.dims == src_dims_before, (
        "A-reference unsound: mutating the result's dims changed the source "
        "(aliasing!). source dims now %r, expected %r"
        % (iv.dims, src_dims_before))

    # (3b) the call itself did not mutate the source's observable state.
    assert iv.dims == src_dims_before, "source dims mutated by the call"
    assert list(np.asarray(iv.values).tolist()) == src_data_before, (
        "source data mutated by the call")


def check_prepatch_would_violate(iv):
    """The discriminating clause is real: `return self` (pre-patch) aliases the
    source, so mutating the 'result' reaches the source — violating (1)/(3)."""
    aliased = iv                                  # models pre-patch `return self`
    assert aliased is iv                          # same object
    before = iv.dims
    bad_dims = tuple(str(d) + "_z" for d in aliased.dims)
    aliased.dims = bad_dims
    violated = (iv.dims != before)                # source changed through alias
    # restore so we don't poison later checks
    iv.dims = before
    assert violated, (
        "discriminator degenerate: aliasing did not surface a source mutation")


def main():
    boundary = [
        _mk("x", ["a"]),                          # the exact F2P construction
        _mk("x", ["a", "b"]),
        _mk("x", []),                             # empty
        _mk("dim_0", list(range(5))),
        _mk("time", [10, 20, 30]),
        _mk("z", np.arange(11) * 10),
        _mk("longdimname", ["only"]),
    ]
    for iv in boundary:
        check_copy_reference(iv)
    # fresh objects for the prepatch-violation demonstration
    for dimname, vals in [("x", ["a"]), ("t", [1, 2, 3]), ("d", list("abc"))]:
        check_prepatch_would_violate(_mk(dimname, vals))

    rng = random.Random(6938)
    letters = list("abcdefghijklmnopqrstuvwxyz")
    for _ in range(2000):
        n = rng.randint(0, 8)
        dimname = "".join(rng.choice(letters) for _ in range(rng.randint(1, 5)))
        if rng.random() < 0.5:
            vals = [rng.randint(-1000, 1000) for _ in range(n)]
        else:
            vals = ["".join(rng.choice(letters)
                            for _ in range(rng.randint(1, 4)))
                    for _ in range(n)]
        # IndexVariable requires a 1-D, hashable-indexable array; lists qualify.
        check_copy_reference(_mk(dimname, vals))

    print("G-AX OK: IndexVariable.copy deep model "
          "(distinct identity + copied dims + source frame) "
          "sound on %d boundary + 2000 fuzz objects; prepatch `return self` "
          "violates res ≠ self as required." % (len(boundary),))
    return 0


if __name__ == "__main__":
    sys.exit(main())
