#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-11790 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures) stripped. The @Pure helpers (default_limit /
attr_maxlength / attr_other / resolve_limit) copy over as plain functions.
There are no @ContractOnly callees in this bundle.

ORACLE: the REAL patched repo operation the model models per mapping.md --
the username-field configuration performed by
`django.contrib.auth.forms.AuthenticationForm.__init__`. The gate applies
patch.diff to /testbed before this script runs; PYTHONPATH=/testbed makes
the patched module importable. Each trial instantiates the real form against
a user model whose identifier column declares a chosen max_length (possibly
None) and with a chosen pre-existing widget-attribute mapping, then reads
off `field.max_length` and the full post-state of `field.widget.attrs`.

Type bridge (mapping.md section 2):
  * `declared_max_length: Optional[int]`  <->  the user model's identifier
    column `max_length`. Per mapping.md the repo domain is None or a
    positive int (never 0), so the fuzz draws None or ints >= 1.
  * `widget_attrs: Dict[str, object]`  <->  the widget's attribute dict
    (str keys, arbitrary values). The attribute-NAME bridge is the IDENTITY:
    a name is carried as the text it actually is, with 'maxlength' <->
    attr_maxlength() and 'autofocus' <-> attr_other() being the same strings
    in the model as in the repo, so this harness passes the real attribute
    dict to the shadow unchanged and compares the post-state for exact dict
    equality. Nothing is tokenized. That matters for what this harness can
    SEE: an injective int tokenization of the names would make an attribute
    name and a LENGTH the same kind of thing, so a shadow that published the
    limit under a name computed out of the length domain would be inverted
    back to the right name and the disagreement would be hidden. Values are
    likewise carried verbatim (the opaque value domain), so a shadow that
    computed with a stored value would be caught by the real TypeError.
  * The shadow's returned int  <->  the real `field.max_length` (identity).

Requires bridge: `dict_pred(widget_attrs)` is the ONLY precondition, so the
domain is TOTAL and every trial is in-domain whatever the widget carries. The
generators accordingly cover all four quadrants: 'maxlength' present/absent
(a pre-existing stale limit, as a subclass-declared CharField widget carries)
crossed with 'autofocus' present/absent (a bare widget). Declared max_length
covers None, 0 (reachable via a TextField USERNAME_FIELD -- see the note in
mapping.md section 2) and positive ints.

The pre-state of the real widget attrs is controlled directly: the form
class's base field widget attrs are replaced per trial, and the form's
per-instance deepcopy of the field carries them into __init__ unchanged.
User model classes are cached per declared max_length (Django registers
model classes globally), bounding registry growth while the attribute
mapping and declared length vary freely across trials.

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz trials.
Pinned fuzz seed: 11790.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import os
import random
import sys
import tempfile

SEED = 11790
N_FUZZ = 100_000


# --- pure helpers from model.py, decorators/contracts stripped ---------------

def default_limit():
    # The length limit used when the user model declares no maximum.
    return 254


def attr_maxlength():
    # The dedicated widget attribute NAME for the rendered length limit.
    return 'maxlength'


def attr_other():
    # A representative pre-existing, unrelated widget attribute NAME.
    return 'autofocus'


def resolve_limit(declared):
    """The resolved length limit: the declared maximum when a usable one is
    declared, otherwise the default. A declared maximum of 0 conveys no usable
    length and resolves to the default, mirroring the repo's truthiness test."""
    if declared is None:
        return default_limit()
    if declared == 0:
        return default_limit()
    return declared


# --- the impl region of model.py, verbatim, contract calls stripped ----------

def configure_username_field(declared_max_length, widget_attrs):
    username_max_length = resolve_limit(declared_max_length)
    field_max_length = username_max_length
    widget_attrs[attr_maxlength()] = username_max_length
    return field_max_length


# --- Django scaffolding (same shape as axiom_check.py) -----------------------
# The throwaway app must be a REAL package on disk (Django computes
# AppConfig.path from the module's location), materialised before setup().

_APP_NAME = 'conf_check_app'
_pkg_parent = tempfile.mkdtemp(prefix='confcheck_')
_pkg_dir = os.path.join(_pkg_parent, _APP_NAME)
os.makedirs(_pkg_dir, exist_ok=True)
with open(os.path.join(_pkg_dir, '__init__.py'), 'w') as _f:
    _f.write('')
with open(os.path.join(_pkg_dir, 'models.py'), 'w') as _f:
    _f.write('')
sys.path.insert(0, _pkg_parent)

import django  # noqa: E402
from django.conf import settings  # noqa: E402

if not settings.configured:
    settings.configure(
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3',
                               'NAME': ':memory:'}},
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'django.contrib.auth',
            _APP_NAME,
        ],
        AUTH_USER_MODEL='auth.User',
        USE_TZ=False,
    )

django.setup()

from django.db import models  # noqa: E402
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager  # noqa: E402
from django.contrib.auth import forms as auth_forms  # noqa: E402


_MODEL_CACHE = {}


def _user_model(declared):
    """A concrete AbstractBaseUser subclass whose USERNAME_FIELD column
    declares max_length == declared (None via IntegerField). Cached per
    declared value: model classes register globally in Django's app
    registry, so trials reuse them."""
    if declared in _MODEL_CACHE:
        return _MODEL_CACHE[declared]
    if declared is None:
        field = models.IntegerField()
        name = 'ConfUserNone'
    elif declared == 0:
        # A declared max_length of 0 is REACHABLE for a USERNAME_FIELD:
        # fields.E121 ("must be a positive integer") comes from
        # CharField._check_max_length_attribute, so it does not apply to
        # TextField. django.core.checks.run_checks() is CLEAN for this model.
        field = models.TextField(unique=True, max_length=0)
        name = 'ConfUserZero'
    else:
        field = models.CharField(max_length=declared)
        name = 'ConfUser%d' % declared
    Meta = type('Meta', (), {'app_label': _APP_NAME})
    cls = type(name, (AbstractBaseUser,), {
        '__module__': _APP_NAME + '.models',
        'Meta': Meta,
        'username': field,
        'password': models.CharField(max_length=255),
        'USERNAME_FIELD': 'username',
        'REQUIRED_FIELDS': [],
        'objects': BaseUserManager(),
    })
    _MODEL_CACHE[declared] = cls
    return cls


# One reusable form subclass; its base field's widget attrs are replaced per
# trial and the per-instance field deepcopy carries them into __init__.
class _ConfForm(auth_forms.AuthenticationForm):
    pass


def run_real(declared, pre_attrs):
    """Execute the REAL patched repo operation: instantiate the form with the
    given pre-existing widget attrs and user model, return (field.max_length,
    post-state widget attrs dict)."""
    auth_forms.UserModel = _user_model(declared)
    _ConfForm.base_fields['username'].widget.attrs = dict(pre_attrs)
    form = _ConfForm()
    field = form.fields['username']
    return field.max_length, dict(field.widget.attrs)


def run_shadow(declared, pre_attrs):
    """Run the contract-stripped impl region on a copy of the real pre-state
    attribute dict and return (returned limit, expected attrs dict, None).

    No bridging is needed in either domain: attribute names are the same
    strings in the model as in the repo, and values are carried verbatim, so
    the shadow's post-state IS the expected attribute dict. Any deviation --
    including publishing the limit under a name other than 'maxlength' --
    shows up directly as a dict inequality rather than being absorbed by an
    inverse mapping."""
    attrs = dict(pre_attrs)
    ret = configure_username_field(declared, attrs)
    for name in attrs:
        if not isinstance(name, str):
            return None, None, ('shadow wrote a non-string attribute name %r: '
                                'the real widget attribute dict is keyed by '
                                'attribute-name strings' % (name,))
    return ret, attrs, None


def check(declared, pre_attrs):
    shadow_ret, shadow_attrs, err = run_shadow(declared, pre_attrs)
    real_ret, real_attrs = run_real(declared, pre_attrs)
    if err is None and shadow_ret == real_ret and shadow_attrs == real_attrs:
        return None
    return ("DISAGREEMENT\n  declared=%r pre_attrs=%r\n"
            "  shadow: max_length=%r attrs=%r%s\n"
            "  real:   max_length=%r attrs=%r"
            % (declared, pre_attrs, shadow_ret, shadow_attrs,
               (' (%s)' % err) if err else '', real_ret, real_attrs))


_ATTR_NAMES = ['autocapitalize', 'autocomplete', 'placeholder', 'class',
               'spellcheck', 'inputmode', 'data-a', 'data-b', 'data-c',
               'size', 'title']
# Deliberately HETEROGENEOUS, matching the real widget attrs (bool / str /
# int all occur: {'autofocus': True, 'autocapitalize': 'none', ...}). This is
# what the Dict[str, object] opaque value carrier abstracts.
_ATTR_VALUES = [True, False, 'none', 'off', 'username', 'text', 'x', '',
                0, 1, 7, 42, 'a b c']


def rand_pre_attrs(rng):
    # The domain is TOTAL, so both 'autofocus' and 'maxlength' vary freely:
    # a bare widget (no other attribute) and a widget that already advertises
    # a stale length limit of its own are both in-domain and both generated.
    attrs = {}
    if rng.random() < 0.75:
        attrs['autofocus'] = rng.choice([True, 'autofocus', 1])
    if rng.random() < 0.25:
        attrs['maxlength'] = rng.choice([75, '75', 150, 254])
    for name in rng.sample(_ATTR_NAMES, rng.randint(0, 6)):
        attrs[name] = rng.choice(_ATTR_VALUES)
    return attrs


def rand_declared(rng):
    if rng.random() < 0.2:
        return None
    if rng.random() < 0.05:
        return 0          # falsy declared maximum -> resolves to the default
    if rng.random() < 0.9:
        return rng.randint(1, 600)
    return rng.randint(601, 4000)


def boundary_cases():
    minimal = {'autofocus': True}
    rich = {'autofocus': True, 'autocapitalize': 'none',
            'autocomplete': 'username', 'placeholder': 'id', 'size': 20}
    bare = {}                                  # a widget with NO attributes
    stale = {'maxlength': '75'}                # already advertises its own cap
    stale_rich = {'autofocus': True, 'autocapitalize': 'none',
                  'autocomplete': 'username', 'maxlength': 75}
    cases = []
    for declared in (None, 0, 1, 2, 150, 253, 254, 255, 256, 320, 999, 1000,
                     1001, 4000):
        for pre in (minimal, rich, bare, stale, stale_rich):
            cases.append((declared, pre))
    return cases


def main():
    rng = random.Random(SEED)
    checked = 0
    n_boundary = 0
    saved = auth_forms.UserModel
    try:
        for declared, pre_attrs in boundary_cases():
            err = check(declared, pre_attrs)
            if err:
                print(err)
                return 1
            checked += 1
            n_boundary += 1
        for _ in range(N_FUZZ):
            declared = rand_declared(rng)
            pre_attrs = rand_pre_attrs(rng)
            err = check(declared, pre_attrs)
            if err:
                print(err)
                return 1
            checked += 1
    finally:
        auth_forms.UserModel = saved

    print("G-CONF OK: shadow impl == real AuthenticationForm username-field "
          "configuration (field.max_length AND full widget attrs post-state) "
          "on %d inputs (%d boundary + %d fuzz, seed %d)."
          % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
