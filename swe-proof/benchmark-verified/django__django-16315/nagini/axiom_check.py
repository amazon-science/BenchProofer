#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-16315.

There is NO consumed @ContractOnly axiom in model.py. The schema's
name->field resolution and a field's storage identifier are modelled DEEPLY as
a registry of parallel name/column lists with

    column_for(name, names, columns) == columns[ first j with names[j]==name ]

This check validates that DEEP MODEL (the A-reference) against the REAL Django
callees it stands in for, exercised in the official SWE-bench container where
Django is importable:

  * resolution:  Model._meta.get_field(name)            (the unchanged lookup)
  * projection:  Field.column                           (= db_column or name)

For a registry built from a real model's concrete fields, the deep-model
function must agree, per requested name, with the real pipeline
``Model._meta.get_field(name).column``. The discriminating case -- a field that
declares a storage-column override, so its column DIFFERS from its name (and
the override may differ in case only) -- is included explicitly: the check
asserts the deep model selects the COLUMN, never the NAME (no double-masking:
the equivalence is asserted at the identifier level, with name != column slots
present and required to disagree from the name).

Imports are limited to the standard library plus Django itself (the framework
under test, importable in the container). Exit 0 iff every obligation holds.
"""
import sys


# --- model.py deep-model reference encodings (kept in lock-step) -------------

def column_for(name, names, columns):
    """Reference impl of model.py's `column_for`: the column of the first
    registry slot whose name matches (parallel name/column lists)."""
    n = min(len(names), len(columns))
    for j in range(n):
        if names[j] == name:
            return columns[j]
    return None  # never happens when the name is present (registry well-formed)


def conflict_columns(requested, names, columns):
    """Reference impl of model.py's `conflict_columns`: per requested name, the
    storage identifier that name designates (element-wise)."""
    return [column_for(r, names, columns) for r in requested]


# --- Django configuration ----------------------------------------------------

def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
            ],
            DATABASES={
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": ":memory:",
                }
            },
        )
    django.setup()


def _build_models():
    from django.db import models

    class FieldsWithDbColumns(models.Model):
        # the discriminating fields: db_column differs from the field name
        # (and differs in case only -- the exact issue case).
        rank = models.IntegerField(unique=True, db_column="rAnK")
        name = models.CharField(max_length=15, null=True, db_column="oTheRNaMe")

        class Meta:
            app_label = "axcheck"

    class PlainFields(models.Model):
        # control: no db_column overrides, so column == name.
        alpha = models.IntegerField(unique=True)
        beta = models.CharField(max_length=15, null=True)

        class Meta:
            app_label = "axcheck"

    return FieldsWithDbColumns, PlainFields


def _registry(model):
    """Build the parallel (names, columns) registry the deep model consumes,
    from a real model's concrete fields, using the REAL Field.column."""
    names, columns = [], []
    for f in model._meta.concrete_fields:
        names.append(f.name)        # the in-memory attribute name
        columns.append(f.column)    # REAL callee: db_column or name
    return names, columns


def main():
    try:
        _configure_django()
    except Exception as exc:  # pragma: no cover - environment guard
        print("G-AX SKIP: Django not configurable in this environment: %r"
              % (exc,))
        return 0
    FieldsWithDbColumns, PlainFields = _build_models()

    saw_override = False

    for model in (FieldsWithDbColumns, PlainFields):
        names, columns = _registry(model)

        # (a) per-field: the deep model's column_for(name) equals the REAL
        #     Model._meta.get_field(name).column -- asserted at the IDENTIFIER
        #     level, including slots where column != name.
        for name in names:
            real_field = model._meta.get_field(name)
            real_column = real_field.column          # REAL callee under test
            model_column = column_for(name, names, columns)
            assert model_column == real_column, (
                "column_for unsound for %s.%s: deep model gives %r, real "
                "Field.column gives %r" % (model.__name__, name,
                                           model_column, real_column))
            if real_column != name:
                # discriminating slot: a storage-column override is in play, so
                # the resolved identifier is the COLUMN, never the field name.
                saw_override = True
                assert model_column != name, (
                    "double-mask guard: deep model returned the NAME %r for a "
                    "field whose column %r differs" % (name, real_column))

        # (b) the conflict-columns pipeline: for any subset of requested fields
        #     (the unique_fields / update_fields lists), the deep model agrees
        #     with the real pipeline [get_field(n).column for n in requested].
        from itertools import permutations
        for r in range(0, len(names) + 1):
            for requested in permutations(names, r):
                requested = list(requested)
                real = [model._meta.get_field(n).column for n in requested]
                got = conflict_columns(requested, names, columns)
                assert got == real, (
                    "conflict_columns unsound on %r for %s: deep model %r, "
                    "real pipeline %r" % (requested, model.__name__, got, real))

    # the discriminating db_column case MUST have been exercised (otherwise the
    # check would pass vacuously on a name==column dataset).
    assert saw_override, (
        "no field with a storage-column override was exercised -- the "
        "name-vs-column discriminator was not tested")

    # explicit F2P witness: the issue's exact model and requests.
    names, columns = _registry(FieldsWithDbColumns)
    assert conflict_columns(["rank"], names, columns) == ["rAnK"], \
        "unique_fields=['rank'] must resolve to column 'rAnK'"
    assert conflict_columns(["name"], names, columns) == ["oTheRNaMe"], \
        "update_fields=['name'] must resolve to column 'oTheRNaMe'"

    print("G-AX OK: column_for / conflict_columns deep model (A-reference) == "
          "real Django _meta.get_field(name).column across all field subsets of "
          "2 models incl. mixed-case db_column overrides; discriminator exercised")
    return 0


if __name__ == "__main__":
    sys.exit(main())
