# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""SQLite-backed comments / flags / threads — the ONLY writable surface.

No admin role: every collaborator can comment, reply, flag, and toggle a
thread's status (pending/resolved). Authorship is self-asserted (name remembered
client-side). Markdown bodies are rendered through the sanitizer at display time.

Schema (single table, thread = a root comment + its replies via parent_id):
  comments(id, benchmark, backend, instance_id, parent_id, author, body, flag,
           status, created_at, resolved_by, resolved_at)
- benchmark: which benchmark row the thread was raised on (verified/pro).
- backend: which backend's board the thread was raised on (a key from
  `settings.BACKENDS`); threads are scoped per (benchmark, backend, instance).
- flag:  one of {'', 'weak-spec', 'imprecise-axiom', 'leakage', 'faithfulness',
         'other'} — only meaningful on root comments (a flag a reviewer raises).
- status: 'pending' | 'resolved' — only on root comments (the thread state).
"""
from __future__ import annotations

import sqlite3
import threading
import time
from contextlib import contextmanager

from . import paths

FLAGS = ["weak-spec", "imprecise-axiom", "leakage", "faithfulness", "other"]
MAX_BODY = 20000
MAX_AUTHOR = 80

_LOCK = threading.RLock()
_CACHED: tuple[str, sqlite3.Connection] | None = None


@contextmanager
def db():
    """The one process-wide connection, one caller at a time.

    Serialized rather than one connection per call, because the database sits
    beside the corpus and that is a network filesystem in any deployment where
    the corpus does not fit on one disk. SQLite's file locks there are not a
    local futex: two connections contending for the SAME read each wait for an
    NFS lock retry, tens of seconds apiece. Every page renders a comment thread,
    so that is the whole site's latency as soon as a second reviewer clicks
    anything. One connection behind one lock cannot conflict with itself.

    Reopened when `paths.REVIEW_DB` moves, which is how a test points it at a
    scratch file. The lock is re-entrant so that a nested use is a no-op rather
    than a deadlock; the outer `with` is then the one that commits.
    """
    global _CACHED
    with _LOCK:
        want = str(paths.REVIEW_DB)
        if _CACHED is None or _CACHED[0] != want:
            if _CACHED is not None:
                _CACHED[1].close()
            fresh = sqlite3.connect(want, timeout=15, check_same_thread=False)
            fresh.row_factory = sqlite3.Row
            fresh.execute("PRAGMA foreign_keys=ON")
            _CACHED = (want, fresh)
        c = _CACHED[1]
        try:
            yield c
            c.commit()
        except Exception:
            c.rollback()
            raise


def init_db() -> None:
    with db() as c:
        # Once per database rather than once per connection: setting the journal
        # mode takes an exclusive lock, and on a network filesystem that is the
        # expensive kind. It is a persistent property of the file, so a second
        # run of this reads it back and changes nothing.
        c.execute("PRAGMA journal_mode=WAL")
        c.execute("""
            CREATE TABLE IF NOT EXISTS comments (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                benchmark   TEXT NOT NULL DEFAULT 'pro',
                backend     TEXT NOT NULL DEFAULT 'nagini',
                instance_id TEXT NOT NULL,
                parent_id   INTEGER REFERENCES comments(id),
                author      TEXT NOT NULL,
                body        TEXT NOT NULL,
                flag        TEXT NOT NULL DEFAULT '',
                status      TEXT NOT NULL DEFAULT 'pending',
                created_at  REAL NOT NULL,
                resolved_by TEXT,
                resolved_at REAL
            )""")
        # fresh name: an older idx would make IF NOT EXISTS a no-op
        c.execute("CREATE INDEX IF NOT EXISTS idx_bm_bk_inst "
                  "ON comments(benchmark, backend, instance_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_parent ON comments(parent_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_status ON comments(status)")


def _clean(s: str, limit: int) -> str:
    return (s or "").strip()[:limit]


def add_comment(benchmark: str, backend: str, instance_id: str, author: str, body: str,
                parent_id: int | None = None, flag: str = "") -> int:
    author = _clean(author, MAX_AUTHOR) or "anonymous"
    body = _clean(body, MAX_BODY)
    if not body:
        raise ValueError("empty comment body")
    flag = flag if flag in FLAGS else ""
    with db() as c:
        if parent_id is not None:
            # a reply must attach to a parent on the SAME board (benchmark +
            # backend + instance) — otherwise a crafted parent_id cross-threads
            row = c.execute(
                "SELECT 1 FROM comments WHERE id=? AND benchmark=? AND backend=? "
                "AND instance_id=?",
                (parent_id, benchmark, backend, instance_id)).fetchone()
            if row is None:
                raise ValueError("parent comment not found on this board")
        cur = c.execute(
            "INSERT INTO comments(benchmark,backend,instance_id,parent_id,author,body,"
            "flag,status,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
            (benchmark, backend, instance_id, parent_id, author, body,
             flag if parent_id is None else "", "pending", time.time()))
        return int(cur.lastrowid or 0)


def set_status(benchmark: str, backend: str, comment_id: int, status: str, who: str) -> None:
    if status not in ("pending", "resolved"):
        raise ValueError("bad status")
    with db() as c:
        if status == "resolved":
            cur = c.execute("UPDATE comments SET status=?,resolved_by=?,resolved_at=? "
                            "WHERE id=? AND benchmark=? AND backend=? AND parent_id IS NULL",
                            (status, _clean(who, MAX_AUTHOR) or "anonymous",
                             time.time(), comment_id, benchmark, backend))
        else:
            cur = c.execute("UPDATE comments SET status=?,resolved_by=NULL,resolved_at=NULL "
                            "WHERE id=? AND benchmark=? AND backend=? AND parent_id IS NULL",
                            (status, comment_id, benchmark, backend))
        if cur.rowcount == 0:
            raise ValueError("thread not found on this board")


def threads_for(benchmark: str, backend: str, instance_id: str) -> list[dict]:
    """Root comments (newest first), each with their full reply TREE (arbitrary
    depth — reply-to-a-reply supported), replies ordered oldest-first per level.

    A `depth` field is attached for indentation (root=0). The tree is flattened
    into each node's `replies` list recursively so the template can render it."""
    with db() as c:
        rows = c.execute(
            "SELECT * FROM comments WHERE benchmark=? AND backend=? AND instance_id=? "
            "ORDER BY created_at ASC",
            (benchmark, backend, instance_id)).fetchall()
    nodes = {r["id"]: {**dict(r), "replies": []} for r in rows}
    roots = []
    for r in rows:
        node = nodes[r["id"]]
        pid = r["parent_id"]
        if pid is None:
            roots.append(node)
        elif pid in nodes:
            nodes[pid]["replies"].append(node)
        else:  # orphaned reply (parent deleted) — surface as a root so it isn't lost
            roots.append(node)

    def _depth(node, d):
        node["depth"] = d
        for child in node["replies"]:
            _depth(child, d + 1)
    for root in roots:
        _depth(root, 0)
    # newest-first by root creation
    roots.sort(key=lambda n: n["created_at"], reverse=True)
    return roots


def counts_by_instance(benchmark: str, backend: str) -> dict[str, dict]:
    """{instance_id: {total, open, resolved}} over root threads — for the index badges."""
    with db() as c:
        rows = c.execute(
            "SELECT instance_id, status, COUNT(*) n FROM comments "
            "WHERE parent_id IS NULL AND benchmark=? AND backend=? "
            "GROUP BY instance_id, status",
            (benchmark, backend)).fetchall()
    out: dict[str, dict] = {}
    for r in rows:
        d = out.setdefault(r["instance_id"], {"total": 0, "open": 0, "resolved": 0})
        d["total"] += r["n"]
        d["open" if r["status"] == "pending" else "resolved"] += r["n"]
    return out


def all_threads(status: str | None = None, flag: str | None = None,
                backend: str | None = None, benchmark: str | None = None) -> list[dict]:
    """Every root thread across all instances (for the shared comments panel).
    backend/benchmark=None -> threads from every cell (each tagged with its own)."""
    q = "SELECT * FROM comments WHERE parent_id IS NULL"
    args: list = []
    if benchmark:
        q += " AND benchmark=?"
        args.append(benchmark)
    if backend:
        q += " AND backend=?"
        args.append(backend)
    if status in ("pending", "resolved"):
        q += " AND status=?"
        args.append(status)
    if flag in FLAGS:
        q += " AND flag=?"
        args.append(flag)
    q += " ORDER BY (status='pending') DESC, created_at DESC"
    with db() as c:
        roots = c.execute(q, args).fetchall()
        out = []
        for r in roots:
            n_replies = c.execute("SELECT COUNT(*) n FROM comments WHERE parent_id=?",
                                  (r["id"],)).fetchone()["n"]
            d = dict(r)
            d["n_replies"] = n_replies
            out.append(d)
        return out


def export_all() -> list[dict]:
    with db() as c:
        return [dict(r) for r in c.execute("SELECT * FROM comments ORDER BY id ASC").fetchall()]


# columns a snapshot carries verbatim; `id`/`parent_id` are remapped on load,
# because the ids in a snapshot are the exporting database's
_SNAPSHOT_COLUMNS = ("benchmark", "backend", "instance_id", "author", "body",
                     "flag", "status", "created_at", "resolved_by", "resolved_at")
# a comment's identity ACROSS databases: nothing here is assigned by sqlite
_IDENTITY = ("benchmark", "backend", "instance_id", "author", "created_at")


def import_snapshot(threads: list[dict]) -> tuple[int, int]:
    """Load an `export_all` snapshot into this database. Returns (added, skipped).

    Without this, committing `viz/review_comments.json` freezes review history that
    nothing can read back: the live DB is gitignored, so a clone renders every
    board as having no comments. Written as an ADD rather than a restore -- an
    existing comment is left alone -- so it can be run against a database that
    already has local review on it.

    Identity across databases is (benchmark, backend, instance_id, author,
    created_at): `id` is the exporting sqlite's, so matching on it would collide
    with unrelated local comments. Replies are attached through the id the parent
    gets HERE, and a reply whose parent was skipped attaches to the existing
    parent rather than being dropped.
    """
    added = skipped = 0
    with db() as c:
        def _insert(row: dict, parent: int | None) -> int | None:
            nonlocal added, skipped
            if not row.get("instance_id") or not row.get("body"):
                skipped += 1
                return None
            where = " AND ".join(f"{k} IS ?" for k in _IDENTITY)
            prior = c.execute(f"SELECT id FROM comments WHERE {where}",
                              tuple(row.get(k) for k in _IDENTITY)).fetchone()
            if prior is not None:
                skipped += 1
                return int(prior["id"])
            cols = ",".join((*_SNAPSHOT_COLUMNS, "parent_id"))
            marks = ",".join("?" * (len(_SNAPSHOT_COLUMNS) + 1))
            values = [row.get(k) for k in _SNAPSHOT_COLUMNS]
            values[_SNAPSHOT_COLUMNS.index("created_at")] = float(
                row.get("created_at") or time.time())
            cur = c.execute(f"INSERT INTO comments({cols}) VALUES({marks})",
                            (*values, parent))
            added += 1
            return int(cur.lastrowid or 0)

        for thread in threads:
            root = _insert(thread, None)
            replies = thread.get("replies") or []
            if root is None:      # unusable root: its replies have no board either
                skipped += len(replies)
                continue
            for reply in replies:
                _insert(reply, root)
    return added, skipped
