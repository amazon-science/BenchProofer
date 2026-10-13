#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13158 (nagini).

SHADOW: the impl regions of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Invariant/Assert and the ghost lemma invocation)
stripped. The @Pure helper ``all_marked`` copies over as a plain function on
top of a small immutable-tuple PSeq shim and serves as an internal cross-check
of the composite's result. This bundle consumes no @ContractOnly axiom, so
every shadow callee is the model's own code.

ORACLE: the REAL patched repo functions the model models per mapping.md —
``django.db.models.sql.query.Query.is_empty`` (modelled by
``matches_nothing``), ``Query.set_empty`` (modelled by
``mark_matching_nothing``), ``Query.clone`` (modelled by ``duplicate``), and
the public composite ``django.db.models.query.QuerySet.none`` (modelled by
``none``). The gate applies the patch to /testbed before this script runs;
the script only imports and drives the patched code.

Type bridge (mapping.md section 2): a model query is a pair
(where_empty: bool, child_empty: List[bool]). It lifts to a real ``Query``
whose own WHERE tree is put into the matching-nothing state iff where_empty
(by adding the node type ``is_empty`` tests for), carrying one constituent
``Query`` per child_empty entry, each likewise put into the matching-nothing
state iff its flag is set. A real query lowers back to the pair
(q.is_empty(), [c.is_empty() for c in q.combined_queries]) — per mapping.md
the constituent's matching-nothing flag is the only constituent property the
compound result reads, so this observable snapshot is exactly the abstraction.
The composite is driven through a real ``QuerySet`` wrapping the lifted query,
mirroring the public entry point the model's ``none`` corresponds to.

Input domain: the model preconditions demand only readable/writable fields
(permissions) — every (bool, list-of-bool) pair is Requires-satisfying.
Generation stresses the discriminating boundaries: no constituents, single
constituent, all/none/mixed flags set, already-matching-nothing sources
(idempotence of the marking), and copy-independence (mutating the copy must
not reach the source and vice versa).

Each generated pair drives all four modelled operations differentially.
>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz pairs.
Pinned fuzz seed: 131580.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 131580
N_FUZZ = 100000
MAX_CHILDREN = 8


# --- PSeq shim: immutable sequence with the operations the pure region uses --

class PSeqShim(object):
    __slots__ = ("_t",)

    def __init__(self, t=()):
        self._t = tuple(t)

    def drop(self, n):
        return PSeqShim(self._t[n:])

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]


def ToSeq(lst):
    return PSeqShim(lst)


# --- the model's minimal query class (contract calls stripped) ---------------

class Query(object):
    def __init__(self):
        self.where_empty = False
        self.child_empty = []


# --- pure helper from model.py, contracts stripped ----------------------------

def all_marked(flags):
    if len(flags) == 0:
        return True
    return flags[0] and all_marked(flags.drop(1))


# --- the impl regions of model.py, verbatim, contract calls stripped ----------

def matches_nothing(q):
    return q.where_empty


def mark_matching_nothing(q):
    q.where_empty = True
    i = 0
    while i < len(q.child_empty):
        q.child_empty[i] = True
        i = i + 1


def duplicate(q):
    obj = Query()
    obj.where_empty = q.where_empty
    i = 0
    while i < len(q.child_empty):
        obj.child_empty.append(q.child_empty[i])
        i = i + 1
    return obj


def none(q):
    c = duplicate(q)
    mark_matching_nothing(c)
    # (ghost lemma invocation stripped: proof-only, no runtime effect)
    return c


# --- oracle plumbing -----------------------------------------------------------

def setup_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(INSTALLED_APPS=[], DATABASES={})
    django.setup()


def lift(where_empty, child_flags):
    """Model pair -> real Query with the same observable emptiness vector."""
    from django.db.models.sql.query import Query as RealQuery
    from django.db.models.sql.where import NothingNode, AND
    q = RealQuery(None)
    if where_empty:
        q.where.add(NothingNode(), AND)
    kids = []
    for f in child_flags:
        c = RealQuery(None)
        if f:
            c.where.add(NothingNode(), AND)
        kids.append(c)
    q.combined_queries = tuple(kids)
    return q


def lower(q):
    """Real Query -> the model pair (its observable emptiness vector)."""
    return (q.is_empty(), [c.is_empty() for c in q.combined_queries])


def shadow_pair(m):
    return (m.where_empty, list(m.child_empty))


def make_shadow(where_empty, child_flags):
    m = Query()
    m.where_empty = where_empty
    m.child_empty = list(child_flags)
    return m


# --- differential driver --------------------------------------------------------

def check_one(where_empty, child_flags):
    """Drive all four modelled operations on one input pair; return an error
    string on any disagreement, else None."""
    from django.db.models.query import QuerySet

    inp = (where_empty, list(child_flags))

    # (1) the emptiness observation
    m = make_shadow(where_empty, child_flags)
    r = lift(where_empty, child_flags)
    s_obs = matches_nothing(m)
    r_obs = r.is_empty()
    if s_obs != r_obs:
        return ("DISAGREEMENT (emptiness observation) on input=%r:\n"
                "  shadow (impl region) = %r\n"
                "  real (is_empty)      = %r" % (inp, s_obs, r_obs))

    # (2) the copy: same observable contents, and independent of the source
    m = make_shadow(where_empty, child_flags)
    r = lift(where_empty, child_flags)
    mc = duplicate(m)
    rc = r.clone()
    if shadow_pair(mc) != lower(rc):
        return ("DISAGREEMENT (copy contents) on input=%r:\n"
                "  shadow (impl region) = %r\n"
                "  real (clone)         = %r" % (inp, shadow_pair(mc), lower(rc)))
    if shadow_pair(m) != lower(r):
        return ("DISAGREEMENT (copy left source changed) on input=%r:\n"
                "  shadow source = %r\n"
                "  real source   = %r" % (inp, shadow_pair(m), lower(r)))
    # independence: mutating the copy must not reach the source, on both sides
    mark_matching_nothing(mc)
    rc.set_empty()
    if shadow_pair(m) != lower(r):
        return ("DISAGREEMENT (copy independence) on input=%r after mutating "
                "the copy:\n  shadow source = %r\n  real source   = %r"
                % (inp, shadow_pair(m), lower(r)))
    if shadow_pair(mc) != lower(rc):
        return ("DISAGREEMENT (mutated copy) on input=%r:\n"
                "  shadow copy = %r\n  real copy   = %r"
                % (inp, shadow_pair(mc), lower(rc)))

    # (3) the emptying operation, applied in place
    m = make_shadow(where_empty, child_flags)
    r = lift(where_empty, child_flags)
    mark_matching_nothing(m)
    r.set_empty()
    if shadow_pair(m) != lower(r):
        return ("DISAGREEMENT (emptying) on input=%r:\n"
                "  shadow (impl region) = %r\n"
                "  real (set_empty)     = %r" % (inp, shadow_pair(m), lower(r)))

    # (4) the public composite: copy-then-empty via the real QuerySet
    m = make_shadow(where_empty, child_flags)
    r = lift(where_empty, child_flags)
    mc = none(m)
    qs = QuerySet(model=None, query=r)
    rc_q = qs.none().query
    if shadow_pair(mc) != lower(rc_q):
        return ("DISAGREEMENT (composite result) on input=%r:\n"
                "  shadow (impl region)  = %r\n"
                "  real (QuerySet-level) = %r"
                % (inp, shadow_pair(mc), lower(rc_q)))
    if shadow_pair(m) != lower(r):
        return ("DISAGREEMENT (composite left source changed) on input=%r:\n"
                "  shadow source = %r\n  real source   = %r"
                % (inp, shadow_pair(m), lower(r)))
    # internal cross-check: the pure fold agrees the composite's result is
    # matching-nothing at every level
    if not all_marked(ToSeq(mc.child_empty)):
        return ("INTERNAL: pure fold rejects the composite's result on "
                "input=%r: %r" % (inp, shadow_pair(mc)))
    return None


def boundary_cases():
    cases = [
        (False, []),
        (True, []),
        (False, [False]),
        (False, [True]),
        (True, [False]),
        (True, [True]),
        (False, [False, False]),
        (False, [True, False]),
        (False, [False, True]),
        (False, [True, True]),
        (True, [True, True]),                    # already matching nothing
        (False, [False] * MAX_CHILDREN),
        (False, [True] * MAX_CHILDREN),
        (False, [bool(i % 2) for i in range(MAX_CHILDREN)]),
        (True, [bool((i + 1) % 2) for i in range(MAX_CHILDREN)]),
    ]
    return cases


def main():
    try:
        setup_django()
    except Exception as exc:  # pragma: no cover - environment guard
        print("G-CONF ERROR: Django not importable/configurable: %r" % (exc,))
        return 1

    checked = 0
    boundary = boundary_cases()
    for where_empty, child_flags in boundary:
        err = check_one(where_empty, child_flags)
        if err:
            print(err)
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        where_empty = rng.random() < 0.5
        n = rng.randint(0, MAX_CHILDREN)
        child_flags = [rng.random() < 0.5 for _ in range(n)]
        err = check_one(where_empty, child_flags)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched is_empty/clone/set_empty/"
          "QuerySet-level composite on %d inputs (%d boundary + %d fuzz, "
          "seed %d), each driving all four modelled operations plus the "
          "copy-independence probe; 0 disagreements."
          % (checked, len(boundary), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
