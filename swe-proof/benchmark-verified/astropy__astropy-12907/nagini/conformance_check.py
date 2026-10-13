#!/usr/bin/env python3
"""G-CONF differential conformance check for astropy__astropy-12907 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Invariant/Assert) stripped and PSeq realized as an
immutable tuple shim. The @Pure helpers `zeros` / `expected_row` copy over as
plain functions (is_grid, whose body is a Forall quantifier used only inside
contracts, is realized as a bounded loop and used only to sanity-check
generated inputs). There are no @ContractOnly callees in this bundle.

ORACLE: the REAL patched repo function the model models per mapping.md —
`astropy.modeling.separable._cstack`, called with both operands already
2-D coord matrices (the branch under specification). The gate applies
patch.diff to /testbed before this script runs; PYTHONPATH=/testbed makes the
patched module importable.

Type bridge (mapping.md section 2): a 2-D float ndarray of 0/1 entries maps to
PSeq[PSeq[int]] with explicit row/column extents; the array's shape supplies
(lr, lc) and (rr, rc). The shadow's resulting sequence-of-rows compares against
the oracle's 2-D array elementwise after lifting the shadow rows to floats
(entries are copied, never computed, so int vs float carries no precision
concern).

Input domain: Requires demands well-formed matrices with non-negative extents.
Coord matrices in the repo always have at least one row and one column, and the
real combiner raises on zero-extent operands instead of returning a value, so
generation is restricted to extents >= 1 — the callee's operating domain.
Entries are drawn from {0, 1} (the coord-matrix alphabet) with a slice of
larger small ints mixed in (still Requires-satisfying; the operation copies
entries verbatim so the comparison stays exact).

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz pairs.
Pinned fuzz seed: 12907.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + numpy only.
"""
import json
import random
import sys

import numpy as np

SEED = 12907
N_FUZZ = 100_000


# --- PSeq shim: immutable sequence, the operations the impl region uses ------

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

    def __add__(self, other):
        return PSeq._wrap(self._t + other._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __hash__(self):
        return hash(self._t)


# --- pure helpers from model.py, contracts stripped ---------------------------

def zeros(n):
    if n == 0:
        return PSeq(0).take(0)
    return zeros(n - 1) + PSeq(0)


def is_grid(m, rows, cols):
    # model.py states this with a Forall quantifier; realized here as a
    # bounded loop (used only to sanity-check generated inputs).
    return len(m) == rows and all(len(m[k]) == cols for k in range(rows))


def expected_row(left, right, lr, lc, rr, rc, i):
    if i < lr:
        return left[i] + zeros(rc)
    return zeros(lc) + right[i - lr]


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def parallel_dependency_matrix(left, right, lr, lc, rr, rc):
    noutp = lr + rr
    result = PSeq(zeros(0)).take(0)  # type: PSeq
    i = 0
    while i < noutp:
        if i < lr:
            # upper row: left[i] then rc trailing zeros (right block empty).
            row = left[i] + zeros(rc)  # type: PSeq
        else:
            # lower row: lc leading zeros (left block empty) then right[i-lr].
            row = zeros(lc) + right[i - lr]
        old_result = result  # type: PSeq
        result = result + PSeq(row)
        i = i + 1
    return result


# --- bridge: ndarray <-> PSeq[PSeq[int]] --------------------------------------

def to_pseq(mat):
    return PSeq._wrap(PSeq._wrap(int(v) for v in row) for row in mat)


def pseq_to_lists(m):
    return [[m[i][j] for j in range(len(m[i]))] for i in range(len(m))]


def check_pair(cstack, left_rows, right_rows):
    """Run shadow and oracle on one (left, right) matrix pair; return an error
    string on disagreement, else None."""
    lr, lc = len(left_rows), len(left_rows[0])
    rr, rc = len(right_rows), len(right_rows[0])
    lp, rp = to_pseq(left_rows), to_pseq(right_rows)
    assert is_grid(lp, lr, lc) and is_grid(rp, rr, rc)  # Requires holds

    shadow = parallel_dependency_matrix(lp, rp, lr, lc, rr, rc)
    shadow_arr = np.array(pseq_to_lists(shadow), dtype=float)

    real = cstack(np.array(left_rows, dtype=float),
                  np.array(right_rows, dtype=float))
    real_arr = np.asarray(real, dtype=float)

    if shadow_arr.shape != real_arr.shape or not np.array_equal(shadow_arr, real_arr):
        return ("DISAGREEMENT\n  left=%r\n  right=%r\n  shadow=\n%r\n  real=\n%r"
                % (left_rows, right_rows, shadow_arr, real_arr))
    return None


def boundary_pairs():
    eye2 = [[1, 0], [0, 1]]
    eye3 = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
    ones2 = [[1, 1], [1, 1]]
    return [
        ([[1]], [[1]]),
        ([[1]], [[0]]),
        ([[0]], [[0]]),
        (eye2, eye2),                     # nested diagonal operand: the
        (ones2, eye2),                    # independence-preservation scenario
        (eye2, ones2),
        (eye3, eye2),
        (eye2, eye3),
        ([[1, 1], [0, 0]], [[0, 1], [1, 0]]),
        ([[1, 0, 1]], [[1], [0], [1]]),   # rectangular extremes
        ([[1]], eye3),
        (eye3, [[1]]),
        ([[2, 0], [0, 3]], [[5]]),        # non-binary ints: copied verbatim
    ]


def rand_matrix(rng, rmax=5, cmax=5):
    r = rng.randint(1, rmax)
    c = rng.randint(1, cmax)
    if rng.random() < 0.05:
        # occasional non-binary small ints (still Requires-satisfying)
        return [[rng.randint(0, 3) for _ in range(c)] for _ in range(r)]
    return [[rng.randint(0, 1) for _ in range(c)] for _ in range(r)]


def main():
    from astropy.modeling.separable import _cstack  # REAL patched callee

    checked = 0
    for left_rows, right_rows in boundary_pairs():
        err = check_pair(_cstack, left_rows, right_rows)
        if err:
            print(err)
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        err = check_pair(_cstack, rand_matrix(rng), rand_matrix(rng))
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real combiner on %d inputs "
          "(%d boundary + %d fuzz, seed %d)."
          % (checked, len(boundary_pairs()), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
