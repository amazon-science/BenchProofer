#!/usr/bin/env python3
"""G-CONF differential conformance for django__django-15563 (plan §4.1).

Refutes (does not prove) the R/I refinement leg of the single modeled function
`parentFilterIds` — the per-ancestor identity-column routing built in the
gold-patched `SQLUpdateCompiler.pre_sql_setup` and consumed by
`UpdateQuery.get_related_updates`. There are NO axioms in this bundle: the only
fact each ancestor is routed on — whether a primary-key chain reaches it from
the child (`sharesChildPk`) — is a FREE INPUT (mapping.md §2/§3), so the whole
impl region is R/I (conf_skip=false).

  * SHADOW  — Solution.lean's `stepCol` / `assignedColumns` / `idColumn` fold,
              transliterated to Python over the mapping.md bijection
              (`Parent.sharesChildPk` ↔ "all(path.join_field.primary_key for
              path in meta.get_path_to_parent(related))"; `rows : List (List
              Int)` ↔ the MULTI cursor's fetched rows; column index ↔ position
              in `fields`).

  * ORACLE  — `patch.diff`'s behaviour: the GOLD-PATCHED column-assignment of
              `pre_sql_setup` transliterated VERBATIM with its real control flow:

                  fields = [pk_name]            # column 0 = child identity
                  related_ids_index = []
                  for related in related_updates:
                      if shares_child_pk(related):
                          related_ids_index.append((related, 0))
                      else:
                          related_ids_index.append((related, len(fields)))
                          fields.append(related_pk_name)
                  # ... fetch rows ...
                  related_ids = defaultdict(list)
                  for rows_block in cursor:
                      for parent, index in related_ids_index:
                          related_ids[parent].extend(r[index] for r in rows_block)
                  # get_related_updates filters parent on related_ids[parent]

ORACLE CHOICE — why we transliterate the patched assignment instead of running
the real `pre_sql_setup`:
  The real method needs a fully-configured ORM: concrete MTI model classes, a
  migrated schema with parent-link fields, a live DB connection, and an executed
  MULTI sub-select — essentially the F2P Django test harness — purely to read
  back which fetched column each ancestor's filter is drawn from. The pieces the
  patch does NOT change (get_path_to_parent / join_field.primary_key resolution,
  and the SQL fetch itself) are abstracted into the free `sharesChildPk` flag and
  the fetched `rows`; the SAME flags/rows are handed to both SHADOW and ORACLE,
  so the only thing under differential test is the column-routing the patch
  actually edits (mapping.md §3). The downstream `get_related_updates` is a pure
  index `self.related_ids[model]`, transliterated as the per-ancestor lookup.

We fuzz random ancestor lists + fetched-row blocks (boundary scenarios first,
incl. the two F2P MTI updates). Both sides must agree on the per-ancestor list
of filter identity values. Exit 0 iff zero disagreements. stdlib only; fuzz seed
pinned (mapping.md §4).
"""
import random
import sys

SEED = 15563
N_FUZZ = 100_000


# ---- SHADOW: Solution.lean transliterated ---------------------------------
def step_col(st, shares):
    """`stepCol` transliterated. st = (cols, next); shares = p.sharesChildPk."""
    cols, nxt = st
    if shares:
        return (cols + [0], nxt)
    return (cols + [nxt], nxt + 1)


def assigned_columns(shares_list):
    """`assignedColumns`: foldl stepCol from ([], 1), read the column list."""
    st = ([], 1)
    for shares in shares_list:
        st = step_col(st, shares)
    return st[0]


def id_column(rows, idx):
    """`idColumn rows idx`: the value at column `idx` of every fetched row."""
    return [row[idx] for row in rows]


def shadow(shares_list, rows):
    """`out = (assignedColumns parents).map (idColumn rows)`."""
    return [id_column(rows, idx) for idx in assigned_columns(shares_list)]


# ---- ORACLE: gold-patched pre_sql_setup routing, verbatim ------------------
def oracle(shares_list, rows):
    # fields = [meta.pk.name]; column 0 is the child identity.
    fields = [0]  # placeholder; we only track len(fields) for column indices
    related_ids_index = []  # list of (parent_position, column_index)
    for pos, shares in enumerate(shares_list):
        if shares:
            related_ids_index.append((pos, 0))
        else:
            related_ids_index.append((pos, len(fields)))
            fields.append(pos)  # append related._meta.pk.name -> a new column
    # related_ids[parent].extend(r[index] for r in rows)
    related_ids = {}
    for parent, index in related_ids_index:
        related_ids.setdefault(parent, [])
        related_ids[parent].extend(r[index] for r in rows)
    # get_related_updates: query.add_filter("pk__in", self.related_ids[model]),
    # one query per ancestor in order.
    return [related_ids[pos] for pos in range(len(shares_list))]


# ---- fuzz inputs -----------------------------------------------------------
def fuzz_inputs(n, rng):
    for _ in range(n):
        n_parents = rng.randint(0, 5)
        shares_list = [rng.random() < 0.5 for _ in range(n_parents)]
        # rows: a block of fetched tuples. Each row must carry one value per
        # column produced by `fields`: 1 (the child pk) + (# non-shared
        # ancestors). The mapping.md bijection ties row width to that count.
        n_cols = 1 + sum(1 for s in shares_list if not s)
        n_rows = rng.randint(0, 4)
        rows = [[rng.randint(-50, 50) for _ in range(n_cols)]
                for _ in range(n_rows)]
        yield shares_list, rows


def boundary_checks():
    """Boundary scenarios incl. the two F2P MTI updates, asserted against BOTH
    shadow and oracle so a transcription error in either is caught up front.

    Each entry: (name, shares_list, rows, expected_out)."""
    out = []
    # (F2P a) Congressman.objects.update(title=...): one ancestor (Politician)
    # whose parent-link is NOT the child pk -> own column (index 1). Two matched
    # children with identities (child_pk, politician_pk): (10,1),(20,2).
    rows_a = [[10, 1], [20, 2]]
    out.append(("congressman_update", [False], rows_a, [[1, 2]]))
    # (F2P b) Senator.objects.update(title=...): one ancestor (Politician) two
    # levels up; the chain Senator->Congressman->Politician is not all-pk ->
    # own column (index 1).
    rows_b = [[100, 7], [200, 8]]
    out.append(("senator_update", [False], rows_b, [[7, 8]]))
    # (c) one ancestor sharing the child pk -> column 0 (reuse child identity).
    rows_c = [[5], [6], [7]]
    out.append(("shared_pk_parent", [True], rows_c, [[5, 6, 7]]))
    # (d) mix: shared, then non-shared, then shared.
    #   columns: [0, 1, 0]; rows have 2 columns (1 child + 1 non-shared).
    rows_d = [[3, 30], [4, 40]]
    out.append(("mixed", [True, False, True], rows_d,
                [[3, 4], [30, 40], [3, 4]]))
    # (e) no ancestors -> no related updates.
    out.append(("none", [], [[9]], []))
    # (f) two non-shared ancestors -> columns [1, 2].
    rows_f = [[1, 11, 21], [2, 12, 22]]
    out.append(("two_nonshared", [False, False], rows_f, [[11, 12], [21, 22]]))
    return out


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    for name, shares_list, rows, expected in boundary_checks():
        count += 1
        s = shadow(shares_list, rows)
        o = oracle(shares_list, rows)
        if s != o:
            disagreements.append(("boundary:%s shadow!=oracle" % name, s, o))
        elif s != expected:
            disagreements.append(("boundary:%s != expected" % name, s, expected))

    for shares_list, rows in fuzz_inputs(N_FUZZ, rng):
        count += 1
        s = shadow(shares_list, rows)
        o = oracle(shares_list, rows)
        if s != o:
            disagreements.append((("shares=%r rows=%r" % (shares_list, rows)),
                                  s, o))
        if len(disagreements) >= 8:
            break

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s) over %d checks:"
              % (len(disagreements), count))
        for d in disagreements:
            print("  %r shadow/oracle-or-expected=%r/%r" % d)
        return 1
    print("G-CONF OK: R/I shadow of parentFilterIds agrees with the gold-patched "
          "pre_sql_setup column routing on %d checks (boundary F2P scenarios + "
          "fuzz, seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
