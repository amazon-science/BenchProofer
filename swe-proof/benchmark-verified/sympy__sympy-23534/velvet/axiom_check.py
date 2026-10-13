#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-23534.

Executes the REAL unchanged callee — the single-name branch of sympy's
`symbols(name, *, cls=…, **args)` — on boundary name forms and randomized
fuzzing, and asserts that every observation matches the model encoded in
Solution.lean's `axioms` region.

The one kind-A obligation (A-consumed):

  (buildName_cls)  `buildName s c` returns only objects of the requested class
      `c`.  Concretely: for every name string `s` and every requested class
      `C ∈ {Symbol, Function, Wild}`, every object produced by the REAL
      single-name `symbols(s, cls=C, **args)` is an instance of `C` — i.e. its
      observable type tag equals the bijection image of `C` (mapping.md §2):
          Symbol   -> 'Symbol'
          Function -> 'UndefinedFunction'   (the metaclass instance Function(name) yields)
          Wild     -> 'Wild'

There is no A-reference here: only the per-element builder is axiomatized (the
genuinely-unchanged callee); the sequence-level loop is modeled deeply in
Solution.lean and validated by G-CONF, not by an axiom.

Imports nothing beyond `sympy` (the same package the gold patch edits). Exit 0
iff every obligation holds.
"""
import random
import sys

from sympy import symbols, Symbol, Wild
from sympy.core.function import Function, UndefinedFunction

# --- the Lean↔Python class bijection (mapping.md §2) -------------------------
# requested class  ->  expected observable type-name of every produced object
_CLS = [
    (Symbol, "Symbol"),
    (Function, "UndefinedFunction"),
    (Wild, "Wild"),
]


def _leaves(obj):
    """Flatten symbols()'s single-name output (an object, tuple, or list) into
    its leaf objects."""
    if isinstance(obj, (tuple, list)):
        for x in obj:
            yield from _leaves(x)
    else:
        yield obj


def check_buildName_cls(name, cls, expected_tag, **args):
    """Assert every object the REAL single-name symbols(name, cls=cls) returns
    carries the requested class (the buildName_cls axiom's Ensures)."""
    produced = symbols(name, cls=cls, **args)         # real callee
    leaves = list(_leaves(produced))
    assert leaves, "no objects produced for %r cls=%r" % (name, cls)
    for o in leaves:
        tag = type(o).__name__
        assert tag == expected_tag, (
            "buildName_cls unsound on name=%r cls=%s args=%r: produced object "
            "of type %r, axiom requires %r" % (name, cls.__name__, args, tag,
                                               expected_tag))


def main():
    # boundary name forms: plain, numeric range, alpha range, multi-range with
    # parenthesised disambiguation, escaped, plus assumption flags.
    boundary_names = [
        "x", "f", "g", "h",
        "q:2", "u:2", "a:d", ":c", "x:z",
        "x:2(1:3)", "x(:c)", r"x(:1\,:2)",
        "alpha", "x0", "phi1",
    ]
    arg_sets = [
        {},
        {"integer": True},
        {"real": True, "positive": True},
    ]

    n_checks = 0
    for cls, tag in _CLS:
        for name in boundary_names:
            for args in arg_sets:
                check_buildName_cls(name, cls, tag, **args)
                n_checks += 1

    # randomized fuzz: random single-name strings (plain + ranges)
    rng = random.Random(23534)
    letters = "abcdefghijklmnopqrstuvwxyz"
    for _ in range(3000):
        kind = rng.randint(0, 2)
        if kind == 0:                       # plain name
            base = "".join(rng.choice(letters) for _ in range(rng.randint(1, 4)))
            name = base
        elif kind == 1:                     # numeric range  base:n
            base = rng.choice(letters)
            name = "%s:%d" % (base, rng.randint(1, 4))
        else:                               # alpha range  a:x
            lo = rng.randint(0, 20)
            hi = lo + rng.randint(1, 5)
            name = "%s:%s" % (letters[lo], letters[hi])
        cls, tag = rng.choice(_CLS)
        check_buildName_cls(name, cls, tag)
        n_checks += 1

    print("G-AX OK: buildName_cls sound on %d real single-name symbols() "
          "observations across {Symbol, Function, Wild}" % n_checks)
    return 0


if __name__ == "__main__":
    sys.exit(main())
