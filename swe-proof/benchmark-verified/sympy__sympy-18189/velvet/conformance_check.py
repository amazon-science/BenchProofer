#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-18189 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's `reorderSolutions` impl
              region, transliterated to Python over the real repo types: build the
              permutation `order` from `(syms, var)`, call the A-tagged callee
              `baseSolve` (the UNCHANGED recursive `diophantine(eq, param,
              permute=permute)` with syms=None — NOT substituted by a model; the
              bundle's A content is opaque, validated by G-AX, so it is out of
              G-CONF's R/I scope), then apply `reorderAll order` (the per-tuple
              positional gather + set build, the I op the change preserves).
              The forwarded `permute` is the content of the fix; the shadow
              forwards it exactly as the gold patch does.
  * ORACLE  — `patch.diff`'s behaviour: the gold-patched
              `diophantine(eq, syms=syms, permute=permute)` itself, called on the
              same inputs (the real correctness oracle, G-RESOLVE — the harness
              applies patch.diff before this runs).

They must agree as SETS of solution tuples (the observation `test_diophantine`
makes) for every (eq, syms, permute) where the requested order differs from the
canonical one (the only inputs within the modeled branch). Exit 0 iff zero
disagreements; any disagreement is a mechanical R/I-fidelity counterexample.

The symbolic solver is a pure function of (eq, permute), so identical (eq, syms,
permute) triples are MEMOIZED: ≥10⁵ generated triples reduce to the far smaller
set of distinct triples actually solved, keeping the oracle within the container
budget (mapping.md §4). Runs in-container (the prebuilt SWE-Bench instance image
with patch.diff applied), stdlib + sympy only. The fuzz seed is pinned.
"""
import random
import sys

SEED = 18189
N_FUZZ = 120_000


def build():
    from sympy import symbols
    from sympy.solvers.diophantine import diophantine
    from sympy.core.compatibility import default_sort_key

    t = symbols("t", integer=True)
    x, y, z = symbols("x y z", integer=True)

    def perm_and_var(eq, syms):
        """Reproduce the branch's own preamble: canonical var order, the filtered
        syms, and (if the reorder branch is taken) the permutation `order`."""
        var = list(eq.expand(force=True).free_symbols)
        var.sort(key=default_sort_key)
        syms_f = [i for i in syms if i in var]
        if syms_f == var or not syms_f:
            return None                      # reorder branch NOT entered
        d = dict(zip(syms_f, range(len(syms_f))))
        order = [d[i] for i in var]
        return var, order

    def shadow(eq, syms, permute):
        """R/I shadow: reorderAll order (baseSolve permute). baseSolve is the
        REAL unchanged recursive solve with syms=None; reorderAll is the
        per-tuple positional gather, transliterated. Classified into the
        observable-outcome domain (set vs raised-exception class) so a callee
        that raises is compared faithfully against the oracle rather than counted
        as a spurious disagreement."""
        pv = perm_and_var(eq, syms)
        if pv is None:
            return None
        var, order = pv
        try:
            base = diophantine(eq, t, permute=permute)    # A-reference: real callee
        except Exception as e:
            return ("raise", type(e).__name__)
        # reorderTuple order tup = [tup[k] for k in order]; reorderAll maps it
        return ("set", {tuple(tup[k] for k in order) for tup in base})

    def oracle(eq, syms, permute):
        """patch.diff's behaviour: the gold-patched diophantine with syms,
        classified into the same observable-outcome domain."""
        try:
            return ("set", diophantine(eq, syms=syms, permute=permute))
        except Exception as e:
            return ("raise", type(e).__name__)

    return symbols, shadow, oracle, perm_and_var, (x, y, z)


def main():
    from sympy import srepr
    symbols, shadow, oracle, perm_and_var, (x, y, z) = build()
    rng = random.Random(SEED)

    # candidate (eq, syms) pairs: equation families admitting variant solutions,
    # paired with a NON-canonical syms order so the reorder branch is taken.
    pairs = [
        (x ** 4 + y ** 4 - 2 ** 4 - 3 ** 4, (y, x)),   # the issue (both orders)
        (x ** 4 + y ** 4 - 2 ** 4 - 3 ** 4, (x, y)),
        (y ** 4 + x ** 4 - 2 ** 4 - 3 ** 4, (x, y)),
        (y ** 4 + x ** 4 - 2 ** 4 - 3 ** 4, (y, x)),
        (x ** 2 + y ** 2 - 25, (y, x)),
        (x ** 2 + y ** 2 - 50, (y, x)),
        (x ** 2 + y ** 2 - 5, (y, x)),
        (x ** 2 + y ** 2 - 65, (y, x)),
        (x ** 4 + y ** 4 - 1 ** 4 - 2 ** 4, (y, x)),
    ]

    def gen(n):
        # boundary cases first (the issue's own examples, both flag values)
        for eq, syms in pairs:
            for p in (True, False):
                yield (eq, syms, p)
        # randomized fuzz over a bounded family (memoized: bounded distinct work)
        for _ in range(n):
            a = rng.randint(1, 5)
            b = rng.randint(1, 5)
            N = rng.randint(2, 90)
            deg = rng.choice([2, 4])
            eq = a * x ** deg + b * y ** deg - N
            syms = rng.choice([(y, x), (x, y)])
            p = rng.choice([True, False])
            yield (eq, syms, p)

    seen = {}
    disagreements = []
    total = 0
    distinct = 0
    in_branch = 0
    for eq, syms, permute in gen(N_FUZZ):
        total += 1
        # only inputs that ENTER the reorder branch are within the modeled spec
        if perm_and_var(eq, syms) is None:
            continue
        in_branch += 1
        key = (srepr(eq), tuple(srepr(s) for s in syms), permute)
        if key in seen:
            continue
        distinct += 1
        sh = shadow(eq, syms, permute)
        orc = oracle(eq, syms, permute)
        seen[key] = True
        # compare observable outcomes: same kind, and same set / same exception
        agree = (sh[0] == orc[0] and
                 (sh[1] == orc[1] if sh[0] == "raise" else bool(sh[1] == orc[1])))
        if not agree:
            disagreements.append((key, repr(sh), repr(orc)))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs (%d in-branch, "
              "%d distinct):" % (len(disagreements), total, in_branch, distinct))
        for k, sh, orc in disagreements:
            print("  key=%s shadow=%s oracle=%s" % (k, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of reorderSolutions agrees with patch.diff "
          "behaviour (gold-patched diophantine(eq, syms, permute)) on %d "
          "generated inputs (%d in-branch, %d distinct, memoized; seed=%d), 0 "
          "disagreements." % (total, in_branch, distinct, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
