#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-15930.

This bundle consumes NO @ContractOnly axioms: the clause-rendering behaviour
(splice a leading keyword, the predicate slot, a separating keyword, the
consequent; substitute a fixed non-empty always-true predicate when the supplied
predicate fragment is empty) is modelled DEEPLY in model.py.

What G-AX validates here is the single **A-reference**: the abstract constants
``true_predicate()`` and ``true_params()`` (model.py pure region) stand for the
real upstream product ``compiler.compile(Value(True))`` (the SQL fragment + bound
parameters of an always-true predicate). The proof relies on exactly one
property of that product, and it is asserted unconditionally against the REAL
Django callee:

  * NON-EMPTINESS: ``compiler.compile(Value(True))[0] != ""`` — the substituted
    predicate fragment is non-empty (so the rendered clause's predicate slot is
    never blank). This is the property the postcondition
    ``len(Result()[0]) > len(lead()) + len(sep()) + len(cons)`` rides on. It is a
    TREE-INVARIANT property: it holds on the pre-patch tree, on the gold tree,
    and in later refactors, so it is the load-bearing obligation of this check.

It also makes two TREE-ROBUST observations about clause rendering. The G-AX
orchestrator runs this script against the **pre-patch** (``apply_gold=False``)
``/testbed`` by default, so no assertion here may depend on the gold fix being
present. Accordingly:

  * SUBSTITUTION TRIGGER (fix-gated, never fails): the all-matching sentinel
    ``~Q(pk__in=[])`` compiles upstream to the EMPTY fragment at this
    base_commit. We render its ``When`` clause and INSPECT the predicate slot.
    If the slot is non-blank the gold substitution is applied (post-patch tree)
    and we additionally confirm there is no malformed ``WHEN  THEN``. If the slot
    is blank we are on the pre-patch tree (the bug the issue reports is present
    by construction); we REPORT that the fix is not applied and continue — we do
    NOT assert-fail, because asserting post-fix behaviour against the pre-patch
    tree would be a false negative on a sound bundle.

  * NON-EMPTY-PREDICATE BOUNDARY (tree-agnostic): a ``When`` whose condition
    compiles to a genuine NON-empty fragment (here ``Q(pk__gt=5)`` ->
    ``"... > %s"``) is rendered with that fragment verbatim, with a non-blank
    predicate slot and NO always-true substitution, on either tree. (The
    earlier match-nothing ``Q(pk__in=[])`` boundary was removed: an empty ``__in``
    rhs raises ``EmptyResultSet`` in ``In.process_rhs`` rather than producing a
    non-empty always-false fragment, so it crashed rather than exercising a
    verbatim non-empty slot.)

Run inside the official SWE-bench container for the instance, where Django is
importable and an in-memory sqlite backend is available. Exit 0 iff every
load-bearing obligation holds. Outside the container (Django absent) it prints
``G-AX SKIP`` and returns 0; the orchestrator runs it in-container.
"""
import sys


def _configure_django():
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
            ],
            DATABASES={
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": ":memory:",
                }
            },
        )
    import django
    django.setup()


def main():
    try:
        import django  # noqa: F401
    except Exception:
        print("G-AX SKIP: Django not importable (run in-container)")
        return 0

    _configure_django()

    from django.db import connection
    from django.db.models import Case, When, Value, Q
    from django.db.models.sql.compiler import SQLCompiler
    from django.db.models.sql.query import Query
    from django.contrib.auth.models import User

    # A bare compiler over a trivial query for the User model: enough to
    # compile()/resolve the expressions exactly as the ORM does.
    query = Query(User)
    compiler = SQLCompiler(query, connection, using="default")

    def render_when(condition):
        """Resolve + compile a single When(condition, then=Value('selected'))
        inside a Case, returning the rendered SQL string for that When clause."""
        case = Case(When(condition, then=Value("selected")),
                    default=Value("not selected"))
        resolved = case.resolve_expression(query, allow_joins=True,
                                            reuse=None, summarize=False)
        when_sql, when_params = compiler.compile(resolved.cases[0])
        return when_sql

    def predicate_slot(when_sql):
        assert isinstance(when_sql, str)
        assert when_sql.startswith("WHEN "), (
            "When clause does not start with the leading keyword: %r"
            % (when_sql,))
        assert " THEN " in when_sql, (
            "When clause missing the THEN separator: %r" % (when_sql,))
        return when_sql[len("WHEN "):when_sql.index(" THEN ")]

    # ---- LOAD-BEARING obligation: compile(Value(True)) is NON-EMPTY ---------
    # This is the only property of the substituted always-true predicate the
    # proof relies on (it is what keeps the rendered predicate slot non-blank).
    # Tree-invariant: holds at base_commit, on the gold tree, and in later
    # refactors, so it is asserted unconditionally.
    true_sql, true_params = compiler.compile(Value(True))
    assert isinstance(true_sql, str), (
        "compile(Value(True)) sql is not a str: %r" % (true_sql,))
    assert true_sql != "", (
        "A-reference unsound: compile(Value(True)) produced an EMPTY SQL "
        "fragment; the model's true_predicate() is modelled as non-empty.")
    # true_params() is modelled abstractly; we only require the always-true
    # predicate carries a finite (possibly empty) parameter sequence.
    assert isinstance(true_params, (list, tuple)), (
        "compile(Value(True)) params not a sequence: %r" % (true_params,))

    # ---- TREE-AGNOSTIC boundary: a genuine non-empty predicate is verbatim --
    # A condition that compiles to a real non-empty fragment ("... > %s") is
    # rendered with that fragment in the predicate slot, with no always-true
    # substitution, on EITHER tree. (We use pk__gt=5; note an empty __in rhs
    # would instead raise EmptyResultSet in In.process_rhs, so it is NOT a
    # usable "non-empty verbatim" boundary.)
    nonempty_sql = render_when(Q(pk__gt=5))
    nonempty_slot = predicate_slot(nonempty_sql)
    assert nonempty_slot.strip() != "", (
        "non-empty-predicate When rendered a blank predicate slot: %r"
        % (nonempty_sql,))
    assert "%s" in nonempty_slot, (
        "non-empty-predicate When slot lost its bound placeholder: %r"
        % (nonempty_sql,))

    # ---- SUBSTITUTION TRIGGER (fix-gated; never fails on the pre-patch tree) -
    # The all-matching sentinel ~Q(pk__in=[]). At this base_commit the
    # underlying WhereNode renders the EMPTY fragment "" for an all-matching
    # condition; the gold fix detects that empty fragment and substitutes
    # compile(Value(True)). We INSPECT the rendered slot rather than assert
    # post-fix behaviour, because the orchestrator runs this against the
    # pre-patch /testbed by default (apply_gold=False), where the fix is absent.
    #
    # If a future tree replaces the empty-string protocol with a FullResultSet
    # exception raised before When.as_sql, that all-matching compile raises; we
    # detect and report it rather than crash.
    full_result_set = None
    try:
        from django.core.exceptions import FullResultSet as full_result_set
    except Exception:
        full_result_set = None

    everything = ~Q(pk__in=[])
    resolved_cond = everything.resolve_expression(
        query, allow_joins=True, reuse=None, summarize=False)
    cond_uses_empty_string = True
    try:
        cond_sql, _ = compiler.compile(resolved_cond)
        if cond_sql != "":
            cond_uses_empty_string = False
    except Exception as exc:
        if full_result_set is not None and isinstance(exc, full_result_set):
            cond_uses_empty_string = False
        else:
            raise

    if cond_uses_empty_string:
        # base_commit empty-fragment protocol: the all-matching condition is the
        # malformed-clause trigger the issue reports. Inspect (do not assert)
        # the rendered slot to tell the pre-patch and gold trees apart.
        when_sql = render_when(~Q(pk__in=[]))
        slot = predicate_slot(when_sql)
        if slot.strip() != "" and "WHEN  THEN" not in when_sql:
            print("G-AX OK: compile(Value(True)) non-empty (A-reference sound); "
                  "Q(pk__gt=5) -> non-blank verbatim predicate slot; "
                  "all-matching ~Q(pk__in=[]) -> empty fragment -> the gold fix "
                  "substituted a non-blank predicate slot (rendered: %r) -- no "
                  "malformed 'WHEN  THEN' (gold tree)." % (when_sql,))
        else:
            print("G-AX OK: compile(Value(True)) non-empty (A-reference sound); "
                  "Q(pk__gt=5) -> non-blank verbatim predicate slot. The "
                  "all-matching ~Q(pk__in=[]) renders a BLANK predicate slot "
                  "(rendered: %r) -- the gold fix is NOT applied on this tree "
                  "(pre-patch /testbed, the orchestrator default); this is the "
                  "exact malformed clause the issue reports, not a check "
                  "failure. The load-bearing A-reference property holds on both "
                  "trees." % (when_sql,))
    else:
        # Newer tree: empty-string protocol replaced by FullResultSet; the
        # base_commit substitution path is absent. The A-reference property
        # (compile(Value(True)) non-empty) is the part that remains relevant.
        print("G-AX OK: compile(Value(True)) non-empty (A-reference sound); "
              "Q(pk__gt=5) -> non-blank verbatim predicate slot. All-matching "
              "condition uses the FullResultSet protocol (a tree newer than "
              "base_commit); the empty-fragment substitution path under test is "
              "exercised against the in-container base_commit tree, not this one.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
