# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Any server that speaks the OpenAI chat-completions protocol.

This covers the OpenAI API and the many servers that reimplement it, including
vLLM, llama.cpp, Ollama, and most hosting providers, so a self-hosted model needs
no new plugin. It is written against `httpx`, which is already a dependency, rather
than against a vendor SDK.

Two environment variables configure it: ``OPENAI_API_KEY`` and, for anything other
than OpenAI itself, ``OPENAI_BASE_URL``.
"""

from __future__ import annotations

import os
import time
from typing import Any, ClassVar

import httpx

from ..core.plugin import Availability
from ..errors import ProviderError
from ..log import logger
from .base import Completion, Message, Provider

__all__ = ["OpenAICompatibleProvider"]

DEFAULT_BASE_URL = "https://api.openai.com/v1"
#: Statuses worth another attempt: rate limiting and transient server faults.
_RETRY_STATUS = frozenset({408, 409, 429, 500, 502, 503, 504})

_log = logger(__name__)


class OpenAICompatibleProvider(Provider):
    """Chat completions over HTTP."""

    name: ClassVar[str] = "openai"
    summary: ClassVar[str] = "any OpenAI-compatible chat-completions endpoint"

    @property
    def base_url(self) -> str:
        """The endpoint root, without a trailing slash."""
        return os.environ.get("OPENAI_BASE_URL", DEFAULT_BASE_URL).rstrip("/")

    def availability(self) -> Availability:
        """Report whether a key is present, unless the endpoint is a local one."""
        if os.environ.get("OPENAI_API_KEY"):
            return Availability.ok(detail=self.base_url)
        if self.base_url != DEFAULT_BASE_URL:
            # Self-hosted servers commonly accept any key, or none at all.
            return Availability.ok(detail=f"{self.base_url} (no key set)")
        return Availability.missing(
            "OPENAI_API_KEY is not set",
            hint="export OPENAI_API_KEY=...  # or set OPENAI_BASE_URL for a local server",
        )

    def complete(
        self,
        messages: list[Message],
        *,
        system: str = "",
        max_tokens: int = 4096,
        temperature: float = 0.0,
    ) -> Completion:
        """Send one chat-completions request.

        Raises:
            ProviderError: The run is offline, the endpoint rejected the request, or
                it kept failing after `ProviderConfig.max_retries` attempts.
        """
        if self.config.offline:
            raise ProviderError("this run is offline, so the openai provider cannot be used")
        if not self.config.model:
            raise ProviderError("the openai provider needs a model id; pass --model")

        payload: dict[str, Any] = {
            "model": self.config.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [
                *([{"role": "system", "content": system}] if system else []),
                *({"role": str(m.role), "content": m.content} for m in messages),
            ],
        }
        document = self._post(payload)

        try:
            choice = document["choices"][0]
            usage = document.get("usage", {})
            return Completion(
                text=str(choice["message"]["content"] or ""),
                model=str(document.get("model", self.config.model)),
                stop_reason=str(choice.get("finish_reason", "")),
                input_tokens=int(usage.get("prompt_tokens", 0)),
                output_tokens=int(usage.get("completion_tokens", 0)),
            )
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise ProviderError(
                f"unexpected response shape from {self.base_url}: {exc}"
            ) from exc

    def _post(self, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.base_url}/chat/completions"
        headers = {"content-type": "application/json"}
        key = os.environ.get("OPENAI_API_KEY")
        if key:
            headers["authorization"] = f"Bearer {key}"

        last = ""
        for attempt in range(1, self.config.max_retries + 1):
            try:
                response = httpx.post(
                    url, json=payload, headers=headers, timeout=self.config.timeout_s
                )
            except httpx.HTTPError as exc:
                last = f"{type(exc).__name__}: {exc}"
            else:
                if response.status_code == httpx.codes.OK:
                    return dict(response.json())
                last = f"HTTP {response.status_code}: {response.text[:500]}"
                if response.status_code not in _RETRY_STATUS:
                    break
            if attempt < self.config.max_retries:
                delay = 2.0**attempt
                _log.info("%s failed (%s); retrying in %.0fs", url, last, delay)
                time.sleep(delay)
        raise ProviderError(f"{url} failed after {self.config.max_retries} attempt(s): {last}")
