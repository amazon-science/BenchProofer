#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13658 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls stripped (Invariant/Assert lines removed; no Requires/Ensures live in
the impl region). The @Pure helpers `bootstrap_name`, `module_invocation`
and `program_name` are copied over as plain functions; `PSeq` becomes a
plain tuple and `ToSeq` materializes a list as a tuple. The minimal
`Parser`/`Utility` carrier classes are copied with their contract lines
stripped. There are no @ContractOnly callees in this bundle.

ORACLE: the REAL patched repo code the model models per mapping.md — the
option-pre-scan parser construction inside
`django.core.management.ManagementUtility.execute`. The gate applies
patch.diff to /testbed before this script runs; PYTHONPATH=/testbed makes
the patched code importable. Because the construction is embedded in a
method that then goes on to parse options and dispatch a subcommand, the
oracle observes it through a recording subclass of the real parser class:
the subclass lets the REAL constructor run to completion (so the real
library's program-name handling — explicit value vs ambient default — is
fully exercised), records the program name the parser reports, and then
aborts the surrounding method via a sentinel exception. The first parser
the method constructs is exactly the pre-scan parser under specification.

Type bridge (mapping.md §2):
  * str program names / basenames <-> List[int] of Unicode code points
    (s[k] <-> ord(s[k]); equality of str <-> sequence equality);
  * the model's inputs are already basenames — the path split happens at
    the boundary — so the driver hands the real utility an argument vector
    whose first element is (optional directory prefix +) the basename, and
    hands the shadow the basename's code points;
  * `Utility.sys_argv0_basename` models the basename of the ambient
    process-wide first argument: the driver pins `sys.argv[0]` per input
    (usually DISAGREEING with the utility's own first argument, which is
    the discriminating scenario) and the real parser's reported program
    name must still match the shadow, which depends on the utility's own
    first argument alone;
  * shadow output `parser.prog: List[int]` vs real `parser.prog: str`
    compare via ''.join(chr(c) ...) == real.

Input domain (the model's Requires are permission-only, so the semantic
domain is: any code-point list that is a basename, i.e. contains no path
separator): boundary cases cover the empty basename, the bootstrap
basename with near-miss variants, typical launcher names, the
module-invocation string itself as a literal basename, dotfiles, '.', '..',
unicode, and long names — each crossed with agreeing/disagreeing/unusual
ambient first arguments and various directory prefixes; fuzz draws random
separator-free basenames with a bias toward the bootstrap name and
near-misses, random prefixes, and an independently random ambient
sys.argv[0].

>= 1e5 Requires-satisfying inputs: boundary grid + 100000 fuzz cases.
Pinned fuzz seed: 13658.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import os
import random
import string
import sys

SEED = 13658
N_FUZZ = 100_000


# --- shims for the model's sequence carrier -----------------------------------

def PSeq(*args):
    return tuple(args)


def ToSeq(xs):
    return tuple(xs)


# --- pure helpers from model.py, decorators stripped ---------------------------

def bootstrap_name():
    # The module-bootstrap basename '__main__.py'.
    return PSeq(95, 95, 109, 97, 105, 110, 95, 95, 46, 112, 121)


def module_invocation():
    # The canonical module invocation name 'python -m django'.
    return PSeq(112, 121, 116, 104, 111, 110, 32, 45, 109, 32,
                100, 106, 97, 110, 103, 111)


def program_name(basename):
    """The program name derived from a first-argument basename: the basename
    itself, except the bootstrap basename maps to the module-invocation name."""
    if basename == bootstrap_name():
        return module_invocation()
    return basename


# --- carrier classes from model.py, contract lines stripped --------------------

class Parser:
    def __init__(self):
        self.prog = []


class Utility:
    def __init__(self):
        self.argv0_basename = []
        self.sys_argv0_basename = []


# --- the impl region of model.py, verbatim (contracts stripped) ----------------

def build_settings_parser(self):
    parser = Parser()

    # parser's program name := the utility's own computed program name.
    #   prog := program_name(argv0_basename)
    if ToSeq(self.argv0_basename) == bootstrap_name():
        # The bootstrap basename maps to the canonical module-invocation name.
        parser.prog = [112, 121, 116, 104, 111, 110, 32, 45, 109, 32,
                       100, 106, 97, 110, 103, 111]
    else:
        i = 0
        while i < len(self.argv0_basename):
            parser.prog.append(self.argv0_basename[i])
            i = i + 1
        # parser.prog now equals the utility's own first-argument basename,
        # which (not being the bootstrap name) is exactly its program name.
    return parser
    # impl-end


# --- oracle plumbing ------------------------------------------------------------

class _Probe(Exception):
    """Carries the program name the real pre-scan parser reports; raised right
    after the real parser constructor completes, aborting the rest of the
    surrounding method (which would otherwise parse options and dispatch)."""

    def __init__(self, prog):
        super().__init__(prog)
        self.prog = prog


def _install_recorder(mgmt):
    """Replace the parser class the method under test constructs with a
    recording subclass. The REAL constructor still runs in full (so the real
    program-name handling is exercised); only the completed parser's reported
    program name is captured before aborting."""
    real_cls = mgmt.CommandParser

    class RecordingParser(real_cls):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            raise _Probe(self.prog)

    mgmt.CommandParser = RecordingParser


def real_prog(mgmt, own_argv0, ambient_argv0):
    """Run the REAL patched utility up to (and through) the construction of
    its option-pre-scan parser and return the program name that parser
    reports, with the ambient process-wide first argument pinned to
    `ambient_argv0` and the utility's OWN argument vector starting at
    `own_argv0`."""
    saved = sys.argv
    try:
        sys.argv = [ambient_argv0, 'help']
        util = mgmt.ManagementUtility([own_argv0, 'help'])
        try:
            util.execute()
        except _Probe as probe:
            return probe.prog
        return None  # pre-scan parser never constructed: disagreement signal
    finally:
        sys.argv = saved


def check_case(mgmt, own_basename, prefix, ambient_argv0):
    # shadow: the utility's own first-argument basename as code points
    util = Utility()
    util.argv0_basename = [ord(c) for c in own_basename]
    util.sys_argv0_basename = [ord(c) for c in os.path.basename(ambient_argv0)]
    shadow_out = ''.join(chr(c) for c in build_settings_parser(util).prog)

    real_out = real_prog(mgmt, prefix + own_basename, ambient_argv0)
    if shadow_out != real_out:
        return ("DISAGREEMENT\n  own_basename=%r prefix=%r ambient_argv0=%r\n"
                "  shadow=%r\n  real=%r"
                % (own_basename, prefix, ambient_argv0, shadow_out, real_out))
    return None


# --- input domain ----------------------------------------------------------------

PREFIXES = ['', './', '/usr/local/bin/', '/a/b/c/']

BOUNDARY_BASENAMES = [
    '',                     # empty basename (own argv0 is '' or a dir path)
    '__main__.py',          # the bootstrap basename (special-cased)
    '__main__.pyc',         # near-misses that must pass through unchanged
    '__main__.py ',
    ' __main__.py',
    '__Main__.py',
    '__main_.py',
    'main.py',
    'manage.py',
    'django-admin',
    'django-admin.py',
    'python -m django',     # the module-invocation string as a literal basename
    'a',
    '.',
    '..',
    '.hidden',
    'x y z',
    'mänage.pyΩ',  # non-ASCII code points
    'n' * 200,               # long name
]

BOUNDARY_AMBIENT = [
    '/x/sub.py',             # disagrees with the own source (the key scenario)
    'django-admin',          # may agree with the own source
    '/path/to/__main__.py',  # ambient basename is the bootstrap name
    '',                      # degenerate ambient first argument
]


def rand_basename(rng, alphabet):
    r = rng.random()
    if r < 0.08:
        return '__main__.py'                       # bootstrap name
    if r < 0.16:                                    # near-miss mutations
        base = list('__main__.py')
        k = rng.randrange(len(base))
        if rng.random() < 0.5:
            base[k] = rng.choice(alphabet)
        else:
            del base[k]
        return ''.join(base)
    n = rng.randint(0, 24)
    return ''.join(rng.choice(alphabet) for _ in range(n))


def main():
    import django.core.management as mgmt
    _install_recorder(mgmt)

    checked = 0
    for own in BOUNDARY_BASENAMES:
        for prefix in PREFIXES:
            for ambient in BOUNDARY_AMBIENT:
                err = check_case(mgmt, own, prefix, ambient)
                if err:
                    print(err)
                    return 1
                checked += 1
    n_boundary = checked

    rng = random.Random(SEED)
    # basenames may not contain the path separator; keep '\\' out too so the
    # split-at-the-boundary bridge is platform-independent
    alphabet = string.ascii_letters + string.digits + '._- '
    for _ in range(N_FUZZ):
        own = rand_basename(rng, alphabet)
        prefix = rng.choice(PREFIXES)
        amb_base = rand_basename(rng, alphabet)
        ambient = rng.choice(PREFIXES) + amb_base
        err = check_case(mgmt, own, prefix, ambient)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real pre-scan parser program name on "
          "%d inputs (%d boundary + %d fuzz, seed %d)."
          % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
