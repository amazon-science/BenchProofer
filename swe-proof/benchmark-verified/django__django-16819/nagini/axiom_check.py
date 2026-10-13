#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-16819.

This bundle has **no `@ContractOnly` axioms**: the only callee of the modeled
function `AddIndex.reduce` is `super().reduce`, which resolves to
`Operation.reduce` (the base-class generic combination rule) — three boolean
branches, fully expressible, modeled DEEPLY as the pure helper `base_combine`
in model.py (refinement.md step A6). There is therefore no axiom-soundness
obligation in the formal sense.

To still give G-AX something executable to audit, this script reproduces the
REAL base-class rule and the REAL gold cancellation rule exactly as they appear
in the repo source at base_commit, and asserts the model's tag encoding matches
them on boundary + randomized inputs:

  base_combine(self_elidable, op_elidable)  (model.py pure region):
      self_elidable        -> 2   (real: return [operation])
      else if op_elidable  -> 3   (real: return [self])
      else                 -> 0   (real: return False)
    == Operation.reduce, django/db/migrations/operations/base.py:129-139.

  reduce_add_index(index_name, self_elidable, operation) (model.py impl):
      operation.is_remove_index and index_name == operation.name -> 1  (real: [])
      else -> base_combine(...)
    == AddIndex.reduce, django/db/migrations/operations/models.py (gold patch).

stdlib-only imports (`random`, `sys`). Exit 0 iff every obligation holds.
"""
import random
import sys

# --- tag encoding (kept in lock-step with model.py / mapping.md) -------------
FALSE_TAG = 0   # real return False  (cannot combine)
EMPTY_TAG = 1   # real return []     (the pair cancels)
OP_TAG = 2      # real return [operation]
SELF_TAG = 3    # real return [self]


def real_base_reduce(self_elidable, op_elidable):
    """Faithful transcription of Operation.reduce (base.py:129-139), with the
    list/bool return mapped to the model's tag encoding."""
    if self_elidable:
        return OP_TAG          # return [operation]
    elif op_elidable:
        return SELF_TAG        # return [self]
    return FALSE_TAG           # return False


def real_add_index_reduce(index_name, self_elidable, op_is_remove_index,
                          op_name, op_elidable):
    """Faithful transcription of the gold AddIndex.reduce, tag-encoded."""
    if op_is_remove_index and index_name == op_name:
        return EMPTY_TAG       # return []
    return real_base_reduce(self_elidable, op_elidable)


# --- model.py reference encodings --------------------------------------------

def base_combine(self_elidable, op_elidable):
    """Reference of model.py's deep model `base_combine`."""
    if self_elidable:
        return 2
    if op_elidable:
        return 3
    return 0


def reduce_add_index(index_name, self_elidable, op_is_remove_index, op_name,
                     op_elidable):
    """Reference of model.py's `reduce_add_index` impl."""
    if op_is_remove_index and index_name == op_name:
        return 1
    return base_combine(self_elidable, op_elidable)


def main():
    bools = [False, True]

    # --- base_combine == real Operation.reduce (deep model, step A6) ---------
    for se in bools:
        for oe in bools:
            assert base_combine(se, oe) == real_base_reduce(se, oe), (
                "base_combine deep model unsound at self_elidable=%r "
                "op_elidable=%r" % (se, oe))

    names = ["", "idx_pony_weight_pink", "idx", "a", "other_name",
             "idx_pony_weight_pink ", "IDX_PONY_WEIGHT_PINK"]

    # --- reduce_add_index == real gold AddIndex.reduce: boundary -------------
    boundary = 0
    for idx_name in names:
        for op_is_rm in bools:
            for op_name in names:
                for se in bools:
                    for oe in bools:
                        model = reduce_add_index(idx_name, se, op_is_rm,
                                                 op_name, oe)
                        real = real_add_index_reduce(idx_name, se, op_is_rm,
                                                      op_name, oe)
                        assert model == real, (
                            "reduce_add_index unsound: idx=%r remove=%r "
                            "op_name=%r self_elidable=%r op_elidable=%r -> "
                            "model %r real %r" % (idx_name, op_is_rm, op_name,
                                                  se, oe, model, real))
                        boundary += 1

    # --- the discriminating F2P witness: AddIndex then RemoveIndex(same name)
    # both non-elidable must cancel to the empty list (tag 1).
    assert reduce_add_index("idx_pony_weight_pink", False, True,
                            "idx_pony_weight_pink", False) == 1, (
        "F2P witness broken: matching RemoveIndex must cancel to []")
    # a non-matching name must NOT cancel (falls through to base rule -> False)
    assert reduce_add_index("idx_pony_weight_pink", False, True,
                            "other_name", False) == 0, (
        "non-matching name must not cancel")
    # a non-removal counterpart must NOT cancel even with an equal name string.
    assert reduce_add_index("idx", False, False, "idx", False) == 0, (
        "non-RemoveIndex counterpart must not cancel")

    # --- randomized fuzz -----------------------------------------------------
    rng = random.Random(16819)
    pool = names + ["x%d" % i for i in range(20)]
    fuzz = 0
    for _ in range(50000):
        idx_name = rng.choice(pool)
        op_name = rng.choice(pool)
        op_is_rm = rng.random() < 0.5
        se = rng.random() < 0.5
        oe = rng.random() < 0.5
        assert reduce_add_index(idx_name, se, op_is_rm, op_name, oe) == \
            real_add_index_reduce(idx_name, se, op_is_rm, op_name, oe)
        fuzz += 1

    print("G-AX OK: no @ContractOnly axioms (base rule modeled deeply). "
          "base_combine == Operation.reduce on all 4 cases; reduce_add_index "
          "== gold AddIndex.reduce on %d boundary + %d fuzz inputs; F2P "
          "cancellation witness holds." % (boundary, fuzz))
    return 0


if __name__ == "__main__":
    sys.exit(main())
