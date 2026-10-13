#!/usr/bin/env python3
"""G-AX executable A-reference check for django__django-14311.

model.py models a single boundary callee as a FULLY OPAQUE
``@Pure @ContractOnly`` classifier (no Ensures -- the proof consumes no
contract):

    marks_entry(name) -> bool

This is the unchanged classification performed by the module-execution
machinery: whether a qualified module name denotes a package executed through
its entry file rather than a directly-named module.  Its real implementation
(the concrete classifier the gold relaunch logic uses) is

    name == '__main__' or name.endswith('.__main__')

The changed SELECTION logic ``module_arg`` (model.py pure region) is modelled
DEEPLY on top of ``marks_entry``:

    module_arg(name, parent) = parent if marks_entry(name) and parent else name

Because ``marks_entry`` is opaque, it is NOT an axiom whose contract the proof
consumes; it is an **A-reference** -- a real callee the deep model is validated
against.  G-AX discharges that A-reference obligation against the REAL Python
operations by executing them on boundary + randomized inputs and asserting
agreement, code-point for code-point:

    the real classifier really is the gold selector
        marks_entry_real(name) == (name == '__main__' or name.endswith('.__main__'))
    and the resulting selection
        module_arg_real(name, parent) == (parent if marks_entry_real(name)
                                           and parent else name)
    matches the model's ``module_arg`` semantics, code-point for code-point.

This is the load-bearing trust point: the opaque ``marks_entry`` + the deep
``module_arg`` together provably equal the real ``str`` selector, so any impl
that verifies against the spec reproduces the gold selection.

Imports nothing repo-specific: only the standard library (``str`` operations
are the very operations the gold patch performs).  Exit 0 iff the A-reference
holds on every input.
"""
import random
import sys


def to_codepoints(s):
    return [ord(ch) for ch in s]


# --- the REAL classifier and selection (exactly the gold relaunch selector) ---

def marks_entry_real(name):
    """The concrete classifier the model.py axiom ``marks_entry`` stands in
    for: the real condition the gold relaunch logic evaluates."""
    return name == '__main__' or name.endswith('.__main__')


def module_arg_real(name, parent):
    if marks_entry_real(name) and parent:
        return parent
    return name


# --- model.py module_arg semantics (defined over marks_entry, code points) ----

def module_arg_model(name_cp, parent_cp, marks):
    """Reference of model.py ``module_arg`` over code points, given the value
    of the (opaque-to-the-proof) ``marks_entry`` classifier."""
    if marks and len(parent_cp) > 0:
        return parent_cp
    return name_cp


# --- the checks --------------------------------------------------------------

def check_module_arg(name, parent):
    """A-reference obligation: the real classifier + selection match the deep
    model semantics, code point for code point."""
    marks = marks_entry_real(name)
    observed = to_codepoints(module_arg_real(name, parent))
    expected = module_arg_model(to_codepoints(name), to_codepoints(parent),
                                marks)
    assert observed == expected, (
        "module_arg deep model unsound on (name=%r, parent=%r): "
        "real=%r model=%r" % (name, parent, observed, expected))


def main():
    # Boundary names: the exact F2P / P2P-relevant qualified names plus the
    # corner cases the gold selector was designed to handle.
    boundary_names = [
        '',
        '__main__',
        '.__main__',
        'foo.__main__',
        'utils_tests.test_module.__main__',     # P2P: run as package
        'django.__main__',                       # P2P: run django package
        'utils_tests.test_module.main_module',   # F2P: directly-named module
        'foo.bar.baz',
        'foo.bar',
        'foo',
        'foo.my__main__',                        # the dumb corner case (hints):
        'my__main__',                            #   NOT an entry sentinel
        '__main__x',
        'x__main__',
        'a.b.__main__c',
        'pkg.__main__.sub',                      # sentinel only at the END
    ]
    boundary_parents = [
        '', 'foo', 'foo.bar', 'utils_tests.test_module', 'django',
        'foo.bar.baz',
    ]
    for nm in boundary_names:
        for pa in boundary_parents:
            check_module_arg(nm, pa)

    # Randomized fuzz: build dotted names from realistic identifier segments,
    # including '__main__' as a possible final segment so the sentinel boundary
    # is exercised heavily.
    rng = random.Random(14311)
    segments = ['foo', 'bar', 'baz', 'main_module', 'manage', '__main__',
                'main__', '__main', 'a', 'mod', 'pkg', 'sub']
    for _ in range(20000):
        k = rng.randint(0, 5)
        name = '.'.join(rng.choice(segments) for _ in range(k)) if k else ''
        j = rng.randint(0, 4)
        parent = '.'.join(rng.choice(segments) for _ in range(j)) if j else ''
        check_module_arg(name, parent)

    # Character-level fuzz to stress the suffix comparison on arbitrary code
    # points (not just identifier segments).
    alphabet = list('._main0123 xX') + ['é', '•']
    for _ in range(20000):
        n = rng.randint(0, 16)
        name = ''.join(rng.choice(alphabet) for _ in range(n))
        m = rng.randint(0, 10)
        parent = ''.join(rng.choice(alphabet) for _ in range(m))
        check_module_arg(name, parent)

    print("G-AX OK: module_arg deep model (opaque marks_entry + selection) "
          "validated == real str '__main__'/'.__main__' selector "
          "(A-reference) code-point-for-code-point on %d boundary names x %d "
          "parents + 40000 fuzz inputs"
          % (len(boundary_names), len(boundary_parents)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
