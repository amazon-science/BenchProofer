#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-15554.

The computation under specification (which existing registry entries a requested
entry may share) is modeled DEEPLY in Solution.lean — there is no axiomatized or
deep-modeled *callee*. What the deep model leans on is the REPOSITORY COMPARISON
SEMANTICS of an entry (a `Join`), abstracted by the mapping.md §2 bijection:

  * a `Join`'s structural identity        -> EntryId.structKey (a Nat)
  * a `Join`'s `filtered_relation` tag    -> EntryId.refineTag (a Nat)

and the two Lean relations

  * matchesStructural (structKey only)    models  Join.equals  (identity[:-1])
  * matchesExact      (structKey+tag)     models  Join.__eq__  (full identity)

This check builds REAL `Join` objects over fuzzed component tuples and asserts
the real comparison methods agree, value-for-value, with the abstraction:

  Join.equals(a, b)  ==  matchesStructural(model(a), model(b))
  (a == b)           ==  matchesExact(model(a), model(b))

i.e. `equals` drops the refinement tag while `==` keeps it — the property the
whole spec turns on (a structural-but-not-exact match is shareable under the OLD
rule, NOT under the new one). Imports only django + stdlib. Exit 0 iff sound.
"""
import itertools
import random
import sys

from django.db.models.sql.datastructures import Join
from django.db.models.query_utils import FilteredRelation, Q


# --- a minimal join_field: identity-compared, with the API Join.__init__ uses -
class FakeField:
    """A stand-in join_field. Distinct instances are unequal (default identity
    __eq__), exactly as distinct real join_field objects are; get_joining_columns
    is the only method Join.__init__ touches."""

    def __init__(self, tag):
        self.tag = tag

    def get_joining_columns(self):
        return ()


def make_join(table_name, parent_alias, field, fr):
    """Build a real Join over the four identity-relevant components (table_alias,
    join_type, nullable do NOT enter identity, so we hold them fixed)."""
    return Join(
        table_name=table_name,
        parent_alias=parent_alias,
        table_alias="ta",
        join_type=None,
        join_field=field,
        nullable=False,
        filtered_relation=fr,
    )


def model_ids(components, fields, frs):
    """Assign each distinct structural-identity tuple a structKey Nat and each
    distinct filtered_relation a refineTag Nat, per mapping.md §2. Dedup of frs
    uses FilteredRelation.__eq__ (None handled separately)."""
    struct_ids = {}
    # refineTag dedup: None -> 0; each distinct FilteredRelation -> a fresh id.
    fr_ids = []  # list of (representative, id), compared with ==

    def refine_id(fr):
        if fr is None:
            return 0
        for rep, rid in fr_ids:
            if rep is not None and rep == fr:
                return rid
        rid = len(fr_ids) + 1
        fr_ids.append((fr, rid))
        return rid

    def struct_id(table_name, parent_alias, field):
        # identity[:-1] = (class, table_name, parent_alias, join_field); class is
        # constant (Join). join_field compared by identity (FakeField -> id()).
        key = (table_name, parent_alias, id(field))
        if key not in struct_ids:
            struct_ids[key] = len(struct_ids) + 1
        return struct_ids[key]

    return struct_id, refine_id


def main():
    rng = random.Random(15554)

    table_names = ["t_book", "t_author", "t_publisher"]
    parents = ["A", "B", "C"]
    fields = [FakeField(i) for i in range(3)]
    # filtered_relation values: None plus several distinct FilteredRelations
    # (some with identical args -> equal under FilteredRelation.__eq__).
    frs = [
        None,
        FilteredRelation("book", condition=Q(book__title__contains="Alice")),
        FilteredRelation("book", condition=Q(book__title__icontains="Jane")),
        FilteredRelation("book", condition=Q(book__title__contains="Alice")),  # == frs[1]
        FilteredRelation("author", condition=Q(author__name="x")),
    ]

    struct_id, refine_id = model_ids(None, fields, frs)

    # --- build a population of real Joins over the component grid -------------
    population = []
    for tn, pa, fld, fr in itertools.product(table_names, parents, fields, frs):
        j = make_join(tn, pa, fld, fr)
        sk = struct_id(tn, pa, fld)
        rt = refine_id(fr)
        population.append((j, sk, rt))

    def model_struct(sk_a, sk_b):
        return sk_a == sk_b

    def model_exact(a, b):
        sk_a, rt_a = a
        sk_b, rt_b = b
        return sk_a == sk_b and rt_a == rt_b

    checked = 0
    # --- exhaustive boundary: every ordered pair in the grid ------------------
    for (ja, ska, rta), (jb, skb, rtb) in itertools.product(population, repeat=2):
        real_equals = ja.equals(jb)
        real_eq = (ja == jb)
        assert real_equals == model_struct(ska, skb), (
            "equals/matchesStructural mismatch: equals=%r model=%r "
            "(sk %r vs %r)" % (real_equals, model_struct(ska, skb), ska, skb))
        assert real_eq == model_exact((ska, rta), (skb, rtb)), (
            "__eq__/matchesExact mismatch: ==%r model=%r (sk %r/%r rt %r/%r)"
            % (real_eq, model_exact((ska, rta), (skb, rtb)), ska, skb, rta, rtb))
        # the discriminating property: a structural-but-not-exact pair (same
        # structKey, different refineTag) is equals-True but ==-False.
        if ska == skb and rta != rtb:
            assert real_equals and not real_eq, (
                "expected structural-only match to be equals-True/==-False, "
                "got equals=%r ==%r" % (real_equals, real_eq))
        checked += 1

    # --- randomized fuzz over fresh component draws ---------------------------
    fuzz = 0
    for _ in range(20000):
        comps = []
        for _ in range(2):
            tn = rng.choice(table_names)
            pa = rng.choice(parents)
            fld = rng.choice(fields)
            fr = rng.choice(frs)
            comps.append((tn, pa, fld, fr))
        (tn1, pa1, f1, fr1), (tn2, pa2, f2, fr2) = comps
        ja, jb = make_join(*comps[0]), make_join(*comps[1])
        ska, skb = struct_id(tn1, pa1, f1), struct_id(tn2, pa2, f2)
        rta, rtb = refine_id(fr1), refine_id(fr2)
        assert ja.equals(jb) == model_struct(ska, skb)
        assert (ja == jb) == model_exact((ska, rta), (skb, rtb))
        fuzz += 1

    print("G-AX OK: Join.equals == matchesStructural (refinement tag dropped) "
          "and Join.__eq__ == matchesExact (tag included) on %d boundary pairs "
          "+ %d fuzz pairs; structural-only matches confirmed equals-True/"
          "==-False." % (checked, fuzz))
    return 0


if __name__ == "__main__":
    sys.exit(main())
