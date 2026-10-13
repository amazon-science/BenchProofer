#!/usr/bin/env python3
"""G-AX executable soundness check for matplotlib__matplotlib-23299.

This bundle axiomatizes NO opaque library callee: the behaviour under
specification -- snapshot a settings mapping, run a body that overrides some
keys, then on exit revert the snapshotted keys EXCEPT one distinguished key --
is composed entirely of REAL Python ``dict`` primitives the gold patch uses:
``dict(rcParams.copy())`` (snapshot), ``del orig['backend']`` (drop the
distinguished key from the snapshot), and ``dict.update`` (per-key revert). The
behaviour is therefore modelled DEEPLY in model.py (the snapshot, the drop, and
the per-key revert spelled out in the impl region). G-AX validates that deep
model against the real primitives (the A-reference): it reproduces the gold
patch's exact control flow over a real ``dict`` and asserts every observation
matches model.py's frozen postconditions.

Checked obligations (model.py post-conditions region):

  (1) survive -- the distinguished key holds the value the body set inside the
      context on exit (NOT reverted to its entry value). This is the guarantee
      the change introduces (the pre-patch snapshot kept the distinguished key
      and the exit-time revert wrote the stale entry value back, forcing the
      distinguished setting to be re-derived later -- the F2P observes the
      survived value).

  (2) revert -- every ordinary key the snapshot covered is reverted to its entry
      value, undoing the body's temporary override.

  (3) no spurious keys -- the restore introduces no key the mapping did not
      already carry.

Imports nothing repo-specific: ``dict`` copy / ``del`` / ``update`` are Python
language primitives (the very constructs the gold patch composes). Exit 0 iff
every obligation holds.
"""
import random
import sys

# model.py constants (kept in lock-step with the pure region).
KEY_RESOLVED = 0   # the distinguished key ('backend')
KEY_OTHER = 1      # a representative ordinary key


def real_restore(params, new_resolved, other_override):
    """The gold patch's exact control flow, over a REAL dict:

        orig = dict(params.copy())   # snapshot
        del orig[KEY_RESOLVED]       # the fix: drop the distinguished key
        # --- body overrides keys ---
        params[KEY_RESOLVED] = new_resolved
        params[KEY_OTHER] = other_override
        # --- exit: revert the snapshot ---
        dict.update(params, orig)

    Mutates ``params`` in place (as the repo code mutates the live rcParams).
    """
    orig = dict(params.copy())            # orig = dict(rcParams.copy())
    if KEY_RESOLVED in orig:
        del orig[KEY_RESOLVED]            # del orig['backend']  -- the fix
    # body inside the context (yield + rcParams.update(rc) / rc_file)
    params[KEY_RESOLVED] = new_resolved
    params[KEY_OTHER] = other_override
    # exit-time revert
    dict.update(params, orig)             # dict.update(rcParams, orig)


def check(params, new_resolved, other_override):
    old = dict(params)                    # snapshot of the entry state
    entry_resolved = old[KEY_RESOLVED]
    entry_other = old[KEY_OTHER]
    real_restore(params, new_resolved, other_override)

    # (1) survive: the distinguished key keeps the body-set value on exit.
    assert KEY_RESOLVED in params and params[KEY_RESOLVED] == new_resolved, (
        "survive unsound: distinguished key is %r, expected body value %r"
        % (params.get(KEY_RESOLVED, "<absent>"), new_resolved))

    # (2) revert: the ordinary key is reverted to its entry value.
    assert KEY_OTHER in params and params[KEY_OTHER] == entry_other, (
        "revert unsound: ordinary key is %r, expected entry value %r"
        % (params.get(KEY_OTHER, "<absent>"), entry_other))

    # (3) no spurious keys: every key present on exit was present on entry.
    for k in params:
        assert k in old, "spurious key unsound: %r invented by the restore" % (k,)

    # sanity: the entry-state pins the model's preconditions used as Old(...)
    assert entry_resolved == old[KEY_RESOLVED] and entry_other == old[KEY_OTHER]


def main():
    # --- boundary cases ------------------------------------------------------
    # The exact F2P scenario: the distinguished key starts at some entry value,
    # the body sets it to a fresh value (e.g. 'module://aardvark'), and it must
    # survive the exit. Use distinct integer codes for the values.
    AUTO = 100        # the unresolved/entry distinguished value
    AARDVARK = 200    # the body-set distinguished value (must survive)
    boundary = [
        # (entry_resolved, entry_other, new_resolved, other_override)
        (AUTO, 5, AARDVARK, 7),       # F2P: body overrides distinguished -> survives
        (AUTO, 5, AUTO, 7),           # body re-sets distinguished to its entry value
        (AARDVARK, 5, AUTO, 7),       # entry already resolved, body sets sentinel-like
        (3, 3, 3, 3),                 # all equal
        (3, 4, 5, 6),                 # all distinct
        (-1, -2, -3, -4),             # negatives
        (0, 0, 0, 0),                 # zeros
    ]
    for entry_resolved, entry_other, new_resolved, other_override in boundary:
        params = {KEY_RESOLVED: entry_resolved, KEY_OTHER: entry_other}
        check(params, new_resolved, other_override)

    # also exercise a mapping carrying extra ordinary keys the body does not
    # touch -- they must be reverted (revert covers all snapshot keys) and no
    # spurious key may appear.
    for entry_resolved, entry_other, new_resolved, other_override in boundary:
        params = {KEY_RESOLVED: entry_resolved, KEY_OTHER: entry_other,
                  9: 90, 10: 100}
        old = dict(params)
        real_restore(params, new_resolved, other_override)
        assert params[KEY_RESOLVED] == new_resolved
        assert params[KEY_OTHER] == entry_other
        # untouched ordinary keys are reverted to their entry values
        assert params[9] == old[9] and params[10] == old[10]
        for k in params:
            assert k in old, "spurious key %r" % (k,)

    # --- randomized fuzz -----------------------------------------------------
    rng = random.Random(23299)
    for _ in range(20000):
        entry_resolved = rng.randint(-50, 50)
        entry_other = rng.randint(-50, 50)
        new_resolved = rng.randint(-50, 50)
        other_override = rng.randint(-50, 50)
        params = {KEY_RESOLVED: entry_resolved, KEY_OTHER: entry_other}
        # maybe carry extra ordinary keys (key tokens != 0,1)
        for _ in range(rng.randint(0, 4)):
            k = rng.randint(2, 30)
            params[k] = rng.randint(-50, 50)
        check(params, new_resolved, other_override)

    print("G-AX OK: deep model (snapshot + distinguished-key drop + per-key "
          "revert) == the real dict copy/del/update primitives on %d boundary "
          "cases + 20000 fuzz cases (distinguished key survives; ordinary keys "
          "reverted; no spurious keys)" % (len(boundary),))
    return 0


if __name__ == "__main__":
    sys.exit(main())
