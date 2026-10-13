#!/usr/bin/env python3
"""G-AX executable soundness check for pytest-dev__pytest-5631.

There is NO consumed `@ContractOnly` axiom in model.py: the membership decision
is the CHANGED operation and is modelled DEEPLY (the total identity classifier
`counts_as_mock`, the front-recursive count `count_sentinel_directives`). This
script validates the deep model against the REAL runtime semantics it abstracts
(an A-reference check):

  The model abstracts each replacement directive by an integer kind tag:
    0 — binds an attribute name        (never counts)
    1 — no attribute name; value IS a placeholder singleton by identity (counts)
    2 — no attribute name; value is a non-placeholder, comparable    (excluded)
    3 — no attribute name; value's equality is non-truth-evaluable   (excluded)

  The two facts the deep model relies on, checked here against real Python
  objects (the very `unittest.mock.DEFAULT` placeholder singleton the patched
  code consults, and a NumPy-like object whose `__eq__` yields a non-scalar):

   (1) The IDENTITY decision `value is sentinel` is TOTAL — it returns a
       definite boolean for every value, including the non-truth-evaluable one
       (kind 3), and is True exactly for the sentinel itself (kind 1).

   (2) The VALUE-EQUALITY membership decision `value in sentinels` (the
       pre-patch operation) RAISES on the kind-3 value, while identity does not.
       This is the discriminator the deep model encodes: the total identity
       count never fails; the equality count does.

  And that the counting function the model computes (`count_sentinel_directives`
  over the kind tags) equals the real count obtained by the identity decision
  over a population of real directive objects (boundary + randomized fuzz).

Imports nothing repo-specific: `unittest.mock` is the Python standard library —
the very module the patched code consults for its placeholder singleton. Exit 0
iff every obligation holds.
"""
import random
import sys
import unittest.mock as um


# --- a faithful stand-in for the real directive objects ----------------------
# Mirrors the only attributes the helper reads on a `_patch` object: the
# replacement value (`.new`) and the bound attribute name (`.attribute_name`).

class Directive:
    def __init__(self, attribute_name, new):
        self.attribute_name = attribute_name
        self.new = new


class NumpyLike:
    """An object whose equality is NON-truth-evaluable (kind 3) — exactly the
    shape from issue #5606: comparing it for equality raises rather than
    yielding a usable boolean (NumPy raises on truth-testing a multi-element
    array; here we make `__eq__` itself raise, which is the strongest form)."""

    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        raise ValueError(
            "like numpy, cannot compare against others for truth")

    __hash__ = None


SENTINELS = [um.DEFAULT]   # the real placeholder singletons the helper consults


# --- model.py deep-model reference encodings (kept in lock-step) -------------

def counts_as_mock(kind):
    return kind == 1


def count_sentinel_directives(kinds):
    return sum(1 for k in kinds if counts_as_mock(k))


# --- the real-semantics classification --------------------------------------

def real_kind(d):
    """The kind tag the model assigns to a real directive, computed by the REAL
    identity decision (the post-patch operation). Total: never raises."""
    if d.attribute_name:
        return 0
    # identity membership against the real placeholder singletons (total)
    is_sentinel = any(d.new is s for s in SENTINELS)
    if is_sentinel:
        return 1
    # distinguish a non-truth-evaluable equality (kind 3) from a comparable
    # non-placeholder (kind 2), purely to label the population for the check.
    try:
        _ = bool(d.new == um.DEFAULT)
        return 2
    except Exception:
        return 3


def real_count_identity(directives):
    """The count produced by the REAL identity decision (post-patch). Total."""
    n = 0
    for d in directives:
        if not d.attribute_name and any(d.new is s for s in SENTINELS):
            n += 1
    return n


def real_count_equality(directives):
    """The count produced by the REAL value-equality membership (pre-patch).
    Raises on a kind-3 directive — the bug. Returns a sentinel marker 'RAISED'
    instead of crashing the harness."""
    try:
        n = 0
        for d in directives:
            if not d.attribute_name and (d.new in SENTINELS):
                n += 1
        return n
    except ValueError:
        return "RAISED"


# --- the checks --------------------------------------------------------------

def check_facts():
    # (1) identity is total and exact on the placeholder singleton
    assert (um.DEFAULT is um.DEFAULT) is True
    assert (NumpyLike(1) is um.DEFAULT) is False
    assert (object() is um.DEFAULT) is False
    # identity never raises, even on the non-truth-evaluable value:
    nl = NumpyLike(50)
    assert (nl is um.DEFAULT) is False        # must NOT raise

    # (2) value-equality membership RAISES on the kind-3 value (the pre-patch
    #     operation), while identity does not.
    raised = False
    try:
        _ = nl in SENTINELS
    except ValueError:
        raised = True
    assert raised, (
        "expected value-equality membership to raise on the NumPy-like value")


def check_population(directives):
    kinds = [real_kind(d) for d in directives]
    # the model's count over the kind tags == the real identity count
    model_n = count_sentinel_directives(kinds)
    real_n = real_count_identity(directives)
    assert model_n == real_n, (
        "deep model count %d != real identity count %d on %r"
        % (model_n, real_n, kinds))
    # 0 <= count <= len  (the soundness clause)
    assert 0 <= model_n <= len(directives)
    # if any directive is kind 3, the pre-patch equality count RAISES while the
    # model's (identity) count is well-defined.
    if any(k == 3 for k in kinds):
        assert real_count_equality(directives) == "RAISED", (
            "expected pre-patch equality count to raise on a kind-3 population")
    else:
        # otherwise the two disciplines agree (DEFAULT equals only itself)
        assert real_count_equality(directives) == real_n


def sample_value(rng):
    r = rng.random()
    if r < 0.30:
        return um.DEFAULT            # kind 1 (if no attribute_name)
    if r < 0.60:
        return NumpyLike(rng.randint(0, 100))   # kind 3
    if r < 0.80:
        return object()              # kind 2 (comparable non-placeholder)
    return rng.choice([0, 1, "x", (1, 2), None, 3.5])   # kind 2


def main():
    check_facts()

    # boundary populations
    boundary = [
        [],
        [Directive(None, um.DEFAULT)],                      # one mock arg
        [Directive("name", um.DEFAULT)],                    # attr-bound: 0
        [Directive(None, NumpyLike(50))],                   # kind 3 alone
        [Directive(None, object())],                        # kind 2 alone
        [Directive(None, um.DEFAULT), Directive(None, NumpyLike(1))],
        [Directive("a", um.DEFAULT), Directive(None, um.DEFAULT),
         Directive(None, NumpyLike(2)), Directive(None, 5)],
    ]
    for pop in boundary:
        check_population(pop)

    # randomized fuzz
    rng = random.Random(5631)
    for _ in range(20000):
        n = rng.randint(0, 8)
        pop = []
        for _ in range(n):
            attr = None if rng.random() < 0.7 else "attr%d" % rng.randint(0, 3)
            pop.append(Directive(attr, sample_value(rng)))
        check_population(pop)

    print("G-AX OK: identity decision total + exact on the real placeholder "
          "singleton; value-equality membership raises on the NumPy-like value; "
          "deep-model count == real identity count over %d boundary + 20000 "
          "fuzz populations." % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
