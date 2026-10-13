#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-11141 (nagini).

SHADOW: the impl region of model.py, copied VERBATIM below with the contract
calls stripped (Requires/Ensures lines removed; the impl body itself carries
no contract calls), plus the @Pure helper `migrated_code` copied over as a
plain function. The model's `List[int]` carrier for the discovered-name
collection is a plain Python list of ints here (only its length is observed).

ORACLE: the REAL patched repo function the model models per mapping.md --
the per-application classification inside
`django.db.migrations.loader.MigrationLoader.load_disk` -- imported from
/testbed (the gate applies patch.diff before this script runs;
PYTHONPATH=/testbed). The classification for one synthetic application is
isolated by monkeypatching the module-level callees load_disk uses
(`apps.get_app_configs`, `import_module`, `pkgutil.iter_modules`,
`MigrationLoader.migrations_module`), exactly as this instance's lean/velvet
sibling checks do. The observed outcome is membership of the app label in
`loader.migrated_apps` (result 1) vs `loader.unmigrated_apps` (result 0).

Type bridge (mapping.md section 2):
  has_regular_file_marker : bool <-> the imported module has a non-None
                                     `__file__` attribute (True) vs an
                                     implicit namespace package (False)
  exposes_search_path : bool     <-> the module exposes `__path__`
  treat_empty_as_migrated : bool <-> loader.ignore_no_migrations
  migration_names : List[int]    <-> the discovered, already-filtered
                                     migration-name set; the carrier is a
                                     list of ints whose len() mirrors the
                                     set's cardinality (element identity is
                                     irrelevant to the modeled decision)
  Result() in {0,1}              <-> unmigrated_apps (0) / migrated_apps (1)

The name-discovery step (iterate the search path, keep non-package entries
whose names do not start with '_' or '~', dedupe as a set) is identical pre-
and post-patch (mapping.md section 3, kind I); the bridge re-derives the
filtered cardinality from the raw fuzzed entries with that same rule so the
shadow's input matches what the oracle's discovery actually produces.

Input domain: the model's Requires places only an access permission on the
carrier list, so every (bool, bool, list-of-ints, bool) tuple is
Requires-satisfying. Boundary cases enumerate all flag combinations x a
fixed battery of entry lists (empty, one valid name, only filtered-out
names, only package entries, duplicates, many); fuzz draws random entry
lists over mixed valid / underscore- or tilde-prefixed / package entries.

>= 1e5 Requires-satisfying inputs: boundary battery + 100000 fuzz.
Pinned fuzz seed: 11141.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outcomes and exits 1. stdlib + django (the repo under test) only.
"""
import json
import random
import sys
import types

# --- configure Django settings before importing the migrations machinery ----
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=False, USE_TZ=False, USE_L10N=False, DATABASES={},
        INSTALLED_APPS=[], USE_I18N=False,
    )
    django.setup()

from django.db.migrations import loader as loader_mod
from django.db.migrations.loader import MigrationLoader

SEED = 11141
N_FUZZ = 100_000

LABEL = "synthlabel"
MODULE_NAME = "synthetic.migrations"


# --- pure helper from model.py, decorator stripped ---------------------------

def migrated_code(exposes_search_path, discovered_file_count,
                  treat_empty_as_migrated):
    if exposes_search_path and (discovered_file_count > 0 or
                                treat_empty_as_migrated):
        return 1
    return 0


# --- the impl region of model.py, verbatim (contracts stripped) --------------

def is_migrated_app(
    has_regular_file_marker,
    exposes_search_path,
    migration_names,
    treat_empty_as_migrated,
):
    # impl-start
    if not exposes_search_path:
        return 0
    if len(migration_names) > 0 or treat_empty_as_migrated:
        return 1
    return 0
    # impl-end


# --- bridge: raw directory entries -> the model's discovered-name carrier ----

def discovered_count(entries):
    """Cardinality of the discovered-name set for the raw (name, is_pkg)
    entries: keep non-package entries whose name does not start with '_' or
    '~', deduped. This discovery rule is identical pre- and post-patch
    (mapping.md section 3, kind I), so re-deriving it here only aligns the
    shadow's input with what the oracle's own discovery step produces."""
    return len({nm for (nm, is_pkg) in entries
                if not is_pkg and nm[0] != "_" and nm[0] != "~"})


# --- fakes to drive the REAL load_disk ---------------------------------------

class FakeAppConfig:
    def __init__(self, label):
        self.label = label


class FakeMigration:
    def __init__(self, name, app_label):
        self.name = name
        self.app_label = app_label


def make_package_module(has_file, has_path):
    m = types.ModuleType(MODULE_NAME)
    if has_file:
        m.__file__ = "/synthetic/migrations/__init__.py"
    elif hasattr(m, "__file__"):
        # implicit namespace package: no __file__ attribute at all
        del m.__file__
    if has_path:
        m.__path__ = ["/synthetic/migrations"]
    elif hasattr(m, "__path__"):
        del m.__path__
    return m


def oracle(has_file, has_path, ignore_no_migrations, entries):
    """Run the REAL patched load_disk on one synthetic app and read back its
    classification: 1 iff the label lands in migrated_apps, 0 iff it lands in
    unmigrated_apps."""
    pkg_module = make_package_module(has_file, has_path)

    def fake_get_app_configs():
        return [FakeAppConfig(LABEL)]

    def fake_migrations_module(self, app_label):
        return MODULE_NAME, False

    def fake_import_module(name):
        if name == MODULE_NAME:
            return pkg_module
        # a discovered migration submodule: expose a Migration class
        sub = types.ModuleType(name)
        sub.Migration = FakeMigration
        return sub

    def fake_iter_modules(path):
        # path is module.__path__; yield (module_finder, name, is_pkg)
        for (nm, is_pkg) in entries:
            yield (None, nm, bool(is_pkg))

    orig_get = loader_mod.apps.get_app_configs
    orig_mig = MigrationLoader.migrations_module
    orig_imp = loader_mod.import_module
    orig_iter = loader_mod.pkgutil.iter_modules
    try:
        loader_mod.apps.get_app_configs = fake_get_app_configs
        MigrationLoader.migrations_module = fake_migrations_module
        loader_mod.import_module = fake_import_module
        loader_mod.pkgutil.iter_modules = fake_iter_modules

        ldr = MigrationLoader(connection=None, load=False,
                              ignore_no_migrations=ignore_no_migrations)
        ldr.load_disk()
        in_migrated = LABEL in ldr.migrated_apps
        in_unmigrated = LABEL in ldr.unmigrated_apps
        if in_migrated == in_unmigrated:
            raise AssertionError(
                "oracle classification not single-valued: migrated=%r "
                "unmigrated=%r" % (in_migrated, in_unmigrated))
        return 1 if in_migrated else 0
    finally:
        loader_mod.apps.get_app_configs = orig_get
        MigrationLoader.migrations_module = orig_mig
        loader_mod.import_module = orig_imp
        loader_mod.pkgutil.iter_modules = orig_iter


def check_case(has_file, has_path, ignore, entries):
    real = oracle(has_file, has_path, ignore, entries)
    # Bridge to the model carrier: the already-filtered discovered-name
    # collection as a list of ints with the matching cardinality.
    names_carrier = list(range(discovered_count(entries)))
    shadow = is_migrated_app(has_file, has_path, names_carrier, ignore)
    if shadow != real:
        return ("DISAGREEMENT\n"
                "  has_regular_file_marker=%r exposes_search_path=%r\n"
                "  treat_empty_as_migrated=%r entries=%r\n"
                "  carrier_len=%d\n  shadow=%r real=%r"
                % (has_file, has_path, ignore, entries,
                   len(names_carrier), shadow, real))
    return None


# --- input generation ---------------------------------------------------------

# The real discovery never yields an empty entry name and indexes name[0],
# so an empty name is outside the discovery domain and is not generated.
_NAMES = ["0001_initial", "0002_auto", "name", "_private", "~tmp", "abc",
          "_", "~", "0003_x", "sub", "9_z", "z"]

_BOUNDARY_ENTRY_SETS = [
    [],                                          # nothing on the search path
    [("0001_initial", False)],                   # one discovered name
    [("_private", False), ("~tmp", False)],      # only filtered-out names
    [("pkg", True), ("sub", True)],              # only package entries
    [("0001_initial", False), ("0001_initial", False)],  # duplicates
    [("0001_initial", False), ("0002_auto", False), ("_x", False),
     ("pkg", True), ("~t", False), ("0003_x", False)],   # mixed, many
]


def rand_entries(rng):
    return [(rng.choice(_NAMES), rng.random() < 0.3)
            for _ in range(rng.randint(0, 6))]


def main():
    checked = 0

    # Boundary battery: all 8 flag combinations x the fixed entry sets.
    n_boundary = 0
    for has_file in (False, True):
        for has_path in (False, True):
            for ignore in (False, True):
                for entries in _BOUNDARY_ENTRY_SETS:
                    err = check_case(has_file, has_path, ignore, entries)
                    if err:
                        print(err)
                        return 1
                    checked += 1
                    n_boundary += 1

    rng = random.Random(SEED)  # pinned seed
    for _ in range(N_FUZZ):
        has_file = rng.random() < 0.5
        has_path = rng.random() < 0.85   # bias toward the package case
        ignore = rng.random() < 0.5
        err = check_case(has_file, has_path, ignore, rand_entries(rng))
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real per-app classification on %d "
          "inputs (%d boundary + %d fuzz, seed %d), 0 disagreements."
          % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
