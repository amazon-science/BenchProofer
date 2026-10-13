#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-12713 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures) stripped. The @Pure helpers (key_component /
default_primary / default_secondary / default_tertiary) copy over as plain
functions. There is no @ContractOnly callee in this bundle. The model IS
Python; the shadow mutates a plain dict exactly as the impl region does.

ORACLE: the REAL patched repo method the model models per mapping.md --
``django.contrib.admin.options.ModelAdmin.formfield_for_manytomany`` (its
keyword-option widget-selection block). The gate applies the patch to
/testbed before this script runs; the script only imports and drives the
patched code.

Type bridge (mapping.md section 2): the model's ``Dict[int, int]`` options
mapping carries option-name tokens to component-identity tokens. Concretely:
token 0 <-> the presentation-component option name ``'widget'``; any nonzero
key token k <-> a distinct unrelated option name ``'opt<k>'``. Component
identities: tokens 1/2/3 <-> instances of the three name-derived widget
classes (AutocompleteSelectMultiple / ManyToManyRawIdWidget /
FilteredSelectMultiple, in the repo's priority order); every caller-supplied
value (whether or not its token collides with 1/2/3) is realised as a
concrete object registered by identity, so lowering is exact. The three
boolean membership tests lift to real name-membership: the relation's name is
placed into (or left out of) the admin's ``autocomplete_fields`` /
``raw_id_fields`` / ``filter_vertical``+``filter_horizontal`` collections;
for the tertiary test the vertical/horizontal channel is varied (their union
is the tested set). ``component_present`` is computed from the entry options
(the precondition pins it to the entry membership of token 0), so every
generated input satisfies the Requires by construction.

Observation point: the method forwards its (post-selection) keyword options
to ``db_field.formfield(**kwargs)``; a stub relation field records that
mapping, which is then lowered back to the ``Dict[int, int]`` carrier and
compared against the shadow's post-state. The admin site's registry is left
empty so the unrelated queryset-defaulting step downstream of the modeled
block contributes no key.

>= 1e5 Requires-satisfying inputs: boundary cases (7 entry maps x 8 flag
combinations x tertiary-channel variants + targeted extras) + 100000 fuzz
tuples. Pinned fuzz seed: 12713. Exit 0 iff zero disagreements; on a
disagreement the input and both outputs are printed and the exit code is 1.
stdlib only (no f-strings: the container Python may be old).
"""
import itertools
import json
import random
import sys

SEED = 12713
N_FUZZ = 100000


# --- pure region of model.py, copied as plain functions -----------------------

def key_component():
    # The option-name token for the presentation component.
    return 0


def default_primary():
    # Component identity selected by the highest-priority name-membership test.
    return 1


def default_secondary():
    # Component identity selected by the second-priority name-membership test.
    return 2


def default_tertiary():
    # Component identity selected by the third-priority name-membership test.
    return 3


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def select_component(options, component_present, test_primary,
                     test_secondary, test_tertiary):
    if not (key_component() in options):
        if test_primary:
            options[key_component()] = default_primary()
        elif test_secondary:
            options[key_component()] = default_secondary()
        elif test_tertiary:
            options[key_component()] = default_tertiary()


# --- oracle plumbing -----------------------------------------------------------

def build_oracle():
    """Configure Django minimally, build the reusable admin object and the
    widget classes used for lowering. Returns (admin_obj, widget_classes)."""
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
                "django.contrib.admin",
            ],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
        )
    django.setup()

    from django.contrib import admin
    from django.contrib.admin.sites import AdminSite
    from django.contrib.admin.widgets import (
        AutocompleteSelectMultiple, ManyToManyRawIdWidget,
        FilteredSelectMultiple)
    from django.db import models

    class Host(models.Model):
        class Meta:
            app_label = "contenttypes"

    site = AdminSite()          # empty registry: no downstream queryset default
    admin_obj = admin.ModelAdmin(Host, site)
    return admin_obj, (AutocompleteSelectMultiple, ManyToManyRawIdWidget,
                       FilteredSelectMultiple)


class StubRemote(object):
    """Relation descriptor stub: enough structure for the method's early
    intermediary-model check and for the widget constructors (which only
    store the relation)."""
    class _Through(object):
        class _meta(object):
            auto_created = True
    through = _Through()
    model = object          # registry lookup key; the registry is empty


class StubField(object):
    """Multi-valued relation field stub. Records the keyword options the
    method forwards to ``formfield`` -- the observation point for the
    modeled selection block."""

    def __init__(self, name):
        self.name = name
        self.verbose_name = name
        self.remote_field = StubRemote()
        self.captured = None

    def formfield(self, **kwargs):
        self.captured = dict(kwargs)

        class _FF(object):
            widget = object()       # not a multi-select: skips help-text step
        return _FF()


class Opaque(object):
    """A caller-supplied component/value carrier with plain object identity."""
    __slots__ = ()


REL_NAME = "relname"


def drive_oracle(admin_obj, widget_classes, options, test_primary,
                 test_secondary, test_tertiary, tertiary_channel):
    """Lift one abstract input, run the REAL patched method, lower the
    forwarded keyword options back to the Dict[int,int] carrier.
    tertiary_channel in ('vertical', 'horizontal', 'both')."""
    auto_cls, rawid_cls, filtered_cls = widget_classes

    admin_obj.autocomplete_fields = [REL_NAME] if test_primary else []
    admin_obj.raw_id_fields = [REL_NAME] if test_secondary else []
    if test_tertiary:
        admin_obj.filter_vertical = (
            [REL_NAME] if tertiary_channel in ("vertical", "both") else [])
        admin_obj.filter_horizontal = (
            [REL_NAME] if tertiary_channel in ("horizontal", "both") else [])
    else:
        admin_obj.filter_vertical = []
        admin_obj.filter_horizontal = []

    # Lift: token key 0 -> 'widget'; nonzero token k -> 'opt<k>'. Every value
    # token is realised as a fresh object registered by identity; a caller
    # component whose token collides with a name-derived default (1/2/3) is
    # realised as an instance of that widget class so type-based lowering of
    # a genuinely-new default cannot be confused with identity preservation.
    ident = {}                     # id(obj) -> value token

    def lift_value(tok):
        if tok == default_primary():
            obj = auto_cls.__new__(auto_cls)
        elif tok == default_secondary():
            obj = rawid_cls.__new__(rawid_cls)
        elif tok == default_tertiary():
            obj = filtered_cls.__new__(filtered_cls)
        else:
            obj = Opaque()
        ident[id(obj)] = tok
        return obj

    kwargs = {}
    for k, v in options.items():
        key = "widget" if k == key_component() else "opt%d" % k
        kwargs[key] = lift_value(v)

    field = StubField(REL_NAME)
    admin_obj.formfield_for_manytomany(field, None, **kwargs)
    if field.captured is None:
        return None, "oracle never reached the observation point"

    # Lower the forwarded mapping back to the Dict[int,int] carrier.
    lowered = {}
    for key, obj in field.captured.items():
        if key == "widget":
            k = key_component()
        elif key.startswith("opt"):
            k = int(key[3:])
        else:
            return None, "oracle forwarded an unexpected option name %r" % key
        if id(obj) in ident:
            lowered[k] = ident[id(obj)]
        elif isinstance(obj, auto_cls):
            lowered[k] = default_primary()
        elif isinstance(obj, rawid_cls):
            lowered[k] = default_secondary()
        elif isinstance(obj, filtered_cls):
            lowered[k] = default_tertiary()
        else:
            return None, "oracle stored an unrecognized value under %r" % key
    return lowered, None


def check_one(admin_obj, widget_classes, options, tp, ts, tt, channel):
    """Run shadow and oracle on one abstract input; return an error string on
    any disagreement, else None."""
    shadow_opts = dict(options)
    component_present = key_component() in shadow_opts   # pins the Requires
    select_component(shadow_opts, component_present, tp, ts, tt)

    lowered, err = drive_oracle(admin_obj, widget_classes, dict(options),
                                tp, ts, tt, channel)
    if err is not None:
        return ("ORACLE BRIDGE ERROR on options=%r tests=(%r,%r,%r) "
                "channel=%r: %s" % (options, tp, ts, tt, channel, err))
    if lowered != shadow_opts:
        return ("DISAGREEMENT on options=%r tests=(%r,%r,%r) channel=%r:\n"
                "  shadow (impl region)          = %r\n"
                "  real (patched selection block) = %r"
                % (options, tp, ts, tt, channel, shadow_opts, lowered))
    return None


def boundary_cases():
    """(options, tp, ts, tt, channel) tuples covering the discriminating
    boundary: entry component present (distinct from / colliding with each
    name-derived identity), absent, alongside unrelated options, under every
    flag combination and every tertiary channel."""
    K = key_component()
    entry_maps = [
        {},                                   # no caller component
        {K: 7},                               # caller component, distinct id
        {K: default_primary()},               # caller id == a default id
        {K: default_secondary()},
        {K: default_tertiary()},
        {K: 7, 5: 50},                        # component + unrelated option
        {5: 50, 6: 60},                       # only unrelated options
    ]
    cases = []
    for base in entry_maps:
        for (tp, ts, tt) in itertools.product([False, True], repeat=3):
            channels = ("vertical", "horizontal", "both") if tt else ("vertical",)
            for ch in channels:
                cases.append((dict(base), tp, ts, tt, ch))
    # a caller component alongside only the third-priority test firing, on
    # both tertiary channels (the scenario the fix's precedence guarantee
    # protects), and a many-option map
    cases.append(({K: 9, 1: 11, 2: 12}, False, False, True, "vertical"))
    cases.append(({K: 9}, False, False, True, "horizontal"))
    cases.append(({3: 30, 4: 40, 5: 50, 6: 60}, True, True, True, "both"))
    return cases


def main():
    try:
        admin_obj, widget_classes = build_oracle()
    except Exception as exc:
        print("G-CONF ERROR: could not build the oracle: %r" % (exc,))
        return 1

    checked = 0
    boundary = boundary_cases()
    for options, tp, ts, tt, ch in boundary:
        err = check_one(admin_obj, widget_classes, options, tp, ts, tt, ch)
        if err:
            print(err)
            return 1
        checked += 1

    rng = random.Random(SEED)
    channels = ("vertical", "horizontal", "both")
    for _ in range(N_FUZZ):
        options = {}
        if rng.getrandbits(1):
            options[key_component()] = rng.randint(-5, 12)
        for _ in range(rng.randint(0, 4)):
            options[rng.randint(1, 20)] = rng.randint(-5, 50)
        tp = bool(rng.getrandbits(1))
        ts = bool(rng.getrandbits(1))
        tt = bool(rng.getrandbits(1))
        ch = channels[rng.randrange(3)]
        err = check_one(admin_obj, widget_classes, options, tp, ts, tt, ch)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched formfield_for_manytomany "
          "selection block on %d inputs (%d boundary + %d fuzz, seed %d); "
          "0 disagreements." % (checked, len(boundary), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
