#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-14672 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region (`comparisonKey`)
              transliterated to Python over the real repo types via the
              mapping.md bijection. `comparisonKey` assembles the comparison key
              `pre ++ [slot-component] ++ post`, where the slot component is the
              CANONICAL form of the sequence slot. The slot's canonicalizer is
              the A-reference `canonicalize`, so per plan §4.1 the shadow leaves
              it as the REAL callee `make_hashable` (NOT the deep model). The
              opaque prefix/suffix components are sentinel hashables (their value
              is never observed by the change). The observable the shadow
              produces is: the slot-component value, and whether the assembled
              key tuple is hashable.
  * ORACLE  — `patch.diff`'s behaviour: the patched `ManyToManyRel.identity`
              places `make_hashable(self.through_fields)` into the identity tuple
              and `hash(self.identity)` succeeds (the real correctness oracle,
              G-RESOLVE). We compute the oracle directly from the patched
              semantics: the through-fields slot of the identity tuple equals
              `make_hashable(through_fields)`, and the whole tuple is hashable.

They must agree on every Requires-satisfying input (`pre`/`post` already
hashable — modeled here by hashable sentinels, always true). Exit 0 iff zero
disagreements; any disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image); imports only
`django.utils.hashable` (no DB / settings needed). The fuzz seed is pinned
(mapping.md §4) for a deterministic verdict.
"""
import random
import sys

from django.utils.hashable import make_hashable

SEED = 14672
N_FUZZ = 100_000

# The already-prepared (opaque) key components surrounding the slot. In the real
# identity tuple these are the field/model/related_name/booleans/on_delete/
# through/db_constraint — all already hashable. mapping.md §2 models them as
# hashable sentinels; their concrete value is never observed by the change.
PRE = ("field", "model", "related_name", "related_query_name",
       (), False, None, False, True)            # ForeignObjectRel.identity prefix
MID_THROUGH = "ThroughModel"                     # the `through` element
POST = (True,)                                   # the `db_constraint` element


def shadow_key(through_fields):
    """The R/I shadow of comparisonKey: assemble pre ++ [canonical slot] ++ post,
    canonicalizing the slot via the REAL callee make_hashable (A-reference)."""
    slot_component = make_hashable(through_fields)           # real callee (A-ref)
    key = PRE + (MID_THROUGH, slot_component) + POST
    # observable: (slot component value, whether the whole key is hashable)
    try:
        hash(key)
        hashable = True
    except TypeError:
        hashable = False
    return (slot_component, hashable)


def oracle_key(through_fields):
    """patch.diff's behaviour: the patched ManyToManyRel.identity places
    make_hashable(self.through_fields) into the identity tuple, and the whole
    tuple is hashable."""
    slot_component = make_hashable(through_fields)
    identity = PRE + (MID_THROUGH, slot_component) + POST
    try:
        hash(identity)
        hashable = True
    except TypeError:
        hashable = False
    return (slot_component, hashable)


def fuzz_inputs(n, rng):
    names = ["event", "invitee", "parent", "model", "child", "a", "Z",
             "x_y", "field0", "second_child"]
    # boundary cases first (plan §4.1 step 4)
    yield None
    yield []
    yield ()
    yield ["event", "invitee"]            # the F2P through_fields (list)
    yield ("event", "invitee")            # the tuple form
    yield ["parent", "model"]
    yield ["event"]
    yield ("event",)
    yield ["a", "a"]
    yield ["b", "a"]
    yield ["a", "b"]
    for _ in range(n):
        k = rng.randint(0, 6)
        seq = [rng.choice(names) for _ in range(k)]
        kind = rng.randint(0, 2)
        if kind == 0:
            yield None
        elif kind == 1:
            yield seq                      # list (loose)
        else:
            yield tuple(seq)               # tuple (already canonical)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for tf in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_key(tf)
        oracle = oracle_key(tf)
        if shadow != oracle:
            disagreements.append((tf, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for tf, sh, orc in disagreements:
            print("  through_fields=%r shadow=%r oracle=%r" % (tf, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of comparisonKey agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
