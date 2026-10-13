#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-16938.

There is NO consumed @ContractOnly axiom in model.py: the changed behaviour is
modelled DEEPLY. This script validates that deep model as an A-REFERENCE against
the REAL Django ORM callees the serializer chains:

  * `QuerySet.select_related()` with no arguments  -> the deep model
    `clear_specific_request`: it resets the eager-co-selection request to its
    unrestricted default, so `query.select_related` is NOT a dict afterwards
    (the "restricted" facet becomes False);
  * `QuerySet.only("pk")` -> the deep model `only_pk`: it narrows the loaded
    projection to the primary-key field;
  * the evaluation-time descend check `select_related_descend`
    (`django/db/models/query_utils.py`) -> the deep model predicate
    `ill_formed(restricted, requested, loaded)`: it errors iff a *specific* set
    of adjacent records is requested for eager co-selection (restricted) AND a
    requested adjacent record is excluded by the projection.

The model's claim, validated here against real Django:

  (1) ill_formed semantics: with a restricted (dict) select_related naming an
      adjacent field that `only("pk")` excludes, building the SQL raises
      FieldError -- the deep `ill_formed` predicate is True. This is the
      PRE-PATCH chain (`getattr(...).only("pk")`) and the model_prepatch
      discriminator.
  (2) reset semantics + well-formedness: prepending `select_related()` (no args)
      makes `query.select_related` a non-dict (restricted=False), so the
      descend check cannot raise; building the SQL succeeds and selects ONLY the
      pk column (no adjacent-record column). This is the POST-PATCH chain
      (`getattr(...).select_related().only("pk")`), which the frozen
      postcondition `not ill_formed(...)` and `loaded == {pk}` require.

Imports are stdlib + Django (the repo under test); exit 0 iff sound.
"""
import sys

import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
    )
    django.setup()

from django.core.exceptions import FieldError  # noqa: E402
from django.db import models  # noqa: E402


# A custom manager whose default queryset bakes in an eager-co-selection request
# (select_related) naming an adjacent record -- exactly the issue's reproducer.
class TagManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("master")


class TagMaster(models.Model):
    name = models.CharField(max_length=120)

    class Meta:
        app_label = "axch"


class Tag(models.Model):
    objects = TagManager()
    name = models.CharField(max_length=120)
    master = models.ForeignKey(TagMaster, models.SET_NULL, null=True)

    class Meta:
        app_label = "axch"


def base_queryset():
    """The base related-collection queryset as the serializer obtains it: from
    the custom manager that has baked in select_related('master')."""
    return Tag.objects.all()


def restricted_flag(qs):
    """The model's `restricted` facet: True iff a *specific* set of adjacent
    records is requested (query.select_related is a dict)."""
    return isinstance(qs.query.select_related, dict)


def selects_only_pk(qs):
    """True iff compiling the query selects exactly the pk column and nothing
    from the adjacent (master) record."""
    compiler = qs.query.get_compiler(using="default")
    compiler.pre_sql_setup()
    cols = [c[0] for c in compiler.select]
    # exactly one selected column, the Tag primary key; no master_id / master.*
    aliases = [getattr(c, "target", None) for c in cols]
    names = [getattr(a, "attname", None) for a in aliases]
    return names == ["id"]


def builds_ok(qs):
    """Run the real SQL setup; return True if it does NOT raise FieldError."""
    try:
        compiler = qs.query.get_compiler(using="default")
        compiler.pre_sql_setup()
        return True
    except FieldError:
        return False


def main():
    # --- (1) ill_formed semantics + PRE-PATCH discriminator -------------------
    # PRE-PATCH chain: getattr(obj, field.name).only("pk")
    prepatch = base_queryset().only("pk")
    # The base accessor baked in select_related('master') -> restricted (dict).
    assert restricted_flag(prepatch), (
        "expected restricted (dict) select_related from the custom manager")
    # Deep model: ill_formed(restricted=True, requested={master}, loaded={pk})
    # is True -> building the SQL must raise FieldError.
    assert not builds_ok(prepatch), (
        "deep model unsound: ill_formed predicted an error (restricted request "
        "names an excluded adjacent record) but the real query built cleanly")

    # --- (2) reset semantics + well-formedness (POST-PATCH chain) -------------
    # POST-PATCH chain: getattr(obj, field.name).select_related().only("pk")
    postpatch = base_queryset().select_related().only("pk")
    # clear_specific_request: query.select_related is no longer a dict -> the
    # model's `restricted` facet is False.
    assert not restricted_flag(postpatch), (
        "deep model unsound: select_related() (no args) should reset the "
        "request to its unrestricted default (non-dict select_related)")
    # not ill_formed -> building the SQL must NOT raise.
    assert builds_ok(postpatch), (
        "deep model unsound: not ill_formed predicted a well-formed query but "
        "the real query raised FieldError")
    # loaded == {pk}: exactly the primary key is selected, no adjacent column.
    assert selects_only_pk(postpatch), (
        "deep model unsound: only_pk should leave loaded == {pk}; the real "
        "query selected columns other than the pk")

    # --- robustness: also valid when the base carries NO baked-in request -----
    # (the ordinary case). Both chains are well-formed; the reset is a no-op on
    # the observable outcome. Simulate a non-restricted base by clearing the
    # select_related request explicitly.
    plain_base = Tag.objects.all().select_related(None)  # clears -> non-dict
    assert not restricted_flag(plain_base)
    assert builds_ok(plain_base.select_related().only("pk"))
    assert selects_only_pk(plain_base.select_related().only("pk"))

    print("G-AX OK: deep model (clear_specific_request / only_pk / ill_formed) "
          "validated against real Django QuerySet.select_related/only + "
          "select_related_descend. Pre-patch chain raises FieldError (ill_formed "
          "True); post-patch chain is well-formed and selects only the pk.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
