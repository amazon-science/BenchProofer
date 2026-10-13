# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Drafting a bundle's artifacts.

This package writes files; it never decides whether they are any good. That
separation is what makes a run's record independent of the model that produced the
artifacts, and it is why the checker results this package collects are labelled
feedback and kept out of `manifest.json`.

The public surface is `Formalizer`, which turns a `Task` into a `Formalization`.
`prompts` is the template library it sends, exposed because a project with an
unusual benchmark may want to reuse or override them.
"""

from __future__ import annotations

from . import prompts
from .session import Draft, Exchange, Formalization, Formalizer

__all__ = [
    "Draft",
    "Exchange",
    "Formalization",
    "Formalizer",
    "prompts",
]
