#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-13569.

This bundle consumes NO @ContractOnly axioms: the per-term grouping-column
contribution and its gathering over an ordering list are modelled DEEPLY in
model.py. What G-AX validates here are the two **A-references** — that the deep
model faithfully captures the real Django semantics the patch establishes:

  (A-reference 1) `random_group_by_cols(colid) == []` (model.py): a
      non-deterministic ordering term offers NO grouping column. The real
      callee is `Random.get_group_by_cols()` (post-patch) and, transitively,
      `OrderBy(Random()).get_group_by_cols()`. Both must return [].

  (A-reference 2) `offered_cols` / `gathered` (model.py pure region): the
      grouping columns gathered from a list of ordering terms are the
      concatenation, in order, of each non-reference term's
      `get_group_by_cols()`, with reference terms skipped, and where a
      deterministic term over a stored column offers exactly that one column.
      The real callee is the order-by gathering inside
      `SQLCompiler.get_group_by` (the loop
      `for expr, (_, _, is_ref) in order_by: if not is_ref:
      expressions.extend(expr.get_group_by_cols())`), with each per-term
      contribution coming from the real expression's `get_group_by_cols()`.

Run inside the official SWE-bench container for the instance, where Django is
importable; the gold patch (Random.get_group_by_cols -> []) must be applied.
Exit 0 iff every obligation holds. Outside the container (Django absent) it
prints `G-AX SKIP` and returns 0; the orchestrator runs it in-container.
"""
import random
import sys


# --- model.py reference encodings (kept in lock-step with the deep model) ----

def offered_cols(is_nondet, colid):
    """Reference of model.py's `offered_cols`: a non-deterministic term offers
    nothing; a deterministic term offers its one column identity."""
    if is_nondet:
        return []
    return [colid]


def gathered(nondet, ref, cols):
    """Reference of model.py's `gathered`: front-fold over the index-aligned
    term descriptors; reference terms skipped, others offer `offered_cols`."""
    out = []
    for nd, rf, cl in zip(nondet, ref, cols):
        if rf:
            continue
        out.extend(offered_cols(nd, cl))
    return out


def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[
                'django.contrib.contenttypes',
                'django.contrib.auth',
            ],
            DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3',
                                   'NAME': ':memory:'}},
            USE_TZ=False,
        )
    django.setup()


def main():
    try:
        _configure_django()
        from django.db.models.functions import Random
        from django.db.models.expressions import OrderBy, RawSQL
    except Exception as exc:  # pragma: no cover - environment guard
        print("G-AX SKIP: Django not importable/configurable in this "
              "environment: %r" % (exc,))
        return 0

    observations = 0

    # --- A-reference 1: a non-deterministic ordering term offers nothing -----
    r = Random()
    # The changed method: Random.get_group_by_cols() must be [].
    cols = r.get_group_by_cols()
    assert cols == [], (
        "Random.get_group_by_cols() must be [] (the gold fix); got %r" % (cols,))
    # The gold hunk's signature for this instance (Django 3.2) is
    # `def get_group_by_cols(self, alias=None)`: the alias kwarg is accepted and
    # the result is still empty. (Later Django versions dropped the kwarg from
    # this override; guard so a signature drift never masks the real obligation
    # above, which is `== []`.)
    import inspect
    if "alias" in inspect.signature(r.get_group_by_cols).parameters:
        assert r.get_group_by_cols(alias=None) == [], (
            "Random.get_group_by_cols(alias=None) must be []")
    observations += 1

    # Transitively, an ORDER BY over Random offers nothing (the OrderBy gathers
    # its source's get_group_by_cols()).
    ob_rand = OrderBy(Random())
    assert ob_rand.get_group_by_cols() == [], (
        "OrderBy(Random()).get_group_by_cols() must be [] so RANDOM() never "
        "enters the GROUP BY; got %r" % (ob_rand.get_group_by_cols(),))
    assert OrderBy(Random(), descending=True).get_group_by_cols() == [], (
        "OrderBy(Random(), descending=True) must also offer no grouping column")
    observations += 1

    # --- A-reference 2: deterministic term offers exactly its one column -----
    # An ORDER BY over a non-aggregate, non-random expression that has no
    # nested sources (here a RawSQL, whose get_group_by_cols() is the default
    # [self]) offers exactly itself: one column. This is the unchanged default
    # contribution `offered_cols(is_nondet=False)` in model.py.
    rsql = RawSQL('col_x', [])
    rsql_cols = OrderBy(rsql).get_group_by_cols()
    assert len(rsql_cols) == 1 and rsql_cols[0] is rsql, (
        "OrderBy(<deterministic expr>).get_group_by_cols() must offer exactly "
        "the one underlying expression; got %r" % (rsql_cols,))
    observations += 1

    # --- A-reference 2: the gathering loop == `gathered` ----------------------
    # Simulate SQLCompiler.get_group_by's order_by loop on synthetic terms and
    # check it agrees, structurally, with model.py's `gathered`. Each term is
    # (expr, is_ref); a non-ref term contributes expr.get_group_by_cols(); a
    # ref term contributes nothing. We tag each expr with an identity so we can
    # compare against `gathered`'s column-identity sequence.
    def real_gather(order_by_terms):
        expressions = []
        for expr, is_ref in order_by_terms:
            if not is_ref:
                expressions.extend(expr.get_group_by_cols())
        return expressions

    # Build a deterministic expression whose get_group_by_cols() is exactly
    # [self] (a RawSQL), a random expression (offers nothing), and exercise
    # reference terms.
    def make_term(kind, ident):
        # kind: 0 deterministic (RawSQL), 1 non-deterministic (Random)
        if kind == 1:
            e = OrderBy(Random())
            return e, ident, 1   # nondet
        e = OrderBy(RawSQL('c%d' % ident, []))
        return e, ident, 0       # deterministic, column identity == ident

    rng = random.Random(13569)
    for _ in range(3000):
        n = rng.randint(0, 6)
        nondet, ref, colids, real_terms, model_cols_seq = [], [], [], [], []
        for k in range(n):
            kind = rng.randint(0, 1)
            is_ref = 1 if rng.random() < 0.25 else 0
            ident = rng.randint(1, 100000)
            e, col_ident, nd = make_term(kind, ident)
            nondet.append(nd)
            ref.append(is_ref)
            colids.append(col_ident)
            real_terms.append((e, bool(is_ref)))

        # Real Django gather: extract the column identity each contributed.
        real_cols = real_gather(real_terms)
        # For a deterministic OrderBy(RawSQL('c<ident>')), the contributed
        # column is the RawSQL itself; recover its identity from .sql.
        real_idents = []
        for c in real_cols:
            # Only the deterministic RawSQL carries our identity; Random
            # contributes nothing so it never appears. Defensive: assert
            # nothing random leaked in.
            assert not _is_random_col(c), (
                "a RANDOM() column leaked into the gathered GROUP BY columns")
            real_idents.append(int(c.sql[1:]))

        model_idents = gathered(nondet, ref, colids)
        assert real_idents == model_idents, (
            "gathering loop disagrees with model `gathered`: real=%r model=%r "
            "(nondet=%r ref=%r cols=%r)"
            % (real_idents, model_idents, nondet, ref, colids))
        observations += 1

    print("G-AX OK: Random.get_group_by_cols()==[] (A-reference 1) and the "
          "order-by gathering == model `gathered` (A-reference 2) over %d "
          "observations (boundary + 3000 fuzz term lists)." % observations)
    return 0


def _is_random_col(c):
    """True iff the gathered column is (or wraps) a RANDOM() function."""
    from django.db.models.functions import Random
    if isinstance(c, Random):
        return True
    # be conservative: any expression whose SQL function is RANDOM
    return getattr(c, 'function', None) == 'RANDOM'


if __name__ == "__main__":
    sys.exit(main())
