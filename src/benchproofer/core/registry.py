# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Plugin registries.

Every kind of component is discovered through `importlib.metadata` entry points. The
built-in ones are registered in this project's ``pyproject.toml`` under the same groups,
so a third-party package adds a component exactly the way the tool ships one.
"""

from __future__ import annotations

from importlib.metadata import entry_points
from typing import Any, Generic, TypeVar

from ..errors import PluginError

__all__ = ["Registry"]

T = TypeVar("T")


class Registry(Generic[T]):
    """Lazily resolved, cached lookup over one entry-point group."""

    def __init__(self, group: str, kind: str) -> None:
        self.group = group
        self.kind = kind
        self._overrides: dict[str, Any] = {}
        self._cache: dict[str, T] = {}

    # ---- discovery ------------------------------------------------------

    def names(self) -> list[str]:
        """Every registered name, sorted."""
        discovered = {ep.name for ep in entry_points(group=self.group)}
        return sorted(discovered | set(self._overrides))

    def get(self, name: str) -> T:
        """Resolve one component by name, reusing the instance across calls.

        Raises:
            PluginError: The name is unknown or its module failed to import.
        """
        if name in self._cache:
            return self._cache[name]
        instance = self._instantiate(name, self._target(name))
        self._cache[name] = instance
        return instance

    def build(self, name: str) -> T:
        """Resolve one component as a new instance, bypassing the cache.

        For a model provider, which two stages of one run may configure with different
        models.

        Raises:
            PluginError: The name is unknown or its module failed to import.
        """
        return self._instantiate(name, self._target(name))

    def load_all(self, *, skip_broken: bool = True) -> dict[str, T]:
        """Resolve every component, optionally tolerating ones that fail to load."""
        loaded: dict[str, T] = {}
        for name in self.names():
            try:
                loaded[name] = self.get(name)
            except PluginError:
                if not skip_broken:
                    raise
        return loaded

    # ---- programmatic registration --------------------------------------

    def register(self, name: str, target: Any) -> None:
        """Register a component in-process, overriding any entry point."""
        self._overrides[name] = target
        self._cache.pop(name, None)

    def unregister(self, name: str) -> None:
        """Remove an in-process registration."""
        self._overrides.pop(name, None)
        self._cache.pop(name, None)

    def _target(self, name: str) -> Any:
        """The registered object or entry point behind one name.

        Raises:
            PluginError: The name is unknown or its module failed to import.
        """
        target = self._overrides.get(name)
        if target is not None:
            return target
        matches = [ep for ep in entry_points(group=self.group) if ep.name == name]
        if not matches:
            raise PluginError(
                f"unknown {self.kind} {name!r}; available: {', '.join(self.names()) or 'none'}"
            )
        try:
            return matches[0].load()
        except Exception as exc:
            raise PluginError(f"{self.kind} {name!r} failed to load: {exc}") from exc

    def _instantiate(self, name: str, target: Any) -> T:
        obj = target() if isinstance(target, type) or callable(target) else target
        if obj is None:
            raise PluginError(f"{self.kind} {name!r} resolved to None")
        return obj  # type: ignore[no-any-return]
