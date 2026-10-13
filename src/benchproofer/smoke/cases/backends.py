# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Does each installed backend really decide anything.

One case per registered backend, generated from the registry, so a third-party
backend is covered the moment it is installed.

Each case asks the two questions that matter about a checker, and nothing else. Does
it accept a correct implementation of its own template? And does it *reject* something
wrong? The second question is the one a smoke test usually forgets: a toolchain that
is misconfigured, or invoked with the wrong arguments, very often accepts everything,
and a suite that only checks the happy path calls that a pass.

The wrong implementations are produced by mutating the template's ``impl`` region
with the tool's own mutation operators, so no per-backend fixture has to be written
and kept in step with the template.

A checker that reaches no verdict inside its budget skips the case rather than failing
it. The suite could not look, and a solver that ran out of time on a loaded machine
must not be reported as a toolchain that decides nothing.
"""

from __future__ import annotations

from ...core import markers
from ...core.mutation import generate
from ...registries import BACKENDS
from ..model import Case, Context, Failure, Observation, Procedure, Unmet, check

__all__ = ["CASES"]

#: How many mutants to try before giving up on getting a rejection. Small, because a
#: checker that rejects nothing among the first few rejects nothing at all, and each
#: attempt costs a verifier invocation.
MUTANT_LIMIT = 6


def _procedure(name: str) -> Procedure:
    """Build the case procedure for one backend."""

    def run(context: Context) -> list[Observation]:
        backend = BACKENDS.get(name)
        timeout = backend.budget(context.settings.verify_timeout_s)
        workdir = context.path("check")

        template = backend.template()
        regions = markers.parse(template, backend.comment)
        for required in markers.REQUIRED_REGIONS:
            check(
                required in regions,
                f"the {name} template has no {required!r} region, so Benchproofer could not "
                "put an implementation into it",
            )
        view = markers.spec_view(template, backend.comment)
        check(
            "benchproofer:elided" in view,
            "the specification view of the template elides nothing, so a leakage or "
            "hygiene check would be reading the implementation as well",
        )
        check(
            regions["impl"].text.strip() not in view,
            "the specification view still contains the implementation verbatim",
        )

        base = backend.check(template, workdir=workdir / "template", timeout_s=timeout)
        if not base.decided:
            raise Unmet(
                f"{name} reached no verdict on its own template in {timeout:.0f}s "
                f"({base.detail}), so this machine cannot decide either question"
            )
        check(
            base.verified,
            f"the {name} template does not verify: {base.status} ({base.detail}); "
            f"output: {base.output[-400:]}",
        )

        mutants = generate(template, backend.comment, limit=MUTANT_LIMIT)
        check(mutants, f"no mutant could be generated from the {name} template")

        tried: list[str] = []
        decided = 0
        for mutant in mutants:
            result = backend.check(
                mutant.source, workdir=workdir / mutant.id, timeout_s=timeout
            )
            tried.append(mutant.operator)
            if result.decided:
                decided += 1
            if result.refuted_on_merits:
                return [
                    Observation("kind", str(backend.kind)),
                    Observation("template", f"verified in {base.duration_s:.1f}s"),
                    Observation(
                        "rejected",
                        f"{mutant.operator} after {len(tried)} attempt(s) "
                        f"in {result.duration_s:.1f}s: {mutant.excerpt}",
                    ),
                ]

        # Undecided is not acceptance: a checker that ran out of budget on every
        # mutant has not been shown to accept everything, and saying it has would
        # turn load on this machine into a defect report about the toolchain.
        if not decided:
            raise Unmet(
                f"{name} reached no verdict on any of {len(tried)} wrong "
                f"implementation(s) within {timeout:.0f}s each"
            )
        raise Failure(
            f"the {name} checker rejected none of {len(tried)} wrong implementation(s) "
            f"({', '.join(tried)}); a checker that accepts everything certifies nothing"
        )

    return run


#: Every backend that loads here, for the metadata the cases are built from.
_LOADED = BACKENDS.load_all()


def _slow(name: str) -> bool:
    """Whether this backend calls one check expensive enough to skip by default.

    Read from the backend, so a checker that needs a large library or a workspace of
    several gigabytes keeps itself out of the hermetic suite. A backend that fails to
    load is not slow: it still gets a case, which then reports the import failure
    instead of vanishing from the suite.
    """
    backend = _LOADED.get(name)
    return backend is not None and backend.slow


CASES: tuple[Case, ...] = tuple(
    Case(
        id=f"backends.{name}",
        summary=f"the {name} backend accepts its template and rejects a mutant of it",
        procedure=_procedure(name),
        requires=(f"backend:{name}",),
        slow=_slow(name),
    )
    for name in BACKENDS.names()
)
