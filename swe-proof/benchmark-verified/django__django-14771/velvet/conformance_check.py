#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-14771 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region
              (`relaunchArgvSpec` / `xFlag` / `warnFlag`) transliterated to
              Python over the *real* repo types (`str`, `list[str]`,
              `dict[str, True|str]`, `bool`), via the mapping.md bijection
              (`List Char` ↔ `str`, `XVal.bare` ↔ value `is True`,
              `XVal.eq v` ↔ a string value).
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `django.utils.autoreload.get_child_arguments()` run at base_commit
              (the real correctness oracle, G-RESOLVE), with `sys.argv`,
              `sys.warnoptions`, `sys._xoptions`, `sys.executable`,
              `sys.implementation`, and `__main__.__spec__` mocked exactly as
              `tests/utils_tests/test_autoreload.py::TestChildArguments` does
              (the `else: args += sys.argv` branch — `__spec__ = None`, an
              existing `sys.argv[0]`).

There are no A-tagged callees in the impl region (mapping.md §3), so the shadow
is pure R/I. They must agree on every input. Exit 0 iff zero disagreements; any
disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image, with patch.diff
applied), stdlib only. The fuzz seed is pinned (mapping.md §4) for a
deterministic verdict.
"""
import os
import random
import sys
import types
from unittest import mock

SEED = 14771
N_FUZZ = 100_000

# An on-disk path that exists in-container, so Path(sys.argv[0]).exists() is True
# and get_child_arguments() takes the `else: args += sys.argv` branch (the branch
# the F2P test_xoptions exercises). The conformance script's own file qualifies.
SCRIPT_PATH = os.path.abspath(__file__)


# --- the R/I shadow: relaunchArgvSpec / xFlag / warnFlag, transliterated ------

def warn_flag(o):
    """warnFlag (Solution.lean): '-W' ++ option text."""
    return "-W%s" % o


def x_flag(key, value):
    """xFlag (Solution.lean): -Xkey for a bare option (value is True), else
    -Xkey=value. Mirrors `value is True` (identity, NOT truthiness)."""
    return "-X%s" % key if value is True else "-X%s=%s" % (key, value)


def shadow_argv(executable, warnopts, is_cpython, xopts, tail):
    """relaunchArgvSpec (Solution.lean) transliterated to str over the real repo
    types. The X-option flags are appended only on CPython, in `xopts` order.
    `tail` is the full trailing argument list (the `else: args += sys.argv`
    branch appends the entire sys.argv, incl. sys.argv[0])."""
    out = [executable]
    out += [warn_flag(o) for o in warnopts]
    if is_cpython:
        out += [x_flag(k, v) for k, v in xopts.items()]
    out += tail
    return out


# --- the oracle: the real patched get_child_arguments() -----------------------

def oracle_argv(executable, warnopts, is_cpython, xopts, tail):
    """patch.diff's behaviour: run the patched get_child_arguments() with the
    interpreter environment mocked exactly as TestChildArguments does, driving the
    `else: args += sys.argv` branch (__spec__ = None, sys.argv[0] exists).
    `tail` is the full mocked sys.argv (its first element is the existing script
    path so Path(sys.argv[0]).exists() is True)."""
    import __main__
    from django.utils import autoreload

    impl = types.SimpleNamespace(name=("cpython" if is_cpython else "pypy"))
    with mock.patch.object(__main__, "__spec__", None), \
         mock.patch.object(sys, "argv", list(tail)), \
         mock.patch.object(sys, "warnoptions", list(warnopts)), \
         mock.patch.object(sys, "_xoptions", dict(xopts)), \
         mock.patch.object(sys, "executable", executable), \
         mock.patch.object(sys, "implementation", impl, create=True):
        return list(autoreload.get_child_arguments())


def fuzz_inputs(n, rng):
    executable = "/usr/bin/python"
    # The trailing arg list is the full mocked sys.argv; its first element must be
    # an existing path so the `else: args += sys.argv` branch is taken.
    def tail(*rest):
        return [SCRIPT_PATH] + list(rest)

    # boundary cases first (plan §4.1 step 4)
    # F2P test_xoptions: no warnopts, {'utf8': True, 'a': 'b'}, cpython
    yield (executable, [], True, {"utf8": True, "a": "b"}, tail("runserver"))
    # no xoptions at all (pre-existing behaviour)
    yield (executable, [], True, {}, tail("runserver"))
    # warnopts only, no xoptions
    yield (executable, ["error"], True, {}, tail("runserver"))
    # bare option only
    yield (executable, [], True, {"dev": True}, tail("runserver"))
    # keyed option only
    yield (executable, [], True, {"utf8": "1"}, tail("runserver"))
    # the tricky case: a value that is the *string* "True" is keyed, not bare
    yield (executable, [], True, {"k": "True"}, tail("runserver"))
    # value False (a non-True object) -> keyed "-Xk=False"
    yield (executable, [], True, {"k": False}, tail("runserver"))
    # NON-cpython: xoptions must be dropped entirely
    yield (executable, ["error"], False, {"utf8": True, "a": "b"}, tail("runserver"))
    # warnopts + xoptions together
    yield (executable, ["error", "ignore"], True,
           {"utf8": True, "a": "b", "tracemalloc": "5"}, tail("runserver", "-v3"))
    # empty trailing argv beyond the script path
    yield (executable, [], True, {"utf8": True}, tail())

    warn_pool = ["error", "ignore", "default", "all", "module", "once"]
    key_pool = ["utf8", "a", "dev", "tracemalloc", "int_max_str_digits",
                "importtime", "frozen_modules", "no_debug_ranges", "k1", "k2"]
    val_pool = [True, "b", "1", "5", "True", "False", "yes", "", "a=b", "0"]
    argv_pool = ["runserver", "-v3", "0.0.0.0:8005", "--noreload", "migrate"]
    for _ in range(n):
        is_cpython = rng.random() < 0.7
        nw = rng.randint(0, 3)
        warnopts = [rng.choice(warn_pool) for _ in range(nw)]
        nx = rng.randint(0, 4)
        xopts = {}
        # dict keys must be unique; sample without replacement
        keys = rng.sample(key_pool, min(nx, len(key_pool)))
        for k in keys:
            xopts[k] = rng.choice(val_pool)
        na = rng.randint(0, 3)
        rest = [rng.choice(argv_pool) for _ in range(na)]
        yield (executable, warnopts, is_cpython, xopts, tail(*rest))


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for executable, warnopts, is_cpython, xopts, tail in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_argv(executable, warnopts, is_cpython, xopts, tail)
        oracle = oracle_argv(executable, warnopts, is_cpython, xopts, tail)
        if shadow != oracle:
            disagreements.append(
                ((warnopts, is_cpython, xopts, tail), shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for cfg, sh, orc in disagreements:
            print("  config=%r shadow=%r oracle=%r" % (cfg, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of relaunchArgv (relaunchArgvSpec) agrees with "
          "patch.diff behaviour on %d configs (seed=%d), 0 disagreements."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
