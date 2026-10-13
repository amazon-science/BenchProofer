#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-11299 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Invariant/Assert/Unfold/Fold) stripped. `QNode` copies
over as a plain attribute holder; the @Pure helpers (`q_kind`, `empty_modes`,
`leaf_modes`) copy over as plain functions on top of a small immutable-tuple
PSeq shim and serve as an internal cross-check of the executable shadow. There
are no @ContractOnly callees in this bundle (the changed traversal is modelled
deeply).

ORACLE: the REAL patched repo function the model models per mapping.md — the
recursive condition-tree compiler `Query._add_q` (the top-level entry
`build_where` is `_add_q` with the plain-column mode set). The gate applies
patch.diff to /testbed before this script runs. Per mapping.md section 2 the
observation is the per-leaf column FORM in left-to-right traversal order: a
leaf's flag is True iff its compiled column reference is the bare table-free
form (`SimpleCol`) rather than the fully-qualified form (`Col`).

TYPE BRIDGE (mapping.md section 2, bijective on the modeled carrier):
  * a QNode sibling/inner tree <-> a Q condition tree: the `nxt` chain is a
    node's child list, a kind==1 node's `inner` chain is the nested group's
    own child list, a kind==0 node is one atomic leaf comparison;
  * `plain: bool` <-> the compiler's plain-column mode argument (identity);
  * the shadow's List[bool] <-> the ordered per-leaf `isinstance(col,
    SimpleCol)` flags collected by walking the compiled WhereNode tree.
  Every generated leaf is a single-column comparison against a distinct
  constant, so each leaf contributes exactly one column reference and the flag
  lists align position-by-position. Group connectors (AND/OR) and negation are
  outside the modeled carrier (orthogonal to the column-form decision, see
  mapping.md section 2) and are held at varied-connector / non-negated.

INPUT DOMAIN: the precondition demands only a well-formed finite tree
(q_pred), i.e. kind in {0,1} with acyclic inner/nxt links, plus an arbitrary
`plain` boolean — every generated (tree, plain) pair is Requires-satisfying.
Generation stresses the discriminating axis: nesting depth (leaves at depth
0..8), group position, empty groups, wide flat lists, both `plain` values.

>= 1e5 Requires-satisfying inputs: boundary trees x both modes + 100000 fuzzed
(tree, plain) pairs. Pinned fuzz seed: 112990.

Exit 0 iff zero disagreements; on disagreement prints the input tree and both
flag lists and exits 1. stdlib + Django (the repo under test) only; the
container is Python 3.6.
"""
import json
import random
import sys

SEED = 112990
N_FUZZ = 100000

# --- repo under test (patched /testbed) --------------------------------------

import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3',
                               'NAME': ':memory:'}},
    )
django.setup()

from django.db import models            # noqa: E402
from django.db.models import Q          # noqa: E402
from django.db.models.expressions import Col, SimpleCol  # noqa: E402
from django.db.models.sql.query import Query              # noqa: E402


class ConfModel(models.Model):
    num = models.IntegerField()
    other = models.IntegerField()
    name = models.CharField(max_length=20)
    flag = models.BooleanField(default=False)

    class Meta:
        app_label = 'confch'


# --- PSeq shim: immutable sequence with the operations the pure region uses ---

class PSeq(object):
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def take(self, n):
        return PSeq._wrap(self._t[:n])

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

    def __add__(self, other):
        return PSeq._wrap(self._t + other._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def list(self):
        return list(self._t)


def ToSeq(lst):
    return PSeq._wrap(lst)


# --- QNode and the pure region of model.py, contracts stripped ----------------

class QNode(object):
    def __init__(self, kind, inner, nxt):
        self.kind = kind      # 0 = leaf, 1 = group
        self.inner = inner    # head of a group's child list (meaningful if group)
        self.nxt = nxt        # next sibling in the current child list


def q_kind(n):
    return n.kind


def empty_modes():
    return PSeq(True).take(0)


def leaf_modes(head, plain):
    if head is None:
        return empty_modes()
    if q_kind(head) == 0:                       # leaf: one flag at current mode
        return PSeq(plain) + leaf_modes(head.nxt, plain)
    # group: its children at the SAME mode, then continue with the siblings.
    return leaf_modes(head.inner, plain) + leaf_modes(head.nxt, plain)


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def append_all(result, src):
    i = 0
    while i < len(src):
        result.append(src[i])
        i = i + 1


def compile_children(head, plain):
    result = []  # type: list
    if head is None:
        return result
    if head.kind == 0:                          # leaf -> one column reference
        result.append(plain)
        rest = compile_children(head.nxt, plain)
        append_all(result, rest)
        return result
    # group -> descend with the SAME mode, then continue with siblings.
    sub = compile_children(head.inner, plain)
    tail = compile_children(head.nxt, plain)
    append_all(result, sub)
    append_all(result, tail)
    return result


# --- bridge: abstract tree shape -> QNode (shadow) and Q object (oracle) ------
#
# A tree shape is a nested list: 'L' is a leaf, a list is a group whose items
# are that group's children (in order).

def shape_to_qnode(items):
    head = None
    for item in reversed(items):
        if item == 'L':
            head = QNode(0, None, head)
        else:
            head = QNode(1, shape_to_qnode(item), head)
    return head


# distinct single-column leaf comparisons, cycled with a strictly increasing
# constant so no two leaf clauses inside one tree can ever compare equal (an
# accumulator that deduplicated equal clauses would misalign the flag lists
# as a bridge artifact, not a real disagreement)
_LEAF_KINDS = ('num__gt', 'other__lt', 'num__lt', 'other__gt', 'name__exact',
               'num__exact', 'other__exact')


class LeafFactory(object):
    def __init__(self):
        self.n = 0

    def next(self):
        k = _LEAF_KINDS[self.n % len(_LEAF_KINDS)]
        self.n += 1
        if k == 'name__exact':
            return (k, 'v%d' % self.n)
        return (k, self.n)


def shape_to_q(items, rng, factory):
    q = Q()
    q.connector = rng.choice((Q.AND, Q.OR))
    children = []
    for item in items:
        if item == 'L':
            children.append(factory.next())
        else:
            children.append(shape_to_q(item, rng, factory))
    q.children = children
    return q


# --- oracle: run the real compiler, collect per-leaf column-form flags --------

def _is_node(obj):
    return hasattr(obj, 'children') and hasattr(obj, 'connector')

def _leaf_flags(node, out):
    for child in node.children:
        if _is_node(child):
            _leaf_flags(child, out)
        else:
            expr = getattr(child, 'lhs', None)
            if isinstance(expr, SimpleCol):
                out.append(True)
            elif isinstance(expr, Col):
                out.append(False)
            else:
                raise AssertionError(
                    "unexpected leaf column shape: %r" % (expr,))


def real_flags(q_object, plain):
    where, _ = Query(ConfModel)._add_q(
        q_object, set(), allow_joins=False, split_subq=True, simple_col=plain)
    out = []
    _leaf_flags(where, out)
    return out


# --- differential driver -------------------------------------------------------

def check(shape, plain, rng):
    head = shape_to_qnode(shape)
    shadow = compile_children(head, plain)
    q_object = shape_to_q(shape, rng, LeafFactory())
    real = real_flags(q_object, plain)
    if shadow != real:
        print("DISAGREEMENT on tree shape %r, plain=%r:\n"
              "  shadow (impl region)      = %r\n"
              "  real (patched compiler)   = %r" % (shape, plain, shadow, real))
        return False
    # internal cross-check: the executable impl equals the pure fold
    if ToSeq(shadow) != leaf_modes(head, plain):
        print("INTERNAL: impl region and pure fold disagree on shape %r, "
              "plain=%r" % (shape, plain))
        return False
    return True


def boundary_shapes():
    deep = 'L'
    shapes = []
    for d in range(9):                      # a leaf at depth 0..8
        shapes.append([deep])
        deep = [deep]
    shapes += [
        [],                                  # empty tree
        ['L'],                               # single leaf
        ['L', 'L', 'L'],                     # flat list
        ['L'] * 12,                          # wide flat list
        [[]],                                # single empty group
        [[], 'L', []],                       # empty groups around a leaf
        [['L', 'L'], 'L'],                   # nested group then leaf (issue shape)
        ['L', ['L', 'L']],                   # leaf then nested group
        [['L'], ['L'], ['L']],               # sibling groups
        [['L', ['L', 'L']], 'L'],            # two-level nesting
        ['L', ['L', ['L', ['L']]], 'L'],     # staircase nesting
        [[['L']], [[]], 'L'],                # deep group + empty group + leaf
        [['L'] * 6, ['L'] * 6],              # two wide groups
    ]
    return shapes


def random_shape(rng, depth):
    n = rng.randint(0, 4)
    items = []
    for _ in range(n):
        if depth > 0 and rng.random() < 0.4:
            items.append(random_shape(rng, depth - 1))
        else:
            items.append('L')
    return items


def main():
    rng = random.Random(SEED)
    checked = 0

    boundary = boundary_shapes()
    for shape in boundary:
        for plain in (True, False):
            if not check(shape, plain, rng):
                return 1
            checked += 1

    for _ in range(N_FUZZ):
        shape = random_shape(rng, rng.randint(1, 5))
        plain = rng.random() < 0.5
        if not check(shape, plain, rng):
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched condition-tree compiler on "
          "%d (tree, mode) inputs (%d boundary x 2 modes + %d fuzz, seed %d); "
          "0 disagreements." % (checked, len(boundary), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
