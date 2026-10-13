# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The model-provider interface.

Providers are used by the stages that write artifacts -- drafting, reviewing, repairing
-- and by nothing else. No gate ever calls a model: a gate reads artifacts and runs
checkers, so the record a run leaves behind does not depend on which model wrote the
artifacts, or on whether a model was involved at all. A review is no exception. It
writes files into the bundle like any other drafting stage, and the gates then re-run
what it wrote.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import ClassVar

from ..core.plugin import Availability
from ..util.digest import digest_json

__all__ = ["Completion", "Message", "Provider", "ProviderConfig", "Role", "request_digest"]


class Role(str, Enum):
    """Who authored a message."""

    USER = "user"
    ASSISTANT = "assistant"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class Message:
    """One turn of a conversation."""

    role: Role
    content: str

    @classmethod
    def user(cls, content: str) -> Message:
        """Build a user turn."""
        return cls(role=Role.USER, content=content)

    @classmethod
    def assistant(cls, content: str) -> Message:
        """Build an assistant turn."""
        return cls(role=Role.ASSISTANT, content=content)


@dataclass(frozen=True, slots=True)
class Completion:
    """One model response."""

    text: str
    model: str = ""
    stop_reason: str = ""
    input_tokens: int = 0
    output_tokens: int = 0


@dataclass(frozen=True, slots=True)
class ProviderConfig:
    """What a provider needs from the run's settings.

    Providers are instantiated by the registry with no arguments, so configuration
    arrives here instead of through ``__init__``. Credentials are not included: a
    provider reads its own environment variable, so a key never passes through a
    settings object that gets written into a report.
    """

    model: str = ""
    cassette_dir: Path = Path("cassettes")
    offline: bool = False
    max_retries: int = 3
    timeout_s: float = 600.0


def request_digest(
    messages: list[Message],
    *,
    system: str,
    model: str,
    max_tokens: int,
    temperature: float,
) -> str:
    """Digest one request, identically for every provider.

    This is the cassette key, so the same request sent to two providers is recorded
    under one key.
    """
    request: dict[str, object] = {
        "system": system,
        "messages": [{"role": str(m.role), "content": m.content} for m in messages],
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    return digest_json(request)


class Provider(ABC):
    """Base class for model providers."""

    #: Registry name, matching the entry point.
    name: ClassVar[str]
    #: One-line description shown by ``benchproofer doctor``.
    summary: ClassVar[str] = ""
    #: True when the same request always yields the same response, as for a provider
    #: that refuses every request. Reproducibility claims in reports read this.
    deterministic: ClassVar[bool] = False

    def __init__(self, config: ProviderConfig | None = None) -> None:
        self.config = config or ProviderConfig()

    def configure(self, config: ProviderConfig) -> None:
        """Apply the run's settings. Called once before the first request."""
        self.config = config

    @abstractmethod
    def complete(
        self,
        messages: list[Message],
        *,
        system: str = "",
        max_tokens: int = 4096,
        temperature: float = 0.0,
    ) -> Completion:
        """Continue a conversation.

        Raises:
            ProviderError: The request could not be completed.
        """

    def availability(self) -> Availability:
        """Report whether this provider is configured and reachable."""
        return Availability.ok()

    def __repr__(self) -> str:
        return f"<{type(self).__name__} name={self.name!r}>"
