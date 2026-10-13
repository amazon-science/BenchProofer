"""Twin-artifact model for matplotlib__matplotlib-25332.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A container keeps its members through *indirect* handles: each stored handle
  does not own its target, it only points at it, and a handle may be resolved to
  the integer identity of the target it points at. Indirect handles are not
  serialisable; a *direct* handle (one that simply IS the target's identity,
  owning nothing extra) is.

  (1) Capturing the container for serialisation must yield a state in which
      every stored handle is DIRECT — i.e. no surviving indirect handle — while
      preserving, slot for slot, the integer identity that each original handle
      pointed at. Element i of the captured state resolves to the same identity
      as original handle i, and is itself direct.

  (2) Restoring the container from such a captured state must rebuild every slot
      as an INDIRECT handle again, preserving, slot for slot, the identity each
      captured direct handle carried. Element i of the restored container
      resolves to the same identity as captured element i, and is itself
      indirect.

  Consequently the capture-then-restore round trip is the identity on the
  resolved identity of every slot: restoring a captured container yields, slot
  for slot, an indirect handle pointing at the same identity as the original.

Modelling. A handle is modelled by two parallel `List[int]`: `ident[i]` is the
integer identity the i-th handle points at (its resolution), and `weak[i]` is
1 iff that handle is indirect (not serialisable) and 0 iff it is direct
(serialisable). The two operations are `capture_state` (resolve every indirect
handle to a direct one) and `restore_state` (wrap every direct handle back into
an indirect one); `roundtrip_weakness` composes them. The identity-resolution of
a handle and the (in)direct discriminator are the modelled carrier of the real
handle-resolution / handle-construction primitives, validated by axiom_check.py
(G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No consumed @ContractOnly axiom. The changed operation is the capture/restore
# of the container's stored handles; it is modelled DEEPLY below — the
# resolution of a handle to an identity and the direct/indirect discriminator
# are spelled out as parallel List[int]. The unchanged primitives these stand
# for — resolving an indirect handle to its target's identity, and constructing
# an indirect handle around a target — are validated against the real handle
# primitives by axiom_check.py (G-AX), not consumed as a contract here.)
# axioms-end


# pure-start
# (No pure helpers needed: the specification is element-wise over the two
# parallel List[int] carriers, expressed directly with Forall + in-bounds
# guards.)
# pure-end


def capture_state(ident: List[int], weak: List[int]) -> List[int]:
    """Capture the container for serialisation: resolve every stored handle to a
    DIRECT handle. Returns the captured directness flags (a fresh List[int] of
    0/1, one per slot). The captured state preserves each slot's resolved
    identity (`ident` is read-only and unchanged) and contains NO indirect
    handle (every returned flag is 0)."""
    # pre-conditions-start
    Requires(Acc(list_pred(ident), 1 / 2))
    Requires(Acc(list_pred(weak), 1 / 2))
    Requires(len(weak) == len(ident))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(ident), 1 / 2))
    Ensures(Acc(list_pred(weak), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The captured state has one directness flag per slot.
    Ensures(len(Result()) == len(ident))
    # Every captured handle is DIRECT (serialisable): no surviving indirect one.
    Ensures(Forall(int, lambda k:
        Implies(0 <= k and k < len(Result()), Result()[k] == 0)))
    # post-conditions-end
    # impl-start
    out = []  # type: List[int]
    i = 0
    while i < len(ident):
        # invariants-start
        Invariant(Acc(list_pred(ident), 1 / 2))
        Invariant(Acc(list_pred(weak), 1 / 2))
        Invariant(Acc(list_pred(out)))
        Invariant(0 <= i and i <= len(ident))
        Invariant(len(out) == i)
        Invariant(Forall(int, lambda k:
            Implies(0 <= k and k < i, out[k] == 0)))
        # invariants-end
        # Resolving the indirect handle to its target's identity (ident[i]) and
        # storing it as a direct handle: the captured slot is direct (flag 0).
        out.append(0)
        i = i + 1
    return out
    # impl-end


def restore_state(ident: List[int], state_weak: List[int]) -> List[int]:
    """Restore the container from a captured state: wrap every captured DIRECT
    handle back into an INDIRECT handle. Returns the restored directness flags
    (a fresh List[int] of 0/1, one per slot). The restored container preserves
    each slot's resolved identity (`ident` is read-only and unchanged) and every
    rebuilt handle is INDIRECT (every returned flag is 1)."""
    # pre-conditions-start
    Requires(Acc(list_pred(ident), 1 / 2))
    Requires(Acc(list_pred(state_weak), 1 / 2))
    Requires(len(state_weak) == len(ident))
    # The captured state being restored consists of DIRECT handles.
    Requires(Forall(int, lambda k:
        Implies(0 <= k and k < len(state_weak), state_weak[k] == 0)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(ident), 1 / 2))
    Ensures(Acc(list_pred(state_weak), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == len(ident))
    # Every restored handle is INDIRECT again (the live container's form).
    Ensures(Forall(int, lambda k:
        Implies(0 <= k and k < len(Result()), Result()[k] == 1)))
    # post-conditions-end
    # impl-start
    out = []  # type: List[int]
    i = 0
    while i < len(ident):
        # invariants-start
        Invariant(Acc(list_pred(ident), 1 / 2))
        Invariant(Acc(list_pred(state_weak), 1 / 2))
        Invariant(Acc(list_pred(out)))
        Invariant(0 <= i and i <= len(ident))
        Invariant(len(out) == i)
        Invariant(Forall(int, lambda k:
            Implies(0 <= k and k < i, out[k] == 1)))
        # invariants-end
        # Constructing an indirect handle around the target identity ident[i]:
        # the rebuilt slot is indirect (flag 1).
        out.append(1)
        i = i + 1
    return out
    # impl-end


def roundtrip_weakness(ident: List[int], weak: List[int]) -> List[int]:
    """Capture then restore: the composition of the two operations. Returns the
    directness flags of the restored container. The round trip preserves each
    slot's resolved identity (`ident` unchanged) and the restored container is
    again all-indirect, regardless of the original directness."""
    # pre-conditions-start
    Requires(Acc(list_pred(ident), 1 / 2))
    Requires(Acc(list_pred(weak), 1 / 2))
    Requires(len(weak) == len(ident))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(ident), 1 / 2))
    Ensures(Acc(list_pred(weak), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == len(ident))
    # The container after a capture/restore round trip is all-indirect again.
    Ensures(Forall(int, lambda k:
        Implies(0 <= k and k < len(Result()), Result()[k] == 1)))
    # post-conditions-end
    # impl-start
    captured = capture_state(ident, weak)
    restored = restore_state(ident, captured)
    return restored
    # impl-end
