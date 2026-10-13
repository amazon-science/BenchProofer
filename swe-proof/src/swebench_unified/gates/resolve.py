# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""G-RESOLVE — patch.diff resolves under the official SWE-bench harness;
velvet/lean flaky-retry policy: resolved-on-any-attempt counts, flagged
flaky when attempts disagree."""
from __future__ import annotations

from ..docker_exec import ensure_image
from ..harness import base_lane_intact, run_resolve
from ..paths import RUN_PREFIX
from .base import Bundle, GateResult
from ._common import docker_oracle_skip, env_int

name = "G-RESOLVE"
applies_to = ("nagini", "velvet", "lean", "ears")
needs_docker = True
agentic = False
# Bundle files this gate's verdict depends on; digested into the record so a
# stamp can be checked against the artifact it describes (base.source_digests).
# This gate grades a patch against a task, and both are edited: patch.diff is
# re-derived when a refinement changes, and the frozen row is what names the
# tests. The solution is deliberately absent -- the oracle never sees it.
reads = ("patch", "instance")

RESOLVE_TIMEOUT_DEFAULT = 3600


def run(bundle: Bundle, *, mode: str = "strict") -> GateResult:
    if (skip := docker_oracle_skip(name)) is not None:
        return skip
    if not bundle.patch_diff.exists():
        return GateResult(name, "error", "patch.diff missing")
    err = ensure_image(bundle.instance_id)
    if err:
        return GateResult(name, "error", err)
    timeout = env_int("SBU_RESOLVE_TIMEOUT", RESOLVE_TIMEOUT_DEFAULT)
    res = run_resolve(bundle.instance_id, bundle.patch_diff.read_text(),
                      run_id=f"sbu-resolve-{RUN_PREFIX}-{bundle.backend.name}"
                             f"-{bundle.instance_id}",
                      timeout=timeout)
    if not res.completed:
        return GateResult(name, "error", res.note)
    data = {"resolved": res.resolved, "attempts": res.attempts,
            "flaky": res.flaky}
    if res.resolved:
        return GateResult(name, "pass", res.note, data)
    # Before recording "the gold patch does not resolve", establish that the
    # oracle could judge ANY patch here. Some instances' suites reach the network,
    # and in a sealed container every one of those tests fails whatever is
    # applied; PASS_TO_PASS failing with no source change proves it, since those
    # tests pass at the base commit by definition. Probed only on this path, so a
    # healthy corpus never pays for it.
    intact, failures, why = base_lane_intact(bundle.instance_id, timeout=timeout)
    data["base_probe"] = why
    if intact is False:
        data["base_pass_to_pass_failures"] = failures
        # skip, not fail: a fail here is a false statement about the gold patch,
        # and it sends a repair lane to edit a spec that was never measured.
        return GateResult(name, "skip",
                          "oracle unfit for this instance on this host: " + why,
                          data)
    if intact is None:
        # The probe is the evidence; without it there is no verdict to record.
        return GateResult(name, "error", f"{res.note}; {why}", data)
    return GateResult(name, "fail", res.note, data)
