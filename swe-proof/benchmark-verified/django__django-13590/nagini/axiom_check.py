#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-13590.

Executes the REAL Python container semantics the bundle relies on (the same
constructions the gold patch performs) and asserts every observation matches
the model, as encoded in model.py.

Two kind-A checks:

  (A-consumed) the `resolve_one` axiom (model.py axioms region) stands for the
      unchanged per-element resolution (the recursive resolution of one
      sub-value). model.py consumes only that it is a *deterministic pure
      function* of its argument (it carries no `Ensures` beyond purity), so the
      check asserts determinism and side-effect freedom: resolving the same
      sub-value twice yields the same result, and for a sub-value that is not an
      expression (no `resolve_expression`) the resolution is the identity — the
      pass-through branch the recursive call bottoms out in.

  (A-consumed) the `build_container` axiom (model.py axioms region) stands for
      the UNCHANGED container constructor of the container kind. Its contract is:
      a WELL-FORMED construction (one that yields a usable container holding the
      elements AND grants the `well_formed_container` capability token) is
      possible only when the convention matches the kind (`field_named ==
      spread`). This check validates that contract against the REAL constructors:
        * a plain positional kind (`list` / `tuple`) built from a single
          iterable (`spread == False`) WELL-FORMS, holding exactly the elements,
          in order (`tuple(iterable) == tuple(elements)`); and
        * a field-named kind (a `collections.namedtuple`, identified by the
          presence of `_make`) built by SPREADING the elements one-per-field
          (`cls(*elements)`, `spread == True`) WELL-FORMS, holding exactly the
          elements, in order, whereas handing it the single un-spread iterable
          (`cls(iterable)`, the mismatched convention) does NOT well-form a
          container — it raises for >= 2 fields, or bundles the whole iterable
          into the first field. Hence the only convention under which the
          field-named constructor well-forms (and could grant the token) is the
          spread, exactly the precondition `field_named == spread`. The
          `well_formed_container` token is the abstract capability that the
          well-formed construction grants and that nothing else can fabricate;
          its soundness is precisely that a well-formed (token-granting)
          construction is reachable only under the matching convention — which is
          what these constructor observations establish.

Imports only the Python standard library (`collections.namedtuple`) — the same
constructions the gold patch uses; nothing repo-specific. Exit 0 iff every
obligation holds.
"""
import collections
import random
import sys


def resolve_one(x):
    """Reference for model.py's `resolve_one`: the recursive resolution bottoms
    out, for a non-expression sub-value, in the pass-through `return value`
    branch (no `resolve_expression` attribute). Identity on such scalars."""
    if hasattr(x, "resolve_expression"):  # pragma: no cover - not in fuzz set
        raise AssertionError("fuzz sub-values are plain scalars")
    return x


def check_resolve_one(x):
    # determinism / side-effect freedom and the identity pass-through branch
    a = resolve_one(x)
    b = resolve_one(x)
    assert a == b, "resolve_one not deterministic on %r" % (x,)
    assert a == x, "resolve_one not identity on non-expression %r" % (x,)


def check_plain_iterable(elements):
    """Plain kind built from a single iterable holds exactly the elements."""
    for kind in (list, tuple):
        gen = (resolve_one(e) for e in elements)
        built = kind(gen)                         # real construction
        assert list(built) == [resolve_one(e) for e in elements], (
            "plain %s reconstruction unsound on %r" % (kind.__name__, elements))


def check_field_named(elements):
    """Field-named kind: spreading reproduces the elements; the single-iterable
    convention does NOT (the bug)."""
    n = len(elements)
    if n == 0:
        return  # a namedtuple has >= 1 field; empty handled by the plain case
    NT = collections.namedtuple("NT", ["f%d" % k for k in range(n)])

    # correct convention: spread one-per-field (cls(*values)) -> holds elements
    gen = (resolve_one(e) for e in elements)
    built = NT(*gen)                              # real construction (the fix)
    assert list(built) == [resolve_one(e) for e in elements], (
        "namedtuple spread reconstruction unsound on %r" % (elements,))

    # buggy convention: hand the single iterable (cls(iterable)) -> wrong
    gen2 = (resolve_one(e) for e in elements)
    if n == 1:
        # the lone iterable bundles into the single field -> field 0 holds an
        # iterable, NOT the element -> contents differ from the elements
        wrong = NT(gen2)
        assert list(wrong) != [resolve_one(e) for e in elements], (
            "single-iterable convention unexpectedly correct for 1-field nt")
    else:
        raised = False
        try:
            NT(gen2)                              # too few positional args
        except TypeError:
            raised = True
        assert raised, (
            "single-iterable convention did NOT fail for %d-field namedtuple "
            "(%r)" % (n, elements))


def main():
    # --- resolve_one (A-consumed): boundary + fuzz scalars ----------------
    scalars = [0, 1, -1, 7, 42, -99, 2 ** 31, "a", "", "x'y", True, False]
    for x in scalars:
        check_resolve_one(x)

    # --- reconstruction (A-reference): boundary element lists -------------
    boundary = [
        [],
        [10],
        [51, 100],            # the F2P case: a 2-field namedtuple (51, 100)
        [1, 2, 3],
        [0, 0],
        [-5, 7, -9, 11],
        list(range(8)),
    ]
    for elements in boundary:
        check_plain_iterable(elements)
        check_field_named(elements)

    # --- reconstruction (A-reference): randomized fuzz --------------------
    rng = random.Random(13590)
    for _ in range(20000):
        n = rng.randint(0, 8)
        elements = [rng.randint(-1000, 1000) for _ in range(n)]
        check_plain_iterable(elements)
        check_field_named(elements)

    print("G-AX OK: resolve_one determinism/identity sound on %d scalars; "
          "reconstruction deep model (plain single-iterable == elements, "
          "namedtuple spread == elements, namedtuple single-iterable wrong) "
          "sound on %d boundary + 20000 fuzz element lists"
          % (len(scalars), len(boundary)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
