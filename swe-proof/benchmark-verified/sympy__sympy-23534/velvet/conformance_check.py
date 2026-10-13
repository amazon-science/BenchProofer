#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-23534 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region (`buildSeq`)
              transliterated to Python over the *real* repo types, via the
              mapping.md bijection (`List String` ↔ tuple/list of name strings,
              `SymCls` ↔ class object). The A-tagged callee `buildName` is NOT
              substituted by its axiom model here; G-CONF isolates the R/I legs,
              so the per-element build runs the REAL repo callee
              (`symbols(name, cls=cls, **args)`, the unchanged single-name
              branch). The R/I content of the shadow is exactly: iterate the
              elements in order, recurse with `cls` PROPAGATED, and wrap with
              `type(names)`.
  * ORACLE  — `patch.diff`'s behaviour: the patched `sympy.core.symbol.symbols`
              applied at base_commit (the real correctness oracle, G-RESOLVE).

We compare the *class tag* of every produced leaf object (mapping.md §2) — the
sole property the fix changes and the F2P test observes. They must agree on
every input. Exit 0 iff zero disagreements; any disagreement is a mechanical
R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + sympy only.
The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

from sympy import symbols, Symbol, Wild
from sympy.core.function import Function

SEED = 23534
N_FUZZ = 100_000

_CLASSES = [Symbol, Function, Wild]


def _tag_tree(obj):
    """Map a produced object / nested tuple/list to a tree of class-name tags
    (the observable abstraction, mapping.md §2)."""
    if isinstance(obj, (tuple, list)):
        return (type(obj).__name__, tuple(_tag_tree(x) for x in obj))
    return type(obj).__name__


def shadow_build(names, cls):
    """The R/I shadow of buildSeq: the else-branch loop with `cls` propagated.
    The per-element build is the REAL single-name callee (A-tagged → run real
    callee). `result.append(symbols(name, cls=cls))` then `type(names)(result)`."""
    result = []
    for name in names:
        result.append(symbols(name, cls=cls))      # A-leg: real per-name callee
    return type(names)(result)


def oracle_build(names, cls):
    """patch.diff's behaviour: the patched symbols() on a sequence input. The
    harness applies patch.diff before this runs, so the imported symbols is
    the fixed one."""
    return symbols(names, cls=cls)


def fuzz_inputs(n, rng):
    letters = "abcdefghijklmnopqrstuvwxyz"

    def rand_name():
        kind = rng.randint(0, 2)
        if kind == 0:
            return "".join(rng.choice(letters) for _ in range(rng.randint(1, 3)))
        if kind == 1:
            return "%s:%d" % (rng.choice(letters), rng.randint(1, 3))
        lo = rng.randint(0, 20)
        return "%s:%s" % (letters[lo], letters[lo + rng.randint(1, 4)])

    # boundary cases first (plan §4.1 step 4): the exact issue input + variants
    yield (("q:2", "u:2"), Function)        # the FAIL_TO_PASS scenario
    yield (("q:2", "u:2"), Symbol)
    yield (("q:2", "u:2"), Wild)
    yield (("x", "y"), Function)
    yield (("a:d", "x:z"), Function)
    yield (["f", "g"], Function)            # list input (type(names) == list)
    yield (("x",), Function)                # singleton sequence
    yield (("f,g", "h"), Function)          # comma inside an element
    for cls in _CLASSES:
        yield (("a", "b", "c"), cls)

    for _ in range(n):
        k = rng.randint(1, 4)
        seq = tuple(rand_name() for _ in range(k))
        if rng.random() < 0.3:
            seq = list(seq)                 # exercise list container too
        cls = rng.choice(_CLASSES)
        yield (seq, cls)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for names, cls in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = _tag_tree(shadow_build(names, cls))
        oracle = _tag_tree(oracle_build(names, cls))
        if shadow != oracle:
            disagreements.append((names, cls.__name__, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for names, cls, sh, orc in disagreements:
            print("  names=%r cls=%s shadow=%r oracle=%r" % (names, cls, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of buildSeq agrees with patch.diff behaviour "
          "on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
