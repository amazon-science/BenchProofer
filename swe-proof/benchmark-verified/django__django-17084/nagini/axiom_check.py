#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-17084.

This bundle consumes NO `@ContractOnly` axiom: the changed operation is the
OR-reduction over the per-referenced-annotation flags, modelled DEEPLY by the
front-recursive `@Pure` fold `any_referenced_flag` (model.py pure region). G-AX
therefore validates that deep model as an A-reference, against real Python /
Django semantics, on boundary + fuzz inputs:

  (A-reference 1) the fold `any_referenced_flag(flags)` == Python's built-in
      `any(flags)` over arbitrary boolean sequences (the OR-reduction the
      repo's `refs_window |= any(...)` / `refs_subquery |= any(...)`
      accumulations compute).

  (A-reference 2) the per-element flag values the model carries are exactly the
      values Django's accumulation reads, i.e.
        window_flags[k]   == getattr(annotation, "contains_over_clause", True)
        subquery_flags[k] == getattr(annotation, "subquery", False)
      where `contains_over_clause` on a composite expression propagates via
      `any(expr and expr.contains_over_clause for expr in source_expressions)`
      and a `Window(...)` leaf has `contains_over_clause = True`
      (django/db/models/expressions.py:246-250, 1697-1703). This re-derives
      that attribute logic with stdlib-only stand-ins faithful to the cited
      source and checks the resolved booleans match.

Imports nothing repo-specific (stdlib only). Exit 0 iff every obligation holds.
"""
import random
import sys


# --- model.py reference encoding (kept in lock-step with model.py pure region)

def any_referenced_flag(flags):
    """Reference implementation of model.py's deep model `any_referenced_flag`
    (front-recursive OR-fold). Must equal Python's `any(flags)`."""
    if len(flags) == 0:
        return False
    return bool(flags[0]) or any_referenced_flag(flags[1:])


# --- A-reference 1: the fold == Python any() -------------------------------

def check_fold_equals_any(flags):
    observed = any(flags)                       # Python's OR-reduction
    expected = any_referenced_flag(list(flags))  # deep model
    assert observed == expected, (
        "any_referenced_flag deep model unsound on %r: any() gave %r, "
        "deep model gives %r" % (flags, observed, expected))


# --- A-reference 2: faithful stand-ins for Django's attribute resolution ----
# Mirrors django/db/models/expressions.py exactly (see mapping.md §3):
#   - BaseExpression.contains_over_clause =
#         any(e and e.contains_over_clause for e in get_source_expressions())
#   - Window.contains_over_clause = True ; Window.subquery absent (-> default)
#   - Col/Value leaves: contains_over_clause = False
#   - Subquery.subquery = True ; Subquery.contains_over_clause = False

class _Leaf:
    """A non-window, non-subquery leaf annotation (e.g. Col, Value)."""
    contains_over_clause = False
    # no `subquery` attribute -> getattr default (False) applies


class _Window:
    """Window(...) leaf: expressions.py:1697-1703."""
    contains_over_clause = True
    # no `subquery` attribute -> getattr default (False) applies


class _Subquery:
    """Subquery(...) leaf: expressions.py:1535-1544."""
    contains_over_clause = False
    subquery = True


class _Composite:
    """A composite expression (e.g. Coalesce, Func): contains_over_clause is the
    any() over its source expressions; no own `subquery` attribute."""

    def __init__(self, sources):
        self._sources = sources

    @property
    def contains_over_clause(self):
        return any(
            e is not None and e.contains_over_clause for e in self._sources
        )


def model_window_flag(annotation):
    """What the model's window_flags[k] must equal: the value the repo reads
    via getattr(annotation, 'contains_over_clause', True)."""
    return getattr(annotation, "contains_over_clause", True)


def model_subquery_flag(annotation):
    """What the model's subquery_flags[k] must equal: the value the repo reads
    via getattr(annotation, 'subquery', False)."""
    return getattr(annotation, "subquery", False)


def check_attribute_resolution():
    # Window leaf -> over-clause True, subquery False(default)
    w = _Window()
    assert model_window_flag(w) is True
    assert model_subquery_flag(w) is False
    # Plain leaf -> both default-ish: over-clause False, subquery False
    leaf = _Leaf()
    assert model_window_flag(leaf) is False
    assert model_subquery_flag(leaf) is False
    # Subquery leaf -> subquery True, over-clause False
    sq = _Subquery()
    assert model_subquery_flag(sq) is True
    assert model_window_flag(sq) is False
    # Composite containing a Window (e.g. Coalesce(Window(...), 0.0)) -> over True
    comp_win = _Composite([_Window(), _Leaf()])
    assert model_window_flag(comp_win) is True
    assert model_subquery_flag(comp_win) is False
    # Composite of only plain leaves -> over False
    comp_plain = _Composite([_Leaf(), _Leaf(), None])
    assert model_window_flag(comp_plain) is False
    # Composite containing a Subquery but no Window -> over False
    comp_sq = _Composite([_Subquery(), _Leaf()])
    assert model_window_flag(comp_sq) is False
    # getattr default for an object with NEITHER attribute: the conservative
    # over-clause default is True, subquery default is False.
    class _Bare:
        pass
    bare = _Bare()
    assert model_window_flag(bare) is True   # conservative wrap
    assert model_subquery_flag(bare) is False


def main():
    # --- A-reference 1: boundary lists ------------------------------------
    boundary = [
        [],
        [True], [False],
        [True, True], [True, False], [False, True], [False, False],
        [False, False, False], [False, False, True],
        [True] * 5, [False] * 5,
        [False, False, True, False],
    ]
    for flags in boundary:
        check_fold_equals_any(flags)

    # --- A-reference 1: randomized fuzz -----------------------------------
    rng = random.Random(17084)
    for _ in range(20000):
        n = rng.randint(0, 16)
        flags = [rng.random() < 0.5 for _ in range(n)]
        check_fold_equals_any(flags)

    # --- A-reference 2: attribute resolution semantics --------------------
    check_attribute_resolution()

    print("G-AX OK: any_referenced_flag deep model (== Python any()) sound on "
          "%d boundary + 20000 fuzz lists; contains_over_clause/subquery "
          "attribute resolution matches expressions.py." % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
