# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Shared machinery for the drafting stages that ask a model for an artifact.

Each is the same conversation with a different question: ask, take the artifact the reply
should carry, retry once when it cannot be used, and record what was sent under its
cassette key. Keeping that in one place keeps the stages' retry and recording rules, and
so their records, alike. A `Session` renders no prompt beyond the retry; each stage owns
its templates and its idea of a good reply.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from ..config import Settings
from ..errors import BenchproofError, ProviderError
from ..llm.base import Completion, Message, Provider, request_digest
from ..log import logger
from .prompts import Library

__all__ = [
    "BREVITY",
    "DECLINED",
    "TEMPERATURE",
    "TRUNCATED",
    "Exchange",
    "Journal",
    "Session",
    "quoted",
]

log = logger(__name__)

#: Stop reasons that mean a response ran out of room rather than finished. The
#: Anthropic API says `max_tokens`; an OpenAI-compatible endpoint says `length`.
TRUNCATED = frozenset({"max_tokens", "length"})
#: Stop reasons that mean the provider stopped the response itself, leaving nothing or a
#: reply cut off part way.
DECLINED = frozenset({"refusal", "content_filter"})
#: Sampling temperature, for the models that still accept one. Zero, for repeatability;
#: ``--record`` is what guarantees it, since a model may answer differently either way.
TEMPERATURE = 0.0
#: What a retry adds when the reply ran out of room. The prompts already name the shape
#: they want, so a model that filled the budget was not unclear about it, and asking the
#: same way again spends a second budget the same way: this round asks for less.
BREVITY = (
    "You spent the whole budget before finishing your reply, so what this request needs is "
    "a shorter reply, not a different conclusion. Write only the lines the request asked "
    "for, in the order it asked for them, and leave the analysis out: a reply that runs "
    "out of room produces no artifact at all, however sound the reasoning in it was."
)


@dataclass(frozen=True, slots=True)
class Exchange:
    """One request to the model, recorded for the manifest under its cassette `key`."""

    stage: str
    round: int
    key: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0

    def record(self) -> dict[str, Any]:
        """The part of this exchange that belongs in a bundle's `manifest.json`."""
        return {"stage": self.stage, "round": self.round, "key": self.key, "model": self.model}


@dataclass
class Journal:
    """Mutable record of the requests one task needed and what went wrong.

    A note says what the tool did and which gate has the last word on it, never that an
    artifact is fine.
    """

    exchanges: list[Exchange] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def note(self, text: str) -> None:
        """Record something a reviewer needs to know about how this run went."""
        log.info("%s", text)
        self.notes.append(text)


class Session:
    """A provider and a template library, with the turn-taking they need.

    A session holds no per-task state, which lives in the journal the caller passes in, so
    one instance can serve a whole run.
    """

    def __init__(self, *, provider: Provider, settings: Settings, prompts: Library) -> None:
        self.provider = provider
        self.settings = settings
        self.prompts = prompts

    @property
    def budget(self) -> int:
        """Response budget for one request, in tokens (`Settings.max_output_tokens`)."""
        return self.settings.max_output_tokens

    def turn(
        self,
        stage: str,
        prompt: str,
        system: str,
        journal: Journal,
        *,
        take: Callable[[str], str],
    ) -> tuple[str, str] | None:
        """Ask one question and take its artifact, retrying an unusable reply.

        Returns:
            The artifact and the reply it came from, or None when no reply could be used.
            A provider failure is noted and returns None, so what the run produced so far
            is kept and the artifact is reported missing.
        """
        messages = [Message.user(prompt)]
        for round_number in (1, 2):
            try:
                completion = self.ask(stage, round_number, messages, system, journal)
            except ProviderError as exc:
                journal.note(f"{stage}: the provider failed, so this stage was skipped: {exc}")
                return None
            reply = completion.text
            try:
                return take(reply), reply
            except BenchproofError as exc:
                problem = self.unusable(exc, completion)
                journal.note(f"{stage} round {round_number}: {problem}")
                messages = [
                    *messages,
                    *quoted(reply),
                    Message.user(
                        self.prompts.render(
                            "retry",
                            problem=problem,
                            remedy=BREVITY if completion.stop_reason in TRUNCATED else "",
                        )
                    ),
                ]
        return None

    def ask(
        self,
        stage: str,
        round_number: int,
        messages: list[Message],
        system: str,
        journal: Journal,
    ) -> Completion:
        """Send one request and record it.

        Raises:
            ProviderError: The model could not be reached.
        """
        key = request_digest(
            messages,
            system=system,
            model=self.provider.config.model,
            max_tokens=self.budget,
            temperature=TEMPERATURE,
        )
        completion = self.provider.complete(
            messages, system=system, max_tokens=self.budget, temperature=TEMPERATURE
        )
        journal.exchanges.append(
            Exchange(
                stage=stage,
                round=round_number,
                key=key,
                model=completion.model or self.provider.config.model,
                input_tokens=completion.input_tokens,
                output_tokens=completion.output_tokens,
            )
        )
        return completion

    def unusable(self, exc: BenchproofError, completion: Completion) -> str:
        """Why a reply could not be used, including where the response stopped.

        A model can spend the whole budget reasoning and show nothing, and a provider can
        stop a response itself; either is reported by where it stopped rather than as a
        malformed reply.
        """
        if completion.stop_reason in TRUNCATED:
            limit = f"the {self.budget}-token limit (max_output_tokens)"
            return f"{exc}; the reply stopped at {limit}"
        if completion.stop_reason in DECLINED:
            return f"{exc}; the provider stopped the response ({completion.stop_reason})"
        return str(exc)


def quoted(reply: str) -> list[Message]:
    """The model's own turn, when there is one to quote back to it.

    A reply that ran out of room while reasoning can be empty, and not every endpoint
    accepts an empty turn.
    """
    return [Message.assistant(reply)] if reply.strip() else []
