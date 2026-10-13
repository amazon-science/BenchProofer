# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""A provider and an agent session that answer a whole run from a fixture bundle.

Drafting, reviewing and repairing are the parts of the pipeline that need a model,
which would make them the parts a hermetic run could not exercise. These two close
that gap. `ScriptedSession` recognizes each session from the report it is asked to
submit, writes the fixture's files where that session's work is read back from, and
submits the report. `ScriptedProvider` recognizes each request drafting sends after the
solution from its prompt and replies with what the fixture already ships, formatted the
way a model is asked to format it. Neither reaches a model.

The replies are reconstructed from the bundle's own files, never stored as separate
text, so a fixture and the script that reproduces it cannot drift apart. What the
resulting cases can therefore assert is strong: not merely that a session ran, but that
it wrote back the artifacts it was given, byte for byte, and that the gates reached the
verdicts the fixture declares.

Four things a review needs and a draft does not:

* the implementations it submits are the fixture's own property-based test suite -- a wrong one
  the specification is supposed to accept is what a uniqueness rival is, and a correct one
  written differently is what a soundness rival is;
* its judgments come from the fixture's ``[review.*]`` sections, since no program can
  decide whether a specification describes a task;
* its fuzzers come from the fixture's ``[[fuzzer]]`` sections, because a bundle ships
  its own program for what it assumes and not the one a reviewer would write against it;
* it answers under a name of its own (`REVIEW_MODEL`, and `reviewing` for the provider
  that names the reviewer), because a review by the model that drafted the bundle is not
  an independent one and the gates say so.

Neither is a mock. Extraction, splicing, checking, repair, re-running submissions and the
manifest all run exactly as they do against a real model, and a request the fixture has no
artifact for raises `ProviderError` rather than inventing one.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any, ClassVar

from ..core import markers
from ..core.bundle import Bundle
from ..core.scripts import SCRATCH
from ..errors import BenchproofError, ProviderError
from ..llm.agentic import AgentSession, SessionSpec, StepOutcome
from ..llm.base import Completion, Message, Provider, ProviderConfig
from ..registries import BACKENDS
from ..util.fsio import load_toml, read_text, write_text
from .fixtures import Fixture, fixture

__all__ = [
    "MODEL",
    "REVIEW_MODEL",
    "ScriptedProvider",
    "ScriptedSession",
    "reviewing",
    "session_of",
    "stage_of",
]

#: The model name recorded for a scripted run. It is not a real model, and a
#: report that shows it is telling the truth about where the artifacts came from.
MODEL = "fixture-script"
#: The model name a scripted *review* records. Different from `MODEL` on purpose:
#: `audit.independence` compares who reviewed a bundle with who drafted it.
REVIEW_MODEL = "fixture-review"

#: Prompt fragments that identify a stage, most specific first.
_MARKERS: tuple[tuple[str, str], ...] = (
    ("Write the pre-fix", "twin"),
    ("Write a uniqueness rival.", "uniqueness"),
    ("Write a soundness rival.", "soundness"),
    ("Write an admissibility case.", "admissibility"),
    ("Write `correspondence.md`", "correspondence"),
    ("tries to refute that claim", "conformance"),
    ("Write `axioms.py`.", "axioms"),
)


def stage_of(prompt: str) -> str:
    """Name the stage a prompt belongs to.

    Raises:
        ProviderError: The prompt matches no stage, which means the templates
            changed and this provider needs to change with them.
    """
    for fragment, stage in _MARKERS:
        if fragment in prompt:
            return stage
    opening = prompt.strip().splitlines()[0] if prompt.strip() else "(empty)"
    raise ProviderError(f"the scripted provider does not recognize this prompt: {opening!r}")


def reviewing(source: Fixture | str | None = None) -> ScriptedProvider:
    """A scripted provider under `REVIEW_MODEL`, which names the reviewer of a review."""
    return ScriptedProvider(ProviderConfig(model=REVIEW_MODEL), source=source)


class ScriptedProvider(Provider):
    """Answer each drafting request with a fixture bundle's own artifact."""

    name: ClassVar[str] = "scripted"
    summary: ClassVar[str] = "answers drafting's requests from a packaged fixture"
    deterministic: ClassVar[bool] = True

    def __init__(
        self, config: ProviderConfig | None = None, *, source: Fixture | str | None = None
    ) -> None:
        """Script a run's requests from one fixture.

        Args:
            config: Provider settings; the model name defaults to `MODEL`.
            source: The fixture whose artifacts every reply is drawn from.
        """
        super().__init__(config or ProviderConfig(model=MODEL))
        self.fixture = _resolve(source)
        self.comment = BACKENDS.get(self.fixture.backend).comment
        #: Stages answered so far, in order, so a case can assert what was asked.
        self.answered: list[str] = []
        #: Prompts answered per stage. A stage asked repeatedly walks the fixture's
        #: artifacts in order, while a retry of one request -- the same prompt again --
        #: gets the same artifact rather than the next one.
        self._asked: dict[str, list[str]] = {}

    def configure(self, config: ProviderConfig) -> None:
        """Apply the run's settings, keeping this instance's own model name.

        A run that named no model would otherwise record an empty one, and the point of
        `MODEL` is that a report says where the artifacts really came from. The instance's
        name is kept rather than the constant, so a reviewer configured by a run that
        named no audit model is still recorded as a reviewer.
        """
        if config.model:
            self.config = config
        else:
            self.config = replace(config, model=self.config.model or MODEL)

    def complete(
        self,
        messages: list[Message],
        *,
        system: str = "",
        max_tokens: int = 4096,
        temperature: float = 0.0,
    ) -> Completion:
        """Answer whichever stage the first user message asks about.

        The stage prompt is the first message of every exchange, so a retry turn
        resolves to the same stage and gets the same answer.

        Raises:
            ProviderError: The conversation is empty, the prompt matches no stage,
                or the fixture ships no artifact for it.
        """
        if not messages:
            raise ProviderError("the scripted provider was given no messages")
        prompt = messages[0].content
        stage = stage_of(prompt)
        text = self._reply(stage, prompt)
        self.answered.append(stage)
        return Completion(
            text=text,
            model=self.config.model or MODEL,
            stop_reason="end_turn",
            input_tokens=_tokens(system) + sum(_tokens(m.content) for m in messages),
            output_tokens=_tokens(text),
        )

    # ---- stages ---------------------------------------------------------

    def _reply(self, stage: str, prompt: str) -> str:
        if stage == "twin":
            return _labelled(
                "RATIONALE",
                "the implementation as it was before the fix",
                self._impl("twins/twin.py"),
            )
        if stage in ("uniqueness", "soundness", "admissibility"):
            body, rationale = self._rival(f"{stage}-{self._cursor(stage, prompt)}")
            return _labelled("RATIONALE", rationale, body)
        if stage == "correspondence":
            return self._read("correspondence.md")
        if stage == "conformance":
            return _fenced(self._read("conformance.py"))
        return _fenced(self._read("axioms.py"))

    # ---- fixture access -------------------------------------------------

    def _cursor(self, stage: str, prompt: str) -> int:
        """Which of a repeated stage's artifacts this prompt is asking for, from one."""
        asked = self._asked.setdefault(stage, [])
        if prompt not in asked:
            asked.append(prompt)
        return asked.index(prompt) + 1

    def _rival(self, rival_id: str) -> tuple[str, str]:
        """One rival's implementation, and the rationale its index records.

        Raises:
            ProviderError: The fixture ships no such case, which is how a session that
                asks for more rivals than the fixture has stops rather than repeats.
        """
        entry = self._index().get(rival_id)
        if entry is None:
            raise ProviderError(f"fixture {self.fixture.name!r} ships no rival {rival_id!r}")
        body = self._impl(f"rivals/{entry['file']}")
        return body, str(entry.get("rationale", rival_id))

    def _impl(self, relative: str) -> str:
        """The implementation region of one of the fixture's files.

        Raises:
            ProviderError: The file does not ship, or its marker regions cannot be read.
        """
        source = self._read(relative)
        try:
            return markers.parse(source, self.comment)["impl"].text
        except BenchproofError as exc:
            raise ProviderError(f"{self.fixture.name}/{relative}: {exc}") from exc

    def _read(self, relative: str) -> str:
        path = self.fixture.directory / relative
        if not path.is_file():
            raise ProviderError(f"fixture {self.fixture.name!r} ships no {relative}")
        return read_text(path)

    def _index(self) -> dict[str, dict[str, object]]:
        path = self.fixture.directory / "rivals" / "index.toml"
        if not path.is_file():
            return {}
        entries = load_toml(path).get("rival", [])
        return {str(entry["id"]): entry for entry in entries}


#: Which auditor a request is for, by a field of the report it asks for; a judging auditor
#: asking for neither is the disclosure auditor.
_LANES: tuple[tuple[str, str], ...] = (
    ("attacks", "attack"),
    ("fuzzers", "fuzz"),
    ("coverage", "faithfulness"),
    ("operations", "equivalence"),
    ("rulings", "validation"),
)


def session_of(spec: SessionSpec) -> str:
    """Name the session a request is for: `draft`, `repair`, `proof`, or an auditor.

    Raises:
        ProviderError: The request asks for a report no session here submits, which means
            a stage changed and this session needs to change with it.
    """
    if spec.submit in ("draft", "repair", "proof"):
        return spec.submit
    if spec.submit == "review":
        return next((lane for field, lane in _LANES if field in spec.fields), "disclosure")
    raise ProviderError(f"the scripted session does not recognize a {spec.submit!r} session")


class ScriptedSession(AgentSession):
    """Answer each session of a run with a fixture bundle's own files, reaching no model.

    What it writes goes where the session's work is read back from, in its workspace:

    * a drafting session's solution file, into the bundle there;
    * a repair's author files -- the solution, the pre-fix implementations, the property-based
      test suite, `correspondence.md`, `conformance.py`, `axioms.py`, those the fixture ships --
      into the bundle there;
    * a proof session's nothing: a fixture ships no proof to write, so it reports `stuck`;
    * the attack auditor's attacks, the fixture's uniqueness rivals, and its controls, the
      fixture's soundness rivals, each spliced into the solution the bundle there ships,
      under `scratch/`;
    * the fuzz auditor's programs, the ones the fixture declares, under `scratch/`;
    * a judging auditor's judgment, the one the fixture declares, and no report where it
      declares none, as a session that ended without submitting files nothing;
    * the attack validation auditor's report with no ruling in it: what an attack or a control
      that cannot be determined by execution shows about the task is not something a
      fixture's files say.
    """

    name: ClassVar[str] = "scripted"
    summary: ClassVar[str] = "answers a run's sessions from a packaged fixture"
    remote: ClassVar[bool] = False

    def __init__(
        self,
        model: str = "",
        *,
        source: Fixture | str | None = None,
        repaired: Fixture | str | None = None,
    ) -> None:
        """Script a run's sessions from one fixture, and its repairs from another.

        Args:
            model: The model name recorded; `MODEL` when unset.
            source: The fixture whose files every session but a repair writes.
            repaired: The fixture a repair writes into the bundle. Left unset, a repair
                writes the source fixture's files, which leaves a bundle drafted from it
                as it was -- a repair that changed nothing, worth scripting too.
        """
        super().__init__(model or MODEL)
        self.fixture = _resolve(source)
        self.repaired = None if repaired is None else _resolve(repaired)
        #: The sessions run so far, in order, and what each was asked, so a case can assert
        #: which sessions a stage started and what it gave them.
        self.answered: list[str] = []
        self.asked: list[SessionSpec] = []

    def run(self, spec: SessionSpec) -> StepOutcome:
        """Write what the fixture ships for this session, and submit its report.

        Raises:
            ProviderError: The request asks for a report no session here submits, or the
                fixture ships nothing a drafting session or a repair could write.
        """
        kind = session_of(spec)
        self.answered.append(kind)
        self.asked.append(spec)
        cwd = Path(spec.cwd)
        payload: dict[str, Any] | None
        if kind == "draft":
            payload = self._draft(_bundle(cwd))
        elif kind == "repair":
            payload = self._repair(_bundle(cwd))
        elif kind == "proof":
            payload = {"status": "stuck", "notes": "a scripted session writes no proof"}
        elif kind == "attack":
            payload = self._attack(cwd, _bundle(cwd))
        elif kind == "fuzz":
            payload = self._fuzz(cwd)
        elif kind == "validation":
            payload = {"rulings": []}
        else:
            payload = self._judgment(kind)
        return StepOutcome(
            text=f"scripted from fixture {self.fixture.name!r}",
            payload=payload,
            turns=1,
            detail="" if payload is not None else f"the fixture declares no {kind} judgment",
        )

    def _draft(self, bundle: Bundle) -> dict[str, Any]:
        """Write the fixture's solution file into ``bundle``."""
        solution = _solution(self.fixture)
        write_text(bundle.root / solution.name, read_text(solution))
        return {"status": "VERIFIED", "summary": f"the solution of {self.fixture.name}"}

    def _repair(self, bundle: Bundle) -> dict[str, Any]:
        """Write every author file of the repaired fixture into ``bundle``."""
        target = self.repaired or self.fixture
        for relative in target.artifacts():
            write_text(bundle.root / relative, read_text(target.directory / relative))
        return {"status": "REPAIRED", "summary": f"the files of {target.name}"}

    def _attack(self, cwd: Path, bundle: Bundle) -> dict[str, Any]:
        """File the fixture's wrong cases as attacks and its correct ones as controls."""
        comment = BACKENDS.get(self.fixture.backend).comment
        shipped = bundle.solution()
        cases = Bundle(self.fixture.directory)
        filed: dict[str, list[dict[str, str]]] = {"attacks": [], "controls": []}
        for field, kind, noun in (
            ("attacks", "uniqueness", "attack"),
            ("controls", "soundness", "control"),
        ):
            for rival in (rival for rival in cases.battery() if rival.kind == kind):
                written = f"{SCRATCH}/{noun}-{len(filed[field]) + 1}{Path(rival.file).suffix}"
                write_text(cwd / written, _spliced(shipped, cases.rival_source(rival), comment))
                filed[field].append({"file": written, "claim": rival.rationale})
        return filed

    def _fuzz(self, cwd: Path) -> dict[str, Any]:
        """File the programs the fixture declares against what its specification assumes."""
        written = []
        for attack in self.fixture.fuzzers:
            file = f"{SCRATCH}/{attack.id}.fuzz.py"
            write_text(cwd / file, attack.program)
            written.append(
                {
                    "callee": attack.callee,
                    "file": file,
                    "claim": attack.claim,
                    "changed": False,
                    "how": "the golden patch leaves it as it was",
                }
            )
        return {"fuzzers": written}

    def _judgment(self, role: str) -> dict[str, Any] | None:
        """The judgment the fixture declares about one question, or None for none."""
        try:
            judged = self.fixture.judgment(role)
        except BenchproofError:
            return None
        return {
            "verdict": judged.verdict,
            "summary": judged.summary,
            "findings": list(judged.findings),
            "coverage": [
                {"behavior": behavior, "tested_by": test, "covered_by": obligation}
                for behavior, test, obligation in judged.coverage
            ],
            "operations": [
                {"kind": kind, "detail": detail} for kind, detail in judged.operations
            ],
        }


def _bundle(workspace: Path) -> Bundle:
    """The one bundle a session's workspace holds, at `bundles/<benchmark>/<task>/<backend>`.

    Raises:
        ProviderError: The workspace holds none, or more than one.
    """
    found = sorted(path for path in (workspace / "bundles").glob("*/*/*") if path.is_dir())
    if len(found) != 1:
        raise ProviderError(
            f"the scripted session expects one bundle under {workspace / 'bundles'}, "
            f"and finds {len(found)}"
        )
    return Bundle(found[0])


def _solution(target: Fixture) -> Path:
    """The fixture's solution file.

    Raises:
        ProviderError: The fixture ships none.
    """
    try:
        return Bundle(target.directory).solution_path
    except BenchproofError as exc:
        raise ProviderError(f"fixture {target.name!r} ships no solution file: {exc}") from exc


def _spliced(solution: str, case: str, comment: str) -> str:
    """``solution`` carrying ``case``'s implementation and, where it has one, its proof."""
    for kind in markers.ELIDED_REGIONS:
        if markers.named(markers.parse(case, comment), kind):
            solution = markers.transplant(solution, case, comment, kind)
    return solution


def _resolve(source: Fixture | str | None) -> Fixture:
    """The fixture a script draws from, named or given whole."""
    return source if isinstance(source, Fixture) else fixture(source or "coin-change-sound")


def _labelled(field: str, prose: str, body: str) -> str:
    """One implementation, in the shape a template asks for: a field line, then a block."""
    return f"{field}: {prose}\n\n{_fenced(body)}"


def _fenced(text: str) -> str:
    """Wrap a body in the single fenced block a reply is expected to carry."""
    return f"```python\n{text.strip()}\n```\n"


def _tokens(text: str) -> int:
    """A stand-in token count, so a scripted run's accounting is not all zeros."""
    return max(1, len(text) // 4)
