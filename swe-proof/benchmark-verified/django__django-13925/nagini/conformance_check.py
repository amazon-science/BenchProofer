#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13925 (nagini).

SHADOW: the impl region of model.py's `check_default_pk`, copied verbatim
below with the contract calls (Requires/Ensures) stripped, together with the
model's `PkField` record (contract calls stripped) and the @Pure helpers
(`reuses_ancestor_declared_key`, `advisory_warranted`) copied over as plain
functions. There are no @ContractOnly callees in this bundle and no PSeq use.

ORACLE: the REAL patched repo classmethod the model models per mapping.md —
`django.db.models.base.Model._check_default_pk` — imported from /testbed with
the gold patch already applied by the gate (this script applies nothing).

Type bridge (mapping.md section 2): the model carries the pk descriptor as a
record of three booleans and the two configuration reads as parameters; the
returned advisory list is carried as an int count. Concretely each 5-tuple of
booleans is realised as genuine Django state and the count is read back off
the real call:

  * auto                  -> `cls._meta.pk.auto_created` (set per input)
  * reuses_ancestor_key_a -> WHICH model class is checked: a model whose pk is
                             the auto-built one-to-one link to a concrete
                             parent (flag True: isinstance test holds) vs a
                             model with a plain auto pk (flag False). When the
                             flag is False the real code never consults flag B
                             (short-circuit), matching the model where the
                             conjunction guards B.
  * reuses_ancestor_key_b -> `cls._meta.pk.remote_field.parent_link` (set per
                             input on the one-to-one pk)
  * setting_overridden    -> run phase: inputs are partitioned and the True
                             half runs under override_settings so
                             `settings.is_overridden(...)` reports True
  * appconfig_overridden  -> WHICH app owns the model: a synthetic app config
                             that sets `default_auto_field` (property
                             `_is_default_auto_field_overridden` True) vs one
                             that does not
  * return int (0/1)      -> `len(cls._check_default_pk())`; when 1 the single
                             advisory's id is additionally asserted so the
                             count abstraction is anchored to the modeled
                             advisory and not some other check output.

Input domain: the preconditions demand only readable fields, i.e. all 2**5
boolean assignments are Requires-satisfying. Boundary = the FULL 32-row truth
table (exhaustive); fuzz = 100000 additional pinned-seed random assignments
(each realised and executed against the real callee, so the differential run
exceeds 1e5 real observations as the contract requires even though the
abstract domain is finite). Pinned fuzz seed: 139250.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + the in-image Django under test only.
"""
import json
import random
import sys

SEED = 139250
N_FUZZ = 100000


# --- the model's record type (contract calls stripped) -----------------------

class PkField:
    """The touched fields of the model's primary-key field descriptor."""

    def __init__(self, auto, reuses_ancestor_key_a, reuses_ancestor_key_b):
        self.auto = auto                                  # key was created automatically
        self.reuses_ancestor_key_a = reuses_ancestor_key_a  # ancestor-key reuse, part A
        self.reuses_ancestor_key_b = reuses_ancestor_key_b  # ancestor-key reuse, part B


# --- @Pure helpers from model.py, copied as plain functions -------------------

def reuses_ancestor_declared_key(auto, reuses_ancestor_key_a,
                                 reuses_ancestor_key_b):
    return reuses_ancestor_key_a and reuses_ancestor_key_b


def advisory_warranted(auto, reuses_ancestor_key_a, reuses_ancestor_key_b,
                       setting_overridden, appconfig_overridden):
    return (
        auto and
        not reuses_ancestor_declared_key(auto, reuses_ancestor_key_a,
                                         reuses_ancestor_key_b) and
        not setting_overridden and
        not appconfig_overridden
    )


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def check_default_pk(pk, setting_overridden, appconfig_overridden):
    if (
        pk.auto and
        not (pk.reuses_ancestor_key_a and pk.reuses_ancestor_key_b) and
        not setting_overridden and
        not appconfig_overridden
    ):
        return 1
    return 0


# --- oracle plumbing -----------------------------------------------------------

def build_oracle():
    """Configure Django, register two synthetic app configs (one with the
    per-app default-auto-field attribute set, one without), and define in each
    a model with a plain auto pk and a child model whose pk is the auto-built
    one-to-one parent link. Returns a dict keyed by
    (reuses_ancestor_key_a, appconfig_overridden) -> model class."""
    import types

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

    from django.apps import apps, AppConfig
    from django.db import models

    plain_mod = types.ModuleType("conf_app_plain")
    over_mod = types.ModuleType("conf_app_over")
    sys.modules["conf_app_plain"] = plain_mod
    sys.modules["conf_app_over"] = over_mod

    class PlainCfg(AppConfig):
        # app-level default-auto-field NOT configured
        name = "conf_app_plain"
        label = "conf_app_plain"
        path = "/tmp"

    class OverCfg(AppConfig):
        # app-level default-auto-field configured
        name = "conf_app_over"
        label = "conf_app_over"
        path = "/tmp"
        default_auto_field = "django.db.models.AutoField"

    pc = PlainCfg("conf_app_plain", plain_mod)
    oc = OverCfg("conf_app_over", over_mod)
    for cfg in (pc, oc):
        cfg.models = {}
        cfg.apps = apps
    apps.app_configs["conf_app_plain"] = pc
    apps.app_configs["conf_app_over"] = oc
    assert pc._is_default_auto_field_overridden is False
    assert oc._is_default_auto_field_overridden is True

    class PlainA(models.Model):          # plain auto pk, app not configured
        class Meta:
            app_label = "conf_app_plain"

    class ChildA(PlainA):                # inherited one-to-one parent-link pk
        class Meta:
            app_label = "conf_app_plain"

    class PlainB(models.Model):          # plain auto pk, app configured
        class Meta:
            app_label = "conf_app_over"

    class ChildB(PlainB):                # inherited one-to-one parent-link pk
        class Meta:
            app_label = "conf_app_over"

    # sanity: the pk shapes are what the bridge assumes
    assert PlainA._meta.pk.remote_field is None
    assert ChildA._meta.pk.remote_field is not None
    assert ChildA._meta.pk.remote_field.parent_link is True

    return {
        (False, False): PlainA,
        (False, True): PlainB,
        (True, False): ChildA,
        (True, True): ChildB,
    }


def real_count(model_pool, auto, key_a, key_b, appcfg_ov):
    """Realise one boolean assignment as Django state and read the real
    check's advisory count. `setting_overridden` is realised by the caller's
    run phase (override_settings entered around the True half)."""
    cls = model_pool[(key_a, appcfg_ov)]
    pk = cls._meta.pk
    old_auto = pk.auto_created
    pk.auto_created = auto
    old_pl = None
    if pk.remote_field is not None:
        old_pl = pk.remote_field.parent_link
        pk.remote_field.parent_link = key_b
    try:
        warnings = cls._check_default_pk()
    finally:
        pk.auto_created = old_auto
        if pk.remote_field is not None:
            pk.remote_field.parent_link = old_pl
    n = len(warnings)
    if n == 1:
        # anchor the count abstraction: the one advisory is the modeled one
        assert warnings[0].id == "models.W042", warnings[0].id
    return n


def check_one(model_pool, auto, key_a, key_b, setting_ov, appcfg_ov):
    """Drive the shadow and the real callee on one assignment; return an
    error string on disagreement, else None."""
    shadow = check_default_pk(PkField(auto, key_a, key_b),
                              setting_ov, appcfg_ov)
    real = real_count(model_pool, auto, key_a, key_b, appcfg_ov)
    if shadow != real:
        return ("DISAGREEMENT on (auto=%r, reuses_a=%r, reuses_b=%r, "
                "setting_ov=%r, appcfg_ov=%r):\n"
                "  shadow (impl region) = %r\n"
                "  real (patched _check_default_pk) advisory count = %r"
                % (auto, key_a, key_b, setting_ov, appcfg_ov, shadow, real))
    # internal cross-check: the executable impl agrees with the pure predicate
    expected = 1 if advisory_warranted(auto, key_a, key_b,
                                       setting_ov, appcfg_ov) else 0
    if shadow != expected:
        return ("INTERNAL: impl region and pure predicate disagree on "
                "(auto=%r, reuses_a=%r, reuses_b=%r, setting_ov=%r, "
                "appcfg_ov=%r)" % (auto, key_a, key_b, setting_ov, appcfg_ov))
    return None


def main():
    try:
        import django  # noqa: F401
    except ImportError as exc:  # pragma: no cover - environment guard
        print("G-CONF ERROR: Django not importable: %r" % (exc,))
        return 1

    model_pool = build_oracle()
    from django.conf import settings
    from django.test.utils import override_settings
    assert settings.is_overridden("DEFAULT_AUTO_FIELD") is False

    import itertools
    inputs = [bits for bits in itertools.product([False, True], repeat=5)]
    n_boundary = len(inputs)  # the full truth table, exhaustive

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        inputs.append(tuple(rng.random() < 0.5 for _ in range(5)))

    # partition by setting_overridden so the settings override is entered once
    phase_false = [t for t in inputs if not t[3]]
    phase_true = [t for t in inputs if t[3]]

    checked = 0
    for auto, key_a, key_b, setting_ov, appcfg_ov in phase_false:
        err = check_one(model_pool, auto, key_a, key_b, setting_ov, appcfg_ov)
        if err:
            print(err)
            return 1
        checked += 1

    with override_settings(DEFAULT_AUTO_FIELD="django.db.models.AutoField"):
        assert settings.is_overridden("DEFAULT_AUTO_FIELD") is True
        for auto, key_a, key_b, setting_ov, appcfg_ov in phase_true:
            err = check_one(model_pool, auto, key_a, key_b,
                            setting_ov, appcfg_ov)
            if err:
                print(err)
                return 1
            checked += 1

    print("G-CONF OK: shadow impl == real patched _check_default_pk advisory "
          "count on %d realised inputs (%d exhaustive truth-table rows + %d "
          "fuzz, seed %d); 0 disagreements."
          % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
