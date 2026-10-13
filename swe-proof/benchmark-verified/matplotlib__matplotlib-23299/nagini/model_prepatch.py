"""Twin-artifact model for matplotlib__matplotlib-23299.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A context manager temporarily overrides entries of a settings mapping: on
  entry it snapshots the mapping, the body it guards may override some entries,
  and on exit it reverts the snapshotted entries. One distinguished key
  (`key_resolved()`) is special: a value written to it inside the context must
  SURVIVE the context's exit, rather than being reverted to the entry value
  along with the ordinary keys. Concretely, after the context exits:

  (1) the distinguished key holds exactly the value the body set inside the
      context (it is NOT reverted to its entry value);
  (2) every ordinary key the snapshot covered is reverted to its entry value
      (the temporary override is undone);
  (3) the restore introduces no key that the mapping did not already carry.

  The consequence that matters: a value established for the distinguished key
  within the context is preserved across the exit, so a later read of that key
  observes the value set inside — not a stale entry value that would force the
  distinguished setting to be re-derived.

Modelling choices (Nagini fragment):
  * The settings mapping is a ``Dict[int, int]`` from a key token to a value
    token; only the membership and values of the two observed keys matter, so
    integer identity is the faithful carrier (mapping.md §2). The distinguished
    key is the module-level constant ``key_resolved()``; a representative
    ordinary key is ``key_other()``.
  * The body's only observable effect on the tested behaviour is the value each
    key holds just before the exit-time revert, captured as the explicit
    parameters ``new_resolved`` (the body's write to the distinguished key) and
    ``other_override`` (the body's write to the ordinary key). The entry values
    are pinned by the parameters ``entry_resolved`` / ``entry_other``, which are
    genuine pre-state facts about the input.

The mapping is genuinely mutated in place, so it is held at FULL permission and
its exact post-state is stated. No string indexing is used (Nagini bans it).
The whole behaviour is modelled deeply (snapshot, the distinguished-key drop,
and the per-key revert are spelled out in the impl region); there is no
axiomatised callee. The restore must actually COMPLETE and hand control back:
Nagini checks partial correctness by default, so a diverging body would satisfy
every post-state claim vacuously; the contract therefore carries an explicit
``MustTerminate`` obligation rejecting non-terminating implementations.
Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Dict
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No axioms: the snapshot, the distinguished-key drop, and the per-key revert
# are the behaviour under specification and are spelled out deeply in the impl
# region over a real Dict[int,int]. There is no unchanged opaque callee to
# axiomatise — only CPython dict primitives (copy / del / update), validated as
# an A-reference by axiom_check.py (G-AX).
# axioms-end


# pure-start
@Pure
def key_resolved() -> int:
    # The distinguished key whose body-set value must survive the context exit.
    return 0


@Pure
def key_other() -> int:
    # A representative ordinary key whose body-set value is reverted on exit.
    return 1
# pure-end


def restore_after_temporary_overrides(params: Dict[int, int],
                                      entry_resolved: int,
                                      entry_other: int,
                                      new_resolved: int,
                                      other_override: int) -> None:
    # pre-conditions-start
    # The restore must terminate: a diverging exit path would satisfy any
    # post-state claim vacuously (partial correctness), so termination is an
    # explicit obligation. The work is bounded and loop-free, so measure 2
    # suffices.
    Requires(MustTerminate(2))
    # The mapping is genuinely mutated, so FULL permission is required.
    Requires(Acc(dict_pred(params)))
    # Both observed keys are present on entry, and the parameters pin their
    # entry values. These are pre-state facts about the input, bound before any
    # mutation, so the survive/revert guarantees gate on the genuine entry state
    # rather than on a membership query an implementation could perturb.
    Requires(key_resolved() in params)
    Requires(key_other() in params)
    Requires(params[key_resolved()] == entry_resolved)
    Requires(params[key_other()] == entry_other)
    # The two observed keys are distinct (the distinguished key is not the
    # ordinary key).
    Requires(key_resolved() != key_other())
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(dict_pred(params)))
    # (1) The distinguished key SURVIVES: after exit it holds the value the body
    #     set inside the context (new_resolved), NOT the entry value. This is the
    #     guarantee the change introduces — the temporary-override revert must
    #     leave this key alone.
    Ensures(key_resolved() in params)
    Ensures(params[key_resolved()] == new_resolved)
    # (2) The ordinary key is REVERTED: after exit it holds its entry value,
    #     undoing the body's temporary override.
    Ensures(key_other() in params)
    Ensures(params[key_other()] == entry_other)
    # (3) The restore introduces no key the mapping did not already carry: any
    #     key present on exit must have been present on entry. Stated forward so
    #     it constrains body/restore-added keys.
    Ensures(Forall(int, lambda k: (Implies(k in params, Old(k in params)))))
    # (4) FRAME / full-revert: every key present on entry, other than the
    #     distinguished key, is reverted to its entry value (ordinary keys
    #     are restored, not corrupted/dropped). This pins the full-revert
    #     behaviour in the spec — the snapshot's temporary override is undone
    #     for ALL non-distinguished keys, not merely the one observed ordinary
    #     key — so an impl that corrupts any third pre-existing key cannot
    #     satisfy the contract.
    Ensures(Forall(int, lambda k: Implies(k in params and k != key_resolved(),
                                          k in params and params[k] == Old(params[k]))))
    # post-conditions-end
    # impl-start
    # Snapshot the mapping (orig = rcParams.copy()): record BOTH observed keys'
    # entry values, including the distinguished key.
    saved = {}  # type: Dict[int, int]
    saved[key_resolved()] = params[key_resolved()]
    saved[key_other()] = params[key_other()]
    # The body overrides both keys (yield + rcParams.update(rc) / rc_file).
    params[key_resolved()] = new_resolved
    params[key_other()] = other_override
    # Restore (dict.update over the snapshot's keys): the snapshot covers BOTH
    # keys, so both are reverted to their entry values — the value set inside the
    # context for the distinguished key does not survive.
    if key_resolved() in saved:
        params[key_resolved()] = saved[key_resolved()]
    if key_other() in saved:
        params[key_other()] = saved[key_other()]
    # impl-end
