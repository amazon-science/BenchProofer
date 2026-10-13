# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The ``benchproofer`` command-line interface.

Each command is one function in its own module, mapping to one pipeline stage. This
module only wires them together and turns exceptions into exit codes:

==== ==========================================================================
code meaning
==== ==========================================================================
0    the command did what it was asked
1    the tool could not do its job: bad settings, missing plugin, broken bundle
2    the command line was wrong (typer's own convention)
3    the tool worked, and the result did not meet the bar --strict set
==== ==========================================================================

Code 3 exists so that continuous integration can distinguish "benchproofer broke"
from "benchproofer worked and the specifications did not hold up".
"""

from __future__ import annotations

from typing import Annotated

import typer

from .. import __version__
from ..errors import BenchproofError
from ..log import configure
from .audit import audit
from .catalog import catalog
from .check import check
from .display import problem
from .doctor import doctor
from .formalize import formalize
from .ingest import ingest
from .repair import repair
from .report import report
from .run import run
from .smoke import smoke

__all__ = ["app", "main"]

app = typer.Typer(
    name="benchproofer",
    help=(
        "Turn a benchmark into a formally verified one, and judge the result "
        "mechanically. Start with 'benchproofer doctor'."
    ),
    no_args_is_help=True,
    add_completion=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)

Verbose = Annotated[
    int,
    typer.Option("--verbose", "-v", count=True, help="Show progress; repeat for debug."),
]
Quiet = Annotated[bool, typer.Option("--quiet", "-q", help="Show errors only.")]


def _version(value: bool) -> bool:
    """Print the version while the command line is still being parsed.

    Handled during parsing rather than in the callback below, because
    ``benchproofer --version`` names no command and a command group given no command
    is a usage error.
    """
    if value:
        typer.echo(__version__)
        raise typer.Exit
    return value


Version = Annotated[
    bool,
    typer.Option(
        "--version",
        help="Print the version and exit.",
        is_eager=True,
        callback=_version,
    ),
]

for command in (catalog, doctor, ingest, formalize, audit, repair, check, run, report, smoke):
    app.command()(command)


@app.callback()
def entry(verbose: Verbose = 0, quiet: Quiet = False, version: Version = False) -> None:
    """Configure output before any command runs.

    ``version`` is declared so that ``--version`` is documented and parsed here; it
    is acted on by `_version` during parsing, so this function never sees it set.
    """
    configure(verbose, quiet=quiet)


def main() -> None:
    """Console-script entry point.

    Errors this package raises deliberately are reported as one line, because they
    describe a situation the user can fix. Anything else keeps its traceback, because
    it is a defect in the tool and the traceback is the bug report.
    """
    try:
        app()
    except BenchproofError as exc:
        problem(f"{type(exc).__name__}: {exc}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
