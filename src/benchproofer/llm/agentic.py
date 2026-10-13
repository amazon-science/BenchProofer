# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Running a model that can act, rather than one that can only answer.

A `base.Provider` answers one request, so whatever a stage needs has to be in the
prompt. That is the wrong shape for a stage whose inputs depend on what it finds: which
callee an obligation needs a fact about depends on the obligation the checker could not
discharge, and which step a proof is short of depends on the goal the checker prints. A
session is a model with tools and turns of its own: it reads and searches the directory
it is given, runs or edits what its request allows, and reports a structured answer
through a tool, so the caller parses no prose.

Two things are deliberately not offered. There is no fallback to a single request for a
session that cannot run: a stage that needs to look things up cannot be approximated by one
that cannot, so the session says so and the stage records that it did not happen, and a run
with no session at all drafts nothing. And there is no cassette: a cassette keys on the
text of a request, and a session's conversation depends on what the filesystem said at the
time, so what a session was asked is recorded (`record_dir`) and its transcript is the
tool's own. An offline run refuses a session that reaches a model; the offline suite runs
its sessions on one that reaches none (`remote`), which writes a fixture's files and
reports (`benchproofer.smoke.scripted.ScriptedSession`).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, ClassVar

from ..core.plugin import Availability

__all__ = [
    "EDIT",
    "READ_ONLY",
    "AgentSession",
    "SessionSpec",
    "StepOutcome",
]

#: Tools that read files and nothing else, the default: for a stage whose result is the
#: payload it submits, which the caller validates like anything else it builds. A session
#: has the built-in tools its set names and no others. No set holds a web tool, since a
#: session's work has to come from the task, the bundle and the repository, and a search of
#: the web can find the golden patch or another tool's formalization of the same instance.
READ_ONLY: tuple[str, ...] = ("Read", "Grep", "Glob")
#: Every tool a session needs to read a bundle and a repository, run the checker and the
#: gates, and edit the file it is repairing: what verified-swebench gives its repair
#: agents. What such a session writes is not taken on trust; the caller reads back only
#: the files it asked for and judges them with the same gates as anything else.
EDIT: tuple[str, ...] = (*READ_ONLY, "Bash", "Write", "Edit", "TodoWrite")


@dataclass(frozen=True, slots=True)
class StepOutcome:
    """What one session run produced.

    `payload` is the structured answer, or None when the session never submitted one,
    which is not an error: a session that could not start raises instead.

    `actions` is what it looked at, one short line per tool use, so a reader can check
    that a claim about code was made after reading that code.
    """

    text: str
    payload: dict[str, Any] | None = None
    duration_s: float = 0.0
    turns: int = 0
    tool_uses: int = 0
    detail: str = ""
    actions: tuple[str, ...] = ()

    @property
    def submitted(self) -> bool:
        """True when the session reported a structured answer."""
        return self.payload is not None

    def record(self, reported: Sequence[str]) -> dict[str, Any]:
        """What manifest.json keeps of this run: its ``reported`` fields, and what it spent."""
        payload = self.payload or {}
        return {
            **{key: payload[key] for key in reported if key in payload},
            "turns": self.turns,
            "tool_uses": self.tool_uses,
            "duration_s": round(self.duration_s, 1),
            "detail": self.detail,
            "actions": list(self.actions),
        }


@dataclass(frozen=True, slots=True)
class SessionSpec:
    """One request for a session, and the budget it gets.

    `cwd` is the directory the session works in: the task's working copy, or a workspace
    laid out for it with the bundle and a copy of the repository.
    """

    system: str
    prompt: str
    cwd: Path
    #: What the submitted payload is called, for the tool the session reports through.
    submit: str
    #: JSON-schema properties of that payload, and which of them are required.
    fields: dict[str, Any] = field(default_factory=dict)
    required: tuple[str, ...] = ()
    #: The built-in tools the session has, and the only ones.
    tools: tuple[str, ...] = READ_ONLY
    max_turns: int = 40
    timeout_s: float = 900.0
    #: The files the session may write with its file tools, and the directories under which
    #: it may write any, besides its scratch directory and its temporary directory, which
    #: every session may write. Its shell is limited only by what it may read and by what
    #: the caller reads back.
    writable: tuple[Path, ...] = ()
    #: What a session that stopped without submitting is asked, in one further turn of the
    #: same conversation, so that work it did is not lost for want of a report. Empty asks
    #: nothing, which is right for a stage that reads the files a session left regardless.
    report: str = ""


class AgentSession(ABC):
    """Base class for a model that can use tools."""

    #: Registry name.
    name: ClassVar[str]
    #: One-line description shown by ``benchproofer doctor``.
    summary: ClassVar[str] = ""
    #: Whether a run of it reaches a model over the network, which an offline run refuses.
    remote: ClassVar[bool] = True

    def __init__(self, model: str = "") -> None:
        self.model = model
        #: Where each request this session is given is written, or None to keep none
        #: (`Settings.record`).
        self.record_dir: Path | None = None
        #: What a session may read besides its own workspace, its Claude Code project
        #: directory and the system directories: the toolchains its checkers use
        #: (`resolve.toolchains`).
        self.readable: tuple[Path, ...] = ()
        #: How long one shell command of a session may run, in seconds, or None for as long
        #: as the session itself (`Settings.oracle_timeout_s`, as `session_for` sets it).
        self.command_timeout_s: float | None = None

    def availability(self) -> Availability:
        """Report whether a session can run here."""
        return Availability.ok()

    @abstractmethod
    def run(self, spec: SessionSpec) -> StepOutcome:
        """Run one session to completion, or until its budget runs out.

        Raises:
            ProviderError: The session could not be started at all. A session that
                started and answered nothing is a `StepOutcome` with no payload, which
                is a different thing and not an error.
        """

    def __repr__(self) -> str:
        return f"<{type(self).__name__} name={self.name!r}>"
