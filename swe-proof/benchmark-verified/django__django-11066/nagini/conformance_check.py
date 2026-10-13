#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-11066 (nagini).

SHADOW: the impl region of model.py `persisted_db`, copied verbatim below
with the contract calls (Requires/Ensures/Invariant/Assert) stripped; the
@Pure helper `alias_eq` copies over as a plain function (PSeq equality ->
list equality). There are no @ContractOnly callees.

ORACLE: the REAL patched repo routine the model models per mapping.md — the
persist step of ``RenameContentType._rename``
(django/contrib/contenttypes/management/__init__.py). The gate applies
patch.diff to /testbed before this script runs; PYTHONPATH=/testbed makes
the patched module importable. The real ``_rename`` is driven end-to-end:
the row-retrieval boundary (outside the modeled persist step) is stubbed to
hand back a preset row object, the write-routing policy is a real
``ConnectionRouter`` router whose choice is the free input ``routed``, and
the resolved write-target alias is captured at the next UNCHANGED boundary
below the resolution — ``Model._save_table``'s ``using`` argument — so the
whole real control flow (the persist call, ``Model.save``,
``Model.save_base``'s ``using or router.db_for_write(...)`` resolution, the
atomic block) executes unmodified.

Type bridge (mapping.md section 2): a connection alias str <-> List[int] of
code points (alias[k] = ord(s[k])); the shadow's output list is decoded via
chr for the comparison. Alias equality is code-point-sequence equality on
both sides. Because a write target must be a configured connection, the
input domain is drawn from a fixed set of configured aliases of varied
shapes (including a non-ASCII one, exercising code-point fidelity); every
configured alias is a non-empty string, so len(db) > 0 and len(routed) > 0
hold for every generated pair, satisfying the model's Requires.

Input domain: all ordered pairs (db, routed) over the configured aliases as
boundary cases (equal pairs, differing pairs, 'default' on each side), then
uniform fuzz over pairs until >= 1e5 Requires-satisfying inputs are checked.
Pinned seed: 11066.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + django (the repo under test) only.
"""
import json
import random
import sys

SEED = 11066
N_TARGET = 100000


# --- the impl region of model.py, verbatim, contract calls stripped ----------

def alias_eq(a, b):
    return a == b


def persisted_db(db, routed):
    # using = explicit_alias or routing_policy_choice
    # An explicit alias is supplied (== db), so it is used directly; the
    # routing-policy fallback is reached only when no explicit alias is given.
    src = db if len(db) > 0 else routed  # type: List[int]
    # Copy the chosen alias into a fresh result carrier.
    target = []  # type: List[int]
    i = 0
    while i < len(src):
        target = target + [src[i]]
        i = i + 1
    return target


# --- bridge -------------------------------------------------------------------

def to_codes(s):
    return [ord(c) for c in s]


def from_codes(cs):
    return "".join(chr(c) for c in cs)


# --- real Django environment ---------------------------------------------------

ALIASES = [
    'default', 'other', 'extra', 'db1', 'replica', 'shard_07', 'a', 'z9',
    'alias_with_a_rather_long_name_0123456789', 'B', 'x_y', 'q8w7e6',
    'défaut',  # non-ASCII code points
]


def setup_django():
    from django.conf import settings
    settings.configure(
        DATABASES={
            alias: {'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': ':memory:'}
            for alias in ALIASES
        },
        DATABASE_ROUTERS=[],
        INSTALLED_APPS=['django.contrib.contenttypes'],
        USE_TZ=False,
    )
    import django
    django.setup()


class FixedRouter:
    """A write-routing policy with a fixed choice — the free input `routed`."""

    def __init__(self, choice):
        self.choice = choice

    def db_for_write(self, model, **hints):
        return self.choice


def main():
    setup_django()

    from django.db import connections, router
    from django.db.models.base import Model
    from django.contrib.contenttypes.management import RenameContentType
    from django.contrib.contenttypes.models import ContentType, \
        ContentTypeManager

    # --- capture at the unchanged boundary below the resolution --------------
    captured = []

    orig_save_table = Model._save_table

    def capture_save_table(self, raw=False, cls=None, force_insert=False,
                           force_update=False, using=None, update_fields=None):
        captured.append(using)
        return True  # report "row updated"; everything above ran for real

    Model._save_table = capture_save_table

    # --- stub the row-retrieval boundary (outside the modeled persist step) --
    state = {'row': None}

    def fake_get_by_natural_key(self, app_label, model):
        return state['row']

    ContentTypeManager.get_by_natural_key = fake_get_by_natural_key

    class _SchemaEditor:
        def __init__(self, alias):
            self.connection = connections[alias]

    from django.apps import apps as global_apps

    def real_persist_target(db_alias, routed_alias):
        """Run the REAL _rename persist step with step alias db_alias and a
        routing policy choosing routed_alias; return the alias the write was
        committed to (captured at _save_table)."""
        router.routers = [FixedRouter(routed_alias)]
        row = ContentType(id=1, app_label='someapp', model='oldname')
        state['row'] = row
        rct = RenameContentType('someapp', 'oldname', 'newname')
        del captured[:]
        rct._rename(global_apps, _SchemaEditor(db_alias), 'oldname', 'newname')
        if len(captured) != 1:
            raise RuntimeError("expected exactly one table write, saw %r"
                               % (captured,))
        return captured[0]

    # --- differential driver ---------------------------------------------------

    def check(db_alias, routed_alias):
        shadow_codes = persisted_db(to_codes(db_alias), to_codes(routed_alias))
        shadow_alias = from_codes(shadow_codes)
        try:
            real_alias = real_persist_target(db_alias, routed_alias)
        except Exception as e:
            return ("DISAGREEMENT on (db=%r, routed=%r):\n"
                    "  shadow persisted alias = %r\n"
                    "  real persist step raised %r"
                    % (db_alias, routed_alias, shadow_alias, e))
        if not alias_eq(shadow_codes, to_codes(real_alias)):
            return ("DISAGREEMENT on (db=%r, routed=%r):\n"
                    "  shadow persisted alias = %r\n"
                    "  real persisted alias = %r"
                    % (db_alias, routed_alias, shadow_alias, real_alias))
        return None

    checked = 0

    # boundary: every ordered pair over the configured aliases (equal pairs,
    # differing pairs, 'default' on either side all included)
    for db_alias in ALIASES:
        for routed_alias in ALIASES:
            err = check(db_alias, routed_alias)
            if err:
                print(err)
                return 1
            checked += 1

    # fuzz to >= 1e5 total
    rng = random.Random(SEED)
    while checked < N_TARGET:
        db_alias = rng.choice(ALIASES)
        routed_alias = rng.choice(ALIASES)
        err = check(db_alias, routed_alias)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched persist-step alias "
          "resolution on %d inputs (seed %d); 0 disagreements."
          % (checked, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
