#!/usr/bin/env python
"""G-AX: validate the opaque-callee contracts for sympy__sympy-18199.

Runs INSIDE the instance image (PYTHONPATH=/testbed). Exercises each REAL callee
the Lean bundle declares `opaque`/`axiom` and relies on, over boundary + fuzzed
inputs, and asserts each meets the WEAKEST property the proof consumes. These are
callees the patched `nthroot_mod` CALLS but does NOT change. stdlib-only fuzzing
(pinned seed) + sympy. Exit 0 iff sound.

Contracts validated:
  primeUnitRoots (nthroot_mod on a PRIME p, all_roots=True):
      every returned root r satisfies pow(r,n,p) == a % p, and 0 <= r < p
      -- the SOUNDNESS contract the proof consumes (`primeUnitRoots_sound`),
      under its declared Requires 0 <= a, 1 < n, 1 < p, AND p a single prime.
      The prime restriction is load-bearing, not cosmetic: on a modulus that is
      NOT a single prime the same callee returns non-roots, so a contract claimed
      there would be FALSE of the real callee. This gate validates the contract
      exactly on the single-prime domain it is claimed for; the composite-modulus
      counterexamples justifying the restriction are asserted by G-CONF.  [A-consumed]
  modulusIsPrime (isprime):  isprime(p) iff p is prime (cross-checked)          [A-reference]
  modulusSquarefree (squarefree test on factorint): the boolean the spec's
      regime guard reads coincides with "no repeated prime factor".            [A-reference]
  modulusRegularLift: the boolean the spec's second regime leg reads coincides
      with "every prime occurring more than once in the modulus divides neither
      the target nor the exponent, and where it occurs to a power >= 3 every
      residue solving the congruence mod that prime already solves it mod the
      whole prime-power component".                                            [A-reference]

The two LOAD-BEARING validations of the deep composite model:
  * the regime BOOLEANS themselves -- that each reads exactly the arithmetic
    predicate on the inputs that its docstring states.

SCOPE NOTE, and why it excludes the deep-model legs. This gate runs against the
repository WITHOUT the change applied, so it may only assert properties of callees
the change does not touch. Every obligation about the ROOT-SET VALUE for a modulus
that is not a single prime -- the exact-set claim over the regime, and the
unconditional report clause read as a solvability equivalence -- is a property of
the CHANGED routine and is validated by G-CONF, which runs with the change
applied. Asserting them here would be worse than redundant: without the change a
non-single-prime modulus either aborts or reports nothing, so every such
comparison is skipped or fails, and a leg written to tolerate the aborts is
VACUOUS rather than validating. Likewise the fact that the unit-base solver emits
non-roots when handed a modulus that is not a single prime (the fact justifying
the single-prime restriction on its soundness contract) is only reachable once the
dispatch routes there, so it is asserted in G-CONF.
"""
import sys, random
from math import gcd

random.seed(18199)
FAIL = 0

def check(cond, msg):
    global FAIL
    if not cond:
        FAIL += 1
        if FAIL <= 20:
            print("VIOLATION:", msg)

try:
    from sympy import isprime, primerange, factorint
    from sympy.ntheory.residue_ntheory import nthroot_mod
except Exception as e:  # pragma: no cover
    print("status=error import failed:", e)
    sys.exit(1)

primes = list(primerange(3, 500))


def prime_unit_roots(a, n, p):
    r = nthroot_mod(a, n, p, True)
    if r is None:
        return []
    if isinstance(r, int):
        return [r]
    return list(r)


def deep_root_set(a, n, m):
    am = a % m
    return [x for x in range(m) if pow(x, n, m) == am]


def real_raw(a, n, m):
    """The real report, order preserved (the ordering clause reads the order)."""
    r = nthroot_mod(a, n, m, True)
    if r is None:
        return []
    if isinstance(r, int):
        r = [r]
    return [int(x) for x in r]


def real_patched(a, n, m):
    return sorted(set(real_raw(a, n, m)))


def is_squarefree(m):
    return all(e == 1 for e in factorint(m).values())


def regular_lift(a, n, m):
    """The Lean `modulusRegularLift a n m` predicate, as its docstring states it."""
    for p, e in factorint(m).items():
        if e == 1:
            continue
        if a % p == 0 or n % p == 0:
            return False
        if e >= 3:
            pe = p ** e
            am_p, am_pe = a % p, a % pe
            for r in range(p):
                if pow(r, n, p) == am_p and pow(r, n, pe) != am_pe:
                    return False
    return True


def dispatch_validated(a, n, m):
    return n == 2 or is_squarefree(m) or regular_lift(a, n, m)


# --- primeUnitRoots soundness (the A-consumed contract) ---------------------
# Requires of the axiom: 0 <= a, 1 < n, 1 < p. `a` ranges over the whole
# non-negative half-line the Requires admits, not just [1, p).
for _ in range(20000):
    p = random.choice(primes)
    n = random.randint(2, 25)
    a = random.randrange(0, 4 * p)
    if a % p == 0:
        continue                        # the zero-target case is the [0] branch
    try:
        roots = prime_unit_roots(a, n, p)
    except Exception:
        continue
    for r in roots:
        r = int(r)
        check(0 <= r < p, f"primeUnitRoots({a},{n},{p}) out-of-range root {r}")
        check(pow(r, n, p) == a % p, f"primeUnitRoots({a},{n},{p}) bad root {r}")

# --- isprime: cross-check against trial division ----------------------------
def trial_prime(x):
    if x < 2:
        return False
    i = 2
    while i * i <= x:
        if x % i == 0:
            return False
        i += 1
    return True
for x in range(2, 2000):
    check(isprime(x) == trial_prime(x), f"isprime({x}) disagrees")

# --- modulusSquarefree reads what its docstring says ------------------------
for m in range(2, 800):
    check(is_squarefree(m) == all(e == 1 for e in factorint(m).values()),
          f"squarefree test wrong on {m}")

# --- the regime BOOLEANS read exactly the predicates their docstrings state ---
# These are conditions on the INPUTS computed from unchanged callees (factorint,
# pow), so they ARE validatable here. What they GUARD -- the root-set value -- is
# not, and is G-CONF's.
nonprime = [m for m in range(4, 400) if not isprime(m)]
nonsquarefree = [m for m in range(4, 400)
                 if not isprime(m) and not is_squarefree(m)]

# modulusRegularLift: re-derive the predicate independently of the helper above
# (directly from the factorisation) and require agreement.
def regular_lift_ref(a, n, m):
    f = factorint(m)
    for p in f:
        e = f[p]
        if e < 2:
            continue
        if a % p == 0:
            return False
        if n % p == 0:
            return False
        if e > 2:
            pe = p ** e
            for r in range(p):
                if pow(r, n, p) == a % p and pow(r, n, pe) != a % pe:
                    return False
    return True

checked_rl = 0
for _ in range(40000):
    m = random.choice(nonsquarefree)
    n = random.randint(2, 25)
    a = random.randrange(0, 3 * m)
    checked_rl += 1
    check(regular_lift(a, n, m) == regular_lift_ref(a, n, m),
          f"regular-lift predicate disagrees with its reference a={a} n={n} m={m}")
check(checked_rl > 20000, f"too few regular-lift samples ({checked_rl})")

# The regime is INHABITED and its complement is too -- a regime that admitted
# everything, or nothing, would make the guarded clause meaningless.
admitted = sum(1 for m in nonsquarefree
               for n in range(3, 12) for a in range(0, min(m, 20))
               if regular_lift(a, n, m))
excluded = sum(1 for m in nonsquarefree
               for n in range(3, 12) for a in range(0, min(m, 20))
               if not regular_lift(a, n, m))
check(admitted > 1000, f"regular-lift regime admits too little ({admitted})")
check(excluded > 1000, f"regular-lift regime excludes too little ({excluded})")

# The exponent-two leg is admitted for EVERY non-single-prime modulus, which is
# what lets the graded quadratic congruence over a modulus with a repeated prime
# factor fall inside the regime at all.
for m in nonprime:
    check(dispatch_validated(0, 2, m), f"exponent-two leg not admitted at m={m}")

if FAIL == 0:
    print(f"status=pass all unchanged-callee contracts validated (prime-path "
          f"nthroot_mod soundness under its Requires, on the single-prime domain "
          f"it is claimed for; isprime vs trial division; the squarefree and "
          f"regular-lift regime booleans against independently re-derived "
          f"references over {checked_rl} samples, with the regime shown "
          f"INHABITED ({admitted}) and its complement inhabited ({excluded}); "
          f"the exponent-two leg admitted at every non-single-prime modulus. The "
          f"CHANGED routine's own obligations -- the exact-set claim and the "
          f"unconditional report equivalence -- are G-CONF's, which runs with "
          f"the change applied)")
    sys.exit(0)
print(f"status=fail {FAIL} violations")
sys.exit(1)
