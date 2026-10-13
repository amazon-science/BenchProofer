#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-13568.

The bundle consumes NO axiom about a foreign callee. The one piece of model
metadata the spec reads — the set of *total* (always-applicable) uniqueness
constraints declared on a model — is modeled DEEPLY in Solution.lean by
`totalUnique` (the `pure` region). This check validates that deep model against
the REAL accessor it abstracts (an **A-reference**, SPEC_GUIDE §3 / mapping.md
§3.1):

    totalUnique(specs)  ==  [list(c.fields) for c in M._meta.total_unique_constraints]

where `M` is a real Django model built from `specs` and `total_unique_constraints`
is the genuine `django.db.models.options.Options` cached property (UNCHANGED by
the gold patch — this gate runs on the unpatched repo).

The Lean↔Python bijection (mapping.md §2):
  * a Lean `Constraint {fields, isUnique := true,  conditional := false}`
        ↔ a real `UniqueConstraint(fields=fields, condition=None)`;
  * `{fields, isUnique := true,  conditional := true}`
        ↔ a real `UniqueConstraint(fields=fields, condition=Q(...))`  (partial);
  * `{isUnique := false, ...}`
        ↔ a real `CheckConstraint(check=Q(...))`  (not a uniqueness constraint).

`totalUnique` keeps `c.fields` iff `c.isUnique and not c.conditional`; the real
accessor keeps `c` iff `isinstance(c, UniqueConstraint) and c.condition is None`.
This check refutes any divergence over boundary + fuzzed constraint lists.

Imports only Django (the repo under test) + stdlib. Exit 0 iff every obligation
holds.
"""
import os
import random
import sys
import tempfile


# ---- Django bootstrap (a real app with a filesystem location) ---------------

def _bootstrap():
    appdir = tempfile.mkdtemp(prefix="axcheck_app_")
    pkg = os.path.join(appdir, "axapp")
    os.makedirs(pkg)
    open(os.path.join(pkg, "__init__.py"), "w").close()
    open(os.path.join(pkg, "models.py"), "w").close()
    sys.path.insert(0, appdir)

    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
                "axapp",
            ],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
            USE_TZ=True,
            SECRET_KEY="axiom-check",
        )
    django.setup()


_bootstrap()

from django.db import models                                    # noqa: E402
from django.db.models import UniqueConstraint, CheckConstraint, Q  # noqa: E402
from django.contrib.auth.models import AbstractBaseUser         # noqa: E402

# field names usable by constraints (must exist on the model)
FIELD_POOL = ["username", "password", "email", "nick"]

_counter = [0]


def build_model(specs):
    """Build a real Django model carrying constraints described by `specs`,
    a list of dicts {fields, isUnique, conditional}."""
    _counter[0] += 1
    constraints = []
    for i, s in enumerate(specs):
        if s["isUnique"]:
            cond = Q(password__isnull=False) if s["conditional"] else None
            constraints.append(UniqueConstraint(
                fields=s["fields"], name="u_%d_%d" % (_counter[0], i),
                condition=cond))
        else:
            constraints.append(CheckConstraint(
                check=Q(password__isnull=False), name="c_%d_%d" % (_counter[0], i)))
    Meta = type("Meta", (), {"app_label": "axapp", "constraints": constraints})
    attrs = {
        "__module__": "axapp.models",
        "username": models.CharField(max_length=30),
        "email": models.CharField(max_length=30),
        "nick": models.CharField(max_length=30),
        "USERNAME_FIELD": "username",
        "Meta": Meta,
    }
    return type("AxM_%d" % _counter[0], (AbstractBaseUser,), attrs)


# ---- the deep model under validation: totalUnique (Solution.lean pure) ------

def total_unique_model(specs):
    """Reference of Solution.lean `totalUnique`: front-recursive keep of
    `fields` for each unique & unconditional constraint, in declaration order."""
    out = []
    for s in specs:
        if s["isUnique"] and not s["conditional"]:
            out.append(list(s["fields"]))
    return out


# ---- the check --------------------------------------------------------------

def check_total_unique(specs):
    M = build_model(specs)
    real = [list(c.fields) for c in M._meta.total_unique_constraints]   # REAL accessor
    model = total_unique_model(specs)                                   # deep model
    assert real == model, (
        "totalUnique deep model unsound on %r: real total_unique_constraints "
        "gave %r, deep model gives %r" % (specs, real, model))


def main():
    cases = []

    # --- boundary: empty, single-shape, the two F2P shapes ------------------
    cases.append([])
    cases.append([{"fields": ["username"], "isUnique": True, "conditional": False}])
    # the test_username_unique_with_model_constraint shape (acquits)
    cases.append([{"fields": ["username"], "isUnique": True, "conditional": False}])
    # the test_username_partially_unique shape (must NOT acquit)
    cases.append([{"fields": ["username"], "isUnique": True, "conditional": True}])
    # a check constraint over the field — not a uniqueness guarantee
    cases.append([{"fields": ["username"], "isUnique": False, "conditional": False}])
    # multi-field unique constraint (does not cover the single field)
    cases.append([{"fields": ["username", "password"], "isUnique": True, "conditional": False}])
    # mixtures
    cases.append([
        {"fields": ["email"], "isUnique": True, "conditional": False},
        {"fields": ["username"], "isUnique": True, "conditional": True},
        {"fields": ["username"], "isUnique": True, "conditional": False},
    ])
    cases.append([
        {"fields": ["username"], "isUnique": False, "conditional": False},
        {"fields": ["password", "username"], "isUnique": True, "conditional": False},
    ])

    for specs in cases:
        check_total_unique(specs)

    # --- randomized fuzz ----------------------------------------------------
    rng = random.Random(13568)
    for _ in range(4000):
        k = rng.randint(0, 4)
        specs = []
        for _j in range(k):
            isUnique = rng.random() < 0.6
            # UniqueConstraint requires non-empty fields
            nf = rng.randint(1, 2)
            fields = [rng.choice(FIELD_POOL) for _ in range(nf)]
            specs.append({
                "fields": fields,
                "isUnique": isUnique,
                "conditional": (rng.random() < 0.5) if isUnique else False,
            })
        check_total_unique(specs)

    print("G-AX OK: totalUnique deep model (== _meta.total_unique_constraints) "
          "sound on %d boundary + 4000 fuzz constraint lists" % len(cases))
    return 0


if __name__ == "__main__":
    sys.exit(main())
