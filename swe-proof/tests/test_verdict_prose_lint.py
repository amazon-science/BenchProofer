# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The record end and the published end of an audit record obey different rules.

`verdict.md` is what a reader of the released corpus sees, so it gets the full
release-prose rule set. `meta.json` is what a driver reads back to decide what
to re-run, and `build_one.run_audit_stage` deliberately keeps the host-side
sentences there -- "load average was 12/4" is how a role burned by load is told
apart from one that found a defect, and `publish_note` removes it when the record
is rendered anyway.

Holding both ends to the published rule set was worse than pedantic: the lint
called a cell dirty at the one end that is supposed to carry those sentences,
and `--fix` answered by deleting the diagnostic. The tests below pin the split,
and the last one pins the property that makes any of it safe -- a repair has to
clear its own finding, or the lint reports the same cell forever and the release
check it backs stops meaning anything.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

import verdict_prose_lint as lint

from swebench_unified.construct.release_prose import findings

ROOT = Path(__file__).resolve().parents[1]

HOST = "Host health: load average was 12/4 while this role ran."
SCRATCH = "Wrote the attack to /tmp/sbu_audit_eq_astropy_9k2j/atk_6.py and re-ran it."


def _meta(note: str) -> dict:
    return {"gates": {"G-PANEL-2": {"status": "pass", "note": note}}}


# ---- the record end keeps what it is meant to keep ----

def test_host_narration_in_meta_is_not_dirt():
    """The class `build_one` records on purpose. Reported once as a finding, it
    would be repaired away on the next `--fix` and lost for good."""
    assert findings(HOST) == ["host-narration"], "premise: the rule does fire"
    _, broken = lint.scan_meta(_meta(HOST))
    assert broken == []


def test_host_narration_in_meta_survives_the_repair():
    meta, _ = lint.scan_meta(_meta(HOST))
    assert meta["gates"]["G-PANEL-2"]["note"] == HOST


def test_a_scratch_path_in_meta_is_dirt_and_is_repaired():
    meta, broken = lint.scan_meta(_meta(SCRATCH))
    assert broken == ["scratch-path"]
    assert "/tmp/" not in meta["gates"]["G-PANEL-2"]["note"]
    assert "atk_6.py" in meta["gates"]["G-PANEL-2"]["note"], \
        "the basename is how the rest of the record refers to the same attack"


def test_repairing_a_path_does_not_take_the_host_sentence_with_it():
    """The reason the meta end uses `scrub_paths` and not `sanitize`: a field with
    both faults must lose the path and keep the diagnostic."""
    meta, broken = lint.scan_meta(_meta(f"{SCRATCH}\n\n{HOST}"))
    assert broken == ["scratch-path"]
    out = meta["gates"]["G-PANEL-2"]["note"]
    assert "/tmp/" not in out
    assert "load average was 12/4" in out


# ---- the published end is held to the published rule set ----

def test_host_narration_in_verdict_md_is_dirt():
    assert "host-narration" in lint.scan_markdown(f"## Role 3\n\n{HOST}\n")


def test_the_published_render_of_a_kept_sentence_is_clean():
    """Why the split is not a hole: the note the card shows is `publish_note` of
    the stored field, so keeping the sentence in the record publishes nothing."""
    from swebench_unified.construct.release_prose import publish_note
    assert findings(publish_note(HOST)) == []


# ---- convergence: what the lint reports, its repair must clear ----

@pytest.mark.parametrize("text", [
    SCRATCH,
    f"{SCRATCH}\n\n{HOST}",
    "Reference worktree /home/someone/wt_13236 with patch.diff applied.",
    "Built at /tmp/atk2f_13236_4xlr and re-ran the suite there.",
    "POSITIVE CONTROL: /tmp/.../positive_control.lean -> exit 0.",
])
def test_the_meta_repair_clears_its_own_finding(text):
    """A repair that leaves its finding standing makes the exit status permanent:
    dirty, rewritten to itself, dirty again. Every dirty field is a path
    class."""
    meta, broken = lint.scan_meta(_meta(text))
    assert broken, "premise: this text is dirty"
    _, again = lint.scan_meta(meta)
    assert again == [], f"still dirty after repair: {again}"


def test_the_verdict_repair_clears_its_own_finding():
    md = f"## Role 3 — G-PANEL-2: pass\n\n- **machine verdict:** {SCRATCH}\n\n{HOST}\n"
    assert lint.scan_markdown(md), "premise"
    assert lint.scan_markdown(lint.clean_markdown(md)) == []


def test_a_fenced_transcript_is_judged_by_the_reference_rules_alone():
    """A verifier transcript inside a fence is evidence, and holding it to the
    prose rules is how a cell keeps reporting a class no `--fix` would touch."""
    md = f"## Role 1\n\n```\n{HOST}\n```\n"
    assert "host-narration" not in lint.scan_markdown(md)


def test_the_two_rule_sets_are_declared_and_disjoint():
    assert lint.RECORD_ONLY & lint.PATH_RULES == frozenset(), \
        "a class cannot be both kept in the record and a reason to rewrite it"
    assert "host-narration" in lint.RECORD_ONLY
    assert lint.PATH_RULES <= set(
        findings(f"{SCRATCH} /home/someone/x. All work in "
                 "/tmp/sbu_audit_eq_astropy_9k2j.")), \
        "PATH_RULES must name real finding classes, not aspirational ones"


def test_scan_meta_walks_the_per_role_record_not_just_the_gate():
    """A multi-role gate keeps each role's own account one level down, and reading
    only the top level found 20 dirty records where there were 89."""
    meta = {"gates": {"G-PANEL": {"data": {"roles": {
        "G-PANEL-2": {"detail": SCRATCH}}}}}}
    fixed, broken = lint.scan_meta(json.loads(json.dumps(meta)))
    assert broken == ["scratch-path"]
    assert "/tmp/" not in fixed["gates"]["G-PANEL"]["data"]["roles"][
        "G-PANEL-2"]["detail"]


# ---- the label a removed reference left with nothing to say ----

def test_a_stranded_label_in_meta_is_dirt_and_is_repaired():
    meta, broken = lint.scan_meta(_meta("All work; bundle never modified."))
    assert broken == ["stranded-workspace-label"]
    assert meta["gates"]["G-PANEL-2"]["note"] == "bundle never modified."
    assert lint.scan_meta(json.loads(json.dumps(meta)))[1] == [], "converged"


def test_a_transcript_field_is_not_dirty_for_a_class_its_repair_leaves():
    """`sanitize_code` keeps a transcript's alignment, so a fenced field cannot be
    repaired for this class: reporting it there would report a defect the repair
    does not touch, and then report it again -- the reason `CODE_EXEMPT` exists."""
    cx = {"gates": {"G-EQ": {
        "counterexample": "atk_3 run in   (fresh, exclusive) -> exit 1"}}}
    assert findings(cx["gates"]["G-EQ"]["counterexample"]) == \
        ["stranded-workspace-label"], "premise: the class does fire on the text"
    fixed, broken = lint.scan_meta(json.loads(json.dumps(cx)))
    assert broken == []
    assert fixed == cx


def test_the_narrow_route_reports_and_repairs_a_stranded_label():
    md = ("## Role 1 — G-EQ (refinement fidelity): pass\n"
          "\n"
          "The spec rejects all 8 rivals.\n"
          "Scratch dir:  (fresh, exclusive).\n"
          "HYGIENE: all work; the bundle was never modified.\n")
    assert lint.scan_markdown(md) == ["stranded-workspace-label",
                                      "workspace-narration"]
    assert set(lint.scan_markdown(md)) <= lint.PATH_RULES | lint.NARRATION, \
        "so the record takes the narrow route, which must clear both"
    out = lint.clean_published(md)
    assert lint.scan_markdown(out) == []
    assert lint.clean_published(out) == out, "idempotent"
    assert "The spec rejects all 8 rivals." in out
    assert "Scratch dir" not in out
    assert "HYGIENE" not in out, "the housekeeping line said nothing else"
    assert "\n\n\n" not in out, "the emptied line is not left as a hole"


def test_a_stranded_label_inside_a_retained_body_is_left_alone():
    """The same words are prose above the fence and quoted evidence inside it.
    `audit_recheck` reads the body back byte for byte."""
    md = ("## Role 1 — G-EQ (refinement fidelity): pass\n\n"
          "Attack 1 — `atk_1.py` → rejected\n\n"
          "```python\n# Scratch dir:  (fresh, exclusive).\ndef f(): pass\n```\n\n"
          "Scratch dir:  (fresh, exclusive).\n")
    for route in (lint.clean_published, lint.clean_markdown):
        out = route(md)
        assert "# Scratch dir:  (fresh, exclusive)." in out, route.__name__
        assert out.count("Scratch dir") == 1, "only the prose line went"


# ---- the battery auditors' own notes: paths, and nothing else ----
#
# `pbt_audit` is not rendered by viz, so no sentence in it is ever published and
# the sentence rules have no reader to protect. Its bytes ship, though, so the
# path rules do apply -- and they are the only ones that may, because these are
# the working notes the next audit is routed by.

MIRROR = "5 build logs under ~/audit_astropy-13033_results/: GOLD_weak-a.log."


def test_a_path_in_the_battery_notes_is_dirt_and_is_repaired():
    meta = {"pbt_audit": {"notes": MIRROR,
                          "witness_evidence": [{"build_logs": SCRATCH}]}}
    fixed, broken = lint.scan_meta(json.loads(json.dumps(meta)))
    assert sorted(broken) == [lint.AUDIT_PATH_RULE, "scratch-path"]
    assert "~/audit_" not in fixed["pbt_audit"]["notes"]
    assert "GOLD_weak-a.log" in fixed["pbt_audit"]["notes"]
    assert "/tmp/" not in fixed["pbt_audit"]["witness_evidence"][0]["build_logs"]


def test_the_mirror_class_is_named_by_the_scrubber_not_the_classifier():
    """The reason the walk cannot classify first: `scrub_paths` clears this and
    `findings` does not name it, so a finding-led walk would repair fields
    without ever calling their cell dirty -- and the sweep only writes a cell it
    called dirty."""
    from swebench_unified.construct.release_prose import scrub_paths
    assert scrub_paths(MIRROR) != MIRROR
    assert findings(MIRROR) == []
    assert lint.AUDIT_PATH_RULE not in lint.PATH_RULES


def test_the_battery_notes_keep_the_sentences_the_next_audit_reads():
    """The whole point of the narrower rule set at this end."""
    _, broken = lint.scan_meta({"pbt_audit": {"notes": HOST}})
    assert broken == []


def test_the_battery_repair_clears_its_own_finding():
    once, _ = lint.scan_meta({"pbt_audit": {"notes": MIRROR + " " + SCRATCH}})
    _, again = lint.scan_meta(json.loads(json.dumps(once)))
    assert again == []


# ---- the published end: build-time narration and a republished account ----
#
# One record, carrying every shape the repair has to survive: a role heading, the
# machine-verdict bullet the record's grammar is read from, narration prose, an
# attack ledger line over a retained body, a positive control, the auditor's own
# fenced evidence block, and the role's own account published a second time at the
# end of its section. It is the fixture for the routing, convergence, idempotence
# and invariance tests below, because those four questions are only interesting
# together.
#
# The `$SCRATCH` in the retained attack body is deliberate and is the tell for the
# rule that matters most here: a fence a checker reads back is passed through, and
# an auditor's own fenced block is not.

ACCOUNT = (
    "The spec admits no weaker implementation. All 10 same-spec attacks were"
    " re-run and 8 were REJECTED by the verifier (exit 1).\n"
    "\n"
    "The 2 that verified are behaviourally identical to the gold impl on every"
    " input the postcondition constrains, so neither is a weakening.")

NARRATION = (
    "<!-- generated by backfill_verdict_md.py 2026-08-04 -->\n"
    "PROTOCOL EXECUTED (in $SCRATCH, project root $ROOT).\n"
    "Verify: `timeout 360 bash scripts/lean_verify.sh atk_1.lean 300`.\n"
    "SCOPE: project root is $ROOT. The spec pins result exactly.")


def _record() -> str:
    return ("# a__b-1 — lean\n"
            "\n"
            "## Role 3 — G-EQ (refinement fidelity): pass\n"
            "\n"
            "- **status (recorded):** `pass`\n"
            "\n"
            f"{NARRATION}\n"
            "\n"
            f"{ACCOUNT}\n"
            "\n"
            "Prepatch bug re-encoded as an attack: `True`.\n"
            "\n"
            "Attack 1 — `atk_1.lean` → rejected\n"
            "\n"
            "```lean\n"
            "-- impl-start\n"
            "def f (xs : List Nat) : Nat := xs.length   -- ran from $SCRATCH\n"
            "-- impl-end\n"
            "```\n"
            "\n"
            "**Positive control** — `pos_control.lean` → verifies\n"
            "\n"
            "```lean\n"
            "-- impl-start\n"
            "def f (xs : List Nat) : Nat := xs.foldl (fun a _ => a + 1) 0\n"
            "-- impl-end\n"
            "```\n"
            "\n"
            "Counterexample / evidence:\n"
            "\n"
            "```\n"
            "  - $SCRATCH/patch_nostream.diff still does NOT resolve.\n"
            "```\n"
            "\n"
            f"{ACCOUNT}\n")


def test_a_record_whose_faults_are_narration_and_shape_takes_the_narrow_route():
    """`clean_markdown` also promotes headings and backticks identifiers, none of
    which any rule here reports. A dirty cell routes this way, so the diff stays a
    diff about the classes reported."""
    broken = set(lint.scan_markdown(_record()))
    assert broken, "premise: the fixture is dirty"
    assert broken <= lint.STRUCTURAL | lint.NARRATION, broken
    assert {"placeholder-path", "host-timeout", "build-tool-banner",
            "republished-account"} <= broken


def test_the_narrow_repair_clears_every_class_it_reported():
    """A repair that leaves its own finding standing makes the exit status
    permanent: dirty, rewritten to itself, dirty again."""
    out = lint.clean_published(_record())
    assert lint.scan_markdown(out) == []


def test_the_narrow_repair_is_idempotent():
    once = lint.clean_published(_record())
    assert lint.clean_published(once) == once


def test_a_placeholder_in_a_fenced_account_is_repaired_by_the_route_that_reports_it():
    """`placeholder-path` is a NARRATION class, so a cell whose ONLY fault is a
    `$SCRATCH` inside the auditor's own fenced block takes the narrow route --
    which therefore has to rewrite references inside a fence too, or the lint
    reports that cell forever. The same non-convergence `internal-diagnostic` was
    excluded for, one class over."""
    md = ("## Role 1 — G-EQ (refinement fidelity): pass\n"
          "\n"
          "Counterexample / evidence:\n"
          "\n"
          "```\n"
          "  - ran as $SCRATCH/atk_1.lean -> exit 1 (unsolved goals)\n"
          "```\n")
    assert lint.scan_markdown(md) == ["placeholder-path"]
    out = lint.clean_published(md)
    assert lint.scan_markdown(out) == []
    assert "atk_1.lean -> exit 1 (unsolved goals)" in out and "$SCRATCH" not in out
    assert out.count("\n") == md.count("\n"), "a fence never loses a line"


def test_a_placeholder_inside_a_retained_body_is_reported_by_nothing():
    """The other side of that split, and the reason it is a split. Nothing may
    rewrite a block `audit_recheck.parse_verdict` returns: it re-verifies the
    attacks, and `check_stamp_freshness._retained_control` compares the control
    against the solution on disk, byte for byte. A rewritable reference lives in
    the auditor's own blocks rather than in a retained body anyway, so this costs
    the release nothing."""
    md = ("## Role 1 — G-EQ (refinement fidelity): pass\n"
          "\n"
          "**Positive control** — `pos_control.lean` → verifies\n"
          "\n"
          "```lean\n"
          "-- derived in $SCRATCH from the frozen spec view\n"
          "def f : Nat := 0\n"
          "```\n")
    assert lint.scan_markdown(md) == []
    assert lint.clean_published(md) == md
    assert lint.clean_markdown(md) == md


def test_the_repair_leaves_the_record_the_recheck_and_the_stamp_check_read():
    """The whole safety argument, stated as the two readers of this file:
    `audit_recheck.parse_verdict` re-verifies the attacks it finds here, and
    `check_stamp_freshness._retained_control` resolves a gate's positive control
    from that gate's own section and compares it against the solution on disk.
    Both read this file through `parse_verdict`, so equality of its output is
    the property the repair has to preserve."""
    import audit_recheck

    md = _record()
    before, after = audit_recheck.parse_verdict(md), \
        audit_recheck.parse_verdict(lint.clean_published(md))
    assert before == after
    assert before["G-EQ"]["control"], "premise: the fixture retains a control"
    assert before["G-EQ"]["attacks"], "premise: the fixture retains an attack"
    assert before["G-EQ"]["prepatch_reproduced"] is True


def test_the_repair_removes_the_second_copy_and_no_evidence():
    out = lint.clean_published(_record())
    assert out.count("neither is a weakening") == 1, "the republished copy goes"
    assert out.count("def f (xs : List Nat) : Nat := xs.length") == 1
    assert "xs.foldl (fun a _ => a + 1) 0" in out, "the positive control stays"
    assert "8 were REJECTED by the verifier (exit 1)" in out
    assert "timeout 360" not in out and "backfill_verdict_md" not in out
    assert "$ROOT" not in out, "the prose references go"
    assert "patch_nostream.diff still does NOT resolve." in out and \
        "$SCRATCH/patch_nostream.diff" not in out, "and so do the fenced ones"
    assert "def f (xs : List Nat) : Nat := xs.length   -- ran from $SCRATCH" in out, \
        "except inside a body a checker reads back"


def test_the_two_repair_routes_name_disjoint_classes():
    assert lint.STRUCTURAL & lint.NARRATION == frozenset()
    assert lint.NARRATION & lint.RECORD_ONLY == frozenset()
    from swebench_unified.construct.release_prose import publish_findings
    assert set(publish_findings(NARRATION)) <= lint.NARRATION, \
        "NARRATION must name the classes the published rule set reports"


def test_every_class_set_is_disjoint_from_every_other():
    """The sets are what the sweep routes by, so a class in two of them is a cell
    repaired one way and reported another. The heading and paragraph sets joined
    STRUCTURAL and NARRATION on the narrow side, which is only sound while no class
    is in both a repair set and the advisory set."""
    sets = {"STRUCTURAL": lint.STRUCTURAL, "NARRATION": lint.NARRATION,
            "PARAGRAPH": lint.PARAGRAPH, "HEADING_FIX": lint.HEADING_FIX,
            "PATH_RULES": lint.PATH_RULES}
    for a in sets:
        for b in sets:
            if a < b:
                assert sets[a] & sets[b] == frozenset(), f"{a} & {b}"
        assert sets[a] & lint.ADVISORY == frozenset(), \
            f"{a} is repaired, so it cannot also be counted-and-left"
    assert lint.HEADING_ADVISORY <= lint.ADVISORY
    assert "wall-of-text-unbreakable" in lint.ADVISORY


def test_the_placeholder_the_fleet_reads_back_stays_in_the_record():
    """`$SCRATCH` in `meta.json` is where a re-run would look, and the verifier's
    cap and the resolve line's `retries=` are read back the same way. This class is
    published-only, and `scan_meta` reporting it would ask the record to stop
    being what a re-run reads."""
    meta, broken = lint.scan_meta(_meta("Attacks at $SCRATCH/atk_1.lean; "
                                       "run_resolve(timeout=1800, retries=1)."))
    assert broken == []
    assert "$SCRATCH/atk_1.lean" in meta["gates"]["G-PANEL-2"]["note"]
    assert "retries=1" in meta["gates"]["G-PANEL-2"]["note"]


# ---- the lines a reader PARSES are not prose ----

LABEL = ("Attack 2 — `atk_2.py` → candidate; the auditor's patch does not apply,"
         " so the oracle graded nothing — inconclusive (no report at"
         " /mnt/data/checkout/experiments/logs/run_evaluation/"
         "sbu-resolve-abc1234/report.json)")


def _labelled(label: str = LABEL) -> str:
    return ("## Role 3 — G-EQ (refinement fidelity): pass\n"
            "\n"
            f"{label}\n"
            "\n"
            "```python\n"
            "def f(xs): return len(xs)\n"
            "```\n")


def test_a_recorded_outcome_label_is_left_alone_by_both_repair_routes():
    """`recheck_cell` compares its own re-run against the label it finds here, so
    the label is evidence about what the oracle said and not a sentence. The full
    prose pass rewrites such lines, and some of that is pure damage with no
    finding behind it."""
    md = _labelled()
    assert lint.clean_published(md) == md
    assert lint.clean_markdown(md) == md
    assert lint.scan_markdown(md) == [], "and nothing reports what nothing repairs"


def test_the_reference_in_a_label_is_still_reported_as_an_advisory():
    """Silence would be worse than a class nobody repairs: the host path is real.
    The place to remove it is the field `run_audit_stage` recorded it in."""
    assert lint.ledger_findings(_labelled()) == ["ledger-reference"]
    assert "ledger-reference" in lint.ADVISORY, "counted, never a reason to rewrite"
    assert lint.ledger_findings(_labelled(
        "Attack 2 — `atk_2.py` → rejected (exit 1)")) == []


def test_a_test_path_in_a_label_is_not_published_with_backticks_in_it():
    """The concrete damage: a FAIL_TO_PASS label goes out as
    ``tests/`_core`/test_plot.py`` because the rule that backticks a dunder-ish
    identifier reached a line that is not prose."""
    label = ("Attack 1 — `atk_1.lean` → BROKEN: verifies but does not resolve"
             " [FAIL_TO_PASS fails 1/2: tests/_core/test_plot.py::TestLegend]")
    assert "tests/_core/test_plot.py" in lint.clean_markdown(_labelled(label))


def test_a_body_is_protected_when_a_line_sits_between_its_caption_and_its_fence():
    """`parse_verdict` arms on the caption and takes the NEXT fence, so the caption
    is not always the line above it. This is the reader's own rule, spelled the
    same way, so that a record which does put a line in between cannot offer a
    body to the rewrite."""
    md = ("## Role 1 — G-EQ (refinement fidelity): pass\n"
          "\n"
          "Attack 1 — `atk_1.lean` → rejected\n"
          "\n"
          "- exit 1 (unsolved goals), 41s\n"
          "\n"
          "```lean\n"
          "def f : Nat := 0   -- derived in $SCRATCH\n"
          "```\n")
    assert [k for k, ln in lint.walk(md) if "def f" in ln] == ["retained"]
    assert lint.clean_published(md) == md and lint.clean_markdown(md) == md


def test_neither_route_rewrites_a_line_separator_a_body_quotes():
    """`splitlines()` breaks on U+2028 and five other separators, so a walk that
    rejoins its own output rewrites the source of every attack in a spec ABOUT
    line separators. In such a cell every retained block carries one -- every
    attack body and both positive controls."""
    import audit_recheck

    md = ("## Role 1 — G-EQ (refinement fidelity): pass\n"
          "\n"
          "Attack 1 — `atk_1.lean` → rejected\n"
          "\n"
          "```lean\n"
          "def sep : String := \"a b\"\n"
          "```\n"
          "\n"
          "PROTOCOL EXECUTED (in $SCRATCH).\n")
    for route in (lint.clean_published, lint.clean_markdown):
        out = route(md)
        assert " " in out and "def sep : String := \"a b\"" in out
        assert audit_recheck.parse_verdict(out) == audit_recheck.parse_verdict(md)
        assert "$SCRATCH" not in out, "premise: the route did do its own work"


def test_the_two_routes_agree_on_a_record_that_has_already_been_repaired():
    """Idempotence across the ROUTES, not just within one: a cell repaired by the
    wide route is re-reported by the next sweep and, being clean, repaired by
    neither -- but a record the narrow route would still change is a record whose
    two repairs disagree, and the exit status alternates. The blank-line drift that
    did that is closed in `_publish_body`, and the promotion drift (a removed
    narration line exposes the next sentence as a paragraph lead, which
    `promote_structure` then bolds) by its fixed-point loop: no change on a
    second pass, by either route."""
    md = _record().replace(
        "Prepatch bug re-encoded",
        "Ran in /tmp/sbu_audit_eq_a__b_9k2j and kept the log.\n\n"
        "Prepatch bug re-encoded")
    assert "scratch-path" in lint.scan_markdown(md), "premise: the wide route"
    once = lint.clean_markdown(md)
    assert lint.scan_markdown(once) == []
    assert lint.clean_markdown(once) == once
    assert lint.clean_published(once) == once


# ---- the role heading, against the gate entry it was rendered from ----
#
# Every field of a role heading is derivable from `meta.json` -- the status and the
# label from the entry for the gate the heading names, the advisory word from the
# audit run that scored it -- so a heading that disagrees is repaired from the record
# and never from the role NUMBER: `merge_verdict_md` interleaves a run's sections
# with the blocks of roles it never attempted, so role 3 is not the third gate.
#
# The line between the classes that are repaired and the ones that are only counted
# is whether the record holds what the right heading needs. Where it does not, the
# heading is the surviving evidence and rewriting it is destruction, not repair.

PANEL2 = {"gates": {"G-PANEL-2": {"status": "pass",
                                  "agent_verdict": "FAITHFUL"}}}


def _composed(n: int, gate: str, meta: dict) -> str:
    """The heading `build_one.compose_verdict_md` would write, built here the way
    the composer builds it -- from `_GATE_ROLE_LABEL` and the gate entry -- so that
    the test pins the repair against the composer and not against a copy of its
    output that can drift out of step with it."""
    from swebench_unified.construct.build_one import _GATE_ROLE_LABEL

    e = meta["gates"][gate]
    head = f"## Role {n} — {_GATE_ROLE_LABEL[gate]}: {e['status']}"
    av = e.get("agent_verdict")
    return head + (f" (agent: {av})" if av else "")


@pytest.mark.parametrize("published", [
    "## Role 3 — G-PANEL-2",                      # gate named, nothing else
    "## Role 3 — G-PANEL-2 (faithfulness)",       # labelled, no status
    "## Role 3 — G-PANEL-2 (leakage): pass (agent: FAITHFUL)",   # wrong label
    "## Role 3 — G-PANEL-2 (faithfulness): FAITHFUL",   # agent verdict as status
])
def test_a_heading_the_composer_would_write_differently_is_composed_again(published):
    """The four shapes whose right form is a pure derivation from the record. The
    last is the one that reaches a reader as a wrong answer rather than a missing
    one: the record says `pass`, the heading published `FAITHFUL`, so the reader
    never sees the recorded status and reads an advisory verdict as one."""
    from swebench_unified.construct.release_prose import is_role_heading

    md = f"{published}\n\nThe account.\n"
    classes = lint.heading_findings(md, PANEL2)
    assert set(classes) & lint.HEADING_FIX, classes
    out = lint.fix_headings(md, PANEL2)
    assert out.split("\n")[0] == _composed(3, "G-PANEL-2", PANEL2)
    assert is_role_heading(out.split("\n")[0]), \
        "and the composed shape is one the published rule set still recognises"
    assert out.split("\n")[1:] == md.split("\n")[1:], "and nothing else moved"
    assert lint.heading_findings(out, PANEL2) == [], "the repair clears its finding"
    assert lint.fix_headings(out, PANEL2) == out


def test_a_published_status_the_record_disagrees_with_is_counted_never_rewritten():
    """The recorded status is the source of truth for green, but a published `fail`
    under a recorded `pass` is a mechanical re-gate that landed after the section
    was rendered. Publishing `pass` over it would erase the audit's own conclusion
    to tidy a heading. 2 headings over 1 released cell read this way, both above a
    `status (recorded)` bullet saying the same `fail`; re-rendering the section from
    the fresh fields is the fix, and only the audit stage can."""
    md = "## Role 3 — G-PANEL-2 (faithfulness): fail (agent: FAITHFUL)\n"
    assert lint.heading_findings(md, PANEL2) == ["role-heading-status-stale"]
    assert lint.fix_headings(md, PANEL2) == md
    assert "role-heading-status-stale" in lint.ADVISORY


def test_an_agent_verdict_no_entry_of_the_run_holds_is_reported_and_kept():
    """A published claim with no record behind it: neither a reader nor
    `audit_recheck` can check it, and nothing here can supply it. So it is reported
    rather than counted quietly, and the heading is left standing rather than have a
    reviewer's verdict deleted to tidy a count. 0 headings over the two corpora."""
    meta = {"gates": {"G-PANEL-2": {"status": "pass"}}}
    md = "## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)\n"
    assert lint.heading_findings(md, meta) == ["role-heading-agent-unrecorded"]
    assert lint.fix_headings(md, meta) == md, "the evidence stays"


# The advisory word is recorded per audit RUN and the status per gate, because one
# reviewer informs more than one gate key -- `_AUDIT_AGENTS` sends the `eq` agent's
# single payload to both `G-EQ` and `G-PANEL-1` -- and only the key with no gate
# module of its own keeps the field: `gates._record` replaces a gate's blob on every
# mechanical re-gate and carries `note`/`model` over but not `agent_verdict`. Reading
# the named gate's entry alone therefore reports a heading as unrecorded whose word
# the record does hold, written from the same payload field by the same loop.

EQ_RUN = {"gates": {"G-EQ": {"status": "pass"},
                    "G-PANEL-1": {"status": "pass", "agent_verdict": "SOUND"}}}


def test_the_advisory_word_is_looked_up_per_run_and_not_per_gate():
    md = "## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)\n"
    assert lint.heading_findings(md, EQ_RUN) == [], \
        "the record holds this word; the heading that publishes it is checkable"
    assert lint.fix_headings(md, EQ_RUN) == md
    own = {"gates": {**EQ_RUN["gates"],
                     "G-EQ": {"status": "pass", "agent_verdict": "WEAK"}}}
    assert lint.heading_findings(md, own) == ["role-heading-agent-mismatch"], \
        "the gate's own entry wins; the fallback is for a gate that has none"


def test_a_role_no_reviewer_shares_borrows_no_word():
    """The lookup is the composer's own run table (`_AUDIT_AGENTS`), so it is not a
    search of the record for any word that fits: another reviewer's verdict is not
    this role's record, however many entries the cell has."""
    md = "## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)\n"
    meta = {"gates": {**EQ_RUN["gates"], "G-PANEL-3": {"status": "pass"}}}
    assert lint.heading_findings(md, meta) == \
        ["role-heading-agent-unrecorded"], \
        "another reviewer's word is not this role's record"


def test_a_published_word_that_is_not_the_recorded_one_is_reported_and_kept():
    """What keeps the lookup above from accepting any word at all. Never rewritten,
    for the reason a stale status is not: the reviewer's own prose restates its
    verdict inside the section body, so composing the recorded word into the heading
    alone would leave the record disagreeing with itself one screen down."""
    for md, meta in (
            ("## Role 3 — G-PANEL-2 (faithfulness): pass (agent: UNFAITHFUL)\n",
             PANEL2),
            ("## Role 1 — G-EQ (refinement fidelity): pass (agent: WEAK)\n",
             EQ_RUN)):
        assert lint.heading_findings(md, meta) == \
            ["role-heading-agent-mismatch"], md
        assert lint.fix_headings(md, meta) == md
    assert "role-heading-agent-mismatch" in lint.ADVISORY


def test_the_status_slot_holding_the_runs_word_is_composed_from_the_record():
    """`role-heading-agent-status` for a role whose word is recorded under the other
    key of its own run: the reader of `## Role 1 — G-EQ: SOUND` never sees the
    recorded status and reads an advisory verdict as one. Both words are in the
    record, so the composer's shape is recoverable exactly. 3 released headings."""
    md = "## Role 1 — G-EQ (refinement fidelity): SOUND\n"
    assert lint.heading_findings(md, EQ_RUN) == ["role-heading-agent-status"]
    assert lint.fix_headings(md, EQ_RUN) == \
        "## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)\n"
    assert lint.heading_findings(lint.fix_headings(md, EQ_RUN), EQ_RUN) == []


def test_a_reviewers_own_synonym_in_the_status_slot_is_the_same_defect():
    """Read on the composer's VOCABULARY and not on equality with the recorded word:
    a status slot holding `TIGHT` where the run recorded `SOUND` publishes an
    advisory verdict as a status just as its exact word would, and a word the
    composer never writes there cannot be a status that went stale. A heading that
    published a reviewer's synonym states it again in the section body, so the
    composed heading moves the reader's answer and drops no evidence."""
    md = ("## Role 2 — G-PANEL-1 (spec-too-weak): TIGHT\n\n"
          "Spec is biconditional-tight. TIGHT.\n")
    assert lint.heading_findings(md, EQ_RUN) == ["role-heading-agent-status"]
    out = lint.fix_headings(md, EQ_RUN)
    assert out.split("\n")[0] == \
        "## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)"
    assert out.split("\n")[1:] == md.split("\n")[1:], "and nothing else moved"
    assert lint.heading_findings(out, EQ_RUN) == []


def test_an_advisory_word_with_no_recorded_verdict_is_left_standing():
    """The reading needs a recorded `agent_verdict` to publish in the slot the word
    moves to. With none there is nothing to compose, and dropping the word to tidy
    the heading is the loss `role-heading-agent-unrecorded` refuses, so it falls
    through to the class that is only counted. 0 headings over the two corpora."""
    meta = {"gates": {"G-PANEL-1": {"status": "pass"}}}
    md = "## Role 2 — G-PANEL-1 (spec-too-weak): TIGHT\n"
    assert lint.heading_findings(md, meta) == ["role-heading-status-stale"]
    assert lint.fix_headings(md, meta) == md, "the reviewer's word stays"


def test_a_heading_with_no_gate_name_is_counted_and_left():
    """There is no entry to key the three fields on. The one reading here that
    cannot be answered from the record, so it is the one that is only reported."""
    for md in ("## Role 3\n", "## Role 3 — the auditor stood down\n"):
        assert lint.heading_findings(md, PANEL2) == ["role-heading-ungated"]
        assert lint.fix_headings(md, PANEL2) == md


def test_a_heading_is_not_composed_from_a_record_that_holds_no_status():
    """`role-heading-unlabelled` and `role-heading-unrecorded` at once. The repair
    is skipped, because composing from an absent status publishes the word `None`
    where the reader looks for the verdict."""
    md = "## Role 3 — G-PANEL-2\n"
    assert sorted(lint.heading_findings(md, {"gates": {}})) == \
        ["role-heading-unlabelled", "role-heading-unrecorded"]
    assert lint.fix_headings(md, {"gates": {}}) == md


def test_a_heading_for_a_gate_the_label_table_does_not_name_is_left_alone():
    """`_GATE_ROLE_LABEL`'s values carry the gate name AND its parenthetical, so the
    bare gate name in their place would compose `G-PANEL-9: pass` -- which
    `release_prose._ROLE_HEADING` does not recognise as a heading at all. A role
    added since this lint last read that table is the composer's business."""
    meta = {"gates": {"G-PANEL-9": {"status": "pass"}}}
    assert lint.heading_findings("## Role 3 — G-PANEL-9 (freshness): pass\n",
                                 meta) == []
    md = "## Role 3 — G-PANEL-9\n"
    assert lint.heading_findings(md, meta) == ["role-heading-unlabelled"]
    assert lint.fix_headings(md, meta) == md


def test_the_heading_rule_reads_prose_and_not_a_retained_body():
    """A heading-shaped line inside an attack body is that attack's source. The rule
    goes through the same `walk` as every other, so a fence is a fence here too."""
    md = ("## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)\n"
          "\n"
          "Attack 1 — `atk_1.py` → rejected\n"
          "\n"
          "```python\n"
          "# ## Role 3 — G-PANEL-2\n"
          "def f(): return 0\n"
          "```\n")
    assert lint.heading_findings(md, PANEL2) == []
    assert lint.fix_headings(md, PANEL2) == md


def test_the_sweep_repairs_a_heading_from_the_record_at_the_other_end(tmp_path):
    """End to end, because the heading rule is the one rule that needs both ends of
    the cell: `scan_markdown` reads the rendering, the gate entry is in `meta.json`,
    and `sweep` is where the two meet."""
    import argparse

    cell = tmp_path / "a__b-1" / "lean"
    cell.mkdir(parents=True)
    (cell / "verdict.md").write_text(
        "# a__b-1 — lean\n"
        "\n"
        "## Role 3 — G-PANEL-2 (faithfulness): FAITHFUL\n"
        "\n"
        "The account, which no rule here touches.\n")
    (cell / "meta.json").write_text(json.dumps(PANEL2, indent=2) + "\n")

    rows, held, rules = lint.sweep([cell], argparse.Namespace(fix=True, limit=0))
    assert held == [] and rows[0]["fixed"] is True
    assert rows[0]["verdict_rules"] == ["role-heading-agent-status"]
    out = (cell / "verdict.md").read_text()
    assert _composed(3, "G-PANEL-2", PANEL2) in out
    assert "The account, which no rule here touches." in out
    assert json.loads((cell / "meta.json").read_text()) == PANEL2, \
        "a heading defect is not a reason to rewrite the record"

    rows, held, rules = lint.sweep([cell], argparse.Namespace(fix=True, limit=0))
    assert rows == [], "and the second sweep finds nothing to do"


# ---- a paragraph longer than the card's whole fold budget ----
#
# `render._fold_long_prose` cuts a long note between top-level MARKDOWN BLOCKS, so
# a single paragraph over the whole budget cannot be folded at all: whichever side
# of the cut it lands on, the card publishes it as one unbroken run. The repair is
# to insert the paragraph break the auditor's own sentences already allow -- and
# nothing else, because these are the audit's words.

LEAD = "VERDICT: NO-LEAKAGE. The spec view was re-derived from the shipped bytes."
SENTENCES = [f"Sentence {i:02d} states a measured fact about the view and the"
             " record." for i in range(60)]
WALL = LEAD + "\n" + " ".join(SENTENCES)


def test_the_budget_is_the_renderers_own_and_cannot_drift_from_it():
    """The rule exists because of one constant in the renderer. Read from it rather
    than copied, so a change there is a failure here and not a silent disagreement
    about what a reader can see."""
    # The renderer is the `viz` extra, and `tests/` is documented as runnable with
    # `[dev]` alone. Skipping is the honest answer there: the constant cannot drift
    # from a renderer this install does not have.
    pytest.importorskip("nh3", reason="the viz extra is not installed")
    from viz.backend.render import _FOLD_PROSE_CHARS

    assert lint.WALL_CHARS == _FOLD_PROSE_CHARS
    assert len(WALL) > lint.WALL_CHARS, "premise: the fixture is over budget"


def test_an_over_long_paragraph_is_split_and_nothing_else_changes():
    """The whole safety argument for this rule: one inter-sentence space becomes a
    blank line, so the words, their order, every number and the first line are the
    auditor's own, byte for byte."""
    import re

    out, classes = lint.split_wall(WALL)
    assert classes == ["wall-of-text-paragraph"]
    assert out.split() == WALL.split(), "no word is reworded, dropped or reordered"
    assert out.split("\n")[0] == LEAD, \
        "the first line is read back by the build and the defect router"
    assert re.sub(r"\s+", " ", out) == re.sub(r"\s+", " ", WALL), \
        "and the only edit is whitespace"
    paras = lint._PARA_SPLIT.split(out)[::2]
    assert len(paras) == 2 and all(len(p) <= lint.WALL_CHARS for p in paras)
    assert min(len(p) for p in paras) > lint.WALL_CHARS // 3, \
        "spread evenly: an orphan tail reads as a new thought the auditor did not have"


def test_the_split_lands_between_sentences_and_never_after_an_abbreviation():
    """`e.g.` ends a word, not a sentence, and the character before its `g` is a
    period rather than a space -- which is why the abbreviation guard has to accept
    a period in its leading context. Without that, the rule read `e.g. Foo` as a
    place to break a sentence in half."""
    para = ("Lead line.\nText e.g. Foo continues here. Real end."
            " i.e. Next starts. Dr. Who arrived. A. B. Cee wrote it. Done.")
    cut = [para[e:e + 6] for _s, e in lint._boundaries(para)]
    assert cut == ["Text e", "Real e", "Dr. Wh", "A. B. ", "Done."], \
        "e.g., i.e., an initial and Dr. are all excluded; the line break after the" \
        " first line is not -- widening it to a blank line leaves that line intact"


def test_a_paragraph_of_one_line_is_counted_and_left():
    """The first-line lock: `build_one.run_audit_stage` and the defect router read a
    recorded note's first line back, so a paragraph that IS one line has no
    breakable gap in it. All 73 unbreakable paragraphs in the two corpora are of
    this shape -- one-line `G-PANEL.detail` and `G-AX.detail` summaries, and not
    one of them is a paragraph of a rendered record."""
    one_line = WALL.replace("\n", " ")
    out, classes = lint.split_wall(one_line)
    assert out == one_line
    assert classes == ["wall-of-text-unbreakable"]
    assert lint._boundaries(one_line) == []


@pytest.mark.parametrize("marker", ["- ", "1. ", "> ", "| ", "#### "])
def test_a_list_a_table_and_a_quote_are_not_split(marker):
    """A break inside a list buys nothing -- markdown-it reports the whole list as
    ONE top-level block and `render._fold_long_list` already cuts it at an item
    boundary -- and a break inside a table destroys it. A published paragraph
    past the budget is of this shape."""
    para = LEAD + "\n" + "\n".join(marker + s for s in SENTENCES)
    assert len(para) > lint.WALL_CHARS, "premise"
    assert lint.split_wall(para) == (para, [])


def test_a_fenced_transcript_is_never_split():
    """A blank line inside a fence belongs to the transcript. Counted across the
    whole field, because a fence opened in one paragraph closes in a later one."""
    md = f"```\n{WALL}\n```\n"
    assert lint.split_wall(md) == (md, [])
    assert lint.fold_wall_paragraphs(f"## Role 1 — G-EQ (x): pass\n\n{md}") == \
        (f"## Role 1 — G-EQ (x): pass\n\n{md}", [])


def test_the_record_end_reports_and_repairs_the_same_paragraph():
    """And converges: the composer re-renders `verdict.md` from these fields on the
    next re-gate, so a wall repaired only in the rendering comes straight back."""
    fixed, broken = lint.scan_meta(_meta(WALL))
    assert broken == ["wall-of-text-paragraph"]
    note = fixed["gates"]["G-PANEL-2"]["note"]
    assert note.split() == WALL.split()
    _, again = lint.scan_meta(_meta(note))
    assert again == []


def test_the_two_ends_break_the_same_text_in_the_same_place():
    """A role's account is stored twice -- `gates.G-PANEL.detail` and the role's own
    entry -- and rendered a third time into `verdict.md`. A rule that broke the
    three differently would make the record disagree with itself, so the boundary
    choice may not depend on where the paragraph sits."""
    meta = {"gates": {"G-PANEL": {"detail": WALL, "data": {"roles": {
        "G-PANEL-2": {"status": "pass", "detail": WALL}}}}}}
    fixed, broken = lint.scan_meta(json.loads(json.dumps(meta)))
    assert broken == ["wall-of-text-paragraph"] * 2
    gate = fixed["gates"]["G-PANEL"]
    assert gate["detail"] == gate["data"]["roles"]["G-PANEL-2"]["detail"]
    rendered, classes = lint.fold_wall_paragraphs(
        f"## Role 3 — G-PANEL-2 (faithfulness): pass\n\n{WALL}\n")
    assert classes == ["wall-of-text-paragraph"]
    assert gate["detail"] in rendered


def test_the_published_end_reports_and_repairs_it_by_the_narrow_route():
    """A cell whose only fault is a wall of text reads no word, so it must not be
    put through `publish_note` -- and `scan_markdown` has to report what the narrow
    route will do, or the lint reports the cell forever."""
    md = f"## Role 3 — G-PANEL-2 (faithfulness): pass\n\n{WALL}\n"
    assert lint.scan_markdown(md) == ["wall-of-text-paragraph"]
    assert set(lint.scan_markdown(md)) <= lint.PARAGRAPH | lint.STRUCTURAL \
        | lint.NARRATION | lint.PATH_RULES | lint.HEADING_FIX, "the narrow route"
    out = lint.clean_published(md)
    assert lint.scan_markdown(out) == []
    assert lint.clean_published(out) == out
    assert out.split() == md.split()


def test_an_unbreakable_paragraph_does_not_make_a_cell_dirty(tmp_path):
    """An advisory class is counted and never repaired, so a cell carrying only one
    has nothing for `--fix` to do. Reported as dirt it would be rewritten to itself
    on every sweep and this script's exit status would be permanently 1."""
    import argparse

    cell = tmp_path / "a__b-1" / "lean"
    cell.mkdir(parents=True)
    (cell / "verdict.md").write_text("# a__b-1 — lean\n")
    (cell / "meta.json").write_text(json.dumps(
        _meta(WALL.replace("\n", " ")), indent=2) + "\n")
    before = (cell / "meta.json").read_text()

    rows, held, rules = lint.sweep([cell], argparse.Namespace(fix=True, limit=0))
    assert rows == [] and held == []
    assert rules["wall-of-text-unbreakable"] == 1
    assert (cell / "meta.json").read_text() == before, \
        "counted, and the record comes back byte-identical"


# ---- a cell another writer holds is skipped, never edited ----

def test_a_cell_held_by_another_writer_is_reported_and_left_alone(tmp_path):
    """Two writers on one bundle is how a record stops matching its gates. The
    sweep takes the same per-cell flock every driver takes, so a cell mid-audit
    is skipped and reported, and `--passes` re-visits exactly those."""
    import argparse

    from pbt_port_fleet import cell_lock

    cell = tmp_path / "a__b-1" / "lean"
    cell.mkdir(parents=True)
    (cell / "verdict.md").write_text(_record())
    (cell / "meta.json").write_text(json.dumps({"gates": {}}))
    args = argparse.Namespace(fix=True, limit=0)

    with cell_lock(cell):
        rows, held, _rules = lint.sweep([cell], args)
    assert [c.name for c in held] == ["lean"]
    assert rows and rows[0]["fixed"] is False
    assert (cell / "verdict.md").read_text() == _record(), \
        "a held cell must come back byte-identical"

    rows, held, _rules = lint.sweep([cell], args)
    assert held == [] and rows[0]["fixed"] is True
    assert (cell / "verdict.md").read_text() != _record()
    assert lint.scan_markdown((cell / "verdict.md").read_text()) == []


def test_a_cell_named_to_skip_is_not_walked_at_all(tmp_path, monkeypatch, capsys):
    """The lock keeps this run out of a cell a driver holds while it WRITES, which
    is not the same as while it re-gates: a driver that has just released the lock
    and is about to re-take it would have its record repaired underneath it, and the
    repair overwritten by the section the driver composes next. A cell known to be
    mid-audit is not measured, so the exit status does not claim it was."""
    for iid in ("a__b-1", "a__b-2"):
        cell = tmp_path / iid / "lean"
        cell.mkdir(parents=True)
        (cell / "verdict.md").write_text(_record())
        (cell / "meta.json").write_text(json.dumps({"gates": {}}, indent=2) + "\n")
    before = (tmp_path / "a__b-2" / "lean" / "verdict.md").read_text()

    monkeypatch.setattr(sys, "argv", [
        "verdict_prose_lint.py", "--benchmark-dir", str(tmp_path), "--fix",
        "--skip", "a__b-2/lean"])
    lint.main()
    out = capsys.readouterr().out
    assert "1 cell(s) walked" in out and "a__b-2/lean" in out
    assert (tmp_path / "a__b-2" / "lean" / "verdict.md").read_text() == before
    assert (tmp_path / "a__b-1" / "lean" / "verdict.md").read_text() != before, \
        "premise: the sweep did repair the cell it was not told to skip"
