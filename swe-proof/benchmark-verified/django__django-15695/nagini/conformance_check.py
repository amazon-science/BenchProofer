#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-15695 (nagini).

SHADOW: the impl regions of ``model.py``, copied VERBATIM below with only the
contract calls (``Requires`` / ``Ensures`` / ``MustTerminate`` / ``Acc``) and the
region markers deleted. Both impl regions are copied: ``issue_rename`` (the deep
model of the backend rename primitive) and ``rename_existing_index`` (the modeled
changed function), together with the two carrier classes ``ExistingIndex`` and
``SchemaEditor``. No restructuring, no renaming: the model IS Python, so the
shadow is the model's own code. There is no ``@ContractOnly`` axiom in this model
(``model.py`` axioms region is empty) and no ``PSeq`` carrier, so no axiom
delegation and no sequence shim are needed.

ORACLE: the REAL patched repo function, CALLED, not transliterated —
``RenameIndex.database_forwards(self, app_label, schema_editor, from_state,
to_state)`` at ``django/db/migrations/operations/models.py:934`` (mapping.md §1),
whose join point at lines 960-966 carries the gold guard::

    +        # Don't alter when the index name is not changed.
    +        if old_index.name == self.new_name:
    +            return
             to_model_state = to_state.models[app_label, self.model_name_lower]
             new_index = to_model_state.get_index_by_name(self.new_name)
             schema_editor.rename_index(model, old_index, new_index)

The gate applies ``patch.diff`` to /testbed and sets ``PYTHONPATH=/testbed``
before this script runs, so the imported ``RenameIndex`` is the patched class.
Unlike the velvet sibling (which transliterates the guard because Lean cannot
drive Django), nothing here needs transliteration: ``database_forwards`` is
drivable in-container over real ``ProjectState`` / ``ModelState`` / ``Index``
objects, and it is driven, on BOTH branches that produce ``old_index``.

THREE LEGS, all driving the real patched ``database_forwards``:

  Leg A (>= 1e5 inputs, the bulk differential).  Real ``database_forwards``
  called with real ``ProjectState``/``ModelState``/``models.Index`` objects and a
  recording stand-in for ``schema_editor`` whose ``rename_index`` records
  ``(old_index.name, new_index.name)``. Observable: whether a rename was issued
  and its target name -> compared against the shadow's ``editor.rename_issued``
  / ``editor.renamed_to``. Both ``old_index`` producers are exercised: the NAMED
  branch (``from_model_state.get_index_by_name(self.old_name)``, models.py:961-962)
  and the UNNAMED ``old_fields`` branch (``schema_editor._constraint_names(...)``
  -> ``matching_index_name[0]``, models.py:939-959) — the model abstracts both to
  the single field ``ExistingIndex.name`` (mapping.md §2, refinement.md A1), so
  both must agree with the one shadow.

  Leg B (real sqlite backend + real DB).  Same real ``database_forwards``, but
  with the REAL ``BaseDatabaseSchemaEditor`` from ``connection.schema_editor()``
  against a real table carrying a real index. Two further observables that a
  recording fake cannot ground:
    * the SQL actually emitted (``editor.execute`` call count) -> the shadow's
      ``editor.rename_issued``; zero-SQL on the no-op path is the
      ``assertNumQueries(0)`` the F2P test relies on;
    * the index names present on the real table afterwards -> the shadow's
      post-state ``old_index.name == new_name`` (the model's claim that the
      existing index ends up carrying the target name in BOTH cases).
  This closes the loop the deep model ``issue_rename`` leaves open, against the
  real ``BaseDatabaseSchemaEditor.rename_index`` (mapping.md §3.1). It includes
  the exact F2P shape ``test_rename_index_unnamed_index``: forward rename,
  backward (a no-op for the unnamed index), then RE-APPLY forward, which must
  emit zero SQL and leave ``new_pony_test_idx`` in place.

  Leg C (bridge soundness).  The type bridge of mapping.md §2 conflates
  ``new_name`` with ``new_index.name``; the justification is that
  ``get_index_by_name(self.new_name)`` returns the index whose ``.name ==
  self.new_name``. That is checked against the real ``ModelState`` rather than
  assumed, plus the shadow's own proof obligation
  ``Requires(old_index.name != new_name)`` on ``issue_rename`` (a shadow that
  reached the backend primitive with equal names would be the very bug).

TYPE BRIDGE (mapping.md §2, inverted): the repo compares index names as ``str``;
the model carries them as ``int`` identifiers, sound because in this change names
are only ever compared for equality, never indexed or sliced. Generation runs in
the ``str`` direction (real names, so the real function is fed real values) and
an exact-match interning table ``str -> int`` (fresh id per distinct name,
starting at 1 so the ``renamed_to`` sentinel ``0`` is never a real name) lowers
each name to the model's carrier. Equal strings <-> equal ints by construction,
so every generated input lands inside the model's ``Requires`` (which constrains
only that the editor starts with ``rename_issued is False`` — every drive uses a
fresh ``SchemaEditor()`` — and never restricts the names). Case-variant and
substring-related name pairs are generated deliberately: a model that compared
names case-insensitively or by prefix would be refuted here.

Inputs: boundary cases first (equal names; differing names; the exact F2P name
``new_pony_test_idx``; case variants; empty target name; Django's auto-generated
``<table>_<cols>_<hash>_<suffix>`` shape; long/max-length names), each branch of
the guard taken on each of the two ``old_index`` producers, then seeded fuzz to
fill the count. The modeled input space (all name pairs) is infinite, so it is
sampled, not enumerated. Pinned seed: 15695 (recorded in mapping.md §G-CONF).

Exit 0 iff zero disagreements; on a disagreement the input and both outputs are
printed and the exit status is 1. stdlib + Django (the repo under test) only.
"""
import random
import sys

SEED = 15695
N_LEG_A = 100_000
APP_LABEL = "contenttypes"
MODEL_NAME = "Pony"
MODEL_KEY = (APP_LABEL, MODEL_NAME.lower())
F2P_NAME = "new_pony_test_idx"


# =============================================================================
# SHADOW — the impl regions of model.py, verbatim, contract calls stripped.
# =============================================================================

class ExistingIndex:
    def __init__(self, name):
        self.name = name


class SchemaEditor:
    def __init__(self):
        self.rename_issued = False  # type: bool
        self.renamed_to = 0  # type: int


# Records a violation of issue_rename's Requires(old_index.name != new_name):
# the shadow must never reach the backend primitive with equal names.
PRECOND_VIOLATIONS = []


def issue_rename(editor, old_index, new_name):
    """Deep model of the unchanged backend rename primitive: it records that a
    rename was issued and effects the index's name change to ``new_name``."""
    # model.py Requires(old_index.name != new_name) — the caller MUST establish
    # this; contracts are stripped from the shadow, so we observe it instead of
    # assuming it (a violation is a finding, not something to paper over).
    if not (old_index.name != new_name):
        PRECOND_VIOLATIONS.append((old_index.name, new_name))
    editor.rename_issued = True
    editor.renamed_to = new_name
    old_index.name = new_name


def rename_existing_index(editor, old_index, new_name):
    # The FIX: don't alter when the current name already equals the target.
    if old_index.name == new_name:
        return
    issue_rename(editor, old_index, new_name)


# =============================================================================
# TYPE BRIDGE — mapping.md §2: index name (str) <-> int identifier.
# =============================================================================

class NameIds(object):
    """Exact-match interning: distinct names <-> distinct ints. Ids start at 1
    so that 0 (the model's ``renamed_to`` "no rename yet" sentinel) is never a
    real name, as mapping.md §2 requires."""

    def __init__(self):
        self._ids = {}

    def to_int(self, name):
        if name not in self._ids:
            self._ids[name] = len(self._ids) + 1
        return self._ids[name]


def shadow_decision(cur_name_id, new_name_id):
    """Run the shadow on the model's carrier. Returns
    (rename_issued, renamed_to, final_index_name_id)."""
    editor = SchemaEditor()          # Requires: rename_issued is False
    old_index = ExistingIndex(cur_name_id)
    rename_existing_index(editor, old_index, new_name_id)
    return (editor.rename_issued, editor.renamed_to, old_index.name)


# =============================================================================
# ORACLE — the real patched RenameIndex.database_forwards.
# =============================================================================

def setup_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes"],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
            USE_TZ=False,
        )
    django.setup()


class RecordingSchemaEditor(object):
    """Stand-in for ``schema_editor`` in Leg A: records the at-most-one
    ``rename_index`` call the patched ``database_forwards`` makes, and serves
    ``_constraint_names`` for the unnamed ``old_fields`` branch. The rename
    primitive itself is modeled deeply (mapping.md §3.1) and grounded against
    the REAL ``BaseDatabaseSchemaEditor`` in Leg B and by G-AX."""

    def __init__(self, connection, constraint_names=None):
        self.connection = connection
        self.calls = []
        self._constraint_name_list = constraint_names

    def _constraint_names(self, model, column_names=None, index=None, **kwargs):
        return list(self._constraint_name_list)

    def rename_index(self, model, old_index, new_index):
        self.calls.append((old_index.name, new_index.name))


def oracle_decision(op, from_state, to_state, editor):
    """Call the REAL patched database_forwards; return
    (rename_issued, renamed_to_name) with renamed_to_name None when no rename
    was issued."""
    op.database_forwards(APP_LABEL, editor, from_state, to_state)
    if not editor.calls:
        return (False, None)
    if len(editor.calls) != 1:
        raise AssertionError("real database_forwards issued %d rename_index "
                             "calls, expected at most 1: %r"
                             % (len(editor.calls), editor.calls))
    return (True, editor.calls[0][1])


# =============================================================================
# Input generation.
# =============================================================================

NAME_POOL = [
    F2P_NAME,                       # the exact F2P target name
    "pony_pink_idx",
    "pony_pink_weight_idx",
    "new_pony_test_idx2",           # F2P name as a strict prefix
    "NEW_PONY_TEST_IDX",            # case variant of the F2P name
    "New_Pony_Test_Idx",
    "idx",
    "IDX",
    "a",
    "A",
    "",                             # empty target name
    "_",
    "0",
    "pony_pink_0c02a7_idx",         # Django auto-generated name shape
    "pony_pink_1f9b3d_idx",
    "x" * 30,                       # Index.max_name_length
    "x" * 29,
]


def rand_name(rng):
    kind = rng.randint(0, 4)
    if kind == 0:
        return rng.choice(NAME_POOL)
    if kind == 1:
        # auto-generated shape: <table>_<col>_<hex>_idx
        return "pony_%s_%06x_idx" % (rng.choice(["pink", "weight", "pink_weight"]),
                                     rng.randrange(0, 1 << 24))
    if kind == 2:
        n = rng.randint(1, 12)
        alphabet = "abcdexyz_0123ABCXYZ"
        return "".join(rng.choice(alphabet) for _ in range(n))
    if kind == 3:
        # case perturbation of a pool name: refutes a case-insensitive model
        base = rng.choice([n for n in NAME_POOL if n])
        return "".join(c.upper() if rng.random() < 0.4 else c.lower() for c in base)
    # near-miss: a pool name with one character appended/removed
    base = rng.choice([n for n in NAME_POOL if n])
    if rng.random() < 0.5:
        return base + rng.choice("x_9")
    return base[:-1]


def boundary_pairs():
    """(current index name, target name) pairs; both guard branches on the
    interesting shapes."""
    pairs = [
        (F2P_NAME, F2P_NAME),                    # the F2P re-apply: equal -> no-op
        ("pony_pink_idx", F2P_NAME),             # first apply: differ -> rename
        ("", ""),                                # equal empties -> no-op
        ("", "x"),                               # differ (empty current)
        ("x", ""),                               # differ (empty target)
        ("a", "a"),
        ("a", "b"),
        ("A", "a"),                              # case variants differ
        ("a", "A"),
        (F2P_NAME, "NEW_PONY_TEST_IDX"),
        (F2P_NAME, F2P_NAME + "2"),              # strict prefix differs
        (F2P_NAME + "2", F2P_NAME),
        ("x" * 30, "x" * 30),                    # max-length, equal
        ("x" * 30, "x" * 29),                    # max-length, differ by one
        ("pony_pink_0c02a7_idx", "pony_pink_0c02a7_idx"),
        ("pony_pink_0c02a7_idx", F2P_NAME),      # auto-generated -> explicit
    ]
    return pairs


# =============================================================================
# Leg A — bulk differential over both old_index producers.
# =============================================================================

def make_states(models_mod, ProjectState, ModelState, pony):
    from_state = ProjectState()
    from_state.add_model(ModelState.from_model(pony))
    to_state = ProjectState()
    to_state.add_model(ModelState.from_model(pony))
    return from_state, to_state


def leg_a(rng, ids, connection, models_mod, ProjectState, ModelState, RenameIndex,
          pony):
    """Drive the real patched database_forwards on both branches. Returns
    (checked, stats, error_string_or_None)."""
    from_state, to_state = make_states(models_mod, ProjectState, ModelState, pony)
    Index = models_mod.Index

    SKIPPED = "<skipped>"

    def one(cur_name, new_name, branch):
        """One differential comparison. branch in {"named", "unnamed"}.
        Returns None on agreement, SKIPPED if the input is not constructible on
        this producer, else the disagreement message."""
        # ---- oracle side: real objects, real function -----------------------
        to_state.models[MODEL_KEY].options["indexes"] = [
            Index(fields=["pink"], name=new_name)]
        if branch == "named":
            # models.py:961-962 — old_index = get_index_by_name(self.old_name),
            # so the resolved current name IS self.old_name.
            if not cur_name:
                return SKIPPED   # RenameIndex rejects an empty old_name
            from_state.models[MODEL_KEY].options["indexes"] = [
                Index(fields=["pink"], name=cur_name)]
            op = RenameIndex(model_name=MODEL_NAME, new_name=new_name,
                             old_name=cur_name)
            editor = RecordingSchemaEditor(connection)
        else:
            # models.py:939-959 — old_index name comes from the DB via
            # _constraint_names, decoupled from the operation's arguments.
            op = RenameIndex(model_name=MODEL_NAME, new_name=new_name,
                             old_fields=("pink",))
            editor = RecordingSchemaEditor(connection, constraint_names=[cur_name])
        model = to_state.apps.get_model(APP_LABEL, MODEL_NAME)
        # Stay inside the modeled domain: the model models the step FROM the
        # join point, so a router that vetoed the migration would make this
        # check vacuous. Assert we really reach the guard.
        if not op.allow_migrate_model(connection.alias, model):
            raise AssertionError("allow_migrate_model vetoed the drive; the "
                                 "join point the model models is unreachable")
        o_issued, o_target = oracle_decision(op, from_state, to_state, editor)

        # ---- shadow side: the model's carrier -------------------------------
        cur_id = ids.to_int(cur_name)
        new_id = ids.to_int(new_name)
        s_issued, s_renamed_to, s_final = shadow_decision(cur_id, new_id)

        # ---- diff -----------------------------------------------------------
        o_target_id = None if o_target is None else ids.to_int(o_target)
        if s_issued != o_issued:
            return ("DISAGREEMENT (leg A, %s branch) on "
                    "(current name=%r, target name=%r) [ints %d, %d]:\n"
                    "  shadow: rename_issued=%r\n"
                    "  real patched database_forwards: rename_issued=%r"
                    % (branch, cur_name, new_name, cur_id, new_id,
                       s_issued, o_issued))
        if o_issued and s_renamed_to != o_target_id:
            return ("DISAGREEMENT (leg A, %s branch) on "
                    "(current name=%r, target name=%r):\n"
                    "  shadow: renamed_to=%d\n"
                    "  real patched database_forwards: rename_index target="
                    "%r (int %d)"
                    % (branch, cur_name, new_name, s_renamed_to,
                       o_target, o_target_id))
        # the model's post-state: the index ends up carrying the target name
        if s_final != new_id:
            return ("DISAGREEMENT (leg A, %s branch): shadow left the index at "
                    "int %d, target is %r (int %d)"
                    % (branch, s_final, new_name, new_id))
        return None

    stats = {"named_equal": 0, "named_differ": 0,
             "unnamed_equal": 0, "unnamed_differ": 0, "skipped_empty_old": 0}
    checked = 0

    def record(cur_name, new_name, branch):
        key = "%s_%s" % (branch, "equal" if cur_name == new_name else "differ")
        stats[key] += 1

    # boundary cases, on both producers
    for cur_name, new_name in boundary_pairs():
        for branch in ("named", "unnamed"):
            err = one(cur_name, new_name, branch)
            if err is SKIPPED:
                stats["skipped_empty_old"] += 1
                continue
            if err is not None:
                return (checked, stats, err)
            checked += 1
            record(cur_name, new_name, branch)

    # seeded fuzz to fill the count; ~40% of pairs are made equal so the no-op
    # branch of the guard is heavily exercised, not merely touched once.
    while checked < N_LEG_A:
        branch = "named" if rng.random() < 0.5 else "unnamed"
        cur_name = rand_name(rng)
        if branch == "named" and not cur_name:
            cur_name = "a"          # empty old_name is not constructible
        new_name = cur_name if rng.random() < 0.4 else rand_name(rng)
        err = one(cur_name, new_name, branch)
        if err is SKIPPED:
            continue
        if err is not None:
            return (checked, stats, err)
        checked += 1
        record(cur_name, new_name, branch)

    return (checked, stats, None)


# =============================================================================
# Leg B — real BaseDatabaseSchemaEditor against a real table.
# =============================================================================

def leg_b(ids, connection, models_mod, ProjectState, ModelState, RenameIndex,
          pony):
    """Ground the deep rename primitive: real schema editor, real sqlite table.
    Returns (checked, error_string_or_None)."""
    Index = models_mod.Index
    from_state, to_state = make_states(models_mod, ProjectState, ModelState, pony)
    table = pony._meta.db_table

    def index_names():
        with connection.cursor() as cur:
            cons = connection.introspection.get_constraints(cur, table)
        return {n for n, info in cons.items()
                if info.get("index") and not info.get("primary_key")}

    def real_drive(cur_name, new_name, branch):
        """Drive the real patched step with the REAL schema editor; return
        (sql_emitted_count, index names on the table afterwards)."""
        to_state.models[MODEL_KEY].options["indexes"] = [
            Index(fields=["pink"], name=new_name)]
        if branch == "named":
            from_state.models[MODEL_KEY].options["indexes"] = [
                Index(fields=["pink"], name=cur_name)]
            op = RenameIndex(model_name=MODEL_NAME, new_name=new_name,
                             old_name=cur_name)
        else:
            op = RenameIndex(model_name=MODEL_NAME, new_name=new_name,
                             old_fields=("pink",))
        with connection.schema_editor() as editor:
            counter = {"n": 0}
            real_execute = editor.execute

            def counting_execute(sql, params=()):
                counter["n"] += 1
                return real_execute(sql, params)

            editor.execute = counting_execute
            op.database_forwards(APP_LABEL, editor, from_state, to_state)
        return counter["n"], index_names()

    def compare(cur_name, new_name, branch, label):
        s_issued, s_renamed_to, s_final = shadow_decision(ids.to_int(cur_name),
                                                          ids.to_int(new_name))
        n_sql, names = real_drive(cur_name, new_name, branch)
        if s_issued != (n_sql > 0):
            return ("DISAGREEMENT (leg B, %s, %s branch) on "
                    "(current name=%r, target name=%r):\n"
                    "  shadow: rename_issued=%r\n"
                    "  real patched step against the real backend: "
                    "%d SQL statement(s) emitted"
                    % (label, branch, cur_name, new_name, s_issued, n_sql))
        if s_final != ids.to_int(new_name) or names != {new_name}:
            return ("DISAGREEMENT (leg B, %s, %s branch) on "
                    "(current name=%r, target name=%r):\n"
                    "  shadow post-state: index carries int %d (target int %d)\n"
                    "  real table afterwards carries index names %r"
                    % (label, branch, cur_name, new_name, s_final,
                       ids.to_int(new_name), sorted(names)))
        return None

    with connection.schema_editor() as editor:
        editor.create_model(pony)
    with connection.schema_editor() as editor:
        editor.add_index(pony, Index(fields=["pink"], name="pony_pink_idx"))
    if index_names() != {"pony_pink_idx"}:
        return (0, "leg B setup failed: table %r indexes = %r"
                   % (table, sorted(index_names())))

    checked = 0
    # (1) differ -> the rename really happens, on the named branch
    err = compare("pony_pink_idx", "pony_renamed_idx", "named", "first apply")
    if err:
        return (checked, err)
    checked += 1
    # (2) equal -> zero SQL, index untouched (re-apply / no-op)
    err = compare("pony_renamed_idx", "pony_renamed_idx", "named", "re-apply")
    if err:
        return (checked, err)
    checked += 1
    # (3) the F2P shape on the UNNAMED branch: forward rename to the F2P name,
    #     then re-apply forward, which the gold guard must turn into a no-op
    #     emitting zero SQL (the assertNumQueries(0) the F2P test asserts).
    err = compare("pony_renamed_idx", F2P_NAME, "unnamed", "F2P forward")
    if err:
        return (checked, err)
    checked += 1
    err = compare(F2P_NAME, F2P_NAME, "unnamed", "F2P re-apply (the fix)")
    if err:
        return (checked, err)
    checked += 1
    err = compare(F2P_NAME, F2P_NAME, "unnamed", "F2P re-apply again")
    if err:
        return (checked, err)
    checked += 1
    # (4) case-variant target: names differ, so a rename really is issued
    err = compare(F2P_NAME, "New_Pony_Test_Idx", "named", "case variant")
    if err:
        return (checked, err)
    checked += 1
    # (5) back to a plain name, differing again
    err = compare("New_Pony_Test_Idx", "pony_pink_idx", "named", "rename back")
    if err:
        return (checked, err)
    checked += 1
    return (checked, None)


# =============================================================================
# Leg C — bridge soundness against the real ModelState.
# =============================================================================

def leg_c(models_mod, ModelState, pony):
    """mapping.md §2 conflates the model's single ``new_name`` with
    ``new_index.name``, justified by get_index_by_name's contract. Check that
    against the real ModelState instead of assuming it."""
    Index = models_mod.Index
    state = ModelState.from_model(pony)
    checked = 0
    for name in NAME_POOL:
        state.options["indexes"] = [Index(fields=["pink"], name=name)]
        got = state.get_index_by_name(name)
        if got.name != name:
            return (checked, "BRIDGE UNSOUND: real ModelState."
                             "get_index_by_name(%r).name = %r, so new_index.name "
                             "!= self.new_name and the model's single new_name "
                             "parameter is not faithful" % (name, got.name))
        checked += 1
    return (checked, None)


# =============================================================================
# Driver.
# =============================================================================

def main():
    setup_django()
    from django.db import connection, models as models_mod
    from django.db.migrations.state import ProjectState, ModelState
    from django.db.migrations.operations.models import RenameIndex

    # the patched guard must actually be present in the imported module
    import inspect
    src = inspect.getsource(RenameIndex.database_forwards)
    if "old_index.name == self.new_name" not in src:
        print("G-CONF ERROR: the imported RenameIndex.database_forwards does "
              "NOT contain the gold guard; the oracle is unpatched code.")
        return 1

    class Pony(models_mod.Model):
        pink = models_mod.IntegerField(default=3)
        weight = models_mod.FloatField(default=1.0)

        class Meta:
            app_label = APP_LABEL

    ids = NameIds()
    rng = random.Random(SEED)

    c_checked, err = leg_c(models_mod, ModelState, Pony)
    if err:
        print(err)
        return 1

    a_checked, stats, err = leg_a(rng, ids, connection, models_mod, ProjectState,
                                  ModelState, RenameIndex, Pony)
    if err:
        print(err)
        return 1

    b_checked, err = leg_b(ids, connection, models_mod, ProjectState, ModelState,
                           RenameIndex, Pony)
    if err:
        print(err)
        return 1

    if PRECOND_VIOLATIONS:
        print("DISAGREEMENT: the shadow reached issue_rename with equal names "
              "%d time(s) (first %r), violating its Requires(old_index.name != "
              "new_name) — the rename-X-to-X the guard exists to prevent."
              % (len(PRECOND_VIOLATIONS), PRECOND_VIOLATIONS[0]))
        return 1

    # a green run must have exercised BOTH branches of the guard on BOTH
    # old_index producers, else it certifies nothing.
    for key in ("named_equal", "named_differ", "unnamed_equal", "unnamed_differ"):
        if stats[key] == 0:
            print("G-CONF ERROR: input generation never produced %s; the check "
                  "would be vacuous. stats=%r" % (key, stats))
            return 1

    total = a_checked + b_checked + c_checked
    print("G-CONF OK: shadow (verbatim contract-stripped impl region of "
          "model.py) == real patched RenameIndex.database_forwards on %d inputs "
          "-- leg A %d drives of the real function over both old_index "
          "producers (named equal/differ %d/%d, unnamed equal/differ %d/%d), "
          "leg B %d drives against the real sqlite backend (SQL count + real "
          "table index names, incl. the F2P re-apply no-op), leg C %d bridge "
          "checks; seed=%d; 0 disagreements."
          % (total, a_checked, stats["named_equal"], stats["named_differ"],
             stats["unnamed_equal"], stats["unnamed_differ"], b_checked,
             c_checked, SEED))
    print('{"checked": %d, "leg_a": %d, "leg_b": %d, "leg_c": %d, '
          '"disagreements": 0, "seed": %d, "shadow": "direct (verbatim '
          'contract-stripped impl region)", "oracle": "called: '
          'RenameIndex.database_forwards (patched)"}'
          % (total, a_checked, b_checked, c_checked, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
