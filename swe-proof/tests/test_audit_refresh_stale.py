# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""`--only-failing` has to see a role whose verdict no longer describes the spec.

`audit_refresh --only-failing` exists so a lane can re-derive just the reviewer
roles that need it instead of putting three passing adversaries back on the dice.
Its docstring promises two kinds: the roles the cell is RED on, and the roles
whose recorded verdict is about bytes that have since moved. The second half
never worked.

`stale_roles` asks `check_stamp_freshness.check_cell`, which reports an audit
gate's digest mismatch as `deferred` rather than `changed` -- deliberately, because
a changed spec file is not by itself a stale audit (a comment edit, an added
termination obligation) and `audit_freshness` is the code that knows the
difference. `stale_roles` counted only `changed`/`vanished`, and for these four
gates `changed` is unreachable. So the function returned nothing however far the
spec had moved from its audit, and the lane recorded `no-audit-fail` -- "every
audit stamp matches the spec on disk" -- for cells whose stamps did not.

These tests pin both directions, because the fix's cost is a re-audit: a moved
spec that `audit_freshness` judges RE-AUDIT yields the role, and one it judges
SPEC-IDENTICAL or STRENGTHENED does not.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import audit_freshness
import audit_refresh


def _cell(tmp_path: Path, sources: dict) -> Path:
    """A lean cell whose four audit gates all passed, with recorded digests."""
    cell = tmp_path / "django__django-1" / "lean"
    cell.mkdir(parents=True)
    (cell / "Solution.lean").write_text("theorem t : True := trivial\n")
    gates = {g: {"status": "pass", "checked_at": "2026-08-01T00:00:00Z",
                 "sources": dict(sources)}
             for g in ("G-EQ", "G-PANEL-1", "G-PANEL-2", "G-PANEL-3")}
    (cell / "meta.json").write_text(json.dumps({"schema_version": 1,
                                                "gates": gates}))
    return cell


# The digest of no file in the bundle, so every record's `sources` mismatches.
_MOVED = {"Solution.lean": "0" * 64}


def test_a_role_whose_audit_predates_the_current_spec_is_stale(tmp_path,
                                                               monkeypatch):
    cell = _cell(tmp_path, _MOVED)
    monkeypatch.setattr(audit_freshness, "verdict_for",
                        lambda c, b: ("RE-AUDIT", "2 spec line(s) removed"))
    assert audit_refresh.stale_roles(cell) == ["eq", "panel_2", "panel_3"]


@pytest.mark.parametrize("verdict", ["SPEC-IDENTICAL", "STRENGTHENED"])
def test_a_spec_edit_that_cannot_have_changed_a_verdict_is_not_stale(
        tmp_path, monkeypatch, verdict):
    """The direction that keeps the fix affordable.

    Re-auditing is an agent per role, so folding in every cell whose spec file
    differs from its audit would re-audit most of the corpus -- and would put two
    passing adversaries back on the dice for each one. A comment edit or an added
    obligation moves the digest without moving the spec, and `audit_freshness` is
    where that judgement lives.
    """
    cell = _cell(tmp_path, _MOVED)
    monkeypatch.setattr(audit_freshness, "verdict_for",
                        lambda c, b: (verdict, "only comments changed"))
    assert audit_refresh.stale_roles(cell) == []


def test_freshness_is_asked_once_per_cell_not_once_per_gate(tmp_path,
                                                            monkeypatch):
    """All four roles read the same spec file, and the answer costs a `git log`
    plus a `cat-file`. Asking per gate would quadruple that for no new
    information."""
    cell = _cell(tmp_path, _MOVED)
    calls = []

    def spy(c, b):
        calls.append((c, b))
        return "RE-AUDIT", "moved"

    monkeypatch.setattr(audit_freshness, "verdict_for", spy)
    audit_refresh.stale_roles(cell)
    assert len(calls) == 1
    # and it is asked about the CELL and its BACKEND, not about a gate
    assert calls[0] == (cell, "lean")


def test_a_matching_stamp_asks_nothing_and_is_not_stale(tmp_path, monkeypatch):
    """A record whose digests match the bundle is fresh by inspection, so the git
    work stays off the common path entirely."""
    import hashlib
    cell = _cell(tmp_path, {})
    src = (cell / "Solution.lean").read_bytes()
    meta = json.loads((cell / "meta.json").read_text())
    for g in meta["gates"]:
        meta["gates"][g]["sources"] = {
            "Solution.lean": hashlib.sha256(src).hexdigest()}
    (cell / "meta.json").write_text(json.dumps(meta))

    def boom(c, b):                      # pragma: no cover - must not be reached
        raise AssertionError("asked audit_freshness about a matching stamp")

    monkeypatch.setattr(audit_freshness, "verdict_for", boom)
    assert audit_refresh.stale_roles(cell) == []


def test_a_vanished_source_is_stale_without_asking(tmp_path, monkeypatch):
    """`vanished` needs no adjudication: no argument about what a verdict was
    about survives the artifact it cited not being in the bundle."""
    cell = _cell(tmp_path, {"Attack.lean": "0" * 64})

    def boom(c, b):                      # pragma: no cover - must not be reached
        raise AssertionError("asked audit_freshness about a vanished source")

    monkeypatch.setattr(audit_freshness, "verdict_for", boom)
    assert audit_refresh.stale_roles(cell) == ["eq", "panel_2", "panel_3"]


def test_a_failure_to_measure_freshness_counts_as_stale(tmp_path, monkeypatch):
    """`UNKNOWN` and `UNPARSEABLE` are in `audit_freshness.NEEDS_AUDIT` because
    they are failures to MEASURE, and treating "I could not tell" as fresh is how
    a stale verdict ships. This reads that set rather than restating it."""
    cell = _cell(tmp_path, _MOVED)
    for verdict in sorted(audit_freshness.NEEDS_AUDIT):
        monkeypatch.setattr(audit_freshness, "verdict_for",
                            lambda c, b, v=verdict: (v, "x"))
        assert audit_refresh.stale_roles(cell), verdict
