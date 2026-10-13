#!/usr/bin/env python3
"""G-CONF for django__django-14580.

The gold patch is already applied to /testbed when this runs. We compare the
R/I Python shadow of `implementation_serializeType` (the Lean impl,
transliterated op-for-op per refinement.md) against the REAL patched
`TypeSerializer.serialize`, over >=1e5 fuzzed inputs. Zero disagreements => exit 0.

Model (refinement.md / mapping.md): serializing a type object yields
`(source_text, imports)`. The implementation scans a two-row special-case table
by identity (`models.Model` -> ("models.Model", {"from django.db import models"});
`type(None)` -> ("type(None)", set())); otherwise it derives the reference from
the type's module/qualname (built-ins by bare name with no import).

  * Oracle  = the REAL patched `TypeSerializer(value).serialize()`.
  * Shadow  = the op-for-op transliteration below.

Type bijection (mapping.md): the input is a Python *type object*; the result is a
`(str, set[str])` pair. The Lean `List String` import view is duplicate-free and
its contents are the only observable, so we compare as sets.
stdlib-only beyond django itself; no hypothesis required.
"""
import builtins
import random
import sys

# --- configure Django settings before importing migration machinery ----------
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=False,
        USE_TZ=False,
        DATABASES={},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    )
    django.setup()

from django.db import models
from django.db.migrations.serializer import TypeSerializer


def oracle(value):
    """Behavior of the patched repo function for this type object."""
    string, imports = TypeSerializer(value).serialize()
    return string, set(imports)


def shadow(value):
    """R/I transliteration of implementation_serializeType (Lean).

    Op 1/2: scan the special-case table by identity.
    Op 3/4: module/qualname fallback (built-ins: bare name, no import).
    """
    special_cases = [
        (models.Model, "models.Model", ["from django.db import models"]),
        (type(None), "type(None)", []),
    ]
    for case, string, imports in special_cases:
        if case is value:
            return string, set(imports)
    module = value.__module__
    if module == builtins.__name__:
        return value.__name__, set()
    return "%s.%s" % (module, value.__qualname__), {"import %s" % module}


# A custom model + other module-qualified types for the `.other` branch.
class _MyModel(models.Model):
    class Meta:
        app_label = "contenttypes"


class _PlainOther:
    pass


import collections
import datetime
import decimal

BUILTINS = [int, str, bytes, float, bool, list, dict, tuple, set, type, object]
OTHERS = [
    models.Model, type(None),                 # the two special cases (oversampled)
    models.TextField, models.CharField, models.Field,
    _MyModel, _PlainOther,
    datetime.datetime, datetime.date, decimal.Decimal,
    collections.OrderedDict, collections.abc.Mapping,
    Exception, ValueError,
]
# Oversample the discriminating special cases.
POOL = [models.Model] * 8 + [type(None)] * 4 + BUILTINS + OTHERS


def main():
    rng = random.Random(14580)  # pinned seed (mapping.md)
    N = 120_000
    disagreements = 0
    first = None
    for _ in range(N):
        value = rng.choice(POOL)
        o = oracle(value)
        s = shadow(value)
        if o != s:
            disagreements += 1
            if first is None:
                first = (value, o, s)
    if disagreements:
        print("G-CONF FAIL: %d/%d disagreements; first=%r" % (disagreements, N, first))
        return 1
    print("G-CONF OK: %d inputs, 0 disagreements (seed=14580)" % N)
    return 0


if __name__ == "__main__":
    sys.exit(main())
