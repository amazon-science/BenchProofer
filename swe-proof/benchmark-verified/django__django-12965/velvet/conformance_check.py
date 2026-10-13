#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-12965 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* repo state. The A-reference callee
              `activate` is NOT replaced by its model here; G-CONF leaves
              A-tagged callees as the REAL repo callee (`Query.get_initial_alias`)
              and isolates the R/I legs. The R/I content under test is the count
              `liveCount tableRefs.tail == 0` (Solution.lean `liveCount`/`.tail`/
              `==0`, all I ops) over the post-`get_initial_alias` refcount state.
              `get_initial_alias` always leaves the head refcount >= 1 and touches
              no other entry, so the real `sum(...) == 1` is pointwise equivalent
              to "no NON-head entry is live" — which is what the shadow computes.
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `SQLDeleteCompiler.single_alias` applied at base_commit (the real
              correctness oracle, G-RESOLVE).

Both run on independent clones of the same fuzzed query state, so any
disagreement is a mechanical R/I-fidelity counterexample (the I-leg `liveCount`
transliteration diverging from `sum(alias_refcount[t] > 0 ...)`).

Faithfulness of the fuzzer: on the only code paths exercised
(`get_initial_alias` non-empty branch, and `single_alias`), the real Django
methods read ONLY `alias_map` (its ordered keys; head = base table) and
`alias_refcount` — never the Join *values*. So driving arbitrary reference-count
vectors via synthetic `alias_map`/`alias_refcount` dicts is behaviourally exact;
the empty-`alias_map` full-delete state (which routes through the real
`join(BaseTable(...))` branch) is additionally covered with real models.

Runs in-container (the prebuilt SWE-Bench instance image), Django + stdlib only.
The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

SEED = 12965
N_FUZZ = 100_000


def setup_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
            DEFAULT_AUTO_FIELD="django.db.models.AutoField",
        )
    django.setup()

    from django.db import models

    class Author(models.Model):
        name = models.CharField(max_length=50)

        class Meta:
            app_label = "conf_app"

    class Book(models.Model):
        title = models.CharField(max_length=50)
        author = models.ForeignKey(Author, on_delete=models.CASCADE)

        class Meta:
            app_label = "conf_app"

    return Author, Book


def make_query_with_state(QueryCls, Author, refcounts):
    """A real Query whose refcount state == `refcounts` (in alias_map order).

    For the empty state we return a genuinely-empty Query(Author) so the real
    `get_initial_alias` runs its `join(BaseTable(...))` branch. For non-empty
    states we synthesize the two dicts the touched methods read; the Join values
    are never dereferenced on these paths (see module docstring)."""
    q = QueryCls(Author)
    if not refcounts:
        return q
    alias_map = {}
    alias_refcount = {}
    for i, c in enumerate(refcounts):
        t = "t%d" % i
        alias_map[t] = object()          # value never read on the tested paths
        alias_refcount[t] = c
    q.alias_map = alias_map
    q.alias_refcount = alias_refcount
    # invalidate any cached base_table so it recomputes over our alias_map
    q.__dict__.pop("base_table", None)
    return q


def shadow_single_alias(q):
    """R/I shadow: real A-reference callee `get_initial_alias`, then the I op
    `liveCount tableRefs.tail == 0` transliterated from Solution.lean."""
    q.get_initial_alias()                                   # A-reference: REAL callee
    refcount = [q.alias_refcount[t] for t in q.alias_map]   # R: the carrier
    others = refcount[1:]                                   # I: .tail
    num_live_others = sum(1 for n in others if n != 0)      # I: liveCount
    return num_live_others == 0                             # I: == 0


def oracle_single_alias(q, SQLDeleteCompiler, connection):
    """patch.diff behaviour: the patched single_alias property."""
    compiler = SQLDeleteCompiler(q, connection, "default")
    return bool(compiler.single_alias)


def fuzz_states(n, rng):
    # boundary cases first (plan §4.1 step 4)
    yield []                       # the F2P full-table-delete state (empty alias_map)
    yield [0]                      # one inactive table
    yield [1]                      # one active table -> single
    yield [2]                      # base referenced twice, still one table
    yield [1, 0]                   # one active + one inactive
    yield [0, 0]                   # all inactive
    yield [1, 1]                   # two active -> not single
    yield [1, 1, 1]
    yield [0, 1]
    yield [3, 0, 0]
    for _ in range(n):
        k = rng.randint(0, 6)
        yield [rng.randint(0, 3) for _ in range(k)]


def main():
    Author, Book = setup_django()
    from django.db.models.sql.query import Query
    from django.db.models.sql.compiler import SQLDeleteCompiler
    from django.db import connection

    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for state in fuzz_states(N_FUZZ, rng):
        count += 1
        q_shadow = make_query_with_state(Query, Author, state)
        q_oracle = make_query_with_state(Query, Author, state)
        shadow = shadow_single_alias(q_shadow)
        oracle = oracle_single_alias(q_oracle, SQLDeleteCompiler, connection)
        if shadow != oracle:
            disagreements.append((state, shadow, oracle))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for st, sh, orc in disagreements:
            print("  state=%r shadow=%r oracle=%r" % (st, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of directDeleteEligible agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
