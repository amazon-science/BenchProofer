#!/usr/bin/env python3
"""G-AX executable soundness check for pytest-dev__pytest-10356.

Executes the REAL repo callee `_pytest.mark.structures.normalize_mark_list`
(textually UNCHANGED by the gold patch; base:366-380 == post:389-403) and
compares it against a Python transliteration of the Lean deep model
`markOf` / `nameOf` / `canonicalize`, as encoded in Solution.lean.

The one kind-A check:

  (A-reference) the deep model `canonicalize` (Solution.lean, pure region) ==
      `list(normalize_mark_list(L))` on the WHOLE raw element domain the changed
      `get_unpacked_marks` can assemble — not merely on canonical lists. Both
      sides are compared on:
        * the SUCCESS value      (Outcome.collected ms  <->  the returned marks)
        * the REFUSAL            (Outcome.refused n     <->  TypeError raised)
        * the refusal's PAYLOAD  (which object the message names, i.e. that the
                                  FIRST offending element is the one reported)

This is deliberately NOT an "identity on canonical lists" check. An earlier
revision of this bundle modeled the callee as the identity, which made the
`isinstance(mark_obj, Mark)` gate at post:401 invisible to the spec; the model now
transliterates the callee in full, so G-AX has to exercise the gate. Every element
shape of mapping.md §2 is covered:

  Item.canonical m  <->  a Mark object                        (unwrap = identity)
  Item.wrapped m    <->  a MarkDecorator whose .mark is a Mark (unwrap = .mark)
  Item.foreign n    <->  anything whose unwrapped value is not a Mark

The changed flatten/MRO logic is modeled DEEPLY too (the `flattenSeq` fold) and
is G-CONF's business, not this gate's; no `axiom` is declared or consumed
(meta.json: axioms = []).

Imports nothing beyond `pytest` / `_pytest.mark.structures` — the same module
the gold patch edits, present in the SWE-Bench instance image. Exit 0 iff every
obligation holds.
"""
import random
import sys

import pytest
from _pytest.mark.structures import Mark, MarkDecorator, normalize_mark_list


# --------------------------------------------------------------------------
# The Lean deep model, transliterated. `Outcome` is ("collected", [tokens]) or
# ("refused", token); tokens stand for the Lean `Int` identity tokens, and are
# represented here by `id()` of the underlying object so equality of tokens is
# exactly object identity (mapping.md §2: only equality is observed).
# --------------------------------------------------------------------------

def mark_of(elem):
    """markOf : Item -> Option Mark. Mirrors post:400-401 — unwrap, then demand
    the unwrapped value be a Mark."""
    unwrapped = getattr(elem, "mark", elem)
    return unwrapped if isinstance(unwrapped, Mark) else None


def name_of(elem):
    """nameOf : Item -> Int. The identity of the object the refusal names, i.e.
    the value `repr`'d in the TypeError message at post:402."""
    return getattr(elem, "mark", elem)


def canonicalize(elems):
    """canonicalize : List Item -> Outcome (Solution.lean, pure region).
    Front-to-back: each element yields the annotation it makes available; the
    first element that makes none refuses the whole collection, naming it."""
    out = []
    for elem in elems:
        m = mark_of(elem)
        if m is None:
            return ("refused", name_of(elem))
        out.append(m)
    return ("collected", out)


# --------------------------------------------------------------------------
# The real callee, packaged as the same Outcome shape.
# --------------------------------------------------------------------------

def real_outcome(elems):
    """`list(normalize_mark_list(elems))` as an Outcome. post:386 drains the
    generator eagerly, so a raise IS the observable result of the collection."""
    try:
        return ("collected", list(normalize_mark_list(elems)))
    except TypeError as exc:
        return ("refused", str(exc))


def check(elems, ctx=""):
    """Assert the deep model agrees with the REAL callee on this element list,
    including which element a refusal names."""
    model = canonicalize(elems)
    real = real_outcome(elems)
    assert model[0] == real[0], (
        "canonicalize A-reference unsound%s on %r: model says %s, "
        "normalize_mark_list says %s" % (ctx, elems, model[0], real[0]))
    if model[0] == "collected":
        assert model[1] == real[1], (
            "canonicalize A-reference unsound%s on %r: model collected %r, "
            "normalize_mark_list collected %r" % (ctx, elems, model[1], real[1]))
        # element identity, not merely equality, on the success path:
        for got, want in zip(real[1], model[1]):
            assert got is want, (
                "normalize_mark_list returned a different object than the model "
                "extracted%s: %r vs %r" % (ctx, want, got))
        for m in real[1]:
            assert isinstance(m, Mark), (
                "normalize_mark_list yielded a non-Mark%s: %r" % (ctx, m))
    else:
        # The refusal payload: the message must name the object the model names,
        # and no other candidate offender. This is what pins `nameOf`, i.e. that
        # the FIRST offending element is the one reported.
        offender = model[1]
        expected = "got %s instead of Mark" % repr(offender)
        assert real[1] == expected, (
            "refusal payload mismatch%s on %r: model names %r (message %r), "
            "normalize_mark_list raised %r"
            % (ctx, elems, offender, expected, real[1]))


# --------------------------------------------------------------------------
# Element builders, one per Item constructor (mapping.md §2).
# --------------------------------------------------------------------------

def it_canonical(name):
    """Item.canonical: a Mark object, as `store_mark` persists."""
    return getattr(pytest.mark, name).mark


def it_wrapped(name):
    """Item.wrapped: a MarkDecorator carrying a Mark, the shape a hand-written
    `pytestmark = [pytest.mark.foo]` produces."""
    deco = getattr(pytest.mark, name)
    assert isinstance(deco, MarkDecorator)
    return deco


class _Plain:
    """A user object that is not, and does not carry, a Mark."""

    def __init__(self, tag):
        self.tag = tag

    def __repr__(self):
        return "<Plain %s>" % self.tag


class _WrapsJunk:
    """An object with a `.mark` attribute that is NOT a Mark: the unwrap
    succeeds and the isinstance check still refuses, and the object NAMED is the
    unwrapped junk, not the wrapper (post:400 then post:402)."""

    def __init__(self, payload):
        self.mark = payload

    def __repr__(self):
        return "<WrapsJunk>"


def it_foreign(kind, tag):
    if kind == "plain":
        return _Plain(tag)
    if kind == "class":
        # exactly the shape of testing/test_mark.py:590-602 (a module-level
        # `class pytestmark`), which is the existing test that asserts the gate
        # is observable.
        return type("pytestmark", (object,), {})
    if kind == "str":
        return "mark-%s" % tag
    if kind == "int":
        return tag
    if kind == "wrapsjunk":
        return _WrapsJunk("junk-%s" % tag)
    raise AssertionError(kind)


def main():
    names = ["foo", "bar", "baz", "xfail", "skip", "a", "b", "c"]
    foreign_kinds = ["plain", "class", "str", "int", "wrapsjunk"]

    boundary = []

    # --- the success path: canonical, wrapped, and mixtures ---------------
    boundary.append([])                                          # empty
    for n in names:
        boundary.append([it_canonical(n)])                       # single Mark
        boundary.append([it_wrapped(n)])                         # single wrapped
    boundary.append([it_canonical("a"), it_canonical("b"), it_canonical("c")])
    boundary.append([it_canonical("c"), it_canonical("a"), it_canonical("b")])
    boundary.append([it_canonical("foo"), it_canonical("foo")])  # duplicates
    boundary.append([it_wrapped("a"), it_canonical("b"), it_wrapped("c")])
    boundary.append([it_canonical(n) for n in names])
    # concatenations of several per-source lists (what the MRO walk assembles):
    boundary.append([it_canonical("c")] + [it_canonical("a")] + [it_canonical("b")])
    boundary.append([] + [it_canonical("foo")] + [] + [it_wrapped("bar")])

    # --- the REFUSAL path: one offender, at every position ----------------
    for kind in foreign_kinds:
        boundary.append([it_foreign(kind, 1)])                   # lone offender
        boundary.append([it_canonical("a"), it_foreign(kind, 2)])   # at the end
        boundary.append([it_foreign(kind, 3), it_canonical("a")])   # at the front
        boundary.append([it_canonical("a"), it_foreign(kind, 4),
                         it_canonical("b")])                        # in the middle
        boundary.append([it_wrapped("a"), it_foreign(kind, 5)])      # after a wrap

    # --- the PAYLOAD: several offenders, the FIRST must be the one named ---
    for k1 in foreign_kinds:
        for k2 in foreign_kinds:
            boundary.append([it_foreign(k1, 11), it_foreign(k2, 12)])
            boundary.append([it_canonical("a"), it_foreign(k1, 13),
                             it_canonical("b"), it_foreign(k2, 14)])

    for i, L in enumerate(boundary):
        check(L, ctx=" (boundary %d)" % i)

    # --- an explicit, named check of the first-offender rule ---------------
    # Two distinguishable offenders: the model must name the FIRST, and the real
    # callee must agree. If the model named the last (or nothing in particular),
    # this comparison fails.
    first, second = _Plain("FIRST"), _Plain("SECOND")
    both = [it_canonical("a"), first, it_canonical("b"), second]
    model = canonicalize(both)
    real = real_outcome(both)
    assert model == ("refused", first), (
        "the model must refuse naming the FIRST offender, got %r" % (model,))
    assert real == ("refused", "got %s instead of Mark" % repr(first)), (
        "the real callee must refuse naming the FIRST offender, got %r" % (real,))
    assert repr(first) != repr(second), "offender reprs must be distinguishable"

    # --- randomized fuzz over all three element shapes --------------------
    rng = random.Random(10356)
    pool_canonical = [it_canonical(n) for n in names]
    pool_wrapped = [it_wrapped(n) for n in names]
    n_refused = 0
    n_collected = 0
    N = 20000
    for _ in range(N):
        k = rng.randint(0, 12)
        L = []
        for j in range(k):
            r = rng.random()
            if r < 0.55:
                L.append(rng.choice(pool_canonical))
            elif r < 0.85:
                L.append(rng.choice(pool_wrapped))
            else:
                L.append(it_foreign(rng.choice(foreign_kinds), j))
        check(L, ctx=" (fuzz)")
        if canonicalize(L)[0] == "refused":
            n_refused += 1
        else:
            n_collected += 1

    # Both branches of the model must have been exercised, or this gate would be
    # passing on the success path alone (the exact hole the earlier revision had).
    assert n_refused > 1000, "fuzz produced too few refusals: %d" % n_refused
    assert n_collected > 1000, "fuzz produced too few collections: %d" % n_collected

    print("G-AX OK: canonicalize/markOf/nameOf deep model == the real "
          "normalize_mark_list on %d boundary + %d fuzz element lists "
          "(%d collected, %d refused); refusal identity and first-offender rule "
          "confirmed on all three element shapes."
          % (len(boundary), N, n_collected, n_refused))
    return 0


if __name__ == "__main__":
    sys.exit(main())
