#!/usr/bin/env python
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Repair the specs an adversarial audit proved defective, then re-judge each
cell mechanically. `--mode` selects the defect class.

`--mode repair`: the spec is TOO WEAK. Its audit found an attack that VERIFIES
against the spec but whose faithful patch does NOT resolve, which is a
counterexample to the `verify => correct` property the benchmark exists to
enforce. The agent adds the postcondition the real patched function satisfies and
the attack does not.

`--mode panel`: the spec is UNFAITHFUL or LEAKS. Every mechanical gate passes and
every attack fails, so nothing mechanical is wrong. A judgment role found either
that the spec predicts something the real repository callee does not do (making a
faithful implementation fail it and a verifying one wrong), or that the spec view
discloses the fix's discriminating behaviour. The agent realigns the model to the
real callee, or restates the obligation without the disclosure.

`--mode mech`: a MECHANICAL gate refuted the artifact, with no judgment involved.
The gate ran the artifact against the real repository code and recorded a concrete
disagreement, so re-running it only re-derives the same failure and the artifact
itself has to be realigned. The agent is told which gate and given its report, and
is forbidden from editing the oracle: narrowing the shadow's generator or deleting
the failing assertion makes the stamp green and meaningless.

The agent's self-report is NEVER the verdict. Two things decide: every static and
docker gate, re-run; and a FRESH adversarial audit whose attacks are authored
against the NEW spec by an agent that did not write the repair. The fresh audit is
not optional, because re-running the old one would only ask whether the spec
resists the attacks it was just edited against, which it will by construction.

A repair that makes the gates green without making the spec stronger is the one
outcome that must never ship, so the driver also asserts the invariants a green
stamp cannot see: the agent must not have narrowed a precondition (nor, in panel
mode, deleted the postcondition or left the witness diverging), and the prepatch
twin must still FAIL the new spec, or the spec no longer captures the bug it
exists to encode.

Usage:
  SBU_BENCHMARK=swe_bench_verified SBU_BENCHMARK_DIR=benchmark-verified \
    python scripts/spec_repair_fleet.py --lane-file lane.tsv \
      --mode repair --jobs 8 [--resume] [--no-reaudit] [--dry-run]

The lane file is `<instance_id>\t<backend>` per line, which is what the
`green_check` classification emits. Every timeout below has an `SBU_REPAIR_*`
environment default; see `main`.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from green_check import classify  # noqa: E402
from pbt_port_fleet import (CellBusy, _env, _py, cell_lock,  # noqa: E402
                            run_capped)
from swebench_unified import benchmarks, triage  # noqa: E402
from swebench_unified.corpus_root import default_benchmark_dir  # noqa: E402
from swebench_unified.paths import EXPERIMENTS_ROOT  # noqa: E402

# Wall-clock budgets in seconds, all overridable. The agent reads the audit record,
# the real repository function at base_commit and the gold patch, edits the spec
# across every twin, then iterates against the verifier and the static gates.
AGENT_TIMEOUT_DEFAULT = int(os.environ.get("SBU_REPAIR_AGENT_TIMEOUT") or 9000)
GATE_TIMEOUT_DEFAULT = int(os.environ.get("SBU_REPAIR_GATE_TIMEOUT") or 3600)
ROLE_TIMEOUT_DEFAULT = int(os.environ.get("SBU_REPAIR_ROLE_TIMEOUT") or 5400)
ATTACK_TIMEOUT_DEFAULT = int(os.environ.get("SBU_REPAIR_ATTACK_TIMEOUT") or 1200)
JOBS_DEFAULT = int(os.environ.get("SBU_REPAIR_JOBS") or 8)

# The re-audit runs its reviewer agents concurrently, so its agent phase costs about
# one role rather than their sum. This outer cap has to cover one full per-role
# budget PLUS the derivation that follows, which is serial and is the part that
# grows: every submitted attack goes through the verifier, and each one that verifies
# also goes through the resolve oracle. When the outer cap binds, the whole re-audit
# is discarded with no verdict recorded -- worse than one role overrunning, which at
# least leaves the other roles' findings.
REAUDIT_TIMEOUT_DEFAULT = int(
    os.environ.get("SBU_REPAIR_REAUDIT_TIMEOUT") or 14400)

# How much of the outer cap to reserve for that post-agent derivation, i.e. the
# part that is not a role's agent budget.
REAUDIT_DERIVATION_RESERVE = int(
    os.environ.get("SBU_REPAIR_DERIVATION_RESERVE") or 3600)
# Ceiling on derived per-role attempts, whatever the outer budget allows. Retrying
# a role only helps against a transient host condition, and the attempts are
# serial under a held cell lock.
REAUDIT_MAX_ATTEMPTS = int(os.environ.get("SBU_REPAIR_MAX_ATTEMPTS") or 4)

SPEC_FILES = {
    "nagini": ["model.py", "model_prepatch.py", "properties.py"],
    "velvet": ["Solution.lean", "Solution_prepatch.lean", "properties.py"],
    "lean": ["Solution.lean", "Solution_prepatch.lean", "properties.py"],
}

STATIC_GATES = ("G-VERIFY", "G-DIFF", "G-GOLD", "G-MUT", "G-PBT",
                "G-INTEGRITY", "G-HYGIENE", "G-LEAK")
AUDIT_GATES = ("G-EQ", "G-PANEL-1", "G-PANEL-2", "G-PANEL-3")
OK = ("pass", "skip", "relaxed")

# Attempt history, kept outside the bundle: a stray file inside one fails
# G-INTEGRITY, and this is driver bookkeeping rather than a published artifact.
ATTEMPTS_DIR = EXPERIMENTS_ROOT / "fleet" / "attempts"

# How many prior attempts to put in front of the agent. The useful signal is what
# the last few tries did and how each was refuted; older ones repeat.
ATTEMPT_RECALL = int(os.environ.get("SBU_REPAIR_ATTEMPT_RECALL") or 4)


def gate_status(bundle: Path, keys) -> dict:
    try:
        g = json.loads((bundle / "meta.json").read_text()).get("gates", {})
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return {k: (g.get(k) or {}).get("status") for k in keys}


def is_green(bundle: Path) -> tuple[bool, str]:
    """The release classifier's verdict, not a local re-derivation.

    `green_check.classify` is the one authority for "green", and it enforces things a
    plain status sweep does not: some gate skips are not green, and every gate must be
    RECORDED, so a missing stamp fails. A driver that re-derived greenness from
    `status in OK` would disagree with the release gate on exactly the cells this lane
    is repairing, and report `repaired` on a cell the census counts as not green.
    """
    verdict, why = classify(bundle, bundle.name, bundle.parent.name)
    return verdict == "GREEN", why


def battery_load_error(iid: str, backend: str, args) -> str:
    """Why this cell's G-PBT battery does not import, or "" if it does.

    `properties.py` asserts its frozen anchors against the spec text at import, so a
    spec edit that misses one makes `load_manifest` raise and G-PBT record `error`.
    Read as "reached no verdict" that becomes an untestable loop: the next agent is
    told its route is untested rather than broken, repairs the spec again, misses the
    anchors again, and the re-audit never runs. So an import error gets its own
    status, and the exception text, which names the anchor that drifted, goes in
    front of the next attempt.

    Calls the SAME function the gate calls, in a child with the gates' own
    environment, so the driver and the gate cannot disagree about what it reports.
    """
    script = (
        "import sys\n"
        f"sys.path.insert(0, {str(ROOT / 'src')!r})\n"
        "from swebench_unified.backends import get_backend\n"
        "from swebench_unified.gates.base import Bundle\n"
        "from swebench_unified.gates.pbt import load_manifest\n"
        f"b = Bundle(instance_id={iid!r}, backend=get_backend({backend!r}))\n"
        "try:\n"
        "    cases = load_manifest(b)\n"
        "except Exception as exc:\n"
        "    msg = ' '.join(f'{type(exc).__name__}: {exc}'.split())\n"
        "    print('LOAD-ERROR ' + msg[:300])\n"
        "else:\n"
        "    print('LOAD-ERROR properties.py absent' if cases is None else 'LOAD-OK')\n"
    )
    try:
        p = subprocess.run([_py(), "-c", script],
                           env=_env(args.benchmark, args.benchmark_dir),
                           cwd=str(ROOT), capture_output=True, text=True,
                           timeout=600)
    except (subprocess.SubprocessError, OSError):
        return ""
    for line in (p.stdout or "").splitlines():
        if line.startswith("LOAD-ERROR "):
            return line[len("LOAD-ERROR "):].strip()
    return ""


# A mech repair may legitimately land entirely outside the spec region: when the
# fault is in the type bridge, the fix is in the check script and the spec was
# right all along. Counting those files as evidence-of-edit keeps the "claimed
# REPAIRED but nothing changed" check honest without rejecting a real bridge fix.
ORACLE_FILES = ("conformance_check.py", "axiom_check.py")


def spec_sha(bundle: Path, backend: str, extra: tuple[str, ...] = ()) -> str:
    """Hash of the bundle's spec-bearing files, to prove the agent edited them."""
    h = hashlib.sha1()
    for name in list(SPEC_FILES.get(backend, [])) + list(extra):
        p = bundle / name
        h.update(p.read_bytes() if p.is_file() else b"")
    return h.hexdigest()[:12]


def failing_roles(bundle: Path) -> str:
    """The judgment roles this cell fails, for the panel prompt.

    The agent has to be told WHICH defect to repair: faithfulness and leakage need
    opposite edits, and a cell failing both needs one repair that satisfies both.
    """
    st = gate_status(bundle, ("G-PANEL-2", "G-PANEL-3"))
    bad = [k for k, v in st.items() if v is not None and v not in OK]
    return ", ".join(bad) or "G-PANEL-2"


def failing_mech_gate(bundle: Path) -> str:
    """The mechanical gate whose report is the evidence for a mech repair.

    Reported in canonical gate order, and only a `fail` counts. An `error` or a
    missing stamp is a gate that reached no verdict, so it names no disagreement
    for the agent to close and belongs in a re-gate lane instead.
    """
    order = STATIC_GATES + ("G-RESOLVE", "G-CONF", "G-AX")
    st = gate_status(bundle, order)
    for k in order:
        if st.get(k) == "fail":
            return k
    return "G-CONF"


def _attempts_path(iid: str, backend: str) -> Path:
    return ATTEMPTS_DIR / f"{iid}.{backend}.jsonl"


def record_attempt(iid: str, backend: str, mode: str, row: dict) -> None:
    """Append this attempt's outcome to the cell's history.

    The supervisor re-derives its lanes from the corpus every cycle, so a cell that
    is still not green comes back around. Without a history each retry starts from
    the same audit record and reaches the same dead end, because how the last
    attempt was refuted is invisible to the next agent. One line per attempt breaks
    that loop, and it is written even for a crash so a wedged cell stays legible.

    `at` is what makes the history readable against the gates: without it there is no
    way to tell a route refuted against the CURRENT spec from one refuted against
    bytes that later repairs replaced, and the second is not evidence an agent can
    act on. Same key and format as the gate entries' `checked_at`.
    """
    try:
        ATTEMPTS_DIR.mkdir(parents=True, exist_ok=True)
        with _attempts_path(iid, backend).open("a") as fh:
            fh.write(json.dumps({
                "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "mode": mode,
                "status": row.get("status"),
                "verdict": row.get("verdict"),
                "detail": (row.get("detail") or "")[:400],
                "agent_s": row.get("agent_s"),
            }) + "\n")
    except OSError:
        pass          # bookkeeping must never fail a repair


def _measured_something(rec: dict) -> bool:
    """Whether this history line is evidence about a REPAIR ROUTE.

    A line written for an attempt whose agent never ran describes the host, not the
    cell, and in front of the next agent it reads as a refuted route: worse than no
    history at all, because the one approach never tried is the one it will now
    avoid. `misrouted` is the same case, a fact about the fleet's routing rather than
    about this spec. Such attempts are labelled `launch-failed` and not recorded; the
    remaining test filters lines written before that label existed, identified by no
    verdict, an outcome that is the pre-existing stamp read back, and an agent that
    returned faster than reading the prompt would take.
    """
    if rec.get("status") in ("launch-failed", "misrouted"):
        return False
    secs = rec.get("agent_s")
    return not (rec.get("status") in ("audit-fail", "gates-fail")
                and not str(rec.get("verdict") or "").strip()
                and isinstance(secs, (int, float)) and secs < 60)


def prior_attempts(iid: str, backend: str) -> list[dict]:
    p = _attempts_path(iid, backend)
    if not p.is_file():
        return []
    out = []
    for ln in p.read_text().splitlines():
        try:
            rec = json.loads(ln)
        except ValueError:
            continue
        if _measured_something(rec):
            out.append(rec)
    return out


DIRECTIVES_DIR = EXPERIMENTS_ROOT / "fleet" / "directives"


def _gate_freshness(bundle: Path) -> dict[str, bool | None]:
    """For each FAILING gate: do its recorded `sources` hashes still match?

    True means the verdict was earned against the exact bytes now on disk, False
    that it judges content since overwritten, and None that it was stamped before
    the field existed and is unknowable here.

    Raises nothing the callers have to handle: an unreadable bundle comes back
    empty, which every caller treats as "no basis to act", never as "stale".
    """
    try:
        gates = json.loads((bundle / "meta.json").read_text()).get("gates", {})
    except (OSError, ValueError):
        return {}
    out: dict[str, bool | None] = {}
    for gate, entry in sorted(gates.items()):
        if gate == "G-PANEL" or not isinstance(entry, dict):
            continue               # the aggregate only restates its own roles
        if str(entry.get("status", "")).lower() not in ("fail", "error"):
            continue
        src = entry.get("sources")
        if not isinstance(src, dict) or not src:
            out[gate] = None
            continue
        try:
            out[gate] = all(
                (bundle / f).is_file()
                and hashlib.sha256((bundle / f).read_bytes()).hexdigest() == h
                for f, h in src.items())
        except OSError:
            out[gate] = None
    return out


def _fresh_failing_gates(bundle: Path) -> list[str]:
    """Failing gates whose recorded `sources` hashes still match the files.

    Anything else is a verdict about bytes that no longer exist. Returns [] on any
    error, because this only decides how a prompt is worded: a bundle that cannot be
    read here is a problem for the gates to report, not a reason to withhold the
    diagnosis.
    """
    try:
        return [g for g, ok in _gate_freshness(bundle).items() if ok]
    except Exception:
        return []


def _stale_only(bundle: Path) -> list[str]:
    """The failing gates, when EVERY one of them judges bytes that are gone.

    Empty unless the answer is known for every failing gate and is "stale" for each.
    A single fresh failure, or a single gate whose freshness cannot be established,
    disqualifies the cell: the caller uses this to skip the repair agent, and
    skipping it on a cell that does have a live hole is the one mistake this must
    never make.

    A MECHANICAL gate that recorded `error` is excluded from that quorum. Such a gate
    reached no verdict by construction (mutants that timed out, a battery that would
    not run), so it cannot be the live hole this protects, and its remedy is
    re-measuring with room. Counting it is not conservative but inverted: with no
    usable `sources` it answers None, the whole cell fails the quorum, and a cell
    whose every audit finding is provably void goes to an agent to be told there is
    nothing to repair. Excluding it costs nothing: the errored gate keeps the cell red
    either way.

    Audit roles are never excluded, whatever their status. An errored role is a spec
    question nobody answered, `_unmeasured_only` is the guard for it, and dropping it
    here would let a scoped re-audit clear the stale roles and leave it standing.
    """
    fresh = _gate_freshness(bundle)
    st = gate_status(bundle, list(fresh))
    quorum = {g: ok for g, ok in fresh.items()
              if g in AUDIT_GATES or str(st.get(g) or "").lower() != "error"}
    if not quorum or any(ok is not False for ok in quorum.values()):
        return []
    return sorted(quorum)


def _unmeasured_only(bundle: Path) -> list[str]:
    """The failing gates, when EVERY one is a role that reached NO verdict.

    The sibling of `_stale_only`, for the same reason: neither condition is a finding,
    and both are settled by a measurement rather than by an agent. This one catches a
    "verdict" that was never one, a role whose agent timed out or failed to launch and
    was recorded `fail` because the gates are fail-closed. Freshness cannot see it,
    because a role can time out against the exact bytes on disk, so its stamp is fresh
    and `_stale_only` rightly declines it.

    This is a guard rather than an optimisation. The repair prompt's premise is that
    the spec admits a wrong implementation, and here the record names no attack
    because nothing looked; with no counterexample to study, the agent's available
    move is to strengthen the spec on speculation, so a saturated host writes a clause
    into a spec nothing found a defect in.

    Two conditions, both needed. Every failing gate must have reached no verdict on
    `triage`'s own predicate, the same one `_audit_split` labels outcomes with, so a
    cell's lane and its attempt history cannot disagree about what a note means; one
    substantive failure anywhere disqualifies the cell. And every failing gate must be
    an AUDIT gate, because a re-audit re-runs the reviewer roles and nothing else: a
    mechanical gate that hit its verifier cap needs a re-gate with more room. The
    `G-PANEL` aggregate is ignored on both counts, since it only restates its roles.
    """
    try:
        gates = json.loads((bundle / "meta.json").read_text()).get("gates", {})
    except (OSError, ValueError):
        return []               # unknown state is never a reason to skip an agent
    unmeasured = []
    for gk, entry in gates.items():
        if gk == "G-PANEL" or not isinstance(entry, dict):
            continue
        if entry.get("status") in OK:
            continue
        if gk not in AUDIT_GATES or not triage._reached_no_verdict(entry):
            return []
        unmeasured.append(gk)
    return sorted(unmeasured)


# The one defect class each mode is the remedy for. The supervisor's `lane_cmd` is the
# other end of this map and the two must agree: `repair` strengthens a spec that admits
# a wrong implementation, `panel` realigns a spec that is untrue of the real callee or
# that leaks the fix, `mech` realigns an artifact a mechanical gate refuted.
_MODE_REMEDIES = {"repair": "REPAIR", "panel": "PANEL", "mech": "AUTHOR"}


def _misrouted(bundle: Path, mode: str) -> str:
    """Why this cell does not belong to a `mode` driver, or "" if it does.

    Only the AUTHORING classes are compared, and only against each other. Being
    deliberately narrow is what makes this safe to act on:

    * A cell whose class is one of the OTHER two authoring classes is a real misroute.
      Each of those has a lane of its own, and this mode's prompt opens by asserting a
      defect the cell does not have.
    * MECH and REAUDIT are NOT misroutes here, even though no mode of this driver is
      their remedy. Both mean nothing was measured and this driver's own re-audit path
      settles that; releasing them would hand them to a re-gate lane that may not be
      running, and a cell nobody remedies is worse than one remedied indirectly.
    * An unreadable bundle or an unknown mode yields "", never a misroute. This decides
      whether to skip work, so every uncertainty resolves to doing it.
    """
    want = _MODE_REMEDIES.get(mode)
    if want is None:
        return ""
    try:
        gates = json.loads((bundle / "meta.json").read_text()).get("gates", {})
        cls, why = triage.defect_class(gates, [])
    except Exception:
        return ""
    if cls == want or cls not in _MODE_REMEDIES.values():
        return ""
    return (f"cell is {cls} but this driver's mode is {mode} (remedies {want});"
            f" released for the {cls.lower()} lane :: {why}")


def directive_note(iid: str, backend: str, bundle: Path) -> str:
    """A standing structural diagnosis for this cell, if one has been written.

    The diagnosis is separated from the edit: a read-only pass can study a hard cell
    without holding its lock, so it costs no throughput, and it leaves what it found
    where every later attempt by any driver reads it instead of re-deriving it from
    the audit record on the agent's own budget.

    Deliberately advisory. A directive is one earlier reader's analysis, not a gate
    verdict and not machine-checked, so an agent that believes it is wrong must be
    free to say so and proceed; promoting it to an instruction would turn one bad
    reading into every later attempt's dead end.

    It also goes out of date in one damaging direction: a reading of "no live hole,
    the failing record judges a spec that was replaced" can be falsified by a later
    re-audit that re-finds the failure against the current bytes. So the note is
    framed by what the gates have measured against the spec the agent is actually
    looking at, which decides how much weight the opinion can carry.
    """
    path = DIRECTIVES_DIR / f"{iid}.{backend}.md"
    try:
        body = path.read_text().strip()
    except OSError:
        return ""
    if not body:
        return ""
    fresh = _fresh_failing_gates(bundle)
    if fresh:
        standing = (
            "BEFORE you read it: " + ", ".join(fresh) + " currently"
            f" fail{'s' if len(fresh) == 1 else ''} against the exact bytes of"
            " the spec now on disk -- the recorded hashes of what those gates"
            " read still match the files. So a claim below that the finding is"
            " stale, superseded, or already repaired has been overtaken by a"
            " measurement, and repeating it will be refuted. Use the diagnosis"
            " for its structural reading of the hole and treat the live gate as"
            " the authority on whether the hole is still there."
        )
    else:
        standing = (
            "BEFORE you read it: no failing gate on this cell was measured"
            " against the spec now on disk -- every failing record's hashes"
            " refer to content that has since been overwritten. Nothing has"
            " established that the current spec is wrong at all, so if you"
            " cannot reproduce a defect against the current files, reporting"
            " that is the correct outcome and is not a failed attempt."
        )
    return "\n\n".join([
        "\n\n## Structural diagnosis from an earlier read-only pass\n",
        "An agent that did not edit this cell studied the failing gate reports,"
        " the spec, and the patched repo, and recorded what it believed the"
        " underlying hole to be. Use it to skip the re-derivation, not to skip"
        " the checking: it is an opinion, it was not machine-checked, and it may"
        " be wrong. Confirm the part you rely on against the artifacts. If you"
        " conclude it is mistaken, say so in your report and repair what you"
        " actually found.\n",
        standing + "\n",
        body,
    ])


def _attempt_age(rec: dict) -> str:
    """` (Nh ago)` for a history line, or "" if it predates the `at` field.

    Deliberately coarse: the precise time is in the file, and all an agent needs
    from the prompt is whether a refutation is recent enough to be about the spec it
    is looking at. A line with no stamp has a genuinely unknown age, so it says
    nothing rather than guessing zero.
    """
    at = rec.get("at")
    if not isinstance(at, str) or not at:
        return ""
    try:
        when = datetime.fromisoformat(at)
    except ValueError:
        return ""
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    hours = (datetime.now(timezone.utc) - when).total_seconds() / 3600.0
    if hours < 1:
        return " (under an hour ago)"
    if hours < 48:
        return f" ({hours:.0f}h ago)"
    return f" ({hours / 24:.0f}d ago)"


def attempts_note(iid: str, backend: str) -> str:
    """The prompt suffix that tells an agent what its predecessors already did.

    Appended to the rendered prompt rather than templated into it, because the
    templates are shared with other drivers and a placeholder a caller forgets to
    fill raises at render time, which would take down every in-flight cell.
    """
    hist = prior_attempts(iid, backend)
    if not hist:
        return ""
    lines = [
        "\n\n## Attempts already made on this cell\n",
        "This cell has been worked before and is still not green. Each line is",
        "an earlier agent's outcome as the DRIVER judged it, not as that agent",
        "reported it. Do not repeat an approach that is refuted below; if the",
        "same route is still the right one, say why the refutation does not",
        "apply.\n",
        "Where a line carries an age, weigh it: a refutation from hours ago was",
        "measured against roughly the spec you are opening, while an older one",
        "may be about a clause that later attempts already replaced. A line with",
        "no age predates the stamping and its vintage is unknown -- check it",
        "against the spec on disk before treating it as settled.\n",
    ]
    for i, a in enumerate(hist[-ATTEMPT_RECALL:], 1):
        lines.append(f"{i}. `{a.get('mode')}`{_attempt_age(a)} ->"
                     f" **{a.get('status')}**"
                     f" (agent verdict {a.get('verdict') or '-'!r}):"
                     f" {a.get('detail') or ''}")
    lines.append(
        "\nWhat each driver verdict means: `no-edit` the spec files came back"
        " byte-identical, so nothing was repaired; `attack-verifies` the added"
        " clause still admits an attack the audit had already submitted;"
        " `prepatch-passes` the new spec is satisfied by the buggy twin, so it"
        " no longer captures the fix; `weakened` a postcondition was deleted"
        " rather than realigned; `narrowed` the precondition's domain was cut"
        " instead of the behaviour being pinned down; `gates-fail` /"
        " `audit-fail` the edit landed and a gate or a review role that reached a"
        " verdict refuted it (the names are in the detail);"
        " `battery-broken` the spec edit landed but `properties.py` no longer"
        " IMPORTS, so no gate judged the edit at all: its frozen anchors still"
        " quote spec text that was replaced. The detail names the exact anchor."
        " Re-sync the anchors to the spec now on disk (never by weakening or"
        " deleting cases) -- until that is done nothing about the repair route"
        " below has been tested, and no re-audit can run;"
        " `stale-cleared` / `stale-refuted` / `stale-unsettled` no agent ran:"
        " every failing verdict on the cell had been earned against bytes that"
        " were later overwritten, so the driver re-measured the spec instead of"
        " asking anyone to repair a finding that quotes a deleted file."
        " `stale-refuted` is the one that matters to you -- the fresh audit found"
        " a weakness in the spec you are looking at now, so its evidence is"
        " reproducible and is the finding to work from;"
        " `unmeasured-cleared` / `unmeasured-refuted` / `unmeasured-unsettled`"
        " the same three outcomes for the other way a cell can carry no finding:"
        " every failing role had reached no verdict at all (its agent timed out or"
        " never came up) and was stamped `fail` because the gates fail closed, so"
        " again the driver measured the spec rather than asking anyone to repair a"
        " defect nothing had found. Read `unmeasured-cleared` as the spec having"
        " been sound all along on that role, and `unmeasured-refuted` as the first"
        " real finding on the cell;"
        " `gates-unmeasured` /"
        " `audit-unmeasured` the edit landed and the gates or the fresh audit reached NO"
        " verdict on it, so nothing below refutes that route -- treat it as"
        " untested rather than beaten; `dispute-refused` an earlier agent"
        " argued the recorded defect was not real and a fresh audit of the"
        " unedited spec found it again, so that argument is settled;"
        " `dispute-unsettled` the same argument was made and the fresh audit"
        " reached no judgment, so it is still open; `*-timeout` nothing was"
        " concluded, so the work is still to do.")
    return "\n".join(lines)


def agent(iid: str, backend: str, args, log_dir: Path, bundle: Path) -> dict:
    """One repair agent for one cell, in its own process."""
    spec_list = "\n".join(
        f"* `{{root}}/{{iid}}/{backend}/{n}`" for n in SPEC_FILES[backend])
    prompt = {"panel": "spec_panel", "mech": "spec_mech"}.get(
        args.mode, "spec_repair")
    # Each prompt takes only the placeholders its own template declares, and
    # load_prompt errors on an extra kwarg: panel needs the failing roles, mech
    # needs the gate whose report is the evidence.
    extra = ""
    if args.mode == "panel":
        extra = f", roles={failing_roles(bundle)!r}"
    elif args.mode == "mech":
        extra = f", gate={failing_mech_gate(bundle)!r}"
    script = (
        "import sys, json\n"
        f"sys.path.insert(0, {str(ROOT / 'src')!r})\n"
        "from swebench_unified.agent import run_agent_step, DEFAULT_MODEL\n"
        "from swebench_unified.prompts import load_prompt\n"
        "from swebench_unified import paths\n"
        f"iid, bk = {iid!r}, {backend!r}\n"
        f"system = load_prompt('{prompt}_system', backend=bk)\n"
        # `bk` not `backend`: load_prompt takes `backend` itself, so a
        # {backend} placeholder would collide with its own parameter.
        f"user = load_prompt('{prompt}', backend=bk, iid=iid,\n"
        "                   root=paths.tasks_root_rel(), python=sys.executable,\n"
        f"                   bk=bk, spec_files={spec_list!r}{extra})\n"
        f"user += {attempts_note(iid, backend)!r}\n"
        f"user += {directive_note(iid, backend, bundle)!r}\n"
        f"model = {args.model!r} or DEFAULT_MODEL\n"
        "out = run_agent_step(system_prompt=system, user_prompt=user,\n"
        f"                    cwd={str(ROOT)!r}, timeout_s={args.agent_timeout},\n"
        f"                     model=model, submit_step='spec_{args.mode}')\n"
        "print(json.dumps({'payload': getattr(out, 'payload', None)}, default=str))\n"
    )
    log = log_dir / f"{iid}.{backend}.repair.log"
    t0 = time.monotonic()
    with log.open("w") as fh:
        p = subprocess.run(
            [_py(), "-c", script],
            # The repair agent is told to be its own adversary, which runs the
            # same attack verifier the audit does. At the 300s library default a
            # starved verify comes back with no verdict, and an agent reading a
            # run of those concludes its repair holds when nothing was measured.
            env=_env(args.benchmark, args.benchmark_dir,
                     SBU_AGENT_TRACE=str(log_dir / "trace" / iid),
                     SBU_ATTACK_VERIFY_TIMEOUT=str(args.attack_verify_timeout)),
            cwd=str(ROOT), stdout=fh, stderr=subprocess.STDOUT, timeout=None)
    payload = None
    for line in reversed(log.read_text().splitlines()):
        if line.startswith('{"payload"'):
            try:
                payload = json.loads(line).get("payload")
            except json.JSONDecodeError:
                pass
            break
    return {"rc": p.returncode, "wall_s": round(time.monotonic() - t0, 1),
            "payload": payload or {}}


def run_gates(iid: str, backend: str, args, log_dir: Path, gates, tag: str) -> bool:
    log = log_dir / f"{iid}.{backend}.{tag}.log"
    cmd = [_py(), "-m", "swebench_unified.cli", "gates", "--backend", backend,
           "--gates", *gates, "--", iid]
    # run_capped, not subprocess.run: a gate step that overruns has verifier and
    # container children, and killing only the step leaves them running with
    # nobody reading their result.
    return run_capped(cmd, log, _env(args.benchmark, args.benchmark_dir),
                      args.gate_timeout)


def _roles_for(gates) -> list[str] | None:
    """The reviewer agents that inform `gates`, or None for "do not scope".

    There are fewer agents than gates, because one payload can score more than one
    gate. The mapping is inverted from `build_one._AUDIT_AGENTS` at call time rather
    than transcribed, since a second copy can drift from the one the stage dispatches
    on and the failure mode of drift is silent: a role nobody re-derived, reported as
    re-derived. None when the gates name every agent, or none of them, so that a full
    re-audit is still invoked exactly the way every green cell was measured.
    """
    from swebench_unified.construct.build_one import _AUDIT_AGENTS
    inverse = {g: r for r, gs in _AUDIT_AGENTS.items() for g in gs}
    roles: list[str] = []
    for g in gates or ():
        r = inverse.get(g)
        if r and r not in roles:
            roles.append(r)
    if not roles or len(roles) == len(_AUDIT_AGENTS):
        return None
    return roles


def _reaudit_attempts(args) -> int:
    """How many attempts per role the outer re-audit budget can actually pay for.

    The audit stage retries a role that reaches no verdict, and those retries are
    SERIAL within the role, so the cost is attempts * role_timeout plus backoff.
    `REAUDIT_TIMEOUT_DEFAULT` is sized for ONE such attempt, so a larger retry count
    authorises work the wrapper cannot fund, and the excess cannot produce a verdict:
    it produces a discarded re-audit, recorded as inconclusive, which reads downstream
    as "this spec has a hole" when nothing finished looking. So the count is derived
    from the budget rather than the budget raised to fit the count, and an explicit
    SBU_AUDIT_RETRIES is honoured as a CEILING: fewer attempts may be asked for, never
    more than the budget funds.
    """
    role = args.audit_role_timeout
    if role <= 0:
        # A non-positive role cap means "no per-role limit", which divides into
        # any budget an unbounded number of times. Without this the arithmetic
        # returns five figures of attempts and the guard becomes the bug.
        return 1
    affordable = (args.reaudit_timeout - REAUDIT_DERIVATION_RESERVE) // role
    fits = min(REAUDIT_MAX_ATTEMPTS, max(1, affordable))
    env = os.environ.get("SBU_AUDIT_RETRIES")
    if env and env.strip().lstrip("-").isdigit():
        fits = min(fits, max(1, int(env) + 1))
    if fits == 1 and role > args.reaudit_timeout - REAUDIT_DERIVATION_RESERVE:
        # Even a single attempt cannot finish inside the wrapper, so every
        # re-audit this lane runs is pre-committed to being discarded. Say so
        # rather than recording the resulting INCONCLUSIVE as a spec finding.
        print(f"[reaudit] --audit-role-timeout {role}s leaves no room inside "
              f"--reaudit-timeout {args.reaudit_timeout}s (reserving "
              f"{REAUDIT_DERIVATION_RESERVE}s for derivation): every re-audit "
              f"will be killed before it can record a verdict. Raise "
              f"--reaudit-timeout to at least "
              f"{role + REAUDIT_DERIVATION_RESERVE}s.",
              file=sys.stderr, flush=True)
    return fits


def reaudit(iid: str, backend: str, args, log_dir: Path,
            roles: list[str] | None = None) -> bool:
    """A FRESH adversarial audit against the repaired spec, with new attacks
    authored by an agent that did not write the repair.

    The per-role attempt count is derived from the outer budget by
    `_reaudit_attempts`, and the outer cap kills the whole process GROUP, because
    the roles' agent CLIs and their verifiers are grandchildren and killing the step
    alone leaves them running.

    `roles` narrows the measurement to the reviewer agents that inform the gates at
    issue (see `_roles_for`). It is cheaper, but the reason that matters is that each
    role is a fresh adversary authoring its own attacks against the current spec, so
    re-deriving every role to settle one role's verdict puts the others back on the
    dice and any that comes back red is a genuine finding this lane now owns.

    Leave it None wherever the whole cell is being re-measured: after a repair EDIT
    every role's recorded verdict is about bytes the repair replaced.
    """
    script = (
        "import sys\n"
        f"sys.path.insert(0, {str(ROOT / 'src')!r})\n"
        "from swebench_unified.construct.build_one import run_audit_stage\n"
        f"for r in run_audit_stage({iid!r}, {backend!r}, roles={roles!r}):\n"
        "    print(r.gate, r.status, (r.detail or '')[:120])\n"
    )
    log = log_dir / f"{iid}.{backend}.reaudit.log"
    return run_capped(
        [_py(), "-c", script], log,
        _env(args.benchmark, args.benchmark_dir,
             SBU_AUDIT_TIMEOUT=str(args.audit_role_timeout),
             SBU_AUDIT_RETRIES=str(_reaudit_attempts(args) - 1),
             SBU_ATTACK_VERIFY_TIMEOUT=str(args.attack_verify_timeout)),
        args.reaudit_timeout)


def _reaudit_disputed(iid: str, backend: str, args, log_dir: Path, bundle: Path,
                      row: dict, payload: dict) -> dict:
    """Settle a NO-REPAIR-NEEDED claim by re-deriving the verdict it disputes.

    The caller has checked that the spec is UNCHANGED, so this is not a re-audit of a
    repair but a second independent measurement of the same artifact, held to the
    standard every green cell met: a fresh reviewer submits its own admissible attacks,
    a positive control and a reproduced prepatch bug, and the derivation re-runs all of
    them. That standard is the point -- the agent's argument does not clear the cell,
    only a fresh audit does, and if the spec really is too weak the fresh audit says so
    again and the cell returns to this lane with better evidence than it had.
    """
    note = str(payload.get("notes", ""))[:120]
    if args.no_reaudit:
        row["status"], row["detail"] = "no-repair-claimed", note
        return row
    # Scoped to the roles actually in dispute. The agent left the spec alone, so the
    # passing roles' verdicts still describe these exact bytes: re-deriving them
    # settles nothing and risks everything, because a fresh adversary asked to re-judge
    # a spec it already passed can find a hole the recorded one did not.
    disputed = [g for g, v in gate_status(bundle, AUDIT_GATES).items()
                if str(v) in ("fail", "error")]
    if not reaudit(iid, backend, args, log_dir, roles=_roles_for(disputed)):
        row["status"] = "no-repair-claimed"
        row["detail"] = f"disputed the verdict; re-audit timed out > {args.reaudit_timeout}s"
        return row
    green, why = is_green(bundle)
    au = gate_status(bundle, AUDIT_GATES)
    row["detail"] = ("disputed the verdict; fresh audit "
                     + " ".join(f"{k}={v}" for k, v in au.items())
                     + ("" if green else f" || {why}"))[:200]
    if green:
        # A repair: the cell is green on a second independent audit of a spec
        # nobody edited, so the recorded defect was an artifact of the first one.
        row["status"] = "dispute-upheld"
        return row
    # Not green is two very different things and they must not share a label. The fresh
    # audit either FOUND the weakness again, settling the dispute against the agent, or
    # reached no judgment (a verifier hit its cap, an agent did not submit), which
    # settles nothing. Recording the second as a refutation would tell the next agent
    # its predecessor's argument had been tested and beaten when it was never answered,
    # and the attempt history is what the next agent is told not to re-litigate.
    if _reaudit_adjudicated_weakness(bundle):
        row["status"] = "dispute-refused"
    else:
        row["status"] = "dispute-unsettled"
    return row


def _reaudit_stale(iid: str, backend: str, args, log_dir: Path, bundle: Path,
                   row: dict, stale: list[str], label: str = "stale",
                   because: str = "judge bytes no longer on disk") -> dict:
    """Re-measure a cell whose failing verdicts have not judged the spec on disk.

    Two callers, two ways that happens, one remedy. `_stale_only` finds a verdict that
    judged bytes which are gone; `_unmeasured_only` finds a "verdict" that was never
    one, a role that reached no conclusion and was stamped `fail` because the gates are
    fail-closed. `label` and `because` carry which, so the attempt history says what
    was actually true of the cell: calling an unmeasured cell `stale-cleared` would
    file a host outage under the label meaning "repaired, and nobody had looked yet".

    Why this skips the repair agent entirely. An agent handed a stale cell is given a
    finding it cannot reproduce, because the text the finding quotes is no longer in
    the file. Its honest outcome is a NO-REPAIR-NEEDED claim, which `_reaudit_disputed`
    then settles with exactly the re-audit below, so the agent step is spent deciding
    to run a measurement that was already the right next move. And since `run_cell`
    holds the cell lock for its whole cycle, an agent-free re-audit lane cannot take
    the cell away; doing the cheap thing from inside the lock resolves that contention
    instead of racing it.

    The safety property is in the CALLER's predicate, not here: each demands that EVERY
    failing gate be in its condition, so a cell with any live hole, or any gate whose
    freshness cannot be established, still gets an agent.
    """
    row["verdict"], row["agent_s"] = "", 0.0
    seen = ", ".join(stale)
    if args.no_reaudit:
        row["status"] = f"{label}-verdict"
        row["detail"] = f"{seen} {because}; --no-reaudit"
        return row
    # Scoped to the roles whose verdicts are the ones being replaced. The other roles
    # pass on the bytes that are here, so re-judging them is a new roll on a gate this
    # cell has already won, paid for to replace a verdict about bytes that are gone.
    if not reaudit(iid, backend, args, log_dir, roles=_roles_for(stale)):
        row["status"] = f"{label}-unsettled"
        row["detail"] = (f"{seen} {because}; the re-audit"
                         f" that would replace them timed out >"
                         f" {args.reaudit_timeout}s")[:250]
        return row
    green, why = is_green(bundle)
    au = gate_status(bundle, AUDIT_GATES)
    shown = " ".join(f"{k}={v}" for k, v in au.items())
    if green:
        # The spec on disk was already sound; the only thing wrong with the cell
        # was that nobody had measured it since it was repaired.
        row["status"] = f"{label}-cleared"
        row["detail"] = (f"{seen} {because}; fresh"
                         f" audit of the spec on disk: {shown}")[:250]
        return row
    if _reaudit_adjudicated_weakness(bundle):
        # Now there IS a live hole, found against the bytes an agent will read.
        # That is the point of coming here first: the next attempt gets evidence
        # it can reproduce instead of a quotation from a deleted file.
        row["status"] = f"{label}-refuted"
        row["detail"] = (f"re-audited because {seen} {because}; the fresh audit"
                         f" found a weakness in the CURRENT spec: {shown}"
                         f" || {why}")[:250]
        return row
    row["status"] = f"{label}-unsettled"
    row["detail"] = (f"re-audited because {seen} {because}; the fresh audit"
                     f" reached no verdict: {shown} || {why}")[:250]
    return row


def _reaudit_adjudicated_weakness(bundle: Path) -> bool:
    """Did the fresh audit ADJUDICATE the spec too weak, or just fail to judge?

    Uses triage's own classifier so there is one authority on what a recorded audit
    note means: the lane a cell routes to and the label its attempt history carries
    cannot be allowed to disagree.
    """
    try:
        gates = json.loads((bundle / "meta.json").read_text()).get("gates", {})
    except (OSError, ValueError):
        return False
    return triage.defect_class(gates, [])[0] == triage.REPAIR


def _audit_split(bundle: Path) -> tuple[list[str], list[str]]:
    """The not-passing audit roles, split into refutations and non-measurements.

    A role that ran and judged the new spec is evidence about the REPAIR. A role whose
    agent never came up, or that submitted no verdict, is evidence about the HOST. Both
    are stamped `fail`, correctly, since an unjudged spec is not a green spec, but they
    call for opposite next moves: change the approach, or re-run the same one.
    Conflating them tells every later agent that a fresh audit refuted the edit, which
    is the one instruction that makes a real repair harder to find. Same predicate
    triage routes on, so a cell's lane and its attempt history cannot disagree about
    what a recorded note means.
    """
    try:
        gates = json.loads((bundle / "meta.json").read_text()).get("gates", {})
    except (OSError, ValueError):
        return [], []
    refuted: list[str] = []
    unmeasured: list[str] = []
    for k in AUDIT_GATES:
        entry = gates.get(k) or {}
        if entry.get("status") in OK:
            continue
        (unmeasured if triage._reached_no_verdict(entry)
         else refuted).append(k)
    return refuted, unmeasured


def run_cell(iid: str, backend: str, args, log_dir: Path) -> dict:
    bundle = ROOT / args.benchmark_dir / iid / backend
    row = {"iid": iid, "backend": backend}
    try:
        with cell_lock(bundle):
            row = _locked(iid, backend, args, log_dir, bundle, row)
    except CellBusy as e:
        # Not an attempt: no agent ran, so recording it would push a real
        # refutation out of the recalled history with a scheduling artifact.
        row["status"], row["detail"] = "busy", f"held by {e}; skipped"
        return row
    if row.get("status") not in ("already-green", "busy", "launch-failed"):
        record_attempt(iid, backend, args.mode, row)
    return row


def _locked(iid: str, backend: str, args, log_dir: Path, bundle: Path,
            row: dict) -> dict:
    # Re-check under the lock: --resume filtered at LAUNCH and another driver may
    # have finished this cell since.
    if args.resume and is_green(bundle)[0]:
        row["status"], row["detail"] = "already-green", "green before its turn came"
        return row

    # Before spending an agent: is there anything here it could reproduce? A cell whose
    # every failing verdict was earned against bytes that have since been overwritten
    # needs a measurement, not a repair. See `_reaudit_stale`. `panel` takes the same
    # route as `repair`, and for a sharper reason: its remedy is to have an adversary
    # re-judge faithfulness, so on a stale cell a fresh panel roll against a spec
    # nobody has measured is how a repaired cell reacquires a weakness verdict it no
    # longer deserves. `mech` is deliberately excluded: its failing gates are
    # mechanical, and the remedy below re-runs AUDIT roles (`_roles_for`), which would
    # leave a stale mechanical stamp exactly as stale as it found it.
    if args.mode in ("repair", "panel") and not args.no_stale_fast_path:
        stale = _stale_only(bundle)
        if stale:
            return _reaudit_stale(iid, backend, args, log_dir, bundle, row, stale)
        # The other way a cell can carry no finding: every failing role reached no
        # verdict, so the `fail` is fail-closed bookkeeping about the HOST and
        # names no attack for an agent to reproduce. Checked second because it is
        # the narrower condition, and separately because such a stamp is FRESH --
        # a role times out against the very bytes on disk -- so the freshness test
        # above rightly declines it and the cell would otherwise reach the agent.
        unmeasured = _unmeasured_only(bundle)
        if unmeasured:
            return _reaudit_stale(iid, backend, args, log_dir, bundle, row,
                                  unmeasured, label="unmeasured",
                                  because="reached no verdict, so nothing has"
                                          " judged this spec")

    # And: is this cell's defect still the one this driver's mode remedies? The lane
    # was written from a classification taken at launch, and a cell whose audit has
    # been re-run since may have moved (REPAIR -> PANEL, when the fresh audit finds no
    # verifying rival but does find the clause untrue of the real callee).
    #
    # Running the wrong remedy is not a no-op: a repair agent is told as its premise
    # that the spec admits a wrong implementation, so on a cell whose only defect is
    # faithfulness it hunts for a hole that is not there and its available move is to
    # strengthen a spec that already claims too much. So release the cell instead,
    # quickly and with the reason recorded, and let the lane whose mode matches take
    # it: the supervisor re-derives lanes every cycle, so that lane exists by the next.
    if not args.no_misroute_guard:
        wrong = _misrouted(bundle, args.mode)
        if wrong:
            row["status"], row["verdict"], row["agent_s"] = "misrouted", "", 0.0
            row["detail"] = wrong[:250]
            return row

    watched = ORACLE_FILES if args.mode == "mech" else ()
    before = spec_sha(bundle, backend, watched)
    a = agent(iid, backend, args, log_dir, bundle)
    p = a["payload"]
    row["agent_s"], row["verdict"] = a["wall_s"], str(p.get("verdict", ""))[:40]
    after = spec_sha(bundle, backend, watched)

    # An agent that never ran leaves NOTHING: no submission, a non-zero exit, and a
    # byte-identical spec. `run_agent_step` already retried the launch and gave up, so
    # there is no repair to measure, and measuring anyway is wrong twice over: it
    # spends a gate sweep and a fresh audit on a spec that is already stamped, then
    # writes the unchanged stamp back as this attempt's outcome, so the history tells
    # the next agent its route was refuted when nothing was tried.
    #
    # The unchanged-spec conjunct is what makes this safe: an agent that edited the
    # spec and then died DID work, and its edit has to be measured however it exited.
    if a.get("rc") and not p and before == after:
        row["status"] = "launch-failed"
        row["detail"] = f"the agent produced nothing in {a['wall_s']}s; " \
                        f"spec untouched, so nothing to measure"
        return row

    # A "REPAIRED" claim with an unchanged spec is not a repair.
    if row["verdict"].upper().startswith("REPAIRED") and before == after:
        row["status"] = "no-edit"
        row["detail"] = "claimed REPAIRED but the spec files are byte-identical"
        return row
    if row["verdict"].upper().startswith("NO-REPAIR"):
        if before != after:
            # Edited anyway, which contradicts its own verdict: needs a human.
            row["status"] = "inconsistent"
            row["detail"] = str(p.get("notes", ""))[:120]
            return row
        # The agent read the recorded verdict and argues there is no defect to repair.
        # Reporting that and stopping makes the cell immortal: the stamp stays, the
        # cell stays not-green, and the next round hands the same argument to another
        # agent that reaches the same conclusion.
        #
        # A disputed verdict is settled by RE-DERIVING it, not by the dispute. So
        # re-run the audit once: a fresh reviewer authors new attacks against this spec
        # and the derivation re-measures them. If the weakness is real the cell comes
        # back with fresh evidence; if the old stamp was an artifact (a patch that
        # never applied, a resolve that dropped out under load) the cell clears on its
        # own merits. ONE re-audit, never a loop: retrying until an audit happens to
        # pass is how a weak spec would sneak through.
        return _reaudit_disputed(iid, backend, args, log_dir, bundle, row, p)

    # The invariants a green stamp cannot see.
    if p.get("narrowed_precondition"):
        row["status"] = "narrowed"
        row["detail"] = "agent narrowed the precondition, which shrinks the claim"
        return row
    if p.get("prepatch_still_fails") is False:
        row["status"] = "prepatch-passes"
        row["detail"] = "prepatch twin satisfies the new spec, so the fix is lost"
        return row
    if args.mode == "mech":
        # A mech repair's failure mode is not a weakened spec, it is a weakened
        # MEASUREMENT: the gate passes because the shadow stopped generating the
        # inputs that disagreed, or the failing assertion is gone. Nothing
        # mechanical can catch that, because the forged oracle is what runs.
        if p.get("domain_narrowed"):
            row["status"] = "domain-narrowed"
            row["detail"] = "excluded the diverging inputs instead of modelling them"
            return row
        if p.get("oracle_unchanged") is False and not str(
                p.get("oracle_change_justification") or "").strip():
            row["status"] = "oracle-edited"
            row["detail"] = "edited the check script with no mis-encoding argument"
            return row
        remaining = p.get("disagreements_after")
        if isinstance(remaining, int) and remaining > 0:
            row["status"] = "still-diverging"
            row["detail"] = f"{remaining} disagreement(s) remain"
            return row
    if args.mode == "panel":
        # A faithfulness repair is only real if the divergence CLOSED. Every gate
        # here already passed before the repair (that is why the cell reached this
        # lane), so nothing mechanical can tell realigning the model apart from
        # deleting the claim that exposed the divergence.
        if p.get("weakened_postcondition"):
            row["status"] = "weakened"
            row["detail"] = "postcondition deleted rather than realigned"
            return row
        if p.get("witness_agrees") is False:
            row["status"] = "witness-diverges"
            row["detail"] = (f"model {str(p.get('model_output_after'))[:40]!r} != "
                             f"real {str(p.get('real_output'))[:40]!r}")
            return row
        # The audit's own attacks are the control on weakening: they were built
        # against this spec and must still fail.
        live = [a for a in (p.get("attacks_rechecked") or [])
                if isinstance(a, dict) and a.get("verifies")]
        if live:
            row["status"] = "attack-verifies"
            row["detail"] = f"{len(live)} re-checked attack(s) now verify"
            return row

    all_gates = STATIC_GATES + ("G-RESOLVE", "G-CONF", "G-AX")
    if not run_gates(iid, backend, args, log_dir, all_gates, "gates"):
        row["status"], row["detail"] = "gate-timeout", f"> {args.gate_timeout}s"
        return row
    # Every DOCKER gate counts too, not just G-RESOLVE. G-CONF shadows the model
    # against the real patched callee over many inputs, so on a faithfulness repair
    # it is the gate most likely to catch a realignment that fixed the reviewer's
    # single witness and left the rest of the class diverging.
    st = gate_status(bundle, all_gates)
    bad = {k: v for k, v in st.items() if v not in OK}
    # A gate that REFUTED the edit says `fail`. A gate that says `error`, or that left
    # no stamp, reached no verdict about anything: the verifier did not launch, an
    # import failed, the host was full. The two cannot share a label, for the same
    # reason as the audit split below, and here the measurement is cheap enough to just
    # repeat -- several gates erroring at once is the runner failing rather than
    # independent refutations. Exactly one retry: a gate that keeps not running is a
    # host problem and a loop here would spin on it.
    if bad and "fail" not in bad.values():
        if not run_gates(iid, backend, args, log_dir, sorted(bad), "gates-retry"):
            row["status"] = "gate-timeout"
            row["detail"] = f"re-measuring {','.join(sorted(bad))} > {args.gate_timeout}s"
            return row
        st = gate_status(bundle, all_gates)
        bad = {k: v for k, v in st.items() if v not in OK}
    if bad:
        refuting = {k: v for k, v in bad.items() if v == "fail"}
        # Before calling an unmeasured sweep unmeasured: a G-PBT that errored
        # because the battery will not IMPORT is a measured, mechanical defect with
        # a named cause, and reporting it as "no verdict" leaves the cell with no
        # actionable next move forever. See `battery_load_error`.
        if not refuting and bad.get("G-PBT") == "error":
            why = battery_load_error(iid, backend, args)
            if why:
                row["status"] = "battery-broken"
                row["detail"] = (
                    f"properties.py does not import :: {why} :: the spec edit"
                    " itself was never judged -- re-sync the battery's frozen"
                    " anchors to the spec text now on disk (do not weaken or"
                    " delete cases), then the gates can measure the repair"
                )[:250]
                return row
        row["status"] = "gates-fail" if refuting else "gates-unmeasured"
        shown = refuting or bad
        row["detail"] = (" ".join(f"{k}={v}" for k, v in shown.items())
                         + ("" if refuting else " (no verdict, twice)"))[:120]
        return row

    if args.no_reaudit:
        row["status"], row["detail"] = "gates-green", "re-audit skipped (--no-reaudit)"
        return row
    # Deliberately UNSCOPED. The agent edited the spec, so every role's recorded
    # verdict -- the passing ones included -- is about bytes that are gone, and the
    # question this answers is whether the spec now on disk survives the whole
    # panel. Narrowing it here is how a repair that closes G-EQ by relaxing a
    # postcondition gets recorded as green with an unfaithful clause nobody re-read.
    if not reaudit(iid, backend, args, log_dir):
        row["status"], row["detail"] = "reaudit-timeout", f"> {args.reaudit_timeout}s"
        return row
    au = gate_status(bundle, AUDIT_GATES)
    green, why = is_green(bundle)
    head = "audit " + " ".join(f"{k}={v}" for k, v in au.items())
    if green:
        row["status"], row["detail"] = "repaired", head[:200]
        return row
    refuted, unmeasured = _audit_split(bundle)
    if refuted:
        row["status"] = "audit-fail"
        row["detail"] = (f"{head} || refuted by {', '.join(refuted)}"
                         + (f"; no verdict from {', '.join(unmeasured)}"
                            if unmeasured else "") + f" || {why}")[:250]
    elif unmeasured:
        row["status"] = "audit-unmeasured"
        row["detail"] = (f"{head} || NOT JUDGED: no verdict from "
                         f"{', '.join(unmeasured)} || {why}")[:250]
    else:
        # Every role passed, so what is not green is mechanical: the re-audit
        # re-stamps G-CONF and G-RESOLVE, and one of them moved after the gate
        # sweep above read them green.
        row["status"] = "gates-fail"
        row["detail"] = f"{head} || {why}"[:200]
    return row


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lane-file", required=True,
                    help="<instance_id>\\t<backend> per line")
    ap.add_argument("--mode", choices=["repair", "panel", "mech"],
                    default="repair",
                    help="repair = spec too weak (a verifying attack whose patch "
                         "does not resolve); panel = spec unfaithful or leaking; "
                         "mech = a mechanical gate refuted the artifact")
    ap.add_argument("--benchmark", default=os.environ.get(
        "SBU_BENCHMARK", benchmarks.DEFAULT_BENCHMARK))
    ap.add_argument("--benchmark-dir", default=default_benchmark_dir())
    ap.add_argument("--jobs", type=int, default=JOBS_DEFAULT,
                    help="concurrent AGENTS")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--agent-timeout", type=int, default=AGENT_TIMEOUT_DEFAULT)
    ap.add_argument("--gate-timeout", type=int, default=GATE_TIMEOUT_DEFAULT)
    ap.add_argument("--reaudit-timeout", type=int, default=REAUDIT_TIMEOUT_DEFAULT)
    ap.add_argument("--audit-role-timeout", type=int, default=ROLE_TIMEOUT_DEFAULT)
    ap.add_argument("--attack-verify-timeout", type=int,
                    default=ATTACK_TIMEOUT_DEFAULT,
                    help="per-attack verifier cap, inside a role and inside the "
                         "repair agent's own adversary runs")
    ap.add_argument("--model", default=None)
    ap.add_argument("--resume", action="store_true",
                    help="skip cells already fully green")
    ap.add_argument("--no-reaudit", action="store_true",
                    help="stop after the gates (leaves the spec unchallenged)")
    ap.add_argument("--no-stale-fast-path", action="store_true",
                    help="in repair/panel mode, spend an agent even when every "
                         "failing verdict judges bytes no longer on disk")
    ap.add_argument("--no-misroute-guard", action="store_true",
                    help="run this mode's remedy even on a cell whose defect "
                         "class is a different authoring class")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--tag", default="r1")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    target = ROOT / args.benchmark_dir
    todo = []
    for ln in Path(args.lane_file).read_text().split("\n"):
        parts = ln.split()
        if len(parts) < 2:
            continue
        iid, backend = parts[0], parts[1]
        bundle = target / iid / backend
        if not bundle.is_dir() or backend not in SPEC_FILES:
            continue
        if args.resume and is_green(bundle)[0]:
            continue
        todo.append((iid, backend))
    if args.limit:
        todo = todo[:args.limit]

    log_dir = EXPERIMENTS_ROOT / "spec_repair" / args.tag
    log_dir.mkdir(parents=True, exist_ok=True)
    print(f"# {len(todo)} cell(s), jobs={args.jobs}, tag={args.tag}", flush=True)
    if args.dry_run:
        for iid, bk in todo:
            print(f"   {bk:<8} {iid}")
        return 0

    # The MODE, not a literal: this string is what the cell lock's holder line carries,
    # so it is how a live cell's owner is identified from outside. Hard coded, every
    # panel and mech driver would read as a repair driver and any survey of what the
    # fleet is doing to a cell would name the wrong remedy.
    os.environ["SBU_WAVE_TAG"] = f"{args.tag}/{args.mode}"
    rows, counts = [], {}
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futs = {pool.submit(run_cell, i, b, args, log_dir): (i, b)
                for i, b in todo}
        done = 0
        for fut in as_completed(futs):
            row = fut.result()
            rows.append(row)
            done += 1
            counts[row["status"]] = counts.get(row["status"], 0) + 1
            print(f"[{done}/{len(todo)}] {row['status']:<18} "
                  f"{row['backend']:<7} {row['iid']:<34} "
                  f"{row.get('detail', '')[:80]}", flush=True)
    print("# " + json.dumps(counts, indent=1))
    if args.out:
        Path(args.out).write_text(
            json.dumps({"summary": counts, "rows": rows}, indent=1) + "\n")
        print(f"# -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
