#!/usr/bin/env python3
"""G-AX executable soundness check for scikit-learn__scikit-learn-12585.

This bundle declares **no consumed axioms**. The operation the gold patch
changes (the `clone` branch-dispatch predicate) is modeled *identically*
(`route`) and is handled mechanically by G-CONF (conformance_check.py). There
is one **deep-model reference (A-reference)**: the observable result of the
`deepCopy` arm on a *class object*, i.e. `copy.deepcopy(C) is C`. G-AX validates
that A-reference against the REAL stdlib callee `copy.deepcopy`, because the F2P
test `test_clone_estimator_types` asserts `clf.empty is clf2.empty` where
`clf.empty` is a class — so the `deepCopy` arm must return the identical object.

What this script asserts:

  1. (no-axiom claim) meta.json lists no consumed axioms — a future edit that
     smuggles in an `axiom` without an executable soundness check is caught here.

  2. (A-reference) `copy.deepcopy(obj) is obj` for class objects (`isinstance(
     obj, type)`), across builtin types, stdlib classes, and user-defined
     classes — including a class that exposes a `get_params` attribute (the very
     shape the bug hit). This is the fact the `deepCopy` arm relies on for the
     F2P observable.

  3. (R bijection, falsifiable) the three predicates the dispatch reads
     (`type(v) in (list,tuple,set,frozenset)`, `hasattr(v,'get_params')`,
     `isinstance(v, type)`) have the values mapping.md §2 claims for a spread of
     real values — in particular a class object that DOES expose `get_params`
     has `exposesParams=True` AND `isClassObject=True` (the discriminating
     combination), while its instances have `isClassObject=False`.

Imports only the standard library (`copy`, `json`, `os`, `sys`). Exit 0 iff
every obligation holds.
"""
import copy
import json
import os
import sys


def check_no_consumed_axioms():
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "meta.json")) as fh:
        meta = json.load(fh)
    axioms = meta.get("axioms", [])
    assert axioms == [], (
        "axiom_check expected no consumed axioms but meta.json lists %r; a "
        "consumed axiom requires an executable soundness check here." % (axioms,))


# A class that advertises the parameter interface (mirrors an sklearn estimator
# class passed as a parameter value, e.g. StandardScaler passed as `with_mean`).
class ParamExposingClass:
    def get_params(self, deep=True):
        return {}


class PlainClass:
    pass


def check_deepcopy_class_identity():
    """A-reference: copy.deepcopy returns class objects by identity."""
    class_objects = [
        int, float, str, list, tuple, dict, set, frozenset, bytes, bool,
        object, Exception, ValueError,
        ParamExposingClass, PlainClass, type,
    ]
    for C in class_objects:
        assert isinstance(C, type), "test fixture %r is not a class" % (C,)
        dc = copy.deepcopy(C)
        assert dc is C, (
            "A-reference VIOLATED: copy.deepcopy(%r) is not the identical "
            "object (got %r); the deepCopy arm would not preserve identity, "
            "breaking `clf.empty is clf2.empty`." % (C, dc))


def _triple(v):
    """The (isCollection, exposesParams, isClassObject) projection (mapping §2)."""
    is_collection = type(v) in (list, tuple, set, frozenset)
    exposes_params = hasattr(v, "get_params")
    is_class = isinstance(v, type)
    return is_collection, exposes_params, is_class


def check_predicate_bijection():
    """R bijection: the three observed predicates have the claimed values."""
    # (value, expected (isCollection, exposesParams, isClassObject))
    cases = [
        # a class object that exposes get_params: the discriminating combination
        (ParamExposingClass, (False, True, True)),
        # an *instance* of it: exposes params, but NOT a class object
        (ParamExposingClass(), (False, True, False)),
        # a plain class object: not a collection, no params, is a class
        (PlainClass, (False, False, True)),
        # ordinary non-estimator values: no params, not a class
        (42, (False, False, False)),
        ("hello", (False, False, False)),
        (3.14, (False, False, False)),
        (None, (False, False, False)),
        # collections (handled first, before either test)
        ([1, 2], (True, False, False)),
        ((1, 2), (True, False, False)),
        ({1, 2}, (True, False, False)),
        (frozenset({1}), (True, False, False)),
    ]
    for v, expected in cases:
        got = _triple(v)
        assert got == expected, (
            "R bijection VIOLATED for value %r: triple %r != expected %r"
            % (v, got, expected))
    # Spell out the discriminating fact: a param-exposing class is both
    # exposesParams AND isClassObject -> routed away from reconstruction.
    _, ep, ic = _triple(ParamExposingClass)
    assert ep and ic, "param-exposing class must satisfy exposesParams & isClassObject"


def main():
    try:
        check_no_consumed_axioms()
        check_deepcopy_class_identity()
        check_predicate_bijection()
    except AssertionError as e:
        print("G-AX FAIL:", e)
        return 1
    except Exception as e:  # pragma: no cover - environment guard
        print("G-AX ERROR: %r" % (e,))
        return 2
    print("G-AX OK: no consumed axioms; copy.deepcopy(class) is identity on 16 "
          "class objects (incl. a get_params-exposing class); the three dispatch "
          "predicates match the mapping.md bijection on 11 boundary values "
          "(param-exposing class -> exposesParams & isClassObject).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
