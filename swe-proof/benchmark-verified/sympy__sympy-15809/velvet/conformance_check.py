#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-15809 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing the observable result:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python. The A-tagged callee `processArgs` is left as the REAL
              repo pipeline (mapping.md §3.1): we re-run the unchanged
              _new_args_filter / _collapse_arguments / _find_localzeros chain to
              obtain the surviving-member set, then apply the MODELED
              count-driven dispatch (the R/I legs A4-A6 of refinement.md):
                  short-circuit (absorbing elt)  -> cls.zero
                  0 survivors                    -> cls.identity
                  1 survivor                     -> that member verbatim
                  >=2 survivors                  -> the built Max/Min object
  * ORACLE  — patch.diff's behaviour: the patched constructor `cls(*raw)` itself
              (the real correctness oracle; the harness has applied patch.diff at
              base_commit before this runs, G-RESOLVE).

They must agree (structural sympy `==`) on every input. The empty input is the
discriminating case: SHADOW reaches the identity leg via the real pipeline,
ORACLE returns `cls()` — under the pre-patch code ORACLE raised, so agreement
witnesses the fix. Exit 0 iff zero disagreements.

Runs in-container (the prebuilt SWE-Bench instance image). Imports only sympy.
The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

from sympy import Max, Min, Symbol, Integer
from sympy.core.operations import ShortCircuit

SEED = 15809
N_FUZZ = 100_000


def real_survivors(cls, raw):
    """Re-run the UNCHANGED normalisation chain (miscellaneous.py:347-360) and
    return the surviving-member frozenset, or None on ShortCircuit. This is the
    A-tagged callee `processArgs` left as the real repo pipeline."""
    args = (a for a in raw)
    try:
        args = frozenset(cls._new_args_filter(args))
    except ShortCircuit:
        return None
    args = cls._collapse_arguments(args, **{})
    args = cls._find_localzeros(args, **{})
    return args


def shadow_result(cls, raw):
    """The R/I count-driven dispatch of constructMinMax, transliterated."""
    surv = real_survivors(cls, raw)
    if surv is None:
        return cls.zero
    surv = list(surv)
    if len(surv) == 0:
        return cls.identity
    if len(surv) == 1:
        return surv[0]
    return cls(*surv)            # build the extremum object over the survivors


def oracle_result(cls, raw):
    """patch.diff behaviour: the patched constructor applied directly."""
    return cls(*raw)


def fuzz_inputs(n, rng):
    syms = [Symbol("a%d" % i, real=True) for i in range(6)]
    ints = [Integer(k) for k in range(-3, 4)]
    pool = syms + ints
    # boundary cases first (plan §4.1 step 4): the empty call is the fix
    yield []
    for s in syms:
        yield [s]                # single survivor
    yield [syms[0], syms[1]]     # two distinct incomparable -> built object
    yield [syms[0], syms[0]]     # duplicate -> collapses to one
    yield [Integer(1), Integer(2), Integer(3)]   # comparable -> one survivor
    yield [syms[0], syms[1], syms[2], syms[0]]
    for _ in range(n):
        k = rng.randint(0, 5)
        yield [rng.choice(pool) for _ in range(k)]


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for cls in (Max, Min):
        for raw in fuzz_inputs(N_FUZZ // 2, rng):
            count += 1
            try:
                shadow = shadow_result(cls, raw)
            except Exception as e:           # noqa: BLE001
                shadow = ("EXC", type(e).__name__)
            try:
                oracle = oracle_result(cls, raw)
            except Exception as e:           # noqa: BLE001
                oracle = ("EXC", type(e).__name__)
            if shadow != oracle:
                disagreements.append((cls.__name__, raw, shadow, oracle))
                if len(disagreements) >= 5:
                    break
        if disagreements:
            break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for name, raw, sh, orc in disagreements:
            print("  %s(*%r) shadow=%r oracle=%r" % (name, raw, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of constructMinMax agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
