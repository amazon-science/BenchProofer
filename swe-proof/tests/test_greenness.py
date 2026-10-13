# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""One definition of "green", and what it refuses to call green.

The predicate decides two things that must not diverge: which cells the release
gate commits, and which cells a repair driver considers done. When it existed twice
-- once in `scripts/green_check.py`, once in `viz/backend/data.py`, each documented
as a mirror of the other -- the disagreement would land on exactly the cells being
repaired, one side spending on work the other had already accepted.

So these tests hold two things: every consumer routes to
`swebench_unified.greenness`, and the STRICT reading (a missing stamp is not green,
a placeholder skip is not a verdict) survives.
"""
from __future__ import annotations

import json

import green_check
import pytest
from swebench_unified.greenness import (GREEN_OK, PANEL_ROLES, REQUIRED_GATES,
                                       failing_gates, failing_reasons, is_green)


def _all_green() -> dict:
    """A gate blob that is fully green, built from the registry rather than a
    literal, so a gate added to the registry appears here too."""
    g: dict = {k: {"status": "pass"} for k in REQUIRED_GATES}
    g["G-CONF"] = {"status": "pass", "data": {}}
    g["G-PBT"] = {"status": "pass", "data": {"cases": 4}}
    for r in PANEL_ROLES:
        g[r] = {"status": "pass"}
    return g


def test_the_baseline_blob_is_green():
    assert is_green(_all_green())
    assert failing_reasons(_all_green()) == []


@pytest.mark.parametrize("status", GREEN_OK)
def test_every_ok_status_counts(status):
    g = _all_green()
    g["G-MUT"] = {"status": status}
    assert is_green(g)


def test_a_missing_stamp_is_not_green():
    """Unrecorded work is not vouched for; the reason names the gate."""
    g = _all_green()
    del g["G-VERIFY"]
    assert not is_green(g)
    assert "G-VERIFY=MISSING" in failing_reasons(g)
    # and it is NOT reported as a gate that said no: nothing said anything
    assert "G-VERIFY" not in failing_gates(g)


def test_a_missing_gate_is_required_for_every_registry_gate():
    for gk in REQUIRED_GATES:
        g = _all_green()
        del g[gk]
        assert not is_green(g), f"{gk} missing still read as green"


@pytest.mark.parametrize("data,reason", [
    ({"docker_oracle_unavailable": True}, "G-CONF=placeholder-skip"),
    ({"conf_missing_script": True}, "G-CONF=placeholder-skip"),
])
def test_a_conf_placeholder_skip_is_not_a_verdict(data, reason):
    g = _all_green()
    g["G-CONF"] = {"status": "skip", "data": data}
    assert not is_green(g)
    assert reason in failing_reasons(g)


@pytest.mark.parametrize("rec,ran", [
    ({"status": "pass"}, True),
    # a FAIL is a real judgment: the driver that authors missing shadows must not
    # overwrite a script the gate has already refuted
    ({"status": "fail"}, True),
    ({"status": "skip", "data": {"conf_skip": True}}, True),
    ({"status": "skip", "data": {"conf_missing_script": True}}, False),
    ({"status": "skip", "data": {"docker_oracle_unavailable": True}}, False),
    ({"status": "skip", "detail": "swe_bench_pro_python does not support G-CONF"},
     False),
    ({}, False),
])
def test_conf_check_ran_asks_only_whether_it_ran(rec, ran):
    from swebench_unified.greenness import conf_check_ran
    g = _all_green()
    g["G-CONF"] = rec
    assert conf_check_ran(g) is ran
    # and green needs BOTH: it ran, and the stamp it left is OK
    assert is_green(g) is (ran and rec.get("status") in GREEN_OK)


def test_the_benchmark_level_conf_skip_is_not_a_verdict():
    g = _all_green()
    g["G-CONF"] = {"status": "skip",
                   "detail": "swe_bench_pro_python does not support G-CONF"}
    assert not is_green(g)


def test_a_pbt_missing_manifest_skip_is_not_a_verdict():
    """No battery constructed is not "the spec survived falsification"."""
    g = _all_green()
    g["G-PBT"] = {"status": "skip", "data": {"pbt_missing_manifest": True}}
    assert not is_green(g)
    assert "G-PBT=missing-manifest" in failing_reasons(g)


def test_a_genuine_pbt_skip_still_counts():
    g = _all_green()
    g["G-PBT"] = {"status": "skip", "data": {"cases": 0}}
    assert is_green(g)


def test_the_legacy_panel_rollup_satisfies_the_roles():
    g = _all_green()
    for r in PANEL_ROLES:
        del g[r]
    g["G-PANEL"] = {"status": "pass"}
    assert is_green(g)


def test_a_failing_role_is_not_covered_by_the_rollup():
    g = _all_green()
    g[PANEL_ROLES[0]] = {"status": "fail"}
    g["G-PANEL"] = {"status": "pass"}
    assert not is_green(g)
    assert failing_gates(g) == [PANEL_ROLES[0]]


def test_an_empty_blob_is_not_green():
    assert not is_green({})
    assert failing_reasons({}) == ["no gates recorded"]


@pytest.mark.parametrize("shape", [["x"], "text", 3, None])
def test_a_damaged_record_costs_only_its_own_verdict(shape):
    """A record written in another shape carries no flags, so it reads not-green
    rather than raising -- on a corpus sweep an exception here loses every OTHER
    cell's verdict too."""
    g = _all_green()
    g["G-PBT"] = {"status": "pass", "data": shape}
    assert is_green(g) in (True, False)      # the point is that it ANSWERS
    g["G-MUT"] = shape                       # the whole record, not just its data
    assert not is_green(g)


def test_green_check_routes_to_the_shared_predicate(tmp_path):
    """`classify` must not re-derive greenness: the reason string it prints is the
    shared predicate's, so a change there reaches the release gate."""
    bundle = tmp_path / "inst" / "nagini"
    bundle.mkdir(parents=True)
    (bundle / "meta.json").write_text(json.dumps({"gates": _all_green()}))
    assert green_check.classify(bundle, "nagini", "inst") == ("GREEN", "ok")

    blob = _all_green()
    blob["G-MUT"] = {"status": "fail"}
    (bundle / "meta.json").write_text(json.dumps({"gates": blob}))
    verdict, why = green_check.classify(bundle, "nagini", "inst")
    assert verdict == "NOTGREEN"
    assert why == ";".join(failing_reasons(blob))


def test_green_check_reports_an_unreadable_record_without_raising(tmp_path):
    bundle = tmp_path / "inst" / "nagini"
    bundle.mkdir(parents=True)
    assert green_check.classify(bundle, "nagini", "inst")[0] == "NORESULT"
    (bundle / "meta.json").write_text("{truncated")
    assert green_check.classify(bundle, "nagini", "inst")[0] == "NOTGREEN"


def test_the_review_site_asks_the_same_predicate():
    """viz renders badges off `data.is_green`; it must be the same function, not a
    second reading of the same rules."""
    from viz.backend import data
    blob = _all_green()
    assert data.is_green(blob) is is_green(blob) is True
    blob["G-EQ"] = {"status": "fail"}
    assert data.is_green(blob) is is_green(blob) is False
    assert data.failing_gates(blob) == ["G-EQ"]
