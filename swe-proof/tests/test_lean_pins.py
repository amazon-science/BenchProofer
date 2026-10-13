# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The shipped Lean workspace matches the pins it is documented to be built from.

A recorded Lean verdict describes the prover that produced it and nothing else,
so PINS.md, `lake-manifest.json` and `lean-toolchain` disagreeing is not a
documentation bug: it means the table naming the prover for 1000 shipped bundles
names revisions the workspace does not use.

`install.sh` already fails closed on that, but reaching its check costs an elan
toolchain and a full Mathlib build, so it cannot be what catches a drift
COMMITTED to git. This is. The comparison itself is imported, never restated
here: a test that re-derives the rule can pass while the installer refuses.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from lean_pins import DEFAULT_SHARED, drift, main, pinned_revisions

ROOT = Path(__file__).resolve().parents[1]


def test_the_shipped_workspace_matches_pins_md():
    assert drift() == [], (
        "lean_shared/PINS.md and the workspace disagree, so install.sh would "
        "refuse this checkout after a full Mathlib build")


def test_every_manifest_package_has_a_row():
    """A missing row is drift, because most deps are requested by BRANCH.

    `inputRev` is `main` or `master` for most of the manifest, so the revision it
    records is the only thing that fixes them; a package with no row is a
    dependency whose pin is documented nowhere.
    """
    pinned = pinned_revisions()
    packages = json.loads((DEFAULT_SHARED / "lake-manifest.json").read_text())["packages"]
    assert packages, "no packages in lake-manifest.json: nothing pins the workspace"
    missing = [p["name"] for p in packages if p["name"].lower() not in pinned]
    assert missing == []


def test_install_sh_asks_this_module_rather_than_its_own_copy():
    """One definition. install.sh used to carry the comparison inline, and an
    installer that answers from its own copy can accept a workspace this refuses."""
    text = (ROOT / "install.sh").read_text()
    assert "scripts/lean_pins.py" in text
    assert "json.loads" not in text and "re.match" not in text


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    """A copy of the real pin files, so a mutation is a one-line edit."""
    ws = tmp_path / "lean_shared"
    ws.mkdir()
    for name in ("PINS.md", "lake-manifest.json", "lean-toolchain"):
        shutil.copy(DEFAULT_SHARED / name, ws / name)
    return ws


def test_a_moved_dependency_revision_is_drift(workspace: Path):
    manifest = json.loads((workspace / "lake-manifest.json").read_text())
    moved = manifest["packages"][0]
    moved["rev"] = "0" * 40
    (workspace / "lake-manifest.json").write_text(json.dumps(manifest))

    problems = drift(workspace)
    assert any(moved["name"] in p and "0000" in p for p in problems), problems
    assert main(["--shared", str(workspace)]) == 1


def test_a_moved_toolchain_is_drift(workspace: Path):
    (workspace / "lean-toolchain").write_text("leanprover/lean4:v4.34.0-rc1\n")
    problems = drift(workspace)
    assert any("lean-toolchain is leanprover/lean4:v4.34.0-rc1" in p for p in problems)
    assert main(["--shared", str(workspace)]) == 1


def test_a_dependency_with_no_row_is_drift(workspace: Path):
    manifest = json.loads((workspace / "lake-manifest.json").read_text())
    manifest["packages"].append({"name": "undocumented", "rev": "1" * 40})
    (workspace / "lake-manifest.json").write_text(json.dumps(manifest))
    assert any("undocumented" in p and "no PINS.md row" in p
               for p in drift(workspace))


def test_a_clean_workspace_exits_zero(workspace: Path):
    assert main(["--shared", str(workspace)]) == 0
