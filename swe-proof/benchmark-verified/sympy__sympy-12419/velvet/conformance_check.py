#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-12419 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW — the R/I-tagged ops of Solution.lean's `identityEntry` impl region
             transliterated to the real repo types via the mapping.md bijection.
             The impl is the TWO-STAGE branch on the two verdicts
             `eq, kd : Option Bool`:
               eq = some true          -> MatEntry.unit        (S.One)
               eq = some false         -> MatEntry.null         (S.Zero)
               eq = none, kd = some t  -> MatEntry.unit         (S.One)
               eq = none, kd = some f  -> MatEntry.null         (S.Zero)
               eq = none, kd = none    -> MatEntry.coincide i j (unevaluated KD)
             The A-tagged component callees are NOT replaced by a model here: the
             comparison verdict is read from the REAL `Eq(a, b)` and the
             indicator's own verdict from the REAL `KroneckerDelta(a, b)` (both
             through the `threeval` / `kdval` bridges). G-CONF thus isolates the
             R/I skeleton (the two-stage branch + the constructor bijection); the
             component-callee soundness stays with G-AX.
  * ORACLE — `patch.diff`'s behaviour: the REAL patched `Identity(n)[a, b]`
             applied at base_commit (the harness applies patch.diff before this
             runs), i.e. the rewritten `Identity._entry`. This is exactly what the
             sole FAIL_TO_PASS `test_Identity` observes.

The observable is the SYMBOLIC value: SHADOW and ORACLE must be the SAME object
under the library's structural equality (`Basic.__eq__`) — the relation
`test_Identity`'s `In[i, j] != 0` and the `Sum(...).doit()` assertions rest on.

Exit 0 iff zero disagreements; any disagreement is a mechanical R/I-fidelity
counterexample. stdlib + sympy only (sympy ships in the testbed env). Seed
pinned (mapping.md §4).
"""
import random
import sys

SEED = 12419
N_FUZZ = 100_000
DISAGREE_CAP = 5


def threeval(v, S):
    """mapping.md §2 bridge: the value Eq(a,b) returns -> Option Bool.
    Mirrors the patched _entry's `eq is S.true` / `eq is S.false` test."""
    if v is S.true:
        return True
    if v is S.false:
        return False
    return None


def kdval(a, b, S, KroneckerDelta):
    """mapping.md §2 bridge for the SECOND verdict: the coincidence indicator's
    OWN three-valued self-evaluation at the two positions -> Option Bool. The
    indicator's rules are broader than the comparison's, so this is an
    INDEPENDENT verdict, not a function of the first one."""
    kd = KroneckerDelta(a, b)
    if kd == S.One:
        return True
    if kd == S.Zero:
        return False
    return None


def shadow_entry(a, b, Eq, S, KroneckerDelta):
    """SHADOW: entryFor/coincideValue transliterated from Solution.lean's
    MatEntry constructors to library value-builders (the mapping.md R bijection).
    Both verdicts are read from the REAL unchanged callees (A-reference)."""
    eq = threeval(Eq(a, b), S)            # real Eq verdict -> Option Bool
    if eq is True:
        return S.One                      # MatEntry.unit
    if eq is False:
        return S.Zero                     # MatEntry.null
    # eq = none: defer to the indicator's OWN verdict (coincideValue i j kd)
    kd = kdval(a, b, S, KroneckerDelta)
    if kd is True:
        return S.One                      # coincideValue .. (some true)  = unit
    if kd is False:
        return S.Zero                     # coincideValue .. (some false) = null
    return KroneckerDelta(a, b)           # coincideValue .. none = coincide i j


def fuzz_pairs(n, rng, syms, ints, affines):
    """Yield index pairs spanning the three verdict classes. Boundary cases
    (the F2P-relevant ones) first, then randomized fuzz."""
    i, j, k = syms[0], syms[1], syms[2]
    # boundary: undetermined, definite-equal, definite-distinct
    yield (i, j)                          # F2P: distinct symbols -> KD, != 0
    yield (i, i)                          # equal -> One
    yield (ints[0], ints[1])              # distinct ints -> Zero  (0,1)
    yield (ints[2], ints[2])              # equal ints -> One
    yield (i, ints[0])                    # symbol vs literal -> undetermined
    yield (affines[0], affines[1])        # affine
    yield (syms[5], syms[6])              # below/above fermi -> eq none, kd false
    yield (syms[6], syms[5])              # the mirrored fermi pair
    pool = syms + ints + affines
    for _ in range(n):
        a = rng.choice(pool)
        b = rng.choice(pool)
        yield (a, b)


def main():
    from sympy import Eq, S, Symbol, symbols, Integer, Identity
    from sympy.functions.special.tensor_functions import KroneckerDelta

    rng = random.Random(SEED)

    n = Symbol('n', integer=True, positive=True)
    i, j, k = symbols('i j k', integer=True)
    syms = [i, j, k, Symbol('p', integer=True), Symbol('q', integer=True),
            # fermi-assumption symbols: the indicator's own rules settle these
            # pairs as DISTINCT while `Eq` leaves them unsettled, so they
            # populate the `eq = none, kd = some false` class the two-stage
            # model exists to get right.
            Symbol('bf', below_fermi=True), Symbol('af', above_fermi=True),
            Symbol('bf2', below_fermi=True), Symbol('af2', above_fermi=True)]
    ints = [Integer(v) for v in range(0, 6)]
    affines = [i + 1, i, j - 1, 2 * i, i + j, 3 * k, 2 * i, i + i]

    In = Identity(n)                      # patched Identity (gold applied)

    disagreements = []
    count = 0
    for a, b in fuzz_pairs(N_FUZZ, rng, syms, ints, affines):
        count += 1
        shadow = shadow_entry(a, b, Eq, S, KroneckerDelta)
        oracle = In[a, b]                 # real patched Identity._entry
        # structural equality — the relation test_Identity's asserts rest on
        if shadow != oracle:
            disagreements.append((a, b, shadow, oracle))
            if len(disagreements) >= DISAGREE_CAP:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for a, b, sh, orc in disagreements:
            print("  i=%r j=%r shadow=%r oracle=%r" % (a, b, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of identityEntry equals patch.diff behaviour "
          "(structural Basic.__eq__) on %d index-pair configurations (seed=%d), "
          "0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
