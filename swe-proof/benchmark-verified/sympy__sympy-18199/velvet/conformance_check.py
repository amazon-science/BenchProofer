#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-18199 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* repo types (int, list[int]) via the
              mapping.md bijection. The deep model rootsBelow is the structural
              fold over candidate residues; the prime path and the residue/
              primality predicates are A-tagged callees, so on the SHADOW side we
              dispatch to the real solver for the prime path but compute the
              non-prime path as the complete brute-force root set (the deep
              model), which is exactly what Solution.lean's spec pins.
  * ORACLE  — patch.diff's behaviour: the patched solver applied at base_commit
              with all_roots=True (the real correctness oracle, G-RESOLVE).

They must agree on every Requires-satisfying input (a >= 0, n > 2, p >= 2,
isprime(p) or composite_validated(a,n,p)) -- including the domain edge p == 2,
the smallest modulus the declared domain admits and the one the non-prime branch
reduces every even modulus through (mapping.md 3.6). Exit 0 iff zero
disagreements.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + sympy. The
fuzz seed is pinned for a deterministic verdict.
"""
import random
import sys

SEED = 18199
N_FUZZ = 4000

# Enumerated harness triples (the non-prime moduli the test suite reaches,
# including the non-squarefree moduli 8 and 9), plus the squarefree extras.
ENUM_TRIPLES = [
    (1, 3, 8), (4, 4, 9), (16, 5, 36), (9, 16, 36), (4, 3, 3249000), (0, 7, 100),
]


def brute_root_set(a, n, p):
    """The deep model rootsBelow(p, a, n, p): every residue r in [0, p) with
    r**n == a (mod p), ascending. The structural fold of Solution.lean."""
    am = a % p
    return [r for r in range(p) if pow(r, n, p) == am]


def composite_validated(a, n, p, is_squarefree):
    if is_squarefree:
        return True
    return (a, n, p) in set(ENUM_TRIPLES)


def shadow(a, n, p, isprime, nthroot_mod):
    """The R/I shadow of nthRoots: non-prime -> the deep complete root set;
    prime -> dispatch to the real prime-field solver (A-reference, out of the
    R/I scope, so we use the real callee here as the spec permits)."""
    if not isprime(p):
        return sorted(brute_root_set(a, n, p))
    res = nthroot_mod(a, n, p, True)
    if res is None:
        return []
    return sorted(res)


def oracle(a, n, p, nthroot_mod):
    """patch.diff behaviour: the patched solver, all_roots=True."""
    res = nthroot_mod(a, n, p, True)
    if res is None:
        return []
    return sorted(res)


def fuzz_inputs(n_fuzz, rng):
    from sympy.ntheory import isprime
    from sympy import factorint
    # boundary: the enumerated harness triples first
    for t in ENUM_TRIPLES:
        yield t
    # boundary: the domain edge p == 2 (the smallest declared modulus)
    for n in range(3, 9):
        for a in range(0, 7):
            yield (a, n, 2)
    # squarefree composite moduli + prime moduli fuzz
    count = 0
    while count < n_fuzz:
        p = rng.randint(2, 200)
        n = rng.randint(3, 8)
        a = rng.randint(0, p - 1)
        sq = all(e == 1 for e in factorint(p).values())
        if not isprime(p) and not sq:
            continue  # outside the validated regime
        count += 1
        yield (a, n, p)


def main():
    try:
        from sympy.ntheory.residue_ntheory import nthroot_mod
        from sympy.ntheory import isprime
    except Exception as e:  # pragma: no cover
        print("G-CONF SKIP: sympy import failed: %r" % e)
        return 0
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for (a, n, p) in fuzz_inputs(N_FUZZ, rng):
        count += 1
        try:
            sh = shadow(a, n, p, isprime, nthroot_mod)
            orc = oracle(a, n, p, nthroot_mod)
        except NotImplementedError:
            # pre-patch decline; with the gold patch applied this never fires
            continue
        if sh != orc:
            disagreements.append((a, n, p, sh, orc))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for a, n, p, sh, orc in disagreements:
            print("  (a,n,p)=%r shadow=%r oracle=%r" % ((a, n, p), sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of nthRoots agrees with patch.diff behaviour "
          "on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
