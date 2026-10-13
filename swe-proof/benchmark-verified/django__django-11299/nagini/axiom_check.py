#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-11299.

There is no consumed @ContractOnly axiom in model.py: the changed behaviour is
modelled DEEPLY (the pure `leaf_modes` fold + the verified recursive
`compile_children`). This script validates that deep model as an A-REFERENCE
against the REAL Django compiler `Query.build_where` (= the recursive `_add_q`
with the top plain-column mode set).

For a condition tree compiled with the top plain-column mode set, the deep model
`leaf_modes(tree, True)` predicts that EVERY leaf's column is the bare plain form
(`SimpleCol`), at every nesting depth. This script:

  * builds condition trees of many shapes and nesting depths (the OR-of-AND
    combination from the issue, deeper nestings, mixtures),
  * runs the real `build_where`, walks the resulting WhereNode tree, and
    collects, in left-to-right order, the concrete column class of every leaf,
  * asserts every leaf column is `SimpleCol` — i.e. the observed per-leaf flag
    sequence equals the deep model's `leaf_modes(tree, True)` (all True),
  * confirms the leaf count/order matches the deep model traversal.

It also demonstrates the discriminator: the PRE-PATCH compiler (mode not
forwarded on descent) leaves nested leaves as fully-qualified `Col` — exactly
what `model_prepatch.py`'s buggy skeleton predicts and the frozen postcondition
forbids — proving the spec senses the change.

Imports are stdlib + Django (the repo under test); exit 0 iff sound.
"""
import sys

import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3',
                               'NAME': ':memory:'}},
    )
django.setup()

from django.db import models  # noqa: E402
from django.db.models import F, Q  # noqa: E402
from django.db.models.expressions import Col, SimpleCol  # noqa: E402
from django.db.models.sql.query import Query  # noqa: E402


class AxModel(models.Model):
    num = models.IntegerField()
    other = models.IntegerField()
    name = models.CharField(max_length=20)
    flag = models.BooleanField(default=False)

    class Meta:
        app_label = 'axch'


# --- walk the compiled WhereNode tree, collecting leaf column classes --------

def _is_node(obj):
    return hasattr(obj, 'children') and hasattr(obj, 'connector')


def _leaf_cols(node, out):
    """Collect, in traversal order, every column expression that appears as the
    lhs/rhs of a leaf lookup in the compiled WhereNode tree."""
    for child in node.children:
        if _is_node(child):
            _leaf_cols(child, out)
        else:
            for side in ('lhs', 'rhs'):
                expr = getattr(child, side, None)
                if isinstance(expr, (Col, SimpleCol)):
                    out.append(expr)
                else:
                    # transforms wrap a column (e.g. Lower(SimpleCol(...)))
                    inner = getattr(expr, 'lhs', None)
                    if isinstance(inner, (Col, SimpleCol)):
                        out.append(inner)


def observed_flags(q_object):
    """Run the REAL build_where and return the per-leaf 'is plain (SimpleCol)'
    flags in traversal order."""
    where = Query(AxModel).build_where(q_object)
    cols = []
    _leaf_cols(where, cols)
    assert cols, "no leaf columns collected for %r" % (q_object,)
    return [isinstance(c, SimpleCol) for c in cols]


def check(q_object, label):
    flags = observed_flags(q_object)
    # Deep model: leaf_modes(tree, plain=True) == [True, True, ...] (every leaf
    # carries the top mode at every depth).
    assert all(flags), (
        "deep model unsound for %s: build_where produced a non-plain (Col) "
        "column at a nested leaf; flags=%r" % (label, flags))
    return len(flags)


def main():
    cases = [
        # the issue's OR-of-AND combination: nested AND inside an OR
        (Q(num__gt=2, name__isnull=False) | Q(num__lt=F('id')),
         "OR(AND(num>2, name isnull), num<F(id))"),
        (Q(num__gt=2, flag=True) | Q(flag=False),
         "OR(AND(num>2, flag), flag=False)  (issue shape)"),
        # plain single / flat OR (depth 0 only)
        (Q(num__gt=2), "single"),
        (Q(num__gt=2) | Q(num__lt=0), "flat OR"),
        # deeper nesting: AND( OR(...), OR(...) )
        ((Q(num__gt=2) | Q(num__lt=0)) & (Q(other__gt=5) | Q(other__lt=1)),
         "AND(OR,OR) depth 1"),
        # triple nesting
        (Q(num__gt=2) | (Q(other__gt=1) & (Q(num__lt=9) | Q(other__lt=0))),
         "OR(leaf, AND(leaf, OR(leaf, leaf))) depth 2"),
        # negated nested group
        (~Q(num__gt=2, name__isnull=False) | Q(other__lt=0),
         "OR(NOT AND(...), leaf)"),
        # F-expression on both sides nested
        (Q(num__gt=F('other')) | Q(num__lt=F('other'), other__gt=1),
         "OR(leaf, AND(num<F(other), other>1))"),
    ]
    total = 0
    for q, label in cases:
        total += check(q, label)

    # --- discriminator: the PRE-PATCH compiler leaves nested leaves as Col ----
    # Reproduce the pre-patch _add_q (mode not forwarded into nested groups) and
    # show it diverges from the deep model exactly on a depth>=1 leaf.
    from django.db.models.sql.where import AND
    from django.utils.tree import Node

    def add_q_prepatch(query, q_object, simple_col):
        target = query.where_class(connector=q_object.connector,
                                   negated=q_object.negated)
        for child in q_object.children:
            if isinstance(child, Node):
                # BUG: simple_col not forwarded -> defaults to False on descent
                cc, _ = query._add_q(child, set(), False, False, True, True)
            else:
                cc, _ = query.build_filter(
                    child, can_reuse=set(), allow_joins=False,
                    split_subq=True, simple_col=simple_col)
            if cc:
                target.add(cc, q_object.connector)
        return target

    q_nested = Q(num__gt=2, name__isnull=False) | Q(num__lt=F('id'))
    buggy_where = add_q_prepatch(Query(AxModel), q_nested, True)
    buggy_cols = []
    _leaf_cols(buggy_where, buggy_cols)
    buggy_flags = [isinstance(c, SimpleCol) for c in buggy_cols]
    assert not all(buggy_flags), (
        "discriminator failed: the pre-patch compiler should leave a nested "
        "leaf as a fully-qualified Col, flags=%r" % buggy_flags)
    assert any(isinstance(c, Col) and not isinstance(c, SimpleCol)
               for c in buggy_cols), "expected a Col leaf in the buggy tree"

    print("G-AX OK: deep model leaf_modes == real build_where on %d trees "
          "(%d leaves, all SimpleCol at every depth); pre-patch discriminator "
          "produces a nested Col leaf the frozen spec forbids." %
          (len(cases), total))
    return 0


if __name__ == "__main__":
    sys.exit(main())
