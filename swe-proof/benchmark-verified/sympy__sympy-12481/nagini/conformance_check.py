#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-12481 (nagini).

SHADOW: the impl region of model.py's `compose_cycles`, copied VERBATIM below
with the contract calls (Invariant/Assert) stripped. The `ToSeq(...)` snapshot
assignments the impl region takes for its (stripped) assertions are kept
verbatim and realized by a `ToSeq` -> tuple shim; `PSeq` is a plain-tuple
constructor shim (both snapshots are read-only captures, so the shims only
need immutability and equality). The @Pure helper `swap_val` copies over as a
plain function. There are no @ContractOnly callees in this bundle.

ORACLE: the REAL patched repo callee the model models per mapping.md — the
cyclic-form construction `Permutation([[a, b], [c, d]], size=n).array_form`
from `sympy.combinatorics.permutations`. The gate applies patch.diff to
/testbed before this script runs; PYTHONPATH=/testbed makes the patched
package importable.

Type bridge (mapping.md section 2): the model's four int parameters (a, b) and
(c, d) are the two GENUINE two-element cycles of a cyclic-form input, applied
left to right over the n points 0..n-1; the model's List[int] result is the
array form (`.array_form`, a list of ints of length n — `size=n` extends,
never truncates, since every named point is < n). The comparison is exact
int-list equality; no numeric abstraction is involved.

Input domain: exactly the model's Requires — n >= 1, all four points in
[0, n), a != b within the first cycle, c != d within the second. The two
cycles MAY share points with each other (including coinciding entirely);
those shared-point inputs are deliberately well represented in the fuzz mix.

>= 1e5 Requires-satisfying inputs: exhaustive over all (n, a, b, c, d) with
n <= 6 (1484 cases, every shared-point configuration of the touched points)
+ boundary cases + fuzz to a total of 100000+. Pinned fuzz seed: 124810.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys
from itertools import product
from typing import List

SEED = 124810
N_TOTAL = 100_000


# --- shims for the sequence snapshots the impl region takes -------------------

def ToSeq(lst):
    """Immutable snapshot of a list's contents."""
    return tuple(lst)


def PSeq(*items):
    """Immutable sequence literal."""
    return tuple(items)


# --- @Pure helper from model.py, contracts stripped ---------------------------

def swap_val(x: int, a: int, b: int) -> int:
    """Image of point x under the swap (a b): a and b trade places, every
    other point keeps its value."""
    if x == a:
        return b
    if x == b:
        return a
    return x


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def compose_cycles(n: int, a: int, b: int, c: int, d: int) -> List[int]:
    """Array form of the composition of the swap (a b) then the swap (c d) over
    the n points 0..n-1, applied left to right."""
    # Build the identity array 0..n-1 (the points in their original order).
    result = []  # type: List[int]
    j = 0
    while j < n:
        old_seq = ToSeq(result)  # type: ignore  # PSeq[int] snapshot
        result.append(j)
        j = j + 1
    # Apply the first swap (a b) point-wise, then the second swap (c d).
    i = 0
    while i < n:
        prev = ToSeq(result)  # type: ignore  # PSeq[int] snapshot
        result[i] = swap_val(i, a, b)
        i = i + 1
    i = 0
    while i < n:
        prev2 = ToSeq(result)  # type: ignore  # PSeq[int] snapshot
        new_val = swap_val(result[i], c, d)  # type: int
        result[i] = new_val
        i = i + 1
    return result


# --- differential driver -------------------------------------------------------

def check_case(Permutation, n, a, b, c, d):
    """Run shadow and oracle on one Requires-satisfying input; return an error
    string on disagreement, else None."""
    shadow = compose_cycles(n, a, b, c, d)
    try:
        real = list(Permutation([[a, b], [c, d]], size=n).array_form)
    except Exception as exc:  # in-domain input must not raise
        return ("DISAGREEMENT (oracle raised)\n  input: n=%d a=%d b=%d c=%d d=%d"
                "\n  shadow=%r\n  real raised %s: %s"
                % (n, a, b, c, d, shadow, type(exc).__name__, exc))
    if shadow != real:
        return ("DISAGREEMENT\n  input: n=%d a=%d b=%d c=%d d=%d"
                "\n  shadow=%r\n  real=%r" % (n, a, b, c, d, shadow, real))
    return None


def boundary_cases():
    """Hand-picked Requires-satisfying corners: smallest n, coinciding cycles,
    cycles sharing exactly one point (in each slot pairing), fully disjoint
    cycles, and points at the ends of the range."""
    return [
        (2, 0, 1, 0, 1),      # smallest n; the two cycles coincide
        (2, 0, 1, 1, 0),      # coincide up to written order
        (3, 0, 1, 0, 2),      # share the first-named point
        (3, 0, 1, 2, 0),      # shared point in opposite slots
        (3, 1, 0, 0, 2),      # shared point, first cycle reversed
        (3, 0, 1, 1, 2),      # chain: second cycle starts where first ends
        (4, 0, 1, 2, 3),      # fully disjoint
        (4, 3, 2, 1, 0),      # disjoint, descending order
        (4, 0, 3, 0, 3),      # coinciding cycles at the range ends
        (5, 0, 4, 4, 0),      # range-end points, opposite written order
        (5, 2, 3, 3, 2),      # inverse pair: composition is the identity
        (7, 0, 6, 3, 4),      # mixed extremes and middle points
    ]


def main():
    # REAL patched callee (mapping.md section 1) — importable from /testbed.
    from sympy.combinatorics.permutations import Permutation

    checked = 0

    # Exhaustive over the model's Requires domain for n <= 6: every placement
    # of the two two-element cycles over up to 6 points, including all
    # shared-point configurations.
    exhaustive = 0
    for n in range(1, 7):
        for a, b, c, d in product(range(n), repeat=4):
            if a == b or c == d:
                continue
            err = check_case(Permutation, n, a, b, c, d)
            if err:
                print(err)
                return 1
            exhaustive += 1
    checked += exhaustive

    for n, a, b, c, d in boundary_cases():
        err = check_case(Permutation, n, a, b, c, d)
        if err:
            print(err)
            return 1
        checked += 1

    # Fuzz over larger sizes until >= N_TOTAL inputs overall. Half the draws
    # force the two cycles to share a point (the interesting overlap regime);
    # the rest are unconstrained across the domain.
    rng = random.Random(SEED)
    n_fuzz = N_TOTAL - checked
    for k in range(n_fuzz):
        n = rng.randint(2, 30)
        a = rng.randint(0, n - 1)
        b = rng.randint(0, n - 1)
        while b == a:
            b = rng.randint(0, n - 1)
        if k % 2 == 0:
            # force a shared point between the cycles
            c = a if rng.random() < 0.5 else b
        else:
            c = rng.randint(0, n - 1)
        d = rng.randint(0, n - 1)
        while d == c:
            d = rng.randint(0, n - 1)
        err = check_case(Permutation, n, a, b, c, d)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real cyclic-form construction on %d "
          "inputs (%d exhaustive n<=6 + %d boundary + %d fuzz, seed %d)."
          % (checked, exhaustive, len(boundary_cases()), n_fuzz, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
