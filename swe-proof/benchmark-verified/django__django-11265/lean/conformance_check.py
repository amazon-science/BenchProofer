#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-11265.

The bundle models TWO pure decisions the query layer makes when an exclude over a
to-many relation is rewritten into a negated subquery (mapping.md):

  1. buildInnerQuery — constructing the nested inner query: which model it binds
     to, which named filtered-relation definitions it carries, the applied filter,
     and that ordering is dropped.
  2. selectInnerJoin — whether the inner query's leading join may be collapsed,
     and which related-field names / alias are selected as a result.

Standing up Django's full ORM + a database to drive `Query.split_exclude` /
`Query.trim_start` is heavy and unnecessary: each modeled value is exactly the
pure decision over the observables the real routine reads at the decision point.
So each ORACLE below is a faithful in-process replica using the EXACT patched
expressions; each SHADOW is the op-for-op transliteration of the Lean impl
(per refinement.md). stdlib-only. Pinned seed: 20240627 (also in mapping.md).
"""
import random
import sys

SEED = 20240627
N = 120_000


# ============================ buildInnerQuery ================================
# Each applied filter is recorded together with the named-relation context present
# WHEN it was applied (the sequencing the bug is about: the filter must resolve
# against the carried-over relations). State = (model, filtered_relations,
# applied_filters, ordering_cleared) where applied_filters is a list of
# (filter_expr, relation_context_snapshot).
def _fresh(model):
    return [model, [], [], False]


def _with_filtered_relations(q, frs):
    q[1] = list(frs)
    return q


def _add_filter(q, fe):
    q[2] = q[2] + [(fe, list(q[1]))]   # snapshot relation context at apply time
    return q


def _clear_ordering(q):
    q[3] = True
    return q


# ORACLE: faithful replica of the patched split_exclude inner-query construction.
#   query = Query(self.model)
#   query._filtered_relations = self._filtered_relations     # gold-added line
#   query.add_filter(filter_expr)                            # resolves against them
#   query.clear_ordering(True)
def oracle_build(self_model, self_filtered_relations, filter_expr):
    q = _fresh(self_model)
    q = _with_filtered_relations(q, self_filtered_relations)
    q = _add_filter(q, filter_expr)
    q = _clear_ordering(q)
    return (q[0], q[1], q[2], q[3])


# SHADOW of implementation_buildInnerQuery (R / A-reference legs): same op order
# via freshInnerQuery / withFilteredRelations / addFilter / clearOrdering.
def shadow_build(self_model, self_filtered_relations, filter_expr):
    q = _fresh(self_model)
    q = _with_filtered_relations(q, self_filtered_relations)
    q = _add_filter(q, filter_expr)
    q = _clear_ordering(q)
    return (q[0], q[1], q[2], q[3])


def disagree_build(sm, sfr, fe):
    o = oracle_build(sm, sfr, fe)
    s = shadow_build(sm, sfr, fe)
    return None if o == s else ((sm, sfr, fe), o, s)


# ============================ selectInnerJoin ================================
# ORACLE: faithful replica of the patched trim_start leading-join decision.
#   first_join = alias_map[...]
#   if first_join.join_type != LOUTER and not first_join.filtered_relation:
#       select_fields = [r[0] for r in related_fields]; select_alias = collapsed
#   else:
#       select_fields = [r[1] for r in related_fields]; select_alias = original
# keeps_outer_rows == (join_type == LOUTER); carries_relation_condition ==
# bool(first_join.filtered_relation).
def oracle_select(keeps_outer_rows, carries_relation_condition,
                  related_fields, alias_original, alias_collapsed):
    can_collapse = (not keeps_outer_rows) and (not carries_relation_condition)
    if can_collapse:
        return ([r[0] for r in related_fields], alias_collapsed)
    else:
        return ([r[1] for r in related_fields], alias_original)


# SHADOW of implementation_selectInnerJoin.
#   canCollapse = (!keepsOuterRows) && (!carriesRelationCondition)
#   if canCollapse: (relatedFields.map .1, aliasCollapsed)
#   else:           (relatedFields.map .2, aliasOriginal)
def shadow_select(keeps_outer_rows, carries_relation_condition,
                  related_fields, alias_original, alias_collapsed):
    can_collapse = (not keeps_outer_rows) and (not carries_relation_condition)
    if can_collapse:
        return ([r[0] for r in related_fields], alias_collapsed)
    return ([r[1] for r in related_fields], alias_original)


def disagree_select(kor, crc, rf, ao, ac):
    o = oracle_select(kor, crc, rf, ao, ac)
    s = shadow_select(kor, crc, rf, ao, ac)
    return None if o == s else ((kor, crc, rf, ao, ac), o, s)


# ================================ drivers ===================================
MODELS = ["Author", "Book", "Editor", "Reservation"]
ALIASES = ["filtered_relation_author", "book_alice", "U1", "T2", "base", ""]
FR_DEFS = ["book", "book_alice=FilteredRelation(book)", "favorite_books", "poem"]
FILTERS = [("book_alice__isnull", "False"), ("name__iexact", "alice"),
           ("pk__in", "subquery"), ("id", "1")]


def _build_edge_cases():
    cases = []
    # no named relations carried (carrying [] equals [], but distinguishes the bug)
    cases.append(("Author", [], ("book_alice__isnull", "False")))
    # the F2P shape: a single named filtered relation must be carried over.
    cases.append(("Author", [("book_alice", "FilteredRelation(book)")],
                  ("book_alice__isnull", "False")))
    # multiple named relations, order preserved.
    cases.append(("Book", [("a", "FilteredRelation(x)"), ("b", "FilteredRelation(y)")],
                  ("name__iexact", "alice")))
    return cases


def _select_edge_cases():
    rf = [("author_id", "id")]
    cases = []
    for kor in (True, False):
        for crc in (True, False):
            cases.append((kor, crc, rf, "src_alias", "dst_alias"))
    # the F2P shape: INNER join (keeps_outer=False) from a filtered relation
    # (carries_condition=True) must NOT be collapsed.
    cases.append((False, True, [("author_id", "id"), ("x", "y")],
                  "filtered_relation_author", "book_alice"))
    # empty related-fields list.
    cases.append((False, False, [], "a", "b"))
    return cases


def main() -> int:
    checked = 0
    for sm, sfr, fe in _build_edge_cases():
        d = disagree_build(sm, sfr, fe)
        if d:
            print(f"DISAGREE build edge {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1
    for kor, crc, rf, ao, ac in _select_edge_cases():
        d = disagree_select(kor, crc, rf, ao, ac)
        if d:
            print(f"DISAGREE select edge {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        # buildInnerQuery fuzz
        sm = rng.choice(MODELS)
        nfr = rng.randint(0, 4)
        sfr = [(rng.choice(ALIASES), rng.choice(FR_DEFS)) for _ in range(nfr)]
        fe = rng.choice(FILTERS)
        d = disagree_build(sm, sfr, fe)
        if d:
            print(f"DISAGREE build fuzz {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

        # selectInnerJoin fuzz
        kor = rng.choice([True, False])
        crc = rng.choice([True, False])
        nrf = rng.randint(0, 4)
        rf = [(rng.choice(ALIASES), rng.choice(ALIASES)) for _ in range(nrf)]
        ao = rng.choice(ALIASES)
        ac = rng.choice(ALIASES)
        d = disagree_select(kor, crc, rf, ao, ac)
        if d:
            print(f"DISAGREE select fuzz {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
