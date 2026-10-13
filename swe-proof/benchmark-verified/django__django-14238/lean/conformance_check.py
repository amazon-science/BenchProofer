#!/usr/bin/env python3
"""G-CONF for django__django-14238.

The gold patch is already applied to /testbed when this runs. We compare the
R/I Python shadow of `implementation_subclassCheck` (the Lean impl,
transliterated op-for-op per refinement.md) against the REAL patched
`AutoFieldMeta.__subclasscheck__` (reached via `issubclass(candidate, AutoField)`),
over >=1e5 fuzzed candidate classes. Zero disagreements => exit 0.

Model (refinement.md): a candidate class is accepted iff it is a reflexive-
transitive subclass of one of the designated member classes
(`AutoField._subclasses == (BigAutoField, SmallAutoField)`), OR the ordinary
inherited check accepts it. The fix replaced the identity-membership test
(`subclass in self._subclasses`) with the subclass test
(`issubclass(subclass, self._subclasses)`).

  * Oracle  = the REAL patched check `issubclass(candidate, models.AutoField)`,
              which dispatches through `AutoFieldMeta.__subclasscheck__`.
  * Shadow  = any(isSub(candidate, m) for m in members) or superCheck(candidate),
              where members      = AutoField._subclasses (the designated tuple),
                    isSub        = the REAL builtin `issubclass` (A-reference op #3),
                    superCheck   = the REAL inherited `type.__subclasscheck__`
                                   bound to AutoField (A-reference op #4).

Type bijection (mapping.md): Cls<->class object; subclasses<->AutoField._subclasses
(tuple/list); isSub<->issubclass (bool); superCheck<->super().__subclasscheck__
(bool); result<->the bool returned (true<->True).
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
        DATABASES={},
        INSTALLED_APPS=[],
        TEMPLATES=[],
    )
    django.setup()

from django.db import models

AutoField = models.AutoField
BigAutoField = models.BigAutoField
SmallAutoField = models.SmallAutoField
IntegerField = models.IntegerField
BigIntegerField = models.BigIntegerField
SmallIntegerField = models.SmallIntegerField

# The designated member tuple, read off the real metaclass property.
MEMBERS = AutoField._subclasses  # (BigAutoField, SmallAutoField)


# --- candidate class pool ---------------------------------------------------
# Real classes plus user subclasses (the regression case) and deeper chains.
class MyBigAutoField(BigAutoField):
    pass


class MySmallAutoField(SmallAutoField):
    pass


class DeeperBigAutoField(MyBigAutoField):
    pass


class MyAutoField(AutoField):
    pass


class UnrelatedField(models.Field):
    pass


CANDIDATES = [
    AutoField, BigAutoField, SmallAutoField,
    MyBigAutoField, MySmallAutoField, DeeperBigAutoField, MyAutoField,
    IntegerField, BigIntegerField, SmallIntegerField,
    models.Field, UnrelatedField,
    object, int, str,
    models.CharField, models.TextField, models.BooleanField,
]


def oracle(candidate):
    """Behavior of the patched repo check for this candidate class."""
    return bool(issubclass(candidate, AutoField))


def shadow(candidate):
    """R/I transliteration of implementation_subclassCheck (Lean).

    Op 1/2: any over the designated member tuple.
    Op 3 (A-reference): the REAL `issubclass` subclass relation per member.
    Op 4 (A-reference): the REAL inherited `type.__subclasscheck__` disjunct.
    """
    matched = False
    for d in MEMBERS:
        if issubclass(candidate, d):
            matched = True
    # superCheck = super(AutoFieldMeta, AutoField).__subclasscheck__(candidate),
    # i.e. the ordinary inherited subclass check (type.__subclasscheck__).
    super_check = bool(type.__subclasscheck__(AutoField, candidate))
    return matched or super_check


def main():
    rng = random.Random(14238)  # pinned seed (mapping.md)
    N = 100_000
    disagreements = 0
    first = None
    for i in range(N):
        candidate = rng.choice(CANDIDATES)
        o = oracle(candidate)
        s = shadow(candidate)
        if o != s:
            disagreements += 1
            if first is None:
                first = (getattr(candidate, "__name__", repr(candidate)), o, s)
    if disagreements:
        print("G-CONF FAIL: %d/%d disagreements; first=%r" % (disagreements, N, first))
        return 1
    print("G-CONF OK: %d inputs, 0 disagreements" % N)
    return 0


if __name__ == "__main__":
    sys.exit(main())
