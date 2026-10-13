#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-14725.

The bundle consumes NO `axiom`. The two unchanged persistence steps the changed
function (`BaseModelFormSet.save`) sits on top of are abstracted in
Solution.lean as free inputs (`existing`, `fresh`) plus a `mut` side-effect
frame (`stored`). This check validates the behavioural REFERENCE properties the
refinement relies on, against the REAL Django modelformset / ORM machinery,
driven over a live in-memory SQLite model exactly as the F2P tests drive it.

  (A-reference 1)  `save_existing_objects(commit)` (mapping.md §3.1) returns the
      already-known rows' identities, is INDEPENDENT of the `edit_only` flag,
      and never creates brand-new rows. So `existing` is a faithful free input
      in both branches.

  (A-reference 2)  `save_new_objects(commit)` (mapping.md §3.2) is the SOLE
      source of brand-new rows in the persistence pass: the identities it
      returns are exactly the brand-new rows it persists, while the OTHER
      component step (`save_existing_objects`) persists none. So suppressing the
      `save_new_objects` call (the edit-only branch of the spec) persists no new
      rows, and when it runs it adds exactly its return value. This validates
      both the `existing`/`fresh` abstraction (return == side effect) and the
      `stored` frame (forbid-new ⇒ stored = storedOld).

The reference properties are checked against the REAL unchanged callees
DIRECTLY — by decomposing the pass into its two component steps as the repo's
`save()` body does — never by calling the changed function under spec
(directive 7). This is exercised at base_commit (where the changed `save()` has
no edit-only branch at all): it only relies on the unchanged callees and the
factory plumbing, setting the `edit_only` class attribute directly when the
factory does not yet accept the kwarg. Imports only the standard library and
Django (the repo under test). Exit 0 iff every observation matches the model.
"""
import os
import random
import sys


def _bootstrap():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
            ],
            USE_TZ=True,
            DEFAULT_AUTO_FIELD="django.db.models.AutoField",
        )
    django.setup()

    from django.db import connection, models

    class Widget(models.Model):
        name = models.CharField(max_length=50)

        class Meta:
            app_label = "auth"  # borrow an installed app's registry

    with connection.schema_editor() as se:
        se.create_model(Widget)

    return Widget


def _make_formset(Widget, edit_only):
    """Build a modelformset class, threading edit_only through the patched
    factory if it accepts it, else setting the class attribute directly (so the
    unchanged-callee checks run at base_commit too)."""
    from django.forms.models import modelformset_factory
    try:
        FormSet = modelformset_factory(Widget, fields="__all__",
                                       edit_only=edit_only)
    except TypeError:
        # base_commit: factory has no edit_only kwarg; set the attribute the
        # patched save() reads, so save() behaviour matches the patched branch.
        FormSet = modelformset_factory(Widget, fields="__all__")
        FormSet.edit_only = edit_only
    return FormSet


def _data(initial_pks, new_names, prefix="form"):
    """POST data: one initial (edit) form per existing pk, plus extra (new)
    forms for each new name."""
    total = len(initial_pks) + len(new_names)
    data = {
        "%s-TOTAL_FORMS" % prefix: str(total),
        "%s-INITIAL_FORMS" % prefix: str(len(initial_pks)),
        "%s-MAX_NUM_FORMS" % prefix: "1000",
    }
    idx = 0
    for pk in initial_pks:
        data["%s-%d-id" % (prefix, idx)] = str(pk)
        data["%s-%d-name" % (prefix, idx)] = "edited%d" % idx
        idx += 1
    for nm in new_names:
        data["%s-%d-name" % (prefix, idx)] = nm
        idx += 1
    return data


def _pks(model):
    return sorted(model.objects.values_list("pk", flat=True))


def check_existing_flag_independent(Widget, n_initial, n_new):
    """A-reference 1: save_existing_objects settles exactly the already-known
    (initial) rows — its result is determined by the initial forms, not by the
    edit_only flag — and it creates/removes no rows. The settled identities are
    compared to THIS run's own seed pks (pks autoincrement across the
    delete/recreate between flag iterations, so absolute pks are not comparable
    across runs; the flag-independence is the structural relation 'returns
    exactly the initial rows', which holds identically under both flags)."""
    for flag in (False, True):
        Widget.objects.all().delete()
        seed_pks = [Widget.objects.create(name="seed%d" % i).pk
                    for i in range(n_initial)]
        before = set(_pks(Widget))
        FormSet = _make_formset(Widget, edit_only=flag)
        # all initial forms are edited (name changes seed%d -> edited%d), so
        # save_existing_objects settles and returns every already-known row.
        fs = FormSet(_data(seed_pks, ["new%d" % j for j in range(n_new)]))
        assert fs.is_valid(), "formset invalid: %r" % fs.errors
        existing = fs.save_existing_objects(commit=True)
        existing_pks = set(o.pk for o in existing)
        after = set(_pks(Widget))
        assert after == before, (
            "save_existing_objects created/removed rows (flag=%r): "
            "before=%r after=%r" % (flag, before, after))
        assert existing_pks == set(seed_pks), (
            "save_existing_objects did not settle exactly the already-known "
            "rows (flag=%r): returned=%r seeds=%r"
            % (flag, existing_pks, set(seed_pks)))


def check_new_objects_is_sole_source(Widget, n_initial, n_new):
    """A-reference 2: validated against the REAL unchanged callees directly, by
    decomposing the persistence pass into its two component steps exactly as the
    repo's `save()` body does (`save_existing_objects(commit) +
    save_new_objects(commit)`) — never by calling the changed function under
    spec (directive 7), which would assert the *patched* branch and is in any
    case absent at base_commit.

    Two reference properties of the unchanged callees:
      (a) `save_existing_objects` persists NO brand-new rows — so the only
          source of new rows in the pass is `save_new_objects`; suppressing
          that call (the edit-only branch of the spec) therefore persists none.
      (b) `save_new_objects` return == the brand-new rows it persists, exactly
          `n_new` of them — so `fresh` (its return) and its side effect on the
          persisted set coincide (`storedAfter` appends exactly `fresh`).
    Both hold for either factory configuration; the callee behaviour does not
    depend on the flag (the patch only chooses whether to RUN save_new_objects).
    """
    for flag in (False, True):
        Widget.objects.all().delete()
        seed_pks = [Widget.objects.create(name="seed%d" % i).pk
                    for i in range(n_initial)]
        before = set(_pks(Widget))
        FormSet = _make_formset(Widget, edit_only=flag)
        fs = FormSet(_data(seed_pks, ["new%d" % j for j in range(n_new)]))
        assert fs.is_valid(), "formset invalid: %r" % fs.errors

        # Step 1 (existing-row persistence): persists no brand-new rows.
        existing = fs.save_existing_objects(commit=True)
        after_existing = set(_pks(Widget))
        assert after_existing == before, (
            "save_existing_objects persisted brand-new rows (flag=%r): "
            "before=%r after=%r" % (flag, before, after_existing))
        # its reported identities are drawn from the already-known rows
        existing_pks = set(o.pk for o in existing)
        assert existing_pks <= before, (
            "save_existing_objects reported non-existing identities: "
            "out=%r existing=%r" % (existing_pks, before))

        # Step 2 (new-row producer): the SOLE source of brand-new rows; its
        # return value equals exactly the rows it persists.
        new = fs.save_new_objects(commit=True)
        after_new = set(_pks(Widget))
        added = after_new - after_existing
        new_pks = set(o.pk for o in new)
        assert added == new_pks, (
            "save_new_objects return != newly-persisted rows: "
            "added=%r returned=%r" % (added, new_pks))
        assert len(added) == n_new, (
            "save_new_objects expected %d new rows, got %d"
            % (n_new, len(added)))


def main():
    Widget = _bootstrap()

    # --- boundary cases ---------------------------------------------------
    boundary = [(0, 0), (0, 1), (1, 0), (1, 1), (2, 3), (3, 0), (0, 4), (5, 5)]
    for n_initial, n_new in boundary:
        check_existing_flag_independent(Widget, n_initial, n_new)
        check_new_objects_is_sole_source(Widget, n_initial, n_new)

    # --- randomized fuzz over the (n_initial, n_new) configuration --------
    rng = random.Random(14725)
    for _ in range(300):
        n_initial = rng.randint(0, 6)
        n_new = rng.randint(0, 6)
        check_existing_flag_independent(Widget, n_initial, n_new)
        check_new_objects_is_sole_source(Widget, n_initial, n_new)

    print("G-AX OK: save_existing_objects settles exactly the already-known "
          "rows and creates none (A-reference 1); save_new_objects is the sole "
          "source of new rows and its return equals the rows it persists "
          "(A-reference 2) — checked against the real unchanged callees "
          "directly over %d boundary + 300 fuzz configs." % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
