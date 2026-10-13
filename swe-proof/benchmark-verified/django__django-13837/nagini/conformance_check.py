#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13837 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls stripped (there are none inside the impl region; the Requires/Ensures
live outside it). The @Pure helpers (dash_m / windows_recovery /
is_module_launch) copy over as plain functions. PSeq is a plain immutable
tuple shim providing the operations the impl uses (construction, `+`,
`drop`, `len`). There are no @ContractOnly callees in this bundle.

ORACLE: the REAL repo function the model models per mapping.md --
`django.utils.autoreload.get_child_arguments()` at /testbed with the diff
applied by the gate before this script runs (this script applies nothing
itself; PYTHONPATH=/testbed resolves the in-tree source).

Type bridge (mapping.md section 2): each runtime observable maps to one
model input --
  [sys.executable] + ['-W%s' % o for o in sys.warnoptions]
                                     -> prefix: PSeq[PSeq[int]] (code points)
  __main__.__spec__ is not None      -> package_reported: bool
  __main__.__spec__.parent ('' when the spec is absent)
                                     -> launch_package: PSeq[int]
  sys.argv                           -> argv: PSeq[PSeq[int]]
  Path(sys.argv[0]).exists()         -> script_exists: bool
str <-> PSeq[int] of Unicode code points; list[str] <-> PSeq[PSeq[int]].
The oracle is driven by save/patch/restore of sys.argv, sys.warnoptions and
the __main__ module's __spec__ attribute (real importlib.machinery.ModuleSpec
objects, or None), with argv[0] pointing at real filesystem fixtures so the
existence probe is genuine.

Outcome bridge: the platform-specific branch taken when the entry script is
absent is represented abstractly in the model by the windows_recovery()
sentinel (that branch is unchanged and unmodeled). A real outcome maps to
model space as follows: a raised RuntimeError -> the sentinel; a returned
alternate-entrypoint vector (one of the two shapes that branch can build,
computed exactly from the fixture) -> the sentinel; any other returned
list[str] -> its code-point encoding. Any other outcome is a disagreement.
This keeps the check tight: a modeled branch returning the wrong vector, or
the unmodeled branch being taken/skipped at the wrong time, is flagged.

>= 1e5 Requires-satisfying inputs (len(argv) >= 1 always holds: argv[0] is
the fixture path): a structured boundary grid over launch shape x entry
existence x warnoptions x argv tails (including the alternate-entrypoint
fixtures), then 100000 fuzz configurations. Pinned fuzz seed: 138370.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outcomes and exits 1. stdlib only (random; hypothesis not needed).
"""
import importlib.machinery
import json
import random
import sys
import tempfile
from pathlib import Path

SEED = 138370
N_FUZZ = 100_000


# --- PSeq shim: immutable sequence with the operations the impl uses ----------

class PSeq(tuple):
    def __new__(cls, *elems):
        return super().__new__(cls, elems)

    def __add__(self, other):
        return tuple.__new__(PSeq, tuple(self) + tuple(other))

    def drop(self, n):
        return tuple.__new__(PSeq, tuple(self)[n:])


# --- pure helpers from model.py, @Pure decorators dropped ---------------------

def dash_m():
    # The module-execution flag '-m'.
    return PSeq(45, 109)


def windows_recovery():
    # Abstract sentinel for the unchanged platform-specific recovery path taken
    # when the entry script no longer exists. Distinct from any normally-built
    # argument vector (it carries the single recovery marker element [0]).
    return PSeq(PSeq(0))


def is_module_launch(package_reported, launch_package):
    return package_reported and len(launch_package) > 0


# --- the impl region of model.py, verbatim ------------------------------------

def child_arguments(prefix, package_reported, launch_package, argv,
                    script_exists):
    if package_reported and len(launch_package) > 0:
        return prefix + PSeq(dash_m(), launch_package) + argv.drop(1)
    elif not script_exists:
        return windows_recovery()
    else:
        return prefix + argv


# --- str/list[str] <-> code-point PSeq encoders --------------------------------

def enc_str(s):
    return tuple.__new__(PSeq, tuple(ord(c) for c in s))


def enc_list(xs):
    return tuple.__new__(PSeq, tuple(enc_str(x) for x in xs))


# --- driving the REAL function -------------------------------------------------

def spec_for_package(package):
    """A genuine ModuleSpec shaped like the one the import system attaches for
    a module launch of PACKAGE (running its __main__ submodule): its .parent
    is PACKAGE."""
    return importlib.machinery.ModuleSpec(
        "%s.__main__" % package, loader=None, is_package=False)


def spec_toplevel():
    """A genuine ModuleSpec of a top-level __main__ (directory/zip launch):
    its .parent is the empty string."""
    return importlib.machinery.ModuleSpec("__main__", loader=None,
                                          is_package=False)


def run_real(get_child_arguments, main_mod, spec, argv, warnoptions):
    """Call the real function under the given process state; return
    ('ret', list) or ('raised', message)."""
    old_argv, old_wo = sys.argv, sys.warnoptions[:]
    had_spec = hasattr(main_mod, "__spec__")
    old_spec = getattr(main_mod, "__spec__", None)
    sys.argv = list(argv)
    sys.warnoptions[:] = list(warnoptions)
    main_mod.__spec__ = spec
    try:
        try:
            return ("ret", get_child_arguments())
        except RuntimeError as e:
            return ("raised", str(e))
    finally:
        sys.argv = old_argv
        sys.warnoptions[:] = old_wo
        if had_spec:
            main_mod.__spec__ = old_spec
        else:
            del main_mod.__spec__


def bridge_real_outcome(outcome, prefix, argv):
    """Map the real outcome into model space. The two alternate-entrypoint
    vector shapes the script-absent branch can build (computed exactly from
    argv[0]) and a raised RuntimeError all map to the abstract sentinel;
    any other returned list[str] maps to its code-point encoding; anything
    else is reported as-is (guaranteed disagreement)."""
    kind, val = outcome
    if kind == "raised":
        return windows_recovery()
    if not (isinstance(val, list) and all(isinstance(x, str) for x in val)):
        return ("non-list-of-str", val)
    py_script = Path(argv[0])
    exe_form = [str(py_script.with_suffix(".exe"))] + list(argv[1:])
    script_form = (list(prefix)
                   + [str(py_script.with_name("%s-script.py" % py_script.name))]
                   + list(argv[1:]))
    if val == exe_form or val == script_form:
        return windows_recovery()
    return enc_list(val)


def check_one(get_child_arguments, main_mod, spec, argv, warnoptions):
    prefix = [sys.executable] + ["-W%s" % o for o in warnoptions]
    package_reported = spec is not None
    launch_package = spec.parent if spec is not None else ""
    script_exists = Path(argv[0]).exists()
    assert len(argv) >= 1  # the model's Requires holds by construction
    shadow = child_arguments(enc_list(prefix), package_reported,
                             enc_str(launch_package), enc_list(argv),
                             script_exists)
    outcome = run_real(get_child_arguments, main_mod, spec, argv, warnoptions)
    real = bridge_real_outcome(outcome, prefix, argv)
    if real != shadow:
        return ("DISAGREEMENT\n"
                "  spec=%r argv=%r warnoptions=%r\n"
                "  bridged(package_reported=%r launch_package=%r "
                "script_exists=%r prefix=%r)\n"
                "  shadow=%r\n  real outcome=%r -> %r"
                % (spec, argv, warnoptions, package_reported, launch_package,
                   script_exists, prefix, shadow, outcome, real))
    return None


# --- input domain ---------------------------------------------------------------

def make_fixtures():
    """Filesystem fixtures for argv[0]: existing entry files, absent paths,
    and absent paths whose alternate-entrypoint siblings exist."""
    root = Path(tempfile.mkdtemp(prefix="conf_entry_"))
    existing = []
    for name in ("entry.py", "manage.py", "run", "tool.pyw"):
        p = root / name
        p.write_text("# fixture\n")
        existing.append(str(p))
    absent = [str(root / "gone.py"), str(root / "missing"),
              str(root / "sub" / "nested.py")]
    # sibling with the alternate executable suffix exists
    exe_base = root / "winentry.py"
    (root / "winentry.exe").write_text("")
    absent_exe = str(exe_base)
    # sibling with the alternate -script.py name exists
    script_base = root / "winscript"
    (root / "winscript-script.py").write_text("# fixture\n")
    absent_script = str(script_base)
    return existing, absent, absent_exe, absent_script


def boundary_specs():
    specs = [None, spec_toplevel()]
    for pkg in ("django", "pkg", "a.b.c", "x", "some_app.management",
                "utils_tests.test_module", "päckage"):
        specs.append(spec_for_package(pkg))
    return specs


ARGV_TAILS = [
    [],
    ["runserver"],
    ["runserver", "0.0.0.0:8000"],
    ["--noreload"],
    [""],
    ["café", "--opt=väl"],
    ["a", "b", "c", "d"],
]

WARNOPTS = [
    [],
    ["all"],
    ["ignore::DeprecationWarning", "error"],
]


def main():
    # REAL repo symbol (the function the model models, per mapping.md):
    from django.utils.autoreload import get_child_arguments
    import __main__ as main_mod

    existing, absent, absent_exe, absent_script = make_fixtures()
    all_entry_paths = existing + absent + [absent_exe, absent_script]

    checked = 0
    n_boundary = 0

    # --- structured boundary grid ---------------------------------------
    for spec in boundary_specs():
        for entry in all_entry_paths:
            for tail in ARGV_TAILS:
                for wo in WARNOPTS:
                    err = check_one(get_child_arguments, main_mod, spec,
                                    [entry] + tail, wo)
                    if err:
                        print(err)
                        return 1
                    checked += 1
                    n_boundary += 1

    # --- fuzz -------------------------------------------------------------
    rng = random.Random(SEED)
    name_alphabet = ("abcdefghijklmnopqrstuvwxyz"
                     "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"
                     "éüα中")
    arg_alphabet = name_alphabet + " -./=:%$\"'\\☃"

    def rand_name():
        parts = [
            "".join(rng.choice(name_alphabet)
                    for _ in range(rng.randint(1, 8)))
            for _ in range(rng.randint(1, 3))
        ]
        return ".".join(parts)

    def rand_arg():
        return "".join(rng.choice(arg_alphabet)
                       for _ in range(rng.randint(0, 12)))

    for _ in range(N_FUZZ):
        shape = rng.random()
        if shape < 0.45:
            spec = spec_for_package(rand_name())   # module launch
        elif shape < 0.60:
            spec = spec_toplevel()                 # top-level __main__
        else:
            spec = None                            # plain script launch
        entry = rng.choice(all_entry_paths)
        tail = [rand_arg() for _ in range(rng.randint(0, 4))]
        wo = [rand_arg() for _ in range(rng.randint(0, 2))]
        err = check_one(get_child_arguments, main_mod, spec,
                        [entry] + tail, wo)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real child-argument reconstruction on "
          "%d inputs (%d boundary + %d fuzz, seed %d)."
          % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
