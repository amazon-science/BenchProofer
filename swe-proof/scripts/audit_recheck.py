#!/usr/bin/env python
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Re-derive a recorded audit verdict from the attacks already in verdict.md.

Why this exists. The mechanized audit roles (G-EQ / G-PANEL-1) judge a cell by
RE-VERIFYING each attack the reviewer wrote, and `check_attack` reports
`verify_completed=False` when the verifier hits its wall-clock cap. The
derivation must call that INCONCLUSIVE rather than "does not verify" -- treating
a cap as a rejection would mask a real weakness -- but it means the HOST's own
load can turn a sound cell's audit into a fail, since under a wide wave the cap
is reached by contention rather than by the attack.

Re-running the reviewer AGENT to clear those is wasteful and non-reproducible: a
fresh agent writes different attacks, so it re-judges a different battery. The
attacks that produced the stamp are retained verbatim in verdict.md, so this
script extracts them, re-verifies them at a cap the caller chooses, and
re-derives the same verdict from the same evidence. A cell whose only complaint
was a timeout, and whose attacks all reject when given room, is a cell whose
recorded fail was infra; that is the one case this clears, and it clears it from
the ORIGINAL evidence.

What it can and cannot conclude. Extraction recovers attack SOURCE, and the
`patches` map (an attack's faithful refined patch) is NOT retained. So:

* every attack behaves as its original label settled, control verifies, floor
  met                                                -> pass (recordable)
* an attack the original run REJECTED now verifies    -> CANDIDATE, and this
  script stops. The spec weakened since the audit, but whether that is a real
  defect needs the attack's refined patch run through the resolve oracle, which
  only a live audit has. The recorded fail stays in place: fail-closed.
* the original run never got an oracle verdict on some attack (its resolve did
  not complete, or no patch was submitted)           -> `needs-live`, no write
* an attack is recorded WEAK/BROKEN                   -> `recorded-break`: a
  real verify-does-not-imply-correct hole, bound for spec repair, not for this
* still inconclusive at the higher cap                -> `inconclusive`, no write

An attack labelled `correct echo` is not re-litigated: the resolve ORACLE settled
it, and `classify_old` says why that verdict outlives a later spec edit.

Usage:
  SBU_BENCHMARK=swe_bench_verified SBU_BENCHMARK_DIR=benchmark-verified \\
    python scripts/audit_recheck.py --lane-file F [--jobs N] [--timeout S]
      [--write --reason timeout|spec-edit] [--out report.json]

`--write` is required to touch meta.json; without it the run is a dry report.
The lane file is `<instance_id>\\t<backend>` per line.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from swebench_unified.construct.release_prose import sanitize_code  # noqa: E402
from swebench_unified.construct.verdict_record import STATUSES  # noqa: E402
from swebench_unified.corpus_root import default_benchmark_dir  # noqa: E402

# role heading -> (gate key, derive role). verdict.md numbers the roles in a
# fixed order; the gate name in the heading is what we key off, not the number.
_ROLE_RE = re.compile(r"^## Role \d+ — (G-[A-Z0-9-]+) ")
_ATTACK_RE = re.compile(r"^Attack (\d+) — `([^`]+)` → (.*)$")
_CONTROL_RE = re.compile(r"^\*\*Positive control\*\*.*`([^`]+)`")
_PREPATCH_RE = re.compile(r"^Prepatch bug re-encoded as an attack: `(True|False)`")
_FENCE_RE = re.compile(r"^```")

# The cross-reference a role carries when its attack bodies were byte-identical to
# an EARLIER role's and were therefore not republished.
#
# Part of the record's grammar, not decoration: this file is the only place the
# attack sources ship, and `_recheck_locked` re-verifies them from here. Left
# unresolved, such a record hands back a role with zero attacks, `_verdict_of`
# reports the floor unmet, and the cell stops being clearable offline -- the
# de-duplication would cost exactly the capability the retained evidence exists
# for. Resolution is EXACT, not a courtesy: the composer proves the two sections'
# bodies equal byte for byte before dropping a copy, and `_resolve_xrefs` re-checks
# the attack NAMES line up before it inherits anything.
_XREF_RE = re.compile(
    r"^_The (\d+) attack bodies behind this role are not republished in this "
    r"section: each is byte-identical to the block published under `"
    r"(G-[A-Z0-9-]+)`")

MECHANIZED = ("G-EQ", "G-PANEL-1")


def classify_old(label: str) -> str:
    """The retained `→ ...` label of an attack, reduced to its class.

    These strings come from `audit_verdict._derive_audit_verdict` and record how
    far the ORIGINAL derivation got on that attack. Two of them already carry an
    oracle verdict that this script must not throw away:

    * `echo` -- "correct echo (verifies AND its patch resolves)", written only
      under `r.completed and r.resolved` (audit_verdict.py:431), i.e. the resolve
      oracle RAN and returned resolved. Whether a patch resolves is a function of
      the patch and the repo, not of the spec, so the verdict stays true however
      the spec moves later: the attack verifying again is EXPECTED and is not a
      weakness. Re-deriving it as a fresh candidate would turn every such
      adjudication into an unresolvable "needs the resolve leg".
    * `changed-spec` -- "not a counterexample (changed the spec)". The original
      derivation discarded these and appended nothing to `reasons`
      (audit_verdict.py:344), so they are benign, NOT evidence of a stale bundle.

    The rest either need the resolve leg (which needs the patch, not retained)
    or are already a recorded break.
    """
    if label.startswith("correct echo"):
        return "echo"
    if label.startswith("rejected"):
        return "reject"
    if label.startswith(("WEAK", "BROKEN")):
        return "break"
    if "changed the spec" in label:
        return "changed-spec"
    if "timed out" in label or label.startswith("inconclusive"):
        return "timeout"
    if "resolve did not complete" in label:
        return "resolve-incomplete"
    if "no submitted patch" in label:
        return "nopatch"
    if label.startswith("same-spec AND verifies"):
        return "unadjudicated"
    return "other"


# Classes whose adjudication needs the resolve oracle on an attack's refined
# patch. The patch is NOT retained in verdict.md, so these can only be settled
# by a live audit -- this script reports `needs-live` and writes nothing.
NEEDS_ORACLE = ("resolve-incomplete", "nopatch", "unadjudicated", "break")

# A retained body that is a DIFF, not a program.
#
# `verdict_record._attack_excerpt` publishes an attack as a unified diff against the
# cell's spec file rather than one near-identical copy of that file per attack,
# cutting every line before the first hunk header. So a body beginning with a hunk
# header is a diff, and the program it describes is not in the record.
#
# It has to be detected because the re-verification below writes each retained
# body out and runs the verifier on it. A diff does not parse, so it does not
# verify and its spec markers are absent, and `_verdict_of` reads that as a claim
# about the SPECIFICATION: an `echo` class body lands in `echo_bad` ("spec may now
# reject a correct impl") and a `reject` class one in `stale` ("bundle edited since
# the audit"), when nothing about either the spec or the bundle has changed.
#
# Excluding these bodies before they reach the verifier fixes both ends at once:
# the false diagnosis cannot be composed from an attack that was never run, and
# the role reports honestly that this record is not re-derivable. It cannot cost a
# real finding -- a diff never verifies, so no excluded body could have been the
# `same-spec AND verifies` candidate that a break rests on -- and it saves the
# verifier run each one would have burned.
_DIFF_BODY_RE = re.compile(r"\A@@ -\d+(?:,\d+)? \+\d+(?:,\d+)? @@")


def is_diff_body(src: str) -> bool:
    """Whether a retained attack body is a diff rather than a whole program."""
    return bool(_DIFF_BODY_RE.match((src or "").lstrip("\n")))


_HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def reconstruct_from_diff(baseline: str, body: str) -> str | None:
    """The whole attack source, rebuilt from a retained diff. None if it will not
    apply cleanly.

    `_attack_excerpt`'s docstring makes the claim this depends on: the baseline
    plus the diff IS the attack, nothing is truncated, so a diff-retained record
    is lossless and not merely smaller. Until that claim is exercised, a
    diff-retained cell is one `audit_recheck` can only decline -- honestly, but
    without re-deriving anything. So apply the hunks and get the program back.

    Written against exactly what the composer emits -- `difflib.unified_diff(...,
    n=3, lineterm="")` with every line before the first `@@` cut -- and strict on
    purpose. A hunk whose context does not match the spec file on disk, or whose
    line count disagrees with its own header, returns None rather than a
    best-effort splice: the point of reconstructing is to re-verify, and a
    mis-applied hunk would be re-verified as though it were the attack the
    reviewer wrote. Failing here costs a `diff_retained` note; guessing here would
    put a fabricated program's verdict into the record.

    Context is compared ignoring trailing whitespace, because the diff makes a
    round trip through Markdown: difflib renders a blank context line as a single
    space and any formatter that touches verdict.md strips it to the empty string.
    The output still uses the BASELINE's own bytes for every context and unchanged
    line, so that tolerance cannot leak into it -- only added (`+`) lines come
    from the record.
    """
    base = sanitize_code(baseline).rstrip().split("\n")
    # `lstrip`, not `strip`: a hunk whose last context line is blank ends the body
    # with what Markdown normalisation leaves as an empty line, and trimming the
    # tail would discard it, leaving the hunk disagreeing with its own header.
    lines = (body or "").lstrip("\n").split("\n")
    if not lines or not _HUNK_RE.match(lines[0]):
        return None
    out: list[str] = []
    pos = 0                    # cursor into `base`, 0-based
    i = 0
    while i < len(lines):
        m = _HUNK_RE.match(lines[i])
        if not m:
            return None        # trailing junk between hunks
        start, old_len = int(m.group(1)), int(m.group(2) or 1)
        # `@@ -0,0` is an insertion before the first line; every other header
        # counts from 1. Hunks are emitted in order and may not overlap.
        idx = max(start - 1, 0)
        if idx < pos or idx > len(base):
            return None
        out.extend(base[pos:idx])
        pos = idx
        i += 1
        consumed = 0
        while i < len(lines) and not _HUNK_RE.match(lines[i]):
            ln = lines[i]
            i += 1
            if ln.startswith("\\"):
                continue       # `\ No newline at end of file`
            tag, text = (ln[0], ln[1:]) if ln else (" ", "")
            if tag in " -":
                if consumed == old_len:
                    # Past what this hunk claims to cover. An empty line here is a
                    # blank the record picked up through Markdown, and skipping it
                    # is safe: the tail is appended from the baseline regardless.
                    # Anything else means body and header disagree -- a refusal.
                    if not ln:
                        continue
                    return None
                if pos >= len(base) or base[pos].rstrip() != text.rstrip():
                    return None
                if tag == " ":
                    out.append(base[pos])
                pos += 1
                consumed += 1
            elif tag == "+":
                out.append(text)
            else:
                return None
        if consumed != old_len:
            return None
    out.extend(base[pos:])
    return "\n".join(out) + "\n"


def parse_verdict(md: str) -> dict:
    """verdict.md -> {gate: {attacks: [(name, src, old_result)],
                            control: (name, src) | None,
                            prepatch_reproduced: bool | None}}.

    The fenced block AFTER an `Attack n — ...` line is that attack's source;
    the one after the positive-control line is the control's. Anything else
    fenced (the judgment roles' prose, machine verdicts) is skipped because we
    only enter a block when a header set `pending`.

    A role whose bodies were not republished because an earlier role's are
    byte-identical (`_XREF_RE`) inherits that role's sources and keeps its own
    outcome labels -- see `_resolve_xrefs`. The returned shape is the same either
    way, so a caller cannot tell a cross-referenced record from one that carries
    both copies, which is the point: the de-duplication is a rendering change and
    must not be a semantic one.

    Split on `\\n` and NOT with `splitlines()`, which also breaks on U+2028,
    U+2029, U+000B, U+000C, U+001C-1E and U+0085. A retained source containing any
    of those AS A LITERAL comes back with it rewritten to `\\n`, so the result is
    not the bytes in the file: same length, zero difflib differences, not equal.
    That matters most in the direction this function is used -- `recheck_cell`
    RE-VERIFIES the attacks it returns, and a source whose literal became a raw
    newline can fail to parse and be recorded as REJECTED, which makes the spec
    look stronger than it is. It also silently costs
    `check_stamp_freshness._retained_control` its comparison against the solution
    on disk. Specs about line-break handling do carry such characters as literals.
    Equivalent to `splitlines()` otherwise: no verdict.md in the corpus holds a CR.
    """
    out: dict[str, dict] = {}
    gate = None
    # ("attack"|"control", name, slot) -- the slot is this line's entry in
    # `slots`, so the body can be filled in when its fence closes.
    pending: tuple[str, str, list] | None = None
    old_result = ""
    buf: list[str] | None = None
    slots: dict[str, list[list]] = {}          # gate -> [[kind, name, old, src]]
    xref: dict[str, tuple[int, str]] = {}      # gate -> (attacks claimed, source)
    lines = md.split("\n")
    for line in lines:
        m = _ROLE_RE.match(line)
        if m:
            gate = m.group(1)
            out.setdefault(gate, {"attacks": [], "control": None,
                                  "prepatch_reproduced": None})
            slots.setdefault(gate, [])
            pending, buf = None, None
            continue
        if gate is None:
            continue
        sec = out[gate]
        if buf is not None:
            if _FENCE_RE.match(line):
                src = "\n".join(buf)
                if pending and pending[0] == "attack":
                    sec["attacks"].append((pending[1], src, old_result))
                    pending[2][3] = src
                elif pending and pending[0] == "control":
                    sec["control"] = (pending[1], src)
                    pending[2][3] = src
                pending, buf = None, None
            else:
                buf.append(line)
            continue
        m = _ATTACK_RE.match(line)
        if m:
            slot = ["attack", m.group(2), m.group(3), None]
            slots[gate].append(slot)
            pending, old_result = ("attack", m.group(2), slot), m.group(3)
            continue
        m = _CONTROL_RE.match(line)
        if m:
            slot = ["control", m.group(1), "", None]
            slots[gate].append(slot)
            pending = ("control", m.group(1), slot)
            continue
        m = _XREF_RE.match(line)
        if m:
            xref[gate] = (int(m.group(1)), m.group(2))
            continue
        m = _PREPATCH_RE.match(line)
        if m:
            sec["prepatch_reproduced"] = m.group(1) == "True"
            continue
        if _FENCE_RE.match(line) and pending:
            buf = []
    _resolve_xrefs(out, slots, xref)
    return out


def _resolve_xrefs(out: dict, slots: dict, xref: dict) -> None:
    """Give a cross-referencing role the bodies of the role it points at.

    The attack SOURCES are inherited and nothing else. Each role's own
    `Attack n — ... → outcome` line supplies that role's outcome, because the two
    mechanized gates score one battery against different questions and do record
    different labels for the same attack -- inheriting the outcome too would
    publish one gate's judgment as the other's.

    Fails CLOSED in every direction it can: the section must retain no body of its
    own (so a partly-republished section is never half-inherited), the two attack
    name sequences must match exactly, and the claimed count must match both. A
    record failing any of these keeps zero attacks for that role, exactly what it
    would have had before, and `_verdict_of` then reports the floor as unmet --
    the honest reading of a section whose reference cannot be resolved.
    """
    for gate, (claimed, src_gate) in xref.items():
        sec, ref = out.get(gate), out.get(src_gate)
        if not sec or not ref or sec["attacks"] or gate == src_gate:
            continue
        mine = [s for s in slots.get(gate, ()) if s[0] == "attack"]
        theirs = [s for s in slots.get(src_gate, ()) if s[0] == "attack"]
        if not mine or len(mine) != len(theirs) or len(mine) != claimed:
            continue
        if any(a[1] != b[1] for a, b in zip(mine, theirs)):
            continue
        if any(b[3] is None for b in theirs):
            continue
        sec["attacks"] = [(a[1], b[3], a[2]) for a, b in zip(mine, theirs)]


def recheck_cell(iid: str, backend: str, args) -> dict:
    """Re-verify one cell's retained attacks; -> a row (never writes).

    Takes the shared bundle lock for the whole re-check, not just the write: a
    driver editing the spec mid-flight would make the retained attacks stale
    underneath us, and the labels would describe neither spec.
    """
    from pbt_port_fleet import CellBusy, cell_lock

    row: dict = {"instance_id": iid, "backend": backend, "outcome": "",
                 "detail": "", "roles": {}}
    bundle_dir = ROOT / args.benchmark_dir / iid / backend
    try:
        with cell_lock(bundle_dir):
            row = _recheck_locked(iid, backend, args, row)
            # Write under the SAME lock that judged: releasing first would let
            # another driver re-gate the cell between the verdict and the stamp.
            if args.write and row["outcome"] == "pass":
                row["written"] = write_cell(iid, backend, row, args)
            return row
    except CellBusy as e:
        row["outcome"], row["detail"] = "busy", f"held by {e}; skipped"
        return row


def _recheck_locked(iid: str, backend: str, args, row: dict) -> dict:
    from swebench_unified.adversary import check_attack
    from swebench_unified.backends import get_backend
    from swebench_unified.gates.base import Bundle

    bundle_dir = ROOT / args.benchmark_dir / iid / backend
    vp = bundle_dir / "verdict.md"
    if not vp.is_file():
        row["outcome"], row["detail"] = "no-verdict", "no verdict.md"
        return row
    parsed = parse_verdict(vp.read_text())
    mech = {g: parsed[g] for g in MECHANIZED if g in parsed}
    if not mech:
        row["outcome"], row["detail"] = "no-attacks", "no mechanized role found"
        return row

    # Triage before spending any verifier time. If the original run left even one
    # attack un-adjudicated by the resolve oracle, no re-verification here can
    # settle this cell (the refined patch is not retained), so the outcome is
    # already known -- and a battery is 5-10 attacks x minutes each. A recorded
    # WEAK/BROKEN is separated out because it is a real defect bound for spec
    # repair, not an infra artifact bound for a re-audit.
    pending: dict[str, list[str]] = {}
    for gate, sec in mech.items():
        for name, _src, old in sec["attacks"]:
            cls = classify_old(old)
            if cls in NEEDS_ORACLE:
                pending.setdefault(cls, []).append(f"{gate}/{name}")
    if "break" in pending:
        row["outcome"] = "recorded-break"
        row["detail"] = (f"{len(pending['break'])} attack(s) recorded as "
                         "WEAK/BROKEN (verify⇏correct): a real spec defect, "
                         f"not clearable ({', '.join(pending['break'][:3])})")
        return row
    if pending:
        flat = [n for v in pending.values() for n in v]
        by_class = "; ".join(f"{k}={len(v)}" for k, v in sorted(pending.items()))
        row["outcome"] = "needs-live"
        row["detail"] = (f"{len(flat)} attack(s) never adjudicated by the resolve "
                         f"oracle ({by_class}); the refined patch is not "
                         "retained, so only a live audit can settle them")
        return row

    bundle = Bundle(iid, get_backend(backend))
    fe = bundle.float_encoding() if backend == "nagini" else None
    ext = Path(bundle.solution).suffix or ".py"
    # The baseline every retained diff was taken against. Read once per cell, under
    # the same lock as the judgment: a driver rewriting the spec file mid-flight
    # would make every hunk fail to apply, which reads as an unrecoverable record
    # rather than as the race it is.
    try:
        spec_text = Path(bundle.solution).read_text()
    except OSError:
        spec_text = ""

    def _whole(src: str) -> str | None:
        """The program a retained body denotes, or None if it is a diff that will
        not apply. A whole-source body is itself."""
        if not is_diff_body(src):
            return src
        return reconstruct_from_diff(spec_text, src) if spec_text else None

    # One scratch dir per cell: check_attack takes a PATH, and the retained
    # source has to land somewhere the verifier can read. mktemp, never a fixed
    # name -- concurrent cells would collide and /tmp is reaped.
    with tempfile.TemporaryDirectory(prefix=f"recheck_{iid[:24]}_") as td:
        d = Path(td)
        for gate, sec in mech.items():
            res = {"attacks": [], "control": None,
                   "prepatch_reproduced": sec["prepatch_reproduced"]}
            # A diff-retained body is not a program, so it is rebuilt from the spec
            # file first. `diff_retained` names only the bodies that could NOT be
            # recovered -- verifying one of those would produce a rejection that
            # says nothing about the spec. See `_DIFF_BODY_RE`.
            whole = {n: _whole(s) for n, s, _o in sec["attacks"]}
            res["diff_retained"] = [n for n, s, _o in sec["attacks"]
                                    if is_diff_body(s) and whole[n] is None]
            for i, (name, src, old) in enumerate(sec["attacks"], 1):
                src = whole[name]
                if src is None:
                    continue
                p = d / f"{gate}_{i}_{Path(name).name}"
                if p.suffix != ext:
                    p = p.with_suffix(ext)
                p.write_text(src.rstrip("\n") + "\n")
                r = check_attack(backend, iid, p, fe)
                res["attacks"].append({
                    "name": name, "old": old, "old_class": classify_old(old),
                    "completed": bool(r.get("verify_completed", True)),
                    "same_spec": bool(r.get("same_spec")),
                    "verifies": bool(r.get("verifies")),
                    "summary": str(r.get("summary", ""))[:160]})
            ctrl_src = _whole(sec["control"][1]) if sec["control"] else None
            if sec["control"] and ctrl_src is not None:
                name, _src = sec["control"]
                p = d / f"{gate}_control_{Path(name).name}"
                if p.suffix != ext:
                    p = p.with_suffix(ext)
                p.write_text(ctrl_src.rstrip("\n") + "\n")
                r = check_attack(backend, iid, p, fe)
                res["control"] = {
                    "name": name,
                    "completed": bool(r.get("verify_completed", True)),
                    "same_spec": bool(r.get("same_spec")),
                    "verifies": bool(r.get("verifies")),
                    "summary": str(r.get("summary", ""))[:160]}
            row["roles"][gate] = res

    row.update(_verdict_of(row["roles"], args.min_attacks))
    return row


def _verdict_of(roles: dict, min_attacks: int) -> dict:
    """Mirror of build_one._derive_audit_verdict's floor, minus the resolve leg
    (no retained patches). Worst role wins: this is one cell's outcome.

    Each attack is judged against the class its ORIGINAL label settled, which is
    what makes a re-verification interpretable. An attack the oracle called a
    `correct echo` is SUPPOSED to verify -- re-verifying confirms it. An attack the
    original run rejected must still be rejected; if it now verifies, the spec did
    weaken since, and only the resolve leg can adjudicate that.
    """
    order = {"pass": 0, "inconclusive": 1, "needs-live": 2, "candidate": 3}
    worst, detail = "pass", []
    for gate, res in roles.items():
        atk = res["attacks"]
        bad, notes = [], []
        # Said FIRST, and in the record's own terms, because it is the reason the
        # rest of this role's floor is unmet: a diff-retained body was never run,
        # so no sentence below it is a measurement of the current spec.
        diffs = res.get("diff_retained") or []
        if diffs:
            bad.append(f"{len(diffs)} retained attack(s) are published as a diff "
                       "against the cell's spec file, not as whole programs "
                       f"({', '.join(diffs[:3])}), so this record cannot be "
                       "re-derived without a live audit")
        if len(atk) < min_attacks:
            bad.append(f"only {len(atk)} attacks (need >= {min_attacks})")
        if not res.get("prepatch_reproduced"):
            bad.append("prepatch bug not reproduced")
        ctrl = res.get("control")
        if not ctrl:
            bad.append("no positive control")
        elif not (ctrl["completed"] and ctrl["same_spec"] and ctrl["verifies"]):
            bad.append(f"positive control did not verify ({ctrl['summary']})")

        # An attack whose adjudication needed the resolve oracle cannot be
        # settled from verdict.md: `patches` is not retained. Report it and
        # write nothing -- these belong to a live audit.
        oracle = [a["name"] for a in atk if a["old_class"] in NEEDS_ORACLE]

        # Attacks the original run had SETTLED as echoes: verifying again is the
        # expected outcome and carries the oracle's `resolved` verdict with it.
        echo_ok, echo_bad = [], []
        for a in atk:
            if a["old_class"] != "echo":
                continue
            (echo_ok if (a["completed"] and a["verifies"]) else echo_bad).append(a["name"])
        if echo_bad:
            # An echo that no longer verifies means the spec got STRICTER and now
            # rejects a correct implementation -- a soundness problem in the other
            # direction, and not something to clear silently.
            bad.append(f"{len(echo_bad)} adjudicated echo(es) no longer verify "
                       f"({', '.join(echo_bad[:3])}): spec may now reject a "
                       "correct impl")
        if echo_ok:
            notes.append(f"{len(echo_ok)} echo(es) re-verify as expected "
                         "(their patches resolved under the oracle)")

        # The falsification lane proper: attacks the original run REJECTED must
        # still fail to verify against the current spec.
        lane = [a for a in atk if a["old_class"] == "reject"]
        verifying = [a["name"] for a in lane
                     if a["completed"] and a["same_spec"] and a["verifies"]]
        inc = [a["name"] for a in lane if not a["completed"]]
        # A `timeout` attack was NEVER adjudicated: the original verifier hit its
        # cap, so nothing is known about whether the spec rejects it. Re-running at
        # a bigger cap can only add information, never contradict -- there is no
        # earlier verdict to weaken from. So it joins the falsification lane only
        # once it REJECTS (which retroactively settles it); if it verifies it is an
        # unadjudicated candidate for the resolve oracle, exactly like a
        # `same-spec AND verifies` attack.
        to = [a for a in atk if a["old_class"] == "timeout"]
        to_verify = [a["name"] for a in to
                     if a["completed"] and a["same_spec"] and a["verifies"]]
        inc += [a["name"] for a in to if not a["completed"]]
        if to_verify:
            oracle = list(oracle) + to_verify
        # A rejected attack that no longer shares the bundle's spec is evidence
        # about a spec that no longer exists: the cell was edited after the audit
        # ran (a MustTerminate obligation added to the pre-conditions region does
        # exactly this, since the region is part of the shared spec). It cannot
        # clear anything, having never challenged the current spec, so this fails
        # closed and the cell goes back to the agent lane rather than passing on
        # stale work. Attacks the ORIGINAL run had already discarded as
        # spec-changing are exempt: the derivation ignored them
        # (audit_verdict.py:344).
        stale = [a["name"] for a in lane if a["completed"] and not a["same_spec"]]
        if stale:
            bad.append(f"{len(stale)} retained attack(s) no longer share the "
                       "bundle's spec (bundle edited since the audit)")

        if verifying:
            v, why = "candidate", (f"{gate}: {len(verifying)} attack(s) the "
                                   "original run REJECTED now VERIFY "
                                   f"({', '.join(verifying[:3])}) — the spec "
                                   "weakened; needs the resolve leg")
        elif oracle:
            v, why = "needs-live", (f"{gate}: {len(oracle)} attack(s) were never "
                                    "adjudicated by the oracle "
                                    f"({', '.join(oracle[:3])}); the refined "
                                    "patch is not retained, so only a live "
                                    "audit can settle them")
        elif inc:
            v, why = "inconclusive", (f"{gate}: {len(inc)} attack(s) still "
                                      "inconclusive at this cap")
        elif bad:
            v, why = "inconclusive", f"{gate}: floor not met — " + "; ".join(bad)
        else:
            v, why = "pass", (f"{gate}: {len(atk)} attacks re-run from the "
                              "retained evidence, none breaks the spec; "
                              "positive control verifies")
            if notes:
                why += "; " + "; ".join(notes)
        detail.append(why)
        if order[v] > order[worst]:
            worst = v
    return {"outcome": worst, "detail": " || ".join(detail)}


# Why a cell is being re-derived, in the words the recorded note will carry.
# "the original run timed out" and "the spec moved after the audit ran" are
# different claims about the same re-verification and at most one is true of any
# cell, so the caller says which rather than the note asserting one over every row.
_REASONS = {
    "timeout": ("Re-derived at a higher verifier cap after a host-load timeout "
                "had made the original run inconclusive; same attacks, same "
                "derivation."),
    "spec-edit": ("Re-derived against the spec this bundle now ships, after a "
                  "later edit moved the spec view the original audit ran "
                  "against; same attacks, same derivation, so the evidence "
                  "behind this verdict is the original battery re-measured "
                  "rather than a fresh one."),
}


# The published label of an attack whose ORIGINAL verifier ran out of clock.
#
# `_verdict_of` can only return `pass` when every `timeout`-class attack
# COMPLETED at the higher cap and did not verify: one still incomplete lands in
# `inc`, one that completes and verifies lands in `oracle`, and both outrank a
# pass. So a written pass is itself the proof that each of those attacks was
# measured and rejected -- "which retroactively settles it", above.
#
# Recording that in meta.json while verdict.md still says `inconclusive` publishes
# evidence that disagrees with the status it licensed, and the cost is not
# hypothetical: `construct/audit_note` composes its release note FROM the retained
# table, meets a label outside its whitelist on a PASSING gate, and declines to
# describe the record at all -- correctly, because from the file alone the pass
# looks like it rests on an undecided attack.
#
# The gloss keeps the original timeout rather than erasing it. A reader is
# entitled to know this line is a second measurement, and the sentence has to
# survive being read next to the `recheck` block in meta.json that says the same.
_RELABEL_GLOSS = ("same spec, does not verify — re-derived at a higher verifier "
                  "cap after the original run's verifier timed out")


def relabel_settled_timeouts(md: str, roles: dict) -> tuple[str, list[str]]:
    """verdict.md with every SETTLED `inconclusive` attack label rewritten.

    Only the `Attack n — ...` header line is touched, never a fenced body: the
    retained source is the evidence, and `check_stamp_freshness._retained_control`
    compares the control's body against the solution on disk byte for byte.

    Conservative on purpose. A line is rewritten only when the original label
    classified as `timeout` AND this run's re-verification `completed`, shares the
    bundle's spec, and does not verify. Anything else keeps its label, which keeps
    the enricher declining the record -- the safe direction, since a declined note
    is merely short and a wrong one is a false claim about a spec.

    Attack numbering restarts per role and names repeat across roles, so the gate
    heading is tracked exactly as `parse_verdict` tracks it, fresh results are
    paired within a gate by position, and the name is re-checked before any rewrite.
    """
    out: list[str] = []
    changed: list[str] = []
    gate: str | None = None
    seen = 0
    for line in md.split("\n"):
        m = _ROLE_RE.match(line)
        if m:
            gate, seen = m.group(1), 0
            out.append(line)
            continue
        m = _ATTACK_RE.match(line) if gate else None
        if not m:
            out.append(line)
            continue
        name, old = m.group(2), m.group(3)
        fresh = (roles.get(gate) or {}).get("attacks") or []
        a = fresh[seen] if seen < len(fresh) else None
        seen += 1
        if (a and a["name"] == name and classify_old(old) == "timeout"
                and a["completed"] and a["same_spec"] and not a["verifies"]):
            out.append(f"Attack {m.group(1)} — `{name}` → rejected "
                       f"({_RELABEL_GLOSS})")
            changed.append(f"{gate}/{name}")
        else:
            out.append(line)
    return "\n".join(out), changed


# A role's published HEAD -- the `## Role n` heading, the `status (recorded)`
# bullet and the `machine verdict` bullet -- is composed FROM the stamp
# (`verdict_record._render_sections`), so a run that re-derives the stamp without
# re-rendering the file leaves the head publishing the earlier attempt's answer
# above the earlier attempt's evidence.
#
# WHAT IS NOT TOUCHED, and why the `recheck` payload is the licence. A stale head
# is sometimes the only surviving evidence for the stamp above it: it is where an
# earlier attempt's status and machine verdict are still written down, so a head
# disagreeing with a DEMOTED stamp is the record of what was demoted, and
# rewriting it destroys what a restoration would have to be proved from. `recheck`
# is the narrow, positive licence -- `write_cell` writes it for the attacks it
# re-verified out of this very file, so head and stamp then describe one
# measurement and the head is merely the older copy of it. A head without the
# payload is left exactly as it is, and a block documenting a demotion is skipped
# even when the payload is there. Only the three head fields ever move: attack
# bodies, positive controls and counterexample transcripts are evidence. A head
# whose shape is not the composer's is REPORTED rather than guessed at.
#
# AN ENRICHED STAMP IS NOT A DISAGREEMENT. The composer publishes a note's
# per-attack account as a block BELOW the bullet, because a multi-line string
# pasted after a list marker ends the list at the first newline
# (`verdict_record._render_note` splits on exactly that). So an enriched role's
# note is `<tally>\n\n<account>` while its bullet carries the tally alone, and
# comparing the whole field would call every enriched role stale: `note_head` is
# the one line a bullet can hold and `note_account` is the rest.
_ALIGN_ROLES = ("G-EQ", "G-PANEL-1", "G-PANEL-2", "G-PANEL-3")
# Looser than `_ROLE_RE`, which needs a label after the gate: a head that
# published no label is exactly the shape this has to find, and the label is
# matched with `[^:]+` for the reason `_split_role_blocks` does -- a role label
# never contains a colon, so the FIRST one separates label from status and the
# colon inside `(agent: ...)` cannot be mistaken for it.
_HEAD_RE = re.compile(r"^## Role \d+ — (\S+)")
_HEAD_STATUS_RE = re.compile(r"^(## Role \d+ — [^:]+): (\S+)((?: \(agent: .*)?)$")
_RECORDED_RE = re.compile(r"^- \*\*status \(recorded\):\*\* `([^`]*)`(.*)$")
_MACHINE_RE = re.compile(r"^- \*\*machine verdict:\*\* (.*)$")
# `merge_verdict_md` above a retained block, and the sentence the composer writes
# for a role whose latest attempt produced nothing. Either one means the head is
# a demotion record.
_DEMOTION_RE = re.compile(
    r"did not reach a verdict for this role"
    r"|reached no verdict on the latest attempt", re.I)


def note_head(note: str) -> str:
    """The one line of a recorded note a `machine verdict` bullet can carry."""
    return (note or "").strip().split("\n", 1)[0].strip()


def note_account(note: str) -> str:
    """Whatever that note holds past its first line, or `""`."""
    return (note or "").strip()[len(note_head(note)):].strip()


def _flat(text: str) -> str:
    """`text` with its whitespace collapsed, for a containment test.

    The account is published as a block and read back out of a line-split file,
    so a byte comparison would turn any rewrap into a false disagreement.
    """
    return " ".join((text or "").split())


def role_span(lines: list[str], gate: str) -> tuple[int, int] | None:
    """`[start, end)` of the FIRST role section for `gate`, or None.

    Fence-aware: an attack body may quote a role heading, and a span taken from
    inside one would put the bullet scan in the middle of the evidence.
    """
    fence = False
    start = -1
    for i, ln in enumerate(lines):
        if ln.startswith("```"):
            fence = not fence
            continue
        if fence:
            continue
        m = _HEAD_RE.match(ln)
        if not m:
            continue
        if start >= 0:
            return start, i                    # the next role bounds this one
        if m.group(1).rstrip(":") == gate:
            start = i
    return (start, len(lines)) if start >= 0 else None


def align_role(md: str, gate: str,
               entry: dict | None) -> tuple[str, list[str], str]:
    """`(md, changed field names, decline reason)` for one role's head.

    Rewrites nothing unless `entry` is a passing stamp carrying the `recheck`
    payload; see the comment above for why that is the licence.
    """
    if not isinstance(entry, dict):
        return md, [], "no stamp"
    if entry.get("status") != "pass":
        return md, [], f"stamp is {entry.get('status')!r}, not a pass"
    if not entry.get("recheck"):
        return md, [], "stamp carries no recheck payload"
    note = (entry.get("note") or "").strip()
    if not note:
        return md, [], "stamp has no note"

    lines = md.split("\n")
    span = role_span(lines, gate)
    if span is None:
        return md, [], "no role section"
    start, end = span
    if _DEMOTION_RE.search("\n".join(lines[start:end])):
        return md, [], "head records a demotion; evidence for a restore"

    # The status bullets sit between the heading and the first fenced body. Bound
    # the scan there so a `- **machine verdict:**` line QUOTED inside an attack
    # can never be taken for the role's own bullet.
    head_end = next((i for i in range(start, end)
                     if lines[i].startswith("```")), end)

    changed: list[str] = []
    m = _HEAD_STATUS_RE.match(lines[start])
    if not m:
        return md, [], f"unrecognised heading: {lines[start][:60]!r}"
    if m.group(2) not in STATUSES:
        return md, [], f"unrecognised heading status {m.group(2)!r}"
    if m.group(2) != "pass":
        lines[start] = f"{m.group(1)}: pass{m.group(3)}"
        changed.append("heading")

    for i in range(start, head_end):
        m = _RECORDED_RE.match(lines[i])
        if m:
            if m.group(1) != "pass":
                lines[i] = f"- **status (recorded):** `pass`{m.group(2)}"
                changed.append("status (recorded)")
            break
    else:
        return md, [], "no `status (recorded)` bullet"

    for i in range(start, head_end):
        m = _MACHINE_RE.match(lines[i])
        if m:
            pub, account = m.group(1).strip(), note_account(note)
            if pub == note:
                break
            # An enriched stamp: the bullet publishes the tally and the account
            # is a block further down the same section -- the shape the renderer
            # produces, so it agrees with the stamp and there is nothing to move.
            if (pub == note_head(note)
                    and _flat(account) in _flat("\n".join(lines[start:end]))):
                break
            if account:
                return md, [], ("stamp note is multi-line and its account is "
                                "not published below; placing that block is "
                                "the composer's job, not a head repair")
            lines[i] = f"- **machine verdict:** {note}"
            changed.append("machine verdict")
            break
    else:
        return md, [], "no `machine verdict` bullet"

    if not changed:
        return md, [], ""
    return "\n".join(lines), changed, ""


def align_cell(md: str, gates: dict) -> tuple[str, dict[str, list[str]]]:
    """`md` with every eligible role head aligned, and what moved per gate.

    Applied one role at a time and re-spanned each time, because a heading
    rewrite changes the line the next span would be measured from.
    """
    moved: dict[str, list[str]] = {}
    for gate in _ALIGN_ROLES:
        new, changed, _why = align_role(md, gate, (gates or {}).get(gate))
        if changed:
            md, moved[gate] = new, changed
    return md, moved


def write_cell(iid: str, backend: str, row: dict, args) -> str:
    """Record the cleared verdict for a `pass` row. Stamps the SAME shape
    run_audit_stage does (status/note/model) so gates/_audit.recorded_verdict reads
    it back, says in the note that this was a re-derivation, and re-labels any
    attack in verdict.md this run settled, so the published evidence and the
    recorded status describe the same measurement.
    """
    if row["outcome"] != "pass":
        return "not written (not a pass)"
    from swebench_unified.backends import get_backend
    from swebench_unified.construct.build_one import (_GATE_DERIVE_ROLE,
                                                      _ROLE_READS)
    from swebench_unified.gates.base import (Bundle, GateResult,
                                             source_digests, stamp)

    bundle = Bundle(iid, get_backend(backend))
    p = ROOT / args.benchmark_dir / iid / backend / "meta.json"
    meta = json.loads(p.read_text())
    blob = meta.setdefault("gates", {})
    for gate, res in row["roles"].items():
        n = len(res["attacks"])
        # Stamp the same provenance a live audit role writes. Without it the record
        # keeps the ORIGINAL run's timestamp and digests, so a re-derived verdict
        # reads as one measured against the earlier artifacts -- exactly the
        # confusion this re-derivation exists to clear up.
        s = stamp(GateResult(gate, "pass"), "strict")
        entry = {
            "status": "pass",
            "note": (f"{gate}: {n} attacks re-verified from the retained audit "
                     "evidence (verdict.md), none breaks the spec; positive "
                     "control verifies. " + _REASONS[args.reason]),
            "recheck": {"attacks": n, "timeout_s": args.timeout,
                        "reason": args.reason},
            "checked_at": s.checked_at, "code_version": s.code_version,
            "harness_digest": s.harness_digest,
        }
        digests = source_digests(
            bundle, _ROLE_READS.get(_GATE_DERIVE_ROLE.get(gate, ""), ()))
        if digests:
            entry["sources"] = digests
        blob.setdefault(gate, {}).update(entry)
    p.write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n")

    vp = p.parent / "verdict.md"
    relabelled: list[str] = []
    aligned: dict[str, list[str]] = {}
    if vp.exists():
        md = vp.read_text()
        md, relabelled = relabel_settled_timeouts(md, row["roles"])
        # The role HEAD is composed from the stamp, so a stamp this run rewrote
        # leaves the published heading, `status (recorded)` and `machine verdict`
        # quoting the earlier attempt -- a passing gate whose own record says it
        # reached no verdict. Aligning them keeps the two halves of the artifact
        # describing one measurement; `align_role` refuses any head it is not
        # licensed to touch, and the licence is the `recheck` payload written into
        # `blob` just above.
        md, aligned = align_cell(md, blob)
        if relabelled or aligned:
            vp.write_text(md)
    row["relabelled"] = relabelled
    row["aligned"] = {g: c for g, c in aligned.items()}
    extra = []
    if relabelled:
        extra.append(f"{len(relabelled)} settled attack label(s) re-derived")
    if aligned:
        extra.append(f"{len(aligned)} role head(s) aligned")
    return f"written (+{'; +'.join(extra)})" if extra else "written"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lane-file", required=True,
                    help="<instance_id>\\t<backend> per line")
    ap.add_argument("--benchmark", default=os.environ.get("SBU_BENCHMARK",
                                                          "swe_bench_verified"))
    ap.add_argument("--benchmark-dir", default=default_benchmark_dir())
    ap.add_argument("--jobs", type=int, default=6)
    ap.add_argument("--timeout", type=int, default=1200,
                    help="per-attack verifier cap (SBU_ATTACK_VERIFY_TIMEOUT)")
    ap.add_argument("--min-attacks", type=int, default=5)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--write", action="store_true",
                    help="record cleared verdicts into meta.json")
    ap.add_argument("--reason", choices=sorted(_REASONS), default="timeout",
                    help="what made the re-derivation necessary; goes into the "
                         "recorded note verbatim")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    os.environ["SBU_BENCHMARK"] = args.benchmark
    os.environ["SBU_BENCHMARK_DIR"] = args.benchmark_dir
    os.environ["SBU_ATTACK_VERIFY_TIMEOUT"] = str(args.timeout)

    cells = []
    for line in Path(args.lane_file).read_text().split("\n"):
        parts = line.split()
        if len(parts) >= 2:
            cells.append((parts[0], parts[1]))
    if args.limit:
        cells = cells[:args.limit]
    print(f"# {len(cells)} cell(s), jobs={args.jobs}, cap={args.timeout}s, "
          f"write={args.write}", flush=True)

    rows, done = [], 0
    with ThreadPoolExecutor(max_workers=args.jobs) as ex:
        futs = {ex.submit(recheck_cell, i, b, args): (i, b) for i, b in cells}
        for f in as_completed(futs):
            iid, backend = futs[f]
            done += 1
            try:
                row = f.result()
            except Exception as e:                     # infra, not a verdict
                row = {"instance_id": iid, "backend": backend,
                       "outcome": "error", "detail": f"{type(e).__name__}: {e}",
                       "roles": {}}
            rows.append(row)
            print(f"[{done}/{len(cells)}] {row['outcome']:13s} {backend:7s} "
                  f"{iid:38s} {row['detail'][:110]}", flush=True)

    tally: dict[str, int] = {}
    for r in rows:
        tally[r["outcome"]] = tally.get(r["outcome"], 0) + 1
    print("# " + "  ".join(f"{k}={v}" for k, v in sorted(tally.items())))
    if args.out:
        Path(args.out).write_text(json.dumps(rows, indent=1))
        print(f"# report -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
