# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""spec_impact joining + statistics — no network/docker/creds/model.

Synthetic audit ballots + grade results in tmp_path with monkeypatched roots, so
every assertion is on the analysis arithmetic, not on a judge.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from swebench_unified.eval import spec_impact as si
from swebench_unified.eval.grade import _SPEC_PROPERTIES

ALL_PASS = dict.fromkeys(_SPEC_PROPERTIES, True)


def rates(rows: list[dict], split: str) -> dict:
    """si.rates for a split we assert is non-empty."""
    out = si.rates(rows, split)
    assert out is not None, f"expected a non-empty {split} split"
    return out


def ballot(**overrides) -> dict:
    """One decisive ballot; overrides flip individual properties to False."""
    return {**ALL_PASS, "pass": not overrides, **overrides}


def write_instance(root: Path, run_id: str, iid: str, votes: list[dict],
                   resolved: bool | None = True, passed: bool = False,
                   spec_ok: bool | None = None, grade: bool = True):
    """One instance's audit ballot record + its grade/result.json."""
    adir = root / "eval" / "m4_spec_audit" / run_id
    adir.mkdir(parents=True, exist_ok=True)
    (adir / f"{iid}.json").write_text(json.dumps({
        "instance_id": iid, "run_id": run_id, "votes": votes,
        "spec_ok": spec_ok if spec_ok is not None
        else (sum(1 for v in votes if v.get("pass")) > len(votes) / 2),
    }))
    if grade:
        gdir = root / "eval" / run_id / iid / "grade"
        gdir.mkdir(parents=True, exist_ok=True)
        (gdir / "result.json").write_text(json.dumps(
            {"resolved": resolved, "passed": passed}))


def write_config(root: Path, run_id: str, **cfg):
    d = root / "eval" / run_id
    d.mkdir(parents=True, exist_ok=True)
    (d / "config.json").write_text(json.dumps({"run_id": run_id, **cfg}))


@pytest.fixture()
def roots(tmp_path, monkeypatch):
    """Point spec_impact's module-level roots at tmp_path."""
    monkeypatch.setattr(si, "EVAL_ROOT", tmp_path / "eval")
    monkeypatch.setattr(si, "AUDIT_ROOT", tmp_path / "eval" / "m4_spec_audit")
    return tmp_path


# ---------------- load_seed: the join ----------------

def test_load_seed_majority_rule(roots):
    # 3 ballots, 2 of which fail `faithful` -> majority failure on faithful only
    write_instance(roots, "r1", "a__b-1",
                   [ballot(faithful=False), ballot(faithful=False), ballot()])
    rows = si.load_seed("r1")
    assert len(rows) == 1
    assert rows[0]["fails"]["faithful"] is True
    assert rows[0]["fails"]["sound"] is False
    assert rows[0]["n_decisive"] == 3


def test_load_seed_tie_is_not_a_failure(roots):
    # 1 of 2 fails: NOT a majority (strict >), matching grade_spec's rule
    write_instance(roots, "r1", "a__b-1", [ballot(sound=False), ballot()])
    assert si.load_seed("r1")[0]["fails"]["sound"] is False


def test_load_seed_ignores_infra_abstentions(roots):
    # a parse_error ballot must not count as a refutation, only shrink the pool
    write_instance(roots, "r1", "a__b-1",
                   [ballot(complete=False), {"parse_error": True}])
    rows = si.load_seed("r1")
    assert rows[0]["n_decisive"] == 1
    assert rows[0]["fails"]["complete"] is True


def test_load_seed_skips_fully_abstained_and_ungraded(roots):
    write_instance(roots, "r1", "all-abstained", [{"parse_error": True}])
    write_instance(roots, "r1", "no-grade", [ballot()], grade=False)
    write_instance(roots, "r1", "good", [ballot()])
    assert [r["instance_id"] for r in si.load_seed("r1")] == ["good"]


def test_load_seed_survives_half_written_json(roots):
    write_instance(roots, "r1", "good", [ballot()])
    (roots / "eval" / "m4_spec_audit" / "r1" / "truncated.json").write_text('{"votes": [')
    assert [r["instance_id"] for r in si.load_seed("r1")] == ["good"]


def test_load_seed_ignores_parked_abstentions_subdir(roots):
    """The driver parks all-abstained records under _abstained/; it must not be
    globbed back in as a ballot (the glob is *.json, non-recursive)."""
    write_instance(roots, "r1", "good", [ballot()])
    park = roots / "eval" / "m4_spec_audit" / "r1" / "_abstained"
    park.mkdir()
    (park / "bad.json").write_text(json.dumps({"votes": [{"parse_error": True}]}))
    assert [r["instance_id"] for r in si.load_seed("r1")] == ["good"]


# ---------------- rates: the split ----------------

def test_rates_split_by_resolved(roots):
    write_instance(roots, "r1", "res-1", [ballot()], resolved=True)
    write_instance(roots, "r1", "unres-1", [ballot(faithful=False)], resolved=False)
    write_instance(roots, "r1", "unres-2", [ballot(faithful=False)], resolved=False)
    rows = si.load_seed("r1")

    assert rates(rows, "resolved")["faithful"] == 0.0
    assert rates(rows, "unresolved")["faithful"] == 100.0
    assert rates(rows, "overall")["faithful"] == pytest.approx(200 / 3)
    assert rates(rows, "resolved")["_n"] == 1
    assert rates(rows, "unresolved")["_n"] == 2


def test_rates_none_for_empty_split(roots):
    write_instance(roots, "r1", "res-1", [ballot()], resolved=True)
    assert si.rates(si.load_seed("r1"), "unresolved") is None


def test_rates_any_key_uses_spec_ok(roots):
    write_instance(roots, "r1", "i1", [ballot(sound=False)], spec_ok=False)
    write_instance(roots, "r1", "i2", [ballot()], spec_ok=True)
    assert rates(si.load_seed("r1"), "overall")[si.ANY_KEY] == 50.0


# ---------------- aggregate: seeds as replicates ----------------

def test_aggregate_across_seeds(roots):
    # seed 1: 0% of unresolved fail faithful; seed 2: 100% -> mean 50, pstdev 50
    write_instance(roots, "s1", "u1", [ballot()], resolved=False)
    write_instance(roots, "s2", "u1", [ballot(faithful=False)], resolved=False)
    agg = si.aggregate(["s1", "s2"])
    e = agg["splits"]["unresolved"]["faithful"]
    assert e["mean"] == 50.0
    assert e["std"] == 50.0
    assert e["per_seed"] == [0.0, 100.0]
    assert agg["splits"]["unresolved"]["n_seeds"] == 2
    assert agg["seeds"] == {"s1": 1, "s2": 1}


def test_aggregate_single_seed_has_zero_std(roots):
    write_instance(roots, "s1", "u1", [ballot(faithful=False)], resolved=False)
    assert si.aggregate(["s1"])["splits"]["unresolved"]["faithful"]["std"] == 0.0


def test_aggregate_skips_empty_seeds(roots):
    write_instance(roots, "s1", "u1", [ballot()], resolved=False)
    (roots / "eval" / "m4_spec_audit" / "s2").mkdir(parents=True)
    agg = si.aggregate(["s1", "s2"])
    assert list(agg["seeds"]) == ["s1"]


def test_aggregate_empty_is_safe(roots):
    (roots / "eval" / "m4_spec_audit" / "s1").mkdir(parents=True)
    agg = si.aggregate(["s1"])
    assert agg["splits"] == {}
    assert agg["seeds"] == {}
    assert "resolve_rate" not in agg          # nothing to average


def test_resolve_rate(roots):
    write_instance(roots, "s1", "a", [ballot()], resolved=True)
    write_instance(roots, "s1", "b", [ballot()], resolved=False)
    assert si.aggregate(["s1"])["resolve_rate"]["mean"] == 50.0


# ---------------- gap: the effect size ----------------

def test_gap_is_unresolved_minus_resolved(roots):
    write_instance(roots, "s1", "r1", [ballot()], resolved=True)
    write_instance(roots, "s1", "u1", [ballot(faithful=False)], resolved=False)
    agg = si.aggregate(["s1"])
    assert si.gap(agg, "faithful") == 100.0
    assert si.gap(agg, "sound") == 0.0


def test_gap_none_when_a_split_is_missing(roots):
    write_instance(roots, "s1", "r1", [ballot()], resolved=True)
    assert si.gap(si.aggregate(["s1"]), "faithful") is None


# ---------------- discovery: runs, configs, cells ----------------

def test_run_config_and_backend(roots):
    write_config(roots, "r1", backend="velvet", mode=4, model="opus-4.8")
    assert si.run_backend("r1") == "velvet"
    assert si.run_config("r1")["mode"] == 4
    assert si.run_config("missing") == {}


def test_run_config_survives_bad_json(roots):
    d = roots / "eval" / "r1"
    d.mkdir(parents=True)
    (d / "config.json").write_text("{not json")
    assert si.run_config("r1") == {}
    assert si.run_backend("r1") is None


def test_audited_runs_needs_a_ballot(roots):
    write_instance(roots, "has-ballot", "i1", [ballot()])
    (roots / "eval" / "m4_spec_audit" / "empty-dir").mkdir(parents=True)
    assert si.audited_runs() == ["has-ballot"]
    assert si.audited_runs(prefix="nagini") == []


def test_audited_runs_empty_when_no_root(tmp_path, monkeypatch):
    monkeypatch.setattr(si, "AUDIT_ROOT", tmp_path / "nope")
    assert si.audited_runs() == []


def test_cells_group_seeds_by_backend_model_mode(roots):
    for run_id, backend in [("n-s1", "nagini"), ("n-s2", "nagini"), ("v-s1", "velvet")]:
        write_config(roots, run_id, backend=backend, mode=4, model="opus-4.8")
        write_instance(roots, run_id, "i1", [ballot()])
    cells = si.cells()
    assert cells[("nagini", "opus-4.8", 4)] == ["n-s1", "n-s2"]
    assert cells[("velvet", "opus-4.8", 4)] == ["v-s1"]


def test_cells_keeps_configless_runs_visible(roots):
    write_instance(roots, "legacy", "i1", [ballot()])
    assert si.cells()[("?", "?", None)] == ["legacy"]


def test_cell_label_and_slug():
    assert si.cell_label(("nagini", "opus-4.8", 4)) == "nagini / opus-4.8 / mode 4"
    assert si.cell_slug(("nagini", "opus-4.8", 4)) == "nagini-opus-4.8-m4"
    assert si.cell_slug(("?", "?", None)) == "?-?-mx"


# ---------------- table rendering ----------------

def test_table_renders_every_property_and_the_gap(roots):
    write_instance(roots, "s1", "r1", [ballot()], resolved=True)
    write_instance(roots, "s1", "u1", [ballot(faithful=False)], resolved=False)
    out = si.table("nagini / opus-4.8 / mode 4", si.aggregate(["s1"]))
    assert "nagini / opus-4.8 / mode 4" in out
    for p in _SPEC_PROPERTIES:
        assert p in out
    assert "SPEC FAILS (any)" in out
    assert "+100.0" in out                    # the faithfulness gap
    for split in ("resolved", "unresolved", "overall"):
        assert split in out
