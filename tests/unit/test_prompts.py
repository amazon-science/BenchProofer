# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""How a template includes a rules file: its own library's, or the one every library shares."""

from __future__ import annotations

import calendar
import re
import sys
import time
from collections.abc import Iterator
from pathlib import Path

import pytest

from benchproofer.audit.prompts import LIBRARY as AUDIT
from benchproofer.config import Settings
from benchproofer.core import prompts
from benchproofer.core.prompts import RULES, SHARED, Library
from benchproofer.core.task import Task
from benchproofer.errors import BenchproofError
from benchproofer.formalize.prompts import LIBRARY as FORMALIZE
from benchproofer.registries import BACKENDS

#: Every library's templates, and every backend's guidance, by where they are written.
WRITTEN = {
    **{
        f"{library.package}/{name}": library.template(name)
        for library in (SHARED, AUDIT, FORMALIZE)
        for name in library.names()
    },
    **{f"{name} guidance": BACKENDS.get(name).guidance() for name in BACKENDS.names()},
}


@pytest.fixture
def packages(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """Two template packages on the import path, one of them standing in for the shared one."""
    monkeypatch.syspath_prepend(str(tmp_path))
    yield tmp_path
    for name in [name for name in sys.modules if name.startswith(("lane_", "common_"))]:
        del sys.modules[name]


def _package(root: Path, name: str, templates: dict[str, str]) -> Library:
    directory = root / name / "templates"
    directory.mkdir(parents=True)
    (root / name / "__init__.py").write_text("")
    for template, text in templates.items():
        (directory / f"{template}.md").write_text(text)
    return Library(name)


def test_a_template_includes_its_own_rules_before_the_shared_ones(
    packages: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    shared = _package(
        packages,
        "common_a",
        {"held-rules": "Held by everyone.", "domain-rules": "Shared domain rule."},
    )
    monkeypatch.setattr(prompts, "SHARED", shared)
    lane = _package(
        packages,
        "lane_a",
        {"ask": "$held_rules\n\n$domain_rules\n\n$tail", "held-rules": "Held by this auditor."},
    )

    rendered = lane.render("ask", tail="The end.")

    assert rendered == "Held by this auditor.\n\nShared domain rule.\n\nThe end.\n"


def test_a_rules_file_may_include_another(
    packages: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    shared = _package(
        packages,
        "common_b",
        {"outer-rules": "Outer, then: $inner_rules", "inner-rules": "the inner rule."},
    )
    monkeypatch.setattr(prompts, "SHARED", shared)
    lane = _package(packages, "lane_b", {"ask": "$outer_rules"})

    assert lane.render("ask") == "Outer, then: the inner rule.\n"
    assert shared.rules("outer") == "Outer, then: the inner rule."


def test_a_rules_file_no_library_ships_is_an_error(
    packages: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(prompts, "SHARED", _package(packages, "common_c", {"x-rules": "x"}))
    lane = _package(packages, "lane_c", {"ask": "$missing_rules"})

    with pytest.raises(BenchproofError, match="missing-rules"):
        lane.render("ask")


def test_a_rules_file_with_fields_of_its_own_is_the_one_its_caller_renders(
    packages: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The template is not rendered again without them, which would fail for want of one."""
    shared = _package(packages, "common_d", {"timed-rules": "Stops after $limit seconds."})
    monkeypatch.setattr(prompts, "SHARED", shared)
    lane = _package(packages, "lane_d", {"ask": "$timed_rules"})

    timed = shared.render("timed-rules", limit="30").rstrip()

    assert lane.render("ask", timed_rules=timed) == "Stops after 30 seconds.\n"
    with pytest.raises(BenchproofError, match="limit"):
        lane.render("ask")


def test_the_tools_are_described_with_the_run_s_limits_and_the_session_s_clock(
    settings: Settings, coin_change: Task
) -> None:
    """Each verb, where it runs, what it prints and when it stops; the shell; the clock.

    A program's limit is the run's or the task's own, whichever is shorter, as the oracle
    takes it, and one shell command's is the run's program budget or the session's.
    """
    from benchproofer.core.scripts import tools_rules

    run = settings.model_copy(
        update={"oracle_timeout_s": 3600, "harness_timeout_s": 1200, "verify_timeout_s": 300}
    )
    task = coin_change.model_copy(
        update={"oracle": coin_change.oracle.model_copy(update={"timeout_s": 1800})}
    )
    lean = BACKENDS.get("lean4")
    before = time.time()

    told = _flat(tools_rules(run, task, lean, session_s=9000, check=True))

    for verb in ("./tools verify FILE", "./tools try FILE", "./tools fuzz FILE", "./tools run"):
        assert verb in told, verb
    assert "`./check`" in told and "`--only GATE`" in told
    # `./check` is a repair's alone, and no other session is told of it.
    assert "`./check`" not in tools_rules(run, task, lean, session_s=9000)
    checker = f"{lean.budget(300):.0f}"
    assert f"The checker stops on a file after {checker} seconds." in told
    # What `verify` prints of a proof's completeness is the backend's to say.
    assert _flat(lean.closure_note) in told
    assert "proof is complete" not in _flat(
        tools_rules(run, task, BACKENDS.get("nagini"), session_s=9000)
    )
    assert "stops FILE after 1800 seconds." in told and "after 1200 seconds" in told
    assert "one still running after 3600 seconds is stopped" in told
    assert "FILE is sent alone, as `/bp/<its name>`" in told and "`scratch/` included" in told
    assert "`settings.configure(...)`" in told and "with the golden patch applied" in told
    assert "keeps its working directory from one call to the next" in told
    assert "which `$TMPDIR` names" in told and "`date -u`" in told
    started = re.search(r"started at (\S+ \S+) UTC and is stopped at (\S+ \S+) UTC", told)
    assert started is not None and "150 minutes later" in told
    opened, stopped = (
        calendar.timegm(time.strptime(stamp, "%Y-%m-%d %H:%M:%S")) for stamp in started.groups()
    )
    assert int(before) - 1 <= opened <= time.time() and stopped - opened == 9000


def _flat(text: str) -> str:
    return " ".join(text.split())


@pytest.mark.parametrize("name", [name for name in SHARED.names() if name.endswith(RULES)])
def test_a_shared_rule_is_written_in_one_file_and_included_where_it_is_stated(
    name: str,
) -> None:
    """No other template and no backend's guidance carries a sentence of it."""
    own = f"{SHARED.package}/{name}"
    sentences = [
        sentence
        for sentence in re.split(r"(?<=[.:])\s+", _flat(re.sub(r"\$\w+", "", WRITTEN[own])))
        if len(sentence) > 60
    ]
    assert sentences
    for where, text in WRITTEN.items():
        if where != own:
            flat = _flat(text)
            assert [sentence for sentence in sentences if sentence in flat] == [], where
    include = re.compile(rf"\$\{{?{name.removesuffix(RULES)}_rules\b")
    assert [where for where, text in WRITTEN.items() if include.search(text)]
