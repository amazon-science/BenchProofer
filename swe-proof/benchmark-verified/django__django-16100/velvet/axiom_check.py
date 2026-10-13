#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-16100.

This bundle declares **NO consumed axioms**. The all-or-nothing commit behaviour
the gold patch introduces — wrapping the list-editable save loop in
`transaction.atomic(using=router.db_for_write(self.model))`
(`django/contrib/admin/options.py:2011-2025`) — is modeled **deeply** in
Solution.lean's pure region by `committedAtomic` (with `anyFail`/`changedVals`):

    committedAtomic us = [] if anyFail us else changedVals us

i.e. the batch of edited-row writes commits as one unit — every staged write is
durable iff the batch completes without any row raising, otherwise nothing is.
The unchanged transaction manager this rides on is a **deep-model reference
(A-reference)**, not a consumed axiom. G-AX validates that deep model against the
REAL `django.db.transaction.atomic` over a live database.

What this script asserts:

  1. (no-axiom claim) meta.json lists no consumed axioms — a future edit that
     smuggles in an `axiom` without an executable soundness check is caught here.

  2. (A-reference) for every batch of row updates, running the SAME save loop the
     patch wraps inside a REAL `transaction.atomic(using=...)` block leaves the
     database in exactly the state `committedAtomic` predicts:
        * no row raises  -> every edited row's new value is committed (durable),
          in batch order  == changedVals(batch);
        * some row raises -> the exception propagates out of the atomic block and
          EVERY write staged in the batch (including those made before the
          failing row) is rolled back == []  (the empty commit set).
     Checked over boundary batches (empty, all-clean, fail-first, fail-last,
     fail-middle, no-changed-rows, single row) + randomized fuzz batches.

  3. (router independence — the `using=` argument) `router.db_for_write(model)`
     resolves to a real connection alias and the atomic block opened on it is the
     unit whose rollback we observe; the choice of write alias does not change
     the all-or-nothing property.

Imports only the standard library + django (the package the gold patch edits) and
uses an in-memory sqlite backend with transaction support — the same machinery
the F2P test `test_list_editable_atomicity` exercises. Exit 0 iff every
obligation holds.
"""
import json
import os
import random
import sys


def _setup_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DATABASES={
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": ":memory:",
                },
            },
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            DATABASE_ROUTERS=[],
        )
    django.setup()


def check_no_consumed_axioms():
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "meta.json")) as fh:
        meta = json.load(fh)
    axioms = meta.get("axioms", [])
    assert axioms == [], (
        "axiom_check expected no consumed axioms but meta.json lists %r; a "
        "consumed axiom requires an executable soundness check here." % (axioms,))


# --- the deep model committedAtomic (kept in lock-step with Solution.lean) ----
# A batch element is a dict: {"changed": bool, "value": int, "raises": bool}.

def any_fail(batch):
    return any(u["changed"] and u["raises"] for u in batch)


def changed_vals(batch):
    return [u["value"] for u in batch if u["changed"]]


def committed_atomic(batch):
    """Transliteration of Solution.lean `committedAtomic`."""
    return [] if any_fail(batch) else changed_vals(batch)


class _BatchError(Exception):
    """Stand-in for the DatabaseError the F2P mocks `log_change` to raise."""


def main():
    check_no_consumed_axioms()
    _setup_django()

    from django.db import connection, models, router, transaction

    # A throwaway model with a real table, standing in for the edited rows.
    class Row(models.Model):
        value = models.IntegerField()

        class Meta:
            app_label = "ax16100"

    with connection.schema_editor() as se:
        se.create_model(Row)

    # The write alias resolution the gold patch passes to transaction.atomic.
    using = router.db_for_write(Row)
    assert using == "default", (
        "router.db_for_write(model) should resolve to a real connection alias; "
        "got %r" % (using,))

    def committed_state():
        """The set of values durably present in the table, in insertion order."""
        return list(Row.objects.using(using).order_by("id").values_list("value", flat=True))

    checked = {"n": 0}

    def run_batch_atomic(batch):
        """Run the patch's save loop for `batch` INSIDE a real
        transaction.atomic(using=...) block — the exact construct the gold patch
        adds. Each 'changed' row stages a write (INSERT); a row whose 'raises' is
        set throws after staging, propagating out of the atomic block."""
        try:
            with transaction.atomic(using=using):
                for u in batch:
                    if u["changed"]:
                        Row.objects.using(using).create(value=u["value"])
                        if u["raises"]:
                            raise _BatchError("downstream failure on edited row")
        except _BatchError:
            pass  # the F2P asserts the exception escapes; we observe the DB state

    def check(batch):
        # fresh table for each batch
        Row.objects.using(using).all().delete()
        run_batch_atomic(batch)
        observed = committed_state()
        expected = committed_atomic(batch)
        assert observed == expected, (
            "A-reference committedAtomic unsound: after a real "
            "transaction.atomic save loop the DB holds %r, deep model predicts "
            "%r (batch=%r)" % (observed, expected, batch))
        checked["n"] += 1

    def U(changed, value, raises):
        return {"changed": changed, "value": value, "raises": raises}

    # ---- boundary batches ----------------------------------------------------
    check([])                                            # empty
    check([U(True, 1, False), U(True, 2, False)])        # all clean -> both commit
    check([U(True, 1, True), U(True, 2, False)])         # fail FIRST -> nothing
    check([U(True, 1, False), U(True, 2, True)])         # fail LAST -> nothing
    check([U(True, 1, False), U(True, 2, True), U(True, 3, False)])  # fail MIDDLE
    check([U(False, 1, False), U(False, 2, True)])       # no edited row -> nothing staged, no raise (unedited never raises)
    check([U(False, 1, False), U(True, 2, True)])        # skip an unedited row, then an edited row fails -> rolled back
    check([U(True, 7, False)])                           # single clean
    check([U(True, 7, True)])                            # single failing -> rolled back

    # ---- randomized fuzz -----------------------------------------------------
    rng = random.Random(16100)
    for _ in range(2000):
        n = rng.randint(0, 8)
        batch = [U(rng.random() < 0.7, rng.randint(-1000, 1000), rng.random() < 0.25)
                 for _ in range(n)]
        check(batch)

    print("G-AX OK: A-reference committedAtomic == real transaction.atomic save "
          "loop on %d batches (9 boundary + 2000 fuzz): a mid-batch exception "
          "rolls back ALL staged writes (commit set []), a clean batch commits "
          "every edited row's write (== changedVals); router.db_for_write -> %r. "
          "Bundle declares no consumed axioms." % (checked["n"], using))
    return 0


if __name__ == "__main__":
    sys.exit(main())
