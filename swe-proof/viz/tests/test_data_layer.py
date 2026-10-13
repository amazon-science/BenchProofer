# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Tests for the read-only data layer: every Pro instance loads, repo browse,
patch parse, guards — plus the Verified benchmark row of the matrix.
Run from the repo root: python -m pytest viz/tests/."""
import pytest
from conftest import BM, FULL_BM, FULL_IID, IID, corpus_size, require_mirror

from backend import data, repo, patchview, paths, settings


def _cell_awaiting_battery() -> str:
    """A constructed cell whose G-PBT is a missing-manifest skip, resolved off the
    corpus rather than pinned: batteries keep landing, so an id pinned for this
    property stops having it."""
    for row in data.summary_table(BM, "nagini"):
        g = data.gates(BM, "nagini", row["instance_id"])
        if not (g.get("G-PBT", {}).get("data") or {}).get("pbt_missing_manifest"):
            continue
        if row["final_status"] == "ok" and data.is_green({**g, "G-PBT": {"status": "pass"}}):
            return row["instance_id"]
    pytest.skip("no constructed pro/nagini cell is still awaiting its battery")


def test_all_instances_load():
    ids = data.all_instance_ids(BM)
    assert len(ids) == corpus_size(BM) > 0
    for iid in ids:
        assert data.dataset_row(BM, iid) is not None


def test_verified_row_loads():
    """The Verified benchmark row is served from its own root."""
    ids = data.all_instance_ids("verified")
    assert len(ids) == corpus_size("verified") > 0
    assert data.dataset_row("verified", ids[0]) is not None
    # the two rows are disjoint id spaces — a Pro id must not resolve under
    # verified (or the boards would silently read the wrong dataset)
    assert data.dataset_row("verified", IID) is None
    assert data.dataset_row(BM, ids[0]) is None


def test_verified_summary_and_green():
    t = data.summary_table("verified", "nagini")
    assert len(t) == corpus_size("verified")
    gc = data.green_counts("verified")
    assert set(gc) == set(settings.BACKENDS)
    assert all(isinstance(v, int) for v in gc.values())


def test_gates_normalized():
    g = data.gates(FULL_BM, "nagini", FULL_IID)
    assert g and g["G-VERIFY"]["status"] == "pass"
    for gate in data.GATE_ORDER:
        assert gate in data.GATE_DEFS, f"no definition for {gate}"


def test_green_classifier_strict():
    import copy
    # the chosen cell has all gates recorded + OK, but its G-PBT is a
    # missing-manifest skip — under the shipped policy that is "battery not
    # yet constructed", NOT green (same convention as G-CONF's missing script)
    g0 = data.gates(BM, "nagini", _cell_awaiting_battery())
    assert (g0["G-PBT"].get("data") or {}).get("pbt_missing_manifest")
    assert not data.is_green(g0)
    # with a real G-PBT verdict the same cell is fully-green
    g = copy.deepcopy(g0)
    g["G-PBT"] = {"status": "pass", "detail": "12 cases, SOUND"}
    assert data.is_green(g)
    assert not data.is_green({})
    assert not data.is_green({"G-VERIFY": {"status": "fail"}})
    # STRICT: a missing stamp is not green, even if everything recorded passes
    for missing in ("G-VERIFY", "G-RESOLVE", "G-EQ", "G-PANEL-2"):
        g2 = copy.deepcopy(g)
        g2.pop(missing, None)
        g2.pop("G-PANEL", None)  # legacy rollup must not paper over a role
        assert not data.is_green(g2), f"green despite missing {missing}"
    # an intentional skip IS green (e.g. G-PBT with no battery)
    g3 = copy.deepcopy(g)
    g3["G-PBT"] = {"status": "skip"}
    g3["G-CONF"] = {"status": "skip", "detail": "no impl region (blocked bundle)"}
    assert data.is_green(g3)
    # ...but the benchmark-unsupported G-CONF placeholder does NOT count:
    # G-CONF is being re-enabled for Pro, so those cells need a real verdict
    g4 = copy.deepcopy(g3)
    g4["G-CONF"] = {"status": "skip", "data": {"docker_oracle_unavailable": True},
                    "detail": "benchmark 'swe_bench_pro_python' does not support "
                              "G-CONF (no wired Docker oracle / generated-script env)"}
    assert not data.is_green(g4)
    # ...nor the missing-script skip: "no conformance_check.py yet" is a
    # construction gap (migrated nagini), not a bundle verdict
    g4["G-CONF"] = {"status": "skip", "data": {"conf_missing_script": True},
                    "detail": "no conformance_check.py (no-RI-content or "
                              "not yet constructed)"}
    assert not data.is_green(g4)
    g4["G-CONF"] = {"status": "pass", "detail": "120000 inputs, 0 disagreements"}
    assert data.is_green(g4)
    # G-PBT missing-manifest skip = battery not yet constructed, not green;
    # a genuine skip (e.g. empty battery on a blocked bundle) still counts
    g5 = copy.deepcopy(g4)
    g5["G-PBT"] = {"status": "skip", "data": {"pbt_missing_manifest": True},
                   "detail": "no properties.py (not yet constructed)"}
    assert not data.is_green(g5)
    g5["G-PBT"] = {"status": "skip", "data": {"pbt_empty_manifest": True},
                   "detail": "properties.py has no SPEC_TESTS"}
    assert data.is_green(g5)


def test_green_counts():
    gc = data.green_counts(BM)
    assert set(gc) == set(settings.BACKENDS)
    assert all(isinstance(v, int) for v in gc.values())


def test_summary_table():
    t = data.summary_table(BM, "nagini")
    assert len(t) == corpus_size(BM)
    by_id = {r["instance_id"]: r for r in t}
    # not green under the G-PBT policy (missing-manifest skip),
    # but constructed ok — green flips back once its battery is written
    awaiting = _cell_awaiting_battery()
    assert not by_id[awaiting]["green"]
    assert by_id[awaiting]["final_status"] == "ok"
    # blocked instances surface as blocked, not green
    assert any(r["final_status"] == "blocked" and not r["green"] for r in t)


def test_bundle_reads_split_layout():
    # backend-level file
    assert "def " in (data.read_bundle_file(FULL_BM, "nagini", FULL_IID, "model.py") or "")
    # instance-level file (patch.diff lives beside the backend dirs)
    assert (data.read_bundle_file(FULL_BM, "nagini", FULL_IID, "patch.diff")
            or "").startswith("diff")


def test_repo_file_at_base():
    require_mirror(BM, IID)
    content = repo.file_at_base(BM, IID, "lib/ansible/module_utils/common/collections.py")
    assert content is None or isinstance(content, str)
    # README must exist at base for ansible
    assert repo.file_at_base(BM, IID, "README.md")


def test_repo_tree_at_base():
    require_mirror(BM, IID)
    root = repo.tree_at_base(BM, IID, "")
    assert root and any(e["name"] == "lib" and e["type"] == "tree" for e in root)


def test_verified_repo_mirror_resolves():
    """Verified mirrors live under repos/, keyed off the <org>__<proj> prefix."""
    ids = [i for i in data.all_instance_ids("verified") if i.startswith("django__django")]
    assert ids, "expected django instances in the verified row"
    assert require_mirror("verified", ids[0]) is not None
    # reading a real file at base_commit exercises the whole mirror path
    assert repo.file_at_base("verified", ids[0], "README.rst") is not None


def test_mirror_for_always_returns_a_gitdir():
    """mirror_for() feeds `git --git-dir`, so it must return a git DIRECTORY
    (bare repo or a worktree's .git) — never a worktree root, which --git-dir
    cannot read."""
    for bm, iid in (("pro", IID),
                    ("verified", data.all_instance_ids("verified")[0])):
        m = require_mirror(bm, iid)
        assert m.name.endswith(".git"), f"{bm}: {m} is not a gitdir"
        # HEAD lives directly in a gitdir; its absence means we handed back a worktree
        assert (m / "HEAD").is_file(), f"{bm}: {m} has no HEAD — not a gitdir"


def test_mirrors_do_not_cross_benchmark_roots():
    """A Pro instance must not resolve against the Verified mirror root (or the
    board would show another dataset's history)."""
    assert paths.mirror_for("verified", IID) is None      # ansible is not in repos/
    vid = next(i for i in data.all_instance_ids("verified") if i.startswith("django__"))
    assert paths.mirror_for("pro", vid) is None           # django is not in repos-pro/
    assert repo.file_at_base("pro", vid, "README.rst") is None


def test_changed_files():
    cf = repo.changed_files(FULL_BM, "nagini", FULL_IID)
    assert cf


def test_patch_parse_and_context():
    diff = data.read_bundle_file(FULL_BM, "nagini", FULL_IID, "patch.diff")
    assert diff
    files = patchview.parse(diff)
    assert files and files[0]["hunks"]
    for f in files:
        for h in f["hunks"]:
            assert h["lines"]
            for ln in h["lines"]:
                assert ln["tag"] in ("ctx", "add", "del")
    st = patchview.stats(diff)
    assert st["added"] > 0 and st["files"] >= 1


def test_prepatch_diffs():
    diffs = data.prepatch_diffs(FULL_BM, "nagini", FULL_IID)
    assert diffs, "expected at least one prepatch diff"
    assert any(ln["tag"] in ("add", "del") for d in diffs for ln in d["lines"])


def test_audit_notes():
    notes = data.audit_notes(FULL_BM, "nagini", FULL_IID)
    assert notes and any(n["gate"] == "G-EQ" for n in notes)


def test_the_g_eq_card_publishes_the_word_its_reviewer_recorded(monkeypatch):
    """The advisory verdict is recorded per reviewer RUN, and one reviewer scores
    both G-EQ and G-PANEL-1 -- but only the second entry keeps the field, since
    `gates._record` replaces a mechanical gate's blob on every re-gate. Read per
    gate, this card published an empty verdict for G-EQ on every cell."""
    monkeypatch.setattr(data, "gates", lambda *a: {
        "G-EQ": {"status": "pass", "detail": "eq: 7 attacks re-run"},
        "G-PANEL-1": {"status": "pass", "note": "panel_1: 7 re-run",
                      "agent_verdict": "SOUND"}})
    cards = {c["gate"]: c for c in data.audit_notes(BM, "nagini", IID)}
    assert cards["G-EQ"]["verdict"] == "SOUND" == cards["G-PANEL-1"]["verdict"]


def test_a_role_that_never_judged_says_so_instead_of_rendering_blank(monkeypatch):
    """Some roles record a status and nothing else. Published as recorded, that
    card is a heading, a badge and an empty body -- indistinguishable from a note
    that failed to render."""
    monkeypatch.setattr(data, "gates", lambda *a: {
        "G-EQ": {"status": "skip", "reason": "blocked"},
        "G-PANEL-1": {"status": "n/a"}})
    cards = {c["gate"]: c for c in data.audit_notes(BM, "nagini", IID)}
    assert "blocked" in cards["G-EQ"]["note"]
    assert "no audit account" in cards["G-PANEL-1"]["note"]


def test_an_empty_note_on_a_passing_role_is_left_empty(monkeypatch):
    """The control: a pass with no account is a defect in the RECORD, and
    inventing a sentence for it here would hide exactly that."""
    monkeypatch.setattr(data, "gates", lambda *a: {"G-EQ": {"status": "pass"}})
    assert data.audit_notes(BM, "nagini", IID)[0]["note"] == ""


def test_audit_notes_do_not_publish_the_audit_s_own_workspace(monkeypatch):
    """This card is a PUBLISHED surface and the recorded field is not one.

    `publish_note` alone leaves the build's own narration in place, because that is
    the rule set the record on disk is held to -- the pipeline reads it back. A
    scratch directory deleted once the audit finished would then be published here
    as if a reader could open it, so the card has to apply the narration rules
    itself, in the order `verdict_prose_lint` applies them to `verdict.md`.
    """
    note = ("Copied the built astropy to $SCRATCH/site-packages and re-ran; "
            "timeout 600 bash scripts/lean_verify.sh spec.lean returned exit 0. "
            "The `__init__` path is unchanged.")
    monkeypatch.setattr(data, "gates", lambda *a: {"G-EQ": {
        "status": "pass", "detail": note, "agent_verdict": "TIGHT"}})
    published = data.audit_notes(BM, "nagini", IID)[0]["note"]
    assert "$SCRATCH" not in published and "timeout 600" not in published
    assert "exit 0" in published                      # the evidence survives
    assert "`__init__`" in published                  # and publish_note still ran


def test_verdict_md_rendered_as_dedicated_card():
    # the consolidated audit prose is surfaced via verdict_md() (a dedicated
    # "Audit verdict" card) — NOT as a file in the bundle file browser.
    assert not any(name == "verdict.md"
                   for name, _l, _lang in data.bundle_files("nagini"))
    ids = data.all_instance_ids("verified")
    for iid in ids:
        txt = data.verdict_md("verified", "nagini", iid)
        if txt:
            assert "P2 adversarial audit" in txt
            return
    raise AssertionError("no nagini verdict.md found under benchmark-verified")


def test_path_traversal_guard():
    root = paths.bench_root(BM)
    with pytest.raises(ValueError):
        paths.safe_under(root, "..", "..", "etc", "passwd")
    p = paths.safe_under(root, IID, "nagini", "model.py")
    assert p.is_file()
    # escaping bundle file read returns None, never raises out
    assert data.read_bundle_file(BM, "nagini", IID, "../../pyproject.toml") is None


def test_repo_path_guard():
    assert repo.file_at_base(BM, IID, "../../../etc/passwd") is None
    assert repo.file_at_base(BM, IID, "/etc/passwd") is None


# ---- the falsification card reads the lane that is kept in sync -------------

def _pbt(monkeypatch, *, gate_rec, file_json):
    """pbt_result() with a synthetic gate record and persisted file."""
    monkeypatch.setattr(data, "gates",
                        lambda *a, **k: {"G-PBT": gate_rec} if gate_rec else {})
    monkeypatch.setattr(data, "read_bundle_file",
                        lambda *a, **k: file_json)
    return data.pbt_result(BM, "nagini", IID)


_GATE = {"status": "pass",
         "data": {"verdict": "SOUND",
                  "cases": [{"id": "fresh-a", "ok": True},
                            {"id": "fresh-b", "ok": True}]}}


def test_spec_lane_comes_from_the_gate_not_the_stale_file(monkeypatch):
    """The two copies disagree wherever a spec repair rewrote the manifest, since
    only the gate re-runs. The card must show the battery that exists now."""
    out = _pbt(monkeypatch, gate_rec=_GATE,
               file_json='{"verdict": "SOUND", "spec_cases": '
                         '[{"id": "stale-only", "ok": true}], "axiom_cases": []}')
    assert [c["id"] for c in out["spec_cases"]] == ["fresh-a", "fresh-b"]


def test_a_backend_that_ships_no_file_still_gets_a_card(monkeypatch):
    """velvet and lean record the same per-case data and ship no file, so reading
    only the file leaves the card blank on every one of their bundles."""
    out = _pbt(monkeypatch, gate_rec=_GATE, file_json=None)
    assert out and len(out["spec_cases"]) == 2 and out["verdict"] == "SOUND"


def test_the_axiom_lane_is_kept(monkeypatch):
    """It is recorded nowhere else -- G-AX keeps only its exit status -- so the
    file is still the source for it."""
    out = _pbt(monkeypatch, gate_rec=_GATE,
               file_json='{"spec_cases": [], "axiom_cases": '
                         '[{"id": "ax-1", "ok": true}]}')
    assert [c["id"] for c in out["axiom_cases"]] == ["ax-1"]


def test_the_gates_verdict_wins_over_the_files(monkeypatch):
    out = _pbt(monkeypatch, gate_rec=_GATE,
               file_json='{"verdict": "UNSOUND", "spec_cases": []}')
    assert out["verdict"] == "SOUND"


def test_no_cases_anywhere_renders_nothing(monkeypatch):
    """A missing-manifest skip must not produce an empty card."""
    assert _pbt(monkeypatch,
                gate_rec={"status": "skip",
                          "data": {"pbt_missing_manifest": True}},
                file_json=None) is None


def test_a_failing_battery_is_not_reported_sound(monkeypatch):
    out = _pbt(monkeypatch,
               gate_rec={"status": "fail",
                         "data": {"cases": [{"id": "c", "ok": False}]}},
               file_json=None)
    assert out["verdict"] == "FAIL"


def test_unparsable_file_does_not_lose_the_gates_lane(monkeypatch):
    out = _pbt(monkeypatch, gate_rec=_GATE, file_json="{not json")
    assert out and len(out["spec_cases"]) == 2
