# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The oracle's service dependencies: a third party's uptime must not decide a
verdict, and a service we cannot provide must not silently change one either."""
from __future__ import annotations

import importlib
import subprocess

import pytest

from swebench_unified import harness_patches, oracle_services


@pytest.fixture
def svc(monkeypatch, tmp_path):
    """A fresh module with an empty URL cache and its own lock dir."""
    monkeypatch.setenv("SBU_SERVICE_LOCK_DIR", str(tmp_path / "locks"))
    monkeypatch.setenv("SBU_SERVICE_READY_WAIT", "0")
    return importlib.reload(oracle_services)


def _fake_docker(mod, monkeypatch, *, gateway="172.17.0.1", running=True,
                 ready=True, start_ok=True, calls=None):
    def run(*args, timeout=120):
        joined = " ".join(args)
        if calls is not None:
            calls.append(joined)
        if "network inspect" in joined:
            return subprocess.CompletedProcess(args, 0, f"'{gateway}'\n", "")
        if joined.startswith("docker inspect"):
            return subprocess.CompletedProcess(
                args, 0, f"'{str(running).lower()}'\n", "")
        if joined.startswith("docker start") or joined.startswith("docker run"):
            return subprocess.CompletedProcess(
                args, 0 if start_ok else 1, "", "" if start_ok else "boom")
        if joined.startswith("curl"):
            return subprocess.CompletedProcess(
                args, 0, "'200'" if ready else "'000'", "")
        raise AssertionError(f"unexpected docker call: {joined}")
    monkeypatch.setattr(mod, "_docker", run)


def test_a_repo_with_a_service_dependency_is_pointed_at_the_local_one(
        svc, monkeypatch):
    _fake_docker(svc, monkeypatch)
    assert svc.service_env_lines({"repo": "psf/requests"}) == [
        "export HTTPBIN_URL=http://172.17.0.1:18080/"]


def test_a_repo_that_needs_nothing_gets_no_exports(svc, monkeypatch):
    _fake_docker(svc, monkeypatch)
    assert svc.service_env_lines({"repo": "django/django"}) == []
    assert svc.service_env_lines({}) == []


def test_a_service_that_cannot_be_provided_changes_nothing(svc, monkeypatch):
    """The suite keeps its own default rather than being pointed at a dead port.

    Returning a URL we could not verify would be worse than doing nothing: every
    test would fail against a closed port, which is the failure this module
    exists to remove, now caused by the fix instead of the outage.
    """
    _fake_docker(svc, monkeypatch, ready=False)
    assert svc.service_url("httpbin") is None
    assert svc.service_env_lines({"repo": "psf/requests"}) == []


def test_a_container_that_will_not_start_is_not_reported_as_a_service(
        svc, monkeypatch):
    _fake_docker(svc, monkeypatch, running=False, start_ok=False)
    assert svc.service_url("httpbin") is None


def test_a_stopped_container_is_started_before_it_is_declared_dead(
        svc, monkeypatch):
    calls: list[str] = []
    _fake_docker(svc, monkeypatch, running=False, calls=calls)
    assert svc.service_url("httpbin") == "http://172.17.0.1:18080/"
    assert any(c.startswith("docker start") for c in calls)


def test_the_url_is_resolved_once_per_process(svc, monkeypatch):
    """Every eval script build would otherwise pay a docker round-trip, under
    the resolve fan-out, for an answer that cannot change."""
    calls: list[str] = []
    _fake_docker(svc, monkeypatch, calls=calls)
    svc.service_url("httpbin")
    n = len(calls)
    svc.service_url("httpbin")
    assert len(calls) == n


def test_an_unknown_service_is_not_invented(svc, monkeypatch):
    _fake_docker(svc, monkeypatch)
    assert svc.service_url("no-such-service") is None


def test_the_gateway_is_used_not_localhost(svc, monkeypatch):
    """`localhost` inside the graded container means the container, not the host
    the sidecar published to."""
    _fake_docker(svc, monkeypatch, gateway="10.9.8.1")
    assert svc.service_url("httpbin") == "http://10.9.8.1:18080/"


def test_no_gateway_means_no_service(svc, monkeypatch):
    _fake_docker(svc, monkeypatch, gateway="")
    assert svc.service_url("httpbin") is None


# ---- what the local service cannot grade is dropped, and only that ----

def _row(**kw):
    row = {"instance_id": "psf__requests-1921", "repo": "psf/requests",
           "FAIL_TO_PASS": '["f1"]',
           "PASS_TO_PASS": '["test_requests.py::RequestsTestCase::'
                           'test_mixed_case_scheme_acceptable", "keep_me"]'}
    row.update(kw)
    return row


def test_the_assertion_a_single_port_service_cannot_answer_is_excluded():
    out = harness_patches._apply_dataset_corrections([_row()])[0]
    assert out["PASS_TO_PASS"] == '["keep_me"]'
    assert out["FAIL_TO_PASS"] == '["f1"]'


def test_the_exclusion_is_repo_wide_not_one_instance():
    """The assertion belongs to the suite, so every version of the repo in the
    dataset carries it."""
    out = harness_patches._apply_dataset_corrections(
        [_row(instance_id="psf__requests-9999")])[0]
    assert out["PASS_TO_PASS"] == '["keep_me"]'


def test_another_repo_keeps_every_test():
    row = {"instance_id": "django__django-1", "repo": "django/django",
           "FAIL_TO_PASS": '["f"]', "PASS_TO_PASS": '["a", "b"]'}
    out = harness_patches._apply_dataset_corrections([row])[0]
    assert out["PASS_TO_PASS"] == '["a", "b"]'


def test_a_repo_fix_and_an_instance_fix_both_apply(monkeypatch):
    """One must not shadow the other: an instance-keyed fix replacing a
    repo-keyed one for the same field would silently re-admit a test the suite
    cannot grade."""
    monkeypatch.setitem(harness_patches.DATASET_CORRECTIONS,
                        "psf__requests-1921",
                        {"PASS_TO_PASS": lambda p2p: [t for t in p2p
                                                      if t != "keep_me"]})
    out = harness_patches._apply_dataset_corrections([_row()])[0]
    assert out["PASS_TO_PASS"] == "[]"


def test_the_eval_script_carries_the_service_export(monkeypatch):
    """The export has to reach the script that runs the suite, or the suite
    keeps talking to the public host."""
    monkeypatch.setattr(harness_patches, "service_env_lines",
                        lambda inst: ["export HTTPBIN_URL=http://gw:1/"])
    monkeypatch.setattr(harness_patches, "get_modified_files", lambda p: [])
    monkeypatch.setattr(harness_patches, "get_new_files", lambda p: [])
    monkeypatch.setattr(harness_patches, "get_test_directives", lambda i: ["t.py"])
    monkeypatch.setattr(harness_patches, "MAP_REPO_VERSION_TO_SPECS",
                        {"psf/requests": {"1.0": {"test_cmd": "pytest"}}})
    cmds = harness_patches.make_eval_script_list_py(
        {"instance_id": "psf__requests-1921", "repo": "psf/requests",
         "version": "1.0"},
        {}, "envname", "/testbed", "deadbeef", "")
    assert "export HTTPBIN_URL=http://gw:1/" in cmds
    # Before the suite runs, or it is set too late to matter.
    assert cmds.index("export HTTPBIN_URL=http://gw:1/") < cmds.index("pytest t.py")
