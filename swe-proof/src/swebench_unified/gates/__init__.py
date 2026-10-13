# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Gate registry + runner (docs/architecture.md §4). A gate that does not apply
to a backend records an explicit skip, never a silent absence, so a consumer can
tell "this was checked and does not apply" from "this was never checked".
run_gates persists stamped verdicts into meta.json gates.<NAME>."""
from __future__ import annotations

import functools
import json
import sys
from typing import Sequence

from ..atomic_io import write_json_atomic
from ..backends import get_backend
from .base import Bundle, GateResult, guarded, source_digests, stamp

# Import order = canonical execution order (static first, Docker last).
from . import verify as g_verify        # noqa: E402
from . import diff as g_diff            # noqa: E402
from . import gold as g_gold            # noqa: E402
from . import mut as g_mut              # noqa: E402
from . import pbt as g_pbt              # noqa: E402
from . import integrity as g_integrity  # noqa: E402
from . import hygiene as g_hygiene      # noqa: E402
from . import leak as g_leak            # noqa: E402
from . import resolve as g_resolve      # noqa: E402
from . import conf as g_conf            # noqa: E402
from . import ax as g_ax                # noqa: E402
from . import eq as g_eq                # noqa: E402
from . import panel as g_panel          # noqa: E402

_MODULES = (g_verify, g_diff, g_gold, g_mut, g_pbt, g_integrity, g_hygiene,
            g_leak, g_resolve, g_conf, g_ax, g_eq, g_panel)

GATES = {m.name: m for m in _MODULES}

ALL_GATES = tuple(m.name for m in _MODULES if not m.agentic)
STATIC_GATES = tuple(m.name for m in _MODULES if not m.needs_docker and not m.agentic)
DOCKER_GATES = tuple(m.name for m in _MODULES if m.needs_docker and not m.agentic)
AUDIT_GATES = tuple(m.name for m in _MODULES if m.agentic)
# Feedback subset for P1 construct refine rounds.
CONSTRUCT_GATES = ("G-INTEGRITY", "G-HYGIENE", "G-LEAK")


@functools.lru_cache(maxsize=1)
def _dataset_ids() -> frozenset[str]:
    """Instance ids present in the active benchmark's frozen dataset."""
    from ..paths import DATASET_JSONL
    ids = set()
    try:
        with DATASET_JSONL.open() as fh:
            for line in fh:
                try:
                    iid = json.loads(line).get("instance_id")
                except json.JSONDecodeError:
                    continue
                if iid:
                    ids.add(iid)
    except OSError:
        return frozenset()
    return frozenset(ids)


def run_gates(instance_id: str, backend_name: str,
              gates: Sequence[str] | None = None, *,
              mode: str = "strict", record: bool = True) -> list[GateResult]:
    """Run the named gates (default: all mechanical). mode="feedback" =
    construct-phase leniency, recorded in results."""
    backend = get_backend(backend_name)
    bundle = Bundle(instance_id, backend)
    # Recording MKDIRS the bundle root, so a caller that passes a non-instance as
    # an instance id silently MATERIALIZES a bundle for it -- a misparsed option
    # becomes a corpus directory holding a half-stamped meta.json, which a
    # worklist then reports as a cell needing repair. Refuse to create a bundle
    # for an id the frozen dataset does not have. Scoped to creation, so re-gating
    # an EXISTING bundle (fixtures, a corpus built from a different frozen list) is
    # untouched, and empty when the dataset is unreadable so a missing dataset
    # cannot block gating.
    known = _dataset_ids()
    if record and known and instance_id not in known and not bundle.root.exists():
        raise ValueError(
            f"refusing to create a bundle for {instance_id!r}: not in the "
            f"frozen dataset (check the caller's argument parsing)")
    # Accept both `--gates` spellings, the comma-separated string and the argparse
    # `nargs` list: the mismatch would otherwise stamp meta.json under a composite
    # key like 'G-VERIFY,G-DIFF,...' that no gate answers to, which green_check
    # reads as a real error.
    names = list(gates) if gates else list(ALL_GATES)
    names = [part.strip() for raw in names for part in str(raw).split(",")
             if part.strip()]
    results: list[GateResult] = []
    for name in names:
        module = GATES.get(name)
        if module is None:
            # Refuse rather than stamp. A recorded verdict for a nonexistent gate
            # outlives the run that made it and is indistinguishable from a real
            # failure; the same argument the dataset check above makes. With
            # record=False nothing is persisted, so a read-only probe may still
            # report it and callers that enumerate gate names keep working.
            if record:
                raise ValueError(
                    f"unknown gate {name!r} (check the caller's argument "
                    f"parsing; --gates takes either space- or comma-separated "
                    f"names)")
            results.append(GateResult(name, "error", "unknown gate"))
            continue
        if backend.name not in module.applies_to:
            results.append(stamp(GateResult(
                name, "skip", f"not applicable to backend {backend.name}"), mode))
            continue
        r = guarded(name, lambda m=module: m.run(bundle, mode=mode))
        results.append(stamp(r, mode))
    if record:
        _record(bundle, results)
    return results


def _is_echo(r: GateResult) -> bool:
    """Whether this result was READ out of meta.json rather than reached here.

    An agentic gate cannot run its attackers during a gate sweep -- that is
    construct-mode work -- so `_audit.recorded_verdict` returns the verdict a
    prior audit recorded, and `panel.run` rolls up three such records. Either way
    the sweep judged nothing, which is why `data.recorded` exists and why a
    rollup over `roles` counts the same: what makes a result an echo is that its
    evidence is older than this process, not which function produced it.
    """
    d = r.data if isinstance(r.data, dict) else {}
    return bool(d.get("recorded") or d.get("roles"))


def _keep_echoed_provenance(blob: dict, gates_blob: dict, gate: str,
                            prior: dict) -> None:
    """Give an echo the provenance of the evidence it echoed, not of this run.

    `stamp` has just set `checked_at` to now, and the branch above would digest
    the files as they are now. Written onto an echo, that pair says "this verdict
    is about these bytes, as of now" about a verdict some earlier audit reached
    against whatever the spec was then. So an echo must carry the provenance of
    the evidence it echoed: otherwise re-running G-EQ after editing a solution
    launders a stale audit into a stamp every freshness check reads as current --
    the one direction that lets `verify => correct` fail on a green cell.

    An echo therefore reports its own moment as `rederived_at` -- the sweep did
    happen, and hiding that would make a re-run look like it never ran -- and
    takes `checked_at`/`code_version`/`harness_digest`/`sources` from the record
    it read. A missing field is left MISSING rather than filled in from this run:
    an audit that recorded no digests is a record that cannot be checked by
    content, and saying so is the honest answer.

    For a rollup the evidence is the ROLE records, and a rollup is exactly as old
    as the oldest of them; `prior` (the rollup's own previous stamp) is used only
    when no role carries a stamp of its own. Both choices are the conservative
    direction: an echo's provenance can only get older, never fresher.
    """
    roles = [v for k, v in gates_blob.items()
             if isinstance(v, dict) and k.startswith(f"{gate}-")
             and str(v.get("checked_at") or "").strip()]
    src = min(roles, key=lambda v: str(v.get("checked_at"))) if roles else prior
    if blob.get("checked_at"):
        blob["rederived_at"] = blob["checked_at"]
    for k in ("checked_at", "code_version", "harness_digest", "sources"):
        if src.get(k):
            blob[k] = src[k]
        else:
            blob.pop(k, None)


def _record(bundle: Bundle, results: list[GateResult]) -> None:
    meta_path = bundle.root / "meta.json"
    meta = bundle.meta()
    gates_blob = meta.setdefault("gates", {})
    for r in results:
        prior = gates_blob.get(r.gate, {})
        # A harness error (an exception out of the gate body, caught by
        # `guarded`) means the gate reached NO verdict, so it must not replace
        # one. The caller still sees status="error" and still treats the cell as
        # unfinished; what it does not do is write that over a good record.
        if getattr(r, "harness_error", False) and prior.get("status"):
            print(f"[{bundle.instance_id}/{bundle.backend.name}] {r.gate}: "
                  f"harness error, keeping recorded {prior['status']} "
                  f":: {r.detail}", file=sys.stderr)
            continue
        blob = r.to_json()
        # Bind the record to the artifact it judged, not just to the code that
        # judged it (harness_digest) and the time it ran (checked_at). Only for a
        # real verdict: a skip or a harness error digested nothing. See
        # base.source_digests for why timestamps cannot serve here.
        module = GATES.get(r.gate)
        reads = getattr(module, "reads", ()) if module is not None else ()
        if _is_echo(r):
            _keep_echoed_provenance(blob, gates_blob, r.gate, prior)
        elif reads and r.status in ("pass", "fail", "relaxed"):
            digests = source_digests(bundle, reads)
            if digests:
                blob["sources"] = digests
        # Preserve operator knobs + record_audit fields across re-runs:
        # agentic gates read them back as their verdict (the P2 audit record).
        for k in ("timeout_seconds", "note", "model", "audited_by", "audit_verdict"):
            if k in prior:
                blob[k] = prior[k]
        gates_blob[r.gate] = blob
    meta.setdefault("schema_version", 1)
    bundle.root.mkdir(parents=True, exist_ok=True)
    # Atomically: gate processes run concurrently and every consumer (the green
    # classifier, the viz, the next gate run) reads this file directly, so a reader
    # must never observe a half-written one. See atomic_io.
    write_json_atomic(meta_path, meta, sort_keys=True)
