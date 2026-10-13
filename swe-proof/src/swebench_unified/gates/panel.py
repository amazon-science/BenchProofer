# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""G-PANEL — agentic blind attacker panel (roles: spec-too-weak,
faithfulness, leakage). Reads recorded per-role gates.G-PANEL-<n> verdicts
(legacy collective G-PANEL fallback), returning the worst status; none
recorded => explicit skip. Running the attackers is construct-mode P2 work
(_audit.run_audit), never done here."""
from __future__ import annotations

from .base import Bundle, GateResult
from ._audit import recorded_verdict

name = "G-PANEL"
applies_to = ("nagini", "velvet", "lean", "ears")
needs_docker = False
agentic = True
# Bundle files this gate's verdict depends on; digested into the record
# so a stamp can be checked against the artifact it describes (base.source_digests).
reads = ("solution", "properties")

ROLES = {1: "spec-too-weak", 2: "faithfulness", 3: "leakage"}

# `reads` for each per-role record this gate summarises, which is NARROWER than
# the gate's own: only the spec-too-weak role attacks the battery, while
# faithfulness and leakage judge the spec view alone. The distinction is what
# keeps a checker from calling those two records stale whenever the battery was
# re-authored -- nothing they looked at moved. Recorded here rather than in the
# construct stage that writes the roles, because these are G-PANEL's record keys
# and a checker holding only a bundle has to be able to resolve them.
SUBGATE_READS = {"G-PANEL-1": ("solution", "properties"),
                 "G-PANEL-2": ("solution",),
                 "G-PANEL-3": ("solution",)}

# worst-first ordering (record_audit's status set; leakage relaxation is
# recorded as "pass" + note, never a status)
_SEVERITY = ("fail", "blocked", "pass", "skip")


def run(bundle: Bundle, *, mode: str = "strict") -> GateResult:
    per_role = {n: recorded_verdict(bundle, f"G-PANEL-{n}") for n in ROLES}
    found = {n: r for n, r in per_role.items() if r is not None}
    if found:
        worst = min((r.status for r in found.values()),
                    key=lambda s: _SEVERITY.index(s) if s in _SEVERITY else 0)
        detail = "; ".join(
            f"G-PANEL-{n} ({ROLES[n]}): {r.status}" + (f" — {r.detail}" if r.detail else "")
            for n, r in sorted(found.items()))
        missing = [f"G-PANEL-{n}" for n in ROLES if n not in found]
        if missing:
            detail += f"; unrecorded roles: {missing}"
        return GateResult(name, worst, detail,
                          {"roles": {f"G-PANEL-{n}": r.to_json()
                                     for n, r in found.items()}})
    # legacy collective G-PANEL entry
    r = recorded_verdict(bundle, name)
    if r is not None:
        return r
    return GateResult(name, "skip",
                      "no recorded G-PANEL verdict in meta.json (P2 audit not run)")
