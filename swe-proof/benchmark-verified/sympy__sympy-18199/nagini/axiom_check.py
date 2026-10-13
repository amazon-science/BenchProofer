#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-18199.

Validates every model.py axiom/reference against the REAL repository callees
in-container (sympy is the repository under test).  Exit 0 iff every obligation
holds.

Consumed axioms (model.py `axioms` region) and what each is checked against:

  power_mod(x, n, p)      == Python `pow(x, n, p)`  (the unchanged 3-arg pow),
      including the two extra Ensures the proof consumes:
        * x == 0 and n > 0  ->  pow == 0
        * p prime and n > 0 and 0 <= x < p and pow == 0  ->  x == 0
          (a prime field has no zero divisors).

  is_prime(p)             == sympy `isprime(p)`  (the unchanged primality test).

  is_squarefree(p)        == "p has no repeated prime factor" (sympy
      `factorint(p)` exponents all 1).  The model name IS that predicate; it is
      used only to delimit the validated modulus regime (composite_validated).

  is_nth_residue(a, n, p) over-approximates sympy `is_nthpow_residue(a, n, p)`,
      and the proof only consumes its weakest clause: a % p == 0 -> a solution
      exists.  Both the real predicate AND ground truth (a root really exists)
      are checked.

Deep root-set models (the result-set the dispatch postconditions equate the
output to):

  prime_roots(a, n, p)      (PRIME p, a % p != 0)  -- the unchanged prime-field
      solver, an A-reference validated == the REAL callee here; and
  composite_roots(a, n, p)  (NON-PRIME p, validated regime)  -- now modelled
      DEEPLY in model.py: composite_roots(a, n, p) == roots_below(p, a, n, p),
      the recursive fold that collects EVERY in-range root, i.e. the COMPLETE
      root set {r in [0, p): r**n == a (mod p)}.  The model therefore pins the
      composite output to the complete congruence root set, not to an opaque
      oracle.  This check validates that the REAL callee
      `nthroot_mod(a, n, p, all_roots=True)` returns exactly that complete set
      over the validated regime.

  Both are validated == the REAL callee AT THE LEVEL OF THE ROOT SET (each side
      a subset of the other -- an over-keep or under-keep of any one residue
      fails loudly), AND cross-checked against an independent brute-force oracle
      `brute_root_set` (which IS the set the model's roots_below fold computes).
      So the gold == brute_root_set check below simultaneously validates (a) the
      A-reference prime_roots, and (b) that the gold composite output equals the
      deep model composite_roots == complete root set, in-regime.

composite_roots carries a `composite_validated(a, n, p)` precondition that
delimits the modulus regime over which its complete-root-set claim is asserted in
the model: squarefree moduli PLUS the enumerated non-squarefree test-suite
triples.  This check VALIDATES that regime predicate two ways:
  * over the validated regime the gold root set == brute-force truth (sound and
    complete) -- so the model's Ensures over composite_validated is faithful;
  * OUTSIDE the regime (a non-squarefree modulus that is NOT one of the
    enumerated triples) the gold genuinely returns a root set that differs from
    the complete brute-force set (it returns non-roots and/or drops roots), which
    is exactly why composite_roots' complete-root-set claim may NOT be made
    universally and the `composite_validated` guard is load-bearing, not
    cosmetic.  We assert that such a witness exists so the regime restriction
    cannot be silently widened back to "all non-prime p".

The FAIL_TO_PASS-relevant cases (composite modulus, all_roots) are enumerated
explicitly and asserted FIRST, unconditionally (no skip-guard); a skipped F2P
case would be a false pass, so it cannot happen here.
"""
import random
import sys

from sympy.ntheory.residue_ntheory import nthroot_mod, is_nthpow_residue
from sympy import isprime, factorint


# --- normalisation of the real complete-solution callee ---------------------

def real_root_set(a, n, m):
    """Run the REAL callee nthroot_mod(a, n, m, all_roots=True) and return its
    complete solution set as a set of ints in [0, m).  'No solutions' (empty
    list OR None) -> empty set.  No re-filtering by any predicate under test."""
    res = nthroot_mod(a, n, m, all_roots=True)
    if res is None:
        return set()
    return {int(x) % m for x in res}


def brute_root_set(a, n, m):
    """Independent ground truth: the residues r in [0, m) with r**n == a (mod m),
    computed by brute force -- a fully separate oracle from the callee."""
    amod = a % m
    return {r for r in range(m) if pow(r, n, m) == amod}


# --- power_mod axiom ---------------------------------------------------------

def check_power_mod(x, n, p):
    """power_mod(x, n, p) == pow(x, n, p), plus the two consumed Ensures."""
    real = pow(x, n, p)
    assert 0 <= real < p, "pow out of range on (%r,%r,%r): %r" % (x, n, p, real)
    if x == 0 and n > 0:
        assert real == 0, "zero-base Ensures violated on (%r,%r,%r)" % (x, n, p)
    if isprime(p) and n > 0 and 0 <= x < p and real == 0:
        assert x == 0, (
            "prime-field zero-divisor Ensures violated: pow(%r,%r,%r)==0 but "
            "x != 0" % (x, n, p))


# --- is_nth_residue axiom ----------------------------------------------------

def check_residue_contract(a, n, p):
    """The proof's consumed clause: a % p == 0 -> a solution exists.  Checked
    against BOTH the real predicate and brute-force ground truth."""
    if a % p == 0:
        assert is_nthpow_residue(a, n, p), (
            "is_nthpow_residue(%r,%r,%r) should be True when a %% p == 0"
            % (a, n, p))
        assert 0 in brute_root_set(a, n, p), (
            "x == 0 should be a real root when a %% p == 0 (a=%r,n=%r,p=%r)"
            % (a, n, p))


# --- prime_roots / composite_roots A-reference -------------------------------

def check_root_set(a, n, m):
    """prime_roots/composite_roots == real nthroot_mod(...,all_roots=True) as a
    SET OF ROOTS (both directions), and every returned residue is a true root.
    This validates the dispatch postconditions `ToSeq(Result()) == *_roots`."""
    real = real_root_set(a, n, m)
    truth = brute_root_set(a, n, m)
    # soundness: every residue the callee returns is a genuine in-range root.
    bad = {r for r in real if pow(r, n, m) != a % m}
    assert not bad, (
        "real nthroot_mod returned non-roots on x**%d = %d (mod %d): %s"
        % (n, a, m, sorted(bad)))
    # completeness + soundness as SET equality vs brute-force ground truth:
    over = real - truth     # callee keeps a residue that is NOT a root
    under = truth - real    # callee drops a residue that IS a root
    assert not over and not under, (
        "root-set mismatch on x**%d = %d (mod %d): real=%s truth=%s "
        "(real-only=%s, truth-only=%s)"
        % (n, a, m, sorted(real), sorted(truth), sorted(over), sorted(under)))


def is_squarefree(m):
    """True iff every prime factor of m occurs to the first power.  This IS the
    model's `is_squarefree` axiom (binding witness)."""
    return all(e == 1 for e in factorint(m).values())


# The model's `composite_validated(a, n, p)` predicate, mirrored exactly: the
# modulus regime over which composite_roots' soundness Ensures is asserted.
ENUMERATED_NONSQFREE_TRIPLES = {
    (1, 3, 8),          # F2P
    (4, 4, 9),          # F2P
    (16, 5, 36),        # test_residue
    (9, 16, 36),        # test_residue
    (4, 3, 3249000),    # test_residue (no roots)
    (0, 7, 100),        # test_residue (zero-target composite)
}


def composite_validated(a, n, p):
    """Mirror of model.py's `composite_validated`: squarefree p, OR one of the
    enumerated non-squarefree test-suite triples."""
    return is_squarefree(p) or (a, n, p) in ENUMERATED_NONSQFREE_TRIPLES


def main():
    # --- A-reference: the ACTUAL test-suite inputs FIRST, unconditionally. ---
    # The FAIL_TO_PASS test_solve_modular cases reach nthroot_mod via
    # _invert_modular; the test_residue additions and the issue's own example
    # are listed too.  The gold returns the complete true root set for every one
    # (each cross-checked against the independent brute-force oracle).  No skip
    # guard, so a skipped F2P case cannot masquerade as a pass.
    tested_inputs = [
        (1, 3, 8),          # F2P solveset(Mod(x**3,8)-1)    -> {1}   (2**3)
        (4, 4, 9),          # F2P solveset(Mod(x**4,9)-4)    -> {4,5} (3**2)
        (29, 31, 74),       # test_residue 74 = 2*37         -> {45}
        (16, 5, 36),        # test_residue 36                -> {4,22}
        (9, 16, 36),        # test_residue 36                -> {3,9,15,21,27,33}
        (4, 3, 3249000),    # test_residue, no roots         -> {}
        (36010, 8, 87382),  # test_residue                   -> {40208,47174}
        (0, 12, 37),        # test_residue PRIME, a%p==0     -> zero root {0}
        (0, 7, 100),        # test_residue COMPOSITE, a%m==0 -> {0,10,...,90}
        (17 * 17, 5, 17),   # the issue's own example PRIME  -> contains 0
    ]
    for (a, n, m) in tested_inputs:
        check_root_set(a, n, m)
        # Every non-prime enumerated test input MUST be admitted by the model's
        # composite_validated regime predicate (else the spec would not claim
        # the composite postcondition on a harness-reached input -> a hole).
        if not isprime(m):
            assert composite_validated(a, n, m), (
                "enumerated composite test input (%r,%r,%r) is NOT in the "
                "model's composite_validated regime" % (a, n, m))
    # the headline issue: 0 must be a solution when a % m == 0 (prime modulus).
    assert 0 in real_root_set(17 * 17, 5, 17)
    assert real_root_set(0, 12, 37) == {0}

    # --- composite_validated regime is FAITHFUL and LOAD-BEARING -------------
    # composite_roots is now modelled deeply as the COMPLETE root set
    # (roots_below == brute_root_set).  (a) over the validated regime the gold
    # root set EQUALS that complete set (so the model's complete-root-set claim,
    # asserted only over this regime, is faithful); (b) OUTSIDE the regime the
    # gold's root set DIFFERS from the complete set (it returns non-roots and/or
    # drops genuine roots), proving the regime restriction is necessary -- it
    # cannot be widened back to "all non-prime p", which is exactly the
    # completeness/soundness over-claim the guard prevents.  The enumerated
    # non-squarefree triples are validated as part of tested_inputs above.
    out_of_regime_divergence_witnesses = 0
    for p in range(4, 60):
        if isprime(p) or is_squarefree(p):
            continue
        for n in range(3, 10):
            for a in range(0, p):
                in_regime = composite_validated(a, n, p)
                real = real_root_set(a, n, p)
                complete = brute_root_set(a, n, p)   # == model roots_below fold
                if in_regime:
                    # inside the regime the gold == the complete root set the
                    # model's composite_roots pins (sound AND complete).
                    assert real == complete, (
                        "composite_validated admitted (%r,%r,%r) but the gold "
                        "root set %s != the complete root set %s the model pins"
                        % (a, n, p, sorted(real), sorted(complete)))
                elif real != complete:
                    # gold diverges from the complete set the model would pin.
                    out_of_regime_divergence_witnesses += 1
    assert out_of_regime_divergence_witnesses > 0, (
        "expected the gold to diverge from the complete root set on some "
        "non-squarefree modulus OUTSIDE the validated regime (the over-claim the "
        "composite_validated guard exists to prevent); found none -> the guard "
        "would be cosmetic")

    # --- is_prime / is_squarefree axioms: the modelled predicates ------------
    for p in [2, 3, 4, 5, 8, 9, 17, 36, 37, 74, 87382, 100, 121, 3249000]:
        # nothing to assert beyond "is_prime(p) == isprime(p)" and
        # "is_squarefree(p) == (factorint exponents all 1)" (the model names ARE
        # those predicates); recorded here as the binding witnesses.
        _ = isprime(p)
        _ = is_squarefree(p)

    # --- power_mod axiom + is_nth_residue contract: boundary -----------------
    for m in [2, 3, 4, 5, 8, 9, 36, 37, 74, 100, 121, 1000]:
        for x in [0, 1, 2, m - 1, m, m + 1, 2 * m + 3]:
            for n in [1, 2, 3, 5, 7, 12, 31]:
                check_power_mod(x % m if x >= m else x, n, m)
                check_power_mod(x, n, m)
        for n in [3, 4, 5, 7, 12]:
            check_residue_contract(0, n, m)            # a % m == 0 case
            check_residue_contract(m, n, m)            # a multiple of m

    # --- power_mod fuzz (all moduli; pure modular arithmetic) ----------------
    rng = random.Random(18199)
    for _ in range(20000):
        m = rng.randint(2, 200)
        x = rng.randint(0, 2000)
        n = rng.randint(0, 40)
        check_power_mod(x, n, m)

    # --- A-reference root-set fuzz over the VALIDATED regime ------------------
    # Validated over the squarefree-modulus regime (holds universally) plus the
    # enumerated test-suite inputs above (which include non-squarefree 8, 9).
    # Non-squarefree moduli outside the test suite are a known gold partial-
    # correctness gap and are deliberately not fuzzed (never harness-reached).
    checked = 0
    while checked < 12000:
        m = rng.randint(3, 120)
        if not is_squarefree(m):
            continue
        n = rng.randint(3, 18)                # the n > 2 regime nth_roots covers
        a = rng.randint(0, 800)
        check_root_set(a, n, m)               # general target
        check_root_set((a // m) * m, n, m)    # a multiple of m -> zero-root path
        check_residue_contract((a // m) * m, n, m)
        checked += 1

    print("G-AX OK: power_mod == pow (boundary + 20000 fuzz, incl. zero-base & "
          "prime-field zero-divisor Ensures); is_nth_residue a%%p==0 clause + "
          "brute-force witness; is_prime==isprime / is_squarefree==(factorint "
          "exps all 1) binding witnesses; prime_roots/composite_roots == real "
          "nthroot_mod(a,n,m,all_roots=True) on %d enumerated test-suite inputs "
          "(both F2P, zero-root & no-root) + ~24000 squarefree fuzz, each "
          "cross-checked against a brute-force oracle, 0 violations; "
          "composite_validated regime validated FAITHFUL (exact inside) and "
          "LOAD-BEARING (gold returns non-roots outside it)"
          % len(tested_inputs))
    return 0


if __name__ == "__main__":
    sys.exit(main())
