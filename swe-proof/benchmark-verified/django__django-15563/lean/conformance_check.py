#!/usr/bin/env python3
"""G-CONF for django__django-15563.

Differential test: the R/I Python shadow of `implementation_relatedTargetIds`
(Solution.lean) vs. the behaviour of the GOLD patch over the two edited
functions (`SQLUpdateCompiler.pre_sql_setup` column selection +
`UpdateQuery.get_related_updates` per-ancestor filter).

The patched functions cannot be invoked in isolation — they drive a live DB
cursor (`execute_sql(MULTI)`) and require a fully configured MTI model graph.
So the GOLD oracle here transliterates the *exact* patched lines (read from the
post-patch `django/db/models/sql/compiler.py` + `subqueries.py`, which the
orchestrator has applied before this runs) operating on the abstracted inputs
defined in mapping.md:

  ancestors          : ordered list of ancestor identities (related_updates keys)
  shares_primary_key : per-ancestor bool == all(path.join_field.primary_key
                       for path in meta.get_path_to_parent(related))
  rows               : the result rows; rows[k][col] is the col-th selected pk

The oracle builds `related_ids_index` and `fields` exactly as the patch does
(`(related, 0)` when the PK chain holds, else `(related, len(fields))` +
append), gathers `related_ids[parent]` from `r[index]`, and emits, per ancestor
in `related_updates` order, the id list `get_related_updates` filters by.

Exit 0 iff zero disagreements over >=1e5 fuzzed inputs. stdlib-only.
"""
import json
import random
import sys

SEED = 15563          # pinned in mapping.md
N_CASES = 120_000     # >= 1e5


def lean_shadow(ancestors, shares_primary_key, rows):
    """R/I transliteration of implementation_relatedTargetIds (Solution.lean).

    op-for-op: build the (ancestor, column) assignment in one pass (shared ->
    column 0; non-shared -> next dedicated column from 1), then pair each
    ancestor with `rows[*][column]`.
    """
    next_col = 1
    assignment = []
    for a in ancestors:
        if shares_primary_key[a]:
            assignment.append((a, 0))
        else:
            assignment.append((a, next_col))
            next_col += 1
    result = []
    for (a, col) in assignment:
        result.append((a, [(r[col] if col < len(r) else 0) for r in rows]))
    return result


def gold_oracle(ancestors, shares_primary_key, rows):
    """Transliteration of the GOLD-patched lines (pre_sql_setup +
    get_related_updates) over the abstracted inputs (mapping.md)."""
    # --- pre_sql_setup: build fields + related_ids_index ---
    fields = ["pk"]                      # fields = [meta.pk.name]
    related_ids_index = []
    for related in ancestors:            # for related in self.query.related_updates
        if shares_primary_key[related]:  # all(path.join_field.primary_key ...)
            related_ids_index.append((related, 0))
        else:
            related_ids_index.append((related, len(fields)))
            fields.append("pk_%s" % related)   # fields.append(related._meta.pk.name)
    # --- gather idents per parent from the result rows ---
    related_ids = {}
    for parent, index in related_ids_index:
        related_ids.setdefault(parent, [])
    for r in rows:
        for parent, index in related_ids_index:
            related_ids[parent].append(r[index] if index < len(r) else 0)
    # --- get_related_updates: per ancestor (related_updates order), the
    #     pk__in target is related_ids[model] ---
    out = []
    for model in ancestors:              # for model, values in self.related_updates.items()
        out.append((model, list(related_ids[model])))
    return out


def rand_case(rng):
    n_anc = rng.randint(0, 5)
    # ancestor identities are distinct small ints (dict keys)
    ancestors = rng.sample(range(0, 12), n_anc)
    shares = {a: bool(rng.getrandbits(1)) for a in ancestors}
    n_nonshare = sum(0 if shares[a] else 1 for a in ancestors)
    width = 1 + n_nonshare              # column 0 + one per non-sharing ancestor
    n_rows = rng.randint(0, 6)
    rows = [[rng.randint(-1000, 1000) for _ in range(width)] for _ in range(n_rows)]
    return ancestors, shares, rows


def main():
    rng = random.Random(SEED)
    # deterministic boundary cases
    boundary = [
        ([], {}, []),
        ([3], {3: True}, [[10], [20]]),
        ([3], {3: False}, [[10, 100], [20, 200]]),
        ([7, 9], {7: True, 9: False}, [[10, 100], [20, 200]]),
        ([7, 9], {7: False, 9: False}, [[10, 100, 1000]]),
        ([1, 2, 3], {1: True, 2: True, 3: True}, [[5]]),
        ([4, 5], {4: False, 5: True}, []),
    ]
    cases = 0
    for (ancestors, shares, rows) in boundary:
        if lean_shadow(ancestors, shares, rows) != gold_oracle(ancestors, shares, rows):
            print(json.dumps({"status": "fail", "case": [ancestors, shares, rows]}))
            sys.exit(1)
        cases += 1
    for _ in range(N_CASES):
        ancestors, shares, rows = rand_case(rng)
        if lean_shadow(ancestors, shares, rows) != gold_oracle(ancestors, shares, rows):
            print(json.dumps({"status": "fail",
                              "case": [ancestors, shares, rows]}))
            sys.exit(1)
        cases += 1
    print(json.dumps({"status": "pass", "cases": cases, "seed": SEED}))
    sys.exit(0)


if __name__ == "__main__":
    main()
