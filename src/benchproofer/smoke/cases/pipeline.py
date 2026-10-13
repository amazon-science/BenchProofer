# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Do the end-to-end paths hold together.

The groups before this one exercise one component each. These cases run the paths a
user actually invokes, and check the properties that make a run worth trusting:

* a corpus of bundles is judged and reported without one bundle's verdict leaking
  into another's, and a bundle that already certified is left alone;
* a formalization session writes back exactly the artifacts it produced, which is
  checked byte for byte against the fixture the session was scripted from.

Both run offline. The model's part is played by
`benchproofer.smoke.scripted.ScriptedSession`, which writes the solution a drafting
session is asked for, and `benchproofer.smoke.scripted.ScriptedProvider`, which answers
the requests that draft the rest; both reconstruct what they hand over from a fixture
bundle, so everything downstream of them runs as it does in a live run.
"""

from __future__ import annotations

from ...core.verdict import Level, Outcome
from ...pipeline.build import build
from ...pipeline.report import collect, write_report
from ...pipeline.run import judge_bundles
from ...registries import BACKENDS
from ...util.fsio import read_json, read_text
from .. import fixtures
from ..model import Case, Context, Observation, check, equals
from ..scripted import MODEL, ScriptedProvider, ScriptedSession

__all__ = ["CASES"]

#: The corpus case judges at the cheaper level: it is about how many bundles are
#: reported and where, not about how any one of them is judged.
CORPUS_LEVEL = Level.STATIC

#: The fixture the build case formalizes. It is the one whose artifacts a
#: full session accepts, so a mismatch is a defect in the pipeline rather than an
#: expected rejection.
SOURCE = "coin-change-sound"

#: The requests a build sends after the drafting session, in order. Written out rather
#: than derived, because a build that quietly stopped asking about rivals or about
#: `conformance.py` would otherwise still look like a passing build.
STAGES = (
    "twin",
    "uniqueness",
    "uniqueness",
    "soundness",
    "correspondence",
    "conformance",
)


def corpus(context: Context) -> list[Observation]:
    """A corpus of bundles is judged, reported, and not judged twice."""
    tasks = fixtures.tasks(context.settings)
    targets = fixtures.coexisting()
    bundles = [
        fixtures.stage(target, tasks[target.task_id], context.settings) for target in targets
    ]
    check(len(bundles) > 1, "the corpus case needs more than one fixture to be worth running")
    equals(
        len({bundle.root for bundle in bundles}),
        len(bundles),
        "distinct bundle directories the corpus was staged into",
    )

    result = judge_bundles(bundles, settings=context.settings, level=CORPUS_LEVEL)
    errors = tuple(outcome.error for outcome in result.errors())
    check(not errors, f"bundle(s) could not be judged: {'; '.join(errors)}")
    equals(result.total, len(bundles), "bundles the run covered")

    expected = {str(outcome): 0 for outcome in Outcome}
    for target in targets:
        expected[str(target.expected(CORPUS_LEVEL))] += 1
    equals(result.report.counts(), expected, "outcomes across the corpus")

    reread = collect(context.settings.bundle_root, level=CORPUS_LEVEL)
    equals(reread.counts(), expected, "outcomes read back from the bundle root alone")
    equals(reread.total, len(bundles), "bundles discovered under the root")

    document, rendered = write_report(reread, context.path("report"))
    check(document.is_file() and rendered.is_file(), "the report files were not written")
    written = read_json(document)
    equals(written["counts"], expected, "outcomes in the written report")
    equals(len(written["bundles"]), len(bundles), "bundle rows in the written report")
    check(
        f"level={CORPUS_LEVEL}" in read_text(rendered),
        "the rendered report does not state the level it was written at",
    )

    # Only one gate is asked for on the second pass: the point is which bundles are
    # visited, not what the gates say, and the classification still comes from each
    # bundle's whole `manifest.json`.
    again = judge_bundles(
        bundles,
        settings=context.settings,
        level=CORPUS_LEVEL,
        only=("artifact.integrity",),
        skip_certified=True,
    )
    rejudged = {outcome.task_key for outcome in again.outcomes if outcome.judged}
    certified = {row.task_id for row in reread.rows if row.outcome is Outcome.CERTIFIED}
    check(certified, "no fixture certified, so skipping certified bundles proves nothing")
    equals(
        sorted(certified & rejudged),
        [],
        "certified bundles judged again despite skip_certified",
    )
    equals(
        len(rejudged), len(bundles) - len(certified), "bundles judged again on the second pass"
    )

    return [
        Observation("counts", ", ".join(f"{k}={v}" for k, v in expected.items() if v)),
        Observation("report", f"{document.name}, {rendered.name}"),
        Observation("second pass", f"{len(rejudged)} of {len(bundles)} judged again"),
    ]


def scripted_build(context: Context) -> list[Observation]:
    """A build writes back the artifacts it was handed, byte for byte."""
    target = fixtures.fixture(SOURCE)
    settings = context.tuned(bundle_root=context.path("built"))
    provider = ScriptedProvider(source=SOURCE)
    session = ScriptedSession(source=SOURCE)
    result = build(
        fixtures.tasks(settings)[target.task_id],
        backend=BACKENDS.get(target.backend),
        provider=provider,
        settings=settings,
        session=session,
    )
    check(
        result.usable,
        f"the build wrote no solution: checker {result.formalization.check.status}; "
        f"{'; '.join(result.formalization.notes)}",
    )
    bundle, formalization = result.bundle, result.formalization

    equals(tuple(session.answered), ("draft",), "sessions the build started")
    equals(tuple(provider.answered), STAGES, "requests the build sent after the session")
    check(
        formalization.accepted,
        f"the checker did not accept the fixture's own solution: "
        f"{formalization.check.status} ({formalization.check.detail})",
    )

    artifacts = target.artifacts()
    check(artifacts, f"fixture {SOURCE!r} declares no artifacts to compare against")
    for relative in artifacts:
        produced = bundle.root / relative
        check(produced.is_file(), f"the build wrote no {relative}")
        equals(
            read_text(produced),
            read_text(target.directory / relative),
            f"{relative} as written by the build",
        )
    check(
        (bundle.root / "notes.md").is_file(),
        "the build left no notes.md, so a reviewer has no account of how the artifacts "
        "were drafted",
    )

    drafted = bundle.manifest().provenance.get("formalization", {})
    equals(drafted.get("provider"), "scripted", "the provider recorded in manifest.json")
    equals(drafted.get("model"), MODEL, "the model recorded in manifest.json")
    equals(len(drafted.get("requests", ())), len(STAGES), "requests recorded in manifest.json")
    equals(
        (drafted.get("session") or {}).get("status"),
        "VERIFIED",
        "what manifest.json keeps of the drafting session's report",
    )
    return [
        Observation("artifacts", f"{len(artifacts)} compared byte for byte"),
        Observation("stages", ", ".join([*session.answered, *provider.answered])),
        Observation("checker", str(formalization.check.status)),
    ]


CASES: tuple[Case, ...] = (
    Case(
        id="pipeline.corpus",
        summary="a corpus of bundles is judged, reported, and not judged twice",
        procedure=corpus,
        requires=fixtures.REQUIRES,
    ),
    Case(
        id="pipeline.build",
        summary="a formalization session writes back its artifacts byte for byte",
        procedure=scripted_build,
        requires=fixtures.REQUIRES,
    ),
)
