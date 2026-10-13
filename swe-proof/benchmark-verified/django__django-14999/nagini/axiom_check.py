#!/usr/bin/env python3
"""G-AX soundness / deep-model-fidelity check for django__django-14999.

This bundle consumes NO @ContractOnly axiom: the behaviour under specification
-- which schema operations the rename REQUESTS of the schema layer, and in which
order -- is modelled DEEPLY in model.py (the table-identity branch plus the two
loops over the dependents). There is therefore no axiom to over-/under-
approximate.

What G-AX validates here is the fidelity of that deep model to the REAL,
post-patch `RenameModel.database_forwards` / `database_backwards`
(`django/db/migrations/operations/models.py:319` / `:371`), on the observable the
model actually claims -- the ORDERED SCHEDULE OF REQUESTS, ONE ENTRY PER
REQUEST, each naming what it operates on:

  (A-reference, clause 1) the schedule is EMPTY -- the method requests NO schema
      operation at all -- exactly when the stored table identifier is unchanged,
      for both forwards and backwards, and crucially even when dependents exist
      (a foreign key pointing at the model and an auto-created many-to-many link
      table). Zero SQL is checked too, since that is what the hidden F2P test
      asserts via assertNumQueries(0).

  (A-reference, clauses 2-5) when the identifier CHANGES, the FIRST request is
      the move of the renamed model's own table, and after it every dependent
      request is issued EXACTLY ONCE and nothing else is requested -- so the
      schedule is one move, plus one rewrite per column relation, plus BOTH
      requests per link relation. Checked forwards and backwards.

  (A-reference, clause 6) within one link relation the MOVE of its link table
      (`alter_db_table`, models.py:358-362) precedes the rewrite of the column
      INSIDE that same link table (`alter_field`, models.py:365-369). These are
      TWO requests aimed at two different things -- a table and a column in that
      table -- so they are two schedule entries and the schedule carries the
      order between them.

  (discrimination) the noop and proceeding cases are run against the SAME built
      scenario, the same models and the same dependents, with ONLY the equality
      of the two table identifiers flipped. So the empty schedule in the first
      case is attributable to the identifier comparison and to nothing else: the
      same dependents DO get their requests when the identifiers differ. A check
      that could not go red certifies nothing.

  (non-vacuity of the order check) the clause-(2)/(6) checkers are additionally
      run on two MUTANTS of the observed schedule -- one with the leading main
      move moved to the end, one with a link relation's two requests swapped --
      and this file fails unless both mutants are REJECTED. That is the control
      for the order clauses: it shows they can go red on exactly the rivals the
      spec exists to exclude, rather than passing because they inspect nothing.

Requests are recorded by wrapping the two schema-layer entry points the method
uses (`alter_db_table`, `alter_field`) on the live editor instance and counting
only TOP-LEVEL calls: the sqlite backend re-enters its own
`alter_field`/`alter_db_table` while rebuilding a table, and those nested calls
are the schema layer's business, not requests the rename made. Consecutive
top-level requests are NEVER merged: a link relation's `alter_db_table` and
`alter_field` are adjacent and address the same link table, and collapsing them
is precisely the granularity that made the order between them unobservable.

Imports only Django + stdlib (the very code the patch lives in). Exit 0 iff every
observation matches the deep model.
"""
import sys

OP_MAIN_MOVE = -1          # model.py `# pure-start`: the main-table move
UNKNOWN_REQUEST = -999     # a request naming no code of the scheme


def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': ':memory:',
                }
            },
            INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
            USE_TZ=False,
        )
    django.setup()


def _is_link_table(model):
    """True for an auto-created many-to-many link table model."""
    return bool(getattr(model._meta, 'auto_created', False))


def _label(op, model, field):
    """What ONE top-level request operates on. A link relation yields TWO
    distinct labels -- the move of its link table and the rewrite of the column
    inside that link table -- because those are two different things."""
    if _is_link_table(model):
        if op == 'alter_db_table':
            return ('m2m-move', model._meta.label_lower)
        return ('m2m-field', model._meta.label_lower)
    if op == 'alter_db_table':
        return ('main',)
    return ('fk', field.name, field.model._meta.label_lower)


class Recorder(object):
    """The ordered top-level requests. Nothing is merged: one entry per request,
    which is what makes the order INSIDE a link relation observable."""

    def __init__(self):
        self.depth = 0
        self.labels = []

    def enter(self, op, model, field):
        if self.depth == 0:
            self.labels.append(_label(op, model, field))
        self.depth += 1

    def leave(self):
        self.depth -= 1


def _instrument(editor, rec):
    orig_adt = editor.alter_db_table
    orig_af = editor.alter_field

    def alter_db_table(model, old_db_table, new_db_table, *a, **kw):
        rec.enter('alter_db_table', model, None)
        try:
            return orig_adt(model, old_db_table, new_db_table, *a, **kw)
        finally:
            rec.leave()

    def alter_field(model, old_field, new_field, *a, **kw):
        rec.enter('alter_field', model, old_field)
        try:
            return orig_af(model, old_field, new_field, *a, **kw)
        finally:
            rec.leave()

    editor.alter_db_table = alter_db_table
    editor.alter_field = alter_field


def _canonical_dependents(old_model, new_model):
    """The two dependent collections the real method walks, in visiting order:

      * COLUMN relations -- every `related_objects` entry (models.py:331-348),
        one rewrite each. Position i of the model's `column_relations` is entry i
        of the first list.
      * LINK relations -- every many-to-many whose auto-created,
        non-self-referential link table the method does not skip
        (models.py:350-369), TWO requests each. Position j of the model's
        `link_relations` is entry j of the second list.
    """
    columns = []
    for related_object in old_model._meta.related_objects:
        field = related_object.field
        columns.append(('fk', field.name, field.model._meta.label_lower))
    links = []
    for old_field, new_field in zip(old_model._meta.local_many_to_many,
                                    new_model._meta.local_many_to_many):
        if (new_field.model == new_field.related_model
                or not new_field.remote_field.through._meta.auto_created):
            continue
        links.append(new_field.remote_field.through._meta.label_lower)
    return columns, links


def _build_states(app_label, db_table_for_rider):
    """Rider (optionally with an explicit db_table), referenced by a Pony FK and
    owning a Stable many-to-many, then RenameModel Rider -> Runner. Returns
    (operation, project_state, new_state)."""
    from django.db import migrations, models
    from django.db.migrations.state import ProjectState

    options = {'db_table': db_table_for_rider} if db_table_for_rider else {}
    operations = [
        migrations.CreateModel('Rider', fields=[
            ('id', models.AutoField(primary_key=True)),
        ], options=options),
        migrations.CreateModel('Pony', fields=[
            ('id', models.AutoField(primary_key=True)),
            ('rider', models.ForeignKey('%s.Rider' % app_label, models.CASCADE)),
        ]),
        migrations.CreateModel('Stable', fields=[
            ('id', models.AutoField(primary_key=True)),
        ]),
        migrations.AddField(
            'Rider', 'stables',
            models.ManyToManyField('%s.Stable' % app_label)),
    ]
    project_state = ProjectState()
    for op in operations:
        new = project_state.clone()
        op.state_forwards(app_label, new)
        project_state = new

    new_state = project_state.clone()
    operation = migrations.RenameModel('Rider', 'Runner')
    operation.state_forwards(app_label, new_state)
    return operation, project_state, new_state


def _materialize_tables(app_label, state):
    """Create the real tables (and the auto-created link tables) so operations
    that introspect the DB (alter_field) have something to act on."""
    from django.db import connection
    with connection.schema_editor(atomic=False) as editor:
        for model_state in state.models.values():
            model = state.apps.get_model(app_label, model_state.name)
            editor.create_model(model)


def _observe(operation, app_label, from_state, to_state, backwards,
             new_table=None):
    """Run the REAL method with the schema layer instrumented and return
    (schedule, nc, nl, n_sql): the ordered request schedule in the model's
    carrier, the sizes of the two dependent collections, and the number of SQL
    statements collected. If `new_table` is given it is installed as the
    post-rename `db_table` (restored afterwards), which is how the identifier
    equality is flipped without changing anything else."""
    from django.db import connection
    old_name = operation.old_name if not backwards else operation.new_name
    new_name = operation.new_name if not backwards else operation.old_name
    old_model = from_state.apps.get_model(app_label, old_name)
    new_model = to_state.apps.get_model(app_label, new_name)
    columns, links = _canonical_dependents(old_model, new_model)
    saved = new_model._meta.db_table
    if new_table is not None:
        new_model._meta.db_table = new_table
    rec = Recorder()
    try:
        with connection.schema_editor(collect_sql=True) as editor:
            _instrument(editor, rec)
            if backwards:
                operation.database_backwards(app_label, editor, from_state,
                                             to_state)
            else:
                operation.database_forwards(app_label, editor, from_state,
                                            to_state)
            n_sql = (len(editor.collected_sql or [])
                     + len(editor.deferred_sql or []))
    finally:
        new_model._meta.db_table = saved
    nc = len(columns)
    schedule = []
    for lab in rec.labels:
        if lab == ('main',):
            schedule.append(OP_MAIN_MOVE)
        elif lab[0] == 'fk' and lab in columns:
            schedule.append(columns.index(lab))
        elif lab[0] == 'm2m-move' and lab[1] in links:
            schedule.append(nc + 2 * links.index(lab[1]))
        elif lab[0] == 'm2m-field' and lab[1] in links:
            schedule.append(nc + 2 * links.index(lab[1]) + 1)
        else:
            schedule.append(UNKNOWN_REQUEST)
    return schedule, nc, len(links), n_sql


def _check_proceeding(tag, schedule, nc, nl, failures):
    """clauses (2)-(6) of model.py, read off the real method's schedule."""
    if not schedule:
        failures.append('%s: requested NOTHING though the table identifier '
                        'changed (deep model requires the main move first)' % tag)
        return
    if schedule[0] != OP_MAIN_MOVE:
        failures.append('%s: the FIRST request is %r, not the move of the '
                        'renamed model\'s own table (deep model clause 2)'
                        % (tag, schedule[0]))
    rest = schedule[1:]
    for entry in rest:
        if not (0 <= entry < nc + 2 * nl):
            failures.append('%s: request %r after the first names no dependent '
                            'request of the scheme (deep model clause 3); '
                            'schedule=%r' % (tag, entry, schedule))
    if len(set(rest)) != len(rest):
        failures.append('%s: some request is issued more than once (deep model '
                        'clause 4); schedule=%r' % (tag, schedule))
    if len(schedule) != 1 + nc + 2 * nl:
        failures.append('%s: requested %d operations for %d column relation(s) '
                        'and %d link relation(s) (deep model clause 5 requires '
                        '%d); schedule=%r'
                        % (tag, len(schedule), nc, nl, 1 + nc + 2 * nl,
                           schedule))
    # clause (6): a link table's move precedes the rewrite of its own column
    for p, code in enumerate(schedule):
        if p < 1 or code < nc or (code - nc) % 2 != 0:
            continue
        for q, other in enumerate(schedule):
            if q >= 1 and other == code + 1 and not p < q:
                failures.append(
                    '%s: the rewrite of the column INSIDE link table %d '
                    '(request code %d, at index %d) is issued BEFORE that link '
                    'table has been moved (request code %d, at index %d) — deep '
                    'model clause 6; schedule=%r'
                    % (tag, (code - nc) // 2, code + 1, q, code, p, schedule))


def main():
    _configure_django()

    failures = []

    # One scenario, built once: Rider with an EXPLICIT db_table (so the rename
    # leaves the stored table name unchanged, as in the F2P test), a dependent
    # Pony.rider foreign key (a COLUMN relation), and an auto-created
    # Rider.stables link table (a LINK relation, worth TWO requests).
    app = 'test_rmwdbtn'
    op, proj, new = _build_states(app, 'rider')
    _materialize_tables(app, proj)

    # --- Case 1: identifier UNCHANGED => the schedule is EMPTY ----------------
    sched, nc, nl, n_sql = _observe(op, app, proj, new, backwards=False)
    if sched or n_sql:
        failures.append('NOOP forwards requested %r (%d SQL) though the stored '
                        'table identifier is unchanged; the deep model requires '
                        'an empty schedule even with %d column relation(s) and '
                        '%d link relation(s) present'
                        % (sched, n_sql, nc, nl))
    sched_b, nc_b, nl_b, n_sql_b = _observe(op, app, new, proj, backwards=True)
    if sched_b or n_sql_b:
        failures.append('NOOP backwards requested %r (%d SQL); the deep model '
                        'requires an empty schedule' % (sched_b, n_sql_b))
    if nc < 1 or nl < 1:
        failures.append('scenario is not discriminating: it realizes %d column '
                        'relation(s) and %d link relation(s); the noop case must '
                        'be checked with a foreign key AND an auto-created link '
                        'table present' % (nc, nl))

    # --- Case 2: same scenario, identifier CHANGED => move first, then every ---
    #     dependent request exactly once, each link table moved before the
    #     column inside it is rewritten. Only the equality of the two
    #     identifiers differs from Case 1, which is what makes Case 1's empty
    #     schedule attributable to the guard and to nothing else.
    sched2, nc2, nl2, _ = _observe(op, app, proj, new, backwards=False,
                                   new_table='runner_renamed')
    _check_proceeding('CHANGED-table forwards', sched2, nc2, nl2, failures)
    sched3, nc3, nl3, _ = _observe(op, app, new, proj, backwards=True,
                                   new_table='rider_renamed')
    _check_proceeding('CHANGED-table backwards', sched3, nc3, nl3, failures)

    # --- Non-vacuity of the ORDER clauses: the checker must REJECT the two -----
    #     order-inverted mutants of what was just observed. Without this, an
    #     order clause that inspected nothing would pass silently.
    controls = []
    if sched2 and sched2[0] == OP_MAIN_MOVE:
        controls.append(('main move last', sched2[1:] + [sched2[0]]))
    pair = [p for p, c in enumerate(sched2)
            if p >= 1 and c >= nc2 and (c - nc2) % 2 == 0
            and (c + 1) in sched2]
    if pair:
        p = pair[0]
        q = sched2.index(sched2[p] + 1)
        mutant = list(sched2)
        mutant[p], mutant[q] = mutant[q], mutant[p]
        controls.append(('link relation\'s two requests swapped', mutant))
    else:
        failures.append('non-vacuity control unavailable: the observed schedule '
                        '%r carries no link-table move whose own column rewrite '
                        'is also present, so clause 6 was never exercised'
                        % (sched2,))
    for what, mutant in controls:
        probe = []
        _check_proceeding('control', mutant, nc2, nl2, probe)
        if not probe:
            failures.append('NON-VACUITY: the deep-model checker ACCEPTED the '
                            'mutant with the %s (%r); the order clauses are not '
                            'discriminating' % (what, mutant))

    if failures:
        for f in failures:
            print('G-AX FAIL:', f)
        return 1

    print('G-AX OK: deep model fidelity confirmed against real '
          'RenameModel.database_forwards/backwards on the ORDERED REQUEST '
          'SCHEDULE, one entry per request -- unchanged db_table => empty '
          'schedule, 0 SQL (forwards & backwards, with %d column relation(s) '
          'and %d link relation(s) present: a foreign key and an auto-created '
          'link table); changed table => %r forwards and %r backwards, i.e. the '
          'move of the model\'s own table FIRST, then every dependent request '
          'exactly once (1 + %d + 2*%d requests), with each link table moved '
          'BEFORE the column inside it is rewritten. Same scenario both times '
          'with only the identifier equality flipped, so the empty schedule is '
          'attributable to the identifier comparison; and the order checkers '
          'were shown to REJECT both the main-move-last and the '
          'swapped-link-pair mutants of the observed schedule. No consumed '
          'axioms.'
          % (nc, nl, sched2, sched3, nc2, nl2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
