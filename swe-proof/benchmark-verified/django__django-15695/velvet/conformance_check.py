#!/usr/bin/env python3
"""G-CONF differential conformance for django__django-15695.

Refutes the R/I refinement leg of `relabelSchedule`'s `do` block: the
emit-decision `emit store-mutation work IFF the resolved index name differs
from the target name`, which is precisely the guard the gold patch adds to
`RenameIndex.database_forwards`:

    +        # Don't alter when the index name is not changed.
    +        if old_index.name == self.new_name:
    +            return
             ...
             schema_editor.rename_index(model, old_index, new_index)

ORACLE CHOICE — why we transliterate the guard instead of running
`database_forwards`:
  The emitted store-mutation work is produced by `schema_editor.rename_index`,
  which requires a live `schema_editor` bound to a materialized DB backend, a
  real index on a real table, and fully-populated `from_state`/`to_state`
  `ProjectState`s — i.e. the F2P integration test itself, not a fuzzable
  transliteration. But the ONLY property the spec pins is zero-vs-nonzero
  emitted work, and that is decided ENTIRELY by the added equality guard, which
  is DB-free computable. So, exactly as for the boolean-flag transliteration
  cases (e.g. django__django-16527), the ORACLE is the patched guard predicate
  transliterated verbatim from the gold-patched
  django/db/migrations/operations/models.py:

      if old_index.name == self.new_name: return     # else -> rename_index(...)

  giving "emit IFF old_index.name != self.new_name". The SHADOW is the modeled
  decision from Solution.lean's `relabelSchedule` impl: emit (non-empty
  schedule) IFF beforeId != afterId. Both sides are bridged through the
  equality bijection (mapping.md §2): two model ints are equal iff the two names
  are equal, so we fuzz NAME PAIRS (strings) directly and compare emit-vs-noemit
  on both sides. Exit 0 iff zero disagreements. stdlib only.

  conf_skip=false: the impl region is R/I-tagged (the guard is modeled deeply),
  not all-A-tagged, so a real differential test applies.
"""
import random
import string
import sys

SEED = 15695
N_FUZZ = 100_000


def shadow(before_id, after_id):
    """relabelSchedule transliterated: emit store-mutation work (non-empty
    schedule) IFF the two identifiers differ. Mirrors
        if beforeId = afterId then return [] else return [applyOp]
    Returns True when work is emitted (schedule non-empty), False otherwise.
    `before_id`/`after_id` are the index name and the target name; only their
    equality is observable (the Int-identity bijection, mapping.md §2)."""
    return before_id != after_id


def oracle(old_index_name, new_name):
    """The patched guard, transliterated verbatim from
    django/db/migrations/operations/models.py (gold-patched):
        if old_index.name == self.new_name:
            return                       # -> NO rename_index call (no work)
        ...
        schema_editor.rename_index(...)  # -> work emitted
    Returns True when the rename_index call is reached (work emitted)."""
    if old_index_name == new_name:
        return False
    return True


def _rand_name(rng):
    # Index names: short identifier-ish strings; include the empty string and
    # the auto-generated-name shape (`<prefix>_<hex>`) as boundary cases.
    kind = rng.randint(0, 3)
    if kind == 0:
        return ""
    if kind == 1:
        n = rng.randint(1, 12)
        return "".join(rng.choice(string.ascii_lowercase + "_") for _ in range(n))
    if kind == 2:
        return "%s_%x" % (rng.choice(["pony", "idx", "new_pony_test"]),
                          rng.randrange(0, 1 << 32))
    return rng.choice(["new_pony_test_idx", "pony_pink_idx", "_id"])


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    # Boundary pairs: equal names (the noop/re-apply case the F2P exercises) and
    # clearly differing names (the first-apply case).
    boundary = [
        ("new_pony_test_idx", "new_pony_test_idx"),   # re-apply: equal -> noop
        ("new_pony_test_idx", "pony_pink_idx"),        # first apply: differ
        ("", ""),                                      # equal empties -> noop
        ("", "x"),                                     # differ
        ("a", "a"),                                    # equal -> noop
        ("a", "b"),                                    # differ
    ]
    for before, after in boundary:
        count += 1
        s = bool(shadow(before, after))
        o = bool(oracle(before, after))
        if s != o:
            disagreements.append((before, after, s, o))

    # Fuzz: random name pairs, biased so ~half are equal (exercises both
    # branches of the guard heavily).
    for _ in range(N_FUZZ):
        count += 1
        a = _rand_name(rng)
        b = a if rng.random() < 0.5 else _rand_name(rng)
        s = bool(shadow(a, b))
        o = bool(oracle(a, b))
        if s != o:
            disagreements.append((a, b, s, o))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s): %r"
              % (len(disagreements), disagreements[:5]))
        return 1
    print("G-CONF OK: R/I shadow of relabelSchedule (emit iff identifiers "
          "differ) agrees with the patched guard on %d name pairs "
          "(6 boundary + fuzz, seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
