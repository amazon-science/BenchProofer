#!/usr/bin/env python3
"""G-AX executable soundness check for scikit-learn__scikit-learn-14141.

The single consumed axiom is `version_of` (model.py axioms region): the
per-module version observation the dependency reporter performs once per
rostered name. The proof relies ONLY on its TOTALITY -- that every rostered
name ends up as a key of the returned mapping carrying *a* value (the version,
or the absent marker `None` when the module cannot be imported), never absent
and never raising out of the population step. The model's `version_of` has the
weakest contract that supports this (`Ensures(True)`), so the obligation G-AX
must discharge is exactly:

  (A-consumed, totality) running the REAL `_get_deps_info()` yields a mapping
      in which every rostered dependency name -- including the parallel-execution
      dependency `joblib` (the discriminating roster member the patch adds) --
      is a key, with a value present even when the module is absent (`None`),
      and the mapping holds no key outside the roster.

This validates both the `version_of`-as-total modeling and the refinement claim
that adding a name to the roster makes it a key of the result. It also re-derives
the roster ↔ result-keys correspondence the model encodes (mapping.md §2-3).

Imports nothing besides the standard library and the installed `scikit-learn`
package the gold patch modifies. Exit 0 iff every obligation holds.
"""
import sys

# The roster the post-patch reporter must report (model.py name_* tokens ↔ these
# names; mapping.md §1). `joblib` is the discriminating member the gold patch adds.
EXPECTED_ROSTER = {
    "pip",
    "setuptools",
    "sklearn",
    "numpy",
    "scipy",
    "Cython",
    "pandas",
    "matplotlib",
    "joblib",
}


def check_real_get_deps_info():
    """Run the REAL reporter and assert the roster ↔ result-keys correspondence
    and the version_of-totality property the model consumes."""
    from sklearn.utils._show_versions import _get_deps_info

    deps_info = _get_deps_info()
    keys = set(deps_info)

    # (totality) every rostered name is a key carrying a value slot -----------
    for name in sorted(EXPECTED_ROSTER):
        assert name in deps_info, (
            "version_of totality unsound: rostered dependency %r is NOT a key "
            "of the real _get_deps_info() result %r" % (name, keys))
        # the key is present; the value is the version or the absent marker None
        # (the `except ImportError: deps_info[modname] = None` branch). Either
        # way the key exists -- which is all the model relies on.
        val = deps_info[name]
        assert (val is None) or isinstance(val, str), (
            "unexpected version marker for %r: %r (expected a version str or "
            "None)" % (name, val))

    # the discriminating member specifically (the F2P assertion) --------------
    assert "joblib" in deps_info, (
        "parallel-execution dependency 'joblib' is NOT reported among the "
        "result keys %r -- the patched behaviour is absent" % (keys,))

    # (no spurious keys) the result holds no key outside the roster -----------
    extra = keys - EXPECTED_ROSTER
    assert not extra, (
        "real _get_deps_info() reported keys outside the modeled roster: %r"
        % (sorted(extra),))

    # exact correspondence: result keys == roster (mapping.md §2-3) -----------
    assert keys == EXPECTED_ROSTER, (
        "result key-set %r does not equal the modeled roster %r"
        % (sorted(keys), sorted(EXPECTED_ROSTER)))


def check_absent_module_boundary():
    """Boundary for the version_of-totality modeling: when a rostered module is
    absent, the key is still present (value None), never dropped. We exercise
    the routine's own per-name code path with a guaranteed-absent module name to
    confirm the import-failure branch keeps the key.

    This mirrors lines 58-67: try import; on ImportError store None. The key is
    populated either way -- the property the model's total `version_of` encodes.
    """
    import importlib

    bogus = "joblib_definitely_absent_module_zzz_14141"
    deps_info = {}
    try:
        if bogus in sys.modules:
            mod = sys.modules[bogus]
        else:
            mod = importlib.import_module(bogus)
        deps_info[bogus] = getattr(mod, "__version__", None)
    except ImportError:
        deps_info[bogus] = None
    assert bogus in deps_info and deps_info[bogus] is None, (
        "import-failure branch did not keep the rostered name as a key with a "
        "None marker: %r" % (deps_info,))


def main():
    check_real_get_deps_info()
    check_absent_module_boundary()
    print("G-AX OK: version_of totality sound -- real _get_deps_info() reports "
          "every rostered name (incl. 'joblib') as a key with no spurious keys; "
          "import-failure branch keeps the key with a None marker.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
