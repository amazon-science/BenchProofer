#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-24443 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs.

The modeled function is the internal `_image(r)` of
`sympy.combinatorics.homomorphisms._check_homomorphism` — the value of a relator
`r` under a generator→image assignment, computed as the ordered group product of
each syllable's image raised to that syllable's (signed) exponent. In
Solution.lean this is `evalWord` / `wordProd`. The observable behaviour of the
whole change is the True/False verdict of `_check_homomorphism`: every relator's
image must be the codomain identity.

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* repo types (PermutationGroup,
              Permutation), via the mapping.md bijection:
                assign : Nat → G        ↔  symbol -> domain generator -> image
                syllables              ↔  r.array_form  ((symbol, power), ...)
                wordProd assign s      ↔  product_{k} images[gen(symbol_k)]**power_k
                wordProd ... = 1       ↔  image.is_identity
              There are NO A-tagged callees: `_image` is the *changed* operation,
              modeled deeply (not behind an axiom), so the impl region is pure
              R/I and this whole shadow is in G-CONF's scope.
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `_check_homomorphism(domain, codomain, images)` applied at
              base_commit (the real correctness oracle, G-RESOLVE). The harness
              applies patch.diff before this script runs.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + sympy only.
The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.

Restricted to PermutationGroup domain == codomain: that is the scenario the
issue and the F2P test (`test_homomorphism`, `homomorphism(D3, D3, ...)`)
exercise, and the one whose verdict is exactly `all(_image(r).is_identity)` —
matching the deep model. (FpGroup codomains route through `codomain.equals` /
`make_confluent`, a different observable that the modeled op does not cover.)
"""
import random
import sys

SEED = 24443
N_FUZZ = 100_000


def _build_groups():
    """A spread of PermutationGroups whose presentations carry relators with
    negative exponents (the discriminating syllables the bug dropped)."""
    from sympy.combinatorics.named_groups import (
        DihedralGroup, CyclicGroup, SymmetricGroup, AlternatingGroup)
    groups = []
    for n in (3, 4, 5, 6):
        groups.append(DihedralGroup(n))
    for n in (4, 5, 6, 7):
        groups.append(CyclicGroup(n))
    for n in (3, 4):
        groups.append(SymmetricGroup(n))
    for n in (4, 5):
        groups.append(AlternatingGroup(n))
    # warm the (cached) presentations once so per-check work is just arithmetic
    for g in groups:
        g.presentation()
    return groups


def shadow_verdict(domain, codomain, images):
    """The R/I shadow of Solution.lean's impl: for every relator, fold the
    ordered group product over its array_form syllables (wordProd) and require
    the result to be the identity.  Pure transliteration of evalWord/wordProd;
    uses only the real sympy group arithmetic (the R-refinement targets)."""
    pres = domain if hasattr(domain, 'relators') else domain.presentation()
    rels = pres.relators
    gens = pres.generators
    symbols = [g.ext_rep[0] for g in gens]
    symbols_to_domain_generators = dict(zip(symbols, domain.generators))
    identity = codomain.identity
    for r in rels:
        w = identity                                  # wordProd ... [] = 1
        for symbol, power in r.array_form:            # front-to-back syllables
            g = symbols_to_domain_generators[symbol]
            w = w * images[g] ** power                # assign sym ^ p * rest
        if not w.is_identity:                         # wordProd ... = 1 ?
            return False
    return True


def oracle_verdict(domain, codomain, images):
    """patch.diff's behaviour: the patched `_check_homomorphism`."""
    from sympy.combinatorics.homomorphisms import _check_homomorphism
    return bool(_check_homomorphism(domain, codomain, images))


def main():
    rng = random.Random(SEED)
    groups = _build_groups()
    # cache each group's element list (the codomain image pool)
    elements = {id(g): list(g.elements) for g in groups}

    disagreements = []
    count = 0

    # boundary cases first (plan §4.1 step 4): the identity assignment on each
    # group (a genuine isomorphism — the exact F2P scenario for D3) and the
    # all-identity assignment (the trivial homomorphism).
    boundary = []
    for g in groups:
        boundary.append((g, dict(zip(g.generators, g.generators))))
        boundary.append((g, {gen: g.identity for gen in g.generators}))
    for g, images in boundary:
        count += 1
        s = shadow_verdict(g, g, images)
        o = oracle_verdict(g, g, images)
        if s != o:
            disagreements.append((repr(g), {str(k): str(v) for k, v in images.items()}, s, o))

    # randomized fuzz: arbitrary generator->element assignments (mostly NOT
    # homomorphisms, exercising the False branch; occasionally genuine, via the
    # identity/automorphism draws above and random hits).
    for _ in range(N_FUZZ):
        g = rng.choice(groups)
        pool = elements[id(g)]
        images = {gen: rng.choice(pool) for gen in g.generators}
        count += 1
        s = shadow_verdict(g, g, images)
        o = oracle_verdict(g, g, images)
        if s != o:
            disagreements.append((repr(g),
                                  {str(k): str(v) for k, v in images.items()}, s, o))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for grp, imgs, s, o in disagreements:
            print("  group=%s images=%s shadow=%r oracle=%r" % (grp, imgs, s, o))
        return 1
    print("G-CONF OK: R/I shadow of evalWord (_image group product) agrees with "
          "patch.diff behaviour on %d inputs (seed=%d), 0 disagreements."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
