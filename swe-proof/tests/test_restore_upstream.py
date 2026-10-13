# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The pointer a copyleft instance ships, and the script that restores its row.

`strip_copyleft.py` withholds a copyleft instance's dataset row (the issue text, the
fix patch and the test patch) and leaves `upstream.json` in its place. The pointer
must name the upstream instance and carry none of its text, and
`restore_upstream.py` must write the row back the way construction freezes it.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from strip_copyleft import COPYLEFT, ROW_FILES, pointer

ROOT = Path(__file__).resolve().parents[1]
IID = "pylint-dev__pylint-4970"
ROW = {"repo": "pylint-dev/pylint", "instance_id": IID, "base_commit": "40cc2ff",
       "patch": "diff --git a/p.py b/p.py\n", "test_patch": "diff --git a/t.py b/t.py\n",
       "problem_statement": "issue text", "hints_text": "a hint", "version": "2.10"}
TEXT = ("patch", "test_patch", "problem_statement", "hints_text")


def _restore(tmp_path: Path, rows: list[dict] | None) -> subprocess.CompletedProcess:
    corpus = tmp_path / "benchmark-verified"
    (corpus / IID).mkdir(parents=True)
    (corpus / IID / "upstream.json").write_text(json.dumps(pointer(ROW, "swe_bench_verified")))
    data = tmp_path / "data"
    if rows is not None:
        (data / "swe_bench_verified").mkdir(parents=True)
        (data / "swe_bench_verified" / "test.jsonl").write_text(
            "".join(json.dumps(r) + "\n" for r in rows))
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "restore_upstream.py"),
         "--benchmark-dir", str(corpus)],
        env=dict(os.environ, SBU_DATA_ROOT=str(data)), capture_output=True, text=True)


def test_the_pointer_names_the_instance_and_carries_none_of_its_text():
    ref = pointer(ROW, "swe_bench_verified")
    assert ref["instance_id"] == IID and ref["dataset"] == "princeton-nlp/SWE-bench_Verified"
    assert ref["license"] == COPYLEFT["pylint-dev/pylint"]
    assert ref["withheld"] == sorted(ROW_FILES)
    assert not set(TEXT) & set(ref)
    assert not any(ROW[k] in json.dumps(ref) for k in TEXT)


def test_a_restored_row_is_written_as_construction_freezes_it(tmp_path):
    done = _restore(tmp_path, [ROW])
    assert done.returncode == 0, done.stderr
    inst = tmp_path / "benchmark-verified" / IID
    assert (inst / "instance.json").read_text() == json.dumps(ROW)
    assert (inst / "patch.diff").read_text() == ROW["patch"]


def test_a_row_the_dataset_no_longer_has_is_reported(tmp_path):
    done = _restore(tmp_path, [dict(ROW, instance_id="other")])
    assert done.returncode == 1 and f"not restored: {IID}" in done.stderr
    assert not (tmp_path / "benchmark-verified" / IID / "instance.json").exists()


def test_an_unfetched_dataset_names_the_command_that_fetches_it(tmp_path):
    done = _restore(tmp_path, None)
    assert done.returncode == 1
    assert "fetch_dataset.py --benchmark swe_bench_verified" in done.stderr
