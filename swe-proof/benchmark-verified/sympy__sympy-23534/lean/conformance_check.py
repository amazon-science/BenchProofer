#!/usr/bin/env python
"""G-CONF for sympy__sympy-23534.

Differential test of the R/I legs of `implementation_symbols` against the
PATCHED sympy `symbols` (the gate git-applies the gold patch first, so
`sympy.symbols` here is the fixed code).

Modeled (R/I) behavior: when the `names` argument is a (possibly nested)
sequence of name-specs, the result mirrors the nesting shape, and the requested
target class `cls` reaches EVERY leaf object — including objects produced from
tokens nested below one or more sequence layers.

Shadow (this file): replicate the dispatch + recursion of the modeled impl in
Python — recurse over each element of a sequence THREADING `cls` (R legs), and
for a single string token build the leaf under the threaded class via the real
repo single-token path `symbols(token, cls=cls)` (the I base case — the token
path is unchanged by the fix). Compare the per-leaf class-shape of the shadow
against what the patched `symbols` produces on the same nested input.

stdlib + sympy only. Exit 0 iff zero disagreements over >=1e5 fuzzed inputs.
"""
import random
import sys

import sympy
from sympy import symbols, Symbol, Function, Wild, Dummy

SEED = 23534
N = 100_000

# Target classes the caller may request (mapping.md: ClassId tag).
CLASSES = [Symbol, Function, Wild, Dummy]
# Single tokens that the unchanged string path turns into exactly one object
# (no range syntax, so the leaf is a single constructed object).
TOKENS = ["x", "y", "z", "f", "g", "h", "a", "abc", "q0", "u1", "alpha"]


def classes_of(obj):
    """Row-major (flattened) list of the *classes* of every leaf object in a
    possibly-nested sympy result container, mirroring nesting via recursion."""
    if isinstance(obj, (tuple, list, set)):
        out = []
        for el in obj:
            out.extend(classes_of(el))
        return out
    return [type(obj)]


def shadow_classes(names, cls):
    """Per-leaf classes produced by the modeled impl: recurse threading `cls`;
    a single token delegates to the real repo construction path."""
    if isinstance(names, str):
        # A-reference leaf: the unchanged token path, under the requested class.
        return classes_of(symbols(names, cls=cls))
    out = []
    for nm in names:
        out.extend(shadow_classes(nm, cls))  # R leg: thread cls into recursion
    return out


def oracle_classes(names, cls):
    """Per-leaf classes the patched `symbols` emits."""
    return classes_of(symbols(names, cls=cls))


def rand_spec(rng, depth):
    """A random (possibly nested) name-spec: a token, or a sequence of specs."""
    if depth <= 0 or rng.random() < 0.4:
        return rng.choice(TOKENS)
    n = rng.randint(1, 4)
    seq = [rand_spec(rng, depth - 1) for _ in range(n)]
    # vary the container type (tuple/list) — set drops order/dupes, skip it for
    # a stable per-leaf comparison.
    return tuple(seq) if rng.random() < 0.5 else list(seq)


def main():
    rng = random.Random(SEED)
    disagreements = 0
    checked = 0
    for i in range(N):
        cls = rng.choice(CLASSES)
        # ensure at least one sequence layer so the recursion (the fix site) is
        # exercised; wrap a bare token in a 1-tuple.
        spec = rand_spec(rng, rng.randint(1, 3))
        if isinstance(spec, str):
            spec = (spec,)
        try:
            shadow = shadow_classes(spec, cls)
            oracle = oracle_classes(spec, cls)
        except Exception as e:  # both paths should agree on validity too
            print(f"[exc] spec={spec!r} cls={cls.__name__}: {e}", file=sys.stderr)
            disagreements += 1
            if disagreements > 20:
                break
            continue
        checked += 1
        if shadow != oracle:
            disagreements += 1
            if disagreements <= 20:
                print(f"[mismatch] spec={spec!r} cls={cls.__name__}\n"
                      f"  shadow={[c.__name__ for c in shadow]}\n"
                      f"  oracle={[c.__name__ for c in oracle]}", file=sys.stderr)
    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements / {checked} checked", file=sys.stderr)
        sys.exit(1)
    print(f"G-CONF OK: 0 disagreements / {checked} checked (seed={SEED})")
    sys.exit(0)


if __name__ == "__main__":
    main()
