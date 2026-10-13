#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-15973.

The reference resolver that maps an "app.Object" token to an
(app_label, object_name) pair is modelled DEEPLY in model.py (the pure region:
`ref_app` / `ref_name` / `lowered` / `dot_index`), not behind a consumed axiom.
G-AX validates that deep model is equal to the REAL resolver on every input it
is exercised on.

The real callee is Django's `django.db.migrations.utils.resolve_relation`
(unchanged by the patch). For a string reference `"app.Object"` it returns
`(app_label, object_name.lower())`, splitting on the FIRST dot. This file
executes that real callee in-container and asserts, for boundary cases over the
dot/case structure plus randomized fuzzing, that:

    (A-reference) ref_app(token)  == real app_label   (prefix before first dot,
                                                        verbatim)
                  ref_name(token) == real object_name (suffix after first dot,
                                                        lower-cased)

The deep model is reproduced below exactly as encoded in model.py. Exit 0 iff
every observation matches the real resolver.

The patch's behavioural change is *which* token is passed to this resolver for
the intermediary ("through") dependency; the resolver itself is unchanged, so
its soundness as a reference is exactly what is checked here.
"""
import os
import random
import sys


# --- model.py deep-model reference encodings (kept in lock-step) -------------

def lower_cp(c):
    """model.py lower_cp: ASCII 'A'..'Z' -> 'a'..'z', else identity."""
    if 65 <= c <= 90:
        return c + 32
    return c


def dot_index(ref, i):
    """model.py dot_index: index of the first '.' (46) at/after i, else len."""
    n = len(ref)
    while i < n and ref[i] != 46:
        i += 1
    return i


def ref_app(ref):
    """model.py ref_app: code points of the prefix before the first dot."""
    d = dot_index(ref, 0)
    return ref[:d]


def ref_name(ref):
    """model.py ref_name: lower-cased code points of the suffix after the
    first dot."""
    d = dot_index(ref, 0)
    return [lower_cp(c) for c in ref[d + 1:]]


# --- the real callee ---------------------------------------------------------

def _load_real_resolver():
    """Import the unchanged real callee resolve_relation (in-container)."""
    here = os.path.dirname(os.path.abspath(__file__))
    # the repo root is the eval container's working tree; add likely roots
    for cand in ("/testbed", os.getcwd(), here):
        if cand not in sys.path:
            sys.path.insert(0, cand)
    from django.db.migrations.utils import resolve_relation
    return resolve_relation


def check_token(resolve_relation, token, app_label="some_app",
                model_name="SomeModel"):
    """Assert the deep model == the real resolver for a dotted token."""
    real_app, real_name = resolve_relation(token, app_label, model_name)
    cps = [ord(ch) for ch in token]
    model_app = ref_app(cps)
    model_name_cps = ref_name(cps)
    assert model_app == [ord(ch) for ch in real_app], (
        "ref_app deep model unsound on %r: real app_label=%r, deep model=%r"
        % (token, real_app, "".join(chr(c) for c in model_app)))
    assert model_name_cps == [ord(ch) for ch in real_name], (
        "ref_name deep model unsound on %r: real object_name=%r, deep model=%r"
        % (token, real_name,
           "".join(chr(c) for c in model_name_cps)))


def main():
    resolve_relation = _load_real_resolver()

    # --- boundary cases: the dotted "app.Object" tokens the patch resolves ---
    boundary = [
        "fonte_variavel.FonteVariavelModel",   # the issue's through model
        "variavel.VariavelModel",              # the issue's target model
        "testapp.Publisher",                   # F2P target
        "contract.Contract",                   # F2P through model
        "authors.Author",
        "a.B",                                 # minimal
        "app.lowercase",                       # already lower-cased name
        "App.UPPER",                           # app label NOT lowered; name is
        "x.y.z",                               # multiple dots: split on FIRST
        "my_app.My_Model123",
        "APP_LABEL.MixedCaseName",
        "ABC.A.B.C",                           # dots inside the object name
        "z9.M0del",
    ]
    for tok in boundary:
        check_token(resolve_relation, tok)

    # --- randomized fuzz over dotted tokens ----------------------------------
    # The deep model's case fold (`lower_cp`) is the ASCII fold, which is what
    # Django app labels / model references are: Python identifiers, i.e. ASCII
    # letters, digits and underscore (the only domain the resolver is exercised
    # on by the autodetector). The fuzz alphabet is therefore the ASCII
    # identifier domain plus a few NON-CASED code points (digits / underscore /
    # marks that `str.lower()` leaves unchanged) to exercise the identity arm of
    # `lower_cp`. (Non-ASCII *cased* letters are out of domain: real model names
    # are ASCII identifiers, and the F2P inputs are all ASCII.)
    rng = random.Random(15973)
    alphabet = (
        [chr(c) for c in range(ord("A"), ord("Z") + 1)]
        + [chr(c) for c in range(ord("a"), ord("z") + 1)]
        + [chr(c) for c in range(ord("0"), ord("9") + 1)]
        + ["_"]
    )
    for _ in range(20000):
        app_len = rng.randint(1, 8)
        name_len = rng.randint(1, 10)
        app = "".join(rng.choice(alphabet) for _ in range(app_len))
        name = "".join(rng.choice(alphabet) for _ in range(name_len))
        # occasionally embed extra dots in the name part (split is on the first)
        if rng.random() < 0.2:
            pos = rng.randint(0, len(name))
            name = name[:pos] + "." + name[pos:]
        token = app + "." + name
        check_token(resolve_relation, token)

    print("G-AX OK: ref_app/ref_name deep model == real resolve_relation on "
          "%d boundary + 20000 fuzz dotted tokens" % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
