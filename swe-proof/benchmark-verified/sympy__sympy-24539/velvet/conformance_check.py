#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-24539 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outcomes:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region (`asExpr`, routed
              through the deep model `asExprSpec`) transliterated to Python over
              the real repo types. The symbol-selection decision is pure R/I; the
              one A-tagged callee, the unchanged renderer `expr_from_dict`, is NOT
              replaced by a model here — the shadow calls the REAL `expr_from_dict`
              (G-CONF isolates the R/I legs; the A leg stays with G-AX).
  * ORACLE  — `patch.diff`'s behaviour: the patched `PolyElement.as_expr` applied
              at base_commit (the real correctness oracle, G-RESOLVE applies the
              gold patch before this runs).

Observable of a call, per the mapping.md §2 bijection:
  - whether the call returns an expression or raises the wrong-number-of-symbols
    ValueError  ↔  `Except.ok _` vs `Except.error .wrongNumberOfSymbols`;
  - on success, the returned expression itself (SymPy structural equality)  ↔  the
    opaque `Int` handle `exprFromDict d chosen`.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement is
a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), `sympy` + stdlib only.
The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

from sympy import ring, ZZ, symbols
from sympy.polys.polyutils import expr_from_dict

SEED = 24539
N_FUZZ = 100_000

_POOL = list(symbols("a b c d e f g h"))


def build_cases():
    cases = []
    R1, x = ring("x", ZZ)
    cases.append(5*x**3 - 2*x + 1)
    R2, x, y = ring("x,y", ZZ)
    cases.append(3*x**2*y - x*y + 7*y**3 + 1)
    R3, x, y, z = ring("x,y,z", ZZ)
    cases.append(3*x**2*y - x*y*z + 7*z**3 + 1)
    R4, x, y, z, t = ring("x,y,z,t", ZZ)
    cases.append(x*y - z*t + 2*x**2*t - 5)
    return cases


def shadow(f, supplied):
    """asExprSpec (pure region) transliterated. Returns ('error',) or
    ('ok', expr) where expr uses the REAL unchanged renderer expr_from_dict on
    the CHOSEN name list — exactly the impl region's selection decision."""
    ring_symbols = list(f.ring.symbols)
    if len(supplied) == 0:                       # symbols.isEmpty
        chosen = ring_symbols
    elif len(supplied) == f.ring.ngens:          # correctly-sized -> honor it
        chosen = list(supplied)
    else:
        return ("error",)
    return ("ok", expr_from_dict(f.as_expr_dict(), *chosen))


def oracle(f, supplied):
    """patch.diff's behaviour: the patched as_expr. A refused call surfaces as
    ValueError."""
    try:
        return ("ok", f.as_expr(*supplied))
    except ValueError:
        return ("error",)


def fuzz_inputs(f, n, rng):
    ng = f.ring.ngens
    # boundary: empty, exact length (own names + a distinct correctly-sized
    # list), and each wrong length around ngens
    yield ()
    yield tuple(f.ring.symbols)
    distinct = tuple(s for s in _POOL if s not in set(f.ring.symbols))[:ng]
    yield distinct
    for k in range(0, ng + 4):
        if k != ng and k <= len(_POOL):
            yield tuple(_POOL[:k])
    for _ in range(n):
        k = rng.randint(0, len(_POOL))
        yield tuple(rng.sample(_POOL, k))


def main():
    rng = random.Random(SEED)
    cases = build_cases()
    disagreements = []
    count = 0
    per_case = N_FUZZ // len(cases) + 1
    for f in cases:
        for supplied in fuzz_inputs(f, per_case, rng):
            count += 1
            sh = shadow(f, supplied)
            orc = oracle(f, supplied)
            # compare tag, and on success compare the expression structurally
            agree = (sh[0] == orc[0]) and (sh[0] == "error" or sh[1] == orc[1])
            if not agree:
                disagreements.append((f, supplied, sh, orc))
                if len(disagreements) >= 5:
                    break
        if disagreements:
            break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for f, sup, sh, orc in disagreements:
            print("  poly=%r supplied=%r shadow=%r oracle=%r" % (f, sup, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of asExpr agrees with patch.diff behaviour on "
          "%d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
