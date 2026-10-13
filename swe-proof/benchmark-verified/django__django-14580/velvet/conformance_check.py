#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-14580 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region (`renderTypeRef`,
              routed through the deep model `typeRef`) transliterated to Python
              over the real repo type (a runtime `type` object), via the
              mapping.md §2 bijection (a Python `type` ↔ its observable-field
              record `TypeInfo`; `set(imports)` ↔ the list literal). There are NO
              A-tagged callees in the impl region (no axioms), so the shadow is
              pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the REAL patched
              `MigrationWriter.serialize(value)` applied at base_commit (the
              harness applies the gold patch before this runs). For a `type`
              value this dispatches through `serializer_factory` to the patched
              `TypeSerializer.serialize` (the function under change).

They must agree on the rendered string AND the import set for every input. Exit
0 iff zero disagreements; any disagreement is a mechanical R/I-fidelity
counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + django only.
The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import collections
import datetime
import decimal
import random
import sys
import uuid

SEED = 14580
N_FUZZ = 100_000

# --- minimal django bootstrap (no DB / app registry beyond models) -----------
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=[
            "django.contrib.contenttypes",
            "django.contrib.auth",
        ],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
        USE_TZ=True,
    )
django.setup()

from django.db import models
from django.db.migrations.writer import MigrationWriter


# --- the R/I shadow: Solution.lean typeRef/renderTypeRef, transliterated -----

def type_info(v):
    """The mapping.md §2 bijection: a Python `type` -> its observable slice
    (the fields TypeSerializer.serialize actually reads)."""
    return {
        "isBaseModelType": v is models.Model,
        "isNoneType": v is type(None),
        "moduleName": getattr(v, "__module__", ""),
        "qualName": getattr(v, "__qualname__", getattr(v, "__name__", "")),
        "simpleName": v.__name__,
    }


def shadow_type_ref(v):
    """typeRef (type_info v) transliterated to Python: returns
    (string, set_of_imports). Branch order EXACTLY as Solution.lean's typeRef
    (and the source special_cases ordering): base-model, then none-type, then
    builtins, then the module tail."""
    t = type_info(v)
    if t["isBaseModelType"]:
        return ("models.Model", {"from django.db import models"})
    elif t["isNoneType"]:
        return ("type(None)", set())
    elif t["moduleName"] == "builtins":
        return (t["simpleName"], set())
    else:
        return ("%s.%s" % (t["moduleName"], t["qualName"]),
                {"import %s" % t["moduleName"]})


def oracle_serialize(v):
    """patch.diff's behaviour: the REAL patched MigrationWriter.serialize for a
    `type` value (dispatches to the patched TypeSerializer.serialize)."""
    string, imports = MigrationWriter.serialize(v)
    return (string, set(imports))


# --- top-level helper classes for the module-tail branch ---------------------

class PlainClass:
    pass


class ModelSubclass(models.Model):
    class Meta:
        app_label = "contenttypes"


class FieldSubclass(models.TextField):
    pass


def corpus():
    """Real `type` objects spanning the four branches. The base-model class
    `models.Model` (the discriminating input the issue + F2P target) is included
    and is exercised on every fuzz iteration via the weighted choice below."""
    builtin_types = [
        int, str, float, bool, bytes, bytearray, list, tuple, set, frozenset,
        dict, object, type, complex, range, slice, memoryview,
    ]
    module_types = [
        PlainClass, ModelSubclass, FieldSubclass,
        collections.OrderedDict, collections.defaultdict, collections.deque,
        collections.Counter, datetime.date, datetime.datetime, datetime.time,
        datetime.timedelta, decimal.Decimal, uuid.UUID,
        models.TextField, models.IntegerField, models.CharField, models.Field,
        Exception, ValueError,
    ]
    special = [models.Model, type(None)]
    return special, builtin_types, module_types


def main():
    rng = random.Random(SEED)
    special, builtin_types, module_types = corpus()
    all_types = special + builtin_types + module_types

    disagreements = []
    count = 0

    def check(v):
        nonlocal count
        count += 1
        shadow = shadow_type_ref(v)
        oracle = oracle_serialize(v)
        if shadow != oracle:
            disagreements.append((v, shadow, oracle))

    # boundary: every corpus type at least once (deterministic coverage)
    for v in all_types:
        check(v)

    # weighted fuzz: keep hammering the discriminating special cases plus the
    # full corpus so the apostrophe of this bundle — the dropped import — would
    # surface immediately on any R/I drift.
    for _ in range(N_FUZZ):
        bucket = rng.random()
        if bucket < 0.35:
            v = models.Model          # the F2P-discriminating input
        elif bucket < 0.45:
            v = type(None)
        else:
            v = rng.choice(all_types)
        check(v)
        if len(disagreements) >= 5:
            break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for v, sh, orc in disagreements:
            print("  type=%r shadow=%r oracle=%r" % (v, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of renderTypeRef agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
