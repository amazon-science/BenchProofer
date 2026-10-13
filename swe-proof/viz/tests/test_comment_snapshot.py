# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Review history has to survive a clone, so the snapshot round-trips.

`viz/data/review.sqlite` is gitignored operational state and the committable form
is `viz/review_comments.json`. An export with no load is a one-way door: the file
is in the repository and every board still renders as never reviewed. These tests
hold the round trip, and the two properties that make loading safe to run against
a database that already has local review on it -- it ADDS, and running it twice
adds nothing.
"""
from __future__ import annotations

import json
from pathlib import Path

import export_comments
import pytest
from backend import comments, paths


@pytest.fixture(autouse=True)
def _own_database(tmp_path):
    was, cached = paths.REVIEW_DB, comments._CACHED
    paths.REVIEW_DB = tmp_path / "review.sqlite"
    comments._CACHED = None
    comments.init_db()
    yield
    paths.REVIEW_DB, comments._CACHED = was, cached


def _thread(bm="verified", bk="nagini", iid="astropy__astropy-12907"):
    root = comments.add_comment(bm, bk, iid, "reviewer", "the spec elides the guard",
                                flag="spec")
    comments.add_comment(bm, bk, iid, "maintainer", "repaired in the regate",
                         parent_id=root)
    return root


def _snapshot(tmp_path) -> Path:
    out = tmp_path / "snap.json"
    assert export_comments.main(["--out", str(out)]) == 0
    return out


def test_a_snapshot_loads_back_into_an_empty_database(tmp_path):
    _thread()
    snap = _snapshot(tmp_path)
    before = comments.export_all()

    paths.REVIEW_DB = tmp_path / "clone.sqlite"      # the reader's fresh clone
    comments._CACHED = None
    comments.init_db()
    assert comments.export_all() == []
    assert export_comments.main(["--load", str(snap)]) == 0

    after = comments.export_all()
    assert len(after) == len(before) == 2
    fields = ("benchmark", "backend", "instance_id", "author", "body", "flag",
              "status", "created_at")
    assert [{k: r[k] for k in fields} for r in after] == \
           [{k: r[k] for k in fields} for r in before]
    # and the thread structure survives, keyed on the ids this database assigned
    root = [r for r in after if r["parent_id"] is None]
    reply = [r for r in after if r["parent_id"] is not None]
    assert len(root) == 1 and len(reply) == 1
    assert reply[0]["parent_id"] == root[0]["id"]


def test_loading_twice_adds_nothing(tmp_path):
    _thread()
    snap = _snapshot(tmp_path)
    paths.REVIEW_DB = tmp_path / "clone.sqlite"
    comments._CACHED = None
    comments.init_db()
    export_comments.main(["--load", str(snap)])
    n = len(comments.export_all())
    export_comments.main(["--load", str(snap)])
    assert len(comments.export_all()) == n


def test_local_review_is_not_replaced(tmp_path):
    """A reader who has already commented keeps their comments."""
    _thread()
    snap = _snapshot(tmp_path)
    paths.REVIEW_DB = tmp_path / "clone.sqlite"
    comments._CACHED = None
    comments.init_db()
    mine = comments.add_comment("verified", "nagini", "astropy__astropy-12907",
                                "me", "my own note")
    export_comments.main(["--load", str(snap)])
    bodies = {r["body"] for r in comments.export_all()}
    assert "my own note" in bodies and "the spec elides the guard" in bodies
    assert any(r["id"] == mine for r in comments.export_all())


def test_the_load_reports_per_board(tmp_path, capsys):
    """Rows carry (benchmark, backend), so a snapshot spanning boards must land on
    all of them rather than on the default row."""
    _thread("verified", "nagini")
    _thread("pro", "lean", "instance_x__y-1-v2")
    snap = _snapshot(tmp_path)
    paths.REVIEW_DB = tmp_path / "clone.sqlite"
    comments._CACHED = None
    comments.init_db()
    export_comments.main(["--load", str(snap)])
    assert capsys.readouterr().out.strip().endswith("added 4, already present 0")
    boards = {(r["benchmark"], r["backend"]) for r in comments.export_all()}
    assert boards == {("verified", "nagini"), ("pro", "lean")}


@pytest.mark.parametrize("doc", ["[]", '{"threads": []}'])
def test_an_empty_snapshot_is_not_an_error(tmp_path, doc):
    p = tmp_path / "empty.json"
    p.write_text(doc)
    assert export_comments.main(["--load", str(p)]) == 0


def test_a_missing_or_malformed_snapshot_exits_nonzero(tmp_path):
    assert export_comments.main(["--load", str(tmp_path / "absent.json")]) == 1
    bad = tmp_path / "bad.json"
    bad.write_text("{not json")
    assert export_comments.main(["--load", str(bad)]) == 1
    wrong = tmp_path / "wrong.json"
    wrong.write_text(json.dumps({"threads": 3}))
    assert export_comments.main(["--load", str(wrong)]) == 1


def test_an_unusable_row_is_counted_not_inserted(tmp_path):
    """A thread with no instance_id belongs to no board; it is skipped with its
    replies rather than landing where nothing can render it."""
    p = tmp_path / "snap.json"
    p.write_text(json.dumps({"threads": [
        {"benchmark": "verified", "backend": "nagini", "instance_id": "",
         "author": "a", "body": "orphan", "created_at": 1.0,
         "replies": [{"benchmark": "verified", "backend": "nagini",
                      "instance_id": "", "author": "b", "body": "reply",
                      "created_at": 2.0}]}]}))
    assert export_comments.main(["--load", str(p)]) == 0
    assert comments.export_all() == []
