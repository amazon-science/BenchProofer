#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-14999 (nagini).

SHADOW: the `# impl-start` / `# impl-end` region of model.py's
`rename_schema_schedule`, copied VERBATIM below
(`shadow_rename_schema_schedule`) with exactly two mechanical deletions, both
forced by the fact that this file is plain Python rather than Nagini: the
`Invariant(...)` calls (with their `# invariants-start` / `# invariants-end`
markers) and the `# type:` annotation comment. Nothing else is dropped -- there
is no `Requires`/`Ensures`/`Assert`/`Fold`/`Unfold`/`Acc` call inside the impl
region (they all sit in the pre/post-condition regions above `# impl-start`), so
the control flow, the emission order and the loops are byte-for-byte the model's.
The `# pure-start` constant it reads (`OP_MAIN_MOVE`) is copied too. No `@Pure`
helper and no `@ContractOnly` callee is involved: the axioms region of model.py
is empty (mapping.md section 3, "No consumed @ContractOnly axiom" -- the
table-identity branch is modeled DEEPLY), so there is nothing here to axiomatize
and nothing to bridge to a real primitive. No PSeq appears in the impl region
(the carriers are plain `int` and `List[int]`), so no sequence shim is needed.

ORACLE: the REAL, patched `RenameModel.database_forwards` and
`RenameModel.database_backwards`
(`django/db/migrations/operations/models.py:319` / `:371` at base_commit
a754b82dac511475b6276039471ccd17cc64aeb8; mapping.md section 1), CALLED, not
transliterated. The velvet sibling ships a conf_skip stub and the lean sibling
transliterates the post-patch control flow, both on the grounds that the
proceeding branch's `alter_field` rewrites need a live `schema_editor` bound to
materialized tables. That premise is true but it is not an obstacle in this
container: `connection.schema_editor(collect_sql=True)` over an in-memory sqlite
backend whose tables have been created with `editor.create_model` runs the whole
real method -- main move, every `related_objects` `alter_field`, and, per m2m,
the link table's own `alter_db_table` and the `alter_field` on the column inside
it. The gate applies patch.diff to /testbed before this script runs and
PYTHONPATH=/testbed makes the patched module importable; the script applies no
patch itself, and asserts up front (via `inspect.getsource`) that the guard the
patch introduces is actually present, so a silently unpatched oracle errors
instead of passing.

WHAT IS OBSERVED: the model's observable is the ORDERED SCHEDULE OF SCHEMA
OPERATIONS THE METHOD REQUESTS, ONE ENTRY PER REQUEST, each entry naming what it
operates on. So this check does not count SQL statements; it records the requests
the real method makes of the schema layer, in order, by wrapping the two entry
points the method uses (`alter_db_table`, `alter_field`) on the live editor
instance. Only TOP-LEVEL requests count: the sqlite backend re-enters its own
`alter_field`/`alter_db_table` while rebuilding a table, and those nested calls
are the schema layer's business, not requests the rename made (a depth counter
separates them). Each top-level request is labelled with what it addresses:

  * an `alter_db_table` on a model that is not an auto-created link table
    -> the move of the renamed model's own table                  -> OP_MAIN_MOVE
  * an `alter_field` on such a model -> the rewrite of the COLUMN RELATION
    `(field name, owning model)` that the request carries
  * an `alter_db_table` on an auto-created link table -> the MOVE of that link
    table (models.py:358-362)
  * an `alter_field` on an auto-created link table -> the rewrite of the COLUMN
    INSIDE that link table (models.py:365-369)

NOTHING IS MERGED. A link relation's two requests are two entries, because they
operate on two different things -- a table, and a column in that table -- and the
order between them is load-bearing: the `alter_field` is addressed to the link
table under its NEW name, so it has to follow the `alter_db_table` that puts the
table there. An earlier revision of this file collapsed consecutive requests
carrying the same link-table label into ONE entry; that collapse is exactly what
made the order between them unobservable, and it is the defect this revision
closes (see properties.py `weak-link-pair-swapped` and the
`link-pair-swapped` discrimination probe below).

Each label is then mapped to the model's code scheme, with `nc` for
`len(column_relations)`: OP_MAIN_MOVE; `i` for the column relation at position
`i`; `nc + 2*j` for the move of link relation `j`'s link table; `nc + 2*j + 1`
for the rewrite of the column inside that same link table. A label that names no
dependent of the two collections maps to a value no schedule entry can carry, so
it can only ever produce a disagreement.

TYPE BRIDGE (mapping.md section 2, inverted):
  * `before_table` / `after_table` (`int` identity) -> a concrete `db_table`
    `str`, via the INJECTIVE pool `TABLE_NAMES[i]`. Injectivity is the whole
    content of row 1 ("two ints are equal iff the two names are equal"): it makes
    `before_table == after_table` in the model equivalent to
    `old_model._meta.db_table == new_model._meta.db_table` in the real guard. The
    names are installed by assigning `_meta.db_table` on the two state-rendered
    model classes around each call and restoring them afterwards, so one built
    scenario realizes every id pair.
  * `column_relations` (`List[int]`, one POSITION per column relation) -> `n_fk`
    other models each carrying a `ForeignKey` to the renamed model (these become
    `old_model._meta.related_objects`, models.py:331).
  * `link_relations` (`List[int]`, one POSITION per link relation) -> `n_m2m`
    `ManyToManyField`s declared ON the renamed model (these become the
    auto-created link tables in `zip(...local_many_to_many)`, models.py:350).
    Position `j` of the model's list is the `j`-th such m2m in the order the real
    method visits them, and it owns the TWO codes `nc + 2*j` and `nc + 2*j + 1`.
  * the RESULT is compared as
      alpha(schedule) = 'empty'                                   if len == 0
                      = ('nonempty', schedule[0], sorted(schedule[1:]),
                         per-link-relation order flags)            otherwise
    applied to the shadow's returned list on one side and to the real method's
    recorded request schedule on the other. That is the strongest observable
    consistent with what model.py claims: it pins emptiness, it pins WHICH
    request comes first (the move of the model's own table, not a dependent
    request), it pins the exact MULTISET of dependent requests (so a request
    issued twice, or skipped, or naming nothing, all disagree), and -- the flags
    -- for each link relation it pins whether its link table's MOVE came before
    the rewrite of the column inside it. `sorted` quotients out exactly the
    freedom the spec leaves: the order of the dependents among THEMSELVES. An
    earlier revision compared only (first entry, multiset) over a carrier that
    gave a link relation ONE entry; that abstraction could not see a rename that
    rewrites a link table's column before moving the link table, which is a wrong
    rename, so it was lifted to the per-request schedule with the order flags.
  * `database_backwards` -> the same `rename_schema_schedule` with the two
    identifiers swapped (row 4). Both directions are driven for every input.

INPUT DOMAIN: the only value-free preconditions are
`Requires(Acc(list_pred(column_relations), 1/2))` and the same for
`link_relations` -- ownership of the lists, no value constraint -- so EVERY
(before_table, after_table, column_relations, link_relations) tuple satisfies the
Requires and no input has to be filtered. The realizable space after the bridge
is finite: 7 table ids x 7 table ids x 12 dependent shapes (n_fk in 0..3, n_m2m
in 0..2) x 2 directions = 1176 points. That space is enumerated EXHAUSTIVELY --
every id pair against every shape in both directions, so both branches of the
impl are taken on every shape and the equal-table branch is taken with 0, 1, ...,
3 column relations and 0, 1, 2 link relations present -- and then fuzzed over the
SAME space with a pinned seed to fill the >= 1e5 budget. Exhausting a finite
domain is a stronger check than 1e5 samples of it, not a weaker one. Boundary
cases run first and include the exact F2P shape (`Rider` with
`options={'db_table': 'rider'}`, a `Pony.rider` FK, renamed to `Runner`, table
identifier unchanged, forwards AND backwards -- the `assertNumQueries(0)`
scenario), the empty dependent lists, the empty table name, the singleton column
relation, the single link relation and the two-link-relation shape.

NAMED EXCLUSIONS FROM THE GENERATOR SPACE (disclosed, not accidental). Two
families of concrete configuration are deliberately NOT realized by the bridge,
because on them the real method does not produce a schedule at all. They are
recorded here so that their absence is a stated scoping decision rather than an
artifact of the name pool, and mapping.md section 3 discloses both:

  (a) the operation not PERMITTED to act on the renamed model's storage --
      `allow_migrate_model` False. Beyond the router case (no DATABASE_ROUTERS are
      configured here), `Options.can_migrate`
      (django/db/models/options.py:343-357) also rejects a proxy, swapped-out or
      unmanaged model and one whose `required_db_vendor` / `required_db_features`
      the connection does not satisfy. On any of those the real method requests
      NOTHING even when the two identifiers differ. The generator builds only
      ordinary managed models with no vendor/feature requirement, so this family
      is unreachable here by construction.

  (b) a link relation whose inside column is NOT addressable under the renamed
      model's `_meta.model_name`, on either side of the rename. When the m2m's
      other endpoint shares the owning model's `model_name`,
      `create_many_to_many_intermediary_model`
      (django/db/models/fields/related.py:1112-1116) computes
      `to = make_model_tuple(to_model)[1]` / `from_ = klass._meta.model_name` and,
      for `to == from_`, names the link table's two FKs `from_<n>` / `to_<n>`
      instead of `<n>`. The argument evaluation of models.py:365-369 --
      `old_m2m_model._meta.get_field(old_model._meta.model_name)` (:367) and
      `new_m2m_model._meta.get_field(new_model._meta.model_name)` (:368) -- then
      raises FieldDoesNotExist AFTER :358-362 has already issued that link
      table's move, so the real method issues a strict PREFIX of the modeled
      schedule and propagates the exception instead of returning. The exclusion is
      TWO-SIDED (target `model_name` distinct from BOTH the old and the new name)
      because those are two separate lookups, and `database_backwards` swaps the
      two names (models.py:371-378) while every input here is driven in both
      directions, so a one-sided carve-out would not be direction-stable.
      Truncation is not bounded: measured on the post-patch tree, with two link
      relations and the colliding one SECOND the real method records 4 requests
      then raises against the model's 5, colliding FIRST records 2 against 5, and
      with a column relation alongside (nc=1, nl=1) it records 3 against 4.
      This family is unreachable for THIS generator because every m2m target it
      builds (`Stable{i}`) lives in the SAME `app_label` as the renamed model, and
      one app cannot hold two models with the same `model_name`; a collision needs
      the target in a DIFFERENT app under the same `model_name`. `assert_named_
      exclusions()` below asserts exactly that property of the generated space,
      so the exclusion is measured rather than assumed, and the inert branch is
      confirmed unaffected (with equal identifiers the colliding shape still
      requests nothing, matching clause (1)).

Neither exclusion is a `Requires` of `rename_schema_schedule` -- the preconditions
remain ownership plus termination, with no value constraint -- and neither touches
the alpha or the generator space below. They restrict which CONCRETE
configurations realize an abstract point, i.e. the domain of the bridge.

DISCRIMINATION SELF-TEST: a green G-CONF that cannot go red certifies nothing, so
before the real run the same harness is pointed at five probe schedules on the
F2P and proceeding shapes:
  1. the impl region of model_prepatch.py (copied verbatim the same way), which
     omits the noop guard, on the unchanged-table shape with dependents present
     -- it must be FLAGGED against the real method's empty schedule;
  2. a probe that requests the main move LAST instead of first, on a proceeding
     shape -- it must be FLAGGED, which is what proves the harness observes the
     ORDER and not just the count;
  3. a probe that rewrites every column relation twice, on a proceeding shape --
     it must be FLAGGED, which is what proves the harness observes per-request
     MULTIPLICITY;
  4. a probe that, for every link relation, asks to rewrite the column inside its
     link table BEFORE moving that link table -- it must be FLAGGED, which is
     what proves the harness observes the order INSIDE one link relation (the
     property the old collapsing recorder destroyed);
  5. a probe that moves every link table but never rewrites the column inside it
     -- it must be FLAGGED, which is what proves a link relation's two requests
     are two observations rather than one.
If any probe is not flagged the harness is blind and this script exits 1 without
reporting a pass.

Exit 0 iff zero disagreements over the whole run. stdlib + Django only (the very
package the patch edits); no f-strings.
"""
import inspect
import json
import random
import sys

SEED = 14999            # pinned; recorded in mapping.md section G-CONF
N_FUZZ = 100_000        # fuzz draws over the same finite space, after the sweep
MIN_CHECKS = 100_000    # contract floor

# The injective int -> db_table bridge (mapping.md section 2 row 1). Distinct
# strings, so name equality holds exactly when the modeled ids are equal. Index 6
# is the empty name (a boundary the guard must treat like any other identifier).
TABLE_NAMES = ['rider', 'runner', 'pony', 'auth_user', 't', 'rider_2', '']

# n_fk in 0..3 x n_m2m in 0..2: realizes 0..3 column relations against 0..2 link
# relations under every split (only WHICH dependent a request operates on
# matters, and that is carried by the code, mapping.md section 2 rows 2-3).
SHAPES = [(n_fk, n_m2m) for n_fk in range(4) for n_m2m in range(3)]

# A request label naming no dependent of the two collections. No schedule entry
# can carry it, so it can only ever produce a disagreement.
UNKNOWN_REQUEST = -999


# ---------------------------------------------------------------------------
# SHADOW: model.py `# pure-start` .. `# pure-end`, verbatim.
# ---------------------------------------------------------------------------
OP_MAIN_MOVE = -1  # the request to move the renamed model's OWN table
# Every other schedule entry is a request belonging to ONE dependent, named by
# the code scheme in the module docstring: a position of ``column_relations``,
# or one of the two consecutive codes of a position of ``link_relations`` (the
# even offset from len(column_relations) being the move of the link table, its
# successor the rewrite of the column inside that link table). Codes are never
# negative, so no dependent request can pass for the move of the model's own
# table and no move can pass for a dependent request.


# ---------------------------------------------------------------------------
# SHADOW: model.py `# impl-start` .. `# impl-end` of rename_schema_schedule,
# verbatim minus the Invariant() calls and the `# type:` comment.
# ---------------------------------------------------------------------------
def shadow_rename_schema_schedule(before_table, after_table, column_relations,
                                  link_relations):
    result = []
    # An unchanged table identifier means there is nothing to do at all.
    if before_table == after_table:
        return result
    # The rename proceeds: ask for the move of the model's own table first.
    result = [OP_MAIN_MOVE]
    nc = len(column_relations)
    nl = len(link_relations)
    # Then one rewrite for each column relation reaching this model.
    i = 0
    while i < nc:
        result.append(i)
        i = i + 1
    # Then the requests the link relations need, each link relation served in
    # turn: its two codes are nc + 2*j (move that link table) and nc + 2*j + 1
    # (rewrite the column inside that same link table), so walking the codes
    # upward from nc issues, for one link relation after another, that link
    # table's move and then immediately that link table's own column rewrite.
    m = 0
    while m < 2 * nl:
        result.append(nc + m)
        m = m + 1
    return result


# ---------------------------------------------------------------------------
# The same region of model_prepatch.py, verbatim minus its Invariant() calls
# and `# invariants-start`/`-end` markers. Used ONLY by the discrimination
# self-test, to prove this harness can go red.
# ---------------------------------------------------------------------------
def prepatch_rename_schema_schedule(before_table, after_table,
                                    column_relations, link_relations):
    result = []
    if before_table != after_table:
        result = [OP_MAIN_MOVE]
    nc = len(column_relations)
    nl = len(link_relations)
    i = 0
    while i < nc:
        result.append(i)
        i = i + 1
    m = 0
    while m < 2 * nl:
        result.append(nc + m)
        m = m + 1
    return result


# --- four more probes for the discrimination self-test (NOT model regions) ---
def probe_main_move_last(before_table, after_table, column_relations,
                         link_relations):
    """Same requests, main move deferred to the end (properties.py
    `weak-main-move-last`). Must be flagged, or the harness is count-only."""
    if before_table == after_table:
        return []
    nc = len(column_relations)
    return (list(range(nc)) + [nc + m for m in range(2 * len(link_relations))]
            + [OP_MAIN_MOVE])


def probe_double_rewrite(before_table, after_table, column_relations,
                         link_relations):
    """Every column relation rewritten twice (properties.py
    `weak-double-rewrite`). Must be flagged, or the harness cannot see
    multiplicity."""
    if before_table == after_table:
        return []
    out = [OP_MAIN_MOVE]
    for i in range(len(column_relations)):
        out.append(i)
        out.append(i)
    nc = len(column_relations)
    for m in range(2 * len(link_relations)):
        out.append(nc + m)
    return out


def probe_link_pair_swapped(before_table, after_table, column_relations,
                            link_relations):
    """Within EVERY link relation, the rewrite of the column inside its link
    table is asked for BEFORE that link table is moved (properties.py
    `weak-link-pair-swapped`). Same first entry, same multiset -- so this probe
    is flagged ONLY IF the harness observes the order inside a link relation,
    which the earlier collapsing recorder did not."""
    if before_table == after_table:
        return []
    nc = len(column_relations)
    out = [OP_MAIN_MOVE] + list(range(nc))
    for j in range(len(link_relations)):
        out.append(nc + 2 * j + 1)
        out.append(nc + 2 * j)
    return out


def probe_link_drop_inner_rewrite(before_table, after_table, column_relations,
                                  link_relations):
    """Every link table is moved but the column inside it is never rewritten
    (properties.py `weak-link-drop-inner-rewrite`). Must be flagged, or a link
    relation's two requests are being read as one observation."""
    if before_table == after_table:
        return []
    nc = len(column_relations)
    out = [OP_MAIN_MOVE] + list(range(nc))
    for j in range(len(link_relations)):
        out.append(nc + 2 * j)
    return out


def alpha(schedule, nc, nl):
    """The observable of mapping.md section 2 row 3: the ORDERED per-request
    schedule, quotiented by exactly the one freedom the model leaves (the order
    of the dependents among THEMSELVES).

    Pins: emptiness; which request is FIRST; the multiset of dependent requests;
    and, per link relation, whether the move of its link table preceded the
    rewrite of the column inside that same link table. Applied to both sides."""
    if not schedule:
        return 'empty'
    rest = schedule[1:]
    flags = []
    for j in range(nl):
        move, field = nc + 2 * j, nc + 2 * j + 1
        if move in schedule and field in schedule:
            flags.append('move-first'
                         if schedule.index(move) < schedule.index(field)
                         else 'rewrite-first')
        elif move in schedule:
            flags.append('rewrite-absent')
        elif field in schedule:
            flags.append('move-absent')
        else:
            flags.append('both-absent')
    return ('nonempty', schedule[0], tuple(sorted(rest)), tuple(flags))


# ---------------------------------------------------------------------------
# ORACLE: the real patched RenameModel.database_forwards / database_backwards.
# ---------------------------------------------------------------------------
def configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3',
                                   'NAME': ':memory:'}},
            INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
            USE_TZ=False,
        )
    django.setup()


def assert_oracle_is_patched():
    """Refuse to report a pass against an unpatched oracle."""
    from django.db.migrations.operations.models import RenameModel
    src = inspect.getsource(RenameModel.database_forwards)
    if 'if old_db_table == new_db_table:' not in src:
        raise AssertionError(
            'oracle is NOT the patched function: the table-identity guard is '
            'absent from RenameModel.database_forwards')


def assert_named_exclusions(scenarios):
    """Assert the two NAMED EXCLUSIONS of the module docstring as properties of
    the space this harness actually generates, so that their absence is measured
    rather than an accident of the name pool.

    (a) every renamed model the bridge builds is migratable -- managed, not a
        proxy, not swapped out, no vendor/feature requirement -- so the
        `allow_migrate_model` family (models/options.py:343-357) is not realized.
    (b) every m2m target the bridge builds lives in the SAME app_label as the
        renamed model, so no m2m target can share the renamed model's
        `model_name`: `create_many_to_many_intermediary_model`'s `to == from_`
        branch (fields/related.py:1112-1116) never fires and every generated link
        table carries the column that :367/:368 look up. A collision requires the
        target in a DIFFERENT app under the same `model_name`, which one app
        cannot contain.

    Raises AssertionError -- i.e. fails the run -- if either property stops
    holding of the generated space, so a later change to the generator cannot
    silently start (or stop) realizing an excluded fiber."""
    for shape, sc in sorted(scenarios.items()):
        for state, name in ((sc.old_state, 'Rider'), (sc.new_state, 'Runner')):
            model = state.apps.get_model(sc.app_label, name)
            meta = model._meta
            if meta.proxy or meta.swapped or not meta.managed:
                raise AssertionError(
                    'exclusion (a) broken: shape %r realizes a non-migratable '
                    'renamed model %s (proxy=%r swapped=%r managed=%r)'
                    % (shape, name, meta.proxy, meta.swapped, meta.managed))
            if meta.required_db_vendor or meta.required_db_features:
                raise AssertionError(
                    'exclusion (a) broken: shape %r realizes a renamed model '
                    '%s with a vendor/feature requirement' % (shape, name))
        old_model = sc.old_state.apps.get_model(sc.app_label, 'Rider')
        new_model = sc.new_state.apps.get_model(sc.app_label, 'Runner')
        for om, nm in ((old_model, 'Rider'), (new_model, 'Runner')):
            for field in om._meta.local_many_to_many:
                target = field.remote_field.model
                if isinstance(target, str):
                    continue
                t_name = target._meta.model_name
                for own in (old_model._meta.model_name,
                            new_model._meta.model_name):
                    if t_name == own:
                        raise AssertionError(
                            'exclusion (b) broken: shape %r realizes an m2m on '
                            '%s whose target model_name %r equals the renamed '
                            "model's %r -- the link table's FKs are then named "
                            'from_/to_ and models.py:367/:368 raise '
                            'FieldDoesNotExist, so the real method issues only a '
                            'PREFIX of the modeled schedule'
                            % (shape, nm, t_name, own))
                if target._meta.app_label != old_model._meta.app_label:
                    raise AssertionError(
                        'exclusion (b) assumption broken: shape %r realizes an '
                        'm2m target in a different app (%r); the same-app '
                        'invariant is what makes a model_name collision '
                        'impossible here' % (shape, target._meta.app_label))


def _is_link_table(model):
    """True for an auto-created many-to-many link table model."""
    return bool(getattr(model._meta, 'auto_created', False))


def _label(op, model, field):
    """What ONE top-level request operates on (see module docstring). `field` is
    the request's field argument (None for alter_db_table). A link relation
    yields TWO distinct labels, because a link table and a column inside that
    link table are two different things."""
    if _is_link_table(model):
        if op == 'alter_db_table':
            return ('m2m-move', model._meta.label_lower)
        return ('m2m-field', model._meta.label_lower)
    if op == 'alter_db_table':
        return ('main',)
    return ('fk', field.name, field.model._meta.label_lower)


class Recorder(object):
    """Records the TOP-LEVEL requests the rename makes of the schema layer, in
    order. Nothing is merged: one entry per request, which is what keeps the
    order inside a link relation observable."""

    __slots__ = ('depth', 'labels')

    def __init__(self):
        self.depth = 0
        self.labels = []

    def enter(self, op, model, field):
        if self.depth == 0:
            self.labels.append(_label(op, model, field))
        self.depth += 1

    def leave(self):
        self.depth -= 1


def instrument(editor, rec):
    """Wrap the two schema-layer entry points the rename uses. Internal
    re-entry (the sqlite table rebuild) goes through the same instance
    attributes, so the depth counter sees it and does not count it as a
    request the rename made."""
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


def canonical_dependents(old_model, new_model):
    """The two dependent collections the real method walks, in the order it
    visits them:

      * COLUMN relations: every `related_objects` entry (`:331`), one rewrite
        each. Position i of the model's `column_relations` is entry i of the
        first list.
      * LINK relations: every many-to-many whose auto-created link table it does
        not `continue` past (`:351-354`), TWO requests each. Position j of the
        model's `link_relations` is entry j of the second list.

    This assigns POSITION LABELS only; the oracle is still the real method's own
    requests, so a wrong list here can only produce disagreements, never a silent
    pass."""
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


class Scenario(object):
    """One built (n_fk, n_m2m) shape: the real RenameModel operation, the two
    project states, and the model classes whose `_meta.db_table` the bridge
    assigns. Built ONCE per shape and reused for every table-id pair, since the
    bridge only has to vary the two identifiers."""

    __slots__ = ('n_fk', 'n_m2m', 'app_label', 'operation', 'old_state',
                 'new_state', 'n_columns', 'n_links')

    def __init__(self, n_fk, n_m2m, app_label):
        from django.db import migrations, models
        from django.db.migrations.state import ProjectState
        self.n_fk = n_fk
        self.n_m2m = n_m2m
        self.app_label = app_label
        # An EXPLICIT db_table, as in the F2P scenario (that is what makes the
        # rename a noop there). The name is per-shape unique only so the shapes
        # can coexist in the one sqlite database; its value is immaterial, since
        # `requested()` overwrites `_meta.db_table` with the bridged name on
        # every call.
        ops = [migrations.CreateModel('Rider', fields=[
            ('id', models.AutoField(primary_key=True)),
        ], options={'db_table': 'rider_%d_%d' % (n_fk, n_m2m)})]
        # `related_objects`: other models pointing a ForeignKey at us.
        for i in range(n_fk):
            ops.append(migrations.CreateModel('Pony%d' % i, fields=[
                ('id', models.AutoField(primary_key=True)),
                ('rider', models.ForeignKey('%s.Rider' % app_label,
                                            models.CASCADE)),
            ]))
        # `local_many_to_many`: m2m declared ON us, so the auto-created link
        # table is named after this model and the rename moves it AND rewrites
        # the column inside it.
        for i in range(n_m2m):
            ops.append(migrations.CreateModel('Stable%d' % i, fields=[
                ('id', models.AutoField(primary_key=True)),
            ]))
            ops.append(migrations.AddField(
                'Rider', 'stables%d' % i,
                models.ManyToManyField('%s.Stable%d' % (app_label, i))))
        state = ProjectState()
        for op in ops:
            nxt = state.clone()
            op.state_forwards(app_label, nxt)
            state = nxt
        self.old_state = state
        self.new_state = state.clone()
        self.operation = migrations.RenameModel('Rider', 'Runner')
        self.operation.state_forwards(app_label, self.new_state)
        self._materialize()
        old_model = self.old_state.apps.get_model(self.app_label, 'Rider')
        new_model = self.new_state.apps.get_model(self.app_label, 'Runner')
        columns, links = canonical_dependents(old_model, new_model)
        self.n_columns = len(columns)
        self.n_links = len(links)

    def _materialize(self):
        """Create the real tables so the proceeding branch's `alter_field` has
        something to introspect."""
        from django.db import connection
        with connection.schema_editor(atomic=False) as editor:
            for ms in self.old_state.models.values():
                editor.create_model(
                    self.old_state.apps.get_model(self.app_label, ms.name))

    def column_relations(self):
        """The abstract carrier: one position per real column relation."""
        return list(range(self.n_columns))

    def link_relations(self):
        """The abstract carrier: one position per real link relation."""
        return list(range(self.n_links))

    def requested(self, before_name, after_name, backwards):
        """Install the bridged table names, run the REAL patched method with the
        schema layer instrumented, and return the ordered schedule of requests it
        made, in the model's code scheme. Names are restored afterwards."""
        from django.db import connection
        if backwards:
            # database_backwards swaps old/new and delegates, so from_state is
            # the renamed state and the identifiers arrive swapped (row 4).
            from_state, to_state = self.new_state, self.old_state
            old_model = from_state.apps.get_model(self.app_label, 'Runner')
            new_model = to_state.apps.get_model(self.app_label, 'Rider')
        else:
            from_state, to_state = self.old_state, self.new_state
            old_model = from_state.apps.get_model(self.app_label, 'Rider')
            new_model = to_state.apps.get_model(self.app_label, 'Runner')
        columns, links = canonical_dependents(old_model, new_model)
        nc = len(columns)
        saved_old = old_model._meta.db_table
        saved_new = new_model._meta.db_table
        old_model._meta.db_table = before_name
        new_model._meta.db_table = after_name
        rec = Recorder()
        try:
            with connection.schema_editor(collect_sql=True) as editor:
                instrument(editor, rec)
                if backwards:
                    self.operation.database_backwards(
                        self.app_label, editor, from_state, to_state)
                else:
                    self.operation.database_forwards(
                        self.app_label, editor, from_state, to_state)
        finally:
            old_model._meta.db_table = saved_old
            new_model._meta.db_table = saved_new
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
        return schedule


class Driver(object):
    def __init__(self, scenarios, shadow):
        self.scenarios = scenarios
        self.shadow = shadow
        self.checked = 0
        self.disagreements = 0
        self.examples = []

    def check(self, shape, before_id, after_id, backwards):
        sc = self.scenarios[shape]
        cols = sc.column_relations()
        links = sc.link_relations()
        got = self.shadow(before_id, after_id, cols, links)
        real = sc.requested(TABLE_NAMES[before_id], TABLE_NAMES[after_id],
                            backwards)
        self.checked += 1
        nc, nl = len(cols), len(links)
        if alpha(got, nc, nl) != alpha(real, nc, nl):
            self.disagreements += 1
            if len(self.examples) < 10:
                self.examples.append({
                    'before_table': before_id, 'after_table': after_id,
                    'column_relations': cols, 'link_relations': links,
                    'shape(n_fk,n_m2m)': shape, 'backwards': backwards,
                    'db_table_before': TABLE_NAMES[before_id],
                    'db_table_after': TABLE_NAMES[after_id],
                    'shadow_schedule': got,
                    'shadow_observable': repr(alpha(got, nc, nl)),
                    'real_schedule': real,
                    'real_observable': repr(alpha(real, nc, nl)),
                })
        return self.disagreements

    def report_failure(self, header):
        print('G-CONF FAIL: ' + header)
        for ex in self.examples:
            print('  ' + json.dumps(ex, sort_keys=True))


def build_scenarios():
    return dict((shape, Scenario(shape[0], shape[1],
                                 'conf%d_%d' % (shape[0], shape[1])))
                for shape in SHAPES)


def discrimination_self_test(scenarios):
    """Prove the harness can go red on each property the spec pins: the noop
    (prepatch region), the position of the main move, per-request multiplicity,
    the order INSIDE one link relation, and the presence of a link relation's
    second request. Returns a list of (name, flagged, expected)."""
    out = []
    probe = Driver(scenarios, prepatch_rename_schema_schedule)
    for backwards in (False, True):
        probe.check((1, 0), 0, 0, backwards)          # unchanged identifier
    out.append(('prepatch-no-noop-guard', probe.disagreements, 2))
    probe = Driver(scenarios, probe_main_move_last)
    for shape in ((1, 0), (3, 2)):
        probe.check(shape, 0, 1, False)               # rename proceeds
    out.append(('main-move-last', probe.disagreements, 2))
    probe = Driver(scenarios, probe_double_rewrite)
    for shape in ((1, 0), (3, 2)):
        probe.check(shape, 0, 1, False)
    out.append(('double-rewrite', probe.disagreements, 2))
    # The two probes the request-level carrier exists for. Both need a link
    # relation to be present, so they run on the m2m-bearing shapes.
    probe = Driver(scenarios, probe_link_pair_swapped)
    for shape in ((0, 1), (3, 2)):
        for backwards in (False, True):
            probe.check(shape, 0, 1, backwards)
    out.append(('link-pair-swapped', probe.disagreements, 4))
    probe = Driver(scenarios, probe_link_drop_inner_rewrite)
    for shape in ((0, 1), (3, 2)):
        for backwards in (False, True):
            probe.check(shape, 0, 1, backwards)
    out.append(('link-drop-inner-rewrite', probe.disagreements, 4))
    return out


def main():
    configure_django()
    assert_oracle_is_patched()

    scenarios = build_scenarios()
    for shape in SHAPES:
        got = (scenarios[shape].n_columns, scenarios[shape].n_links)
        if got != shape:
            print('G-CONF ERROR: bridge broken for shape %r: realized %r '
                  '(column relations, link relations)' % (shape, got))
            return 1

    assert_named_exclusions(scenarios)

    self_test = discrimination_self_test(scenarios)
    for name, flagged, expected in self_test:
        if flagged != expected:
            print('G-CONF ERROR: harness is blind -- probe %r was flagged on '
                  '%d of %d inputs; a check that cannot fail certifies '
                  'nothing.' % (name, flagged, expected))
            return 1

    drv = Driver(scenarios, shadow_rename_schema_schedule)

    # --- Boundary cases first ------------------------------------------------
    # The exact F2P shape: db_table unchanged with a dependent FK present,
    # forwards and backwards (the assertNumQueries(0) scenario).
    boundary = [((1, 0), 0, 0, False), ((1, 0), 0, 0, True)]
    boundary += [((0, 0), 0, 0, False),          # no dependents, noop
                 ((0, 0), 0, 1, False),          # no dependents, proceeds
                 ((1, 0), 0, 1, False),          # one column relation, proceeds
                 ((1, 0), 0, 1, True),
                 ((0, 1), 0, 0, False),          # link relation only, noop
                 ((0, 1), 0, 1, False),          # link relation only, proceeds
                 ((0, 1), 0, 1, True),
                 ((0, 2), 0, 1, False),          # TWO link relations, proceeds
                 ((0, 2), 0, 1, True),
                 ((3, 2), 0, 0, False),          # widest shape, noop
                 ((3, 2), 0, 0, True),
                 ((3, 2), 0, 1, False),          # widest shape, proceeds
                 ((3, 2), 0, 1, True),
                 ((1, 0), 6, 6, False),          # empty table name, noop
                 ((1, 0), 6, 0, False),          # empty -> non-empty, proceeds
                 ((1, 0), 0, 6, False)]          # non-empty -> empty, proceeds
    for shape, b, a, bw in boundary:
        drv.check(shape, b, a, bw)
    n_boundary = drv.checked

    # --- Exhaustive sweep of the finite realizable space ---------------------
    n_ids = len(TABLE_NAMES)
    for shape in SHAPES:
        for before_id in range(n_ids):
            for after_id in range(n_ids):
                for backwards in (False, True):
                    drv.check(shape, before_id, after_id, backwards)
    n_sweep = drv.checked - n_boundary

    # --- Seeded fuzz over the same space, to fill the >= 1e5 budget ----------
    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        shape = SHAPES[rng.randrange(len(SHAPES))]
        before_id = rng.randrange(n_ids)
        # Half the draws collide the identifiers, so the inert branch (the one
        # the gold patch introduces) stays heavily exercised.
        if rng.random() < 0.5:
            after_id = before_id
        else:
            after_id = rng.randrange(n_ids)
        drv.check(shape, before_id, after_id, rng.random() < 0.5)

    if drv.disagreements:
        drv.report_failure(
            '%d of %d inputs disagree: the shadow of model.py\'s impl region '
            'and the real patched RenameModel.database_forwards/backwards '
            'request different schedules of schema operations.'
            % (drv.disagreements, drv.checked))
        print(json.dumps({'status': 'fail', 'checked': drv.checked,
                          'disagreements': drv.disagreements, 'seed': SEED}))
        return 1

    if drv.checked < MIN_CHECKS:
        print('G-CONF ERROR: input budget not met: %d < %d'
              % (drv.checked, MIN_CHECKS))
        return 1

    print('G-CONF OK: shadow of model.py impl region == real patched '
          'RenameModel.database_forwards/backwards (ordered PER-REQUEST '
          'schedule: emptiness, which request comes FIRST, the multiset of '
          'dependent requests, and per link relation whether its link table was '
          'moved before the column inside it was rewritten; mapping.md section '
          '2 row 3) on %d inputs (%d boundary incl. the F2P '
          'assertNumQueries(0) shape + %d exhaustive sweep of the whole finite '
          'realizable space + %d fuzz, seed %d); 0 disagreements; harness proven '
          'red-capable against the prepatch impl region, a main-move-last '
          'probe, a double-rewrite probe, a swapped-link-pair probe and a '
          'dropped-link-rewrite probe.'
          % (drv.checked, n_boundary, n_sweep, N_FUZZ, SEED))
    print(json.dumps({
        'checked': drv.checked, 'disagreements': 0, 'seed': SEED,
        'exhaustive_sweep': n_sweep, 'boundary': n_boundary, 'fuzz': N_FUZZ,
        'shadow': 'direct (impl region minus Invariant() calls; no axiom, '
                  'no PSeq)',
        'observable': 'ordered per-request schedule, alpha = (first entry, '
                      'multiset of dependent requests, per-link-relation '
                      'move-before-its-own-rewrite flags)',
        'oracle': 'called: real patched RenameModel.database_forwards/'
                  'database_backwards via schema_editor(collect_sql=True) with '
                  'alter_db_table/alter_field instrumented at top level, '
                  'nothing merged',
        'discrimination_self_test': dict((n, '%d/%d' % (f, e))
                                         for n, f, e in self_test)}))
    return 0


if __name__ == '__main__':
    sys.exit(main())
