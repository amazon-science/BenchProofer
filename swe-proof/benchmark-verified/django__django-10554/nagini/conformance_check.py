#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-10554 (nagini).

SHADOW: the impl region of model.py's ``relabel_order_term``, copied VERBATIM
below with only the contract calls (Requires / Ensures / Invariant / Assert /
Exsures) stripped. The @Pure helper ``first_pos`` copies over as a plain
function on top of a small immutable PSeq shim (tuple-backed; supports
``drop``, ``+``, ``==``, ``len``, indexing); it is iterative here to sidestep
Python recursion limits on long inputs but is extensionally the same
leftmost-match fold as model.py's front recursion, and it doubles as an
internal cross-check of the executable shadow's scan. There are no
@ContractOnly callees (mapping.md section 3: no axiomatized callees).

ORACLE: the REAL patched repo code the model models per mapping.md section 1 —
the per-term rewrite of an ordering expression for a combined query inside
``SQLCompiler.get_order_by`` (django/db/models/sql/compiler.py). The gate
applies patch.diff to /testbed and sets PYTHONPATH=/testbed before this
script runs, so the import resolves to the patched module. Each probe builds
a bare ``Query`` with a combinator set, installs the selected columns on both
the query and a fresh ``SQLCompiler`` (mirroring how ``get_select`` lays them
out: plain columns carry no alias), pushes ONE ordering term, runs the real
``get_order_by``, and observes (a) the 1-based position rendered into the
rewritten term, or the database error, and (b) the post-state of the query's
selected-column tuple.

TYPE BRIDGE (mapping.md section 2): the model carrier is ``cols: List[int]``
of column identities; identity k is realized as a ``RawSQL('COL_<k>', ())``
expression, whose structural equality is exactly the ``==`` the repo scan
performs, so equal ints correspond to equal selected expressions (a
bijection). ``src: int`` lowers the same way into the ordering term.
``aliased: bool`` is the discriminator for the no-match outcome: it is
realized by appending one aliased, never-matching selected entry at the END
of the compiler's column triples (aliased entries are skipped by the repo's
match scan, so match positions over the plain prefix are unaffected, and the
alias is what the repo's no-match branch consults). The rejection
(``OrderTermUnmatched`` in the model) corresponds to the repo raising
``django.db.utils.DatabaseError``; positions correspond as
shadow int == int rendered into the rewritten term; the post-state
correspondence is ``cols`` (as COL_<k> strings) == the query's select tuple.

DOMAIN NOTE: the carrier is the result set's selected-column list, which is
non-empty for any compilable query (SQL demands at least one selected
column); the empty-``cols`` / plain-term combination is therefore outside the
refinement's realizable domain and is not generated (empty ``cols`` IS
exercised on the aliased side, where the aliased entry keeps the real column
triples non-empty).

INPUT PLAN (>= 1e5 Requires-satisfying inputs): boundary triples (singleton
match / no-match, duplicates preferring the leftmost, the term at every
position of a window, all-equal lists, negative / zero / large identities,
long lists, empty-cols aliased rejects) plus 100000 random fuzz triples over
small pools (to force collisions and duplicates) mixed with wide identities,
each with a fuzzed aliased flag. Pinned fuzz seed: 10554. Exit 0 iff zero
disagreements; on disagreement prints the input and both outputs and exits 1.
stdlib only.
"""
import json
import random
import sys

SEED = 10554
N_FUZZ = 100000


# --- PSeq shim: immutable sequence with the operations the model uses --------

class PSeq(object):
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

    def take(self, n):
        return PSeq._wrap(self._t[:n])

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


def ToSeq(lst):
    return PSeq._wrap(lst)


# --- user exception from model.py ---------------------------------------------

class OrderTermUnmatched(Exception):
    pass


# --- pure region of model.py, copied as a plain function -----------------------

def first_pos(src, cols):
    """The 1-based position of the FIRST element equal to ``src`` in ``cols``,
    or 0 if none is. (Iterative here to sidestep recursion limits on long fuzz
    inputs; extensionally the same leftmost-match fold as model.py's front
    recursion.)"""
    i = 0
    while i < len(cols):
        if cols[i] == src:
            return i + 1
        i = i + 1
    return 0


# --- impl region of model.py, verbatim with contract calls stripped ------------

def relabel_order_term(cols, src, aliased):
    entry_fp = first_pos(src, ToSeq(cols))  # type: int
    pos = 0  # type: int
    i = len(cols)
    while i > 0:
        if cols[i - 1] == src:
            pos = i
        i = i - 1
    if pos != 0:
        # MATCH: reference the first matching position; list unchanged.
        return pos
    # No column matched (entry_fp == 0 over the unchanged list).
    if aliased:
        # REJECT: an unmatched aliased term cannot be ordered by.
        raise OrderTermUnmatched()
    # APPEND: add the plain column and reference its new (last) position.
    old_seq = ToSeq(cols)  # type: PSeq[int]
    cols.append(src)
    return len(cols)


# --- oracle: the real patched repo rewrite, observed via get_order_by ----------

_ALIASED_SENTINEL_SQL = "ALIASED_SENTINEL"


def _setup_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
            INSTALLED_APPS=[],
        )
    django.setup()


def _col_sql(k):
    return "COL_%d" % k


def real_relabel(cols_ints, src_int, aliased):
    """Drive the real (patched) get_order_by on one ordering term of a
    combined query whose selected columns realize ``cols_ints`` per the
    bridge; return ('raise' | position, post-state select sql list)."""
    from django.db import connection
    from django.db.models.expressions import OrderBy, RawSQL
    from django.db.models.sql.compiler import SQLCompiler
    from django.db.models.sql.query import Query
    from django.db.utils import DatabaseError

    q = Query(None)
    q.combinator = "union"
    sel_exprs = [RawSQL(_col_sql(k), ()) for k in cols_ints]
    q.select = tuple(sel_exprs)
    q.order_by = (OrderBy(RawSQL(_col_sql(src_int), ())),)
    comp = SQLCompiler(q, connection, "default")
    # Mirror get_select's layout: the query's selected columns carry no alias;
    # an aliased (derived) entry, when present, sits after them and is what
    # the no-match branch consults. Its expression never equals any COL_<k>.
    triples = [(e, ("", ()), None) for e in sel_exprs]
    if aliased:
        triples.append((RawSQL(_ALIASED_SENTINEL_SQL, ()), ("", ()),
                        "derived_alias"))
    comp.select = triples
    try:
        result = comp.get_order_by()
    except DatabaseError:
        return "raise", [e.sql for e in q.select]
    resolved = result[0][0]
    inner = resolved.get_source_expressions()[0]
    return int(inner.sql), [e.sql for e in q.select]


# --- differential driver --------------------------------------------------------

def check(cols_ints, src_int, aliased):
    """Run shadow and oracle on one (cols, src, aliased) triple; return an
    error string on disagreement, else None."""
    shadow_cols = list(cols_ints)
    entry_fp = first_pos(src_int, ToSeq(shadow_cols))
    try:
        shadow_out = relabel_order_term(shadow_cols, src_int, aliased)
    except OrderTermUnmatched:
        shadow_out = "raise"
    # internal cross-check: the shadow's scan agrees with the pure fold
    if shadow_out != "raise" and entry_fp != 0 and shadow_out != entry_fp:
        return ("INTERNAL: impl-region scan (%r) and pure first_pos (%r) "
                "disagree on cols=%r src=%r"
                % (shadow_out, entry_fp, cols_ints, src_int))

    real_out, real_select = real_relabel(cols_ints, src_int, aliased)
    shadow_select = [_col_sql(k) for k in shadow_cols]
    if shadow_out != real_out or shadow_select != real_select:
        return ("DISAGREEMENT on cols=%r src=%r aliased=%r:\n"
                "  shadow (impl region): outcome=%r post-cols=%r\n"
                "  real (patched repo):  outcome=%r post-select=%r"
                % (cols_ints, src_int, aliased,
                   shadow_out, shadow_select, real_out, real_select))
    return None


def boundary_cases():
    cases = []
    # empty column list: only realizable on the aliased side (see DOMAIN NOTE)
    cases.append(([], 0, True))
    cases.append(([], -7, True))
    # singleton: match / no-match, both flags
    for flag in (False, True):
        cases.append(([3], 3, flag))
        cases.append(([3], 4, flag))
        cases.append(([0], 0, flag))
        cases.append(([-1], -1, flag))
        cases.append(([-1], 1, flag))
    # duplicates: the FIRST matching position must win
    for flag in (False, True):
        cases.append(([5, 5], 5, flag))
        cases.append(([1, 5, 5, 2], 5, flag))
        cases.append(([5, 1, 5], 5, flag))
        cases.append(([2, 2, 2, 2], 2, flag))
        cases.append(([2, 2, 2, 2], 3, flag))
    # the term at every position of a 6-wide window
    base = [10, 11, 12, 13, 14, 15]
    for j in range(len(base)):
        for flag in (False, True):
            cases.append((list(base), base[j], flag))
    # absent term over the same window
    for flag in (False, True):
        cases.append((list(base), 99, flag))
    # negative / zero / large identities
    for flag in (False, True):
        cases.append(([-5, 0, 5], 0, flag))
        cases.append(([-5, 0, 5], -5, flag))
        cases.append(([-5, 0, 5], 7, flag))
        cases.append(([10 ** 9, -10 ** 9], 10 ** 9, flag))
        cases.append(([10 ** 9, -10 ** 9], 123, flag))
    # long lists: match at head / middle / tail, and no match
    long_list = list(range(200))
    for flag in (False, True):
        cases.append((list(long_list), 0, flag))
        cases.append((list(long_list), 100, flag))
        cases.append((list(long_list), 199, flag))
        cases.append((list(long_list), 999, flag))
    return cases


def main():
    _setup_django()

    checked = 0
    boundary = boundary_cases()
    for cols_ints, src_int, aliased in boundary:
        err = check(cols_ints, src_int, aliased)
        if err:
            print(err)
            return 1
        checked += 1

    # randomized fuzz: small pools force collisions/duplicates and frequent
    # matches; wide identities stress the bridge (pinned seed)
    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        aliased = rng.random() < 0.5
        n = rng.randint(0 if aliased else 1, 10)
        if rng.random() < 0.7:
            cols_ints = [rng.randint(0, 6) for _ in range(n)]
            src_int = rng.randint(0, 8)
        else:
            cols_ints = [rng.randint(-1000, 1000) for _ in range(n)]
            src_int = rng.randint(-1000, 1000)
        err = check(cols_ints, src_int, aliased)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched order-term rewrite on %d "
          "inputs (%d boundary + %d fuzz, seed %d); 0 disagreements."
          % (checked, len(boundary), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
