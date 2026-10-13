#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-24443 (nagini).

SHADOW: the impl region of model.py, copied VERBATIM below with the contract
calls (Requires/Ensures/Invariant/Assert) stripped. The model is Python, so
`relator_image` runs directly. Its three @ContractOnly callees are realized by
the REAL repo operations they model (mapping.md section 1/3.1):

    gid()      -> the codomain group's identity element
    gmul(a, b) -> group element __mul__  (a * b)
    gpow(g, e) -> group element __pow__  (g ** e, total over negative e)

The @Pure helper `image_fold` copies over as a plain function with PSeq
realized as an immutable tuple shim (it is contract-only in model.py; here it
doubles as a self-consistency probe on the boundary set).

ORACLE: the REAL patched repo function per mapping.md — the per-relator image
computation nested inside `sympy.combinatorics.homomorphisms
._check_homomorphism`. The nested helper is not importable by name, so the
oracle is the enclosing `_check_homomorphism(domain, codomain, images)`
itself: for a PermutationGroup codomain its boolean verdict is exactly
"every relator's image is the identity", i.e. the modeled function's output
compared against the identity, relator by relator. The gate applies patch.diff
to /testbed before this script runs; PYTHONPATH=/testbed imports the patched
module.

Type bridge (mapping.md section 2): model.py carries a relator as two parallel
List[int] block arrays — block_elems[k] the codomain element resolved for
block k's generator, block_pows[k] its (possibly negative) exponent — with
codomain elements as opaque handles. Here the handles are the real group
elements, and each relator's blocks are resolved through the unchanged TOTAL
lookup chain (relator symbol -> domain generator -> its assigned image), the
same resolution axiom_check.py uses. The shadow verdict is
`all(relator_image(elems, pows) == identity)` over the domain's relators; it
must equal the oracle's boolean on every input.

Input domain: Requires demands two equal-length lists — every resolved relator
satisfies it by construction, and relators routinely contain negative-exponent
(inverted-generator) blocks, the discriminating case. Cases are PermutationGroup
self-maps (domain == codomain) with arbitrary generator->element assignments,
so both accepting and rejecting verdicts occur. (FpGroup codomains route the
verdict through a rewriting-system equality — a different observable than the
modeled per-relator image — so they are exercised by axiom_check.py / G-AX,
not here.)

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz cases, each
case evaluating relator_image once per relator of the domain (several
Requires-satisfying inputs per case). Pinned fuzz seed: 24443.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + sympy (the repo under test) only.
"""
import json
import random
import sys

SEED = 24443
N_FUZZ = 100_000

# --- the real callee bindings for the @ContractOnly axioms -------------------
# gid() reads the current codomain identity from this module-level slot, set
# once per case before the shadow runs (the model treats it as an opaque
# constant of the codomain).
_IDENTITY = None


def gid():
    return _IDENTITY            # real codomain identity element


def gmul(a, b):
    return a * b                # real group element product


def gpow(g, e):
    return g ** e               # real group element integer power


# --- PSeq shim + the @Pure helper from model.py, contracts stripped ----------

class PSeqShim:
    __slots__ = ("_t",)

    def __init__(self, items=()):
        self._t = tuple(items)

    def drop(self, n):
        return PSeqShim(self._t[n:])

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]


def image_fold(acc, elems, pows):
    if len(elems) == 0:
        return acc
    return image_fold(gmul(acc, gpow(elems[0], pows[0])),
                      elems.drop(1), pows.drop(1))


# --- the impl region of model.py, verbatim, contract calls stripped ----------

def relator_image(block_elems, block_pows):
    w = gid()
    i = 0
    while i < len(block_elems):
        w = gmul(w, gpow(block_elems[i], block_pows[i]))
        i = i + 1
    return w


# --- bridge: resolve a relator into the model's two parallel block arrays ----

def blocks_for(domain, images, r):
    """block_elems[k] = the codomain element assigned to block k's generator,
    block_pows[k] = block k's exponent — the unchanged total resolution chain
    (mapping.md section 2; identical to axiom_check.py's resolution)."""
    pres = domain if hasattr(domain, 'relators') else domain.presentation()
    gens = pres.generators
    symbols = [g.ext_rep[0] for g in gens]
    lookup = dict(zip(symbols, domain.generators))
    elems, pows = [], []
    for symbol, power in r.array_form:
        elems.append(images[lookup[symbol]])
        pows.append(power)
    return elems, pows


def relators_of(domain):
    pres = domain if hasattr(domain, 'relators') else domain.presentation()
    return list(pres.relators)


def shadow_verdict(domain, codomain, images):
    """Run the SHADOW relator_image on every relator's resolved blocks and
    require each image to be the identity. Returns (bool, n_inputs)."""
    global _IDENTITY
    _IDENTITY = codomain.identity
    n = 0
    ok = True
    for r in relators_of(domain):
        elems, pows = blocks_for(domain, images, r)
        assert len(elems) == len(pows)      # the Requires holds by construction
        w = relator_image(elems, pows)
        n += 1
        if ok and w != _IDENTITY:
            ok = False
    return ok, n


def check_case(oracle, domain, images):
    """One (domain, images) case: shadow vs the REAL patched repo function.
    Returns (err_or_None, n_relator_inputs)."""
    s, n = shadow_verdict(domain, domain, images)
    o = bool(oracle(domain, domain, images))
    if s != o:
        return ("DISAGREEMENT\n  domain=%r\n  images=%s\n  shadow=%r real=%r"
                % (domain, {str(k): str(v) for k, v in images.items()}, s, o),
                n)
    return None, n


def build_groups():
    from sympy.combinatorics.named_groups import (
        DihedralGroup, CyclicGroup, SymmetricGroup, AlternatingGroup)
    groups = []
    for n in (3, 4, 5, 6):
        groups.append(DihedralGroup(n))
    for n in (2, 4, 5, 6, 7):
        groups.append(CyclicGroup(n))
    for n in (3, 4):
        groups.append(SymmetricGroup(n))
    for n in (4, 5):
        groups.append(AlternatingGroup(n))
    for g in groups:
        g.presentation()        # warm the cached presentation once
    return groups


def main():
    from sympy.combinatorics.homomorphisms import _check_homomorphism  # REAL

    rng = random.Random(SEED)
    groups = build_groups()
    elements = {id(g): list(g.elements) for g in groups}

    checked_cases = 0
    checked_inputs = 0
    saw_negative = False

    # boundary: for every group, the identity self-map (accepting) and the
    # all-identity map (accepting); plus the fold self-consistency probe.
    global _IDENTITY
    for g in groups:
        for images in (dict(zip(g.generators, g.generators)),
                       {gen: g.identity for gen in g.generators}):
            err, n = check_case(_check_homomorphism, g, images)
            if err:
                print(err)
                return 1
            checked_cases += 1
            checked_inputs += n
            # pure-region probe: the verbatim loop equals the fold spec
            _IDENTITY = g.identity
            for r in relators_of(g):
                elems, pows = blocks_for(g, images, r)
                if any(p < 0 for p in pows):
                    saw_negative = True
                if relator_image(elems, pows) != image_fold(
                        gid(), PSeqShim(elems), PSeqShim(pows)):
                    print("SELF-INCONSISTENCY: impl loop != pure fold on %r" % (r,))
                    return 1

    assert saw_negative, ("no negative-exponent block exercised on the "
                          "boundary set — the discriminating case is missing")

    # fuzz: arbitrary generator->element self-map assignments (mostly rejecting,
    # occasionally accepting), pinned seed.
    for _ in range(N_FUZZ):
        g = rng.choice(groups)
        pool = elements[id(g)]
        images = {gen: rng.choice(pool) for gen in g.generators}
        err, n = check_case(_check_homomorphism, g, images)
        if err:
            print(err)
            return 1
        checked_cases += 1
        checked_inputs += n

    print("G-CONF OK: shadow impl (verbatim model.py impl region, real group "
          "ops for the opaque callees) == real patched verdict on %d cases / "
          "%d relator inputs (seed %d), 0 disagreements."
          % (checked_cases, checked_inputs, SEED))
    print(json.dumps({"checked": checked_cases,
                      "relator_inputs": checked_inputs,
                      "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
