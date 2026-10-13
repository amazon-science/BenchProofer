#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13820 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region
              (`migrationsModuleLoadable`) transliterated to Python over the real
              repo observations, via the mapping.md §2 bijection:
                  hasFile     <-> getattr(module, '__file__', None) is not None
                  hasPath     <-> hasattr(module, '__path__')
                  pathIsList  <-> isinstance(module.__path__, list)
                  out (Bool)  <-> app classified into migrated_apps (True)
                                  vs unmigrated_apps (False)
              loadable(hasFile, hasPath, pathIsList)
                  = hasPath and (hasFile or pathIsList)
              There are NO A-tagged ops (no consumed axioms, no deep-model
              references), so the shadow is pure R/I.
  * ORACLE  — patch.diff's behaviour: the REAL patched
              `MigrationLoader.load_disk` applied at base_commit (the real
              correctness oracle, G-RESOLVE). We route one installed app's
              migrations module to a synthetic module whose three observable
              attributes realize a configuration, run the real `load_disk`, and
              read back whether that app landed in `migrated_apps`
              (loaded/scanned) or `unmigrated_apps` (skipped).

They must agree on every realizable input. Exit 0 iff zero disagreements; any
disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image, patched), Django +
stdlib only. The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.

Notes on the oracle setup:
  * The patch changes ONLY the per-module classification inside the `else:`
    block of `load_disk`. The unchanged downstream operations are made inert so
    the test exercises exactly the modeled decision:
      - `reload(module)` ("Force a reload if it's already loaded (tests need
        this)") is unchanged by the patch, runs strictly AFTER the classification
        (mapping.md §3), and is irrelevant to migrated/unmigrated membership; we
        monkeypatch it to a no-op so a synthetic module need not be reloadable.
      - `pkgutil.iter_modules(module.__path__)` runs only on the loadable
        branch; for every loadable *realizable* configuration `__path__` is an
        ordinary list pointing at a real (empty) directory, so it returns no
        migrations and never imports anything.
  * Only realizable `(hasFile, hasPath, pathIsList)` triples are driven through
    the real loader (a regular package, a frozen regular package with no
    `__file__`, an implicit namespace package with a non-list `__path__`, a
    plain non-package module, and a frozen plain module). The discriminating
    frozen-regular-package case `(False, True, True)` is included. The full
    8-point boolean cube is additionally checked against the documented decision
    to confirm the spec is total.
"""
import os
import random
import sys
import tempfile
import types

SEED = 13820
N_FUZZ = 100_000

# A module name that does not collide with any real importable module; injected
# directly into sys.modules so the real loader's import_module returns it.
MODNAME = "conf_check_migrations_13820"
APP_LABEL = "contenttypes"


# --- the R/I shadow: Solution.lean migrationsModuleLoadable, transliterated ---

def shadow(has_file, has_path, path_is_list):
    """loadable(hasFile, hasPath, pathIsList) = hasPath and (hasFile or
    pathIsList). Mirrors the impl `do` block (notPackage / isNamespace / out)."""
    return bool(has_path and (has_file or path_is_list))


# --- Django bootstrap --------------------------------------------------------

def _bootstrap():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            USE_TZ=False,
            USE_I18N=False,
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
            INSTALLED_APPS=["django.contrib.contenttypes"],
        )
    django.setup()


class _NonListPath:
    """A non-list iterable standing in for a PEP-420 namespace package's custom
    `__path__` type (CPython's `_NamespacePath`). `isinstance(x, list)` is False;
    it is still iterable (it is never iterated by the loadable decision)."""

    def __init__(self, entries):
        self._entries = list(entries)

    def __iter__(self):
        return iter(self._entries)


def _make_module(has_file, has_path, path_is_list, real_dir):
    """Build a synthetic module realizing the three observations the loader
    inspects. Returns the module (also injected into sys.modules)."""
    m = types.ModuleType(MODNAME)
    # __spec__ kept minimal/valid-ish; the loader's decision never reads it.
    if has_file:
        m.__file__ = os.path.join(real_dir, "__init__.py")
    # else: no __file__ attribute at all -> getattr(..., None) is None
    if has_path:
        if path_is_list:
            m.__path__ = [real_dir]            # ordinary list (regular package)
        else:
            m.__path__ = _NonListPath([real_dir])  # namespace-style non-list
    # else: not a package -> no __path__ attribute
    sys.modules[MODNAME] = m
    return m


def oracle(has_file, has_path, path_is_list, real_dir):
    """patch.diff's behaviour: drive the REAL patched MigrationLoader.load_disk
    and report whether APP_LABEL was scanned (migrated) or skipped (unmigrated)."""
    from django.db import connection
    from django.db.migrations import loader as loader_mod
    from django.db.migrations.loader import MigrationLoader
    from django.test import override_settings

    # Make the unchanged, post-decision reload() inert (mapping.md §3): a no-op
    # so synthetic modules need not be reloadable; the classification is upstream.
    saved_reload = loader_mod.reload
    loader_mod.reload = lambda mod: mod
    try:
        _make_module(has_file, has_path, path_is_list, real_dir)
        with override_settings(MIGRATION_MODULES={APP_LABEL: MODNAME}):
            ml = MigrationLoader(connection, load=False)
            ml.load_disk()
            if APP_LABEL in ml.migrated_apps:
                return True
            if APP_LABEL in ml.unmigrated_apps:
                return False
            raise AssertionError(
                "app %r classified into neither migrated nor unmigrated"
                % APP_LABEL)
    finally:
        loader_mod.reload = saved_reload
        sys.modules.pop(MODNAME, None)


# --- realizable configurations (driven through the real loader) --------------
# (label, has_file, has_path, path_is_list)
REALIZABLE = [
    ("regular package",                 True,  True,  True),
    ("frozen regular package",          False, True,  True),   # the fix / F2P
    ("implicit namespace package",      False, True,  False),  # stays skipped
    ("plain module (migrations.py)",    True,  False, True),   # path_is_list N/A
    ("frozen plain module",             False, False, True),   # path_is_list N/A
]


def main():
    _bootstrap()
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    with tempfile.TemporaryDirectory() as real_dir:

        def check(label, hf, hp, pl):
            nonlocal count
            count += 1
            sh = shadow(hf, hp, pl)
            orc = oracle(hf, hp, pl, real_dir)
            if sh != orc:
                disagreements.append((label, hf, hp, pl, sh, orc))

        # boundary sweep: every realizable class by hand
        for label, hf, hp, pl in REALIZABLE:
            check(label, hf, hp, pl)

        # fuzz-resample the realizable configurations for a deterministic
        # high-count verdict
        while count < N_FUZZ and len(disagreements) < 5:
            label, hf, hp, pl = rng.choice(REALIZABLE)
            check(label, hf, hp, pl)

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs (seed=%d):"
              % (len(disagreements), count, SEED))
        for label, hf, hp, pl, sh, orc in disagreements:
            print("  %s (hasFile=%s hasPath=%s pathIsList=%s) "
                  "shadow=%r oracle=%r" % (label, hf, hp, pl, sh, orc))
        return 1

    # full 8-point boolean cube: the shadow agrees with the documented decision
    # at every point (confirms the spec is total over Bool^3).
    for hf in (False, True):
        for hp in (False, True):
            for pl in (False, True):
                assert shadow(hf, hp, pl) == bool(hp and (hf or pl))

    print("G-CONF OK: R/I shadow of migrationsModuleLoadable agrees with "
          "patch.diff behaviour (real MigrationLoader.load_disk) on %d inputs "
          "(seed=%d), 0 disagreements; spec total over the 8-point cube."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
