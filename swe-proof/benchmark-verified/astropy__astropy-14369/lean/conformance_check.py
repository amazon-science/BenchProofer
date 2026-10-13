#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of implementation_divChain
against the patch.diff behaviour (the post-patch left-associative division
chain reduction of the CDS grammar).

The impl region is NOT all-A-tagged (it is the R/I left-fold structure). The
A-reference op (the unit `*`/`/`/`⁻¹` algebra) is left as the REAL carrier — the
free-abelian-group exponent vector that a `CompositeUnit` reduces to. The shadow
therefore reproduces the post-patch reduction op-for-op:

    acc = head; for u in rest: acc = acc / u; return acc

We assert zero disagreements vs an independent reconstruction of the patched
grammar's `division_of_units` reduction over >=10^5 fuzzed inputs spanning
single-term chains, the single-`/x` inverse case, and long chains.

Units are represented by their base-exponent vectors (the only observable of a
parsed unit value): `*` adds, `/` subtracts, `⁻¹` negates. exit 0 iff zero
disagreements. stdlib-only.
"""
import random
import sys
from collections import defaultdict

SEED = 14369
N = 120_000
NBASE = 6


def mul(a, b):
    out = defaultdict(int)
    for k, v in a.items():
        out[k] += v
    for k, v in b.items():
        out[k] += v
    return {k: v for k, v in out.items() if v != 0}


def inv(a):
    return {k: -v for k, v in a.items()}


def div(a, b):
    return mul(a, inv(b))


def norm(a):
    return tuple(sorted((k, v) for k, v in a.items() if v != 0))


def shadow(head, rest):
    """R/I shadow of implementation_divChain: left fold, acc := acc / u."""
    acc = dict(head)
    for u in rest:
        acc = div(acc, u)              # REAL unit `/` (A-reference carrier)
    return norm(acc)


def patched_reduce(head, rest):
    """Independent reconstruction of the POST-patch grammar reduction.

    Post-patch `division_of_units : combined_units DIVISION unit_expression`
    with `p[0] = p[1] / p[3]` is left-associative, so a chain
    `head / r0 / r1 / ... / rk` reduces to `(((head / r0) / r1) ...) / rk`,
    i.e. `head` divided by the product of the trailing terms."""
    prod = {}
    for u in rest:
        prod = mul(prod, u)
    return norm(div(head, prod))


def prepatch_reduce(head, rest):
    """The PRE-patch (right-associative) reduction, for a sanity assertion that
    the test is discriminating (NOT compared against the shadow)."""
    if not rest:
        return norm(head)
    # right-recursive: head / (r0 / (r1 / ... / rk))
    acc = dict(rest[-1])
    for u in reversed(rest[:-1]):
        acc = div(u, acc)
    return norm(div(head, acc))


def rand_unit(rng):
    d = {}
    for i in range(NBASE):
        e = rng.randint(-3, 3)
        if e:
            d[i] = e
    return d


def main() -> int:
    rng = random.Random(SEED)
    disagreements = 0
    examples = []

    # Deterministic boundary cases first.
    fixed = [
        ({}, []),                                   # dimensionless, no division
        ({0: 1}, []),                               # single term, no division
        ({}, [{0: 1}]),                             # /x  -> x^-1 (the len==2 case)
        ({0: 1}, [{1: 1}]),                         # A/B
        ({0: 1}, [{1: 1}, {2: 1}]),                 # A/B/C  (the issue's shape)
        ({2: 1}, [{0: 1}, {1: 1}, {3: 2}]),         # J/m/s/kpc2 analogue
        ({0: 1}, [{0: 1}, {0: 1}]),                 # repeated base -> cancellation
    ]

    cases = list(fixed)
    for _ in range(N):
        head = rand_unit(rng)
        k = rng.randint(0, 8)
        rest = [rand_unit(rng) for _ in range(k)]
        cases.append((head, rest))

    # discriminating-test guard: confirm at least one case where pre != post.
    discriminating = False
    for head, rest in cases:
        got = shadow(head, rest)
        want = patched_reduce(head, rest)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append((head, rest, got, want))
        if not discriminating and prepatch_reduce(head, rest) != want:
            discriminating = True

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for h, r, g, w in examples:
            print(f"  head={h} rest={r} shadow={g} patched={w}")
        return 1
    if not discriminating:
        print("G-CONF FAIL: test not discriminating (pre==post on all cases)")
        return 1

    print(f"G-CONF OK: {len(cases)} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
