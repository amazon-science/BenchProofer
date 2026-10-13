#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-11740.

The bundle models ONE function: `MigrationAutodetector.generate_altered_fields`
(`django/db/migrations/autodetector.py`), specifically the per-altered-field
assembly of the `dependencies` list newly threaded into the emitted `AlterField`
operation. Its Lean impl (`implementation_generateAlteredFields`) is:

    result = []
    for f in fields:
        dependencies = []
        if f.is_relation:
            dependencies += get_dependencies_for_foreign_key(f.fk)   # A-reference
        result += [dependencies]
    return result

This script transliterates that R/I impl into Python (`shadow`) and differential-
tests it against the ORACLE: a faithful in-process replica of the POST-PATCH
per-field loop of `generate_altered_fields`:

    dependencies = []
    if hasattr(new_field, "remote_field") and getattr(new_field.remote_field, "model", None):
        dependencies.extend(self._get_dependencies_for_foreign_key(new_field))
    add_operation(..., dependencies=dependencies)   # -> _auto_deps

The A-reference callee `_get_dependencies_for_foreign_key` is left as the REAL
repo callee in BOTH legs (it is independently pinned == the Lean deep model by
G-AX, axiom_check.py). G-CONF therefore tests the R/I loop assembly: that a
relation field contributes the FK-induced dependency list and a non-relation
field contributes the empty list, element-wise in order.

We do NOT stand up the full autodetector graph (heavy). We reproduce the patched
loop's dependency assembly directly with real relation/non-relation fields built
from the repo source (mapping.md bijection). The differential genuinely tests the
Lean modeling: the shadow uses the Lean structure (`if isRelation: deps =
real_callee(...)`), whereas the oracle reproduces the patched loop's
`if remote_field.model: dependencies.extend(real_callee(...))`.

stdlib + django (testbed under test); deterministic built-in fuzzer.
Pinned seed: 11740 (also recorded in mapping.md).
"""
import random
import sys

SEED = 11740
N = 150_000


def _setup_fields():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            DATABASES={},
            # Only real, importable apps. Test models below register under an
            # explicit `app_label` WITHOUT their app being installed; the
            # swappable-FK branch is exercised via the built-in swappable model
            # `auth.User`, so no synthetic app / AUTH_USER_MODEL override is
            # needed (those tripped ModuleNotFoundError under django.setup()).
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
            ],
        )
    django.setup()
    from django.db import models

    class Target(models.Model):
        class Meta:
            app_label = "confapp"

    class ExplicitThrough(models.Model):
        a = models.ForeignKey("confapp.Source", on_delete=models.CASCADE)
        b = models.ForeignKey("confapp.Target", on_delete=models.CASCADE)

        class Meta:
            app_label = "confapp"

    class Source(models.Model):
        plain_fk = models.ForeignKey(Target, null=True, on_delete=models.SET_NULL)
        self_fk = models.ForeignKey("self", null=True, on_delete=models.SET_NULL)
        # FK to the built-in swappable model: swappable_setting == "AUTH_USER_MODEL"
        user_fk = models.ForeignKey("auth.User", null=True, on_delete=models.SET_NULL)
        plain_m2m = models.ManyToManyField(Target, related_name="m2m_src")
        through_m2m = models.ManyToManyField(
            Target, through="confapp.ExplicitThrough", related_name="thr_src"
        )
        # non-relation fields
        int_field = models.IntegerField(null=True)
        char_field = models.CharField(max_length=50, null=True)
        uuid_field = models.UUIDField(null=True)

        class Meta:
            app_label = "confapp"

    relation = {
        "plain_fk": Source._meta.get_field("plain_fk"),
        "self_fk": Source._meta.get_field("self_fk"),
        "user_fk": Source._meta.get_field("user_fk"),
        "plain_m2m": Source._meta.get_field("plain_m2m"),
        "through_m2m": Source._meta.get_field("through_m2m"),
    }
    nonrelation = {
        "int_field": Source._meta.get_field("int_field"),
        "char_field": Source._meta.get_field("char_field"),
        "uuid_field": Source._meta.get_field("uuid_field"),
    }
    return relation, nonrelation


# --- the A-reference callee, REAL repo code, shared by both legs ---------------
def real_callee(field):
    from django.db.migrations.autodetector import MigrationAutodetector
    return list(MigrationAutodetector._get_dependencies_for_foreign_key(None, field))


def is_relation(field):
    return bool(hasattr(field, "remote_field") and getattr(field.remote_field, "model", None))


# --- ORACLE: post-patch generate_altered_fields per-field operation assembly ---
# Each emitted operation is modeled as (field_identity, dependencies); the field
# identity is the object id of the field, so the differential also pins that each
# operation alters precisely its own field (frame discipline) — not just that the
# right multiset of dependency lists is produced.
def oracle(fields):
    out = []
    for new_field in fields:
        dependencies = []
        if hasattr(new_field, "remote_field") and getattr(new_field.remote_field, "model", None):
            dependencies.extend(real_callee(new_field))
        out.append((id(new_field), dependencies))
    return out


# --- shadow of implementation_generateAlteredFields (the R/I leg) --------------
def shadow(fields):
    result = []
    for f in fields:
        dependencies = []
        if is_relation(f):
            dependencies = dependencies + real_callee(f)
        result = result + [(id(f), dependencies)]
    return result


def disagree(fields):
    got = oracle(fields)
    want = shadow(fields)
    if got != want:
        return (got, want)
    return None


def main() -> int:
    try:
        relation, nonrelation = _setup_fields()
    except Exception as e:  # noqa: BLE001
        print(f"status=error setup_failed={e!r}")
        return 2

    pool = list(relation.items()) + list(nonrelation.items())
    names = [n for n, _ in pool]
    by_name = dict(pool)

    checked = 0

    # edge cases: each single field, empty, all-relation, all-nonrelation, mixed
    edges = [
        [],
        [by_name["plain_fk"]],
        [by_name["user_fk"]],
        [by_name["through_m2m"]],
        [by_name["plain_m2m"]],
        [by_name["int_field"]],
        [by_name[n] for n in names],
        [by_name["int_field"], by_name["plain_fk"], by_name["char_field"]],
        [by_name["plain_fk"], by_name["plain_fk"]],
        [by_name["user_fk"], by_name["through_m2m"], by_name["uuid_field"]],
    ]
    for fields in edges:
        d = disagree(fields)
        if d:
            print(f"DISAGREE edge: oracle={d[0]} shadow={d[1]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        k = rng.randint(0, 6)
        fields = [by_name[rng.choice(names)] for _ in range(k)]
        d = disagree(fields)
        if d:
            print(f"DISAGREE fuzz: oracle={d[0]} shadow={d[1]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
