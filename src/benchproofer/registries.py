# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The six plugin registries.

Import these rather than calling `importlib.metadata` directly. Tests and
embedding applications can add a component in-process with
``BACKENDS.register("mine", MyBackend)``, which shadows any entry point of the
same name for the lifetime of the process.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .core.registry import Registry

if TYPE_CHECKING:
    from .backends.base import Backend
    from .benchmarks.base import Benchmark
    from .gates.base import Gate
    from .llm.agentic import AgentSession
    from .llm.base import Provider
    from .oracles.base import Oracle

__all__ = ["BACKENDS", "BENCHMARKS", "GATES", "ORACLES", "PROVIDERS", "SESSIONS"]

BACKENDS: Registry[Backend] = Registry("benchproofer.backends", "backend")
BENCHMARKS: Registry[Benchmark] = Registry("benchproofer.benchmarks", "benchmark")
ORACLES: Registry[Oracle] = Registry("benchproofer.oracles", "oracle")
GATES: Registry[Gate] = Registry("benchproofer.gates", "gate")
PROVIDERS: Registry[Provider] = Registry("benchproofer.providers", "provider")
#: Separate from `PROVIDERS`: a provider continues a conversation, while a session acts
#: (reads files, decides what to read next, reports through a tool), and a run may have
#: one without the other.
SESSIONS: Registry[AgentSession] = Registry("benchproofer.sessions", "session")
