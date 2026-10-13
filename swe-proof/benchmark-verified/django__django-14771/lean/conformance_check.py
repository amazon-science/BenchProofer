#!/usr/bin/env python3
r"""G-CONF for django__django-14771.

The gold patch is already applied to /testbed when this runs. We compare the
R/I Python shadow of `implementation_reloaderArgv` (the Lean impl, transliterated
op-for-op per refinement.md) against the REAL patched
`django.utils.autoreload.get_child_arguments`, driven over the modeled relaunch
scenario (`__main__.__spec__` is None and the invocation script exists, so the
function returns `args` after appending `sys.argv`), over >=1e5 fuzzed inputs.
Zero disagreements => exit 0.

Modeled object (mapping.md / refinement.md): the relaunch argument vector. Post
patch it is, in order: the executable, one `-W<o>` per warning option, then — on
CPython only — one `-X<key>` / `-X<key>=<value>` per `sys._xoptions` item, then
the original `sys.argv`.

  * Oracle  = the REAL patched `get_child_arguments`, called with `sys.executable`,
              `sys.warnoptions`, `sys.implementation.name`, `sys._xoptions`,
              `sys.argv` and `__main__.__spec__` mocked to the fuzzed input; the
              invocation script is pointed at a real existing file so the common
              relaunch path is taken.
  * Shadow  = the op-for-op transliteration of implementation_reloaderArgv.

Type bijection (mapping.md):
  executable:String <-> sys.executable:str;
  warnoptions:List String <-> sys.warnoptions:list[str];
  isCpython:Bool <-> (sys.implementation.name == 'cpython');
  xoptions:List (String x XVal) <-> sys._xoptions.items()
      (XVal.flag <-> value is True; XVal.val s <-> value == s:str);
  argv:List String <-> sys.argv:list[str];
  result:List String <-> the returned arg list (PosixPath/str compared as str).
stdlib-only.
"""
import os
import random
import sys
import tempfile
from unittest import mock

import django.__main__
from django.utils import autoreload


# ---- shadow: op-for-op transliteration of implementation_reloaderArgv -------

def warn_arg(o):
    return "-W" + o


def xopt_arg(key, value):
    # XVal.flag <-> value is True  ;  XVal.val v <-> value is a str
    if value is True:
        return "-X" + key
    return "-X" + key + "=" + str(value)


def shadow(executable, warnoptions, is_cpython, xoptions, argv):
    args = [executable]
    for o in warnoptions:
        args = args + [warn_arg(o)]
    if is_cpython:
        for key, value in xoptions:
            args = args + [xopt_arg(key, value)]
    args = args + argv
    return args


# ---- oracle: the REAL patched get_child_arguments ---------------------------

def oracle(script_path, executable, warnoptions, impl_name, xoptions, extra_argv):
    """Drive the real function in the modeled relaunch scenario.

    sys.argv[0] = an existing script (so py_script.exists() is True and __spec__
    is None => the function hits `else: args += sys.argv`).
    """
    argv = [script_path] + list(extra_argv)
    import types as _t
    impl = _t.SimpleNamespace(name=impl_name)
    with mock.patch.object(sys, "executable", executable), \
         mock.patch.object(sys, "warnoptions", list(warnoptions)), \
         mock.patch.object(sys, "argv", list(argv)), \
         mock.patch.object(sys, "implementation", impl), \
         mock.patch.object(sys, "_xoptions", dict(xoptions)), \
         mock.patch.object(django.__main__, "__spec__", None, create=True), \
         mock.patch.dict(sys.modules, {"__main__": django.__main__}):
        out = autoreload.get_child_arguments()
    return [str(x) for x in out]


# ---- fuzz -------------------------------------------------------------------

_TOK = ["a", "b", "utf8", "dev", "key", "x=y", "1", "", "frozen_modules"]
_XKEYS = ["utf8", "dev", "a", "frozen_modules", "int_max_str_digits", "tracemalloc"]
_IMPLS = ["cpython", "pypy", "jython", "graalpy"]


def rand_list(rng, pool, lo, hi):
    return [rng.choice(pool) for _ in range(rng.randint(lo, hi))]


def rand_xoptions(rng):
    n = rng.randint(0, 4)
    items = []
    used = set()
    for _ in range(n):
        k = rng.choice(_XKEYS)
        if k in used:           # dicts have unique keys
            continue
        used.add(k)
        # value is True (flag) or a string (valued)
        if rng.random() < 0.5:
            items.append((k, True))
        else:
            items.append((k, rng.choice(["1", "y", "1000", "", "a=b"])))
    return items


FIXED = [
    # executable, warnoptions, impl_name, xoptions, extra_argv
    ("/usr/bin/python", [], "cpython", [], ["runserver"]),
    ("/usr/bin/python", [], "cpython", [("utf8", True), ("a", "b")], ["runserver"]),
    ("/usr/bin/python", ["error"], "cpython", [], ["runserver"]),
    ("/usr/bin/python", ["all"], "cpython", [("dev", True)], ["runserver", "-v3"]),
    ("/usr/bin/python", [], "pypy", [("utf8", True)], ["runserver"]),  # non-cpython: -X dropped
    ("/usr/bin/python", ["error"], "jython", [("a", "b")], ["x"]),
    ("/usr/bin/python", [], "cpython", [("k", "")], ["runserver"]),     # empty valued option
]


def main():
    rng = random.Random(14771)  # pinned seed (mapping.md)
    N = 100_000
    disagreements = 0
    first = None
    with tempfile.TemporaryDirectory() as tmp:
        script = os.path.join(tmp, "manage.py")
        with open(script, "w") as fh:
            fh.write("# manage.py\n")
        for i in range(N):
            if i < len(FIXED):
                executable, warnoptions, impl_name, xoptions, extra_argv = FIXED[i]
            else:
                executable = rng.choice(["/usr/bin/python", "/opt/py/python3"])
                warnoptions = rand_list(rng, _TOK, 0, 3)
                impl_name = rng.choice(_IMPLS)
                xoptions = rand_xoptions(rng)
                extra_argv = rand_list(rng, _TOK, 0, 3)

            o = oracle(script, executable, warnoptions, impl_name, xoptions, extra_argv)

            is_cpython = (impl_name == "cpython")
            # shadow's argv == the full sys.argv the oracle saw = [script] + extra
            sh = shadow(executable, warnoptions, is_cpython, xoptions,
                        [script] + list(extra_argv))

            if o != sh:
                disagreements += 1
                if first is None:
                    first = (executable, warnoptions, impl_name, xoptions,
                             extra_argv, o, sh)
    if disagreements:
        print("G-CONF FAIL: %d/%d disagreements; first=%r" % (disagreements, N, first))
        return 1
    print("G-CONF OK: %d inputs, 0 disagreements" % N)
    return 0


if __name__ == "__main__":
    sys.exit(main())
