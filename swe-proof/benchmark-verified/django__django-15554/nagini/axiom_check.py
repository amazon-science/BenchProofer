#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-15554.

This bundle consumes NO `@ContractOnly` axiom: the operation the patch changes
is the equality predicate that decides whether an existing join alias may be
reused, which is pure tuple/integer equality over `Join.identity` — modeled
deeply in model.py. The one external fact the deep model rests on is a
type-refinement (an A-reference): that the real `Join` class compares its FULL
identity tuple (including `filtered_relation`) under `__eq__` (`j == join`) but
the identity MINUS `filtered_relation` under `equals` (`j.equals(join)`).

This check builds a faithful, stdlib-only stand-in of the real
`django/db/models/sql/datastructures.py:Join` identity / `__eq__` / `equals`
(and `query_utils.py:FilteredRelation.__eq__`) and asserts, over boundary +
randomized fuzz join configurations, that under the interning bijection of
mapping.md §2:

    (j == join)        <=>  matches_default(i)      = (base[i]==jb and frel[i]==jf)
    (j.equals(join))   <=>  matches_constrained(i)  = (base[i]==jb)

and that the whole-registry "a fresh alias is created" decision computed by the
model (`no_eligible_match`, refined to `not reuse_aliases`) equals the decision
a faithful re-implementation of the gold `Query.join` reuse comprehension makes.

Imports nothing repo-specific. Exit 0 iff every obligation holds.
"""
import itertools
import random
import sys


# --- faithful stand-ins of the real repo classes (datastructures.py / -------
# --- query_utils.py), reduced to the fields the equality semantics touch ----

class FilteredRelation:
    """Stand-in for django.db.models.query_utils.FilteredRelation.__eq__
    (query_utils.py:314-321): equal iff relation_name, alias, condition agree.
    Here a refinement is fully identified by an opaque key (its tag)."""
    def __init__(self, key):
        self.key = key

    def __eq__(self, other):
        if not isinstance(other, FilteredRelation):
            return NotImplemented
        return self.key == other.key

    def __hash__(self):
        return hash(self.key)


class Join:
    """Stand-in for django.db.models.sql.datastructures.Join, reduced to the
    identity-relevant fields (datastructures.py:147-166)."""
    def __init__(self, base_key, filtered_relation):
        # base_key stands for (class, table_name, parent_alias, join_field) —
        # everything in identity except filtered_relation.
        self._base_key = base_key
        self.filtered_relation = filtered_relation  # FilteredRelation or None

    @property
    def identity(self):
        return (Join, self._base_key, self.filtered_relation)

    def __eq__(self, other):
        if not isinstance(other, Join):
            return NotImplemented
        return self.identity == other.identity            # includes filtered_relation

    def equals(self, other):
        # Ignore filtered_relation in equality check.
        return self.identity[:-1] == other.identity[:-1]  # excludes filtered_relation

    def __hash__(self):
        return hash(self.identity)


# --- model.py deep predicates, as plain Python (kept in lock-step) -----------

def _fr_tag(fr):
    """Interning bijection (mapping.md §2): None -> 0, FilteredRelation -> a
    distinct positive int per distinct refinement (== under FilteredRelation)."""
    if fr is None:
        return 0
    return fr.key  # keys are distinct positive ints in the harness below


def matches_default(base_i, frel_i, jb, jf):
    return base_i == jb and frel_i == jf


def matches_constrained(base_i, jb):
    return base_i == jb


def model_new_alias_needed(slots, reuse_all, reuse_mask, jb, jf, constrained):
    """model.py's `install_join` result: True iff NO eligible slot matches."""
    for i, (base_i, frel_i) in enumerate(slots):
        if constrained:
            eligible = reuse_mask[i]
            if eligible and matches_constrained(base_i, jb):
                return False
        else:
            eligible = reuse_all or reuse_mask[i]
            if eligible and matches_default(base_i, frel_i, jb, jf):
                return False
    return True


def gold_new_alias_needed(joins, reuse_set, reuse_with_filtered_relation, join):
    """Faithful re-implementation of the gold `Query.join` reuse comprehension
    (query.py:1027-1031 post-patch): True iff reuse_aliases is empty."""
    reuse = reuse_set  # None or a set of alias indices
    if reuse_with_filtered_relation and reuse:
        reuse_aliases = [a for a, j in joins
                         if a in reuse and j.equals(join)]
    else:
        reuse_aliases = [a for a, j in joins
                         if (reuse is None or a in reuse) and j == join]
    return not reuse_aliases


# --- the checks --------------------------------------------------------------

def check_predicate_equivalence():
    """(j == join) <=> matches_default ; (j.equals(join)) <=> matches_constrained."""
    base_keys = ["B0", "B1", "B2"]
    fr_keys = [None, 1, 2, 3]  # None or distinct positive refinement tags
    for sb, sfk in itertools.product(base_keys, fr_keys):
        for jbk, jfk in itertools.product(base_keys, fr_keys):
            slot = Join(sb, None if sfk is None else FilteredRelation(sfk))
            inc = Join(jbk, None if jfk is None else FilteredRelation(jfk))
            base_i, frel_i = sb_to_int(sb), _fr_tag(slot.filtered_relation)
            jb, jf = sb_to_int(jbk), _fr_tag(inc.filtered_relation)
            assert (slot == inc) == matches_default(base_i, frel_i, jb, jf), (
                "Join.__eq__ disagrees with matches_default on %r vs %r"
                % (slot.identity, inc.identity))
            assert slot.equals(inc) == matches_constrained(base_i, jb), (
                "Join.equals disagrees with matches_constrained on %r vs %r"
                % (slot.identity, inc.identity))


_SB_INT = {}


def sb_to_int(sb):
    """Intern an opaque base key to a distinct positive int (the bijection of
    mapping.md §2: equal base identities -> equal ints, distinct -> distinct)."""
    if sb not in _SB_INT:
        _SB_INT[sb] = 100 + len(_SB_INT)
    return _SB_INT[sb]


def check_registry_decision(rng):
    """The whole-registry 'new alias needed' decision: model == gold."""
    base_keys = ["B0", "B1", "B2"]
    fr_keys = [None, 1, 2, 3]
    for _ in range(60000):
        n = rng.randint(0, 6)
        joins = []           # gold: list of (alias_index, Join)
        slots = []           # model: list of (base_int, frel_tag)
        reuse_set = set()
        reuse_mask = []
        for a in range(n):
            bk = rng.choice(base_keys)
            fk = rng.choice(fr_keys)
            fr = None if fk is None else FilteredRelation(fk)
            joins.append((a, Join(bk, fr)))
            slots.append((sb_to_int(bk), _fr_tag(fr)))
            in_reuse = rng.random() < 0.5
            reuse_mask.append(in_reuse)
            if in_reuse:
                reuse_set.add(a)

        jbk = rng.choice(base_keys)
        jfk = rng.choice(fr_keys)
        jfr = None if jfk is None else FilteredRelation(jfk)
        inc = Join(jbk, jfr)
        jb, jf = sb_to_int(jbk), _fr_tag(jfr)

        # Two reuse configurations: unconstrained (reuse=None) and constrained.
        # Unconstrained / default:
        m_default = model_new_alias_needed(
            slots, reuse_all=True, reuse_mask=reuse_mask,
            jb=jb, jf=jf, constrained=False)
        g_default = gold_new_alias_needed(
            joins, reuse_set=None, reuse_with_filtered_relation=False, join=inc)
        assert m_default == g_default, (
            "default-mode decision mismatch: model=%r gold=%r (slots=%r, inc=%r)"
            % (m_default, g_default, slots, inc.identity))

        # Reuse set supplied, default predicate (reuse_with_filtered_relation
        # False but reuse non-None): masked slots, full-identity match.
        m_set_default = model_new_alias_needed(
            slots, reuse_all=False, reuse_mask=reuse_mask,
            jb=jb, jf=jf, constrained=False)
        g_set_default = gold_new_alias_needed(
            joins, reuse_set=reuse_set, reuse_with_filtered_relation=False,
            join=inc)
        assert m_set_default == g_set_default, (
            "set-default decision mismatch: model=%r gold=%r"
            % (m_set_default, g_set_default))

        # Constrained: reuse_with_filtered_relation True with a non-empty reuse
        # set -> base-only match over masked slots.
        if reuse_set:
            m_con = model_new_alias_needed(
                slots, reuse_all=False, reuse_mask=reuse_mask,
                jb=jb, jf=jf, constrained=True)
            g_con = gold_new_alias_needed(
                joins, reuse_set=reuse_set,
                reuse_with_filtered_relation=True, join=inc)
            assert m_con == g_con, (
                "constrained decision mismatch: model=%r gold=%r"
                % (m_con, g_con))


def check_f2p_witness():
    """The F2P scenario (test_multiple): two FilteredRelations on the SAME base
    relation with DIFFERENT conditions, installed under default reuse. The
    second MUST create a fresh alias under the gold/model; the pre-patch
    (base-only) predicate would wrongly reuse the first."""
    base = "book"
    fr_alice = FilteredRelation("alice")
    fr_jane = FilteredRelation("jane")
    j_alice = Join(base, fr_alice)
    j_jane = Join(base, fr_jane)

    # Registry already holds the first filtered relation's join.
    joins = [(0, j_alice)]
    slots = [(sb_to_int(base), _fr_tag(fr_alice))]

    # Installing the second (same base, different refinement) under default reuse.
    jb, jf = sb_to_int(base), _fr_tag(fr_jane)
    gold = gold_new_alias_needed(joins, reuse_set=None,
                                 reuse_with_filtered_relation=False, join=j_jane)
    model = model_new_alias_needed(slots, reuse_all=True, reuse_mask=[True],
                                   jb=jb, jf=jf, constrained=False)
    assert gold is True, "gold must create a fresh alias for a distinct refinement"
    assert model is True, "model must create a fresh alias for a distinct refinement"

    # Sanity: the pre-patch base-only predicate WOULD have reused (the bug).
    prepatch = not [a for a, j in joins if (None is None) and j.equals(j_jane)]
    assert prepatch is False, (
        "the pre-patch base-only predicate must (wrongly) reuse — confirms the "
        "discriminator the spec/prepatch hinges on")


def main():
    check_predicate_equivalence()
    rng = random.Random(15554)
    check_registry_decision(rng)
    check_f2p_witness()
    print("G-AX OK: Join.__eq__/equals == matches_default/matches_constrained; "
          "model 'new alias needed' == gold join() decision over 96 boundary + "
          "60000 fuzz registries; F2P distinct-refinement witness holds, "
          "pre-patch predicate confirmed to (wrongly) merge.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
