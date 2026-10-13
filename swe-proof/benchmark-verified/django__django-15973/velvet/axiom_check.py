#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-15973.

This bundle declares **no consumed axioms**. The operation the gold patch
changes (which model reference feeds the through-dependency resolution) is
modeled *identically* over a deeply-modeled callee, and is differential-tested
by G-CONF (conformance_check.py). There is one **deep-model reference
(A-reference)**: `resolveRef`, which models the UNCHANGED relation resolver
`django.db.migrations.utils.resolve_relation`. G-AX validates that deep model
against the REAL callee.

What this script asserts:

  1. (no-axiom claim) meta.json lists no consumed axioms — a future edit that
     smuggles in an `axiom` without an executable soundness check is caught here.

  2. (A-reference) for every model-reference shape the bijection (mapping.md §2)
     maps a `RelRef` to, the REAL `resolve_relation` returns exactly the
     `(app, name)` pair the deep model `resolveRef` predicts:
        "self"        (.selfRef)        -> (app_label, model_name)
        "app.Model"   (.qualified a n)  -> (a, n.lower())
        "Model"       (.bare n)         -> (app_label, n.lower())
        model object  (.resolved a n)   -> (obj._meta.app_label, obj._meta.model_name)
     over boundary references and randomized mixed-case ASCII fuzz.

Imports only the standard library + django (the same package the gold patch
edits). Exit 0 iff every obligation holds.
"""
import json
import os
import random
import sys


def _setup_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(INSTALLED_APPS=[], DATABASES={})
    django.setup()


def check_no_consumed_axioms():
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "meta.json")) as fh:
        meta = json.load(fh)
    axioms = meta.get("axioms", [])
    assert axioms == [], (
        "axiom_check expected no consumed axioms but meta.json lists %r; a "
        "consumed axiom requires an executable soundness check here." % (axioms,))


# --- the deep model resolveRef (kept in lock-step with Solution.lean) --------
# A RelRef and the (app, name) pair resolveRef predicts, in scope (app_label,
# model_name). Returns the expected (app, name) tuple.
def resolve_ref_model(ref, app_label, model_name):
    kind = ref[0]
    if kind == "selfRef":
        return (app_label, model_name)
    if kind == "qualified":
        _, a, n = ref
        return (a, n.lower())
    if kind == "bare":
        _, n = ref
        return (app_label, n.lower())
    if kind == "resolved":
        _, a, n = ref
        return (a, n)
    raise AssertionError("unknown RelRef %r" % (ref,))


class _FakeMeta:
    def __init__(self, app_label, model_name):
        self.app_label = app_label
        self.model_name = model_name


class _FakeModel:
    """A model OBJECT: resolve_relation falls to `model._meta.(app_label,
    model_name)` for any non-str. Mirrors the .resolved RelRef arm."""
    def __init__(self, app_label, model_name):
        self._meta = _FakeMeta(app_label, model_name)


def real_reference(ref):
    """Build the REAL argument resolve_relation receives for a RelRef
    (mapping.md §2 bijection)."""
    kind = ref[0]
    if kind == "selfRef":
        return "self"                       # RECURSIVE_RELATIONSHIP_CONSTANT
    if kind == "qualified":
        _, a, n = ref
        return "%s.%s" % (a, n)             # "app.Model"
    if kind == "bare":
        _, n = ref
        return n                            # "Model", no dot
    if kind == "resolved":
        _, a, n = ref
        return _FakeModel(a, n)             # model object exposing _meta
    raise AssertionError("unknown RelRef %r" % (ref,))


def main():
    check_no_consumed_axioms()
    _setup_django()
    from django.db.migrations.utils import resolve_relation

    scopes = [("authors", "author"), ("fonte", "fontemodel"),
              ("testapp", "publisher"), ("", "")]

    # ---- boundary references -------------------------------------------------
    boundary = [
        ("selfRef",),
        ("qualified", "testapp", "Publisher"),
        ("qualified", "contract", "Contract"),
        ("qualified", "variavel", "VariavelModel"),
        ("qualified", "fonte_variavel", "FonteVariavelModel"),
        ("bare", "Publisher"),
        ("bare", "Contract"),
        ("bare", "ALLCAPS"),
        ("bare", "lower"),
        ("resolved", "contract", "contract"),
        ("resolved", "testapp", "publisher"),
    ]

    checked = 0
    for ref in boundary:
        for app_label, model_name in scopes:
            observed = resolve_relation(real_reference(ref), app_label, model_name)
            expected = resolve_ref_model(ref, app_label, model_name)
            assert tuple(observed) == tuple(expected), (
                "A-reference resolveRef unsound on RelRef=%r scope=(%r,%r): real "
                "resolve_relation gave %r, deep model says %r"
                % (ref, app_label, model_name, tuple(observed), tuple(expected)))
            checked += 1

    # ---- randomized mixed-case ASCII fuzz ------------------------------------
    rng = random.Random(15973)
    letters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_0123456789"

    def rand_ident(n):
        return "".join(rng.choice(letters) for _ in range(n))

    for _ in range(20000):
        app_label, model_name = rng.choice(scopes)
        choice = rng.randint(0, 3)
        if choice == 0:
            ref = ("selfRef",)
        elif choice == 1:
            ref = ("qualified", rand_ident(rng.randint(1, 8)),
                   rand_ident(rng.randint(1, 10)))
        elif choice == 2:
            # bare: an identifier with NO dot (resolve_relation's "." test)
            ref = ("bare", rand_ident(rng.randint(1, 10)))
        else:
            ref = ("resolved", rand_ident(rng.randint(1, 8)),
                   rand_ident(rng.randint(1, 10)))
        observed = resolve_relation(real_reference(ref), app_label, model_name)
        expected = resolve_ref_model(ref, app_label, model_name)
        assert tuple(observed) == tuple(expected), (
            "A-reference resolveRef unsound (fuzz) on RelRef=%r scope=(%r,%r): "
            "real resolve_relation gave %r, deep model says %r"
            % (ref, app_label, model_name, tuple(observed), tuple(expected)))
        checked += 1

    print("G-AX OK: A-reference resolveRef == real resolve_relation on %d "
          "(reference x scope) cases (%d boundary + 20000 fuzz); bundle declares "
          "no consumed axioms." % (checked, len(boundary) * len(scopes)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
