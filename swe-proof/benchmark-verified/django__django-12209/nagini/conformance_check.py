#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-12209 (nagini).

SHADOW: the impl region of model.py `store_single_table`, copied verbatim
below with the contract calls stripped; the @Pure helpers exist only in the
specification layer and are not called by the impl. The one @ContractOnly
callee, `update_matched_row`, calls the REAL repo function: it is passed in
as a closure that invokes the real ``Model._do_update`` (the unchanged
UPDATE primitive) against the live sqlite database for the same instance
identifier the oracle run uses.

ORACLE: the REAL patched repo routine the model models per mapping.md —
``django.db.models.base.Model._save_table``. The gate applies patch.diff to
/testbed before this script runs; PYTHONPATH=/testbed makes the patched
module importable. The routine is driven end-to-end on real model instances
over an in-memory sqlite database; only ``_do_insert`` — the INSERT fallback
BELOW the modeled decision, explicitly abstracted away per mapping.md
section 2 — is stubbed to a no-op so runs that reach it leave the database
unchanged. Everything the model covers (the short-cut guard, the effective
insertion decision, the update path with the real `_do_update`, the returned
`updated` flag) executes unmodified.

Type bridge (mapping.md section 2): five plain bools.
  pk_explicit    <-> the `raw` parameter (spec-view abstract name);
  force_insert   <-> the `force_insert` parameter;
  pk_set         <-> `pk_val is not None` after pk resolution;
  adding         <-> `self._state.adding` (set directly on the instance);
  pk_has_default <-> the pk field carries a generating default (realised by
                     two model classes: one with a uuid4-defaulted pk, one
                     with a plain CharField pk and no default).
Realizability: when the pk field has a generating default the repo always
resolves a pk value (pk_set is True); pk_set=False is therefore generated
only for the no-default class, matching the repo's own reachable states.
The axiom's value (whether a stored row matches the identifier) is
controlled by pre-inserting one persistent row per class and drawing the
instance identifier from {existing, absent}.

Input domain: Requires is True, so every realizable 6-tuple (raw,
force_insert, adding, pk_has_default, pk_set, row_exists) is
Requires-satisfying. Boundary: the full cross product of realizable
combinations. Fuzz: uniform draws until >= 1e5 checks. Pinned seed: 12209.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + django (the repo under test) only.
"""
import json
import random
import sys
import uuid

SEED = 12209
N_TARGET = 100000


# --- the impl region of model.py, verbatim, contract calls stripped ----------
# (update_matched_row is @ContractOnly: supplied as a closure onto the REAL
#  repo primitive, per the conformance contract.)

def store_single_table(pk_explicit, force_insert, pk_set, adding,
                       pk_has_default, update_matched_row):
    force_insert_eff = force_insert
    if (not pk_explicit) and (not force_insert) and adding and pk_has_default:
        force_insert_eff = True
    updated = False
    if pk_set and not force_insert_eff:
        updated = update_matched_row()
    return updated


# --- real Django environment ---------------------------------------------------

def setup_django():
    from django.conf import settings
    settings.configure(
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
        USE_TZ=False,
    )
    import django
    django.setup()


def main():
    setup_django()

    from django.db import connection, models
    from django.db.models.base import Model

    class PkWithDefault(models.Model):
        # pk field carries a generating default (pk_has_default = True)
        pk_field = models.UUIDField(primary_key=True, default=uuid.uuid4)
        data = models.IntegerField(default=0)

        class Meta:
            app_label = "contenttypes"

    class PkNoDefault(models.Model):
        # pk field with no generating default (pk_has_default = False)
        pk_field = models.CharField(primary_key=True, max_length=64)
        data = models.IntegerField(default=0)

        class Meta:
            app_label = "contenttypes"

    with connection.schema_editor() as editor:
        editor.create_model(PkWithDefault)
        editor.create_model(PkNoDefault)

    # one persistent stored row per class; a second identifier stays absent
    EXISTING = {
        PkWithDefault: uuid.UUID(int=1),
        PkNoDefault: "row-present",
    }
    ABSENT = {
        PkWithDefault: uuid.UUID(int=2),
        PkNoDefault: "row-absent",
    }
    PkWithDefault.objects.create(pk_field=EXISTING[PkWithDefault], data=7)
    PkNoDefault.objects.create(pk_field=EXISTING[PkNoDefault], data=7)

    # stub the INSERT fallback (below the modeled decision, abstracted away):
    # keeps every run side-effect free on the two persistent rows
    def stub_do_insert(self, manager, using, fields, returning_fields, raw):
        return []

    Model._do_insert = stub_do_insert

    def run_real(model_cls, raw, force_insert, adding, pk_value):
        """Drive the REAL patched _save_table; return the `updated` flag."""
        if pk_value is None:
            obj = model_cls(data=3)
            obj.pk = None  # ensure no resolved identifier (no-default class)
        else:
            obj = model_cls(pk_field=pk_value, data=3)
        obj._state.adding = adding
        obj._state.db = None
        return obj._save_table(raw=raw, cls=model_cls,
                               force_insert=force_insert)

    def make_axiom_callee(model_cls, pk_value):
        """The @ContractOnly callee bound to the REAL repo primitive: probes
        Model._do_update for this identifier (no non-pk values, so the
        primitive reports whether a stored row matches)."""
        def update_matched_row():
            probe = model_cls(pk_field=pk_value, data=3)
            base_qs = model_cls._base_manager.using("default")
            return probe._do_update(base_qs, "default", pk_value, [],
                                    None, False)
        return update_matched_row

    def check(model_cls, raw, force_insert, adding, pk_set, row_exists):
        pk_has_default = model_cls is PkWithDefault
        if pk_set:
            pk_value = EXISTING[model_cls] if row_exists else ABSENT[model_cls]
        else:
            pk_value = None
        shadow = store_single_table(
            raw, force_insert, pk_set, adding, pk_has_default,
            make_axiom_callee(model_cls, pk_value))
        try:
            real = run_real(model_cls, raw, force_insert, adding, pk_value)
        except Exception as e:
            return ("DISAGREEMENT on (cls=%s raw=%r force_insert=%r "
                    "adding=%r pk_set=%r row_exists=%r):\n"
                    "  shadow updated = %r\n  real routine raised %r"
                    % (model_cls.__name__, raw, force_insert, adding,
                       pk_set, row_exists, shadow, e))
        if bool(shadow) != bool(real):
            return ("DISAGREEMENT on (cls=%s raw=%r force_insert=%r "
                    "adding=%r pk_set=%r row_exists=%r):\n"
                    "  shadow updated = %r\n  real updated = %r"
                    % (model_cls.__name__, raw, force_insert, adding,
                       pk_set, row_exists, shadow, real))
        return None

    # realizable input space: with a defaulted pk the repo always resolves an
    # identifier, so pk_set=False occurs only for the no-default class
    def realizable():
        combos = []
        for model_cls in (PkWithDefault, PkNoDefault):
            pk_set_choices = [True] if model_cls is PkWithDefault \
                else [True, False]
            for raw in (False, True):
                for force_insert in (False, True):
                    for adding in (False, True):
                        for pk_set in pk_set_choices:
                            for row_exists in ((False, True) if pk_set
                                               else (False,)):
                                combos.append((model_cls, raw, force_insert,
                                               adding, pk_set, row_exists))
        return combos

    checked = 0
    combos = realizable()
    for combo in combos:
        err = check(*combo)
        if err:
            print(err)
            return 1
        checked += 1

    rng = random.Random(SEED)
    while checked < N_TARGET:
        combo = rng.choice(combos)
        err = check(*combo)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched _save_table decision on "
          "%d inputs (%d boundary combos, seed %d); 0 disagreements."
          % (checked, len(combos), SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
