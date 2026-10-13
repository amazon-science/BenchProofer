# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The scripted provider and session that stand in for a model in a hermetic run.

Everything the offline suite says about drafting, reviewing and repairing is said
through these two, so two properties of them carry the weight of the rest:

* it recognizes the prompts the tool actually sends. The prompts live in packaged
  templates and the provider keys off phrases in them, so a template reworded in one
  place and not the other would leave the offline suite exercising nothing. The first
  test renders every opening template and requires each to resolve to its stage.
* it answers from the fixture rather than from a script kept beside it. A stage the
  fixture has no artifact for raises, which is what stops a case from passing on a
  reply nobody wrote down.

The session is recognized by the report it is asked to submit rather than by its prompt,
so the same holds of it through the report fields each stage declares.

No checker, oracle, or network is involved here: this is about the two scripts alone.
"""

from __future__ import annotations

import shutil
from collections import defaultdict
from dataclasses import replace
from pathlib import Path
from string import Template
from typing import Any

import pytest

from benchproofer.audit import prompts as audit_prompts
from benchproofer.audit.agents import _FIELDS as LANE_FIELDS
from benchproofer.core import markers
from benchproofer.core.bundle import Bundle
from benchproofer.core.prompts import RULES, SHARED, Library
from benchproofer.errors import ProviderError
from benchproofer.formalize import prompts as formalize_prompts
from benchproofer.llm.agentic import SessionSpec
from benchproofer.llm.base import Message, ProviderConfig
from benchproofer.registries import BACKENDS
from benchproofer.smoke.fixtures import fixture
from benchproofer.smoke.scripted import (
    MODEL,
    REVIEW_MODEL,
    ScriptedProvider,
    ScriptedSession,
    reviewing,
    session_of,
    stage_of,
)

SOUND = "coin-change-sound"
WEAK = "coin-change-weak"

#: Every template a session opens a request with, and the stage it must resolve to.
#: The rest of the templates -- the system prompts, and the retry and repair follow-ups
#: -- are later turns of a conversation that opened with one of these, and the provider
#: reads the opening message, so they are not stages of their own.
OPENINGS: tuple[tuple[Library, str, dict[str, str], str], ...] = (
    (formalize_prompts.LIBRARY, "twin", {}, "twin"),
    (formalize_prompts.LIBRARY, "rival", {"case": "a uniqueness rival"}, "uniqueness"),
    (
        formalize_prompts.LIBRARY,
        "rival",
        {"case": "an admissibility case"},
        "admissibility",
    ),
    (formalize_prompts.LIBRARY, "correspondence", {}, "correspondence"),
    (formalize_prompts.LIBRARY, "conformance", {}, "conformance"),
    (formalize_prompts.LIBRARY, "axioms", {}, "axioms"),
)

#: The templates that are follow-up turns rather than openings. Listed so that a new
#: template cannot be added without deciding which of the two it is. `sites`,
#: `conformance-bridge`, `passing`, `callees` and the `-rules` templates are neither: each is
#: a section rendered into other prompts -- `sites` into two openings, `conformance-bridge`
#: into `conformance-run`, `passing` and a `-rules` section into the session asking one
#: question, `callees` into the system prompts that say how a file states a callee,
#: `conformance-copy` and `conformance-port` into the rules `conformance.py` is held to --
#: and never sent on its own.
FOLLOW_UPS = {
    formalize_prompts.LIBRARY: {
        "conformance-bridge",
        "conformance-repair",
        "conformance-run",
        "correspondence-system",
        "program-system",
        "retry",
        "sites",
        "system",
        *(name for name in formalize_prompts.names() if name.endswith(RULES)),
    },
    audit_prompts.LIBRARY: {
        "port",
        "programs",
        "refutation",
        "system",
        "tests",
        *(name for name in audit_prompts.names() if name.endswith(RULES)),
    },
    SHARED: {
        "callees",
        "conformance-copy",
        "conformance-port",
        *(name for name in SHARED.names() if name.endswith(RULES)),
    },
}

#: The templates a *session* sends rather than a provider: a model with tools and turns
#: of its own, which this provider never sees. Listed for the same reason as the other
#: two sets -- so a new template has to be classified -- and separately, because the
#: scripted session tells its stages apart by the report each asks for, not by its prompt.
SESSION_PROMPTS = {
    formalize_prompts.LIBRARY: {
        "draft-agent",
        "draft-agent-report",
        "prove-agent",
        "prove-agent-system",
        "prove-claim",
        "prove-lean",
        "prove-nagini",
        "prove-probe",
        "prove-tactics",
        "prove-velvet",
        "prove-witness",
        "repair-agent",
        "repair-agent-report",
        "repair-agent-system",
        # The sections of `repair-agent` giving the rules of each file beside the solution.
        "repair-axioms",
        "repair-conformance",
        "repair-correspondence",
        "repair-rivals",
        "repair-twins",
    },
    audit_prompts.LIBRARY: {
        "agent-attack",
        "agent-disclosure",
        "agent-equivalence",
        "agent-faithfulness",
        "agent-fuzz",
        "agent-report",
        "agent-system",
        "agent-validation",
    },
    SHARED: set(),
}


def _rendered(library: Library, name: str, fields: dict[str, str]) -> str:
    """One template with every placeholder filled, except those the caller pins.

    The pinned ones are the placeholders that appear inside a phrase the provider keys
    off, such as which kind of rival is being asked for.
    """
    values: defaultdict[str, str] = defaultdict(lambda: "(a value)")
    values.update(fields)
    return Template(library.template(name)).safe_substitute(values)


@pytest.mark.parametrize(
    ("library", "name", "fields", "stage"),
    OPENINGS,
    ids=[f"{name}-{stage}" for _, name, _, stage in OPENINGS],
)
def test_every_opening_prompt_resolves_to_the_stage_that_answers_it(
    library: Library, name: str, fields: dict[str, str], stage: str
) -> None:
    assert stage_of(_rendered(library, name, fields)) == stage


@pytest.mark.parametrize("library", list(FOLLOW_UPS), ids=lambda item: item.package)
def test_every_packaged_template_is_classified(library: Library) -> None:
    """A new template must be classified, so it cannot go unrecognized unnoticed."""
    openings = {name for shipped, name, _, _ in OPENINGS if shipped is library}

    assert set(library.names()) == openings | FOLLOW_UPS[library] | SESSION_PROMPTS[library]


def test_an_unrecognized_prompt_says_so_rather_than_guessing() -> None:
    with pytest.raises(ProviderError, match="does not recognize this prompt"):
        stage_of("Please do something the templates never ask for.")

    with pytest.raises(ProviderError, match="was given no messages"):
        ScriptedProvider().complete([])


def test_a_review_answers_under_a_name_of_its_own_even_when_the_run_names_none() -> None:
    """`audit.independence` compares reviewer with author, so the two must differ."""
    reviewer, author = reviewing(SOUND), ScriptedProvider(source=SOUND)
    assert REVIEW_MODEL != MODEL
    assert (reviewer.config.model, author.config.model) == (REVIEW_MODEL, MODEL)

    reviewer.configure(ProviderConfig(model=""))
    author.configure(ProviderConfig(model=""))

    assert (reviewer.config.model, author.config.model) == (REVIEW_MODEL, MODEL)


def test_the_same_request_twice_gets_the_same_artifact() -> None:
    """A retry is a second attempt at one request, not a request for the next rival."""
    provider = ScriptedProvider(source=SOUND)
    prompt = _rendered(formalize_prompts.LIBRARY, "rival", {"case": "a uniqueness rival"})

    first = provider.complete([Message.user(prompt)]).text
    again = provider.complete([Message.user(prompt)]).text

    assert first == again
    assert provider.answered == ["uniqueness", "uniqueness"]


def test_consecutive_requests_walk_the_fixture_in_order_and_then_stop() -> None:
    """Two rivals ship, so a third request is a request the fixture cannot answer."""
    provider = ScriptedProvider(source=SOUND)
    asked = [
        _rendered(
            formalize_prompts.LIBRARY,
            "rival",
            {"case": "a uniqueness rival", "rivals_rules": brief},
        )
        for brief in ("the first", "the second", "the third")
    ]

    bodies = [provider.complete([Message.user(prompt)]).text for prompt in asked[:2]]

    assert bodies[0] != bodies[1]
    with pytest.raises(ProviderError, match="ships no rival 'uniqueness-3'"):
        provider.complete([Message.user(asked[2])])


# ---- the scripted session -------------------------------------------------


def _asked(cwd: Path, submit: str, fields: dict[str, Any] | None = None) -> SessionSpec:
    """A request for a session, as a stage makes it, but for its prompt."""
    return SessionSpec(system="", prompt="", cwd=cwd, submit=submit, fields=fields or {})


def _workspace(root: Path, name: str = SOUND) -> Bundle:
    """A session's workspace holding one fixture as its bundle, as `lay_out` places it."""
    bundle = root / "bundles" / "fixtures" / "coin-change" / "falsifier"
    shutil.copytree(fixture(name).directory, bundle)
    return Bundle(bundle)


@pytest.mark.parametrize("lane", sorted(LANE_FIELDS))
def test_every_auditor_s_request_resolves_to_that_auditor(lane: str) -> None:
    fields, _ = LANE_FIELDS[lane]  # type: ignore[index]

    assert session_of(_asked(Path(), "review", fields)) == lane


def test_a_session_it_does_not_know_says_so_rather_than_guessing() -> None:
    with pytest.raises(ProviderError, match="does not recognize a 'axiom' session"):
        ScriptedSession().run(_asked(Path(), "axiom"))


def test_a_drafting_session_writes_the_fixture_s_solution_into_its_bundle(
    tmp_path: Path,
) -> None:
    bundle = _workspace(tmp_path, WEAK)
    session = ScriptedSession(source=SOUND)

    outcome = session.run(_asked(tmp_path, "draft"))

    assert bundle.solution() == (fixture(SOUND).directory / "solution.py").read_text()
    assert outcome.payload is not None and outcome.payload["status"] == "VERIFIED"
    assert session.answered == ["draft"]
    assert session.model == MODEL


def test_a_repair_session_writes_every_file_of_the_repaired_fixture(tmp_path: Path) -> None:
    bundle = _workspace(tmp_path, WEAK)
    sound = fixture(SOUND)

    ScriptedSession(source=WEAK, repaired=SOUND).run(_asked(tmp_path, "repair"))

    for relative in sound.artifacts():
        assert (bundle.root / relative).read_text() == (sound.directory / relative).read_text()


def test_the_attack_auditor_files_the_fixture_s_cases_against_the_shipped_specification(
    tmp_path: Path,
) -> None:
    """Each submission carries the bundle's specification and a case's implementation."""
    bundle = _workspace(tmp_path, SOUND)
    fields, _ = LANE_FIELDS["attack"]
    cases = [rival for rival in bundle.battery() if rival.kind in ("uniqueness", "soundness")]

    outcome = ScriptedSession(source=SOUND).run(_asked(tmp_path, "review", fields))

    assert outcome.payload is not None
    filed = [*outcome.payload["attacks"], *outcome.payload["controls"]]
    assert len(filed) == len(cases)
    comment = BACKENDS.get(fixture(SOUND).backend).comment
    shipped = markers.parse(bundle.solution(), comment)["spec"].text
    for entry in filed:
        written = (tmp_path / entry["file"]).read_text()
        assert markers.parse(written, comment)["spec"].text == shipped
    assert {entry["claim"] for entry in filed} == {rival.rationale for rival in cases}


def test_a_judging_auditor_whose_fixture_declares_no_judgment_submits_nothing(
    tmp_path: Path,
) -> None:
    """As a session that ended without submitting, which files nothing."""
    fields, _ = LANE_FIELDS["faithfulness"]
    session = ScriptedSession(source=replace(fixture(SOUND), review={}))

    outcome = session.run(_asked(tmp_path, "review", fields))

    assert outcome.payload is None
    assert "declares no faithfulness judgment" in outcome.detail


def test_a_proof_session_reports_it_is_stuck_and_writes_nothing(tmp_path: Path) -> None:
    outcome = ScriptedSession().run(_asked(tmp_path, "proof"))

    assert outcome.payload == {"status": "stuck", "notes": "a scripted session writes no proof"}
    assert list(tmp_path.iterdir()) == []
