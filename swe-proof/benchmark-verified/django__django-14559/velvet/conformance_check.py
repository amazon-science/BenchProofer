#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-14559 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged op of Solution.lean's impl region transliterated to
              Python over the *real* repo type: `rowSum counts` becomes
              `sum(counts)`, where `counts` is the sequence of per-batch
              `QuerySet.update()` return values produced by the REAL callee while
              the patched `bulk_update` runs (mapping.md bijection
              `list[int] ↔ List Nat`, `int ↔ Nat`). The A-reference callee
              `update()` is NOT replaced by a model here — G-CONF isolates the
              R/I (summation) leg and leaves the callee real (its soundness is
              G-AX's job).
  * ORACLE  — `patch.diff`'s behaviour: the patched `QuerySet.bulk_update`'s
              own returned integer (the real correctness oracle, G-RESOLVE).

They must agree on every Requires-satisfying input. Exit 0 iff zero
disagreements; any disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (patch.diff applied at base_commit), in-memory SQLite Django,
stdlib + django only. The fuzz seed is pinned (mapping.md §4) for a deterministic
verdict.
"""
import random
import sys

SEED = 14559
N_FUZZ = 100_000


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

    rng = random.Random(SEED)

    # A captured patched-update() that records each per-batch return so the
    # SHADOW can sum the SAME counts the ORACLE produced. This isolates the
    # summation (R/I) leg: shadow = sum(per-batch counts); oracle = bulk_update's
    # own returned total. Any divergence is an R/I (fold) infidelity, not a
    # callee discrepancy.
    captured = []
    orig_update = models.QuerySet.update

    def recording_update(self, **kwargs):
        n = orig_update(self, **kwargs)
        captured.append(n)
        return n

    def shadow_and_oracle(objs, fields, batch_size):
        captured.clear()
        oracle = Row.objects.bulk_update(objs, fields, batch_size=batch_size)
        shadow = sum(captured)  # rowSum counts, transliterated (mapping.md A2)
        return shadow, oracle

    models.QuerySet.update = recording_update
    try:
        rows = [Row.objects.create(val=0) for _ in range(40)]

        def gen_cases():
            # boundary cases first (plan §4.1 step 4)
            yield ([], ["val"], None)                       # empty objs -> 0
            yield ([rows[0]], ["val"], None)                # singleton
            yield ([rows[0], rows[0]], ["val"], None)       # dup in one batch -> 1
            yield ([rows[0], rows[0]], ["val"], 1)          # dup across batches -> 2
            yield (rows[:], ["val"], None)                  # all rows, default batch
            yield (rows[:], ["val"], 1)                     # one row per batch
            yield (rows[:], ["val"], 7)                     # uneven batches
            yield (rows[:10] + rows[:10], ["val"], 3)       # duplicates, small batch
            for _ in range(N_FUZZ):
                k = rng.randint(0, 30)
                objs = [rng.choice(rows) for _ in range(k)]  # may repeat
                bs = rng.choice([None, 1, 2, 3, 5, 10, 50])
                yield (objs, ["val"], bs)

        disagreements = []
        count = 0
        for objs, fields, bs in gen_cases():
            count += 1
            shadow, oracle = shadow_and_oracle(objs, fields, bs)
            if shadow != oracle:
                disagreements.append((len(objs), bs, shadow, oracle))
                if len(disagreements) >= 5:
                    break
    finally:
        models.QuerySet.update = orig_update

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for n_objs, bs, sh, orc in disagreements:
            print("  n_objs=%d batch_size=%r shadow=%r oracle=%r"
                  % (n_objs, bs, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of totalBatchCount (sum of per-batch counts) "
          "agrees with patch.diff bulk_update() return on %d inputs (seed=%d), "
          "0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
