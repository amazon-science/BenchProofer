#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-14351 (nagini).

SHADOW: the impl region of model.py's ``membership_group_by_cols``, copied
VERBATIM below with only the contract calls (Requires / Ensures / Invariant)
stripped.  The three @ContractOnly callees of the axioms region are backed by
the REAL repo callees they are bound to in mapping.md section 1:

  * ``nested_group_by_cols``  -> ``self.rhs.get_group_by_cols()`` on the real
    ``Query``, with the query's contribution abstracted — exactly as mapping.md
    section 2 documents — as the sequence of SELECT sub-columns the query
    renders (``compiler.select`` after ``pre_sql_setup``);
  * ``clear_output_columns``  -> ``Query.clear_select_clause()``;
  * ``add_identity_column``   -> ``Query.add_fields(['pk'])``.

The shadow's ``NestedQuery`` shim therefore wraps its OWN ``Query.clone()`` of
the case's rhs query, so shadow and oracle each mutate an independent real
query and their post-states can be compared as well.

ORACLE: the REAL patched repo function per mapping.md section 1 —
``django.db.models.lookups.In.get_group_by_cols`` (called with no alias, the
single contracted behaviour).  The gate applies patch.diff to /testbed and
sets PYTHONPATH=/testbed before this script runs, so ``import django``
resolves to the patched module.  Each probe builds a fresh ``In`` lookup from
a real lhs expression and a real rhs (a ``Query`` or a literal collection)
and calls the method.

TYPE BRIDGE (mapping.md section 2): grouping columns are opaque ``int``
identifiers.  A per-case intern table maps each real column identity — a
``Col``'s (alias, target column), a rendered annotation's alias, or an
opaque non-Col expression — to a fresh ``int``; both sides intern through
the same table, so identifier equality mirrors real column identity exactly.
A ``Query`` element in a grouping-columns list lowers to the identifiers of
its rendered SELECT sub-columns (the documented carrier of ``explicit_cols``
/ ``default_cols``).  ``lhs_cols`` is the interned lowering of
``lhs.get_group_by_cols()``; ``rhs_is_query`` is
``hasattr(rhs, 'get_group_by_cols')``.

INPUT PLAN (>= 1e5 Requires-satisfying inputs): boundary crossings of model
shapes (0/1/2/6 declared fields) x lhs shapes (a plain column, a literal
Value contributing no columns, aggregate and non-aggregate compound
expressions) x rhs shapes (field-less query, filtered field-less query,
``none()`` query, plain-annotate field-less query, ``values(...)`` in random
subsets and orders, ``values()``, ``values('pk')``, ``values_list(...)``,
``values(...).annotate(...)``, and literal lists/tuples including the empty
collection), same-model and cross-model — plus 100000 random fuzz cases over
the same recipe space.  Pinned fuzz seed: 14351.

Checked per probe: the full result sequence, and (for query rhs) the rhs
post-state — ``has_select_fields`` plus the rendered SELECT sub-columns of
the shadow's clone vs the oracle's query.  Exit 0 iff zero disagreements; on
disagreement prints the input and both outputs and exits 1.  stdlib + django
(the framework under test) only.
"""
import json
import random
import sys

SEED = 14351
N_FUZZ = 100000


# --- Django setup (no database access is ever performed; queries are only
# --- built and rendered, never executed) --------------------------------------

from django.conf import settings  # noqa: E402

if not settings.configured:
    settings.configure(
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
    )

import django  # noqa: E402

django.setup()

from django.db import models  # noqa: E402
from django.db.models import Count, F, Value  # noqa: E402
from django.db.models.lookups import In  # noqa: E402
from django.db.models.sql.query import Query as RealQuery  # noqa: E402


# Scenario models: 0 / 1 / 2 / 6 declared fields (pk is the implicit ``id``).
# Piggyback on an installed app so no throwaway app module is needed.

class ConfM0(models.Model):
    class Meta:
        app_label = "contenttypes"


class ConfM1(models.Model):
    f1 = models.IntegerField(default=0)

    class Meta:
        app_label = "contenttypes"


class ConfM2(models.Model):
    name = models.CharField(max_length=50)
    f1 = models.IntegerField(default=0)

    class Meta:
        app_label = "contenttypes"


class ConfM6(models.Model):
    name = models.CharField(max_length=50)
    f1 = models.IntegerField(default=0)
    f2 = models.IntegerField(default=0)
    f3 = models.IntegerField(default=0)
    f4 = models.IntegerField(default=0)
    f5 = models.IntegerField(default=0)

    class Meta:
        app_label = "contenttypes"


MODELS = [ConfM0, ConfM1, ConfM2, ConfM6]
FIELDS = {
    ConfM0: [],
    ConfM1: ["f1"],
    ConfM2: ["name", "f1"],
    ConfM6: ["name", "f1", "f2", "f3", "f4", "f5"],
}
INT_FIELDS = {
    ConfM0: [],
    ConfM1: ["f1"],
    ConfM2: ["f1"],
    ConfM6: ["f1", "f2", "f3", "f4", "f5"],
}


# --- PSeq shim: immutable sequence with the operations the model uses ---------

class PSeq(object):
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def take(self, n):
        return PSeq._wrap(self._t[:n])

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

    def __add__(self, other):
        return PSeq._wrap(self._t + other._t)

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]


# --- column-identity bridge ----------------------------------------------------

class Intern(object):
    """Per-case bijection: real column identity -> opaque int identifier."""

    def __init__(self):
        self._map = {}

    def __call__(self, key):
        if key not in self._map:
            self._map[key] = len(self._map) + 1
        return self._map[key]


def _col_key(expr, alias_hint=None):
    """Canonical identity of one real grouping/select column.

    A ``Col`` is identified by its (table alias, target db column) — equal
    across independent clones of the same query.  A rendered annotation is
    identified by its select alias.  Any other expression object is opaque
    and identified by object id (such objects are shared, not cloned,
    between the two sides of a probe).
    """
    target = getattr(expr, "target", None)
    if target is not None:
        return ("col", getattr(expr, "alias", None), target.column)
    if alias_hint:
        return ("anno", alias_hint)
    return ("obj", id(expr))


def _rendered_sel_keys(query):
    """The identities of the SELECT sub-columns the query renders — the
    documented carrier of a query's grouping-columns contribution."""
    compiler = query.get_compiler(using="default")
    compiler.pre_sql_setup()
    return [_col_key(entry[0], entry[2]) for entry in compiler.select]


def _lower_group_by(elements, intern):
    """Lower a real grouping-columns list to opaque int identifiers: a Query
    element contributes its rendered SELECT sub-columns; anything else is one
    column identity."""
    out = []
    for el in elements:
        if isinstance(el, RealQuery):
            out.extend(intern(k) for k in _rendered_sel_keys(el))
        else:
            out.append(intern(_col_key(el)))
    return out


# --- @ContractOnly callees, backed by the REAL repo callees (mapping.md §3) ---

class NestedQuery(object):
    """The model's NestedQuery facets realized over a REAL ``Query``:
    ``has_fields`` reads the real ``has_select_fields`` property;
    ``explicit_cols`` / ``default_cols`` are the interned rendered SELECT
    sub-column identities; ``pk_col`` is the identity column's identifier."""

    def __init__(self, query, intern, default_keys, pk_key):
        self._q = query
        self._intern = intern
        self.default_cols = PSeq._wrap(intern(k) for k in default_keys)
        self.pk_col = intern(pk_key)

    @property
    def has_fields(self):
        return bool(self._q.has_select_fields)

    @property
    def explicit_cols(self):
        if not self._q.has_select_fields:
            return PSeq()   # facet unobservable while field-less (ghost read)
        return PSeq._wrap(self._intern(k) for k in _rendered_sel_keys(self._q))


def nested_group_by_cols(q):
    # the REAL unchanged reader on the real query, lowered per the bridge
    return PSeq._wrap(_lower_group_by(q._q.get_group_by_cols(), q._intern))


def clear_output_columns(q):
    q._q.clear_select_clause()          # the REAL repo primitive


def add_identity_column(q):
    q._q.add_fields(['pk'])             # the REAL repo primitive


# --- impl region of model.py, verbatim with contract calls stripped -----------

def membership_group_by_cols(lhs_cols, rhs_is_query, rhs):
    orig_default = rhs.default_cols  # type: PSeq[int]
    orig_explicit = rhs.explicit_cols  # type: PSeq[int]
    orig_had_fields = rhs.has_fields  # type: bool
    orig_pk = rhs.pk_col  # type: int
    cols = list(lhs_cols)  # type: List[int]
    if rhs_is_query:
        if not rhs.has_fields:
            clear_output_columns(rhs)
            add_identity_column(rhs)
        rhs_cols = nested_group_by_cols(rhs)  # type: PSeq[int]
        i = 0
        while i < len(rhs_cols):
            cols.append(rhs_cols[i])
            i = i + 1
    return cols
    # (orig_* are the impl's ghost snapshots; unused once contracts are
    # stripped but kept verbatim)


# --- input recipes --------------------------------------------------------------

_DEFAULT_KEYS = {}
_PK_KEY = {}
_LHS_COLS = {}
_LHS_AGG = {}
_LHS_COMB = {}


def _prepare_shapes():
    for M in MODELS:
        _DEFAULT_KEYS[M] = _rendered_sel_keys(M.objects.all().query)
        _PK_KEY[M] = ("col", M._meta.db_table, M._meta.pk.column)
        _LHS_COLS[M] = [
            M._meta.pk.get_col(M._meta.db_table)
        ] + [
            M._meta.get_field(f).get_col(M._meta.db_table) for f in FIELDS[M]
        ]
        ints = INT_FIELDS[M]
        if ints:
            _LHS_AGG[M] = M.objects.annotate(
                c=Count(ints[0]) + F(ints[-1])).query.annotations["c"]
            _LHS_COMB[M] = M.objects.annotate(
                c=F(ints[0]) + Value(7)).query.annotations["c"]


def _rhs_query(M, kind, rng):
    """Build a fresh rhs Query of the given shape."""
    fields = FIELDS[M]
    ints = INT_FIELDS[M]
    if kind == "all":
        return M.objects.all().query
    if kind == "filter":
        if ints:
            return M.objects.filter(**{ints[0] + "__gt": rng.randint(-5, 5)}).query
        return M.objects.filter(pk__gt=rng.randint(-5, 5)).query
    if kind == "none":
        return M.objects.none().query
    if kind == "annotate_plain":
        f = ints[0] if ints else "pk"
        return M.objects.annotate(c=Count(f)).query
    if kind == "values_subset":
        pool = ["pk"] + fields
        n = rng.randint(1, len(pool))
        chosen = rng.sample(pool, n)
        return M.objects.values(*chosen).query
    if kind == "values_all":
        return M.objects.values().query
    if kind == "values_pk":
        return M.objects.values("pk").query
    if kind == "values_list":
        pool = ["pk"] + fields
        n = rng.randint(1, len(pool))
        chosen = rng.sample(pool, n)
        return M.objects.values_list(*chosen).query
    if kind == "values_annotate":
        f = fields[0] if fields else "pk"
        g = ints[0] if ints else "pk"
        return M.objects.values(f).annotate(cnt=Count(g)).query
    raise AssertionError(kind)


QUERY_RHS_KINDS = ["all", "filter", "none", "annotate_plain", "values_subset",
                   "values_all", "values_pk", "values_list", "values_annotate"]


def _lhs_choices(M):
    out = list(_LHS_COLS[M])
    out.append(Value(3))
    if M in _LHS_AGG:
        out.append(_LHS_AGG[M])
        out.append(_LHS_COMB[M])
    return out


# --- one differential probe -----------------------------------------------------

def run_probe(lhs, rhs_real, describe):
    """Run shadow and oracle on one (lhs, rhs) case; return an error string on
    disagreement, else None."""
    intern = Intern()
    rhs_is_query = hasattr(rhs_real, "get_group_by_cols")

    # bridge the lhs contribution (read-only on both sides)
    lhs_cols = _lower_group_by(lhs.get_group_by_cols(), intern)

    # shadow side: its OWN real-query clone behind the NestedQuery shim
    if rhs_is_query:
        M = rhs_real.model
        shadow_q = rhs_real.clone()
    else:
        # a literal collection: the branch is untaken; supply a fresh
        # field-less query so the shim's facet reads are well-defined
        M = ConfM2
        shadow_q = ConfM2.objects.all().query
    nq = NestedQuery(shadow_q, intern, _DEFAULT_KEYS[M], _PK_KEY[M])
    pre_fields = nq.has_fields
    shadow_out = membership_group_by_cols(lhs_cols, rhs_is_query, nq)

    # oracle side: the real patched method on the real objects
    lookup = In(lhs, rhs_real)
    real_raw = lookup.get_group_by_cols()
    real_out = _lower_group_by(real_raw, intern)

    if shadow_out != real_out:
        return ("DISAGREEMENT (result) on %s:\n  shadow = %r\n  real   = %r\n"
                "  (lhs_cols=%r, rhs_is_query=%r)"
                % (describe, shadow_out, real_out, lhs_cols, rhs_is_query))

    if rhs_is_query:
        # post-state: both sides mutated (or preserved) their own real query
        s_has, r_has = shadow_q.has_select_fields, rhs_real.has_select_fields
        if bool(s_has) != bool(r_has):
            return ("DISAGREEMENT (post-state has_select_fields) on %s:\n"
                    "  shadow = %r\n  real   = %r" % (describe, s_has, r_has))
        s_sel = _rendered_sel_keys(shadow_q)
        r_sel = _rendered_sel_keys(rhs_real)
        if s_sel != r_sel:
            return ("DISAGREEMENT (post-state select) on %s:\n"
                    "  shadow = %r\n  real   = %r" % (describe, s_sel, r_sel))
    else:
        # internal check: the untaken branch must leave the dummy untouched
        if nq.has_fields != pre_fields:
            return ("INTERNAL: literal-rhs probe mutated the shadow dummy "
                    "on %s" % describe)
    return None


# --- driver ---------------------------------------------------------------------

def boundary_cases():
    """Every model x lhs shape x rhs recipe crossing, plus literal rhs."""
    cases = []
    for M in MODELS:
        for lhs in _lhs_choices(M):
            for kind in QUERY_RHS_KINDS:
                for M_rhs in (M, ConfM6 if M is not ConfM6 else ConfM1):
                    cases.append((lhs, ("query", M_rhs, kind)))
            for lit in ([], [1], [1, 2, 3], (5,), (0, -1, 2, 3, 4)):
                cases.append((lhs, ("literal", None, lit)))
    return cases


def main():
    _prepare_shapes()
    rng = random.Random(SEED)

    checked = 0

    def run_one(lhs, rhs_spec):
        tag, M_rhs, payload = rhs_spec
        if tag == "query":
            rhs_real = _rhs_query(M_rhs, payload, rng)
            desc = ("lhs=%s rhs=%s(%s)"
                    % (type(lhs).__name__, M_rhs.__name__, payload))
        else:
            rhs_real = payload
            desc = "lhs=%s rhs=literal %r" % (type(lhs).__name__, payload)
        return run_probe(lhs, rhs_real, desc)

    for lhs, rhs_spec in boundary_cases():
        err = run_one(lhs, rhs_spec)
        if err:
            print(err)
            return 1
        checked += 1

    for _ in range(N_FUZZ):
        M_lhs = rng.choice(MODELS)
        lhs = rng.choice(_lhs_choices(M_lhs))
        if rng.random() < 0.8:
            M_rhs = rng.choice(MODELS)
            rhs_spec = ("query", M_rhs, rng.choice(QUERY_RHS_KINDS))
        else:
            n = rng.randint(0, 5)
            lit = [rng.randint(-100, 100) for _ in range(n)]
            rhs_spec = ("literal", None, tuple(lit) if rng.random() < 0.3 else lit)
        err = run_one(lhs, rhs_spec)
        if err:
            print(err)
            return 1
        checked += 1

    print("PASS: shadow impl == real patched In.get_group_by_cols on %d "
          "inputs (%d boundary crossings + %d fuzz; result sequences and rhs "
          "post-states agree); pinned seed %d"
          % (checked, checked - N_FUZZ, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region; "
                                "@ContractOnly callees delegated to the real "
                                "Query primitives)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
