# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The three corpus-wide release checks, on the parts that bind them to ONE
benchmark rather than to the one they were pointed at.

`battery_integrity.py`, `audit_freshness.py` and `pbt_audit_completeness.py` are
release checks (release_gate.CHECKS `batteries`, `audit-freshness`,
`audit-complete`), and the release claim about them is that a second benchmark is
a registry entry, not a scatter of edits. Two ways that was false, both of them
quiet:

  * `battery_integrity` spawns one subprocess per battery and told each one the
    corpus was `<repo>/benchmark-verified`, whatever `--benchmark-dir` said: it
    walked the tree it was pointed at while naming another one to every battery
    in it. No battery shipped today reads that variable at import, so nothing
    failed -- which is the whole problem with a check that misreports its own
    inputs.
  * every tool with a `--benchmark-dir` flag hardcoded `default="benchmark-verified"`
    and never read `SBU_BENCHMARK_DIR`, so a caller who exported the variable and
    left the flag off measured the shipped corpus: `battery_integrity.py` reported
    `ok=500 broken=0` while pointed at a 1-cell corpus. The default now comes from
    `corpus_root.default_benchmark_dir`, one definition for all 14 tools.
  * each of the three carried its own copy of the gated backend tuple, in two
    different orders, so "which backends does the release cover" had three
    places to keep in step and a fourth proof backend would have had to be added
    to a list none of them named. It now comes from
    `backends.registry.GATED_BACKENDS`.

The backend test ties that constant to the GATE layer rather than to another
list: a name is release-gated exactly when the proof gates run on it, and
`gates/verify.py applies_to` is where that is declared.
"""
from __future__ import annotations

import argparse
import importlib
import os
import re
import subprocess
import sys
from pathlib import Path

import audit_freshness
import battery_integrity
import green_check
import pbt_audit_completeness
import pytest

from swebench_unified import corpus_root
from swebench_unified.backends.registry import BACKENDS, GATED_BACKENDS
from tracked_sources import pipeline_sources

ROOT = Path(__file__).resolve().parents[1]

# A battery that reports what corpus it was told about instead of asserting
# anchors, so the subprocess environment is the only thing under test.
BATTERY = """
import os
SPEC_TESTS = [os.environ["SBU_BENCHMARK_DIR"]]
assert SPEC_TESTS[0] == os.environ["EXPECTED_BENCHMARK_DIR"], SPEC_TESTS[0]
"""


def _bundle(tmp_path: Path) -> Path:
    cell = tmp_path / "some__instance-1" / "nagini"
    cell.mkdir(parents=True)
    (cell / "properties.py").write_text(BATTERY)
    return cell


def test_the_battery_subprocess_is_told_the_corpus_it_was_pointed_at(tmp_path,
                                                                    monkeypatch):
    """`--benchmark-dir` governs SBU_BENCHMARK_DIR for the import subprocess."""
    bench = tmp_path
    monkeypatch.setenv("EXPECTED_BENCHMARK_DIR", str(bench))
    ok, detail = battery_integrity.import_one(_bundle(bench), sys.executable, bench)
    assert ok, detail
    # The battery echoes what it was told, so this is the value that arrived.
    assert detail == "SPEC_TESTS=1"


def test_that_assertion_is_not_vacuous(tmp_path, monkeypatch):
    """The control: the same battery FAILS when the environment names a
    different corpus, which is what the old hardcoded value made every run do on
    any benchmark but one."""
    bench = tmp_path
    monkeypatch.setenv("EXPECTED_BENCHMARK_DIR", str(ROOT / "benchmark-verified"))
    ok, detail = battery_integrity.import_one(_bundle(bench), sys.executable, bench)
    assert not ok
    assert "AssertionError" in detail


def test_the_battery_subprocess_inherits_the_active_benchmark(tmp_path, monkeypatch):
    """SBU_BENCHMARK is passed through and never re-defaulted here.

    `benchmarks.DEFAULT_BENCHMARK` owns that default, and a checker carrying its
    own copy is how a tool ends up disagreeing with the pipeline it checks. Both
    halves: a caller's value arrives, and no value is invented when the caller
    set none (this tool used to inject `swe_bench_verified`).
    """
    bench = tmp_path
    monkeypatch.setenv("EXPECTED_BENCHMARK_DIR", str(bench))
    cell = _bundle(bench)
    (cell / "properties.py").write_text(
        BATTERY + "\nassert os.environ['SBU_BENCHMARK'] == 'swe_bench_pro_python'\n")

    monkeypatch.setenv("SBU_BENCHMARK", "swe_bench_pro_python")
    ok, detail = battery_integrity.import_one(cell, sys.executable, bench)
    assert ok, detail

    monkeypatch.delenv("SBU_BENCHMARK", raising=False)
    ok, detail = battery_integrity.import_one(cell, sys.executable, bench)
    assert not ok and "KeyError" in detail, detail


def test_the_three_checks_read_one_gated_backend_list():
    """One definition, in the module that owns the backend vocabulary."""
    assert battery_integrity.GATED_BACKENDS is GATED_BACKENDS
    assert pbt_audit_completeness.GATED_BACKENDS is GATED_BACKENDS
    # `audit_freshness` re-exports it under the short name `stale_fail_triage`
    # imports; that alias must stay a binding, not a copy.
    assert audit_freshness.GATED is GATED_BACKENDS


def test_gated_means_the_proof_gates_run_on_it():
    """Not another list: the release-gated set is the set the proof gates apply
    to, and `ears` is excluded because it has no verifier -- the verified corpus
    ships ears bundles that would otherwise read as unjudged forever."""
    from swebench_unified.gates import verify as g_verify

    assert set(GATED_BACKENDS) == set(g_verify.applies_to)
    assert set(GATED_BACKENDS) < set(BACKENDS)          # a strict subset, spelled right
    assert "ears" not in GATED_BACKENDS


def test_audit_freshness_writes_nothing_the_caller_did_not_name():
    """`--out` used to default to a path under the gitignored `experiments/`
    tree, so the check's first act on a fresh clone was to create one."""
    args = audit_freshness._argparser().parse_args([])
    assert args.out == ""


def test_green_classify_returns_the_pair_audit_freshness_unpacks(tmp_path):
    """`audit_freshness` reads greenness by unpacking `(verdict, why)` -- the
    contract every one of green_check.classify's return paths satisfies. It used
    to guard that with an isinstance() fallback onto a bare string and a set of
    verdict spellings ("ok", "true") the classifier never emits."""
    cell = tmp_path / "iid" / "nagini"
    cell.mkdir(parents=True)
    for text, expected in (("", "NORESULT"),        # no meta.json at all
                           ("{}", "NOTGREEN"),      # no gates recorded
                           ("not json", "NOTGREEN")):
        if text:
            (cell / "meta.json").write_text(text)
        got = green_check.classify(cell, "nagini", "iid")
        assert isinstance(got, tuple) and len(got) == 2
        assert got[0] == expected
        assert all(isinstance(part, str) for part in got)


# --------------------------------------------------- the corpus a tool measures
# Every tool that names a corpus root on its command line: its module, the flag,
# and whatever else that tool requires before it will parse at all.
# `pbt_audit_completeness.py` is absent on purpose: it has no flag and reads
# `paths.TASKS_ROOT` through a lazy import inside `main`, which is the same
# precedence by another route.
ROOT_FLAG_TOOLS = (
    ("audit_freshness", "--benchmark-dir", ()),
    ("audit_recheck", "--benchmark-dir", ("--lane-file", "/dev/null")),
    ("audit_refresh", "--benchmark-dir", ("--lane-file", "/dev/null")),
    ("battery_integrity", "--benchmark-dir", ()),
    ("check_stamp_freshness", "--benchmark-dir", ()),
    ("pbt_audit_fleet", "--benchmark-dir", ("--backend", "velvet")),
    ("pbt_certify", "--dir", ()),
    ("pbt_coverage", "--benchmark-dir", ("--backend", "velvet")),
    ("pbt_port_fleet", "--benchmark-dir", ("--backend", "velvet")),
    ("pbt_static_audit", "--benchmark-dir", ()),
    ("release_gate", "--benchmark-dir", ()),
    ("spec_repair_fleet", "--benchmark-dir", ("--lane-file", "/dev/null")),
    ("stale_fail_triage", "--benchmark-dir", ()),
    ("verdict_prose_lint", "--benchmark-dir", ()),
)


class _ParserBuilt(Exception):
    """Raised in place of `parse_args`, so no tool walks a corpus here."""


def _root_parser(module_name: str, monkeypatch) -> argparse.ArgumentParser:
    """The tool's OWN parser, captured as `main()` hands it the command line.

    All but one of these tools build their parser inside `main()`, so this is what
    lets the test read a real default rather than assert on source text -- which
    would pass for a default that is the right string for the wrong reason.
    """
    real_parse = argparse.ArgumentParser.parse_args
    captured: list[argparse.ArgumentParser] = []

    def parse(self, *a, **kw):
        captured.append(self)
        raise _ParserBuilt

    monkeypatch.setattr(argparse.ArgumentParser, "parse_args", parse)
    with pytest.raises(_ParserBuilt):
        importlib.import_module(module_name).main()
    monkeypatch.setattr(argparse.ArgumentParser, "parse_args", real_parse)
    return captured[0]


def _dest(flag: str) -> str:
    return flag.lstrip("-").replace("-", "_")


@pytest.mark.parametrize("tool,flag,extra", ROOT_FLAG_TOOLS)
def test_the_corpus_root_default_is_the_one_the_environment_names(tool, flag, extra,
                                                                 monkeypatch):
    """SBU_BENCHMARK_DIR beats the shipped default. A tool that ignores it walks a
    tree the caller did not name and reports a clean bill of health about it."""
    monkeypatch.setenv("SBU_BENCHMARK_DIR", "/tmp/corpus-the-caller-exported")
    args = _root_parser(tool, monkeypatch).parse_args(list(extra))
    assert getattr(args, _dest(flag)) == "/tmp/corpus-the-caller-exported"


@pytest.mark.parametrize("tool,flag,extra", ROOT_FLAG_TOOLS)
def test_an_explicit_flag_beats_the_environment(tool, flag, extra, monkeypatch):
    """The top rung of the precedence, on every tool rather than by argparse's
    reputation: the flag is what a driver passes and it has to win."""
    monkeypatch.setenv("SBU_BENCHMARK_DIR", "/tmp/corpus-the-caller-exported")
    args = _root_parser(tool, monkeypatch).parse_args(
        [flag, "/tmp/corpus-named-on-the-line", *extra])
    assert getattr(args, _dest(flag)) == "/tmp/corpus-named-on-the-line"


@pytest.mark.parametrize("tool,flag,extra", ROOT_FLAG_TOOLS)
def test_with_no_environment_the_default_is_the_generic_root(tool, flag, extra,
                                                             monkeypatch):
    """The bottom rung: with nothing exported the default is `benchmark/`, not one
    corpus this repository happens to ship."""
    monkeypatch.delenv("SBU_BENCHMARK_DIR", raising=False)
    args = _root_parser(tool, monkeypatch).parse_args(list(extra))
    assert getattr(args, _dest(flag)) == corpus_root.DEFAULT_BENCHMARK_DIR


def test_the_default_is_the_root_paths_uses():
    """One spelling of `benchmark`. Two would diverge the moment either moved, and
    `paths.TASKS_ROOT` is what the constructed bundles actually land under.

    In a subprocess with the variable cleared, because `paths` binds TASKS_ROOT at
    import and this suite may run with a corpus exported.
    """
    env = {k: v for k, v in os.environ.items() if k != "SBU_BENCHMARK_DIR"}
    env["PYTHONPATH"] = str(ROOT / "src")
    out = subprocess.run(
        [sys.executable, "-c",
         "from swebench_unified import corpus_root, paths;"
         "print(paths.TASKS_ROOT.name, corpus_root.DEFAULT_BENCHMARK_DIR)"],
        capture_output=True, text=True, env=env, check=True).stdout.split()
    assert out[0] == out[1] == corpus_root.DEFAULT_BENCHMARK_DIR


def test_reading_the_default_binds_no_corpus_at_import():
    """`corpus_root` may not import `paths`.

    `release_gate.py` and `benchmark_smoke.py` export the roots AFTER parsing, and
    `paths` binds TASKS_ROOT and the dataset location at import -- so a tool whose
    argparse default reached through `paths` would fix those bindings while
    building its parser, one step before the flags that set them were read.
    """
    out = subprocess.run(
        [sys.executable, "-c",
         "import sys; import swebench_unified.corpus_root;"
         "print(sorted(m for m in sys.modules if m.startswith('swebench_unified')))"],
        capture_output=True, text=True, check=True,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")}).stdout.strip()
    assert out == "['swebench_unified', 'swebench_unified.corpus_root']"


def _experiments_root(value: str | None) -> str:
    """`paths.EXPERIMENTS_ROOT` as a fresh interpreter computes it. A subprocess
    for the same reason as above: the root is bound at import."""
    env = {k: v for k, v in os.environ.items() if k != "SBU_EXPERIMENTS_DIR"}
    env["PYTHONPATH"] = str(ROOT / "src")
    if value is not None:
        env["SBU_EXPERIMENTS_DIR"] = value
    return subprocess.run(
        [sys.executable, "-c",
         "from swebench_unified import paths; print(paths.EXPERIMENTS_ROOT)"],
        capture_output=True, text=True, env=env, check=True).stdout.strip()


def test_the_run_output_root_can_leave_the_checkout():
    """Every root a clone READS is relocatable; this is the one it WRITES, and it
    could only be the checkout. A read-only or network-mounted clone cannot host
    construction logs, eval artifacts and the official harness's cwd, and there
    was no variable to move them.

    Same rule as the corpus root: absolute is used as given, a bare name is taken
    under the checkout, and with nothing exported the default does not move.
    """
    default = "experiments"     # named, not joined: the guard below matches joins
    assert _experiments_root("/tmp/sbu-run-output") == "/tmp/sbu-run-output"
    assert _experiments_root("scratch-runs") == str(ROOT / "scratch-runs")
    assert _experiments_root(None) == str(ROOT / default)


def test_the_port_smoke_driver_contains_every_root_the_pipeline_reads():
    """`benchmark_smoke.py --root DIR` promises DIR holds everything the run
    touches, which is what lets a port be checked against a clone it may not
    write into. The promise is only as good as the list, so the list is derived
    from the modules that DEFINE the roots rather than restated: a root added
    there and not there stays in the checkout, and the smoke run still passes.
    """
    import benchmark_smoke

    contained = benchmark_smoke.contained_roots(Path("/tmp/port-root"))
    assert contained and all(v.startswith("/tmp/port-root/")
                             for v in contained.values()), contained
    declared = set()
    for mod in ("paths.py", "corpus_root.py", "benchmarks.py"):
        declared |= set(re.findall(r"SBU_[A-Z_]+(?:ROOT|DIR)",
                                   (ROOT / "src" / "swebench_unified"
                                    / mod).read_text()))
    assert declared, "no root variables found; the pattern went stale"
    assert declared <= set(contained), sorted(declared - set(contained))


def test_nothing_builds_the_run_output_root_for_itself():
    """The variable is only true if every writer derives from it. Seven sites
    across four drivers built `<repo>/experiments/<subdir>` themselves, so
    exporting it would have moved some output and silently left the rest in the
    checkout -- the failure mode being a half-populated run directory.

    Matches the path-JOIN shape only: prose and docstrings that describe the
    default layout are the documentation of it.
    """
    joins = re.compile(r'/\s*"experiments"|"experiments"\s*/')
    offenders = []
    for rel in pipeline_sources():
        p = ROOT / rel
        for n, line in enumerate(p.read_text(errors="replace").splitlines(), 1):
            # the definition itself, and tests that PATCH the attribute, are the
            # two legitimate mentions
            if "EXPERIMENTS_ROOT" in line:
                continue
            if joins.search(line):
                offenders.append(f"{rel}:{n}: {line.strip()}")
    assert not offenders, (
        "these build the run-output root themselves, so SBU_EXPERIMENTS_DIR would "
        "not move them; import paths.EXPERIMENTS_ROOT:\n" + "\n".join(offenders))
