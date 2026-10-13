# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The documentation, checked against the tool rather than against a reviewer.

Three properties are cheap to check and expensive to lose. A task row printed in the
documentation has to be a row the tool accepts, a command shown there has to be a
command that exists with the options it is shown with, and a link between documents has
to point at a file that is there. The first two are what a new user runs, and the third
is how they get to it, so a stale example costs them more than a stale paragraph.

Only code is read for the first two: fenced blocks and inline spans. Prose is not a
promise, except where it links.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import pytest
import typer

from benchproofer.cli.main import app
from benchproofer.config import Settings
from benchproofer.pipeline.ingest import ingest

#: Repository root, as seen from this file.
ROOT = Path(__file__).resolve().parents[2]

FENCE = re.compile(r"^```(?P<language>\w*)\n(?P<body>.*?)^```", re.MULTILINE | re.DOTALL)
INLINE = re.compile(r"`(?P<body>[^`\n]+)`")
#: ``benchproofer`` where it starts a command, so that ``conda activate benchproofer``
#: and the entry-point group ``benchproofer.gates`` are not read as invocations.
USAGE = re.compile(
    r"(?:^|[;&|]\s*|\$\s*|\bpython -m )benchproofer[ \t]+(?P<rest>[^\n`]*)", re.MULTILINE
)
#: A word that is an option rather than a value, an arrow, or a negative number.
OPTION = re.compile(r"^--?[A-Za-z]")
#: A markdown link or image, by what it points at. A title after the target is ignored.
LINK = re.compile(r"\[[^\]]*\]\((?P<target>[^)\s]+)")
#: A target that names a protocol rather than a path: http, https, mailto.
SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


def documents() -> list[Path]:
    """Every markdown file that documents Benchproofer to its users."""
    found = [ROOT / "README.md", ROOT / "CONTRIBUTING.md", ROOT / "CHANGELOG.md"]
    for directory in ("docs", "examples"):
        found.extend(sorted((ROOT / directory).rglob("*.md")))
    return [path for path in found if path.is_file()]


def code_of(document: str) -> str:
    """The code in one markdown document: fenced blocks and inline spans."""
    blocks = [match.group("body") for match in FENCE.finditer(document)]
    spans = [match.group("body") for match in INLINE.finditer(FENCE.sub("", document))]
    return "\n".join([*blocks, *spans])


def invocations(document: str) -> list[list[str]]:
    """Every ``benchproofer ...`` command line the document shows, tokenized."""
    found: list[list[str]] = []
    for match in USAGE.finditer(code_of(document)):
        words: list[str] = []
        for word in match.group("rest").split():
            if word.startswith("#"):  # a trailing comment, not an argument
                break
            words.append(word)
        if words:
            found.append(words)
    return found


def rows(document: str) -> list[dict[str, Any]]:
    """Every task row the document shows in a fenced JSON block."""
    found: list[dict[str, Any]] = []
    for match in FENCE.finditer(document):
        body = match.group("body")
        if match.group("language") != "json" or '"task_id"' not in body:
            continue
        try:
            found.append(json.loads(body))
        except json.JSONDecodeError:  # a JSON Lines block: one object per line
            found.extend(json.loads(line) for line in body.splitlines() if line.strip())
    return found


def targets(document: str) -> list[str]:
    """Every path a link in the document's prose points at, without its anchor.

    Code is skipped: a link inside a fenced block is an example of markdown, not a
    promise about this repository.
    """
    found: list[str] = []
    for match in LINK.finditer(FENCE.sub("", document)):
        target = match.group("target").split("#")[0]
        if target and not SCHEME.match(target):
            found.append(target)
    return found


def flags(parameters: Iterable[Any]) -> set[str]:
    """Every spelling of every option in a click parameter list."""
    return {flag for parameter in parameters for flag in parameter.opts}


@pytest.fixture(scope="module")
def application() -> tuple[set[str], dict[str, set[str]]]:
    """The application's own options, and the options each command declares."""
    group = typer.main.get_command(app)
    commands: dict[str, Any] = group.commands  # type: ignore[attr-defined]
    return flags(group.params), {
        name: flags(command.params) for name, command in commands.items()
    }


@pytest.mark.parametrize("path", documents(), ids=lambda path: str(path.relative_to(ROOT)))
def test_every_documented_command_line_exists_as_documented(
    path: Path, application: tuple[set[str], dict[str, set[str]]]
) -> None:
    """A command shown in the documentation runs, and its options are declared."""
    global_options, options = application
    for words in invocations(path.read_text(encoding="utf-8")):
        # An application-level option comes before the command name: -v, --quiet.
        remaining = [word for word in words if word not in global_options]
        if not remaining:
            # Nothing but application-level options, which is a complete command line
            # on its own: `benchproofer --version` names no command by design.
            continue
        command, arguments = remaining[0], remaining[1:]
        assert command in options, f"{path.name}: no such command: benchproofer {command}"
        shown = {word.split("=")[0] for word in arguments if OPTION.match(word)}
        unknown = sorted(shown - options[command])
        assert not unknown, f"{path.name}: benchproofer {command} has no {', '.join(unknown)}"


@pytest.mark.parametrize("path", documents(), ids=lambda path: str(path.relative_to(ROOT)))
def test_every_link_between_documents_points_at_something_that_exists(path: Path) -> None:
    """A moved or missing page is a failure here rather than a 404 for a reader.

    `mkdocs --strict` checks the pages under `docs/`; the files a reader arrives at
    first, and the links from them out of the site, are checked only here.
    """
    for target in targets(path.read_text(encoding="utf-8")):
        assert (path.parent / target).exists(), f"{path.name}: broken link: {target}"


@pytest.mark.parametrize("path", documents(), ids=lambda path: str(path.relative_to(ROOT)))
def test_every_documented_task_row_is_a_task_the_tool_accepts(
    path: Path, settings: Settings, tmp_path: Path
) -> None:
    """A row printed as an example is ingested through the adapter that reads it."""
    documented = rows(path.read_text(encoding="utf-8"))
    if not documented:
        pytest.skip("no task rows in this document")
    source = tmp_path / "documented.jsonl"
    source.write_text("\n".join(json.dumps(row) for row in documented), encoding="utf-8")

    ingestion = ingest("jsonl", settings, extras={"source": str(source)})

    assert ingestion.count == len(documented)
