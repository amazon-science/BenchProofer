# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""A driver must supply its own toolchain, and say so when it cannot.

The property: a missing tool must never be recorded as a fact about a
specification. A driver launched with a minimal `PATH` -- no interpreter, no
per-user bin, no conda -- does not crash. Its lanes start and write records
("verifier did not reach a verdict", "0 admissible attacks of 0 submitted") that
read as verdicts on the cell when the real cause is that nothing could be
launched. So the toolchain is checked before any lane writes, not discovered one
damaged cell at a time.

Two defences, each tested here:
  1. the verify script finds its own env instead of trusting PATH,
  2. the drivers put what their children need back on PATH.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

NAGINI_VERIFY = ROOT / "scripts" / "nagini_verify.sh"
BARE_PATH = "/usr/local/bin:/usr/bin:/bin"
ENV_NAME = "test-verifier-env"


def _fake_env(prefix: Path) -> Path:
    """A directory that looks like a conda env with nagini installed."""
    bin_dir = prefix / "bin"
    bin_dir.mkdir(parents=True)
    stub = bin_dir / "nagini"
    stub.write_text("#!/bin/sh\necho 'Verification successful'\n")
    stub.chmod(0o755)
    return prefix


def _run_check_env(env: dict) -> subprocess.CompletedProcess:
    return subprocess.run(["bash", str(NAGINI_VERIFY), "--check-env"],
                          capture_output=True, text=True, timeout=180, env=env)


# ---- 1. the verify script finds its own env ----

def test_check_env_finds_the_verifier_under_a_bare_path(tmp_path):
    """The environment a scheduler hands a job: no conda anywhere on PATH."""
    prefix = _fake_env(tmp_path / "anaconda3" / "envs" / ENV_NAME)
    p = _run_check_env({"HOME": str(tmp_path), "PATH": BARE_PATH,
                        "SWEBENCH_NAGINI_VERIFIER_ENV": ENV_NAME})
    assert p.returncode == 0, p.stderr
    assert str(prefix) in p.stdout


def test_check_env_accepts_an_explicit_prefix(tmp_path):
    """An operator must be able to say where the env is without a conda layout:
    a container image, a shared install, a non-standard root."""
    prefix = _fake_env(tmp_path / "somewhere" / "else")
    p = _run_check_env({"HOME": "/nonexistent", "PATH": BARE_PATH,
                        "SWEBENCH_NAGINI_VERIFIER_PREFIX": str(prefix)})
    assert p.returncode == 0, p.stderr
    assert str(prefix) in p.stdout


def test_check_env_derives_the_base_from_an_activated_env(tmp_path):
    """An activated conda env exports CONDA_EXE even when PATH is stripped, so it
    is the cheapest correct answer available."""
    base = tmp_path / "conda-base"
    _fake_env(base / "envs" / ENV_NAME)
    (base / "bin").mkdir(parents=True, exist_ok=True)
    p = _run_check_env({"HOME": "/nonexistent", "PATH": BARE_PATH,
                        "CONDA_EXE": str(base / "bin" / "conda"),
                        "SWEBENCH_NAGINI_VERIFIER_ENV": ENV_NAME})
    assert p.returncode == 0, p.stderr
    assert str(base / "envs" / ENV_NAME) in p.stdout


def test_a_genuinely_missing_env_still_fails_with_the_places_it_looked():
    """Discovery must not become "always succeeds": a missing verifier is a real
    env problem (exit 2 = no verdict), and the message has to be actionable."""
    p = _run_check_env({"HOME": "/nonexistent", "PATH": BARE_PATH,
                        "SWEBENCH_NAGINI_VERIFIER_ENV": ENV_NAME})
    assert p.returncode == 2
    assert "not found" in p.stderr
    assert "looked for bin/nagini under" in p.stderr
    assert "/nonexistent/anaconda3" in p.stderr   # names the candidates tried


def test_check_env_does_not_run_a_verification(tmp_path):
    """`--check-env` is a startup probe, so it must not pay for a verification:
    a supervisor runs it before every launch decision."""
    prefix = _fake_env(tmp_path / "p")
    (prefix / "bin" / "nagini").write_text("#!/bin/sh\nexit 99\n")  # would fail
    p = _run_check_env({"HOME": "/nonexistent", "PATH": BARE_PATH,
                        "SWEBENCH_NAGINI_VERIFIER_PREFIX": str(prefix)})
    assert p.returncode == 0, "the stub verifier must not have been invoked"


# ---- 2. the drivers put the toolchain back on PATH ----

def test_driver_env_puts_this_interpreter_on_path():
    """`python` inside an agent's shell must mean the interpreter the drivers run
    under. Under a minimal PATH there is no `python` at all, and every command an
    agent is asked to run fails for a reason unrelated to the cell."""
    from pbt_port_fleet import _env
    env = _env("swe_bench_verified", "benchmark-verified")
    entries = env["PATH"].split(os.pathsep)
    assert str(Path(sys.executable).parent) in entries
    assert str(Path.home() / ".elan" / "bin") in entries
    assert str(Path.home() / ".local" / "bin") in entries
