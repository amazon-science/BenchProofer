#!/usr/bin/env python3
r"""G-CONF differential conformance check for django__django-11551 (plan §4.1).

Runs IN-CONTAINER with the gold patch applied (the orchestrator passes
apply_gold=True), so the ORACLE is the patched repo's real behaviour.

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same inputs and comparing observable outputs:

  * SHADOW  — Solution.lean's modeled decision (`listDisplayItemOutcome`)
              transliterated to Python over the real repo types. Its five
              boolean inputs are the REAL runtime observations, computed live by
              running the unchanged observation primitives on real Django
              objects, via the mapping.md §2 bijection:
                  isCallable      <-> callable(item)
                  hasAttrObj      <-> hasattr(obj, item)
                  getFieldRaises  <-> obj.model._meta.get_field(item) raises
                                      FieldDoesNotExist
                  modelAttrRaises <-> getattr(obj.model, item) raises
                                      AttributeError
                  fieldIsM2M      <-> isinstance(<resolved field>,
                                      models.ManyToManyField)
              There are NO A-tagged ops (no consumed axioms), so the shadow is
              pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `ModelAdminChecks._check_list_display_item(obj, item, label)` run
              on a real `ModelAdmin` over a real model; the observable is the
              produced error id (or None for the empty `[]` report).

They must agree on every scenario. Exit 0 iff zero disagreements; any
disagreement is a mechanical R/I-fidelity counterexample.

The realizable inputs form a discrete set of scenarios (each a real
admin/model/item triple that exhibits a distinct observation pattern, including
the issue's instance-only descriptor field — the F2P path). The fuzz loop
resamples that set with a pinned seed so the verdict is reproducible and the
boundary cross-product is covered. stdlib + django only; in-memory only (no DB
rows are created). Fuzz seed pinned (mapping.md §4).
"""
import random
import sys

SEED = 11551
N_FUZZ = 100_000


def _bootstrap_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
            ],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
            USE_TZ=True,
        )
    django.setup()


_bootstrap_django()

from django.contrib.admin.options import ModelAdmin              # noqa: E402
from django.contrib.admin.sites import AdminSite                 # noqa: E402
from django.contrib.admin.checks import ModelAdminChecks         # noqa: E402
from django.core.exceptions import FieldDoesNotExist             # noqa: E402
from django.db import models                                     # noqa: E402


# --- real models / admins realizing each observation pattern ----------------

class _Target(models.Model):
    class Meta:
        app_label = "modeladmin_conf"


class _PlainModel(models.Model):
    number = models.IntegerField(default=0)
    rel = models.ManyToManyField(_Target, related_name="+")

    # A plain method and a property: known to the class via getattr but NOT to
    # the field registry (get_field raises, getattr succeeds, not a field).
    @property
    def computed(self):
        return 1

    def a_model_method(self):
        return 2

    class Meta:
        app_label = "modeladmin_conf"


class _PositionField(models.Field):
    """Custom field accessible only via instance — mirrors the F2P test's
    PositionField. Registered in the field registry, but class-level attribute
    access raises AttributeError (so the pre-patch hasattr-gate wrongly
    condemned it)."""

    def contribute_to_class(self, cls, name, **kwargs):
        super().contribute_to_class(cls, name, **kwargs)
        setattr(cls, self.name, self)

    def __get__(self, instance, owner):
        if instance is None:
            raise AttributeError()


class _PosModel(models.Model):
    order = _PositionField()

    class Meta:
        app_label = "modeladmin_conf"


class _AdminWithMethod(ModelAdmin):
    def an_admin_method(self, obj):
        return []


def _a_callable(obj):
    return []


# Each scenario: (label, admin_class, model_class, item). The five observations
# are computed LIVE from these real objects; nothing is hardcoded.
SCENARIOS = [
    ("callable_item",        _AdminWithMethod, _PlainModel, _a_callable),
    ("admin_method",         _AdminWithMethod, _PlainModel, "an_admin_method"),
    ("plain_field",          ModelAdmin,       _PlainModel, "number"),
    ("m2m_field",            ModelAdmin,       _PlainModel, "rel"),
    ("missing_name",         ModelAdmin,       _PlainModel, "no_such_name"),
    ("model_property",       ModelAdmin,       _PlainModel, "computed"),
    ("model_method",         ModelAdmin,       _PlainModel, "a_model_method"),
    # The bug's signature case: a registry-known field whose class-level
    # attribute access raises AttributeError. Pre-patch -> E108; correct -> [].
    ("instance_only_field",  ModelAdmin,       _PosModel,   "order"),
]


def _result_to_id(result):
    """CheckResult -> the error id the real check would carry (or None)."""
    return {"ok": None, "e108": "admin.E108", "e109": "admin.E109"}[result]


def observe(admin_obj, item):
    """Compute the five abstracted booleans by running the REAL observation
    primitives, mirroring the post-patch control-flow short-circuits."""
    is_callable = callable(item)
    if is_callable:
        return (True, False, False, False, False)

    has_attr_obj = hasattr(admin_obj, item)
    if has_attr_obj:
        return (False, True, False, False, False)

    model = admin_obj.model
    field = None
    try:
        field = model._meta.get_field(item)
        get_field_raises = False
    except FieldDoesNotExist:
        get_field_raises = True

    model_attr_raises = False
    if get_field_raises:
        try:
            field = getattr(model, item)
        except AttributeError:
            model_attr_raises = True
            field = None

    field_is_m2m = field is not None and isinstance(field, models.ManyToManyField)
    return (is_callable, has_attr_obj, get_field_raises, model_attr_raises,
            field_is_m2m)


def shadow_outcome(is_callable, has_attr_obj, get_field_raises,
                   model_attr_raises, field_is_m2m):
    """listDisplayItemOutcome transliterated to Python (pure R/I)."""
    if is_callable:
        return "ok"
    if has_attr_obj:
        return "ok"
    if get_field_raises:
        if model_attr_raises:
            return "e108"
        if field_is_m2m:
            return "e109"
        return "ok"
    if field_is_m2m:
        return "e109"
    return "ok"


def oracle(admin_class, model_class, item):
    """patch.diff behaviour: run the patched _check_list_display_item on a real
    ModelAdmin, read back the produced error id (None for the empty report)."""
    admin_obj = admin_class(model_class, AdminSite())
    checker = ModelAdminChecks()
    errors = checker._check_list_display_item(admin_obj, item, "list_display[0]")
    if not errors:
        return None
    assert len(errors) == 1, "unexpected multi-error report: %r" % (errors,)
    return errors[0].id


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    def all_inputs(n):
        # boundary: every scenario at least once, in order
        for sc in SCENARIOS:
            yield sc
        for _ in range(n):
            yield rng.choice(SCENARIOS)

    for label, admin_class, model_class, item in all_inputs(N_FUZZ):
        count += 1
        admin_obj = admin_class(model_class, AdminSite())
        obs = observe(admin_obj, item)
        shadow_id = _result_to_id(shadow_outcome(*obs))
        oracle_id = oracle(admin_class, model_class, item)
        if shadow_id != oracle_id:
            disagreements.append((label, obs, shadow_id, oracle_id))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs (seed=%d):"
              % (len(disagreements), count, SEED))
        for label, obs, sh, orc in disagreements:
            print("  scenario=%s obs=%r shadow=%r oracle=%r"
                  % (label, obs, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of listDisplayItemCheck agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements (field registry "
          "consulted before condemning; E108 only when both get_field and "
          "getattr fail; instance-only descriptor field accepted)." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
