#!/usr/bin/env python
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Run a wave of INDEPENDENT audits over ported G-PBT batteries.

The port fleet's gate answers "does every case behave as declared". This answers
the question that survives it: is the recorded SOUND EARNED. They are different
questions, and only the second one catches a battery that passes for the wrong
reason — a rival that is merely reshaped rather than wrong, a positive whose
proof was restated rather than reproven, a witness that fails on gold for a
syntactic reason, a rationale claiming a sub-domain nothing demonstrates.

Only cells whose G-PBT already records a pass are auditable: a cell that has not
passed the gate is a port job, not an audit job, and mixing the two would let an
audit "fix" a cell into passing and then attest to its own repair.

The audit agent MAY edit `properties.py` (repairing a bad case is the point) and
may NOT touch the frozen artifact. That asymmetry is why the verdict this script
records is not the agent's: after the agent finishes, the real gate is re-run and
the stamped status is read back out of meta.json. An audit that edited a cell
into failing is a regression the driver reports, not a verdict the agent gets to
narrate.

What the payload contributes that no gate can re-derive is WHICH cases were
examined and with what evidence, so it is recorded alongside the re-run status.

Usage:
  SBU_BENCHMARK=swe_bench_verified SBU_BENCHMARK_DIR=benchmark-verified \\
    python scripts/pbt_audit_fleet.py --backend lean --jobs 24 \\
      [--instances a b c | --limit N] [--resume] [--dry-run]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from pbt_port_fleet import (VERIFY_TIMEOUT_DEFAULT, CellBusy,  # noqa: E402
                            _env, _py, cell_lock, recorded_pbt)
from swebench_unified.atomic_io import write_json_atomic  # noqa: E402
from swebench_unified.backends import get_backend  # noqa: E402
from swebench_unified.corpus_root import default_benchmark_dir  # noqa: E402
from swebench_unified.paths import EXPERIMENTS_ROOT  # noqa: E402

AUDIT_TIMEOUT_DEFAULT = 7200   # the probe attacks (D/E) are real lake builds
GATE_TIMEOUT_DEFAULT = 7200
# Where an audit's own record lives. Not a gate: gates are the collaborator's
# schema and an advisory audit must not masquerade as one.
AUDIT_KEY = "pbt_audit"

# `submit_result`'s schema is deliberately loose (it captures a self-report; the
# gate is what judges), so nothing forces an agent to use the field names the
# prompt lists, and a wave produces about as many payload shapes as it has
# agents. Reading only the documented names silently discards a real audit's
# record and reports the cell as `no-payload`, so the shapes that occur are
# aliased rather than the schema tightened: a rejected submission would lose the
# report entirely, and the report is the one thing the re-run gate cannot
# reproduce.
_ALIASES: dict[str, tuple[str, ...]] = {
    "verdict": ("verdict", "audit_verdict", "conclusion", "final_verdict"),
    "cases": ("cases", "per_case_verdicts", "case_verdicts"),
    "attacks_tried": ("attacks_tried", "attacks", "attacks_run", "probes"),
    "spec_holes": ("spec_holes", "spec_defect", "spec_defects",
                   "frozen_spec_defect"),
    "omissions_reviewed": ("omissions_reviewed", "omissions", "nagini_omissions"),
    "witnesses_rebuilt": ("witnesses_rebuilt", "witness_exit_codes",
                          "exit_codes_observed"),
    "edited": ("edited", "edits_made", "battery_edited",
               "properties_py_edited", "repairs_made", "bundle_changes"),
    "notes": ("notes", "summary", "spec_summary", "explanation"),
    "regate_verdict": ("regate_verdict", "gate_rerun_verdict", "gate_verdict",
                       "gate_rerun", "gate_reran", "final_gate_rerun"),
}

# Agents write "none"/"no"/"n/a" prose where the schema wants an empty list, so
# a bare truthiness test reads the STRING "none" as a reported defect.
_NEGATIVE = {"", "none", "no", "n/a", "na", "null", "nil", "false", "-",
             "no spec defect", "no spec defects", "none found", "not found",
             "no defect", "no defects", "no holes", "none observed"}
# A sentence that OPENS with a negation. Kept separate from `_NEGATIVE` and used
# only for the boolean field, because the two error directions are not
# symmetric: misreading "none to properties.py; removed a __pycache__ dir" as
# edited=True is cosmetic, while misreading a spec hole whose description
# happens to begin with "no" as "nothing reported" would DISCARD a real finding.
# So prose-negation is honoured for `edited` and never for the evidence fields.
_NEGATIVE_LEAD = re.compile(r"^\s*(none|no|not|nope|n/a|nil|null|false)\b",
                            re.I)


def _is_empty(v) -> bool:
    """True when a field says "nothing here", however the agent spelled it."""
    if v is None or v is False:
        return True
    if isinstance(v, str):
        return v.strip().lower() in _NEGATIVE
    if isinstance(v, (list, tuple, dict)):
        # a list of "none" strings is still nothing
        return all(_is_empty(x) for x in
                   (v.values() if isinstance(v, dict) else v))
    return False


def normalize(payload: dict | None) -> dict:
    """Map an agent's field names onto the documented ones.

    Unrecognized keys are preserved so nothing an audit reported is lost, but
    the canonical names are what the driver and the recorded artifact read.
    """
    if not isinstance(payload, dict):
        return {}
    out = dict(payload)
    for canon, names in _ALIASES.items():
        if not _is_empty(out.get(canon)):
            continue
        for n in names:
            if n in payload and not _is_empty(payload[n]):
                out[canon] = payload[n]
                break
    # `witnesses_rebuilt` is documented as a count; agents often send the exit
    # codes themselves, which is strictly more evidence. Keep both.
    wr = out.get("witnesses_rebuilt")
    if isinstance(wr, (list, dict)):
        out["witness_evidence"] = wr
        out["witnesses_rebuilt"] = len(wr)
    for k in ("spec_holes", "attacks_tried", "omissions_reviewed"):
        if _is_empty(out.get(k)):
            out[k] = []
    ed = out.get("edited")
    # Prose here is usually a DESCRIPTION of the edits rather than a flag, and as
    # often a denial as a confirmation ("none to properties.py; removed a
    # __pycache__ dir"). Keep the description and read the flag from its leading
    # negation. The driver overwrites this with a hash comparison anyway; this
    # only matters when there is no before-hash to compare against.
    if isinstance(ed, str):
        out["edits_described"] = ed
        out["edited"] = not (_is_empty(ed) or bool(_NEGATIVE_LEAD.match(ed)))
    else:
        out["edited"] = not _is_empty(ed)
    return out


def reports_a_spec_hole(payload: dict) -> bool:
    """Whether this audit actually reported a hole in the FROZEN spec.

    A hole is the highest-value thing this lane can produce, so it must not be
    diluted -- but it must not be invented either, and a bare truthiness test on
    `spec_holes` invents them. The field is documented as a list and arrives as
    prose about as often, and prose here is usually a DENIAL: "none - attacks D
    and E found no hole in the frozen spec" is truthy, and `_is_empty`'s fixed
    vocabulary of negatives cannot recognize a whole sentence as one.

    Widening `_is_empty` to strip prose negation is the wrong fix: reading a real
    finding whose description opens with "no" as "nothing reported" would DISCARD
    it, and the two error directions are not symmetric (see `_NEGATIVE_LEAD`).

    So a prose denial is trusted only when the VERDICT agrees with it. SHIP and
    REPAIRED are the verdicts that cannot express a hole -- the documented ones
    for a hole are SPEC-DEFECT and CORRUPT -- so a denial under SHIP is
    corroborated by the field the agent was most likely to fill in correctly.
    Under any other verdict the row stays a spec-defect for a human to read.

    Both spellings of the verdict field are accepted because this predicate has
    two callers with two shapes: the live driver passes the payload, where the
    field is `verdict`, while anything re-reading a RECORDED audit passes what
    `record_audit` wrote, where it is `agent_verdict` (keeping the agent's claim
    visibly distinct from the gate's `gate_verdict_after`). Reading only `verdict`
    there sees an empty string, so the corroboration branch never fires and EVERY
    prose denial reads back as a fabricated spec hole.
    """
    holes = payload.get("spec_holes")
    if not holes:
        return False
    verdict = str(payload.get("verdict")
                  or payload.get("agent_verdict") or "").strip().upper()
    denied = isinstance(holes, str) and bool(_NEGATIVE_LEAD.match(holes))
    return not (denied and verdict in ("SHIP", "REPAIRED"))


def is_complete(rec: dict) -> bool:
    """Whether a recorded audit carries the evidence the payload spec asks for.

    Used by `--resume-incomplete` to re-audit the cells whose record predates a
    prompt change. Three fields are load-bearing and none is recoverable from the
    artifact: the per-case verdict list (which cases were examined at all), the
    witness exit codes (the discrimination re-derivation, attack B), and the new
    rivals/reshapes (attacks D and E). `attacks_tried` arrives as a list of dicts
    or as a dict keyed by attack letter depending on the prompt generation, and
    both are real evidence, so shape is not the test.

    A record written before the payload spec named those fields cannot be topped
    up, only re-audited: the attacks ran, but nothing kept their exit codes, and
    an attack leaves no other trace in the artifact.
    """
    def filled(v) -> bool:
        return bool(v) and not _is_empty(v)

    return (filled(rec.get("cases"))
            and filled(rec.get("witness_evidence"))
            and filled(rec.get("attacks_tried")))


def audited(bundle: Path) -> dict | None:
    """This cell's recorded audit, if any — and `--resume` skips on this.

    A record needs BOTH a stamp and a verdict. The stamp rule is the gates'
    convention (an entry with no timestamp is a placeholder). The verdict rule is
    this lane's: an audit is recorded even when the agent submitted nothing,
    because the re-run gate DID run and its status is worth keeping -- but such a
    record attests to nothing about which cases were examined, which is the only
    thing an audit contributes that a gate cannot re-derive, so treating it as
    done would strand the cell permanently. The driver already distinguishes this
    as `no-payload`; this makes the ARTIFACT agree with it.
    """
    try:
        meta = json.loads((bundle / "meta.json").read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    rec = meta.get(AUDIT_KEY)
    if not (isinstance(rec, dict) and rec.get("audited_at")):
        return None
    # `or ""` before `str`, not after: `str(None)` is the truthy "None", so a
    # record whose verdict came back as JSON null would read as a real one.
    return rec if str(rec.get("agent_verdict") or "").strip() else None


def record_audit(bundle: Path, payload: dict, regate: tuple[str | None, str],
                 stamp: str) -> None:
    """Stamp the audit outcome into meta.json, next to the gates.

    Written AFTER the re-run gate, and carrying that gate's status rather than
    the agent's claim, so a released bundle records what was checked and by what
    evidence — an audit whose only trace is a log file cannot be cited later.

    A cell audited a SECOND time keeps the first record under `history`. A
    re-audit under a sharpened prompt is a genuinely stronger check, but the
    earlier record is independent evidence from a different agent and overwriting
    it would trade two audits for one. `history` holds the prior records
    oldest-first; the live fields always describe the newest.
    """
    path = bundle / "meta.json"
    try:
        meta = json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return
    st, verdict = regate
    prior = meta.get(AUDIT_KEY)
    history: list = []
    if isinstance(prior, dict) and prior.get("audited_at"):
        # Flatten rather than nest: the previous record's own history plus the
        # record itself, so the list stays one level deep however many times a
        # cell is re-audited.
        history = list(prior.get("history") or [])
        history.append({k: v for k, v in prior.items() if k != "history"})
    meta[AUDIT_KEY] = {
        "audited_at": stamp,
        # the gate's word, not the agent's
        "gate_status_after": st,
        "gate_verdict_after": verdict,
        "agent_verdict": str(payload.get("verdict", "")),
        # measured by hash, not self-reported
        "edited": bool(payload.get("edited")),
        # present only when violated, so a clean record stays quiet
        **({"frozen_artifact_modified": True}
           if payload.get("frozen_artifact_modified") else {}),
        "witnesses_rebuilt": payload.get("witnesses_rebuilt"),
        "witness_evidence": payload.get("witness_evidence"),
        "cases": payload.get("cases"),
        "attacks_tried": payload.get("attacks_tried"),
        "spec_holes": payload.get("spec_holes"),
        "omissions_reviewed": payload.get("omissions_reviewed"),
        "notes": str(payload.get("notes", ""))[:4000],
        # absent on a first audit, so a single-audit record stays as it was
        **({"history": history} if history else {}),
    }
    write_json_atomic(path, meta)


def run_audit(iid: str, backend: str, benchmark: str, benchmark_dir: str,
              log_dir: Path, timeout_s: int, model: str | None,
              lean_slots: int) -> dict:
    """One audit agent for one cell, out of process."""
    script = (
        "import sys, json\n"
        f"sys.path.insert(0, {str(ROOT / 'src')!r})\n"
        "from swebench_unified.agent import run_agent_step, DEFAULT_MODEL\n"
        "from swebench_unified.prompts import load_prompt\n"
        "from swebench_unified import paths\n"
        "from swebench_unified.backends import get_backend\n"
        f"iid, bk = {iid!r}, {backend!r}\n"
        "lang = get_backend(bk).language\n"
        "system = load_prompt('pbt_audit_system', backend=bk)\n"
        "user = load_prompt('pbt_audit', backend=bk, iid=iid, backend_name=bk,\n"
        "                   root=paths.tasks_root_rel(),\n"
        "                   solution_filename=lang.solution_filename)\n"
        f"model = {model!r} or DEFAULT_MODEL\n"
        "out = run_agent_step(system_prompt=system, user_prompt=user,\n"
        f"                    cwd={str(ROOT)!r}, timeout_s={timeout_s},\n"
        "                     model=model, submit_step='pbt_audit')\n"
        "print('PAYLOAD ' + json.dumps(getattr(out, 'payload', None), default=str))\n"
    )
    log = log_dir / f"{iid}.{backend}.audit.log"
    t0 = time.monotonic()
    with log.open("w") as fh:
        p = subprocess.run([_py(), "-c", script],
                           env=_env(benchmark, benchmark_dir,
                                    SBU_AGENT_TRACE=str(log_dir / "trace" / iid),
                                    SBU_LEAN_SLOTS=lean_slots),
                           cwd=str(ROOT), stdout=fh, stderr=subprocess.STDOUT,
                           timeout=None)
    payload: dict = {}
    # The payload is the LAST such line: an agent may print progress that
    # happens to start with the marker, and only the final submission counts.
    for line in log.read_text(errors="replace").splitlines():
        if line.startswith("PAYLOAD "):
            try:
                got = json.loads(line[len("PAYLOAD "):])
            except json.JSONDecodeError:
                continue
            if isinstance(got, dict):
                payload = got
    return {"rc": p.returncode, "wall_s": round(time.monotonic() - t0, 1),
            "payload": payload}


def regate(iid: str, backend: str, benchmark: str, benchmark_dir: str,
           log_dir: Path, timeout_s: int, workers: int, verify_timeout: int,
           lean_slots: int) -> bool:
    """Re-run G-PBT so the recorded status reflects any audit edit."""
    log = log_dir / f"{iid}.{backend}.regate.log"
    cmd = [_py(), str(ROOT / "scripts" / "pbt_gate.py"), iid,
           "--backend", backend]
    try:
        with log.open("w") as fh:
            subprocess.run(cmd, env=_env(benchmark, benchmark_dir,
                                         SBU_PBT_WORKERS=workers,
                                         SBU_PBT_VERIFY_TIMEOUT=verify_timeout,
                                         SBU_LEAN_SLOTS=lean_slots),
                           cwd=str(ROOT), stdout=fh, stderr=subprocess.STDOUT,
                           timeout=timeout_s)
    except subprocess.TimeoutExpired:
        return False
    return True


def _digest(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except FileNotFoundError:
        return ""


def audit_cell(iid: str, backend: str, args, log_dir: Path, stamp: str) -> dict:
    bundle = ROOT / args.benchmark_dir / iid / backend
    row = {"iid": iid, "backend": backend}
    # The SAME lock the port driver takes, and for a sharper reason: an auditor
    # is allowed to EDIT properties.py, so auditing a cell a port agent is
    # rewriting means two processes editing one file with no coordination. The
    # lock is shared across drivers because it lives with the bundle.
    try:
        with cell_lock(bundle):
            return _audit_cell_locked(iid, backend, args, log_dir, stamp,
                                      bundle, row)
    except CellBusy as e:
        row["status"] = "busy"
        row["detail"] = f"held by {e}; skipped"
        return row


def wanted(bundle: Path, resume: bool, resume_incomplete: bool) -> dict | None:
    """The record that makes this cell NOT worth auditing, or None to go ahead.

    The same predicate `main` filters the id list with, factored out so it can be
    re-applied under the lock. `main` filters at LAUNCH, and with two audit
    drivers running, a cell can be finished by the other one between the filter
    and this cell's turn: the flock stops them overlapping in TIME, not from
    doing the same cell in sequence, and a redundant second audit costs a full
    agent plus a re-gate. Under `--resume-incomplete` an incomplete record is
    still work to do, so it is not a reason to skip.
    """
    if not (resume or resume_incomplete):
        return None
    rec = audited(bundle)
    if rec is None:
        return None
    if resume_incomplete and not is_complete(rec):
        return None
    return rec


def _audit_cell_locked(iid: str, backend: str, args, log_dir: Path, stamp: str,
                       bundle: Path, row: dict) -> dict:
    if rec := wanted(bundle, args.resume, args.resume_incomplete):
        row["status"] = "already-audited"
        row["detail"] = (f"recorded {rec.get('agent_verdict') or '?'} at "
                         f"{rec.get('audited_at')} before this cell's turn")
        return row

    before = recorded_pbt(bundle)
    if before[0] != "pass":
        row["status"] = "not-auditable"
        row["detail"] = f"G-PBT={before[0] or 'unrecorded'} — port it first"
        return row

    props = bundle / "properties.py"
    # From the registry, not a literal: `_digest` of an absent file is "", so a
    # hardcoded name on a backend that spells its solution differently would
    # compare "" against "" and never detect a frozen-artifact edit at all.
    frozen_name = get_backend(backend).language.solution_filename
    before_props, before_frozen = _digest(props), _digest(bundle / frozen_name)

    a = run_audit(iid, backend, args.benchmark, args.benchmark_dir, log_dir,
                  args.audit_timeout, args.model, args.lean_slots)
    payload = normalize(a["payload"])
    row["audit_s"] = a["wall_s"]
    row["agent_verdict"] = str(payload.get("verdict", "")) or "no-verdict"

    # `edited` is MEASURED, not believed: agents describe their edits in prose as
    # often as they flag them, and a description is as often a denial as a
    # confirmation — a hash comparison settles it and costs nothing.
    payload["edited"] = _digest(props) != before_props
    # The one thing an auditor must never touch. Detected rather than trusted,
    # because a frozen-file edit would make every subsequent case verdict
    # meaningless: the battery would be judged against a solution that is no
    # longer the released one.
    if _digest(bundle / frozen_name) != before_frozen:
        payload["frozen_artifact_modified"] = True

    # Always re-gate, even when the hashes say nothing changed: the gate is what
    # attests to the cell, and re-running it is how the audit's own record gets
    # a status that is not the agent's word.
    ok = regate(iid, backend, args.benchmark, args.benchmark_dir, log_dir,
                args.gate_timeout, args.gate_workers, args.verify_timeout,
                args.lean_slots)
    after = recorded_pbt(bundle)
    row["gate_after"] = f"{after[0]}/{after[1]}"
    record_audit(bundle, payload, after, stamp)

    if payload.get("frozen_artifact_modified"):
        # Worse than a regression: the cell may still PASS, against a solution
        # that is no longer the frozen one. Reported first for that reason.
        row["status"] = "FROZEN-TOUCHED"
        row["detail"] = f"{frozen_name} was modified by the auditor"
    elif not ok:
        row["status"], row["detail"] = "regate-timeout", f"> {args.gate_timeout}s"
    elif after[0] != "pass":
        # The audit left the cell worse than it found it. Loud, because the cell
        # was passing before and is not now.
        row["status"] = "REGRESSED"
        row["detail"] = f"was pass/{before[1]}, now {after[0]}/{after[1]}"
    elif reports_a_spec_hole(payload):
        row["status"], row["detail"] = "spec-defect", "frozen spec hole reported"
    elif payload.get("spec_holes"):
        row["status"] = "audited"
        row["detail"] = f"{row['agent_verdict']} (spec_holes: prose denial)"
    elif not payload.get("verdict"):
        # Either nothing was submitted, or it was submitted under field names
        # `normalize` does not know. Both mean nothing attests to WHICH cases were
        # examined, so the cell is not audited however much work the agent did.
        # Keyed on the VERDICT rather than on `payload` being empty: a dict full
        # of unrecognized keys is not a record either, and reporting that as
        # `audited` with a `no-payload` detail is a self-contradicting row.
        row["status"], row["detail"] = "no-payload", "no verdict in submission"
    else:
        row["status"] = "audited"
        row["detail"] = row["agent_verdict"]
    return row


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", required=True, choices=["velvet", "lean"])
    ap.add_argument("--benchmark", default=os.environ.get("SBU_BENCHMARK",
                                                         "swe_bench_verified"))
    ap.add_argument("--benchmark-dir", default=default_benchmark_dir())
    ap.add_argument("--instances", nargs="*", default=None)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--jobs", type=int, default=8, help="concurrent AUDITORS")
    ap.add_argument("--gate-workers", type=int, default=8)
    ap.add_argument("--lean-slots", type=int, default=72,
                    help="HOST-WIDE concurrent lake builds (see pbt_port_fleet)")
    # Shared with the port fleet: the re-gate this driver runs is the same gate,
    # and a cap that condemns a battery here would contradict the one that
    # cleared it there.
    ap.add_argument("--verify-timeout", type=int, default=VERIFY_TIMEOUT_DEFAULT)
    ap.add_argument("--audit-timeout", type=int, default=AUDIT_TIMEOUT_DEFAULT)
    ap.add_argument("--gate-timeout", type=int, default=GATE_TIMEOUT_DEFAULT)
    ap.add_argument("--model", default=None)
    ap.add_argument("--resume", action="store_true",
                    help="skip cells that already carry a recorded audit")
    ap.add_argument("--resume-incomplete", action="store_true",
                    help="like --resume, but ALSO re-audit cells whose record "
                         "lacks per-case verdicts, witness exit codes, or "
                         "attacks (a record written before the payload spec "
                         "named those fields). The prior record is kept under "
                         "`history`.")
    ap.add_argument("--stamp", default="",
                    help="audited_at value; defaults to the wave tag")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--tag", default="audit")
    args = ap.parse_args()
    # See pbt_port_fleet.main: makes a `busy` row name the wave, not just a pid.
    os.environ["SBU_WAVE_TAG"] = f"{args.tag}/audit"

    root = ROOT / args.benchmark_dir
    if args.instances:
        ids = list(args.instances)
    else:
        # Auditable = the gate already recorded a pass. Cheapest-first is
        # pointless here (every cell is one agent plus one re-gate), so plain
        # id order keeps waves reproducible.
        ids = sorted(p.parent.parent.name
                     for p in root.glob(f"*/{args.backend}/properties.py")
                     if recorded_pbt(p.parent)[0] == "pass")
    # Same predicate the per-cell path re-applies under the lock, so a wave's
    # announced size and its skip decisions cannot disagree.
    ids = [i for i in ids
           if not wanted(root / i / args.backend, args.resume,
                         args.resume_incomplete)]
    if args.limit:
        ids = ids[:args.limit]

    log_dir = EXPERIMENTS_ROOT / "pbt_audit" / f"{args.tag}.{args.backend}"
    print(f"# {len(ids)} auditable cell(s) on {args.backend}, "
          f"jobs={args.jobs}, lean-slots={args.lean_slots}; logs -> {log_dir}",
          flush=True)
    if args.dry_run:
        for i in ids:
            print(i)
        return 0
    log_dir.mkdir(parents=True, exist_ok=True)
    stamp = args.stamp or args.tag

    rows, t0 = [], time.monotonic()
    with ThreadPoolExecutor(max_workers=args.jobs) as ex:
        futs = {ex.submit(audit_cell, i, args.backend, args, log_dir, stamp): i
                for i in ids}
        for fut in as_completed(futs):
            iid = futs[fut]
            try:
                row = fut.result()
            except Exception as e:   # one cell must never sink the wave
                row = {"iid": iid, "backend": args.backend, "status": "error",
                       "detail": f"{type(e).__name__}: {e}"}
            rows.append(row)
            print(f"[{len(rows)}/{len(ids)}] {row['status']:<14} {iid} "
                  f"{row.get('detail', '')}", flush=True)

    summary: dict[str, int] = {}
    for r in rows:
        summary[r["status"]] = summary.get(r["status"], 0) + 1
    out = log_dir / "wave.json"
    out.write_text(json.dumps(
        {"backend": args.backend, "wall_s": round(time.monotonic() - t0, 1),
         "summary": summary, "rows": sorted(rows, key=lambda r: r["iid"])},
        indent=2))
    print(f"# {summary} in {round((time.monotonic() - t0) / 60, 1)} min -> {out}")
    # A regression or a spec defect is the reason this lane exists; both are
    # non-zero so a wave script stops rather than rolling on.
    bad = sum(summary.get(k, 0) for k in
              ("REGRESSED", "regate-timeout", "error", "spec-defect"))
    if bad:
        return 1
    # See pbt_port_fleet.main: `busy` is not a verdict on the cell, so a wave
    # that only skipped held cells has work left and exits 3 for a retry.
    if summary.get("busy"):
        print(f"# {summary['busy']} cell(s) were held by another driver; "
              "exiting 3 so a supervisor retries them")
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
