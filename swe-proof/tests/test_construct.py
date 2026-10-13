# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Construction-mode unit tests (build_one, prove, cli) — no docker, verifier
envs, or live agent: paths monkeypatched, agent/checker calls mocked.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from swebench_unified import cli, paths, prove as prove_mod
from swebench_unified.agent import StepOutcome
from swebench_unified.config import ProofConfig
from swebench_unified.construct import build_one as b1
from swebench_unified.gates.base import GateResult

from gates_fixtures import tmp_corpus

IID = "astropy__astropy-99999"

ROW = {
    "instance_id": IID,
    "repo": "astropy/astropy",
    "base_commit": "",  # filled by the fixture with the local repo's HEAD
    "patch": "diff --git a/f.py b/f.py\n--- a/f.py\n+++ b/f.py\n@@ -1 +1 @@\n-x = 1\n+x = 2\n",
    "problem_statement": "off by one",
}


def _init_repo(root: Path) -> tuple[Path, str]:
    """A tiny local git repo posing as the bare mirror of astropy/astropy."""
    work = root / "work"
    work.mkdir()
    subprocess.run(["git", "init", "-q", str(work)], check=True)
    (work / "f.py").write_text("x = 1\n")
    env_args = ["-c", "user.email=t@t", "-c", "user.name=t"]
    subprocess.run(["git", "-C", str(work), *env_args, "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(work), *env_args, "commit", "-qm", "base"],
                   check=True)
    sha = subprocess.run(["git", "-C", str(work), "rev-parse", "HEAD"],
                         capture_output=True, text=True, check=True).stdout.strip()
    mirrors = root / "repos"
    mirrors.mkdir()
    mirror = mirrors / "astropy_astropy.git"
    subprocess.run(["git", "clone", "-q", "--bare", str(work), str(mirror)],
                   check=True)
    return mirrors, sha


@pytest.fixture()
def env(tmp_path, monkeypatch):
    mirrors, sha = _init_repo(tmp_path)
    row = dict(ROW, base_commit=sha)          # HEAD of the mirror just built
    tasks = tmp_corpus(tmp_path, monkeypatch, row)
    monkeypatch.setattr(paths, "REPOS_ROOT", mirrors)
    monkeypatch.setattr(paths, "EXPERIMENTS_ROOT", tmp_path / "experiments")
    monkeypatch.setattr(paths, "RUN_PREFIX", f"test{tmp_path.name[-8:]}")
    return {"tasks": tasks, "row": row, "tmp": tmp_path}


def test_prepare_freezes_inputs_at_instance_root_and_creates_worktree(env):
    wt, err = b1.prepare(IID, "nagini", env["row"])
    try:
        assert err is None
        inst = env["tasks"] / IID
        # immutable inputs at the INSTANCE root, not the backend dir
        assert json.loads((inst / "instance.json").read_text()) == env["row"]
        assert (inst / "patch.diff").read_text() == env["row"]["patch"]
        assert not (inst / "nagini" / "instance.json").exists()
        meta = json.loads((inst / "nagini" / "meta.json").read_text())
        assert meta["spec_provenance"] == "cold"
        assert wt.exists() and (wt / "f.py").read_text() == "x = 1\n"
        assert f"_{paths.RUN_PREFIX}_nagini_{IID}" in wt.name
    finally:
        b1.cleanup_worktree(IID, "nagini", env["row"])
    assert not wt.exists()


def test_prepare_blocked_without_mirror(env, monkeypatch):
    monkeypatch.setattr(paths, "REPOS_ROOT", env["tmp"] / "nope")
    wt, err = b1.prepare(IID, "nagini", env["row"])
    assert err and "no repo clone at" in err


def test_prepare_repo_path_override(env):
    # --repo PATH points directly at a (here nonexistent) clone; the error must
    # name that path and hint at --repo, not the default repos/ layout.
    missing = str(env["tmp"] / "my-clone.git")
    wt, err = b1.prepare(IID, "nagini", env["row"], repo_path=missing)
    assert err and missing in err and "--repo" in err


def test_every_step_names_a_mirror_through_one_definition(env, monkeypatch):
    """One `paths.mirror_dir`, so the steps that CREATE a mirror and the ones that
    READ it cannot disagree about its name.

    It was spelled five times -- the clone step, the smoke port (which also
    clones), construction, eval's adversary and the localization builder -- and a
    change on either writer would have left the readers looking for a directory
    nothing makes. That surfaces as `no repo clone at ...`, or worse as a worktree
    failure deep inside a build, rather than as the mismatch it is. Two of the
    five also re-derived SBU_REPOS_ROOT at import, so a test or a driver moving
    the root moved only some of them.
    """
    import build_eval_localization as bel
    import setup_repos

    from swebench_unified.eval import adversary

    elsewhere = env["tmp"] / "other-mirrors"
    monkeypatch.setattr(paths, "REPOS_ROOT", elsewhere)
    want = elsewhere / "astropy_astropy.git"

    assert b1._mirror("astropy/astropy") == want          # construction reads
    assert setup_repos.mirror_dir("astropy/astropy") == want   # the clone writes
    assert adversary.mirror_dir("astropy/astropy") == want
    # benchmark_smoke.py imports paths inside main() on purpose (the roots are
    # read after it sets the benchmark env), so it has no import-time binding to
    # assert here; the source guard below is what covers it.
    # The localization builder takes the root on its command line; the NAME under
    # it is still the one definition.
    assert (bel.mirror_dir("astropy/astropy", env["tmp"] / "cli")
            == env["tmp"] / "cli" / "astropy_astropy.git")


def test_no_step_spells_a_mirror_name_itself():
    """The guard for the test above: it compares resolutions, so it stays green if
    a sixth site re-inlines the rule and happens to agree today."""
    # Assembled, or this file is its own first hit.
    pattern = 'replace("/", "_")' + ' + ".git"'
    hits = subprocess.run(
        ["git", "grep", "-l", "-e", pattern,
         "--", "src", "scripts", "tests", "viz"],
        cwd=str(paths.PROJECT_ROOT), capture_output=True, text=True).stdout.split()
    assert hits == ["src/swebench_unified/paths.py"]


def _write_result(env, backend: str, status: str) -> Path:
    d = env["tasks"] / IID / backend
    d.mkdir(parents=True, exist_ok=True)
    p = d / "result.json"
    p.write_text(json.dumps({"instance_id": IID, "final_status": status}))
    return p


def test_already_green_skips_unless_force(env, monkeypatch):
    _write_result(env, "nagini", "ok")
    called = []
    monkeypatch.setattr(b1, "construct",
                        lambda *a, **k: called.append(1) or (False, "no"))
    out = b1.build_one(IID, "nagini")
    assert out["final_status"] == "ok"
    assert "already green" in out["note"]
    assert not called  # nothing re-ran
    out2 = b1.build_one(IID, "nagini", force=True, skip_docker=True)
    assert called and out2["final_status"] == "blocked"


def _green_gates() -> dict:
    """A fully green gate blob, built from the registry the way
    tests/test_greenness.py builds it, so a gate added there appears here too."""
    from swebench_unified.greenness import PANEL_ROLES, REQUIRED_GATES
    g: dict = {k: {"status": "pass"} for k in REQUIRED_GATES}
    g["G-CONF"] = {"status": "pass", "data": {}}
    g["G-PBT"] = {"status": "pass", "data": {"cases": 4}}
    for r in PANEL_ROLES:
        g[r] = {"status": "pass"}
    return g


def _write_meta(env, backend: str, gates: dict) -> Path:
    d = env["tasks"] / IID / backend
    d.mkdir(parents=True, exist_ok=True)
    p = d / "meta.json"
    p.write_text(json.dumps({"gates": gates}))
    return p


def test_a_green_cell_with_no_result_json_is_still_skipped(env, monkeypatch):
    """The shipped corpora carry no result.json for the proof backends -- it is
    this builder's marker, not part of a bundle -- so a fresh clone asking only
    that question spends an agent run on all 500 cells of a green corpus. The
    recorded verdicts are what travel, read through the shared predicate."""
    _write_meta(env, "nagini", _green_gates())
    assert not (env["tasks"] / IID / "nagini" / "result.json").exists()
    assert b1.already_green(IID, "nagini")
    called = []
    monkeypatch.setattr(b1, "construct",
                        lambda *a, **k: called.append(1) or (False, "no"))
    out = b1.build_one(IID, "nagini")
    assert out["final_status"] == "ok" and "already green" in out["note"]
    assert not called


@pytest.mark.parametrize("damage", ["missing", "failing", "empty"])
def test_a_cell_short_of_green_is_still_built(env, monkeypatch, damage):
    """The skip has to be strictly harder to earn than the marker was, or it
    silently drops work: a missing stamp is not a verdict, and neither is an
    unstamped bundle."""
    gates = _green_gates()
    if damage == "missing":
        del gates["G-VERIFY"]
    elif damage == "failing":
        gates["G-VERIFY"] = {"status": "fail"}
    else:
        gates = {}
    _write_meta(env, "nagini", gates)
    assert not b1.already_green(IID, "nagini")


def test_blocked_result_does_not_skip(env, monkeypatch):
    _write_result(env, "nagini", "blocked")
    monkeypatch.setattr(b1, "construct", lambda *a, **k: (False, "still failing"))
    out = b1.build_one(IID, "nagini", skip_docker=True)
    assert out["final_status"] == "blocked"
    assert "already green" not in out.get("note", "")


def test_unknown_instance_is_blocked(env):
    out = b1.build_one("nope__nope-1", "nagini")
    assert out["final_status"] == "blocked" and "not in frozen dataset" in out["note"]
    # terminal result persisted
    p = env["tasks"] / "nope__nope-1" / "nagini" / "result.json"
    assert json.loads(p.read_text())["final_status"] == "blocked"


def test_construct_failure_writes_blocked_md(env, monkeypatch):
    monkeypatch.setattr(b1, "construct", lambda *a, **k: (False, "gate says no"))
    out = b1.build_one(IID, "nagini", skip_docker=True)
    assert out["final_status"] == "blocked"
    bm = env["tasks"] / IID / "nagini" / "BLOCKED.md"
    assert bm.exists() and "gate says no" in bm.read_text()
    assert not b1._worktree_path(IID, "nagini").exists()  # cleaned on blocked path too


def test_principled_blocked_preserves_agent_breadcrumb(env, monkeypatch):
    def fake_construct(instance_id, backend_name, wt, *a, **k):
        d = env["tasks"] / IID / "nagini"
        meta = json.loads((d / "meta.json").read_text())
        meta["status"] = "blocked"
        (d / "meta.json").write_text(json.dumps(meta))
        (d / "BLOCKED.md").write_text("agent's own detailed reasoning")
        return False, "agent blocked on principle"

    monkeypatch.setattr(b1, "construct", fake_construct)
    out = b1.build_one(IID, "nagini", skip_docker=True)
    assert out["final_status"] == "blocked"
    assert "principled BLOCKED" in out["note"]
    # the agent's breadcrumb is NOT clobbered
    bm = env["tasks"] / IID / "nagini" / "BLOCKED.md"
    assert bm.read_text() == "agent's own detailed reasoning"
    assert not (env["tasks"] / IID / "nagini" / "model.py").exists()


def test_green_path_runs_gates_and_clears_blocked(env, monkeypatch):
    (env["tasks"] / IID).mkdir(exist_ok=True)

    def fake_construct(instance_id, backend_name, wt, *a, **k):
        d = env["tasks"] / IID / "nagini"
        d.mkdir(parents=True, exist_ok=True)
        (d / "BLOCKED.md").write_text("stale from an earlier failed round")
        return True, "built"

    calls = []

    def fake_run_gates(iid, backend, gates, *, mode, record):
        calls.append((tuple(gates), mode))
        return [GateResult("G-X", "pass", "ok")]

    monkeypatch.setattr(b1, "construct", fake_construct)
    monkeypatch.setattr(b1, "run_gates", fake_run_gates)
    out = b1.build_one(IID, "nagini", skip_docker=True)
    assert out["final_status"] == "ok"
    assert all(mode == "strict" for _, mode in calls)
    assert not (env["tasks"] / IID / "nagini" / "BLOCKED.md").exists()
    assert "p1_construct" in out["phase_times"] and "gates" in out["phase_times"]
    assert "p1_5_prove" not in out["phase_times"]  # prove is lean-only


def test_lean_prove_failure_blocks(env, monkeypatch):
    monkeypatch.setattr(b1, "construct", lambda *a, **k: (True, "built"))
    import swebench_unified.prove as pm
    monkeypatch.setattr(pm, "prove", lambda *a, **k: (False, "budget exhausted"))
    out = b1.build_one(IID, "lean", skip_docker=True)
    assert out["final_status"] == "blocked"
    assert out["proof_note"] == "budget exhausted"
    bm = env["tasks"] / IID / "lean" / "BLOCKED.md"
    assert bm.exists() and "Proof did not close" in bm.read_text()


def _outcome(payload):
    return StepOutcome(text="", payload=payload, elapsed_s=1.0,
                       submission_count=1, tool_use_count=1)


def test_prove_lying_agent_self_report_is_not_ok(env, monkeypatch):
    """A claimed status=ok with failing G-VERIFY never yields ok."""
    monkeypatch.setattr(prove_mod, "load_prompt", lambda *a, **k: "p")
    monkeypatch.setattr(prove_mod, "run_agent_step",
                        lambda **k: _outcome({"status": "ok", "notes": "trust me"}))
    monkeypatch.setattr(prove_mod, "_gverify",
                        lambda iid, b: GateResult("G-VERIFY", "fail", "sorryAx"))
    ok, note = prove_mod.prove(IID, "lean",
                               ProofConfig(proof_gen=300, max_proof_attempts=3),
                               model="m")
    assert ok is False
    assert "still failing after 3 proof attempt(s)" in note


def test_prove_ok_only_from_mechanical_pass(env, monkeypatch):
    """A self-reported FAIL is overridden when the mechanical check passes."""
    monkeypatch.setattr(prove_mod, "load_prompt", lambda *a, **k: "p")
    monkeypatch.setattr(prove_mod, "run_agent_step",
                        lambda **k: _outcome({"status": "fail"}))
    monkeypatch.setattr(prove_mod, "_gverify",
                        lambda iid, b: GateResult("G-VERIFY", "pass", "clean"))
    ok, note = prove_mod.prove(IID, "lean", ProofConfig(), model="m")
    assert ok is True and "G-VERIFY passes" in note


def test_prove_self_reported_fail_bounces_to_p1(env, monkeypatch):
    monkeypatch.setattr(prove_mod, "load_prompt", lambda *a, **k: "p")
    monkeypatch.setattr(prove_mod, "run_agent_step",
                        lambda **k: _outcome({"status": "fail", "notes": "spec is wrong"}))
    monkeypatch.setattr(prove_mod, "_gverify",
                        lambda iid, b: GateResult("G-VERIFY", "fail", "no"))
    ok, note = prove_mod.prove(IID, "lean", ProofConfig(max_proof_attempts=5),
                               model="m")
    assert ok is False and "bounce to P1" in note and "spec is wrong" in note


def test_prove_total_budget_shared_across_attempts(env, monkeypatch):
    """proof_gen is a TOTAL budget; the phase stops when it is spent."""
    clock = {"t": 1000.0}
    monkeypatch.setattr(prove_mod.time, "monotonic", lambda: clock["t"])
    monkeypatch.setattr(prove_mod, "load_prompt", lambda *a, **k: "p")
    seen_timeouts = []

    def fake_agent(**kw):
        seen_timeouts.append(kw["timeout_s"])
        clock["t"] += 120.0  # each attempt burns 120s of the 300s budget
        return _outcome({"status": "stuck"})

    monkeypatch.setattr(prove_mod, "run_agent_step", fake_agent)
    monkeypatch.setattr(prove_mod, "_gverify",
                        lambda iid, b: GateResult("G-VERIFY", "fail", "open goal"))
    ok, note = prove_mod.prove(
        IID, "lean", ProofConfig(proof_gen=300, max_proof_attempts=10), model="m")
    assert ok is False
    # 300s budget / 120s per attempt => attempts at t=0,120,240; t=360 is over
    assert seen_timeouts == [300, 180, 60]
    assert "budget (300s) exhausted" in note


def test_prove_axiom_refinement_runs_propose_on_stuck(env, monkeypatch):
    monkeypatch.setattr(prove_mod, "load_prompt", lambda *a, **k: "p")
    steps = []

    def fake_agent(**kw):
        steps.append(kw["submit_step"])
        if kw["submit_step"] == "proof":
            # stuck first; after an axiom lands, the proof closes
            return _outcome({"status": "stuck", "stuck_goal": "g",
                             "needed_property": "n"})
        return _outcome({"verdict": "AXIOM-ADDED"})

    verdicts = iter(["fail", "pass"])
    monkeypatch.setattr(prove_mod, "run_agent_step", fake_agent)
    monkeypatch.setattr(prove_mod, "_gverify",
                        lambda iid, b: GateResult("G-VERIFY", next(verdicts), ""))
    ok, note = prove_mod.prove(
        IID, "lean", ProofConfig(axiom_refinement=True, max_axiom_iterations=3),
        model="m")
    assert ok is True
    assert steps == ["proof", "axiom_propose", "proof"]


def test_prove_baseline_stuck_has_no_axiom_escape(env, monkeypatch):
    monkeypatch.setattr(prove_mod, "load_prompt", lambda *a, **k: "p")
    steps = []

    def fake_agent(**kw):
        steps.append(kw["submit_step"])
        return _outcome({"status": "stuck"})

    monkeypatch.setattr(prove_mod, "run_agent_step", fake_agent)
    monkeypatch.setattr(prove_mod, "_gverify",
                        lambda iid, b: GateResult("G-VERIFY", "fail", ""))
    ok, _ = prove_mod.prove(IID, "lean", ProofConfig(max_proof_attempts=2),
                            model="m")
    assert ok is False
    assert steps == ["proof", "proof"]  # never axiom_propose in baseline mode


def test_worklist_deterministic_shuffle_and_limit():
    from swebench_unified.construct.run_all import worklist
    ids = [f"i{n}" for n in range(20)]
    a = worklist(ids, seed=1776, limit=0)
    b = worklist(ids, seed=1776, limit=0)
    assert a == b and sorted(a) == sorted(ids) and a != ids
    # limit takes a PREFIX of the shuffle, not the head ids
    assert worklist(ids, seed=1776, limit=5) == a[:5]
    assert worklist(ids, seed=42, limit=0) != a


def test_run_all_reads_dataset_ids(env):
    from swebench_unified.construct.run_all import all_instance_ids
    assert all_instance_ids() == [IID]


def test_run_all_passthrough_flags_without_separator(env, monkeypatch):
    """Unknown flags flow through to build_one with no literal `--` needed."""
    import swebench_unified.construct.run_all as ra
    seen = {}
    monkeypatch.setattr(ra, "run_all",
                        lambda backend, ids, *, jobs, wall_seconds, extra:
                        seen.update(backend=backend, ids=ids, extra=extra)
                        or {"ok": len(ids)})
    rc = ra.main(["--backend", "lean", "--limit", "1",
                  "--skip-docker", "--axiom-refinement"])
    assert rc == 0
    assert seen["extra"] == ["--skip-docker", "--axiom-refinement"]
    assert seen["ids"] == [IID]


def test_dry_run_reports_the_worklist_and_launches_nothing(env, monkeypatch, capsys):
    """`--all` spends one agent run per cell, and every precondition it needs was
    checked inside a child after the fan-out had started -- so the only way to
    learn that no provider is configured was to start the run."""
    import swebench_unified.construct.run_all as ra
    monkeypatch.setattr(ra, "run_all", lambda *a, **k: pytest.fail(
        "a dry run must launch nothing"))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    rc = ra.main(["--backend", "nagini", "--dry-run"])
    out = capsys.readouterr().out
    assert rc == 0, out
    assert "nothing is launched" in out and "1 instance(s)" in out
    assert str(env["tasks"]) in out          # the corpus it would write to
    assert "0 blocker(s)" in out


def test_dry_run_names_every_blocker_it_would_hit(env, monkeypatch, capsys):
    import swebench_unified.construct.run_all as ra
    for var in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN",
                "CLAUDE_CODE_OAUTH_TOKEN", "CLAUDE_CODE_USE_BEDROCK",
                "CLAUDE_CODE_USE_VERTEX"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("HOME", str(env["tmp"] / "no-such-home"))
    monkeypatch.setattr(paths, "REPOS_ROOT", env["tmp"] / "no-mirrors")
    rc = ra.main(["--backend", "nagini", "--only", IID, "nope__nope-1",
                  "--dry-run"])
    out = capsys.readouterr().out
    assert rc == 1
    assert "no provider is configured" in out
    assert "not in the frozen dataset" in out and "nope__nope-1" in out
    assert "no mirror" in out and "setup_repos.py" in out


@pytest.mark.parametrize("dry", [True, False])
def test_an_unfetched_dataset_is_reported_not_traced(env, monkeypatch, capsys, dry):
    """The fresh-clone case: nothing under `data/` is committed.

    Reading the frozen dataset unguarded made `--all` a FileNotFoundError
    traceback out of its first line -- including the dry run, whose whole job is
    to report that precondition -- and the reader has no way to tell that from a
    crash in the pipeline.
    """
    import swebench_unified.construct.run_all as ra
    monkeypatch.setattr(paths, "DATASET_JSONL", env["tmp"] / "never-fetched.jsonl")
    monkeypatch.setattr(ra, "run_all", lambda *a, **k: pytest.fail(
        "a run must not start without a worklist"))

    rc = ra.main(["--backend", "nagini"] + (["--dry-run"] if dry else []))
    got = capsys.readouterr()
    assert rc == (1 if dry else 2)
    assert "frozen dataset not found" in (got.out if dry else got.err)
    assert "fetch-dataset" in (got.out if dry else got.err)


def test_run_all_persists_timeout_result(env):
    """A wall-kill leaves a terminal timeout result.json but never clobbers a
    verdict the child managed to write."""
    from swebench_unified.construct.run_all import _persist_timeout_result
    _persist_timeout_result(IID, "nagini", 60)
    p = env["tasks"] / IID / "nagini" / "result.json"
    blob = json.loads(p.read_text())
    assert blob["final_status"] == "timeout" and "60s" in blob["note"]
    p.write_text(json.dumps({"instance_id": IID, "final_status": "ok"}))
    _persist_timeout_result(IID, "nagini", 60)
    assert json.loads(p.read_text())["final_status"] == "ok"


# CLI smoke: help paths + gates on a synthetic bundle

def test_cli_no_args_prints_help(capsys):
    assert cli.main([]) == 2
    assert "construct" in capsys.readouterr().out


@pytest.mark.parametrize("cmd", ["construct", "gates"])
def test_cli_subcommand_help(cmd, capsys):
    with pytest.raises(SystemExit) as e:
        cli.main([cmd, "--help"])
    assert e.value.code == 0
    out = capsys.readouterr().out
    assert "--backend" in out


def test_cli_construct_all_delegates_with_passthrough(env, monkeypatch):
    import swebench_unified.construct.run_all as ra
    seen = {}
    monkeypatch.setattr(ra, "run_all",
                        lambda backend, ids, *, jobs, wall_seconds, extra:
                        seen.update(backend=backend, extra=extra)
                        or {"ok": len(ids)})
    rc = cli.main(["construct", "--all", "--backend", "lean", "--skip-docker"])
    assert rc == 0
    assert seen["backend"] == "lean" and seen["extra"] == ["--skip-docker"]


def test_cli_gates_runs_on_synthetic_bundle(env, capsys):
    inst = env["tasks"] / IID
    inst.mkdir(exist_ok=True)
    (inst / "instance.json").write_text(json.dumps(env["row"]))
    (inst / "patch.diff").write_text(env["row"]["patch"])
    d = inst / "nagini"
    d.mkdir()
    (d / "model.py").write_text("x = 1\n")
    (d / "meta.json").write_text("{}")
    rc = cli.main(["gates", "--backend", "nagini", IID,
                   "--gates", "G-INTEGRITY", "--no-record"])
    out = capsys.readouterr().out
    assert "G-INTEGRITY=pass" in out
    assert rc == 0


def test_cli_gates_mode_feedback_accepted(env, capsys):
    inst = env["tasks"] / IID
    inst.mkdir(exist_ok=True)
    (inst / "instance.json").write_text(json.dumps(env["row"]))
    (inst / "patch.diff").write_text(env["row"]["patch"])
    (inst / "nagini").mkdir()
    rc = cli.main(["gates", "--backend", "nagini", IID, "--mode", "feedback",
                   "--gates", "G-LEAK", "--no-record"])
    assert rc in (0, 1)  # parsed + ran; verdict depends on the synthetic bundle
    assert "G-LEAK" in capsys.readouterr().out
