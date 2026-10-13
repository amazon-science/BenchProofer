#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-14559.

The modeled `bulk_update` change consumes exactly ONE property of the unchanged
callee `QuerySet.update()`: each per-batch call returns a NON-NEGATIVE integer
equal to the number of distinct, existing primary keys it matched. That count is
carried into the Lean model as a `Nat` element of `counts` (the A-reference,
mapping.md §3.1) — there is no consumed axiom, so this gate validates the
deep-model reference: the real `QuerySet.update()` truly returns `>= 0`, and
equals the distinct-existing-pk count, on boundary + fuzzed `pk__in` sets.

Runs in-container against an in-memory SQLite Django (the repo at base_commit /
the patched repo — `update()` is unchanged by the patch either way). stdlib +
django only. Exit 0 iff every observation satisfies the reference.
"""
import os
import random
import sys


def _configure():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
            DEFAULT_AUTO_FIELD="django.db.models.AutoField",
        )
    django.setup()


def main():
    _configure()

    from django.db import connection, models

    # A throwaway test model under a real installed app's label ("auth"), so the
    # app has a genuine filesystem location (Django 4.0 rejects synthetic modules
    # with an empty __path__).
    class Row(models.Model):
        val = models.IntegerField(default=0)

        class Meta:
            app_label = "auth"

    with connection.schema_editor() as se:
        se.create_model(Row)

    rng = random.Random(14559)

    # Seed N rows; remember which pks exist.
    existing = []
    for _ in range(60):
        existing.append(Row.objects.create(val=0).pk)
    max_pk = max(existing)
    missing = [max_pk + 1, max_pk + 2, max_pk + 1000]  # pks that do NOT exist

    def distinct_existing(pks):
        return len({p for p in pks if p in set(existing)})

    def check(pks):
        """Run the REAL QuerySet.update() with pk__in=pks; assert its return is a
        non-negative int equal to the distinct-existing-pk count (the property the
        bulk_update change relies on, mapping.md §3.1)."""
        observed = Row.objects.filter(pk__in=pks).update(val=models.F("val") + 1)
        assert isinstance(observed, int), \
            "update() returned non-int %r for pks=%r" % (observed, pks)
        assert observed >= 0, \
            "update() returned negative %r for pks=%r" % (observed, pks)
        expected = distinct_existing(pks)
        assert observed == expected, \
            "update() matched %r rows, expected distinct-existing %r for pks=%r" \
            % (observed, expected, pks)
        return observed

    # --- boundary cases -----------------------------------------------------
    boundary = [
        [],                              # empty filter -> 0
        [existing[0]],                   # singleton
        [existing[0], existing[0]],      # duplicate pk in one batch -> matched once
        existing[:],                     # all rows
        missing[:],                      # only missing pks -> 0
        [existing[0]] + missing,         # mix of existing + missing
        existing[:5] + existing[:5],     # duplicates over an existing slice
    ]
    for pks in boundary:
        check(pks)

    # --- randomized fuzz ----------------------------------------------------
    pool = existing + missing
    for _ in range(20000):
        k = rng.randint(0, 30)
        pks = [rng.choice(pool) for _ in range(k)]
        check(pks)

    print("G-AX OK: real QuerySet.update() returns a non-negative int equal to "
          "the distinct-existing-pk count on %d boundary + 20000 fuzz pk sets "
          "(A-reference for bulk_update's per-batch counts)." % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
