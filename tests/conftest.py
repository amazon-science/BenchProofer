# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Shared fixtures.

Every test is hermetic: no network, no container runtime, no model provider, and no
dependence on the machine's configuration. The settings fixture is built in a temporary
directory with ``offline=True``, ``BENCHPROOFER_*`` variables are removed, and the
variables that force colored output are dropped at startup. Cases that need the network
or Docker live in the smoke suite (docs/reproducibility.md).
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from benchproofer.config import Settings
from benchproofer.core.bundle import Bundle
from benchproofer.core.task import Task
from benchproofer.smoke import fixtures


@pytest.fixture(autouse=True)
def _insulated_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Hide the developer's own configuration from the tool under test."""
    for name in [key for key in os.environ if key.startswith("BENCHPROOFER_")]:
        monkeypatch.delenv(name, raising=False)


def pytest_configure(config: pytest.Config) -> None:
    """Drop the variables that force colored output, before anything builds a console.

    The CLI makes its Rich consoles on import, so a fixture is too late, and escape codes
    would split the text a test looks for.
    """
    for name in ("FORCE_COLOR", "CLICOLOR_FORCE", "TTY_COMPATIBLE"):
        os.environ.pop(name, None)


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    """Settings pointing at a fresh bundle root and cache, with no network and no session.

    A session spawns the Claude Code tool and reaches a model, so the stages that use one
    are tested against a double.
    """
    return Settings(
        bundle_root=tmp_path / "bundles",
        cache_dir=tmp_path / "cache",
        cassette_dir=tmp_path / "cassettes",
        offline=True,
        provider="null",
        session="",
    )


@pytest.fixture
def tasks(settings: Settings) -> dict[str, Task]:
    """The packaged fixture tasks, ingested through the jsonl adapter."""
    return fixtures.tasks(settings)


@pytest.fixture
def coin_change(tasks: dict[str, Task]) -> Task:
    """The repair task the fixture bundles formalize."""
    return tasks["coin-change"]


@pytest.fixture
def running_total(tasks: dict[str, Task]) -> Task:
    """The from-scratch task, whose reference ships whole files rather than a patch."""
    return tasks["running-total"]


@pytest.fixture
def solution() -> str:
    """The sound fixture's solution file, as text."""
    return (fixtures.fixture("coin-change-sound").directory / "solution.py").read_text()


@pytest.fixture
def sound(coin_change: Task, settings: Settings) -> Bundle:
    """The sound fixture, staged as a writable bundle with the frozen task beside it.

    No fixture ships a review, so a gate that reads one starts only from evidence the
    test chose to write.
    """
    return fixtures.stage(fixtures.fixture("coin-change-sound"), coin_change, settings)


@pytest.fixture
def leaky(running_total: Task, settings: Settings) -> Bundle:
    """The fixture whose specification restates the benchmark's own solution."""
    return fixtures.stage(fixtures.fixture("running-total-leaky"), running_total, settings)
