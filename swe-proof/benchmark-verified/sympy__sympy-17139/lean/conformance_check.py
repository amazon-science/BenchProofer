#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for sympy__sympy-17139.

The bundle models ONE routine: `_f`, the per-node rewrite that `_TR56` maps over
an expression tree (sympy/simplify/fu.py). Given a candidate expression `rv`, `_f`
returns:

    post-patch:  rv                    if not is_matching(rv)
                 rv                    elif not exp_is_real(rv)     # the added guard
                 transform(rv)         else

    pre-patch:   rv                    if not is_matching(rv)
                 transform(rv)         else                        # no realness guard

The soundness-critical decision the patch changes is the middle branch: a
matching power with a NON-real exponent must be returned unchanged (post-patch)
rather than passed to `transform` (pre-patch, which in reality crashes on the
invalid complex order comparison).

The structural matching test, the realness query, and the rewrite body are
UNCHANGED operations; they appear identically in the oracle and the shadow, so
they cancel out and this differential test isolates exactly the R leg — the added
realness guard.

An expression is modeled as a triple `(is_matching: bool, exp_real: bool,
tval: int)`: the two booleans are exactly what `is_matching` / `exp_is_real`
observe, and `transform` maps the expression to a distinct tag `("T", tval)` so a
transformed result is observably different from the untouched expression.

ORACLE = faithful in-process replica of the POST-PATCH `_f` decision tree.
SHADOW = op-for-op transliteration of `implementation_powerRewrite`
(Solution.lean impl region), per refinement.md.

stdlib-only. Pinned seed: 17139 (also in mapping.md).
"""
import random
import sys

SEED = 17139
N = 120_000


def is_matching(rv):
    # Unchanged callee model: byte-identical between oracle and shadow.
    return rv[0]


def exp_is_real(rv):
    # Unchanged callee model: byte-identical between oracle and shadow.
    return rv[1]


def transform(rv):
    # Unchanged callee model: the exponent-driven rewrite body. Produces a value
    # observably distinct from the untouched expression (so a wrongly-applied
    # transform is detectable).
    return ("T", rv[2])


# --- ORACLE: faithful replica of the POST-PATCH _f decision tree --------------
def oracle(rv):
    if not is_matching(rv):
        return rv
    if not exp_is_real(rv):
        return rv
    return transform(rv)


# --- SHADOW of implementation_powerRewrite (the R leg) ------------------------
# Mirrors Solution.lean impl region exactly: guarded early-return chain.
def shadow(rv):
    if not is_matching(rv):
        return rv
    if not exp_is_real(rv):
        return rv
    return transform(rv)


def disagree(rv):
    got = oracle(rv)
    want = shadow(rv)
    if got != want:
        return (rv, got, want)
    return None


def _edge_cases():
    cases = []
    # non-matching expression -> unchanged (regardless of exp_real).
    cases.append((False, True, 1))
    cases.append((False, False, 2))
    # matching power with a REAL exponent -> transformed.
    cases.append((True, True, 3))
    # F2P scenario: matching power with a NON-real exponent -> unchanged.
    cases.append((True, False, 4))
    # matching power, non-real exponent, transform would coincide with rv's tval
    # namespace but stays distinct due to the ("T", .) tag.
    cases.append((True, False, 0))
    return cases


def _rand_case(rng):
    return (rng.random() < 0.5, rng.random() < 0.5, rng.randint(0, 50))


def main() -> int:
    checked = 0
    for rv in _edge_cases():
        d = disagree(rv)
        if d:
            print(f"DISAGREE edge: oracle={d[1]} shadow={d[2]} rv={d[0]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        rv = _rand_case(rng)
        d = disagree(rv)
        if d:
            print(f"DISAGREE fuzz: oracle={d[1]} shadow={d[2]} rv={d[0]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
