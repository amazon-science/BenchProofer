#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-16661 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW — the R/I-tagged ops of Solution.lean's impl region transliterated to
             Python over the real repo per-hop state (the `Hop` -> the loop's
             per-iteration introspection facts, mapping.md §2). Two pieces:
               (a) `keepSegment` — the deep model of the CHANGED per-segment keep
                   decision (Solution.lean's Boolean combination, step A7);
               (b) the backward `while` fold of `keptSegments` (build `result` by
                   prepending while a decreasing index walks the path, step A8).
             There are NO A-tagged callees in the impl region, so the shadow is
             pure R/I.
  * ORACLE — `patch.diff`'s behaviour: the patched append guard, transcribed
             INDEPENDENTLY from the gold patch's `+` lines (NOT copied from
             keepSegment's spelling), applied left-to-right (`relation_parts`
             forward append) over the same walked path.

They must agree on every walked path. Two differential properties are checked:

  1. keep-decision fidelity (refutes A4-A7): SHADOW `keepSegment(h)` ==
     ORACLE patched-guard(h) over ALL 2**7 = 128 single-`Hop` configurations and
     over every hop of every fuzzed path. A mis-transliterated Boolean in
     Solution.lean would diverge from the independent patch transcription here.
  2. fold order-faithfulness (refutes A8): the backward prepend-fold produces the
     SAME per-segment flag stream as the forward append. A loop-direction or
     off-by-one error would diverge.

Exit 0 iff zero disagreements over all configs + >=10**5 fuzzed paths; any
disagreement is a mechanical R/I-fidelity counterexample. Runs in-container,
stdlib-only. The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import itertools
import random
import sys

SEED = 16661
N_FUZZ = 100_000

# Field order of the Lean `Hop` structure (Solution.lean).
HOP_FIELDS = (
    "isFirst", "priorIsRelation", "concreteParentLink", "redundantLocalValue",
    "hasRedundantLocalValue", "priorAlreadyCovers", "targetOfPrior",
)


# --- the R/I SHADOW: Solution.lean keepSegment, transliterated verbatim -------
# keepSegment (h : Hop) : Bool :=
#   h.isFirst ||
#   (h.priorIsRelation && !h.concreteParentLink && !h.redundantLocalValue
#     && (!h.hasRedundantLocalValue || !h.priorAlreadyCovers))
def shadow_keep_segment(h):
    return h["isFirst"] or (
        h["priorIsRelation"]
        and not h["concreteParentLink"]
        and not h["redundantLocalValue"]
        and (not h["hasRedundantLocalValue"] or not h["priorAlreadyCovers"])
    )


def shadow_kept_segments(hops):
    """The backward `while i>0` fold of keptSegments: walk the path from the end,
    prepending each segment's flag. Transliterated from the impl `do` block."""
    result = []
    i = len(hops)
    while i > 0:
        h = hops[i - 1]
        result = [shadow_keep_segment(h)] + result
        i = i - 1
    return result


# --- the ORACLE: patch.diff's patched append guard, transcribed from + lines --
# Post-patch guard (django/contrib/admin/options.py:464-470):
#   if not prev_field or (
#       prev_field.is_relation
#       and field not in model._meta.parents.values()
#       and field is not model._meta.auto_field
#       and (model._meta.auto_field is None
#            or part not in getattr(prev_field, "to_fields", []))):
#       relation_parts.append(part)
#
# Under mapping.md §2:  not prev_field          <-> isFirst
#                       prev_field.is_relation  <-> priorIsRelation
#                       field in parents.values <-> concreteParentLink
#                       field is auto_field      <-> redundantLocalValue
#                       auto_field is not None   <-> hasRedundantLocalValue
#                       part in prev_field.to_fields <-> priorAlreadyCovers
def oracle_patched_guard(h):
    not_prev_field = h["isFirst"]
    prev_is_relation = h["priorIsRelation"]
    field_in_parents = h["concreteParentLink"]
    field_is_auto = h["redundantLocalValue"]
    auto_is_not_none = h["hasRedundantLocalValue"]
    part_in_to_fields = h["priorAlreadyCovers"]
    # transcribed structurally from the + lines:
    return not_prev_field or (
        prev_is_relation
        and (not field_in_parents)            # field not in parents.values()
        and (not field_is_auto)               # field is not auto_field
        and (
            (not auto_is_not_none)            # auto_field is None
            or (not part_in_to_fields)        # OR part not in to_fields
        )
    )


def oracle_relation_mask(hops):
    """patch.diff behaviour: forward left-to-right append, recording per segment
    whether the patched guard fired (the keep/drop flag stream `relation_parts`
    is the filter-true projection of)."""
    mask = []
    for h in hops:
        mask.append(bool(oracle_patched_guard(h)))
    return mask


# --- fuzzing ------------------------------------------------------------------

def all_single_hops():
    for bits in itertools.product((False, True), repeat=len(HOP_FIELDS)):
        yield dict(zip(HOP_FIELDS, bits))


def rand_hop(rng):
    return {f: bool(rng.getrandbits(1)) for f in HOP_FIELDS}


def fuzz_paths(n, rng):
    # boundary: empty path, every single-Hop config, and the F2P discriminator
    yield []
    for h in all_single_hops():
        yield [h]
    # the FK-as-PK genuine-descent segment the F2P test exercises:
    fk_pk = {
        "isFirst": False, "priorIsRelation": True, "concreteParentLink": False,
        "redundantLocalValue": False, "hasRedundantLocalValue": True,
        "priorAlreadyCovers": False, "targetOfPrior": True,
    }
    yield [fk_pk]
    yield [{**fk_pk, "isFirst": True}, fk_pk, {**fk_pk, "hasRedundantLocalValue": False}]
    for _ in range(n):
        k = rng.randint(0, 8)
        yield [rand_hop(rng) for _ in range(k)]


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    # property 1: keep-decision fidelity over ALL 128 single-Hop configs
    for h in all_single_hops():
        if bool(shadow_keep_segment(h)) != bool(oracle_patched_guard(h)):
            disagreements.append(("single", h, shadow_keep_segment(h),
                                  oracle_patched_guard(h)))

    # properties 1 & 2 over fuzzed paths: per-segment decision + fold order
    for hops in fuzz_paths(N_FUZZ, rng):
        count += 1
        shadow = [bool(x) for x in shadow_kept_segments(hops)]
        oracle = oracle_relation_mask(hops)
        if shadow != oracle:
            disagreements.append(("path", hops, shadow, oracle))
        if len(disagreements) >= 5:
            break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s):" % len(disagreements))
        for kind, inp, sh, orc in disagreements:
            print("  [%s] input=%r shadow=%r oracle=%r" % (kind, inp, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of keptSegments (keepSegment + backward fold) "
          "agrees with patch.diff append-guard behaviour on all 128 single-Hop "
          "configs + %d fuzzed paths (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
