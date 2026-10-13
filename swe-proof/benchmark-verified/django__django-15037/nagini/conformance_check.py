#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-15037 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Invariant/Assert) stripped. The @Pure helpers
(names_equal / qualifier_required) copy over as plain functions; ToSeq becomes
a plain tuple shim over the code-point lists. There is no @ContractOnly callee
in this bundle: the other table's primary-key column is an introspected INPUT
of the modeled decision (an A-reference — its own soundness against the real
callee is G-AX's job, see axiom_check.py and mapping.md §3).

ORACLES (the REAL patched repo code, per mapping.md §1; the gate applies
patch.diff to /testbed before this script runs):

  (1) EXTRACTED BLOCK — the modeled decision lives inside a per-column loop of
      ``django.core.management.commands.inspectdb`` (the relation-handling
      branch of ``handle_inspection``), so it is not importable as a function.
      The REAL statements are EXTRACTED FROM THE RUNNING MODULE'S SOURCE AT
      RUNTIME via ast (the branch guarded by the relation flag, located by its
      assignment targets, not by hard-coded text), compiled once, and executed
      against controlled namespaces. No decision text is transcribed here:
      whatever the patched source computes is what the shadow is diffed
      against. The namespace supplies the loop-scope facts the block reads
      (the relations entry for the column, the parameter dict, the current
      table name) and a stub introspection whose primary-key lookup returns
      the fuzzed input — exactly the model's input boundary for that value.

  (2) LIVE END-TO-END GROUNDING — a real sqlite database with real tables and
      real foreign keys, introspected through the real management command
      (``call_command('inspectdb', <table>)``), covering the boundary shapes:
      relation to a unique non-primary column, relation to the primary key,
      one-to-one (unique) relation, relation to a table without a primary
      key, and a self relation. This grounds oracle (1): the block really is
      the code the command runs.

TYPE BRIDGE (mapping.md §2):
  * column/table name str  <->  List[int] of Unicode code points
    (enc(s) = [ord(c) for c in s]; dec inverts); string ==/!= <-> tuple
    equality of the code-point sequences.
  * relation-kind string (the one-to-one field class vs the many-to-one
    field class — the only two values the branch produces)
    <->  is_one_to_one bool; target-is-self <-> the rel-to value being the
    literal self marker.
  * the qualifier key being present in the parameter dict, with its value
    <->  needs_qualifier bool + qualifier_column (empty list <-> key absent).
  * the uniqueness flag bool is the truthiness of the parameter-dict
    expression at the binding site (mapping.md §1 row for unique_or_pk);
    fuzzed parameter dicts cover truthy/falsy/missing forms of both keys.
  * Optional primary-key column: None <-> None, present name <-> code points.

INPUT DOMAIN: relation_field's Requires are pure permission clauses, so every
well-typed (bool, str, str, str, Optional[str]) tuple is Requires-satisfying.
Boundary grid (exhaustive over parameter-dict forms x name pools, 10240
cases, incl. empty-string and unicode names and the falsy-primary-key edge)
+ 100000 fuzz cases. Pinned fuzz seed: 150370.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import ast
import inspect
import random
import sys
from io import StringIO

SEED = 150370
N_FUZZ = 100000


# -----------------------------------------------------------------------------
# Django bootstrap: real settings over an in-memory sqlite database (the same
# backend family the instance's tests use), needed for oracle (2) and to
# import the real command module for oracle (1).
# -----------------------------------------------------------------------------
import django  # noqa: E402
from django.conf import settings  # noqa: E402

if not settings.configured:
    settings.configure(
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3',
                               'NAME': ':memory:'}},
        INSTALLED_APPS=[],
        USE_TZ=False,
    )
django.setup()

from django.core.management import call_command  # noqa: E402
from django.core.management.commands import inspectdb as inspectdb_mod  # noqa: E402
from django.db import connection  # noqa: E402


# -----------------------------------------------------------------------------
# SHADOW: model.py impl region, verbatim, contracts stripped.
# ToSeq -> tuple shim; List[int] carriers are plain Python lists of ints.
# -----------------------------------------------------------------------------

def ToSeq(xs):
    return tuple(xs)


# pure helpers (model.py pure region, contract lines stripped)

def names_equal(a, b):
    """Two column/table names are equal iff their code-point sequences match."""
    return ToSeq(a) == ToSeq(b)


def qualifier_required(unique_or_pk, referenced_column, other_pk_column):
    """The referenced-column qualifier is required exactly for a plain
    many-to-one relationship whose other table has a (non-empty) primary-key
    column name that is not the referenced column."""
    return (not unique_or_pk) and other_pk_column is not None and \
        len(other_pk_column) > 0 and \
        ToSeq(other_pk_column) != ToSeq(referenced_column)


class RelationField:
    """Carrier of the three decisions about one relational column."""

    def __init__(self):
        self.is_one_to_one = False  # type: bool
        self.rel_to_self = False  # type: bool
        self.needs_qualifier = False  # type: bool
        self.qualifier_column = []  # type: list


def relation_field(unique_or_pk, referenced_column, referenced_table,
                   table_name, other_pk_column):
    # impl region of model.py, verbatim (Invariant/Assert stripped)
    out = RelationField()
    # Build a private copy of the referenced-column name up front, so all heap
    # allocation precedes the pure decisions (keeps framing local).
    col_copy = []  # type: list
    i = 0
    while i < len(referenced_column):
        col_copy.append(referenced_column[i])
        i = i + 1
    out.is_one_to_one = unique_or_pk
    out.rel_to_self = names_equal(referenced_table, table_name)
    if qualifier_required(unique_or_pk, referenced_column, other_pk_column):
        out.needs_qualifier = True
        out.qualifier_column = col_copy
    return out


# -----------------------------------------------------------------------------
# Type bridge: str <-> List[int] of code points
# -----------------------------------------------------------------------------

def enc(s):
    return [ord(c) for c in s]


def dec(xs):
    return ''.join(chr(v) for v in xs)


def uniqueness_flag(extra_params):
    """The bool input of the shadow: truthiness of the parameter-dict
    expression at the real binding site (mapping.md §1), computed on a copy
    (the real block mutates its own dict when it runs)."""
    ep = dict(extra_params)
    return bool(ep.pop('unique', False) or ep.get('primary_key'))


# -----------------------------------------------------------------------------
# ORACLE (1): the real relation-handling block, extracted from the running
# patched module's source via ast and compiled once.
# -----------------------------------------------------------------------------

def _extract_relation_block():
    src = inspect.getsource(inspectdb_mod)
    tree = ast.parse(src)
    candidates = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.If):
            continue
        # locate the branch by what it computes, not by any hard-coded text:
        # the (unique) If statement whose body assigns both the relation-kind
        # and relation-target locals.
        assigned = set()
        for sub in ast.walk(node):
            if isinstance(sub, ast.Assign):
                for tgt in sub.targets:
                    if isinstance(tgt, ast.Name):
                        assigned.add(tgt.id)
        if {'rel_type', 'rel_to'} <= assigned and isinstance(node.test, ast.Name):
            candidates.append(node)
    if len(candidates) != 1:
        print("G-CONF ERROR: expected exactly 1 relation-handling block in the "
              "real module source, found %d" % len(candidates))
        sys.exit(2)
    block = candidates[0]
    guard_name = block.test.id
    mod = ast.Module(body=[block], type_ignores=[])
    return compile(ast.fix_missing_locations(mod), '<real-relation-block>',
                   'exec'), guard_name


_BLOCK_CODE, _GUARD_NAME = _extract_relation_block()


class _StubIntrospection:
    """Supplies the modeled INPUT other_pk_column at the model's boundary:
    the primary-key lookup for the referenced table returns the fuzzed value
    (the callee itself is validated against reality by G-AX)."""

    def __init__(self, table, pk):
        self._table, self._pk = table, pk

    def get_primary_key_column(self, cursor, table_name):
        assert table_name == self._table, (table_name, self._table)
        return self._pk


class _StubConnection:
    def __init__(self, table, pk):
        self.introspection = _StubIntrospection(table, pk)


def _stub_table2model(t):
    # only the self-vs-other choice is observed; any non-self marker works
    return 'M<%s>' % (t,)


def real_block_decision(extra_params, ref_col, ref_table, table_name, pk_col):
    """Run the REAL extracted block and observe its effects:
    (relation kind, target-is-self, qualifier key present, qualifier value)."""
    ns = {
        _GUARD_NAME: True,
        'column_name': 'c0',
        'relations': {'c0': (ref_col, ref_table)},
        'extra_params': dict(extra_params),
        'connection': _StubConnection(ref_table, pk_col),
        'cursor': object(),
        'table_name': table_name,
        'table2model': _stub_table2model,
        'known_models': [],
    }
    exec(_BLOCK_CODE, ns)
    rel_type = ns['rel_type']
    rel_to = ns['rel_to']
    extra = ns['extra_params']
    assert rel_type in ('OneToOneField', 'ForeignKey'), rel_type
    return (rel_type == 'OneToOneField', rel_to == 'self',
            'to_field' in extra, extra.get('to_field'))


def check_case(extra_params, ref_col, ref_table, table_name, pk_col,
               disagreements):
    unique_or_pk = uniqueness_flag(extra_params)
    sh = relation_field(unique_or_pk, enc(ref_col), enc(ref_table),
                        enc(table_name),
                        None if pk_col is None else enc(pk_col))
    shadow_obs = (bool(sh.is_one_to_one), bool(sh.rel_to_self),
                  bool(sh.needs_qualifier),
                  dec(sh.qualifier_column) if sh.needs_qualifier else None)
    # absent-qualifier canonical form: empty list
    if not sh.needs_qualifier and len(sh.qualifier_column) != 0:
        shadow_obs = shadow_obs[:3] + ('<NONEMPTY:%r>' % dec(sh.qualifier_column),)
    real_obs = real_block_decision(extra_params, ref_col, ref_table,
                                   table_name, pk_col)
    if shadow_obs != real_obs:
        disagreements.append(
            ((dict(extra_params), ref_col, ref_table, table_name, pk_col),
             shadow_obs, real_obs))


# -----------------------------------------------------------------------------
# ORACLE (2): live end-to-end grounding over a real sqlite schema through the
# real management command.
# -----------------------------------------------------------------------------

def live_grounding(disagreements):
    with connection.cursor() as c:
        c.execute('CREATE TABLE g_target (id integer PRIMARY KEY, '
                  'ucol integer UNIQUE)')
        c.execute('CREATE TABLE g_nopk (val integer UNIQUE)')
        # relation to a unique non-primary column of the target
        c.execute('CREATE TABLE g_fk_nonpk (id integer PRIMARY KEY, '
                  'ref_id integer REFERENCES g_target (ucol))')
        # relation to the target's primary key
        c.execute('CREATE TABLE g_fk_pk (id integer PRIMARY KEY, '
                  'ref_id integer REFERENCES g_target (id))')
        # one-to-one (unique) relation to a non-primary column
        c.execute('CREATE TABLE g_o2o (id integer PRIMARY KEY, '
                  'ref_id integer UNIQUE REFERENCES g_target (ucol))')
        # relation to a table without a primary key
        c.execute('CREATE TABLE g_fk_nopk (id integer PRIMARY KEY, '
                  'ref_id integer REFERENCES g_nopk (val))')
        # self relation
        c.execute('CREATE TABLE g_self (id integer PRIMARY KEY, '
                  'parent_id integer REFERENCES g_self (id))')

    # (source table, referenced column, referenced table, uniqueness flag)
    cases = [
        ('g_fk_nonpk', 'ucol', 'g_target', False),
        ('g_fk_pk', 'id', 'g_target', False),
        ('g_o2o', 'ucol', 'g_target', True),
        ('g_fk_nopk', 'val', 'g_nopk', False),
        ('g_self', 'id', 'g_self', False),
    ]
    with connection.cursor() as c:
        pk_of = {t: connection.introspection.get_primary_key_column(c, t)
                 for t in ('g_target', 'g_nopk', 'g_self')}
    n = 0
    for table, ref_col, ref_table, is_unique in cases:
        out = StringIO()
        call_command('inspectdb', table, stdout=out)
        text = out.getvalue()
        # relation attribute names may strip a column-name suffix, so locate
        # the line by the relational field constructor instead.
        line = next((l for l in text.splitlines()
                     if 'models.ForeignKey' in l
                     or 'models.OneToOneField' in l), '')
        if not line:
            disagreements.append((('live', table), 'no relation line emitted',
                                  text))
            continue
        real_obs = (
            'OneToOneField' in line,
            "'self'" in line,
            'to_field=' in line,
            ("to_field='%s'" % ref_col) in line if 'to_field=' in line
            else None,
        )
        pk_col = pk_of[ref_table]
        sh = relation_field(is_unique, enc(ref_col), enc(ref_table),
                            enc(table), None if pk_col is None else enc(pk_col))
        shadow_obs = (
            bool(sh.is_one_to_one),
            bool(sh.rel_to_self),
            bool(sh.needs_qualifier),
            (dec(sh.qualifier_column) == ref_col) if sh.needs_qualifier
            else None,
        )
        if shadow_obs != real_obs:
            disagreements.append((('live', table, ref_col, ref_table,
                                   is_unique, pk_col), shadow_obs,
                                  (real_obs, line.strip())))
        n += 1
    return n


# -----------------------------------------------------------------------------
# Input generation: boundary grid + pinned-seed fuzz
# -----------------------------------------------------------------------------

EP_FORMS = [
    {},
    {'unique': True},
    {'unique': False},
    {'primary_key': True},
    {'primary_key': False},
    {'primary_key': ''},
    {'unique': False, 'primary_key': True},
    {'unique': True, 'primary_key': True},
    {'blank': True},
    {'unique': True, 'null': True},
]

NAME_POOL = ['', 'id', 'ucol', 'other_id', 'a', 'Id', 'café_id',
             '名前']
TABLE_POOL = ['t_alpha', 't_beta', 'self', '']
PK_POOL = [None, '', 'id', 'ucol', 'other_id', 'a', 'café_id',
           '名前']


def main():
    disagreements = []

    n_live = live_grounding(disagreements)

    # boundary grid: exhaustive over the pools
    n_grid = 0
    for ep in EP_FORMS:
        for ref_col in NAME_POOL:
            for ref_table in TABLE_POOL:
                for table in TABLE_POOL:
                    for pk in PK_POOL:
                        check_case(ep, ref_col, ref_table, table, pk,
                                   disagreements)
                        n_grid += 1
                        if len(disagreements) >= 5:
                            return report(disagreements, n_live, n_grid, 0)

    # fuzz: pinned seed
    rng = random.Random(SEED)
    alphabet = 'abcdefgh_0129AZ' + 'é中 '
    def rand_name():
        return ''.join(rng.choice(alphabet)
                       for _ in range(rng.randrange(0, 12)))
    n_fuzz = 0
    for _ in range(N_FUZZ):
        ep = dict(rng.choice(EP_FORMS))
        ref_col = rand_name() if rng.random() < 0.5 else rng.choice(NAME_POOL)
        ref_table = rand_name() if rng.random() < 0.5 else rng.choice(TABLE_POOL)
        # make self-relations and pk==ref_col collisions common
        table = ref_table if rng.random() < 0.3 else (
            rand_name() if rng.random() < 0.5 else rng.choice(TABLE_POOL))
        r = rng.random()
        if r < 0.15:
            pk = None
        elif r < 0.45:
            pk = ref_col
        else:
            pk = rand_name() if rng.random() < 0.5 else rng.choice(PK_POOL[2:])
        check_case(ep, ref_col, ref_table, table, pk, disagreements)
        n_fuzz += 1
        if len(disagreements) >= 5:
            break

    return report(disagreements, n_live, n_grid, n_fuzz)


def report(disagreements, n_live, n_grid, n_fuzz):
    total = n_live + n_grid + n_fuzz
    if disagreements:
        print("G-CONF FAIL: %d disagreement(s) over %d inputs "
              "(%d live + %d grid + %d fuzz, seed=%d):"
              % (len(disagreements), total, n_live, n_grid, n_fuzz, SEED))
        for inp, sh, real in disagreements:
            print("  input=%r\n    shadow=%r\n    real=%r" % (inp, sh, real))
        return 1
    print("G-CONF OK: shadow of the impl region agrees with the real patched "
          "relation-handling block on %d inputs (%d live end-to-end + %d "
          "boundary grid + %d fuzz, seed=%d), 0 disagreements."
          % (total, n_live, n_grid, n_fuzz, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
