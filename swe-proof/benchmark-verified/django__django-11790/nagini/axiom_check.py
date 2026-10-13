#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-11790.

This bundle has NO consumed axioms: the username-field configuration is
modelled DEEPLY (the length resolution and the two writes are spelled out in
model.py's impl region). G-AX therefore validates the single **A-reference** --
that the deep model equals the real operation it mirrors -- by executing the
REAL repository code (`django.contrib.auth.forms.AuthenticationForm.__init__`,
gold-patched) in the evaluation container and asserting that, for a range of
user models, the resulting username field's length limit and the rendered
widget's length-limit attribute both match the deep model.

The real operation, for a user model whose identifier column declares
``max_length`` (possibly ``None``), configures the form's ``username`` field as:

    username_max_length = <declared max_length> or 254
    field.max_length            = username_max_length
    widget.attrs['maxlength']   = username_max_length

We instantiate the actual `AuthenticationForm` against several user models
whose `USERNAME_FIELD` declares varying `max_length` (including ``None``, which
must resolve to the default 254), reading off `field.max_length` and
`field.widget.attrs.get('maxlength')` exactly as the FAIL_TO_PASS tests do.
No database row is required: `__init__` only reads field metadata.

Deep model under check (model.py impl region):
    resolved   = declared if declared is not None else 254
    field.max_length          == resolved
    widget.attrs['maxlength']  == resolved      (the key the regression dropped)
    other widget attributes preserved unchanged

Imports: the standard library plus the Django package under evaluation (the
very module the gold patch edits). Exit 0 iff every observation matches.
"""
import os
import random
import sys
import tempfile

import django
from django.conf import settings

# A throwaway app holding test user models with various username max_length.
# Django rejects an app module with no filesystem location (it computes
# AppConfig.path from the module's __file__/__path__), so the app must be a
# REAL package on disk. We materialise an empty package in a tempdir and put
# its parent on sys.path BEFORE django.setup() runs.
_APP_NAME = 'axiom_check_app'
_pkg_parent = tempfile.mkdtemp(prefix='axcheck_')
_pkg_dir = os.path.join(_pkg_parent, _APP_NAME)
os.makedirs(_pkg_dir, exist_ok=True)
with open(os.path.join(_pkg_dir, '__init__.py'), 'w') as _f:
    _f.write('')
with open(os.path.join(_pkg_dir, 'models.py'), 'w') as _f:
    _f.write('')
sys.path.insert(0, _pkg_parent)

# Minimal Django configuration so the auth forms / models import cleanly.
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


def _make_user_model(name, username_field):
    """Build a concrete AbstractBaseUser subclass whose USERNAME_FIELD column
    is `username_field`, registered in the throwaway app."""
    Meta = type('Meta', (), {'app_label': 'axiom_check_app'})
    attrs = {
        '__module__': 'axiom_check_app.models',
        'Meta': Meta,
        'username': username_field,
        'password': models.CharField(max_length=255),
        'USERNAME_FIELD': 'username',
        'REQUIRED_FIELDS': [],
        'objects': BaseUserManager(),
    }
    return type(name, (AbstractBaseUser,), attrs)


def deep_model(declared):
    """model.py's deep model: resolve declared-or-254, used for both writes.
    A declared maximum that is absent OR zero (no usable length) resolves to
    the default, mirroring the repo's truthiness test."""
    if declared is None or declared == 0:
        return 254
    return declared


def check(model_name, username_field, declared):
    user_model = _make_user_model(model_name, username_field)
    # Point the auth machinery at this user model for the form construction.
    auth_forms.UserModel = user_model
    form = auth_forms.AuthenticationForm()                 # real repo __init__
    field = form.fields['username']
    observed_field = field.max_length                      # real callee
    observed_attr = field.widget.attrs.get('maxlength')    # real callee
    expected = deep_model(declared)                        # deep model
    assert observed_field == expected, (
        "deep model unsound (field.max_length) for declared=%r: real form gave "
        "%r, deep model gives %r" % (declared, observed_field, expected))
    assert observed_attr == expected, (
        "deep model unsound (widget maxlength attr) for declared=%r: real form "
        "gave %r, deep model gives %r" % (declared, observed_attr, expected))
    # The attribute NAMES are textual, and that is recorded here because it is
    # what makes the model's name domain a text domain disjoint from the length
    # domain (mapping.md section 2). Every key of the real widget attribute
    # mapping is an attribute-name string, and no length is ever a key: a
    # number could not name an attribute a browser honours. If a key were ever
    # numeric, an attribute name and a LENGTH would be the same kind of thing
    # in the repo too, and the model's separation of the two would be wrong.
    for key in field.widget.attrs:
        assert isinstance(key, str) and not isinstance(key, bool), (
            "widget attribute name %r is not a string; the textual name domain "
            "in model.py assumes every attribute name is one" % (key,))
        assert not isinstance(key, int), (
            "widget attribute name %r is numeric; model.py's name domain is "
            "disjoint from the length domain and assumes no length can name "
            "an attribute" % (key,))
    # The dedicated name is the literal string the browser honours, so the
    # model's attr_maxlength() is that name itself and not an encoding of it.
    assert 'maxlength' in field.widget.attrs, (
        "the length limit is not published under 'maxlength' for declared=%r"
        % (declared,))
    # Other widget attributes the field configures (autocapitalize/autocomplete
    # /autofocus) must survive: the operation only adds 'maxlength'.
    # The pre-existing widget attributes must survive, AND their runtime types
    # are recorded here because they are what makes the model's value domain
    # OPAQUE (mapping.md section 2): these values are NOT uniformly numeric, so
    # nothing may be computed from a value read out of the attribute mapping.
    for preserved in ('autocapitalize', 'autocomplete', 'autofocus'):
        if preserved in field.widget.attrs:
            value = field.widget.attrs[preserved]
            assert value is not None
            # A non-numeric attribute value must NOT support arithmetic or
            # ordering against an int -- the operations the int carrier used to
            # admit silently. If this ever stopped raising, the opaque value
            # domain would be over-strong and the mapping note would be wrong.
            if isinstance(value, str):
                for op in ('arith', 'order'):
                    try:
                        if op == 'arith':
                            1 + 0 * value          # noqa: B018
                        else:
                            value > 0              # noqa: B015
                    except TypeError:
                        pass
                    else:
                        raise AssertionError(
                            "widget attribute %r value %r unexpectedly supports "
                            "%s against an int; the opaque value carrier in "
                            "model.py assumes it does not" % (preserved, value, op))


def main():
    saved = auth_forms.UserModel
    try:
        # --- boundary cases ------------------------------------------------
        # IntegerField has no max_length -> None -> resolves to default 254.
        check('IntUser', models.IntegerField(), None)
        # A DECLARED ZERO is reachable and resolves to the default too: the
        # positive-integer check (fields.E121) lives on CharField, so a
        # TextField USERNAME_FIELD with max_length=0 passes the full check
        # registry cleanly. The real form yields 254 here (0 is falsy).
        check('ZeroTextUser', models.TextField(unique=True, max_length=0), 0)
        # The two FAIL_TO_PASS configurations: 255 and the 254 default.
        check('Char255User', models.CharField(max_length=255), 255)
        check('Char254User', models.CharField(max_length=254), 254)
        # Other declared lengths must be reflected verbatim in BOTH places.
        check('Char1User', models.CharField(max_length=1), 1)
        check('Char150User', models.CharField(max_length=150), 150)
        check('Char1000User', models.CharField(max_length=1000), 1000)
        check('EmailUser', models.EmailField(max_length=320), 320)

        # --- randomized fuzz over declared lengths -------------------------
        rng = random.Random(11790)
        for i in range(200):
            n = rng.randint(1, 4000)
            check('FuzzUser%d' % i, models.CharField(max_length=n), n)
    finally:
        auth_forms.UserModel = saved

    print("G-AX OK: deep model (A-reference) == real AuthenticationForm "
          "username-field configuration (field.max_length AND "
          "widget.attrs['maxlength']) over 7 boundary + 200 fuzz user models; "
          "None resolves to the default 254.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
