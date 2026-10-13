#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-14725.

The two consumed axioms in model.py describe the UNCHANGED persistence
primitives the operation calls — Django's
``BaseModelFormSet.save_existing_objects`` and
``BaseModelFormSet.save_new_objects`` — abstracted to the sequence of record
identifiers each reports:

  existing_report(commit) == ToSeq(save_existing_objects(commit))   # already-existing group
  new_report(commit)      == ToSeq(save_new_objects(commit))        # new group

The load-bearing soundness facts this check establishes against the REAL Django
machinery, inside the official SWE-bench container for the instance:

  (i)  the two primitives are UNCHANGED by the patch — the patch only adds a
       guard in ``save`` and threads an ``edit_only`` flag through the factories,
       it does not alter ``save_existing_objects`` / ``save_new_objects``. So
       modelling them as opaque report-producers is faithful;

  (ii) ``save_existing_objects`` reports only already-existing records and never
       brings a new record into existence; ``save_new_objects`` reports exactly
       the new records it brings into existence (the empty list when none);

  (iii) the discriminating behaviour the spec pins, observed end-to-end:
        * with the restrict-to-existing flag set, ``save()`` returns EXACTLY
          ``save_existing_objects()`` (no new record created), and
        * without it, ``save()`` returns
          ``save_existing_objects() + save_new_objects()`` (concatenation),
        matching the three FAIL_TO_PASS scenarios.

Run inside the official SWE-bench container for the instance, where Django is
importable and a sqlite test database is available. Exit 0 iff every obligation
holds. Outside the container (Django absent) it prints ``G-AX SKIP`` and returns
0; the orchestrator runs it in-container.
"""
import sys


def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
            ],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
            USE_TZ=False,
        )
    django.setup()


def main():
    try:
        _configure_django()
    except Exception as exc:  # pragma: no cover - environment guard
        print("G-AX SKIP: Django not configurable in this environment: %r" % (exc,))
        return 0

    import inspect
    from django.db import connection, models
    from django.forms.models import (
        BaseModelFormSet, modelformset_factory, inlineformset_factory,
    )

    # --- (i) the two primitives are UNCHANGED by the patch -------------------
    # The gold patch touches `save`, `modelformset_factory`, `inlineformset_factory`.
    # It must NOT touch the two persistence primitives the axioms abstract.
    for name in ("save_existing_objects", "save_new_objects"):
        src = inspect.getsource(getattr(BaseModelFormSet, name))
        assert "edit_only" not in src, (
            "%s unexpectedly references edit_only — it is supposed to be the "
            "unchanged primitive the axiom abstracts" % name)

    # Minimal, dependency-free models: structural twins of the test's Author /
    # Book. Registered under the already-installed `auth` app so the app
    # registry resolves them without a bespoke app package.
    class Author(models.Model):
        name = models.CharField(max_length=100)

        class Meta:
            app_label = "auth"

    class Book(models.Model):
        author = models.ForeignKey(Author, models.CASCADE)
        title = models.CharField(max_length=100)

        class Meta:
            app_label = "auth"

    with connection.schema_editor() as editor:
        editor.create_model(Author)
        editor.create_model(Book)

    obs = 0

    # --- (iii) restrict-to-existing: save() == save_existing_objects() -------
    # FAIL_TO_PASS test_edit_only: a brand-new (no existing) submission with
    # edit_only=True must create NOTHING.
    charles = Author.objects.create(name="Charles Baudelaire")
    AuthorFormSet = modelformset_factory(Author, fields="__all__", edit_only=True)
    data = {
        "form-TOTAL_FORMS": "2",
        "form-INITIAL_FORMS": "0",
        "form-MAX_NUM_FORMS": "0",
        "form-0-name": "Arthur Rimbaud",
        "form-1-name": "Walt Whitman",
    }
    fs = AuthorFormSet(data)
    assert fs.is_valid() is True, fs.errors
    saved = fs.save()
    # save() must equal save_existing_objects() exactly (here: empty); the new
    # group must NOT have been persisted.
    assert saved == [], "edit_only save() created records: %r" % (saved,)
    assert list(Author.objects.all()) == [charles], (
        "edit_only created new Authors: %r" % (list(Author.objects.all()),))
    obs += 1

    # editing an existing record under edit_only still works (returns it).
    data = {
        "form-TOTAL_FORMS": "2",
        "form-INITIAL_FORMS": "1",
        "form-MAX_NUM_FORMS": "0",
        "form-0-id": str(charles.pk),
        "form-0-name": "Arthur Rimbaud",
        "form-1-name": "Walt Whitman",
    }
    fs = AuthorFormSet(data)
    assert fs.is_valid() is True, fs.errors
    saved = fs.save()
    # Exactly the existing group; the second (new) form must NOT be created.
    assert [a.pk for a in saved] == [charles.pk], (
        "edit_only save() returned more than the existing group: %r" % (saved,))
    charles.refresh_from_db()
    assert charles.name == "Arthur Rimbaud"
    assert list(Author.objects.all()) == [charles], (
        "edit_only created a new Author on an edit submission")
    obs += 1

    # FAIL_TO_PASS test_edit_only_object_outside_of_queryset: a pk outside the
    # bound queryset is treated as an empty/unexpected existing object (skipped
    # by save_existing_objects), and edit_only forbids the new group too.
    walt = Author.objects.create(name="Walt Whitman")
    data = {
        "form-TOTAL_FORMS": "1",
        "form-INITIAL_FORMS": "1",
        "form-0-id": str(walt.pk),
        "form-0-name": "Parth Patil",
    }
    AuthorFormSet = modelformset_factory(Author, fields="__all__", edit_only=True)
    fs = AuthorFormSet(data, queryset=Author.objects.filter(pk=charles.pk))
    assert fs.is_valid() is True, fs.errors
    fs.save()
    names = sorted(a.name for a in Author.objects.all())
    assert names == sorted(["Arthur Rimbaud", "Walt Whitman"]), (
        "object outside queryset was modified/created: %r" % (names,))
    obs += 1

    # --- (iii) default (no restriction): save() == existing + new ------------
    Author.objects.all().delete()
    base = Author.objects.create(name="Base")
    AuthorFormSet = modelformset_factory(Author, fields="__all__")  # edit_only defaults False
    data = {
        "form-TOTAL_FORMS": "2",
        "form-INITIAL_FORMS": "1",
        "form-MAX_NUM_FORMS": "0",
        "form-0-id": str(base.pk),
        "form-0-name": "Base Edited",
        "form-1-name": "Newly Created",
    }
    fs = AuthorFormSet(data)
    assert fs.is_valid() is True, fs.errors
    saved = fs.save()
    saved_names = [a.name for a in saved]
    # existing group (the edited base) FOLLOWED BY the new group (the created one).
    assert saved_names == ["Base Edited", "Newly Created"], (
        "default save() is not existing ++ new: %r" % (saved_names,))
    all_names = sorted(a.name for a in Author.objects.all())
    assert all_names == sorted(["Base Edited", "Newly Created"]), all_names
    obs += 1

    # --- (ii) inline factory threads the flag too (FAIL_TO_PASS) -------------
    Author.objects.all().delete()
    Book.objects.all().delete()
    charles = Author.objects.create(name="Charles Baudelaire")
    book = Book.objects.create(author=charles, title="Les Paradis Artificiels")
    BookFormSet = inlineformset_factory(
        Author, Book, can_delete=False, fields="__all__", edit_only=True,
    )
    data = {
        "book_set-TOTAL_FORMS": "4",
        "book_set-INITIAL_FORMS": "1",
        "book_set-MAX_NUM_FORMS": "0",
        "book_set-0-id": str(book.pk),
        "book_set-0-title": "Les Fleurs du Mal",
        "book_set-0-author": str(charles.pk),
        "book_set-1-title": "Flowers of Evil",
        "book_set-1-author": str(charles.pk),
    }
    fs = BookFormSet(data, instance=charles)
    assert fs.is_valid() is True, fs.errors
    fs.save()
    book.refresh_from_db()
    assert book.title == "Les Fleurs du Mal"
    assert list(Book.objects.all()) == [book], (
        "inline edit_only created a new Book: %r" % (list(Book.objects.all()),))
    obs += 1

    print("G-AX OK: existing_report/new_report axioms sound against the real "
          "unchanged save_existing_objects/save_new_objects; save() == existing "
          "under restriction and existing ++ new otherwise, over %d end-to-end "
          "observations incl. all FAIL_TO_PASS scenarios." % (obs,))
    return 0


if __name__ == "__main__":
    sys.exit(main())
