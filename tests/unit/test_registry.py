# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Plugin discovery.

The built-in components are registered through the same entry-point groups a
third-party package uses, so these tests double as a check that the packaging
metadata of this project is intact.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from benchproofer.core.registry import Registry
from benchproofer.errors import PluginError
from benchproofer.registries import BACKENDS, BENCHMARKS, GATES, ORACLES, PROVIDERS

#: What an installation is expected to expose. A component may be added without
#: touching this list; one may not silently disappear.
EXPECTED = {
    "backends": (
        BACKENDS,
        {"crosshair", "dafny", "falsifier", "lean4", "nagini", "smt", "velvet"},
    ),
    "benchmarks": (
        BENCHMARKS,
        {
            "bigcodebench",
            "gsm8k",
            "humaneval",
            "jsonl",
            "mbpp",
            "quixbugs",
            "swebench-lite",
            "swebench-pro",
            "swebench-verified",
        },
    ),
    "oracles": (ORACLES, {"answer", "docker", "inline-tests", "none", "pytest"}),
    "providers": (PROVIDERS, {"anthropic", "null", "openai"}),
}


@pytest.fixture
def sandbox() -> Iterator[Registry[object]]:
    """A registry over an entry-point group nothing publishes."""
    yield Registry("benchproofer.tests.nothing", "widget")


@pytest.mark.parametrize("kind", sorted(EXPECTED))
def test_the_declared_components_are_all_discoverable(kind: str) -> None:
    registry, expected = EXPECTED[kind]

    assert expected <= set(registry.names())


@pytest.mark.parametrize("kind", sorted(EXPECTED))
def test_every_declared_component_imports_and_reports_its_own_name(kind: str) -> None:
    registry, expected = EXPECTED[kind]

    for name in sorted(expected):
        assert registry.get(name).name == name  # type: ignore[attr-defined]


def test_every_gate_answers_to_its_id_and_states_its_rationale() -> None:
    loaded = GATES.load_all(skip_broken=False)

    assert len(loaded) >= 10
    for gate_id, gate in loaded.items():
        assert gate.id == gate_id
        assert gate.rationale.strip()


def test_an_unknown_name_lists_what_is_available(sandbox: Registry[object]) -> None:
    sandbox.register("widget", object)

    with pytest.raises(PluginError, match="unknown widget 'other'; available: widget"):
        sandbox.get("other")


def test_an_in_process_registration_shadows_an_entry_point() -> None:
    class Stub:
        name = "falsifier"

    try:
        BACKENDS.register("falsifier", Stub)
        assert isinstance(BACKENDS.get("falsifier"), Stub)
    finally:
        BACKENDS.unregister("falsifier")

    assert not isinstance(BACKENDS.get("falsifier"), Stub)


def test_a_component_that_fails_to_import_is_reported_not_hidden(
    sandbox: Registry[object],
) -> None:
    def explode() -> object:
        raise RuntimeError("this component is broken")

    sandbox.register("broken", explode)

    with pytest.raises(RuntimeError, match="broken"):
        sandbox.get("broken")


def test_an_entry_point_that_cannot_be_imported_names_the_plugin(
    sandbox: Registry[object], monkeypatch: pytest.MonkeyPatch
) -> None:
    """A plugin whose module is broken must not read as a plugin nobody installed.

    The two are fixed differently -- one is a defect to report to whoever wrote it, the
    other an install away -- so the message says which happened, and to what.
    """

    class Broken:
        name = "widget"

        @staticmethod
        def load() -> object:
            raise ImportError("no module named 'widget_internals'")

    monkeypatch.setattr(
        "benchproofer.core.registry.entry_points", lambda group: [Broken()] if group else []
    )

    with pytest.raises(PluginError, match="widget 'widget' failed to load: no module named"):
        sandbox.get("widget")


def test_loading_everything_tolerates_a_broken_component_only_when_asked(
    sandbox: Registry[object],
) -> None:
    sandbox.register("fine", object)
    sandbox.register("broken", lambda: None)

    assert set(sandbox.load_all()) == {"fine"}
    with pytest.raises(PluginError, match="resolved to None"):
        sandbox.load_all(skip_broken=False)


def test_resolution_is_cached_until_the_name_is_registered_again(
    sandbox: Registry[object],
) -> None:
    sandbox.register("widget", object)
    first = sandbox.get("widget")

    assert sandbox.get("widget") is first
    sandbox.register("widget", object)
    assert sandbox.get("widget") is not first
