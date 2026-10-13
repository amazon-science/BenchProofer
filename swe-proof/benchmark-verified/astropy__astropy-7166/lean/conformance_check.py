#!/usr/bin/env python
"""G-CONF: differential conformance for astropy__astropy-7166.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). Builds the Python R/I shadow of the Lean
`implementation_inheritDocstrings` skeleton and diffs it against the REAL patched
callee — the per-member docstring-filling loop of
`astropy.utils.misc.InheritDocstrings.__init__` — driven by actually creating
classes under that metaclass and reading the resulting member docstrings.

Modeled function: when a class is built under `InheritDocstrings`, each of its
own namespace members is examined. The guard the gold patch edits decides which
members get a missing docstring filled from the base classes: a member is
eligible iff it is an ordinary callable OR an attribute-access descriptor, its
name is public, and it currently has no docstring of its own. For an eligible
member the missing docstring is filled with the one resolved through the class's
bases (its inherited docstring, possibly absent); every other member is left
untouched.

Bridge (mapping.md):
  Lean `Member`              <->  one (key, val) of the subclass's own namespace
    .key : List Char         <->  the attribute name (str)
    .isFunction : Bool       <->  inspect.isfunction(val)
    .isDataDescriptor : Bool <->  inspect.isdatadescriptor(val)
    .doc : Option (List Char) <-> val.__doc__ BEFORE the metaclass runs (None<->none)
  Lean `superDoc key`        <->  the docstring the unchanged MRO walk
                                  (`for base in cls.__mro__[1:]: getattr(base,key,None)`)
                                  would assign — an A-reference, reproduced here
                                  with the real getattr/MRO primitives.
  Lean result `Member.doc`   <->  Subclass.__dict__[key].__doc__ AFTER class creation.

Exit 0 iff zero disagreements over a discrete catalogue + >=1e5 fuzzed class
configurations. stdlib-only; pinned seed.
"""
import inspect
import random
import sys

from astropy.utils.misc import InheritDocstrings

SEED = 20240627
N_RANDOM = 120_000  # >= 1e5


# ---- Lean-faithful pure predicates (R/I leg of the impl) --------------------

def is_public_member(key):
    """Transliteration of `isPublicMember` (and the real `is_public_member`)."""
    return ((key.startswith('__') and key.endswith('__') and len(key) > 4)
            or not key.startswith('_'))


def eligible(is_function, is_datadescriptor, doc_before, key):
    """Transliteration of `eligible`: the POST-PATCH guard.
    (is_function OR is_datadescriptor) AND public AND currently undocumented."""
    return ((is_function or is_datadescriptor)
            and is_public_member(key)
            and doc_before is None)


def super_doc(cls, key):
    """The inherited docstring resolved through the bases — the unchanged MRO
    walk (A-reference). Mirrors the real loop exactly."""
    for base in cls.__mro__[1:]:
        super_method = getattr(base, key, None)
        if super_method is not None:
            return super_method.__doc__
    return None


# ---- member factories: exercise every (isFunction, isDataDescriptor) combo --

def make_member(kind, doc):
    """Return a class-body value of the requested kind carrying docstring `doc`.
    kinds:  func (function), prop (property/data-descriptor), static
    (staticmethod – non-data descriptor), plain (an int – neither)."""
    if kind == 'func':
        def f(self):
            pass
        f.__doc__ = doc
        return f
    if kind == 'prop':
        def g(self):
            return 0
        return property(g, doc=doc)
    if kind == 'static':
        def h():
            pass
        h.__doc__ = doc
        return staticmethod(h)
    # plain attribute
    return 7


KINDS = ['func', 'prop', 'static', 'plain']
NAMES = ['foo', 'bar', 'baz_method', '_private', '__call__', '__weird__',
         'publicName', '_x', '__init__']
DOCS = [None, "ALPHA", "BETA", ""]


def build_case(base_specs, sub_specs):
    """base_specs / sub_specs: list of (name, kind, doc). Build a plain Base and
    a Subclass(Base) under the real InheritDocstrings metaclass. Return
    (Subclass, sub_dct_before) where sub_dct_before records each member's
    pre-metaclass (isfunction, isdatadescriptor, doc) keyed by name."""
    base_ns = {}
    for name, kind, doc in base_specs:
        base_ns[name] = make_member(kind, doc)
    Base = type('Base', (object,), base_ns)

    sub_ns = {}
    before = {}
    for name, kind, doc in sub_specs:
        val = make_member(kind, doc)
        sub_ns[name] = val
        before[name] = (inspect.isfunction(val), inspect.isdatadescriptor(val),
                        val.__doc__)
    # The metaclass mutates member objects in place during __init__.
    Subclass = InheritDocstrings('Subclass', (Base,), sub_ns)
    return Subclass, before


def check_case(base_specs, sub_specs):
    """Return None on agreement, else a description string of the disagreement."""
    Subclass, before = build_case(base_specs, sub_specs)
    for name, _kind, _doc in sub_specs:
        is_fn, is_dd, doc_before = before[name]
        if eligible(is_fn, is_dd, doc_before, name):
            expected = super_doc(Subclass, name)
        else:
            expected = doc_before
        actual = Subclass.__dict__[name].__doc__
        if expected != actual:
            return (f"key={name!r} kind-before=(fn={is_fn},dd={is_dd},doc={doc_before!r}) "
                    f"expected={expected!r} actual={actual!r}")
    return None


def discrete_catalogue():
    """Hand-picked cases incl. the F2P scenario (an undocumented subclass
    property inheriting a documented base property)."""
    cases = []
    # the exact F2P shape: documented function + property in base, undocumented
    # overrides in subclass.
    cases.append((
        [('__call__', 'func', "FOO"), ('bar', 'prop', "BAR")],
        [('__call__', 'func', None), ('bar', 'prop', None)],
    ))
    # property already documented in subclass -> keep own doc.
    cases.append((
        [('bar', 'prop', "BASEDOC")],
        [('bar', 'prop', "OWNDOC")],
    ))
    # private property -> not public -> untouched (stays None).
    cases.append((
        [('_p', 'prop', "BASE")],
        [('_p', 'prop', None)],
    ))
    # static method (neither function nor data-descriptor) -> untouched.
    cases.append((
        [('foo', 'static', "BASE")],
        [('foo', 'static', None)],
    ))
    # plain attribute -> untouched.
    cases.append((
        [('foo', 'plain', None)],
        [('foo', 'plain', None)],
    ))
    # base lacks the key -> nothing to inherit, stays None.
    cases.append((
        [],
        [('bar', 'prop', None)],
    ))
    # base member's doc is None -> inherits None.
    cases.append((
        [('bar', 'prop', None)],
        [('bar', 'prop', None)],
    ))
    return cases


def main():
    rng = random.Random(SEED)

    for base_specs, sub_specs in discrete_catalogue():
        bad = check_case(base_specs, sub_specs)
        if bad is not None:
            print(f"FAIL (discrete): {bad}")
            return 1

    for _ in range(N_RANDOM):
        # subclass members: 1..4 distinct names
        k = rng.randint(1, 4)
        names = rng.sample(NAMES, k)
        sub_specs = [(n, rng.choice(KINDS), rng.choice(DOCS)) for n in names]
        # base: a (possibly partial, possibly differently-kinded) set over the
        # SAME names so the MRO walk sometimes finds an attribute, sometimes not.
        base_specs = []
        for n in names:
            if rng.random() < 0.75:
                base_specs.append((n, rng.choice(KINDS), rng.choice(DOCS)))
        bad = check_case(base_specs, sub_specs)
        if bad is not None:
            print(f"FAIL (fuzz): {bad}")
            return 1

    print(f"OK: {N_RANDOM} fuzzed + {len(discrete_catalogue())} discrete cases "
          f"agree with real InheritDocstrings (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
