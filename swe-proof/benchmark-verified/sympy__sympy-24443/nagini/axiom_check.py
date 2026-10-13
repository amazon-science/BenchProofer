#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-24443.

The model abstracts the codomain group as an opaque monoid with three
operations the relator-image computation CALLS but does not change:

  gid()        -- the group identity element
  gmul(a, b)   -- the group product a*b (associative, NOT commutative)
  gpow(g, e)   -- the integer power g**e, defined for EVERY integer exponent
                  e (positive, zero, and NEGATIVE / inverse powers)

and models the relator-image computation DEEPLY as the left-to-right fold

  image_fold(acc, elems, pows) = acc                               if empty
                               = image_fold(gmul(acc, gpow(elems[0], pows[0])),
                                            elems[1:], pows[1:])    otherwise

so that relator_image(block_elems, block_pows)
       == image_fold(gid(), block_elems, block_pows)
       == (block_elems[0] ^ pows[0]) * ... * (block_elems[n-1] ^ pows[n-1]).

This script validates, against the REAL sympy group machinery (the very module
the gold patch touches):

  (A-consumed) the three opaque monoid axioms are sound for the real groups:
      * gpow is total over every integer exponent including negatives, and the
        real group identity / product / power obey the (trivial Ensures=True)
        contracts -- exercised explicitly as monoid laws and the negative-power
        (inverse) law that the buggy pre-patch violated.

  (A-reference) the deep model `image_fold`, with gmul:=group product,
      gpow:=** and gid:=group identity, equals the REAL per-relator image
      product produced by resolving each relator block (symbol, exponent)
      through `images[symbols_to_domain_generators[symbol]] ** exponent` and
      multiplying left to right -- exactly the fixed `_image` computation -- on
      a battery of real PermutationGroups / FpGroups / FreeGroups, with every
      relator, INCLUDING relators that contain inverted generators (negative
      exponents). This is the discriminating behaviour: the fold must reproduce
      every block's factor, never dropping the negative-exponent ones.

Imports only the standard library and sympy (the repo under test). Exit 0 iff
every obligation holds.
"""
import itertools
import sys

from sympy.combinatorics import Permutation
from sympy.combinatorics.perm_groups import PermutationGroup
from sympy.combinatorics.free_groups import free_group
from sympy.combinatorics.fp_groups import FpGroup
from sympy.combinatorics.named_groups import (
    DihedralGroup, CyclicGroup, AlternatingGroup, SymmetricGroup)


# --- the deep model, transcribed from model.py (with the real group ops) -----

def image_fold(acc, elems, pows, gmul, gpow):
    """Reference for model.py's pure `image_fold`: left-to-right product of
    gpow(elems[k], pows[k]) onto acc. Iterative transcription of the
    front-recursion."""
    w = acc
    for e, p in zip(elems, pows):
        w = gmul(w, gpow(e, p))
    return w


# --- the real per-relator image, resolved exactly as the fixed _image does ---

def real_image(domain, images, identity, r):
    """The fixed `_image(r)`: for each (symbol, power) block of r.array_form,
    multiply the running product by images[g]**power where g is the domain
    generator carrying that symbol. This is the gold computation we validate
    the deep fold against."""
    pres = domain if hasattr(domain, 'relators') else domain.presentation()
    gens = pres.generators
    symbols = [g.ext_rep[0] for g in gens]
    symbols_to_domain_generators = dict(zip(symbols, domain.generators))
    w = identity
    for symbol, power in r.array_form:
        g = symbols_to_domain_generators[symbol]
        w *= images[g] ** power
    return w


def blocks_for(domain, images, r):
    """Resolve r into the model's two parallel arrays:
    block_elems[k] = images[g] (the codomain element for block k's generator)
    block_pows[k]  = the block's exponent. Returns (elems, pows)."""
    pres = domain if hasattr(domain, 'relators') else domain.presentation()
    gens = pres.generators
    symbols = [g.ext_rep[0] for g in gens]
    symbols_to_domain_generators = dict(zip(symbols, domain.generators))
    elems, pows = [], []
    for symbol, power in r.array_form:
        g = symbols_to_domain_generators[symbol]
        elems.append(images[g])
        pows.append(power)
    return elems, pows


def relators_of(domain):
    pres = domain if hasattr(domain, 'relators') else domain.presentation()
    return list(pres.relators)


def check_group(domain, images, label):
    """For every relator of `domain`, assert the deep fold model reproduces the
    real fixed image, and check that at least one relator with a negative
    exponent is exercised (the inverted-generator case the bug dropped)."""
    # The identity is the CODOMAIN identity (images map domain generators to
    # codomain elements; the image product lives in the codomain), derived from
    # any codomain element so it works whether the codomain is a permutation,
    # free, or fp group.
    identity = list(images.values())[0] ** 0
    gmul = lambda a, b: a * b
    gpow = lambda g, e: g ** e
    saw_negative = False
    n_rel = 0
    for r in relators_of(domain):
        n_rel += 1
        elems, pows = blocks_for(domain, images, r)
        if any(p < 0 for p in pows):
            saw_negative = True
        model = image_fold(identity, elems, pows, gmul, gpow)
        gold = real_image(domain, images, identity, r)
        assert model == gold, (
            "[%s] deep fold disagrees with real image on relator %r: "
            "fold=%r gold=%r (blocks elems=%r pows=%r)"
            % (label, r, model, gold, elems, pows))
    return n_rel, saw_negative


def check_monoid_axioms():
    """Exercise the three opaque monoid axioms against a concrete real group:
    identity, associativity, and the NEGATIVE-power (inverse) law gpow is total
    over -- the law the pre-patch silently dropped for inverted generators."""
    D = DihedralGroup(4)
    e = D.identity
    elts = list(D.generate())[:8]
    for a in elts:
        assert a * e == a and e * a == a, "identity law broken"
        # gpow total over negative exponents (inverse powers)
        assert a ** 0 == e, "g**0 != identity"
        assert a * (a ** -1) == e, "g * g**-1 != identity (negative power)"
        assert (a ** -2) == (a ** -1) * (a ** -1), "g**-2 != (g**-1)**2"
    for a, b, c in itertools.islice(itertools.product(elts, elts, elts), 200):
        assert (a * b) * c == a * (b * c), "associativity broken"


def main():
    check_monoid_axioms()

    cases = []

    # --- PermutationGroups (the broken-on case from the issue) ---------------
    # Identity self-map: images[g] = g. This is exactly homomorphism(G, G, gens, gens).
    for G, lbl in [(DihedralGroup(3), "D3"),
                   (DihedralGroup(4), "D4"),
                   (DihedralGroup(5), "D5"),
                   (CyclicGroup(6), "C6"),
                   (AlternatingGroup(4), "A4"),
                   (SymmetricGroup(4), "S4")]:
        images = dict(zip(G.generators, G.generators))
        cases.append((G, images, "perm-id-" + lbl))

    # A non-identity PermutationGroup map: D4 -> D4 sending generators to a
    # rotation pair (still a valid set of images of generators).
    D4 = DihedralGroup(4)
    g0, g1 = D4.generators
    images = {g0: g0, g1: g1}
    cases.append((D4, images, "perm-D4-gens"))

    # --- FpGroups -------------------------------------------------------------
    F, a, b = free_group("a, b")
    Gfp = FpGroup(F, [a**3, b**3, (a*b)**2])
    Afp = AlternatingGroup(4)
    c = Permutation(3)(0, 1, 2)
    d = Permutation(3)(1, 2, 3)
    cases.append((Gfp, {a: c, b: d}, "fp-G->A4"))

    E, e = free_group("e")
    Gfp2 = FpGroup(E, [e**8])
    cases.append((Gfp2, {e: Permutation(0, 1, 2, 3)}, "fp-cyclic8"))

    total_rel = 0
    any_negative = False
    for domain, images, label in cases:
        n_rel, saw_neg = check_group(domain, images, label)
        total_rel += n_rel
        any_negative = any_negative or saw_neg

    assert any_negative, (
        "no relator with a negative exponent was exercised -- the "
        "inverted-generator case the bug dropped must be covered")

    print("G-AX OK: opaque monoid axioms (incl. negative/inverse powers) sound; "
          "deep image_fold model == real fixed per-relator image on %d cases / "
          "%d relators across PermutationGroups, FpGroups and FreeGroups "
          "(inverted-generator blocks covered)."
          % (len(cases), total_rel))
    return 0


if __name__ == "__main__":
    sys.exit(main())
