# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Recording what a run asks of its models.

`Recorder` wraps a live provider and writes every exchange to a cassette keyed by the
request digest, so recording is the same code path as a normal run plus a file write.
The cassettes are the record of each request a run sent and the answer it got, beside the
bundle the run wrote and the transcripts its agent sessions left.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar

from ..core.plugin import Availability
from ..util.fsio import write_json
from .base import Completion, Message, Provider, ProviderConfig, request_digest

__all__ = ["Recorder", "cassette_path"]


def cassette_path(cassette_dir: Path, key: str) -> Path:
    """Path of the cassette for one request digest."""
    return Path(cassette_dir) / f"{key[:16]}.json"


class Recorder(Provider):
    """A live provider that writes every exchange to a cassette."""

    name: ClassVar[str] = "recorder"
    summary: ClassVar[str] = "delegates to another provider and records the exchange"

    def __init__(self, inner: Provider, config: ProviderConfig | None = None) -> None:
        super().__init__(config or inner.config)
        self.inner = inner

    def configure(self, config: ProviderConfig) -> None:
        """Apply settings to this recorder and to the provider it wraps."""
        super().configure(config)
        self.inner.configure(config)

    def complete(
        self,
        messages: list[Message],
        *,
        system: str = "",
        max_tokens: int = 4096,
        temperature: float = 0.0,
    ) -> Completion:
        """Delegate, then write the cassette that records this exchange."""
        completion = self.inner.complete(
            messages, system=system, max_tokens=max_tokens, temperature=temperature
        )
        key = request_digest(
            messages,
            system=system,
            model=self.config.model,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        document: dict[str, Any] = {
            "key": key,
            "provider": self.inner.name,
            "request": {
                "system": system,
                "messages": [{"role": str(m.role), "content": m.content} for m in messages],
                "model": self.config.model,
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
            "completion": {
                "text": completion.text,
                "model": completion.model,
                "stop_reason": completion.stop_reason,
                "input_tokens": completion.input_tokens,
                "output_tokens": completion.output_tokens,
            },
        }
        write_json(cassette_path(self.config.cassette_dir, key), document)
        return completion

    def availability(self) -> Availability:
        """Report the wrapped provider's availability."""
        return self.inner.availability()
