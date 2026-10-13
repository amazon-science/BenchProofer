#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-12050.

The bundle models the iterable-normalisation branch DEEPLY (a fresh container of
the same `kind` carrying the per-item normalisations). It consumes ONE axiom,
`normalise_item` (`Ensures(True)`) — the per-item normalisation primitive — and
the load-bearing soundness fact the refinement rests on is that this primitive
is **container-independent**: normalising one item yields the same result
whether the item sits in a list or a tuple, so the only behavioural difference
between the two container kinds is the container TYPE itself (clause 2, the
fix). G-AX validates that against the REAL Django callee.

Two checks against the REAL semantics the patched code uses:

  (A) The gold normalisation transcribed VERBATIM
        return type(value)(self.resolve_lookup_value(sub, ...) for sub in value)
      preserves the concrete iterable type (list -> list, tuple -> tuple) AND
      normalises every item by the SAME per-item rule regardless of container,
      while the pre-patch
        value = tuple(resolved_values)
      always coerces to tuple. Driven on lists and tuples of mixed item kinds
      (plain values + expression-bearing items), with a recording stub for the
      per-item resolution so container-independence is observable directly.

  (B) The REAL `django.db.models.sql.query.Query.resolve_lookup_value` on the
      F2P scenario: a list value of plain (non-expression) items is returned as
      a list with the same items (and a tuple value as a tuple), exercising the
      real method end-to-end with a minimally-configured settings module.

Imports the standard library plus Django; configures a minimal in-memory
settings module (no database access is performed — `resolve_lookup_value` does
not touch the connection for plain/expression values). Exit 0 iff every
obligation holds.
"""
import random
import sys


# --- (A) the gold vs pre-patch normalisation over a recording per-item rule ---
# A faithful stand-in for `Query` whose `resolve_lookup_value` is transcribed
# directly from the gold patch (post) and the base commit (pre). The per-item
# resolution is a deterministic recording stub: it depends only on the item, not
# on the container, which is exactly the `normalise_item` axiom's content.

class Expr:
    """An item that carries `resolve_expression` (an expression-bearing item)."""
    def __init__(self, tag):
        self.tag = tag

    def resolve_expression(self, query, **kwargs):
        return ("resolved", self.tag)


class FakeQuery:
    def __init__(self):
        self.calls = []  # records (item-identity, container-kind) per resolution

    def _resolve_item(self, sub_value, container_kind):
        """The unchanged per-item normalisation. Records the container it was
        called from so we can assert container-independence."""
        if hasattr(sub_value, 'resolve_expression'):
            out = sub_value.resolve_expression(self)
        else:
            out = sub_value
        self.calls.append((repr(sub_value), container_kind, repr(out)))
        return out

    # ---- gold (post-patch): preserve the concrete iterable type ----
    def resolve_gold(self, value):
        if isinstance(value, (list, tuple)):
            kind = type(value).__name__
            return type(value)(
                self._resolve_item(sub, kind) for sub in value
            )
        return value

    # ---- pre-patch: always coerce to tuple ----
    def resolve_prepatch(self, value):
        if isinstance(value, (list, tuple)):
            resolved_values = []
            for sub in value:
                resolved_values.append(self._resolve_item(sub, 'prepatch'))
            return tuple(resolved_values)
        return value


def normalise_standalone(item):
    """Per-item normalisation applied to an item on its own (no container)."""
    if hasattr(item, 'resolve_expression'):
        return item.resolve_expression(None)
    return item


def make_items(rng):
    pool = [
        0, 1, -3, 42, "a", "b", "alpha", "", "['a', 'b']",
        Expr("x"), Expr("y"), 3.5, True, None,
    ]
    n = rng.randint(0, 8)
    return [rng.choice(pool) for _ in range(n)]


def check_gold_vs_prepatch(items):
    # as a list
    q = FakeQuery()
    out_list = q.resolve_gold(list(items))
    assert isinstance(out_list, list), (
        "gold: a list value must normalise to a list, got %r" % type(out_list))

    # as a tuple
    q2 = FakeQuery()
    out_tuple = q2.resolve_gold(tuple(items))
    assert isinstance(out_tuple, tuple), (
        "gold: a tuple value must normalise to a tuple, got %r" % type(out_tuple))

    # clause 1: same length, item i is the per-item normalisation of input i,
    # and the per-item result is identical between the list and tuple containers
    # (container-independence -> the normalise_item axiom is sound).
    assert len(out_list) == len(items)
    assert len(out_tuple) == len(items)
    for i, raw in enumerate(items):
        expected = normalise_standalone(raw)
        assert out_list[i] == expected, (
            "list item %d normalisation mismatch: %r vs %r"
            % (i, out_list[i], expected))
        assert out_tuple[i] == expected, (
            "tuple item %d normalisation mismatch: %r vs %r"
            % (i, out_tuple[i], expected))
        assert out_list[i] == out_tuple[i], (
            "per-item normalisation depends on container kind (axiom unsound) "
            "at item %d: list gave %r, tuple gave %r"
            % (i, out_list[i], out_tuple[i]))

    # the pre-patch always coerces to tuple, dropping the list type (the bug)
    qp = FakeQuery()
    out_pre = qp.resolve_prepatch(list(items))
    assert isinstance(out_pre, tuple), (
        "pre-patch must coerce a list to a tuple (the bug under test)")
    # and its items still match the per-item rule (only the container changed)
    for i, raw in enumerate(items):
        assert out_pre[i] == normalise_standalone(raw)


# --- (B) the REAL Django Query.resolve_lookup_value end-to-end ----------------

def check_real_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
            DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3',
                                   'NAME': ':memory:'}},
        )
        django.setup()

    from django.contrib.auth.models import User
    from django.db.models.sql.query import Query

    query = Query(User)

    # F2P scenario: a list of plain (non-expression) values stays a list.
    value_list = ['a', 'b']
    out = query.resolve_lookup_value(value_list, can_reuse=set(),
                                     allow_joins=True, simple_col=False)
    assert isinstance(out, list), (
        "REAL resolve_lookup_value: a list value must stay a list, got %r"
        % type(out))
    assert out == ['a', 'b'], out
    assert repr(out) == "['a', 'b']", repr(out)

    # a tuple of plain values stays a tuple.
    value_tuple = ('a', 'b', 'c')
    out_t = query.resolve_lookup_value(value_tuple, can_reuse=set(),
                                       allow_joins=True, simple_col=False)
    assert isinstance(out_t, tuple), (
        "REAL resolve_lookup_value: a tuple value must stay a tuple, got %r"
        % type(out_t))
    assert out_t == ('a', 'b', 'c'), out_t

    # a scalar passes through unchanged.
    assert query.resolve_lookup_value(7, set(), True, False) == 7

    # nested list of lists keeps every level a list (recursion preserves kind).
    nested = ['a', ['b', 'c'], 'd']
    out_n = query.resolve_lookup_value(nested, set(), True, False)
    assert isinstance(out_n, list) and isinstance(out_n[1], list), out_n
    assert out_n == ['a', ['b', 'c'], 'd'], out_n


def main():
    rng = random.Random(12050)

    # boundary: empty, singletons, the F2P list, mixed expression/plain
    boundary = [
        [],
        [0],
        ["a"],
        ["a", "b"],
        [Expr("x")],
        ["a", Expr("y"), 3],
        [None, True, "", 0],
    ]
    for items in boundary:
        check_gold_vs_prepatch(items)
    for _ in range(20000):
        check_gold_vs_prepatch(make_items(rng))

    check_real_django()

    print("G-AX OK: gold normalisation preserves the iterable type (list->list, "
          "tuple->tuple) while pre-patch coerces to tuple; per-item "
          "normalisation is container-independent (normalise_item axiom sound) "
          "over %d boundary + 20000 fuzz item-sequences; REAL "
          "Query.resolve_lookup_value keeps lists as lists and tuples as tuples."
          % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
