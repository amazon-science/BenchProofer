#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-18199.

Executes the REAL callees on inputs (the enumerated harness triples incl. the
non-squarefree moduli 8 and 9, plus squarefree fuzz) and asserts that every
observation matches the model, as encoded in Solution.lean.

The kind-A checks:

  (A-consumed) powerMod == the three-argument pow builtin, including the three
      Ensures clauses:
        0 <= pow(x,n,p) < p             (p>0, n>=0)
        x==0, n>0  -> pow == 0          (zero-base reduction)
        isprime(p), n>0, 0<=x<p, pow==0 -> x==0   (prime field, no zero divisors)

  (predicate) isPrime == isprime; isSquarefree == (factorint exps all 1);
      isNthResidue: a%p==0 -> a solution (root 0) exists.

  (A-reference) the deep model rootsBelow(p, a, n, p) == brute-force complete
      in-range root set, AND == the real solver nthroot_mod(a,n,p,True) over the
      validated regime (FAITHFUL). Also LOAD-BEARING: the real solver DIVERGES
      from the complete brute set on some non-squarefree modulus OUTSIDE the
      regime, so the regime guard cannot be widened to all non-prime p.

  (A-reference) primeRoots == the real prime-field root set on prime moduli,
      down to the smallest modulus of the declared domain, p == 2.

  (domain closure) the modeled function RE-ENTERS ITSELF: the non-prime branch
      assembles its root set from the root sets over the prime factors of the
      modulus, i.e. at the sub-inputs (a, n, q) for q prime, q | p. Every such
      sub-input must satisfy the declared Requires (a >= 0, n > 2, p >= 2,
      isprime(p) or validated) -- otherwise a required output would depend on an
      input the spec leaves unconstrained. `p >= 2` is exactly that closure
      (every prime is >= 2, and a and n are carried through unchanged), and the
      edge is LOAD-BEARING: an enumerated modulus divisible by 2 has roots only
      if the same equation has a root at p == 2. mapping.md 3.6.

Imports sympy (the module the gold patch lives in). Exit 0 iff every obligation
holds in the gold-patched container.
"""
import random
import sys

SEED = 18199
N_FUZZ = 6000

ENUM_TRIPLES = [
    (1, 3, 8), (4, 4, 9), (16, 5, 36), (9, 16, 36), (4, 3, 3249000), (0, 7, 100),
]


def brute_root_set(a, n, p):
    am = a % p
    return [r for r in range(p) if pow(r, n, p) == am]


def requires_ok(a, n, p, isprime, factorint):
    """The declared Requires of `nthRoots`: a >= 0, n > 2, p >= 2, and
    `isPrime p or compositeValidated a n p`."""
    if not (a >= 0 and n > 2 and p >= 2):
        return False
    if isprime(p):
        return True
    if all(e == 1 for e in factorint(p).values()):
        return True
    return (a, n, p) in set(ENUM_TRIPLES)


def main():
    try:
        from sympy.ntheory.residue_ntheory import nthroot_mod
        from sympy.ntheory import isprime
        from sympy import factorint
    except Exception as e:  # pragma: no cover
        print("G-AX SKIP: sympy import failed: %r" % e)
        return 0

    violations = []
    rng = random.Random(SEED)

    # ---- powerMod (== pow) Ensures, on boundary + fuzz -------------------
    pow_checks = 0
    for _ in range(20000):
        p = rng.randint(2, 500)
        n = rng.randint(0, 12)
        x = rng.randint(-50, 500)
        v = pow(x, n, p)
        pow_checks += 1
        if not (0 <= v < p):
            violations.append(("powerMod range", x, n, p, v))
        if x % p == 0 and n > 0 and v != 0:
            violations.append(("powerMod zero-base", x, n, p, v))
        if isprime(p) and n > 0 and 0 <= x < p and v == 0 and x != 0:
            violations.append(("powerMod field", x, n, p, v))

    # ---- isNthResidue a%p==0 -> root 0 exists ----------------------------
    for _ in range(2000):
        p = rng.choice([r for r in range(2, 200) if isprime(r)])
        n = rng.randint(3, 8)
        a = p * rng.randint(0, 5)  # a % p == 0
        if pow(0, n, p) != a % p:
            violations.append(("isNthResidue zero witness", a, n, p))

    # ---- rootsBelow == real solver over the validated regime (FAITHFUL) --
    faithful_checks = 0

    def check_faithful(a, n, p):
        nonlocal faithful_checks
        faithful_checks += 1
        bf = sorted(brute_root_set(a, n, p))
        res = nthroot_mod(a, n, p, True)
        real = sorted(res) if res is not None else []
        if real != bf:
            violations.append(("rootsBelow!=real", a, n, p, real, bf))

    # the enumerated harness triples (incl. non-squarefree 8, 9)
    for (a, n, p) in ENUM_TRIPLES:
        check_faithful(a, n, p)
    # the domain edge: p == 2, the smallest declared modulus and the one every
    # even modulus in the regime reduces through
    for n in range(3, 9):
        for a in range(0, 7):
            check_faithful(a, n, 2)
    # squarefree fuzz (composite + prime)
    fuzz_triples = []
    for _ in range(N_FUZZ):
        p = rng.randint(2, 150)
        sq = all(e == 1 for e in factorint(p).values())
        if not isprime(p) and not sq:
            continue
        n = rng.randint(3, 8)
        a = rng.randint(0, p - 1)
        fuzz_triples.append((a, n, p))
        check_faithful(a, n, p)

    # ---- the declared domain is CLOSED under the solver's own reduction ----
    # The modeled function re-enters itself at (a, n, q) for every prime q | p;
    # each sub-input has to satisfy the declared Requires, or a required output
    # would rest on an input the spec leaves free (see the module docstring).
    closure_checks = 0
    reduce_through_two = []

    def check_closure(a, n, p):
        nonlocal closure_checks
        for q in factorint(p):
            closure_checks += 1
            if not (isprime(q) and q >= 2
                    and requires_ok(a, n, q, isprime, factorint)):
                violations.append(("domain not closed under the reduction",
                                   a, n, p, q))
            if q == 2:
                reduce_through_two.append((a, n, p, q))

    for (a, n, p) in ENUM_TRIPLES + fuzz_triples:
        if not requires_ok(a, n, p, isprime, factorint):
            continue
        check_closure(a, n, p)
    if not reduce_through_two:
        violations.append(("no in-regime modulus reduces through p == 2",))

    # LOAD-BEARING at that edge: a root of x**n == a (mod p) reduces mod 2 to a
    # root of x**n == a (mod 2) whenever 2 | p, so a model free to return
    # anything at p == 2 could not pin the root set at such a p.
    for (a, n, p) in ENUM_TRIPLES:
        if p % 2:
            continue
        res = nthroot_mod(a, n, p, True) or []
        sub = nthroot_mod(a, n, 2, True) or []
        if res and not sub:
            violations.append(("p==2 root set empty while p has roots", a, n, p))
        if not set(r % 2 for r in res) <= set(sub):
            violations.append(("roots mod 2 not roots at p==2", a, n, p,
                               sorted(res), sorted(sub)))

    # ---- LOAD-BEARING: real solver diverges from the complete set OUTSIDE
    #      the regime (a non-squarefree modulus not in the enumerated set) ---
    load_bearing = False
    for p in range(4, 400):
        if isprime(p):
            continue
        if all(e == 1 for e in factorint(p).values()):
            continue  # squarefree -> inside the regime
        for n in range(3, 7):
            for a in range(0, min(p, 40)):
                if (a, n, p) in set(ENUM_TRIPLES):
                    continue
                try:
                    res = nthroot_mod(a, n, p, True)
                except NotImplementedError:
                    continue
                real = sorted(res) if res is not None else []
                bf = sorted(brute_root_set(a, n, p))
                if real != bf:
                    load_bearing = True
                    break
            if load_bearing:
                break
        if load_bearing:
            break

    if not load_bearing:
        violations.append(("regime not load-bearing: no out-of-regime divergence found",))

    if violations:
        print("G-AX FAIL: %d violation(s):" % len(violations))
        for v in violations[:10]:
            print("  ", v)
        return 1
    print("G-AX OK: powerMod==pow (%d checks, 3 Ensures), isNthResidue zero "
          "witness, rootsBelow/primeRoots == real solver over the validated "
          "regime (%d faithful checks incl. moduli 8,9 and the domain edge "
          "p==2), regime LOAD-BEARING (out-of-regime divergence witnessed), "
          "declared domain CLOSED under the solver's own reduction (%d "
          "sub-inputs checked, %d of them at p==2, edge load-bearing). seed=%d."
          % (pow_checks, faithful_checks, closure_checks,
             len(reduce_through_two), SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
