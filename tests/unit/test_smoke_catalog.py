# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The smoke catalog's own invariants.

The smoke suite is how an installation is checked, so a defect in the catalog is a
defect in the evidence: a case that cannot be named cannot be run, and a case that
declares a requirement nobody probes would be skipped forever without saying why.
"""

from __future__ import annotations

import pytest

from benchproofer.errors import BenchproofError
from benchproofer.registries import BACKENDS, BENCHMARKS, ORACLES, PROVIDERS
from benchproofer.smoke.model import Case
from benchproofer.smoke.probe import KINDS
from benchproofer.smoke.suites import GROUPS, SUITES, cases, select

REGISTRIES = {
    "backend": BACKENDS,
    "benchmark": BENCHMARKS,
    "oracle": ORACLES,
    "provider": PROVIDERS,
}


def test_the_catalog_is_not_empty_and_covers_every_group() -> None:
    assert len(cases()) >= 20
    assert set(GROUPS) >= {
        "registry",
        "backends",
        "benchmarks",
        "oracles",
        "gates",
        "pipeline",
        "review",
    }


def test_the_hermetic_suite_reaches_the_top_of_the_ladder() -> None:
    """An installation with no API key must still be able to check the audited gates.

    They are the ones a program cannot decide for itself, so they are the easiest to
    leave untested -- and the ones a bundle's certification rests on.
    """
    hermetic = {item.id for item in SUITES["offline"].cases()}

    assert GROUPS["review"], "no case reviews a bundle"
    for item in GROUPS["review"]:
        assert item.id in hermetic, f"{item.id} cannot run without an API key"


def test_a_case_id_starts_with_the_group_it_is_reported_under() -> None:
    for name, group in GROUPS.items():
        for item in group:
            assert item.id.startswith(f"{name}.")
            assert item.group == name


def test_every_case_states_what_it_asks() -> None:
    for item in cases():
        assert item.summary.strip(), f"{item.id} has no summary"
        assert callable(item.procedure)


@pytest.mark.parametrize("item", cases(), ids=lambda item: item.id)
def test_every_requirement_uses_the_probed_vocabulary(item: Case) -> None:
    for requirement in item.requires:
        kind, _, name = requirement.partition(":")
        assert kind in KINDS, f"{requirement}: unknown requirement kind"
        if kind in REGISTRIES:
            assert name in REGISTRIES[kind].names(), f"{requirement}: nothing registered"
        elif kind in ("tool", "module"):
            assert name, f"{requirement}: names nothing"


def test_the_hermetic_suite_excludes_anything_that_reaches_outside_this_machine() -> None:
    for item in SUITES["offline"].cases(include_slow=True):
        assert "network" not in item.requires
        assert "docker" not in item.requires


def test_a_slow_case_is_reachable_through_the_suite_that_describes_it() -> None:
    """Otherwise `--slow` would silently do nothing under the suite a run defaults to.

    A case that takes minutes but reaches outside nothing belongs to the offline suite;
    what it costs is a reason to leave it out of a quick run, not a reason to make the
    only selection that says it could run here unable to name it.
    """
    quick = SUITES["offline"].cases()
    asked = SUITES["offline"].cases(include_slow=True)
    added = set(asked) - set(quick)

    assert not any(item.slow for item in quick)
    assert added, "no slow case is hermetic, so nothing here is pinned"
    assert all(item.slow for item in added)
    assert select("offline", include_slow=True) == asked


def test_the_full_suite_is_the_whole_catalog() -> None:
    assert SUITES["all"].cases() == cases()
    assert set(SUITES["offline"].cases()) < set(cases())


def test_a_suite_a_group_and_a_case_id_can_all_be_selected() -> None:
    assert select("offline") == SUITES["offline"].cases()
    assert select("gates") == GROUPS["gates"]
    assert [item.id for item in select("gates.waiver")] == ["gates.waiver"]
    assert select("  gates  ") == GROUPS["gates"]


def test_a_name_that_matches_nothing_lists_what_does() -> None:
    with pytest.raises(BenchproofError, match="Groups: registry"):
        select("gate")


def test_a_case_is_slow_only_for_a_reason_it_declares() -> None:
    """`--slow` is what a case costs, so what it costs has to be visible.

    Two things earn the flag: reaching upstream for a dataset or an image, and a
    toolchain too large to install for a quick run. The second is `Backend.slow` rather
    than a flag on the case, so the case that skips is the one whose checker said why.
    """
    heavy = {f"backends.{name}" for name, item in BACKENDS.load_all().items() if item.slow}
    slow = {item.id for item in cases() if item.slow}

    assert slow and heavy
    for item in cases():
        if item.slow and item.id not in heavy:
            assert set(item.requires) & {"network", "docker"}, (
                f"{item.id} is slow for no reason"
            )
    assert heavy <= slow
