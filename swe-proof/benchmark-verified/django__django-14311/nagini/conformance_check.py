#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-14311 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Invariant/Assert) stripped. The @Pure helper
``module_arg`` copies over as a plain function on top of a small
immutable-tuple PSeq shim (it is contract-side but serves here as an internal
cross-check of the shadow). The single @ContractOnly callee ``marks_entry``
is the unchanged boundary classification the modeled selection consumes; its
shim performs the REAL classification with the real ``str`` operations
(``str.__eq__`` / ``str.endswith``), exactly the concrete callee identified in
mapping.md section 3.1 and validated by axiom_check.py (G-AX).

ORACLE: the REAL patched repo function the model models per mapping.md —
``django.utils.autoreload.get_child_arguments``. The gate applies patch.diff
to /testbed before this script runs. For each input pair the launched unit's
module spec is installed on the real ``__main__`` module (a plain object with
``name`` / ``parent`` attributes, the two code-point strings the model
carries), ``get_child_arguments()`` is called, and the module-name argument
following the interpreter's module flag is extracted from the returned argv.
That extracted value is exactly the modeled behaviour: which name is
reproduced for the relaunch command.

Type bridge (mapping.md section 2): both inputs are ``str``; the model
carrier is ``List[int]`` of Unicode code points via ``ord``. The bridge is a
bijection, so generation happens over ``str`` and is lowered per call.
``str`` truthiness bridges to ``len(...) > 0`` (a str is falsy iff empty).

Input domain: the preconditions demand only readable lists of code points, so
every pair of ``str`` values lowers to a Requires-satisfying input. Generation
stresses the decision boundary: qualified dotted names whose final segment is
or resembles the interpreter's entry-point sentinel, names containing but not
dotted-ending in it, the empty name/parent, plus character-level fuzz over the
sentinel's alphabet and astral/accented code points.

>= 1e5 Requires-satisfying inputs: 16 boundary names x 6 boundary parents +
60000 segment-fuzz pairs + 45000 character-fuzz pairs. Pinned fuzz seed:
14311.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 14311
N_SEG_FUZZ = 60000
N_CHR_FUZZ = 45000


# --- PSeq shim: immutable sequence, the operations the model regions use -----

class PSeq(object):
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def take(self, n):
        return PSeq._wrap(self._t[:n])

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __hash__(self):
        return hash(self._t)


def ToSeq(lst):
    return PSeq._wrap(lst)


def seq_to_str(s):
    return "".join(chr(s[i]) for i in range(len(s)))


# --- @ContractOnly callee shim: the REAL classification ----------------------
# marks_entry is the model's opaque boundary callee: whether the qualified
# name denotes a package executed through its entry file. Its shim performs
# the real classification with the real str operations (the concrete callee
# per mapping.md section 3.1, A-reference-validated by G-AX).

def marks_entry(name_seq):
    name = seq_to_str(name_seq)
    return name == '__main__' or name.endswith('.__main__')


# --- pure helper from model.py, contracts stripped (cross-check only) --------

def module_arg(name, parent):
    if marks_entry(name) and len(parent) > 0:
        return parent
    return name


# --- the impl region of model.py, verbatim, contract calls stripped ----------

def select_module_name(name, parent):
    sentinel = marks_entry(ToSeq(name))
    result = []  # type: list
    if sentinel and len(parent) > 0:
        i = 0
        while i < len(parent):
            result = result + [parent[i]]
            i = i + 1
    else:
        i = 0
        while i < len(name):
            result = result + [name[i]]
            i = i + 1
    return result
    # (the stripped Assert lines carried only proof-side sequence facts)


# --- oracle: the real patched get_child_arguments -----------------------------

class FakeSpec(object):
    """A module spec carrying exactly the two code-point strings the model
    takes as inputs (the launched unit's qualified import name and its
    enclosing package name)."""

    def __init__(self, name, parent):
        self.name = name
        self.parent = parent


def real_selected_name(autoreload, main_mod, name, parent):
    """Install the spec on the real __main__ module, call the REAL patched
    repo function, and extract the module-name argument that follows the
    interpreter's module flag in the returned argv."""
    main_mod.__spec__ = FakeSpec(name, parent)
    args = autoreload.get_child_arguments()
    i = args.index('-m')
    return args[i + 1]


# --- differential driver -------------------------------------------------------

def make_check(autoreload, main_mod):
    def check(name, parent):
        name_cp = [ord(ch) for ch in name]        # bridge: str -> List[int]
        parent_cp = [ord(ch) for ch in parent]
        shadow = select_module_name(name_cp, parent_cp)
        real = real_selected_name(autoreload, main_mod, name, parent)
        real_cp = [ord(ch) for ch in real]
        if shadow != real_cp:
            return ("DISAGREEMENT on (name=%r, parent=%r):\n"
                    "  shadow (impl region)          = %r (%r)\n"
                    "  real (patched repo function)  = %r (%r)"
                    % (name, parent, seq_to_str(ToSeq(shadow)), shadow,
                       real, real_cp))
        # internal cross-check: the executable impl agrees with the pure spec
        expected = module_arg(ToSeq(name_cp), ToSeq(parent_cp))
        if ToSeq(shadow) != expected:
            return ("INTERNAL: impl region and pure spec disagree on "
                    "(name=%r, parent=%r)" % (name, parent))
        return None
    return check


def boundary_pairs():
    # Qualified names stressing the classification boundary: the F2P
    # directly-named module, the P2P package-entry names, the bare/dangling
    # sentinel forms, sentinel-in-the-middle, and names that contain but do
    # not dotted-end in the sentinel token.
    names = [
        '',
        '__main__',
        '.__main__',
        'foo.__main__',
        'utils_tests.test_module.__main__',
        'django.__main__',
        'utils_tests.test_module.main_module',
        'foo.bar.baz',
        'foo.bar',
        'foo',
        'foo.my__main__',
        'my__main__',
        '__main__x',
        'x__main__',
        'a.b.__main__c',
        'pkg.__main__.sub',
    ]
    parents = [
        '', 'foo', 'foo.bar', 'utils_tests.test_module', 'django',
        'foo.bar.baz',
    ]
    return [(n, p) for n in names for p in parents]


def main():
    # Import the REAL patched repo module (the gate applied patch.diff to
    # /testbed and PYTHONPATH points there).
    from django.utils import autoreload
    import __main__ as main_mod

    old_spec = getattr(main_mod, '__spec__', None)
    old_argv = sys.argv[:]
    # Keep argv minimal so the produced argv's tail is empty and the value
    # after the module flag is exactly the selected name.
    sys.argv = [old_argv[0] if old_argv else 'conformance_check.py']

    check = make_check(autoreload, main_mod)
    checked = 0
    failures = 0
    try:
        boundary = boundary_pairs()
        for nm, pa in boundary:
            err = check(nm, pa)
            if err:
                print(err)
                failures += 1
                if failures >= 5:
                    return 1
            checked += 1

        rng = random.Random(SEED)

        # Segment fuzz: dotted names built from realistic identifier segments,
        # with the sentinel token as a frequent segment so the classification
        # boundary is exercised heavily.
        segments = ['foo', 'bar', 'baz', 'main_module', 'manage', '__main__',
                    'main__', '__main', 'a', 'mod', 'pkg', 'sub']
        for _ in range(N_SEG_FUZZ):
            k = rng.randint(0, 5)
            nm = '.'.join(rng.choice(segments) for _ in range(k)) if k else ''
            j = rng.randint(0, 4)
            pa = '.'.join(rng.choice(segments) for _ in range(j)) if j else ''
            err = check(nm, pa)
            if err:
                print(err)
                failures += 1
                if failures >= 5:
                    return 1
            checked += 1

        # Character-level fuzz to stress the suffix comparison on arbitrary
        # code points (not just identifier segments).
        alphabet = list('._main0123 xX') + ['é', '•', '\U0001d518']
        for _ in range(N_CHR_FUZZ):
            n = rng.randint(0, 16)
            nm = ''.join(rng.choice(alphabet) for _ in range(n))
            m = rng.randint(0, 10)
            pa = ''.join(rng.choice(alphabet) for _ in range(m))
            err = check(nm, pa)
            if err:
                print(err)
                failures += 1
                if failures >= 5:
                    return 1
            checked += 1
    finally:
        main_mod.__spec__ = old_spec
        sys.argv = old_argv

    if failures:
        print("G-CONF: %d disagreement(s) over %d inputs" % (failures, checked))
        return 1

    print("G-CONF OK: shadow impl == real patched get_child_arguments "
          "module-name selection on %d inputs (%d boundary + %d segment fuzz "
          "+ %d char fuzz, seed %d); 0 disagreements."
          % (checked, len(boundary), N_SEG_FUZZ, N_CHR_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
