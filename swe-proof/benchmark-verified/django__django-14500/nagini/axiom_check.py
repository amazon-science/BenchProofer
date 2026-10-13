#!/usr/bin/env python3
"""G-AX / deep-model soundness check for django__django-14500.

This bundle consumes NO `@ContractOnly` axiom: recording which bookkeeping keys
leave the "applied" set when a migration is rolled back is pure control-flow /
data-flow over the migration's own key and the keys it replaces, modelled
DEEPLY by `keys_leaving_applied_set` in model.py. There is therefore no opaque
library callee to over-approximate. What this script validates is the
A-reference of the deep model: that the abstract `keys_leaving_applied_set` build
(re-encoded here in lock-step with model.py) computes EXACTLY the sequence of
keys recorded as no-longer-applied by the REAL fixed control flow that the gold
patch establishes -- the post-patch `unapply_migration` recording branch:

    if migration.replaces:
        for app_label, name in migration.replaces:
            self.recorder.record_unapplied(app_label, name)   # each replaced key
    self.recorder.record_unapplied(migration.app_label, migration.name)  # own key

i.e. each replaced key (in listed order) is recorded, and THEN the migration's
own key is recorded -- unconditionally, whether or not it is a replacement.

We run that real decision (a faithful transcription of the patched repo branch,
recording each `record_unapplied(app_label, name)` call as it would be issued)
against the abstract model over boundary cases and heavy randomized fuzzing, and
assert they agree on every input. We also assert that the abstract model
strictly DISAGREES with the pre-patch (buggy) branch on the witness family the
issue describes (a rolled-back replacement migration whose own key would NOT be
recorded), so the differential is real.

stdlib-only imports; exit 0 iff every observation matches.
"""
import itertools
import random
import sys


# --- model.py reference encoding (kept in lock-step with the impl region) -----

def m_keys_leaving_applied_set(own_key, replaced_keys):
    """Abstract `keys_leaving_applied_set` build from model.py: the keys recorded
    as no-longer-applied are each replaced key (in listed order) followed by the
    migration's own key -- i.e. `list(replaced_keys) + [own_key]`."""
    result = []
    for k in replaced_keys:            # the loop over migration.replaces
        result = result + [k]
    result = result + [own_key]        # then the own key, ALWAYS
    return result


# --- the REAL fixed unapply_migration recording branch (post-patch repo) ------

def real_fixed_recorded(own_key, replaces):
    """Faithful transcription of the post-patch `unapply_migration` recording
    branch (django/db/migrations/executor.py), reduced to the ordered list of
    `record_unapplied(app_label, name)` calls it issues.

    Post-patch:
        if migration.replaces:
            for app_label, name in migration.replaces:
                record_unapplied(app_label, name)
        record_unapplied(migration.app_label, migration.name)   # always
    """
    recorded = []
    if replaces:                                   # `if migration.replaces:`
        for key in replaces:                       # each replaced (app_label, name)
            recorded.append(key)                   # record_unapplied(replaced)
    recorded.append(own_key)                       # record_unapplied(own) -- always
    return recorded


def real_buggy_recorded(own_key, replaces):
    """The PRE-patch (buggy) branch: the own key was recorded ONLY in the `else`
    (non-replacement) case, so a rolled-back replacement migration's own key was
    never recorded as no-longer-applied. Used only to confirm the differential."""
    recorded = []
    if replaces:                                   # `if migration.replaces:`
        for key in replaces:
            recorded.append(key)
    else:                                          # `else:` -- own key only here
        recorded.append(own_key)
    return recorded


def applied_after(applied_before, recorded):
    """The observable the F2P test checks: `applied_migrations()` is a SET keyed
    by (app_label, name); `record_unapplied(k)` removes k. The final applied set
    is the starting set minus every recorded key (order-irrelevant)."""
    return set(applied_before) - set(recorded)


def check_match(own_key, replaces):
    """Assert the abstract build == the real fixed recording, in order."""
    expected = real_fixed_recorded(own_key, replaces)
    observed = m_keys_leaving_applied_set(own_key, list(replaces))
    assert observed == expected, (
        "deep model unsound on own_key=%r replaces=%r: real fixed "
        "unapply_migration recorded %r, model recorded %r"
        % (own_key, replaces, expected, observed))
    # The own key must always be among the recorded keys (the discriminating
    # property): present whether or not there are replaced keys.
    assert own_key in observed, (
        "own_key %r not recorded for replaces=%r" % (own_key, replaces))
    for k in replaces:
        assert k in observed, (
            "replaced key %r not recorded for own_key=%r" % (k, own_key))


def main():
    # --- boundary cases: the witness family from the issue -------------------
    # A rolled-back replacement migration (own key 0001_squashed_0002 modelled
    # as 100; replaces 0001_initial=1, 0002_second=2). Its own key MUST leave
    # the applied set; the pre-patch branch never records it.
    own = 100
    rep = [1, 2]
    applied = {1, 2, 100, 200}                      # 200 unrelated, stays applied
    fixed = applied_after(applied, real_fixed_recorded(own, rep))
    buggy = applied_after(applied, real_buggy_recorded(own, rep))
    assert own in buggy, "pre-condition of differential: buggy keeps own applied"
    assert own not in fixed, "fixed must remove own from applied"
    assert buggy == {100, 200} and fixed == {200}, (buggy, fixed)
    check_match(own, rep)

    # non-replacement migration: replaces empty -> records only its own key.
    assert real_fixed_recorded(7, []) == [7]
    assert real_buggy_recorded(7, []) == [7]        # else-branch, identical here
    check_match(7, [])

    # assorted explicit boundaries
    explicit = [
        (0, []),
        (5, [5]),                  # own key also among its replaced keys
        (3, [1, 2, 3, 4]),
        (10, [10, 10]),            # duplicate replaced keys preserved in order
        (-1, [-2, -3]),
        (42, [1]),
    ]
    for own_key, replaces in explicit:
        check_match(own_key, replaces)

    # --- exhaustive small enumeration ----------------------------------------
    universe = [0, 1, 2, 3, 4]
    for own_key in universe:
        for length in range(0, 5):
            for replaces in itertools.product(universe, repeat=length):
                check_match(own_key, list(replaces))

    # --- randomized fuzz ------------------------------------------------------
    rng = random.Random(14500)
    for _ in range(40000):
        own_key = rng.randint(-50, 50)
        n = rng.randint(0, 10)
        replaces = [rng.randint(-50, 50) for _ in range(n)]
        check_match(own_key, replaces)

    print("G-AX OK: abstract keys_leaving_applied_set build == real fixed "
          "unapply_migration recording (each replaced key, then the own key "
          "unconditionally) on %d boundary + exhaustive small enumeration + "
          "40000 fuzz inputs; pre-patch differential confirmed on the "
          "rolled-back-replacement witness (own key stays applied pre-patch, "
          "removed post-patch)." % (len(explicit) + 2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
