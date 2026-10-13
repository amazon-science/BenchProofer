# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The G-PANEL badge must publish a rollup, not the three role notes again.

`gates/panel.py:43` re-derives the rollup's `detail` on every gate run by joining
the three per-role records' notes, so every character of it is already published
by the three per-role cards `data.audit_notes` renders. The badge tooltip
(`_macros.html:13`) prints `note` as plain text and never runs it through `md()`,
so the rollup published thousands of unformatted characters, three times over.
These tests pin the compact derivation and, just as importantly, the two things it
must NOT do: recompute the status, or swallow a legacy collective record that
nothing else carries.
"""
from backend import data, settings

_TITLES = {"G-PANEL-1": "spec-too-weak", "G-PANEL-2": "faithfulness",
           "G-PANEL-3": "leakage"}
_VERDICTS = {"G-PANEL-1": "SOUND", "G-PANEL-2": "FAITHFUL",
             "G-PANEL-3": "NO-LEAKAGE"}
# distinctive bodies: long enough that a concatenation is unmistakable
_BODY = {r: (f"{_TITLES[r]} account. " + f"role-{r[-1]}-evidence " * 120)
         for r in data.PANEL_ROLES}


def _roles(present=data.PANEL_ROLES, status="pass") -> dict:
    return {r: {"status": status, "detail": _BODY[r],
                "agent_verdict": _VERDICTS[r], "model": "m"}
            for r in present}


def _rollup_detail(roles: dict) -> str:
    """What `gates/panel.py:43-48` writes: the roles' notes joined with '; '."""
    # U+2014 by escape, because panel.py emits one and this fixture has to be
    # byte-faithful to the record it stands in for.
    parts = [f"{r} ({_TITLES[r]}): {v['status']} — {v['detail']}"
             for r, v in sorted(roles.items())]
    out = "; ".join(parts)
    missing = [r for r in data.PANEL_ROLES if r not in roles]
    if missing:
        out += f"; unrecorded roles: {missing}"
    return out


def _meta(roles: dict, *, rollup_status="pass", rollup_detail=None,
          extra_rollup=None) -> dict:
    g = dict(roles)
    rec = {"status": rollup_status,
           "detail": (_rollup_detail(roles) if rollup_detail is None
                      else rollup_detail),
           "data": {"roles": {r: dict(v) for r, v in roles.items()}}}
    rec.update(extra_rollup or {})
    g["G-PANEL"] = rec
    g["G-EQ"] = {"status": "pass", "detail": "7 attacks re-run, none breaks the "
                 "spec; positive control verifies", "agent_verdict": "TIGHT"}
    return {"gates": g}


# ---- the rollup row itself ---------------------------------------------------

def test_rollup_note_is_not_the_role_details_again():
    """The defect: the badge published the concatenation the roles already show."""
    note = data.gates_from_meta(_meta(_roles()))["G-PANEL"]["note"]
    for r, body in _BODY.items():
        assert body not in note, f"{r}'s account is republished in the rollup"
        assert body[:60] not in note
    assert len(note) < 400, f"rollup note is {len(note)} chars: {note[:200]}"


def test_rollup_note_says_what_it_summarises_and_where_the_evidence_is():
    note = data.gates_from_meta(_meta(_roles()))["G-PANEL"]["note"]
    for r, title in _TITLES.items():
        assert r in note and title in note
        assert _VERDICTS[r] in note, f"{r}'s recorded verdict token is missing"
    assert "pass" in note
    assert "Audit verdicts" in note, "a reader is not told where the evidence is"
    assert "—" not in note


def test_a_failing_role_is_named_in_the_rollup_note():
    roles = _roles()
    roles["G-PANEL-2"] = {"status": "fail", "detail": _BODY["G-PANEL-2"],
                          "agent_verdict": "UNFAITHFUL"}
    note = data.gates_from_meta(
        _meta(roles, rollup_status="fail"))["G-PANEL"]["note"]
    assert "G-PANEL-2 (faithfulness): fail / UNFAITHFUL" in note
    assert len(note) < 400


def test_the_rollup_status_is_read_from_the_record_never_recomputed():
    """Requirement: the row keeps its real status. If the record and the roles
    ever disagree, the board must show what was recorded, not its own opinion."""
    g = data.gates_from_meta(_meta(_roles(), rollup_status="fail"))
    assert g["G-PANEL"]["status"] == "fail"
    g2 = data.gates_from_meta(_meta(_roles(status="fail"),
                                    rollup_status="pass"))
    assert g2["G-PANEL"]["status"] == "pass"
    # and the row is never dropped or invented
    assert "G-PANEL" in g
    assert "G-PANEL" not in data.gates_from_meta({"gates": _roles()})


def test_the_role_records_are_left_alone():
    g = data.gates_from_meta(_meta(_roles()))
    for r in data.PANEL_ROLES:
        assert g[r]["note"] == _BODY[r]
        assert g[r]["detail"] == _BODY[r]
        assert g[r]["agent_verdict"] == _VERDICTS[r]
    # the rollup's own recorded detail is untouched: only `note` (what the
    # tooltip prints) is derived, so a reader of the raw record loses nothing
    assert _BODY["G-PANEL-1"] in g["G-PANEL"]["detail"]


def test_audit_notes_still_shows_only_g_eq_and_the_three_roles(monkeypatch):
    monkeypatch.setattr(data, "gates",
                        lambda *a, **k: data.gates_from_meta(_meta(_roles())))
    got = data.audit_notes("verified", "nagini", "iid")
    assert [a["gate"] for a in got] == ["G-EQ"] + data.PANEL_ROLES
    for a in got:
        if a["gate"] in _BODY:
            assert "role-" in a["note"], "a role card lost its account"


# ---- the records the derivation must not swallow -----------------------------

def test_a_legacy_collective_record_still_publishes_its_own_text():
    """`gates/panel.py:52-55` falls back to a collective G-PANEL entry when no
    per-role record exists. Nothing else on the page carries that text -- there
    are no role cards to point at -- so it must be published as recorded."""
    legacy = ("collective panel verdict: 3 roles run in one pass, no "
              "spec-too-weak finding, no drift, no leakage. " + "detail " * 200)
    g = data.gates_from_meta({"gates": {"G-PANEL": {"status": "pass",
                                                    "detail": legacy}}})
    assert g["G-PANEL"]["note"] == legacy
    assert g["G-PANEL"]["status"] == "pass"


def test_a_roleless_stub_keeps_its_recorded_shape():
    """A role-less rollup record: status skip/n-a, empty detail, sometimes a
    `reason`. Nothing to derive, nothing to lose."""
    g = data.gates_from_meta(
        {"gates": {"G-PANEL": {"status": "skip", "reason": "blocked"}}})
    assert g["G-PANEL"]["note"] == ""
    assert g["G-PANEL"]["status"] == "skip" and g["G-PANEL"]["reason"] == "blocked"


def test_a_partial_record_names_the_unrecorded_role():
    """A cell with 1-2 roles: every recorded role has a card, so the derivation
    is safe -- but it must not imply the missing one passed."""
    roles = _roles(present=["G-PANEL-1", "G-PANEL-3"])
    note = data.gates_from_meta(_meta(roles))["G-PANEL"]["note"]
    assert "G-PANEL-2 (faithfulness): UNRECORDED" in note
    assert "three panel roles" not in note, "3 roles claimed, 2 recorded"
    assert _BODY["G-PANEL-1"] not in note and len(note) < 400


def test_a_role_with_no_verdict_token_publishes_its_status_alone():
    roles = {"G-PANEL-1": {"status": "pass", "detail": "x"},
             "G-PANEL-2": {"status": "pass", "detail": "x", "agent_verdict": ""},
             "G-PANEL-3": {"status": "pass", "detail": "x",
                           "agent_verdict": "NO-LEAKAGE"}}
    note = data.gates_from_meta(_meta(roles))["G-PANEL"]["note"]
    assert "G-PANEL-1 (spec-too-weak): pass;" in note
    assert "G-PANEL-2 (faithfulness): pass;" in note
    assert "G-PANEL-3 (leakage): pass / NO-LEAKAGE." in note


def test_a_role_recorded_as_a_bare_status_string_is_not_dropped():
    """`gates_from_meta` normalizes a non-dict gate value to {'status': ...};
    such a role has a card, so the rollup must name it rather than call it
    UNRECORDED."""
    g = {"G-PANEL-1": "pass", "G-PANEL-2": {"status": "pass", "detail": "x",
                                            "agent_verdict": "FAITHFUL"},
         "G-PANEL-3": {"status": "pass", "detail": "x",
                       "agent_verdict": "NO-LEAKAGE"},
         "G-PANEL": {"status": "pass", "detail": "long " * 900}}
    note = data.gates_from_meta({"gates": g})["G-PANEL"]["note"]
    assert "G-PANEL-1 (spec-too-weak): pass" in note
    assert "UNRECORDED" not in note and len(note) < 400


# ---- the real corpus --------------------------------------------------------

def _cells(bm, n=12):
    ids = data.all_instance_ids(bm)
    step = max(1, len(ids) // n)
    for iid in ids[::step][:n]:
        for bk in settings.BACKENDS:
            g = data.gates(bm, bk, iid)
            if g:
                yield iid, bk, g


def test_recorded_cells_publish_a_compact_rollup():
    seen = 0
    for iid, bk, g in _cells("verified"):
        rec = g.get("G-PANEL")
        if not rec:
            continue
        roles = [r for r in data.PANEL_ROLES if g.get(r)]
        if not roles:
            continue           # legacy/stub: its own text, checked above
        seen += 1
        note = rec["note"]
        assert len(note) < 400, f"{iid}/{bk}: rollup note is {len(note)} chars"
        for r in roles:
            body = g[r].get("note") or ""
            assert body[:120] not in note, f"{iid}/{bk}: {r} republished"
            assert (g[r].get("status") or "") in note
        assert rec["status"] == ((data.meta("verified", bk, iid).get("gates")
                                 or {}).get("G-PANEL") or {}).get("status")
    assert seen >= 20, f"only {seen} recorded cells sampled"
