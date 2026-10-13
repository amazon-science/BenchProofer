#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-16263.

This bundle consumes NO axioms. It has ONE deep-model reference (A-reference):

  collect_refs  ==  the real recursive reference-gatherer `get_refs()` that the
  gold patch adds to expressions / where-nodes:

      BaseExpression.get_refs():  union of get_refs() over source expressions
      Ref.get_refs():             {self.refs}
      WhereNode.get_refs():       union of get_refs() over children

  model.py models this DEEPLY as `collect_refs`: a flatten of the expression's
  source tree to a sequence of leaf codes, where a `Ref` leaf contributes its
  referent code and every non-referencing sub-expression contributes nothing;
  membership in `collect_refs(flatten(tree))` must equal membership in the real
  `get_refs()` set.

This script (run in-container, G-AX) constructs real Django expression trees,
runs the REAL `get_refs()`, and asserts the deep model agrees at the level the
decision observes (set membership of reference codes). It also exercises the two
decision discriminators the gold patch installs in `get_aggregation` against the
real Django expression attribute semantics, on the four F2P scenarios:

  (1) has_existing_aggregation = any existing annotation contains an aggregate /
      over-clause, or a HAVING/QUALIFY filter is retained.
  (2) the inner-query annotation mask keeps an alias iff it is a pushed-out
      summary name or is referenced (via get_refs) by a pushed-out summary.

Exit 0 iff every obligation holds. Imports Django (the repo whose method is the
reference) plus the standard library only.
"""
import os
import random
import sys

import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        USE_TZ=False,
    )
    django.setup()

from django.db.models import Value
from django.db.models.expressions import Ref, ExpressionWrapper
from django.db.models.functions import Concat, Lower
from django.db.models.aggregates import Count, Sum, Avg
from django.db.models.fields import IntegerField, CharField


# --- model.py reference encodings (kept in lock-step) -----------------------
#
# These transcribe the model.py @Pure definitions EXACTLY (same front-recursive
# shape) so the G-AX check drives the actual modelled fold, not a divergent
# hand-copy. The model is a Nagini @Pure over PSeq[int] (it imports
# nagini_contracts and cannot run as plain Python), so we mirror its recursion
# here and `_assert_collect_refs_mirrors_model` checks the transcription against
# the same fold spelled the obvious iterative way — they must agree on every
# tree the suite builds.

def collect_refs(tree):
    """Transcription of model.py's @Pure `collect_refs` (front-recursive):
        if len(tree)==0: return []
        if tree[0]!=0:   return [tree[0]] + collect_refs(tree[1:])
        else:            return collect_refs(tree[1:])
    i.e. the sequence of reference leaves (code != 0) in flatten order."""
    if len(tree) == 0:
        return []
    if tree[0] != 0:
        return [tree[0]] + collect_refs(tree[1:])
    return collect_refs(tree[1:])


def _collect_refs_iter(tree):
    """The same fold spelled iteratively — used only to cross-check the
    front-recursive transcription above mirrors the model with no drift."""
    return [node for node in tree if node != 0]


def seq_contains(seq, x):
    """Transcription of model.py's @Pure `seq_contains` (front-recursive)."""
    if len(seq) == 0:
        return False
    return seq[0] == x or seq_contains(seq[1:], x)


# --- flatten a real Django expression into the model's leaf-code carrier -----
#
# We map each distinct Ref.refs string to a small positive integer code; every
# non-Ref sub-expression flattens to its children (contributing 0 for itself).
# This mirrors collect_refs exactly: membership of a code in the flattened
# sequence == the alias is reachable as a Ref leaf.

def _code_for(refs, codes):
    if refs not in codes:
        codes[refs] = len(codes) + 1
    return codes[refs]


def _source_expressions(expr):
    getter = getattr(expr, "get_source_expressions", None)
    if getter is None:
        return []
    return getter()


def flatten_expr(expr, codes):
    """Flatten a real expression to the model's List[int] carrier.

    A `Ref` is a LEAF: it contributes ONLY its own referent code and the
    flatten does NOT descend into its source subtree. This matches the real
    reference-gatherer exactly — `Ref.get_refs(self): return {self.refs}` (a
    hard leaf with no recursion into `self.source`), while
    `BaseExpression.get_refs` unions over source expressions. A non-referencing
    node contributes nothing of its own but its children are still folded."""
    if isinstance(expr, Ref):
        # Leaf: referent code only; do NOT recurse into the Ref's source, exactly
        # as Ref.get_refs() returns {self.refs} and never calls get_refs on the
        # source. (Recursing here would over-collect refs nested inside a Ref's
        # source, which the real get_refs never sees.)
        return [_code_for(expr.refs, codes)]
    out = [0]  # a non-referencing node contributes nothing of its own
    for sub in _source_expressions(expr):
        if sub is not None:
            out.extend(flatten_expr(sub, codes))
    return out


def real_get_refs_codes(expr, codes):
    """The REAL recursive get_refs(), as a set of integer codes."""
    return {_code_for(r, codes) for r in expr.get_refs()}


def check_collect_refs(expr):
    """Assert the deep model collect_refs agrees with the real get_refs at the
    level the decision observes: set membership of reference codes."""
    codes = {}
    flat = flatten_expr(expr, codes)
    real = real_get_refs_codes(expr, codes)
    # The front-recursive transcription of the @Pure model must mirror the fold
    # with no drift (Defect 4: the check must drive the actual modelled fold).
    assert collect_refs(flat) == _collect_refs_iter(flat), (
        "collect_refs transcription drifted from the model fold on %r" % (expr,))
    model_set = set(collect_refs(flat))
    assert model_set == real, (
        "collect_refs deep model unsound on %r: real get_refs codes %r, "
        "deep model codes %r" % (expr, real, model_set))
    # And the per-alias membership the model.py inner_column_kept uses:
    for code in list(codes.values()):
        assert seq_contains(collect_refs(flat), code) == (code in real), (
            "membership mismatch on code %d for %r" % (code, expr))


# --- the A-reference checks: collect_refs == real get_refs -------------------

def check_collect_refs_suite():
    # Boundary expression trees (referencing and non-referencing leaves). These
    # deliberately include Refs whose SOURCE itself contains other Refs: the real
    # Ref.get_refs() is a leaf ({self.refs}) and must NOT report the inner Refs,
    # so these directly exercise the leaf-vs-recurse boundary (Defect 2).
    src = Sum("x")
    cases = [
        Ref("a", src),                                   # bare ref
        ExpressionWrapper(Ref("a", src), output_field=IntegerField()),
        ExpressionWrapper(Value(1), output_field=IntegerField()),    # no refs
        Concat(Ref("a", src), Value(" "), Ref("b", src)),            # two refs
        Concat(Value("x"), Value("y")),                              # no refs
        Avg(Ref("authors_count", src)),                              # ref under aggregate
        ExpressionWrapper(
            Concat(Ref("a", src), Concat(Ref("b", src), Ref("a", src))),
            output_field=CharField(),
        ),                                                            # nested + dup
        # --- nested-Ref-in-source cases (the divergent region) ---
        Ref("outer", Ref("inner", src)),                 # Ref whose source is a Ref:
                                                         #   real get_refs == {outer}
        Ref("outer", Concat(Ref("inner1", src), Ref("inner2", src))),
                                                         #   real get_refs == {outer}
        Avg(Ref("outer", Sum(Ref("inner", src)))),       # Ref-in-source under aggregate:
                                                         #   real get_refs == {outer}
        Concat(Ref("a", Ref("b", src)), Ref("c", src)),  # composite of nested + bare:
                                                         #   real get_refs == {a, c}
        ExpressionWrapper(
            Ref("outer", ExpressionWrapper(Ref("inner", src),
                                           output_field=IntegerField())),
            output_field=IntegerField(),
        ),                                               #   real get_refs == {outer}
    ]
    for e in cases:
        check_collect_refs(e)

    # Randomized fuzz: build random trees of Refs / non-ref nodes. CRUCIAL: a
    # Ref's SOURCE is itself a randomly-built subtree (which may contain more
    # Refs), so the fuzz actually constructs Ref-inside-Ref-source — the region
    # where a source-recursing flatten would over-collect. Composites also carry
    # Refs as children. (Defect 2: the old fuzz held the Ref source constant at
    # the leaf `Sum('x')`, never reaching this region.)
    rng = random.Random(16263)
    names = ["a", "b", "c", "d", "outer", "inner", "authors_count", "name_lower"]

    def build(depth):
        if depth <= 0 or rng.random() < 0.35:
            r = rng.random()
            if r < 0.5:
                # A Ref whose source is a (possibly Ref-bearing) subtree.
                return Ref(rng.choice(names), build(depth - 1))
            elif r < 0.7:
                return Ref(rng.choice(names), src)
            return Value(rng.randint(0, 9))
        kids = [build(depth - 1) for _ in range(rng.randint(1, 3))]
        return Concat(*kids) if len(kids) >= 2 else ExpressionWrapper(
            kids[0], output_field=IntegerField())

    for _ in range(5000):
        check_collect_refs(build(rng.randint(0, 4)))


# --- decision discriminator checks against real Django expression semantics --

def existing_summary_forces_derived(selected, summ, filter_summary):
    """model.py existing_summary_forces_derived, as a Python reference: the derived
    form is forced iff some SELECTED column carries a row-summary, or a retained
    HAVING/QUALIFY filter exists."""
    return any(
        s != 0 and m != 0 for s, m in zip(selected, summ)
    ) or filter_summary != 0


def inner_column_kept(alias, added, flat_ref_tree):
    """model.py inner_column_kept, as a Python reference."""
    return seq_contains(added, alias) or seq_contains(collect_refs(flat_ref_tree), alias)


def _selected_bit(query, alias):
    """The model's `selected` bit, GROUNDED in real Django: an annotated column
    participates in the wrapping decision iff its alias is in `annotation_select`
    (i.e. it is a SELECTED annotation, as `annotate()` produces — not an
    alias-only annotation, as `alias()` produces via add_annotation(select=False))."""
    return 1 if alias in query.annotation_select else 0


def _summary_bit(ann):
    """The model's `summ` bit: the annotation carries a row-summary iff it is an
    aggregate or a windowed value (the two attributes the gold disjoins)."""
    return 1 if (getattr(ann, "contains_aggregate", True)
                 or getattr(ann, "contains_over_clause", True)) else 0


def check_decisions():
    from django.db.models.sql.query import Query

    # ---- GROUND the `selected` bit against real Django add_annotation -------
    # `annotate(x=expr)` => add_annotation(expr, x, select=True) => x in
    #   annotation_select. `alias(x=expr)` => add_annotation(expr, x,
    #   select=False) => x NOT in annotation_select. The wrapping decision reads
    #   ONLY annotation_select (the gold's source switch self.annotations ->
    #   self.annotation_select). We exercise both on a real Query.
    q_sel = Query(None)
    q_sel.add_annotation(Count(Value(1)), "authors_count", select=True)
    assert _selected_bit(q_sel, "authors_count") == 1, (
        "an annotate()d column must be SELECTED (in annotation_select)")

    q_alias = Query(None)
    q_alias.add_annotation(Count(Value(1)), "authors_count", select=False)
    assert _selected_bit(q_alias, "authors_count") == 0, (
        "an alias()-only column must NOT be selected (absent from "
        "annotation_select) — this is the source switch the gold installs")

    # (test 1: test_unused_aliased_aggregate_pruned) an alias-ONLY aggregate:
    #   selected = 0, summ = 1  -> MUST NOT force the derived form (1 SELECT).
    cnt = Count(Value(1))
    assert cnt.contains_aggregate is True
    assert existing_summary_forces_derived([0], [_summary_bit(cnt)], 0) is False, (
        "an alias-only (unselected) aggregate must NOT force wrapping; only the "
        "annotation_select source stops it (the predicate alone would wrap)")

    # (test 2: test_non_aggregate_annotation_pruned) a SELECTED non-aggregate
    #   Lower(...): selected = 1, summ = 0 -> MUST NOT force the derived form.
    lower = Lower(Value("name"))
    assert lower.contains_aggregate is False
    assert lower.contains_over_clause is False
    assert existing_summary_forces_derived([1], [_summary_bit(lower)], 0) is False, (
        "a selected non-aggregate annotation must NOT force wrapping")

    # (test 3: test_unreferenced_aggregate_annotation_pruned) a SELECTED Count()
    #   aggregate: selected = 1, summ = 1 -> wrapping required.
    assert existing_summary_forces_derived([1], [_summary_bit(cnt)], 0) is True, (
        "a selected aggregate annotation must force wrapping")

    # a SELECTED over-clause annotation also forces wrapping (no HAVING needed).
    assert existing_summary_forces_derived([1], [1], 0) is True
    # a retained HAVING/QUALIFY filter alone forces wrapping (even with no
    # selected summary column).
    assert existing_summary_forces_derived([1], [0], 1) is True
    assert existing_summary_forces_derived([0], [1], 1) is True
    # no selected summary and no filter -> no wrapping.
    assert existing_summary_forces_derived([1, 0], [0, 0], 0) is False
    assert existing_summary_forces_derived([0, 0], [1, 1], 0) is False  # all unselected
    assert existing_summary_forces_derived([], [], 0) is False

    # (test 3) unreferenced aggregate annotation 'authors_count' pruned: the
    # pushed-out summary __count references nothing.
    src = Sum("x")
    count_star = Count("*")              # the __count summary, no refs
    codes = {}
    flat = flatten_expr(count_star, codes)
    ac = _code_for("authors_count", codes)
    cstar = _code_for("__count", codes)
    # __count itself is kept (it is the pushed-out name); authors_count is not
    # referenced by it, so it is pruned.
    assert inner_column_kept(cstar, [cstar], flat) is True
    assert inner_column_kept(ac, [cstar], flat) is False, (
        "unreferenced aggregate annotation must be pruned from inner select")

    # (test 4) referenced aggregate annotation 'authors_count' kept: the
    # pushed-out summary Avg(Ref('authors_count', ...)) references it.
    avg = Avg(Ref("authors_count", src))
    codes2 = {}
    flat2 = flatten_expr(avg, codes2)
    ac2 = _code_for("authors_count", codes2)
    avg_name = _code_for("__aggr", codes2)
    assert inner_column_kept(ac2, [avg_name], flat2) is True, (
        "referenced aggregate annotation must be kept in inner select")
    # And the real get_refs of the pushed-out Avg DOES contain authors_count.
    assert "authors_count" in avg.get_refs()


def main():
    check_collect_refs_suite()
    check_decisions()
    print("G-AX OK: collect_refs deep model (== real get_refs, Ref-as-leaf) "
          "sound on 12 boundary (incl. nested Ref-in-source) + 5000 fuzz "
          "expression trees whose Ref sources are themselves Ref-bearing "
          "subtrees; the front-recursive transcription mirrors the model fold; "
          "the wrapping (selected-AND-summary, grounded in annotation_select) "
          "and masking discriminators agree with real Django semantics on all "
          "F2P scenarios incl. the alias-only-aggregate source case.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
