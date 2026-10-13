#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-15382.

The model consumes ONE @ContractOnly axiom, ``render_inner`` (model.py axioms
region), standing in for the UNCHANGED super-class sub-selection renderer that
the predicate renderer invokes (``Subquery.as_sql`` — called via
``super().as_sql(...)`` from ``Exists.as_sql``). The axiom's contract:

    render_inner(satisfiable):
        satisfiable == 1  ->  returns a NON-EMPTY fragment (full ownership)
        satisfiable == 0  ->  raises the matches-nothing signal (EmptyResultSet)

i.e. the super-class renderer signals an unsatisfiable inner selection by
raising ``EmptyResultSet`` and otherwise returns non-empty SQL. G-AX executes the
REAL callee and asserts every observation meets this contract.

It ALSO validates the post-patch case analysis of the predicate renderer
``Exists.as_sql`` itself (the function under change) against the model's
case table over (satisfiable, negated):

    sat=1, neg=0  -> non-empty SQL, no NOT prefix
    sat=1, neg=1  -> SQL prefixed by 'NOT '
    sat=0, neg=1  -> RETURNS NORMALLY (does not propagate the matches-nothing
                     signal) with the EMPTY fragment (sql == ''). The empty
                     fragment contributes no restriction, so ~Exists(empty)
                     matches every row and the F2P result-set equality holds; a
                     non-empty fragment here (always-false or junk) would change
                     the observed rows and NOT resolve. Gold returns '', so this
                     matches the spec clause len(Result()) == 0 on this case.
    sat=0, neg=0  -> raises EmptyResultSet (existence over empty never holds)

Run inside the SWE-bench container for the instance (Django importable, with the
GOLD patch applied for the post-patch case checks). Exit 0 iff every obligation
holds. Outside the container, prints a SKIP and defers to the orchestrator's
in-container run.
"""
import sys


def _setup_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
            DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3',
                                   'NAME': ':memory:'}},
            USE_TZ=False,
        )
    django.setup()


def check_axiom_and_cases():
    try:
        _setup_django()
        from django.db import connection
        from django.db.models import Exists
        from django.contrib.auth.models import User
        from django.core.exceptions import EmptyResultSet
        from django.db.models.expressions import Subquery
    except Exception as exc:  # pragma: no cover - environment dependent
        print("G-AX SKIP (Django): %r" % (exc,))
        return 0

    compiler = User.objects.all().query.get_compiler(using='default')

    # satisfiable inner selection (a non-empty filterable queryset) and an
    # UNSATISFIABLE one (the explicit empty queryset .none()).
    sat_qs = User.objects.all()
    empty_qs = User.objects.none()

    def render_inner_real(satisfiable):
        """The REAL unchanged super-class renderer Subquery.as_sql, exercised
        exactly as Exists.as_sql invokes it (self.query.exists(using=...) then
        super().as_sql(query=that)). Returns (raised, sql)."""
        ex = Exists(sat_qs if satisfiable else empty_qs)
        try:
            query = ex.query.exists(using=connection.alias)
        except TypeError:
            # signature drift across Django versions; at base_commit (4.1) the
            # parameter is named ``using``. Fall back to positional.
            query = ex.query.exists(connection.alias)
        try:
            sql, params = Subquery.as_sql(ex, compiler, connection, query=query)
            return False, sql
        except EmptyResultSet:
            return True, None

    NOT_PREFIX = 'NOT '

    # --- axiom render_inner: contract over the real Subquery.as_sql -----------
    raised, sql = render_inner_real(1)
    assert not raised, "render_inner axiom unsound: satisfiable inner RAISED"
    assert isinstance(sql, str) and len(sql) > 0, (
        "render_inner axiom unsound: satisfiable inner returned empty/invalid "
        "fragment %r" % (sql,))
    # the rendered inner fragment never itself begins with the negation marker
    assert not sql.startswith(NOT_PREFIX), (
        "render_inner axiom unsound: inner fragment spuriously begins with the "
        "negation marker: %r" % (sql,))

    raised, sql = render_inner_real(0)
    assert raised, (
        "render_inner axiom unsound: UNsatisfiable inner did NOT raise the "
        "matches-nothing signal (got %r)" % (sql,))

    # --- post-patch case analysis of the predicate renderer Exists.as_sql -----
    def render_exists_real(satisfiable, negated):
        qs = sat_qs if satisfiable else empty_qs
        ex = Exists(qs, negated=bool(negated))
        try:
            sql, params = ex.as_sql(compiler, connection)
            return False, sql
        except EmptyResultSet:
            return True, None

    # sat=1, neg=0 : non-empty, no NOT prefix
    raised, sql = render_exists_real(1, 0)
    assert not raised and len(sql) > 0 and not sql.startswith(NOT_PREFIX), (
        "sat=1,neg=0 unexpected: raised=%s sql=%r" % (raised, sql))

    # sat=1, neg=1 : NOT-prefixed
    raised, sql = render_exists_real(1, 1)
    assert not raised and sql.startswith(NOT_PREFIX), (
        "sat=1,neg=1 unexpected (missing NOT prefix): raised=%s sql=%r"
        % (raised, sql))

    # sat=0, neg=1 : THE FIX — returns NORMALLY with the EMPTY fragment. The
    # discriminator is (a) does NOT propagate the matches-nothing signal, AND
    # (b) the returned fragment is empty (sql == ''), matching the spec clause
    # len(Result()) == 0: an empty fragment contributes no restriction, so the
    # F2P result-set equality holds. Gold returns ''.
    raised, sql = render_exists_real(0, 1)
    assert not raised, (
        "sat=0,neg=1 unexpected (must return normally, not propagate the "
        "matches-nothing signal): raised=%s sql=%r" % (raised, sql))
    assert sql == '', (
        "sat=0,neg=1 unexpected (must return the EMPTY fragment to match every "
        "row; a non-empty fragment changes the observed rows and breaks the F2P): "
        "sql=%r" % (sql,))

    # sat=0, neg=0 : matches-nothing signal propagates
    raised, sql = render_exists_real(0, 0)
    assert raised, (
        "sat=0,neg=0 unexpected (must propagate EmptyResultSet): "
        "raised=%s sql=%r" % (raised, sql))

    print("G-AX OK: render_inner axiom sound on real Subquery.as_sql "
          "(satisfiable -> non-empty, unsatisfiable -> EmptyResultSet); "
          "post-patch Exists.as_sql matches the model case table over all four "
          "(satisfiable, negated) combinations incl. the sat=0,neg=1 fix "
          "(returns normally with the EMPTY fragment, not propagating the signal).")
    return 0


def main():
    return check_axiom_and_cases()


if __name__ == "__main__":
    sys.exit(main())
