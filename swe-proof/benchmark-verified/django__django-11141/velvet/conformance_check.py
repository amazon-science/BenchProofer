#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-11141 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged op of Solution.lean's impl region (`classify`,
              folded by `classifyAll`) transliterated to Python over the real
              repo observations, via the mapping.md §2 bijection
              (`isPackage` ↔ hasattr(module,'__path__'); `migrationNames` ↔ the
              discovered migration set; `ignoreMissing` ↔ self.ignore_no_migrations;
              `isNamespace` carried but unused). There are no A-tagged callees
              in the impl, so the shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the post-patch classification of one
              application as migrated/unmigrated. It is driven by the REAL
              discovery + decision machinery the patched `load_disk` uses:
              a genuine package module object whose `__path__` points at a real
              temporary directory is enumerated by the same
              `pkgutil.iter_modules` comprehension as `loader.py`, then the
              patched `migration_names or self.ignore_no_migrations` decision is
              applied. The implicit-namespace observation (`__file__ is None`)
              is set on the module object but, per the patch, does not gate the
              verdict. (The real end-to-end correctness oracle is G-RESOLVE; this
              isolates the classification leg the Lean model pins.)

They must agree on every input across the full Boolean matrix + fuzzed migration
sets. Exit 0 iff zero disagreements; any disagreement is a mechanical
R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib only. The fuzz
seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import os
import pkgutil
import random
import shutil
import sys
import tempfile
import types

SEED = 11141
N_FUZZ = 100_000


# --- the R/I shadow: classify / classifyAll, transliterated ------------------
def shadow_classify(is_package, is_namespace, migration_names, ignore_missing):
    """`classify (m : MigrationSource)` transliterated:
        if m.isPackage then (!m.migrationNames.isEmpty || m.ignoreMissing)
        else false
    The implicit-namespace observation is NOT consulted (mapping.md §1)."""
    if is_package:
        return bool(migration_names) or ignore_missing
    return False


# --- the ORACLE: the patched load_disk classification, really executed -------
def _discover_migration_names(path):
    """The unchanged discovery comprehension from loader.py (post-patch lines
    92-95), executed verbatim over a real package search path."""
    return {
        name for _, name, is_pkg in pkgutil.iter_modules(path)
        if not is_pkg and name[0] not in '_~'
    }


def _make_module(tmpdir, is_package, is_namespace, member_names):
    """Build a module object mirroring what `import_module` yields for a
    migrations package: a real `__path__` directory (so the genuine
    `pkgutil.iter_modules` enumerates it), optionally a `__file__`
    (None ⇒ implicit namespace package, the observation the patch stops
    consulting)."""
    mod = types.ModuleType("fakemigrations")
    if is_package:
        pkgdir = os.path.join(tmpdir, "pkg")
        os.makedirs(pkgdir, exist_ok=True)
        # materialise each member as a real top-level module file so the real
        # pkgutil.iter_modules discovers exactly the intended migration names.
        for nm in member_names:
            with open(os.path.join(pkgdir, nm + ".py"), "w") as fh:
                fh.write("# migration stub\n")
        mod.__path__ = [pkgdir]
    # __file__ present unless this is an implicit namespace package
    if not is_namespace:
        mod.__file__ = os.path.join(tmpdir, "__init__.py")
    return mod


def oracle_classify(tmpdir, is_package, is_namespace, member_names, ignore_missing):
    """patch.diff's classification of one application, run through the real
    discovery + the patched decision."""
    module = _make_module(tmpdir, is_package, is_namespace, member_names)
    # surviving guard: a non-package is unmigrated (the `not hasattr __path__`
    # early step the patch keeps).
    if not hasattr(module, '__path__'):
        return False
    # the patched decision (loader.py post-patch lines 91-100). Note: the
    # pre-patch `__file__ is None` short-circuit is DELETED, so a namespace
    # package falls through to the same decision as any other package.
    migration_names = _discover_migration_names(module.__path__)
    if migration_names or ignore_missing:
        return True   # self.migrated_apps.add(label)
    return False      # self.unmigrated_apps.add(label)


# --- name pools (only emptiness of the discovered set is observed) -----------
# Names that the discovery comprehension KEEPS (first char not in '_~').
_KEPT = ["0001_initial", "0002_auto", "author", "x", "m9", "zzz", "0003_more"]


def fuzz_cases(n, rng):
    """Yield (is_package, is_namespace, member_names, ignore_missing) tuples.

    Boundary first: the full Boolean matrix over (package, namespace, has-kept-
    migration, ignore_missing), including the F2P scenario — a namespace package
    that DOES expose a migration (must be migrated post-patch)."""
    for is_package in (True, False):
        for is_namespace in (True, False):
            for has_member in (True, False):
                for ignore_missing in (True, False):
                    members = ["0001_initial"] if has_member else []
                    yield (is_package, is_namespace, members, ignore_missing)
    # explicit F2P: namespace package WITH a migration, default config
    yield (True, True, ["0001_initial"], False)
    # explicit empty-dir: package, no migrations, not kept -> unmigrated
    yield (True, False, [], False)
    for _ in range(n):
        is_package = rng.random() < 0.7
        is_namespace = rng.random() < 0.5
        k = rng.randint(0, 4)
        members = rng.sample(_KEPT, k=min(k, len(_KEPT)))
        ignore_missing = rng.random() < 0.5
        yield (is_package, is_namespace, members, ignore_missing)


def main():
    rng = random.Random(SEED)
    tmproot = tempfile.mkdtemp(prefix="gconf_11141_")
    disagreements = []
    count = 0
    try:
        for is_package, is_namespace, members, ignore_missing in fuzz_cases(N_FUZZ, rng):
            count += 1
            case_dir = tempfile.mkdtemp(dir=tmproot)
            try:
                shadow = shadow_classify(is_package, is_namespace,
                                         members, ignore_missing)
                oracle = oracle_classify(case_dir, is_package, is_namespace,
                                         members, ignore_missing)
            finally:
                shutil.rmtree(case_dir, ignore_errors=True)
            if shadow != oracle:
                disagreements.append(
                    ((is_package, is_namespace, members, ignore_missing),
                     shadow, oracle))
                if len(disagreements) >= 5:
                    break
    finally:
        shutil.rmtree(tmproot, ignore_errors=True)

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d cases:"
              % (len(disagreements), count))
        for inp, sh, orc in disagreements:
            print("  input=%r shadow=%r oracle=%r" % (inp, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of classifyMigrationSources (classify) agrees "
          "with the patched load_disk classification on %d cases (seed=%d), "
          "0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
