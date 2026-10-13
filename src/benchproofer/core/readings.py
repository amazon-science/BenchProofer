# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""What a review's reading of a bundle rests on, digest by digest.

A judgment records the digests of what it read and expires when one of them changes. A
whole solution file is the wrong grain: a repair that rewrites a proof or a comment leaves
the specification as it was, and a reading of it as current. So besides every file, the
solution is read as three parts: the specification view, which disclosure and the review's
attacks are about, since a comment or a docstring can give the fix away; the same view with
its comments masked, which faithfulness and equivalence are about, since what a comment says
is not what the specification states; and the implementation without comments and layout,
which equivalence is about as well. The pre-fix implementations are read as one part, so
that adding or removing one changes it too.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..errors import BenchproofError
from ..util.digest import digest_text
from . import markers, variant

if TYPE_CHECKING:
    from ..backends.base import Backend
    from .bundle import Bundle, Submission

__all__ = ["CITES", "IMPL", "SPEC", "SPEC_UNCOMMENTED", "TWINS", "readings", "ruling_reads"]

#: The solution's specification view.
SPEC = "solution:spec"
#: The solution's specification view with its comments masked (`markers.mask_comments`,
#: which masks a Lean docstring too) and the lines that leaves blank dropped.
SPEC_UNCOMMENTED = "solution:spec-without-comments"
#: The solution's implementation regions, comments and layout aside.
IMPL = "solution:impl"
#: Every file under `twins/`, the pre-fix implementations and their index, as one digest.
TWINS = "twins/"
#: What a submission's witness test cites, as a ruling on the submission records it.
CITES = "cites"


def readings(bundle: Bundle, backend: Backend) -> dict[str, str]:
    """Every artifact's digest, plus the parts of the solution a reading can rest on.

    A solution the markers cannot read contributes only its file digest, so a judgment
    resting on its specification reads as stale.
    """
    digests = bundle.artifact_digests()
    digests[TWINS] = digest_text(
        "\n".join(
            f"{name} {digest}"
            for name, digest in sorted(digests.items())
            if name.startswith(TWINS)
        )
    )
    try:
        solution = bundle.solution()
        regions = markers.parse(solution, backend.comment)
        view = backend.spec_view(solution)
    except BenchproofError:
        return digests
    digests[SPEC] = digest_text(view)
    masked = markers.mask_comments(view, backend.comment).splitlines()
    digests[SPEC_UNCOMMENTED] = digest_text(
        "\n".join(line.rstrip() for line in masked if line.strip())
    )
    digests[IMPL] = variant.fingerprint(markers.joined(regions, "impl"), backend)
    return digests


def ruling_reads(submission: Submission, digests: dict[str, str]) -> dict[str, str]:
    """What a ruling on ``submission`` is reached from (`Ruling.reads`), with its digests.

    The specification with its comments masked, the axioms region included, and the
    implementation, as ``digests`` (`readings`) gives them; the submission's own files; and
    what its witness test cites (`CITES`), which is part of the submission as its files are.
    """
    files = (submission.file, submission.shadow, submission.test)
    names = (SPEC_UNCOMMENTED, IMPL, *(f"audit/{name}" for name in files if name))
    read = {name: digests[name] for name in names if name in digests}
    if submission.cites.strip():
        read[CITES] = digest_text(submission.cites)
    return read
