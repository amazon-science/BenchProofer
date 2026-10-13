# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""G-CONF — differential conformance: shadow of the formal impl vs the real
patched repo function, >=1e5 hypothesis inputs, pinned seed, in-container.
Runs on ALL backends (docs/architecture.md §5); nagini's shadow is the
impl region run directly. REFUTES R/I fidelity, does not prove it.

Missing conformance_check.py => explicit skip, not error, tagged
`conf_missing_script: true`. That tag is NOT a real verdict for green
(green_check / viz _conf_is_real_verdict): a bundle that predates the gate has
no script yet and must have one constructed, not skipped around. The status
stays "skip" (a fail would conflate "no script yet" with a real conformance
disagreement). Otherwise runs with the gold patch, recording shadow provenance
and the optional structured report; a report declaring `unsupported` constructs
is an explicit skip, never a silent pass (docs/architecture.md §5).
`conf_skip: true` (impl all-A-tagged) => explicit skip; weight shifts to
G-AX/G-EQ/G-PANEL.
"""
from __future__ import annotations

import json

from ..docker_exec import ensure_image, run_in_container
from .base import Bundle, GateResult
from ._common import docker_oracle_skip, env_int

name = "G-CONF"
applies_to = ("nagini", "velvet", "lean")
needs_docker = True
agentic = False
# Bundle files this gate's verdict depends on; digested into the record so a
# stamp can be checked against the artifact it describes (base.source_digests).
# The shadow and the impl it shadows: re-authoring either one invalidates a
# conformance verdict about the pair.
reads = ("conformance_check", "solution")

CONTAINER_TIMEOUT_DEFAULT = 1800


def run(bundle: Bundle, *, mode: str = "strict") -> GateResult:
    if (skip := docker_oracle_skip(name)) is not None:
        return skip
    if bool(bundle.meta().get("conf_skip", False)):
        return GateResult(name, "skip",
                          "no-RI-content (impl region all-A-tagged)",
                          {"conf_skipped": True})
    shadow = bundle.backend.conf_shadow(bundle.root)
    if shadow is None:
        return GateResult(
            name, "skip",
            "no conformance_check.py (no-RI-content or not yet constructed)",
            {"conf_missing_script": True})
    if not bundle.patch_diff.exists():
        return GateResult(name, "error", "patch.diff missing")
    err = ensure_image(bundle.instance_id)
    if err:
        return GateResult(name, "error", err)
    timeout = env_int("SBU_CONTAINER_TIMEOUT", CONTAINER_TIMEOUT_DEFAULT)
    r = run_in_container(bundle.instance_id, str(bundle.root.resolve()),
                         shadow.script.name,
                         gold_patch_path=str(bundle.patch_diff.resolve()),
                         apply_gold=True, timeout=timeout, need_hypothesis=True)
    data = {"exit": r.returncode, "shadow_provenance": shadow.provenance}
    if r.returncode == 124:
        return GateResult(name, "timeout", r.stderr[-200:], data)
    lines = r.stdout.strip().splitlines() or [""]
    detail = lines[-1]
    report = _structured_report(lines)
    if report is not None:
        data["report"] = report
        if report.get("unsupported"):
            # unmodelable constructs: explicit skip, never a silent pass
            return GateResult(
                name, "skip",
                f"shadow reports unsupported constructs: {report['unsupported']}",
                data)
    status = "pass" if r.ok else "fail"
    if status == "fail":
        # A checker that cannot START prints nothing to stdout, so `detail` above
        # is the `[""]` fallback and the reason -- a SyntaxError, a missing import,
        # an interpreter that will not accept the file -- is on stderr. Without
        # this the record is `G-CONF=fail` with an EMPTY detail: a red cell naming
        # no reason. (One real cause: a non-ASCII comment byte is a PEP 263
        # SyntaxError under the python 2.7 an older instance's image ships.)
        err = (r.stderr or "").strip()
        if not detail:
            detail = (f"stderr: {err[-300:]}" if err
                      else f"no output; exit {r.returncode}")
        elif err:
            detail = f"{detail} | stderr: {err[-300:]}"
    return GateResult(name, status, detail, data)


def _structured_report(stdout_lines: list[str]) -> dict | None:
    """Last stdout line that parses as a JSON object, if any."""
    for line in reversed(stdout_lines):
        line = line.strip()
        if line.startswith("{") and line.endswith("}"):
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                return None
            return obj if isinstance(obj, dict) else None
    return None
