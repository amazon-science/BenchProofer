#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-14122 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed query shapes and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python: `orderFold` (per-term contribution) and `groupingSet`
              (the four contributions concatenated under the `metaOrdering`
              guard). The bundle has NO axioms (mapping.md §3), so the whole
              shadow is in scope for G-CONF.
  * ORACLE  — `patch.diff`'s behaviour: the REAL, gold-patched
              `SQLCompiler.get_group_by` (django/db/models/sql/compiler.py),
              run in-container over a duck-typed compiler. We do not build a
              full DB query; `get_group_by` only reads `self.query.group_by`,
              `self.having`, `self._meta_ordering`, and calls `self.compile` /
              `self.collapse_group_by` — so we feed it a duck-typed `self` whose
              `collapse_group_by` / `compile` are the REAL bound methods and
              whose expressions are duck-typed columns. The changed code path
              (the `if not self._meta_ordering:` guard) therefore decides the
              produced grouping-column set.

The test observes the SET of grouping columns (mapping.md §2: SQL GROUP BY is a
set; the downstream collapse/dedup/render are unchanged and observationally the
identity on which columns group; the F2P test asserts the aggregation counts,
which depend only on that set). The two sides must agree on the column set for
every shape. Exit 0 iff zero disagreements.

Runs in-container against the prebuilt SWE-Bench instance image (gold patch
applied by the harness before this runs). stdlib + the in-image Django only.
The fuzz seed is pinned (mapping.md §4).
"""
import random
import sys
import types

SEED = 14122
N_FUZZ = 100_000


# --- ORACLE setup: import the REAL patched SQLCompiler.get_group_by ----------

def _setup_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[],
            USE_I18N=False,
            USE_TZ=False,
            DATABASES={},
            DEFAULT_AUTO_FIELD="django.db.models.AutoField",
        )
        django.setup()
    from django.db.models.sql.compiler import SQLCompiler
    return SQLCompiler


class _FakeCol:
    """A duck-typed grouping column, identified by its rendered sql string.

    `get_group_by_cols` returns itself (it IS a leaf column); `as_sql` renders
    the column; `select_format` is the identity. Two columns are observationally
    equal iff their sql strings match (mapping.md §2: column id -> "c{n}")."""
    def __init__(self, cid):
        self.sql = "c%d" % cid

    def get_group_by_cols(self):
        return [self]

    def as_sql(self, compiler, connection):
        return self.sql, []

    def select_format(self, compiler, sql, params):
        return sql, params


class _FakeOrderExpr:
    """A duck-typed ORDER BY expression: contributes a fixed column list."""
    def __init__(self, cids):
        self._cols = [_FakeCol(c) for c in cids]

    def get_group_by_cols(self):
        return list(self._cols)


class _FakeHaving:
    def __init__(self, cids):
        self._cols = [_FakeCol(c) for c in cids]

    def get_group_by_cols(self):
        return list(self._cols)


class _FakeFeatures:
    # Both False => collapse_group_by returns the expressions unchanged (no
    # primary-key collapsing). The patch does not touch collapse_group_by; this
    # isolates the changed accumulation/guard, exactly the R/I legs under test.
    allows_group_by_pk = False
    allows_group_by_selected_pks = False


class _FakeConnection:
    vendor = "sqlite"
    features = _FakeFeatures()


class _FakeQuery:
    def __init__(self, group_by):
        self.group_by = group_by

    def resolve_ref(self, name):  # only reached for exprs lacking as_sql (none here)
        return _FakeCol(hash(name) & 0xffff)


def _make_compiler(SQLCompiler, base_cids, meta_ordering, having_cids):
    """A duck-typed `self` for SQLCompiler.get_group_by, with the REAL bound
    collapse_group_by / compile methods so the genuine patched code runs."""
    fake = types.SimpleNamespace()
    fake.query = _FakeQuery([_FakeCol(c) for c in base_cids])
    fake._meta_ordering = ["meta"] if meta_ordering else None
    fake.having = _FakeHaving(having_cids) if having_cids else None
    fake.connection = _FakeConnection()
    fake.collapse_group_by = types.MethodType(SQLCompiler.collapse_group_by, fake)
    fake.compile = types.MethodType(SQLCompiler.compile, fake)
    return fake


def oracle_group_set(SQLCompiler, base_cids, select_cids, order_terms,
                     having_cids, meta_ordering):
    """Run the REAL patched get_group_by; return the produced column SET."""
    fake = _make_compiler(SQLCompiler, base_cids, meta_ordering, having_cids)
    select = [(_FakeCol(c), ("", []), None) for c in select_cids]
    order_by = [
        (_FakeOrderExpr(cols), ("", [], is_ref))
        for (cols, is_ref) in order_terms
    ]
    result = SQLCompiler.get_group_by(fake, select, order_by)
    # result is a list of (sql, params); the grouping SET is the set of sql.
    return {sql for (sql, _params) in result}


# --- SHADOW: Solution.lean orderFold / groupingSet, transliterated -----------

def shadow_order_fold(order_terms):
    """orderFold: each non-reference term contributes its columns; reference
    terms contribute nothing."""
    out = []
    for (cols, is_ref) in order_terms:
        out.extend([] if is_ref else cols)
    return out


def shadow_group_set(base_cids, select_cids, order_terms, having_cids,
                     meta_ordering):
    """groupingSet: base ++ select ++ (order unless metaOrdering) ++ having,
    observed as the SET of column ids (mapping.md §2)."""
    order_contrib = [] if meta_ordering else shadow_order_fold(order_terms)
    cols = (list(base_cids) + list(select_cids) + order_contrib
            + list(having_cids))
    return {"c%d" % c for c in cols}


# --- fuzzing -----------------------------------------------------------------

def fuzz_shapes(n, rng):
    pool = list(range(12))

    def sample(k_max):
        k = rng.randint(0, k_max)
        return [rng.choice(pool) for _ in range(k)]

    # boundary cases first (the issue + the added F2P scenario)
    # F2P: values('author').annotate(Count('author')) => base=[author],
    #      Meta.ordering present (-pub_date, headline, author__name, second_author__name)
    yield ([0], [], [([1], False), ([2], False), ([3], False)], [], True)   # bug case
    yield ([0], [], [([1], False), ([2], False), ([3], False)], [], False)  # explicit ordering
    yield ([], [], [], [], True)                # nothing
    yield ([], [], [], [], False)
    yield ([0], [1], [], [], True)              # base + select, meta
    yield ([0], [1], [], [2], True)             # + having (having is unguarded)
    yield ([0], [1], [([2], True)], [], False)  # a reference order term (drops)
    yield ([0], [1], [([2], True)], [], True)
    yield ([0], [1], [([2], False), ([3], True), ([4], False)], [5], False)
    yield ([0], [1], [([2], False), ([3], True), ([4], False)], [5], True)
    yield ([0, 1], [1, 2], [([0], False)], [1], True)   # overlapping ids (set dedup)
    yield ([0, 1], [1, 2], [([0], False)], [1], False)

    for _ in range(n):
        base = sample(3)
        select = sample(3)
        n_terms = rng.randint(0, 4)
        order_terms = [(sample(2), rng.random() < 0.3) for _ in range(n_terms)]
        having = sample(2)
        meta = rng.random() < 0.5
        yield (base, select, order_terms, having, meta)


def main():
    rng = random.Random(SEED)
    try:
        SQLCompiler = _setup_django()
    except Exception as e:  # pragma: no cover - environment guard
        print("G-CONF ERROR: could not import patched SQLCompiler: %r" % e)
        return 2

    disagreements = []
    count = 0
    for (base, select, order_terms, having, meta) in fuzz_shapes(N_FUZZ, rng):
        count += 1
        shadow = shadow_group_set(base, select, order_terms, having, meta)
        oracle = oracle_group_set(SQLCompiler, base, select, order_terms,
                                  having, meta)
        if shadow != oracle:
            disagreements.append((base, select, order_terms, having, meta,
                                  shadow, oracle))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for b, s, o, h, m, sh, orc in disagreements:
            print("  base=%r select=%r order=%r having=%r meta=%r "
                  "shadow=%r oracle=%r" % (b, s, o, h, m, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of groupingColumns agrees with the real "
          "patched SQLCompiler.get_group_by grouping-column set on %d inputs "
          "(12 boundary + fuzz, seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
