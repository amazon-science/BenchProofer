# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""G-MUT — impl-region mutants killed: a spec-tightness floor, NOT a
correctness proof (the real spec-strength check is G-PANEL).

The threshold is a per-backend parameter rather than a constant: on a
tactic-proof backend a surviving mutant can mean incomplete proof search rather
than a weak spec, so demanding every mutant die would fail sound bundles.
"""
from __future__ import annotations

from ..mutation import generate_mutants
from .base import Bundle, GateResult
from ._common import check_bundle_source, env_int, no_verdict, worst_no_verdict

name = "G-MUT"
applies_to = ("nagini", "velvet", "lean")
needs_docker = False
agentic = False
# Bundle files this gate's verdict depends on; digested into the record
# so a stamp can be checked against the artifact it describes (base.source_digests).
reads = ("solution",)

KILL_THRESHOLD = {"nagini": 0.8, "velvet": 0.8, "lean": 0.8}

MUTATION_CAP_DEFAULT = 20
# One JVM/Viper verifier per worker, so this is how many verifiers a SINGLE
# cell's G-MUT run puts on the host at once. Oversubscribing does not merely slow
# G-MUT down, it MANUFACTURES spec defects: mutants competing for the machine
# grind past a cap the gold clears in seconds and reach NO VERDICT, which this
# gate charges to the spec (see the `unjudged` branch below). 2 keeps some overlap
# without one cell's mutants starving each other. Size it by verifier processes
# the host can run without them slowing each other, not by core count.
MUTATION_WORKERS_DEFAULT = 2
# A mutant can be far harder to DECIDE than the gold it mutates: flipping an
# operator turns a linear obligation nonlinear and the solver stops converging,
# so a cap that the gold clears in seconds is not evidence the mutants can clear
# it. Without a knob the only way to give them longer is to raise the CELL's
# `timeout_seconds`, which moves every sibling gate's budget with it. Mirrors
# SBU_PBT_VERIFY_TIMEOUT deliberately, including the `max`: the env var wins only
# when it asks for MORE, so it cannot silently lower a cap the cell recorded a
# need for. 0 means "use bundle.verify_timeout()".
MUTATION_TIMEOUT_DEFAULT = 0


def _rescue_non_programs(bundle: Bundle, src: str, timeout: int, outcomes):
    """Split the unjudged mutants into non-programs and open questions.

    Two very different things arrive as "no verdict" and the accounting has to
    separate them. A mutation operator can produce something that is not a
    program in the modelling language at all -- `+` -> `-` over a sequence or
    string concatenation is the common one, and nagini's front end then refuses
    the FILE with the rejection exit code without Viper ever judging the
    implementation. Charging that to the spec is wrong in both directions: a
    non-program is not a rival implementation, so there is nothing for the spec to
    have turned down, and the mutant tells us nothing about its tightness. A cap
    or a dead verifier is the opposite -- the rival was well formed and the
    question is genuinely still open, which is what the `error` branch below is
    for.

    Separated by measurement, not by matching the checker's error text (see
    `backends/nagini._no_verdict` on why that taxonomy must not be guessed at):
    re-run the mutant, and require the UNMUTATED source to reach a verdict in the
    same environment. Then "the checker refuses this file" is attributable to the
    mutation rather than to the host, and a flaky non-verdict fails the retry.
    Returns `(outcomes without the non-programs, their descriptions)`.
    """
    pending = [(m, r) for m, r in outcomes if no_verdict(r)]
    if not pending:
        return outcomes, []
    control = check_bundle_source(bundle, src, timeout)
    if no_verdict(control):
        # The environment cannot judge the bundle's own solution right now, so it
        # cannot attribute anything to a mutation either.
        return outcomes, []
    settled = {}
    invalid: set[int] = set()
    for m, _ in pending:
        again = check_bundle_source(bundle, m.source, timeout)
        if not no_verdict(again):
            settled[id(m)] = again          # the first run was the flake
        elif not again.timed_out and again.no_verdict_detail:
            # Reproducible, and the checker named its own refusal of the file
            # rather than dying: this text is not a program.
            invalid.add(id(m))
    kept = [(m, settled.get(id(m), r)) for m, r in outcomes if id(m) not in invalid]
    return kept, [m.description for m, _ in outcomes if id(m) in invalid]


def run(bundle: Bundle, *, mode: str = "strict") -> GateResult:
    src = bundle.solution_src()
    cap = env_int("SBU_MUTATION_CAP", MUTATION_CAP_DEFAULT)
    workers = env_int("SBU_MUTATION_WORKERS", MUTATION_WORKERS_DEFAULT)
    mutants = generate_mutants(src, bundle.backend.language, cap=cap)
    if not mutants:
        # Not necessarily assignment-only: an impl region can be a fold of
        # verifier directives around one assignment, and those are excluded
        # because mutating them cannot make the implementation incorrect. Either
        # way this gate learned nothing about the spec and must say so plainly,
        # since `skip` is green-eligible and a reader takes the detail for the
        # reason. G-PANEL is the spec-strength check on such a cell.
        return GateResult(name, "skip",
                          "no behavioural impl mutants (impl region carries no "
                          "mutable computation outside verifier directives)")
    timeout = max(env_int("SBU_MUTATION_TIMEOUT", MUTATION_TIMEOUT_DEFAULT),
                  bundle.verify_timeout())

    def check(m):
        return m, check_bundle_source(bundle, m.source, timeout)

    if workers > 1:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=workers) as ex:
            outcomes = list(ex.map(check, mutants))
    else:
        outcomes = [check(m) for m in mutants]
    outcomes, invalid = _rescue_non_programs(bundle, src, timeout, outcomes)
    # A mutant with no verdict was not killed (see _common.no_verdict). It is
    # also not a survivor: nothing was learned about it. So it leaves the sample
    # entirely and the kill rate is over the mutants that were actually judged.
    unjudged = [m.description for m, r in outcomes if no_verdict(r)]
    survivors = [m.description for m, r in outcomes if r.success]
    judged = len(outcomes) - len(unjudged)
    killed = judged - len(survivors)
    threshold = KILL_THRESHOLD[bundle.backend.name]
    mutants = [m for m, _ in outcomes]
    if invalid and not mutants:
        # Every mutant this operator set produced was a non-program, so the gate
        # measured nothing about the spec -- the same situation as generating no
        # behavioural mutants at all, and `skip` says so where `error` would
        # invite a repair agent to weaken a spec that was never probed.
        return GateResult(name, "skip",
                          f"every mutant ({len(invalid)}) is not a program in "
                          f"this language, so none is a rival implementation: "
                          f"{invalid}", {"invalid": invalid})
    if not judged:
        # `no_verdict` names whether the cap or the environment did this. Every
        # mutant timing out is the signature of a saturated host, and this gate
        # runs the checker once per mutant, so it meets a loaded host more often
        # than most and a caller has to be able to tell that from a battery that
        # cannot run at all.
        return GateResult(name, "error",
                          f"no verdict on any of {len(mutants)} mutants",
                          {"total": len(mutants), "unjudged": unjudged,
                           "no_verdict": worst_no_verdict(
                               [r for _, r in outcomes])})
    rate = killed / judged
    detail = f"killed {killed}/{judged} ({rate:.0%})"
    if survivors:
        detail += f"; survivors: {survivors}"
    if unjudged:
        detail += f"; no verdict on {len(unjudged)}: {unjudged}"
    if invalid:
        detail += (f"; {len(invalid)} mutant(s) left the sample as non-programs "
                   f"(the checker refused the file, reproducibly, while the "
                   f"unmutated source reached a verdict): {invalid}")
    data = {"killed": killed, "total": len(mutants), "judged": judged,
            "survivors": survivors, "threshold": threshold,
            "unjudged": unjudged}
    if invalid:
        data["invalid"] = invalid
    if unjudged:
        # Which non-verdict this was decides what to do next, and a PARTIAL one is
        # the case a re-stamp lane hits: a cell whose judged mutants were all
        # killed still files `error`, and without this the record cannot say
        # whether a larger cap would fix it or the environment is broken.
        data["no_verdict"] = worst_no_verdict(
            [r for m, r in outcomes if no_verdict(r)])
    if rate < threshold:
        return GateResult(name, "fail", detail, data)
    # Dropping the unjudged mutants raised the rate. Passing on that is only
    # honest while the verdict they never gave could not have changed the answer,
    # so charge them all to the spec and require the floor to hold anyway.
    if unjudged and (killed / len(mutants)) < threshold:
        return GateResult(
            name, "error",
            f"{len(unjudged)} mutant(s) reached no verdict and the rate turns on "
            f"them ({killed}/{len(mutants)} counting them as survivors): {detail}",
            data)
    return GateResult(name, "pass", detail, data)
