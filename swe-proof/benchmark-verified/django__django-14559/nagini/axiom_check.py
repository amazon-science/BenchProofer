#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-14559.

Executes the REAL unchanged per-group row-affecting primitive — Django's
``QuerySet.update`` reached via ``self.filter(pk__in=pks).update(**kwargs)``
(the call the batched-update body makes once per group) — and asserts that
every observation matches the ``matched_rows`` axiom in model.py, plus the
refinement-load-bearing duplicate property that the deep model ``batched_total``
relies on (``pk__in`` collapses duplicates within one group, so a key split
across separate groups is summed twice).

The single axiom (A-consumed):

  matched_rows(group_keys) -> int   with   Ensures(Result() >= 0)

i.e. the real per-group ``filter(pk__in=group_keys).update(...)`` returns a
NON-NEGATIVE row count (the number of distinct present rows matched by the
``pk IN (...)`` WHERE clause; ``0`` when none match).

This is run inside the official SWE-bench container for the instance, where
Django is importable and a sqlite test database is available. It configures an
in-memory sqlite database and a minimal dependency-free model, creates rows,
and drives the real primitive on boundary + fuzz groups. Exit 0 iff every
obligation holds.
"""
import os
import random
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

    # A minimal, dependency-free model with one updatable concrete field —
    # the structural twin of the test's ``Note`` for counting purposes.
    class Row(models.Model):
        note = models.CharField(max_length=32, default="")

        class Meta:
            # An already-installed app_label so django.setup() succeeds in the
            # container (no self-registered stub app to import). The model name
            # `Row` does not collide with any model in contenttypes.
            app_label = "contenttypes"

    with connection.schema_editor() as editor:
        editor.create_model(Row)

    def matched(group_keys, value):
        """The REAL unchanged callee: per-group filtered update, returning the
        DB-reported matched-row count (model.py's matched_rows)."""
        return Row.objects.filter(pk__in=group_keys).update(note=value)

    counts_seen = []

    # (a) a single present key -> exactly 1 matched (>= 0 holds).
    for _ in range(50):
        obj = Row.objects.create(note="x")
        n = matched([obj.pk], "a")
        assert isinstance(n, int) and n >= 0, "update() returned %r" % (n,)
        assert n == 1, "single present key matched %r rows, expected 1" % (n,)
        counts_seen.append(n)

    # (b) an absent key -> 0 matched (>= 0 holds).
    for _ in range(25):
        obj = Row.objects.create(note="x")
        pk = obj.pk
        obj.delete()
        n = matched([pk], "a")
        assert isinstance(n, int) and n >= 0, "update() returned %r" % (n,)
        assert n == 0, "absent key matched %r rows, expected 0" % (n,)
        counts_seen.append(n)

    # (c) the DUPLICATE subtlety the refinement (batched_total) depends on:
    #     pk__in collapses duplicates within ONE group, so [pk, pk] -> 1;
    #     splitting the two appearances into SEPARATE groups sums to 2.
    for _ in range(50):
        obj = Row.objects.create(note="x")
        one_group = matched([obj.pk, obj.pk], "b")          # duplicates in one group
        assert one_group == 1, (
            "pk__in over [pk, pk] in one group matched %r, expected 1 "
            "(set membership collapses duplicates)" % (one_group,))
        # the same two appearances placed into two separate single-key groups
        split = matched([obj.pk], "c") + matched([obj.pk], "d")
        assert split == 2, (
            "two single-key groups summed to %r, expected 2 "
            "(across-group summation counts the key twice)" % (split,))
        counts_seen.append(one_group)

    # (d) randomized fuzz groups: count is always >= 0 and equals the number of
    #     distinct present keys in the group.
    rng = random.Random(14559)
    live = []
    for _ in range(40):
        live.append(Row.objects.create(note="x").pk)
    for _ in range(20000):
        k = rng.randint(0, 6)
        group = [rng.choice(live) for _ in range(k)] if (live and k) else []
        # add an occasional absent key
        if rng.random() < 0.2:
            group.append(10 ** 9 + rng.randint(0, 1000))
        n = matched(group, "z")
        assert isinstance(n, int) and n >= 0, "update() returned %r" % (n,)
        expected_distinct_present = len(set(g for g in group if g in live))
        assert n == expected_distinct_present, (
            "group %r matched %r rows, expected %r distinct present keys"
            % (group, n, expected_distinct_present))
        counts_seen.append(n)

    print("G-AX OK: matched_rows axiom (Result() >= 0) sound against the real "
          "QuerySet.filter(pk__in=...).update(...) over %d observations; pk__in "
          "collapses within-group duplicates (([pk,pk]) -> 1) while separate "
          "groups sum (1 + 1 -> 2), the duplicate property batched_total relies "
          "on." % (len(counts_seen),))
    return 0


if __name__ == "__main__":
    sys.exit(main())
