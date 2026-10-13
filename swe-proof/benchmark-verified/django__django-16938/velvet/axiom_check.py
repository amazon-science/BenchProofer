#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-16938.

`Solution.lean` models the load plan a many-to-many relation iterator hands to
the SQL compiler as a `QState` (a `RelatedPlan` + an immediate-load mask) and
three deep-model transformers/predicates:

  * selectAllRelated  <-  QuerySet.select_related()      (no-arg form)
  * loadOnlyPk         <-  QuerySet.only("pk")
  * planRejected       <-  the FieldError raised by select_related_descend
                           (django/db/models/query_utils.py) when a related
                           selection is restricted to named relations and one of
                           those relations is deferred — surfaced through the SQL
                           compiler's get_related_selections.

Each is an **A-reference**: it stands for UNCHANGED queryset / compiler
machinery that the changed closure calls but does not modify. This check stands
up the REAL Django ORM (in-container, on the repo at base_commit) around models
that mirror the issue — a m2m relation whose related model carries a custom
manager doing `select_related(<fk>)` — and asserts:

  (1) selectAllRelated soundness: after a no-arg `.select_related()`, the real
      `query.select_related` is the boolean form (`True`), i.e. NOT a dict, so
      `restricted = isinstance(query.select_related, dict)` is False
      (RelatedPlan.unrestricted).
  (2) loadOnlyPk soundness: after `.only("pk")`, the immediate-load mask defers
      the related fk field (the relation is deferred).
  (3) planRejected soundness — the load-bearing one: for EVERY combination of
      {related selection restricted-to-names | unrestricted} x {only("pk") |
      no only}, the model's `planRejected` predicate equals whether the REAL SQL
      compiler raises FieldError while building the query. In particular the
      pre-patch plan (`only("pk")` over a manager that select_related's the fk)
      raises, and inserting the no-arg `.select_related()` (the gold fix) makes
      it not raise.

The flag dependency of mapping.md §3 is exercised directly: the conflict fires
only when `select_related` is a *dict* (restricted), so both the restricted and
unrestricted configurations are built and checked.

Stdlib + Django (the repo under test) only. Exit 0 iff every observation matches
the model. Boundary configurations plus randomized fuzz over the manager's
select_related field set and the immediate-load mask. Seed pinned (mapping.md).
"""
import random
import sys

SEED = 16938
N_FUZZ = 2000


def _bootstrap():
    """Minimal Django project with models mirroring the issue: a m2m relation
    whose related model has a custom manager that select_related's a nullable
    fk. Returns the handles the checks need."""
    import django
    from django.conf import settings

    if not settings.configured:
        settings.configure(
            DEBUG=True,
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "axcheck.apps.AxcheckConfig",
            ],
            USE_TZ=True,
            DEFAULT_AUTO_FIELD="django.db.models.AutoField",
        )
    # Register a throwaway app so our models have an app_label.
    from django.apps import AppConfig
    import importlib.machinery
    import types

    # NB: synthetic modules MUST carry a real __spec__. Django's AppConfig.create
    # calls module_has_submodule() -> importlib.util.find_spec("axcheck.apps"),
    # which raises `ValueError: axcheck.apps.__spec__ is None` for a bare
    # types.ModuleType (whose __spec__ defaults to None). Attach ModuleSpecs.
    app_module = types.ModuleType("axcheck")
    app_module.__path__ = []
    app_module.__spec__ = importlib.machinery.ModuleSpec(
        "axcheck", loader=None, is_package=True)
    app_module.__spec__.submodule_search_locations = []
    sys.modules["axcheck"] = app_module

    import tempfile

    class AxcheckConfig(AppConfig):
        name = "axcheck"
        label = "axcheck"
        # A real on-disk location satisfies AppConfig._path_from_module, which
        # rejects synthetic modules that lack a filesystem path.
        path = tempfile.mkdtemp(prefix="axcheck_")

    apps_module = types.ModuleType("axcheck.apps")
    apps_module.__spec__ = importlib.machinery.ModuleSpec(
        "axcheck.apps", loader=None)
    apps_module.AxcheckConfig = AxcheckConfig
    sys.modules["axcheck.apps"] = apps_module

    django.setup()

    from django.db import models

    class TagMaster(models.Model):
        name = models.CharField(max_length=120)

        class Meta:
            app_label = "axcheck"

    class TagManagerSR(models.Manager):
        """Custom manager that follows `master` by default (the issue)."""
        def get_queryset(self):
            return super().get_queryset().select_related("master")

    class Tag(models.Model):
        name = models.CharField(max_length=120)
        master = models.ForeignKey(TagMaster, on_delete=models.SET_NULL,
                                   null=True)
        objects = TagManagerSR()

        class Meta:
            app_label = "axcheck"

    class TagPlain(models.Model):
        """Same shape, but the default manager does NOT select_related —
        the unrestricted configuration."""
        name = models.CharField(max_length=120)
        master = models.ForeignKey(TagMaster, on_delete=models.SET_NULL,
                                   null=True)

        class Meta:
            app_label = "axcheck"

    class Holder(models.Model):
        name = models.CharField(max_length=120)
        tags = models.ManyToManyField(Tag)
        plain_tags = models.ManyToManyField(TagPlain)

        class Meta:
            app_label = "axcheck"

    from django.db import connection
    with connection.schema_editor() as se:
        se.create_model(TagMaster)
        se.create_model(Tag)
        se.create_model(TagPlain)
        se.create_model(Holder)

    return TagMaster, Tag, TagPlain, Holder


def _compiler_raises_fielderror(qs):
    """Run the REAL SQL setup for `qs` and report whether it raises the
    deferred+traversed FieldError. We force query compilation (which calls
    get_related_selections -> select_related_descend) without needing rows."""
    from django.core.exceptions import FieldError
    try:
        # Forces SQLCompiler.pre_sql_setup -> get_select ->
        # get_related_selections -> select_related_descend (the raise site).
        qs.query.get_compiler(using="default").as_sql()
    except FieldError as e:
        msg = str(e)
        assert "deferred" in msg and "select_related" in msg, (
            "unexpected FieldError (not the deferred+traversed conflict): %r"
            % msg)
        return True
    return False


# --- the model predicate (lock-step with Solution.lean planRejected) ---------

def model_plan_rejected(restricted, requested_relations, immediate):
    """planRejected (QState): isRestricted && any requested relation deferred.
    `immediate` is None (load all) or a set of immediately-loaded field names."""
    if not restricted:
        return False
    if immediate is None:
        return False
    return any(rel not in immediate for rel in requested_relations)


def check_config(relation_manager_qs, requested_relations, restricted,
                 apply_only):
    """Build the real iterator queryset for a relation and compare the SQL
    compiler's raise/no-raise verdict against the model's planRejected."""
    qs = relation_manager_qs
    immediate = None
    if apply_only:
        qs = qs.only("pk")
        immediate = {"pk"}

    # (1) selectAllRelated soundness is checked separately (see main()).
    # (2)/(3): does the REAL compiler raise, and does planRejected agree?
    real_raises = _compiler_raises_fielderror(qs)
    model_rejects = model_plan_rejected(restricted, requested_relations,
                                        immediate)
    assert real_raises == model_rejects, (
        "planRejected unsound: restricted=%r requested=%r only_pk=%r -> real "
        "compiler raises=%r but model planRejected=%r"
        % (restricted, requested_relations, apply_only, real_raises,
           model_rejects))
    return real_raises


def main():
    TagMaster, Tag, TagPlain, Holder = _bootstrap()

    # seed data: one holder with one tag (with a master) on each m2m relation
    master = TagMaster.objects.create(name="m")
    tag = Tag.objects.create(name="t", master=master)
    ptag = TagPlain.objects.create(name="p", master=master)
    holder = Holder.objects.create(name="h")
    holder.tags.add(tag)
    holder.plain_tags.add(ptag)

    n_checks = 0

    # --- (1) selectAllRelated soundness: no-arg select_related() yields the
    #         boolean (unrestricted) form, NOT a dict ------------------------
    restricted_qs = getattr(holder, "tags").all()          # manager SR("master")
    assert isinstance(restricted_qs.query.select_related, dict), (
        "test setup: the custom manager should leave a restricted (dict) "
        "select_related, got %r" % (restricted_qs.query.select_related,))
    reset_qs = restricted_qs.select_related()
    assert reset_qs.query.select_related is True, (
        "selectAllRelated unsound: no-arg select_related() must reset to the "
        "boolean True (unrestricted), got %r"
        % (reset_qs.query.select_related,))
    n_checks += 1

    # --- (2) loadOnlyPk soundness: only('pk') defers the related fk ----------
    only_qs = getattr(holder, "tags").all().only("pk")
    deferred = only_qs.query.deferred_loading
    # deferred_loading == (field_names, defer_flag); with only(), defer_flag is
    # False meaning "these are the immediate (only) fields". Note Django rewrites
    # the alias 'pk' to the concrete pk field name (e.g. 'id') in this set.
    only_fields, defer_flag = deferred
    pk_name = Tag._meta.pk.name
    assert defer_flag is False and pk_name in only_fields, (
        "loadOnlyPk unsound: only('pk') should set the immediate-load set to "
        "{%r} (defer the rest), got %r" % (pk_name, deferred,))
    # 'master' (the related fk) is therefore NOT immediately loaded => deferred
    assert "master" not in only_fields, (
        "loadOnlyPk unsound: the related fk 'master' must be deferred by "
        "only('pk'), but appears in the immediate set %r" % (only_fields,))
    n_checks += 1

    # --- (3) planRejected soundness over the configuration matrix ------------
    # restricted manager (select_related('master')) x {only('pk'), no only}
    #   - pre-patch:  only('pk')                       -> should RAISE
    #   - no only:    full load                        -> no raise
    #   - post-patch: select_related().only('pk')      -> no raise
    # unrestricted manager (plain) x {only('pk'), no only} -> never raises
    matrix = [
        # (queryset factory, requested_relations, restricted, apply_only, expect_raise)
        (lambda: getattr(holder, "tags").all(), ["master"], True, True, True),
        (lambda: getattr(holder, "tags").all(), ["master"], True, False, False),
        (lambda: getattr(holder, "tags").all().select_related(), [], False, True, False),
        (lambda: getattr(holder, "tags").all().select_related(), [], False, False, False),
        (lambda: getattr(holder, "plain_tags").all(), [], False, True, False),
        (lambda: getattr(holder, "plain_tags").all(), [], False, False, False),
    ]
    for make_qs, req, restricted, apply_only, expect in matrix:
        got = check_config(make_qs(), req, restricted, apply_only)
        assert got == expect, (
            "boundary mismatch: restricted=%r only_pk=%r expected raise=%r got=%r"
            % (restricted, apply_only, expect, got))
        n_checks += 1

    # --- randomized fuzz: vary the manager's select_related field set and the
    #     immediate-load mask, re-deriving the model verdict each time --------
    rng = random.Random(SEED)
    # candidate relations the related model actually has (only 'master' is a
    # real fk; non-fk names would error differently, so we restrict to it).
    for _ in range(N_FUZZ):
        use_sr = rng.random() < 0.5            # restricted (dict) vs unrestricted
        use_only = rng.random() < 0.5          # apply only('pk') or not
        if use_sr:
            qs = getattr(holder, "tags").all()  # manager already SR('master')
            requested = ["master"]
            restricted = True
        else:
            # randomly choose plain manager OR explicit reset via no-arg SR
            if rng.random() < 0.5:
                qs = getattr(holder, "plain_tags").all()
            else:
                qs = getattr(holder, "tags").all().select_related()
            requested = []
            restricted = False
        check_config(qs, requested, restricted, use_only)
        n_checks += 1

    print("G-AX OK: selectAllRelated (no-arg select_related -> unrestricted "
          "boolean), loadOnlyPk (only('pk') defers the related fk), and "
          "planRejected (== real SQL-compiler FieldError) sound on %d "
          "observations across restricted (dict select_related) and "
          "unrestricted configurations x {only('pk'), full load}; pre-patch "
          "plan raises, gold .select_related().only('pk') does not."
          % n_checks)
    return 0


if __name__ == "__main__":
    sys.exit(main())
