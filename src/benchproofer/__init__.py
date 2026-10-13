# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Benchproofer: turn a real-world benchmark into a formally verified one.

The public surface is small on purpose. Everything else is reached through the
plugin registries in `benchproofer.registries`.
"""

from __future__ import annotations

from .core.bundle import Bundle, Manifest
from .core.provenance import tool_version
from .core.task import Task
from .core.verdict import Certification, Level, Outcome, Status, Verdict, classify
from .errors import BenchproofError

__version__ = tool_version()

__all__ = [
    "BenchproofError",
    "Bundle",
    "Certification",
    "Level",
    "Manifest",
    "Outcome",
    "Status",
    "Task",
    "Verdict",
    "__version__",
    "classify",
]
