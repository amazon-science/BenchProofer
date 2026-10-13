# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Claude models, through the Anthropic API or Amazon Bedrock.

The SDK is an optional dependency: install it with ``pip install -e '.[llm]'``. Which
endpoint is used follows from the model id, so the same command works on a laptop
with an API key and on a cluster with Bedrock credentials.
"""

from __future__ import annotations

import os
from typing import Any, ClassVar

from ..core.plugin import Availability
from ..errors import ProviderError
from ..log import logger
from .base import Completion, Message, Provider

__all__ = ["AnthropicProvider"]

#: Used when no model is given. Overridden with ``--model``.
DEFAULT_MODEL = "claude-opus-5"
#: Model id prefixes that name a Bedrock inference profile rather than an API model.
_BEDROCK_PREFIXES = ("anthropic.", "us.anthropic.", "eu.anthropic.", "apac.anthropic.")
_INSTALL = "pip install -e '.[llm]'"

_log = logger(__name__)


def _refused(exc: Exception, *fields: str) -> bool:
    """True when a request was rejected because it carried one of ``fields``."""
    return getattr(exc, "status_code", None) == 400 and any(name in str(exc) for name in fields)


class AnthropicProvider(Provider):
    """Anthropic's messages API."""

    name: ClassVar[str] = "anthropic"
    summary: ClassVar[str] = "Claude models through the Anthropic API or Amazon Bedrock"

    #: Whether this model accepts a sampling parameter. Some Claude models answer a
    #: request that sets `temperature` with a 400 rather than ignoring it, and which ones
    #: is not something this file can state for long, so the API is asked once and the
    #: answer kept for the rest of the run.
    _sampling: bool = True

    @property
    def model(self) -> str:
        """The model this provider will call."""
        return self.config.model or DEFAULT_MODEL

    @property
    def on_bedrock(self) -> bool:
        """True when the model id names a Bedrock inference profile."""
        return self.model.startswith(_BEDROCK_PREFIXES)

    def availability(self) -> Availability:
        """Report whether the SDK is installed and a credential is present."""
        try:
            import anthropic
        except ImportError:
            return Availability.missing("the anthropic package is not installed", hint=_INSTALL)
        if self.on_bedrock:
            if not (os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION")):
                return Availability.missing(
                    "AWS_REGION is not set, and the model id names a Bedrock profile",
                    hint="export AWS_REGION=us-east-1",
                )
        elif not os.environ.get("ANTHROPIC_API_KEY"):
            return Availability.missing(
                "ANTHROPIC_API_KEY is not set",
                hint="export ANTHROPIC_API_KEY=...  # or use a Bedrock model id",
            )
        return Availability.ok(version=getattr(anthropic, "__version__", None))

    def complete(
        self,
        messages: list[Message],
        *,
        system: str = "",
        max_tokens: int = 4096,
        temperature: float = 0.0,
    ) -> Completion:
        """Send one request and return the text of the response.

        Raises:
            ProviderError: The run is offline, the SDK is absent, or the request
                failed after the client's own retries.
        """
        if self.config.offline:
            raise ProviderError("this run is offline, so the anthropic provider cannot be used")
        request: dict[str, Any] = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": [{"role": str(m.role), "content": m.content} for m in messages],
        }
        # An empty string is a real, empty system prompt to the API, so the field is
        # left out entirely when there is nothing to say.
        if system:
            request["system"] = system
        if self._sampling:
            request["temperature"] = temperature
        response = self._send(request)

        text = "".join(
            block.text for block in response.content if getattr(block, "type", "") == "text"
        )
        return Completion(
            text=text,
            model=str(response.model),
            stop_reason=str(response.stop_reason or ""),
            input_tokens=int(response.usage.input_tokens),
            output_tokens=int(response.usage.output_tokens),
        )

    def _send(self, request: dict[str, Any]) -> Any:
        """Stream one request, retrying without `temperature` if the model refuses it.

        The response is streamed rather than awaited in one piece. Drafting a proof is
        given a large output budget, and a model that spends it takes minutes to
        answer; a request that sends nothing back in the meantime is indistinguishable
        from a stalled connection, so the client abandons it at `timeout_s` and tries
        again, at full length, until the retries are gone. Streaming keeps the answer
        arriving while it is being written, which leaves the timeout meaning what it
        says.

        That retry runs at most once: the next attempt no longer carries the field that
        provoked the refusal.

        Raises:
            ProviderError: The request failed after the client's own retries.
        """
        client = self._client()
        while True:
            try:
                with client.messages.stream(**request) as stream:
                    return stream.get_final_message()
            except Exception as exc:
                if "temperature" in request and _refused(exc, "temperature"):
                    _log.info(
                        "%s does not accept a temperature; sending requests without one",
                        self.model,
                    )
                    self._sampling = False
                    del request["temperature"]
                    continue
                raise ProviderError(
                    f"anthropic request failed: {type(exc).__name__}: {exc}"
                ) from exc

    def _client(self) -> Any:
        try:
            import anthropic
        except ImportError as exc:
            raise ProviderError(f"the anthropic package is not installed; {_INSTALL}") from exc
        if self.on_bedrock:
            region = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION")
            return anthropic.AnthropicBedrock(
                aws_region=region,
                max_retries=self.config.max_retries,
                timeout=self.config.timeout_s,
            )
        return anthropic.Anthropic(
            max_retries=self.config.max_retries, timeout=self.config.timeout_s
        )
