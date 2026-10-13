#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-10880.

The modeled method `aggregateAsSql` invokes exactly one callee the gold patch
does NOT change: the generic SQL function-call renderer `Func.as_sql`, which
performs `template % data` with the aggregate template
`'%(function)s(%(distinct)s%(expressions)s)'`. That renderer is modeled DEEPLY
by `render_call` (Solution.lean's `renderCall`, pure region); there is no
consumed axiom about it. This is the single kind-A check:

  (A-reference) for ARBITRARY (function, qualifier, expressions) strings,
      render_call(function, qualifier, expressions)
          == the REAL `Func.as_sql` template substitution
      where render_call(f, q, e) = f + "(" + q + e + ")".

CRUCIAL decoupling: G-AX validates the UNCHANGED renderer over an *arbitrary*
qualifier value `q` — it does NOT assume `q == 'DISTINCT '`. The qualifier value
itself (`distinctQualifier`: `'DISTINCT '` when deduplicating, `''` otherwise) is
the CHANGED operation; it is modeled concretely and differential-tested by
G-CONF (conformance_check.py), not asserted here. This keeps G-AX honest: it
audits only the callee the patch leaves alone.

To exercise the REAL renderer we drive `Func.as_sql` directly with the aggregate
template and explicit `function`/`distinct` (qualifier) keyword arguments, over
a stub compiler/connection (mapping.md §2 — the no-filter render path). Imports
only `django` (the repo under test) + stdlib. Exit 0 iff sound.
"""
import random
import sys

# The aggregate call template (django/db/models/aggregates.py:17, unchanged by
# the patch). The renderer substitutes the three named placeholders.
TEMPLATE = "%(function)s(%(distinct)s%(expressions)s)"


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


class _StubConnection:
    ops = _StubOps()


class _StubCompiler:
    """Returns a fixed rendered SQL string for the single source expression, so
    the joined argument text equals the modeled `expressions`."""
    def __init__(self, arg_sql):
        self.arg_sql = arg_sql

    def compile(self, node):
        return (self.arg_sql, [])


def render_call(function, qualifier, expressions):
    """Reference implementation of Solution.lean's deep model `renderCall`:
    function + "(" + qualifier + expressions + ")". The qualifier is left as a
    free parameter — this is the UNCHANGED renderer, not the changed value."""
    return function + "(" + qualifier + expressions + ")"


def real_render(function, qualifier, expressions):
    """Drive the REAL `Func.as_sql` renderer directly with the aggregate
    template and an explicit qualifier, reading off the rendered SQL string."""
    from django.db.models.expressions import Func

    f = Func.__new__(Func)
    f.template = TEMPLATE
    f.extra = {}
    f.source_expressions = [object()]  # one arg; compiled by the stub
    sql, params = f.as_sql(
        _StubCompiler(expressions), _StubConnection(),
        function=function, distinct=qualifier,
    )
    return sql


def check(function, qualifier, expressions):
    observed = real_render(function, qualifier, expressions)
    expected = render_call(function, qualifier, expressions)
    assert observed == expected, (
        "render_call deep model unsound on (function=%r, qualifier=%r, "
        "expressions=%r): real Func.as_sql gave %r, deep model gives %r"
        % (function, qualifier, expressions, observed, expected))


def main():
    _setup_django()

    functions = ["COUNT", "SUM", "AVG", "MAX", "MIN", "F", "X"]
    # arbitrary qualifier strings — incl. both patch states and unrelated ones,
    # to prove the renderer is qualifier-agnostic (the A-reference claim).
    qualifiers = ["DISTINCT ", "DISTINCT", "", " ", "ALL ", "qq", "DISTINCT  "]
    expr_samples = [
        "CASE WHEN pages > 300 THEN rating END",  # the F2P shape
        "rating", "*", "", "a", "id, name",
        "CASE WHEN x THEN y END", "  spaced  ", "'quoted'",
    ]

    boundary = 0
    for f in functions:
        for q in qualifiers:
            for e in expr_samples:
                check(f, q, e)
                boundary += 1

    rng = random.Random(10880)
    alphabet = list("abcXYZ 0129_,*()<>='CASEWHENTHENDISTINCT") + ["é", "•"]
    for _ in range(20000):
        f = "".join(rng.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ_")
                    for _ in range(rng.randint(1, 8)))
        q = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 12)))
        e = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 30)))
        check(f, q, e)

    print("G-AX OK: render_call deep model (== real Func.as_sql template "
          "substitution) sound for arbitrary qualifiers on %d boundary + 20000 "
          "fuzz triples." % boundary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
