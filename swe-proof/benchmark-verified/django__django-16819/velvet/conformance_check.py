#!/usr/bin/env python3
"""G-CONF differential conformance for django__django-16819 (plan §4.1).

Refutes the R/I refinement legs of refinement.md by executing both sides on the
same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated to
              Python over the *real* repo types, via the mapping.md bijection:
                removes_added_index(added_name, next) ::= the guard, AND
                out = [] (cancel) if removes_added_index else inherited_outcome
              The free input `inherited_outcome` is bound to the REAL inherited
              decision `Operation.reduce(add, op, app_label)` (UNCHANGED by the
              patch, mapping.md §3), so the differential isolates the ONE thing
              the patch adds: the cancellation guard + its `[]` branch.
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `django.db.migrations.operations.models.AddIndex.reduce`, run at
              base_commit with the gold patch applied (the real correctness
              oracle, G-RESOLVE).

There are NO axioms in this bundle: every op is pure (an isinstance/name test and
a two-way branch over free inputs), so the whole impl region is R/I-tagged
(conf_skip=false). The discriminating power: if the modeled guard were wrong
(e.g. it also compared the model name, or compared the wrong attribute), a
following RemoveIndex with the *same index name but a different model name* — or
any other mis-modeled pairing — would make SHADOW and ORACLE disagree.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + django only.
The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
Exit 0 iff zero disagreements.
"""
import random
import sys

SEED = 16819
N_FUZZ = 100_000

from django.db.migrations.operations.base import Operation
from django.db.migrations.operations.models import AddIndex, RemoveIndex
from django.db.models import Index

APP_LABEL = "myapp"


class _ElidableOp(Operation):
    """A minimal elidable operation, used only to exercise the inherited
    `Operation.reduce` elidable branches (returns [operation]/[self]); it is NOT
    a RemoveIndex, so the modeled guard must treat it as `NextOp.other`."""
    elidable = True

    def state_forwards(self, app_label, state):
        pass

    def database_forwards(self, *a):
        pass

    def database_backwards(self, *a):
        pass


def make_add(model_name, index_name):
    return AddIndex(model_name, Index(fields=["field0"], name=index_name))


# ---- SHADOW: Solution.lean transliterated ---------------------------------

def removes_added_index(added_name, op):
    """`removesAddedIndex addedName next` transliterated. The `NextOp` carrier:
    a RemoveIndex projects to `removesIndex op.name`, anything else to `other`.
    The guard fires iff the following op is a RemoveIndex whose name equals the
    added index name (mapping.md §2). Compares ONLY the index name, matching the
    gold guard (which does not consult the model name)."""
    if isinstance(op, RemoveIndex):
        return op.name == added_name          # NextOp.removesIndex name => name = addedName
    return False                              # NextOp.other => false


def shadow_reduce(add, op, app_label):
    """reduceAddIndex post-image: cancel (== []) when the guard fires, else the
    UNCHANGED inherited decision (free input `inherited_outcome`, bound to the
    real Operation.reduce)."""
    if removes_added_index(add.index.name, op):
        return []                             # Reduction.cancel
    return Operation.reduce(add, op, app_label)   # inheritedOutcome (real super())


# ---- ORACLE: patched AddIndex.reduce --------------------------------------

def oracle_reduce(add, op, app_label):
    """patch.diff's behaviour: the real patched AddIndex.reduce."""
    return add.reduce(op, app_label)


def rand_name(rng):
    pool = ["idx_a", "idx_b", "idx_pony_weight_pink", "idx_c", "i", "name_1"]
    return rng.choice(pool)


def rand_model(rng):
    return rng.choice(["Pony", "Rider", "Stable"])


def make_next(rng, added_name):
    """A fuzzed following operation, spanning every NextOp case and the cases
    that would catch a mis-modeled guard."""
    kind = rng.randint(0, 4)
    if kind == 0:                              # RemoveIndex, SAME index name
        return RemoveIndex(rand_model(rng), added_name)
    if kind == 1:                              # RemoveIndex, possibly-different name
        return RemoveIndex(rand_model(rng), rand_name(rng))
    if kind == 2:                              # another AddIndex (not RemoveIndex)
        return make_add(rand_model(rng), rand_name(rng))
    if kind == 3:                              # elidable op -> exercises super() branches
        return _ElidableOp()
    return RemoveIndex(added_name, added_name)  # RemoveIndex whose *model* == name (still name match)


def iter_inputs(n, rng):
    # boundary cases first (plan §4.1 step 4)
    yield make_add("Pony", "idx_pony_weight_pink"), RemoveIndex("Pony", "idx_pony_weight_pink")  # the F2P pair
    yield make_add("Pony", "idx_pony_weight_pink"), RemoveIndex("Pony", "other_name")            # name mismatch
    yield make_add("Pony", "idx_a"), RemoveIndex("Rider", "idx_a")                               # model mismatch, name match
    yield make_add("Pony", "idx_a"), make_add("Pony", "idx_a")                                   # not a RemoveIndex
    yield make_add("Pony", "idx_a"), _ElidableOp()                                               # elidable -> [self]
    for _ in range(n):
        add = make_add(rand_model(rng), rand_name(rng))
        nxt = make_next(rng, add.index.name)
        yield add, nxt


def normalize(out):
    """Canonical comparable form for a reduce() result (a list of operations or
    a bool). [] is the cancellation; otherwise tag by deconstructed identity so
    two equal-but-distinct objects compare equal."""
    if isinstance(out, list):
        return ("list", tuple(repr(o.deconstruct()) for o in out))
    return ("bool", bool(out))


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for add, op in iter_inputs(N_FUZZ, rng):
        count += 1
        shadow = normalize(shadow_reduce(add, op, APP_LABEL))
        oracle = normalize(oracle_reduce(add, op, APP_LABEL))
        if shadow != oracle:
            disagreements.append((add.index.name, type(op).__name__,
                                  getattr(op, "name", None), shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for d in disagreements:
            print("  added=%r next=%s next_name=%r shadow=%r oracle=%r" % d)
        return 1
    print("G-CONF OK: R/I shadow of reduceAddIndex agrees with the patched "
          "AddIndex.reduce on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
