# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The provider that declines every request.

This is the default, so a run that was never given a model says so instead of
quietly producing an artifact from nothing. Every stage that does not need a model,
which is every stage that produces a verdict, works with it selected.
"""

from __future__ import annotations

from typing import ClassVar

from ..errors import ProviderError
from .base import Completion, Message, Provider

__all__ = ["NullProvider"]


class NullProvider(Provider):
    """Refuse every request, naming what to configure instead."""

    name: ClassVar[str] = "null"
    summary: ClassVar[str] = "no model; formalization is unavailable, checking is not"
    deterministic: ClassVar[bool] = True

    def complete(
        self,
        messages: list[Message],
        *,
        system: str = "",
        max_tokens: int = 4096,
        temperature: float = 0.0,
    ) -> Completion:
        """Raise, because no model is configured.

        Raises:
            ProviderError: Always.
        """
        raise ProviderError(
            "no model provider is configured, so nothing can be drafted; select one "
            "with --provider (anthropic, openai) or set provider in "
            "benchproofer.toml"
        )
