#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13028 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python: `anyBad`/`nodeBad` over the flattened operand tree
              (`raised = OR over visited nodes of (isOperand AND not filterable)`),
              via the mapping.md bijection (tree ↔ List Node; attribute presence
              ↔ Bool field; raise ↔ raised). There are NO A-tagged callees in
              this bundle, so the shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `django.db.models.sql.query.Query.check_filterable` applied at
              base_commit (the real correctness oracle, G-RESOLVE). Its only
              observable is whether it raises NotSupportedError.

They must agree on every Requires-satisfying input. Exit 0 iff zero
disagreements; any disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib only. The
fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

SEED = 13028
N_FUZZ = 100_000

# --- Django bootstrap (minimal settings so query.py imports) -----------------
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        INSTALLED_APPS=[],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
    )
    django.setup()

from django.db.models.sql.query import Query
from django.db.utils import NotSupportedError

# Bind the REAL (patched) check_filterable to a shim self whose recursion goes
# back through the real function. check_filterable uses `self` only to recurse.
_real_check = Query.check_filterable


class _Shim:
    def check_filterable(self, expr):
        return _real_check(self, expr)


_SHIM = _Shim()


# --- node spec: a lightweight description of one fuzzed tree node -------------
class _Spec:
    __slots__ = ("has_filterable", "filterable_val", "has_resolve", "children")

    def __init__(self, has_filterable, filterable_val, has_resolve, children):
        self.has_filterable = has_filterable
        self.filterable_val = filterable_val
        self.has_resolve = has_resolve
        self.children = children


def _build_obj(spec):
    """Materialize a real Python object with exactly the attributes the spec
    dictates, so the real builtins `getattr`/`hasattr` see what the bijection
    (mapping.md §2) claims. `get_source_expressions` is present iff the node has
    children (mirrors the real recursion guard, query.py:1132)."""
    class _N:
        pass
    obj = _N()
    if spec.has_filterable:
        obj.filterable = spec.filterable_val
    if spec.has_resolve:
        # A non-callable sentinel is enough: the patch only does
        # hasattr(expression, 'resolve_expression').
        obj.resolve_expression = True
    child_objs = [_build_obj(c) for c in spec.children]
    if spec.children:
        obj.get_source_expressions = lambda co=child_objs: co
    return obj


def _shadow_raised(spec):
    """anyBad over the flattened tree: OR of nodeBad across root + descendants.
    nodeBad = isOperand AND NOT (filterable-with-default-True).
    Descendants are visited only through children (the unchanged recursion)."""
    filt = spec.filterable_val if spec.has_filterable else True   # getattr default True
    node_bad = spec.has_resolve and (not filt)                    # isOperand && !filterable
    if node_bad:
        return True
    return any(_shadow_raised(c) for c in spec.children)


def _oracle_raised(spec):
    obj = _build_obj(spec)
    try:
        _SHIM.check_filterable(obj)
        return False
    except NotSupportedError:
        return True


def _rand_spec(rng, depth):
    has_filterable = rng.random() < 0.6
    filterable_val = rng.random() < 0.5
    has_resolve = rng.random() < 0.5
    children = []
    if depth > 0:
        for _ in range(rng.randint(0, 3)):
            children.append(_rand_spec(rng, depth - 1))
    return _Spec(has_filterable, filterable_val, has_resolve, children)


def _boundary_specs():
    S = _Spec
    leaf = lambda hf, fv, hr: S(hf, fv, hr, [])
    return [
        # the F2P bug scenario: a plain value (no resolve_expression) carrying
        # filterable=False must NOT raise.
        leaf(True, False, False),
        # an operand declaring itself non-filterable MUST raise.
        leaf(True, False, True),
        # operand, filterable True -> no raise.
        leaf(True, True, True),
        # value with no filterable attr at all -> default True -> no raise.
        leaf(False, False, False),
        leaf(False, False, True),
        # nested: clean root, offending operand child.
        S(True, True, True, [leaf(True, False, True)]),
        # nested: clean root, non-operand non-filterable child (no raise).
        S(True, True, True, [leaf(True, False, False)]),
        # deep tree, offending grandchild.
        S(False, False, False, [S(True, True, True, [leaf(True, False, True)])]),
    ]


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for spec in _boundary_specs():
        count += 1
        if _shadow_raised(spec) != _oracle_raised(spec):
            disagreements.append((count, _shadow_raised(spec), _oracle_raised(spec)))
    for _ in range(N_FUZZ):
        spec = _rand_spec(rng, depth=4)
        count += 1
        sh = _shadow_raised(spec)
        orc = _oracle_raised(spec)
        if sh != orc:
            disagreements.append((count, sh, orc))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for idx, sh, orc in disagreements:
            print("  input#%d shadow=%r oracle=%r" % (idx, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of checkFilterable agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
