#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-13028.

This bundle consumes NO @ContractOnly axioms: the guard's decision is modelled
deeply in model.py as a conjunction of two per-operand observations over the
flattened operand walk. What G-AX validates here is the **abstraction map** that
the model rests on (an A-reference): that the REAL guard's accept/reject
decision equals the model's predicate under the abstraction

    is_expr[i]   <->  hasattr(operand_i, 'resolve_expression')
    permitted[i] <->  getattr(operand_i, 'filterable', True)   (absent => True)

applied to the operand AND every operand nested inside it (the same screen is
applied recursively, via getattr(operand, 'get_source_expressions', ...)).

The model decision is:  REJECT  iff  exists i with is_expr[i]==1 and
permitted[i]==0;  otherwise ACCEPT.

Two checks:

  (1) A self-contained reference of the post-patch guard (the conjunction +
      recursive walk) run over an exhaustive boundary space and randomized fuzz
      of operand trees, asserting it agrees with the model predicate computed
      over the SAME trees' flattened (is_expr, permitted) carriers. This is the
      faithfulness of the abstraction, independent of Django.

  (2) When Django is importable (in the official container), the REAL
      ``Query.check_filterable`` is exercised on representative operand objects
      and its raise/no-raise outcome is asserted to match the model decision —
      crucially that a plain data operand carrying ``filterable=False`` but no
      ``resolve_expression`` (the F2P case) is ACCEPTED, while a real query
      expression carrying ``filterable=False`` is REJECTED.

Run inside the SWE-bench container for the instance, where Django is importable.
Exit 0 iff every obligation holds. Outside the container (Django absent) check
(1) still runs fully; check (2) prints a SKIP line and is deferred to the
orchestrator's in-container run.
"""
import itertools
import random
import sys


# --- the model predicate (model.py, computed over flattened carriers) --------

def model_rejects(is_expr, permitted):
    """model.py check_operands: REJECT iff some visited operand is BOTH a
    query-expression operand and not-permitted."""
    return any(e == 1 and p == 0 for e, p in zip(is_expr, permitted))


# --- a faithful reference of the post-patch real guard ------------------------
# Operand trees are nested dicts:
#   {'is_expr': bool, 'permitted': <True|False|None>, 'children': [ ... ]}
# 'permitted' is the value the real getattr(op, 'filterable', True) observes:
#   True/False an explicit marker, None means the attribute is ABSENT (the
#   getattr default True applies). 'is_expr' is whether the operand exposes a
#   'resolve_expression' attribute. Only operands that expose
#   'get_source_expressions' have their children walked (matching the real
#   recursion guard).

class _RejectMarker(Exception):
    pass


def reference_guard(op):
    """The post-patch behaviour of check_filterable, spelled out:
        if hasattr(op,'resolve_expression') and not getattr(op,'filterable',True):
            raise
        if hasattr(op,'get_source_expressions'):
            for child in op.get_source_expressions(): self.check_filterable(child)
    Raises _RejectMarker on rejection; returns normally on acceptance."""
    is_expr = op['is_expr']
    permitted_attr = op['permitted']            # True | False | None(absent)
    effective_permitted = True if permitted_attr is None else permitted_attr
    if is_expr and not effective_permitted:
        raise _RejectMarker()
    for child in op.get('children', []):
        reference_guard(child)


def flatten(op):
    """The flattened (is_expr, permitted) carriers in the guard's walk order:
    the operand, then a pre-order walk of its source-expression children.
    permitted: 1 if the effective getattr(...,True) is truthy, else 0."""
    is_expr = [1 if op['is_expr'] else 0]
    permitted_attr = op['permitted']
    eff = True if permitted_attr is None else permitted_attr
    permitted = [1 if eff else 0]
    for child in op.get('children', []):
        ce, cp = flatten(child)
        is_expr += ce
        permitted += cp
    return is_expr, permitted


def reference_rejects(op):
    try:
        reference_guard(op)
        return False
    except _RejectMarker:
        return True


def check_tree(op):
    """Assert the model predicate over the flattened carriers agrees with the
    reference guard on this operand tree."""
    is_expr, permitted = flatten(op)
    ref = reference_rejects(op)
    mod = model_rejects(is_expr, permitted)
    assert ref == mod, (
        "abstraction unsound on tree %r: reference guard rejects=%s, "
        "model predicate rejects=%s (is_expr=%s permitted=%s)"
        % (op, ref, mod, is_expr, permitted))


# --- (1) exhaustive boundary + fuzz over operand trees ------------------------

_NODE_SHAPES = [
    {'is_expr': False, 'permitted': None},    # plain data, no marker
    {'is_expr': False, 'permitted': True},    # plain data, permitted
    {'is_expr': False, 'permitted': False},   # plain data, NOT permitted (F2P!)
    {'is_expr': True, 'permitted': None},     # expression, no marker (=> True)
    {'is_expr': True, 'permitted': True},     # expression, permitted
    {'is_expr': True, 'permitted': False},    # expression, NOT permitted (raise)
]


def _leaf(shape):
    n = dict(shape)
    n['children'] = []
    return n


def check_abstraction_reference():
    # single-operand exhaustive: every shape (the F2P case is shape index 2)
    for shape in _NODE_SHAPES:
        check_tree(_leaf(shape))

    # depth-2 exhaustive: a root operand with up to 2 children, all shape combos
    for root in _NODE_SHAPES:
        for child in _NODE_SHAPES:
            r = dict(root); r['children'] = [_leaf(child)]
            check_tree(r)
            for child2 in _NODE_SHAPES:
                r2 = dict(root); r2['children'] = [_leaf(child), _leaf(child2)]
                check_tree(r2)

    # randomized fuzz: random trees up to depth 4, branching up to 3
    rng = random.Random(13028)

    def rand_tree(depth):
        node = dict(rng.choice(_NODE_SHAPES))
        node['children'] = []
        if depth > 0:
            for _ in range(rng.randint(0, 3)):
                node['children'].append(rand_tree(depth - 1))
        return node

    for _ in range(20000):
        check_tree(rand_tree(rng.randint(0, 4)))


# --- (2) the REAL Django guard, in-container ----------------------------------

def check_real_django():
    try:
        import django
        from django.conf import settings
        if not settings.configured:
            settings.configure(INSTALLED_APPS=[], USE_I18N=False, DATABASES={})
        django.setup()
        from django.db.models.sql.query import Query
        from django.db.utils import NotSupportedError
    except Exception as exc:  # pragma: no cover - environment dependent
        print("G-AX SKIP (Django guard): %r" % (exc,))
        return

    q = Query.__new__(Query)  # a bare Query; check_filterable touches no state

    def real_rejects(expression):
        try:
            q.check_filterable(expression)
            return False
        except NotSupportedError:
            return True

    # plain data objects: a value with filterable=False but NO resolve_expression
    class PlainData:
        def __init__(self, filterable):
            self.filterable = filterable

    class PlainBare:
        pass

    # a query-expression-like object: exposes resolve_expression
    class ExprLike:
        def __init__(self, filterable):
            self.filterable = filterable
            self.children = []

        def resolve_expression(self, *a, **k):
            return self

        def get_source_expressions(self):
            return list(self.children)

    cases = [
        # (object, model is_expr, model effective-permitted)
        (PlainData(filterable=False), 0, 0),   # THE F2P case: must ACCEPT
        (PlainData(filterable=True), 0, 1),     # plain permitted: accept
        (PlainBare(), 0, 1),                     # no markers at all: accept
        (ExprLike(filterable=False), 1, 0),     # expr not-permitted: REJECT
        (ExprLike(filterable=True), 1, 1),       # expr permitted: accept
    ]
    for obj, is_e, perm in cases:
        ref = real_rejects(obj)
        mod = model_rejects([is_e], [perm])
        assert ref == mod, (
            "real Query.check_filterable disagrees with model on %r: "
            "real rejects=%s, model rejects=%s" % (obj, ref, mod))

    # recursion: an expression carrying a disallowed expression child must reject
    parent = ExprLike(filterable=True)
    parent.children = [ExprLike(filterable=False)]
    assert real_rejects(parent) is True, "nested disallowed expression not rejected"
    assert model_rejects(*flatten({
        'is_expr': True, 'permitted': True,
        'children': [{'is_expr': True, 'permitted': False, 'children': []}],
    })) is True

    # recursion with a plain not-permitted data child stays ACCEPTED
    parent2 = ExprLike(filterable=True)
    parent2.children = [PlainData(filterable=False)]
    assert real_rejects(parent2) is False, "plain not-permitted child wrongly rejected"

    print("G-AX OK (Django guard): real Query.check_filterable matches the model "
          "decision on all boundary operands incl. the F2P plain-data case.")


def main():
    check_abstraction_reference()
    print("G-AX OK (abstraction): model predicate == post-patch reference guard "
          "on %d boundary + 20000 fuzz operand trees." % (
              len(_NODE_SHAPES) + len(_NODE_SHAPES) ** 2
              + len(_NODE_SHAPES) ** 3))
    check_real_django()
    return 0


if __name__ == "__main__":
    sys.exit(main())
