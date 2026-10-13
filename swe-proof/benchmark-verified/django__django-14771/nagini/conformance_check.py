#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-14771 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Invariant/Assert) stripped, running on a small immutable-tuple
PSeq shim. The @Pure helpers (dash_x/eq/dash_m/windows_recovery/
is_module_launch/option_token/option_tokens) copy over as plain functions.
There are no @ContractOnly callees in this bundle.

ORACLE: the REAL patched repo function the model models per mapping.md --
``django.utils.autoreload.get_child_arguments`` (the gate applies patch.diff
to /testbed before this script runs). The function reads its whole input from
process state, so each trial installs a controlled process state (argument
vector, warning options, implementation options, implementation name, the
reported __main__ spec) via save/patch/restore around one real call.

Type bridge (mapping.md section 2):
  * str -> List[int] of Unicode code points (``ord`` per character);
  * list-of-str (the argument vector, the leading arguments, the result)
    -> PSeq of code-point PSeqs;
  * the implementation-option dict -> three index-aligned sequences
    (names, per-option value-is-the-boolean-present-sentinel, rendered
    values), in dict iteration order;
  * the interpreter-identity / entry-script-existence observations -> the two
    booleans the model takes as parameters;
  * the leading arguments (interpreter path + warning options) are computed
    by an unchanged step before the modeled insertion point and bound as the
    opaque ``prefix`` parameter;
  * a module launch's re-invoked name is selected from the reported spec by
    an unchanged selection step (parent package for a dotted-main launch with
    a truthy parent, else the spec name) and bound as ``launch_package``;
  * the platform-specific recovery branch taken when the entry script is
    absent (an alternate-entrypoint return or an error) is collapsed to the
    single sentinel ``windows_recovery()`` -- a real outcome on that branch
    conforms iff the shadow yields the sentinel (documented abstraction,
    unchanged by the patch).

Input domain: preconditions are (a) the three option sequences index-aligned
and (b) at least one argument-vector element; every generated process state
satisfies both by construction. Module-launch spec names are generated
non-empty, matching the invariant of real module specs (an empty selected
name is unreachable in the repo; see mapping.md / the recorded panel note).

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz trials.
Pinned fuzz seed: 14771 (recorded here). Exit 0 iff zero disagreements; on
disagreement prints the input and both outputs and exits 1. stdlib only.
"""
import json
import random
import sys
import tempfile
import types
from pathlib import Path

SEED = 14771
N_FUZZ = 100000


# --- PSeq shim: immutable sequence with the operations the model uses ---------

class PSeq(object):
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls.__new__(cls)
        s._t = tuple(t)
        return s

    def take(self, n):
        return PSeq._wrap(self._t[:n])

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

    def __add__(self, other):
        return PSeq._wrap(self._t + other._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self._t)

    def __repr__(self):
        return "PSeq%r" % (self._t,)


# --- pure helpers from model.py, contracts stripped ---------------------------

def dash_x():
    # The implementation-option flag '-X'.
    return PSeq(45, 88)


def eq():
    # The name/value separator '='.
    return PSeq(61)


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


def option_token(key, is_flag, val):
    if is_flag:
        return dash_x() + key
    return dash_x() + key + eq() + val


def option_tokens(keys, flags, vals):
    if len(keys) == 0:
        return PSeq(PSeq(0)).take(0)
    return PSeq(option_token(keys[0], flags[0], vals[0])) \
        + option_tokens(keys.drop(1), flags.drop(1), vals.drop(1))


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def child_arguments(prefix,
                    is_reference_impl,
                    opt_keys,
                    opt_is_flag,
                    opt_vals,
                    package_reported,
                    launch_package,
                    argv,
                    script_exists):
    empty = PSeq(PSeq(0)).take(0)  # type: PSeq[PSeq[int]]
    options = empty
    if is_reference_impl:
        i = len(opt_keys)
        while i > 0:
            # (stripped Invariant/Assert lines carried only proof-side facts)
            tok = option_token(opt_keys[i - 1], opt_is_flag[i - 1],
                               opt_vals[i - 1])
            options = PSeq(tok) + options
            i = i - 1
    leading = prefix + options
    if package_reported and len(launch_package) > 0:
        return leading + PSeq(dash_m(), launch_package) + argv.drop(1)
    elif not script_exists:
        return windows_recovery()
    else:
        return leading + argv
    # impl-end


# --- bridge helpers ------------------------------------------------------------

def cp(s):
    """A str rendered as the model carrier: a PSeq of Unicode code points."""
    return PSeq._wrap(ord(ch) for ch in s)


def cps(strings):
    """A list of str rendered as a PSeq of code-point PSeqs."""
    return PSeq._wrap(cp(s) for s in strings)


def render_value(value):
    """The string an option value interpolates to on the command line (the
    model's value carrier for a non-sentinel value)."""
    return "%s" % (value,)


def plain(seq):
    """A PSeq tree lowered to nested tuples for printing/comparison."""
    return tuple(plain(x) if isinstance(x, PSeq) else x for x in seq._t)


RECOVERY = plain(windows_recovery())


class FakeSpec(object):
    """A stand-in for the reported __main__ module spec: only the two
    attributes the callee reads (name, parent)."""

    def __init__(self, name, parent):
        self.name = name
        self.parent = parent

    def __repr__(self):
        return "FakeSpec(name=%r, parent=%r)" % (self.name, self.parent)


def selected_module_name(spec):
    """The module name a module launch re-invokes, selected from the reported
    spec by the unchanged selection step: the parent package when the spec
    names a dotted main entry and has a truthy parent, else the spec name.
    This is the mapping.md binding for the model's launch_package carrier."""
    if (spec.name == '__main__' or spec.name.endswith('.__main__')) \
            and spec.parent:
        return spec.parent
    return spec.name


def run_real(get_child_arguments, argv, warnoptions, xoptions, impl_name, spec):
    """Call the REAL patched callee under a controlled process state.
    Returns ('ok', <list>) or ('raise', <exception repr>)."""
    old_argv = sys.argv
    old_warn = sys.warnoptions
    old_x = sys._xoptions
    old_impl_name = sys.implementation.name
    old_main = sys.modules.get('__main__')
    fake_main = types.ModuleType('__sbu_conf_main__')
    fake_main.__spec__ = spec  # None => no launch package reported
    try:
        sys.argv = list(argv)
        sys.warnoptions = list(warnoptions)
        sys._xoptions = dict(xoptions)
        sys.implementation.name = impl_name
        sys.modules['__main__'] = fake_main
        try:
            out = get_child_arguments()
            return ('ok', out)
        except RuntimeError as exc:
            return ('raise', repr(exc))
    finally:
        sys.argv = old_argv
        sys.warnoptions = old_warn
        sys._xoptions = old_x
        sys.implementation.name = old_impl_name
        if old_main is None:
            del sys.modules['__main__']
        else:
            sys.modules['__main__'] = old_main


def check(get_child_arguments, argv, warnoptions, xoptions, impl_name, spec):
    """One differential trial. Returns an error string on disagreement."""
    # -- model inputs (the bridge) -----------------------------------------
    prefix_strs = [sys.executable] + ['-W%s' % o for o in warnoptions]
    prefix = cps(prefix_strs)
    is_reference_impl = (impl_name == 'cpython')
    opt_keys = cps(xoptions.keys())
    opt_is_flag = PSeq._wrap(v is True for v in xoptions.values())
    opt_vals = cps("" if v is True else render_value(v)
                   for v in xoptions.values())
    package_reported = spec is not None
    launch_package = cp(selected_module_name(spec)) if spec is not None \
        else cp("")
    argv_seq = cps(argv)
    script_exists = Path(argv[0]).exists()

    shadow = plain(child_arguments(prefix, is_reference_impl, opt_keys,
                                   opt_is_flag, opt_vals, package_reported,
                                   launch_package, argv_seq, script_exists))

    kind, out = run_real(get_child_arguments, argv, warnoptions, xoptions,
                         impl_name, spec)

    ctx = ("argv=%r warnoptions=%r xoptions=%r impl=%r spec=%r "
           "script_exists=%r" % (argv, warnoptions, xoptions, impl_name,
                                 spec, script_exists))

    if spec is None and not script_exists:
        # Recovery branch: the model collapses it to the sentinel; the real
        # outcome must be one of the recovery shapes (an alternate-entrypoint
        # return containing a filesystem path object, or the error).
        if shadow != RECOVERY:
            return ("DISAGREEMENT (recovery expected) on %s:\n"
                    "  shadow = %r (not the recovery sentinel)" % (ctx, shadow))
        is_recovery_shape = (kind == 'raise'
                             or any(isinstance(el, Path) for el in out))
        if not is_recovery_shape:
            return ("DISAGREEMENT on %s:\n"
                    "  shadow = recovery sentinel\n"
                    "  real   = ordinary return %r" % (ctx, out))
        return None

    # Ordinary branches: the real result is a list of str; lower and compare.
    if kind != 'ok':
        return ("DISAGREEMENT on %s:\n"
                "  shadow = %r\n"
                "  real raised %s" % (ctx, shadow, out))
    real_lowered = tuple(tuple(ord(ch) for ch in el) for el in out)
    if shadow != real_lowered:
        return ("DISAGREEMENT on %s:\n"
                "  shadow (impl region) = %r == %r\n"
                "  real (patched repo)  = %r == %r"
                % (ctx, shadow,
                   tuple("".join(chr(c) for c in t) for t in shadow),
                   real_lowered, tuple(out)))
    return None


def main():
    from django.utils.autoreload import get_child_arguments

    # Filesystem fixtures (created once, reused across trials):
    tmp = tempfile.mkdtemp(prefix="sbu_conf_14771_")
    existing = str(Path(tmp) / "entry.py")
    Path(existing).write_text("# fixture entry script\n")
    missing_plain = str(Path(tmp) / "gone" / "entry.py")          # error path
    exe_dir = Path(tmp) / "exe"
    exe_dir.mkdir()
    missing_with_exe = str(exe_dir / "entry.py")                  # alt-exe path
    (exe_dir / "entry.exe").write_text("")
    script_dir = Path(tmp) / "script"
    script_dir.mkdir()
    missing_with_script = str(script_dir / "entry.py")            # alt-script path
    (script_dir / "entry.py-script.py").write_text("")
    existing_scripts = [existing, __file__]
    missing_scripts = [missing_plain, missing_with_exe, missing_with_script]

    specs = [
        None,
        FakeSpec('django.__main__', 'django'),   # dotted main, truthy parent
        FakeSpec('__main__', 'pkg'),             # bare main, truthy parent
        FakeSpec('__main__', ''),                # bare main, empty parent
        FakeSpec('foo.bar.__main__', ''),        # dotted main, empty parent
        FakeSpec('plainmod', ''),                # ordinary module name
        FakeSpec('plainmod', 'ignored_parent'),  # parent ignored (name kept)
    ]
    xoption_cases = [
        {},
        {'utf8': True},
        {'a': 'b'},
        {'utf8': True, 'a': 'b'},
        {'a': 'b', 'utf8': True},
        {'importtime': True, 'tracemalloc': '5', 'utf8': True},
        {'opt': ''},
        {'k': 'v=w'},
        {'truthy': 'True'},
        {'falsey': False},
        {'n': 0},
        {'n': 1},
    ]
    warn_cases = [[], ['error'], ['error', 'ignore::DeprecationWarning']]
    impl_names = ['cpython', 'pypy']
    argv_tails = [[], ['runserver'], ['runserver', '--noreload', '0:8000']]

    checked = 0
    disagreements = 0

    # --- boundary sweep: full cross-product of the structured cases ----------
    for spec in specs:
        for xo in xoption_cases:
            for warn in warn_cases:
                for impl in impl_names:
                    for tail in argv_tails:
                        for script in (existing_scripts + missing_scripts):
                            argv = [script] + tail
                            err = check(get_child_arguments, argv, warn, xo,
                                        impl, spec)
                            checked += 1
                            if err:
                                print(err)
                                return 1

    # --- randomized fuzz (pinned seed) ----------------------------------------
    rng = random.Random(SEED)
    key_alphabet = "abcdefghijklmnopqrstuvwxyz_0123456789"
    val_alphabet = key_alphabet + "=.-/ "
    name_pool = ['django.__main__', '__main__', 'a.b.c.__main__',
                 'plain', 'pkg.sub', 'x']
    parent_pool = ['', 'django', 'a.b.c', 'pkg', 'x_y']
    warn_pool = ['error', 'ignore', 'default', 'always', 'once',
                 'error::DeprecationWarning', 'ignore::UserWarning']
    arg_pool = ['runserver', '--noreload', '8000', '0.0.0.0:8000',
                '--settings=proj.settings', 'extra arg', 'ünïcode', '']
    for _ in range(N_FUZZ):
        n = rng.randint(0, 5)
        xo = {}
        for _k in range(n):
            klen = rng.randint(1, 8)
            key = "".join(rng.choice(key_alphabet) for _c in range(klen))
            r = rng.random()
            if r < 0.4:
                xo[key] = True
            elif r < 0.7:
                vlen = rng.randint(0, 8)
                xo[key] = "".join(rng.choice(val_alphabet)
                                  for _c in range(vlen))
            elif r < 0.85:
                xo[key] = rng.randint(0, 1000)
            else:
                xo[key] = rng.choice([False, 'True', 'true', '0', ''])
        warn = [rng.choice(warn_pool) for _w in range(rng.randint(0, 3))]
        impl = rng.choice(['cpython', 'cpython', 'cpython', 'pypy', 'jython'])
        r = rng.random()
        if r < 0.45:
            spec = None
        else:
            spec = FakeSpec(rng.choice(name_pool), rng.choice(parent_pool))
        r = rng.random()
        if r < 0.7:
            script = rng.choice(existing_scripts)
        else:
            script = rng.choice(missing_scripts)
        argv = [script] + [rng.choice(arg_pool)
                           for _a in range(rng.randint(0, 4))]
        err = check(get_child_arguments, argv, warn, xo, impl, spec)
        checked += 1
        if err:
            print(err)
            return 1

    print("G-CONF OK: shadow impl region == real patched child-argument "
          "reconstruction on %d process states (boundary cross-product + %d "
          "fuzz, seed %d); 0 disagreements." % (checked, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": disagreements,
                      "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
