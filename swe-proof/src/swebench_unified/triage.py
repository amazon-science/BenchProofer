# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Why a bundle is not green, reduced to the KIND OF WORK that would fix it.

`green_check.classify` answers "is this cell green, and which gates say no" --
the release gate's question. It is not enough to schedule work: the gates that
say no do not all fail for the same kind of reason, and the remedies are not
interchangeable. Routing a cell to work that cannot address its class is the
expensive failure mode -- it reports the same not-green and makes no progress.

A mechanical gate failing is a measurement about the artifact, so re-running it
is meaningful. An adjudicated audit failure (WEAK / BROKEN / UNFAITHFUL /
LEAKAGE) is a JUDGMENT that the spec admits a wrong implementation: re-measuring
cannot touch it and the spec itself has to change. An INCONCLUSIVE failure, or
one recorded against a spec the bundle NO LONGER SHIPS (a verdict is evidence
about the bytes the role read and `sources` records them, so that check is
mechanical), is the ABSENCE of a judgment and the remedy is to measure again
with room. The two must not be merged: treating absence as a spec defect invents
a weakness the evidence never showed, and treating a spec defect as absence
hides a real one. The same split applies WITHIN the mechanical gates -- missing,
errored or placeholder was never concluded, while FAILED was and will refute the
artifact again on every re-run.

Classes, in the order they are checked (first match wins: a cell blocked
mechanically cannot be audited at all -- the audit stage only runs once the
mechanical gates are green):

  MECH     a mechanical gate is missing, errored, or holds a placeholder stamp
           that is not a real verdict: never concluded, so re-measure.
  AUTHOR   a mechanical gate FAILED -- the model diverges from the real function
           (G-CONF), an assumed axiom is false of it (G-AX), the solution does
           not verify (G-VERIFY), the spec admits a mutant (G-MUT). Author.
  REPAIR   an audit role adjudicated the spec too weak (WEAK / BROKEN): a
           witness verifies against the spec yet its patch does not resolve, a
           `verify => correct` counterexample. Strengthen the spec.
  PANEL    a judgment role adjudicated the spec unfaithful to the real callee,
           or found the fix leaked into it. Re-align, do not strengthen.
  REAUDIT  an audit role failed with no adjudication (INCONCLUSIVE), against a
           spec the bundle no longer ships, or with no recorded reason at all.
           Re-measure.
  GREEN    nothing to do.

A verdict may be recorded in any of three fields of a gate entry (`detail`,
`note`, `agent_verdict`) depending on the code path that stamped it, so all
three are scanned. Reading only `detail` silently misclassifies an adjudicated
cell as REAUDIT and sends a real defect to work that will only re-measure it.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

# Statuses that count as green-eligible, from the one definition rather than a
# copy of it: "relaxed" is a recorded, justified exception and IS green, and a
# local list that fell behind on that would route a green cell into repair work.
from .greenness import GREEN_OK as OK  # noqa: E402

MECH, AUTHOR, REPAIR, PANEL, REAUDIT, GREEN = (
    "MECH", "AUTHOR", "REPAIR", "PANEL", "REAUDIT", "GREEN")

# The judgment roles' remedy is a property of the ROLE, because their recorded
# note is the AUDITOR'S OWN PROSE. G-PANEL-2 judges the spec against the real
# patched callee and G-PANEL-3 against the public problem statement, so a fail
# from either says the spec claims too much or reveals too much, and the remedy
# is to realign it -- whatever words the auditor reached for while saying so.
#
# Reading their prose for the vocabulary instead misroutes records, and always in
# the expensive direction: a G-PANEL-2 note that opens "the spec is not too weak"
# before laying out a spec-too-STRONG finding contains the substring WEAK, so the
# cell is routed to a prompt that tells the agent to close a hole that is not
# there. Negation and quotation make that unavoidable in free prose. Best case
# the agent disputes the verdict and the cell is untouched; worst case it
# strengthens a spec that was already too strong.
#
# The mechanized roles are deliberately NOT here. Their note is written by
# `_derive_audit_verdict`, which withholds the weakness vocabulary exactly when
# the refutation is not attributable to the spec (an attack patch that would not
# apply, an oracle that cannot certify gold), so for them the vocabulary is a
# real signal and a gate-name rule would route those cells to spec repair
# instead of to the re-measurement they need.
_ROLE_REMEDY = {"G-PANEL-2": PANEL, "G-PANEL-3": PANEL}

# WEAK/BROKEN are the mechanized roles' labels for a `verify => correct`
# counterexample; UNFAITHFUL/LEAKAGE are what the legacy rollup gate recorded,
# which does not name the role that spoke.
_WEAKNESS = ("BROKEN", "WEAK")
_FAITHFULNESS = ("UNFAITHFUL", "LEAKAGE")

# `build_one` records a role that reached no verdict as "<role>: INCONCLUSIVE —
# ...", so the harness's own decision is recognisable by its position. An
# auditor's prose may use the word for something else entirely ("the mechanical
# G-LEAK result is not INCONCLUSIVE here"), and treating that as an absent
# verdict sends an adjudicated cell to work that only re-measures it.
_INCONCLUSIVE = re.compile(r"\s*[\w-]+:\s*INCONCLUSIVE\b|^\s*INCONCLUSIVE\b")


def _reached_no_verdict(entry: dict) -> bool:
    """True when the HARNESS recorded this role as having reached no verdict."""
    return any(_INCONCLUSIVE.match(str(entry.get(k) or ""))
               for k in ("note", "detail"))


def _placeholder_blockers(gates: dict) -> list[str]:
    """Mechanical gates whose stamp is OK but is not a real verdict.

    Both cases are "not yet constructed" tagged as a skip so that the absence of
    an input is never conflated with a real refutation. They are not green, and
    the fix is to construct the missing input and re-measure -- mechanical work.
    """
    out = []
    conf = gates.get("G-CONF", {})
    if conf.get("status") in OK:
        data = conf.get("data") or {}
        if (data.get("conf_missing_script")
                or data.get("docker_oracle_unavailable")
                or "does not support G-CONF" in (conf.get("detail") or "")):
            out.append("G-CONF=placeholder")
    pbt = gates.get("G-PBT", {})
    if pbt.get("status") in OK and (pbt.get("data") or {}).get("pbt_missing_manifest"):
        out.append("G-PBT=placeholder")
    return out


def _role_text(entry: dict) -> str:
    """Every field a verdict may have been recorded in, upper-cased."""
    return " ".join(str(entry.get(k) or "")
                    for k in ("detail", "note", "agent_verdict")).upper()


def _stamp_moved(bundle_dir: Path, entry: dict) -> str:
    """The artifacts this record read that are no longer what it read, or "".

    A role's verdict is evidence about the bytes it was shown. `sources`
    (`gates/base.source_digests`) records the sha256 of each of them, so once a
    later build edits the spec, "this finding is about a file that is gone" stops
    being an argument about mtimes and becomes a hash comparison.

    Why this has to gate the ROUTING and not just a report: an adjudicated
    `WEAK` is the strongest signal this module has, and it sends the cell to a
    prompt that tells an agent to close a hole in the spec. If the spec that had
    the hole was already replaced, that agent is being asked to fix something it
    cannot find -- so it disputes the finding, no repair is recorded, the cell
    stays red carrying the same stale label, and the next cycle schedules it
    again, spending an agent launch each time to re-discover that there is
    nothing to repair.

    An UNDIGESTED record (written before `sources` existed) returns "": it
    cannot be shown stale, and guessing that it is would re-audit most of a
    corpus on no evidence. That is the same rule
    `scripts/check_stamp_freshness.py` applies -- `unverifiable` is not a
    finding -- and the two must agree, or a cell gets scheduled by one and
    cleared by the other forever.
    """
    import hashlib
    srcs = entry.get("sources")
    if not isinstance(srcs, dict) or not srcs:
        return ""
    moved = []
    for name, want in sorted(srcs.items()):
        p = bundle_dir / str(name)
        try:
            got = hashlib.sha256(p.read_bytes()).hexdigest()
        except OSError:
            moved.append(f"{name}=gone")
            continue
        if got != str(want):
            moved.append(name)
    return ";".join(moved)


def defect_class(gates: dict, mech_gates: list[str],
                 bundle_dir: Path | None = None) -> tuple[str, str]:
    """-> (class, why). `mech_gates` is STATIC_GATES + DOCKER_GATES.

    `bundle_dir` is optional so that a caller holding only a parsed meta.json
    keeps working. Without it an audit adjudication cannot be checked against
    the artifact on disk, so a stale finding routes by its own vocabulary --
    today's behaviour, and the reason the parameter is worth threading through.
    """
    if not gates:
        return MECH, "no gates recorded"

    # A gate that FAILED reached a verdict about the artifact; one that is
    # missing or errored reached none. Re-measuring is the remedy for the
    # second and a waste on the first, so they are separate classes -- and the
    # refuted one is reported first, since a cell with both needs the authoring
    # either way.
    refuted, unmeasured = [], []
    for g in mech_gates:
        st = gates.get(g, {}).get("status")
        if st in OK:
            continue
        (refuted if st == "fail" else unmeasured).append(
            f"{g}={st or 'MISSING'}")
    unmeasured += _placeholder_blockers(gates)
    if refuted:
        return AUTHOR, ";".join(refuted + unmeasured)
    if unmeasured:
        return MECH, ";".join(unmeasured)

    # Audit completeness: all three panel roles, or the legacy rollup. A missing
    # audit is not an adjudication, so it is REAUDIT -- there is work to do and
    # no judgment to overturn.
    roles = [gates.get(f"G-PANEL-{n}", {}).get("status") for n in (1, 2, 3)]
    panel_keys = [f"G-PANEL-{n}" for n in (1, 2, 3)]
    if not all(s is not None for s in roles):
        panel_keys = ["G-PANEL"]
    keys = ["G-EQ"] + panel_keys
    missing = [k for k in keys if gates.get(k, {}).get("status") is None]
    if missing:
        return REAUDIT, "audit incomplete: " + ";".join(f"{k}=MISSING" for k in missing)

    failed = [k for k in keys if gates.get(k, {}).get("status") not in OK]
    if not failed:
        return GREEN, "ok"

    weakness, faithfulness, inconclusive, silent, moved = [], [], [], [], []
    for k in failed:
        entry = gates.get(k, {})
        # A role that reached no verdict adjudicated nothing, whatever class its
        # gate belongs to: there is a measurement to redo, not a finding to fix.
        if _reached_no_verdict(entry):
            inconclusive.append(k)
            continue
        # Nor did a role whose verdict describes an artifact that has since been
        # replaced. Checked BEFORE the vocabulary, because the vocabulary is
        # precisely what would misroute it: a decisive `WEAK` about a deleted
        # postcondition reads as the most urgent class there is.
        if bundle_dir is not None:
            gone = _stamp_moved(bundle_dir, entry)
            if gone:
                moved.append(f"{k}({gone})")
                continue
        remedy = _ROLE_REMEDY.get(k)
        if remedy == REPAIR:
            weakness.append(k)
        elif remedy == PANEL:
            faithfulness.append(k)
        else:
            # the legacy rollup: the role is unknown, so read the vocabulary
            txt = _role_text(entry)
            if any(t in txt for t in _WEAKNESS):
                weakness.append(k)
            elif any(t in txt for t in _FAITHFULNESS):
                faithfulness.append(k)
            elif "INCONCLUSIVE" in txt:
                inconclusive.append(k)
            else:
                silent.append(k)

    # A spec that admits a wrong implementation outranks every other complaint:
    # it is the one failure that falsifies `verify => correct`, so it must be
    # repaired even if the same cell also has a faithfulness note.
    if weakness:
        return REPAIR, "spec too weak: " + ";".join(weakness)
    if faithfulness:
        return PANEL, "spec unfaithful/leaked: " + ";".join(faithfulness)
    if inconclusive:
        return REAUDIT, "inconclusive: " + ";".join(inconclusive)
    # Reported after the two live classes on purpose. A cell can hold a stale
    # G-EQ next to a FRESH G-PANEL-2 finding, and there the fresh judgment is
    # real work that must not be deferred behind a re-measurement; dropping the
    # stale role from consideration is the whole of the correction.
    if moved:
        return REAUDIT, "verdict describes a spec no longer shipped: " + ";".join(moved)
    return REAUDIT, "failed with no recorded verdict: " + ";".join(silent)


def classify_bundle(bundle_dir: Path, mech_gates: list[str]) -> tuple[str, str]:
    """Read a bundle's meta.json and class it. An unreadable meta.json is MECH
    (the bundle needs re-gating), never GREEN."""
    meta_p = bundle_dir / "meta.json"
    if not meta_p.is_file():
        return MECH, "no meta.json"
    try:
        meta = json.loads(meta_p.read_text())
    except (OSError, json.JSONDecodeError) as e:
        return MECH, f"meta.json unreadable: {type(e).__name__}"
    return defect_class(meta.get("gates", {}), mech_gates, bundle_dir)


def worklist(benchmark_dir: Path, backends: list[str],
             green_classify) -> list[dict]:
    """Every non-green cell under `benchmark_dir`, with its class.

    `green_classify(bundle_dir, backend, instance_id) -> (verdict, why)` is the
    release gate's own classifier, INJECTED rather than imported: it is the one
    authority on greenness and it lives with the release tooling, so a second
    copy here could drift from it and vouch for a cell the gate refuses. This
    module only decides what KIND of work a non-green cell needs.

    A cell this module calls GREEN but the gate calls not-green is reported as
    MECH carrying the gate's own reason, so a scheduler can never conclude there
    is no work left on a cell the gate still rejects.
    """
    from .gates import DOCKER_GATES, STATIC_GATES
    mech = list(STATIC_GATES) + list(DOCKER_GATES)

    out = []
    for d in sorted(p for p in benchmark_dir.iterdir() if p.is_dir()):
        for bk in backends:
            b = d / bk
            if not (b / "meta.json").is_file():
                continue
            verdict, gate_why = green_classify(b, bk, d.name)
            if verdict == "GREEN":
                continue
            cls, why = classify_bundle(b, mech)
            if cls == GREEN:
                cls, why = MECH, f"release gate disagrees: {gate_why}"
            out.append({"instance_id": d.name, "backend": bk,
                        "cls": cls, "why": why, "gate_why": gate_why})
    return out
