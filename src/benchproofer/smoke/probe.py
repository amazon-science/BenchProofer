# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Deciding what this machine can be asked to do.

A case declares its requirements as strings, and this module turns each one into an
`Availability`. The vocabulary is small and uniform:

============================  =================================================
``network``                   the run is allowed to reach the network
``docker``                    a container runtime the docker oracle can drive
``tool:<name>``               an executable on the path, such as ``git``
``module:<name>``             an importable Python module
``backend:<name>``            a registered backend whose checker runs here
``benchmark:<name>``          a registered benchmark adapter that can load here
``oracle:<name>``             a registered correctness oracle that can run here
``provider:<name>``           a registered model provider that is configured
============================  =================================================

Probes are cached per instance, because resolving a backend runs its version check
and half the suite asks about the same three components.
"""

from __future__ import annotations

import shutil
from importlib.util import find_spec
from typing import Any

from ..config import Settings
from ..core.plugin import Availability
from ..core.registry import Registry
from ..errors import PluginError
from ..registries import BACKENDS, BENCHMARKS, ORACLES, PROVIDERS

__all__ = ["KINDS", "Probes"]

#: The prefixes `Probes.resolve` understands, for error messages and documentation.
KINDS: tuple[str, ...] = (
    "network",
    "docker",
    "tool",
    "module",
    "backend",
    "benchmark",
    "oracle",
    "provider",
)

_REGISTRIES: dict[str, Registry[Any]] = {
    "backend": BACKENDS,
    "benchmark": BENCHMARKS,
    "oracle": ORACLES,
    "provider": PROVIDERS,
}


class Probes:
    """Resolve requirement strings against this machine, once each."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._cache: dict[str, Availability] = {}

    def resolve(self, requirement: str) -> Availability:
        """Report whether one requirement is met here."""
        if requirement not in self._cache:
            self._cache[requirement] = self._resolve(requirement)
        return self._cache[requirement]

    def unmet(self, requirements: tuple[str, ...]) -> str:
        """Describe the first unmet requirement, or return an empty string.

        The first is enough: a case that cannot run needs one reason, and probing
        the rest would charge the suite for version checks nobody reads.
        """
        for requirement in requirements:
            availability = self.resolve(requirement)
            if availability:
                continue
            hint = f" ({availability.hint})" if availability.hint else ""
            return f"{requirement}: {availability.detail}{hint}"
        return ""

    def _resolve(self, requirement: str) -> Availability:
        kind, _, name = requirement.partition(":")
        if kind == "network":
            return self._network()
        if kind == "docker":
            return self._component("oracle", "docker")
        if kind == "tool":
            return self._tool(name)
        if kind == "module":
            return self._module(name)
        if kind in _REGISTRIES:
            return self._component(kind, name)
        return Availability.missing(
            f"unknown requirement kind {kind!r}; known kinds are {', '.join(KINDS)}"
        )

    def _network(self) -> Availability:
        if self.settings.offline:
            return Availability.missing(
                "the run is hermetic", hint="run without --offline to include this case"
            )
        return Availability.ok(detail="network access is allowed")

    @staticmethod
    def _tool(name: str) -> Availability:
        located = shutil.which(name) if name else None
        if located is None:
            return Availability.missing(f"{name or 'tool'} is not on PATH")
        return Availability.ok(detail=located)

    @staticmethod
    def _module(name: str) -> Availability:
        try:
            found = find_spec(name) is not None
        except (ImportError, ValueError):
            found = False
        if not found:
            return Availability.missing(
                f"{name} is not importable", hint='pip install -e ".[all]"'
            )
        return Availability.ok(detail=f"{name} is importable")

    def _component(self, kind: str, name: str) -> Availability:
        registry = _REGISTRIES[kind]
        try:
            component = registry.get(name)
        except PluginError as exc:
            return Availability.missing(str(exc))
        availability: Availability = component.availability()
        return availability
