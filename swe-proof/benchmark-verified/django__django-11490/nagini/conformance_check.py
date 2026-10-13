#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-11490 (nagini).

SHADOW: the impl regions of model.py, copied VERBATIM below with only the
contract calls (Requires / Ensures / Invariant / Assert / MustTerminate)
stripped: the minimal ``Query`` carrier class, the two deep models
``detached_copy`` / ``with_columns`` (A-references — they have real impl
regions, not @ContractOnly axioms, so they shadow directly), and the modelled
changed code ``columns_for_subquery``. The pure region is NOT part of the impl
and is not shadowed: every ``@Pure`` function (``kept_leading`` /
``kept_trailing`` / ``own_columns``) appears only inside the stripped contract
lines, so no PSeq shim is needed.

ORACLE: the REAL patched repo code the model models per mapping.md section 1
— the column-setting branch of ``SQLCompiler.get_combinator_sql``
(django/db/models/sql/compiler.py), reached when a component sub-query of a
compound query has no column list of its own and the outer query restricts
the columns. The gate applies patch.diff to /testbed and sets
PYTHONPATH=/testbed before this script runs, so imports resolve to the
patched module. Each probe builds ONE shared component ``Query`` (empty
``values_select``; a chosen family of leading derived columns realized as
``extra`` select entries and of trailing derived columns realized as
``annotations``; its accumulated state realized as a WHERE filter whose
parameter is the probe's state token), then compiles it as part of a
compound query MULTIPLE times with per-compilation outer column lists —
the reuse-across-compilations scenario the behaviour is about. Per
compilation the oracle observes (a) the column names rendered into the
component SELECT, in order, (b) the bound parameter list (the carried
accumulated state), and (c) the shared query's post-state (its
``values_select``, both of its derived-column families and its WHERE
parameter must all be untouched).

TYPE BRIDGE (mapping.md section 2): the model carrier for a column list is
``List[int]`` of column codes; code k is realized as the name ``f<k>`` on a
10-column model. WHICH family a code belongs to is a property of the query,
not of the code: on a given component, a code in ``leading`` is realized as
an ``extra`` select entry aliased ``f<k>``, a code in ``trailing`` as an
annotation aliased ``f<k>``, and any other code as the plain column
``f<k>``. Aliasing the derived columns onto real column names keeps every
generated request inside the callee's domain (a requested name classified as
one of the component's OWN columns must be a column the component's table
actually has). A component sub-query renders leading derived columns first,
then its own columns, then trailing ones, so the rendered name list is the
concatenation of the shadow result's ``leading``, ``columns`` and
``trailing``. The opaque ``state`` token (mapping.md section 1: the
accumulated row restriction together with the DEFINITIONS of the derived
columns, equal tokens <-> observably-equal state) is realized as the WHERE
filter's integer bound parameter: a compilation whose working object carries
the shared query's state renders exactly that parameter; a blank-slate
working object would drop it. Correspondences checked per compilation:
rendered SELECT names == bridge of (shadow leading ++ columns ++ trailing);
bound params == [shadow result's ``state``]; the shared query's
``values_select`` == bridge of shadow ``cached.columns`` (stays empty), its
``extra_select`` / ``annotation_select`` keys == bridge of shadow
``cached.leading`` / ``cached.trailing`` (stay un-narrowed) and its WHERE
parameter == shadow ``cached.state`` (unchanged).

DOMAIN: the modelled branch is entered only for a component with no column
list of its own and a non-empty outer list (the model's preconditions
``len(cached.columns) == 0`` / ``len(outer_select) > 0``), so generation
stays inside that domain: every probe starts from an empty shared list and
every outer list is non-empty. The outer query is shaped so that the list the
real branch passes down — ``(*extra_select, *values_select,
*annotation_select)`` of the outer — is exactly the probe's chosen list.

INPUT PLAN (>= 1e5 Requires-satisfying inputs, one per compilation):
boundary probes over the cross product of component derived families (none
at all — the callee's shortcut path — leading-only, trailing-only, both,
several of each in and out of column order, a code exposed by BOTH families,
a wide leading family, a wide trailing family) x chosen lists (single plain
column, duplicated columns, the full and reversed column range, a leading
derived column, a trailing one, one of each, groups out of column order, a
wide own part, a long repeating list, every code derived but one) x extreme
and zero state tokens, each compiled as an a->b->a reuse chain so a
compilation is re-checked after a DIFFERENT one; plus 34000 random fuzz
probes of three compilations each over random tokens, random derived
families and random chosen lists with duplicates (>= 100000 compilation
checks total). Pinned fuzz seed: 11490. Exit 0 iff zero disagreements; on
disagreement prints the input and both observations and exits 1. stdlib only.
"""
import json
import random
import sys
from typing import List

SEED = 11490
N_FUZZ = 34000
N_COLS = 10


# --- impl regions of model.py, verbatim with contract calls stripped ----------

class Query:
    def __init__(self, columns: List[int], leading: List[int],
                 trailing: List[int], state: int) -> None:
        self.columns = columns
        self.leading = leading
        self.trailing = trailing
        self.state = state


def detached_copy(q: Query) -> Query:
    copied = []  # type: List[int]
    i = 0
    while i < len(q.columns):
        copied.append(q.columns[i])
        i = i + 1

    front = []  # type: List[int]
    j = 0
    while j < len(q.leading):
        front.append(q.leading[j])
        j = j + 1

    back = []  # type: List[int]
    k = 0
    while k < len(q.trailing):
        back.append(q.trailing[k])
        k = k + 1

    result = Query(copied, front, back, q.state)
    return result


def with_columns(q: Query, fields: List[int]) -> None:
    kept_front = []  # type: List[int]
    i = 0
    while i < len(q.leading):
        name = q.leading[i]
        if name in fields:
            kept_front.append(name)
        i = i + 1

    kept_back = []  # type: List[int]
    j = 0
    while j < len(q.trailing):
        later = q.trailing[j]
        if later in fields and not (later in q.leading):
            kept_back.append(later)
        j = j + 1

    chosen = []  # type: List[int]
    k = 0
    while k < len(fields):
        wanted = fields[k]
        if not (wanted in q.leading) and not (wanted in q.trailing):
            chosen.append(wanted)
        k = k + 1

    q.columns = chosen
    q.leading = kept_front
    q.trailing = kept_back


def columns_for_subquery(cached: Query, outer_select: List[int]) -> Query:
    private = detached_copy(cached)
    with_columns(private, outer_select)
    return private


# --- oracle: the real patched compound-query compilation ----------------------

CODE_NAMES = ["f%d" % k for k in range(N_COLS)]

_state = {}


def _setup_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes"],
            DATABASES={"default": {
                "ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        )
    django.setup()

    from django.db import models

    # A minimal model with 10 plain integer columns (the bridge's column-code
    # carriers) plus one filter column realizing the state token. Registered
    # under an installed app so model registration succeeds in the eval
    # image; no table is created (compilation only, nothing executes).
    attrs = {"__module__": __name__,
             "Meta": type("Meta", (), {"app_label": "contenttypes"}),
             "s": models.IntegerField()}
    for name in CODE_NAMES:
        attrs[name] = models.IntegerField()
    _state["model"] = type("ConfCombo", (models.Model,), attrs)


def _add_families(q, leading, trailing):
    """Realize the two ordered families of derived columns on ``q``: a leading
    code as an ``extra`` select entry (rendered ahead of the query's own
    columns), a trailing code as an annotation (rendered after them). Both are
    aliased onto the code's column name."""
    from django.db.models import F
    for k in leading:
        # a params-free SQL fragment: the bound parameter list must observe the
        # carried state token alone.
        q.add_extra({CODE_NAMES[k]: "1+1"}, None, None, None, None, None)
    for k in trailing:
        q.add_annotation(F(CODE_NAMES[(k + 1) % N_COLS]), CODE_NAMES[k])


def _new_shared(token, leading, trailing):
    """The reused component sub-query: no column list of its own, the given
    families of derived columns, and its accumulated state realized as a WHERE
    filter bound to ``token``."""
    from django.db.models import Q
    from django.db.models.sql.query import Query as RepoQuery
    shared = RepoQuery(_state["model"])
    shared.add_q(Q(s__gt=token))
    _add_families(shared, leading, trailing)
    return shared


def _alias_of(piece):
    """The column name a rendered SELECT item exposes: the AS alias when there
    is one (extra entries and annotations), else the bare column name."""
    if " AS " in piece:
        piece = piece.rsplit(" AS ", 1)[1]
    return piece.split(".")[-1].strip('"')


def _compile_once(shared, lead_req, own_req, trail_req):
    """One compound-query compilation over the shared component. The outer
    query is shaped so the list the real branch passes down —
    ``(*extra_select, *values_select, *annotation_select)`` — is exactly
    ``lead_req + own_req + trail_req``: the outer exposes the requested leading
    codes as ``extra`` entries and the requested trailing codes as annotations,
    so its own column list is exactly ``own_req``. ``own_req`` must be
    non-empty — the real branch is guarded on the OUTER query restricting the
    columns (``self.query.values_select``), so an outer whose every requested
    name is one of its own derived columns does not reach the modelled code at
    all. Returns (rendered names, params)."""
    from django.db.models.sql.query import Query as RepoQuery
    outer = RepoQuery(_state["model"])
    outer.combined_queries = (shared,)
    outer.combinator = "union"
    _add_families(outer, lead_req, trail_req)
    outer.set_values(tuple(CODE_NAMES[k] for k in lead_req + own_req + trail_req))
    comp = outer.get_compiler("default")
    parts, params = comp.get_combinator_sql("union", False)
    sql = parts[0]
    sel = sql[len("SELECT "):sql.index(" FROM ")]
    return [_alias_of(p) for p in sel.split(", ")], list(params)


def _shared_obs(shared):
    """The shared component's observable post-state: its own column list, both
    families of derived columns it still exposes, and its WHERE parameter (the
    state-token realization)."""
    lookups = shared.where.children
    assert len(lookups) == 1, "probe query shape changed: %r" % (lookups,)
    return (list(shared.values_select), list(shared.extra_select),
            list(shared.annotation_select), lookups[0].rhs)


# --- differential driver -------------------------------------------------------

def check(token, leading, trailing, requests):
    """One probe: the SAME shared component (exposing ``leading`` /
    ``trailing`` derived columns) compiled len(requests) times, each with its
    own outer column list. A request is a (lead_req, own_req, trail_req)
    triple; the chosen list is their concatenation. Returns an error string on
    disagreement, else the number of compilation checks performed."""
    # shadow: the reused sub-query as the model carries it
    cached = Query([], list(leading), list(trailing), token)
    shadow_obs = []
    for lead_req, own_req, trail_req in requests:
        outer = lead_req + own_req + trail_req
        res = columns_for_subquery(cached, list(outer))
        if (res is cached or res.columns is cached.columns
                or res.leading is cached.leading
                or res.trailing is cached.trailing):
            return ("INTERNAL: shadow returned an object aliasing the shared "
                    "sub-query on token=%r leading=%r trailing=%r requests=%r"
                    % (token, leading, trailing, requests))
        shadow_obs.append((list(res.leading) + list(res.columns)
                           + list(res.trailing), res.state,
                           list(cached.columns), list(cached.leading),
                           list(cached.trailing), cached.state))
        if len(cached.columns) != 0:
            # the next compilation's precondition would no longer hold: the
            # shadow locked in a column list on the shared sub-query
            return ("INTERNAL: shadow left a column list on the shared "
                    "sub-query: token=%r outer=%r cached.columns=%r"
                    % (token, outer, cached.columns))

    # real: the SAME shared repo query compiled once per outer list
    shared = _new_shared(token, leading, trailing)
    for req, obs in zip(requests, shadow_obs):
        lead_req, own_req, trail_req = req
        s_names, s_state, s_cc, s_cl, s_ct, s_cs = obs
        real_names, real_params = _compile_once(shared, lead_req, own_req,
                                               trail_req)
        (real_shared_cols, real_shared_lead, real_shared_trail,
         real_shared_tok) = _shared_obs(shared)
        want_names = [CODE_NAMES[k] for k in s_names]
        want_shared = [CODE_NAMES[k] for k in s_cc]
        want_shared_lead = [CODE_NAMES[k] for k in s_cl]
        want_shared_trail = [CODE_NAMES[k] for k in s_ct]
        if (real_names != want_names or real_params != [s_state]
                or real_shared_cols != want_shared
                or real_shared_lead != want_shared_lead
                or real_shared_trail != want_shared_trail
                or real_shared_tok != s_cs):
            return ("DISAGREEMENT on token=%r leading=%r trailing=%r "
                    "requests=%r at request=%r:\n"
                    "  shadow (impl region): rendered=%r carried state=%r"
                    " shared columns=%r leading=%r trailing=%r state=%r\n"
                    "  real (patched repo):  rendered=%r params=%r"
                    " shared values_select=%r extra_select=%r"
                    " annotation_select=%r where param=%r"
                    % (token, leading, trailing, requests, req,
                       want_names, s_state, want_shared, want_shared_lead,
                       want_shared_trail, s_cs,
                       real_names, real_params, real_shared_cols,
                       real_shared_lead, real_shared_trail, real_shared_tok))
    return len(requests)


def _valid_triple(triple):
    """An outer query can realize the chosen list ``lead + own + trail`` exactly
    when: its own part is NON-EMPTY (else the real branch's guard on the outer
    restricting the columns does not fire); the derived groups hold distinct
    codes (an alias dict cannot repeat a key); and the three groups are pairwise
    disjoint (a code exposed as one of the outer's derived columns is classified
    there, so it cannot also appear in its own column list)."""
    lead, own, trail = triple
    if not own:
        return False
    if len(set(lead)) != len(lead) or len(set(trail)) != len(trail):
        return False
    if set(lead) & set(trail) or set(lead) & set(own) or set(trail) & set(own):
        return False
    return True


def boundary_probes():
    """Each entry: (token, leading, trailing, [(lead, own, trail), ...]) — the
    component's own two derived families, then the outer-shaped chosen lists to
    compile it with. The component's families are chosen INDEPENDENTLY of the
    requested ones, which is what stresses the classification: a code the outer
    asks for as a plain column may be one the COMPONENT exposes as derived, and
    vice versa."""
    probes = []
    full = list(range(N_COLS))
    tokens = [0, 1, -1, 7, 10 ** 9, -(10 ** 9), 2 ** 31 - 1, -(2 ** 31)]
    families = [
        ([], []),                 # no derived columns: the callee's shortcut
        ([0], []),                # leading only
        ([], [0]),                # trailing only
        ([0], [1]),               # one of each
        ([2, 5], [7, 3]),         # several of each, out of column order
        ([5, 2], [3, 7]),         # the same sets in the other order
        ([4], [4]),               # ONE code exposed by BOTH families
        ([0, 1, 2, 3], []),       # a wide leading family
        ([], [6, 7, 8, 9]),       # a wide trailing family
    ]
    # chosen lists, as the (lead, own, trail) shape an outer query realizes
    triples = [
        ([], [0], []),                       # one plain column
        ([], [4], []),
        ([], [9], []),
        ([], [0, 0], []),                    # duplicates in the own part
        ([], [1, 1, 1], []),
        ([], full, []),                      # every column, plain
        ([], list(reversed(full)), []),
        ([0], [1], []),                      # a leading derived column
        ([], [1], [2]),                      # a trailing one
        ([0], [1], [2]),                     # one of each
        ([0, 1], [2, 3], [4, 5]),
        ([5, 2], [0], [7, 3]),               # groups out of column order
        ([2, 5], [9, 9], [3, 7]),
        ([7], [0, 1, 2, 3, 4, 5, 6], [8]),   # wide own part
        ([], [k % 5 for k in range(30)], []),  # long, repeating
        ([1, 3, 5, 7, 9], [0], [2, 4, 6, 8]),  # every code derived but one
    ]
    for t in triples:
        assert _valid_triple(t), "boundary triple outside the branch: %r" % (t,)
    for tok in tokens:
        for leading, trailing in families:
            probes.append((tok, leading, trailing, triples))
    return probes


def main():
    _setup_django()

    checked = 0
    n_probes = 0
    for token, leading, trailing, triples in boundary_probes():
        # every consecutive pair of chosen lists is a reuse chain (wide then
        # narrow, narrow then wide, identical twice), compiled a->b->a so the
        # third compilation re-checks the first after a different one.
        for a, b in zip(triples, triples[1:] + triples[:1]):
            got = check(token, leading, trailing, [a, b, a])
            if isinstance(got, str):
                print(got)
                return 1
            checked += got
            n_probes += 1

    rng = random.Random(SEED)
    generated = 0
    while generated < N_FUZZ:
        token = rng.randint(-10 ** 9, 10 ** 9)
        pool = list(range(N_COLS))
        rng.shuffle(pool)
        n_lead = rng.randint(0, 3)
        n_trail = rng.randint(0, 3)
        leading = pool[:n_lead]
        trailing = pool[n_lead:n_lead + n_trail]
        if rng.random() < 0.1 and leading:
            trailing = list(trailing) + [leading[0]]   # a both-families code
        requests = []
        for _c in range(3):
            codes = list(range(N_COLS))
            rng.shuffle(codes)
            n_l = rng.randint(0, 3)
            n_t = rng.randint(0, 3)
            lead = codes[:n_l]
            trail = codes[n_l:n_l + n_t]
            rest = codes[n_l + n_t:]
            own = [rest[rng.randrange(len(rest))]
                   for _ in range(rng.randint(1, 8))]
            triple = (lead, own, trail)
            if not _valid_triple(triple):
                continue
            requests.append(triple)
        if not requests:
            continue
        got = check(token, leading, trailing, requests)
        if isinstance(got, str):
            print(got)
            return 1
        checked += got
        n_probes += 1
        generated += 1

    if checked < 100000:
        print("G-CONF FAIL: input plan under-generated (%d < 100000 checks)"
              % checked)
        return 1

    print("G-CONF OK: shadow impl == real patched compound-query "
          "column-setting branch on %d compilation checks (%d probes of 3 "
          "compilations each, seed %d); the classification/narrowing of both "
          "derived-column families and the carried state agree everywhere; "
          "0 disagreements." % (checked, n_probes, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
