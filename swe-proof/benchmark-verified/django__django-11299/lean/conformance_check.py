#!/usr/bin/env python3
"""G-CONF for django__django-11299.

The gold patch is already applied to /testbed when this runs. We compare the
R/I Python shadow of `implementation_resolveColumns` (the Lean impl,
transliterated op-for-op per refinement.md) against the REAL patched lowering
path `Query.build_where` -> `Query._add_q` (django/db/models/sql/query.py) over
>=1e5 fuzzed inputs. Zero disagreements => exit 0.

What the modeled behavior is:
  `build_where(q)` lowers a (possibly deeply nested) boolean filter expression
  `q` to a tree of column references, with a single GLOBAL boolean choice of
  column form. `build_where` fixes that choice to "bare column" (it calls
  `_add_q(..., simple_col=True)`). The contract is that the choice applies
  uniformly to EVERY leaf at EVERY nesting depth: every leaf column must be a
  bare `SimpleCol`, never a table-qualified `Col`.

Type bijection (mapping.md):
  QTree.leaf field          <-> a single field lookup, e.g. Q(num__gt=2)
  QTree.node [c0, c1, ...]   <-> a Q(...) grouping node with those children
  bare = True                <-> build_where's global simple_col=True
  ColTree.col field True     <-> a leaf lookup whose lhs is a SimpleCol
  ColTree.col field False    <-> a leaf lookup whose lhs is a (qualified) Col
  ColTree.node [...]         <-> a WhereNode grouping those lowered children
  result == expectedCol      <-> every leaf lowered with the same global form

We generate random nested Q trees over non-relational fields {num, name} of a
synthetic model, run the REAL `build_where`, walk the resulting WhereNode tree
collecting each leaf's column-form (SimpleCol -> True, Col -> False) in order,
and compare against the shadow, which (mirroring the Lean impl that threads the
flag through the recursion) predicts EVERY leaf is bare=True.

Exit 0 iff zero disagreements over >=1e5 fuzzed inputs. stdlib + django only.
"""
import os
import random
import sys

SEED = 11299
N = 100_000

# --- configure Django before importing the ORM internals --------------------
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=False, USE_TZ=False, USE_L10N=False, USE_I18N=False,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
        INSTALLED_APPS=["confapp"],
        DEFAULT_AUTO_FIELD="django.db.models.AutoField",
    )

# a synthetic app + model with two non-relational fields
import types
confapp = types.ModuleType("confapp")
confapp.__path__ = [os.path.dirname(os.path.abspath(__file__))]
confapp.__file__ = os.path.abspath(__file__)
sys.modules["confapp"] = confapp
django.setup()

from django.db import models
from django.db.models import Q
from django.db.models.expressions import Col, SimpleCol
from django.db.models.sql.query import Query
from django.db.models.sql.where import WhereNode


class M(models.Model):
    num = models.IntegerField()
    name = models.CharField(max_length=10)

    class Meta:
        app_label = "confapp"


# field -> a lookup that yields a non-relational leaf column reference.
LEAF_CHOICES = [
    ("num__gt", 2),
    ("num__lt", 5),
    ("num__gte", 0),
    ("num__lte", 9),
    ("name__isnull", False),
    ("name__exact", "x"),
]


# --- random nested Q-tree generator -----------------------------------------
def gen_tree(rng, depth):
    """Return (q_object, is_leaf_flag). At depth 0 we force a node so that
    build_where always receives a Q with children."""
    # leaf with prob rising as depth grows
    if depth > 0 and (depth >= 4 or rng.random() < 0.4):
        key, val = rng.choice(LEAF_CHOICES)
        return Q(**{key: val})
    n = rng.randint(1, 3)
    children = [gen_tree(rng, depth + 1) for _ in range(n)]
    connector = rng.choice(["AND", "OR"])
    q = Q(*children, _connector=connector)
    if rng.random() < 0.3:
        q.negated = True
    return q


# --- walk the REAL lowered WhereNode collecting leaf column forms -----------
def collect_real(node, out):
    """In-order list of bare-flags (True=SimpleCol) for every leaf column."""
    if isinstance(node, WhereNode):
        for child in node.children:
            collect_real(child, out)
        return
    # a leaf lookup: inspect its lhs column reference
    lhs = getattr(node, "lhs", None)
    if isinstance(lhs, SimpleCol):
        out.append(True)
    elif isinstance(lhs, Col):
        out.append(False)
    else:
        # any other expression carries no column-form decision; skip it
        return


# --- shadow: R/I transliteration of implementation_resolveColumns -----------
def collect_shadow(q, bare, out):
    """Mirror of the Lean impl: thread `bare` through every recursion, so every
    leaf gets the same global form."""
    for child in q.children:
        if isinstance(child, Q):
            collect_shadow(child, bare, out)
        else:
            # a (key, value) leaf -> one bare column
            out.append(bare)


def main():
    rng = random.Random(SEED)
    mismatches = 0
    examples = []
    for i in range(N):
        q = gen_tree(rng, 0)
        # REAL patched lowering: build_where fixes the global form to bare
        try:
            where = Query(M).build_where(q)
        except Exception as e:  # pragma: no cover - generator should stay valid
            examples.append(("build_where raised", repr(e)))
            mismatches += 1
            continue
        real = []
        collect_real(where, real)
        shadow = []
        collect_shadow(q, True, shadow)
        if real != shadow:
            mismatches += 1
            if len(examples) < 5:
                examples.append((str(q), real, shadow))
    if mismatches:
        print("G-CONF FAIL: %d/%d disagreements" % (mismatches, N))
        for ex in examples:
            print("  ", ex)
        sys.exit(1)
    print("G-CONF OK: 0/%d disagreements (seed=%d)" % (N, SEED))
    sys.exit(0)


if __name__ == "__main__":
    main()
