# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Prompt templates, shipped as package data.

Prompts live in ``<package>/templates/*.md`` so they can be read, reviewed, and diffed
like the rest of the tool, and each stage that talks to a model binds a `Library` to its
own package. Substitution uses ``$name`` placeholders and is strict: a field the caller
did not supply raises rather than leaving a hole in the prompt.

A template includes a rules file by naming ``$<name>_rules``: `Library.render` fills it with
the template ``<name>-rules``, the library's own where it has one and otherwise the one in
``core/templates``, which every library shares (`SHARED`). So a rule the drafter, the repair
and the auditors all need is written in one file and included wherever it is stated. A
rules file with fields of its own is rendered by the caller, which passes the text as
``<name>_rules``.
"""

from __future__ import annotations

import re
from functools import cache
from importlib.resources import files
from string import Template

from ..errors import BenchproofError

__all__ = ["RULES", "SHARED", "Library"]

_DIRECTORY = "templates"
_SUFFIX = ".md"
#: The suffix of a template holding rules other templates include.
RULES = "-rules"
#: A placeholder naming a rules file to include.
_INCLUDE = re.compile(r"\$\{?(\w+)_rules\b")


class Library:
    """The templates packaged under one package's ``templates`` directory."""

    def __init__(self, package: str) -> None:
        self.package = package

    def template(self, name: str) -> str:
        """Read one template by name, without its ``.md`` suffix.

        Raises:
            BenchproofError: No such template ships with this package.
        """
        text = _read(self.package, name)
        if text is None:
            raise BenchproofError(
                f"no prompt template named {name!r} in {self.package}; "
                f"have {', '.join(self.names())}"
            )
        return text

    def names(self) -> list[str]:
        """Every template in this library, sorted."""
        directory = files(self.package) / _DIRECTORY
        if not directory.is_dir():
            return []
        return sorted(
            entry.name.removesuffix(_SUFFIX)
            for entry in directory.iterdir()
            if entry.name.endswith(_SUFFIX)
        )

    def render(self, name: str, **fields: str) -> str:
        """Render one template, with the rules files it names filled in (`rules`).

        Raises:
            BenchproofError: The template names a field that was not supplied, or a rules
                file that neither this library nor the shared one ships.
        """
        text = self.template(name)
        for included in _INCLUDE.findall(text):
            if f"{included}_rules" not in fields:
                fields[f"{included}_rules"] = self.rules(included)
        try:
            return Template(text).substitute(fields).strip() + "\n"
        except KeyError as exc:
            raise BenchproofError(f"prompt {name!r} needs a value for {exc}") from exc

    def rules(self, name: str) -> str:
        """The rules file ``<name>-rules``: this library's own, or else the shared one.

        Rendered, so the rules files it includes are filled in too.

        Raises:
            BenchproofError: Neither library ships it.
        """
        owner = self if _read(self.package, name + RULES) is not None else SHARED
        return owner.render(name + RULES).rstrip()


#: The rules every library shares, under ``core/templates``.
SHARED = Library(__package__ or "benchproofer.core")


@cache
def _read(package: str, name: str) -> str | None:
    """One template's text, or None when it does not ship."""
    resource = files(package) / _DIRECTORY / f"{name}{_SUFFIX}"
    return resource.read_text(encoding="utf-8") if resource.is_file() else None
