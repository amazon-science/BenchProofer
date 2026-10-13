#!/usr/bin/env python3
"""G-AX for django__django-11740 — validate the deep model
`getDependenciesForForeignKey` against the REAL repo callee
`MigrationAutodetector._get_dependencies_for_foreign_key`, in-container at
base_commit.

The bundle models ONE changed behavior (`generate_altered_fields`): an altered
field that is a relation now contributes FK-induced ordering dependencies to its
`AlterField` operation. The dependency computation itself is the UNCHANGED callee
`_get_dependencies_for_foreign_key`, modeled DEEPLY as `getDependenciesForForeignKey`
(refinement.md, A-reference).

This check builds real relation fields (ForeignKey / ManyToManyField, plain and
swappable, with and without an explicit non-auto-created `through`) from the repo
source, drives the ACTUAL callee, and asserts every observation matches the Lean
deep model:

  getDependenciesForForeignKey(fk_info(field)) == _get_dependencies_for_foreign_key(field)

where the comparison is on the 4-tuple list
`[(app_label, object_name, field_name, create), ...]`.

stdlib + django (the testbed under test). Exit 0 iff sound. Pinned seed: 11740.
"""
import random
import sys

SEED = 11740
N = 4000


def _setup():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            DATABASES={},
            # Only real, importable apps. Test models below register under an
            # explicit `app_label` WITHOUT their app being installed (Django
            # allows this); the swappable-FK branch is exercised via the
            # built-in swappable model `auth.User` (swappable_setting =
            # "AUTH_USER_MODEL"), so no synthetic app/AUTH_USER_MODEL override
            # is needed — those tripped ModuleNotFoundError under django.setup().
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
            ],
        )
    django.setup()


# ---- Lean deep model (mirror Solution.lean `getDependenciesForForeignKey`) ----
def model_get_dependencies(fk):
    """fk is a dict {swappableSetting, remoteAppLabel, remoteObjectName, through}
    where through is None or (app, obj, auto_created)."""
    if fk["swappableSetting"] is not None:
        base = ("__setting__", fk["swappableSetting"], None, True)
    else:
        base = (fk["remoteAppLabel"], fk["remoteObjectName"], None, True)
    deps = [base]
    through = fk["through"]
    if through is not None:
        t_app, t_obj, auto_created = through
        if not auto_created:
            deps.append((t_app, t_obj, None, True))
    return deps


# ---- read FKInfo off a real field, per mapping.md bijection -------------------
def fk_info(field):
    swappable_setting = getattr(field, "swappable_setting", None)
    rf = field.remote_field
    remote_app = rf.model._meta.app_label
    remote_obj = rf.model._meta.object_name
    through = None
    th = getattr(rf, "through", None)
    if th is not None:
        through = (th._meta.app_label, th._meta.object_name, th._meta.auto_created)
    return {
        "swappableSetting": swappable_setting,
        "remoteAppLabel": remote_app,
        "remoteObjectName": remote_obj,
        "through": through,
    }


def real_get_dependencies(field):
    from django.db.migrations.autodetector import MigrationAutodetector
    # the method reads only `field` (no other self use); call it unbound.
    return list(MigrationAutodetector._get_dependencies_for_foreign_key(None, field))


def build_fields():
    """Construct real relation fields bound to models in `axapp`."""
    from django.db import models

    class Target(models.Model):
        class Meta:
            app_label = "axapp"

    class ExplicitThrough(models.Model):
        # an explicit (non-auto-created) through model
        a = models.ForeignKey("axapp.Source", on_delete=models.CASCADE)
        b = models.ForeignKey("axapp.Target", on_delete=models.CASCADE)

        class Meta:
            app_label = "axapp"

    class Source(models.Model):
        plain_fk = models.ForeignKey(Target, null=True, on_delete=models.SET_NULL)
        self_fk = models.ForeignKey("self", null=True, on_delete=models.SET_NULL)
        # FK to the built-in swappable model: swappable_setting == "AUTH_USER_MODEL"
        user_fk = models.ForeignKey(
            "auth.User", null=True, on_delete=models.SET_NULL
        )
        plain_m2m = models.ManyToManyField(Target, related_name="m2m_src")
        through_m2m = models.ManyToManyField(
            Target, through="axapp.ExplicitThrough", related_name="thr_src"
        )

        class Meta:
            app_label = "axapp"

    fields = {
        "plain_fk": Source._meta.get_field("plain_fk"),
        "self_fk": Source._meta.get_field("self_fk"),
        "user_fk": Source._meta.get_field("user_fk"),       # swappable (AUTH_USER_MODEL)
        "plain_m2m": Source._meta.get_field("plain_m2m"),   # auto-created through
        "through_m2m": Source._meta.get_field("through_m2m"),  # explicit through
    }
    return fields


def main() -> int:
    try:
        _setup()
        fields = build_fields()
    except Exception as e:  # noqa: BLE001
        print(f"status=error setup_failed={e!r}")
        return 2

    checked = 0
    names = list(fields.keys())
    # deterministic repeated sampling of the constructed field set (boundary +
    # fuzz over which fields are inspected; the field set itself spans the
    # branches: plain FK, self FK, swappable FK, auto-created through M2M,
    # explicit non-auto-created through M2M).
    rng = random.Random(SEED)
    order = names + [rng.choice(names) for _ in range(N)]

    for name in order:
        field = fields[name]
        try:
            real = real_get_dependencies(field)
        except Exception as e:  # noqa: BLE001
            print(f"status=fail real callee raised on {name}: {e!r}")
            return 1
        model = model_get_dependencies(fk_info(field))
        if real != model:
            print(f"status=fail mismatch on {name}: real={real} model={model}")
            return 1
        checked += 1

    print(f"checked={checked} mismatches=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
