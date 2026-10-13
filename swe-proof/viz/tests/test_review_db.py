# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Every page reads a comment thread, so the review DB is on the hot path.

The database sits beside the corpus, which is a network filesystem in any
deployment where the corpus does not fit on one disk, and SQLite's file locks
there are not a local futex: two connections contending for the SAME read each
wait for an NFS lock retry, tens of seconds apiece. `instance_page` calls
`threads_for`, so that is the latency of the whole site as soon as a second
reviewer clicks anything.

So the invariant is structural, not a stopwatch: however many readers there are,
there is ONE connection. These tests assert that, and that the connection still
follows `paths.REVIEW_DB` when it moves -- which is what every other test in this
directory relies on to get a scratch database.
"""
import sqlite3
import tempfile
import threading
from pathlib import Path

import pytest

from backend import comments, paths


@pytest.fixture(autouse=True)
def _own_database():
    """Every test here repoints `paths.REVIEW_DB`; put it back afterwards.

    Module-level state, so leaving it moved would hand the next test file a
    database it never wrote to -- and the sibling files set theirs at import
    time, which has already happened by the time these run.
    """
    was, cached = paths.REVIEW_DB, comments._CACHED
    yield
    paths.REVIEW_DB, comments._CACHED = was, cached


def _fresh_db(tmp_path, name="review.sqlite"):
    paths.REVIEW_DB = tmp_path / name
    comments.init_db()
    return paths.REVIEW_DB


def test_one_connection_serves_every_caller(tmp_path):
    _fresh_db(tmp_path)
    with comments.db() as a:
        pass
    with comments.db() as b:
        pass
    assert a is b


def test_concurrent_readers_share_the_one_connection(tmp_path, monkeypatch):
    """N concurrent readers must open the database once, not N times.

    Counting `sqlite3.connect` rather than timing the reads: the cost this
    guards against is paid by the filesystem the DB happens to sit on, so a
    local-disk test run would pass a timing assertion no matter how many
    connections it opened.
    """
    _fresh_db(tmp_path)
    comments.add_comment("verified", "lean", "a__a-1", "me", "hello")

    opened = []
    real = sqlite3.connect

    def counted(*args, **kwargs):
        opened.append(args[0])
        return real(*args, **kwargs)

    monkeypatch.setattr(comments.sqlite3, "connect", counted)
    # Drop the cached connection so this run has to open exactly one.
    comments._CACHED = None

    seen = []
    barrier = threading.Barrier(8)

    def reader():
        barrier.wait()
        seen.append(comments.threads_for("verified", "lean", "a__a-1"))

    threads = [threading.Thread(target=reader) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(opened) == 1, f"opened {len(opened)} connections for 8 readers"
    assert len(seen) == 8
    assert all(len(s) == 1 and s[0]["body"] == "hello" for s in seen)


def test_the_connection_follows_the_configured_path(tmp_path):
    """A moved `paths.REVIEW_DB` reopens rather than reading the old file."""
    first = _fresh_db(tmp_path, "first.sqlite")
    comments.add_comment("verified", "lean", "a__a-1", "me", "in the first db")
    assert len(comments.threads_for("verified", "lean", "a__a-1")) == 1

    second = _fresh_db(tmp_path, "second.sqlite")
    assert second != first
    assert comments.threads_for("verified", "lean", "a__a-1") == []
    comments.add_comment("verified", "lean", "a__a-1", "me", "in the second db")

    paths.REVIEW_DB = first
    rows = comments.threads_for("verified", "lean", "a__a-1")
    assert [r["body"] for r in rows] == ["in the first db"]


def test_a_failed_write_leaves_the_shared_connection_usable(tmp_path):
    """The connection outlives the request, so a raising caller must not park a
    transaction on it -- the next reader would then be reading inside it."""
    _fresh_db(tmp_path)
    comments.add_comment("verified", "lean", "a__a-1", "me", "kept")
    try:
        with comments.db() as c:
            c.execute("INSERT INTO comments(instance_id,author,body,created_at) "
                      "VALUES(?,?,?,?)", ("a__a-1", "me", "rolled back", 1.0))
            raise RuntimeError("the route raised after writing")
    except RuntimeError:
        pass
    bodies = [r["body"] for r in comments.threads_for("verified", "lean", "a__a-1")]
    assert bodies == ["kept"]


def test_pages_do_not_reopen_the_db_per_request(tmp_path, monkeypatch):
    """The route-level statement of the same invariant, over the real app."""
    paths.REVIEW_DB = Path(tempfile.mkdtemp()) / "routes.sqlite"
    comments.init_db()
    comments._CACHED = None

    opened = []
    real = sqlite3.connect
    monkeypatch.setattr(comments.sqlite3, "connect",
                        lambda *a, **k: (opened.append(a[0]), real(*a, **k))[1])

    from starlette.testclient import TestClient
    from backend.app import app
    client = TestClient(app)
    for _ in range(3):
        client.get("/comments")
    assert len(opened) == 1
