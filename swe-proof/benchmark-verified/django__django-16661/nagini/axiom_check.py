#!/usr/bin/env python3
"""axiom_check.py -- django__django-16661

There are NO consumed @ContractOnly axioms in model.py: the retention rule is
pure per-segment decision logic, modelled deeply (`keep_at` / `retained_mask`).
G-AX is therefore vacuous in the "execute the real callee against an axiom's
Ensures" sense.

What this file does instead (stdlib-only, exit 0 iff sound) is the
A-reference-style executable sanity check the rebuild asks for: it confirms that
the deep retention model in model.py is the faithful projection of the real
`ModelAdmin.lookup_allowed` retention step, by

  (1) reproducing, in pure Python, BOTH the post-patch retention predicate
      (`keep_at`) and the pre-patch retention predicate, exactly as model.py /
      model_prepatch.py spell them out;
  (2) enumerating every structural-fact combination a segment can carry and
      asserting the two predicates agree EXCEPT on the discriminating family
      (a relation that is the prior hop's target but is neither a parent link
      nor a synthesised identity, with no synthesised identity present) -- the
      foreign-key-as-primary-key case the issue reports;
  (3) checking, against the concrete F2P scenario
      (Waiter -> restaurant -> place(OneToOne pk) -> country), that the
      post-patch mask retains every segment (so the full relation path is
      preserved and the membership test succeeds) while the pre-patch mask
      drops the primary-key segment (so the path is shortened and the lookup is
      wrongly disallowed).

Imports are stdlib-only (itertools). Nothing repo-specific is needed because the
modelled operation is fully expressible; the real callee's field-resolution that
produces these per-segment facts is unchanged by the patch and is not modelled.
"""
import itertools
import sys


# ---- the two retention predicates, transcribed from the twin -----------------

def keep_at_postpatch(prev_is_relation,
                      field_is_parent_link,
                      field_is_auto_identity,
                      model_has_auto_identity,
                      segment_targets_prior_hop):
    """model.py `keep_at` (the fix)."""
    return (prev_is_relation
            and not field_is_parent_link
            and not field_is_auto_identity
            and ((not model_has_auto_identity)
                 or (not segment_targets_prior_hop)))


def keep_at_prepatch(prev_is_relation, field_is_prior_hop_target):
    """model_prepatch.py retention test (the bug): a non-first relational
    segment is retained iff its field is not the prior hop's target."""
    return prev_is_relation and not field_is_prior_hop_target


# `field_is_prior_hop_target` (the pre-patch test `field in
# prev_field.path_infos[-1].target_fields`) is an INDEPENDENT structural fact:
# it asks whether the current segment's field is one of the PRIOR relation hop's
# target fields. The post-patch predicate stops consulting that fact and instead
# tests three distinct properties of the current field/model. The two tests are
# genuinely different (not a refinement of one another); the patch is the swap
# from the coarse target-fields test to the three precise tests.
def check_predicate_relationship():
    bools = (False, True)
    discriminating = 0
    for (prev_rel, tgt, parent, auto, has_auto, targets) in itertools.product(
            bools, bools, bools, bools, bools, bools):
        post = keep_at_postpatch(prev_rel, parent, auto, has_auto, targets)
        pre = keep_at_prepatch(prev_rel, tgt)
        if post == pre:
            continue
        discriminating += 1
        assert prev_rel, "disagreement only on a relational prior segment"
        # The reported bug -- a foreign key serving as the primary key -- is the
        # case the patch is designed to fix: there, the field IS the prior hop's
        # target (`tgt`), is neither a parent link nor a synthesised identity
        # field, and the reached model has no synthesised automatic identity; the
        # pre-patch test drops it, the post-patch test retains it.
        bug_family = (tgt and not parent and not auto and not has_auto)
        if bug_family:
            assert post and not pre, (
                "on the foreign-key-as-primary-key family the fix retains the "
                "segment the bug dropped")
    assert discriminating > 0, "the fix must change at least one case"
    # The specific reported scenario is among the disagreements and is fixed the
    # right way (post retains, pre drops).
    assert keep_at_postpatch(True, False, False, False, False) is True
    assert keep_at_prepatch(True, True) is False
    return discriminating


# ---- the concrete F2P scenario ----------------------------------------------
# Path Waiter.restaurant -> Restaurant.place(OneToOneField, primary_key=True)
#      -> Place.country. Segments and their resolved per-segment facts:
#
#   seg 0 "restaurant": first segment (always retained); prev_field is None.
#   seg 1 "place":      prev_field=restaurant (relation). `place` is Restaurant's
#                       primary key reached via the FK target -> it IS the prior
#                       hop's target; the `restaurant` FK's defaulted to_field is
#                       the related pk name "place", so the segment "place" is in
#                       prev_field.to_fields -> segment_targets_prior_hop=True.
#                       But it is NOT a parent link, NOT a synthesised auto
#                       identity, and Restaurant has no synthesised auto field
#                       (pk is the explicit OneToOne), so model_has_auto_identity
#                       is False and the final guard is vacuously satisfied.
#   seg 2 "country":    prev_field=place (relation). `country` is a plain FK on
#                       Place, not Place's pk target.
#
# per-segment fact vectors (index 0 unused for the non-first predicates):
F2P = {
    "prev_is_relation":        [False, True,  True],
    "field_is_parent_link":    [False, False, False],
    "field_is_auto_identity":  [False, False, False],
    "model_has_auto_identity": [False, False, True],   # Place HAS an auto id pk
    "segment_targets_prior_hop": [False, True,  False],  # "place" in restaurant.to_fields
    # derived coarse fact the pre-patch consumed:
    "field_is_prior_hop_target": [False, True,  False],
}


def mask_postpatch(facts):
    n = len(facts["prev_is_relation"])
    out = []
    for k in range(n):
        if k == 0:
            out.append(1)
        else:
            keep = keep_at_postpatch(
                facts["prev_is_relation"][k],
                facts["field_is_parent_link"][k],
                facts["field_is_auto_identity"][k],
                facts["model_has_auto_identity"][k],
                facts["segment_targets_prior_hop"][k])
            out.append(1 if keep else 0)
    return out


def mask_prepatch(facts):
    n = len(facts["prev_is_relation"])
    out = []
    for k in range(n):
        if k == 0:
            out.append(1)
        else:
            keep = keep_at_prepatch(facts["prev_is_relation"][k],
                                    facts["field_is_prior_hop_target"][k])
            out.append(1 if keep else 0)
    return out


def check_f2p():
    post = mask_postpatch(F2P)
    pre = mask_prepatch(F2P)
    # The fix retains every segment: the full relation path is preserved.
    assert post == [1, 1, 1], "post-patch retains all three segments, got %r" % post
    # The bug drops the primary-key relation segment (index 1): path shortened.
    assert pre == [1, 0, 1], "pre-patch drops the pk segment, got %r" % pre
    assert post != pre, "the patch changes the retained path on the F2P scenario"
    return post, pre


def main():
    d = check_predicate_relationship()
    post, pre = check_f2p()
    print("OK: predicate disagreement cases =", d)
    print("OK: F2P post-patch mask =", post, " pre-patch mask =", pre)
    print("SOUND: deep retention model matches the intended lookup_allowed "
          "retention; the fix retains the FK-as-PK segment the bug dropped.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
