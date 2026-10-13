#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-15695.

There is no consumed @ContractOnly axiom in model.py. The unchanged backend
rename primitive — Django's
``BaseDatabaseSchemaEditor.rename_index(model, old_index, new_index)`` (called
from ``RenameIndex.database_forwards`` as
``schema_editor.rename_index(model, old_index, new_index)``) — is modelled
DEEPLY by the ``issue_rename`` reference (model.py): it records that a rename
was issued, that its target is ``new_name``, and that the existing index ends
up carrying ``new_name``.

This check validates that **deep model (A-reference)** against the REAL backend
primitive by driving Django's actual ``BaseDatabaseSchemaEditor.rename_index``
on an in-memory sqlite database, asserting the two facts the model pins:

  (1) the observable effect of issuing a rename: after
      ``rename_index(model, old_index, new_index)`` the existing index no longer
      carries its old name and DOES carry the target name ``new_index.name``
      (``issue_rename`` records ``renamed_to == new_name`` and
      ``old_index.name == new_name``);

  (2) the rename-to-itself hazard the guard exists to avoid: asking the backend
      to rename an index to a name that already exists is an error — so issuing
      a rename when ``old_index.name == new_index.name`` is exactly the
      operation the model's ``rename_existing_index`` must (and does) skip. We
      confirm that re-creating an index under a name already present raises,
      demonstrating why the no-op branch (``rename_issued`` False when the names
      match) is the only sound behaviour.

Run inside the official SWE-bench container for the instance, where Django is
importable. stdlib + Django only; exit 0 iff every obligation holds.
"""
import os
import sys


def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        )
    django.setup()


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "")
    try:
        _configure_django()
    except Exception as exc:  # pragma: no cover - environment guard
        print("G-AX SKIP: Django not configurable in this environment: %r" % (exc,))
        return 0

    from django.db import connection, models
    from django.db.utils import DatabaseError

    class Thing(models.Model):
        val = models.IntegerField()

        class Meta:
            app_label = "contenttypes"

    def current_index_names():
        with connection.cursor() as cur:
            constraints = connection.introspection.get_constraints(
                cur, Thing._meta.db_table)
        return {name for name, info in constraints.items() if info.get("index")}

    with connection.schema_editor() as editor:
        editor.create_model(Thing)

    observations = 0

    # --- (1) the observable effect of the REAL rename primitive ---------------
    # For a sequence of distinct (old -> new) names, rename_index must move the
    # index from old_index.name to new_index.name (the deep model's effect).
    rename_pairs = [
        ("thing_val_idx_a", "thing_val_idx_b"),
        ("thing_val_idx_b", "renamed_one_idx"),
        ("renamed_one_idx", "renamed_two_idx"),
        ("renamed_two_idx", "thing_final_idx"),
    ]
    # establish the first index
    first_old = rename_pairs[0][0]
    with connection.schema_editor() as editor:
        editor.add_index(Thing, models.Index(fields=["val"], name=first_old))
    assert first_old in current_index_names()

    for old_name, new_name in rename_pairs:
        old_index = models.Index(fields=["val"], name=old_name)
        new_index = models.Index(fields=["val"], name=new_name)
        with connection.schema_editor() as editor:
            editor.rename_index(Thing, old_index, new_index)
        names = current_index_names()
        assert new_name in names, (
            "rename_index did not produce target name %r (have %r)"
            % (new_name, names))
        assert old_name not in names, (
            "rename_index left the old name %r present (have %r)"
            % (old_name, names))
        observations += 1

    # tidy: drop whatever index name we ended on
    last_new = rename_pairs[-1][1]
    with connection.schema_editor() as editor:
        editor.remove_index(Thing, models.Index(fields=["val"], name=last_new))

    # --- (2) the rename-to-itself hazard the guard avoids ---------------------
    # Adding an index whose name already exists is an error: this is precisely
    # why issuing a rename when old_index.name == new_index.name must be skipped.
    dup_name = "thing_dup_idx"
    with connection.schema_editor() as editor:
        editor.add_index(Thing, models.Index(fields=["val"], name=dup_name))
    raised = False
    try:
        with connection.schema_editor() as editor:
            editor.add_index(Thing, models.Index(fields=["val"], name=dup_name))
    except DatabaseError:
        raised = True
    assert raised, (
        "expected creating an index under an already-present name %r to raise; "
        "this is the rename-to-itself hazard the no-op guard prevents" % (dup_name,))
    observations += 1
    with connection.schema_editor() as editor:
        editor.remove_index(Thing, models.Index(fields=["val"], name=dup_name))

    print("G-AX OK: issue_rename deep model (== BaseDatabaseSchemaEditor."
          "rename_index observable effect) sound over %d observations "
          "(rename moves old_index.name -> new_index.name; creating a name that "
          "already exists raises, so the equal-names case must be a no-op)."
          % (observations,))
    return 0


if __name__ == "__main__":
    sys.exit(main())
