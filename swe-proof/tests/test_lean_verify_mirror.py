# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The local-disk mirror must never change a verdict.

When `lean_shared/.lake` lives on a network filesystem, elaborating one file
re-opens the whole Mathlib olean tree, so a build is bound on metadata
round-trips rather than CPU and the cores sit idle. A byte copy on local disk is
an order of magnitude faster, so lean_verify.sh prefers a mirror.

That optimization is only sound while the mirror elaborates against the SAME
Mathlib. A mirror built from different pins would hand back verdicts that do not
describe the shipped artifact, silently corrupting every G-PBT record it touched
-- far worse than being slow. Hence the fingerprint check, and hence this file:
the fallback has to fail CLOSED on every way a mirror can be wrong.

These tests never invoke Lean. They assert which workspace the script CHOOSES,
by giving it a file that does not exist: the choice is announced on stderr, and
the `no such file` exit happens before any build. That keeps the check free
enough to run in the ordinary suite.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "lean_verify.sh"
# The four files whose bytes decide what the oleans are: dep revisions, the
# toolchain, the build's targets, and the prelude every artifact imports.
PINS = ("lake-manifest.json", "lean-toolchain", "lakefile.lean",
        "LeanShared.lean")


def run(mirror: str | None, tmp_path: Path) -> str:
    """stderr from a run whose target file does not exist.

    The mirror decision is made before the build, so a missing file exercises
    the choice without paying for Lean.
    """
    env = {"PATH": "/usr/bin:/bin", "HOME": str(tmp_path)}
    if mirror is not None:
        env["SBU_LEAN_SHARED"] = mirror
    p = subprocess.run(["bash", str(SCRIPT), str(tmp_path / "absent.lean")],
                       capture_output=True, text=True, env=env, cwd=str(ROOT))
    return p.stderr


def fake_mirror(tmp_path: Path, *, pins_match: bool = True,
                built: bool = True) -> Path:
    """A mirror directory, optionally with the canonical pins and a .lake."""
    m = tmp_path / "mirror"
    m.mkdir()
    for name in PINS:
        src = ROOT / "lean_shared" / name
        text = src.read_text() if src.is_file() else ""
        (m / name).write_text(text if pins_match else text + "\n-- drift\n")
    if built:
        (m / ".lake").mkdir()
    return m


def test_a_matching_mirror_is_used(tmp_path: Path):
    """The whole point: same pins, so the oleans are the same oleans."""
    m = fake_mirror(tmp_path)
    err = run(str(m), tmp_path)
    assert "pins differ" not in err and "no .lake" not in err, (
        f"a pin-identical mirror must be used, got: {err!r}")


@pytest.mark.parametrize("name", PINS)
def test_a_drifted_pin_falls_back(name: str, tmp_path: Path):
    """One byte in ANY of the four pin files disqualifies the mirror.

    Parametrized because a fingerprint that covered only the manifest would let
    a toolchain or prelude change through, and that is precisely the mismatch
    that yields verdicts about a different Mathlib.
    """
    m = fake_mirror(tmp_path)
    (m / name).write_text((m / name).read_text() + "\n-- drift\n")
    assert "pins differ" in run(str(m), tmp_path), (
        f"drift in {name} must disqualify the mirror")


def test_a_missing_pin_file_falls_back(tmp_path: Path):
    """An absent pin file must not fingerprint-match by both sides being empty.

    `cat` on a missing file writes nothing, so a mirror that simply lacks
    `lean-toolchain` would hash as if the canonical one also lacked it. It does
    not (the canonical files are all present), so the hashes differ and the
    fallback triggers -- but this pins that, because the failure mode of a
    fingerprint built from `cat` is exactly a silent empty read.
    """
    m = fake_mirror(tmp_path)
    (m / "lean-toolchain").unlink()
    assert "pins differ" in run(str(m), tmp_path)


def test_an_unbuilt_mirror_falls_back(tmp_path: Path):
    """Right pins, no oleans: every build would fail as an infra error, which a
    gate would record as a spec defect."""
    m = fake_mirror(tmp_path, built=False)
    assert "no .lake" in run(str(m), tmp_path)


def test_an_absent_mirror_falls_back(tmp_path: Path):
    """The default path need not exist -- on a fresh host it will not."""
    assert "no .lake" in run(str(tmp_path / "nope"), tmp_path)


def test_the_mirror_can_be_switched_off(tmp_path: Path):
    """An empty value is an explicit opt-out, and must be silent rather than
    warning about a mirror the caller never asked for."""
    err = run("", tmp_path)
    assert "pins differ" not in err and "no .lake" not in err


def test_the_canonical_workspace_is_never_reported_as_a_mirror(tmp_path: Path):
    """Pointing the mirror at the workspace itself is a no-op, not a warning."""
    err = run(str(ROOT / "lean_shared"), tmp_path)
    assert "pins differ" not in err and "no .lake" not in err


def test_the_default_is_local_disk():
    """Defaulted rather than opt-in on purpose: the drivers spawn many agent
    subprocesses that invoke this script fresh per build, so a default reaches
    work already in flight, where an env var would need a relaunch and would
    discard hours of unfinished agent work."""
    text = SCRIPT.read_text()
    assert 'MIRROR="${SBU_LEAN_SHARED-' in text, (
        "the default must use ${VAR-default} (unset-only) rather than "
        "${VAR:-default}, or an explicit empty opt-out silently re-enables it")
    assert "lean_shared_local" in text


def test_a_probe_in_the_repo_root_is_refused(tmp_path: Path):
    """Prose in the prompts has not been enough to keep scratch out of the root.

    Agents have repeatedly written a rival beside the checkout and redirected its
    build log there too, so `new__rival.lean` and `new__rival.log` end up staged
    into a commit and ship in the released artifacts. Refusing the build is what
    actually stops it: the agent's own inner loop fails at once, with the fix in
    the message, rather than the stray surviving until someone reads
    `git status`.
    """
    probe = ROOT / ".pytest_root_probe.lean"
    probe.write_text("-- scratch\n")
    try:
        p = subprocess.run(["bash", str(SCRIPT), str(probe)],
                           capture_output=True, text=True,
                           env={"PATH": "/usr/bin:/bin", "HOME": str(tmp_path)},
                           cwd=str(ROOT))
        assert p.returncode == 2, p.stderr
        assert "repo root" in p.stderr and "mktemp" in p.stderr
    finally:
        probe.unlink(missing_ok=True)


def test_a_bundle_file_is_not_refused(tmp_path: Path):
    """The screen must catch only the ROOT. Every real build target lives in a
    bundle directory, and refusing one of those would stop every real build."""
    d = ROOT / "benchmark-verified"
    target = (d if d.is_dir() else tmp_path) / "absent_probe.lean"
    p = subprocess.run(["bash", str(SCRIPT), str(target)],
                       capture_output=True, text=True,
                       env={"PATH": "/usr/bin:/bin", "HOME": str(tmp_path)},
                       cwd=str(ROOT))
    assert "repo root" not in p.stderr, p.stderr
