#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13568 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by running
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW — the R/I-tagged ops of Solution.lean's impl region
             (`usernameUniquenessVerdict`) transliterated to Python, over the
             real repo carriers via the mapping.md bijection. The deep model
             `totalUnique`/`coversField` (A-reference) is left as its own
             transliteration here — G-CONF isolates the R/I legs; the agreement
             of that deep model with the real `_meta.total_unique_constraints`
             accessor is the A-reference validated separately by G-AX.

  * ORACLE — `patch.diff`'s behaviour: the patched `check_user_model`
             (`django.contrib.auth.checks`) run at base_commit with the gold
             applied (the harness applies patch.diff before this runs). We map
             its emitted system-check messages to the three-valued Verdict
             (auth.E003 -> error, auth.W004 -> warning, neither -> ok).

The bridge (mapping.md §2): a fuzzed scenario is
  (constraints, fieldUnique, defaultBackendOnly)
realized BOTH as Lean-side `Constraint` records (for the shadow) and as a real
Django model + AUTHENTICATION_BACKENDS setting (for the oracle). They must agree
on every scenario. Exit 0 iff zero disagreements.

Runs in-container (the prebuilt SWE-Bench instance image, conda env `testbed`,
PYTHONPATH=/testbed) with the gold patch applied. Django + stdlib only. The fuzz
seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import os
import random
import sys
import tempfile

SEED = 13568
N_FUZZ = 100_000

FIELD_POOL = ["username", "password", "email", "nick"]
DEFAULT_BACKEND = ["django.contrib.auth.backends.ModelBackend"]
CUSTOM_BACKEND = ["my.custom.backend"]


# ---- Django bootstrap -------------------------------------------------------

def _bootstrap():
    appdir = tempfile.mkdtemp(prefix="confcheck_app_")
    pkg = os.path.join(appdir, "confapp")
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
                "confapp",
            ],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
            USE_TZ=True,
            SECRET_KEY="conf-check",
            AUTHENTICATION_BACKENDS=list(DEFAULT_BACKEND),
        )
    django.setup()


_bootstrap()

from django.apps import apps                                    # noqa: E402
from django.db import models                                    # noqa: E402
from django.db.models import UniqueConstraint, CheckConstraint, Q  # noqa: E402
from django.contrib.auth.models import AbstractBaseUser         # noqa: E402
from django.contrib.auth.checks import check_user_model         # noqa: E402
from django.conf import settings                                # noqa: E402


# ---- the R/I shadow: usernameUniquenessVerdict transliterated ---------------

def total_unique_shadow(specs):
    """totalUnique (Solution.lean pure): field tuples of unique & unconditional
    constraints, in order."""
    return [list(s["fields"]) for s in specs
            if s["isUnique"] and not s["conditional"]]


def covers_field_shadow(specs, uf):
    """coversField: some total uniqueness constraint ranges over exactly [uf]."""
    return any(fs == [uf] for fs in total_unique_shadow(specs))


def shadow_verdict(specs, field_unique, default_backend_only, uf="username"):
    """The impl region's `do` block, transliterated (R/I ops)."""
    covered = covers_field_shadow(specs, uf)
    if (not field_unique) and (not covered):
        return "error" if default_backend_only else "warning"
    return "ok"


# ---- the oracle: patched check_user_model -----------------------------------

_counter = [0]


def build_model(specs, field_unique):
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
    Meta = type("Meta", (), {"app_label": "confapp", "constraints": constraints})
    attrs = {
        "__module__": "confapp.models",
        "username": models.CharField(max_length=30, unique=field_unique),
        "email": models.CharField(max_length=30),
        "nick": models.CharField(max_length=30),
        "USERNAME_FIELD": "username",
        "Meta": Meta,
    }
    return type("ConfM_%d" % _counter[0], (AbstractBaseUser,), attrs)


def oracle_verdict(model, default_backend_only):
    """Run the patched check_user_model and reduce its emitted messages to the
    three-valued Verdict."""
    settings.AUTH_USER_MODEL = model._meta.label
    settings.AUTHENTICATION_BACKENDS = (
        list(DEFAULT_BACKEND) if default_backend_only else list(CUSTOM_BACKEND))
    ids = {getattr(e, "id", None)
           for e in check_user_model(app_configs=apps.get_app_configs())}
    if "auth.E003" in ids:
        return "error"
    if "auth.W004" in ids:
        return "warning"
    return "ok"


# ---- fuzz -------------------------------------------------------------------

def gen_specs(rng):
    k = rng.randint(0, 4)
    specs = []
    for _ in range(k):
        is_unique = rng.random() < 0.6
        nf = rng.randint(1, 2)
        fields = [rng.choice(FIELD_POOL) for _ in range(nf)]
        specs.append({
            "fields": fields,
            "isUnique": is_unique,
            "conditional": (rng.random() < 0.5) if is_unique else False,
        })
    return specs


def build_pool(rng, n_shapes):
    """Prebuild a pool of distinct (specs, field_unique, model) shapes ONCE.
    Building a real Django model is the expensive step and the decision depends
    only on (fieldUnique, whether a total-unique constraint == [username],
    defaultBackendOnly) — a small space a few hundred shapes saturate — so we
    build a fixed pool and fuzz by sampling it × both backends, rather than
    constructing one model per input (which also grows the app registry
    unboundedly)."""
    pool = []
    for _ in range(n_shapes):
        specs = gen_specs(rng)
        fu = rng.random() < 0.4
        pool.append((specs, fu, build_model(specs, fu)))
    return pool


def boundary_scenarios():
    """(specs, field_unique, default_backend_only) covering the F2P + P2P
    discriminating shapes and both backend configurations."""
    shapes = [
        [],
        [{"fields": ["username"], "isUnique": True, "conditional": False}],   # acquits
        [{"fields": ["username"], "isUnique": True, "conditional": True}],    # partial: no
        [{"fields": ["username"], "isUnique": False, "conditional": False}],  # check: no
        [{"fields": ["username", "password"], "isUnique": True, "conditional": False}],
        [{"fields": ["email"], "isUnique": True, "conditional": False}],
        [{"fields": ["email"], "isUnique": True, "conditional": False},
         {"fields": ["username"], "isUnique": True, "conditional": False}],
    ]
    for specs in shapes:
        for fu in (False, True):
            for dbo in (False, True):
                yield (specs, fu, dbo)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    def run(specs, fu, model, dbo):
        nonlocal count
        count += 1
        shadow = shadow_verdict(specs, fu, dbo)
        oracle = oracle_verdict(model, dbo)
        if shadow != oracle:
            disagreements.append((specs, fu, dbo, shadow, oracle))

    # boundary scenarios: build a fresh model per shape (few, cheap)
    for specs, fu, dbo in boundary_scenarios():
        run(specs, fu, build_model(specs, fu), dbo)
        if len(disagreements) >= 5:
            break

    # fuzz: prebuild a pool of model shapes once, then sample pool × backend
    if not disagreements:
        pool = build_pool(rng, 600)
        for _ in range(N_FUZZ):
            specs, fu, model = pool[rng.randrange(len(pool))]
            dbo = rng.random() < 0.5
            run(specs, fu, model, dbo)
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for specs, fu, dbo, sh, orc in disagreements:
            print("  specs=%r fieldUnique=%r defaultBackendOnly=%r shadow=%r oracle=%r"
                  % (specs, fu, dbo, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of usernameUniquenessVerdict agrees with "
          "patch.diff behaviour on %d inputs (seed=%d), 0 disagreements."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
