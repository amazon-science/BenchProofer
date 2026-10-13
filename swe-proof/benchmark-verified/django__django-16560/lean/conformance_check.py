#!/usr/bin/env python3
"""G-CONF for django__django-16560.

The gold patch is already applied to /testbed when this runs. We compare the R/I
Python shadow of the three impls (`implementation_validateError`,
`implementation_constraintEq`, `implementation_serializedCode`, transliterated
op-for-op per refinement.md) against the REAL patched constraint behaviors, over
>=1e5 fuzzed inputs total. Zero disagreements => exit 0.

Modeled behaviors (mapping.md), all on `django.db.models.CheckConstraint` (the
optional code is threaded identically across BaseConstraint/CheckConstraint/
UniqueConstraint/ExclusionConstraint; CheckConstraint exercises all three without
needing a populated DB table):

  1. VALIDATION ERROR (`validateError`): call the real `constraint.validate(...)`.
     Oracle outcome modeled as Option (Option String):
       none      <-> nothing raised (no violation detected);
       some c    <-> a ValidationError was raised whose `.code` is c
                     (some s <-> code s, none <-> code None).
     Shadow = (some code) if violated else none.

  2. EQUALITY (`constraintEq`): real `a == b` for two CheckConstraints.
     rest <-> (name, message) comparison key (unchanged by the fix);
     code <-> violation_error_code. Shadow = (a.rest==b.rest) and (a.code==b.code).

  3. RECONSTRUCTION DATA (`serializedCode`): real
     `constraint.deconstruct()[2].get("violation_error_code")`.
     Shadow = code (some c <-> key present with value c; none <-> key absent).

stdlib-only; no hypothesis required.
"""
import random
import sys

import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=False,
        USE_TZ=False,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    )
    django.setup()

from django.core.exceptions import ValidationError
from django.db import models


class Product(models.Model):
    price = models.IntegerField()
    discounted_price = models.IntegerField()

    class Meta:
        app_label = "auth"  # piggy-back on an installed app; no table needed


# The conditional check used by the validation leg: violated iff
# price > discounted_price.
CHECK = models.Q(price__gt=models.F("discounted_price"))

# A pool of DISTINCT conditional checks for the equality leg, so the differential
# test exercises the unchanged `self.check == other.check` conjunct of `__eq__`
# (not just name/message). Keyed by index so the shadow's `rest` key can track
# check-equality exactly as real Q equality does.
CHECK_POOL = [
    models.Q(price__gt=models.F("discounted_price")),
    models.Q(price__gte=0),
    models.Q(price__lt=1),
    models.Q(discounted_price__gt=0),
]

CODE_POOL = [None, "fake_discount", "more_than_one", "custom_code", "baz", ""]
NAME_POOL = ["price", "price_lt_one", "name_uniq", "c"]
MSG_POOL = [None, "custom error", "discount is fake", "More than 1"]
KEY = "violation_error_code"


# ----- leg 1: validation error ------------------------------------------------

def oracle_validate(code, violated):
    """Outcome of the patched real validate(): None | ('raise', code)."""
    constraint = models.CheckConstraint(
        check=CHECK, name="price", violation_error_code=code,
        violation_error_message="msg %(name)s",
    )
    # violated -> price > discounted_price ; else not.
    if violated:
        instance = Product(price=10, discounted_price=42)
    else:
        instance = Product(price=10, discounted_price=5)
    try:
        constraint.validate(Product, instance)
    except ValidationError as e:
        return ("raise", e.code)
    return None


def shadow_validate(code, violated):
    """R/I transliteration of implementation_validateError."""
    if violated:
        return ("raise", code)
    return None


# ----- leg 2: equality --------------------------------------------------------

def make_check(name, chk_idx, msg, code):
    return models.CheckConstraint(
        check=CHECK_POOL[chk_idx], name=name, violation_error_message=msg,
        violation_error_code=code,
    )


def oracle_eq(a, b):
    return make_check(*a) == make_check(*b)


def shadow_eq(a, b):
    na, ka, ma, ca = a
    nb, kb, mb, cb = b
    # `rest` collapses the unchanged comparison payload (name, check, message);
    # `ca/cb` is the threaded code. `ka/kb` index distinct Q checks, so the key
    # captures real `self.check == other.check` (Q equality is structural).
    rest_a, rest_b = (na, ka, ma), (nb, kb, mb)
    return (rest_a == rest_b) and (ca == cb)


# ----- leg 3: reconstruction data ---------------------------------------------

def oracle_serialized(code):
    """Observe BOTH the serialized kwargs (key presence + value) AND that the
    code survives a deconstruct/reconstruct round-trip. Returns the round-tripped
    code value, or a sentinel when the key is absent from the kwargs."""
    constraint = make_check("price", 0, None, code)
    path, args, kwargs = constraint.deconstruct()
    present = KEY in kwargs
    if not present:
        # key absent from reconstruction data
        rebuilt = constraint.clone()
        assert rebuilt.violation_error_code == constraint.violation_error_code
        return "__ABSENT__"
    # key present: confirm a reconstructed constraint carries the same code
    from django.utils.module_loading import import_string
    klass = import_string(path)
    rebuilt = klass(*args, **kwargs)
    assert rebuilt.violation_error_code == kwargs[KEY], (rebuilt.violation_error_code, kwargs[KEY])
    return kwargs[KEY]


def shadow_serialized(code):
    # `some c` ⇒ key present with value c; `none` ⇒ key absent.
    return code if code is not None else "__ABSENT__"


def main():
    rng = random.Random(16560)  # pinned seed (mapping.md)
    N = 120_000
    disagreements = 0
    first = None

    def note(tag, args, o, s):
        nonlocal disagreements, first
        disagreements += 1
        if first is None:
            first = (tag, args, o, s)

    for _ in range(N):
        which = rng.randint(0, 2)
        if which == 0:
            code = rng.choice(CODE_POOL)
            violated = rng.choice([True, False])
            o = oracle_validate(code, violated)
            s = shadow_validate(code, violated)
            if o != s:
                note("validate", (code, violated), o, s)
        elif which == 1:
            a = (rng.choice(NAME_POOL), rng.randrange(len(CHECK_POOL)),
                 rng.choice(MSG_POOL), rng.choice(CODE_POOL))
            b = (rng.choice(NAME_POOL), rng.randrange(len(CHECK_POOL)),
                 rng.choice(MSG_POOL), rng.choice(CODE_POOL))
            o = oracle_eq(a, b)
            s = shadow_eq(a, b)
            if o != s:
                note("eq", (a, b), o, s)
        else:
            code = rng.choice(CODE_POOL)
            o = oracle_serialized(code)
            s = shadow_serialized(code)
            if o != s:
                note("serialized", (code,), o, s)

    if disagreements:
        print("G-CONF FAIL: %d/%d disagreements; first=%r" % (disagreements, N, first))
        return 1
    print("G-CONF OK: %d inputs, 0 disagreements" % N)
    return 0


if __name__ == "__main__":
    sys.exit(main())
