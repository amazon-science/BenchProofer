# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""restamp_gate: refreshing a stamp must not be able to demote a cell.

This tool re-runs a named subset of gates to bind old records to the bytes they
judged. That is a book-keeping job, and it acquires the power to change the
release verdict only through one accident: three of the gates it re-runs
(`G-VERIFY`, `G-DIFF`, `G-GOLD` via `verify.py:31`, plus `ax.py:47` and
`conf.py:63`) return a verdict-shaped `GateResult(name, "timeout", ...)` when
their subprocess misses the wall clock, and none of them honours an environment
override of `bundle.verify_timeout()` -- unlike `mut.py:62` and `pbt.py:756`,
which both take `max(env_int(...), bundle.verify_timeout())`. So a cell whose
solution verifies well inside its cap can still miss the wall clock when the
machine is busy, and `run_gates` writes the result before this tool sees it.

The asymmetry these tests pin down: a WALL CLOCK over a green record is
suppressed, and nothing else is. A `fail` is a measurement -- the verifier ran and
the proof did not close -- and an `error` normally names a real defect like a
missing conformance script. Suppressing either would hide exactly what the sweep
exists to find.

"Wall clock" is THREE spellings, which is the part that is easy to get wrong, and
only one of them is a status: the verdict-shaped `timeout` above; G-PBT's `error`
carrying `TIMED-OUT` in its data (`pbt.py:868`); and G-DIFF/G-GOLD/G-MUT's `error`
naming the file that never came back, which now carries
`data["no_verdict"] == "timeout"`. None of those three gates has a `timeout`
status to return. A guard that reads the status only covers the first spelling
and silently keeps the timeouts the other two report as an `error`.

`no_verdict == "crash"` is not a wall clock, and the test below says so: a
verifier environment that breaks does so at any load, so it is a finding.
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

import restamp_gate


@dataclass
class R:
    """The shape `undo_timeouts` reads off a GateResult."""
    gate: str
    status: str
    data: dict | None = None


def _cell(tmp_path: Path, gates: dict) -> Path:
    b = tmp_path / "django__django-1" / "velvet"
    b.mkdir(parents=True, exist_ok=True)
    (b / "meta.json").write_text(json.dumps({"schema_version": 1,
                                             "gates": gates}, indent=2))
    return b


def _recorded(cell: Path, gate: str) -> dict:
    return json.loads((cell / "meta.json").read_text())["gates"][gate]


_GREEN = {"status": "pass", "checked_at": "2026-08-10T00:00:00Z",
          "detail": "verified in 4.1s"}


def test_a_timeout_over_a_green_record_puts_the_green_record_back(tmp_path):
    cell = _cell(tmp_path, {"G-VERIFY": _GREEN})
    prior = restamp_gate.prior_gates(cell, ["G-VERIFY"])
    # what run_gates would have written before this tool got a look
    meta = json.loads((cell / "meta.json").read_text())
    meta["gates"]["G-VERIFY"] = {"status": "timeout",
                                 "detail": "timeout after 300s"}
    (cell / "meta.json").write_text(json.dumps(meta))

    assert restamp_gate.undo_timeouts(cell, [R("G-VERIFY", "timeout")],
                                      prior) == ["G-VERIFY"]
    assert _recorded(cell, "G-VERIFY") == _GREEN


def test_a_recorded_failure_is_left_alone(tmp_path):
    """The direction that must not be softened. A `fail` means the verifier got
    its wall clock and the proof did not close, so it is a measurement of the
    artifact -- which may well have been edited since the green record was
    written, and that is the whole reason to re-run."""
    cell = _cell(tmp_path, {"G-VERIFY": _GREEN})
    prior = restamp_gate.prior_gates(cell, ["G-VERIFY"])
    fail = {"status": "fail", "detail": "verification failed"}
    meta = json.loads((cell / "meta.json").read_text())
    meta["gates"]["G-VERIFY"] = fail
    (cell / "meta.json").write_text(json.dumps(meta))

    assert restamp_gate.undo_timeouts(cell, [R("G-VERIFY", "fail")], prior) == []
    assert _recorded(cell, "G-VERIFY") == fail


def test_an_error_is_left_alone(tmp_path):
    """`ax.py` and `conf.py` return `error` for defects with names -- a missing
    conformance script, an unimportable checker. Those are findings."""
    cell = _cell(tmp_path, {"G-CONF": _GREEN})
    prior = restamp_gate.prior_gates(cell, ["G-CONF"])
    err = {"status": "error", "detail": "conf_missing_script"}
    meta = json.loads((cell / "meta.json").read_text())
    meta["gates"]["G-CONF"] = err
    (cell / "meta.json").write_text(json.dumps(meta))

    assert restamp_gate.undo_timeouts(cell, [R("G-CONF", "error")], prior) == []
    assert _recorded(cell, "G-CONF") == err


def test_a_pbt_battery_that_missed_the_cap_is_a_wall_clock_not_a_finding(tmp_path):
    """G-PBT has no `timeout` status: a battery that ran out of wall clock comes
    back `error` with `TIMED-OUT` in its data (gates/pbt.py:868), which means the
    battery was never actually judged -- so it is exactly what this function
    protects against.
    """
    cell = _cell(tmp_path, {"G-PBT": _GREEN})
    prior = restamp_gate.prior_gates(cell, ["G-PBT"])
    meta = json.loads((cell / "meta.json").read_text())
    meta["gates"]["G-PBT"] = {"status": "error", "detail": "TIMED-OUT",
                              "data": {"verdict": "TIMED-OUT"}}
    (cell / "meta.json").write_text(json.dumps(meta))

    r = R("G-PBT", "error", {"verdict": "TIMED-OUT"})
    assert restamp_gate.undo_timeouts(cell, [r], prior) == ["G-PBT"]
    assert _recorded(cell, "G-PBT") == _GREEN


def test_a_pbt_error_that_names_a_defect_is_still_a_finding(tmp_path):
    """Matched on the recorded verdict, not on the status, so the errors that name
    something real -- an unimportable battery, a malformed manifest -- survive. A
    broken battery caps its cell red however strong the spec is, which is the one
    thing this sweep must not suppress."""
    cell = _cell(tmp_path, {"G-PBT": _GREEN})
    prior = restamp_gate.prior_gates(cell, ["G-PBT"])
    err = {"status": "error", "detail": "battery_import_failed",
           "data": {"verdict": "DEFECT"}}
    meta = json.loads((cell / "meta.json").read_text())
    meta["gates"]["G-PBT"] = err
    (cell / "meta.json").write_text(json.dumps(meta))

    assert restamp_gate.undo_timeouts(
        cell, [R("G-PBT", "error", {"verdict": "DEFECT"})], prior) == []
    assert _recorded(cell, "G-PBT") == err
    # and an error with no data at all is a finding too, not a free pass
    assert restamp_gate.undo_timeouts(cell, [R("G-PBT", "error", None)],
                                      prior) == []


def test_a_gold_check_that_never_came_back_in_time_is_a_wall_clock(tmp_path):
    """The third spelling, and the one that actually cost stamps.

    G-DIFF and G-GOLD have no timeout status either: a check that hit the cap is
    an `error` naming the file (`no verdict on model.py: timeout`), which is
    indistinguishable from a broken environment unless the reason is recorded.
    """
    for gate in ("G-DIFF", "G-GOLD", "G-MUT"):
        cell = _cell(tmp_path / gate, {gate: _GREEN})
        prior = restamp_gate.prior_gates(cell, [gate])
        meta = json.loads((cell / "meta.json").read_text())
        meta["gates"][gate] = {"status": "error",
                               "detail": "no verdict on model.py: timeout",
                               "data": {"no_verdict": "timeout"}}
        (cell / "meta.json").write_text(json.dumps(meta))

        r = R(gate, "error", {"no_verdict": "timeout"})
        assert restamp_gate.undo_timeouts(cell, [r], prior) == [gate], gate
        assert _recorded(cell, gate) == _GREEN, gate


def test_a_verifier_that_crashed_is_a_finding_not_a_wall_clock(tmp_path):
    """The distinction the reason exists to make. A crashed checker -- a dead JVM
    under Viper, an unimportable environment -- is reproducible rather than a
    load artifact, so it is exactly what this sweep is for. Suppressing it
    because it also produced no verdict would restore a green record over a cell
    whose verifier cannot run."""
    cell = _cell(tmp_path, {"G-GOLD": _GREEN})
    prior = restamp_gate.prior_gates(cell, ["G-GOLD"])
    err = {"status": "error", "detail": "no verdict on model.py: JVM died",
           "data": {"no_verdict": "crash"}}
    meta = json.loads((cell / "meta.json").read_text())
    meta["gates"]["G-GOLD"] = err
    (cell / "meta.json").write_text(json.dumps(meta))

    assert restamp_gate.undo_timeouts(
        cell, [R("G-GOLD", "error", {"no_verdict": "crash"})], prior) == []
    assert _recorded(cell, "G-GOLD") == err


def test_a_timeout_over_a_red_record_is_kept(tmp_path):
    """There is nothing to protect: the cell was already not green, so the
    timeout is the freshest thing known about it and hiding it would restore a
    verdict that is no better."""
    cell = _cell(tmp_path, {"G-VERIFY": {"status": "fail", "detail": "old"}})
    prior = restamp_gate.prior_gates(cell, ["G-VERIFY"])
    to = {"status": "timeout", "detail": "timeout after 300s"}
    meta = json.loads((cell / "meta.json").read_text())
    meta["gates"]["G-VERIFY"] = to
    (cell / "meta.json").write_text(json.dumps(meta))

    assert restamp_gate.undo_timeouts(cell, [R("G-VERIFY", "timeout")], prior) == []
    assert _recorded(cell, "G-VERIFY") == to


def test_a_gate_with_no_prior_record_is_not_invented(tmp_path):
    """A first-ever run that times out has no green to fall back to, and
    `prior_gates` must not manufacture one."""
    cell = _cell(tmp_path, {})
    prior = restamp_gate.prior_gates(cell, ["G-VERIFY"])
    assert prior == {}
    meta = json.loads((cell / "meta.json").read_text())
    meta["gates"]["G-VERIFY"] = {"status": "timeout"}
    (cell / "meta.json").write_text(json.dumps(meta))
    assert restamp_gate.undo_timeouts(cell, [R("G-VERIFY", "timeout")], prior) == []
    assert _recorded(cell, "G-VERIFY")["status"] == "timeout"


def test_only_the_timed_out_gate_is_reverted(tmp_path):
    """The sweep runs three gates per cell. A timeout in one must not roll back
    the fresh evidence the other two just earned -- that would make the guard
    cost coverage every time it fired."""
    cell = _cell(tmp_path, {"G-VERIFY": _GREEN, "G-DIFF": _GREEN,
                            "G-GOLD": _GREEN})
    prior = restamp_gate.prior_gates(cell, ["G-VERIFY", "G-DIFF", "G-GOLD"])
    fresh = {"status": "pass", "checked_at": "2026-08-16T00:00:00Z",
             "sources": {"Solution.lean": "a" * 64}}
    meta = json.loads((cell / "meta.json").read_text())
    meta["gates"]["G-VERIFY"] = {"status": "timeout"}
    meta["gates"]["G-DIFF"] = dict(fresh)
    meta["gates"]["G-GOLD"] = dict(fresh)
    (cell / "meta.json").write_text(json.dumps(meta))

    restored = restamp_gate.undo_timeouts(
        cell, [R("G-VERIFY", "timeout"), R("G-DIFF", "pass"),
               R("G-GOLD", "pass")], prior)
    assert restored == ["G-VERIFY"]
    assert _recorded(cell, "G-VERIFY") == _GREEN
    assert _recorded(cell, "G-DIFF") == fresh          # kept its new digests
    assert _recorded(cell, "G-GOLD") == fresh


def test_reverting_preserves_the_rest_of_the_record(tmp_path):
    """It rewrites meta.json, so everything else in the file has to survive:
    the operator caps, the audit fields, other gates' stamps."""
    cell = _cell(tmp_path, {"G-VERIFY": dict(_GREEN, timeout_seconds=1800),
                            "G-PBT": {"status": "pass", "note": "keep me"}})
    prior = restamp_gate.prior_gates(cell, ["G-VERIFY"])
    meta = json.loads((cell / "meta.json").read_text())
    meta["gates"]["G-VERIFY"] = {"status": "timeout"}
    meta["float_encoding"] = "ieee32"
    (cell / "meta.json").write_text(json.dumps(meta))

    restamp_gate.undo_timeouts(cell, [R("G-VERIFY", "timeout")], prior)
    got = json.loads((cell / "meta.json").read_text())
    assert got["gates"]["G-VERIFY"]["timeout_seconds"] == 1800
    assert got["gates"]["G-PBT"]["note"] == "keep me"
    assert got["float_encoding"] == "ieee32"
    assert got["schema_version"] == 1


def test_an_unreadable_meta_reverts_nothing(tmp_path):
    """Rather than writing a reconstructed file over whatever is there."""
    cell = _cell(tmp_path, {"G-VERIFY": _GREEN})
    prior = restamp_gate.prior_gates(cell, ["G-VERIFY"])
    (cell / "meta.json").write_text("{not json")
    assert restamp_gate.undo_timeouts(cell, [R("G-VERIFY", "timeout")],
                                      prior) == []
    assert (cell / "meta.json").read_text() == "{not json"


def test_prior_gates_on_an_unreadable_meta_is_empty(tmp_path):
    cell = tmp_path / "x" / "velvet"
    cell.mkdir(parents=True)
    (cell / "meta.json").write_text("{nope")
    assert restamp_gate.prior_gates(cell, ["G-VERIFY"]) == {}


def test_a_cell_another_holder_had_is_left_for_the_next_pass():
    """The resume file has to name the cells nobody measured, not just the ones a
    wall clock beat.

    A re-stamp pass skips a cell another writer holds, which is right -- two
    writers on one meta.json is how a record gets lost. But the cell still has no
    fresh stamp, so it belongs in the file a relaunch reads. Omitting it lets the
    wrapper that resumes from that file read an empty resume list as "every cell
    measured", so a pass whose cells were all held reports success with none of
    its stamps taken.
    """
    rows = [{"instance_id": "a", "backend": "velvet", "status": "busy"},
            {"instance_id": "b", "backend": "lean", "status": "unmeasured"},
            {"instance_id": "c", "backend": "nagini", "status": "ok"},
            {"instance_id": "d", "backend": "nagini", "status": "blocked"},
            {"instance_id": "e", "backend": "lean", "status": "missing"}]
    left = [(r["instance_id"], r["backend"]) for r in
            restamp_gate.unmeasured_rows(rows)]
    assert left == [("a", "velvet"), ("b", "lean")]


def test_prior_gates_ignores_a_non_dict_record(tmp_path):
    """A legacy record can carry a string-valued gate key; treating one as a
    record would put a string where a stamp belongs."""
    cell = _cell(tmp_path, {"G-VERIFY": "pass"})
    assert restamp_gate.prior_gates(cell, ["G-VERIFY"]) == {}


# ------------------------------------------------------- absorbed regate_gates --
# The behaviours the deleted `regate_gates.py` carried, now flags here: wait for a
# held cell instead of skipping it, and report "nobody measured this" as its own
# exit code rather than as a red gate.

def test_waiting_for_a_held_cell_gives_up_rather_than_stamping(tmp_path):
    """A cell held for the whole wait must raise, not proceed.

    The failure this forbids is the reason the wait exists at all: two writers on
    one meta.json, last one wins, and the loser's verdict is gone with no record
    that it existed.
    """
    from pbt_port_fleet import CellBusy, cell_lock
    cell = _cell(tmp_path, {"G-VERIFY": _GREEN})
    with cell_lock(cell):                      # another driver holds it
        with pytest.raises(CellBusy):
            with restamp_gate.cell_lock_waiting(cell, wait=1, poll=1):
                pytest.fail("entered the body while the cell was held")


def test_waiting_acquires_a_free_cell_and_releases_it(tmp_path):
    """And the claim really is released, so a second pass is not locked out by
    the first -- the flock lives on the inode, not on the process."""
    from pbt_port_fleet import cell_lock
    cell = _cell(tmp_path, {"G-VERIFY": _GREEN})
    with restamp_gate.cell_lock_waiting(cell, wait=0, poll=1):
        pass
    with cell_lock(cell):
        pass


def test_a_body_raising_cellbusy_is_not_retried(tmp_path):
    """The retry wraps the CLAIM only. Retrying the body would run the gates
    twice on one cell, and the second run would be the one that got recorded."""
    from pbt_port_fleet import CellBusy
    cell = _cell(tmp_path, {"G-VERIFY": _GREEN})
    entered = []
    with pytest.raises(CellBusy):
        with restamp_gate.cell_lock_waiting(cell, wait=600, poll=1):
            entered.append(1)
            raise CellBusy("from the body")
    assert entered == [1]


def test_an_all_busy_pass_is_not_a_verdict():
    """Exit 3, not 1. A caller that read "every cell busy" as "every gate red"
    routes a repair at cells nobody looked at."""
    busy = [{"status": "busy"}, {"status": "busy"}]
    assert restamp_gate.exit_code(busy) == 3
    assert restamp_gate.exit_code([{"status": "ok"}, {"status": "busy"}]) == 1
    assert restamp_gate.exit_code([{"status": "ok"}]) == 0
    assert restamp_gate.exit_code([{"status": "blocked"}]) == 1
    assert restamp_gate.exit_code([]) == 0


@pytest.mark.parametrize("argv,want", [
    (["--gates", "G-CONF,G-AX"], ["G-CONF", "G-AX"]),
    (["--gates", "G-CONF", "G-AX"], ["G-CONF", "G-AX"]),
    (["--gates", "G-PBT"], ["G-PBT"]),
])
def test_both_gate_spellings_parse_to_the_same_names(argv, want, tmp_path,
                                                     monkeypatch, capsys):
    """Comma and space have to agree. Feeding one spelling to a parser expecting
    the other stamps meta.json under a key like 'G-CONF,G-AX' -- a record for a
    gate that does not exist, which green_check reads as an error the cell can
    never clear."""
    seen = {}

    def fake_one(iid, backend, gates, bench_dir, wait=0, poll=120):
        seen["gates"] = list(gates)
        return {"instance_id": iid, "backend": backend, "status": "ok",
                "gates": {}, "detail": ""}

    monkeypatch.setattr(restamp_gate, "one", fake_one)
    monkeypatch.setattr(sys, "argv", ["restamp_gate.py", "--benchmark-dir",
                                      str(tmp_path), *argv,
                                      "--cell", "django__django-1", "velvet"])
    assert restamp_gate.main() == 0
    assert seen["gates"] == want


def test_a_cell_list_and_a_named_cell_are_exclusive(tmp_path, monkeypatch):
    """Both, or neither, is a caller bug rather than a thing to guess at: the two
    would silently disagree about which cells the pass covered."""
    for extra in ([], ["--cells", str(tmp_path / "c.tsv"),
                       "--cell", "django__django-1", "velvet"]):
        monkeypatch.setattr(sys, "argv", ["restamp_gate.py", "--benchmark-dir",
                                          str(tmp_path), "--gates", "G-CONF",
                                          *extra])
        with pytest.raises(SystemExit):
            restamp_gate.main()
