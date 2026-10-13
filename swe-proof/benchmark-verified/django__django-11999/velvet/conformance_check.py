#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-11999 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region (`registerAccessor`
              / the pure `registerDisplay`) transliterated to Python over the real
              repo carrier. The modeled operation is the registration step of
              `Field.contribute_to_class`: install the auto-generated accessor at
              `key = 'get_%s_display' % field.name` ONLY if `key` is currently
              free in the class namespace; otherwise leave the existing binding
              untouched. Per the mapping.md bijection a namespace is a name ->
              identity-kind partial map (`0` = a user-supplied accessor, `1` = the
              auto-generated `partialmethod`). The shadow computes the resulting
              identity-kind at `key` purely from the input carrier (was an
              override present before the step?), exactly as `registerDisplay`
              does. No A-tagged callee appears, so this shadow is pure R/I.

  * ORACLE  — `patch.diff`'s behaviour: the real `Field.contribute_to_class`
              run by Django's metaclass (`ModelBase.__new__`) at base_commit with
              the gold patch applied (the harness applies patch.diff before this
              runs). The observable is the identity-kind of the accessor the built
              class actually exposes at `key` along its MRO.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + Django only.
The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys
from functools import partialmethod

SEED = 11999
N_FUZZ = 100_000

# Three observable configurations of the class-namespace BEFORE the registration
# step runs (mapping.md): whether the field's choices accessor name is already
# bound, and where.
#   "none"    : no user-defined get_<name>_display  -> key is free
#   "same"    : the model body defines get_<name>_display -> key bound (kind 0)
#   "inherit" : a parent model defines it           -> key bound via MRO (kind 0)
CONFIGS = ("none", "same", "inherit")

USER_KIND = 0   # a user-supplied accessor
AUTO_KIND = 1   # the auto-generated partialmethod


def setup_django():
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
        )
    django.setup()


# --- the R/I shadow: registerDisplay, transliterated -------------------------
def shadow_kind(config):
    """The identity-kind `registerDisplay` installs at `key`, computed from the
    input carrier alone. Input namespace before the step:
        lookup(key) = none           if config == "none"   (key free)
        lookup(key) = some USER_KIND otherwise              (override present)
    The generated accessor token is gen = AUTO_KIND. registerDisplay:
        if (lookup key).isNone then bind gen  else keep the existing binding.
    """
    override_present = config in ("same", "inherit")
    lookup_key = USER_KIND if override_present else None
    if lookup_key is None:           # (lookup key).isNone
        return AUTO_KIND             # install the generated accessor
    else:
        return lookup_key            # keep what is already bound


# --- the oracle: the real patched Field.contribute_to_class ------------------
def _make_model(idx, config, fname):
    from django.db import models
    from django.apps import apps

    disp = "get_%s_display" % fname
    module = "django.contrib.contenttypes.models"

    def user_accessor(self):
        return "user-defined"

    base = models.Model
    if config == "inherit":
        parent_attrs = {
            "__module__": module,
            "Meta": type("Meta", (), {"app_label": "contenttypes", "abstract": True}),
            disp: user_accessor,
        }
        base = type("P%d" % idx, (models.Model,), parent_attrs)

    attrs = {
        "__module__": module,
        "Meta": type("Meta", (), {"app_label": "contenttypes"}),
        fname: models.IntegerField(choices=[(1, "foo"), (2, "bar")]),
    }
    if config == "same":
        attrs[disp] = user_accessor

    cls = type("M%d" % idx, (base,), attrs)
    return cls, disp


def oracle_kind(idx, config, fname):
    """Identity-kind the real built class exposes at `key` along its MRO."""
    cls, disp = _make_model(idx, config, fname)
    owner = None
    for k in cls.__mro__:
        if disp in k.__dict__:
            owner = k.__dict__[disp]
            break
    if owner is None:
        return None  # nothing bound (should not happen for a choices field)
    return AUTO_KIND if isinstance(owner, partialmethod) else USER_KIND


def _clear_registry():
    from django.apps import apps
    apps.all_models["contenttypes"].clear()
    apps.clear_cache()


def fuzz_inputs(n, rng):
    # boundary cases first (plan §4.1 step 4): each config with a simple name.
    for cfg in CONFIGS:
        yield (cfg, "foo")
    # the exact F2P scenario: a model that supplies its own get_foo_bar_display.
    yield ("same", "foo_bar")
    # assorted field names (the accessor name is derived from the field name).
    names = ["foo", "bar", "foo_bar", "status", "x", "value", "a1", "type_code"]
    for _ in range(n):
        cfg = rng.choice(CONFIGS)
        fname = rng.choice(names)
        yield (cfg, fname)


def main():
    try:
        setup_django()
    except Exception as e:  # pragma: no cover
        print("G-CONF SETUP-FAIL %r" % e)
        return 1

    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for cfg, fname in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_kind(cfg)
        try:
            oracle = oracle_kind(count, cfg, fname)
        finally:
            _clear_registry()
        if shadow != oracle:
            disagreements.append((cfg, fname, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for cfg, fname, sh, orc in disagreements:
            print("  config=%r field=%r shadow_kind=%r oracle_kind=%r"
                  % (cfg, fname, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of registerAccessor agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
