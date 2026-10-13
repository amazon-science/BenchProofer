#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13820 (nagini).

SHADOW: the impl region of model.py, copied VERBATIM below with the contract
calls stripped (Requires/Ensures lines removed; the impl body itself carries
no contract calls). The @Pure helper `is_source` is copied over as a plain
function for reference; the impl does not call it. All carriers are plain
bools -- no PSeq shim is needed and there are no @ContractOnly callees.

ORACLE: the REAL patched repo behaviour the model models per mapping.md --
the per-module classification block inside
`django.db.migrations.loader.MigrationLoader.load_disk`, imported from
/testbed (the gate applies patch.diff before this script runs;
PYTHONPATH=/testbed; this script never applies any diff itself). The
classification for one synthetic application is isolated by monkeypatching
the module-level callees load_disk uses (`apps.get_app_configs`,
`import_module`, `pkgutil.iter_modules`, `MigrationLoader.migrations_module`),
the same driver pattern as the sibling bundle for this repo region. The
observed outcome is membership of the app label in `loader.migrated_apps`
(the module is a source to enumerate -> True) vs `loader.unmigrated_apps`
(the module is skipped -> False).

Type bridge (mapping.md section 2) -- each runtime introspection of the
imported module refines to one bool model input:

  is_package : bool             <-> the module exposes a `__path__`
                                    (child-search location) at all
  file_is_set : bool            <-> the module carries a non-None `__file__`
                                    (a recorded source-file location); False
                                    covers both an absent attribute and an
                                    explicit None value
  path_is_ordinary_list : bool  <-> the exposed `__path__` is a built-in list
                                    (vs. some other iterable carrier)
  Result() in {True, False}     <-> migrated_apps / unmigrated_apps outcome

Input domain: the model precondition pins `path_is_ordinary_list` to False
whenever `is_package` is False (a module with no child-search location has no
list-ness to speak of), leaving 6 faithful boolean combinations. Each
combination is realised by many concrete module shapes: `__file__` absent vs
explicitly None vs assorted path strings; `__path__` as lists of varying
contents vs several non-list iterable carriers (tuple, iterator, generator,
custom iterable object, str). Boundary battery enumerates every combination
x every representation variant; fuzz draws random shapes.

>= 1e5 Requires-satisfying inputs: boundary battery + 100000 fuzz.
Pinned fuzz seed: 138200.

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
        DEBUG=False, USE_TZ=False, DATABASES={}, INSTALLED_APPS=[],
        USE_I18N=False,
    )
    django.setup()

from django.db.migrations import loader as loader_mod
from django.db.migrations.loader import MigrationLoader

SEED = 138200
N_FUZZ = 100_000

LABEL = "synthlabel"
MODULE_NAME = "synthetic.migrations"


# --- pure helper from model.py, decorator stripped (reference only) ----------

def is_source(is_package, file_is_set, path_is_ordinary_list):
    return is_package and (file_is_set or path_is_ordinary_list)


# --- the impl region of model.py, verbatim (contracts stripped) --------------

def treat_as_migration_source(is_package, file_is_set, path_is_ordinary_list):
    # impl-start
    if not is_package:
        return False
    if (not file_is_set) and (not path_is_ordinary_list):
        return False
    return True
    # impl-end


# --- concrete module shapes realising the three boolean facts ----------------

class _CustomIterable:
    """A non-list iterable carrier for a child-search location."""

    def __init__(self, items):
        self._items = list(items)

    def __iter__(self):
        return iter(self._items)


def _gen(items):
    for it in items:
        yield it


# representation variants for file_is_set == False: absent attribute / None
_FILE_UNSET_VARIANTS = ["absent", "none"]
# representation variants for file_is_set == True
_FILE_SET_VARIANTS = [
    "/synthetic/migrations/__init__.py",
    "relative/pkg/__init__.py",
    "/x.py",
    "",  # empty string is still a non-None value
]
# list-shaped child-search locations (path_is_ordinary_list == True)
_LIST_PATH_MAKERS = [
    lambda: [],
    lambda: ["/synthetic/migrations"],
    lambda: ["/a", "/b", "/c"],
]
# non-list iterable child-search locations (path_is_ordinary_list == False)
_NONLIST_PATH_MAKERS = [
    lambda: ("/synthetic/migrations",),
    lambda: iter(["/synthetic/migrations"]),
    lambda: _gen(["/synthetic/migrations"]),
    lambda: _CustomIterable(["/synthetic/migrations"]),
    lambda: "/synthetic/migrations",
]


def make_module(is_package, file_variant, path_maker):
    """Build a module object realising the requested facts. file_variant is
    'absent' / 'none' / a string value; path_maker is None (no __path__) or a
    zero-arg callable producing the __path__ carrier."""
    m = types.ModuleType(MODULE_NAME)
    if file_variant == "absent":
        pass  # a fresh module object has no __file__ attribute
    elif file_variant == "none":
        m.__file__ = None
    else:
        m.__file__ = file_variant
    if is_package:
        m.__path__ = path_maker()
    return m


def observed_facts(module):
    """The three refined booleans, read off the module exactly as the model's
    abstraction defines them (mapping.md section 2)."""
    is_package = hasattr(module, "__path__")
    file_is_set = getattr(module, "__file__", None) is not None
    path_is_ordinary_list = is_package and isinstance(module.__path__, list)
    return is_package, file_is_set, path_is_ordinary_list


# --- drive the REAL load_disk on one synthetic app ---------------------------

class FakeAppConfig:
    def __init__(self, label):
        self.label = label


def oracle(module):
    """Run the REAL patched load_disk with `module` as the app's migrations
    module and read back the classification: True iff the label lands in
    migrated_apps (source to enumerate), False iff in unmigrated_apps."""

    def fake_get_app_configs():
        return [FakeAppConfig(LABEL)]

    def fake_migrations_module(self, app_label):
        return MODULE_NAME, False

    def fake_import_module(name):
        assert name == MODULE_NAME, "unexpected submodule import: %r" % name
        return module

    def fake_iter_modules(path):
        # No submodules discovered: keeps the run inside the classification
        # block's scope (discovery is out of scope for this model) and avoids
        # consuming one-shot iterable __path__ carriers.
        return iter(())

    orig_get = loader_mod.apps.get_app_configs
    orig_mig = MigrationLoader.migrations_module
    orig_imp = loader_mod.import_module
    orig_iter = loader_mod.pkgutil.iter_modules
    try:
        loader_mod.apps.get_app_configs = fake_get_app_configs
        MigrationLoader.migrations_module = fake_migrations_module
        loader_mod.import_module = fake_import_module
        loader_mod.pkgutil.iter_modules = fake_iter_modules

        ldr = MigrationLoader(connection=None, load=False)
        ldr.load_disk()
        in_migrated = LABEL in ldr.migrated_apps
        in_unmigrated = LABEL in ldr.unmigrated_apps
        if in_migrated == in_unmigrated:
            raise AssertionError(
                "oracle classification not single-valued: migrated=%r "
                "unmigrated=%r" % (in_migrated, in_unmigrated))
        return in_migrated
    finally:
        loader_mod.apps.get_app_configs = orig_get
        MigrationLoader.migrations_module = orig_mig
        loader_mod.import_module = orig_imp
        loader_mod.pkgutil.iter_modules = orig_iter


def check_case(is_package, file_variant, path_maker):
    module = make_module(is_package, file_variant, path_maker)
    facts = observed_facts(module)
    # The model precondition holds by construction for facts read off a real
    # module object: no __path__ means no list-ness.
    assert facts[0] or not facts[2]
    shadow = treat_as_migration_source(*facts)
    real = oracle(module)
    if shadow != real:
        return ("DISAGREEMENT\n"
                "  module shape: is_package=%r file_variant=%r "
                "path_carrier=%r\n"
                "  facts (is_package, file_is_set, path_is_ordinary_list)"
                "=%r\n  shadow=%r  real=%r"
                % (is_package, file_variant,
                   type(getattr(module, "__path__", None)).__name__,
                   facts, shadow, real))
    return None


def boundary_battery():
    """Every faithful boolean combination x every representation variant."""
    cases = []
    file_variants = _FILE_UNSET_VARIANTS + _FILE_SET_VARIANTS
    # non-package: no __path__ at all (list-ness vacuously False)
    for fv in file_variants:
        cases.append((False, fv, None))
    # package with a list __path__ / with each non-list carrier
    for fv in file_variants:
        for mk in _LIST_PATH_MAKERS:
            cases.append((True, fv, mk))
        for mk in _NONLIST_PATH_MAKERS:
            cases.append((True, fv, mk))
    return cases


def main():
    checked = 0

    n_boundary = 0
    for is_package, fv, mk in boundary_battery():
        err = check_case(is_package, fv, mk)
        if err:
            print(err)
            return 1
        checked += 1
        n_boundary += 1

    rng = random.Random(SEED)  # pinned seed
    for _ in range(N_FUZZ):
        is_package = rng.random() < 0.8   # bias toward the package case
        if rng.random() < 0.5:
            fv = rng.choice(_FILE_UNSET_VARIANTS)
        else:
            fv = rng.choice(_FILE_SET_VARIANTS)
        if is_package:
            if rng.random() < 0.5:
                mk = rng.choice(_LIST_PATH_MAKERS)
            else:
                mk = rng.choice(_NONLIST_PATH_MAKERS)
        else:
            mk = None
        err = check_case(is_package, fv, mk)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real per-module classification on %d "
          "inputs (%d boundary + %d fuzz, seed %d), 0 disagreements."
          % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
