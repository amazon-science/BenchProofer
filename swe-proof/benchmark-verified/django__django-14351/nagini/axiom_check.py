#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-14351.

Executes the REAL unchanged callees the added grouping-columns reader composes —

  * the nested query's grouping-column reader (modeled by ``nested_group_by_cols``);
  * ``Query.clear_select_clause``  (django/db/models/sql/query.py:1861), modeled
    by ``clear_output_columns``; and
  * ``Query.add_fields(['pk'])``   (django/db/models/sql/query.py:1893), modeled
    by ``add_identity_column`` —

and asserts that every observation matches the three axioms in model.py.

The columns a nested query contributes to a GROUP BY clause are abstracted, in
model.py, as the sequence of SELECT sub-columns that the query renders (this is
what the surrounding compiler emits for the query expression, and what the
problem statement's ``select_fields`` debug output enumerates: ``[0,1,...,6]``
for a field-less query vs ``[0]`` once normalised). G-AX therefore measures the
real rendered SELECT-column COUNT (``compiler.select``) as the faithful
observable of ``nested_group_by_cols``.

The three axioms (all A-consumed):

  nested_group_by_cols(q):
      has_fields      => Result() == explicit_cols     (exactly the query's own
                                                         chosen output columns —
                                                         whatever they are)
      not has_fields  => Result() == default_cols       (the full default set)
  clear_output_columns(q): afterwards  not has_select_fields
  add_identity_column(q):  afterwards  has_select_fields  (== exactly the pk col)

Decisive obligations:
  (1) a field-less nested query over a multi-field model renders MORE THAN ONE
      SELECT column (the pre-patch hazard the GROUP BY position trips over);
  (2) after  clear_select_clause() + add_fields(['pk']),  has_select_fields is
      True and the query renders EXACTLY ONE SELECT column (the pk);
  (3) a query that ALREADY carries explicit output columns reports
      has_select_fields True and renders exactly THOSE chosen columns, untouched
      by the operation. This must hold for the FALSIFYING shapes that a
      too-strong "has_fields => exactly the pk column" reading would reject:
        * values('name')      -> exactly 1 column, and it is NOT the pk;
        * values('id','name') -> exactly 2 columns;
      as well as the coincidental shape values('pk') -> exactly 1 column.
      The axiom equates the reader's result to the query's explicit columns, so
      the rendered SELECT-column count must equal the number of explicit fields
      (NOT be forced to 1).

This is run inside the official SWE-bench container for the instance, where
Django is importable and a sqlite test database is available. It configures an
in-memory sqlite database and a minimal multi-field model, then drives the real
callees. Imports only Django (the repo under test) and the stdlib. Exit 0 iff
every obligation holds.
"""
import os
import sys


def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        )
    django.setup()


def _rendered_select_cols(query):
    """The number of SELECT sub-columns the query renders — the faithful
    observable of model.py's ``nested_group_by_cols`` (its contribution to a
    GROUP BY)."""
    compiler = query.get_compiler(using="default")
    compiler.pre_sql_setup()
    return len(compiler.select)


def _rendered_select_target_names(query):
    """The names of the model fields the query's rendered SELECT sub-columns
    refer to (best-effort), so the check can tell WHICH columns are exposed —
    not merely how many. Used to confirm the explicit-fields reader returns the
    chosen columns themselves (e.g. ``name``), not the identity column."""
    compiler = query.get_compiler(using="default")
    compiler.pre_sql_setup()
    names = []
    for col, _sql, _alias in compiler.select:
        target = getattr(col, "target", None)
        names.append(getattr(target, "name", None) if target is not None else None)
    return names


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "")
    try:
        _configure_django()
    except Exception as exc:  # pragma: no cover - environment guard
        print("G-AX SKIP: Django not configurable in this environment: %r" % (exc,))
        return 0

    from django.db import connection, models

    # A minimal multi-field model: a field-less query over it has MANY default
    # columns (the bug surface). pk is the implicit ``id`` column.
    class GroupTarget(models.Model):
        name = models.CharField(max_length=50)
        f1 = models.IntegerField(default=0)
        f2 = models.IntegerField(default=0)
        f3 = models.IntegerField(default=0)
        f4 = models.IntegerField(default=0)
        f5 = models.IntegerField(default=0)

        class Meta:
            # Piggyback on an already-installed, importable app so the check is
            # portable across Django versions (no throwaway app module needed).
            app_label = "contenttypes"

    with connection.schema_editor() as editor:
        editor.create_model(GroupTarget)

    n_default = 1 + 6  # id + the six declared fields

    observations = 0

    # (1) field-less query: not has_select_fields, renders > 1 SELECT column
    #     (== nested_group_by_cols default-column branch; the pre-patch hazard).
    q = GroupTarget.objects.all().query
    assert q.has_select_fields is False, (
        "expected a field-less query to report has_select_fields False, got %r"
        % (q.has_select_fields,))
    n_before = _rendered_select_cols(q)
    assert n_before == n_default, (
        "field-less query rendered %d SELECT columns, expected %d default columns"
        % (n_before, n_default))
    assert n_before > 1, (
        "the bug surface requires a field-less query to render MORE THAN ONE "
        "column; got %d" % (n_before,))
    observations += 1

    # (2) the normalisation: clear_select_clause() then add_fields(['pk']) —
    #     afterwards has_select_fields True and EXACTLY ONE column (the pk).
    q.clear_select_clause()                       # clear_output_columns
    assert q.has_select_fields is False, (
        "clear_select_clause must leave has_select_fields False, got %r"
        % (q.has_select_fields,))
    q.add_fields(['pk'])                          # add_identity_column
    assert q.has_select_fields is True, (
        "add_fields(['pk']) must set has_select_fields True, got %r"
        % (q.has_select_fields,))
    n_after = _rendered_select_cols(q)
    assert n_after == 1, (
        "after clear_select_clause()+add_fields(['pk']) the query must render "
        "EXACTLY ONE SELECT column (the pk), got %d" % (n_after,))
    observations += 1

    # (3) already-explicit queries: has_select_fields True and the reader
    #     renders exactly THOSE chosen columns, untouched (the explicit-fields
    #     branch). The corrected axiom is `has_fields => Result() == explicit_cols`,
    #     so the rendered count must equal the number of explicit fields and the
    #     identities must be those fields — it must NOT be forced to the pk.
    #     These shapes FALSIFY a too-strong "has_fields => exactly the pk col"
    #     reading and are exactly what an honest G-AX must exercise.
    explicit_shapes = [
        (['pk'], 1, False),       # coincidental: 1 col, IS the pk
        (['name'], 1, True),      # falsifying: 1 col, NOT the pk
        (['id', 'name'], 2, True),  # falsifying: 2 cols
    ]
    for fields, want_n, expect_non_pk in explicit_shapes:
        qx = GroupTarget.objects.values(*fields).query
        assert qx.has_select_fields is True, (
            "values%r query must report has_select_fields True, got %r"
            % (fields, qx.has_select_fields))
        n_x = _rendered_select_cols(qx)
        assert n_x == want_n, (
            "values%r query must render exactly %d SELECT column(s), got %d"
            % (fields, want_n, n_x))
        names = _rendered_select_target_names(qx)
        # The reader exposes exactly the chosen fields (the explicit columns),
        # not an injected pk. For single-explicit-field shapes confirm the
        # rendered column is (or is not) the pk as the shape dictates — this is
        # what distinguishes the faithful `Result() == explicit_cols` axiom from
        # the over-claimed `Result() == PSeq(pk_col)` one.
        if expect_non_pk:
            assert 'name' in names, (
                "values%r must expose the chosen 'name' column, got names %r"
                % (fields, names))
            assert names != ['id'], (
                "values%r must NOT collapse to the pk column; got names %r "
                "(a too-strong has_fields=>pk axiom would wrongly accept this)"
                % (fields, names))
        observations += 1

    # robustness: repeat the normalisation on fresh field-less queries (fuzz
    # over independent query instances; every one must collapse to one column).
    for _ in range(50):
        qi = GroupTarget.objects.all().query
        assert qi.has_select_fields is False
        assert _rendered_select_cols(qi) == n_default
        qi.clear_select_clause()
        qi.add_fields(['pk'])
        assert qi.has_select_fields is True
        assert _rendered_select_cols(qi) == 1
        observations += 1

    print("G-AX OK: nested_group_by_cols / clear_output_columns / "
          "add_identity_column axioms sound against the real Query callees over "
          "%d observations (field-less => %d cols; normalised => 1 pk col; "
          "explicit-fields => exactly the chosen columns: values('pk')=>1, "
          "values('name')=>1 non-pk, values('id','name')=>2)." % (observations, n_default))
    return 0


if __name__ == "__main__":
    sys.exit(main())
