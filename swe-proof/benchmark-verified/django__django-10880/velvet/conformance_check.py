#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-10880 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the real repo type (`str`), via the mapping.md
              bijection (`List Char` ↔ `str`). This is `renderCall` with the
              changed `distinctQualifier` op spelled out: the post-patch
              qualifier `'DISTINCT '` (with separator) when deduplicating, `''`
              otherwise. No A-tagged callee appears in the computed `out` (the
              renderer is modeled deeply and is itself the R/I content here), so
              the shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the patched `Aggregate.as_sql` applied
              at base_commit (the real correctness oracle, G-RESOLVE), driven
              over the no-filter render path (mapping.md §2) with a stub
              compiler/connection so we read off the rendered SQL string.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample. Runs in-container (the patched
SWE-Bench instance image), `django` + stdlib only. Seed pinned (mapping.md §4).
"""
import random
import sys

SEED = 10880
N_FUZZ = 100_000


def _setup_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
            USE_TZ=False,
        )
    django.setup()


class _StubOps:
    def check_expression_support(self, expr):
        return None


class _StubFeatures:
    supports_aggregate_filter_clause = True


class _StubConnection:
    ops = _StubOps()
    features = _StubFeatures()


class _StubCompiler:
    def __init__(self, arg_sql):
        self.arg_sql = arg_sql

    def compile(self, node):
        return (self.arg_sql, [])


# --- the R/I shadow: distinctQualifier / renderCall, transliterated ----------

def shadow_distinct_qualifier(distinct):
    """distinctQualifier (distinct : Bool) : List Char — the changed op."""
    return "DISTINCT " if distinct else ""


def shadow_as_sql(function, distinct, expressions):
    """renderCall function distinct expressions, transliterated to str
    (mapping.md §3): function + "(" + qualifier + expressions + ")"."""
    return function + "(" + shadow_distinct_qualifier(distinct) + expressions + ")"


# --- the oracle: the patched real Aggregate.as_sql ---------------------------

def oracle_as_sql(function, distinct, expressions):
    """patch.diff's behaviour: the patched `Aggregate.as_sql` (no-filter path).
    The harness applies patch.diff before this runs, so `self.distinct` true
    yields the post-patch 'DISTINCT ' qualifier."""
    from django.db.models.aggregates import Aggregate

    class _Probe(Aggregate):
        name = "Probe"
        allow_distinct = True

    agg = _Probe.__new__(_Probe)
    agg.function = function
    agg.distinct = distinct
    agg.filter = None
    agg.extra = {}
    agg.source_expressions = [object()]  # one arg; compiled by the stub
    sql, params = agg.as_sql(_StubCompiler(expressions), _StubConnection())
    return sql


def fuzz_inputs(n, rng):
    functions = ["COUNT", "SUM", "AVG", "MAX", "MIN"]
    expr_samples = [
        "CASE WHEN pages > 300 THEN rating END",  # the F2P shape
        "rating", "*", "", "a", "id, name",
        "CASE WHEN x THEN y END",
    ]
    # boundary cases first (plan §4.1 step 4): both distinct states, F2P shape
    for f in functions:
        for d in (True, False):
            for e in expr_samples:
                yield (f, d, e)
    alphabet = list("abcXYZ 0129_,*()<>='CASEWHENTHENDISTINCT") + ["é", "•"]
    for _ in range(n):
        f = "".join(rng.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ_")
                    for _ in range(rng.randint(1, 8)))
        d = bool(rng.getrandbits(1))
        e = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 30)))
        yield (f, d, e)


def main():
    _setup_django()
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for (f, d, e) in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_as_sql(f, d, e)
        oracle = oracle_as_sql(f, d, e)
        if shadow != oracle:
            disagreements.append(((f, d, e), shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for inp, sh, orc in disagreements:
            print("  input=%r shadow=%r oracle=%r" % (inp, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of aggregateAsSql agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
