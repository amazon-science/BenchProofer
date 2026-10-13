#!/usr/bin/env python3
"""G-CONF for django__django-11138.

The gold patch is already applied to /testbed when this runs. We compare the
R/I Python shadow of `implementation_tzConvertSql` (the Lean impl, transliterated
op-for-op per refinement.md) against the REAL patched
`mysql.operations.DatabaseOperations._convert_field_to_tz`, over >=1e5 fuzzed
inputs. Zero disagreements => exit 0.

Type bijection (mapping.md): useTz<->settings.USE_TZ (bool),
connTz<->self.connection.timezone_name (str), tzname<->tzname (str),
fieldName<->field_name (str), result<->return value (str).
stdlib-only; no hypothesis required.
"""
import os
import random
import sys

# --- configure Django settings before importing the backend module ---------
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=False,
        USE_TZ=True,
        TIME_ZONE="UTC",
        DATABASES={},
        INSTALLED_APPS=[],
    )
    django.setup()

from django.db.backends.mysql.operations import DatabaseOperations


class _FakeConnection:
    def __init__(self, timezone_name):
        self.timezone_name = timezone_name


class _FakeOps:
    """Minimal stand-in exposing only what `_convert_field_to_tz` reads."""
    def __init__(self, conn_tz):
        self.connection = _FakeConnection(conn_tz)


# The real (patched) method, called against our fake self.
_real_method = DatabaseOperations.__dict__["_convert_field_to_tz"]


def oracle(use_tz, conn_tz, tzname, field_name):
    """Behavior of the patched repo function for these inputs."""
    settings.USE_TZ = use_tz
    return _real_method(_FakeOps(conn_tz), field_name, tzname)


def shadow(use_tz, conn_tz, tzname, field_name):
    """R/I transliteration of implementation_tzConvertSql (Lean)."""
    field = field_name
    if use_tz and conn_tz != tzname:
        field = "CONVERT_TZ(%s, '%s', '%s')" % (field, conn_tz, tzname)
    return field


TZ_POOL = [
    "UTC", "Europe/Paris", "Asia/Bangkok", "Africa/Nairobi",
    "America/New_York", "Australia/Sydney", "Etc/GMT+5", "local",
]
FIELD_POOL = [
    "`my_model`.`dt`", "col", "`t`.`f`", "x", "DATE(`a`.`b`)",
    "`field_name`", "f0", "tbl.column",
]


def rand_str(rng):
    n = rng.randint(0, 6)
    alpha = "abcEFG_/+0123 "
    return "".join(rng.choice(alpha) for _ in range(n))


def main():
    rng = random.Random(11138)  # pinned seed (mapping.md)
    N = 100_000
    disagreements = 0
    first = None
    for i in range(N):
        use_tz = rng.choice([True, False])
        # Bias toward equal-tz / unequal-tz / UTC boundaries, plus random noise.
        if i % 3 == 0:
            conn_tz = rng.choice(TZ_POOL)
            tzname = conn_tz                 # equal-tz boundary
        elif i % 3 == 1:
            conn_tz = rng.choice(TZ_POOL)
            tzname = rng.choice(TZ_POOL)
        else:
            conn_tz = rand_str(rng) or "UTC"
            tzname = rand_str(rng) or "UTC"
        field_name = rng.choice(FIELD_POOL) if rng.random() < 0.7 else rand_str(rng)
        o = oracle(use_tz, conn_tz, tzname, field_name)
        s = shadow(use_tz, conn_tz, tzname, field_name)
        if o != s:
            disagreements += 1
            if first is None:
                first = (use_tz, conn_tz, tzname, field_name, o, s)
    if disagreements:
        print("G-CONF FAIL: %d/%d disagreements; first=%r" % (disagreements, N, first))
        return 1
    print("G-CONF OK: %d inputs, 0 disagreements" % N)
    return 0


if __name__ == "__main__":
    sys.exit(main())
