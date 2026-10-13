#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13028 (nagini).

SHADOW: the impl region of model.py `check_operands`, copied verbatim below
with the contract calls (Requires/Ensures/Invariant/Exsures) stripped. The
model IS Python: the carriers are plain List[int], no PSeq shim is needed, and
this bundle has no @Pure helpers and no @ContractOnly callees.

ORACLE: the REAL patched repo function the model models per mapping.md —
`django.db.models.sql.query.Query.check_filterable`. The gate applies
patch.diff to /testbed before this script runs; PYTHONPATH=/testbed makes the
patched module importable.

Type bridge (mapping.md section 2): the real guard's input is an operand
object plus the operands nested inside it (reached via its source-expression
walk); the model's input is the flattened pre-order walk as two index-aligned
List[int] carriers:

    is_expr[i]   <->  hasattr(operand_i, 'resolve_expression')
    permitted[i] <->  bool(getattr(operand_i, 'filterable', True))
                      (attribute absent => the getattr default True => 1)

Children are attached only under operands that expose the walk hook (the real
recursion only descends there), so the flattening is computed with the exact
same hasattr/getattr observations the real guard makes. The compared
observable is the guard's outcome: accept (normal return) vs reject (raise) —
the shadow's user-defined rejection class stands in for the repo's
NotSupportedError (mapping.md section 1); the rejection's message payload is
not part of the pinned behaviour.

Input domain: Requires demands index-aligned carriers with entries in {0, 1};
every flattening of an operand tree satisfies that by construction (asserted
per input). Trees fuzz over every per-operand shape: with/without the
query-expression marker, with/without the walk hook, and a permitted marker
that is absent / truthy / falsy (including non-bool truthy and falsy values,
which the effective-boolean bridge collapses).

>= 1e5 Requires-satisfying inputs: 258 exhaustive boundary trees (every
single-operand shape, every root x child and root x child x child combination
over the six effective shapes) + 100000 fuzz trees (depth <= 4, branching
<= 3, plus wide flat trees). Pinned fuzz seed: 13028.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outcomes and exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 13028
N_FUZZ = 100_000


# --- the impl region of model.py, verbatim, contract calls stripped -----------

class OperandNotAllowed(Exception):
    pass


def check_operands(is_expr, permitted):
    i = 0
    while i < len(is_expr):
        if is_expr[i] == 1 and permitted[i] == 0:
            raise OperandNotAllowed()
        i = i + 1


def shadow_rejects(is_expr, permitted):
    try:
        check_operands(is_expr, permitted)
        return False
    except OperandNotAllowed:
        return True


# --- operand-object realizations (the real guard's input space) ---------------
# A node is realized as an object whose attribute surface drives the exact
# hasattr/getattr observations the real guard makes:
#   expr:      exposes resolve_expression        (the query-expression marker)
#   walk:      exposes get_source_expressions    (the sub-operand walk hook)
#   permitted: the 'filterable' attribute value, or ABSENT

_ABSENT = object()


def make_node(expr, walk, permitted_value, children):
    ns = {}
    if expr:
        ns["resolve_expression"] = lambda self, *a, **k: self
    if walk:
        kids = list(children)
        ns["get_source_expressions"] = lambda self, _k=kids: list(_k)
    cls = type("OperandNode", (object,), ns)
    node = cls()
    if permitted_value is not _ABSENT:
        node.filterable = permitted_value
    return node


def flatten(node):
    """The bridge: the flattened (is_expr, permitted) carriers in the guard's
    pre-order walk order, computed with the guard's own observations."""
    is_expr = [1 if hasattr(node, "resolve_expression") else 0]
    permitted = [1 if getattr(node, "filterable", True) else 0]
    if hasattr(node, "get_source_expressions"):
        for child in node.get_source_expressions():
            ce, cp = flatten(child)
            is_expr += ce
            permitted += cp
    return is_expr, permitted


def describe(node):
    d = {
        "expr": hasattr(node, "resolve_expression"),
        "filterable": getattr(node, "filterable", "<absent>"),
    }
    if hasattr(node, "get_source_expressions"):
        d["children"] = [describe(c) for c in node.get_source_expressions()]
    return d


# --- the differential check ----------------------------------------------------

def check_node(real_rejects, node):
    is_expr, permitted = flatten(node)
    # the Requires of the shadow hold by construction of the bridge:
    assert len(is_expr) == len(permitted)
    assert all(v in (0, 1) for v in is_expr)
    assert all(v in (0, 1) for v in permitted)

    real = real_rejects(node)
    shad = shadow_rejects(is_expr, permitted)
    if real != shad:
        print("DISAGREEMENT\n  operand tree=%s\n  carriers: is_expr=%r permitted=%r"
              "\n  real guard rejects=%s\n  shadow rejects=%s"
              % (json.dumps(describe(node)), is_expr, permitted, real, shad))
        return False
    return True


# boundary shape space: every effective per-operand shape. permitted values
# exercise absent / bool / non-bool truthy / non-bool falsy markers.
_SHAPES = [
    # (expr, walk, permitted_value)
    (False, False, _ABSENT),   # plain data, no marker
    (False, False, True),      # plain data, permitted
    (False, False, False),     # plain data, NOT permitted (the F2P shape)
    (True, True, _ABSENT),     # expression, no marker (=> permitted)
    (True, True, True),        # expression, permitted
    (True, True, False),       # expression, NOT permitted (must reject)
]

# fuzz shape space: adds hook combinations and non-bool marker values.
_FUZZ_EXPR = [False, True]
_FUZZ_WALK = [False, True]
_FUZZ_PERMITTED = [_ABSENT, True, False, 1, 0, "x", "", None, [], [0]]


def boundary_trees():
    trees = []
    for s in _SHAPES:
        trees.append(make_node(s[0], s[1], s[2], []))
    for r in _SHAPES:
        for c in _SHAPES:
            child = make_node(c[0], c[1], c[2], [])
            trees.append(make_node(r[0], True, r[2], [child]))
            for c2 in _SHAPES:
                trees.append(make_node(
                    r[0], True, r[2],
                    [make_node(c[0], c[1], c[2], []),
                     make_node(c2[0], c2[1], c2[2], [])]))
    return trees


def rand_tree(rng, depth, wide=False):
    expr = rng.choice(_FUZZ_EXPR)
    walk = rng.choice(_FUZZ_WALK)
    permitted_value = rng.choice(_FUZZ_PERMITTED)
    children = []
    if depth > 0 and walk:
        branch = rng.randint(0, 6 if wide else 3)
        for _ in range(branch):
            children.append(rand_tree(rng, depth - 1))
    return make_node(expr, walk, permitted_value, children)


def main():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(INSTALLED_APPS=[], USE_I18N=False, DATABASES={})
    django.setup()
    from django.db.models.sql.query import Query          # REAL patched callee
    from django.db.utils import NotSupportedError

    q = Query.__new__(Query)  # the guard touches no per-query state

    def real_rejects(node):
        try:
            q.check_filterable(node)
            return False
        except NotSupportedError:
            return True

    checked = 0
    n_boundary = 0
    for node in boundary_trees():
        if not check_node(real_rejects, node):
            return 1
        checked += 1
        n_boundary += 1

    rng = random.Random(SEED)
    for i in range(N_FUZZ):
        node = rand_tree(rng, rng.randint(0, 4), wide=(i % 10 == 0))
        if not check_node(real_rejects, node):
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real guard on %d operand trees "
          "(%d boundary + %d fuzz, seed %d)."
          % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
