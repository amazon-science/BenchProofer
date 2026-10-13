# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The worked example plugin, against the interfaces it implements.

`examples/plugin` is what someone copies to write their own component, and the guides
under `docs/` quote it line by line. It is a separate distribution, so nothing in a
normal installation imports it and nothing else in this suite would notice the day an
interface it implements changes.

These tests put it on the import path out of the checkout rather than installing it --
no build, no network -- and then run its two components the way a registered one is
run: the metadata is resolved, the adapter's tasks are frozen through `ingest`, and the
gate judges a real bundle and records a verdict.
"""

from __future__ import annotations

import importlib
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from benchproofer.benchmarks.base import Benchmark
from benchproofer.config import Settings
from benchproofer.core import markers
from benchproofer.core.bundle import Bundle
from benchproofer.core.task import Task
from benchproofer.core.verdict import Level, Outcome, Status, Verdict
from benchproofer.gates.base import Gate
from benchproofer.pipeline.adjudicate import STATIC_REQUIRED, adjudicate, certify
from benchproofer.pipeline.ingest import ingest
from benchproofer.registries import BACKENDS, BENCHMARKS, GATES, ORACLES, PROVIDERS
from benchproofer.smoke import fixtures
from benchproofer.util.fsio import load_toml, write_text

PLUGIN = Path(__file__).resolve().parents[2] / "examples" / "plugin"
BENCHMARK = "benchproofer_example.benchmark:MiniBenchmark"
GATE = "benchproofer_example.gate:NoTodoGate"
#: Per entry-point group: the base class a component implements, and the attribute it
#: calls itself by. A registry resolves a name to a component, so a component whose
#: own identifier disagrees with the name it is declared under is unreachable.
KINDS: dict[str, tuple[type, str]] = {
    BENCHMARKS.group: (Benchmark, "name"),
    GATES.group: (Gate, "id"),
}


def declared() -> list[tuple[str, str, str]]:
    """Every entry point the example publishes, as (group, name, target)."""
    groups = load_toml(PLUGIN / "pyproject.toml")["project"]["entry-points"]
    return [
        (group, name, target)
        for group, entries in sorted(groups.items())
        for name, target in sorted(entries.items())
    ]


@pytest.fixture(autouse=True)
def _importable() -> Iterator[None]:
    """Make the example importable without installing it, and leave no trace."""
    source = str(PLUGIN / "src")
    sys.path.insert(0, source)
    try:
        yield
    finally:
        sys.path.remove(source)
        for name in [module for module in sys.modules if module.startswith("benchproofer_")]:
            del sys.modules[name]


def resolve(target: str) -> Any:
    """Import ``module:attribute``, the way an entry point is resolved."""
    module_name, _, attribute = target.partition(":")
    return getattr(importlib.import_module(module_name), attribute)


def test_the_example_publishes_groups_this_tool_actually_reads() -> None:
    """A typo in a group name is invisible: the component simply never appears."""
    groups = {group for group, _, _ in declared()}

    assert groups
    assert groups <= {
        registry.group for registry in (BACKENDS, BENCHMARKS, GATES, ORACLES, PROVIDERS)
    }


@pytest.mark.parametrize(("group", "name", "target"), declared())
def test_every_component_the_example_declares_resolves_and_names_itself(
    group: str, name: str, target: str
) -> None:
    base, attribute = KINDS[group]
    component = resolve(target)

    assert issubclass(component, base)
    identifier = getattr(component, attribute)
    assert identifier == name, f"{target} calls itself {identifier!r}, declared as {name!r}"


def test_the_example_adapter_freezes_tasks_like_a_built_in_one(settings: Settings) -> None:
    """The adapter goes through the registry and the ingest stage, not a direct call."""
    adapter = resolve(BENCHMARK)
    BENCHMARKS.register(adapter.name, adapter)
    try:
        assert BENCHMARKS.get(adapter.name).availability().ok
        ingestion = ingest(adapter.name, settings)
    finally:
        BENCHMARKS.unregister(adapter.name)

    assert [task.task_id for task in ingestion.tasks] == ["clamp", "count-vowels", "last-index"]
    assert all((frozen / "task.json").is_file() for frozen in ingestion.frozen)
    for task in ingestion.tasks:
        # A repair task: something to fix, something to fix it to, and a way to tell.
        assert task.context.files and task.reference is not None
        assert task.oracle.kind in ORACLES.names()


def test_the_example_gate_records_a_verdict_and_cannot_change_certification(
    settings: Settings, tasks: dict[str, Task]
) -> None:
    """A third-party gate is judged alongside the built-in set and adds to `manifest.json`.

    What it must not do is move the outcome. The required set is fixed in
    `pipeline.adjudicate`, so an installed plugin cannot certify a bundle the tool
    would not certify, nor reject one it would.
    """
    target = fixtures.fixture("coin-change-sound")
    bundle = fixtures.stage(target, tasks[target.task_id], settings)
    gate = resolve(GATE)
    assert gate.id not in STATIC_REQUIRED

    verdict = _judge(gate, bundle, settings)

    assert verdict.status is Status.PASS
    assert verdict.judge_digest and verdict.tool_version
    assert gate.id in bundle.manifest().verdicts

    bundle.record([_passed(gate_id) for gate_id in STATIC_REQUIRED])
    assert certify(bundle, Level.STATIC).outcome is Outcome.CERTIFIED


def test_the_example_gate_can_fail(settings: Settings, tasks: dict[str, Task]) -> None:
    """A gate that passes everything is worse than no gate, so provoke this one."""
    target = fixtures.fixture("coin-change-sound")
    bundle = fixtures.stage(target, tasks[target.task_id], settings)
    gate = resolve(GATE)
    backend = BACKENDS.get(target.backend)
    unfinished = markers.replace_region(
        bundle.solution(), backend.comment, "spec", "# TODO: state the postcondition"
    )
    write_text(bundle.solution_path, unfinished)

    verdict = _judge(gate, bundle, settings)

    assert verdict.status is Status.FAIL
    assert "TODO" in verdict.summary


def _judge(gate: type[Gate], bundle: Bundle, settings: Settings) -> Verdict:
    """Run one third-party gate over a bundle, registered as an installation would."""
    GATES.register(gate.id, gate)
    try:
        adjudication = adjudicate(
            bundle,
            backend=BACKENDS.get(bundle.backend_name),
            settings=settings,
            level=Level.STATIC,
            only=(gate.id,),
        )
    finally:
        GATES.unregister(gate.id)
    return adjudication.verdicts[gate.id]


def _passed(gate_id: str) -> Verdict:
    """A favorable verdict for a required gate, so certification has something to read."""
    return Verdict(
        gate=gate_id, status=Status.PASS, summary="recorded by a test", level=Level.STATIC
    )
