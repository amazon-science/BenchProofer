#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-23413 (nagini).

SHADOW: the impl region of model.py's `leftmost_pivot_column`, copied VERBATIM
below with the contract calls stripped (the Requires/Ensures block, the loop
`Invariant(...)` calls, and the three proof-only `Assert(...)` lines, one of
which invokes the proof lemma `pivot_count_monotone`). The `@Pure` helpers
(`valid_flags`, `pivot_count`, `pivot_count_monotone`) copy over as plain
functions with their contract calls stripped; `PSeq[int]` becomes a plain
Python list (indexing and `len` are identical). There are no `@ContractOnly`
callees in this bundle (the axioms region is empty).

ORACLE: the REAL patched repo function the model models per mapping.md —
`sympy.polys.matrices.normalforms._hermite_normal_form`. The gate applies
patch.diff to /testbed before this script runs and sets PYTHONPATH=/testbed;
this script applies nothing itself. The observable the model pins is the final
column marker `k`: the routine returns the columns from `k` to the right edge,
so its result's column count equals `n - k`.

TYPE BRIDGE (mapping.md section 2): the model abstracts the integer matrix to
its per-row pivot OUTCOMES. For a concrete matrix, `found[t]` (t = 0 is the
bottom row) is 1 iff the t-th-from-bottom row yields a nonzero pivot, and `n`
is the column count. The pivot outcome of each row is decided by the unchanged
extended-gcd column arithmetic; the bridge below reifies it by running a
faithful stdlib-only rendition of that unchanged per-row arithmetic
(extended gcd + column combinations, exactly mapping.md's abstraction map and
the same reification G-AX validated) to record each row's outcome flag. Rows
past the point where the marker reaches 0 are never examined and contribute
flag 0. The `found` list so produced satisfies the model's Requires by
construction (each entry is 0 or 1, `n >= 0`).

DIFF: for every input matrix, the shadow runs on the bridged `(found, n)` and
the real patched routine runs on the corresponding DomainMatrix over ZZ; they
disagree iff `n - shadow_k` differs from the real result's column count.

>= 1e5 Requires-satisfying inputs: 14 structured boundary matrices (the
reported input shapes, tall/wide/zero/rank-deficient, marker-hits-zero cases,
negative pivots) plus 100000 fuzz matrices over varied small shapes and signed
entries. Pinned fuzz seed: 234131.

Exit 0 iff zero disagreements; on disagreement prints the input matrix, the
bridged flags, and both outcomes, then exits 1. stdlib only (random;
hypothesis not needed).
"""
import json
import random
import sys

SEED = 234131
N_FUZZ = 100_000


# --- @Pure helpers from model.py, contracts stripped, PSeq -> list -----------

def valid_flags(s):
    """Every entry of `s` is a 0/1 pivot-outcome flag."""
    return all(s[t] == 0 or s[t] == 1 for t in range(len(s)))


def pivot_count(s, upto):
    """Number of pivot-yielding rows among the first `upto` rows of the
    bottom-to-top sequence `s` (each entry 0 or 1). Front-recursive on the
    suffix so a single unfold is available per loop step."""
    if upto == 0:
        return 0
    return s[upto - 1] + pivot_count(s, upto - 1)


def pivot_count_monotone(s, a, b):
    """Lemma: pivot_count is non-decreasing in its bound (a <= b)."""
    if a == b:
        return True
    return pivot_count_monotone(s, a, b - 1)


# --- the impl region of model.py, verbatim, contract calls stripped ----------

def leftmost_pivot_column(found, n):
    k = n
    i = 0
    while i < len(found):
        if k == 0:
            # Every column already holds a pivot; no further rows can help.
            # pivot_count is monotone, so the full count is still >= n.
            break
        c = found[i]
        if c == 1:
            k = k - 1
        i = i + 1
    return k


# --- bridge: matrix -> per-row pivot-outcome flags (mapping.md section 2) ----
# The flags are decided by the UNCHANGED per-row column arithmetic; the
# helpers below are a faithful stdlib rendition of that arithmetic (the same
# reification axiom_check.py validated against the real routine under G-AX).

def _gcdex(a, b):
    old_r, r = a, b
    old_s, s = 1, 0
    old_t, t = 0, 1
    while r != 0:
        q = old_r // r
        old_r, r = r, old_r - q * r
        old_s, s = s, old_s - q * s
        old_t, t = t, old_t - q * t
    x, y, g = old_s, old_t, old_r
    # mirror the repo's extended-gcd normalisation when a divides b
    if a != 0 and b % a == 0:
        y = 0
        x = -1 if a < 0 else 1
    return x, y, g


def _add_columns(M, i, j, a, b, c, d):
    for k in range(len(M)):
        e = M[k][i]
        M[k][i] = a * e + b * M[k][j]
        M[k][j] = c * e + d * M[k][j]


def bridge_found_flags(A):
    """Reify the model's abstract input for a concrete matrix: (found, n)
    where found[t] is the pivot-outcome flag of the t-th-from-bottom row.
    Runs the per-row reduction bottom-to-top over all rows; a row reached
    after the marker hits 0 is unexamined and flagged 0."""
    m = len(A)
    n = len(A[0]) if m else 0
    A = [row[:] for row in A]
    k = n
    found = []
    for i in range(m - 1, -1, -1):
        if k == 0:
            found.append(0)
            continue
        k -= 1
        for j in range(k - 1, -1, -1):
            if A[i][j] != 0:
                u, v, d = _gcdex(A[i][k], A[i][j])
                r, s = A[i][k] // d, A[i][j] // d
                _add_columns(A, k, j, u, v, -s, r)
        b = A[i][k]
        if b < 0:
            _add_columns(A, k, k, -1, 0, -1, 0)
            b = -b
        if b == 0:
            k += 1
            found.append(0)
        else:
            for j in range(k + 1, n):
                q = A[i][j] // b
                _add_columns(A, j, k, 1, -q, 0, 1)
            found.append(1)
    return found, n


# --- oracle: the REAL patched repo function ----------------------------------

def make_oracle():
    from sympy.polys.domains import ZZ
    from sympy.polys.matrices import DomainMatrix
    from sympy.polys.matrices.normalforms import _hermite_normal_form

    def real_retained_cols(A):
        m = len(A)
        n = len(A[0]) if m else 0
        dm = DomainMatrix([[ZZ(x) for x in row] for row in A], (m, n), ZZ)
        return _hermite_normal_form(dm).shape[1]

    return real_retained_cols


def check_one(real_retained_cols, A):
    found, n = bridge_found_flags(A)
    # Requires hold by construction
    assert valid_flags(found) and n >= 0
    shadow_k = leftmost_pivot_column(found, n)
    shadow_cols = n - shadow_k
    real_cols = real_retained_cols(A)
    if shadow_cols != real_cols:
        return ("DISAGREEMENT\n  A=%r\n  bridged found=%r n=%d\n"
                "  shadow: k=%d retained-cols=%d\n  real retained-cols=%d"
                % (A, found, n, shadow_k, shadow_cols, real_cols))
    return None


BOUNDARY = [
    [[1, 12], [0, 8], [0, 5]],     # reported shape: pivot in the top row
    [[0, 12], [1, 8], [0, 5]],     # pivot in the middle row
    [[0, 12], [0, 8], [1, 5]],     # pivot in the bottom row
    [[2, 7], [0, 0], [0, 0]],      # tall, single pivot in top row
    [[2, 7, 17, 29, 41], [3, 11, 19, 31, 43], [5, 13, 23, 37, 47]],  # wide
    [[-2, 1], [0, 1]],             # negative pivot
    [[5, 8, 12], [0, 0, 1]],       # wide 2x3
    [[1]],                         # 1x1
    [[0]],                         # zero 1x1
    [[1, 0], [0, 1], [0, 0]],      # identity-ish tall
    [[0, 0], [0, 0], [0, 0]],      # all-zero tall
    [[1], [0], [0]],               # tall single column
    [[1, 2, 3]],                   # single wide row
    [[1], [1], [1]],               # tall, every row a pivot (marker hits 0)
]


def main():
    real_retained_cols = make_oracle()

    checked = 0
    for A in BOUNDARY:
        err = check_one(real_retained_cols, A)
        if err:
            print(err)
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        m = rng.randint(1, 5)
        n = rng.randint(1, 5)
        A = [[rng.randint(-4, 4) for _ in range(n)] for _ in range(m)]
        err = check_one(real_retained_cols, A)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow leftmost_pivot_column == real patched routine's "
          "retained-column count on %d inputs (%d boundary + %d fuzz, seed %d)."
          % (checked, len(BOUNDARY), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
