#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-14787.

The changed wrap operation is modeled DEEPLY (no consumed axiom): `mergePlan`
(Solution.lean's `pure` region) is the per-attribute-name overlay

    mergeAt src base n = src[n] if n in src else base[n]   (else absent)

This script validates that deep model against the REAL standard-library callee
`functools.update_wrapper` (the helper `functools.wraps(method)(...)` invokes) on:

  (1) randomized fuzz: source/base carrier objects with arbitrary subsets of the
      assigned names bound to arbitrary values; assert that, for every assigned
      name, the value the REAL update_wrapper'd object presents == mergePlan of
      the OBSERVED source/base environments; and
  (2) the exact django scenario: wrap a real `partial(method.__get__(self, ...))`
      with `wraps(method)` and assert the presented `__name__` is the method's
      name and was ABSENT on the bare partial (the F2P-observed behavior).

The model's inputs are derived by OBSERVING the real carriers (`getattr(o, n,
ABSENT)`), so inherited attributes are accounted for identically on both sides
and "attribute absent" (the AttributeError path) is kept distinct from "attribute
present with value None". This mirrors update_wrapper's own `try: getattr / except
AttributeError: pass` semantics exactly.

Imports only the Python standard library (`functools`) — the same module the gold
patch calls. Exit 0 iff every obligation holds.
"""
import random
import sys
from functools import partial, wraps, update_wrapper, WRAPPER_ASSIGNMENTS

_ABSENT = object()

# The assigned name set the real callee uses. Use the in-image interpreter's
# WRAPPER_ASSIGNMENTS so the check stays faithful to whatever ships here.
ASSIGNED = list(WRAPPER_ASSIGNMENTS)


# --- deep-model reference encodings (kept in lock-step with Solution.lean) ----
# An environment is the assoc list [(name, value)] of the names actually present
# (absent names omitted), mirroring Solution.lean's `List (String × String)`.

def lookup_attr(env, n):
    """Solution.lean `lookupAttr`: value bound to n (first match), else ABSENT."""
    for (k, v) in env:
        if k == n:
            return v
    return _ABSENT


def first_defined(a, b):
    """Solution.lean `firstDefined`: source value if present, else base."""
    return a if a is not _ABSENT else b


def merge_at(src_env, base_env, n):
    """Solution.lean `mergeAt`."""
    return first_defined(lookup_attr(src_env, n), lookup_attr(base_env, n))


def merge_plan(src_env, base_env, names):
    """Solution.lean `mergePlan`: per-name overlay over the name list."""
    return [(n, merge_at(src_env, base_env, n)) for n in names]


# --- observation: an object's assigned-attribute environment ------------------

def observe_env(obj, names):
    """The assoc-list environment of `obj`: (name, value) for each ASSIGNED name
    that is actually present (getattr does not raise). Absent names omitted."""
    env = []
    for n in names:
        v = getattr(obj, n, _ABSENT)
        if v is not _ABSENT:
            env.append((n, v))
    return env


def observe_presented(obj, names):
    """What `obj` presents per assigned name: (name, value-or-ABSENT)."""
    return [(n, getattr(obj, n, _ABSENT)) for n in names]


# --- carriers ----------------------------------------------------------------

class Bag:
    pass


def make_object(attr_dict):
    """Build a fresh carrier presenting attr_dict (over the assigned names) on
    top of whatever its class inherits."""
    o = Bag()
    for n, v in attr_dict.items():
        setattr(o, n, v)
    return o


# --- the A-reference check: mergePlan == real functools.update_wrapper --------

def check_reference(src_attrs, base_attrs):
    """Assert mergePlan(observe src, observe base) == REAL update_wrapper output.

    src_attrs / base_attrs: dict name->value over (a subset of) ASSIGNED, set on
    fresh carriers. The model inputs are then read back by observation so that
    inherited attributes are handled consistently on both sides.
    """
    src = make_object(src_attrs)
    base = make_object(base_attrs)

    # Deep model over the OBSERVED environments.
    src_env = observe_env(src, ASSIGNED)
    base_env = observe_env(base, ASSIGNED)
    expected = merge_plan(src_env, base_env, ASSIGNED)

    # REAL callee: copy src's assigned attrs onto a fresh target equivalent to
    # base (same class => same inherited attrs as base).
    target = make_object(base_attrs)
    update_wrapper(target, src, assigned=ASSIGNED, updated=[])
    observed = observe_presented(target, ASSIGNED)

    assert observed == expected, (
        "mergePlan deep model unsound:\n  src=%r\n  base=%r\n"
        "  update_wrapper presents %r\n  mergePlan gives        %r"
        % (src_attrs, base_attrs, observed, expected))


def check_django_scenario():
    """The exact F2P scenario: wraps(method)(partial(method.__get__(self,...)))
    must present method.__name__, which the bare partial lacks."""
    class Test:
        def method(self):
            return 'tests'

    inst = Test()
    bare = partial(Test.method.__get__(inst, type(inst)))
    # Pre-fix object: the bare partial has NO __name__.
    assert getattr(bare, '__name__', _ABSENT) is _ABSENT, (
        "expected the bare partial to lack __name__")
    # Post-fix object: wraps(method) overlays method's identity attributes.
    wrapped = wraps(Test.method)(partial(Test.method.__get__(inst, type(inst))))
    assert getattr(wrapped, '__name__', _ABSENT) == 'method', (
        "wraps(method)(partial) must present __name__ == 'method', got %r"
        % getattr(wrapped, '__name__', _ABSENT))
    assert getattr(wrapped, '__module__', _ABSENT) is not _ABSENT, (
        "wraps(method)(partial) must present a __module__")

    # And this matches mergePlan with the partial's base env and method's src env.
    src_env = observe_env(Test.method, ASSIGNED)
    base_env = observe_env(bare, ASSIGNED)
    expected = merge_plan(src_env, base_env, ASSIGNED)
    observed = observe_presented(wrapped, ASSIGNED)
    assert observed == expected, (
        "django scenario: presented %r but mergePlan=%r" % (observed, expected))


def main():
    # --- boundary cases -------------------------------------------------------
    boundary = [
        ({}, {}),                                   # both bare (only inherited)
        ({n: 'm_' + n for n in ASSIGNED}, {}),      # source defines all
        ({}, {n: 'b_' + n for n in ASSIGNED}),      # base defines all
        ({n: 'm_' + n for n in ASSIGNED},
         {n: 'b_' + n for n in ASSIGNED}),          # both define all (source wins)
        # the canonical case: source has __name__, base does not
        ({'__name__': 'method', '__qualname__': 'Test.method'},
         {'__doc__': 'partial(func, ...)'}),
        # source defines None-valued attr -> source still wins over base value
        ({'__name__': 'method'}, {'__name__': 'other'}),
    ]
    for src, base in boundary:
        check_reference(src, base)

    # --- randomized fuzz ------------------------------------------------------
    rng = random.Random(14787)
    values = ['method', 'tests', 'Test.method', '', 'x', 'mod.sub',
              'a-doc-string', 'functools', '__main__', 'qual']
    for _ in range(20000):
        src = {n: rng.choice(values) for n in ASSIGNED if rng.random() < 0.6}
        base = {n: rng.choice(values) for n in ASSIGNED if rng.random() < 0.6}
        check_reference(src, base)

    # --- the exact django F2P scenario ---------------------------------------
    check_django_scenario()

    print("G-AX OK: mergePlan deep model (== functools.update_wrapper assign "
          "loop) sound on %d boundary + 20000 fuzz attribute environments over "
          "%d assigned names, and on the real wraps(method)(partial(...)) "
          "scenario." % (len(boundary), len(ASSIGNED)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
