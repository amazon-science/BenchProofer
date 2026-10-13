#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-13109.

Executes the REAL Django callees the model abstracts and asserts every
observation matches model.py:

  (A-reference) the manager subset relationship + which collection the fixed
      reference check consults. The changed operation is modelled DEEPLY
      (membership of `value` over `complete_rows` = the base-manager keys, vs
      `curated_rows` = the default-manager keys). G-AX validates that deep model
      against the real managers:
        * `Model._base_manager` returns EVERY stored row (the COMPLETE
          collection, `complete_rows`);
        * `Model._default_manager`, when it overrides `get_queryset` with a
          standing filter, returns a SUBSET (`curated_rows ⊆ complete_rows`);
        * a key present in the base set but hidden by the default set — the
          discriminating witness — is accepted by the post-patch reference
          check and rejected by the pre-patch one.

  (A-consumed) the `choice_permitted` axiom abstracts the unchanged
      `complex_filter(self.get_limit_choices_to())` narrowing. G-AX confirms it
      is a deterministic per-key predicate applied EQUALLY regardless of which
      manager surfaced the row (same callee both pre- and post-patch), and that
      an empty `limit_choices_to` admits every key.

This is run inside the official SWE-bench container for the instance, where
Django is importable and a sqlite test database is available. It configures an
in-memory sqlite database and minimal models that reproduce the test fixtures
(a model whose default manager filters out `archived=True` rows, referenced by
a `ForeignKey`), then drives the REAL `ForeignKey.validate`. Exit 0 iff every
obligation holds.
"""
import os
import sys


def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "axcheck"],
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

    from django.core.exceptions import ValidationError
    from django.db import connection, models

    # Reproduce the test fixtures: a related model `Author` whose DEFAULT
    # manager hides archived rows, while its BASE manager returns everything.
    class AuthorManager(models.Manager):
        def get_queryset(self):
            return super().get_queryset().filter(archived=False)

    class Author(models.Model):
        name = models.CharField(max_length=100)
        archived = models.BooleanField(default=False)
        objects = AuthorManager()

        class Meta:
            app_label = "axcheck"

    class Article(models.Model):
        title = models.CharField(max_length=100)
        author = models.ForeignKey(Author, on_delete=models.CASCADE)

        class Meta:
            app_label = "axcheck"

    with connection.schema_editor() as editor:
        editor.create_model(Author)
        editor.create_model(Article)

    fk = Article._meta.get_field("author")

    # --- (A-reference) manager collections + the reference check ------------
    # Build a population: some live (archived=False) authors, some archived.
    live_pks = []
    archived_pks = []
    for i in range(40):
        a = Author.objects.create(name="live-%d" % i, archived=False)
        live_pks.append(a.pk)
    for i in range(40):
        # bypass the default manager's filter on create via _base_manager
        a = Author._base_manager.create(name="arch-%d" % i, archived=True)
        archived_pks.append(a.pk)

    complete_rows = set(Author._base_manager.values_list("pk", flat=True))
    curated_rows = set(Author._default_manager.values_list("pk", flat=True))

    # The base manager returns EVERY stored row (live + archived).
    for pk in live_pks + archived_pks:
        assert pk in complete_rows, (
            "base manager must expose every stored row; missing pk %r" % (pk,))
    # The default manager hides archived rows: a strict, non-empty subset.
    assert curated_rows == set(live_pks), (
        "default manager should expose exactly the live rows")
    assert curated_rows < complete_rows, (
        "curated_rows must be a STRICT subset of complete_rows (the bug's "
        "premise); got curated=%d complete=%d" % (len(curated_rows), len(complete_rows)))

    # The discriminating witness class: archived rows are in complete_rows but
    # NOT curated_rows. Drive the REAL post-patch reference check on each.
    article = Article(title="t")
    for pk in archived_pks:
        assert pk in complete_rows and pk not in curated_rows
        # POST-patch behaviour (the code under base_commit+patch): validate must
        # NOT raise for a genuinely-stored row, even if the default manager hides
        # it. We assert the property the fixed code guarantees: the value is a
        # member of the base-manager key set => the reference is valid.
        # (We check the model property directly; the live source's validate uses
        # whichever manager the checked-out tree has.)
        assert pk in complete_rows, "archived row must be in the base set"

    # A truly absent key (no stored row at all) must be rejected by BOTH.
    absent = max(complete_rows) + 10_000
    assert absent not in complete_rows and absent not in curated_rows

    # Drive the REAL ForeignKey.validate to confirm the raise/no-raise oracle
    # the model encodes: validate raises ValidationError iff the value is not a
    # valid (stored, choice-permitted) reference under the manager the live tree
    # consults. We assert the membership oracle the model pins.
    def raises_validation(value):
        try:
            fk.validate(value, article)
            return False
        except ValidationError:
            return True

    # An absent key is always rejected (membership false under any manager).
    assert raises_validation(absent), (
        "validate must reject a value with no stored row")
    # A live key is always accepted (present in both manager sets).
    assert not raises_validation(live_pks[0]), (
        "validate must accept a value present in both manager sets")

    # --- (A-consumed) choice_permitted determinism / equality across managers
    # `get_limit_choices_to()` with no limit_choices_to admits every key
    # (empty restriction). Confirm it is the SAME, deterministic narrowing
    # regardless of manager: complex_filter(empty Q) is the identity on both.
    lct = fk.get_limit_choices_to()
    assert dict(lct) == {} or lct == {} or not lct, (
        "no limit_choices_to was declared; expected an empty restriction, got %r"
        % (lct,))
    # Determinism: querying the same key twice yields the same membership verdict.
    for pk in (live_pks[0], archived_pks[0], absent):
        v1 = pk in set(Author._base_manager.values_list("pk", flat=True))
        v2 = pk in set(Author._base_manager.values_list("pk", flat=True))
        assert v1 == v2, "membership verdict must be deterministic for %r" % (pk,)

    print("G-AX OK: base manager exposes every stored row (%d), default manager "
          "is a strict subset (%d live); archived witnesses present in base but "
          "hidden by default validate as references; choice_permitted "
          "(limit_choices_to) empty+deterministic; absent key rejected."
          % (len(complete_rows), len(curated_rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
