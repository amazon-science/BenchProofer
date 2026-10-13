# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""P2: drive the reviewer agents over one bundle and record what they submitted.

Runs each audit role, re-derives its gate status from the submitted artifacts
(`audit_verdict`), writes the per-gate entries into meta.json and the evidence
into verdict.md (`verdict_record`), then lets the agentic gates read that record
back as their verdict. Off the construction path: a cell is audited long after it
is built, which is why none of this lives in `build_one`.
"""
from __future__ import annotations

import os
import shutil
import sys
import time
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path

from ..atomic_io import write_json_atomic
from ..gates import AUDIT_GATES, run_gates
from ..gates.base import Bundle, GateResult
from . import audit_note, judgment_note, leakage_note
from .audit_roles import (
    AUDIT_ROLE_TIMEOUT_DEFAULT, MIN_ATTACKS_DEFAULT, _AUDIT_AGENTS,
    _GATE_DERIVE_ROLE, _MECHANIZED, _ROLE_READS)
from .audit_verdict import _derive_audit_verdict
from .release_prose import sanitize_code, scrub_paths
from .verdict_record import (
    _keeps_prior_verdict, _section_inconclusive, merge_verdict_md)


def _elide(s: str, head: int = 260, tail: int = 420) -> str:
    """Shorten a diagnostic note, keeping BOTH ends: the classification is at the
    front, but the part that says WHY is at the back, where run_resolve appends
    the harness's own last words. A head-only truncation would drop them, and the
    run directory is purged per attempt, so they cannot be recovered after."""
    if len(s) <= head + tail + 5:
        return s
    return f"{s[:head]} […] {s[-tail:]}"


def _judgment_account(bundle, gate: str, note: str, agent_verdict: str) -> str:
    """The account a passing role with no outcome table publishes, or "".

    Leakage runs FIRST and only on the deferral sentence, which `leakage_note`
    matches as the whole note -- so a frame paragraph added first would stop it
    matching. The frame then composes OVER the quotation, carrying its own
    idempotence marker. `judgment_note`'s `record` is left empty on purpose: the
    record is rendered from these sections afterwards, so there is no text to read
    yet, and `_render_sections` discloses the same limitation for itself.
    """
    try:
        meta = bundle.meta()
    except Exception:
        return ""
    base = note
    if gate == leakage_note.GATE and leakage_note.is_deferral_sentence(note):
        doc = bundle.root / leakage_note.DOC
        try:
            text = doc.read_text() if doc.is_file() else None
        except (OSError, UnicodeDecodeError):
            # A file the composer cannot hash is a file it cannot claim was the
            # one G-LEAK digested, and that claim is the note's whole standing.
            text = None
        quoted, _why = (leakage_note.compose(note, text, meta=meta,
                                             agent_verdict=agent_verdict)
                        if text is not None
                        else leakage_note.compose_recorded(
                            note, meta=meta, agent_verdict=agent_verdict))
        base = quoted or note
    body, _why = judgment_note.compose(
        gate, base, agent_verdict=agent_verdict, gates=meta.get("gates") or {},
        shipped=sorted(p.name for p in bundle.root.iterdir() if p.is_file()))
    return body or (base if base != note else "")


def run_audit_stage(instance_id: str, backend_name: str,
                    timeout_s: int | None = None,
                    min_attacks: int = MIN_ATTACKS_DEFAULT,
                    roles: Iterable[str] | None = None) -> list[GateResult]:
    """P2: drive the audit agents per role. For the mechanized roles the recorded
    pass/fail is RE-DERIVED from the submitted attack artifacts, never from the
    agent's verdict string; the agentic gates then read the record back.

    Per-role wall-clock is SBU_AUDIT_TIMEOUT, else `AUDIT_ROLE_TIMEOUT_DEFAULT`,
    whose comment states why the cap must sit above one working role's work: an
    overrun yields an empty payload, and the stage fails closed on it.

    `roles` names a SUBSET of `_AUDIT_AGENTS` to re-derive and overrides
    SBU_AUDIT_ONLY. A parameter and not only an env var because a caller may run
    cells in a thread pool, where a per-cell `os.environ` write is read by
    whichever cell happens to be mid-dispatch."""
    from ..adversary import check_attack
    from ..agent import DEFAULT_MODEL
    from ..backends import get_backend
    from ..gates._audit import run_audit
    from ..harness import run_resolve

    if timeout_s is None:
        v = os.environ.get("SBU_AUDIT_TIMEOUT")
        timeout_s = int(v) if v and v.isdigit() else AUDIT_ROLE_TIMEOUT_DEFAULT

    bundle = Bundle(instance_id, get_backend(backend_name))
    meta = bundle.meta()
    gates_blob = meta.setdefault("gates", {})

    audit_retries = int(os.environ.get("SBU_AUDIT_RETRIES") or 2)
    # Seconds before re-running a role that reached no verdict: the usual cause is
    # a resource condition an IMMEDIATE re-launch cannot change, which spends the
    # attempt and records a shortage as an unauditable spec. Linear backoff per
    # attempt; 0 disables the wait.
    audit_retry_wait = int(os.environ.get("SBU_AUDIT_RETRY_WAIT") or 120)

    def _capture_attacks(payload: dict) -> dict:
        """Read the attack/positive-control SOURCE out of the scratch dir BEFORE
        it is deleted, so verdict.md can show what was re-run. Best-effort;
        `canon` is the realpath, the join key for the per-attack labels
        _derive_audit_verdict fills in."""

        def _read(p: str) -> dict | None:
            try:
                path = Path(p)
                return {"name": path.name, "src": path.read_text(),
                        "canon": os.path.realpath(p)}
            except (OSError, UnicodeDecodeError, TypeError):
                return None

        attacks = [r for r in (_read(a) for a in (payload.get("attacks") or [])
                               if isinstance(a, str)) if r]
        ctrl = _read(payload["positive_control"]) if payload.get("positive_control") else None
        return {"attacks": attacks, "positive_control": ctrl,
                "prepatch_reproduced": payload.get("prepatch_reproduced")}

    def _run_and_derive(agent_role: str, gate_keys: tuple):
        """One agent run -> list of PER-GATE section dicts, cleaning its scratch
        after the verdict derivation (which re-runs the agent's attack files)."""
        from ..agent import AgentAuthError
        # The scratch path, known independently of how `run_audit` exits: the
        # `finally` reads it out of the PAYLOAD, which both error paths replace or
        # never bind, so the tree would survive exactly when the run failed.
        scratch_ref: dict = {}
        try:
            payload = run_audit(bundle, agent_role, timeout_s=timeout_s,
                                scratch_out=scratch_ref)
        except AgentAuthError:
            shutil.rmtree(scratch_ref.get("_scratch") or "", ignore_errors=True)
            # The CLI never authenticated, so nobody looked and there is nothing to
            # record; INCONCLUSIVE here would turn an auth outage into a NOTGREEN
            # cell every re-audit re-confirms. Propagate: the caller aborts the
            # stage with the cell untouched.
            raise
        except Exception as e:  # timeout / agent CLI error -> empty payload
            # `_role_error` is an internal key (agent payloads never set it) read by
            # the derivation, so the recorded verdict says the audit did not run
            # rather than describing an agent that ran and submitted nothing. The
            # cap is wide because every field the CLI reports sits AFTER the SDK's
            # error-result prefix, and bounded because this lands in meta.json.
            err = f"{type(e).__name__}: {str(e)[:600]}"
            payload = {"verdict": "", "notes": f"audit role errored: {err}",
                       "_role_error": err,
                       # Carried forward so the `finally` can still find it: this
                       # dict REPLACES the one run_audit would have returned.
                       "_scratch": scratch_ref.get("_scratch")}
        try:
            # Capture attack source now (scratch is deleted in `finally`). Only
            # the mechanized roles (eq/panel_1) carry attacks.
            atk = _capture_attacks(payload)
            # `scrub_paths` and nothing more, HERE at the record: the auditor names
            # its attacks by the scratch directory the `finally` deletes, so the
            # path is dead as written and the basename it collapses to is how the
            # rest of the record already names that file. The remaining rules stay
            # at render time on purpose (see release_prose.scrub_paths) -- the
            # pipeline reads these fields back, and the resource-condition sentences
            # are what tell a role that could not run from a real finding.
            av = scrub_paths(str(payload.get("verdict", "")))
            notes = scrub_paths(str(payload.get("notes", "")))
            # The counterexample is a TRANSCRIPT, so it gets the fenced-block rule
            # instead: `scrub_paths` also closes up after the reference it removed,
            # and a rewritten gap in a verifier's output misreports what ran.
            cx = sanitize_code(str(payload.get("counterexample", "")))
            # One payload scores BOTH mechanized gates and each re-derives its own
            # labels, so unmemoized the same (instance, patch) pair goes through the
            # Docker harness twice and the two runs can disagree if one drops out.
            # Resolving is a pure function of (instance, patch), so caching it per
            # payload makes the derivations consistent by construction.
            resolve_cache: dict[tuple[str, str], object] = {}

            def _resolve_once(iid: str, patch_text: str):
                key = (iid, patch_text)
                if key not in resolve_cache:
                    resolve_cache[key] = run_resolve(iid, patch_text)
                return resolve_cache[key]

            def _provenance(gate_key: str, role: str, status: str) -> dict:
                """Same provenance a mechanical record carries (gates/base.stamp).

                This stage writes per-role entries straight into meta.json,
                bypassing `_record`, and `update`s them onto whatever sits under
                that key -- so without this an older record's `checked_at` stands
                in front of a status this run just replaced. `sources` only for
                statuses that are a verdict ABOUT the artifacts: `blocked`/`skip`
                mean nobody judged them, so a digest would attest to a review that
                did not happen."""
                from ..gates.base import source_digests, stamp
                r = stamp(GateResult(gate_key, status), "strict")
                prov: dict[str, object] = {"checked_at": r.checked_at,
                                           "code_version": r.code_version,
                                           "harness_digest": r.harness_digest}
                if status in ("pass", "fail"):
                    digests = source_digests(bundle, _ROLE_READS.get(role, ()))
                    if digests:
                        prov["sources"] = digests
                return prov

            secs = []
            for gk in gate_keys:
                derive_role = _GATE_DERIVE_ROLE[gk]
                ar: dict = {}  # per-attack outcome labels (canon path -> text)
                status, note = _derive_audit_verdict(
                    derive_role, bundle, payload, min_attacks=min_attacks,
                    check_attack=check_attack, run_resolve=_resolve_once,
                    attack_results=ar)
                # The derivation names attacks by the canonicalised path it re-ran
                # and a judgment role's note is agent prose, so both arrive carrying
                # the scratch directory. Same rule as above, and it must reach the
                # DERIVED note: `G-PANEL.data.roles.*` is a copy of this field.
                note = scrub_paths(note)
                sec = {"gate": gk, "agent_role": agent_role,
                       "entry": {"status": status, "model": DEFAULT_MODEL,
                                 "note": note, "agent_verdict": av,
                                 **_provenance(gk, derive_role, status)},
                       "status": status, "note": note, "agent_verdict": av,
                       "notes": notes, "counterexample": cx,
                       # The derivation's own answer, so neither the retry nor the
                       # evidence retention has to read it back out of a note that,
                       # for a judgment role, is agent prose.
                       "inconclusive": status == "fail" and note.lstrip().startswith(
                           f"{derive_role}: INCONCLUSIVE"),
                       "mechanized": derive_role in _MECHANIZED}
                if sec["mechanized"]:
                    # attach this gate's per-attack result to a COPY of the shared
                    # captured attacks (each gate derives its own labels).
                    sec.update(atk)
                    sec["attacks"] = [{**a, "result": ar.get(a.get("canon"), "")}
                                      for a in atk.get("attacks", [])]
                    if status == "pass":
                        # The derived sentence is a counter and the per-attack labels
                        # are in hand here, so the note carries the account, not only
                        # the count. `audit_note` declines on anything it cannot
                        # restate from a label, and preserves the first line byte for
                        # byte, so the defect router's view of the field is unchanged.
                        body, why = audit_note.compose(
                            note, sec["attacks"],
                            control=str((atk.get("positive_control")
                                         or {}).get("name") or ""),
                            prepatch=atk.get("prepatch_reproduced"))
                        if not body and why in judgment_note.UNGRADED_REASONS:
                            # A mechanized role can pass with no outcome to tabulate
                            # (attacks re-verified from retained evidence); the
                            # account then points at the evidence instead.
                            body = _judgment_account(bundle, gk, note, av)
                        if body:
                            note = scrub_paths(body)
                            sec["note"] = sec["entry"]["note"] = note
                elif status == "pass":
                    # A judgment role has no outcome table by construction: it
                    # publishes the reviewer's prose, and the frame states which
                    # question was asked and how far the record can be re-checked. A
                    # decline leaves the recorded note as it is.
                    body = _judgment_account(bundle, gk, note, av)
                    if body:
                        note = scrub_paths(body)
                        sec["note"] = sec["entry"]["note"] = note
                secs.append(sec)
            return secs
        finally:
            sc = payload.get("_scratch")
            if sc:
                shutil.rmtree(sc, ignore_errors=True)

    def _one_agent(agent_role: str, gate_keys: tuple) -> list[dict]:
        """Run ONE reviewer agent; RETRY (up to SBU_AUDIT_RETRIES) if every gate it
        informs comes back INCONCLUSIVE — the agent intermittently times out or
        fails to submit, which would false-block an otherwise-green bundle. A real
        pass/fail (attacks re-run, verdict submitted) is kept. Each retry WAITS
        first, for `audit_retry_wait` seconds and for the reason recorded there."""
        secs = _run_and_derive(agent_role, gate_keys)
        for attempt in range(1, audit_retries + 1):
            if not all(_section_inconclusive(s) for s in secs):
                break  # got a real verdict for at least one key — keep it
            if audit_retry_wait:
                # Print the REASON, not just the fact: an inconclusive role is
                # either a condition to wait out or a bug to fix, and
                # "inconclusive, retry 1/2" cannot tell those apart.
                why = _elide("; ".join(sorted({s["note"] for s in secs})))
                print(f"[{instance_id}/{backend_name}] {agent_role}: inconclusive, "
                      f"retry {attempt}/{audit_retries} in "
                      f"{audit_retry_wait * attempt}s :: {why}",
                      file=sys.stderr, flush=True)
                time.sleep(audit_retry_wait * attempt)
            secs = _run_and_derive(agent_role, gate_keys)
        return secs

    # The reviewer AGENTS run CONCURRENTLY — each run_audit is a blocking agent
    # subprocess, so threads give real parallelism and per-bundle wall clock is
    # ~max(agent), not sum. The spec-too-weak agent's payload scores both G-EQ and
    # G-PANEL-1 (no redundant extra agent); SBU_AUDIT_JOBS caps concurrency.
    #
    # SBU_AUDIT_ONLY restricts the run to named agent roles (comma-separated).
    # Scoping is not merely a saving: each role is a fresh adversary that authors
    # its own attacks, so re-auditing all of them to clear one red role puts the
    # passing ones back on the dice.
    #
    # Everything downstream is already per-gate and so tolerates a partial set:
    # the meta.json writeback touches only the gates in `sections`,
    # `merge_verdict_md` merges against the verdict.md already on disk, and the
    # closing `run_gates(AUDIT_GATES)` re-derives all four statuses from the
    # recorded entries, the ones this run did not touch included. It is a narrower
    # measurement, never a partial record.
    from concurrent.futures import ThreadPoolExecutor
    only = ({r.strip() for r in roles if r and r.strip()} if roles is not None
            else {r.strip() for r in (os.environ.get("SBU_AUDIT_ONLY") or "").split(",")
                  if r.strip()})
    unknown = only - set(_AUDIT_AGENTS)
    if unknown:
        # Fail loudly rather than silently auditing nothing: a typo'd role name
        # would run zero agents and leave every stale entry standing, which reads
        # downstream as "the audit ran and changed nothing".
        raise ValueError(f"SBU_AUDIT_ONLY names unknown role(s) {sorted(unknown)}; "
                         f"known: {sorted(_AUDIT_AGENTS)}")
    agents = {k: v for k, v in _AUDIT_AGENTS.items() if not only or k in only}
    jobs = int(os.environ.get("SBU_AUDIT_JOBS") or len(agents))
    if only:
        print(f"[{instance_id}/{backend_name}] audit scoped to "
              f"{sorted(agents)} ({', '.join(g for v in agents.values() for g in v)})",
              file=sys.stderr, flush=True)
    sections = []
    with ThreadPoolExecutor(max_workers=max(1, jobs)) as ex:
        for secs in ex.map(lambda kv: _one_agent(*kv), agents.items()):
            for sec in secs:
                sections.append(sec)
                gates_blob.setdefault(sec["gate"], {}).update(sec["entry"])
    # Write the audit entries onto a FRESH read, not onto the copy loaded before the
    # agents ran: that copy is hours old, and writing it whole would revert every
    # unrelated edit made in the meantime, a spec repair landed mid-run included.
    # This function owns exactly the audit gate entries.
    fresh = bundle.meta()
    fresh_gates = fresh.setdefault("gates", {})
    for sec in sections:
        entry = fresh_gates.setdefault(sec["gate"], {})
        if _keeps_prior_verdict(bundle, sec, entry):
            # The attempt is recorded, the verdict is not touched. One scalar rather
            # than a growing list: a reader needs "the last re-audit of this passing
            # gate did not run, and why"; the run logs carry the full history.
            entry["last_inconclusive_attempt"] = {
                "at": sec["entry"].get("checked_at"),
                "note": sec["note"][:400],
            }
            print(f"[{instance_id}/{backend_name}] {sec['gate']}: attempt reached "
                  f"no verdict; keeping the pass derived on these same bytes "
                  f":: {_elide(sec['note'])}", file=sys.stderr, flush=True)
            continue
        # A conclusive verdict supersedes the outage note as well as the status.
        entry.pop("last_inconclusive_attempt", None)
        entry.update(sec["entry"])
    write_json_atomic(bundle.meta_path, fresh, sort_keys=True)
    # Persist the per-role audit prose + attacks as an inspectable verdict.md
    # (all backends), ordered G-EQ, G-PANEL-1, G-PANEL-2, G-PANEL-3.
    gate_order = ["G-EQ", "G-PANEL-1", "G-PANEL-2", "G-PANEL-3"]
    sections.sort(key=lambda s: gate_order.index(s["gate"])
                  if s["gate"] in gate_order else len(gate_order))
    vpath = bundle.root / "verdict.md"
    prior = vpath.read_text() if vpath.exists() else None
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    # The spec file every attack is a variant of, so each one can be published
    # as its own diff instead of as another copy of this.
    spec_path = bundle.root / bundle.backend.language.solution_filename
    baseline = spec_path.read_text() if spec_path.is_file() else None
    vpath.write_text(merge_verdict_md(instance_id, backend_name, sections,
                                      prior, stamp, baseline))
    return run_gates(instance_id, backend_name, list(AUDIT_GATES),
                     mode="strict", record=True)
