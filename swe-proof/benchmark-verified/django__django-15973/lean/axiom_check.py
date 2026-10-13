#!/usr/bin/env python3
"""G-AX for django__django-15973 — A-reference validation.

The bundle deep-models the UNCHANGED helper `resolve_relation`
(django/db/migrations/utils.py) as the Lean `modelRefToPair`. This is an
A-reference: it must be observationally EQUAL to the real callee on every input
the modeled branch can feed it. This check runs the REAL `resolve_relation`
in-container on boundary + fuzz inputs and asserts the Lean replica
(`_model_ref_to_pair`, the op-for-op transliteration of `modelRefToPair`) agrees.

Inputs the call site can produce (mapping.md): the `model` argument is a string
reference (`"app.Object"`, bare `"Object"`, or the recursive marker `"self"`) or
a model class; `app_label` / `model_name` (the owning model's scope) are always
non-None at this site. We fuzz the string forms (the model-class form is the
trivial `_meta` projection and is exercised by one synthetic stub object).

Interpretation note: the Lean model leaves the object-name case normalization
ABSTRACT (`opaque lower : String → String`, mapping.md) because Python's
`str.lower` is a full Unicode case fold that no concrete Lean per-character
fold reproduces. The replica below interprets `lower` as the REAL `str.lower`
— this file is precisely the executable validation of that binding (replica ==
real `resolve_relation`), so the A-reference grounds the opaque symbol.

stdlib-only. Pinned seed: 15973 (also in mapping.md). exit 0 iff sound.
"""
import json
import random
import sys

SEED = 15973
N = 50_000

# Import the REAL callee from the repo under test (in-container).
from django.db.migrations.utils import resolve_relation  # noqa: E402
from django.db.models.fields.related import RECURSIVE_RELATIONSHIP_CONSTANT  # noqa: E402


# --- Lean replica: transliteration of modelRefToPair (str case) --------------
def _split_first_dot(s):
    # mirrors splitFirstDot: split on FIRST '.' only
    if "." not in s:
        return None
    a, n = s.split(".", 1)
    return a, n


def _model_ref_to_pair_str(s, scope_app, scope_name):
    if s == "self":
        return (scope_app, scope_name)
    sd = _split_first_dot(s)
    if sd is not None:
        a, n = sd
        return (a, n.lower())
    return (scope_app, s.lower())


class _StubMeta:
    def __init__(self, app_label, model_name):
        self.app_label = app_label
        self.model_name = model_name


class _StubModel:
    def __init__(self, app_label, model_name):
        self._meta = _StubMeta(app_label, model_name)


def _model_ref_to_pair_concrete(model):
    return (model._meta.app_label, model._meta.model_name)


def disagree_str(s, scope_app, scope_name):
    got = resolve_relation(s, scope_app, scope_name)
    want = _model_ref_to_pair_str(s, scope_app, scope_name)
    if tuple(got) != tuple(want):
        return ((s, scope_app, scope_name), got, want)
    return None


WORDS = ["Author", "Publisher", "Contract", "Model", "self", "X", "abcModel",
         "MiXeD", "lower", "UPPER", "Sub.Model", "a.b.c"]
APPS = ["authors", "testapp", "contract", "fonte", "variavel", "app1", "self"]


def main() -> int:
    checked = 0

    # --- model-class form: trivial _meta projection ---
    stub = _StubModel("someapp", "somemodel")
    got = resolve_relation(stub, "scope", "scopename")
    want = _model_ref_to_pair_concrete(stub)
    if tuple(got) != tuple(want):
        print(f"DISAGREE concrete: real={got} model={want}")
        print("status=fail")
        return 1
    checked += 1

    # --- boundary string cases ---
    edges = [
        ("testapp.Publisher", "authors", "author"),
        ("contract.Contract", "authors", "author"),
        ("Publisher", "testapp", "author"),
        ("self", "authors", "author"),
        ("a.b.c", "x", "y"),            # multi-dot: split once
        ("ALLCAPS", "app", "m"),
        ("app.UPPER", "app", "m"),
        ("x.", "app", "m"),             # trailing dot
        (".Model", "app", "m"),         # leading dot -> empty app part
    ]
    for s, sa, sn in edges:
        d = disagree_str(s, sa, sn)
        if d:
            print(f"DISAGREE edge {d[0]!r}: real={d[1]} model={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    # --- fuzz ---
    rng = random.Random(SEED)
    for _ in range(N):
        scope_app = rng.choice(APPS)
        scope_name = rng.choice(WORDS).lower()
        form = rng.randint(0, 3)
        if form == 0:
            s = RECURSIVE_RELATIONSHIP_CONSTANT  # "self"
        elif form == 1:
            s = f"{rng.choice(APPS)}.{rng.choice(WORDS)}"
        else:
            s = rng.choice(WORDS)
        d = disagree_str(s, scope_app, scope_name)
        if d:
            print(f"DISAGREE fuzz {d[0]!r}: real={d[1]} model={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    print(json.dumps({
        "status": "pass",
        "instance": "django__django-15973",
        "checked": checked,
        "disagreements": 0,
        "callee": "resolve_relation",
        "kind": "A-reference",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
