# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Local stand-ins for the checker, the benchmark's oracle and the model.

Each answers from a script the test writes and reads nothing it is handed, so a test
asserts what the tool did with an answer it was told, not what a property search found
or how loaded the machine was. And a fix written from a file's two versions, with what it
edits read from them, as drafting reads it from the repository's working copy.
"""

from __future__ import annotations

import difflib
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from benchproofer.backends.base import Backend, BackendKind, CheckResult
from benchproofer.backends.falsifier import FalsifierBackend
from benchproofer.core.plugin import Availability
from benchproofer.core.task import Task
from benchproofer.gates.base import GateContext
from benchproofer.llm.base import Completion, Message, Provider
from benchproofer.oracles.base import Candidate, Oracle, OracleResult, Program
from benchproofer.util.patch import Edited, edited_definitions

__all__ = [
    "Accepting",
    "Answering",
    "Proving",
    "Refusing",
    "Rigged",
    "Ruling",
    "Screening",
    "Scripted",
    "revised",
]


def revised(path: str, before: str, after: str, *, header: str = "") -> tuple[str, Edited]:
    """The unified diff taking ``before`` to ``after`` at ``path``, and what it edits.

    ``header`` is written after each hunk's line numbers, where `git` writes the nearest
    definition above the hunk.
    """
    lines = difflib.unified_diff(
        before.splitlines(keepends=True),
        after.splitlines(keepends=True),
        f"a/{path}",
        f"b/{path}",
    )
    patch = f"diff --git a/{path} b/{path}\n" + "".join(lines)
    if header:
        patch = re.sub(r"(?m)^@@ .* @@$", lambda hunk: f"{hunk.group(0)} {header}", patch)
    return patch, edited_definitions(patch, {path: before} if before else {}, {path: after})


class Accepting(Backend):
    """A checker that accepts every file, so that every stage of a session runs."""

    name = "accepting"
    language = "Python"
    extension = ".py"
    comment = "#"
    kind = BackendKind.FALSIFIER

    def check(self, source: str, *, workdir: Path, timeout_s: float = 120.0) -> CheckResult:
        return CheckResult.ok("accepted, because this backend accepts everything")


class Refusing(Accepting):
    """A checker that rejects every file on its merits."""

    name = "refusing"

    def check(self, source: str, *, workdir: Path, timeout_s: float = 120.0) -> CheckResult:
        return CheckResult.no("property_change_sums_to_the_amount failed on cents=40")


class Screening(FalsifierBackend):
    """The shipped falsifier's metadata, with its checker and its probe removed.

    A gate test needs the real comment token, specification view and banned tokens, and
    none of a property search's cost. A gate reaches the checker through
    `GateContext.check`, which `Rigged` answers, so calling this one is a defect in the test.
    """

    name = "screening"

    def availability(self) -> Availability:
        return Availability.ok()

    def check(self, source: str, *, workdir: Path, timeout_s: float = 120.0) -> CheckResult:
        raise AssertionError("a gate reaches the checker through GateContext.check")


class Proving(Screening):
    """The same metadata, from a checker whose acceptance is a proof.

    Paired with `Screening`, only the meaning of an accepting verdict differs.
    """

    name = "proving"
    kind = BackendKind.PROVER


class Answering(Screening):
    """The same metadata, with a checker that answers from a script.

    A review session calls its checker itself, once per submission, so a test of a
    review needs a backend that answers.
    """

    name = "answering"

    def __init__(self, *answers: CheckResult) -> None:
        #: Answers in the order they are given, the last one reused after that.
        self.answers = answers or (CheckResult.ok("accepted by script"),)
        #: The label each call was made under, which names the submission and the round.
        self.checked: list[str] = []

    def check(self, source: str, *, workdir: Path, timeout_s: float = 120.0) -> CheckResult:
        self.checked.append(workdir.name)
        return self.answers[min(len(self.checked), len(self.answers)) - 1]


class Ruling(Oracle):
    """An oracle that answers from a scripted context, by label.

    Both things a benchmark's environment is asked for are scripted: its judgment of a
    candidate, and what a program run in it printed.
    """

    name = "ruling"
    summary = "answers from a script, one entry per candidate"

    def __init__(self, context: Rigged) -> None:
        self.context = context

    def judge(
        self,
        task: Task,
        candidate: Candidate,
        *,
        workdir: Path,
        timeout_s: float = 300.0,
    ) -> OracleResult:
        self.context.judged.append(candidate.label)
        ruling = self.context.rulings.get(candidate.label, self.context.ruling)
        if isinstance(ruling, OracleResult):
            return ruling
        asked = self.context.judged.count(candidate.label)
        return ruling[min(asked, len(ruling)) - 1]

    def probe(
        self,
        task: Task,
        program: Program,
        *,
        workdir: Path,
        timeout_s: float = 300.0,
    ) -> OracleResult:
        self.context.probed.append(program)
        return self.context.outputs.get(program.label, self.context.output)


@dataclass
class Rigged(GateContext):
    """A gate context whose checker and oracle answer from a script.

    Answers are keyed by checker slot and by oracle label; anything the script does not
    mention gets the fallback, so a test states only the answers it reasons about.
    """

    #: Checker answers, by the slot `GateContext.check` was called with.
    answers: dict[str, CheckResult] = field(default_factory=dict)
    #: What the checker says about a slot the script does not mention.
    otherwise: CheckResult = field(default_factory=lambda: CheckResult.ok("accepted by script"))
    #: Oracle answers, by candidate label: one answer, or one per time it is asked, the last
    #: one reused.
    rulings: dict[str, OracleResult | tuple[OracleResult, ...]] = field(default_factory=dict)
    #: What the oracle says about a candidate the script does not mention.
    ruling: OracleResult = field(default_factory=lambda: OracleResult.no("rejected by script"))
    #: What running a program in the task's environment printed, by program label.
    outputs: dict[str, OracleResult] = field(default_factory=dict)
    #: What the environment says about a program the script does not mention.
    output: OracleResult = field(
        default_factory=lambda: OracleResult.unavailable("no program answer in the script")
    )
    #: Slots checked, candidates judged, and programs run, in order, for a test
    #: about what the gate put to the checker and the benchmark's own environment.
    checked: list[str] = field(default_factory=list)
    judged: list[str] = field(default_factory=list)
    probed: list[Program] = field(default_factory=list)

    def check(self, source: str, slot: str) -> CheckResult:
        self.checked.append(slot)
        return self.answers.get(slot, self.otherwise)

    def oracle(self) -> Oracle:
        return Ruling(self)


class Scripted(Provider):
    """A model whose reply depends only on which stage is asking.

    A stage's replies are consumed in order and the last is reused. Subclasses set
    `stages`, a phrase of each prompt template, most specific first, so a reworded
    template fails by name rather than taking a wrong branch.
    """

    name = "scripted"
    summary = "replies from a fixed script, one entry per stage"

    #: Phrase to stage name, most specific first.
    stages: tuple[tuple[str, str], ...] = ()

    def __init__(self, script: Mapping[str, Sequence[str | Completion]]) -> None:
        super().__init__()
        self.script = script
        self.asked: list[str] = []
        self.sent: list[list[Message]] = []
        self.systems: list[str] = []
        self.budgets: list[int] = []

    def complete(
        self,
        messages: list[Message],
        *,
        system: str = "",
        max_tokens: int = 4096,
        temperature: float = 0.0,
    ) -> Completion:
        stage = self.stage(messages[-1].content)
        self.asked.append(stage)
        self.sent.append(list(messages))
        self.systems.append(system)
        self.budgets.append(max_tokens)
        replies = self.script[stage]
        reply = replies[min(self.turns(stage), len(replies)) - 1]
        return (
            reply if isinstance(reply, Completion) else Completion(text=reply, model="script")
        )

    def stage(self, prompt: str) -> str:
        """Which stage a prompt came from."""
        for phrase, stage in self.stages:
            if phrase in prompt:
                return stage
        raise AssertionError(f"no scripted stage matches this prompt:\n{prompt[:400]}")

    def turns(self, stage: str) -> int:
        """How many times one stage has asked."""
        return self.asked.count(stage)
