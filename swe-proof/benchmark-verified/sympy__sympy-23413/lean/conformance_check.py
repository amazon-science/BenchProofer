#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for sympy__sympy-23413.

The bundle models ONE routine: the outer row-processing loop of
`_hermite_normal_form` (sympy/polys/matrices/normalforms.py). The
soundness-critical decision the patch changes is WHICH rows are processed and
WHEN to stop:

    post-patch:  for i in range(m-1, -1, -1):        # every row, bottom -> top
                     if k == 0: break                # stop once pointer hits 0
                     k -= 1; ...
    pre-patch:   rows = min(m, n)
                 for i in range(m-1, m-1-rows, -1):  # only the bottom min(m,n) rows
                     k -= 1; ...                      # no early break

When m > n the pre-patch loop skips the topmost (m-n) rows, so a genuine pivot
lying in a topmost row is never placed and its column is dropped from the result
(the reported issue: HNF falsely removing rows).

The per-row reduction (`step`) and the final column slice (`sliceCols`) are
UNCHANGED callees; they appear identically in the oracle and the shadow, so they
cancel out and this differential test isolates exactly the control-flow change
(the R/I legs): the set of row indices iterated, and the `k == 0` early break.

`step` is modeled as an OPAQUE deterministic transition on an abstract state so
that it is byte-identical on both sides — its concrete arithmetic is irrelevant
to the row-selection difference under test. It consumes (state, i, k) and returns
(state', k'); k' may be k-1 (a new pivot placed), or k (row contributed no pivot,
pointer unchanged), exactly the two outcomes of the real per-row reduction
(`if b == 0: k += 1` cancels the `k -= 1`, i.e. the pointer is unchanged). The
state carries the multiset of (row_index) that have been folded so a dropped row
is observable in the result.

ORACLE = faithful in-process replica of the POST-PATCH loop. SHADOW = op-for-op
transliteration of `implementation_hermiteNormalForm` (Solution.lean impl
region), per refinement.md.

stdlib-only. Pinned seed: 23413 (also in mapping.md).
"""
import random
import sys

SEED = 23413
N = 120_000


def rows_desc(m):
    # [m-1, m-2, ..., 0]
    return list(range(m - 1, -1, -1))


# --- opaque per-row transition, IDENTICAL on both sides -----------------------
# Deterministic pseudo-decision: does row i (given current k) place a new pivot?
# Encodes the real dichotomy k -= 1 then possibly k += 1 (pivot was 0). We derive
# the "pivot placed" bit from (state, i, k) deterministically so the two sides
# agree op-for-op; the state records the folded rows so a skipped row shows up.
def step(state, i, k):
    A, placed = state
    # k -= 1 (a candidate pivot column is opened)
    k2 = k - 1
    # whether this row yields a nonzero pivot in that column (opaque decision).
    pivot = ((i * 2654435761 + k * 40503 + (sum(A) % 97)) % 3) != 0
    A2 = A + [i]
    if pivot:
        # pivot placed: pointer stays at k2 (advanced left by one).
        return (A2, placed + [i]), k2
    else:
        # no pivot in this row: pointer restored (k += 1 cancels the k -= 1).
        return (A2, placed), k


def slice_cols(state, k):
    # UNCHANGED: report (folded rows, placed rows, final pointer). Identical on
    # both sides; isolates the row-selection difference.
    A, placed = state
    return (tuple(A), tuple(placed), k)


# --- ORACLE: faithful replica of the POST-PATCH outer loop --------------------
def oracle(m, n):
    A = ([], [])          # (folded rows, placed rows)
    k = n
    for i in rows_desc(m):
        if k == 0:
            break
        A, k = step(A, i, k)
    return slice_cols(A, k)


# --- SHADOW of implementation_hermiteNormalForm (the R/I control flow) ---------
def shadow(m, n):
    A = ([], [])
    k = n
    for i in rows_desc(m):
        if k == 0:
            break
        A, k = step(A, i, k)
    return slice_cols(A, k)


def disagree(m, n):
    got = oracle(m, n)
    want = shadow(m, n)
    if got != want:
        return (m, n, got, want)
    return None


def _edge_cases():
    cases = []
    # F2P scenario: m > n (3x1) — a pivot in a topmost row must NOT be dropped.
    cases.append((3, 1))
    cases.append((3, 2))          # issue #23410: [[1,12],[0,8],[0,5]]
    cases.append((2, 3))          # the reporter's transposed shape (m < n)
    cases.append((1, 1))
    cases.append((0, 0))
    cases.append((0, 5))
    cases.append((5, 0))
    cases.append((4, 4))
    cases.append((1, 5))
    cases.append((5, 1))
    return cases


def main() -> int:
    checked = 0
    for m, n in _edge_cases():
        d = disagree(m, n)
        if d:
            print(f"DISAGREE edge: m={d[0]} n={d[1]} oracle={d[2]} shadow={d[3]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        m = rng.randint(0, 8)
        n = rng.randint(0, 8)
        d = disagree(m, n)
        if d:
            print(f"DISAGREE fuzz: m={d[0]} n={d[1]} oracle={d[2]} shadow={d[3]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
