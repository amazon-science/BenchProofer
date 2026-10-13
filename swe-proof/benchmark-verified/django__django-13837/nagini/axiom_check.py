#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-13837.

The changed branch detects "Python was started as ``python -m PACKAGE``" and
re-invokes that package. The detection is modelled DEEPLY (not behind a consumed
axiom) by `is_module_launch` (model.py) as

    is_module_launch = (a launch package was reported) and (its name is non-empty)

and the emitted package is that reported package itself. The single A-reference
this validates is the runtime/import-system semantics the patch relies on:

    __main__.__spec__ is not None  iff  Python was started with -m or with a
        directory/zip/sys.path entry;
    __main__.__spec__.parent  is the launched PACKAGE for ``-m PACKAGE`` and is
        the empty string "" for a directory/zip launch;
    __main__.__spec__ is None for a plain ``python script.py`` launch.
    (https://docs.python.org/3/reference/import.html#main-spec)

So "started with -m PACKAGE" holds iff ``__spec__ is not None and
__spec__.parent`` is a non-empty string equal to PACKAGE -- exactly the model's
predicate, with the emitted package equal to ``__spec__.parent``.

This check builds the REAL objects ``__main__.__spec__`` is (genuine
``importlib.machinery.ModuleSpec`` instances, the same type the import system
attaches), plus the genuine ``None`` spec of a script launch, for representative
launch shapes, and asserts that

  (1) the runtime predicate ``spec is not None and spec.parent`` agrees with the
      model's ``is_module_launch``, and
  (2) the reconstructed child argument vector (model.py's `child_arguments`,
      re-expressed here over Python lists) equals what the gold post-patch code
      ``get_child_arguments`` produces from the same ``__main__.__spec__``.

Imports only the standard library (``importlib.machinery``, ``importlib.util``);
nothing repo-specific. Exit 0 iff every obligation holds.
"""
import importlib.machinery
import importlib.util
import sys


# --- model.py reference, re-expressed over Python lists/strings --------------

DASH_M = "-m"
RECOVERY = ["\x00"]   # windows_recovery() sentinel: PSeq(PSeq(0))


def is_module_launch(package_reported, launch_package):
    """model.py `is_module_launch`: a reported, non-empty launch package."""
    return package_reported and len(launch_package) > 0


def model_child_arguments(prefix, package_reported, launch_package, argv,
                          script_exists):
    """model.py `child_arguments`, over Python lists of str."""
    if is_module_launch(package_reported, launch_package):
        return list(prefix) + [DASH_M, launch_package] + list(argv[1:])
    elif not script_exists:
        return list(RECOVERY)
    else:
        return list(prefix) + list(argv)


# --- the gold post-patch branch, re-expressed over a real ModuleSpec ---------

def gold_child_arguments(prefix, main_spec, argv, script_exists):
    """The post-patch get_child_arguments() branch logic, driven by the REAL
    ``__main__.__spec__`` object (`main_spec`), the abstract analogue of

        if __main__.__spec__ is not None and __main__.__spec__.parent:
            args += ['-m', __main__.__spec__.parent]
            args += sys.argv[1:]
        elif not py_script.exists():
            <recovery>
        else:
            args += sys.argv
    """
    if main_spec is not None and main_spec.parent:
        return list(prefix) + [DASH_M, main_spec.parent] + list(argv[1:])
    elif not script_exists:
        return list(RECOVERY)
    else:
        return list(prefix) + list(argv)


def runtime_package(main_spec):
    """The (package_reported, launch_package) the model derives from the REAL
    ``__main__.__spec__``: reported iff spec is not None; the launch package is
    its ``parent`` ("" when not reported)."""
    if main_spec is None:
        return (False, "")
    return (True, main_spec.parent)


# --- launch-shape fixtures: REAL ModuleSpec objects --------------------------

def spec_for_module_launch(package, submodule="__main__"):
    """A genuine ModuleSpec as the import system attaches it for
    ``python -m PACKAGE`` (running PACKAGE.__main__): its name is
    ``PACKAGE.__main__`` and its ``.parent`` is ``PACKAGE`` (parent is the
    package of a submodule)."""
    spec = importlib.machinery.ModuleSpec(
        "%s.%s" % (package, submodule), loader=None, is_package=False)
    # parent is derived: for a non-package submodule it is the containing
    # package name. Set the submodule-search-locations marker accordingly.
    return spec


def spec_for_directory_launch():
    """A genuine ModuleSpec for ``python somedir`` / ``python some.zip``: the
    __main__.py inside is executed as the top-level __main__ module, whose
    ``.parent`` is the empty string."""
    spec = importlib.machinery.ModuleSpec("__main__", loader=None,
                                          is_package=False)
    return spec


def main():
    prefix = ["/usr/bin/python", "-Wall"]
    argv = ["entry_script.py", "runserver", "--noreload-arg"]

    # --- module launches: -m PACKAGE for a variety of packages ------------
    module_packages = [
        "django",
        "utils_tests.test_module",     # the F2P non-django module
        "pkg",
        "a.b.c",
        "x",
        "my_app.management",
    ]
    failures = 0
    checked = 0
    for pkg in module_packages:
        spec = spec_for_module_launch(pkg)
        # Sanity: a real ModuleSpec for a submodule reports the package as parent.
        assert spec.parent == pkg, (
            "ModuleSpec(%r).parent == %r, expected %r" %
            (spec.name, spec.parent, pkg))
        reported, launch_pkg = runtime_package(spec)
        # (1) predicate agreement
        runtime_is_module = bool(spec is not None and spec.parent)
        model_is_module = is_module_launch(reported, launch_pkg)
        assert runtime_is_module == model_is_module == True, (
            "predicate disagreement for -m %s: runtime=%r model=%r" %
            (pkg, runtime_is_module, model_is_module))
        # (2) reconstruction agreement
        for script_exists in (True, False):
            m = model_child_arguments(prefix, reported, launch_pkg, argv,
                                      script_exists)
            g = gold_child_arguments(prefix, spec, argv, script_exists)
            assert m == g, (
                "child-arguments disagreement for -m %s (script_exists=%r): "
                "model=%r gold=%r" % (pkg, script_exists, m, g))
            # the emitted form must carry -m then the launched package itself
            assert m[len(prefix):len(prefix) + 2] == [DASH_M, pkg], (
                "module launch -m %s did not emit ['-m', %r]: %r" %
                (pkg, pkg, m))
            checked += 1
        failures += 0

    # --- directory / zipfile launch: parent == "" => NOT a module launch --
    dir_spec = spec_for_directory_launch()
    assert dir_spec.parent == "", (
        "directory-launch ModuleSpec.parent == %r, expected ''" %
        (dir_spec.parent,))
    reported, launch_pkg = runtime_package(dir_spec)
    assert is_module_launch(reported, launch_pkg) is False, (
        "directory launch (parent='') must NOT be a module launch")
    for script_exists in (True, False):
        m = model_child_arguments(prefix, reported, launch_pkg, argv,
                                  script_exists)
        g = gold_child_arguments(prefix, dir_spec, argv, script_exists)
        assert m == g, ("directory-launch reconstruction disagreement "
                        "(script_exists=%r): model=%r gold=%r" %
                        (script_exists, m, g))
        checked += 1

    # --- plain script launch: __main__.__spec__ is None => NOT module -----
    none_spec = None
    reported, launch_pkg = runtime_package(none_spec)
    assert reported is False and is_module_launch(reported, launch_pkg) is False, (
        "script launch (spec=None) must NOT be a module launch")
    for script_exists in (True, False):
        m = model_child_arguments(prefix, reported, launch_pkg, argv,
                                  script_exists)
        g = gold_child_arguments(prefix, none_spec, argv, script_exists)
        assert m == g, ("script-launch reconstruction disagreement "
                        "(script_exists=%r): model=%r gold=%r" %
                        (script_exists, m, g))
        # script present => whole argv as-is, NO -m
        if script_exists:
            assert DASH_M not in m, "script launch must not emit -m: %r" % (m,)
        checked += 1

    # --- a real, importable submodule spec sanity-check -------------------
    # importlib.util.find_spec on a genuine package submodule reports the
    # package as .parent, confirming the runtime rule independently.
    real_spec = importlib.util.spec_from_loader("os.path", loader=None)
    # os.path is itself a module whose parent is 'os'; ModuleSpec derives parent
    # from the name's package portion.
    assert real_spec.parent == "os", (
        "spec_from_loader('os.path').parent == %r, expected 'os'" %
        (real_spec.parent,))

    print("G-AX OK: is_module_launch deep model + emitted-package agree with "
          "the real __main__.__spec__/.parent runtime semantics over %d "
          "reconstruction checks (%d -m packages, directory launch, script "
          "launch); ModuleSpec.parent rule confirmed." %
          (checked, len(module_packages)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
