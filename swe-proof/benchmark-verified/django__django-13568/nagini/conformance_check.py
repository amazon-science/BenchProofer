#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13568 (nagini).

SHADOW: the impl region of model.py's ``username_field_diagnostic``, copied
verbatim below with the contract calls (Requires/Ensures/Invariant/Assert)
stripped. The @Pure helpers ``covers`` / ``any_covers`` copy over as plain
functions on a small immutable-tuple PSeq shim; they are contract-side but
serve here as an internal cross-check of the shadow's loop. There are no
@ContractOnly callees in this bundle (the axioms region is empty).

ORACLE: the REAL patched repo behaviour the model models per mapping.md —
the username-uniqueness block of ``django.contrib.auth.checks.check_user_model``
at /testbed with the patch applied (the gate applies it before this script
runs; the script only imports and drives the patched code). Each input tuple
is realised as a genuine user-model class: the login field's ``unique``
attribute carries ``field_unique``, ``Meta.constraints`` carries the
constraint list, ``settings.AUTHENTICATION_BACKENDS`` carries the regime, and
``check_user_model`` is invoked through the explicit app-config branch.

Type bridge (mapping.md section 2): field names lift from int codes through a
fixed pool of distinct concrete field names (only equality is performed on
them). A constraint record ``(span, single, total)`` lifts to a real
``UniqueConstraint`` whose fields tuple has ``span`` names with the coded name
first and whose condition is a row predicate iff ``total == 0``; the concrete
constructor rejects an empty fields list, so the bridgeable concrete domain
has ``span >= 1`` (a 0-field constraint has no concrete counterpart) and
``single`` is meaningful as the sole field only when ``span == 1``, exactly
the reading the model assigns it. ``default_regime`` lifts to the
single-default-backend list vs several non-default lists. The oracle's
diagnostic lowers by id to the model's outcome code: no diagnostic -> 0,
the hard error -> 1, the warning -> 2 (the observable the F2P tests assert).

Input domain: the preconditions demand three readable equal-length lists;
every generated tuple satisfies them by construction.

>= 1e5 Requires-satisfying inputs: boundary cases (constraint-shape corners
crossed with both field_unique values and default/non-default regimes) +
100000 fuzz tuples. Pinned fuzz seed: 135680.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only (plain random; no f-strings for older
container Pythons).
"""
import json
import random
import sys
import warnings

SEED = 135680
N_FUZZ = 100000

NO_DIAGNOSTIC = 0
HARD_ERROR = 1
WARNING = 2


# --- PSeq shim: immutable sequence, the operations the pure region uses ------

class PSeq(object):
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]


def ToSeq(lst):
    return PSeq._wrap(lst)


# --- pure helpers from model.py, contracts stripped ---------------------------

def covers(span, single, total, field):
    return total == 1 and span == 1 and single == field


def any_covers(span, single, total, field):
    if len(span) == 0:
        return False
    return (covers(span[0], single[0], total[0], field) or
            any_covers(span.drop(1), single.drop(1), total.drop(1), field))


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def username_field_diagnostic(field_unique, c_span, c_single, c_total,
                              username_field, default_regime):
    satisfied = field_unique
    if not satisfied:
        i = len(c_span)
        found = False
        while i > 0:
            sp = c_span[i - 1]
            sg = c_single[i - 1]
            tt = c_total[i - 1]
            if tt == 1 and sp == 1 and sg == username_field:
                found = True
            i = i - 1
        satisfied = found
    if satisfied:
        return NO_DIAGNOSTIC
    if default_regime:
        return HARD_ERROR
    return WARNING


# --- field-name <-> int code bridge (mapping.md section 2) ---------------------

NAMES = ["handle", "mail", "phone", "tag", "code_field"]
CODE = {n: i for i, n in enumerate(NAMES)}

DEFAULT_BACKENDS = ["django.contrib.auth.backends.ModelBackend"]
OTHER_BACKENDS = [
    [],
    ["conf_shadow.other.Backend"],
    ["django.contrib.auth.backends.ModelBackend", "conf_shadow.other.Backend"],
    ["conf_shadow.other.Backend", "django.contrib.auth.backends.ModelBackend"],
]

APP_LABEL = "conf_shadow"


# --- oracle plumbing -----------------------------------------------------------

class _AppConfigStub(object):
    """Minimal app-config carrying the freshly built user-model class into
    check_user_model's explicit app_configs branch."""
    label = APP_LABEL

    def __init__(self, model_cls):
        self._model_cls = model_cls

    def get_model(self, model_name):
        return self._model_cls


def build_oracle():
    """Configure Django once; return (django_bits) used per input."""
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
            ],
            DATABASES={},
        )
    django.setup()
    # Point the swappable user-model setting at the class this script builds
    # per input (the app-config branch only splits this string).
    settings.AUTH_USER_MODEL = APP_LABEL + ".TestUser"

    from django.apps import apps
    from django.db import models
    from django.db.models import Q, UniqueConstraint
    from django.contrib.auth.base_user import AbstractBaseUser
    from django.contrib.auth.checks import check_user_model

    # Rebuilding a model class of the same name re-registers it; the stale
    # entry is popped first, so silence the (unraised) re-registration class.
    warnings.filterwarnings("ignore", category=RuntimeWarning)

    return apps, models, Q, UniqueConstraint, AbstractBaseUser, check_user_model


def make_user_model(bits, field_unique, username, con_specs):
    """Lift one abstract input to a real user-model class.

    con_specs: list of (fields_tuple_of_names, conditional_bool)."""
    apps, models, Q, UniqueConstraint, AbstractBaseUser, _ = bits
    apps.all_models[APP_LABEL].pop("testuser", None)
    attrs = {"__module__": APP_LABEL + "_mod", "USERNAME_FIELD": username}
    for n in NAMES:
        attrs[n] = models.CharField(
            max_length=30, unique=(field_unique and n == username))
    constraints = []
    for idx, (fields, conditional) in enumerate(con_specs):
        cond = Q(tag__isnull=False) if conditional else None
        constraints.append(UniqueConstraint(
            fields=list(fields), name="c%d" % idx, condition=cond))
    attrs["Meta"] = type("Meta", (), {"app_label": APP_LABEL,
                                      "constraints": constraints})
    return type("TestUser", (AbstractBaseUser,), attrs)


def real_outcome(bits, field_unique, username, con_specs, backends):
    """Drive the REAL patched check and lower the diagnostic to the model's
    outcome code (mapping.md section 2: nothing/hard-error/warning -> 0/1/2)."""
    from django.conf import settings
    check_user_model = bits[5]
    model_cls = make_user_model(bits, field_unique, username, con_specs)
    settings.AUTHENTICATION_BACKENDS = list(backends)
    diags = [d for d in check_user_model(app_configs=[_AppConfigStub(model_cls)])
             if d.id in ("auth.E003", "auth.W004")]
    if len(diags) > 1:
        raise AssertionError("oracle emitted %d username-uniqueness "
                             "diagnostics" % len(diags))
    if not diags:
        return NO_DIAGNOSTIC
    return HARD_ERROR if diags[0].id == "auth.E003" else WARNING


# --- differential driver --------------------------------------------------------

def check_one(bits, field_unique, username, con_specs, backends):
    """One input tuple: shadow vs real; returns an error string on any
    disagreement, else None."""
    c_span = [len(f) for (f, _c) in con_specs]
    c_single = [CODE[f[0]] for (f, _c) in con_specs]
    c_total = [0 if c else 1 for (_f, c) in con_specs]
    username_field = CODE[username]
    default_regime = (list(backends) == DEFAULT_BACKENDS)

    shadow = username_field_diagnostic(field_unique, c_span, c_single,
                                       c_total, username_field, default_regime)
    real = real_outcome(bits, field_unique, username, con_specs, backends)
    if shadow != real:
        return ("DISAGREEMENT on field_unique=%r username=%r constraints=%r "
                "backends=%r:\n  shadow (impl region) = %r\n"
                "  real (patched repo check) = %r"
                % (field_unique, username, con_specs, backends, shadow, real))

    # internal cross-check: the loop agrees with the pure existential.
    expected = (NO_DIAGNOSTIC
                if field_unique or any_covers(ToSeq(c_span), ToSeq(c_single),
                                              ToSeq(c_total), username_field)
                else (HARD_ERROR if default_regime else WARNING))
    if shadow != expected:
        return ("INTERNAL: impl region and pure predicate disagree on "
                "span=%r single=%r total=%r field=%r: %r vs %r"
                % (c_span, c_single, c_total, username_field, shadow, expected))
    return None


def boundary_cases():
    """(field_unique, username, con_specs, backends) tuples covering the
    constraint-shape corners crossed with both direct-uniqueness values and
    default/non-default regimes."""
    shapes = [
        [],                                                # no constraints
        [(("handle",), False)],                            # exact match
        [(("handle",), True)],                             # conditional only
        [(("mail",), False)],                              # wrong field
        [(("handle", "mail"), False)],                     # composite
        [(("mail", "handle"), False)],                     # composite, tail hit
        [(("handle",), True), (("handle",), False)],       # one unconditional
        [(("mail",), False), (("handle",), False)],        # later one matches
        [(("handle",), True), (("mail",), True)],          # all conditional
        [(("tag",), False)],                               # other single field
        [(("handle",), False), (("handle",), False)],      # duplicates
        [(("handle", "mail", "phone"), False)],            # 3-field composite
        [(("handle", "handle"), False)],                   # repeated name, span 2
    ]
    cases = []
    for shape in shapes:
        for field_unique in (False, True):
            for backends in (DEFAULT_BACKENDS, OTHER_BACKENDS[2]):
                cases.append((field_unique, "handle", shape, backends))
    # a different login field and every non-default regime variant
    cases.append((False, "mail", [(("mail",), False)], DEFAULT_BACKENDS))
    cases.append((False, "mail", [(("handle",), False)], DEFAULT_BACKENDS))
    for backends in OTHER_BACKENDS:
        cases.append((False, "phone", [], backends))
    return cases


def main():
    try:
        bits = build_oracle()
    except Exception as exc:  # pragma: no cover - environment guard
        print("G-CONF ERROR: could not set up the repo oracle: %r" % (exc,))
        return 1

    checked = 0
    boundary = boundary_cases()
    for field_unique, username, con_specs, backends in boundary:
        err = check_one(bits, field_unique, username, con_specs, backends)
        if err:
            print(err)
            return 1
        checked += 1

    rng = random.Random(SEED)
    backend_choices = [DEFAULT_BACKENDS] * 4 + OTHER_BACKENDS
    for _ in range(N_FUZZ):
        field_unique = rng.random() < 0.3
        username = rng.choice(NAMES)
        n = rng.randint(0, 5)
        con_specs = []
        for _ in range(n):
            k = rng.randint(1, 3)
            fields = tuple(rng.choice(NAMES) for _ in range(k))
            con_specs.append((fields, rng.random() < 0.4))
        backends = rng.choice(backend_choices)
        err = check_one(bits, field_unique, username, con_specs, backends)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched username-uniqueness check "
          "on %d inputs (%d boundary + %d fuzz, seed %d); 0 disagreements."
          % (checked, len(boundary), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
