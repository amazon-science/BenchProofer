#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-12209.

Executes the REAL unchanged UPDATE primitive — Django's
``django.db.models.base.Model._do_update`` (invoked from the single-table save
routine ``Model._save_table`` along the ``if pk_set and not force_insert:``
path) — and asserts that every observation matches the ``update_matched_row``
axiom in model.py.

The single axiom (A-consumed):

  update_matched_row() -> bool

  i.e. the real ``_do_update`` returns True iff it matched and updated a stored
  row for the instance's identifier (True for a present row, False for absent).

This is run inside the official SWE-bench container for the instance, where
Django is importable and a sqlite test database is available. It configures an
in-memory sqlite database and a minimal dependency-free model whose primary key
carries a generating default (``uuid.uuid4``) — the structural twin of the
test's ``UUIDDefaultData`` — then drives the real primitive. Exit 0 iff every
obligation holds.
"""
import os
import sys
import uuid


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
    except Exception as exc:  # setup failure must FAIL, never silently pass
        print("G-AX FAIL: Django could not be configured in this environment: %r"
              % (exc,))
        return 1

    from django.db import connection, models

    # A minimal model whose primary key carries a generating default — the
    # structural twin of the test's ``UUIDDefaultData`` and exactly the case the
    # changed short-cut guard targets (adding + pk.default is not NOT_PROVIDED).
    class UUIDDefault(models.Model):
        data = models.UUIDField(primary_key=True, default=uuid.uuid4)

        class Meta:
            # Register under an already-installed, importable app label so
            # django.setup() never raises ModuleNotFoundError. (A non-importable
            # label would abort setup; the guard above now FAILs rather than
            # silently SKIP-passing, but we avoid the abort entirely here.)
            app_label = "contenttypes"

    with connection.schema_editor() as editor:
        editor.create_model(UUIDDefault)

    observations = 0

    # ---- (a) direct _do_update probe: present vs absent identifier ----------
    # The axiom: _do_update returns True iff a stored row matched the pk.
    for _ in range(50):
        obj = UUIDDefault.objects.create()        # INSERT a row (pk present)
        stored_pk = obj.pk
        assert stored_pk is not None

        base_qs = UUIDDefault._base_manager.using("default")

        # A live row: _do_update must report a match (True). No non-pk fields,
        # so this exercises the ``if not values:`` branch -> filtered.exists().
        matched = obj._do_update(base_qs, "default", stored_pk, [], None, False)
        assert matched is True, (
            "_do_update on a present identifier returned %r, expected True"
            % (matched,))
        observations += 1

        # Absent identifier: delete the row, then _do_update must report no
        # match (False).
        UUIDDefault.objects.filter(pk=stored_pk).delete()
        unmatched = obj._do_update(base_qs, "default", stored_pk, [], None, False)
        assert unmatched is False, (
            "_do_update on an absent identifier returned %r, expected False"
            % (unmatched,))
        observations += 1

    # Sanity: the pk field genuinely carries a generating default distinct from
    # the NOT_PROVIDED sentinel (the unchanged operands of the guard).
    from django.db.models.fields import NOT_PROVIDED
    assert UUIDDefault._meta.pk.default is not NOT_PROVIDED
    assert UUIDDefault._meta.pk.default

    print("G-AX OK: update_matched_row axiom sound against the real "
          "Model._do_update over %d observations (True for a present row, "
          "False for absent)."
          % (observations,))
    return 0


if __name__ == "__main__":
    sys.exit(main())
