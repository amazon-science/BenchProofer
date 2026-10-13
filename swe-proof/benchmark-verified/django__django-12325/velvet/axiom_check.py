#!/usr/bin/env python3
r"""G-AX executable soundness check for django__django-12325.

This bundle has **NO consumed axiom and NO deep-model reference** (refinement.md
§C, mapping.md §3): the changed behaviour is a pure data-flow over the scanned
`OneToOneField` list, modeled DIRECTLY by `selectRef`/`collectLinks`. G-AX
therefore validates the *structural layout facts the direct R-model depends on*,
by executing the REAL Django metaclass machinery in-container (UNPATCHED base
commit — the orchestrator runs G-AX without applying the gold patch).

The facts checked (each is part of the mapping.md §2 bijection that G-CONF then
exercises end-to-end):

  1. Flag reading is faithful: for a declared `OneToOneField`, the model's
     `Ref.isLink` is exactly `field.remote_field.parent_link` — `True` iff the
     field was declared `parent_link=True`, `False` otherwise. (Standalone field
     objects, no class attach, so this is independent of the pk-promotion path.)

  2. Per-ancestor keying is faithful and injective on ancestors: for the fields a
     child declares, `make_model_tuple(resolve_relation(child, f.remote_field
     .model))` (the dict key the loop writes under — modeled as `Ref.target`)
     is equal for two references iff they target the same ancestor, and distinct
     ancestors get distinct keys. So `Ref.target : Nat` (distinct ancestors ->
     distinct Nats) is a sound abstraction of the key.

  3. Scan order is declaration order: the `OneToOneField`s the loop scans
     (`base._meta.local_fields` filtered to `isinstance(field, OneToOneField)`)
     appear in declaration order, so `refs[i]` <-> the i-th declared field, and
     the left-to-right fold matches the loop's last-writer-wins semantics.

Imports only `django` (the module under change) + the standard library. Exit 0
iff every obligation holds.
"""
import sys


def _bootstrap_django():
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


def main():
    _bootstrap_django()
    from django.db import models
    from django.db.models.fields.related import OneToOneField, resolve_relation
    from django.db.models.utils import make_model_tuple
    from django.apps import apps

    class Place(models.Model):
        class Meta:
            app_label = "auth"

    class Town(models.Model):
        class Meta:
            app_label = "auth"

    # --- fact 1: flag reading is faithful (standalone fields, no attach) ------
    f_link = OneToOneField(Place, on_delete=models.CASCADE, parent_link=True)
    f_plain = OneToOneField(Place, on_delete=models.CASCADE)
    assert f_link.remote_field.parent_link is True, (
        "isLink unsound: parent_link=True field reads %r"
        % f_link.remote_field.parent_link)
    assert f_plain.remote_field.parent_link is False, (
        "isLink unsound: a plain OneToOneField reads parent_link=%r (expected "
        "False) — the model's `Ref.isLink = false` for non-link refs is wrong"
        % f_plain.remote_field.parent_link)

    # --- fact 3: scan order is declaration order ------------------------------
    # Build a child declaring two parent_link refs to Place plus one to Town, in
    # a fixed declaration order. (All parent_link=True so the UNPATCHED metaclass
    # does not raise — fact 3/2 are about layout, independent of the fix.)
    attrs = {
        "__module__": "ax_order",
        "Meta": type("Meta", (), {"app_label": "auth"}),
        "a": models.OneToOneField(Place, on_delete=models.CASCADE,
                                  parent_link=True, related_name="+"),
        "b": models.OneToOneField(Town, on_delete=models.CASCADE,
                                  parent_link=True, related_name="+"),
        "c": models.OneToOneField(Place, on_delete=models.CASCADE,
                                  parent_link=True, related_name="+"),
    }
    Child = type("AxChild", (Place, Town), attrs)
    try:
        scanned = [f for f in Child._meta.local_fields
                   if isinstance(f, OneToOneField)]
        names = [f.name for f in scanned]
        # 'a','b','c' must appear before the auto-synthesised ptr, in decl order
        decl = [n for n in names if n in ("a", "b", "c")]
        assert decl == ["a", "b", "c"], (
            "scan order not declaration order: got %r" % decl)

        # --- fact 2: per-ancestor keying faithful + injective on ancestors ----
        key = {}
        for f in scanned:
            if f.name in ("a", "b", "c"):
                related = resolve_relation(Child, f.remote_field.model)
                key[f.name] = make_model_tuple(related)
        # same ancestor (Place) -> same key
        assert key["a"] == key["c"], (
            "keying unsound: two refs to the SAME ancestor got distinct keys "
            "%r vs %r" % (key["a"], key["c"]))
        # distinct ancestors (Place vs Town) -> distinct keys
        assert key["a"] != key["b"], (
            "keying unsound: refs to DISTINCT ancestors collided on key %r"
            % (key["a"],))
        assert key["a"] == ("auth", "place") and key["b"] == ("auth", "town"), (
            "keying values unexpected: %r" % key)
    finally:
        apps.all_models["auth"].pop(Child._meta.model_name, None)

    print("G-AX OK: structural layout facts sound (no consumed axiom / "
          "deep-model ref): isLink == remote_field.parent_link (True for "
          "parent_link fields, False otherwise); per-ancestor keying faithful & "
          "injective on ancestors; scan order == declaration order.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
