#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-15629 (nagini).

SHADOW: the impl regions of model.py, copied verbatim below with the contract
calls (Requires/Ensures) stripped. The @Pure helpers (key_type/key_check/
key_collation/none_value/differs/emits_collation_clause) copy over as plain
functions. The impl regions use only dict writes and boolean operators, so the
shadow is the model's Python run directly -- no transliteration. There are no
@ContractOnly callees in this bundle.

ORACLES (the REAL patched repo code, per mapping.md section 1; the gate applies
patch.diff to /testbed before this script runs):

  (1) `reported_reference_parameters` <-> the real
      ``ForeignKey.db_parameters(connection)``. We build real model pairs (a
      CharField primary key carrying a db_collation, and a second model with a
      ForeignKey to it) and call the real method; the referenced column's own
      real ``db_parameters`` dict is the shadow's ``target_params`` input.

  (2) `references_need_rebuild` <-> the decision inside the real
      ``BaseDatabaseSchemaEditor._alter_field`` that re-derives columns
      referencing an altered column (and its sqlite3 mirror). The decision is
      a sub-expression of a large stateful method, so the REAL statements are
      EXTRACTED FROM THE RUNNING MODULE'S SOURCE AT RUNTIME via ast (the
      collation-lifting assignments plus the trigger expression), compiled,
      and executed against stub namespaces in which the surrounding guards the
      model declares out of scope (feature support, primary-key/unique-ness)
      are held satisfied. No decision text is hard-coded here: whatever the
      patched source computes is what the shadow is diffed against.

TYPE BRIDGE (mapping.md section 2): parameter values (type / check /
collation strings, or None) map to int identities through an interning table;
``None`` maps to ``none_value()`` (= 0), every distinct non-None value to a
distinct positive int. Only equality and dict membership are observed, so the
injective interning is a faithful bridge. A real ``db_parameters`` dict maps
to the model carrier ``Dict[int, int]`` via the token constants
key_type()/key_check()/key_collation(); a missing key stays absent.

INPUT DOMAIN:
  (1) requires ``key_collation() in target_params``; a CharField-PK target's
      real parameters always carry that key, and the script asserts it before
      lowering (a pair without it would simply not be Requires-satisfying).
  (2) has no precondition: any four identities qualify.

>= 1e5 Requires-satisfying inputs total: 6 boundary + 1200 fuzz real model
pairs for (1) (plus COLLATE-emission cross-checks on a subset via the real
``column_sql``), and an exhaustive small identity grid + 100000 fuzz tuples
for (2). Pinned fuzz seed: 156290.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import ast
import json
import os
import random
import sys
import tempfile
import types

SEED = 156290
N_FUZZ_PAIRS = 1200      # real model pairs for oracle (1)
N_FUZZ_TUPLES = 100000   # identity tuples for oracle (2)


# -----------------------------------------------------------------------------
# Django bootstrap (same pattern as axiom_check.py): the throwaway app holding
# dynamically-built models must be a REAL package on disk, importable BEFORE
# django.setup().
# -----------------------------------------------------------------------------
_APP_NAME = 'conf_check_15629'
_pkg_parent = tempfile.mkdtemp(prefix='confcheck15629_')
_pkg_dir = os.path.join(_pkg_parent, _APP_NAME)
os.makedirs(_pkg_dir, exist_ok=True)
with open(os.path.join(_pkg_dir, '__init__.py'), 'w') as _f:
    _f.write('')
with open(os.path.join(_pkg_dir, 'models.py'), 'w') as _f:
    _f.write('')
sys.path.insert(0, _pkg_parent)

import django  # noqa: E402
from django.conf import settings  # noqa: E402

if not settings.configured:
    settings.configure(
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3',
                               'NAME': ':memory:'}},
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'django.contrib.auth',
            _APP_NAME,
        ],
        USE_TZ=False,
    )

django.setup()

from django.db import connection, models  # noqa: E402
from django.db.backends.base import schema as base_schema  # noqa: E402
from django.db.backends.sqlite3 import schema as sqlite_schema  # noqa: E402


# -----------------------------------------------------------------------------
# SHADOW: pure helpers from model.py, contracts stripped (verbatim bodies)
# -----------------------------------------------------------------------------

def key_type():
    # Parameter-name token for the storage type.
    return 1


def key_check():
    # Parameter-name token for the column check.
    return 2


def key_collation():
    # Parameter-name token for the column collation.
    return 3


def none_value():
    # Sentinel value meaning "declared, but empty" (no type / no collation).
    return 0


def differs(before, after):
    # Whether a storage characteristic changed between the old and new shape.
    return before != after


def emits_collation_clause(params):
    return key_collation() in params and params[key_collation()] != none_value()


# -----------------------------------------------------------------------------
# SHADOW: the impl regions of model.py, verbatim, contract calls stripped
# -----------------------------------------------------------------------------

def reported_reference_parameters(target_params, own_type, own_check):
    result = {}
    result[key_type()] = own_type
    result[key_check()] = own_check
    result[key_collation()] = target_params[key_collation()]
    return result


def references_need_rebuild(old_type, new_type, old_collation, new_collation):
    return differs(old_type, new_type) or differs(old_collation, new_collation)


# -----------------------------------------------------------------------------
# Type bridge: identity interning (mapping.md section 2)
# -----------------------------------------------------------------------------

class Intern(object):
    """Injective map from real parameter values to int identities:
    None -> none_value() (0); every distinct non-None value -> a distinct
    positive int. Only equality / membership are observed by the model, so
    this is a faithful carrier."""

    def __init__(self):
        self._t = {}

    def __call__(self, v):
        if v is None:
            return none_value()
        if v not in self._t:
            self._t[v] = len(self._t) + 1
        return self._t[v]


def lower_params(intern, d):
    """Real db_parameters dict -> model carrier Dict[int, int]; a missing key
    stays absent (membership is observable)."""
    out = {}
    if 'type' in d:
        out[key_type()] = intern(d['type'])
    if 'check' in d:
        out[key_check()] = intern(d['check'])
    if 'collation' in d:
        out[key_collation()] = intern(d['collation'])
    # any unexpected key would make the carrier unfaithful; surface it
    for k in d:
        if k not in ('type', 'check', 'collation'):
            raise AssertionError("unbridgeable db_parameters key %r in %r"
                                 % (k, d))
    return out


# -----------------------------------------------------------------------------
# Oracle (1): real ForeignKey.db_parameters over real model pairs
# -----------------------------------------------------------------------------

_counter = [0]


def _make_pair(collation):
    """Build a (target, referrer) model pair: the target has a CharField PK
    with the given db_collation (possibly None); the referrer has a ForeignKey
    to it. Returns (fk_field, pk_field)."""
    _counter[0] += 1
    n = _counter[0]
    target_attrs = {
        '__module__': _APP_NAME + '.models',
        'Meta': type('Meta', (), {'app_label': _APP_NAME}),
        'id': models.CharField(primary_key=True, max_length=22,
                               db_collation=collation),
    }
    Target = type('ConfTarget%d' % n, (models.Model,), target_attrs)
    ref_attrs = {
        '__module__': _APP_NAME + '.models',
        'Meta': type('Meta', (), {'app_label': _APP_NAME}),
        'target': models.ForeignKey(Target, models.CASCADE),
    }
    Ref = type('ConfRef%d' % n, (models.Model,), ref_attrs)
    return Ref._meta.get_field('target'), Target._meta.get_field('id')


def check_fn1(collation, do_sql_check):
    """Diff the shadow against the real relational-field db_parameters on one
    real model pair. Returns an error string on disagreement, else None."""
    fk_field, pk_field = _make_pair(collation)
    target_real = pk_field.db_parameters(connection=connection)   # real callee
    observed = fk_field.db_parameters(connection=connection)      # REAL oracle

    intern = Intern()
    target_lo = lower_params(intern, target_real)
    # Requires: the referenced column reports a collation entry.
    if key_collation() not in target_lo:
        raise AssertionError(
            "target params lack a collation entry (not Requires-satisfying): %r"
            % (target_real,))
    # own type/check are R-refined inputs supplied by unchanged callees.
    own_type = intern(fk_field.db_type(connection=connection))
    own_check = intern(fk_field.db_check(connection=connection))

    shadow = reported_reference_parameters(target_lo, own_type, own_check)
    real_lo = lower_params(intern, observed)

    if shadow != real_lo:
        return ("DISAGREEMENT (reported_reference_parameters) on "
                "collation=%r:\n  target params (real) = %r\n"
                "  shadow (impl region, lowered) = %r\n"
                "  real db_parameters (lowered)  = %r\n"
                "  real db_parameters (raw)      = %r"
                % (collation, target_real, shadow, real_lo, observed))

    if do_sql_check:
        # consequence cross-check: the shadow's emission predicate must track
        # the real column SQL's COLLATE token.
        with connection.schema_editor(collect_sql=True) as editor:
            col_sql, _p = editor.column_sql(fk_field.model, fk_field)
        emits_real = (col_sql is not None) and ('COLLATE' in col_sql.upper())
        emits_shadow = emits_collation_clause(shadow)
        if emits_real != emits_shadow:
            return ("DISAGREEMENT (emits_collation_clause) on collation=%r:\n"
                    "  shadow predicate = %r\n"
                    "  real column SQL COLLATE presence = %r (sql=%r)"
                    % (collation, emits_shadow, emits_real, col_sql))
    return None


# -----------------------------------------------------------------------------
# Oracle (2): the real re-derive decision, extracted from the running module
# -----------------------------------------------------------------------------

def _fn_ast(fn):
    import inspect
    import textwrap
    src = textwrap.dedent(inspect.getsource(fn))
    return ast.parse(src).body[0]


def _assign_to(fn_node, name):
    """First statement in the function assigning to the given simple name."""
    for node in ast.walk(fn_node):
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            t = node.targets[0]
            if isinstance(t, ast.Name) and t.id == name:
                return node
    raise AssertionError("no assignment to %r found in real source" % name)


def _compile_stmts(stmts, tag):
    mod = ast.Module(body=[s for s in stmts], type_ignores=[])
    ast.fix_missing_locations(mod)
    return compile(mod, '<real:%s>' % tag, 'exec')


def _names_in(node):
    return set(n.id for n in ast.walk(node) if isinstance(n, ast.Name))


def build_base_oracle():
    """Compile, from the REAL base schema-editor source: the two collation
    lifts plus the re-derive trigger assignment. Returns a callable
    (old_type, new_type, old_db_params, new_db_params) -> bool with the
    out-of-scope guards (feature support, pk/unique) held satisfied."""
    fn_node = _fn_ast(base_schema.BaseDatabaseSchemaEditor._alter_field)
    stmts = [_assign_to(fn_node, 'old_collation'),
             _assign_to(fn_node, 'new_collation'),
             _assign_to(fn_node, 'drop_foreign_keys')]
    code = _compile_stmts(stmts, 'base')
    referenced = set()
    for s in stmts:
        referenced |= _names_in(s)

    field_stub = types.SimpleNamespace(primary_key=True, unique=True)
    self_stub = types.SimpleNamespace(connection=types.SimpleNamespace(
        features=types.SimpleNamespace(supports_foreign_keys=True)))

    def oracle(old_type, new_type, old_db_params, new_db_params):
        ns = {'self': self_stub,
              'old_field': field_stub, 'new_field': field_stub,
              'old_type': old_type, 'new_type': new_type,
              'old_db_params': old_db_params, 'new_db_params': new_db_params}
        missing = referenced - set(ns) - {'old_collation', 'new_collation',
                                          'drop_foreign_keys'}
        if missing:
            raise AssertionError(
                "real trigger references unstubbed names %r" % sorted(missing))
        exec(code, {}, ns)
        return bool(ns['drop_foreign_keys'])

    return oracle


def build_sqlite_oracle():
    """Same, for the mirrored sqlite guard: the collation lifts plus the
    rebuild-referencing-tables If test, with new_field.unique held True."""
    fn_node = _fn_ast(sqlite_schema.DatabaseSchemaEditor._alter_field)
    guard = None
    for node in ast.walk(fn_node):
        if isinstance(node, ast.If) and 'old_type' in _names_in(node.test):
            guard = node.test
            break
    if guard is None:
        raise AssertionError("no type-sensitive guard found in real sqlite "
                             "schema source")
    stmts = [_assign_to(fn_node, 'old_collation'),
             _assign_to(fn_node, 'new_collation'),
             ast.Assign(targets=[ast.Name(id='_verdict', ctx=ast.Store())],
                        value=guard)]
    code = _compile_stmts(stmts, 'sqlite')

    field_stub = types.SimpleNamespace(unique=True)

    def oracle(old_type, new_type, old_db_params, new_db_params):
        ns = {'new_field': field_stub,
              'old_type': old_type, 'new_type': new_type,
              'old_db_params': old_db_params, 'new_db_params': new_db_params}
        exec(code, {}, ns)
        return bool(ns['_verdict'])

    return oracle


def check_fn2(base_oracle, sqlite_oracle,
              old_type, new_type, old_coll, new_coll):
    """Diff the shadow decision against BOTH real extracted decisions on one
    identity tuple. The special marker _ABSENT means the params dict does not
    carry the collation key at all (real .get then yields None; the bridge
    maps that to none_value(), matching the model's input carrier)."""
    def params(coll):
        d = {'type': 'T'}
        if coll is not _ABSENT:
            d['collation'] = coll
        return d

    old_p, new_p = params(old_coll), params(new_coll)
    real_base = base_oracle(old_type, new_type, old_p, new_p)
    real_sqlite = sqlite_oracle(old_type, new_type, old_p, new_p)

    intern = Intern()
    shadow = references_need_rebuild(
        intern(old_type), intern(new_type),
        intern(old_p.get('collation')), intern(new_p.get('collation')))

    if shadow != real_base or shadow != real_sqlite:
        return ("DISAGREEMENT (references_need_rebuild) on "
                "old_type=%r new_type=%r old_collation=%r new_collation=%r:\n"
                "  shadow (impl region) = %r\n"
                "  real base decision   = %r\n"
                "  real sqlite decision = %r"
                % (old_type, new_type, old_coll, new_coll,
                   shadow, real_base, real_sqlite))
    return None


_ABSENT = object()


# -----------------------------------------------------------------------------
# driver
# -----------------------------------------------------------------------------

def main():
    rng = random.Random(SEED)
    checked = 0

    # ---- oracle (1): boundary collations on real model pairs ----------------
    boundary = [None, 'nocase', 'binary', 'utf8_bin', 'und-x-icu', 'C']
    for coll in boundary:
        err = check_fn1(coll, do_sql_check=True)
        if err:
            print(err)
            return 1
        checked += 1

    # ---- oracle (1): randomized fuzz over collation identities --------------
    named = ['nocase', 'binary', 'rtrim', 'utf8_bin', 'utf8mb4_unicode_ci',
             'C', 'POSIX', 'en-x-icu', 'sv-x-icu', 'da_DK', 'latin1_general_cs']
    charset = 'abcdefghijklmnopqrstuvwxyz0123456789_'
    for i in range(N_FUZZ_PAIRS):
        r = rng.random()
        if r < 0.15:
            coll = None
        elif r < 0.6:
            coll = rng.choice(named)
        else:
            coll = ''.join(rng.choice(charset)
                           for _ in range(rng.randint(1, 24)))
        err = check_fn1(coll, do_sql_check=(i < 200))
        if err:
            print(err)
            return 1
        checked += 1

    # ---- oracle (2): compile the real decisions once ------------------------
    base_oracle = build_base_oracle()
    sqlite_oracle = build_sqlite_oracle()

    # exhaustive small grid: 4 type identities x 5 collation shapes squared
    # (including the absent-key shape and the equal/unequal boundary cases)
    types_pool = ['t0', 't1', 'varchar(22)', 'integer']
    colls_pool = [None, _ABSENT, 'c0', 'c1', 'nocase']
    for ot in types_pool:
        for nt in types_pool:
            for oc in colls_pool:
                for nc in colls_pool:
                    err = check_fn2(base_oracle, sqlite_oracle, ot, nt, oc, nc)
                    if err:
                        print(err)
                        return 1
                    checked += 1

    # randomized fuzz over identity tuples (pinned seed continues)
    fuzz_types = ['t0', 't1', 't2', 'varchar(10)', 'varchar(22)', 'integer',
                  'text', 'char(1)']
    fuzz_colls = [None, _ABSENT, 'c0', 'c1', 'c2', 'nocase', 'binary',
                  'utf8_bin', 'POSIX', '']
    for _ in range(N_FUZZ_TUPLES):
        err = check_fn2(base_oracle, sqlite_oracle,
                        rng.choice(fuzz_types), rng.choice(fuzz_types),
                        rng.choice(fuzz_colls), rng.choice(fuzz_colls))
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl regions == real patched code on %d inputs "
          "(%d boundary + %d fuzz real model pairs for the reported reference "
          "parameters incl. COLLATE-emission tracking; %d-cell identity grid "
          "+ %d fuzz tuples for the re-derive decision against the extracted "
          "real base + sqlite triggers; seed %d); 0 disagreements."
          % (checked, len(boundary), N_FUZZ_PAIRS,
             len(types_pool) ** 2 * len(colls_pool) ** 2, N_FUZZ_TUPLES, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == '__main__':
    sys.exit(main())
