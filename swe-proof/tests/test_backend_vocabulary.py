# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""No entry point keeps its own list of backend names.

`backends/registry.py` owns the vocabulary: `BACKENDS` is every backend that
ships, `GATED_BACKENDS` the subset the release gate covers, and each gate's
`applies_to` the subset it can judge. A CLI that spells the names into an argparse
`choices=` instead refuses a newly registered backend with "invalid choice" -- the
one failure mode that looks like the backend is broken rather than the flag being
stale, and adding a backend is meant to be a registry entry plus the files
`docs/adding_a_backend.md` lists, not a grep for string literals.

So each entry point below is asked what it actually accepts, and the expected set
is computed from the registry rather than written out here: a backend added to the
registry changes both sides at once, which is the only way this test can keep
meaning after the vocabulary grows.
"""
from __future__ import annotations

import contextlib
import io
import re
import sys
from pathlib import Path

import pytest
from swebench_unified.backends.registry import BACKENDS, GATED_BACKENDS
from tracked_sources import pipeline_sources

ROOT = Path(__file__).resolve().parents[1]


def _help_choices(main, flag: str) -> set[str]:
    """The choice set `flag` advertises, read out of the tool's own --help.

    Through the real parser rather than by importing a constant, so a tool that
    derives its list correctly but then narrows it somewhere else still fails.
    """
    buf = io.StringIO()
    argv = sys.argv
    sys.argv = ["prog", "--help"]
    try:
        with contextlib.redirect_stdout(buf), pytest.raises(SystemExit):
            main()
    finally:
        sys.argv = argv
    text = " ".join(buf.getvalue().split())
    m = re.search(rf"{re.escape(flag)} \{{([^}}]*)\}}", text)
    assert m, f"{flag} advertises no choice set; --help was:\n{text[:400]}"
    return set(m.group(1).split(","))


def _all_backends() -> set[str]:
    return set(BACKENDS)


def _gated() -> set[str]:
    return set(GATED_BACKENDS)


def _pbt_backends() -> set[str]:
    from swebench_unified.gates.pbt import applies_to
    return set(applies_to)


# (label, import path, attribute, flag, expected-set factory). The factories are
# called at test time so a registry edit moves the expectation with the code.
ENTRY_POINTS = [
    ("construct one cell", "swebench_unified.construct.build_one", "main",
     "--backend", _all_backends),
    ("construct a corpus", "swebench_unified.construct.run_all", "main",
     "--backend", _all_backends),
    ("eval driver", "swebench_unified.eval.run", "main", "--backend",
     _all_backends),
    ("regate a corpus", "regate_resume", "main", "--backends", _all_backends),
    # scoring runs a verifier, so the ungated backend cannot be asked for
    ("consumer scorer", "swebench_unified.eval.score", "main", "--backend",
     _gated),
    ("one G-PBT run", "pbt_gate", "main", "--backend", _pbt_backends),
]


@pytest.mark.parametrize("label,module,attr,flag,expected",
                         ENTRY_POINTS, ids=[e[0] for e in ENTRY_POINTS])
def test_an_entry_point_accepts_the_registry_s_backends(label, module, attr,
                                                        flag, expected):
    main = getattr(__import__(module, fromlist=[attr]), attr)
    want = expected()
    got = _help_choices(main, flag)
    assert got == want, (
        f"{label} accepts {sorted(got)} but the registry says {sorted(want)}: "
        f"a backend the registry knows would be refused as an invalid choice")


def test_the_gated_subset_is_a_subset():
    """Guard on the two expectations above being distinguishable at all: if the
    sets ever coincide, the scorer test stops carrying information and should be
    re-pointed at whatever the narrower set has become."""
    assert _gated() < _all_backends()


# The argparse shape only: a literal list of backend names in a flag
# declaration. `applies_to` tables, the registry itself and prose are all
# legitimate places for the names.
_FLAG_LIST = re.compile(r"(?:choices|default)\s*=\s*[\[(]([^\])]*)[\])]")
_NAME = re.compile(r"[\"']([a-z_]+)[\"']")


def _restated_registry_set(line: str) -> str | None:
    """The registry set this flag declaration spells out, if it spells one out.

    A NARROWER list is the tool's own scope, not a stale copy -- the PBT port
    drivers legitimately accept only the two backends they know how to port to,
    and `pbt_static_audit --backend all` means the ported pair. Only a list equal
    to a whole registry set is a restatement of it, and only that goes stale when
    a backend is registered.
    """
    m = _FLAG_LIST.search(line)
    if not m:
        return None
    names = set(_NAME.findall(m.group(1)))
    if names == set(BACKENDS):
        return "BACKENDS"
    if names == set(GATED_BACKENDS):
        return "GATED_BACKENDS"
    return None


def test_no_tracked_source_restates_a_registry_set_in_a_flag():
    offenders = []
    for rel in pipeline_sources():
        p = ROOT / rel
        for n, line in enumerate(p.read_text(errors="replace").splitlines(), 1):
            which = _restated_registry_set(line)
            if which:
                offenders.append(f"{rel}:{n}: restates {which}: {line.strip()}")
    assert not offenders, (
        "a flag restates the backend registry, so a newly registered backend "
        "would be refused as an invalid choice; import BACKENDS / "
        "GATED_BACKENDS or the gate's applies_to instead:\n"
        + "\n".join(offenders))


def test_the_guard_would_catch_a_restated_list():
    """Vacuity control, and the boundary: whole sets are caught, narrower scopes
    and computed lists are not.

    The two offending lines are ASSEMBLED from the registry rather than written
    out, for the same reason the tests above compute their expectations: a
    literal here would be a restatement of the registry in a tracked file, which
    is what the guard exists to reject, so it would flag this module.
    """
    assert _restated_registry_set(
        f'ap.add_argument("--backend", choices={sorted(BACKENDS)!r})') == "BACKENDS"
    assert _restated_registry_set(
        f"    choices={tuple(sorted(GATED_BACKENDS))!r},") == "GATED_BACKENDS"
    assert _restated_registry_set('choices=["velvet", "lean"])') is None
    assert _restated_registry_set('applies_to = ("nagini", "velvet")') is None
    assert _restated_registry_set("choices=sorted(BACKENDS))") is None
