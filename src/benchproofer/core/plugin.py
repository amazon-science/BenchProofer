# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Shared vocabulary for plugin components."""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["Availability"]


@dataclass(frozen=True, slots=True)
class Availability:
    """Whether a component can run here, and what to do when it cannot.

    `hint` is printed by ``benchproofer doctor``, so it should name the exact
    command that installs the missing piece.
    """

    available: bool
    detail: str = ""
    version: str | None = None
    hint: str = ""

    @classmethod
    def ok(cls, version: str | None = None, detail: str = "") -> Availability:
        """Report a working component."""
        return cls(available=True, version=version, detail=detail)

    @classmethod
    def missing(cls, detail: str, hint: str = "") -> Availability:
        """Report a component that cannot run, with remediation."""
        return cls(available=False, detail=detail, hint=hint)

    def __bool__(self) -> bool:
        return self.available
