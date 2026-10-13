#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-11265 (nagini).

SHADOW: the impl regions of model.py's two contracted functions, copied
verbatim below with the contract calls (Requires/Ensures/Invariant/Assert)
stripped. The @Pure helpers (LOUTER/INNER/may_trim_leading_join) copy over as
plain functions. There are no @ContractOnly callees in this bundle.

ORACLE: the REAL patched repo methods per mapping.md —
`django.db.models.sql.query.Query.split_exclude` (site 1) and
`Query.trim_start` (site 2), driven end-to-end through the public queryset
API: an annotated-relation-alias queryset excluded over an N-to-many path.
The gate applies patch.diff to /testbed before this script runs;
PYTHONPATH=/testbed makes the patched ORM importable. A spy on
`Query.add_filter` captures the freshly built inner subquery (the only
add_filter call in these code paths runs on that subquery).

Type bridge (mapping.md section 2):
  * site 1 — the outer query's declared-relation-alias registry maps to
    List[int]: alias name 'fr_<t>' <-> token t, registry insertion order <->
    list order. The real observation is the inner subquery's own registry
    (its declared-alias mapping) read back as a token list, plus the fact
    that the referenced alias resolved (the exclusion built without a field
    resolution error).
  * site 2 — the inner subquery's leading join maps to (join_type token,
    is_filtered_relation bool): a relation-alias join carries a
    relation-specific filter; an isnull-style lookup makes the leading join
    left-outer, a value lookup keeps it inner. Both facts are fixed by
    scenario construction and cross-checked against the join metadata the
    built subquery actually records whenever the leading join survives.
    Filter-condition tokens map to unique marker strings planted in the
    relation condition (leading) and the exclusion lookup (downstream); the
    real retained-condition set is read off the compiled subquery SQL — the
    leading condition is in effect iff its marker (or, for a plain join, the
    join itself) appears in the FROM clause, and the downstream condition
    shows in the WHERE clause.

Input domain: site 1's precondition requires the referenced alias to be
declared on the outer query — satisfied by construction (the exclusion always
targets one of the annotated aliases). Site 2's preconditions are pure access
permissions. Scenarios vary registry size (1-5 aliases), referenced position,
all four leading-join decision cells (inner/left-outer x plain/relation-
filtered), and the downstream lookup shape.

>= 1e5 Requires-satisfying inputs: boundary scenarios + 100000 fuzz
scenarios (each contributing a site-2 input and, when annotated, a site-1
input). Pinned fuzz seed: 11265.

Exit 0 iff zero disagreements; on disagreement prints the scenario and both
outputs and exits 1. stdlib + Django (the repo under test) only; the
container is Python 3.6.
"""
import json
import random
import sys
import types

SEED = 11265
N_FUZZ = 100000

# --- repo under test (patched /testbed) ---------------------------------------

import django
from django.conf import settings

# a minimal in-memory app package so the test models are installable
_app = types.ModuleType('confch')
_app.__path__ = ['/tmp']
sys.modules['confch'] = _app

if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.contenttypes', 'confch'],
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3',
                               'NAME': ':memory:'}},
    )
django.setup()

from django.db import models                       # noqa: E402
from django.db.models import Q, FilteredRelation   # noqa: E402
from django.db.models.sql.query import Query       # noqa: E402


class Author(models.Model):
    name = models.CharField(max_length=50)

    class Meta:
        app_label = 'confch'


class Book(models.Model):
    title = models.CharField(max_length=50)
    author = models.ForeignKey(Author, models.CASCADE, related_name='book')

    class Meta:
        app_label = 'confch'


# --- pure helpers from model.py, contracts stripped ---------------------------

def LOUTER_TOK():
    return 1


def INNER_TOK():
    return 0


def may_trim_leading_join(join_type, is_filtered_relation):
    return join_type != LOUTER_TOK() and not is_filtered_relation


# --- the impl regions of model.py, verbatim, contract calls stripped ----------

def propagate_relation_registry(outer_relations, referenced_alias):
    result = []
    i = 0
    while i < len(outer_relations):
        result = result + [outer_relations[i]]
        i = i + 1
    return result


def subquery_retained_filters(join_type, is_filtered_relation,
                              leading_filter, other_filters):
    result = []
    if not may_trim_leading_join(join_type, is_filtered_relation):
        result = result + [leading_filter]
    i = 0
    while i < len(other_filters):
        result = result + [other_filters[i]]
        i = i + 1
    return result


# --- spy: capture the inner subquery the exclusion builds ---------------------

_captured = []
_orig_add_filter = Query.add_filter


def _spy_add_filter(self, *args, **kwargs):
    _captured.append(self)
    return _orig_add_filter(self, *args, **kwargs)


Query.add_filter = _spy_add_filter

REAL_LOUTER_STR = 'LEFT OUTER JOIN'


def run_scenario(alias_tokens, ref_index, left_outer, lead_markers,
                 down_marker):
    """Build one exclusion queryset and diff both shadows against the reals.

    alias_tokens: registry tokens (may be empty => plain, non-annotated path)
    ref_index:    which alias the exclusion references (ignored when plain)
    left_outer:   isnull-style lookup (left-outer leading join) vs value lookup
    lead_markers: one unique marker string per alias (relation conditions)
    down_marker:  unique marker string for the downstream condition
    Returns an error string on any disagreement, else None.
    """
    annotated = bool(alias_tokens)
    annotations = {}
    for tok, marker in zip(alias_tokens, lead_markers):
        annotations['fr_%d' % tok] = FilteredRelation(
            'book', condition=Q(book__title=marker))

    if annotated:
        target = 'fr_%d' % alias_tokens[ref_index]
    else:
        target = 'book'

    if left_outer:
        kwargs = {target + '__title__isnull': True}
    else:
        kwargs = {target + '__title': down_marker}

    qs = Author.objects.all()
    if annotated:
        qs = qs.annotate(**annotations)
    del _captured[:]
    try:
        qs = qs.exclude(**kwargs)
        str(qs.query)  # force the outer compile (subquery built eagerly above)
    except Exception as e:
        return ('SCENARIO ERROR tokens=%r ref=%r left_outer=%r: %s: %s'
                % (alias_tokens, ref_index, left_outer, type(e).__name__, e))
    if len(_captured) != 1:
        return ('SPY ERROR tokens=%r: expected 1 inner query, saw %d'
                % (alias_tokens, len(_captured)))
    inner = _captured[0]

    # ---- site 1: registry propagation (annotated scenarios only) ----------
    if annotated:
        name_to_tok = dict(('fr_%d' % t, t) for t in alias_tokens)
        real_registry = [name_to_tok[n] for n in inner._filtered_relations]
        shadow_registry = propagate_relation_registry(
            list(alias_tokens), alias_tokens[ref_index])
        if shadow_registry != real_registry:
            return ('DISAGREEMENT site1\n  tokens=%r ref_index=%d\n'
                    '  shadow=%r\n  real=%r'
                    % (alias_tokens, ref_index, shadow_registry,
                       real_registry))
        if alias_tokens[ref_index] not in real_registry:
            return ('DISAGREEMENT site1 (referenced alias unresolvable)\n'
                    '  tokens=%r ref_index=%d real=%r'
                    % (alias_tokens, ref_index, real_registry))

    # ---- site 2: leading-join condition retention --------------------------
    sql, params = inner.get_compiler('default').as_sql()
    inlined = sql % tuple(params)
    if ' WHERE ' not in inlined:
        return 'SITE2 ERROR: subquery has no WHERE clause: %r' % inlined
    from_part, where_part = inlined.split(' WHERE ', 1)

    join_tok = LOUTER_TOK() if left_outer else INNER_TOK()
    is_filtered = annotated
    lead_tok = 777001
    down_tok = 777002
    shadow = subquery_retained_filters(join_tok, is_filtered, lead_tok,
                                       [down_tok])

    if annotated:
        # leading condition in effect iff its marker sits in the FROM clause
        lead_marker = lead_markers[ref_index]
        real_lead = lead_marker in from_part
        if lead_marker in where_part:
            return ('SITE2 ERROR: relation condition leaked into WHERE: %r'
                    % inlined)
    else:
        # plain join: the leading join is in effect iff it survived (a JOIN
        # clause remains in the subquery's FROM)
        real_lead = ' JOIN ' in from_part

    if left_outer:
        real_down = 'IS NULL' in where_part
    else:
        real_down = down_marker in where_part

    real = ([lead_tok] if real_lead else []) + ([down_tok] if real_down else [])
    if shadow != real:
        return ('DISAGREEMENT site2\n  tokens=%r left_outer=%r annotated=%r\n'
                '  shadow=%r real=%r\n  subquery=%r'
                % (alias_tokens, left_outer, annotated, shadow, real, inlined))

    # cross-check the scenario-fixed join classification against the join
    # metadata the built subquery records, whenever the leading join survived
    entries = list(inner.alias_map.values())
    if real_lead:
        if len(entries) < 2:
            return 'SITE2 ERROR: leading join in effect but no join recorded'
        first_join = entries[1]
        jt = getattr(first_join, 'join_type', None)
        fr = bool(getattr(first_join, 'filtered_relation', None))
        if (jt == REAL_LOUTER_STR) != left_outer or fr != is_filtered:
            return ('BRIDGE ERROR: join metadata %r/%r does not match the '
                    'scenario classification left_outer=%r filtered=%r'
                    % (jt, fr, left_outer, is_filtered))
    return None


def main():
    checked = 0

    def mark(tag, n):
        return 'zzmk_%s_%d' % (tag, n)

    # --- boundary scenarios: every decision cell, registry shapes ----------
    boundary = [
        # (alias_tokens, ref_index, left_outer)
        ([3], 0, False),          # inner + relation-filtered (the bug cell)
        ([3], 0, True),           # left-outer + relation-filtered
        ([], 0, False),           # inner + plain (trimmed)
        ([], 0, True),            # left-outer + plain (kept)
        ([1, 2, 3], 0, False),    # referenced first
        ([1, 2, 3], 1, False),    # referenced middle
        ([1, 2, 3], 2, False),    # referenced last
        ([1, 2, 3], 1, True),
        ([9, 5, 7, 2, 4], 3, False),   # unordered tokens, larger registry
        ([9, 5, 7, 2, 4], 0, True),
        ([100], 0, False),
        ([0], 0, False),          # token value 0
    ]
    n = 0
    for alias_tokens, ref_index, left_outer in boundary:
        n += 1
        leads = [mark('l%d' % i, n) for i in range(len(alias_tokens))]
        err = run_scenario(alias_tokens, ref_index, left_outer, leads,
                           mark('d', n))
        if err:
            print(err)
            return 1
        checked += 2 if alias_tokens else 1

    # --- fuzz ---------------------------------------------------------------
    rng = random.Random(SEED)
    for it in range(N_FUZZ):
        n += 1
        annotated = rng.random() < 0.7
        if annotated:
            size = rng.randint(1, 5)
            alias_tokens = rng.sample(range(0, 10000), size)
            ref_index = rng.randrange(size)
        else:
            alias_tokens, ref_index = [], 0
        left_outer = rng.random() < 0.4
        leads = [mark('l%d' % i, n) for i in range(len(alias_tokens))]
        err = run_scenario(alias_tokens, ref_index, left_outer, leads,
                           mark('d', n))
        if err:
            print(err)
            return 1
        checked += 2 if annotated else 1

    print('G-CONF OK: shadow impls == real registry propagation + '
          'leading-join retention on %d inputs (%d boundary + %d fuzz '
          'scenarios, seed %d).' % (checked, len(boundary), N_FUZZ, SEED))
    print(json.dumps({'checked': checked, 'disagreements': 0, 'seed': SEED,
                      'shadow': 'direct (contract-stripped impl region)'}))
    return 0


if __name__ == '__main__':
    sys.exit(main())
