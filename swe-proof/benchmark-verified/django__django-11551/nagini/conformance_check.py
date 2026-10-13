#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-11551 (nagini).

SHADOW  — the impl region of model.py (`check_display_item`), copied VERBATIM;
          the impl region carries no contract calls, so nothing needed
          stripping. It is a pure decision over six boolean observations and
          returns an int verdict code in {0, 108, 109}.

BRIDGE  — mapping.md §§1-2: each parameter is the single observation one
          unchanged primitive produces on the concrete scenario —
            is_invokable          <- callable(item)
            is_presenter_attr     <- hasattr(obj, item)
            structural_absent     <- obj.model._meta.get_field(item) raises
                                     FieldDoesNotExist
            structural_is_relation<- isinstance(field, ManyToManyField) on the
                                     yielded field
            attribute_absent      <- getattr(obj.model, item) raises
                                     AttributeError
            attribute_is_relation <- isinstance(value, ManyToManyField) on the
                                     yielded value
          and the real return value (a list of zero or one checks.Error) maps
          to the int code by 0 <-> [], 108 <-> [id 'admin.E108'],
          109 <-> [id 'admin.E109'].

ORACLE  — the REAL patched repo function ModelAdminChecks.
          _check_list_display_item (PYTHONPATH=/testbed; the gate applies the
          gold patch before this script runs), driven with genuine Django
          model classes and ModelAdmin instances built to realize every
          reachable observation shape: callable entries, presenter
          attributes, declared plain fields, declared many-to-many fields,
          declared fields shadowed by a class descriptor that raises
          AttributeError on class access (the F2P shape), non-field class
          attributes (plain and relation-valued), inherited object/Model
          attributes, and fully absent names.

For every scenario the six observations are derived with the primitives
above, the shadow verdict is computed from them, the real function is
called on the same concrete objects, and its abstracted verdict must equal
the shadow's. Exit 0 iff zero disagreements over the boundary cases +
100000 fuzzed scenarios. Pinned seed: 11551. stdlib only.
"""
import random
import string
import sys

SEED = 11551
N_FUZZ = 100_000


# ---------------------------------------------------------------------------
# model.py impl region, copied VERBATIM (no contract calls appear in it).
# ---------------------------------------------------------------------------

def check_display_item(
        is_invokable: bool,
        is_presenter_attr: bool,
        structural_absent: bool,
        structural_is_relation: bool,
        attribute_absent: bool,
        attribute_is_relation: bool) -> int:
    if is_invokable:
        return 0
    if is_presenter_attr:
        return 0
    if not structural_absent:
        relation = structural_is_relation  # type: bool
    elif attribute_absent:
        return 108
    else:
        relation = attribute_is_relation
    if relation:
        return 109
    return 0


# ---------------------------------------------------------------------------
# Django bootstrap (in-container: PYTHONPATH=/testbed, gold patch applied by
# the gate). Minimal settings; no database access is performed — the checked
# routine only inspects class-level metadata.
# ---------------------------------------------------------------------------

import django
from django.conf import settings

settings.configure(
    INSTALLED_APPS=[
        "django.contrib.contenttypes",
        "django.contrib.auth",
    ],
    DATABASES={},
)
django.setup()

from django.contrib.admin.checks import ModelAdminChecks     # noqa: E402
from django.contrib.admin.options import ModelAdmin          # noqa: E402
from django.contrib.admin.sites import AdminSite             # noqa: E402
from django.core.exceptions import FieldDoesNotExist         # noqa: E402
from django.db import models                                 # noqa: E402


# ---------------------------------------------------------------------------
# Bridge: derive the six observations from the concrete (obj, item) pair
# using exactly the unchanged primitives mapping.md binds each parameter to.
# ---------------------------------------------------------------------------

def derive_observations(obj, item):
    is_invokable = callable(item)
    if is_invokable:
        # The remaining primitives are never consulted for an invokable
        # entry (and hasattr needs a string); the model treats them as
        # don't-cares on this path.
        return (True, False, False, False, False, False)
    is_presenter_attr = hasattr(obj, item)
    try:
        f = obj.model._meta.get_field(item)
        structural_absent = False
        structural_is_relation = isinstance(f, models.ManyToManyField)
    except FieldDoesNotExist:
        structural_absent = True
        structural_is_relation = False
    try:
        v = getattr(obj.model, item)
        attribute_absent = False
        attribute_is_relation = isinstance(v, models.ManyToManyField)
    except AttributeError:
        attribute_absent = True
        attribute_is_relation = False
    return (is_invokable, is_presenter_attr,
            structural_absent, structural_is_relation,
            attribute_absent, attribute_is_relation)


def real_verdict(errors):
    """Abstract the real return (list of checks.Error) to the int code."""
    if not errors:
        return 0
    assert len(errors) == 1, "validator returned %d errors" % len(errors)
    eid = errors[0].id  # e.g. 'admin.E108'
    assert eid in ("admin.E108", "admin.E109"), "unexpected error id %r" % eid
    return int(eid.rsplit("E", 1)[1])


# ---------------------------------------------------------------------------
# Concrete scenario construction: genuine model classes + ModelAdmin
# instances realizing every reachable observation shape.
# ---------------------------------------------------------------------------

class _RaisingDescriptor:
    """A class-level descriptor whose __get__ raises AttributeError when
    accessed on the class — makes the attribute lookup report absent even
    though the structural lookup yields a field (the F2P shape)."""

    def __get__(self, instance, owner):
        raise AttributeError("not reachable on the class")


_LETTERS = string.ascii_lowercase


def _rand_name(rng, prefix):
    return prefix + "".join(rng.choice(_LETTERS) for _ in range(rng.randint(3, 8)))


class ScenarioModel:
    """One dynamically created model class + its admins, with the item names
    that drive each observation shape recorded."""

    _counter = 0

    def __init__(self, rng):
        ScenarioModel._counter += 1
        idx = ScenarioModel._counter
        self.plain_field = _rand_name(rng, "pf_")
        self.m2m_field = _rand_name(rng, "mm_")
        self.shadowed_field = _rand_name(rng, "sf_")
        self.class_attr = _rand_name(rng, "ca_")
        self.class_attr_m2m = _rand_name(rng, "cm_")
        self.presenter_attr = _rand_name(rng, "pa_")
        attrs = {
            "__module__": __name__,
            "Meta": type("Meta", (), {"app_label": "conf_check_app"}),
            self.plain_field: models.CharField(max_length=16),
            self.m2m_field: models.ManyToManyField("self"),
            self.shadowed_field: models.IntegerField(),
        }
        self.model = type("ConfModel%d" % idx, (models.Model,), attrs)
        # Shadow the declared field with a descriptor that raises on class
        # access: structural lookup yields, attribute lookup reports absent.
        setattr(self.model, self.shadowed_field, _RaisingDescriptor())
        # Non-field class attributes: one arbitrary object, one that IS a
        # (unbound) many-to-many field instance so the attribute path can
        # yield a relation without the structural path knowing it.
        setattr(self.model, self.class_attr, object())
        setattr(self.model, self.class_attr_m2m, models.ManyToManyField("self"))
        site = AdminSite()
        self.plain_admin = ModelAdmin(self.model, site)
        admin_cls = type("ConfAdmin%d" % idx, (ModelAdmin,),
                         {self.presenter_attr: lambda self_, o: "x"})
        self.presenter_admin = admin_cls(self.model, site)


CHECKER = ModelAdminChecks()


def run_case(obj, item):
    """Return (observations, shadow_code, real_code) for one scenario."""
    obs = derive_observations(obj, item)
    shadow = check_display_item(*obs)
    real = real_verdict(CHECKER._check_list_display_item(obj, item, "list_display[0]"))
    return obs, shadow, real


def boundary_cases(sm):
    """(obj, item) pairs pinning each observation shape + inherited-name
    edges, all on one scenario model."""
    yield sm.plain_admin, lambda o: "x"          # invokable entry
    yield sm.presenter_admin, sm.presenter_attr  # presenter attribute
    yield sm.plain_admin, sm.plain_field         # structural yields, plain
    yield sm.plain_admin, sm.m2m_field           # structural yields, relation
    yield sm.plain_admin, sm.shadowed_field      # structural yields, attribute absent (F2P shape)
    yield sm.plain_admin, sm.class_attr          # structural absent, attribute yields plain
    yield sm.plain_admin, sm.class_attr_m2m      # structural absent, attribute yields relation
    yield sm.plain_admin, "zz_definitely_absent" # both lookups absent
    yield sm.plain_admin, ""                     # empty name: both absent
    yield sm.plain_admin, "pk"                   # property, not a field
    yield sm.plain_admin, "id"                   # implicit auto field
    yield sm.plain_admin, "objects"              # manager: attribute yields
    yield sm.plain_admin, "save"                 # inherited method attribute
    yield sm.plain_admin, "_meta"                # meta attribute
    yield sm.presenter_admin, sm.m2m_field       # presenter admin, relation name
    yield sm.presenter_admin, "zz_definitely_absent"


def main():
    rng = random.Random(SEED)
    n_models = 120
    scenario_models = [ScenarioModel(rng) for _ in range(n_models)]

    disagreements = []
    count = 0

    def check(obj, item):
        nonlocal count
        count += 1
        obs, shadow, real = run_case(obj, item)
        if shadow != real:
            disagreements.append((item, obs, shadow, real))

    for obj, item in boundary_cases(scenario_models[0]):
        check(obj, item)
        if disagreements:
            break

    kinds = ("callable", "presenter", "plain_field", "m2m_field",
             "shadowed_field", "class_attr", "class_attr_m2m",
             "absent", "inherited")
    inherited_names = ("pk", "id", "objects", "save", "delete", "_meta",
                       "DoesNotExist", "__str__", "clean")

    for _ in range(N_FUZZ):
        if len(disagreements) >= 5:
            break
        sm = rng.choice(scenario_models)
        kind = rng.choice(kinds)
        if kind == "callable":
            obj, item = sm.plain_admin, (lambda o: o)
        elif kind == "presenter":
            obj, item = sm.presenter_admin, sm.presenter_attr
        elif kind == "plain_field":
            obj, item = rng.choice((sm.plain_admin, sm.presenter_admin)), sm.plain_field
        elif kind == "m2m_field":
            obj, item = rng.choice((sm.plain_admin, sm.presenter_admin)), sm.m2m_field
        elif kind == "shadowed_field":
            obj, item = sm.plain_admin, sm.shadowed_field
        elif kind == "class_attr":
            obj, item = sm.plain_admin, sm.class_attr
        elif kind == "class_attr_m2m":
            obj, item = sm.plain_admin, sm.class_attr_m2m
        elif kind == "absent":
            obj, item = sm.plain_admin, _rand_name(rng, "zz_")
        else:  # inherited
            obj, item = sm.plain_admin, rng.choice(inherited_names)
        check(obj, item)

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s) over %d scenarios (seed=%d):"
              % (len(disagreements), count, SEED))
        for item, obs, shadow, real in disagreements:
            print("  item=%r observations=%r\n    shadow=%r\n    real=%r"
                  % (item, obs, shadow, real))
        return 1
    print("G-CONF OK: model.py impl shadow (six-boolean observation carrier, "
          "bridged per mapping.md) agrees with the real patched "
          "_check_list_display_item verdict on %d scenarios (seed=%d), "
          "0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
