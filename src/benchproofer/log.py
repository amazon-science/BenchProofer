# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Logging setup.

The library only calls `logger`. Handlers are installed by `configure`, which only the
CLI calls, so importing benchproofer does not change another program's logging.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from rich.logging import RichHandler

__all__ = ["PROGRESS", "configure", "logger", "progress"]

ROOT = "benchproofer"
#: The logger that says what a judgment is about to run, which a command showing progress
#: turns up to INFO (`cli.check`): a gate can run for many minutes, and a reader who sees
#: nothing for that long cannot tell a long run from a stuck one.
PROGRESS = f"{ROOT}.progress"


def logger(name: str) -> logging.Logger:
    """Return the logger for a module of the package, by its ``__name__``."""
    return logging.getLogger(name)


def progress(message: str, *args: object) -> None:
    """Say on `PROGRESS` what is about to run, after the time of day in UTC."""
    logging.getLogger(PROGRESS).info(
        "%s " + message, datetime.now(timezone.utc).strftime("%H:%M:%S UTC"), *args
    )


def configure(verbosity: int = 0, *, quiet: bool = False) -> None:
    """Install a single Rich handler on the package logger.

    Args:
        verbosity: 0 shows warnings, 1 shows progress, 2 or more shows debug.
        quiet: Suppress everything below an error.
    """
    if quiet:
        level = logging.ERROR
    elif verbosity >= 2:
        level = logging.DEBUG
    elif verbosity == 1:
        level = logging.INFO
    else:
        level = logging.WARNING

    root = logging.getLogger(ROOT)
    root.setLevel(level)
    root.propagate = False
    for handler in list(root.handlers):
        root.removeHandler(handler)
    root.addHandler(
        RichHandler(
            show_time=False,
            show_path=level <= logging.DEBUG,
            rich_tracebacks=True,
            markup=False,
        )
    )
