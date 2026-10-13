# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The evaluation container's CPU quota (harness_patches PATCH 6).

Two properties, and the second is the one that makes the patch admissible at
all. A quota BOUNDS the container, so one suite cannot take the host and turn
every other verifier's wall clock into a timeout. And a quota does not change
what the suite DECIDES: it is cgroup bandwidth, not affinity, so the visible CPU
count is untouched and a thread pool sized from that count is the same size --
same number of threads, same order of floating-point reductions. A cpuset would
fail that second property, which is why this must never quietly become one.
"""
from __future__ import annotations

import pytest

from swebench_unified import harness_patches as hp


class _Container:
    def __init__(self, *, fail: bool = False) -> None:
        self.updates: list[dict] = []
        self.fail = fail

    def update(self, **kwargs):
        if self.fail:
            raise RuntimeError("cgroup bandwidth control unavailable")
        self.updates.append(kwargs)


@pytest.fixture
def built(monkeypatch):
    """`build_container` with upstream's call stubbed out."""
    made: list[_Container] = []

    def install(container):
        monkeypatch.setattr(hp, "_orig_build_container",
                            lambda *a, **k: container)
        made.append(container)
        return container
    return install


# ---- the quota is chosen and applied ----

def test_the_created_container_is_given_the_quota(built, monkeypatch):
    monkeypatch.setenv("SBU_RESOLVE_CPUS", "6")
    ct = built(_Container())
    assert hp.build_container("spec", "client", "run", "log", False) is ct
    assert ct.updates == [{"cpu_period": hp.CPU_PERIOD,
                           "cpu_quota": 6 * hp.CPU_PERIOD}]


def test_the_default_is_a_quarter_of_the_host(monkeypatch):
    monkeypatch.delenv("SBU_RESOLVE_CPUS", raising=False)
    monkeypatch.setattr(hp.os, "cpu_count", lambda: 96)
    assert hp.resolve_cpu_quota() == 24 * hp.CPU_PERIOD


def test_a_small_host_is_left_alone(monkeypatch):
    """A quota at or above the core count is not a limit, so the 8-core floor
    leaves any host at or below it effectively uncapped."""
    monkeypatch.delenv("SBU_RESOLVE_CPUS", raising=False)
    monkeypatch.setattr(hp.os, "cpu_count", lambda: 4)
    assert hp.resolve_cpu_quota() == 8 * hp.CPU_PERIOD


@pytest.mark.parametrize("raw", ["0", "0.0", "-1"])
def test_the_cap_can_be_turned_off(built, monkeypatch, raw):
    monkeypatch.setenv("SBU_RESOLVE_CPUS", raw)
    ct = built(_Container())
    hp.build_container("spec", "client", "run", "log", False)
    assert ct.updates == [], "asked for no cap, so upstream's behavior verbatim"


# ---- failing to cap must never fail the evaluation ----

def test_a_host_without_bandwidth_control_still_evaluates(built, monkeypatch):
    """Running unbounded is upstream's behavior; refusing to run is not, and a
    resolve that dies here would be recorded as a gate error."""
    monkeypatch.setenv("SBU_RESOLVE_CPUS", "6")
    ct = built(_Container(fail=True))
    assert hp.build_container("spec", "client", "run", "log", False) is ct


def test_a_build_that_returns_nothing_is_passed_through(built, monkeypatch):
    monkeypatch.setenv("SBU_RESOLVE_CPUS", "6")
    monkeypatch.setattr(hp, "_orig_build_container", lambda *a, **k: None)
    assert hp.build_container("spec", "client", "run", "log", False) is None


# ---- the patch reaches both places the symbol is bound ----

def test_the_patch_is_installed_at_the_source_and_in_run_evaluation():
    """`run_evaluation` binds the name at import, and our wrapper re-executes a
    fresh copy of it through runpy, so both bindings have to be replaced."""
    import swebench.harness.docker_build as db
    import swebench.harness.run_evaluation as rev
    assert db.build_container is hp.build_container
    assert rev.build_container is hp.build_container


def test_the_quota_is_bandwidth_and_never_a_cpuset(built, monkeypatch):
    """The semantic-safety property. `cpuset_cpus` would shrink the visible CPU
    set, resize every thread pool sized from it, and change the order of
    floating-point reductions -- a different answer, not a slower one."""
    monkeypatch.setenv("SBU_RESOLVE_CPUS", "6")
    ct = built(_Container())
    hp.build_container("spec", "client", "run", "log", False)
    assert set(ct.updates[0]) == {"cpu_period", "cpu_quota"}
