#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-15732 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Exsures) stripped. The @Pure helper ``disambiguates``
copies over as a plain function; ``ToSeq`` becomes a plain-tuple shim. The
user-defined exception class stands in for the wrong-count failure exactly as
in model.py. There are no @ContractOnly callees in this bundle (mapping.md
section 3: no consumed axiom).

ORACLE: the REAL patched repo method the model models per mapping.md section 1
- ``BaseDatabaseSchemaEditor._delete_composed_index`` in
``django/db/backends/base/schema.py`` (the gate applies patch.diff to /testbed
before this script runs). The method is exercised on a real schema-editor
instance; the CHANGED selection logic runs untouched. The modeling boundary of
mapping.md is realized as follows:

  * ``candidates`` input: ``_constraint_names`` is an UNCHANGED discovery
    callee whose RESULT is the model's input (mapping.md section 3.1), so the
    editor's ``_constraint_names`` is overridden to return the generated
    candidate-name list - this is input injection at the documented model
    boundary, not a stub of changed code.
  * ``default_name`` input: computed by the REAL patched helper
    ``str(editor._unique_constraint_name(table, columns, quote=False))``
    (mapping.md section 3.2) - NOT stubbed; whether it is among the candidates
    is controlled by which strings the generated candidate list contains.
  * ``unique`` input: realized as the ``constraint_kwargs`` dict the method
    receives; the bridge is ``unique == (kwargs.get("unique") is True)``
    (mapping.md section 1), and the fuzz feeds non-True truthy values too so
    the identity-vs-truthiness distinction is actually exercised.
  * ``feature_on`` input: the connection ``features`` flag on the (fake)
    connection object - environment plumbing, not repo logic.
  * observable: WHICH constraint name the method targets for deletion
    (mapping.md section 2 / refinement.md A10: the SQL rendering/execution is
    an unchanged downstream op) - captured by overriding the unchanged
    downstream ``_delete_constraint_sql`` to record the name; a wrong-count
    failure is the raised ValueError.

TYPE BRIDGE (mapping.md section 2): constraint names are str in the repo and
distinct int identifiers in the model. Per test case a bijection is fixed:
id 0 <-> the real computed default name string; id k>0 <-> a distinct
generated name string (which can never equal the default: the default carries
a digest+suffix shape the generated names do not). List order, length,
duplicates, membership and [0] are preserved by the bijection.

INPUT DOMAIN: the model's only precondition is a readable candidate list, so
every generated (candidates, kwargs, feature_on) case is Requires-satisfying.
Boundary grid: candidate lists of length 0..3 over {default, others} incl.
duplicates, crossed with kwargs variants (True / absent / False / truthy
non-True) and both feature flags, over several table/column shapes (incl. a
name long enough to take the shortening path of the underlying name builder).
Fuzz: 100000 randomized cases, pinned seed 15732 (recorded here).

Exit 0 iff zero disagreements; on disagreement prints the input and both
observations and exits 1. stdlib only.
"""
import random
import sys

SEED = 15732
N_FUZZ = 100000


# --- ToSeq shim: the impl only uses `in` membership over the sequence --------

def ToSeq(lst):
    return tuple(lst)


class AmbiguousConstraintSelection(Exception):
    """model.py's user-defined stand-in for the wrong-count failure."""


# --- pure helper from model.py, contracts stripped ----------------------------

def disambiguates(unique, feature_on, n_candidates):
    return unique and feature_on and n_candidates >= 1


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def select_constraint_to_remove(candidates, default_name, unique, feature_on):
    # Start from the full discovered set; narrow it when disambiguation applies
    # and the rule's default name is among the candidates.
    narrowed_to_default = False
    if disambiguates(unique, feature_on, len(candidates)):
        if default_name in ToSeq(candidates):
            narrowed_to_default = True
    # After (optional) narrowing, exactly one of the following holds:
    #   * narrowed_to_default      -> the single name is ``default_name``
    #   * len(candidates) == 1     -> the single name is ``candidates[0]``
    # otherwise selection is impossible.
    if narrowed_to_default:
        return default_name
    if len(candidates) == 1:
        return candidates[0]
    raise AmbiguousConstraintSelection()


# --- oracle plumbing: a real schema editor over a minimal fake connection -----

def build_oracle():
    """Import the REAL patched schema editor and wire the minimal environment
    it needs (connection features/ops, a model-metadata stand-in). Returns a
    callable oracle(candidate_strs, kwargs, feature_on, shape) ->
    ('ok', deleted_name_str) | ('raise', None), plus a function computing the
    real default name for a shape via the REAL patched helper."""
    from django.conf import settings
    if not settings.configured:
        settings.configure()
    from django.db.backends.base.schema import BaseDatabaseSchemaEditor

    class FakeOps(object):
        def max_name_length(self):
            return 200

        def quote_name(self, name):
            return '"%s"' % name

    class FakeFeatures(object):
        can_rollback_ddl = False
        allows_multiple_constraints_on_same_fields = True

    class FakeConnection(object):
        alias = "default"

        def __init__(self):
            self.features = FakeFeatures()
            self.ops = FakeOps()

    class FakeField(object):
        def __init__(self, column):
            self.column = column

    class FakeMeta(object):
        def __init__(self, db_table, columns):
            self.db_table = db_table
            self.constraints = []
            self.indexes = []
            self._fields = {c: FakeField(c) for c in columns}

        def get_field(self, name):
            return self._fields[name]

    class FakeModel(object):
        def __init__(self, db_table, columns):
            self._meta = FakeMeta(db_table, columns)

    class ProbeEditor(BaseDatabaseSchemaEditor):
        """REAL editor; only the two documented model-boundary seams are
        overridden: the unchanged discovery callee (its result IS the model
        input) and the unchanged downstream deletion-SQL builder (its name
        argument IS the model's observable)."""

        def __init__(self, connection, injected_names):
            super(ProbeEditor, self).__init__(connection)
            self._injected_names = injected_names
            self.deleted_names = []

        def _constraint_names(self, model, column_names=None, **kwargs):
            return list(self._injected_names)

        def _delete_constraint_sql(self, template, model, name):
            self.deleted_names.append(name)
            return None

        def execute(self, sql, params=()):
            pass

    def default_name_for(shape):
        table, columns = shape
        conn = FakeConnection()
        editor = ProbeEditor(conn, [])
        # the REAL patched helper computes the composed rule's default name
        return str(editor._unique_constraint_name(table, columns, quote=False))

    def oracle(candidate_strs, kwargs, feature_on, shape):
        table, columns = shape
        conn = FakeConnection()
        conn.features.allows_multiple_constraints_on_same_fields = feature_on
        editor = ProbeEditor(conn, candidate_strs)
        model = FakeModel(table, columns)
        try:
            editor._delete_composed_index(model, list(columns), dict(kwargs),
                                          "DROP CONSTRAINT %(name)s")
        except ValueError:
            return ("raise", None)
        assert len(editor.deleted_names) == 1, editor.deleted_names
        return ("ok", editor.deleted_names[0])

    return oracle, default_name_for


# --- differential driver -------------------------------------------------------

def observe_shadow(candidates, default_name, unique, feature_on):
    try:
        return ("ok", select_constraint_to_remove(list(candidates),
                                                  default_name, unique,
                                                  feature_on))
    except AmbiguousConstraintSelection:
        return ("raise", None)


def check_one(oracle, default_str, shape, id_pattern, kwargs, feature_on):
    """id_pattern: list of int ids (0 = the default name's id, k>0 = other
    distinct names). Runs shadow (over ids) and oracle (over the bijected
    strings) and compares observations under the bijection."""
    id_to_str = {0: default_str}
    for k in set(id_pattern):
        if k != 0:
            id_to_str[k] = "other_name_%d" % k
    candidate_strs = [id_to_str[k] for k in id_pattern]
    # bridge: the model's boolean is the identity-with-True of the kwargs entry
    unique = kwargs.get("unique") is True

    shadow = observe_shadow(id_pattern, 0, unique, feature_on)
    real = oracle(candidate_strs, kwargs, feature_on, shape)

    # biject the real observation back to ids for comparison
    str_to_id = dict((v, k) for k, v in id_to_str.items())
    real_ids = (real[0], str_to_id[real[1]] if real[0] == "ok" else None)
    if shadow != real_ids:
        print("DISAGREEMENT:")
        print("  shape=%r kwargs=%r feature_on=%r" % (shape, kwargs, feature_on))
        print("  candidates(ids)=%r default(id)=0 unique=%r" % (id_pattern, unique))
        print("  candidates(strs)=%r default(str)=%r" % (candidate_strs, default_str))
        print("  shadow (impl region)      = %r" % (shadow,))
        print("  real (patched repo method)= %r (as ids: %r)" % (real, real_ids))
        return False
    return True


SHAPES = [
    ("app_thing", ["a", "b"]),
    ("app_thing", ["col"]),
    ("some_app_model_with_quite_a_long_table_name_indeed_yes_really_long",
     ["first_column_name", "second_column_name", "third_column_name"]),
]

KWARGS_VARIANTS = [
    {"unique": True, "primary_key": False},   # the composed-uniqueness removal
    {"unique": True},
    {},
    {"unique": False, "primary_key": False},
    {"unique": 1},        # truthy but not identical to True
    {"unique": "yes"},    # truthy but not identical to True
    {"index": True},      # a non-uniqueness composed removal
]


def main():
    oracle, default_name_for = build_oracle()

    checked = 0
    failures = 0

    # --- boundary grid --------------------------------------------------------
    patterns = [
        [],                # nothing discovered
        [0],               # sole candidate = the default
        [1],               # sole candidate, not the default
        [0, 1], [1, 0],    # two candidates incl. the default (either order)
        [1, 2],            # two candidates, default absent
        [0, 1, 2], [1, 0, 2], [1, 2, 0],   # three incl. default
        [1, 2, 3],         # three, default absent
        [0, 0],            # duplicated default
        [1, 1],            # duplicated non-default
        [0, 1, 0],         # default twice among others
    ]
    for shape in SHAPES:
        default_str = default_name_for(shape)
        for pattern in patterns:
            for kwargs in KWARGS_VARIANTS:
                for feature_on in (True, False):
                    ok = check_one(oracle, default_str, shape, pattern,
                                   kwargs, feature_on)
                    checked += 1
                    if not ok:
                        failures += 1
                        if failures >= 5:
                            return 1

    # --- randomized fuzz (pinned seed) ---------------------------------------
    rng = random.Random(SEED)
    shape = SHAPES[0]
    default_str = default_name_for(shape)
    id_pool = [0, 1, 2, 3, 4, 5]
    for _ in range(N_FUZZ):
        n = rng.randint(0, 5)
        pattern = [rng.choice(id_pool) for _ in range(n)]
        kwargs = rng.choice(KWARGS_VARIANTS)
        feature_on = rng.choice([True, False])
        ok = check_one(oracle, default_str, shape, pattern, kwargs, feature_on)
        checked += 1
        if not ok:
            failures += 1
            if failures >= 5:
                return 1

    if failures:
        return 1
    print("G-CONF OK: shadow impl == real patched selection on %d inputs "
          "(boundary grid over 3 shapes + %d fuzz, seed %d); 0 disagreements."
          % (checked, N_FUZZ, SEED))
    print('{"checked": %d, "disagreements": 0, "seed": %d, '
          '"shadow": "direct (contract-stripped impl region)"}'
          % (checked, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
