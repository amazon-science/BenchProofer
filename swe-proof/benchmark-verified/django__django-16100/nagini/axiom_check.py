#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-16100.

Executes the REAL callee the gold patch introduces — `django.db.transaction.
atomic(using=...)` as a context manager wrapping a sequence of row writes —
against an in-memory SQLite database, and asserts that the committed database
state matches the deep model encoded in model.py.

The kind-A check (A-reference; there is NO consumed axiom in this bundle):

  the deep model `committed_value` / `any_fails` (model.py pure region) ==
  the real `transaction.atomic` commit/rollback verdict:

    * block completes with no raise  -> COMMIT  -> every row holds its
      replacement value                            (any_fails == False)
    * any write inside the block raises -> ROLLBACK -> every row reverts to its
      original value, INCLUDING rows written before the failing one
                                                     (any_fails == True)

We realize a batch of row writes inside one `atomic` block and inject a failure
at each possible position (and at no position), then read the committed rows
back and compare to the deep model. This is exactly the all-or-nothing property
the patch adds and the pre-patch (per-write autocommit) violates.

Imports only Django's own `django.db` (the module the gold patch calls),
configured against an in-memory SQLite database; nothing instance-specific.
Exit 0 iff every observation matches the deep model.
"""
import random
import sys

import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        INSTALLED_APPS=[],
        DATABASES={
            "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}
        },
        DEFAULT_AUTO_FIELD="django.db.models.AutoField",
    )

django.setup()

from django.db import connection, models, transaction  # noqa: E402


class Row(models.Model):
    val = models.IntegerField()

    class Meta:
        app_label = "axcheck_app"


# --- model.py deep-model reference encodings (kept in lock-step) -------------

def any_fails(fails, i):
    """Reference of model.py's `any_fails`: a failing edit anywhere in tail i.."""
    return any(f == 1 for f in fails[i:])


def committed_value(original, newval, batch_fails):
    """Reference of model.py's `committed_value`: replacement on success, the
    original value on any failure (rollback)."""
    return original if batch_fails else newval


def deep_model(original, newvals, fails):
    """The committed store predicted by the deep model: the batch-global verdict
    applied uniformly to every row."""
    bf = any_fails(fails, 0)
    return [committed_value(original[k], newvals[k], bf) for k in range(len(original))]


# --- the real callee under check --------------------------------------------

class _InjectedFailure(Exception):
    pass


def real_atomic_commit(original, newvals, fails):
    """Apply the batch inside a REAL `transaction.atomic` block, writing each
    row's replacement value one at a time (mirroring the per-form save loop),
    raising when an edit's failure signal is set. Return the committed values
    read back from the database after the block (rolled back on any raise)."""
    # Seed the rows with their original values (committed before the batch).
    Row.objects.all().delete()
    for k, ov in enumerate(original):
        Row.objects.create(id=k + 1, val=ov)

    raised = False
    try:
        with transaction.atomic(using="default"):
            for k in range(len(original)):
                # Apply (stage) this row's replacement, exactly as the save loop
                # would persist the edited value.
                Row.objects.filter(id=k + 1).update(val=newvals[k])
                if fails[k] == 1:
                    # This edit's processing raises (e.g. log_change DatabaseError
                    # in the F2P test): the exception propagates out of the block.
                    raise _InjectedFailure()
    except _InjectedFailure:
        raised = True

    committed = [Row.objects.get(id=k + 1).val for k in range(len(original))]
    return committed, raised


# --- the check ---------------------------------------------------------------

def check_batch(original, newvals, fails):
    observed, raised = real_atomic_commit(original, newvals, fails)
    expected = deep_model(original, newvals, fails)
    assert observed == expected, (
        "deep model unsound on original=%r newvals=%r fails=%r: real atomic "
        "committed %r, deep model predicts %r" % (
            original, newvals, fails, observed, expected))
    # cross-check the verdict bit too
    assert raised == any_fails(fails, 0), (
        "any_fails mismatch on fails=%r: real atomic raised=%r, model=%r" % (
            fails, raised, any_fails(fails, 0)))


def main():
    with connection.schema_editor() as se:
        se.create_model(Row)

    checks = 0

    # --- boundary cases: failure injected at every position (and none) -------
    for n in range(0, 6):
        original = [10 + k for k in range(n)]
        newvals = [100 + k for k in range(n)]
        # no failure -> full commit
        check_batch(original, newvals, [0] * n)
        checks += 1
        # failure at each single position -> full rollback (no committed prefix)
        for pos in range(n):
            fails = [0] * n
            fails[pos] = 1
            check_batch(original, newvals, fails)
            checks += 1
        # all fail
        if n:
            check_batch(original, newvals, [1] * n)
            checks += 1

    # explicit witness for the F2P test's two scenarios (n=2):
    #  (1) first form fails; (2) first succeeds, second fails. Both must revert.
    check_batch([4, 2], [9, 5], [1, 0]); checks += 1
    check_batch([4, 2], [9, 5], [0, 1]); checks += 1
    check_batch([4, 2], [9, 5], [0, 0]); checks += 1

    # --- randomized fuzz ------------------------------------------------------
    rng = random.Random(16100)
    for _ in range(2000):
        n = rng.randint(0, 8)
        original = [rng.randint(-50, 50) for _ in range(n)]
        newvals = [rng.randint(-50, 50) for _ in range(n)]
        fails = [1 if rng.random() < 0.3 else 0 for _ in range(n)]
        check_batch(original, newvals, fails)
        checks += 1

    print("G-AX OK: committed_value/any_fails deep model == real "
          "transaction.atomic commit/rollback over %d batches "
          "(boundary failure-at-each-position + F2P witnesses + 2000 fuzz)"
          % checks)
    return 0


if __name__ == "__main__":
    sys.exit(main())
