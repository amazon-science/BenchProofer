#!/usr/bin/env python3
r"""G-CONF differential conformance check for django__django-14311 (plan §4.1).

Runs IN-CONTAINER with the gold patch applied (the orchestrator passes
apply_gold=True), so the ORACLE is the patched repo's real behaviour: the real
`django.utils.autoreload.get_child_arguments()` taking the `__spec__`-present
`-m` relaunch branch, driven by mocking `__main__.__spec__`, `sys.argv`, and
`sys.warnoptions` exactly as the repo's own TestChildArguments tests do.

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW — Solution.lean's modeled rule, transliterated to Python over the
             real repo types via the mapping.md §2 bijection:
                 moduleName    <-> __main__.__spec__.name   (str)
                 parentPackage <-> __main__.__spec__.parent (str, '' if none)
                 leadingArgs   <-> [sys.executable] + ['-W%s'%o for o in
                                    sys.warnoptions]
                 trailingArgs  <-> sys.argv[1:]
             moduleToReexec(name, parent) =
                 parent  if (name == '__main__' or name.endswith('.__main__'))
                            and parent != ''
                 else name
             predicted cmdline = leadingArgs + ['-m', moduleToReexec(...)]
                                 + trailingArgs.
             There are NO A-tagged ops (no consumed axioms), so the shadow is
             pure R/I.
  * ORACLE — patch.diff behaviour: the REAL patched get_child_arguments(), run
             with a fake `__main__` whose `__spec__.name`/`.parent` are the fuzz
             inputs, the matching `sys.argv` / `sys.warnoptions`, reading back
             the real returned argument list.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample. stdlib + django only. Fuzz seed
pinned (mapping.md §4).
"""
import random
import sys
import types
from unittest import mock

SEED = 14311
N_FUZZ = 100_000


def _import_real():
    sys.path.insert(0, ".")
    from django.utils import autoreload  # noqa: E402
    return autoreload


# ---- the R/I shadow: Solution.lean moduleToReexec, transliterated -----------
def module_to_reexec(name, parent):
    if (name == "__main__" or name.endswith(".__main__")) and parent != "":
        return parent
    return name


def shadow_cmdline(name, parent, warnoptions, argv):
    leading = [sys.executable] + ["-W%s" % o for o in warnoptions]
    trailing = list(argv[1:])
    return leading + ["-m", module_to_reexec(name, parent)] + trailing


# ---- the ORACLE: the REAL patched get_child_arguments() ---------------------
def oracle_cmdline(autoreload, name, parent, warnoptions, argv):
    fake_main = types.ModuleType("__main__")
    fake_main.__spec__ = types.SimpleNamespace(name=name, parent=parent)
    with mock.patch.dict(sys.modules, {"__main__": fake_main}), \
            mock.patch.object(sys, "argv", list(argv)), \
            mock.patch.object(sys, "warnoptions", list(warnoptions)):
        return autoreload.get_child_arguments()


def main():
    autoreload = _import_real()
    rng = random.Random(SEED)

    # Vocabulary of dotted-name components, including the package-entry sentinel
    # and the corner case the issue/hints call out (`my__main__`, which embeds
    # the text but is NOT a package entry).
    COMPS = ["foo", "bar", "baz", "pkg", "manage", "main_module",
             "my__main__", "__main__x", "x__main__", "a"]
    PROGS = [["runserver"], ["runserver", "--noreload"], [], ["test", "app"]]
    WARNS = [[], ["error"], ["error", "ignore::DeprecationWarning"]]

    def rand_name():
        # Possibly a package-entry name (ends in __main__ / .__main__), possibly
        # an ordinary dotted module, possibly empty.
        roll = rng.random()
        if roll < 0.12:
            return "__main__"
        if roll < 0.30:
            depth = rng.randint(1, 3)
            return ".".join(rng.choice(COMPS) for _ in range(depth)) + ".__main__"
        if roll < 0.36:
            return ""
        depth = rng.randint(1, 4)
        return ".".join(rng.choice(COMPS) for _ in range(depth))

    def rand_parent(name):
        roll = rng.random()
        if roll < 0.30:
            return ""  # no parent package (falsy)
        if roll < 0.60 and "." in name:
            return name.rsplit(".", 1)[0]  # the realistic parent of `name`
        depth = rng.randint(1, 3)
        return ".".join(rng.choice(COMPS) for _ in range(depth))

    # Boundary sweep: the three behavioural classes by hand.
    boundary = [
        # (name, parent) : genuine deeper module keeps its own name (the fix)
        ("utils_tests.test_module.main_module", "utils_tests.test_module"),
        ("foo.bar.baz", "foo.bar"),
        ("django", "django"),                       # name==parent, ordinary
        # package-entry names collapse to the parent
        ("__main__", "pkg"),
        ("pkg.__main__", "pkg"),
        ("utils_tests.test_module.__main__", "utils_tests.test_module"),
        # package-entry name but no parent -> keep the name
        ("__main__", ""),
        ("pkg.__main__", ""),
        # the hint's corner case: embeds the text but is not a package entry
        ("foo.my__main__", "foo"),
        ("x__main__", "x"),
        ("foo.__main__x", "foo"),
        # ordinary module, no parent
        ("manage", ""),
    ]

    disagreements = []
    count = 0

    def one(name, parent, warns, argv):
        nonlocal count
        count += 1
        sh = shadow_cmdline(name, parent, warns, argv)
        orc = oracle_cmdline(autoreload, name, parent, warns, argv)
        if sh != orc:
            disagreements.append((name, parent, warns, argv, sh, orc))

    SCRIPT = "/path/to/manage.py"  # argv[0]; unused by the -m branch
    for name, parent in boundary:
        for warns in WARNS:
            for prog in PROGS:
                one(name, parent, warns, [SCRIPT] + prog)

    while count < N_FUZZ:
        name = rand_name()
        parent = rand_parent(name)
        warns = rng.choice(WARNS)
        prog = rng.choice(PROGS)
        one(name, parent, warns, [SCRIPT] + prog)
        if len(disagreements) >= 10:
            break

    if disagreements:
        print(f"G-CONF FAIL: {len(disagreements)} R/I disagreement(s) over "
              f"{count} inputs (seed={SEED}):")
        for name, parent, warns, argv, sh, orc in disagreements[:10]:
            print(f"  name={name!r} parent={parent!r} warns={warns} "
                  f"argv={argv}\n    shadow={sh}\n    oracle={orc}")
        return 1

    print(f"G-CONF OK: R/I shadow of relaunchCommand agrees with patch.diff "
          f"behaviour (real get_child_arguments -m branch) on {count} inputs "
          f"(seed={SEED}), 0 disagreements.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
