# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Whether a variant's rejection is the specification's, under a checker that replays a proof.

Two gates read a rejection as evidence about the specification: the property-based test suite,
of a case meant to be wrong, and `spec.discriminates`, of the code before the fix. Under a
checker whose acceptance replays a proof script the file writes, neither may read it off the
checker's verdict alone. The script is tuned to one implementation's syntactic form, so a
variant that merely reshapes a correct implementation fails to build exactly as a wrong one
does. What attributes the rejection is the variant's refutation witness, and the two builds it
has to clear (`core.witness`). Both gates ask the same question in the same order, so it is
decided here once.
"""

from __future__ import annotations

from ..backends.base import Backend, CheckResult
from ..core import witness
from ..core.variant import refused_within
from .base import GateContext

__all__ = ["attributed"]


def attributed(
    context: GateContext, source: str, claim: str, *, slot: str, of: str
) -> str | None:
    """Why the checker's rejection of ``source`` is not the specification's, or None if it is.

    None also where the question does not arise: under a checker that discharges the
    obligation itself, a rejection is the contract failing to hold and there is nothing
    further to establish. See `Backend.witness_required`.

    Two builds, in the order that costs least. The witness has to hold of the variant,
    which is what says the variant contradicts the specification somewhere; then it has to
    fail against the reference implementation, which is what says it is a discriminator
    rather than something true of any implementation at all. A build that reached no verdict
    is its own reason: nothing was established, which is not the same as a witness that
    failed.

    Args:
        context: The gate's context, whose checker runs both builds.
        source: The variant the checker rejected.
        claim: Its refutation witness, empty where it ships none.
        slot: The prefix the two builds are checked under, unique to the variant.
        of: What the variant is called in its slot and, through `_CALLED`, in the reasons
            given, such as ``rival``.
    """
    backend = context.backend
    if not backend.witness_required:
        return None
    accepted = context.solution
    objections = witness.objections(accepted, source, claim, backend)
    if objections:
        return "; ".join(objections)

    probe = witness.probe(source, claim, backend)
    against_variant = context.check(probe, f"{slot}-{of}")
    called = _CALLED.get(of, of)
    if not against_variant.decided:
        return (
            f"the witness's build against the {called} reached no verdict: "
            f"{against_variant.detail}"
        )
    if not against_variant.verified:
        return f"{_refused(against_variant, probe, backend, called)}: {against_variant.detail}"

    against_accepted = context.check(
        witness.probe(accepted, claim, backend), f"{slot}-accepted"
    )
    if not against_accepted.decided:
        return (
            "the witness's build against the reference implementation reached no verdict: "
            f"{against_accepted.detail}"
        )
    if against_accepted.verified:
        return (
            "the witness holds of the reference implementation too, so it does not "
            f"discriminate the {called}: it asserts something true of any implementation"
        )
    return None


#: What a variant is called in the reasons, where its slot name is not that: the `twin` slot
#: holds the pre-fix implementation.
_CALLED = {"twin": "pre-fix implementation"}


def _refused(result: CheckResult, probe: str, backend: Backend, of: str) -> str:
    """Which of three things a refused witness build is, as the reason opens.

    They call for different repairs and read alike in a verdict that names only one: a
    witness the checker could not elaborate -- a tactic it does not have, a `decide` over a
    carrier with no instance -- was never asked whether it holds, and a build that failed
    inside the variant's own implementation says nothing about the claim at all. Only the
    third is the claim going through or not, and there the checker's verdict alone does not
    separate a false claim from a proof missing a step, so both are named.
    """
    if not result.well_formed:
        return (
            f"the witness's build against the {of} could not be read, so nothing was asked "
            "of the claim: its statement or its proof reaches for something the checker "
            "does not have"
        )
    if refused_within(probe, f"{result.detail}\n{result.output}", backend):
        return (
            f"the witness's build against the {of} failed inside its implementation region "
            "rather than at the claim, so what did not go through is that file and not the "
            "witness"
        )
    return (
        f"the witness's proof did not close against the {of}, so either the specification "
        "holds there or the proof is missing a step, and the rejection is not the "
        "specification's either way"
    )
