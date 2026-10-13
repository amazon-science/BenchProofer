# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Ingestion: what a task is called, and where that files it.

The suite name is not cosmetic. It is the directory a bundle lives under and the
argument every later command filters on, so a task filed under a name the user did
not expect is a task `formalize` cannot find.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from benchproofer.config import Settings
from benchproofer.errors import BenchmarkError
from benchproofer.pipeline.ingest import ingest, load_tasks


def write(path: Path, *rows: dict[str, Any]) -> str:
    """Write rows in the shape the `jsonl` adapter reads."""
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
    return str(path)


def test_the_name_extra_files_tasks_that_do_not_name_a_suite(
    settings: Settings, tmp_path: Path
) -> None:
    source = write(tmp_path / "tasks.jsonl", {"task_id": "one", "statement": "do a thing"})

    result = ingest("jsonl", settings, extras={"source": source, "name": "demo"})

    assert result.suites == ("demo",)
    assert (settings.bundle_root / "demo" / "one" / "task.json").is_file()
    assert [task.task_id for task in load_tasks(settings, benchmark="demo")] == ["one"]


def test_a_row_that_names_its_own_suite_keeps_it(settings: Settings, tmp_path: Path) -> None:
    """One file may hold tasks of several suites, so the row wins over the default.

    `suites` is what reports that, because otherwise the only way to learn where a
    task landed is to look on disk.
    """
    source = write(
        tmp_path / "tasks.jsonl",
        {"task_id": "one", "statement": "do a thing"},
        {"task_id": "two", "statement": "do another", "benchmark": "elsewhere"},
    )

    result = ingest("jsonl", settings, extras={"source": source, "name": "demo"})

    assert result.suites == ("demo", "elsewhere")
    assert (settings.bundle_root / "elsewhere" / "two" / "task.json").is_file()


def test_without_a_name_the_file_stem_is_the_suite(settings: Settings, tmp_path: Path) -> None:
    source = write(tmp_path / "my-suite.jsonl", {"task_id": "one", "statement": "do a thing"})

    assert ingest("jsonl", settings, extras={"source": source}).suites == ("my-suite",)


def test_a_row_missing_a_required_field_says_which_line(
    settings: Settings, tmp_path: Path
) -> None:
    source = write(
        tmp_path / "tasks.jsonl",
        {"task_id": "one", "statement": "do a thing"},
        {"task_id": "two"},
    )

    with pytest.raises(BenchmarkError, match=r"tasks\.jsonl:2: missing 'statement'"):
        ingest("jsonl", settings, extras={"source": source})


def test_ingesting_again_reuses_what_is_already_frozen(
    settings: Settings, tmp_path: Path
) -> None:
    """Frozen inputs are the record a bundle was judged against, so they stand."""
    source = write(tmp_path / "tasks.jsonl", {"task_id": "one", "statement": "do a thing"})
    ingest("jsonl", settings, extras={"source": source})
    frozen = settings.bundle_root / "tasks" / "one" / "task.json"
    before = frozen.read_text(encoding="utf-8")

    write(tmp_path / "tasks.jsonl", {"task_id": "one", "statement": "do something else"})
    again = ingest("jsonl", settings, extras={"source": source})

    assert again.reused == 1
    assert frozen.read_text(encoding="utf-8") == before
    assert ingest("jsonl", settings, extras={"source": source}, refresh=True).reused == 0
    assert frozen.read_text(encoding="utf-8") != before
