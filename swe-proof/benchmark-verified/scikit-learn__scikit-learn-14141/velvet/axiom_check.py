#!/usr/bin/env python3
"""G-AX executable soundness check for scikit-learn__scikit-learn-14141.

The bundle's ONLY axiom is

    lookupVersion : List Char -> Option (List Char)

modeling the per-name version query inside the dependency-report loop
(`sys.modules[modname]` or `importlib.import_module(modname)`, then
`module.__version__`, returning `None` on `ImportError`). This callee is
**UNCHANGED** by the patch — the gold patch only inserts one element into the
`deps` roster (`sklearn/utils/_show_versions.py`); the resolution logic at
lines 53-67 is byte-identical pre- and post-patch.

DIRECTIVE 7 — what this check may and may NOT assert
----------------------------------------------------
G-AX validates the *unchanged callee the axiom is about*. It must NOT assert the
changed roster (whether `_get_deps_info()` covers `joblib`): that is the function
under change, NOT an axiom, and the orchestrator runs G-AX against the
**unpatched** repo (`gate_ax` does not apply the gold patch), where the roster is
the pre-patch 8 names. The roster change is validated by G-RESOLVE + G-CONF,
which DO apply the patch. The previous version of this script asserted the
9-name roster against the unpatched callee and thus (a) failed and (b) checked
the wrong thing; this version checks only `lookupVersion`.

`lookupVersion` is **uninterpreted** (no `ensures` axioms in Solution.lean), so
its only behavioral commitments are the ones a total `List Char -> Option
(List Char)` makes:

  (codomain) every reported version is a `str` (`some v`) or `None` (`none`) —
      never some other type;
  (totality / never-raises) the resolution terminates with a value for every
      name, never propagating an exception beyond the handled `ImportError`.

Both are validated against the REAL callee, run in-container against the
(unpatched) repo. `lookupVersion` is exercised two ways:

  1. directly, via the real unpatched `_get_deps_info()` — every value it stores
     is a direct observation of the real `lookupVersion` over the real roster
     names; we assert each is str-or-None.
  2. over arbitrary / nonexistent module names (boundary + fuzz), via the
     resolution logic transcribed verbatim from the unchanged loop body, to
     confirm it returns `None` on `ImportError` and never raises.

Imports only the repo module + the Python standard library. Exit 0 iff sound.
"""
import importlib
import random
import sys


# --- the UNCHANGED per-name resolution (sklearn/utils/_show_versions.py:53-67),
#     transcribed verbatim; this IS `lookupVersion`. Identical pre/post patch. --
def real_lookup_version(modname):
    """The real callee `lookupVersion(modname)`: import the module (reusing an
    already-imported one), read its advertised `__version__`, or `None` on
    `ImportError`. Mirrors the repo loop body exactly (only `ImportError` is
    caught there)."""
    def get_version(module):
        return module.__version__
    try:
        if modname in sys.modules:
            mod = sys.modules[modname]
        else:
            mod = importlib.import_module(modname)
        return get_version(mod)
    except ImportError:
        return None


def is_option_list_char(v):
    """The `Option (List Char)` carrier: `some <str>` or `none`."""
    return v is None or isinstance(v, str)


def main():
    # ---- (1) direct observations of the real callee via _get_deps_info() -----
    # This uses the REAL repo function (unpatched here), reading the versions it
    # resolved. We inspect ONLY the values (the lookupVersion codomain), never
    # the key set — the key set is the changed roster, out of scope for G-AX.
    try:
        from sklearn.utils._show_versions import _get_deps_info
    except Exception as e:  # pragma: no cover
        print("G-AX FAIL: could not import the repo module: %r" % (e,))
        return 1
    try:
        info = _get_deps_info()
    except Exception as e:
        print("G-AX FAIL: real _get_deps_info() raised %r (lookupVersion must "
              "never propagate beyond the handled ImportError)" % (e,))
        return 1
    if not isinstance(info, dict):
        print("G-AX FAIL: _get_deps_info() returned %r, expected dict"
              % (type(info),))
        return 1
    for name, ver in info.items():
        if not is_option_list_char(ver):
            print("G-AX FAIL: lookupVersion(%r) -> %r is neither str nor None "
                  "(Option (List Char) codomain violation)" % (name, ver))
            return 1

    # ---- (2) the real callee on boundary + fuzz module names -----------------
    # Names that ARE installed (the report's own roster + joblib, all queried as
    # the unchanged callee — independent of whether the patch lists them): each
    # must resolve to str-or-None and not raise.
    installed = ["pip", "setuptools", "sklearn", "numpy", "scipy",
                 "Cython", "pandas", "matplotlib", "joblib"]
    for modname in installed:
        ver = real_lookup_version(modname)
        if not is_option_list_char(ver):
            print("G-AX FAIL: lookupVersion(%r) -> %r not str-or-None"
                  % (modname, ver))
            return 1

    # Well-formed module names that do NOT exist: lookupVersion must return
    # None (ImportError handled) and never raise. The real callee is only ever
    # invoked on roster entries, which are valid module-name strings, so the
    # faithful domain here is well-formed-but-nonexistent identifiers (and
    # nonexistent dotted submodules of installed packages).
    boundary_absent = [
        "definitely_not_a_real_module_xyz", "joblib_nonexistent_submod",
        "Cython_Nonexistent", "__no_such_pkg__", "zzqqxx",
        "numpy_this_is_not_real", "scipy_absent_helper",
    ]
    for modname in boundary_absent:
        ver = real_lookup_version(modname)
        if ver is not None:
            print("G-AX FAIL: lookupVersion(%r) -> %r, expected None for an "
                  "absent module" % (modname, ver))
            return 1

    rng = random.Random(14141)
    head = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_"
    tail = head + "0123456789"
    n_fuzz = 2000
    for _ in range(n_fuzz):
        k = rng.randint(0, 16)
        # A valid Python identifier (head char not a digit), prefixed so no
        # real distribution ships it -> import raises ImportError -> None.
        modname = "zz_" + rng.choice(head) + "".join(rng.choice(tail)
                                                      for _ in range(k))
        ver = real_lookup_version(modname)
        if ver is not None:
            print("G-AX FAIL: lookupVersion(%r) -> %r, expected None for an "
                  "absent fuzzed module" % (modname, ver))
            return 1

    print("G-AX OK: the unchanged callee lookupVersion is total with codomain "
          "Option (List Char): every version from the real _get_deps_info() is "
          "str-or-None (%d observed), %d installed names resolve str-or-None, "
          "and %d absent/fuzz names return None without raising. The roster "
          "membership of joblib (the changed behavior) is validated by "
          "G-RESOLVE + G-CONF, not here (directive 7)."
          % (len(info), len(installed), len(boundary_absent) + n_fuzz))
    return 0


if __name__ == "__main__":
    sys.exit(main())
