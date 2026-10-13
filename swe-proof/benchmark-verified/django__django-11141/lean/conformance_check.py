#!/usr/bin/env python3
"""G-CONF for django__django-11141.

The gold patch is already applied to /testbed when this runs. We compare the
R/I Python shadow of `implementation_migration_module_status` (the Lean impl,
transliterated op-for-op per refinement.md) against the REAL patched
`MigrationLoader.load_disk` (django/db/migrations/loader.py) over >=1e5 fuzzed
inputs. Zero disagreements => exit 0.

`load_disk` walks every app config, imports its migrations package, decides
whether the app is migrated/unmigrated, and records the discovered migration
files. The fix concerns the per-app decision in the success branch:

  * an imported package is classified ONLY by whether it exposes a search path
    (`__path__`) and whether any migration file was discovered (or the
    ignore-no-migrations flag is set); the legacy `__file__` attribute is no
    longer consulted, so implicit namespace packages (no `__file__`) now load;
  * a package that exposes a path but yields no migration files (and no flag) is
    classified unmigrated, not migrated.

We isolate that decision by driving the REAL `load_disk` with one synthetic app
whose migrations package and discovered entries we control via monkeypatching
the module-level callees `load_disk` uses (`apps.get_app_configs`,
`import_module`, `pkgutil.iter_modules`, and `MigrationLoader.migrations_module`).

Type bijection (mapping.md):
  hasFile : Bool            <-> module has a non-None `__file__` attribute
  hasPath : Bool            <-> module exposes `__path__` (is a package)
  ignoreNoMigrations : Bool <-> loader.ignore_no_migrations
  entries : List(name,isPkg)<-> pkgutil.iter_modules(module.__path__) yield
  result.migrated           <-> app label in loader.migrated_apps
  result.names (as a set)   <-> {name for (label,name) in loader.disk_migrations}
                               (load_disk builds migration_names as a SET, so the
                                comparison is order-independent)

Exit 0 iff zero disagreements over >=1e5 fuzzed inputs. stdlib + django only.
"""
import os
import random
import sys
import types

# --- configure Django settings before importing the migrations machinery -----
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

LABEL = "migrations"
MODULE_NAME = "synthetic.migrations"


# --- shadow: R/I transliteration of implementation_migration_module_status ----
def valid_migration_name(name):
    if not name:
        return False
    c = name[0]
    return c != "_" and c != "~"


def filtered_names(entries):
    return [nm for (nm, is_pkg) in entries if (not is_pkg) and valid_migration_name(nm)]


def shadow(has_file, has_path, ignore_no_migrations, entries):
    """Mirror of the Lean impl: hasFile is deliberately not consulted."""
    if not has_path:
        return {"migrated": False, "names": []}
    names = []
    for (nm, is_pkg) in entries:
        if (not is_pkg) and valid_migration_name(nm):
            names.append(nm)
    migrated = (len(names) > 0) or ignore_no_migrations
    return {"migrated": migrated, "names": names}


# --- fakes to drive the REAL load_disk ----------------------------------------
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
    else:
        # implicit namespace package: no __file__ attribute at all
        if hasattr(m, "__file__"):
            del m.__file__
    if has_path:
        m.__path__ = ["/synthetic/migrations"]
    else:
        if hasattr(m, "__path__"):
            del m.__path__
    return m


def oracle(has_file, has_path, ignore_no_migrations, entries):
    """Run the REAL patched load_disk on one synthetic app and read back its
    classification + discovered file names."""
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
        migrated = LABEL in ldr.migrated_apps
        names = sorted({name for (lab, name) in ldr.disk_migrations if lab == LABEL})
        return {"migrated": migrated, "names": names}
    finally:
        loader_mod.apps.get_app_configs = orig_get
        MigrationLoader.migrations_module = orig_mig
        loader_mod.import_module = orig_imp
        loader_mod.pkgutil.iter_modules = orig_iter


# pkgutil.iter_modules never yields an empty name, and the real load_disk
# indexes name[0]; an empty name is outside the discovery domain, so it is not
# fuzzed here (the Lean spec still models it via validMigrationName = false).
_NAMES = ["0001_initial", "0002_auto", "name", "_private", "~tmp", "abc",
          "_", "~", "0003_x", "sub", "9_z"]


def rand_entries(rng):
    n = rng.randint(0, 6)
    out = []
    for _ in range(n):
        nm = rng.choice(_NAMES)
        is_pkg = rng.random() < 0.3
        out.append((nm, is_pkg))
    return out


def main():
    rng = random.Random(11141)  # pinned seed (mapping.md)
    N = 100_000
    disagreements = 0
    first = None
    for _ in range(N):
        has_file = rng.random() < 0.5
        has_path = rng.random() < 0.85   # bias toward the package case
        ino = rng.random() < 0.5
        entries = rand_entries(rng)

        o = oracle(has_file, has_path, ino, entries)
        s = shadow(has_file, has_path, ino, entries)
        s_cmp = {"migrated": s["migrated"], "names": sorted(set(s["names"]))}
        if o != s_cmp:
            disagreements += 1
            if first is None:
                first = (has_file, has_path, ino, entries, o, s_cmp)
    if disagreements:
        print("G-CONF FAIL: %d/%d disagreements; first=%r" % (disagreements, N, first))
        return 1
    print("G-CONF OK: %d inputs, 0 disagreements" % N)
    return 0


if __name__ == "__main__":
    sys.exit(main())
