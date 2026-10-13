# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""`--benchmark-dir` has to reach the gates, not just the existence check.

`paths.TASKS_ROOT` is read from `SBU_BENCHMARK_DIR` once at import and defaults to
`benchmark`, and `run_gates` resolves every artifact through it while taking no
root argument. So a caller that passed the flag and forgot the variable checked
`benchmark-verified/<iid>/<backend>/meta.json` existed and then measured
`benchmark/`, where nothing does: each gate recorded `model.py missing or empty`
into a brand-new stub tree, the cell's real record was never touched, and the
driver struck it off its list anyway.

The failure is silent in the only direction that matters -- it produces records
and a nonzero exit, so it reads as a re-stamp that ran, not as one that looked in
the wrong place. These tests pin the export and the refusal.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from restamp_gate import _export_benchmark_dir

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("argv", [
    pytest.param(["--benchmark-dir", "benchmark-verified"], id="separate_value"),
    pytest.param(["--benchmark-dir=benchmark-verified"], id="equals_form"),
])
def test_the_flag_is_exported(monkeypatch, argv):
    monkeypatch.delenv("SBU_BENCHMARK_DIR", raising=False)
    _export_benchmark_dir(["x", *argv])
    assert os.environ["SBU_BENCHMARK_DIR"] == "benchmark-verified"


def test_an_agreeing_variable_is_left_alone(monkeypatch):
    """A caller that sets both is the common case and must not raise. Compared as
    paths, so a trailing slash is agreement rather than a conflict."""
    monkeypatch.setenv("SBU_BENCHMARK_DIR", "benchmark-verified/")
    _export_benchmark_dir(["x", "--benchmark-dir", "benchmark-verified"])


def test_a_disagreeing_variable_is_refused(monkeypatch):
    """Not silently overridden in either direction: the two roots would be read by
    two different halves of this script, so whichever one wins the caller asked
    for something it did not get, and that is the bug to report rather than to
    guess at."""
    monkeypatch.setenv("SBU_BENCHMARK_DIR", "benchmark")
    with pytest.raises(SystemExit) as e:
        _export_benchmark_dir(["x", "--benchmark-dir", "benchmark-verified"])
    assert "disagrees" in str(e.value)


def test_no_flag_leaves_the_environment_untouched(monkeypatch):
    """`--benchmark-dir` is required by the parser, but the pre-scan runs before
    the parser exists -- `--help` and a usage error both reach it first."""
    monkeypatch.setenv("SBU_BENCHMARK_DIR", "benchmark-verified")
    _export_benchmark_dir(["x", "--gates", "G-LEAK"])
    assert os.environ["SBU_BENCHMARK_DIR"] == "benchmark-verified"


def test_the_gates_resolve_against_the_flag_end_to_end():
    """The property the unit tests above only approximate: after importing the
    script with the flag alone, the root `run_gates` uses is the flag's."""
    prog = (
        "import sys, os\n"
        "sys.argv = ['restamp_gate.py', '--benchmark-dir', 'benchmark-verified']\n"
        f"sys.path.insert(0, {str(ROOT / 'scripts')!r})\n"
        f"sys.path.insert(0, {str(ROOT / 'src')!r})\n"
        "import restamp_gate\n"
        "from swebench_unified import paths\n"
        "print(paths.TASKS_ROOT.name)\n"
    )
    env = {k: v for k, v in os.environ.items() if k != "SBU_BENCHMARK_DIR"}
    out = subprocess.run([sys.executable, "-c", prog], cwd=ROOT, env=env,
                         capture_output=True, text=True, timeout=300)
    assert out.returncode == 0, out.stderr[-2000:]
    assert out.stdout.strip().splitlines()[-1] == "benchmark-verified"
