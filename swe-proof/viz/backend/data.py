# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Read-only loaders for the dataset + per-instance bundle artifacts.

Unified split layout: instance-level inputs live at <bench>/<id>/ (instance.json
= the frozen dataset row, patch.diff = gold patch); the reviewed backend's
constructed bundle lives at <bench>/<id>/<backend>/. The instance.json files ARE
the dataset (no separate jsonl needed), so the board lists every instance dir —
including blocked / parked / never-built ones — with its construction status.

Every loader takes (bm, bk, ...): bm = the benchmark cell (verified | pro), bk =
the backend. Caches are keyed on both so the two boards never share entries.
"""
from __future__ import annotations

import functools
import json
import threading
import time
from collections.abc import Callable
from typing import Any, TypeVar

from swebench_unified.construct.audit_roles import recorded_agent_verdict
from swebench_unified.construct.release_prose import (
    publish_note, scrub_build_narration)
from swebench_unified.gates import AUDIT_GATES, DOCKER_GATES, STATIC_GATES
from swebench_unified.gates.panel import ROLES as _PANEL_ROLES
from swebench_unified.greenness import failing_gates as _failing_gates
from swebench_unified.greenness import is_green as _is_green

from . import paths, settings

# Construction rewrites meta.json/result.json while the site is serving, so
# derived state may only be cached briefly. instance.json is immutable by
# contract (G-INTEGRITY), so dataset_row stays lru-cached.
_TTL_S = 30.0
_ttl_store: dict[str, tuple[float, Any]] = {}
_ttl_lock = threading.Lock()
_ttl_refreshing: set[str] = set()

_T = TypeVar("_T")


def _ttl_cached(key: str, compute: Callable[[], _T]) -> _T:
    """A TTL cache that only ever makes the FIRST caller wait.

    An expiry recomputes in the background and serves the stale value meanwhile.
    Without that, one request in every TTL pays the whole cost: a page's header
    renders `green_counts` for every cell of the matrix, which is seconds of
    reading over a shipped corpus, so one visitor per TTL waited for all of it.
    Serving a value up to a TTL out of date is the right trade for a review site,
    because the underlying records change on the order of minutes.
    """
    now = time.monotonic()
    hit = _ttl_store.get(key)
    if hit is None:
        val = compute()
        _ttl_store[key] = (time.monotonic(), val)
        return val
    if now - hit[0] < _TTL_S:
        return hit[1]
    _refresh_soon(key, compute)
    return hit[1]


def _refresh_soon(key: str, compute) -> None:
    """Recompute `key` off the request path, one worker at a time.

    A failed recompute keeps the stale value and re-stamps it, so the retry is
    one TTL away rather than on the next request: the alternative spawns a thread
    per request for as long as the failure lasts.
    """
    with _ttl_lock:
        if key in _ttl_refreshing:
            return
        _ttl_refreshing.add(key)

    def run() -> None:
        try:
            val = compute()
        except Exception:                                        # noqa: BLE001
            val = _ttl_store.get(key, (0.0, None))[1]
        with _ttl_lock:
            _ttl_store[key] = (time.monotonic(), val)
            _ttl_refreshing.discard(key)

    threading.Thread(target=run, daemon=True, name=f"viz-ttl-{key}").start()


# ---- shape guards for the records on disk ---------------------------------
#
# Construction rewrites meta.json / result.json while the site is serving, and
# every reader below calls `.get`, `len` or `re` on what came back. A record that
# PARSES but is not the shape it should be (`null`, a list, a bare string) used to
# raise out of the loader, and because `summary_table` feeds `green_counts` --
# which `base.html` renders in the header of EVERY page -- one such cell answered
# HTTP 500 on every page of the site, including the other benchmark's board and
# /comments. A malformed record is missing information, so it reads as absent
# rather than as an outage. Unparsable JSON was already handled; only the
# parses-but-wrong-type case reached the caller.

def _obj(v) -> dict:
    """A record read as a mapping ({} when it is anything else)."""
    return v if isinstance(v, dict) else {}


def _seq(v) -> list:
    """A record read as a list, i.e. something len() may be taken of."""
    return v if isinstance(v, list) else []


def _text(v) -> str:
    """A recorded field published as prose. `release_prose.publish_note` runs
    `re.split` over it, so a note recorded as a number or a dict has to arrive as
    its own text rather than as a TypeError."""
    if isinstance(v, str):
        return v
    return "" if v is None else str(v)

# Badges are shown in the gates' canonical execution order (static, then the
# Docker gates, then the agentic pair), read off the gate registry rather than
# restated: a gate added there has to appear on the board, and GATE_DEFS below is
# then the only thing left to write (a test holds the two to the same key set).
GATE_ORDER = [*STATIC_GATES, *DOCKER_GATES, *AUDIT_GATES]
# the agentic panel roles recorded alongside the rollup, and what each judges
PANEL_ROLES = [f"G-PANEL-{i}" for i in sorted(_PANEL_ROLES)]
PANEL_ROLE_TITLES = {f"G-PANEL-{i}": _PANEL_ROLES[i] for i in sorted(_PANEL_ROLES)}

# one-line definition of each gate (shown on hover in the UI). What it CHECKS.
GATE_DEFS = {
    "G-VERIFY": "the committed model verifies (the reference impl satisfies its own spec).",
    "G-DIFF": "every prepatch twin shares the spec exactly yet FAILS verification "
              "(the bug is genuinely caught by the spec, not the proof).",
    "G-GOLD": "the gold-faithful impl verifies and the prepatches re-fail under it.",
    "G-MUT": "mutation kill: random impl mutants must fail verification (a spec-tightness "
             "floor, not a correctness proof; skipped when the impl is assignment-only).",
    "G-PBT": "property-based falsification: an adversarial battery (properties.py) of "
             "same-spec impl variants cannot show the spec too-weak / too-strong "
             "(judged by verifier accept/reject vs each case's expectation).",
    "G-INTEGRITY": "instance.json is byte-identical to the frozen dataset row; the bundle "
                   "is additions-only (the underlying task is never altered).",
    "G-HYGIENE": "static scan: markers/regions parse, spec-view idempotent, imports within "
                 "the allowlist, no Assume/Refute, region hashes recorded.",
    "G-LEAK": "the spec view (what a solver sees) leaks no localization the public problem "
              "statement doesn't already imply (relaxed = a documented PS↔gold mismatch).",
    "G-RESOLVE": "the equivalent real patch.diff resolves the instance in the official "
                 "harness (SWE-bench Docker; Pro = the pro grading oracle).",
    "G-CONF": "differential conformance: a shadow of the formal impl is fuzzed against the "
              "REAL patched function in-container (skip where not wired).",
    "G-AX": "axiom soundness: axiom_check.py fuzzes every axiom / deep-model reference "
            "against the REAL callee in-container (vacuous = no consumed axioms).",
    "G-EQ": "agentic refinement-fidelity attack: same-spec wrong impls are rejected and a "
            "structurally-different correct impl verifies (no SPEC-TOO-WEAK / TOO-STRONG).",
    "G-PANEL": "agentic blind panel rollup (roles 1-3: spec-tightness attack, faithfulness, "
               "leakage): the spec mirrors the real changed behaviour and reveals no more "
               "than the problem statement. Status = the worst of the three role verdicts; "
               "the roles carry the evidence, this key records none of its own.",
    "G-PANEL-1": "panel role 1: adversarial spec-tightness attack legs re-run.",
    "G-PANEL-2": "panel role 2: blind faithfulness: the spec mirrors the real change.",
    "G-PANEL-3": "panel role 3: leakage: the spec view reveals no gold localization.",
}

# What each gate is FOR, grouped the way the methodology is: which of the two
# directions of verify-implies-correct it defends, or which input to that
# argument it protects. This is the overview page's taxonomy, and it is a
# different statement from GATE_DEFS above (what a gate mechanically checks), so
# it is written once here rather than in the template. `test_home_page` holds it
# to GATE_ORDER, which makes a newly registered gate a classification decision
# instead of a silent omission from the front page.
GATE_FAMILIES = [
    ("Mechanical foundations",
     "Deterministic checks with no model in the loop. The reference "
     "implementation must verify, the pre-fix twin must fail under the same "
     "specification, mutants of the implementation must stop verifying, and the "
     "equivalent patch must resolve the instance in the official harness.",
     ["G-VERIFY", "G-DIFF", "G-GOLD", "G-MUT", "G-RESOLVE"]),
    ("Modelling boundary",
     "Axioms stand in for unchanged callees, so they are assumed rather than "
     "proved. Each one is fuzzed against the real callee inside the instance's "
     "own container, and the formal artifact is checked against the frozen task "
     "record and the verifier's admitted fragment.",
     ["G-AX", "G-CONF", "G-INTEGRITY", "G-HYGIENE"]),
    ("Adversarial specification audit",
     "Independent auditors are instructed to refute the instance: to exhibit a "
     "correct implementation the specification rejects, or an incorrect one it "
     "admits. A single reproduced counterexample reopens the instance.",
     ["G-EQ", "G-PANEL"]),
    ("Property-based falsification",
     "The adversarial attacks made re-runnable. Each instance ships a battery of "
     "rival implementations with machine-checkable expected outcomes, adjudicated "
     "by re-running the verifier under the frozen specification.",
     ["G-PBT"]),
    ("Evaluation integrity",
     "The specification view is what a solver is shown, so it must disclose no "
     "more of the fix than the public issue text already does.",
     ["G-LEAK"]),
]

# bundle files we surface, with a human label + language hint for highlighting.
# patch.diff lives at the INSTANCE level (split layout); the rest in <bk>/.
# The model's own filename is backend-specific -- `settings.model_file`.
def bundle_files(bk: str) -> list[tuple[str, str, str]]:
    lang = settings.model_lang(bk)
    return [
        (settings.model_file(bk), "Formal model (post-patch)", lang),
        (settings.prepatch_file(bk), "Formal model (pre-patch / buggy)", lang),
        ("refinement.md", "Refinement map (patch ↔ model)", "markdown"),
        ("mapping.md", "Symbol mapping / provenance", "markdown"),
        ("axiom_check.py", "In-container axiom check", "python"),
        ("conformance_check.py", "Differential conformance shadow (G-CONF)", "python"),
        ("properties.py", "Property-based falsification battery (G-PBT)", "python"),
        ("BLOCKED.md", "Blocked rationale (no bundle by design)", "markdown"),
        ("RELAXED_LEAKAGE.md", "Relaxed-leakage rationale", "markdown"),
        ("patch.diff", "Equivalent real patch (gold)", "diff"),
    ]


#: What a copyleft instance ships in place of its dataset row (README, "Copyleft
#: material"): the upstream instance it names, and none of its text.
POINTER = "upstream.json"


def all_instance_ids(bm: str) -> list[str]:
    """Every instance dir under the benchmark root (has instance.json, or the
    pointer that stands in for it)."""
    def _scan():
        root = paths.bench_root(bm)
        if not root.is_dir():
            return []
        return sorted(d.name for d in root.iterdir()
                      if d.is_dir() and ((d / "instance.json").is_file()
                                         or (d / POINTER).is_file()))
    return _ttl_cached(f"ids-{bm}", _scan)


@functools.lru_cache(maxsize=8192)
def dataset_row(bm: str, instance_id: str) -> dict | None:
    """The frozen dataset row = the instance-level instance.json.

    None means "no such instance": every route treats that as a 404, so a row
    that is not a JSON object is reported the same way as one that is missing or
    unreadable. Returning it raw would hand a list to `row.get(...)`.
    """
    try:
        p = paths.safe_under(paths.bench_root(bm), instance_id, "instance.json")
    except ValueError:
        return None
    if not p.is_file():
        return _pointer_row(p.with_name(POINTER))
    try:
        row = json.loads(p.read_text())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return row if isinstance(row, dict) else None


def _pointer_row(p: Path) -> dict | None:
    """The row a page can show for an instance whose dataset row is withheld: where
    it comes from, with every text field empty and the pointer under `upstream`."""
    try:
        ref = json.loads(p.read_text()) if p.is_file() else None
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(ref, dict):
        return None
    return {"instance_id": ref.get("instance_id", p.parent.name),
            "repo": ref.get("repo", ""), "base_commit": ref.get("base_commit", ""),
            "problem_statement": "", "hints_text": "", "patch": "", "test_patch": "",
            "upstream": ref}


def read_bundle_file(bm: str, bk: str, instance_id: str, name: str) -> str | None:
    """Read a bundle artifact: backend dir first, then the instance level
    (patch.diff / instance.json live beside the backend dirs)."""
    if bk not in settings.BACKENDS:
        return None
    root = paths.bench_root(bm)
    for parts in ((instance_id, bk, name), (instance_id, name)):
        try:
            p = paths.safe_under(root, *parts)
        except ValueError:
            return None
        try:
            if p.is_file():
                return p.read_text()
        except (OSError, UnicodeDecodeError):
            return None  # a build may be replacing the file mid-read
    return None


def list_prepatch(bm: str, bk: str, instance_id: str) -> list[str]:
    d = paths.bundle_dir(bm, bk, instance_id)
    if not d.is_dir():
        return []
    return sorted(p.name for p in d.glob(
        settings.prepatch_stem(bk) + "*" + settings.model_ext(bk)))


def meta(bm: str, bk: str, instance_id: str) -> dict:
    raw = read_bundle_file(bm, bk, instance_id, "meta.json")
    if not raw:
        return {}
    try:
        return _obj(json.loads(raw))
    except json.JSONDecodeError:
        return {}


def result(bm: str, bk: str, instance_id: str) -> dict:
    """Construction result.json (final_status: ok/blocked/timeout, phase times)."""
    raw = read_bundle_file(bm, bk, instance_id, "result.json")
    if not raw:
        return {}
    try:
        return _obj(json.loads(raw))
    except json.JSONDecodeError:
        return {}


def gates(bm: str, bk: str, instance_id: str) -> dict[str, dict]:
    return gates_from_meta(meta(bm, bk, instance_id))


def _rollup_note(out: dict[str, dict], roles: list[str]) -> str:
    """The one line the G-PANEL badge shows, derived from the role records.

    G-PANEL is a rollup, not a gate: `gates/panel.py:43` re-derives its `detail`
    on every gate run by joining the three roles' own notes, so every character
    of it is already published by the three per-role cards `audit_notes` renders.
    The badge tooltip prints `note` as plain text and never runs it through
    `md()`, so the concatenation reached readers as one unformatted blob of
    thousands of characters, all of it a third copy of the cards below.

    What this states instead is the rollup's own claim and nothing else: which
    roles it summarises, each one's recorded status and verdict token, and where
    the evidence is. `roles` is the roles that actually have a record, so a role
    the audit never stamped is named UNRECORDED rather than smoothed into a pass
    (`panel.py:46-48` records it the same way).
    """
    parts = []
    for k in PANEL_ROLES:
        r = out.get(k) or {}
        st = str(r.get("status") or "").strip()
        if k not in roles or not st:
            parts.append(f"{k} ({PANEL_ROLE_TITLES[k]}): UNRECORDED")
            continue
        av = str(r.get("agent_verdict") or "").strip()
        parts.append(f"{k} ({PANEL_ROLE_TITLES[k]}): {st}"
                     + (f" / {av}" if av else ""))
    lead = ("worst of the three panel roles. " if len(roles) == len(PANEL_ROLES)
            else "worst of the panel roles recorded. ")
    return (lead + "; ".join(parts)
            + ". Each role's full account is the card of the same name under "
              "'Audit verdicts' below; this row records no evidence of its own.")


def gates_from_meta(m: dict) -> dict[str, dict]:
    # `m` and its `gates` are read off disk, so both are guarded: this runs once
    # per instance of the benchmark on every board render.
    g = _obj(_obj(m).get("gates"))
    # normalize to dicts; surface the gate's detail/note under 'note' for hover
    out = {}
    for k, v in g.items():
        if not isinstance(v, dict):
            out[k] = {"status": str(v)}
            continue
        d = dict(v)
        d.setdefault("note", d.get("detail") or d.get("note") or "")
        out[k] = d
    # The rollup's hover text is derived, not republished -- see _rollup_note.
    # Only where a role record exists to point at: with none, the collective
    # G-PANEL entry (`panel.py:52-55`, the legacy shape) is the only thing
    # carrying that account, so it is published as recorded. Its STATUS is never
    # touched, here or anywhere -- `is_green`, `failing_gates`, `green_check.py`
    # and `triage.py` all read it, and the board shows what was recorded.
    if isinstance(g.get("G-PANEL"), dict):
        recorded = [r for r in PANEL_ROLES if out.get(r)]
        if recorded:
            out["G-PANEL"]["note"] = _rollup_note(out, recorded)
    return out


def failing_gates(g: dict[str, dict]) -> list[str]:
    """Gates with a genuine negative verdict, in the board's display order."""
    return _failing_gates(g, GATE_ORDER)


def is_green(g: dict[str, dict]) -> bool:
    """Fully green, per `swebench_unified.greenness` -- the same predicate the
    release gate picks commit batches with, so a badge cannot disagree with it."""
    return _is_green(g)


def prepatch_diffs(bm: str, bk: str, instance_id: str) -> list[dict]:
    """Unified diff prepatch twin -> the formal model, per prepatch variant.

    The spec regions are identical (same_spec), so the diff cleanly isolates the
    impl difference — i.e. exactly what the bug-fix changes. Returns
    [{name, lines:[{tag,old,new,text}]}] where tag is ctx/add/del, ready for the
    same diff renderer as the gold patch.
    """
    import difflib
    model = read_bundle_file(bm, bk, instance_id, settings.model_file(bk))
    if model is None:
        return []
    out = []
    for name in list_prepatch(bm, bk, instance_id):
        pre = read_bundle_file(bm, bk, instance_id, name)
        if pre is None:
            continue
        a, b = pre.splitlines(), model.splitlines()
        lines: list[dict] = []
        sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "equal":
                # collapse long unchanged runs to a little context around edits
                run = list(range(i1, i2))
                keep = set(run[:3]) | set(run[-3:]) if len(run) > 7 else set(run)
                gap = False
                for k, i in enumerate(run):
                    if i in keep:
                        lines.append({"tag": "ctx", "old": i + 1, "new": j1 + k + 1, "text": a[i]})
                        gap = False
                    elif not gap:
                        lines.append({"tag": "gap", "old": None, "new": None, "text": "⋯"})
                        gap = True
            else:
                for i in range(i1, i2):
                    lines.append({"tag": "del", "old": i + 1, "new": None, "text": a[i]})
                for j in range(j1, j2):
                    lines.append({"tag": "add", "old": None, "new": j + 1, "text": b[j]})
        # only emit if there is an actual impl difference
        if any(ln["tag"] in ("add", "del") for ln in lines):
            out.append({"name": name, "lines": lines})
    return out


def pbt_result(bm: str, bk: str, instance_id: str) -> dict | None:
    """The falsification battery's verdict and per-case outcomes, two lanes.

    The SPEC lane comes from the gate's own record in meta.json, not from the
    persisted file, because only the gate's copy is kept in sync: G-PBT rewrites
    `data.cases` every time it runs, while nothing rewrites `pbt_result.json`
    after a spec repair changes the manifest, so the two can disagree about which
    cases exist. Not every bundle ships the file at all, and preferring it left
    the card blank where the gate record was right there.

    The AXIOM lane still comes from the file, which is the only place it is
    recorded -- G-AX keeps just its exit status -- so dropping the file would
    lose it.
    """
    rec = gates(bm, bk, instance_id).get("G-PBT") or {}
    d: dict = _obj(rec.get("data"))
    persisted: dict = {}
    raw = read_bundle_file(bm, bk, instance_id, "pbt_result.json")
    if raw:
        try:
            persisted = _obj(json.loads(raw))
        except json.JSONDecodeError:
            persisted = {}
    # the template renders each lane as a table of case rows, so a lane recorded
    # as anything but a list of cases is an empty lane
    spec_cases = _seq(d.get("cases")) or _seq(persisted.get("spec_cases"))
    axiom_cases = _seq(persisted.get("axiom_cases"))
    if not spec_cases and not axiom_cases:
        return None
    status = str(rec.get("status") or "")
    return {
        "instance_id": instance_id,
        # The gate's verdict wins over the file's: they can disagree, and only
        # one of them was recomputed against the manifest that is there now.
        "verdict": (d.get("verdict") or persisted.get("verdict")
                    or ("SOUND" if status == "pass" else status.upper())),
        "spec_cases": spec_cases,
        "axiom_cases": axiom_cases,
        "note": persisted.get("note") or "",
    }


def verdict_md(bm: str, bk: str, instance_id: str) -> str | None:
    """The consolidated adversarial-audit PROSE (verdict.md), rendered as a
    dedicated card. verdict.md lives inside the backend bundle dir, so it is
    read as a bundle file."""
    return read_bundle_file(bm, bk, instance_id, "verdict.md")


def _absent_account(entry: dict) -> str:
    """What to publish for a role that recorded no account at all.

    A role that never judged has nothing to say, and the card should say THAT
    instead of rendering an empty section. Only for the statuses that MEAN it did
    not judge: an empty note on a pass or a fail is a defect in the record, and
    papering over it here would hide the one case worth seeing.
    """
    status = str(entry.get("status") or "").lower()
    if status not in ("skip", "n/a"):
        return ""
    reason = _text(entry.get("reason") or "")
    return (f"This role recorded `{status}`{f' ({reason})' if reason else ''} "
            f"rather than a judgment, so it has no audit account to publish.")


def audit_notes(bm: str, bk: str, instance_id: str) -> list[dict]:
    """Agentic audit verdicts recorded in meta.json (no standalone verdict file
    in the unified layout): G-EQ detail + each panel role's agent_verdict/note.

    Rendered through `release_prose.publish_note` and then
    `scrub_build_narration` -- both of them, in that order, which is the pair
    `verdict_prose_lint` holds `verdict.md` to. The recorded field is
    deliberately NOT sanitised on disk (the build reads it back, and its
    machine-side diagnostics are what tell an audit that failed for
    environmental reasons from one that found a real spec defect), so every
    publisher has to apply the rules itself. Both calls, not one:
    `publish_note` backticks the identifiers Markdown would otherwise eat
    (it is what stops `__init__` from publishing as a bold "init"), and the
    narration pass is what drops the scratch and mirror paths, which point at
    directories deleted once the audit finished.

    The advisory verdict comes from `audit_roles.recorded_agent_verdict` rather
    than from this gate's own entry, because it is recorded per reviewer RUN: read
    per gate, the G-EQ card published an empty verdict on every cell in the corpus.
    """
    g = gates(bm, bk, instance_id)
    out = []
    for k in ["G-EQ"] + PANEL_ROLES:
        v = g.get(k)
        if not v:
            continue
        note = _text(v.get("note") or v.get("detail") or "")
        out.append({"gate": k, "status": v.get("status", "—"),
                    "verdict": recorded_agent_verdict(g, k),
                    "note": (scrub_build_narration(publish_note(note)) if note
                             else _absent_account(v)),
                    "model": v.get("model", "")})
    return out


def bundle_present_files(bm: str, bk: str, instance_id: str) -> list[tuple[str, str, str]]:
    """The bundle files that actually exist for this instance (+ prepatch variants)."""
    out = []
    pp_file = settings.prepatch_file(bk)
    for name, label, lang in bundle_files(bk):
        if name == pp_file:
            for pp in list_prepatch(bm, bk, instance_id):
                lbl = label if pp == pp_file else f"Formal model (pre-patch: {pp})"
                out.append((pp, lbl, lang))
        elif read_bundle_file(bm, bk, instance_id, name) is not None:
            out.append((name, label, lang))
    return out


def green_counts(bm: str) -> dict[str, int]:
    """{backend: n_green} for one benchmark row — the header scoreboard."""
    return {bk: sum(1 for r in summary_table(bm, bk) if r["green"])
            for bk in settings.BACKENDS}


def instance_counts(bm: str) -> int:
    """How many instances the benchmark row holds (0 if its root is absent)."""
    return len(all_instance_ids(bm))


def bundle_counts(bm: str) -> dict[str, int]:
    """{backend: n_bundles_present} for one benchmark row.

    Not instances x backends: a lane may cover a subset of the row while a corpus
    is still being built, so multiplying would publish bundles that do not exist.
    "missing" is the status `_summary_row` gives a cell with neither a record nor
    a directory, which is exactly the absent case.
    """
    return {bk: sum(1 for r in summary_table(bm, bk) if r["status"] != "missing")
            for bk in settings.BACKENDS}


def summary_table(bm: str, bk: str) -> list[dict]:
    """One compact record per instance for the index page (TTL-cached; bundles
    can change while the site is serving)."""
    return _ttl_cached(f"summary-{bm}-{bk}", lambda: _summary_table(bm, bk))


def _summary_table(bm: str, bk: str) -> list[dict]:
    rows = []
    for iid in all_instance_ids(bm):
        try:
            rows.append(_summary_row(bm, bk, iid))
        except Exception:                                        # noqa: BLE001
            # A record this table cannot read costs its own row and nothing else.
            # The shape guards above cover what has actually been seen on disk;
            # this is the floor under them, because the blast radius of anything
            # they miss is the whole site: green_counts() reads this table for
            # every backend and `base.html` renders it in the header of EVERY
            # page, so one raising cell used to answer 500 on all of them.
            rows.append(_unreadable_row(iid))
    return rows


def _unreadable_row(iid: str) -> dict:
    """The index row for a cell whose record could not be read.

    Carries every key `index.html` reads, so the rest of the board renders; the
    status is its own word rather than one of the recorded ones, because "this
    record does not parse" is not a construction verdict and must not be counted
    as one (`green` is False, so it can never reach the green count).
    """
    return {"instance_id": iid, "repo": "", "final_status": "unreadable",
            "status": "unreadable", "failing_gates": [], "green": False,
            "gates": {k: "—" for k in GATE_ORDER}, "relaxed_leakage": False,
            "n_axioms": 0, "n_deepref": 0, "float_encoding": None, "n_modeled": 0}


def _summary_row(bm: str, bk: str, iid: str) -> dict:
    m = meta(bm, bk, iid)
    g = gates_from_meta(m)
    row = dataset_row(bm, iid) or {}
    res = result(bm, bk, iid)
    has_bundle = bool(m) or paths.bundle_dir(bm, bk, iid).is_dir()
    fs = res.get("final_status") or ("—" if has_bundle else "missing")
    green = is_green(g)
    bad = failing_gates(g)
    # display status: what a reviewer should act on
    if green:
        status = "green"
    elif bad:
        status = "failing"
    elif fs == "ok" or (fs == "—" and has_bundle):
        # constructed (or migrated without a result.json); verdicts
        # incomplete / in-flight — nothing recorded has failed
        status = "pending"
    else:
        status = fs             # blocked / timeout / missing
    return {
        "instance_id": iid,
        # the index sorts the repo column into a filter list, so a row whose
        # repo is not text has to arrive as text and not break the sort
        "repo": _text(row.get("repo")),
        "final_status": fs,
        "status": status,
        "failing_gates": bad,
        "green": green,
        "gates": {k: g.get(k, {}).get("status", "—") for k in GATE_ORDER},
        "relaxed_leakage": g.get("G-LEAK", {}).get("status") == "relaxed",
        "n_axioms": len(_seq(m.get("axioms"))),
        "n_deepref": len(_seq(m.get("deep_model_references"))),
        "float_encoding": m.get("float_encoding"),
        "n_modeled": len(_seq(m.get("modeled_functions"))),
    }
