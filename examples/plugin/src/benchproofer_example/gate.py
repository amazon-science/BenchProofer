# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""A gate that refuses a specification with unfinished business in it.

The check itself is trivial on purpose. What the example is about is the shape: one
question, three honest answers, and no guessing.

* `self.failed` only when the finding is established from the artifact.
* `self.undecided` with a reason when the check could not be performed, so an
  absent judgment never reads like a favorable one.
* nothing else. A crash becomes an `error` verdict on its own, and a gate that
  reported a failure it was unsure of would put the tool's problem on the artifact's
  record.

Because it is registered under `benchproofer.gates`, this gate runs on every bundle
`benchproofer check` visits. It is not in the required set that certification depends
on, which is fixed in `benchproofer.pipeline.adjudicate`, so its verdict is recorded
and reported without changing what "certified" means.
"""

from __future__ import annotations

from typing import ClassVar

from benchproofer.core import markers
from benchproofer.core.verdict import Level, SkipReason, Verdict
from benchproofer.errors import BenchproofError
from benchproofer.gates.base import Gate, GateContext

#: Markers that mean the author was not finished.
UNFINISHED = ("TODO", "FIXME", "XXX", "placeholder")


class NoTodoGate(Gate):
    """The specification region contains no unfinished-work marker."""

    id: ClassVar[str] = "spec.no_todo"
    title: ClassVar[str] = "Specification has no unfinished-work markers"
    rationale: ClassVar[str] = (
        "A specification that still says TODO was not finished, and a verifier "
        "cannot tell the difference between a contract and a note to self."
    )
    level: ClassVar[Level] = Level.STATIC
    #: Recorded on the verdict, with digests, so the record names what it read.
    sources: ClassVar[tuple[str, ...]] = ("solution.*",)

    def judge(self, context: GateContext) -> Verdict:
        """Read the spec region and look for a marker."""
        try:
            regions = markers.parse(context.solution, context.backend.comment)
        except BenchproofError as exc:
            # A malformed or absent solution file is artifact.integrity's finding to
            # report, not this gate's. Say why this check did not run and stop.
            return self.undecided(SkipReason.ARTIFACT_ABSENT, f"unreadable solution: {exc}")

        spec = regions["spec"].text
        found = [marker for marker in UNFINISHED if marker in spec]
        if found:
            return self.failed(
                f"the specification still contains {', '.join(found)}",
                markers=found,
            )
        return self.passed("no unfinished-work markers in the specification")
