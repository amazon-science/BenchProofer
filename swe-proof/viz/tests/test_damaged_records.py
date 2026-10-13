# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""A cell whose record cannot be read must cost that record, never a page.

Each case is a record that parses but is not the shape its reader expects. They
are built as a synthetic corpus because the shipped one holds none of them --
which is also why a green suite says nothing about them: the route tests drive
the healthy corpus.

The blast radius is the reason each case checks other pages too, not just the
damaged cell's own: `base.html` renders `green_counts()` in the header of EVERY
page, and that reads `summary_table` for every backend of both benchmarks. So a
loader raising on ONE cell answers 500 on every page of the site, including the
other benchmark's board and /comments.
"""
import json
import os
from pathlib import Path

import pytest
from backend import paths, settings

settings.AGENT_ENABLED = False

from starlette.testclient import TestClient  # noqa: E402
from backend import data, render, repo  # noqa: E402
from backend.app import app  # noqa: E402

HEALTHY = "healthy__healthy-1"
CASE = "case__case-1"

GOOD_ROW = {"repo": "org/proj", "base_commit": "c" * 40, "version": "1.0",
            "problem_statement": "It breaks on empty input.",
            "FAIL_TO_PASS": '["t1"]', "PASS_TO_PASS": "[]"}
GOOD_META = {"gates": {g: {"status": "pass", "detail": "ok"} for g in data.GATE_ORDER},
             "axioms": [], "modeled_functions": [{"model_symbol": "f", "repo_symbol": "g"}]}
GOLD_DIFF = ("diff --git a/x.py b/x.py\n--- a/x.py\n+++ b/x.py\n"
             "@@ -1,2 +1,2 @@\n-a\n+b\n c\n")


def _write_cell(root: Path, iid: str, row="keep", meta="keep", verdict="v",
                result="keep", unreadable=(), replace_with_dir=(), bk="nagini"):
    """One instance dir in the split layout, with the damage the case asks for."""
    d = root / iid
    (d / bk).mkdir(parents=True, exist_ok=True)
    r = dict(GOOD_ROW) if row == "keep" else row
    if isinstance(r, dict):
        r = dict(r)
        r["instance_id"] = iid
    (d / "instance.json").write_text(json.dumps(r))
    (d / "patch.diff").write_text(GOLD_DIFF)
    if meta == "keep":
        meta = json.dumps(GOOD_META)
    if meta is not None:
        (d / bk / "meta.json").write_text(meta)
    if verdict is not None:
        (d / bk / "verdict.md").write_text("# G-EQ\n\nThe attacks were re-run.\n")
    if result == "keep":
        result = json.dumps({"final_status": "ok"})
    if result is not None:
        (d / bk / "result.json").write_text(result)
    for name in replace_with_dir:
        p = d / bk / name
        if p.exists():
            p.unlink()
        p.mkdir()
    for name in unreadable:
        p = (d / bk / name) if (d / bk / name).exists() else (d / name)
        os.chmod(p, 0o000)
    return d


@pytest.fixture
def corpus(tmp_path, monkeypatch):
    """A two-cell benchmark root: one healthy instance and one the test damages.

    Points `paths.REPO_ROOT` at a tmp tree (both benchmark roots exist, so the
    header's counts are computed for real) and clears the loaders' caches on the
    way in AND out, so the modules that run after this one see the real corpus.
    """
    def _reset():
        data.dataset_row.cache_clear()
        data._ttl_store.clear()
        repo.file_at_base.cache_clear()
        repo.tree_at_base.cache_clear()

    for bm in settings.BENCHMARKS:
        (tmp_path / settings.benchmark_dir(bm)).mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(paths, "REPO_ROOT", tmp_path)
    _reset()
    root = tmp_path / settings.benchmark_dir("pro")
    _write_cell(root, HEALTHY)

    def make(**damage):
        d = _write_cell(root, CASE, **damage)
        _reset()
        return d
    try:
        yield make
    finally:
        for p in (root / CASE).rglob("*"):
            if p.is_file() or p.is_dir():
                os.chmod(p, 0o700)      # so tmp_path can be cleaned up
        _reset()


def _pages(client):
    """Status of the damaged cell's page and of the pages a reader reaches from
    it, plus whether the healthy neighbour is still listed on the board."""
    board = client.get("/pro/nagini/")
    return {
        "cell": client.get(f"/pro/nagini/i/{CASE}").status_code,
        "board": board.status_code,
        "filtered": client.get("/pro/nagini/?flagged=axioms").status_code,
        "other_cell": client.get(f"/pro/nagini/i/{HEALTHY}").status_code,
        "other_board": client.get("/verified/nagini/").status_code,
        "comments": client.get("/comments").status_code,
        "neighbour_listed": HEALTHY in board.text,
    }


# Each entry: the damage, and the status the DAMAGED cell's own page must answer.
# 200 = "render the record as far as it goes"; 404 = "there is no such instance"
# (an instance.json that is unreadable or is not an object identifies nothing).
DAMAGE = {
    # meta.json parses, but not to an object
    "meta-null": (dict(meta="null"), 200),
    "meta-list": (dict(meta="[]"), 200),
    "meta-string": (dict(meta='"pass"'), 200),
    "meta-number": (dict(meta="7"), 200),
    # ...or its gates are not a mapping of gate -> record
    "gates-list": (dict(meta=json.dumps({"gates": []})), 200),
    "gates-string": (dict(meta=json.dumps({"gates": "pass"})), 200),
    # ...or a field the page counts is a scalar
    "axioms-number": (dict(meta=json.dumps({"gates": {}, "axioms": 5})), 200),
    "modeled-number": (dict(meta=json.dumps({"modeled_functions": 3})), 200),
    "deepref-string": (dict(meta=json.dumps({"deep_model_references": "x"})), 200),
    # ...or a recorded audit note is not prose (publish_note runs re.split on it)
    "audit-note-list": (dict(meta=json.dumps(
        {"gates": {"G-EQ": {"status": "pass", "note": ["a", "b"]}}})), 200),
    "audit-detail-dict": (dict(meta=json.dumps(
        {"gates": {"G-EQ": {"status": "pass", "detail": {"why": "ok"}}}})), 200),
    "panel-note-number": (dict(meta=json.dumps(
        {"gates": {"G-PANEL-1": {"status": "pass", "note": 12}}})), 200),
    # ...or a gate's data blob is not a mapping (G-PBT reads cases out of it)
    "gate-data-list": (dict(meta=json.dumps(
        {"gates": {"G-PBT": {"status": "pass", "data": ["x"]}}})), 200),
    "pbt-cases-mapping": (dict(meta=json.dumps(
        {"gates": {"G-PBT": {"status": "pass", "data": {"cases": {"a": 1}}}}})), 200),
    # result.json parses, but not to an object
    "result-null": (dict(result="null"), 200),
    "result-list": (dict(result="[1]"), 200),
    # the dataset row is short of, or wrong about, what the page renders
    "row-without-base-commit": (dict(row={"repo": "org/proj", "problem_statement": "x"}), 200),
    "row-empty": (dict(row={}), 200),
    "row-non-text-fields": (dict(row={"repo": 5, "base_commit": 7,
                                      "problem_statement": 9, "version": []}), 200),
    "row-not-an-object": (dict(row=["org/proj"]), 404),
    "row-test-lists-not-lists": (dict(row={**GOOD_ROW, "FAIL_TO_PASS": {"a": 1},
                                           "PASS_TO_PASS": 3}), 200),
    # nothing constructed for this backend at all (the shipped state of pro/ears)
    "no-bundle-dir": (dict(meta=None, verdict=None, result=None), 200),
    # present but unreadable: a mid-build chmod, a truncated write, a stray dir
    "meta-unreadable": (dict(unreadable=["meta.json"]), 200),
    "verdict-unreadable": (dict(unreadable=["verdict.md"]), 200),
    "result-unreadable": (dict(unreadable=["result.json"]), 200),
    "patch-unreadable": (dict(unreadable=["patch.diff"]), 200),
    "meta-is-a-directory": (dict(meta=None, replace_with_dir=["meta.json"]), 200),
    "verdict-is-a-directory": (dict(verdict=None, replace_with_dir=["verdict.md"]), 200),
    "instance-json-unreadable": (dict(unreadable=["instance.json"]), 404),
}


@pytest.mark.parametrize("name", sorted(DAMAGE))
def test_a_damaged_record_costs_its_own_record_and_nothing_else(corpus, name):
    damage, want_cell = DAMAGE[name]
    corpus(**damage)
    with TestClient(app, raise_server_exceptions=False) as c:
        got = _pages(c)
    assert got["cell"] == want_cell, f"{name}: instance page {got['cell']}"
    for page in ("board", "filtered", "other_cell", "other_board", "comments"):
        assert got[page] == 200, f"{name}: {page} answered {got[page]}"
    assert got["neighbour_listed"], f"{name}: the healthy instance left the board"


# Damage in the BYTES of an artifact rather than in the shape of a record. None of
# these needed a fix -- `read_bundle_file` already answers None for a file it
# cannot decode, `patchview` tolerates a non-diff, and the battery's lanes are
# guarded -- so these are here to keep it that way. A build writing a bundle while
# the site reads it is what produces them.
CONTENT = {
    "patch-is-not-a-diff": {"patch.diff": "this is not a diff\n@@ bogus @@\n"},
    "patch-headers-only": {"patch.diff": "diff --git a/x b/x\n"},
    "patch-hunk-without-header": {"patch.diff": "@@ -1,5 +1,5 @@\n-a\n+b\n"},
    "patch-non-numeric-hunk": {"patch.diff": "--- a/x\n+++ b/x\n@@ -q,w +e,r @@\n-a\n+b\n"},
    "patch-not-utf8": {"patch.diff": b"\xff\xfe\x00\x01binary\n"},
    "verdict-not-utf8": {"verdict.md": b"\xff\xfe not utf8"},
    "verdict-holds-a-nul": {"verdict.md": "a\x00b\n"},
    "model-not-utf8": {"model.py": b"\xc3\x28 bad utf8"},
    "pbt-result-null": {"pbt_result.json": "null"},
    "pbt-result-list": {"pbt_result.json": "[1, 2]"},
    "pbt-lanes-not-lists": {"pbt_result.json": json.dumps(
        {"spec_cases": 3, "axiom_cases": {"a": 1}})},
    "pbt-case-not-a-record": {"pbt_result.json": json.dumps(
        {"spec_cases": ["x", 2], "axiom_cases": [None]})},
    "result-status-not-text": {"result.json": json.dumps({"final_status": ["ok"]})},
    "meta-gate-not-a-record": {"meta.json": json.dumps(
        {"gates": {"G-EQ": "pass", "G-PBT": None}})},
    "meta-modeled-fns-are-strings": {"meta.json": json.dumps(
        {**GOOD_META, "modeled_functions": ["f", None]})},
    "meta-float-encoding-is-a-dict": {"meta.json": json.dumps(
        {**GOOD_META, "float_encoding": {"a": 1}})},
    "row-hints-not-text": {"instance.json": json.dumps({**GOOD_ROW, "instance_id": CASE,
                                                        "hints_text": {"h": 1}})},
}


@pytest.mark.parametrize("name", sorted(CONTENT))
def test_an_artifact_whose_bytes_are_wrong_still_renders_the_rest(corpus, name):
    d = corpus()
    (d / "nagini" / "model.py").write_text("def f(x):\n    return x\n")
    (d / "nagini" / "pbt_result.json").write_text(
        json.dumps({"spec_cases": [], "axiom_cases": []}))
    for fname, content in CONTENT[name].items():
        p = d / fname if fname in ("patch.diff", "instance.json") else d / "nagini" / fname
        p.write_bytes(content) if isinstance(content, bytes) else p.write_text(content)
    data.dataset_row.cache_clear()
    data._ttl_store.clear()
    with TestClient(app, raise_server_exceptions=False) as c:
        got = _pages(c)
    assert got["cell"] == 200, f"{name}: instance page {got['cell']}"
    for page in ("board", "filtered", "other_cell", "other_board", "comments"):
        assert got[page] == 200, f"{name}: {page} answered {got[page]}"


def test_a_bare_symbol_in_modeled_functions_is_shown(corpus):
    """Not damage: the second convention actually in the corpus. Many bundles
    record `modeled_functions` as bare model-side symbol names rather than
    {model_symbol, repo_symbol} records, and read as records those render as an
    empty row with an arrow."""
    d = corpus(meta=json.dumps({**GOOD_META, "modeled_functions": ["resolveOrderColumn"]}))
    assert d.is_dir()
    with TestClient(app, raise_server_exceptions=False) as c:
        page = c.get(f"/pro/nagini/i/{CASE}")
    assert page.status_code == 200
    # not merely somewhere on the page: the raw meta.json fold prints the whole
    # record, so the assertion has to be the symbol AS the fold's own entry
    assert "<code>resolveOrderColumn</code>" in page.text


def test_the_board_survives_a_record_no_guard_anticipated(corpus, monkeypatch):
    """The floor under the shape guards: whatever a loader raises, the row is the
    only thing lost. Driven by making `meta()` itself raise, because every shape
    the corpus can actually hold is handled above -- so without this the fallback
    would be untested code."""
    corpus()
    real_meta = data.meta

    def boom(bm, bk, iid, *a, **kw):
        if iid == CASE:
            raise RuntimeError("record is not readable")
        return real_meta(bm, bk, iid, *a, **kw)

    monkeypatch.setattr(data, "meta", boom)
    data._ttl_store.clear()
    with TestClient(app, raise_server_exceptions=False) as c:
        board = c.get("/pro/nagini/")
        assert board.status_code == 200
        assert HEALTHY in board.text, "the readable instance left the board"
        assert CASE in board.text, "the unreadable instance was dropped silently"
        assert "unreadable" in board.text, "no marker on the row that failed"
        assert c.get("/comments").status_code == 200
        # ...and it is findable, which is the point of marking it
        only = c.get("/pro/nagini/?flagged=unreadable")
        assert only.status_code == 200
        assert CASE in only.text and HEALTHY not in only.text
    # it is NOT counted as constructed, and never as green
    rows = {r["instance_id"]: r for r in data.summary_table("pro", "nagini")}
    assert rows[CASE]["status"] == "unreadable" and rows[CASE]["green"] is False
    assert data.green_counts("pro")["nagini"] == 1        # the healthy one only


def test_an_unknown_instance_is_a_clean_404(corpus):
    corpus()
    with TestClient(app, raise_server_exceptions=False) as c:
        for u in ("/pro/nagini/i/nosuch__nosuch-1",
                  "/pro/nagini/i/nosuch__nosuch-1/tree",
                  "/pro/nagini/i/nosuch__nosuch-1/file?path=README.md",
                  # a crafted id that leaves the benchmark root
                  "/pro/nagini/i/..%2F..%2Fetc",
                  "/pro/nagini/i/a%2Fb"):
            assert c.get(u).status_code == 404, u


# ---------------------------------------------------------------- the two filters
#
# Both exist because Jinja does NOT degrade these to Undefined: a slice compiles
# to a plain subscript, and `|length` / `{% for %}` call len()/iter() on whatever
# they are given. That is a TypeError out of the template, i.e. a 500 page.

def test_sha_filter_survives_a_row_with_no_base_commit():
    from backend.app import _sha
    assert _sha("c" * 40) == "c" * 10
    assert _sha("c" * 40, 12) == "c" * 12
    assert _sha(None) == "" and _sha("") == ""
    from jinja2 import Environment, UndefinedError, select_autoescape
    env = Environment(autoescape=select_autoescape(default_for_string=True))
    env.filters["sha"] = _sha
    # the shape the page sees: a dict row with the key absent
    assert env.from_string("{{ row.base_commit|sha }}").render(row={}) == ""
    with pytest.raises(UndefinedError):
        env.from_string("{{ row.base_commit[:10] }}").render(row={})


def test_as_list_filter_counts_and_iterates_a_scalar_field():
    from backend.app import _as_list
    assert _as_list([1, 2]) == [1, 2]
    assert _as_list(5) == [] and _as_list("x") == [] and _as_list(None) == []
    from jinja2 import Environment, select_autoescape
    env = Environment(autoescape=select_autoescape(default_for_string=True))
    env.filters["as_list"] = _as_list
    assert env.from_string("{{ m.axioms|as_list|length }}").render(m={"axioms": 5}) == "0"
    assert env.from_string("{{ m.axioms|as_list|length }}").render(m={}) == "0"
    with pytest.raises(TypeError):
        env.from_string("{{ m.axioms|length }}").render(m={"axioms": 5})


def test_md_publishes_a_field_that_is_not_prose():
    """`row.problem_statement | md` and the audit notes are read off disk."""
    assert "12" in render.md(12)
    assert "a" in render.md(["a"])
    assert render.md(None) == "" and render.md("") == "" and render.md(0) == ""
