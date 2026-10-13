# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""A reader must never see a half-written record.

`meta.json` is the only record of what has been verified about a cell, it is
rewritten by several drivers at once, and every consumer reads it directly with
no lock. A plain `write_text` is a truncate followed by a write, so a reader that
lands between the two gets zero bytes for a file that is perfectly healthy -- and
a whole-corpus triage sweep that aborts on `json.loads` of one such file takes
every other cell's verdict down with it.

These tests pin both halves of the fix: writers swap the file in one step, and
the whole-corpus classifier survives a record it cannot read (reporting it
not-green, never green and never by raising).
"""
from __future__ import annotations

import json
import threading

import pytest

from swebench_unified.atomic_io import (
    read_json_or_none, write_bytes_atomic, write_json_atomic,
    write_text_atomic)


def test_write_json_atomic_round_trips(tmp_path):
    p = tmp_path / "meta.json"
    write_json_atomic(p, {"b": 1, "a": 2}, sort_keys=True)
    assert json.loads(p.read_text()) == {"a": 2, "b": 1}
    assert p.read_text().endswith("\n"), "the corpus convention is a final newline"


def test_no_temp_file_is_left_behind(tmp_path):
    """G-INTEGRITY does not allowlist the temp name, so a leftover would fail a
    released bundle. It must be gone on success AND on failure."""
    write_json_atomic(tmp_path / "meta.json", {"a": 1})
    assert [p.name for p in tmp_path.iterdir()] == ["meta.json"]

    with pytest.raises(TypeError):
        write_json_atomic(tmp_path / "meta.json", {"a": {1, 2}})  # not JSON
    assert [p.name for p in tmp_path.iterdir()] == ["meta.json"]
    assert json.loads((tmp_path / "meta.json").read_text()) == {"a": 1}, \
        "a failed write must leave the previous record intact"


def test_a_concurrent_reader_never_sees_a_partial_file(tmp_path):
    """The actual regression. A reader looping on the file while a writer
    rewrites it must only ever observe whole documents -- the old one or the new
    one, never a prefix and never zero bytes."""
    p = tmp_path / "meta.json"
    old = {"gates": {"G-VERIFY": {"status": "pass"}}}
    new = {"gates": {"G-VERIFY": {"status": "pass"}, "G-EQ": {"status": "pass"}}}
    write_json_atomic(p, old)

    seen, stop = [], threading.Event()

    def reader():
        while not stop.is_set():
            try:
                seen.append(json.loads(p.read_text()))
            except (ValueError, OSError) as e:  # what we are proving cannot happen
                seen.append(e)

    t = threading.Thread(target=reader, daemon=True)
    t.start()
    try:
        for i in range(300):
            write_json_atomic(p, new if i % 2 else old)
    finally:
        stop.set()
        t.join(timeout=5)

    torn = [s for s in seen if isinstance(s, Exception)]
    assert not torn, f"reader saw {len(torn)} torn read(s), e.g. {torn[0]!r}"
    assert seen, "the reader never ran, so this proved nothing"
    assert all(s in (old, new) for s in seen)


def test_write_bytes_atomic_handles_a_missing_parent(tmp_path):
    p = tmp_path / "deep" / "er" / "solution.lean"
    write_bytes_atomic(p, b"import Mathlib\n")
    assert p.read_bytes() == b"import Mathlib\n"


def test_write_text_atomic_preserves_exact_bytes(tmp_path):
    """The snapshot/restore path compares bytes, so a restore that re-encoded
    would loop forever declaring the file still wrong."""
    text = "measure: n - i + 1  # é中\n"
    p = tmp_path / "model.py"
    write_text_atomic(p, text)
    assert p.read_text() == text


def test_read_json_or_none_reports_unreadable_rather_than_raising(tmp_path):
    p = tmp_path / "meta.json"
    assert read_json_or_none(p) is None, "absent"
    p.write_text("")
    assert read_json_or_none(p) is None, "truncated"
    p.write_text('{"gates": {')
    assert read_json_or_none(p) is None, "half-written"
    p.write_text('{"gates": {}}')
    assert read_json_or_none(p) == {"gates": {}}


def test_green_check_survives_an_unreadable_meta(tmp_path):
    """The crash that aborts a whole sweep from one damaged record.

    `green_check.classify` is injected into `triage.worklist`, which runs it over
    every cell in the corpus. Raising on one cell loses every other verdict, so
    an unreadable record is NOT-green with a loud reason instead.
    """
    import green_check
    b = tmp_path / "nagini"
    b.mkdir()
    (b / "meta.json").write_text("")            # exactly what the sweep hit
    verdict, why = green_check.classify(b, "nagini", "some__instance-1")
    assert verdict == "NOTGREEN", "an unreadable record must never read as green"
    assert "unreadable" in why


def test_green_check_still_distinguishes_absent_from_unreadable(tmp_path):
    """"Never constructed" and "record damaged" are different situations and a
    scheduler acts differently on them, so they must not collapse."""
    import green_check
    b = tmp_path / "nagini"
    b.mkdir()
    assert green_check.classify(b, "nagini", "i")[0] == "NORESULT"
    (b / "meta.json").write_text("{}")
    assert green_check.classify(b, "nagini", "i") == ("NOTGREEN", "no gates recorded")
