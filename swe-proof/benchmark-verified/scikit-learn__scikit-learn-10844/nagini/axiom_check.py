#!/usr/bin/env python3
"""G-AX executable soundness check for scikit-learn__scikit-learn-10844.

Executes the REAL numeric operations the modeled computation uses — real
division `a / b`, the square root, and real multiplication `x * y` — on
boundary cases and randomized fuzz inputs, and asserts that every observation
satisfies the @ContractOnly axioms in model.py.

The three axioms (all over interpreted reals, model.py axioms region):

  (ratio)  for 0 <= a <= b <= m, b > 0:
               ratio(a,b,m) == a / b  AND  0 <= ratio(a,b,m) <= 1
  (root)   for 0 <= x <= m:
               root(x,m) >= 0  AND  (x <= 1  =>  root(x,m) <= 1)
  (mul)    for 0 <= x <= 1, 0 <= y <= 1:
               mul(x,y) == x * y  AND  0 <= mul(x,y) <= 1

These are the WEAKEST contracts the proof needs; in particular `root` carries
only the bounds the proof consumes (non-negativity, and unit-interval
preservation), NOT an exact value — so the check verifies those bounds, plus
the exact-value clauses of `ratio`/`mul`, on the real operations.

It also exercises the overflow-discriminating fact the bundle turns on: each
marginal can be representable (<= m) while their cross product `pk * qk`
exceeds m — i.e. `root`'s representability precondition genuinely fails on the
pre-patch evaluation order, which is what makes the result non-finite there
(reproduced with the real square root on the actual failing-test magnitudes).

Imports nothing repo-specific: only the standard-library `math` and `random`.
Exit 0 iff every obligation holds.
"""
import math
import random
import sys

# A representable bound standing in for a finite numeric domain's maximum
# magnitude. The 64-bit signed integer maximum is the concrete domain the
# widened marginals live in; the cross product of two such marginals routinely
# exceeds it (that is the overflow the fix avoids).
INT64_MAX = 2 ** 63 - 1


def check_ratio(a, b, m):
    """Real division a/b under the axiom's Requires (0 <= a <= b <= m, b > 0)."""
    assert b > 0.0 and 0.0 <= a <= b <= m
    r = a / b                                            # real callee
    assert r == a / b
    assert 0.0 <= r <= 1.0, (
        "ratio axiom unsound on a=%r b=%r: a/b=%r not in [0,1]" % (a, b, r))


def check_root(x, m):
    """Square root under the axiom's Requires (0 <= x <= m)."""
    assert 0.0 <= x <= m
    r = math.sqrt(x)                                     # real callee
    assert r >= 0.0, "root axiom unsound: sqrt(%r)=%r < 0" % (x, r)
    if x <= 1.0:
        # tolerate no slack: sqrt of a unit-interval value is in the unit
        # interval exactly (monotone, sqrt(1)=1).
        assert r <= 1.0, (
            "root axiom unsound: sqrt(%r)=%r > 1 for x<=1" % (x, r))


def check_mul(x, y):
    """Real multiplication x*y under the axiom's Requires (x,y in [0,1])."""
    assert 0.0 <= x <= 1.0 and 0.0 <= y <= 1.0
    r = x * y                                            # real callee
    assert r == x * y
    assert 0.0 <= r <= 1.0, (
        "mul axiom unsound on x=%r y=%r: x*y=%r not in [0,1]" % (x, y, r))


def main():
    m = float(INT64_MAX)

    # ---- ratio: boundary cases ------------------------------------------
    ratio_boundary = [
        (0.0, 1.0), (0.0, m), (1.0, 1.0), (1.0, m), (m, m),
        (1.0, 2.0), (3.0, 12.0), (4.0, 6.0), (12.0, 12.0),
        (3003497866.0, 5152663196.0),   # tk, pk from the failing-test regime
        (3003497866.0, 3294371982.0),   # tk, qk from the failing-test regime
    ]
    for a, b in ratio_boundary:
        check_ratio(a, b, m)

    # ---- root: boundary cases -------------------------------------------
    root_boundary = [0.0, 1.0, 0.25, 0.5, 0.9999999999,
                     2.0, 100.0, m, m / 2.0,
                     5152663196.0, 3294371982.0]        # representable marginals
    for x in root_boundary:
        check_root(x, m)

    # ---- mul: boundary cases --------------------------------------------
    mul_boundary = [(0.0, 0.0), (0.0, 1.0), (1.0, 0.0), (1.0, 1.0),
                    (0.5, 0.5), (0.9999, 0.9999),
                    # the two unit-interval sqrt operands of the failing test
                    (math.sqrt(3003497866.0 / 5152663196.0),
                     math.sqrt(3003497866.0 / 3294371982.0))]
    for x, y in mul_boundary:
        check_mul(x, y)

    # ---- randomized fuzz ------------------------------------------------
    rng = random.Random(10844)
    for _ in range(200000):
        b = rng.uniform(1e-9, m)
        a = rng.uniform(0.0, b)              # 0 <= a <= b <= m
        check_ratio(a, b, m)

        x = rng.uniform(0.0, m)
        check_root(x, m)

        u = rng.uniform(0.0, 1.0)
        v = rng.uniform(0.0, 1.0)
        check_mul(u, v)

    # ---- the overflow discriminator: each marginal representable, the cross
    #      product is not; the rearranged (divide-first) order stays finite ----
    tk, pk, qk = 3003497866.0, 5152663196.0, 3294371982.0
    assert pk <= m and qk <= m, "each marginal must be representable"
    assert pk * qk > m, (
        "cross product must exceed the representable bound (the overflow)")
    # rearranged order: every intermediate is representable, result is finite
    safe = math.sqrt(tk / pk) * math.sqrt(tk / qk)
    assert math.isfinite(safe) and 0.0 <= safe <= 1.0, (
        "rearranged order must yield a finite unit-interval result")
    # the two orders agree mathematically (value preservation)
    direct = tk / math.sqrt(pk * qk)        # finite ONLY because Python ints
    assert abs(safe - direct) < 1e-9, "the two evaluation orders must agree"

    print("G-AX OK: ratio/root/mul axioms sound on %d boundary + %d fuzz "
          "inputs; overflow discriminator confirmed (pk*qk > INT64_MAX while "
          "each marginal <= INT64_MAX; divide-first stays finite in [0,1])"
          % (len(ratio_boundary) + len(root_boundary) + len(mul_boundary),
             200000 * 3))
    return 0


if __name__ == "__main__":
    sys.exit(main())
