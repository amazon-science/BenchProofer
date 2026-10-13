#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-14122 (nagini).

SHADOW: the impl region of model.py `assemble_grouping_key`, copied verbatim
below with the contract calls (Requires/Ensures/Invariant/Assert) stripped.
The model IS Python: the carriers are plain List[int] and the impl region
uses no PSeq at runtime (the @Pure helpers `empty_seq`/`order_contrib` are
spec-only ghosts consumed by contracts and Asserts, all of which are
stripped here). This bundle has no @ContractOnly callees.

ORACLE: the REAL patched repo function the model models per mapping.md —
`django.db.models.sql.compiler.SQLCompiler.get_group_by(select, order_by)`.
The gate applies patch.diff to /testbed before this script runs and sets
PYTHONPATH=/testbed, so the import below resolves the patched source. The
compiler is driven directly: a `Query` with `group_by = True` (the modeled
regime: the grouping key is assembled from the contributing sources, with
no pre-seeded expression list) on the default sqlite connection, whose
features make the grouping-list post-processing an order-preserving
identity for the realized inputs.

Type bridge (mapping.md section 2):

    token t (int)        <-> a RawSQL leaf expression rendering as 'tok<t>'
                             (a distinct grouping column per distinct int;
                             one grouping column offered per entry)
    select_cols[i]       <-> select entry (expr_i, None, None)
    order_cols[k] /      <-> order_by entry (expr_k, (sql, params, is_ref))
    order_is_backref[k]      with is_ref passed as the raw int flag
                             (truthy iff != 0, matching the model's != 0 test)
    trailing_cols[j]     <-> the compiler's `having` node with one leaf per
                             token; its grouping columns are appended after
                             the ordering source
    ordering_was_requested   <-> compiler._meta_ordering is falsy (None);
                             not requested <-> a truthy default-ordering
                             marker is set
    result               <-> the (sql, params) list mapped back to ints via
                             each token's rendered sql

Input domain: the Requires demand equal-length order carriers; the declared
abstraction (mapping.md section 2) additionally maps each DISTINCT grouping
column to a distinct int — the repo's trailing duplicate-collapse
post-processing (unchanged by the patch, outside the modeled hunk) is
identity exactly on distinct-column inputs, so all generated token lists
use pairwise-distinct ints across the three sources. Boundary: every
(select, order, trailing) length combination in 0..2 x 0..3 x 0..2 crossed
with every back-reference flag shape and both flag polarities, plus
non-canonical (negative / >1) flag ints and token extremes. Fuzz: 100_000
random cases (lengths <= 6/6/4, mixed flags, both polarities). Pinned fuzz
seed: 141220. Total > 1e5 oracle calls.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only (plain random).
"""
import json
import random
import sys

SEED = 141220
N_FUZZ = 100_000


# --- the impl region of model.py, verbatim, contract calls stripped ----------

def assemble_grouping_key(select_cols, order_cols, order_is_backref,
                          trailing_cols, ordering_was_requested):
    result = []  # type: ignore[var-annotated]
    # selected-column source (unconditional)
    s = 0
    while s < len(select_cols):
        result.append(select_cols[s])
        s = s + 1
    # result-ordering source (only when the ordering was explicitly requested)
    if ordering_was_requested:
        k = 0
        while k < len(order_cols):
            is_ref = order_is_backref[k]
            col = order_cols[k]
            if is_ref == 0:
                result.append(col)
            k = k + 1
    # trailing source (unconditional)
    t = 0
    while t < len(trailing_cols):
        result.append(trailing_cols[t])
        t = t + 1
    return result


# --- the differential check ---------------------------------------------------

def main():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=['django.contrib.contenttypes'],
            DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3',
                                   'NAME': ':memory:'}},
            USE_TZ=False,
        )
    django.setup()
    from django.db import connection
    from django.db.models import IntegerField
    from django.db.models.expressions import RawSQL
    from django.db.models.sql.query import Query
    from django.db.models.sql.where import WhereNode
    from django.contrib.contenttypes.models import ContentType

    # The realized post-processing must be order-preserving identity on
    # distinct columns: true on this connection (no pk-collapse features).
    assert not connection.features.allows_group_by_pk
    assert not connection.features.allows_group_by_selected_pks

    query = Query(ContentType)
    # The modeled regime: the grouping key is assembled purely from the
    # contributing sources (no pre-seeded minimal grouping set).
    query.group_by = True
    compiler = query.get_compiler(using='default')

    def tok(t):
        """Realize token t as a distinct grouping-column leaf."""
        return RawSQL('tok%d' % t, [], output_field=IntegerField())

    def sql_to_token(sql):
        """Invert the token realization from a compiled sql fragment."""
        s = sql.strip('()')
        if s.startswith('tok'):
            try:
                return int(s[3:])
            except ValueError:
                pass
        return '<unmapped:%r>' % (sql,)

    checked = 0

    def check_one(select_cols, order_cols, order_is_backref, trailing_cols,
                  ordering_was_requested):
        nonlocal checked
        # Requires hold by construction: equal-length order carriers.
        assert len(order_cols) == len(order_is_backref)
        select = [(tok(t), None, None) for t in select_cols]
        order_by = [(tok(t), ('placeholder', [], flag))
                    for t, flag in zip(order_cols, order_is_backref)]
        compiler.having = (WhereNode([tok(t) for t in trailing_cols])
                           if trailing_cols else None)
        compiler._meta_ordering = (None if ordering_was_requested
                                   else ['default-order-marker'])
        real = compiler.get_group_by(select, order_by)
        real_tokens = [sql_to_token(sql) for sql, params in real]
        shadow = assemble_grouping_key(select_cols, order_cols,
                                       order_is_backref, trailing_cols,
                                       ordering_was_requested)
        checked += 1
        if real_tokens != shadow:
            print("DISAGREEMENT\n"
                  "  input: select=%r order=%r refs=%r trailing=%r "
                  "requested=%r\n"
                  "  real get_group_by tokens = %r (raw %r)\n"
                  "  shadow                   = %r"
                  % (select_cols, order_cols, order_is_backref, trailing_cols,
                     ordering_was_requested, real_tokens, real, shadow))
            return False
        return True

    rng = random.Random(SEED)
    token_pool_hi = 10 ** 6

    def fresh_tokens(n, used):
        out = []
        while len(out) < n:
            t = rng.randint(-token_pool_hi, token_pool_hi)
            if t not in used:
                used.add(t)
                out.append(t)
        return out

    # --- boundary: all small length combos x flag shapes x both polarities ---
    n_boundary = 0
    for ns in range(0, 3):
        for no in range(0, 4):
            for nt in range(0, 3):
                for flag_mask in range(2 ** no):
                    for requested in (True, False):
                        base = 1
                        select_cols = list(range(base, base + ns))
                        order_cols = list(range(base + ns, base + ns + no))
                        trailing_cols = list(range(base + ns + no,
                                                   base + ns + no + nt))
                        refs = [(flag_mask >> k) & 1 for k in range(no)]
                        if not check_one(select_cols, order_cols, refs,
                                         trailing_cols, requested):
                            return 1
                        n_boundary += 1

    # boundary: non-canonical flag ints (any non-zero marks a back-reference)
    # and token extremes
    for select_cols, order_cols, refs, trailing_cols, requested in [
        ([1], [2, 3, 4], [2, 0, -7], [5], True),
        ([1], [2, 3, 4], [2, 0, -7], [5], False),
        ([10 ** 9], [-(10 ** 9)], [0], [7], True),
        ([10 ** 9], [-(10 ** 9)], [0], [7], False),
        ([], [1, 2], [0, 0], [], True),
        ([], [1, 2], [0, 0], [], False),
        ([0], [1], [0], [2], True),   # token 0 is a valid distinct column
        ([0], [1], [0], [2], False),
    ]:
        if not check_one(select_cols, order_cols, refs, trailing_cols,
                         requested):
            return 1
        n_boundary += 1

    # --- fuzz -----------------------------------------------------------------
    flag_pool = [0, 0, 0, 1, 1, 2, -1, 5, -100]
    for _ in range(N_FUZZ):
        used = set()
        ns = rng.randint(0, 6)
        no = rng.randint(0, 6)
        nt = rng.randint(0, 4)
        select_cols = fresh_tokens(ns, used)
        order_cols = fresh_tokens(no, used)
        trailing_cols = fresh_tokens(nt, used)
        refs = [rng.choice(flag_pool) for _ in range(no)]
        requested = rng.choice([True, False])
        if not check_one(select_cols, order_cols, refs, trailing_cols,
                         requested):
            return 1

    print("G-CONF OK: shadow impl == real patched SQLCompiler.get_group_by "
          "on %d inputs (%d boundary + %d fuzz, seed %d)."
          % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
