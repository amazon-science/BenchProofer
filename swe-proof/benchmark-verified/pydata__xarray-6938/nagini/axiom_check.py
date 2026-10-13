#!/usr/bin/env python3
"""G-AX executable soundness check for pydata__xarray-6938.

This bundle has NO consumed `@ContractOnly` axioms: the changed behaviour --
re-presenting a one-dimensional coordinate variable yields an INDEPENDENT
object rather than an alias of the receiver -- is modelled DEEPLY in model.py
via Nagini's permission discipline (the result is handed full write permission
to its own `dims` field while the receiver keeps only a fractional read
permission; an aliasing result cannot satisfy this).

What is validated here is therefore the **A-reference** obligation: that the
deep model (independent allocation, with the result's `dims` initially equal to
the receiver's and thereafter mutable without touching the receiver) matches the
REAL post-patch callee `xarray.IndexVariable.to_index_variable` (and the sibling
re-presentations `Variable.to_base_variable` / `Variable.to_index_variable`,
which already returned fresh objects). It runs the real callees in-container on
boundary + fuzz inputs and asserts every observation meets the modelled
behaviour:

    (1) result is a DISTINCT object from the receiver        (Result() is not self)
    (2) result initially carries the receiver's dim names     (ToSeq equality)
    (3) reassigning result.dims leaves receiver.dims unchanged (independent storage)

Imports only `xarray` itself -- the very module the gold patch edits; nothing
test-specific. Exit 0 iff every obligation holds.
"""
import random
import sys

import numpy as np
from xarray import IndexVariable, Variable


def _check_independence(orig, repres, new_dims_tuple, label):
    """Assert the modelled copy semantics on a real re-presentation result.

    `orig`    : the receiver variable
    `repres`  : orig.to_index_variable() / to_base_variable() (the real callee)
    `new_dims_tuple` : a fresh dims tuple to assign to the result
    """
    orig_dims_before = tuple(orig.dims)

    # (1) distinct object: never an alias of the receiver.
    assert repres is not orig, (
        "%s: re-presentation returned the receiver itself (alias); "
        "expected a distinct object" % label)

    # (2) same dimension names initially.
    assert tuple(repres.dims) == orig_dims_before, (
        "%s: result dims %r != receiver dims %r"
        % (label, tuple(repres.dims), orig_dims_before))

    # (3) independent storage: mutating the result's dims must not change the
    #     receiver's dims.
    repres.dims = new_dims_tuple
    assert tuple(orig.dims) == orig_dims_before, (
        "%s: mutating result.dims to %r changed receiver dims to %r "
        "(expected %r) -- aliasing bug"
        % (label, new_dims_tuple, tuple(orig.dims), orig_dims_before))
    assert tuple(repres.dims) == tuple(new_dims_tuple), (
        "%s: result.dims reassignment did not take effect" % label)


def main():
    # --- boundary: the exact F2P scenario (issue #6931) -------------------
    a = IndexVariable("x", ["a"])
    b = a.to_index_variable()
    assert a is not b, "F2P: IndexVariable.to_index_variable returned self"
    b.dims = ("y",)
    assert a.dims == ("x",), "F2P: original dims mutated to %r" % (a.dims,)

    # --- boundary: a handful of explicit 1-D index variables --------------
    boundary = [
        ("x", ["a"]),
        ("z", [0]),
        ("lev", list(range(11))),
        ("t", ["2020-01-01", "2020-01-02"]),
        ("k", [1.5, 2.5, 3.5]),
    ]
    for name, data in boundary:
        iv = IndexVariable(name, data)
        # IndexVariable.to_index_variable -- the patched callee.
        _check_independence(iv, iv.to_index_variable(), ("renamed",),
                            "IndexVariable.to_index_variable %r" % name)
        # Variable.to_base_variable / to_index_variable -- the sibling
        # re-presentations (already fresh; the patch only switched .dims to
        # ._dims, an identical-value read).
        v = Variable(name, np.asarray(data))
        _check_independence(v, v.to_base_variable(), ("rb",),
                            "Variable.to_base_variable %r" % name)
        _check_independence(v, v.to_index_variable(), ("ri",),
                            "Variable.to_index_variable %r" % name)

    # --- randomized fuzz over 1-D index variables -------------------------
    rng = random.Random(6938)
    names = ["x", "y", "z", "lev", "time", "lat", "lon", "k", "q"]
    for _ in range(2000):
        name = rng.choice(names)
        n = rng.randint(0, 12)
        # distinct integer labels keep the pandas.Index construction cheap.
        data = list(range(n))
        iv = IndexVariable(name, data)
        new_name = rng.choice([nm for nm in names if nm != name])
        _check_independence(iv, iv.to_index_variable(), (new_name,),
                            "fuzz IndexVariable.to_index_variable")

    print("G-AX OK: deep model (independent allocation; result.dims initially "
          "== receiver.dims; reassigning result.dims leaves receiver.dims "
          "unchanged) matches real xarray.IndexVariable.to_index_variable / "
          "Variable.to_base_variable / to_index_variable on the F2P scenario, "
          "5 boundary variables, and 2000 fuzz cases. No consumed axioms.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
