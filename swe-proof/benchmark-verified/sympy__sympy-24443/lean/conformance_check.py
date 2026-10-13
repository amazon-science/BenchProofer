#!/usr/bin/env python
"""G-CONF: differential conformance for sympy__sympy-24443.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). Diffs the Python R/I shadow of the Lean
`implementation_checkRelators` skeleton against the REAL post-patch routine

    sympy.combinatorics.homomorphisms._check_homomorphism(domain, codomain, images)

over a boundary set plus >= 1e5 randomized (domain, generator→image) candidates.

  shadow of `implementation_checkRelators`   vs   real post-patch _check_homomorphism
  observable: the boolean "does this map of generators define a homomorphism".

The modeled function decides whether a valuation of the domain's generators
extends to a homomorphism by checking that EVERY defining relator word evaluates
to the codomain identity. The Lean inputs abstract the unchanged scaffold the
real routine computes once up front:

  * `rels`   <-  pres.relators                 (each relator's `.array_form`,
                 a list of (symbol, power) pairs)             -- I (verbatim shape)
  * `genOf`  <-  symbols_to_domain_generators  (relator symbol -> domain generator)
  * `imageOf`<-  images                        (domain generator -> codomain elem)

The shadow rebuilds those three from the SAME real objects, then transliterates
the Lean loop EXACTLY: for each relator word, fold the ordered product
`w *= images[genOf(symbol)] ** power`, and reject (return False) on the first
word whose product is not the codomain identity; accept otherwise. The compared
observable is the final boolean.

Domains/codomains are small PermutationGroups (the issue's setting); images are
drawn so that BOTH genuine homomorphisms (e.g. the identity map, the bug report's
exact `homomorphism(D3, D3, D3.generators, D3.generators)`) and non-homomorphisms
occur, and relators routinely contain inverted generators (negative powers) — the
discriminating case the fix repairs.

Exit 0 iff zero disagreements. stdlib + sympy only; pinned seed.
"""
import random
import sys

SEED = 24443
N_RANDOM = 120_000   # >= 1e5


def real_outcome(domain, codomain, images):
    """The REAL post-patch _check_homomorphism boolean (or a tagged exception)."""
    from sympy.combinatorics.homomorphisms import _check_homomorphism
    try:
        return ("ok", bool(_check_homomorphism(domain, codomain, images)))
    except Exception as e:                       # e.g. RuntimeError on FpGroup
        return ("exc", type(e).__name__)


def shadow_outcome(domain, codomain, images):
    """Transliteration of `implementation_checkRelators`.

    Rebuild (rels, genOf, imageOf) from the same real objects the post-patch
    routine uses, then mirror the Lean skeleton: per-relator product fold over
    `.array_form`, early-reject on the first non-identity word."""
    try:
        pres = domain if hasattr(domain, 'relators') else domain.presentation()
        rels = pres.relators
        gens = pres.generators
        symbols = [g.ext_rep[0] for g in gens]
        genOf = dict(zip(symbols, domain.generators))      # symbol -> domain generator
        identity = codomain.identity
        for r in rels:                                     # for r in rels do
            w = identity
            for symbol, power in r.array_form:             # for (s,p) in r do
                g = genOf[symbol]
                w = w * images[g] ** power                 # w := w * imageOf g ^ p
            if w != identity:                              # if w ≠ 1 then
                return ("ok", False)                       #   return false
        return ("ok", True)                                # return true
    except Exception as e:
        return ("exc", type(e).__name__)


def build_groups():
    from sympy.combinatorics.named_groups import (
        DihedralGroup, CyclicGroup, SymmetricGroup, AlternatingGroup,
    )
    groups = []
    for n in (3, 4, 5):
        groups.append(DihedralGroup(n))
    for n in (2, 3, 4, 5, 6):
        groups.append(CyclicGroup(n))
    for n in (3, 4):
        groups.append(SymmetricGroup(n))
    for n in (3, 4):
        groups.append(AlternatingGroup(n))
    return groups


def random_images(G, H, rng):
    """A dict {g: h} sending each generator of G to a random element of H.

    Elements are sampled from H by random words in H's generators (so inverses /
    negative powers are well exercised), occasionally the identity, and
    occasionally H's own generators (to hit genuine (iso)morphisms when G==H)."""
    Hgens = H.generators
    images = {}
    for i, g in enumerate(G.generators):
        choice = rng.random()
        if choice < 0.25 and len(Hgens) >= 1:
            # mirror generator (identity map when G is H)
            images[g] = Hgens[i % len(Hgens)]
        elif choice < 0.35:
            images[g] = H.identity
        else:
            h = H.identity
            for _ in range(rng.randint(1, 4)):
                gen = rng.choice(Hgens)
                p = rng.choice([-2, -1, 1, 2])
                h = h * gen ** p
            images[g] = h
    return images


def main():
    rng = random.Random(SEED)
    groups = build_groups()

    cases = []  # (domain, codomain, images)

    # the bug report's exact example: identity map D3 -> D3
    from sympy.combinatorics.named_groups import DihedralGroup
    D3 = DihedralGroup(3)
    cases.append((D3, D3, {g: g for g in D3.generators}))

    # boundary: identity self-maps for every group (always a homomorphism)
    for G in groups:
        cases.append((G, G, {g: g for g in G.generators}))
        # trivial map: everything to identity (always a homomorphism)
        cases.append((G, G, {g: G.identity for g in G.generators}))

    # fuzz: random images, domain==codomain (so the map is type-compatible)
    for _ in range(N_RANDOM):
        G = rng.choice(groups)
        cases.append((G, G, random_images(G, G, rng)))

    disagreements = 0
    checked = 0
    for domain, codomain, images in cases:
        got = real_outcome(domain, codomain, images)
        exp = shadow_outcome(domain, codomain, images)
        checked += 1
        # tolerate identical exception tags (both legs hit the same scaffold limit)
        if got != exp:
            disagreements += 1
            if disagreements <= 5:
                print(f"MISMATCH domain={domain} images={images}: "
                      f"real={got!r} shadow={exp!r}")

    print(f"checked={checked} disagreements={disagreements}")
    if disagreements == 0:
        print(f"status=pass conformance OK ({checked} checks, 0 disagreements, "
              f"seed={SEED})")
        return 0
    print(f"status=fail {disagreements} disagreement(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
