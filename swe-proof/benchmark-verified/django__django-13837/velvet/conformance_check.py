#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13837 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region (`buildChildArgs`
              / `childArgsSpec`) transliterated to Python over the real repo
              types, via the mapping.md bijection. The impl computes the child
              argument vector by branching on the program-entry descriptor and,
              when not a module, on the on-disk probe of the invoking script
              path. There is NO axiomatized callee in the computed value (the
              proof consumes no axiom); the impl region is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `django.utils.autoreload.get_child_arguments`, invoked at
              base_commit with the gold patch applied, under the exact runtime
              state (sys.argv / sys.executable / sys.warnoptions /
              sys.modules['__main__'] and an on-disk script-path realization)
              that the modeled inputs denote. This is the real correctness
              oracle (G-RESOLVE); the F2P test mocks the very same state.

They must agree on every input: the same argument vector, or both raising the
"script does not exist" error. Exit 0 iff zero disagreements.

Runs in-container (the prebuilt SWE-Bench image with the gold patch applied),
stdlib only. The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import os
import random
import sys
import tempfile
from pathlib import Path
from unittest import mock

SEED = 13837
N_FUZZ = 100_000

# A sentinel distinct from any argument vector, denoting the
# "script does not exist" failure (Except.error ArgErr.scriptMissing).
ERROR = ("__SCRIPT_MISSING__",)


# --- a fake top-level program-entry descriptor -------------------------------
class _FakeSpec:
    def __init__(self, parent):
        self.parent = parent


class _FakeMain:
    """Stands in for sys.modules['__main__'] with a controllable __spec__,
    mirroring how the F2P test substitutes a module via mock.patch.dict."""
    def __init__(self, spec):
        self.__spec__ = spec


def _make_main(entry):
    kind = entry[0]
    if kind == "notModule":
        return _FakeMain(None)                 # __spec__ is None
    if kind == "pathEntry":
        return _FakeMain(_FakeSpec(""))         # __spec__.parent is "" (falsy)
    if kind == "moduleEntry":
        return _FakeMain(_FakeSpec(entry[1]))   # __spec__.parent == pkg (non-empty)
    raise AssertionError("bad entry %r" % (entry,))


# --- the R/I shadow: Solution.lean buildChildArgs, transliterated ------------
def shadow_child_args(interp, warnoptions, entry, probe, argv0, rest,
                      exe_path, script_path):
    """childArgsSpec transliterated to the real repo types (mapping.md §2):
       - wflags  ↔ ['-W%s' % o for o in sys.warnoptions]   (warnFlags = id)
       - baseArgs = [interp] + wflags
       - scriptArgv = [argv0] + rest   (full sys.argv)
       - restArgv   = rest             (sys.argv[1:])
    The entry descriptor selects the module branch (non-empty package) over the
    script-path branches, exactly as the spec's outer `match entry`."""
    wflags = ['-W%s' % o for o in warnoptions]
    base_args = [interp] + wflags
    script_argv = [argv0] + list(rest)
    rest_argv = list(rest)

    if entry[0] == "moduleEntry":              # .moduleEntry pkg
        pkg = entry[1]
        return base_args + (['-m', pkg] + rest_argv)
    # .notModule and .pathEntry both fall through to the script-path probe
    if probe == "exists":
        return base_args + script_argv
    if probe == "exeEntry":
        return [exe_path] + rest_argv
    if probe == "scriptEntry":
        return base_args + ([script_path] + rest_argv)
    if probe == "missing":
        return list(ERROR)
    raise AssertionError("bad probe %r" % (probe,))


# --- the oracle: patch.diff's get_child_arguments under the denoted state ----
def oracle_child_args(interp, warnoptions, entry, probe, argv0, rest, tmpdir):
    """patch.diff behaviour: realize the runtime state the modeled inputs denote
    (mocked sys state + on-disk script-path probe) and invoke the patched
    `get_child_arguments`. Returns the argument vector, or the ERROR sentinel
    when it raises the "script does not exist" RuntimeError."""
    from django.utils import autoreload

    py_script = Path(argv0)
    exe_entrypoint = py_script.with_suffix('.exe')
    script_entrypoint = py_script.with_name('%s-script.py' % py_script.name)

    # Realize the on-disk probe outcome for the invoking script path. (The
    # module branch ignores this, which the differential also exercises.)
    created = []
    try:
        if probe == "exists":
            py_script.touch()
            created.append(py_script)
        elif probe == "exeEntry":
            exe_entrypoint.touch()
            created.append(exe_entrypoint)
        elif probe == "scriptEntry":
            script_entrypoint.touch()
            created.append(script_entrypoint)
        elif probe == "missing":
            pass  # nothing exists -> RuntimeError on the non-module path
        else:
            raise AssertionError("bad probe %r" % (probe,))

        argv = [argv0] + list(rest)
        with mock.patch.object(sys, 'executable', interp), \
             mock.patch.object(sys, 'argv', argv), \
             mock.patch.object(sys, 'warnoptions', list(warnoptions)), \
             mock.patch.dict(sys.modules, {'__main__': _make_main(entry)}):
            try:
                return autoreload.get_child_arguments()
            except RuntimeError:
                return list(ERROR)
    finally:
        for p in created:
            try:
                p.unlink()
            except OSError:
                pass


ENTRIES = [
    ("notModule",),
    ("pathEntry",),
    ("moduleEntry", "django"),
    ("moduleEntry", "utils_tests.test_module"),
    ("moduleEntry", "pkg_other_than_django"),
    ("moduleEntry", "a.b.c"),
    ("moduleEntry", "x"),
]
PROBES = ["exists", "exeEntry", "scriptEntry", "missing"]
NAMES = ["prog", "manage", "django-admin", "runner", "main"]
WARNOPTS = [[], ["error"], ["all"], ["error", "ignore::DeprecationWarning"]]


def scenarios(n, rng):
    interp = "/usr/bin/python3"
    # boundary cases first (plan §4.1 step 4): every entry x every probe, so the
    # module branch's independence from the probe is checked explicitly.
    for entry in ENTRIES:
        for probe in PROBES:
            yield (interp, [], entry, probe, "prog", ["runserver"])
            yield (interp, ["error"], entry, probe, "django-admin",
                   ["runserver", "--noreload"])
    # the exact F2P scenario: started as a non-django module, script path absent
    yield (interp, [], ("moduleEntry", "utils_tests.test_module"),
           "missing", "test_module_main", ["runserver"])
    # randomized fuzz
    for _ in range(n):
        entry = rng.choice(ENTRIES)
        if entry[0] == "moduleEntry":
            # occasionally randomize the package name too
            if rng.random() < 0.3:
                k = rng.randint(1, 3)
                entry = ("moduleEntry",
                         ".".join(rng.choice(["pkg", "app", "tool", "x", "mymod"])
                                  for _ in range(k)))
        probe = rng.choice(PROBES)
        name = rng.choice(NAMES)
        warn = rng.choice(WARNOPTS)
        nrest = rng.randint(0, 3)
        rest = [rng.choice(["runserver", "--noreload", "0.0.0.0:8000",
                            "test", "--verbosity=2"]) for _ in range(nrest)]
        yield (interp, warn, entry, probe, name, rest)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    with tempfile.TemporaryDirectory() as tmpdir:
        for (interp, warn, entry, probe, name, rest) in scenarios(N_FUZZ, rng):
            count += 1
            argv0 = os.path.join(tmpdir, name)
            py_script = Path(argv0)
            exe_path = str(py_script.with_suffix('.exe'))
            script_path = str(py_script.with_name('%s-script.py' % py_script.name))

            shadow = shadow_child_args(interp, warn, entry, probe, argv0, rest,
                                       exe_path, script_path)
            oracle = oracle_child_args(interp, warn, entry, probe, argv0, rest,
                                       tmpdir)
            if shadow != oracle:
                disagreements.append(((entry, probe, name, warn, rest),
                                      shadow, oracle))
                if len(disagreements) >= 5:
                    break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for inp, sh, orc in disagreements:
            print("  input=%r\n    shadow=%r\n    oracle=%r" % (inp, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of buildChildArgs agrees with patch.diff "
          "get_child_arguments behaviour on %d inputs (seed=%d), 0 "
          "disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
