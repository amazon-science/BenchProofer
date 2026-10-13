#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-13820.

This bundle consumes NO `@ContractOnly` axiom: the changed operation (whether a
just-imported module is a source of submodules to enumerate, or is skipped) is
modelled deeply as boolean predicate logic over three observable module facts.
The three runtime introspections the patched block performs are *unchanged*
Python builtins refined to their truth values (kind R), not axioms:

  * `hasattr(module, '__path__')`                 -> is_package: bool
  * `getattr(module, '__file__', None) is not None` -> file_is_set: bool
  * `isinstance(module.__path__, list)`           -> path_is_ordinary_list: bool

There is no axiom Ensures for G-AX to reject. This script instead validates, in
the real interpreter, the two refinement facts the bundle relies on, so the
R-refinements are demonstrably sound:

  (R-pkg/list) `isinstance(module.__path__, list)` is the documented marker that
      discriminates a REGULAR package (an ordinary `list` for `__path__`, value
      True) from a PEP-420 NAMESPACE package (a custom iterable, value False).
      We build a real regular package and a real namespace package on disk,
      import them, and assert the discrimination holds - including a regular
      package whose `__file__` has been deleted (the frozen-environment case),
      which must still expose a `list` __path__.
      Ref: https://docs.python.org/3/reference/import.html#namespace-packages

  (R-decision) the deep boolean decision `is_source` (model.py) matches the real
      `load_disk` classification on all eight `(is_package, file_is_set,
      path_is_ordinary_list)` combinations. The real classification is the gold
      post-patch block transcribed faithfully (it is pure boolean logic with no
      external dependency); the discriminating frozen-environment row
      `(True, False, True)` must classify as a migration source.

Imports only the Python standard library; exit 0 iff every obligation holds.
"""
import importlib
import os
import shutil
import sys
import tempfile


# --- model.py reference encoding (kept in lock-step with `is_source`) --------

def is_source(is_package, file_is_set, path_is_ordinary_list):
    """Reference of model.py's deep decision `is_source`."""
    return is_package and (file_is_set or path_is_ordinary_list)


# --- gold post-patch classification, transcribed faithfully ------------------

def gold_classification(module):
    """The post-patch `load_disk` per-module classification (the `else:` arm),
    returning True iff `module` is treated as a migration source (falls through
    to migrated_apps / iter_modules), False iff skipped (added to
    unmigrated_apps). Pure boolean logic, no external dependency."""
    # Module is not a package (e.g. migrations.py).
    if not hasattr(module, '__path__'):
        return False
    # Empty directories are namespaces. Namespace packages have no __file__ and
    # don't use a list for __path__.
    if (
        getattr(module, '__file__', None) is None and
        not isinstance(module.__path__, list)
    ):
        return False
    return True


def observed_facts(module):
    """The three R-refined booleans observed from a real module object."""
    is_package = hasattr(module, '__path__')
    file_is_set = getattr(module, '__file__', None) is not None
    path_is_ordinary_list = is_package and isinstance(module.__path__, list)
    return is_package, file_is_set, path_is_ordinary_list


# --- (R-pkg/list) build real packages on disk and import them ----------------

def check_path_list_discriminates():
    root = tempfile.mkdtemp(prefix="sbn_13820_")
    sys.path.insert(0, root)
    try:
        # A REGULAR package: has __init__.py.
        regdir = os.path.join(root, "sbn_regular_pkg")
        os.makedirs(regdir)
        with open(os.path.join(regdir, "__init__.py"), "w") as f:
            f.write("# regular package\n")

        # A PEP-420 NAMESPACE package: a directory with NO __init__.py.
        nsdir = os.path.join(root, "sbn_namespace_pkg")
        os.makedirs(nsdir)
        # (no __init__.py)

        importlib.invalidate_caches()
        reg = importlib.import_module("sbn_regular_pkg")
        ns = importlib.import_module("sbn_namespace_pkg")

        # Regular package: __path__ IS a list; file_is_set normally True.
        assert hasattr(reg, "__path__"), "regular package missing __path__"
        assert isinstance(reg.__path__, list), (
            "regular package __path__ is not a list: %r" % type(reg.__path__))

        # Namespace package: __path__ is NOT an ordinary list, and __file__ None.
        assert hasattr(ns, "__path__"), "namespace package missing __path__"
        assert not isinstance(ns.__path__, list), (
            "namespace package __path__ unexpectedly a list: %r"
            % type(ns.__path__))
        assert getattr(ns, "__file__", None) is None, (
            "namespace package unexpectedly has __file__=%r"
            % getattr(ns, "__file__", None))

        # The frozen-environment case: a REGULAR package whose __file__ has been
        # deleted must STILL expose a list __path__ (so path_is_ordinary_list
        # stays True even though file_is_set becomes False).
        saved_file = reg.__file__
        try:
            del reg.__file__
            ip, fset, plist = observed_facts(reg)
            assert ip is True, "regular pkg no longer a package after del __file__"
            assert fset is False, "del __file__ did not clear file_is_set"
            assert plist is True, (
                "regular pkg __path__ stopped being a list after del __file__")
            # The discriminating decision: must be a migration source.
            assert gold_classification(reg) is True, (
                "frozen regular package wrongly skipped by gold classification")
            assert is_source(ip, fset, plist) is True, (
                "model is_source disagrees on the frozen-package case")
        finally:
            reg.__file__ = saved_file
    finally:
        if root in sys.path:
            sys.path.remove(root)
        for m in ("sbn_regular_pkg", "sbn_namespace_pkg"):
            sys.modules.pop(m, None)
        shutil.rmtree(root, ignore_errors=True)


# --- (R-decision) full truth table: model == gold classification -------------

class _Fake:
    """A stand-in module object exposing exactly the three observable facts."""


def _make_module(is_package, file_is_set, path_is_ordinary_list):
    m = _Fake()
    if file_is_set:
        m.__file__ = "/some/where/__init__.py"
    # else: no __file__ attribute at all (getattr(..., None) is None)
    if is_package:
        if path_is_ordinary_list:
            m.__path__ = ["/some/where"]          # ordinary list
        else:
            m.__path__ = iter(["/some/where"])    # custom iterable (not a list)
    # else: no __path__ attribute at all
    return m


def check_decision_table():
    for is_package in (False, True):
        for file_is_set in (False, True):
            for path_is_ordinary_list in (False, True):
                # Faithful input space: list-ness is only meaningful for a
                # package (mirrors the model precondition).
                if not is_package and path_is_ordinary_list:
                    continue
                m = _make_module(is_package, file_is_set, path_is_ordinary_list)
                ip, fset, plist = observed_facts(m)
                assert (ip, fset, plist) == (
                    is_package, file_is_set, path_is_ordinary_list), (
                    "fake module did not realise facts %r, got %r"
                    % ((is_package, file_is_set, path_is_ordinary_list),
                       (ip, fset, plist)))
                gold = gold_classification(m)
                model = is_source(ip, fset, plist)
                assert gold == model, (
                    "model/gold mismatch on (is_package=%r, file_is_set=%r, "
                    "path_is_ordinary_list=%r): gold=%r model=%r"
                    % (is_package, file_is_set, path_is_ordinary_list,
                       gold, model))
    # The discriminating row, explicit:
    assert is_source(True, False, True) is True, "frozen regular pkg must load"
    assert is_source(True, False, False) is False, "namespace pkg must be skipped"
    assert is_source(False, False, False) is False, "non-package must be skipped"
    assert is_source(True, True, False) is True, "normal pkg must load"
    assert is_source(True, True, True) is True, "normal pkg (list path) must load"


def main():
    check_path_list_discriminates()
    check_decision_table()
    print("G-AX OK: no consumed axiom; R-refinements sound - "
          "isinstance(__path__, list) discriminates regular (True) from "
          "PEP-420 namespace (False) packages on real imports incl. a "
          "__file__-deleted regular package; is_source == gold load_disk "
          "classification on all 6 faithful (is_package, file_is_set, "
          "path_is_ordinary_list) combinations, incl. the discriminating "
          "frozen-environment row (True, False, True) -> migration source.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
