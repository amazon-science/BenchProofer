#!/usr/bin/env python3
"""G-AX executable soundness check for sphinx-doc__sphinx-10673.

This bundle consumes NO @ContractOnly axiom: the classification of a listed
target is modelled DEEPLY in model.py (the pure `mem` / `known` / `kept` folds
over PSeq[int]). The single A-reference to validate is therefore that the deep
model agrees with the real set-membership semantics the patched code uses, i.e.

    a listed target is retained  <=>  its name is in  found_docs UNION generated

where in the real code `found_docs` is the set of discovered source documents
and `generated` is the set of always-provided reference-page names
(frozenset(self.env.domains['std'].initial_data['labels'].keys()) ==
{'genindex', 'modindex', 'search'}), and the membership test is exactly
`docname in self.env.found_docs | generated_docnames`.

We reproduce the deep model (`kept`) as a list-of-int reference and assert it is
equal, over boundary + randomized fuzz inputs, to the real Python set-union /
membership semantics — the very operation the patched `parse_content` performs.

We also assert the concrete F2P scenario: with the three real reference-page
names present in `generated` but absent from `found`, all three are retained in
order (the pre-patch behaviour dropped them). Imports are stdlib-only. Exit 0
iff every obligation holds.
"""
import random
import sys


# --- model.py reference encodings (kept in lock-step with the deep model) ----

def mem(x, s):
    """Reference for model.py's `mem`: membership in a sequence."""
    for e in s:
        if e == x:
            return True
    return False


def known(x, found, gen):
    """Reference for model.py's `known`: in EITHER family."""
    return mem(x, found) or mem(x, gen)


def kept(entries, found, gen):
    """Reference for model.py's `kept`: order-preserving retention filter."""
    out = []
    for e in entries:
        if known(e, found, gen):
            out.append(e)
    return out


# --- the real semantics: set union + membership (what parse_content does) ----

def real_select(entries, found, gen):
    """The real classification: retain a target iff its name is in the union of
    the discovered documents and the generated reference pages, in order.
    Mirrors `docname in self.env.found_docs | generated_docnames`."""
    universe = set(found) | set(gen)          # the real `found_docs | generated`
    return [e for e in entries if e in universe]


# --- the checks --------------------------------------------------------------

def check(entries, found, gen):
    model = kept(entries, found, gen)
    real = real_select(entries, found, gen)
    assert model == real, (
        "deep model `kept` disagrees with real set-union membership on "
        "entries=%r found=%r gen=%r: model=%r real=%r"
        % (entries, found, gen, model, real))


def main():
    # --- concrete F2P scenario -------------------------------------------------
    # Distinct int ids standing in for the document names. The three generated
    # reference pages (genindex/modindex/search) are present in `generated` but
    # absent from `found`; an ordinary discovered document `foo` is in `found`.
    FOO, GENINDEX, MODINDEX, SEARCH = 1, 100, 101, 102
    found = [FOO]
    generated = [GENINDEX, MODINDEX, SEARCH]
    entries = [GENINDEX, MODINDEX, SEARCH]
    result = kept(entries, found, generated)
    assert result == [GENINDEX, MODINDEX, SEARCH], (
        "F2P scenario broken: the three generated reference pages must all be "
        "retained, in order; got %r" % (result,))
    check(entries, found, generated)
    # also with the ordinary doc interleaved
    check([FOO, GENINDEX, MODINDEX, SEARCH], found, generated)
    # an unknown name (neither family) must be dropped
    check([999, GENINDEX, 42, SEARCH], found, generated)

    # --- boundary cases --------------------------------------------------------
    boundary = [
        ([], [], []),
        ([1], [], []),                 # unknown only -> dropped
        ([1], [1], []),                # found only -> kept
        ([1], [], [1]),                # generated only -> kept (the bug)
        ([1, 1], [], [1]),             # duplicates, generated only
        ([1, 2, 3], [2], [3]),         # mixed: 1 dropped, 2 found, 3 generated
        ([3, 2, 1], [2], [3]),         # order preserved
        ([5], [5], [5]),               # in both families
        ([1, 2, 3, 4, 5], [1, 2], [3, 4]),
    ]
    for entries, found, generated in boundary:
        check(entries, found, generated)

    # --- randomized fuzz -------------------------------------------------------
    rng = random.Random(10673)
    for _ in range(50000):
        nf = rng.randint(0, 8)
        ng = rng.randint(0, 4)
        ne = rng.randint(0, 12)
        # small id domain so found/generated overlap with entries frequently
        found = [rng.randint(0, 20) for _ in range(nf)]
        generated = [rng.randint(0, 20) for _ in range(ng)]
        entries = [rng.randint(0, 20) for _ in range(ne)]
        check(entries, found, generated)

    print("G-AX OK: deep model `kept` == real set-union membership over "
          "%d boundary + 50000 fuzz inputs; F2P scenario retains all three "
          "generated reference pages in order" % (len(boundary),))
    return 0


if __name__ == "__main__":
    sys.exit(main())
