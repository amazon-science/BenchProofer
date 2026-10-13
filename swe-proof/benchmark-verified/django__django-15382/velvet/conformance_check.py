#!/usr/bin/env python3
r"""G-CONF differential conformance check for django__django-15382 (plan §4.1).

Runs IN-CONTAINER with the gold patch applied (the orchestrator passes
apply_gold=True), so the ORACLE is the patched repo's real behaviour.

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — `renderExists(inverted, inner)` (Solution.lean impl region)
              transliterated to Python over the real `(sql, params)` carrier, via
              the mapping.md §2 bijection:
                  inverted            <->  self.negated (bool)
                  Except.ok (sql,prm) <->  super().as_sql(...) returned (sql,prm)
                  Except.error ()     <->  super().as_sql(...) raised EmptyResultSet
                  "NOT " ++ sql       <->  'NOT {}'.format(sql)
                  Except.ok ([],[])   <->  return '', ()
              The free input `inner` is OBTAINED, not invented: we call the
              UNCHANGED `super().as_sql` (Subquery.as_sql, expressions.py:1177) on
              exactly the arguments the patched `Exists.as_sql` builds, and record
              whether it returned a fragment or raised EmptyResultSet. There are
              NO A-tagged ops (no axioms): the renderer outcome is an R-tagged
              free input and the negation / empty-fragment ops are I-tagged
              concrete transliterations. So the shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the REAL patched
              `django.db.models.expressions.Exists.as_sql` driven end-to-end with
              a real SQLite compiler over a real subquery. We observe its result
              as either the returned (sql, params) fragment or the EmptyResultSet
              it (re-)raises.

The two outcomes the renderer can produce are exercised for real: a non-empty
subquery (`.all()` / ordinary filters) -> fragment; a provably-empty subquery
(`.none()`, `pk__in=[]`) -> EmptyResultSet. The negation flag is fuzzed over both
values, giving the full 2x2 matrix the fix distinguishes (mapping.md §3).

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample. (At UNPATCHED base_commit the
`negated=True` + empty-subquery cell re-raises EmptyResultSet where the shadow
returns ('', []): G-CONF validates the PATCHED behaviour only, as intended.)

No database rows are touched — `as_sql` is pure SQL generation. stdlib + django
only. The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

from django.conf import settings                              # noqa: E402
if not settings.configured:
    settings.configure(
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        USE_TZ=True,
    )
import django                                                  # noqa: E402
django.setup()

from django.core.exceptions import EmptyResultSet              # noqa: E402
from django.db import connections                              # noqa: E402
from django.db.models import Exists                            # noqa: E402
from django.db.models.expressions import Subquery              # noqa: E402

SEED = 15382
N_FUZZ = 100_000

EMPTY = object()   # sentinel: super()/Exists signalled EmptyResultSet


def _model():
    """A minimal concrete model to build real subqueries against. Registered in
    an installed app; only its SQL generation is used (no DB rows)."""
    from django.db import models

    class Widget(models.Model):
        name = models.CharField(max_length=50)
        size = models.IntegerField()

        class Meta:
            app_label = "auth"

    return Widget


def _compiler():
    """A real SQLite SQLCompiler + connection (no rows fetched)."""
    Widget = _model()
    query = Widget.objects.all().query
    connection = connections["default"]
    compiler = query.get_compiler(using="default", connection=connection)
    return compiler, connection, Widget


# ---- the R/I shadow: renderExists transliterated to Python ------------------
def shadow_render(inverted, inner):
    """renderExists(inverted, inner) (Solution.lean). `inner` is EMPTY (the
    Except.error () signal) or a (sql, params) tuple (Except.ok)."""
    if inner is EMPTY:
        if inverted:
            return ("", [])           # Except.ok (empty, always-true fragment)
        return EMPTY                  # Except.error () propagated
    sql, params = inner
    if inverted:
        sql = "NOT " + sql            # "NOT " ++ f.sql ; params unchanged
    return (sql, list(params))


def obtain_inner(expr, compiler, connection):
    """Compute the free input `inner` exactly as the patched Exists.as_sql sees
    it: run the UNCHANGED super().as_sql (Subquery.as_sql) on the same args."""
    query = expr.query.exists(using=connection.alias)
    try:
        sql, params = Subquery.as_sql(expr, compiler, connection,
                                      template=None, query=query)
        return (sql, list(params))
    except EmptyResultSet:
        return EMPTY


# ---- the oracle: the REAL patched Exists.as_sql, end-to-end ------------------
def oracle_render(expr, compiler, connection):
    """patch.diff's behaviour: the gold-patched Exists.as_sql."""
    try:
        sql, params = expr.as_sql(compiler, connection)
        return (sql, list(params))
    except EmptyResultSet:
        return EMPTY


def subqueries(rng, Widget):
    """Yield (label, queryset) test points: provably-empty and non-empty subs.
    Boundary cases first (plan §4.1 step 4)."""
    yield ("none", Widget.objects.none())
    yield ("pk_in_empty", Widget.objects.filter(pk__in=[]))
    yield ("all", Widget.objects.all())
    yield ("filter_name", Widget.objects.filter(name="x"))
    yield ("filter_size", Widget.objects.filter(size__gt=3))
    yield ("exclude", Widget.objects.exclude(size=0))
    empty_builders = [
        lambda: Widget.objects.none(),
        lambda: Widget.objects.filter(pk__in=[]),
        lambda: Widget.objects.filter(size__in=[]),
    ]
    nonempty_builders = [
        lambda: Widget.objects.all(),
        lambda: Widget.objects.filter(name=rng.choice(["a", "bb", "ccc"])),
        lambda: Widget.objects.filter(size__gt=rng.randint(0, 9)),
        lambda: Widget.objects.exclude(size=rng.randint(0, 9)),
        lambda: Widget.objects.filter(name="q", size=rng.randint(0, 9)),
    ]
    for _ in range(N_FUZZ):
        if rng.random() < 0.5:
            yield ("empty-fuzz", rng.choice(empty_builders)())
        else:
            yield ("nonempty-fuzz", rng.choice(nonempty_builders)())


def main():
    rng = random.Random(SEED)
    compiler, connection, Widget = _compiler()

    disagreements = []
    count = 0
    for label, qs in subqueries(rng, Widget):
        for inverted in (False, True):
            count += 1
            # Two independent Exists instances: one for the oracle (real as_sql),
            # one to extract `inner` via the unchanged super (no shared mutation).
            expr_o = Exists(qs, negated=inverted)
            expr_s = Exists(qs, negated=inverted)
            inner = obtain_inner(expr_s, compiler, connection)
            shadow = shadow_render(inverted, inner)
            oracle = oracle_render(expr_o, compiler, connection)
            if shadow != oracle:
                disagreements.append((label, inverted, shadow, oracle))
                if len(disagreements) >= 5:
                    break
        if len(disagreements) >= 5:
            break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for lab, inv, sh, orc in disagreements:
            print("  sub=%s negated=%s shadow=%r oracle=%r" % (lab, inv, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of renderExistsTest agrees with the gold-patched "
          "Exists.as_sql end-to-end behaviour on %d inputs (negated x renderer "
          "outcome, seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
