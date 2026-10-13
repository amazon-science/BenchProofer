#!/usr/bin/env python3
"""G-CONF for django__django-13741.

The gold patch is already applied to /testbed when this runs. We compare the
R/I Python shadow of `implementation_passwordHashField` (the Lean impl,
transliterated op-for-op per refinement.md) against the REAL patched
`ReadOnlyPasswordHashField`: for each fuzzed case we construct the field with the
chosen `disabled` kwarg and read `field.disabled` and
`field.has_changed(initial, data)`. Over >=1e5 fuzzed cases, zero disagreements
=> exit 0.

Model (refinement.md):
  * disabled = the supplied `disabled` kwarg, or True when not supplied
    (`kwargs.setdefault('disabled', True)`);
  * changed  = False if disabled, else (initial_value != data_value) with
    None normalised to '' on each side (base Field.has_changed, no _coerce /
    to_python override on this field).

Type bijection (mapping.md):
  disabledArg : Option Bool  <->  presence/value of the `disabled` kwarg
  initial, data : Option String  <->  None | str
  FieldOutcome.disabled : Bool   <->  field.disabled
  FieldOutcome.changed : Bool    <->  field.has_changed(initial, data)
stdlib-only; no hypothesis required.
"""
import random
import sys

# --- configure Django settings before importing the form machinery -----------
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=False,
        # importing django.contrib.auth.forms eagerly builds
        # default_token_generator, which reads settings.SECRET_KEY at import.
        SECRET_KEY="conformance-check-13741",
        USE_TZ=False,
        USE_L10N=False,
        DATABASES={},
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'django.contrib.auth',
        ],
        USE_I18N=False,
    )
    django.setup()

from django.contrib.auth.forms import ReadOnlyPasswordHashField


def oracle(disabled_arg, initial, data):
    """Observable config + decision of the REAL patched field.

    disabled_arg: None (kwarg absent) | True | False.
    Returns (field.disabled, field.has_changed(initial, data)).
    """
    if disabled_arg is None:
        field = ReadOnlyPasswordHashField()
    else:
        field = ReadOnlyPasswordHashField(disabled=disabled_arg)
    return (bool(field.disabled), bool(field.has_changed(initial, data)))


def _val_eq(a, b):
    """R/I `valEq`: missing (None) normalised to '' then compared for equality."""
    av = a if a is not None else ""
    bv = b if b is not None else ""
    return av == bv


def shadow(disabled_arg, initial, data):
    """R/I transliteration of implementation_passwordHashField (Lean).

    Op 1: disabled := disabledArg.getD true  (setdefault('disabled', True)).
    Op 2: if disabled -> changed = False.
    Op 3: else changed = not valEq(initial, data).
    """
    disabled = disabled_arg if disabled_arg is not None else True
    if disabled:
        changed = False
    else:
        changed = not _val_eq(initial, data)
    return (bool(disabled), bool(changed))


_STRINGS = [None, "", "a", "b", "abc", "abc", "café", "Éric", "  ", "hash$pbkdf2",
            "x", "x ", " x", "0", "False", "None"]


def rand_case(rng):
    disabled_arg = rng.choice([None, True, False])
    initial = rng.choice(_STRINGS)
    data = rng.choice(_STRINGS)
    return disabled_arg, initial, data


FIXED = [
    (None, "aaa", "bbb"),     # the F2P scenario: default-disabled field, differing values
    (None, "aaa", "aaa"),
    (None, None, None),
    (None, None, "x"),
    (True, "aaa", "bbb"),
    (False, "aaa", "bbb"),
    (False, "aaa", "aaa"),
    (False, None, ""),
    (False, "", None),
    (False, None, "x"),
    (False, "x", None),
]


def main():
    rng = random.Random(13741)  # pinned seed (mapping.md)
    N = 100_000
    disagreements = 0
    first = None
    for i in range(N):
        case = FIXED[i] if i < len(FIXED) else rand_case(rng)
        o = oracle(*case)
        s = shadow(*case)
        if o != s:
            disagreements += 1
            if first is None:
                first = (case, o, s)
    if disagreements:
        print("G-CONF FAIL: %d/%d disagreements; first=%r" % (disagreements, N, first))
        return 1
    print("G-CONF OK: %d inputs, 0 disagreements" % N)
    return 0


if __name__ == "__main__":
    sys.exit(main())
