#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-13158.

This bundle consumes NO `@ContractOnly` axiom: the changed operations are pure
object/structure logic (emptying a compound query and copying it), modelled
DEEPLY over a minimal `Query` (boolean `where_empty` + `child_empty: List[bool]`
constituent flags). G-AX therefore validates the *behavioural facts the deep
model rests on* against the REAL runtime semantics the patched code uses:

  (1) The `where_empty` / `is_empty` observable the model abstracts. In Django a
      query's own emptiness is "its WHERE tree contains a `NothingNode`". G-AX
      drives the REAL `django.db.models.sql.where.WhereNode` /
      `django.utils.tree.Node.add` / `NothingNode` (the exact callees behind
      `set_empty`'s `self.where.add(NothingNode(), AND)` and `is_empty`'s
      `any(isinstance(c, NothingNode) ...)`): a fresh node reports NOT empty;
      after adding a `NothingNode` it reports empty. This is the model's
      `is_empty(q) == q.where_empty` and `set_empty`'s `where_empty := True`.

  (2) The constituent recursion + copy-independence the patch adds. G-AX
      reconstructs the patched `clone` / `set_empty` data flow EXACTLY as the
      gold patch writes it
        clone:     obj.combined_queries = tuple(c.clone() for c in self.combined_queries)
        set_empty: self.where.add(NothingNode(), AND);  for q in self.combined_queries: q.set_empty()
      over the real `WhereNode` emptiness observable, and asserts the model's
      `none` postcondition holds: after `none()` the returned copy is empty at
      every level (own WHERE + every constituent) while the SOURCE query and all
      its constituents are left exactly as they were. It also asserts the
      PRE-patch skeletons (no recursion / shared constituents) violate exactly
      the model clauses the two `model_prepatch*` files fail on.

Imports only the standard library plus `django.db.models.sql.where` and its
transitive imports (`django.utils.tree`, and the `asgiref` / `pytz` packages
that layer pulls in); no DB connection and no settings configuration. Exit 0 iff
every obligation holds.
"""
import copy
import random
import sys

from django.db.models.sql.where import WhereNode, NothingNode, AND


# --- (1) the real where/is_empty observable the model abstracts --------------

def real_where_is_empty(where):
    """Reconstruct the REAL `Query.is_empty`: a NothingNode among the children."""
    return any(isinstance(c, NothingNode) for c in where.children)


def check_where_observable():
    w = WhereNode()
    assert real_where_is_empty(w) is False, "fresh WHERE must not be empty"
    # the exact operation behind set_empty's first line:
    w.add(NothingNode(), AND)
    assert real_where_is_empty(w) is True, (
        "after where.add(NothingNode(), AND) the query must report empty "
        "(the model's where_empty := True / is_empty observable)")
    # idempotent / monotone: adding more never un-empties it
    w.add(NothingNode(), AND)
    assert real_where_is_empty(w) is True


# --- a faithful real-semantics Query mirroring the patched data flow ---------
# Each node owns its own WhereNode (real emptiness observable) and a tuple of
# constituent RealQuery objects (the `combined_queries`). clone / set_empty are
# transcribed VERBATIM from the gold patch.

class RealQuery:
    def __init__(self, combined=()):
        self.where = WhereNode()
        self.combined_queries = tuple(combined)

    def is_empty(self):                                  # gold (unchanged)
        return any(isinstance(c, NothingNode) for c in self.where.children)

    # ---- gold (post-patch) ----
    def clone(self):
        obj = RealQuery.__new__(RealQuery)
        # real Query.clone does `obj.where = self.where.clone()`; deepcopy
        # yields the same observable here (an independent WHERE tree whose
        # emptiness vector equals the source's), which is all is_empty reads.
        obj.where = copy.deepcopy(self.where)
        obj.combined_queries = tuple(q.clone() for q in self.combined_queries)
        return obj

    def set_empty(self):
        self.where.add(NothingNode(), AND)
        for query in self.combined_queries:
            query.set_empty()

    # ---- pre-patch skeletons (for the differential witnesses) ----
    def clone_prepatch(self):
        obj = RealQuery.__new__(RealQuery)
        obj.where = copy.deepcopy(self.where)
        obj.combined_queries = self.combined_queries     # SHARED (the bug)
        return obj

    def set_empty_prepatch(self):
        self.where.add(NothingNode(), AND)               # no recursion (the bug)


def none_real(q):
    """QuerySet.none(): clone then empty the clone (gold path)."""
    c = q.clone()
    c.set_empty()
    return c


def snapshot(q):
    """Observable emptiness vector: (own, [each constituent], deep all-empty)."""
    own = q.is_empty()
    kids = [k.is_empty() for k in q.combined_queries]
    return own, kids


def make_compound(n_children):
    return RealQuery(combined=[RealQuery() for _ in range(n_children)])


def check_none_scenario(n_children):
    q = make_compound(n_children)
    before = snapshot(q)
    assert before[0] is False and all(v is False for v in before[1]), (
        "a freshly built compound query must not be empty anywhere")

    c = none_real(q)

    # model `none` postcondition: returned copy empty at EVERY level
    own_c, kids_c = snapshot(c)
    assert own_c is True, "none(): returned copy's own WHERE must be empty"
    assert all(v is True for v in kids_c), (
        "none(): every constituent of the returned copy must be empty "
        "(the set_empty recursion fix)")
    assert len(kids_c) == n_children

    # model `none` postcondition: SOURCE unchanged at every level
    own_q, kids_q = snapshot(q)
    assert own_q is False, "none(): source query's own WHERE must be untouched"
    assert all(v is False for v in kids_q), (
        "none(): source's constituents must be untouched (the clone "
        "deep-copy fix); shared constituents would all read empty here")


def check_prepatch_witnesses():
    """The two pre-patch skeletons each violate exactly the model clause its
    `model_prepatch*` file fails on."""
    # prepatch.py: set_empty does NOT recurse -> constituents stay non-empty
    q = make_compound(2)
    c = q.clone()
    c.set_empty_prepatch()
    _, kids_c = snapshot(c)
    assert any(v is False for v in kids_c), (
        "non-recursive set_empty must leave constituents non-empty "
        "(model_prepatch.py's failing clause)")

    # prepatch_2.py: shallow clone SHARES constituents -> emptying the copy
    # corrupts the source
    q = make_compound(2)
    c = q.clone_prepatch()
    c.set_empty()
    _, kids_q = snapshot(q)
    assert any(v is True for v in kids_q), (
        "shared-constituent clone must corrupt the source when the copy is "
        "emptied (model_prepatch_2.py's failing clause)")


def main():
    check_where_observable()

    boundary = [0, 1, 2, 3, 5, 8]   # number of constituents (0 = not compound)
    for n in boundary:
        check_none_scenario(n)

    rng = random.Random(13158)
    for _ in range(5000):
        check_none_scenario(rng.randint(0, 12))

    check_prepatch_witnesses()

    print("G-AX OK: real WhereNode/NothingNode is_empty observable matches the "
          "model's where_empty; gold clone+set_empty recursion empties the copy "
          "at every level and leaves the source intact over %d boundary + 5000 "
          "fuzz compound shapes; both pre-patch skeletons violate exactly their "
          "modelled clauses." % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
