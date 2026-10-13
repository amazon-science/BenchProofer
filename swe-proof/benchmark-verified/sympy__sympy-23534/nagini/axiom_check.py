#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-23534.

There is NO consumed `@ContractOnly` axiom in this bundle: the per-entry
expansion is modelled deeply (`expand_entry` / `all_tag` / `all_nonneg` in
model.py's pure + impl regions). This script validates the one **A-reference**
deep-model claim against the REAL callee (sympy's `symbols`), exactly the way
G-AX validates a deep model == its real counterpart.

A-reference claim (model.py `expand_entry` + `symbols_on_sequence`):

  * Per entry (`expand_entry`): processing a single name entry under a
    requested output class `cls` produces a sequence of EXACTLY the entry's
    multiplicity many objects -- which may be ZERO (an empty/null range such as
    `'x:c'`, `'x:0'`) -- and EVERY produced object was constructed by `cls`.

  * Per container (`symbols_on_sequence`): given a *container* of entries, the
    output is grouped one-group-per-entry, in order
    (`len(Result()) == len(names)`); group k holds exactly the multiplicity of
    entry k (`len(Result()[k]) == names[k]`), and EVERY leaf in EVERY group
    carries the requested class -- never the default `Symbol`
    (`all_tag(Result()[k], cls)`).

In the model an object's class is abstracted to an integer class tag; the
concrete realisation of "the tag of the objects `cls` produces" is the Python
type `type(cls(<name>))` (note `Function` is a metaclass, so
`symbols('x', cls=Function)` yields an `UndefinedFunction` instance, i.e.
`type(cls('x'))`, not a `Function` instance). We run the real factory and
assert the multiplicity/grouping and that every leaf has that type -- and
crucially is NOT the default `Symbol` when a non-default class is requested.

This is the property the F2P test observes
(`type(symbols(('q:2','u:2'), cls=Function)[0][0]) == UndefinedFunction`):
the first entry is a range producing a TUPLE group of >= 2 objects, so `[0]`
is subscriptable and `[0][0]` is the requested class.

Imports only the repo package `sympy` (the same module the gold patch lives in)
and the stdlib. Exit 0 iff every observation is consistent with the model.
"""
import random
import sys

from sympy import symbols, Function
from sympy.core.symbol import Symbol
from sympy.core.function import UndefinedFunction


def _leaves(obj):
    """Flatten a (possibly nested) tuple/list/set of produced objects to its
    leaf objects."""
    if isinstance(obj, (tuple, list, set)):
        out = []
        for x in obj:
            out.extend(_leaves(x))
        return out
    return [obj]


def _multiplicity(obj):
    """The number of leaf objects a single entry's expansion produced. A range
    entry yields a (possibly empty) tuple; a single-name entry yields a scalar
    object (multiplicity 1)."""
    return len(_leaves(obj))


def tag_of(cls):
    """The concrete class tag of the objects `cls` produces: the Python type of
    a single object built directly by the requested class (for `Symbol` this is
    `Symbol`; for the `Function` metaclass it is `UndefinedFunction`)."""
    return type(cls("probe"))


def expand_entry_real(name, cls):
    """The REAL per-entry processing: the single-name-string branch of the
    factory under the requested class. Returns its leaf objects."""
    return _leaves(symbols(name, cls=cls, seq=True))


def check_entry_reference(name, cls):
    """A-reference (model.py `expand_entry`): the entry expands to >= 0 objects,
    every one carrying the tag of the requested class (all_tag(Result(), cls)).
    The multiplicity (which may be 0 for a null range) is a property of the
    entry, modelled by the entry token's value; we only check the SOUND facts
    the model relies on: non-negativity (trivially true -- a count) and the
    class of every produced object."""
    tag = tag_of(cls)
    leaves = expand_entry_real(name, cls)
    assert len(leaves) >= 0, "entry %r produced a negative count?!" % (name,)
    for obj in leaves:
        assert type(obj) is tag, (
            "expand_entry deep model unsound on name=%r cls=%r: produced %r "
            "of type %r, model requires every object to carry the tag %r of cls"
            % (name, cls, obj, type(obj), tag))


def check_container_behaviour(names, cls):
    """The pinned behaviour (model.py `symbols_on_sequence`): given a container
    of entries, the result is grouped one-group-per-entry in order; group k has
    exactly the multiplicity of entry k; and every leaf in every group carries
    the requested class tag (never the default)."""
    tag = tag_of(cls)
    res = symbols(names, cls=cls)
    # one group per entry, in order (len(Result()) == len(names))
    assert len(res) == len(names), (
        "grouping unsound on names=%r cls=%r: %d groups for %d entries"
        % (names, cls, len(res), len(names)))
    for k, entry in enumerate(names):
        group = res[k]
        # group k == entry k's own expansion, with entry k's multiplicity
        expected_mult = _multiplicity(symbols(entry, cls=cls, seq=True))
        actual_mult = _multiplicity(group)
        assert actual_mult == expected_mult, (
            "per-entry multiplicity unsound on names=%r cls=%r: group %d has "
            "%d leaves, entry %r expands to %d"
            % (names, cls, k, actual_mult, entry, expected_mult))
        # every leaf in this group carries the requested class tag
        for obj in _leaves(group):
            assert type(obj) is tag, (
                "symbols_on_sequence unsound on names=%r cls=%r: leaf %r in "
                "group %d has type %r, every produced object must carry the "
                "requested class tag %r"
                % (names, cls, obj, k, type(obj), tag))


def main():
    classes = [Symbol, Function]

    # The exact F2P witness from the issue / test: a range entry produces a
    # subscriptable group whose leaves carry the requested (Function) class.
    res = symbols(('q:2', 'u:2'), cls=Function)
    assert len(res) == 2, "F2P witness: expected 2 groups, got %d" % len(res)
    assert type(res[0][0]) is UndefinedFunction, (
        "F2P witness failed: type(symbols(('q:2','u:2'), cls=Function)[0][0]) "
        "= %r, expected UndefinedFunction" % (type(res[0][0]),))

    # --- A-reference: single-entry expansion honours cls ------------------
    # Includes NULL-RANGE entries (multiplicity 0) so the boundary the model's
    # multiplicity clause must be sound on is exercised, not skipped.
    single_names = [
        "x", "y", "alpha", "f",
        "q:2", "u:2", "a:d", "x5:10",
        "x(:2)", "x:2(1:3)",
        # null ranges (expand to ZERO objects): the model's len-clause must be
        # sound here (names[k] == 0), so the check must reach this subdomain.
        "x:0", "x1:1", "x:c", "b:a",
    ]
    for name in single_names:
        for cls in classes:
            check_entry_reference(name, cls)

    # --- the pinned container behaviour: boundary containers --------------
    # Includes containers with a null-range entry (a group of zero leaves) and
    # mixed range / single-name / null-range entries.
    boundary_containers = [
        ("x",),
        ("x", "y"),
        ("q:2", "u:2"),
        ("a:d", "x:z"),
        ("x5:10", "y:5"),
        ["p", "q", "r"],          # list container
        ("f", "g", "h"),
        ("x:c", "y"),             # null-range entry then a single name
        ("q:2", "x:0"),           # range entry then a null range
        ("x:0", "x1:1", "x:c"),   # all null ranges -> all empty groups
    ]
    for names in boundary_containers:
        for cls in classes:
            check_container_behaviour(names, cls)

    # --- randomized fuzz over containers ----------------------------------
    # Ranges include null ranges (start==end via ':0', or a<-letter) so the
    # fuzzer is NOT structurally blind to the zero-multiplicity subdomain.
    rng = random.Random(23534)
    bases = ["a", "b", "c", "x", "y", "z", "f", "g", "p", "q"]
    range_suffixes = [":0", ":1", ":2", ":3", ":c", "5:10", ":z"]
    for _ in range(300):
        n = rng.randint(1, 4)
        names = tuple(
            rng.choice(bases) + (rng.choice(range_suffixes) if rng.random() < 0.6 else "")
            for _ in range(n)
        )
        cls = rng.choice(classes)
        check_container_behaviour(names, cls)

    print("G-AX OK: expand_entry deep model (A-reference) == real sympy "
          "per-entry class handling; symbols_on_sequence grouping + per-entry "
          "multiplicity (incl. zero-multiplicity null ranges) + leaf class hold "
          "on %d boundary + 300 fuzz containers; F2P witness "
          "(cls=Function -> UndefinedFunction) reproduced."
          % (len(boundary_containers),))
    return 0


if __name__ == "__main__":
    sys.exit(main())
